{{
  config(
    materialized = 'table',
    schema = 'marts',
    partition_by = {
      "field": "date",
      "data_type": "date",
      "granularity": "month"
    },
    cluster_by = ["location_id", "year_month"]
  )
}}

/*
  mart_climate__daily_facts
  ─────────────────────────
  Tabela fato central do DW. Combina dados diários com enriquecimentos:
  - Localização + metadados geográficos (via seed)
  - Cálculo de dias úteis / finais de semana
  - Classificação do clima (WMO codes → label amigável)
  - Anomalia em relação à média histórica (últimos 30 dias)

  Particionada por mês, clusterizada por location_id para
  reduzir bytes lidos nas queries analíticas mais comuns.
*/

with daily as (
    select * from {{ ref('stg_weather__daily') }}
),

locations as (
    select * from {{ ref('locations') }}  -- seed
),

-- Média histórica rolling 30 dias para detectar anomalias
rolling_avg as (
    select
        location_id,
        date,
        avg(temp_avg_c) over (
            partition by location_id
            order by date
            rows between 29 preceding and current row
        )                                               as temp_avg_30d_c,
        avg(precipitation_mm) over (
            partition by location_id
            order by date
            rows between 29 preceding and current row
        )                                               as precip_avg_30d_mm
    from daily
),

final as (
    select
        -- Dimensão tempo
        d.date,
        extract(year from d.date)::integer              as year,
        extract(month from d.date)::integer             as month,
        extract(day from d.date)::integer               as day,
        format_date('%Y-%m', d.date)                    as year_month,
        extract(dayofweek from d.date)::integer         as day_of_week,
        case
            when extract(dayofweek from d.date) in (1, 7)
            then true else false
        end                                             as is_weekend,
        extract(quarter from d.date)::integer           as quarter,

        -- Dimensão localização
        d.location_id,
        l.city_name,
        l.state_name,
        l.country,
        l.region,
        l.latitude,
        l.longitude,
        l.altitude_m,

        -- Métricas de temperatura
        d.temp_max_c,
        d.temp_min_c,
        d.temp_avg_c,
        round(d.temp_max_c - d.temp_min_c, 2)          as temp_amplitude_c,

        -- Anomalia de temperatura
        round(d.temp_avg_c - ra.temp_avg_30d_c, 2)     as temp_anomaly_c,
        ra.temp_avg_30d_c,

        -- Precipitação
        d.precipitation_mm,
        d.rain_mm,
        ra.precip_avg_30d_mm,
        round(d.precipitation_mm - ra.precip_avg_30d_mm, 2) as precip_anomaly_mm,
        case
            when d.precipitation_mm = 0     then 'dry'
            when d.precipitation_mm < 5     then 'light'
            when d.precipitation_mm < 20    then 'moderate'
            when d.precipitation_mm < 50    then 'heavy'
            else 'extreme'
        end                                             as precipitation_class,

        -- Vento e UV
        d.wind_speed_max_kmh,
        d.uv_index_max,
        case
            when d.uv_index_max < 3  then 'low'
            when d.uv_index_max < 6  then 'moderate'
            when d.uv_index_max < 8  then 'high'
            when d.uv_index_max < 11 then 'very_high'
            else 'extreme'
        end                                             as uv_risk_level,

        -- Horas de sol
        d.sunrise_at,
        d.sunset_at,
        timestamp_diff(d.sunset_at, d.sunrise_at, minute) / 60.0 as daylight_hours,

        -- Metadados de pipeline
        d._extracted_at,
        d._loaded_at,
        current_timestamp                               as _dbt_updated_at

    from daily d
    left join locations l using (location_id)
    left join rolling_avg ra using (location_id, date)
)

select * from final
