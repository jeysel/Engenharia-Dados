---
title: Weather Analytics — Visão Geral
---

```sql totais
select
  count(distinct location_id)                          as total_locais,
  count(distinct date)                                 as total_dias,
  min(date)                                            as data_inicial,
  max(date)                                            as data_final,
  round(avg(temp_avg_c), 1)                            as temp_media_geral_c,
  round(avg(precipitation_mm), 1)                      as precip_media_diaria_mm
from weather_dw.mart_climate__daily_facts
```

```sql alertas_ativos
select count(*) as total_alertas
from weather_dw.mart_climate__alerts
where date >= date_sub(current_date(), interval 7 day)
```

```sql temperatura_nacional_30d
select
  date,
  round(avg(temp_max_c), 1)   as temp_max,
  round(avg(temp_avg_c), 1)   as temp_media,
  round(avg(temp_min_c), 1)   as temp_min
from weather_dw.mart_climate__daily_facts
where date >= date_sub(current_date(), interval 30 day)
group by date
order by date
```

```sql alertas_por_tipo_30d
select
  alert_type                    as tipo,
  count(*)                      as ocorrencias,
  countif(severity = 'critical') as criticos,
  countif(severity = 'high')    as altos
from weather_dw.mart_climate__alerts
where date >= date_sub(current_date(), interval 30 day)
group by alert_type
order by ocorrencias desc
```

```sql resumo_por_regiao
select
  region                                              as regiao,
  count(distinct location_id)                         as cidades,
  round(avg(temp_avg_c), 1)                           as temp_media_c,
  round(avg(precipitation_mm), 1)                     as precip_media_mm,
  round(avg(temp_anomaly_c), 2)                       as anomalia_media_c
from weather_dw.mart_climate__daily_facts
where date >= date_sub(current_date(), interval 30 day)
group by region
order by temp_media_c desc
```

```sql ultimas_atualizacoes
select
  city_name                                           as cidade,
  state_code,
  max(date)                                           as ultimo_dado,
  max(_extracted_at)                                  as ultima_coleta
from weather_dw.mart_climate__daily_facts
group by city_name, state_code
order by ultima_coleta desc
limit 10
```

# Weather Analytics Pipeline

Pipeline de dados climáticos cobrindo **{totais[0].total_locais} localidades** brasileiras,
com dados históricos de **{totais[0].data_inicial}** a **{totais[0].data_final}**
({totais[0].total_dias} dias de série temporal).

<BigValue
  data={totais}
  value="total_locais"
  title="Localidades Monitoradas"
/>
<BigValue
  data={totais}
  value="total_dias"
  title="Dias de Histórico"
/>
<BigValue
  data={totais}
  value="temp_media_geral_c"
  title="Temp. Média Geral"
  fmt="0.0°C"
/>
<BigValue
  data={alertas_ativos}
  value="total_alertas"
  title="Alertas (últimos 7 dias)"
/>

---

## Temperatura Nacional — Últimos 30 dias

<LineChart
  data={temperatura_nacional_30d}
  x="date"
  y={["temp_max", "temp_media", "temp_min"]}
  yAxisTitle="Temperatura (°C)"
  title="Máxima / Média / Mínima diária (média entre todas as localidades)"
  labels
/>

---

## Alertas por Tipo — Últimos 30 dias

<BarChart
  data={alertas_por_tipo_30d}
  x="tipo"
  y="ocorrencias"
  yAxisTitle="Ocorrências"
  title="Eventos climáticos extremos detectados"
  colorPalette={["#e74c3c", "#e67e22"]}
/>

---

## Resumo por Região

<DataTable data={resumo_por_regiao}>
  <Column id="regiao" title="Região" />
  <Column id="cidades" title="Cidades" />
  <Column id="temp_media_c" title="Temp. Média (°C)" fmt="0.0" />
  <Column id="precip_media_mm" title="Precip. Média (mm)" fmt="0.0" />
  <Column id="anomalia_media_c" title="Anomalia Temp. (°C)" fmt="+0.00;-0.00" contentType="colorscale" />
</DataTable>

---

## Frescos de Pipeline

<DataTable data={ultimas_atualizacoes} title="Últimas coletas por cidade" />

---

**Navegação:** [Temperatura](/temperatura) · [Precipitação](/precipitacao) · [Alertas](/alertas)
