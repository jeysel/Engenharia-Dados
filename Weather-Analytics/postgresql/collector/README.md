# collector/ — App de Coleta Open-Meteo

Script Python que roda dentro do container PostgreSQL e é responsável por
buscar os dados da API Open-Meteo e gravá-los diretamente nas tabelas
`raw.open_meteo_hourly` e `raw.open_meteo_daily`.

## Por que no container PostgreSQL?

O Airbyte usa **PostgreSQL como Source** (conector nativo, sem customização).
O app coletor resolve o problema de autenticação, paginação e flatten do JSON
da API, entregando dados já estruturados em tabelas SQL para o Airbyte consumir.

```
Open-Meteo API
      │  HTTP GET
      ▼
collector.py  (roda no container weather_postgres)
      │  INSERT / UPSERT
      ▼
raw.open_meteo_hourly
raw.open_meteo_daily
      │  CDC / full refresh
      ▼
Airbyte (Source: PostgreSQL → Destination: BigQuery)
```

## Uso

```bash
# Executa uma vez (últimos 7 dias)
docker exec weather_postgres python3 /opt/collector/collector.py --mode once

# Backfill histórico
docker exec weather_postgres python3 /opt/collector/collector.py \
  --mode backfill --start 2024-01-01 --end 2024-12-31

# Loop agendado (00:30, 06:30, 12:30, 18:30 BRT)
docker compose --profile collector up -d collector
docker logs -f weather_collector
```

## Localizações monitoradas

Configuradas diretamente no código — lista `LOCATIONS` em `collector.py`.
31 localizações no total:
- 13 capitais e grandes centros brasileiros
- 18 municípios de Santa Catarina, organizados em 5 regiões:
  - Grande Florianópolis: Florianópolis, Palhoça, Santo Amaro da Imperatriz, Angelina
  - Litoral Sul: Garopaba, Imbituba, Laguna, Tubarão, Criciúma, Araranguá
  - Serra / Planalto: Lages, Campos Novos, Joaçaba
  - Litoral Norte / Vale do Itajaí: Balneário Camboriú, Itajaí, Joinville
  - Oeste: Chapecó, São Miguel do Oeste
