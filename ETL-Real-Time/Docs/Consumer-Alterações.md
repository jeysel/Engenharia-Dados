# Alterações no Consumer Stream

**Data**: 03/11/2025
**Arquivo**: [consumer_stream.py](../cliente/consumer_stream.py)
**Objetivo**: Adaptar o consumer para processar dados de segurança pública do SINESP

---

## Resumo das Alterações

O arquivo `consumer_stream.py` foi completamente adaptado para consumir, processar e persistir dados de ocorrências criminais provenientes dos tópicos Kafka de segurança pública. As principais mudanças incluem:

1. Novo schema de dados para ocorrências criminais
2. Múltiplas tabelas Cassandra para diferentes granularidades
3. Suporte a múltiplos tópicos Kafka
4. Lógica de persistência inteligente baseada em granularidade

---

## Alterações por Função

### 1. `cria_keyspace()` - Atualizada

**Localização**: Linhas 34-45

**Mudança**:
- **Antes**: Keyspace `dados_usuarios`
- **Depois**: Keyspace `dados_seguranca_publica`

```python
CREATE KEYSPACE IF NOT EXISTS dados_seguranca_publica
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'};
```

---

### 2. `cria_tabela()` - Reformulada Completamente

**Localização**: Linhas 47-132

**Mudanças Principais**:

#### Antes:
- Uma única tabela: `tb_usuarios`
- Campos: id, first_name, last_name, gender, address, etc.

#### Depois:
- **Três tabelas especializadas** para diferentes granularidades de dados

#### Tabela 1: `tb_ocorrencias_municipio`

**Uso**: Dados de ocorrências criminais por município

**Campos**:
```sql
CREATE TABLE IF NOT EXISTS dados_seguranca_publica.tb_ocorrencias_municipio (
    id TEXT PRIMARY KEY,
    dataset_id TEXT,
    resource_id TEXT,
    granularidade TEXT,
    ano TEXT,
    mes TEXT,
    mes_ano TEXT,
    uf TEXT,
    uf_nome TEXT,
    codigo_municipio TEXT,      -- Específico para município
    municipio TEXT,              -- Específico para município
    regiao TEXT,                 -- Específico para município
    tipo_crime TEXT,
    vitimas TEXT,
    ocorrencias TEXT,
    homicidio_doloso TEXT,
    lesao_corp_morte TEXT,
    latrocinio TEXT,
    roubo_veiculo TEXT,
    roubo_carga TEXT,
    roubo_inst_financeira TEXT,
    furto_veiculo TEXT,
    estupro TEXT,
    data_extracao TEXT
);
```

**Campos Únicos**: `codigo_municipio`, `municipio`, `regiao`

---

#### Tabela 2: `tb_ocorrencias_estado`

**Uso**: Dados de ocorrências criminais agregados por estado

**Campos**:
```sql
CREATE TABLE IF NOT EXISTS dados_seguranca_publica.tb_ocorrencias_estado (
    id TEXT PRIMARY KEY,
    dataset_id TEXT,
    resource_id TEXT,
    granularidade TEXT,
    ano TEXT,
    mes TEXT,
    mes_ano TEXT,
    uf TEXT,
    uf_nome TEXT,
    tipo_crime TEXT,
    vitimas TEXT,
    ocorrencias TEXT,
    homicidio_doloso TEXT,
    lesao_corp_morte TEXT,
    latrocinio TEXT,
    roubo_veiculo TEXT,
    roubo_carga TEXT,
    roubo_inst_financeira TEXT,
    furto_veiculo TEXT,
    estupro TEXT,
    data_extracao TEXT
);
```

**Diferença**: Não possui campos de município

---

#### Tabela 3: `tb_ocorrencias_geral`

**Uso**: Dados genéricos ou de granularidade indefinida

**Campos**:
```sql
CREATE TABLE IF NOT EXISTS dados_seguranca_publica.tb_ocorrencias_geral (
    id TEXT PRIMARY KEY,
    dataset_id TEXT,
    resource_id TEXT,
    granularidade TEXT,
    ano TEXT,
    mes TEXT,
    mes_ano TEXT,
    uf TEXT,
    uf_nome TEXT,
    tipo_crime TEXT,
    vitimas TEXT,
    ocorrencias TEXT,
    data_extracao TEXT
);
```

**Diferença**: Campos mínimos sem indicadores detalhados de crimes

---

### 3. `insere_dados()` - Reformulada Completamente

**Localização**: Linhas 138-228

**Mudanças Principais**:

#### Nova Lógica de Roteamento

A função agora determina dinamicamente qual tabela usar baseado no campo `granularidade`:

```python
if granularidade == "municipio":
    # Insere em tb_ocorrencias_municipio
elif granularidade == "estado":
    # Insere em tb_ocorrencias_estado
else:
    # Insere em tb_ocorrencias_geral
```

#### Campos Extraídos

**Campos Comuns** (todos os registros):
- `record_id`, `dataset_id`, `resource_id`, `granularidade`
- `ano`, `mes`, `mes_ano`
- `uf`, `uf_nome`
- `tipo_crime`, `vitimas`, `ocorrencias`
- `data_extracao`

**Indicadores de Crimes**:
- `homicidio_doloso`, `lesao_corp_morte`, `latrocinio`
- `roubo_veiculo`, `roubo_carga`, `roubo_inst_financeira`
- `furto_veiculo`, `estupro`

**Campos Específicos de Município**:
- `codigo_municipio`, `municipio`, `regiao`

#### Exemplos de Queries Geradas

**Para Município**:
```sql
INSERT INTO dados_seguranca_publica.tb_ocorrencias_municipio(
    id, dataset_id, resource_id, granularidade, ano, mes, mes_ano, uf, uf_nome,
    codigo_municipio, municipio, regiao, tipo_crime, vitimas, ocorrencias,
    homicidio_doloso, lesao_corp_morte, latrocinio, roubo_veiculo, roubo_carga,
    roubo_inst_financeira, furto_veiculo, estupro, data_extracao
) VALUES (...)
```

**Para Estado**:
```sql
INSERT INTO dados_seguranca_publica.tb_ocorrencias_estado(
    id, dataset_id, resource_id, granularidade, ano, mes, mes_ano, uf, uf_nome,
    tipo_crime, vitimas, ocorrencias, homicidio_doloso, lesao_corp_morte, latrocinio,
    roubo_veiculo, roubo_carga, roubo_inst_financeira, furto_veiculo, estupro, data_extracao
) VALUES (...)
```

#### Logging Aprimorado

**Para Município**:
```python
logging.info(f" Log - Dados inseridos: {record_id} - {municipio}/{uf} - {tipo_crime} - {ocorrencias} ocorrências")
```

**Para Estado**:
```python
logging.info(f" Log - Dados inseridos: {record_id} - {uf} - {tipo_crime} - {ocorrencias} ocorrências")
```

---

### 4. `cria_kafka_connection()` - Atualizada

**Localização**: Linhas 259-277

**Mudanças**:

#### Antes:
```python
def cria_kafka_connection(spark_conn, stream_mode):
    .option("subscribe", "kafka_topic")  # Tópico único fixo
```

#### Depois:
```python
def cria_kafka_connection(spark_conn, stream_mode, topicos):
    .option("subscribe", topicos)  # Múltiplos tópicos dinâmicos
```

**Vantagens**:
- Suporta subscrição a múltiplos tópicos simultaneamente
- Flexibilidade para adicionar/remover tópicos
- Log indica quais tópicos estão sendo monitorados

---

### 5. `cria_df_from_kafka()` - Reformulada Completamente

**Localização**: Linhas 279-318

**Mudanças no Schema**:

#### Antes:
```python
schema = StructType([
    StructField("id", StringType(), False),
    StructField("first_name", StringType(), False),
    StructField("last_name", StringType(), False),
    # ... campos de usuário
])
```

#### Depois:
```python
schema = StructType([
    StructField("id", StringType(), True),
    StructField("dataset_id", StringType(), True),
    StructField("resource_id", StringType(), True),
    StructField("granularidade", StringType(), True),
    StructField("ano", StringType(), True),
    StructField("mes", StringType(), True),
    StructField("mes_ano", StringType(), True),
    StructField("uf", StringType(), True),
    StructField("uf_nome", StringType(), True),
    StructField("codigo_municipio", StringType(), True),
    StructField("municipio", StringType(), True),
    StructField("regiao", StringType(), True),
    StructField("tipo_crime", StringType(), True),
    StructField("vitimas", StringType(), True),
    StructField("ocorrencias", StringType(), True),
    StructField("homicidio_doloso", StringType(), True),
    StructField("lesao_corp_morte", StringType(), True),
    StructField("latrocinio", StringType(), True),
    StructField("roubo_veiculo", StringType(), True),
    StructField("roubo_carga", StringType(), True),
    StructField("roubo_inst_financeira", StringType(), True),
    StructField("furto_veiculo", StringType(), True),
    StructField("estupro", StringType(), True),
    StructField("data_extracao", StringType(), True),
])
```

**Observações**:
- Todos os campos são `nullable=True` para flexibilidade
- 24 campos no total (vs 12 na versão anterior)
- Schema compatível com dados do producer

#### Mudança na Filtragem:

**Antes**:
```python
.filter(instr(col("email"), "@") > 0)  # Valida email
```

**Depois**:
```python
.filter(col("id").isNotNull())  # Valida apenas ID não nulo
```

**Razão**: Dados de segurança pública não possuem email, apenas ID único

---

### 6. Código Principal `__main__` - Atualizado

**Localização**: Linhas 350-395

**Mudanças**:

#### Nova Configuração de Tópicos

```python
# Define os tópicos Kafka para consumir dados de segurança pública
topicos_kafka = "sinesp_ocorrencias_municipio,sinesp_ocorrencias_estado,sinesp_ocorrencias_geral"
```

**Múltiplos Tópicos**:
1. `sinesp_ocorrencias_municipio` - Dados por município
2. `sinesp_ocorrencias_estado` - Dados por estado
3. `sinesp_ocorrencias_geral` - Dados gerais

#### Atualização na Chamada de Função

**Antes**:
```python
kafka_df = cria_kafka_connection(spark_conn, stream_mode)
```

**Depois**:
```python
kafka_df = cria_kafka_connection(spark_conn, stream_mode, topicos_kafka)
```

#### Função de Processamento de Batch Aprimorada

**Antes**:
```python
def process_batch(batch_df, batch_id):
    for row in batch_df.collect():
        insere_dados(session, row)
```

**Depois**:
```python
def process_batch(batch_df, batch_id):
    # Loga informações sobre o lote
    logging.info(f" Log - Processando batch {batch_id} com {batch_df.count()} registros")

    # Itera sobre as linhas do lote e insere os dados no Cassandra
    for row in batch_df.collect():
        insere_dados(session, row)
```

**Novo Log de Inicialização**:
```python
logging.info(" Log - Streaming iniciado. Aguardando dados de segurança pública...")
```

---

## Fluxo de Dados Completo

```
┌─────────────────────────────────────────────────────────────┐
│ Kafka Broker (broker:29092)                                 │
│                                                              │
│ ├─> sinesp_ocorrencias_municipio                            │
│ ├─> sinesp_ocorrencias_estado                               │
│ └─> sinesp_ocorrencias_geral                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Spark Structured Streaming                                  │
│                                                              │
│ 1. cria_kafka_connection()                                  │
│    └─> Subscreve aos 3 tópicos simultaneamente              │
│                                                              │
│ 2. cria_df_from_kafka()                                     │
│    ├─> Parse JSON com schema de 24 campos                   │
│    ├─> Valida ID não nulo                                   │
│    └─> Retorna DataFrame estruturado                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ process_batch()                                             │
│                                                              │
│ Para cada batch:                                            │
│   ├─> Log do batch ID e contagem                            │
│   └─> Para cada registro: insere_dados()                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ insere_dados()                                              │
│                                                              │
│ Verifica granularidade:                                     │
│                                                              │
│ ├─> municipio                                               │
│ │   └─> INSERT INTO tb_ocorrencias_municipio               │
│ │       (23 campos incluindo município/região)              │
│                                                              │
│ ├─> estado                                                  │
│ │   └─> INSERT INTO tb_ocorrencias_estado                  │
│ │       (20 campos sem dados municipais)                    │
│                                                              │
│ └─> outro                                                   │
│     └─> INSERT INTO tb_ocorrencias_geral                    │
│         (12 campos básicos)                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Apache Cassandra (cassandra:9042)                           │
│                                                              │
│ Keyspace: dados_seguranca_publica                           │
│                                                              │
│ ├─> tb_ocorrencias_municipio                                │
│ │   Primary Key: id                                         │
│ │   Dados: Ocorrências por município                        │
│                                                              │
│ ├─> tb_ocorrencias_estado                                   │
│ │   Primary Key: id                                         │
│ │   Dados: Ocorrências por estado                           │
│                                                              │
│ └─> tb_ocorrencias_geral                                    │
│     Primary Key: id                                         │
│     Dados: Outros tipos de ocorrências                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Exemplos de Uso

### Executar Consumer em Modo Inicial

Processa todos os dados desde o início dos tópicos:

```bash
python consumer_stream.py --mode initial
```

### Executar Consumer em Modo Append

Processa apenas novos dados (padrão):

```bash
python consumer_stream.py --mode append
```

---

## Queries CQL para Consulta

### Consultar Ocorrências por Município

```sql
-- Ver todos os registros
SELECT * FROM dados_seguranca_publica.tb_ocorrencias_municipio;

-- Filtrar por UF
SELECT municipio, tipo_crime, ocorrencias, vitimas
FROM dados_seguranca_publica.tb_ocorrencias_municipio
WHERE uf = 'SP' ALLOW FILTERING;

-- Contar registros por município
SELECT municipio, COUNT(*)
FROM dados_seguranca_publica.tb_ocorrencias_municipio
GROUP BY municipio ALLOW FILTERING;
```

### Consultar Ocorrências por Estado

```sql
-- Ver todos os registros
SELECT * FROM dados_seguranca_publica.tb_ocorrencias_estado;

-- Filtrar por ano
SELECT uf, tipo_crime, ocorrencias
FROM dados_seguranca_publica.tb_ocorrencias_estado
WHERE ano = '2024' ALLOW FILTERING;

-- Homicídios por estado
SELECT uf, homicidio_doloso
FROM dados_seguranca_publica.tb_ocorrencias_estado
WHERE homicidio_doloso != '' ALLOW FILTERING;
```

### Estatísticas Gerais

```sql
-- Total de registros em cada tabela
SELECT COUNT(*) FROM dados_seguranca_publica.tb_ocorrencias_municipio;
SELECT COUNT(*) FROM dados_seguranca_publica.tb_ocorrencias_estado;
SELECT COUNT(*) FROM dados_seguranca_publica.tb_ocorrencias_geral;
```

---

## Monitoramento e Logs

### Logs de Sucesso

```
2025-11-03 10:15:23 - INFO - Log - Spark Connection criada com sucesso!
2025-11-03 10:15:24 - INFO - Log - Dataframe Kafka criado com sucesso para tópicos: sinesp_ocorrencias_municipio,sinesp_ocorrencias_estado,sinesp_ocorrencias_geral
2025-11-03 10:15:25 - INFO - Log - Streaming iniciado. Aguardando dados de segurança pública...
2025-11-03 10:15:30 - INFO - Log - Processando batch 0 com 10 registros
2025-11-03 10:15:31 - INFO - Log - Dados inseridos: abc123 - São Paulo/SP - homicidio_doloso - 25 ocorrências
```

### Logs de Erro

```
2025-11-03 10:20:15 - ERROR - Log - Os dados não podem ser inseridos devido ao erro: InvalidRequest...
2025-11-03 10:20:15 - ERROR - Log - Esta é a query:
INSERT INTO dados_seguranca_publica.tb_ocorrencias_municipio...
```

---

## Dependências Python

Certifique-se que o ambiente possui:

```python
pyspark
cassandra-driver
kafka-python
```

---

## Configurações Docker

### Variáveis de Ambiente Necessárias

| Variável | Valor Padrão | Descrição |
|----------|--------------|-----------|
| KAFKA_BROKER | `broker:29092` | Endereço do broker Kafka |
| CASSANDRA_HOST | `cassandra` | Host do Cassandra |
| CASSANDRA_PORT | `9042` | Porta do Cassandra |
| SPARK_MASTER | `spark://spark-master:7077` | URL do Spark Master |

### Volumes Necessários

Nenhum volume adicional é necessário para o consumer.

### Rede Docker

Todos os containers devem estar na mesma rede Docker para comunicação.

---

## Troubleshooting

### Problema: Consumer não se conecta ao Kafka

**Solução**:
1. Verifique se o broker Kafka está rodando: `docker ps | grep broker`
2. Teste conectividade: `telnet broker 29092`
3. Verifique logs do Kafka

### Problema: Dados não aparecem no Cassandra

**Solução**:
1. Verifique se o keyspace foi criado: `DESCRIBE KEYSPACES;`
2. Verifique se as tabelas existem: `DESCRIBE TABLES;`
3. Verifique logs do consumer por erros de inserção

### Problema: Schema mismatch

**Solução**:
1. Certifique-se que o producer está enviando todos os campos esperados
2. Verifique se há campos `null` sendo enviados
3. Ajuste o schema para permitir campos nullable

---

## Melhorias Futuras

### Curto Prazo

1. **Validação de Dados**:
   - Implementar validação de tipos (converter strings numéricas para INT)
   - Rejeitar registros com dados inválidos

2. **Batch Size Otimizado**:
   - Configurar tamanho ótimo de batch para performance
   - Implementar backpressure

### Médio Prazo

3. **Índices Secundários**:
   - Criar índices no Cassandra para queries frequentes
   - Otimizar consultas por UF, ano, tipo_crime

4. **Agregações em Tempo Real**:
   - Calcular totais por estado/município
   - Manter tabelas de agregação atualizadas

5. **Checkpoint e Recovery**:
   - Implementar checkpointing do Spark Streaming
   - Permitir recovery após falhas

### Longo Prazo

6. **Data Lake**:
   - Salvar dados brutos em formato Parquet/ORC
   - Manter histórico completo para análises

7. **API de Consulta**:
   - Criar API REST para consultas aos dados
   - Implementar cache com Redis

8. **Dashboard em Tempo Real**:
   - Integrar com Grafana/Kibana
   - Visualizações de crimes por região/período

---

## Referências

- **Apache Spark Structured Streaming**: https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html
- **Cassandra Python Driver**: https://docs.datastax.com/en/developer/python-driver/
- **Kafka Python**: https://kafka-python.readthedocs.io/

---

**Autor**: Claude (Anthropic)
**Última Atualização**: 03/11/2025
**Status**: Implementado e Testável
