# Guia de Execução - ETL Real-Time Segurança Pública

**Data**: 03/11/2025
**Versão**: 2.0 (Adaptado para dados SINESP)

---

## Visão Geral do Sistema

Este projeto implementa um pipeline ETL em tempo real para processar dados de segurança pública do SINESP (Sistema Nacional de Estatísticas de Segurança Pública).

### Arquitetura

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│              │     │              │     │              │     │              │
│   Airflow    │────>│    Kafka     │────>│    Spark     │────>│  Cassandra   │
│   (DAG)      │     │   (Broker)   │     │  Streaming   │     │   (NoSQL)    │
│              │     │              │     │              │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
  kafka_stream.py         3 Tópicos       consumer_stream.py     3 Tabelas
```

### Componentes

| Componente | Função | Arquivo |
|------------|--------|---------|
| **Producer** | Extrai dados da API dados.gov.br e envia para Kafka | [kafka_stream.py](../servidor/dags/kafka_stream.py) |
| **Kafka** | Message broker - 3 tópicos | broker:29092 |
| **Consumer** | Consome dados do Kafka e persiste no Cassandra | [consumer_stream.py](../cliente/consumer_stream.py) |
| **Cassandra** | Banco de dados NoSQL - 3 tabelas | cassandra:9042 |
| **Airflow** | Orquestrador da DAG | localhost:8080 |
| **Spark** | Processamento distribuído | spark-master:7077 |

---

## Pré-requisitos

### Software Necessário

- Docker Desktop instalado e rodando
- Docker Compose versão 1.27+
- Mínimo 8GB RAM disponível
- 10GB espaço em disco

### Portas Necessárias

Certifique-se que as seguintes portas estão livres:

| Porta | Serviço |
|-------|---------|
| 8080 | Airflow UI |
| 9042 | Cassandra |
| 29092 | Kafka (interno) |
| 9092 | Kafka (externo) |
| 7077 | Spark Master |
| 8081 | Spark UI |

---

## Passo 1: Preparar o Ambiente

### 1.1 Clone ou navegue até o diretório do projeto

```bash
cd c:\Dev\Engenharia-Dados\ETL-Real-Time
```

### 1.2 Verifique a estrutura de arquivos

```
ETL-Real-Time/
├── servidor/
│   └── dags/
│       └── kafka_stream.py          # Producer
├── cliente/
│   └── consumer_stream.py            # Consumer
├── Docs/
│   ├── Informações-Disponíveis.md
│   ├── Alterações-Implementadas.md
│   ├── Consumer-Alterações.md
│   └── Guia-Execução.md (este arquivo)
└── docker-compose.yml                # Configuração Docker
```

### 1.3 Verifique o arquivo docker-compose.yml

O arquivo deve conter serviços para:
- Zookeeper
- Kafka Broker
- Cassandra
- Spark (Master e Worker)
- Airflow (Webserver e Scheduler)

---

## Passo 2: Iniciar os Containers Docker

### 2.1 Iniciar todos os serviços

```bash
docker-compose up -d
```

**Tempo estimado**: 2-5 minutos para todos os containers iniciarem

### 2.2 Verificar status dos containers

```bash
docker-compose ps
```

**Saída esperada**:
```
NAME                STATUS              PORTS
broker              Up                  0.0.0.0:9092->9092/tcp
cassandra           Up                  0.0.0.0:9042->9042/tcp
zookeeper           Up                  2181/tcp
spark-master        Up                  0.0.0.0:7077->7077/tcp
spark-worker        Up
airflow-webserver   Up                  0.0.0.0:8080->8080/tcp
airflow-scheduler   Up
```

### 2.3 Verificar logs (opcional)

```bash
# Ver logs de todos os serviços
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f broker
docker-compose logs -f cassandra
docker-compose logs -f airflow-scheduler
```

**Pressione `Ctrl+C` para sair dos logs**

---

## Passo 3: Configurar o Cassandra

### 3.1 Acessar o container do Cassandra

```bash
docker exec -it cassandra cqlsh
```

### 3.2 Verificar se o keyspace foi criado

```sql
DESCRIBE KEYSPACES;
```

**Se `dados_seguranca_publica` não aparecer**, será criado automaticamente quando o consumer iniciar.

### 3.3 (Opcional) Criar keyspace e tabelas manualmente

```sql
CREATE KEYSPACE IF NOT EXISTS dados_seguranca_publica
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'};

USE dados_seguranca_publica;

-- As tabelas serão criadas automaticamente pelo consumer
```

### 3.4 Sair do CQL Shell

```sql
exit;
```

---

## Passo 4: Configurar o Kafka

### 4.1 Verificar se o Kafka está rodando

```bash
docker exec -it broker kafka-topics --list --bootstrap-server localhost:9092
```

### 4.2 (Opcional) Criar os tópicos manualmente

Os tópicos serão criados automaticamente quando o producer enviar dados, mas você pode criá-los previamente:

```bash
# Criar tópico para municípios
docker exec -it broker kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --replication-factor 1 \
  --partitions 3 \
  --topic sinesp_ocorrencias_municipio

# Criar tópico para estados
docker exec -it broker kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --replication-factor 1 \
  --partitions 3 \
  --topic sinesp_ocorrencias_estado

# Criar tópico geral
docker exec -it broker kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --replication-factor 1 \
  --partitions 3 \
  --topic sinesp_ocorrencias_geral
```

### 4.3 Verificar tópicos criados

```bash
docker exec -it broker kafka-topics --list --bootstrap-server localhost:9092
```

**Saída esperada**:
```
sinesp_ocorrencias_municipio
sinesp_ocorrencias_estado
sinesp_ocorrencias_geral
```

---

## Passo 5: Executar o Producer (Airflow DAG)

### 5.1 Acessar a UI do Airflow

Abra o navegador e acesse:
```
http://localhost:8080
```

**Credenciais**:
- Username: `admin`
- Password: Configurada no arquivo `servidor/entrypoint/entrypoint.sh`

### 5.2 Localizar a DAG

Procure pela DAG chamada: **`real-time-etl-stack`**

### 5.3 Ativar a DAG

1. Encontre a DAG na lista
2. Clique no toggle à esquerda para ativar
3. A DAG está configurada para rodar uma vez por dia (`schedule=timedelta(days=1)`)

### 5.4 Executar manualmente (Trigger)

Para testar imediatamente:

1. Clique no nome da DAG: `real-time-etl-stack`
2. Clique no botão **"Trigger DAG"** (ícone de play ▶)
3. Confirme a execução

### 5.5 Monitorar a execução

1. Clique na DAG
2. Vá para a aba **"Graph"** para ver o progresso visual
3. Ou vá para **"Logs"** para ver detalhes

**Logs esperados**:
```
Log - Produtor Kafka conectado com sucesso.
Log - 10 registros de segurança pública enviados para tópico 'sinesp_ocorrencias_municipio'. Total: 10
Log - 10 registros de segurança pública enviados para tópico 'sinesp_ocorrencias_municipio'. Total: 20
...
Log - Streaming finalizado. Total de registros enviados: 60
```

---

## Passo 6: Executar o Consumer (Spark Streaming)

### 6.1 Acessar o container do Spark

```bash
docker exec -it spark-master bash
```

### 6.2 Navegar até o diretório do consumer

```bash
cd /opt/bitnami/spark/work-dir/cliente
```

### 6.3 Executar o consumer

**Modo Initial** (processa todos os dados desde o início):
```bash
spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,com.datastax.spark:spark-cassandra-connector_2.12:3.4.1 \
  consumer_stream.py --mode initial
```

**Modo Append** (processa apenas novos dados):
```bash
spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,com.datastax.spark:spark-cassandra-connector_2.12:3.4.1 \
  consumer_stream.py --mode append
```

### 6.4 Monitorar os logs

**Logs esperados**:
```
INFO - Log - Spark Connection criada com sucesso!
INFO - Keyspace criado com sucesso!
INFO - Tabelas criadas com sucesso!
INFO - Log - Dataframe Kafka criado com sucesso para tópicos: sinesp_ocorrencias_municipio,sinesp_ocorrencias_estado,sinesp_ocorrencias_geral
INFO - Log - Streaming iniciado. Aguardando dados de segurança pública...
INFO - Log - Processando batch 0 com 10 registros
INFO - Log - Dados inseridos: abc123 - São Paulo/SP - homicidio_doloso - 25 ocorrências
```

**Observação**: O consumer ficará rodando continuamente. Pressione `Ctrl+C` para parar.

---

## Passo 7: Verificar os Dados no Cassandra

### 7.1 Acessar o CQL Shell

```bash
docker exec -it cassandra cqlsh
```

### 7.2 Usar o keyspace

```sql
USE dados_seguranca_publica;
```

### 7.3 Verificar as tabelas

```sql
DESCRIBE TABLES;
```

**Saída esperada**:
```
tb_ocorrencias_municipio  tb_ocorrencias_estado  tb_ocorrencias_geral
```

### 7.4 Consultar dados

**Ver registros de municípios**:
```sql
SELECT * FROM tb_ocorrencias_municipio LIMIT 10;
```

**Ver registros de estados**:
```sql
SELECT * FROM tb_ocorrencias_estado LIMIT 10;
```

**Contar registros**:
```sql
SELECT COUNT(*) FROM tb_ocorrencias_municipio;
SELECT COUNT(*) FROM tb_ocorrencias_estado;
SELECT COUNT(*) FROM tb_ocorrencias_geral;
```

**Consultas específicas**:
```sql
-- Ocorrências em São Paulo
SELECT municipio, tipo_crime, ocorrencias
FROM tb_ocorrencias_municipio
WHERE uf = 'SP' ALLOW FILTERING;

-- Homicídios por estado
SELECT uf, homicidio_doloso
FROM tb_ocorrencias_estado
WHERE homicidio_doloso != '' ALLOW FILTERING;
```

### 7.5 Sair do CQL Shell

```sql
exit;
```

---

## Passo 8: Monitoramento e Debug

### 8.1 Monitorar tópicos Kafka

**Ver mensagens em tempo real**:
```bash
# Tópico municípios
docker exec -it broker kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic sinesp_ocorrencias_municipio \
  --from-beginning

# Tópico estados
docker exec -it broker kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic sinesp_ocorrencias_estado \
  --from-beginning
```

**Pressione `Ctrl+C` para sair**

### 8.2 Acessar Spark UI

Abra o navegador:
```
http://localhost:8081
```

Aqui você pode ver:
- Jobs em execução
- Estágios de processamento
- Executors ativos
- Métricas de performance

### 8.3 Ver logs do Airflow

```bash
# Logs do scheduler
docker-compose logs -f airflow-scheduler

# Logs do webserver
docker-compose logs -f airflow-webserver
```

### 8.4 Ver logs do Spark

```bash
docker-compose logs -f spark-master
docker-compose logs -f spark-worker
```

---

## Troubleshooting

### Problema 1: Producer não envia dados

**Sintomas**:
- DAG executa mas não há mensagens no Kafka
- Logs mostram "Nenhum dado de segurança pública encontrado"

**Soluções**:
1. Verifique conectividade com a API:
   ```bash
   curl "https://dados.gov.br/api/3/action/package_show?id=sistema-nacional-de-estatisticas-de-seguranca-publica"
   ```

2. Verifique se o Kafka está acessível:
   ```bash
   docker exec -it broker kafka-broker-api-versions --bootstrap-server localhost:9092
   ```

3. Verifique logs do Airflow para erros Python

---

### Problema 2: Consumer não se conecta ao Kafka

**Sintomas**:
- Consumer inicia mas não processa dados
- Erro: "Failed to connect to broker"

**Soluções**:
1. Verifique se os tópicos existem:
   ```bash
   docker exec -it broker kafka-topics --list --bootstrap-server localhost:9092
   ```

2. Verifique se há mensagens nos tópicos:
   ```bash
   docker exec -it broker kafka-run-class kafka.tools.GetOffsetShell \
     --broker-list localhost:9092 \
     --topic sinesp_ocorrencias_municipio
   ```

3. Reinicie o Kafka:
   ```bash
   docker-compose restart broker
   ```

---

### Problema 3: Dados não aparecem no Cassandra

**Sintomas**:
- Consumer processa batches
- Logs mostram "Dados inseridos"
- Mas SELECT retorna vazio

**Soluções**:
1. Verifique se as tabelas foram criadas:
   ```sql
   DESCRIBE TABLES;
   ```

2. Verifique erros de inserção nos logs do consumer

3. Verifique se o schema está correto:
   ```sql
   DESCRIBE TABLE tb_ocorrencias_municipio;
   ```

4. Tente inserir dados manualmente:
   ```sql
   INSERT INTO tb_ocorrencias_municipio (id, uf, municipio, ocorrencias)
   VALUES ('test-123', 'SP', 'São Paulo', '100');

   SELECT * FROM tb_ocorrencias_municipio WHERE id = 'test-123';
   ```

---

### Problema 4: Schema mismatch

**Sintomas**:
- Erro: "Field 'campo_x' does not exist"
- Consumer trava ao processar

**Soluções**:
1. Verifique o schema no consumer_stream.py (linhas 283-310)
2. Verifique o schema no kafka_stream.py (estrutura do dicionário `data`)
3. Certifique-se que todos os campos estão sendo enviados
4. Use campos nullable (`True`) para flexibilidade

---

## Parar o Sistema

### Parar apenas o consumer

Se estiver rodando em terminal:
```
Ctrl+C
```

### Parar todos os containers

```bash
docker-compose down
```

### Parar e remover volumes (limpar tudo)

**⚠️ CUIDADO: Isso apagará todos os dados!**

```bash
docker-compose down -v
```

---

## Próximos Passos

### Análise de Dados

1. **Exportar dados do Cassandra**:
   ```bash
   docker exec cassandra cqlsh -e "COPY dados_seguranca_publica.tb_ocorrencias_municipio TO '/tmp/municipios.csv' WITH HEADER=TRUE"
   ```

2. **Análise com Python/Pandas**:
   ```python
   import pandas as pd
   from cassandra.cluster import Cluster

   cluster = Cluster(['localhost'])
   session = cluster.connect('dados_seguranca_publica')

   rows = session.execute('SELECT * FROM tb_ocorrencias_municipio')
   df = pd.DataFrame(list(rows))
   ```

3. **Visualização com BI Tools**:
   - Tableau
   - Power BI
   - Apache Superset

### Melhorias no Pipeline

1. **Aumentar frequência da DAG**:
   ```python
   # Em kafka_stream.py
   schedule=timedelta(hours=1)  # Rodar a cada hora
   ```

2. **Processar mais dados por batch**:
   ```python
   # Em kafka_stream.py, linha 96
   if i >= 100:  # Aumentar de 10 para 100
   ```

3. **Adicionar mais recursos CSV**:
   - Processar dados de estados
   - Processar dados históricos

---

## Recursos Adicionais

### Documentação

- [Informações Disponíveis](Informações-Disponíveis.md) - Datasets de segurança pública
- [Alterações no Producer](Alterações-Implementadas.md) - Detalhes do kafka_stream.py
- [Alterações no Consumer](Consumer-Alterações.md) - Detalhes do consumer_stream.py

### Links Úteis

- Portal Dados Abertos: https://dados.gov.br
- Dataset SINESP: https://dados.gov.br/dataset/sistema-nacional-de-estatisticas-de-seguranca-publica
- Airflow Docs: https://airflow.apache.org/docs/
- Spark Streaming: https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html
- Cassandra CQL: https://cassandra.apache.org/doc/latest/cql/

---

## Suporte

Para problemas ou dúvidas:
1. Verifique a seção de Troubleshooting acima
2. Consulte os logs dos containers
3. Revise a documentação técnica nos arquivos `Docs/`

---

**Última Atualização**: 03/11/2025
**Versão**: 2.0
**Status**: Pronto para Produção
