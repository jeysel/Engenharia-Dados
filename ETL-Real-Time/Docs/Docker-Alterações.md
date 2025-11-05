# Alterações nos Arquivos Docker

**Data**: 03/11/2025
**Objetivo**: Adicionar serviço consumer automatizado e otimizar configuração Docker

---

## Resumo das Alterações

Foram realizadas alterações significativas na configuração Docker para automatizar completamente o pipeline ETL, incluindo a adição de um serviço dedicado para o Spark Consumer que processa dados do Kafka automaticamente.

---

## Arquivos Modificados

### 1. docker-compose.yml

**Localização**: [servidor/docker-compose.yml](../servidor/docker-compose.yml)

#### Alterações Realizadas

##### A. Healthcheck no Cassandra (Linhas 185-189)

**Adicionado**:
```yaml
healthcheck:
  test: ["CMD-SHELL", "cqlsh -e 'describe cluster'"]
  interval: 30s
  timeout: 10s
  retries: 5
```

**Razão**:
- Permite que outros serviços aguardem o Cassandra estar completamente pronto
- Evita erros de conexão do consumer ao tentar conectar antes do Cassandra estar disponível
- Testa conectividade através do cqlsh

---

##### B. Novo Serviço: spark-consumer (Linhas 191-226)

**Serviço Completo Adicionado**:

```yaml
spark-consumer:
  build:
    context: ../cliente
    dockerfile: Dockerfile
  container_name: spark-consumer
  depends_on:
    broker:
      condition: service_healthy
    cassandra_db:
      condition: service_healthy
    spark-master:
      condition: service_started
  environment:
    - SPARK_MASTER_URL=spark://spark-master:7077
    - KAFKA_BOOTSTRAP_SERVERS=broker:29092
    - CASSANDRA_HOST=cassandra
    - CASSANDRA_PORT=9042
  volumes:
    - ../cliente/consumer_stream.py:/app/consumer_stream.py
  networks:
    - engdados
  command: >
    bash -c "
    echo 'Aguardando inicialização dos serviços...' &&
    sleep 30 &&
    echo 'Iniciando consumer Spark Streaming...' &&
    spark-submit
      --master spark://spark-master:7077
      --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.4,com.datastax.spark:spark-cassandra-connector_2.12:3.5.1
      --conf spark.cassandra.connection.host=cassandra
      --conf spark.cassandra.connection.port=9042
      --conf spark.executor.memory=1g
      --conf spark.executor.cores=1
      --conf spark.cores.max=2
      /app/consumer_stream.py --mode append
    "
```

#### Detalhamento das Configurações

**Build**:
- `context: ../cliente` - Usa o diretório cliente como contexto de build
- `dockerfile: Dockerfile` - Usa o Dockerfile personalizado

**Dependências**:
- `broker: condition: service_healthy` - Aguarda Kafka estar saudável
- `cassandra_db: condition: service_healthy` - Aguarda Cassandra estar saudável
- `spark-master: condition: service_started` - Aguarda Spark Master iniciar

**Variáveis de Ambiente**:
| Variável | Valor | Descrição |
|----------|-------|-----------|
| `SPARK_MASTER_URL` | `spark://spark-master:7077` | URL do Spark Master |
| `KAFKA_BOOTSTRAP_SERVERS` | `broker:29092` | Servidor Kafka |
| `CASSANDRA_HOST` | `cassandra` | Host do Cassandra |
| `CASSANDRA_PORT` | `9042` | Porta do Cassandra |

**Volumes**:
- `../cliente/consumer_stream.py:/app/consumer_stream.py` - Monta o script consumer para hot-reload

**Comando de Inicialização**:

1. **Aguarda 30 segundos** para garantir que todos os serviços estejam estáveis
2. **Executa spark-submit** com as seguintes configurações:

**Parâmetros do spark-submit**:
- `--master spark://spark-master:7077` - Conecta ao Spark Master
- `--packages` - Baixa dependências automaticamente:
  - `spark-sql-kafka-0-10_2.12:3.5.4` - Conector Kafka para Spark
  - `spark-cassandra-connector_2.12:3.5.1` - Conector Cassandra para Spark
- `--conf spark.cassandra.connection.host=cassandra` - Configura host Cassandra
- `--conf spark.cassandra.connection.port=9042` - Configura porta Cassandra
- `--conf spark.executor.memory=1g` - Memória do executor
- `--conf spark.executor.cores=1` - Cores por executor
- `--conf spark.cores.max=2` - Máximo de cores totais
- `/app/consumer_stream.py --mode append` - Script e modo de execução

---

### 2. Dockerfile (Cliente)

**Localização**: [cliente/Dockerfile](../cliente/Dockerfile)

#### Alterações Completas

##### Antes:
```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    openjdk-17-jre \
    curl && \
    apt-get clean

RUN pip install pyspark==3.5.4 kafka-python==2.0.2 cassandra-driver==3.29.2

COPY consumer_stream.py /app/consumer_stream.py

WORKDIR /app
```

**Problemas**:
- Imagem base genérica sem Spark configurado
- Necessita instalação manual de Java e Spark
- Maior tamanho de imagem
- Mais propenso a erros de configuração

##### Depois:
```dockerfile
# Usa imagem oficial do Bitnami Spark que já tem tudo configurado
FROM bitnami/spark:3.5.4

# Muda para usuário root para instalar dependências
USER root

# Instala dependências Python adicionais necessárias para o consumer
RUN pip install --no-cache-dir \
    kafka-python==2.0.2 \
    cassandra-driver==3.29.2

# Cria diretório de trabalho
RUN mkdir -p /app

# Copia o script consumer para o container
COPY consumer_stream.py /app/consumer_stream.py

# Define permissões corretas
RUN chown -R 1001:1001 /app

# Volta para o usuário padrão do Spark
USER 1001

# Configura diretório de trabalho
WORKDIR /app

# Define variáveis de ambiente
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

# Comando padrão (será sobrescrito pelo docker-compose)
CMD ["spark-submit", "--help"]
```

**Vantagens**:
- ✅ Imagem base oficial do Bitnami com Spark já configurado
- ✅ Java e Spark pré-instalados e otimizados
- ✅ Menor tamanho de imagem
- ✅ Configurações de segurança com usuário não-root (1001)
- ✅ Variáveis de ambiente corretas para PySpark
- ✅ Apenas dependências Python adicionais necessárias

#### Detalhamento das Mudanças

**Imagem Base**:
- `FROM bitnami/spark:3.5.4` - Versão compatível com o Spark Master

**Instalação de Dependências**:
- `kafka-python==2.0.2` - Cliente Kafka para Python
- `cassandra-driver==3.29.2` - Driver Cassandra para Python
- `--no-cache-dir` - Reduz tamanho da imagem

**Segurança**:
- Operações como root apenas quando necessário
- Retorna para usuário `1001` (padrão Bitnami)
- Permissões corretas nos arquivos (`chown -R 1001:1001 /app`)

**Variáveis de Ambiente**:
- `PYSPARK_PYTHON=python3` - Define Python 3 para o PySpark
- `PYSPARK_DRIVER_PYTHON=python3` - Define Python 3 para o driver

---

## Diagrama de Arquitetura Atualizado

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Docker Network: engdados                        │
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │
│  │   Zookeeper  │    │    Kafka     │    │    Schema    │             │
│  │              │◄──►│   (Broker)   │◄──►│   Registry   │             │
│  │              │    │  :29092      │    │   :8081      │             │
│  └──────────────┘    └──────┬───────┘    └──────────────┘             │
│                             │                                           │
│  ┌──────────────┐           │                                           │
│  │  Control     │           │                                           │
│  │  Center      │◄──────────┘                                           │
│  │  :9021       │                                                       │
│  └──────────────┘                                                       │
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐                                  │
│  │  PostgreSQL  │    │   Airflow    │                                  │
│  │              │◄──►│  Webserver   │                                  │
│  │   :5432      │    │   :8080      │                                  │
│  └──────────────┘    └──────┬───────┘                                  │
│                             │                                           │
│                      ┌──────▼───────┐                                  │
│                      │   Airflow    │                                  │
│                      │  Scheduler   │                                  │
│                      └──────┬───────┘                                  │
│                             │                                           │
│                             ▼                                           │
│                      ┌──────────────┐                                  │
│                      │ Producer DAG │                                  │
│                      │kafka_stream  │                                  │
│                      └──────┬───────┘                                  │
│                             │                                           │
│                             ▼                                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │
│  │ Spark Master │    │    Kafka     │    │Spark Consumer│             │
│  │   :7077      │◄──►│   Topics     │──►│  (NOVO)      │             │
│  │   :8080      │    │  - municipio │    │              │             │
│  └──────┬───────┘    │  - estado    │    └──────┬───────┘             │
│         │            │  - geral     │           │                      │
│  ┌──────▼───────┐    └──────────────┘           │                      │
│  │ Spark Worker │                               │                      │
│  │              │                               │                      │
│  └──────────────┘                               ▼                      │
│                                          ┌──────────────┐              │
│                                          │  Cassandra   │              │
│                                          │   :9042      │              │
│                                          │              │              │
│                                          │ 3 Tabelas:   │              │
│                                          │ - municipio  │              │
│                                          │ - estado     │              │
│                                          │ - geral      │              │
│                                          └──────────────┘              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Fluxo de Inicialização

### Ordem de Inicialização

1. **Postgres** - Banco de dados do Airflow
2. **Broker (Kafka)** - Message broker (aguarda healthcheck)
3. **Schema Registry** - Registro de schemas Kafka
4. **Control Center** - UI de monitoramento Kafka
5. **Cassandra** - Banco NoSQL (aguarda healthcheck)
6. **Spark Master** - Coordenador Spark
7. **Spark Worker** - Executor Spark
8. **Airflow Webserver** - UI do Airflow
9. **Airflow Scheduler** - Agendador de DAGs
10. **Spark Consumer** (NOVO) - Processa dados automaticamente

### Healthchecks

| Serviço | Healthcheck | Intervalo |
|---------|-------------|-----------|
| Kafka | `nc -z localhost 9092` | 20s |
| Schema Registry | `curl http://localhost:8081/` | 30s |
| Control Center | `curl http://localhost:9021/health` | 30s |
| Cassandra | `cqlsh -e 'describe cluster'` | 30s |
| Airflow | `[ -f /opt/airflow/airflow-webserver.pid ]` | 30s |

---

## Comandos Docker Úteis

### Iniciar Todo o Sistema

```bash
cd servidor
docker-compose up -d
```

### Ver Logs do Consumer

```bash
docker logs -f spark-consumer
```

### Ver Status de Todos os Containers

```bash
docker-compose ps
```

### Reiniciar Apenas o Consumer

```bash
docker-compose restart spark-consumer
```

### Parar o Consumer

```bash
docker-compose stop spark-consumer
```

### Rebuild do Consumer (após alterações no código)

```bash
docker-compose up -d --build spark-consumer
```

### Ver Logs de Todos os Serviços

```bash
docker-compose logs -f
```

### Executar comandos dentro do Consumer

```bash
docker exec -it spark-consumer bash
```

---

## Variáveis de Ambiente Disponíveis

### No Consumer (spark-consumer)

| Variável | Valor | Uso |
|----------|-------|-----|
| `SPARK_MASTER_URL` | `spark://spark-master:7077` | Conexão com Spark Master |
| `KAFKA_BOOTSTRAP_SERVERS` | `broker:29092` | Servidores Kafka |
| `CASSANDRA_HOST` | `cassandra` | Host Cassandra |
| `CASSANDRA_PORT` | `9042` | Porta Cassandra |
| `PYSPARK_PYTHON` | `python3` | Interpretador Python |
| `PYSPARK_DRIVER_PYTHON` | `python3` | Driver Python |

---

## Volumes Montados

### Airflow

```yaml
volumes:
  - ./dags:/opt/airflow/dags                           # DAGs
  - ./entrypoint/entrypoint.sh:/opt/airflow/script/entrypoint.sh  # Script inicialização
  - ./requirements.txt:/opt/airflow/requirements.txt   # Dependências Python
```

### Spark Consumer

```yaml
volumes:
  - ../cliente/consumer_stream.py:/app/consumer_stream.py  # Script consumer (hot-reload)
```

**Vantagem do Volume**: Permite alterar o código do consumer sem rebuild da imagem Docker!

---

## Troubleshooting

### Consumer não inicia

**Verificar logs**:
```bash
docker logs spark-consumer
```

**Causas comuns**:
1. Kafka não está healthy - Verificar: `docker-compose ps`
2. Cassandra não está healthy - Verificar: `docker logs cassandra`
3. Spark Master não iniciou - Verificar: `docker logs spark-master`

**Solução**: Aguardar healthchecks passarem ou reiniciar:
```bash
docker-compose restart broker cassandra_db spark-master
docker-compose up -d spark-consumer
```

---

### Consumer trava ao conectar

**Sintoma**: Consumer inicia mas não processa dados

**Verificar conectividade**:
```bash
# Entrar no container
docker exec -it spark-consumer bash

# Testar Kafka
telnet broker 29092

# Testar Cassandra
nc -zv cassandra 9042
```

---

### Pacotes Spark não baixam

**Sintoma**: Erro "Could not find artifact"

**Solução**: Verificar conectividade com Maven Central:
```bash
docker exec -it spark-consumer bash
ping repo1.maven.org
```

Se não houver conectividade, configure proxy ou use packages locais.

---

### Memória insuficiente

**Sintoma**: OOM (Out of Memory) errors

**Solução 1**: Reduzir configurações no docker-compose:
```yaml
--conf spark.executor.memory=512m
--conf spark.cores.max=1
```

**Solução 2**: Aumentar memória disponível no Docker Desktop:
- Settings → Resources → Memory → Aumentar para 8GB+

---

## Melhorias Futuras

### Curto Prazo

1. **Modo de Execução Configurável**:
   ```yaml
   environment:
     - CONSUMER_MODE=append  # ou initial
   ```

2. **Configuração de Tópicos Dinâmica**:
   ```yaml
   environment:
     - KAFKA_TOPICS=sinesp_ocorrencias_municipio,sinesp_ocorrencias_estado
   ```

### Médio Prazo

3. **Multi-Consumer**:
   - Um consumer para cada tópico
   - Processamento paralelo

4. **Auto-scaling**:
   - Escalar consumers baseado na carga

5. **Checkpointing**:
   - Persistir estado do streaming
   - Recovery automático

### Longo Prazo

6. **Kubernetes**:
   - Migrar para K8s para produção
   - Helm charts

7. **Monitoring Stack**:
   - Prometheus + Grafana
   - Alertas automáticos

---

## Recursos Computacionais

### Requisitos Mínimos

| Componente | CPU | RAM | Disco |
|------------|-----|-----|-------|
| Kafka | 1 core | 1GB | 10GB |
| Cassandra | 2 cores | 2GB | 20GB |
| Spark Master | 1 core | 1GB | 5GB |
| Spark Worker | 2 cores | 2GB | 5GB |
| Spark Consumer | 2 cores | 2GB | 2GB |
| Airflow | 2 cores | 2GB | 5GB |
| **Total** | **10 cores** | **10GB** | **47GB** |

### Recomendado

| Recurso | Valor |
|---------|-------|
| CPU | 12+ cores |
| RAM | 16GB |
| Disco | 100GB SSD |
| Docker Memory Limit | 12GB |

---

## Referências

- **Bitnami Spark**: https://hub.docker.com/r/bitnami/spark
- **Docker Compose**: https://docs.docker.com/compose/
- **Spark Submit**: https://spark.apache.org/docs/latest/submitting-applications.html
- **Healthchecks**: https://docs.docker.com/compose/compose-file/compose-file-v3/#healthcheck

---

**Autor**: Claude (Anthropic)
**Última Atualização**: 03/11/2025
**Status**: Pronto para Deploy
