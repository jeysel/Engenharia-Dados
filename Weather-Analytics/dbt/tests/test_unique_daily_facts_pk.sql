-- tests/test_unique_daily_facts_pk.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Verifica a unicidade da chave primária composta (location_id + date)
-- na tabela fato principal. Duplicatas indicam erro de ingestão ou
-- lógica incorreta no modelo dbt.
-- ─────────────────────────────────────────────────────────────────────────────

SELECT
    location_id,
    date,
    COUNT(*) AS occurrences
FROM {{ ref('mart_climate__daily_facts') }}
GROUP BY location_id, date
HAVING COUNT(*) > 1
ORDER BY occurrences DESC
