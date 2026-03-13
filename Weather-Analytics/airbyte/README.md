# Airbyte — Configuração PostgreSQL → BigQuery

O Airbyte já está instalado e rodando localmente.
Nesta arquitetura, o Airbyte usa dois conectores nativos — sem configuração customizada:

- **Source**: PostgreSQL (lê `raw.*` populado pelo `collector.py`)
- **Destination**: BigQuery (envia os dados ao Data Warehouse)

Acesse: **http://localhost:9000**

---

## Pré-requisito

O container PostgreSQL deve estar rodando e as tabelas `raw.open_meteo_hourly`
e `raw.open_meteo_daily` devem conter dados antes de configurar as connections.
Ver `postgresql/README.md` — passos 1 a 10.

---

## 1. Configurar o Source — PostgreSQL

### 1.1 Criar novo Source

Menu lateral → **Sources → New Source**
Busque e selecione: **PostgreSQL**

### 1.2 Preencher os campos

| Campo | Valor |
|-------|-------|
| Source name | `weather-postgres-raw` |
| Host | `host.docker.internal` (Airbyte roda em Docker via abctl) |
| Port | `5432` |
| Database | `weather_staging` |
| Username | `airbyte_user` |
| Password | senha definida em `postgresql/init/01_schemas.sql` — variável `airbyte_pass_troque` (altere antes de usar em produção) |
| Default Schema | `raw` |
| SSL mode | `disable` (rede local) |

### 1.3 Replication method

Selecione: **Xmin System Column**

> Esta é a forma mais simples de replicação incremental no PostgreSQL.
> Não requer configuração de WAL ou slots de replicação.
> O Airbyte usa a coluna interna `xmin` para identificar linhas novas/atualizadas.

Alternativa (se preferir): **Logical Replication (CDC)**
- Requer `wal_level = logical` no postgresql.conf
- Adicione `wal_level = logical` ao arquivo `config/postgresql.conf.append`
- Reinicie o container após adicionar

### 1.4 Testar e salvar

**Test connection** → **Set up source**

---

## 2. Configurar o Destination — BigQuery

### 2.1 Criar novo Destination

Menu lateral → **Destinations → New Destination**
Busque e selecione: **BigQuery**

### 2.2 Preencher os campos

| Campo | Valor |
|-------|-------|
| Destination name | `weather-bigquery` |
| Project ID | ID do seu projeto GCP |
| Dataset Location | `southamerica-east1` |
| Default Dataset ID | `weather_raw` |
| Credentials JSON | cole o conteúdo do arquivo `gcp-service-account.json` |

> O dataset `weather_raw` será criado automaticamente pelo Airbyte se não existir.
> Use um Service Account com as roles: **BigQuery Data Editor** + **BigQuery Job User**.

### 2.3 Loading method

Selecione: **Standard Inserts**

> Para volumes maiores (>1M linhas/dia), considere **Batch Loading via GCS**,
> que requer um bucket GCS adicional mas é significativamente mais eficiente.

### 2.4 Testar e salvar

**Test connection** → **Set up destination**

---

## 3. Criar a Connection hourly

**Menu**: Connections → New Connection

### 3.1 Source → Destination

Selecione: `weather-postgres-raw` → `weather-bigquery`

### 3.2 Configurar a connection

| Campo | Valor |
|-------|-------|
| Connection name | `postgres-raw-hourly-to-bigquery` |
| Schedule type | `Scheduled` |
| Schedule | `Every 6 hours` |
| Destination namespace | `Mirror source structure` |
| Destination stream prefix | *(deixar vazio)* |

### 3.3 Selecionar streams

Na lista de streams disponíveis, ative apenas:

- `open_meteo_hourly`
  - Sync mode: **Incremental \| Append**
  - Cursor field: `_extracted_at`

Desative todos os outros streams que aparecerem.

### 3.4 Salvar

**Set up connection**

---

## 4. Criar a Connection daily

Repita o processo da seção 3 com as diferenças:

| Campo | Valor |
|-------|-------|
| Connection name | `postgres-raw-daily-to-bigquery` |
| Schedule | `Every 24 hours` |

Stream a ativar:

- `open_meteo_daily`
  - Sync mode: **Incremental \| Append**
  - Cursor field: `_extracted_at`

---

## 5. Executar sync manual e verificar

Após salvar as connections, execute um sync manual em cada uma:

**Connection → Sync now**

Acompanhe em: **Jobs** → verifique status `Succeeded`.

Para confirmar no BigQuery, execute no console GCP:

```sql
SELECT location_id, COUNT(*) as registros, MAX(_extracted_at) as ultima_carga
FROM `seu-projeto.weather_raw.open_meteo_daily`
GROUP BY 1
ORDER BY 1;
```

---

## 6. Fluxo completo de dados

```
Open-Meteo API
      │  HTTP GET (4x por dia)
      ▼
collector.py  (container weather_postgres)
      │  UPSERT
      ▼
raw.open_meteo_hourly    raw.open_meteo_daily
(PostgreSQL — staging)   (PostgreSQL — staging)
      │                        │
      └────────┬───────────────┘
               │  Airbyte — conector nativo PostgreSQL
               │  Incremental | Append (cursor: _extracted_at)
               ▼
weather_raw.open_meteo_hourly    weather_raw.open_meteo_daily
(BigQuery — dataset weather_raw)
               │
               │  dbt (target: prod, lê do BigQuery)
               ▼
weather_dw.staging.*   →   weather_dw.marts.*
```

---

## 7. Permissões necessárias no PostgreSQL para o Airbyte

O usuário `airbyte_user` precisa de SELECT nas tabelas raw.
Já configurado em `init/01_schemas.sql`. Verifique com:

```bash
docker exec -it weather_postgres \
  psql -U airbyte_user -d weather_staging -c \
  "SELECT COUNT(*) FROM raw.open_meteo_daily;"
```

---

## 8. Alertas recomendados

Configure em **Connection → Settings → Alerts**:

| Alerta | Threshold |
|--------|-----------|
| Sync failed | Notificar imediatamente |
| No sync in | 25 horas |
| Rows synced < | 10 por run |
