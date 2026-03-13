# dbt — Transformações e Data Warehouse

Projeto dbt para transformação dos dados coletados da Open-Meteo API.
Conecta no PostgreSQL (dev) e no BigQuery (prod) via profiles configurados localmente.

> **Os containers dbt fazem parte do agrupador `weather-analytics`.**
> Todos os comandos são executados a partir da pasta `postgresql/`.

## Estrutura

```
dbt/
├── dbt_project.yml             # Configuração central + variáveis + testes
├── packages.yml                # dbt_utils, dbt_expectations, audit_helper
├── profiles.yml.example        # Template para ~/.dbt/profiles.yml
├── models/
│   ├── staging/
│   │   ├── sources.yml         # Fontes + freshness + testes de source
│   │   ├── schema.yml          # Documentação e testes dos modelos staging
│   │   ├── stg_weather__hourly.sql
│   │   └── stg_weather__daily.sql
│   ├── intermediate/           # (para joins futuros)
│   └── marts/
│       ├── schema.yml          # Documentação e testes dos marts
│       ├── mart_climate__daily_facts.sql
│       └── mart_climate__alerts.sql
├── tests/                      # Testes personalizados (singular tests)
│   ├── test_temp_min_less_than_max.sql
│   ├── test_no_date_gaps_per_location.sql
│   ├── test_unique_daily_facts_pk.sql
│   ├── test_alerts_have_valid_location.sql
│   └── test_raw_data_freshness.sql
├── macros/
│   └── weather_utils.sql       # wmo_code_to_label, beaufort, celsius_to_f
└── seeds/
    └── locations.csv           # cidades brasileiras monitoradas
```

## Setup inicial

```powershell
# 1. Configure o profiles.yml (Windows PowerShell)
New-Item -ItemType Directory -Force "$env:USERPROFILE\.dbt"
Copy-Item "C:\Dev\Engenharia-Dados\Weather-Analytics\dbt\profiles.yml.example" `
          "$env:USERPROFILE\.dbt\profiles.yml"
```

> O build e a subida dos containers e feita a partir da pasta `postgresql/`.
> Ver `postgresql/README.md`.

## Executando o pipeline

Todos os comandos abaixo devem ser executados dentro da pasta `postgresql/`:

```bash
cd C:\Dev\Engenharia-Dados\Weather-Analytics\postgresql

# Validar conexao com o banco
docker compose run --rm dbt-debug

# Carregar seeds (locations.csv)
docker compose run --rm dbt-seed

# Pipeline completo (run + test)
docker compose run --rm dbt-build

# So os modelos
docker compose run --rm dbt-run

# So os testes
docker compose run --rm dbt-test

# Camada por camada
docker compose run --rm dbt-run-staging
docker compose run --rm dbt-run-marts
```

## Documentacao (http://localhost:8080)

```bash
cd C:\Dev\Engenharia-Dados\Weather-Analytics\postgresql

# Gera a documentacao
docker compose run --rm dbt-docs-generate

# Serve a documentacao (mante rodando -- acesse http://localhost:8080)
docker compose run --rm --service-ports dbt-docs
```

## Executar em producao (BigQuery)

```bash
cd C:\Dev\Engenharia-Dados\Weather-Analytics\postgresql

DBT_TARGET=prod docker compose run --rm dbt-build
```

## Testes implementados

### Testes default (schema.yml)

| Modelo | Coluna | Teste |
|--------|--------|-------|
| staging/hourly | location_id | not_null, accepted_values |
| staging/hourly | temperature_c | accepted_range (-20..55) |
| staging/hourly | relative_humidity_pct | accepted_range (0..100) |
| marts/daily_facts | temp_max_c | not_null, accepted_range |
| marts/daily_facts | precipitation_class | accepted_values |
| marts/daily_facts | uv_risk_level | accepted_values |
| marts/alerts | alert_type | not_null, accepted_values |
| marts/alerts | severity | accepted_values |

### Testes personalizados (tests/)

| Arquivo | O que verifica |
|---------|---------------|
| `test_temp_min_less_than_max` | temp_min nunca maior que temp_max |
| `test_no_date_gaps_per_location` | sem dias faltando (ultimos 30 dias) |
| `test_unique_daily_facts_pk` | unicidade de location_id + date |
| `test_alerts_have_valid_location` | alertas com cidade existente no seed |
| `test_raw_data_freshness` | todos os locais com dados < 25h |

## Lineage

```
raw.open_meteo_hourly  --> stg_weather__hourly
                                   |
raw.open_meteo_daily   --> stg_weather__daily --> mart_climate__daily_facts
                                                          |
seeds.locations        -----------------------------------+
                                                          |
                                              mart_climate__alerts
```
