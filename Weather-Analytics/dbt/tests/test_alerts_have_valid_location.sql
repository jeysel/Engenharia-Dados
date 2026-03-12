-- tests/test_alerts_have_valid_location.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Garante que todo alerta em mart_climate__alerts tem uma localização
-- correspondente no seed de localizações. Alerta sem cidade = dado inconsistente.
-- ─────────────────────────────────────────────────────────────────────────────

SELECT
    a.location_id,
    a.date,
    a.alert_type
FROM {{ ref('mart_climate__alerts') }} a
LEFT JOIN {{ ref('locations') }} l
    ON a.location_id = l.location_id
WHERE l.location_id IS NULL
