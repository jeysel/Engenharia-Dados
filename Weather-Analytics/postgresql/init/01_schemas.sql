-- ─────────────────────────────────────────────────────────────────────────────
-- 01_schemas.sql
-- Cria schemas, roles e permissões do projeto weather_pipeline.
-- Executado automaticamente na primeira inicialização do container.
-- ─────────────────────────────────────────────────────────────────────────────

-- ── Roles ─────────────────────────────────────────────────────────────────────

-- Role somente-leitura (BI tools, dashboards)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'weather_readonly') THEN
        CREATE ROLE weather_readonly NOLOGIN;
    END IF;
END $$;

-- Role de escrita — usada pelo Airbyte
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'weather_writer') THEN
        CREATE ROLE weather_writer NOLOGIN;
    END IF;
END $$;

-- Role do dbt — leitura total + escrita nos schemas de saída
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'weather_dbt') THEN
        CREATE ROLE weather_dbt NOLOGIN;
    END IF;
END $$;

-- ── Schemas ───────────────────────────────────────────────────────────────────

-- raw: dados brutos do Airbyte, sem modificação
CREATE SCHEMA IF NOT EXISTS raw;

-- staging: views limpas geradas pelo dbt
CREATE SCHEMA IF NOT EXISTS staging;

-- intermediate: modelos efêmeros do dbt (ephemeral — pode não criar tabelas)
CREATE SCHEMA IF NOT EXISTS intermediate;

-- marts: tabelas analíticas finais antes do envio ao BigQuery
CREATE SCHEMA IF NOT EXISTS marts;

-- seeds: tabelas de referência carregadas pelo dbt seed
CREATE SCHEMA IF NOT EXISTS seeds;

-- dbt_test_failures: armazena registros que falharam nos testes dbt
CREATE SCHEMA IF NOT EXISTS dbt_test_failures;

-- ── Permissões por schema ─────────────────────────────────────────────────────

-- raw: collector/Airbyte escrevem, dbt lê
GRANT USAGE ON SCHEMA raw TO weather_writer, weather_dbt;
GRANT CREATE ON SCHEMA raw TO weather_writer;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA raw TO weather_writer;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA raw TO weather_writer;
GRANT SELECT ON ALL TABLES IN SCHEMA raw TO weather_dbt;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw
    GRANT SELECT, INSERT, UPDATE ON TABLES TO weather_writer;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw
    GRANT USAGE ON SEQUENCES TO weather_writer;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw
    GRANT SELECT ON TABLES TO weather_dbt;

-- staging, intermediate, marts, seeds, dbt_test_failures: dbt é dono
GRANT USAGE, CREATE ON SCHEMA staging          TO weather_dbt;
GRANT USAGE, CREATE ON SCHEMA intermediate     TO weather_dbt;
GRANT USAGE, CREATE ON SCHEMA marts           TO weather_dbt;
GRANT USAGE, CREATE ON SCHEMA seeds           TO weather_dbt;
GRANT USAGE, CREATE ON SCHEMA dbt_test_failures TO weather_dbt;

-- readonly acessa staging e marts
GRANT USAGE ON SCHEMA staging TO weather_readonly;
GRANT USAGE ON SCHEMA marts   TO weather_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA staging TO weather_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA marts   TO weather_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA staging
    GRANT SELECT ON TABLES TO weather_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA marts
    GRANT SELECT ON TABLES TO weather_readonly;

-- ── Usuários de aplicação ─────────────────────────────────────────────────────

-- Usuário principal da aplicação (collector) — criado pelo entrypoint.sh
-- Recebe weather_writer para gravar em raw.*
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'weather_user') THEN
        GRANT weather_writer TO weather_user;
    END IF;
END $$;

-- Usuário do Airbyte
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'airbyte_user') THEN
        CREATE USER airbyte_user PASSWORD 'airbyte_pass_troque';
    END IF;
END $$;
GRANT weather_writer TO airbyte_user;
GRANT CONNECT ON DATABASE weather_staging TO airbyte_user;

-- Usuário do dbt
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'dbt_user') THEN
        CREATE USER dbt_user PASSWORD 'dbt_pass_troque';
    END IF;
END $$;
GRANT weather_dbt TO dbt_user;
GRANT CONNECT ON DATABASE weather_staging TO dbt_user;

-- ── Extensões úteis ───────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;  -- análise de queries
CREATE EXTENSION IF NOT EXISTS btree_gin;            -- índices em JSON

-- ── Comentários de documentação ───────────────────────────────────────────────
COMMENT ON SCHEMA raw          IS 'Dados brutos ingeridos pelo Airbyte. Não modificar manualmente.';
COMMENT ON SCHEMA staging      IS 'Views dbt com limpeza e tipagem dos dados raw.';
COMMENT ON SCHEMA intermediate IS 'Modelos intermediários dbt (joins, agregações).';
COMMENT ON SCHEMA marts        IS 'Tabelas analíticas finais. Fonte para o BigQuery.';
COMMENT ON SCHEMA seeds        IS 'Dados de referência carregados via dbt seed.';
