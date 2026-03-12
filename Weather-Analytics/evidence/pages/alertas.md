---
title: Alertas Climáticos
---

```sql alertas_recentes
select
  date,
  city_name,
  state_name,
  region,
  alert_type,
  severity,
  temp_max_c,
  temp_min_c,
  temp_anomaly_c,
  precipitation_mm,
  wind_speed_max_kmh,
  uv_index_max
from weather_dw.mart_climate__alerts
where date >= date_sub(current_date(), interval 30 day)
order by date desc, severity desc
```

```sql contagem_por_tipo
select
  alert_type                                        as tipo_alerta,
  count(*)                                          as total,
  countif(severity = 'critical')                    as criticos,
  countif(severity = 'high')                        as altos,
  countif(severity = 'medium')                      as medios,
  countif(severity = 'low')                         as baixos
from weather_dw.mart_climate__alerts
where date >= date_sub(current_date(), interval 30 day)
group by alert_type
order by total desc
```

```sql contagem_por_severidade
select
  severity                                          as severidade,
  count(*)                                          as total
from weather_dw.mart_climate__alerts
where date >= date_sub(current_date(), interval 30 day)
group by severity
order by
  case severity
    when 'critical' then 1
    when 'high'     then 2
    when 'medium'   then 3
    when 'low'      then 4
  end
```

```sql historico_alertas_diario
select
  date,
  count(*)                                          as total_alertas,
  countif(severity = 'critical')                    as criticos,
  countif(severity = 'high')                        as altos
from weather_dw.mart_climate__alerts
where date >= date_sub(current_date(), interval 60 day)
group by date
order by date
```

```sql cidades_mais_alertas
select
  city_name,
  state_code,
  region,
  count(*)                                          as total_alertas,
  countif(severity = 'critical')                    as criticos,
  string_agg(distinct alert_type, ', ')             as tipos_detectados
from weather_dw.mart_climate__alerts
where date >= date_sub(current_date(), interval 30 day)
group by city_name, state_code, region
order by total_alertas desc
limit 15
```

```sql alertas_criticos
select
  date,
  city_name,
  state_name,
  alert_type,
  temp_max_c,
  precipitation_mm,
  wind_speed_max_kmh,
  uv_index_max
from weather_dw.mart_climate__alerts
where severity = 'critical'
  and date >= date_sub(current_date(), interval 30 day)
order by date desc
```

# Alertas Climáticos

Eventos climáticos extremos detectados nos **últimos 30 dias**.

<BigValue
  data={contagem_por_severidade}
  value="total"
  title="Alertas Críticos"
  filter="severidade = 'critical'"
/>
<BigValue
  data={contagem_por_severidade}
  value="total"
  title="Alertas Altos"
  filter="severidade = 'high'"
/>
<BigValue
  data={contagem_por_severidade}
  value="total"
  title="Alertas Médios"
  filter="severidade = 'medium'"
/>

---

## Evolução Diária de Alertas

<AreaChart
  data={historico_alertas_diario}
  x="date"
  y={["criticos", "altos", "total_alertas"]}
  yAxisTitle="Número de alertas"
  title="Alertas por dia (últimos 60 dias)"
/>

---

## Alertas por Tipo

<BarChart
  data={contagem_por_tipo}
  x="tipo_alerta"
  y={["criticos", "altos", "medios", "baixos"]}
  yAxisTitle="Ocorrências"
  title="Breakdown por severidade dentro de cada tipo"
  type="stacked"
/>

---

## Cidades com Mais Alertas

<DataTable data={cidades_mais_alertas}>
  <Column id="city_name" title="Cidade" />
  <Column id="state_code" title="UF" />
  <Column id="region" title="Região" />
  <Column id="total_alertas" title="Total" />
  <Column id="criticos" title="Críticos" contentType="colorscale" />
  <Column id="tipos_detectados" title="Tipos Detectados" />
</DataTable>

---

## Alertas Críticos — Detalhes

{#if alertas_criticos.length > 0}

<DataTable data={alertas_criticos} rows=20>
  <Column id="date" title="Data" />
  <Column id="city_name" title="Cidade" />
  <Column id="state_name" title="Estado" />
  <Column id="alert_type" title="Tipo de Alerta" />
  <Column id="temp_max_c" title="Temp. Máx (°C)" fmt="0.0" />
  <Column id="precipitation_mm" title="Precip. (mm)" fmt="0.0" />
  <Column id="wind_speed_max_kmh" title="Vento (km/h)" fmt="0.0" />
  <Column id="uv_index_max" title="UV Máx" fmt="0.0" />
</DataTable>

{:else}

> Nenhum alerta crítico nos últimos 30 dias.

{/if}

---

## Todos os Alertas Recentes

<DataTable data={alertas_recentes} rows=30 search=true>
  <Column id="date" title="Data" />
  <Column id="city_name" title="Cidade" />
  <Column id="region" title="Região" />
  <Column id="alert_type" title="Tipo" />
  <Column id="severity" title="Severidade" contentType="colorscale" />
  <Column id="temp_max_c" title="Temp. Máx" fmt="0.0°C" />
  <Column id="precipitation_mm" title="Precip." fmt="0.0mm" />
  <Column id="wind_speed_max_kmh" title="Vento" fmt="0.0 km/h" />
</DataTable>

---

**Navegação:** [Início](/) · [Temperatura](/temperatura) · [Precipitação](/precipitacao)
