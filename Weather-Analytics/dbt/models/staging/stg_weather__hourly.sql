{{
  config(
    materialized = 'view',
    schema = 'staging',
  )
}}

/*
  stg_weather__hourly
  ───────────────────
  Limpeza e tipagem dos dados brutos horários vindos do Airbyte.
  Fonte: raw.open_meteo_hourly (PostgreSQL staging)
*/

with source as (
    select * from {{ source('open_meteo', 'hourly') }}
),

renamed as (
    select
        -- Chaves
        location_id::text                                   as location_id,
        timestamp::timestamp with time zone                 as observed_at,

        -- Geo
        latitude::numeric(9,6)                              as latitude,
        longitude::numeric(9,6)                             as longitude,
        elevation::numeric(7,2)                             as elevation_m,
        timezone::text                                      as timezone,

        -- Temperatura
        temperature_2m::numeric(5,2)                        as temperature_c,

        -- Umidade
        relative_humidity_2m::integer                       as relative_humidity_pct,

        -- Precipitação
        precipitation::numeric(6,2)                         as precipitation_mm,

        -- Vento
        wind_speed_10m::numeric(5,2)                        as wind_speed_kmh,
        wind_direction_10m::integer                         as wind_direction_deg,

        -- Atmosfera
        surface_pressure::numeric(7,2)                      as surface_pressure_hpa,
        cloud_cover::integer                                as cloud_cover_pct,
        visibility::numeric(8,2)                            as visibility_m,

        -- Código WMO de condição climática
        weather_code::integer                               as wmo_weather_code,

        -- Metadados
        _extracted_at::timestamp                            as _extracted_at,
        current_timestamp                                   as _loaded_at

    from source
    where timestamp is not null
      and location_id is not null
)

select * from renamed
