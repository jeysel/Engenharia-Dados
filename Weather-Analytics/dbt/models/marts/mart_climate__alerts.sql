{{
  config(
    materialized = 'table',
    schema = 'marts',
  )
}}

/*
  mart_climate__alerts
  ────────────────────
  Detecta eventos climáticos extremos por localização.
  Útil para dashboards de monitoramento e notificações.
*/

with facts as (
    select * from {{ ref('mart_climate__daily_facts') }}
),

alerts as (
    select
        date,
        location_id,
        city_name,
        state_name,
        region,

        -- Tipo de alerta
        case
            when temp_max_c > 40                            then 'extreme_heat'
            when temp_min_c < 0                             then 'frost'
            when precipitation_mm > 80                      then 'heavy_rain'
            when wind_speed_max_kmh > 90                    then 'high_winds'
            when uv_index_max >= 11                         then 'extreme_uv'
            when temp_anomaly_c > 5                         then 'heat_anomaly'
            when temp_anomaly_c < -5                        then 'cold_anomaly'
            when precip_anomaly_mm > 40                     then 'precip_anomaly'
            else null
        end                                                 as alert_type,

        -- Severidade
        case
            when temp_max_c > 45 or precipitation_mm > 150 then 'critical'
            when temp_max_c > 40 or precipitation_mm > 80  then 'high'
            when temp_anomaly_c > 5 or uv_index_max >= 11  then 'medium'
            else 'low'
        end                                                 as severity,

        -- Valores que causaram o alerta
        temp_max_c,
        temp_min_c,
        temp_anomaly_c,
        precipitation_mm,
        wind_speed_max_kmh,
        uv_index_max,

        _dbt_updated_at

    from facts
),

-- Filtra apenas linhas com alerta
filtered as (
    select * from alerts
    where alert_type is not null
)

select * from filtered
order by date desc, severity desc
