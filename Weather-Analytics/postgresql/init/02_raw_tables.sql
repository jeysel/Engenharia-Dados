-- ─────────────────────────────────────────────────────────────────────────────
-- 02_raw_tables.sql
-- Tabelas do schema raw que o Airbyte vai popular.
-- Criadas antecipadamente para garantir tipos corretos e índices.
-- ─────────────────────────────────────────────────────────────────────────────

-- ── raw.open_meteo_hourly ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS raw.open_meteo_hourly (
    -- Chaves
    id                      BIGSERIAL       PRIMARY KEY,
    location_id             TEXT            NOT NULL,
    "timestamp"             TIMESTAMPTZ     NOT NULL,

    -- Geo
    latitude                NUMERIC(9,6),
    longitude               NUMERIC(9,6),
    elevation               NUMERIC(7,2),
    timezone                TEXT,

    -- Variáveis climáticas horárias
    temperature_2m          NUMERIC(5,2),       -- °C
    relative_humidity_2m    INTEGER,            -- %
    precipitation           NUMERIC(6,2),       -- mm
    wind_speed_10m          NUMERIC(5,2),       -- km/h
    wind_direction_10m      INTEGER,            -- graus
    surface_pressure        NUMERIC(7,2),       -- hPa
    cloud_cover             INTEGER,            -- %
    visibility              NUMERIC(8,2),       -- metros
    weather_code            INTEGER,            -- WMO code

    -- Controle de pipeline
    _extracted_at           TIMESTAMP       NOT NULL DEFAULT now(),
    _airbyte_raw_id         TEXT,
    _airbyte_extracted_at   TIMESTAMPTZ,

    CONSTRAINT uq_hourly UNIQUE (location_id, "timestamp")
);

CREATE INDEX IF NOT EXISTS idx_hourly_location_ts
    ON raw.open_meteo_hourly (location_id, "timestamp" DESC);

CREATE INDEX IF NOT EXISTS idx_hourly_extracted
    ON raw.open_meteo_hourly (_extracted_at DESC);

COMMENT ON TABLE raw.open_meteo_hourly
    IS 'Medições horárias da Open-Meteo API. Populado pelo Airbyte.';

-- ── raw.open_meteo_daily ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS raw.open_meteo_daily (
    id                      BIGSERIAL       PRIMARY KEY,
    location_id             TEXT            NOT NULL,
    date                    DATE            NOT NULL,

    -- Geo
    latitude                NUMERIC(9,6),
    longitude               NUMERIC(9,6),

    -- Variáveis climáticas diárias
    temperature_2m_max      NUMERIC(5,2),       -- °C
    temperature_2m_min      NUMERIC(5,2),       -- °C
    precipitation_sum       NUMERIC(7,2),       -- mm
    rain_sum                NUMERIC(7,2),       -- mm
    wind_speed_10m_max      NUMERIC(5,2),       -- km/h
    sunrise                 TIMESTAMPTZ,
    sunset                  TIMESTAMPTZ,
    uv_index_max            NUMERIC(4,2),

    -- Controle
    _extracted_at           TIMESTAMP       NOT NULL DEFAULT now(),
    _airbyte_raw_id         TEXT,
    _airbyte_extracted_at   TIMESTAMPTZ,

    CONSTRAINT uq_daily UNIQUE (location_id, date)
);

CREATE INDEX IF NOT EXISTS idx_daily_location_date
    ON raw.open_meteo_daily (location_id, date DESC);

CREATE INDEX IF NOT EXISTS idx_daily_extracted
    ON raw.open_meteo_daily (_extracted_at DESC);

COMMENT ON TABLE raw.open_meteo_daily
    IS 'Resumo diário da Open-Meteo API. Populado pelo Airbyte.';
