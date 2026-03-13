#!/usr/bin/env python3
"""
collector.py
────────────
App que roda no container PostgreSQL e coleta dados da API Open-Meteo,
gravando diretamente nas tabelas raw.open_meteo_hourly e raw.open_meteo_daily.

O Airbyte então lê dessas tabelas como Source (PostgreSQL CDC ou full refresh)
e envia ao BigQuery como Destination — sem precisar de conector HTTP customizado.

Modos de execução:
  python3 collector.py --mode once       # executa uma vez e sai
  python3 collector.py --mode scheduled  # loop contínuo com schedule
  python3 collector.py --mode backfill --start 2024-01-01 --end 2024-12-31
"""

import os
import argparse
import logging
import time
from datetime import datetime, timedelta, date
from typing import Generator

import requests
import psycopg2
import psycopg2.extras
import schedule

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Configuração ──────────────────────────────────────────────────────────────
API_BASE = "https://api.open-meteo.com/v1"
API_TIMEOUT = 30

HOURLY_VARS = (
    "temperature_2m,relative_humidity_2m,precipitation,"
    "wind_speed_10m,wind_direction_10m,surface_pressure,"
    "cloud_cover,visibility,weather_code"
)

DAILY_VARS = (
    "temperature_2m_max,temperature_2m_min,precipitation_sum,"
    "rain_sum,wind_speed_10m_max,sunrise,sunset,uv_index_max"
)

LOCATIONS = [
    # ── Santa Catarina — Grande Florianópolis ─────────────────────────────────
    {"id": "florianopolis",               "lat": -27.5954, "lon": -48.5480},
    {"id": "palhoca",                     "lat": -27.6444, "lon": -48.6694},
    {"id": "santo_amaro_da_imperatriz",   "lat": -27.6936, "lon": -48.7697},
    {"id": "angelina",                    "lat": -27.5697, "lon": -48.9658},

    # ── Santa Catarina — Litoral Sul ──────────────────────────────────────────
    {"id": "garopaba",                    "lat": -28.0248, "lon": -48.6186},
    {"id": "imbituba",                    "lat": -28.2400, "lon": -48.6639},
    {"id": "laguna",                      "lat": -28.4844, "lon": -48.7812},
    {"id": "tubarao",                     "lat": -28.4671, "lon": -49.0092},
    {"id": "criciuma",                    "lat": -28.6773, "lon": -49.3700},
    {"id": "ararangua",                   "lat": -28.9344, "lon": -49.4866},

    # ── Santa Catarina — Serra / Planalto ─────────────────────────────────────
    {"id": "lages",                       "lat": -27.8153, "lon": -50.3261},
    {"id": "campos_novos",                "lat": -27.4011, "lon": -51.2258},
    {"id": "joaçaba",                     "lat": -27.1767, "lon": -51.5047},

    # ── Santa Catarina — Litoral Norte / Vale do Itajaí ──────────────────────
    {"id": "balneario_camboriu",          "lat": -26.9906, "lon": -48.6342},
    {"id": "itajai",                      "lat": -26.9069, "lon": -48.6606},
    {"id": "joinville",                   "lat": -26.3045, "lon": -48.8487},

    # ── Santa Catarina — Oeste ────────────────────────────────────────────────
    {"id": "chapeco",                     "lat": -27.1006, "lon": -52.6156},
    {"id": "sao_miguel_do_oeste",         "lat": -26.7278, "lon": -53.5167},
]

# ── Conexão PostgreSQL ────────────────────────────────────────────────────────

def get_connection():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        dbname=os.environ.get("POSTGRES_DB", "weather_staging"),
        user=os.environ.get("POSTGRES_USER", "weather_user"),
        password=os.environ.get("POSTGRES_PASSWORD", "weather_pass"),
    )


# ── Fetchers da API ───────────────────────────────────────────────────────────

def fetch_forecast(location: dict, start_date: str, end_date: str) -> dict:
    params = {
        "latitude":   location["lat"],
        "longitude":  location["lon"],
        "hourly":     HOURLY_VARS,
        "daily":      DAILY_VARS,
        "timezone":   "America/Sao_Paulo",
        "start_date": start_date,
        "end_date":   end_date,
    }
    resp = requests.get(f"{API_BASE}/forecast", params=params, timeout=API_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


# ── Flatten de dados horários ─────────────────────────────────────────────────

def iter_hourly_records(raw: dict, location_id: str) -> Generator[dict, None, None]:
    hourly = raw.get("hourly", {})
    times = hourly.get("time", [])
    vars_list = [v for v in HOURLY_VARS.split(",")]
    now = datetime.utcnow()

    for i, ts in enumerate(times):
        yield {
            "location_id":          location_id,
            "timestamp":            ts,
            "latitude":             raw.get("latitude"),
            "longitude":            raw.get("longitude"),
            "elevation":            raw.get("elevation"),
            "timezone":             raw.get("timezone"),
            "temperature_2m":       hourly.get("temperature_2m",       [None] * len(times))[i],
            "relative_humidity_2m": hourly.get("relative_humidity_2m", [None] * len(times))[i],
            "precipitation":        hourly.get("precipitation",         [None] * len(times))[i],
            "wind_speed_10m":       hourly.get("wind_speed_10m",        [None] * len(times))[i],
            "wind_direction_10m":   hourly.get("wind_direction_10m",    [None] * len(times))[i],
            "surface_pressure":     hourly.get("surface_pressure",      [None] * len(times))[i],
            "cloud_cover":          hourly.get("cloud_cover",           [None] * len(times))[i],
            "visibility":           hourly.get("visibility",            [None] * len(times))[i],
            "weather_code":         hourly.get("weather_code",          [None] * len(times))[i],
            "_extracted_at":        now,
        }


# ── Flatten de dados diários ──────────────────────────────────────────────────

def iter_daily_records(raw: dict, location_id: str) -> Generator[dict, None, None]:
    daily = raw.get("daily", {})
    dates = daily.get("time", [])
    now = datetime.utcnow()

    for i, d in enumerate(dates):
        yield {
            "location_id":        location_id,
            "date":               d,
            "latitude":           raw.get("latitude"),
            "longitude":          raw.get("longitude"),
            "temperature_2m_max": daily.get("temperature_2m_max", [None] * len(dates))[i],
            "temperature_2m_min": daily.get("temperature_2m_min", [None] * len(dates))[i],
            "precipitation_sum":  daily.get("precipitation_sum",  [None] * len(dates))[i],
            "rain_sum":           daily.get("rain_sum",            [None] * len(dates))[i],
            "wind_speed_10m_max": daily.get("wind_speed_10m_max",  [None] * len(dates))[i],
            "sunrise":            daily.get("sunrise",             [None] * len(dates))[i],
            "sunset":             daily.get("sunset",              [None] * len(dates))[i],
            "uv_index_max":       daily.get("uv_index_max",        [None] * len(dates))[i],
            "_extracted_at":      now,
        }


# ── Upsert no PostgreSQL ──────────────────────────────────────────────────────

UPSERT_HOURLY = """
    INSERT INTO raw.open_meteo_hourly (
        location_id, "timestamp", latitude, longitude, elevation, timezone,
        temperature_2m, relative_humidity_2m, precipitation,
        wind_speed_10m, wind_direction_10m, surface_pressure,
        cloud_cover, visibility, weather_code, _extracted_at
    ) VALUES (
        %(location_id)s, %(timestamp)s, %(latitude)s, %(longitude)s,
        %(elevation)s, %(timezone)s, %(temperature_2m)s,
        %(relative_humidity_2m)s, %(precipitation)s, %(wind_speed_10m)s,
        %(wind_direction_10m)s, %(surface_pressure)s, %(cloud_cover)s,
        %(visibility)s, %(weather_code)s, %(_extracted_at)s
    )
    ON CONFLICT (location_id, "timestamp") DO UPDATE SET
        temperature_2m       = EXCLUDED.temperature_2m,
        relative_humidity_2m = EXCLUDED.relative_humidity_2m,
        precipitation        = EXCLUDED.precipitation,
        wind_speed_10m       = EXCLUDED.wind_speed_10m,
        wind_direction_10m   = EXCLUDED.wind_direction_10m,
        surface_pressure     = EXCLUDED.surface_pressure,
        cloud_cover          = EXCLUDED.cloud_cover,
        visibility           = EXCLUDED.visibility,
        weather_code         = EXCLUDED.weather_code,
        _extracted_at        = EXCLUDED._extracted_at
"""

UPSERT_DAILY = """
    INSERT INTO raw.open_meteo_daily (
        location_id, date, latitude, longitude,
        temperature_2m_max, temperature_2m_min, precipitation_sum,
        rain_sum, wind_speed_10m_max, sunrise, sunset, uv_index_max,
        _extracted_at
    ) VALUES (
        %(location_id)s, %(date)s, %(latitude)s, %(longitude)s,
        %(temperature_2m_max)s, %(temperature_2m_min)s, %(precipitation_sum)s,
        %(rain_sum)s, %(wind_speed_10m_max)s, %(sunrise)s, %(sunset)s,
        %(uv_index_max)s, %(_extracted_at)s
    )
    ON CONFLICT (location_id, date) DO UPDATE SET
        temperature_2m_max = EXCLUDED.temperature_2m_max,
        temperature_2m_min = EXCLUDED.temperature_2m_min,
        precipitation_sum  = EXCLUDED.precipitation_sum,
        rain_sum           = EXCLUDED.rain_sum,
        wind_speed_10m_max = EXCLUDED.wind_speed_10m_max,
        sunrise            = EXCLUDED.sunrise,
        sunset             = EXCLUDED.sunset,
        uv_index_max       = EXCLUDED.uv_index_max,
        _extracted_at      = EXCLUDED._extracted_at
"""


def upsert_batch(conn, sql: str, records: list):
    if not records:
        return 0
    with conn.cursor() as cur:
        psycopg2.extras.execute_batch(cur, sql, records, page_size=500)
    conn.commit()
    return len(records)


# ── Coleta principal ──────────────────────────────────────────────────────────

def collect(start_date: str, end_date: str):
    log.info(f"Iniciando coleta: {start_date} → {end_date} ({len(LOCATIONS)} locais)")
    conn = get_connection()
    total_hourly = total_daily = 0

    for loc in LOCATIONS:
        try:
            raw = fetch_forecast(loc, start_date, end_date)

            hourly_records = list(iter_hourly_records(raw, loc["id"]))
            daily_records  = list(iter_daily_records(raw, loc["id"]))

            total_hourly += upsert_batch(conn, UPSERT_HOURLY, hourly_records)
            total_daily  += upsert_batch(conn, UPSERT_DAILY,  daily_records)

            log.info(f"  ✓ {loc['id']:20s} — {len(hourly_records)}h / {len(daily_records)}d registros")

        except requests.HTTPError as e:
            log.error(f"  ✗ {loc['id']} — HTTP {e.response.status_code}: {e}")
        except Exception as e:
            log.error(f"  ✗ {loc['id']} — {e}")

    conn.close()
    log.info(f"Coleta concluída: {total_hourly} horárias, {total_daily} diárias")


def collect_recent():
    """Coleta os últimos 2 dias (chamada do scheduler)."""
    end   = date.today().isoformat()
    start = (date.today() - timedelta(days=2)).isoformat()
    collect(start, end)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Coletor Open-Meteo → PostgreSQL")
    parser.add_argument(
        "--mode",
        choices=["once", "scheduled", "backfill"],
        default="once",
        help="once = roda e sai | scheduled = loop | backfill = período customizado",
    )
    parser.add_argument("--start", default=None, help="Data inicial (backfill): YYYY-MM-DD")
    parser.add_argument("--end",   default=None, help="Data final (backfill):   YYYY-MM-DD")
    args = parser.parse_args()

    if args.mode == "once":
        end   = date.today().isoformat()
        start = (date.today() - timedelta(days=7)).isoformat()
        collect(start, end)

    elif args.mode == "backfill":
        if not args.start or not args.end:
            parser.error("--start e --end são obrigatórios no modo backfill")
        collect(args.start, args.end)

    elif args.mode == "scheduled":
        log.info("Modo scheduled: coleta a cada 6h (00:00, 06:00, 12:00, 18:00 BRT)")
        collect_recent()  # roda imediatamente na inicialização
        schedule.every().day.at("00:30").do(collect_recent)
        schedule.every().day.at("06:30").do(collect_recent)
        schedule.every().day.at("12:30").do(collect_recent)
        schedule.every().day.at("18:30").do(collect_recent)
        while True:
            schedule.run_pending()
            time.sleep(60)


if __name__ == "__main__":
    main()
