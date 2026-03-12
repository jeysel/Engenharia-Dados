{{
  config(
    materialized = 'view',
    schema = 'staging',
  )
}}

/*
  stg_weather__daily
  ──────────────────
  Dados diários agregados da Open-Meteo (forecast + archive).
*/

with source as (
    select * from {{ source('open_meteo', 'daily') }}
),

renamed as (
    select
        location_id::text                                   as location_id,
        date::date                                          as date,
        latitude::numeric(9,6)                              as latitude,
        longitude::numeric(9,6)                             as longitude,

        -- Temperatura
        temperature_2m_max::numeric(5,2)                    as temp_max_c,
        temperature_2m_min::numeric(5,2)                    as temp_min_c,
        (temperature_2m_max + temperature_2m_min)::numeric
            / 2                                             as temp_avg_c,

        -- Precipitação
        precipitation_sum::numeric(7,2)                     as precipitation_mm,
        rain_sum::numeric(7,2)                              as rain_mm,

        -- Vento
        wind_speed_10m_max::numeric(5,2)                    as wind_speed_max_kmh,

        -- Radiação / UV
        uv_index_max::numeric(4,2)                          as uv_index_max,

        -- Sol
        sunrise::timestamp                                  as sunrise_at,
        sunset::timestamp                                   as sunset_at,

        -- Metadados
        _extracted_at::timestamp                            as _extracted_at,
        current_timestamp                                   as _loaded_at

    from source
    where date is not null
      and location_id is not null
)

select * from renamed
