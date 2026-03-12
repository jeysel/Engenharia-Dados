-- tests/test_temp_min_less_than_max.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Garante que a temperatura mínima nunca é maior que a máxima.
-- Uma violação indica dado corrompido ou erro no ETL.
-- Retorna linhas que falham no teste (0 linhas = teste passou).
-- ─────────────────────────────────────────────────────────────────────────────

SELECT
    location_id,
    date,
    temp_min_c,
    temp_max_c
FROM {{ ref('mart_climate__daily_facts') }}
WHERE temp_min_c > temp_max_c
