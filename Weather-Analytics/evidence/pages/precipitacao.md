---
title: Análise de Precipitação
---

```sql regioes
select distinct region as value, region as label
from weather_dw.mart_climate__daily_facts
order by region
```

<Dropdown
  name="regiao_selecionada"
  data={regioes}
  value="value"
  label="label"
  title="Região"
  defaultValue="Sul"
/>

```sql serie_precipitacao_regiao
select
  date,
  city_name,
  precipitation_mm,
  precipitation_class,
  precip_avg_30d_mm,
  precip_anomaly_mm
from weather_dw.mart_climate__daily_facts
where region = '${inputs.regiao_selecionada}'
  and date >= date_sub(current_date(), interval 90 day)
order by date, city_name
```

```sql acumulado_por_cidade
select
  city_name,
  state_code,
  round(sum(precipitation_mm), 1)                as acumulado_90d_mm,
  round(avg(precipitation_mm), 1)                as media_diaria_mm,
  countif(precipitation_mm > 0)                  as dias_com_chuva,
  countif(precipitation_class = 'heavy')         as dias_chuva_forte,
  countif(precipitation_class = 'extreme')       as dias_chuva_extrema,
  round(avg(precip_anomaly_mm), 2)               as anomalia_media_mm
from weather_dw.mart_climate__daily_facts
where region = '${inputs.regiao_selecionada}'
  and date >= date_sub(current_date(), interval 90 day)
group by city_name, state_code
order by acumulado_90d_mm desc
```

```sql distribuicao_classes
select
  precipitation_class             as classe,
  count(*)                        as dias,
  round(100.0 * count(*) / sum(count(*)) over (), 1) as percentual
from weather_dw.mart_climate__daily_facts
where region = '${inputs.regiao_selecionada}'
  and date >= date_sub(current_date(), interval 90 day)
group by precipitation_class
order by
  case precipitation_class
    when 'dry'      then 1
    when 'light'    then 2
    when 'moderate' then 3
    when 'heavy'    then 4
    when 'extreme'  then 5
  end
```

```sql precipitacao_mensal
select
  year_month,
  city_name,
  round(sum(precipitation_mm), 1)     as acumulado_mensal_mm,
  countif(precipitation_mm > 0)       as dias_com_chuva
from weather_dw.mart_climate__daily_facts
where region = '${inputs.regiao_selecionada}'
group by year_month, city_name
order by year_month, city_name
```

```sql anomalia_precipitacao
select
  date,
  city_name,
  precipitation_mm,
  precip_avg_30d_mm,
  precip_anomaly_mm
from weather_dw.mart_climate__daily_facts
where region = '${inputs.regiao_selecionada}'
  and date >= date_sub(current_date(), interval 60 day)
  and abs(precip_anomaly_mm) > 5
order by abs(precip_anomaly_mm) desc
limit 50
```

# Análise de Precipitação

Análise dos **últimos 90 dias** para a região selecionada.

---

## Acumulado por Cidade

<BarChart
  data={acumulado_por_cidade}
  x="city_name"
  y="acumulado_90d_mm"
  yAxisTitle="Precipitação acumulada (mm)"
  title="Total acumulado nos últimos 90 dias"
  swapXY=true
/>

---

## Distribuição de Classificação de Chuva

> Classificação baseada na precipitação diária:
> **dry** = 0 mm · **light** < 5 mm · **moderate** < 20 mm · **heavy** < 50 mm · **extreme** ≥ 50 mm

<BarChart
  data={distribuicao_classes}
  x="classe"
  y="percentual"
  yAxisTitle="% dos dias"
  title="Proporção de dias por classificação"
/>

---

## Tabela Detalhada por Cidade

<DataTable data={acumulado_por_cidade} rows=20>
  <Column id="city_name" title="Cidade" />
  <Column id="state_code" title="UF" />
  <Column id="acumulado_90d_mm" title="Acumulado 90d (mm)" fmt="0.0" />
  <Column id="media_diaria_mm" title="Média Diária (mm)" fmt="0.0" />
  <Column id="dias_com_chuva" title="Dias c/ Chuva" />
  <Column id="dias_chuva_forte" title="Dias Forte" />
  <Column id="dias_chuva_extrema" title="Dias Extremo" />
  <Column id="anomalia_media_mm" title="Anomalia Média (mm)" fmt="+0.0;-0.0" contentType="colorscale" />
</DataTable>

---

## Dias com Anomalia de Precipitação Significativa (> 5 mm)

<DataTable data={anomalia_precipitacao} rows=20>
  <Column id="date" title="Data" />
  <Column id="city_name" title="Cidade" />
  <Column id="precipitation_mm" title="Precipitação (mm)" fmt="0.0" />
  <Column id="precip_avg_30d_mm" title="Média 30d (mm)" fmt="0.0" />
  <Column id="precip_anomaly_mm" title="Anomalia (mm)" fmt="+0.0;-0.0" contentType="colorscale" />
</DataTable>

---

**Navegação:** [Início](/) · [Temperatura](/temperatura) · [Alertas](/alertas)
