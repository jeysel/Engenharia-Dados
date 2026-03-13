# ─────────────────────────────────────────────────────────────────────────────
# Weather Pipeline — PostgreSQL Staging Server
#
# Base: Ubuntu 24.04 LTS (Noble Numbat)
# PostgreSQL: 17 (repositório oficial postgresql.org)
#
# Responsabilidades deste container:
#   1. Banco de staging: app coletor (collector/) busca a API e grava em raw.*
#   2. Source do Airbyte: Airbyte lê raw.* e envia ao BigQuery
#
# O cluster PostgreSQL é inicializado manualmente após o primeiro build.
# Ver README.md — seção "Setup passo a passo".
# ─────────────────────────────────────────────────────────────────────────────

FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive
ARG PG_VERSION=17

# ── Sistema base ──────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    locales \
    tzdata \
    gosu \
    cron \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Locale e timezone Brasil
RUN locale-gen pt_BR.UTF-8
ENV LANG=pt_BR.UTF-8 \
    LANGUAGE=pt_BR:pt \
    LC_ALL=pt_BR.UTF-8 \
    TZ=America/Sao_Paulo

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# ── Repositório oficial PostgreSQL ────────────────────────────────────────────
RUN curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
    | gpg --dearmor -o /usr/share/keyrings/postgresql.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/postgresql.gpg] \
    https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" \
    > /etc/apt/sources.list.d/pgdg.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
    postgresql-${PG_VERSION} \
    postgresql-client-${PG_VERSION} \
    postgresql-contrib-${PG_VERSION} \
 && rm -rf /var/lib/apt/lists/*

# ── Python 3 + dependências do coletor ───────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Dependências do app coletor Open-Meteo → PostgreSQL
RUN pip install --no-cache-dir \
    requests==2.* \
    psycopg2-binary==2.* \
    schedule==1.*

# ── Variáveis de ambiente (defaults — sobrescreva via .env) ──────────────────
ENV PG_VERSION=${PG_VERSION} \
    PGDATA=/var/lib/postgresql/${PG_VERSION}/main \
    POSTGRES_DB=weather_staging \
    POSTGRES_USER=weather_user \
    POSTGRES_PASSWORD=weather_pass \
    POSTGRES_PORT=5432

# ── Copia o app coletor, scripts SQL e entrypoint ────────────────────────────
COPY collector/    /opt/collector/
COPY init/         /opt/init/
COPY config/       /opt/config/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5432

VOLUME ["/var/lib/postgresql/17/main", "/var/log/postgresql"]

ENTRYPOINT ["/entrypoint.sh"]
