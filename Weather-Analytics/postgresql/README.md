# PostgreSQL + dbt — Weather Pipeline

Container Ubuntu 24.04 + PostgreSQL 17. Centraliza todos os servicos do pipeline:

- **postgres** — banco de staging; o `collector/` busca a API Open-Meteo e grava em `raw.*`
- **collector** — coletor agendado (profile: `collector`)
- **dbt-*** — servicos de transformacao (run, test, seed, docs etc.)

O cluster PostgreSQL é inicializado automaticamente na primeira execucao
(`initdb` + criacao de usuario/banco + scripts SQL via `entrypoint.sh`).

## Estrutura

```
postgresql/
├── Dockerfile
├── entrypoint.sh               # Inicializa o cluster na 1a execucao
├── docker-compose.yml          # Todos os servicos: postgres + collector + dbt
├── .env.example
├── secrets/                    # Credenciais GCP (ignorado pelo git)
│   └── gcp-service-account.json
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

### Passo 1 — Variaveis de ambiente

```bash
cd C:\Dev\Engenharia-Dados\Weather-Analytics\postgresql
cp .env.example .env
```

Edite o `.env` com suas credenciais de PostgreSQL, dbt e GCP.

### Passo 2 — Credencial GCP

1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
2. IAM e Admin -> Service Accounts -> Create Service Account
3. Papel sugerido: Proprietario
4. Aba Chaves -> Add Key -> Create new key -> JSON -> salve como:
   `postgresql\secrets\gcp-service-account.json`
5. Informe o ID do projeto no `.env`: `GCP_PROJECT_ID=seu-projeto-gcp`

### Passo 3 — Configurar o dbt (profiles.yml)

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.dbt"
Copy-Item "C:\Dev\Engenharia-Dados\Weather-Analytics\dbt\profiles.yml.example" `
          "$env:USERPROFILE\.dbt\profiles.yml"
```

### Passo 4 — Build e subir os containers

```bash
cd C:\Dev\Engenharia-Dados\Weather-Analytics\postgresql

# Constroi as imagens (postgres + dbt)
docker compose build

# Sobe o banco (inicializa cluster automaticamente na 1a vez)
docker compose up -d postgres

# Sobe o coletor
docker compose --profile collector up -d collector

# Configuração e carga com o coletor
postgresql\collector\README.md
```

### Passo 5 — Executar o dbt

> Execute o coletor (`collector/README.md`) antes de continuar.
> A imagem dbt já foi construída no Passo 4 (`docker compose build`).

```bash
# 1. Instalar pacotes dbt (apenas na 1ª vez ou quando packages.yml mudar)
docker compose run --rm dbt-deps

# 2. Validar conexão
docker compose run --rm dbt-debug

# 3. Carregar seeds (locations.csv)
docker compose run --rm dbt-seed

# 4. Executar modelos
docker compose run --rm dbt-run

# 5. Validar dados - Testes de qualidade dos dados
docker compose run --rm dbt-test
```

---

## Documentacao dbt 

```bash
docker compose run --rm dbt-docs-generate
docker compose run --rm --service-ports dbt-docs
```
Acessar: http://localhost:8080
---

## Strings de conexao (para o Airbyte)

| Campo    | Valor                                                        |
|----------|--------------------------------------------------------------|
| Host     | `localhost` ou `host.docker.internal` se Airbyte for Docker  |
| Port     | `5432`                                                       |
| Database | `weather_staging`                                            |
| Username | `airbyte_user`                                               |
| Password | senha definida em `01_schemas.sql` (alterar apos setup)      |
| Schema   | `raw`                                                        |

---

## Configuração e funcionamento do DBT, Coletor e PostgresSQL concluidos

* Retornar para:\Weather-Analytics\README.md


## Comandos uteis

```bash
# Acessar o psql
docker exec -it weather_postgres psql -U weather_user -d weather_staging

# Ver logs do PostgreSQL
docker exec weather_postgres tail -f /var/log/postgresql/postgresql-$(date +%Y-%m-%d).log

# Parar tudo
docker compose --profile collector down

# Remover volumes -- APAGA TODOS OS DADOS
docker compose down -v
```
