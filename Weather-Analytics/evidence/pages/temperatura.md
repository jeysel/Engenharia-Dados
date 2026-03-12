---
title: Análise de Temperatura
---

```sql cidades_disponiveis
select distinct
  location_id  as value,
  city_name    as label
from weather_dw.mart_climate__daily_facts
order by city_name
```

<Dropdown
  name="cidade_selecionada"
  data={cidades_disponiveis}
  value="value"
  label="label"
  title="Cidade"
  defaultValue="florianopolis"
/>

```sql serie_temperatura
select
  date,
  temp_max_c,
  temp_avg_c,
  temp_min_c,
  temp_avg_30d_c,
  temp_anomaly_c,
  temp_amplitude_c
from weather_dw.mart_climate__daily_facts
where location_id = '${inputs.cidade_selecionada}'
  and date >= date_sub(current_date(), interval 90 day)
order by date
```

```sql resumo_cidade
select
  city_name,
  state_name,
  region,
  round(avg(temp_max_c), 1)         as media_maxima,
  round(avg(temp_min_c), 1)         as media_minima,
  round(avg(temp_avg_c), 1)         as media_temperatura,
  round(max(temp_max_c), 1)         as recorde_max,
  round(min(temp_min_c), 1)         as recorde_min,
  round(avg(temp_anomaly_c), 2)     as anomalia_media,
  round(avg(daylight_hours), 1)     as horas_luz_media
from weather_dw.mart_climate__daily_facts
where location_id = '${inputs.cidade_selecionada}'
  and date >= date_sub(current_date(), interval 90 day)
group by city_name, state_name, region
```

```sql anomalia_por_mes
select
  year_month,
  round(avg(temp_anomaly_c), 2)     as anomalia_media,
  round(avg(temp_avg_c), 1)         as temp_media,
  round(avg(temp_avg_30d_c), 1)     as baseline_30d
from weather_dw.mart_climate__daily_facts
where location_id = '${inputs.cidade_selecionada}'
group by year_month
order by year_month
```

```sql amplitude_termica
select
  date,
  temp_amplitude_c,
  is_weekend
from weather_dw.mart_climate__daily_facts
where location_id = '${inputs.cidade_selecionada}'
  and date >= date_sub(current_date(), interval 90 day)
order by date
```

```sql ranking_anomalia_hoje
select
  city_name,
  state_code,
  region,
  temp_avg_c,
  temp_anomaly_c,
  temp_avg_30d_c
from weather_dw.mart_climate__daily_facts
where date = (
    select max(date) from weather_dw.mart_climate__daily_facts
)
order by temp_anomaly_c desc
```

# Análise de Temperatura

Série dos **últimos 90 dias** para a cidade selecionada.

{#if resumo_cidade.length > 0}

**{resumo_cidade[0].city_name}** — {resumo_cidade[0].state_name} · {resumo_cidade[0].region}

<BigValue data={resumo_cidade} value="media_temperatura" title="Temp. Média" fmt="0.0°C" />
<BigValue data={resumo_cidade} value="media_maxima" title="Máxima Média" fmt="0.0°C" />
<BigValue data={resumo_cidade} value="media_minima" title="Mínima Média" fmt="0.0°C" />
<BigValue data={resumo_cidade} value="anomalia_media" title="Anomalia Média" fmt="+0.00;-0.00°C" />

{/if}

---

## Série Temporal — Máxima / Média / Mínima

<LineChart
  data={serie_temperatura}
  x="date"
  y={["temp_max_c", "temp_avg_c", "temp_min_c", "temp_avg_30d_c"]}
  yAxisTitle="Temperatura (°C)"
  labels
/>

---

## Anomalia de Temperatura por Mês

> Desvio da temperatura média em relação à rolling average de 30 dias.
> Positivo = mais quente que o normal; negativo = mais frio.

<BarChart
  data={anomalia_por_mes}
  x="year_month"
  y="anomalia_media"
  yAxisTitle="Anomalia (°C)"
  colorPalette={["#e74c3c"]}
/>

---

## Amplitude Térmica Diária

> Diferença entre temperatura máxima e mínima em cada dia.
> Amplitudes maiores indicam clima mais seco e continental.

<LineChart
  data={amplitude_termica}
  x="date"
  y="temp_amplitude_c"
  yAxisTitle="Amplitude (°C)"
/>

---

## Ranking de Anomalia — Último Dia Disponível

<DataTable data={ranking_anomalia_hoje} rows=32>
  <Column id="city_name" title="Cidade" />
  <Column id="state_code" title="UF" />
  <Column id="region" title="Região" />
  <Column id="temp_avg_c" title="Temp. Média (°C)" fmt="0.0" />
  <Column id="temp_avg_30d_c" title="Baseline 30d (°C)" fmt="0.0" />
  <Column id="temp_anomaly_c" title="Anomalia (°C)" fmt="+0.00;-0.00" contentType="colorscale" />
</DataTable>

---

**Navegação:** [Início](/) · [Precipitação](/precipitacao) · [Alertas](/alertas)
