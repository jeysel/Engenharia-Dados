# ─────────────────────────────────────────────────────────────────────────────
# Weather Pipeline — dbt Runner
#
# Imagem leve com dbt-postgres + dbt-bigquery instalados.
# O projeto dbt é montado via volume — não copiado para a imagem,
# facilitando o desenvolvimento sem rebuild.
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim

ARG DBT_VERSION=1.8.*

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ── Instala dbt e adaptadores ─────────────────────────────────────────────────
RUN pip install --no-cache-dir \
    "dbt-core==${DBT_VERSION}" \
    "dbt-postgres==${DBT_VERSION}" \
    "dbt-bigquery==${DBT_VERSION}" \
    "dbt-utils>=1.0.0" \
    "elementary-data>=0.12"     # observabilidade opcional

# ── Diretório de trabalho ─────────────────────────────────────────────────────
WORKDIR /dbt

# profiles.yml é montado em /root/.dbt via volume
ENV DBT_PROFILES_DIR=/root/.dbt

# ── Healthcheck básico ────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD dbt --version || exit 1

# Entrypoint padrão — sobrescreva no docker-compose com o comando desejado
ENTRYPOINT ["dbt"]
CMD ["--help"]
