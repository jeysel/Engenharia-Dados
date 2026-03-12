---
title: Detalhes por Cidade
---

```sql info_cidade
select distinct
  city_name,
  state_name,
  state_code,
  country,
  region,
  latitude,
  longitude,
  altitude_m
from weather_dw.mart_climate__daily_facts
where location_id = '${params.cidade}'
limit 1
```

```sql serie_90d
select
  date,
  temp_max_c,
  temp_avg_c,
  temp_min_c,
  temp_avg_30d_c,
  temp_anomaly_c,
  temp_amplitude_c,
  precipitation_mm,
  precip_avg_30d_mm,
  precipitation_class,
  wind_speed_max_kmh,
  uv_index_max,
  uv_risk_level,
  daylight_hours,
  is_weekend
from weather_dw.mart_climate__daily_facts
where location_id = '${params.cidade}'
  and date >= date_sub(current_date(), interval 90 day)
order by date
```

```sql resumo_periodo
select
  round(avg(temp_max_c), 1)              as media_maxima,
  round(avg(temp_min_c), 1)             as media_minima,
  round(avg(temp_avg_c), 1)             as media_temperatura,
  round(max(temp_max_c), 1)             as recorde_calor,
  round(min(temp_min_c), 1)             as recorde_frio,
  round(sum(precipitation_mm), 0)       as chuva_acumulada_mm,
  countif(precipitation_mm > 0)         as dias_com_chuva,
  round(avg(daylight_hours), 1)         as horas_luz_media,
  round(avg(temp_anomaly_c), 2)         as anomalia_media_c
from weather_dw.mart_climate__daily_facts
where location_id = '${params.cidade}'
  and date >= date_sub(current_date(), interval 90 day)
```

```sql alertas_cidade
select
  date,
  alert_type,
  severity,
  temp_max_c,
  temp_min_c,
  temp_anomaly_c,
  precipitation_mm,
  wind_speed_max_kmh,
  uv_index_max
from weather_dw.mart_climate__alerts
where location_id = '${params.cidade}'
  and date >= date_sub(current_date(), interval 90 day)
order by date desc
```

```sql uv_distribuicao
select
  uv_risk_level                         as nivel_uv,
  count(*)                              as dias,
  round(avg(uv_index_max), 1)          as uv_medio
from weather_dw.mart_climate__daily_facts
where location_id = '${params.cidade}'
  and date >= date_sub(current_date(), interval 90 day)
group by uv_risk_level
order by
  case uv_risk_level
    when 'low'       then 1
    when 'moderate'  then 2
    when 'high'      then 3
    when 'very_high' then 4
    when 'extreme'   then 5
  end
```

```sql lista_todas_cidades
select
  location_id  as cidade,
  city_name,
  state_code,
  region
from weather_dw.mart_climate__daily_facts
group by location_id, city_name, state_code, region
order by region, city_name
```

{#if info_cidade.length > 0}

# {info_cidade[0].city_name}

**{info_cidade[0].state_name}** · {info_cidade[0].region} · {info_cidade[0].country}

> Lat: {info_cidade[0].latitude} · Lon: {info_cidade[0].longitude} · Altitude: {info_cidade[0].altitude_m} m

{/if}

**Período:** últimos 90 dias

<BigValue data={resumo_periodo} value="media_temperatura" title="Temp. Média" fmt="0.0°C" />
<BigValue data={resumo_periodo} value="recorde_calor" title="Recorde de Calor" fmt="0.0°C" />
<BigValue data={resumo_periodo} value="recorde_frio" title="Recorde de Frio" fmt="0.0°C" />
<BigValue data={resumo_periodo} value="chuva_acumulada_mm" title="Chuva Acumulada" fmt="0mm" />
<BigValue data={resumo_periodo} value="dias_com_chuva" title="Dias com Chuva" />
<BigValue data={resumo_periodo} value="anomalia_media_c" title="Anomalia Média" fmt="+0.00;-0.00°C" />

---

## Temperatura — Série Temporal

<LineChart
  data={serie_90d}
  x="date"
  y={["temp_max_c", "temp_avg_c", "temp_min_c", "temp_avg_30d_c"]}
  yAxisTitle="Temperatura (°C)"
  labels
/>

---

## Precipitação Diária

<BarChart
  data={serie_90d}
  x="date"
  y="precipitation_mm"
  yAxisTitle="Precipitação (mm)"
  colorPalette={["#3498db"]}
/>

---

## Anomalia de Temperatura

<LineChart
  data={serie_90d}
  x="date"
  y="temp_anomaly_c"
  yAxisTitle="Anomalia (°C)"
  yMin={-10}
  yMax={10}
  colorPalette={["#e74c3c"]}
/>

---

## Distribuição de Risco UV

<BarChart
  data={uv_distribuicao}
  x="nivel_uv"
  y="dias"
  yAxisTitle="Número de dias"
  title="Dias por nível de risco UV (OMS)"
/>

---

## Alertas Recentes

{#if alertas_cidade.length > 0}

<DataTable data={alertas_cidade} rows=10>
  <Column id="date" title="Data" />
  <Column id="alert_type" title="Tipo" />
  <Column id="severity" title="Severidade" contentType="colorscale" />
  <Column id="temp_max_c" title="Temp. Máx (°C)" fmt="0.0" />
  <Column id="precipitation_mm" title="Precip. (mm)" fmt="0.0" />
  <Column id="wind_speed_max_kmh" title="Vento (km/h)" fmt="0.0" />
  <Column id="uv_index_max" title="UV Máx" fmt="0.0" />
</DataTable>

{:else}

> Nenhum alerta climático extremo nos últimos 90 dias.

{/if}

---

## Outras Cidades

<DataTable data={lista_todas_cidades} rows=10 search=true>
  <Column id="city_name" title="Cidade" contentType="link" linkLabel="city_name" valueLabel="cidade" href="/cidades/{cidade}" />
  <Column id="state_code" title="UF" />
  <Column id="region" title="Região" />
</DataTable>

---

**Navegação:** [Início](/) · [Temperatura](/temperatura) · [Precipitação](/precipitacao) · [Alertas](/alertas)
