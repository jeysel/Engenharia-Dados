# PostgreSQL — Staging Server

Container Ubuntu 24.04 + PostgreSQL 17 com duas responsabilidades:

1. **Staging area** — o app `collector/` busca a API Open-Meteo e grava em `raw.*`
2. **Source do Airbyte** — o Airbyte lê `raw.*` e envia ao BigQuery (conector nativo PostgreSQL → BigQuery)

## Estrutura

```
postgresql/
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── config/
│   ├── postgresql.conf.append
│   └── pg_hba.conf.append
├── init/
│   ├── 01_schemas.sql
│   └── 02_raw_tables.sql
└── collector/
    ├── collector.py
    └── README.md
```

---

## Setup passo a passo

### Passo 1 — Variáveis de ambiente

```bash
cp .env.example .env
# Edite .env: POSTGRES_PASSWORD e GCP_PROJECT_ID
```

### Passo 2 — Build e subir o container

```bash
docker compose build
docker compose up -d postgres
```

### Passo 3 — Inicializar o cluster PostgreSQL

```bash
docker exec -it -u postgres weather_postgres \
  /usr/lib/postgresql/17/bin/initdb \
  --pgdata=/var/lib/postgresql/17/main \
  --auth-local=md5 \
  --auth-host=md5 \
  --encoding=UTF8 \
  --locale=pt_BR.UTF-8
```

### Passo 4 — Aplicar configurações de rede e performance

```bash
# postgresql.conf
docker exec weather_postgres bash -c \
  "cat /opt/config/postgresql.conf.append >> /var/lib/postgresql/17/main/postgresql.conf"

# pg_hba.conf
docker exec weather_postgres bash -c \
  "cat /opt/config/pg_hba.conf.append >> /var/lib/postgresql/17/main/pg_hba.conf"
```

### Passo 5 — Reiniciar para aplicar configurações

```bash
docker compose restart postgres
docker exec weather_postgres pg_isready -U postgres
```

### Passo 6 — Criar banco de dados

```bash
docker exec -it -u postgres weather_postgres \
  /usr/lib/postgresql/17/bin/psql -c \
  "CREATE DATABASE weather_staging ENCODING 'UTF8' LC_COLLATE 'pt_BR.UTF-8' LC_CTYPE 'pt_BR.UTF-8' TEMPLATE template0;"

docker exec -it -u postgres weather_postgres \
  /usr/lib/postgresql/17/bin/psql -c \
  "ALTER USER postgres PASSWORD 'SUA_SENHA_AQUI';"
```

### Passo 7 — Executar scripts SQL

```bash
docker exec -it -u postgres weather_postgres \
  /usr/lib/postgresql/17/bin/psql -d weather_staging -f /opt/init/01_schemas.sql

docker exec -it -u postgres weather_postgres \
  /usr/lib/postgresql/17/bin/psql -d weather_staging -f /opt/init/02_raw_tables.sql
```

### Passo 8 — Trocar senhas dos usuários de aplicação

> Estes usuários são criados pelo 01_schemas.sql com senhas placeholder.

```bash
docker exec -it -u postgres weather_postgres \
  /usr/lib/postgresql/17/bin/psql -d weather_staging -c \
  "ALTER USER airbyte_user PASSWORD 'SUA_SENHA_AIRBYTE';"

docker exec -it -u postgres weather_postgres \
  /usr/lib/postgresql/17/bin/psql -d weather_staging -c \
  "ALTER USER dbt_user PASSWORD 'SUA_SENHA_DBT';"
```

### Passo 9 — Verificar schemas

```bash
docker exec -it weather_postgres \
  psql -U weather_user -d weather_staging -c "\dn"
```

Saída esperada: `raw`, `staging`, `intermediate`, `marts`, `seeds`.

### Passo 10 — Primeira coleta

```bash
docker exec weather_postgres \
  python3 /opt/collector/collector.py --mode once

# Verificar dados
docker exec weather_postgres \
  psql -U weather_user -d weather_staging -c \
  "SELECT location_id, COUNT(*) FROM raw.open_meteo_daily GROUP BY 1 ORDER BY 1;"
```

### Passo 11 — Coletor agendado

```bash
docker compose --profile collector up -d collector
docker logs -f weather_collector
```

Roda automaticamente às 00:30, 06:30, 12:30 e 18:30 (horário de Brasília).

---

## Strings de conexão (para o Airbyte)

| Campo    | Valor                                                        |
|----------|--------------------------------------------------------------|
| Host     | `localhost` ou `host.docker.internal` se Airbyte for Docker  |
| Port     | `5432`                                                       |
| Database | `weather_staging`                                            |
| Username | `airbyte_user`                                               |
| Password | senha definida no passo 8                                    |
| Schema   | `raw`                                                        |

---

## Comandos úteis

```bash
# Acessar o psql
docker exec -it weather_postgres psql -U weather_user -d weather_staging

# Ver logs do PostgreSQL
docker exec weather_postgres tail -f /var/log/postgresql/postgresql-$(date +%Y-%m-%d).log

# Parar tudo
docker compose --profile collector down

# Remover volumes — APAGA TODOS OS DADOS
docker compose down -v
```
