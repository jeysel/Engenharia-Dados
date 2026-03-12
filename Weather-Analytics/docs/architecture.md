# Arquitetura — Weather Analytics Pipeline

## Fluxo de dados

```
 ┌──────────────────────┐
 │   Open-Meteo API     │  REST JSON, gratuita, sem autenticação
 └──────────┬───────────┘
            │  HTTP GET 4x/dia (00:30, 06:30, 12:30, 18:30 BRT)
            ▼
 ┌──────────────────────────────────────────────────────┐
 │   container: weather_postgres (Ubuntu 24.04 + PG 17) │
 │                                                      │
 │   collector.py        UPSERT                         │
 │   (Python + schedule) ──────► raw.open_meteo_hourly  │
 │                               raw.open_meteo_daily   │
 └──────────────────────────────┬───────────────────────┘
                                │
                                │  Airbyte (conector nativo PostgreSQL)
                                │  Source: raw.* | Incremental + _extracted_at
                                │  Schedule: 6h / 24h
                                ▼
                 ┌──────────────────────────────┐
                 │   BigQuery — dataset          │
                 │   weather_raw                 │
                 │                               │
                 │   open_meteo_hourly           │
                 │   open_meteo_daily            │
                 └──────────────┬────────────────┘
                                │
                                │  dbt (target: prod)
                                │  Sources: weather_raw.*
                                ▼
                 ┌──────────────────────────────┐
                 │   BigQuery — dataset          │
                 │   weather_dw                  │
                 │                               │
                 │   staging.*  (views)          │
                 │   marts.*    (tables parti.)  │
                 └──────────────────────────────┘
```

## Dois targets do dbt

| Target | Source | Destination | Quando usar |
|--------|--------|-------------|-------------|
| `dev` | `weather_staging.raw` (PostgreSQL) | `weather_staging.dbt_dev` (PostgreSQL) | Desenvolvimento local |
| `prod` | `weather_raw` (BigQuery) | `weather_dw` (BigQuery) | Produção |

A variável `DBT_SOURCE_DATABASE` controla qual banco o dbt usa como source:
- dev: `weather_staging` (PostgreSQL)
- prod: `weather_raw` (BigQuery, populado pelo Airbyte)

## Responsabilidades por pasta

| Pasta | Responsabilidade |
|-------|-----------------|
| `postgresql/` | Container PG17 + app coletor + setup manual documentado |
| `airbyte/` | Guia de configuração Source (PostgreSQL) → Destination (BigQuery) |
| `dbt/` | Transformações staging → marts, testes, documentação |

## Estrutura de arquivos

```
weather_pipeline/
├── README.md
├── docs/
│   └── architecture.md
│
├── postgresql/
│   ├── Dockerfile                   # Ubuntu 24.04 + PG17 + Python
│   ├── docker-compose.yml           # services: postgres + collector
│   ├── .env.example
│   ├── README.md                    # 11 passos de setup manual
│   ├── config/
│   │   ├── postgresql.conf.append
│   │   └── pg_hba.conf.append
│   ├── init/
│   │   ├── 01_schemas.sql           # schemas, roles, permissões
│   │   └── 02_raw_tables.sql        # tabelas raw pré-criadas
│   └── collector/
│       ├── collector.py             # busca API → upsert raw.*
│       └── README.md
│
├── airbyte/
│   └── README.md                    # Source: PostgreSQL → Destination: BigQuery
│
└── dbt/
    ├── Dockerfile
    ├── docker-compose.yml           # services por comando dbt
    ├── dbt_project.yml
    ├── packages.yml
    ├── profiles.yml.example
    ├── models/
    │   ├── staging/
    │   │   ├── sources.yml          # source parametrizado dev/prod
    │   │   ├── schema.yml
    │   │   ├── stg_weather__hourly.sql
    │   │   └── stg_weather__daily.sql
    │   └── marts/
    │       ├── schema.yml
    │       ├── mart_climate__daily_facts.sql
    │       └── mart_climate__alerts.sql
    ├── tests/                       # 5 testes personalizados
    ├── macros/
    └── seeds/
        └── locations.csv
```
