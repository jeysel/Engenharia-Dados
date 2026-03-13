#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# entrypoint.sh — Inicializa o cluster PostgreSQL na primeira execução
# e inicia o servidor nas execuções seguintes.
# ─────────────────────────────────────────────────────────────────────────────
set -e

PG_VERSION="${PG_VERSION:-17}"
PGDATA="/var/lib/postgresql/${PG_VERSION}/main"
PG_BIN="/usr/lib/postgresql/${PG_VERSION}/bin"
PG_LOG="/var/log/postgresql"

# Marcador gravado apenas após setup 100% concluído.
# Usar PG_VERSION como marcador é inseguro — initdb o cria antes de terminar.
MARKER="$PGDATA/.cluster_ready"

DB="${POSTGRES_DB:-weather_staging}"
USER="${POSTGRES_USER:-weather_user}"
PASS="${POSTGRES_PASSWORD:-weather_pass}"

# Garante diretórios com permissão correta
mkdir -p "$PGDATA" "$PG_LOG"
chown -R postgres:postgres "$PGDATA" "$PG_LOG"
chmod 700 "$PGDATA"

# ── Setup: roda somente se o marcador não existir ──────────────────────────
if [ ! -f "$MARKER" ]; then

    # Cluster parcial (initdb abortou antes)? Limpa para recomeçar.
    if [ -f "$PGDATA/PG_VERSION" ]; then
        echo "[entrypoint] Cluster incompleto detectado — limpando para reinicializar..."
        rm -rf "${PGDATA:?}"/*
    fi

    echo "[entrypoint] Inicializando cluster PostgreSQL ${PG_VERSION}..."
    gosu postgres "$PG_BIN/initdb" \
        -D "$PGDATA" \
        --encoding=UTF8 \
        --locale=pt_BR.UTF-8 \
        -U postgres

    # Aplica configurações customizadas
    echo "[entrypoint] Aplicando configurações..."
    cat /opt/config/postgresql.conf.append >> "$PGDATA/postgresql.conf"
    cat /opt/config/pg_hba.conf.append    >> "$PGDATA/pg_hba.conf"

    # Inicia PostgreSQL temporariamente (apenas socket local)
    echo "[entrypoint] Iniciando PostgreSQL temporário para setup..."
    gosu postgres "$PG_BIN/pg_ctl" start \
        -D "$PGDATA" \
        -l "$PG_LOG/setup.log" \
        -o "-c listen_addresses=''" \
        -w -t 60

    # Cria usuário e banco
    echo "[entrypoint] Criando usuário '$USER' e banco '$DB'..."
    gosu postgres "$PG_BIN/psql" -U postgres <<SQL
CREATE USER "$USER" WITH PASSWORD '$PASS';
CREATE DATABASE "$DB"
    OWNER "$USER"
    ENCODING 'UTF8'
    LC_COLLATE 'pt_BR.UTF-8'
    LC_CTYPE   'pt_BR.UTF-8'
    TEMPLATE template0;
GRANT ALL PRIVILEGES ON DATABASE "$DB" TO "$USER";
SQL

    # Executa scripts de inicialização em ordem
    echo "[entrypoint] Executando scripts SQL de inicialização..."
    for f in $(ls /opt/init/*.sql 2>/dev/null | sort); do
        echo "[entrypoint]   → $f"
        gosu postgres "$PG_BIN/psql" -U postgres -d "$DB" -f "$f"
    done

    # Para o PostgreSQL temporário
    echo "[entrypoint] Parando PostgreSQL temporário..."
    gosu postgres "$PG_BIN/pg_ctl" stop -D "$PGDATA" -m fast -w

    # Grava marcador de conclusão — só chegamos aqui se tudo funcionou
    touch "$MARKER"
    chown postgres:postgres "$MARKER"
    echo "[entrypoint] Setup inicial concluído com sucesso."
fi

# ── Inicia PostgreSQL normalmente ─────────────────────────────────────────
echo "[entrypoint] Iniciando PostgreSQL ${PG_VERSION}..."
exec gosu postgres "$PG_BIN/postgres" -D "$PGDATA"
