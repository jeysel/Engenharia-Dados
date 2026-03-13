{% macro generate_schema_name(custom_schema_name, node) -%}
  {%- if custom_schema_name is none -%}
    {{ target.schema }}
  {%- else -%}
    {{ custom_schema_name | trim }}
  {%- endif -%}
{%- endmacro %}


{% macro wmo_code_to_label(wmo_code_column) %}
  /*
    Converte códigos WMO (World Meteorological Organization) para labels legíveis.
    Referência: https://open-meteo.com/en/docs
  */
  case {{ wmo_code_column }}
    when 0  then 'Clear sky'
    when 1  then 'Mainly clear'
    when 2  then 'Partly cloudy'
    when 3  then 'Overcast'
    when 45 then 'Fog'
    when 48 then 'Icy fog'
    when 51 then 'Light drizzle'
    when 53 then 'Moderate drizzle'
    when 55 then 'Dense drizzle'
    when 61 then 'Slight rain'
    when 63 then 'Moderate rain'
    when 65 then 'Heavy rain'
    when 71 then 'Slight snow'
    when 73 then 'Moderate snow'
    when 75 then 'Heavy snow'
    when 77 then 'Snow grains'
    when 80 then 'Slight showers'
    when 81 then 'Moderate showers'
    when 82 then 'Violent showers'
    when 85 then 'Slight snow showers'
    when 86 then 'Heavy snow showers'
    when 95 then 'Thunderstorm'
    when 96 then 'Thunderstorm with hail'
    when 99 then 'Thunderstorm with heavy hail'
    else 'Unknown'
  end
{% endmacro %}


{% macro celsius_to_fahrenheit(col) %}
  round(({{ col }} * 9.0 / 5.0) + 32, 2)
{% endmacro %}


{% macro wind_beaufort_scale(wind_speed_kmh_col) %}
  /*
    Classifica velocidade do vento na escala Beaufort (0–12).
  */
  case
    when {{ wind_speed_kmh_col }} < 1   then 0   -- Calm
    when {{ wind_speed_kmh_col }} < 6   then 1   -- Light air
    when {{ wind_speed_kmh_col }} < 12  then 2   -- Light breeze
    when {{ wind_speed_kmh_col }} < 20  then 3   -- Gentle breeze
    when {{ wind_speed_kmh_col }} < 29  then 4   -- Moderate breeze
    when {{ wind_speed_kmh_col }} < 39  then 5   -- Fresh breeze
    when {{ wind_speed_kmh_col }} < 50  then 6   -- Strong breeze
    when {{ wind_speed_kmh_col }} < 62  then 7   -- High wind
    when {{ wind_speed_kmh_col }} < 75  then 8   -- Gale
    when {{ wind_speed_kmh_col }} < 89  then 9   -- Strong gale
    when {{ wind_speed_kmh_col }} < 103 then 10  -- Storm
    when {{ wind_speed_kmh_col }} < 118 then 11  -- Violent storm
    else 12                                       -- Hurricane
  end
{% endmacro %}


{% macro generate_date_spine(start_date, end_date) %}
  /*
    Gera uma spine de datas entre start e end para garantir
    que todos os dias apareçam mesmo sem dados.
    Uso: {{ generate_date_spine(var('start_date'), 'current_date') }}
  */
  with date_spine as (
    {{ dbt_utils.date_spine(
        datepart = "day",
        start_date = "cast('" ~ start_date ~ "' as date)",
        end_date = end_date
    ) }}
  )
  select date_day as date from date_spine
{% endmacro %}
