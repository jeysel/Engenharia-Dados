# ETL Real-Time - Segurança Pública SINESP

Pipeline ETL em tempo real para processamento de dados de segurança pública do Brasil usando Apache Airflow, Kafka, Spark Streaming e Cassandra.

![Version](https://img.shields.io/badge/version-2.0-blue)
![Python](https://img.shields.io/badge/python-3.11-green)
![Spark](https://img.shields.io/badge/spark-3.5.4-orange)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Funcionalidades](#funcionalidades)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Uso](#uso)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Documentação](#documentação)
- [Monitoramento](#monitoramento)
- [Troubleshooting](#troubleshooting)
- [Contribuição](#contribuição)
- [Licença](#licença)

---

## 🎯 Visão Geral

Este projeto implementa um pipeline ETL (Extract, Transform, Load) em tempo real para processar dados de ocorrências criminais do **SINESP** (Sistema Nacional de Estatísticas de Segurança Pública) disponibilizados através do Portal Brasileiro de Dados Abertos.

### O que o Sistema Faz?

1. **Extrai** dados de segurança pública da API dados.gov.br
2. **Processa** em tempo real usando Apache Spark
3. **Armazena** no Cassandra para análises
4. **Orquestra** todo o pipeline com Apache Airflow

### Dados Processados

- ✅ Homicídios dolosos
- ✅ Roubos (veículos, carga, instituições financeiras)
- ✅ Furtos de veículos
- ✅ Latrocínios
- ✅ Estupros
- ✅ Lesões corporais seguidas de morte

**Granularidade**: Dados disponíveis por município e por estado.

---

## 🏗️ Arquitetura

### Stack Tecnológico

| Componente | Tecnologia | Versão | Função |
|------------|-----------|---------|--------|
| **Orquestração** | Apache Airflow | 2.10.4 | Agendamento de DAGs |
| **Message Broker** | Apache Kafka | 3.9.0 | Streaming de mensagens |
| **Processamento** | Apache Spark | 3.5.4 | Processamento distribuído |
| **Armazenamento** | Apache Cassandra | 5.0.2 | Banco de dados NoSQL |
| **Containerização** | Docker | - | Isolamento de serviços |
| **Linguagem** | Python | 3.11 | Desenvolvimento |

---

## 🚀 Instalação

### 1. Clone o Repositório

```bash
git clone <url-do-repositorio>
cd ETL-Real-Time
```

### 2. Verifique a Estrutura


### 3. Inicie os Containers

```bash
cd servidor
docker-compose up -d
```

**Tempo de inicialização**: ~5 minutos

### 4. Verifique o Status

```bash
docker-compose ps
```

**Todos os serviços devem estar "Up"**

---

## 💻 Uso

### Acesso às Interfaces

#### Airflow UI
- **URL**: http://localhost:8080
- **Usuário**: `admin`
- **Senha**: Configurada no entrypoint do Airflow (ver arquivo `servidor/entrypoint/entrypoint.sh`)

#### Kafka Control Center
- **URL**: http://localhost:9021

#### Spark Master UI
- **URL**: http://localhost:9090

### Executar o Pipeline

#### 1. Via Airflow UI

1. Acesse http://localhost:8080
2. Localize a DAG `real-time-etl-stack`
3. Ative o toggle
4. Clique em "Trigger DAG"

#### 2. Via Linha de Comando

```bash
# Trigger manual da DAG
docker exec -it <airflow-scheduler-container> \
  airflow dags trigger real-time-etl-stack
```

### Monitorar Processamento

#### Ver Logs do Producer (Airflow)

```bash
docker-compose logs -f scheduler
```

#### Ver Logs do Consumer (Spark)

```bash
docker logs -f spark-consumer
```

#### Verificar Dados no Cassandra

```bash
# Acessar CQL Shell
docker exec -it cassandra cqlsh

# Executar queries
USE dados_seguranca_publica;
SELECT COUNT(*) FROM tb_ocorrencias_municipio;
SELECT * FROM tb_ocorrencias_municipio LIMIT 10;
```

---

### Arquivos Principais

| Arquivo | Descrição |
|---------|-----------|
| `kafka_stream.py` | Producer - Extrai dados da API e envia para Kafka |
| `consumer_stream.py` | Consumer - Processa dados e persiste no Cassandra |
| `docker-compose.yml` | Define todos os serviços Docker |
| `Dockerfile` | Imagem Docker do Consumer |
| `requirements.txt` | Dependências Python do Airflow |

---

## 📊 Monitoramento

### Kafka Control Center

Acesse http://localhost:9021 para:
- 📈 Monitorar tópicos e throughput
- 📊 Ver consumers e lag
- 🔍 Inspecionar mensagens
- ⚙️ Gerenciar configurações

### Spark UI

Acesse http://localhost:9090 para:
- 📊 Ver jobs em execução
- 📈 Métricas de performance
- 🔍 Logs de executors
- ⏱️ Timeline de execução

### Logs

```bash
# Todos os serviços
docker-compose logs -f

# Serviço específico
docker-compose logs -f spark-consumer
docker-compose logs -f broker
docker-compose logs -f cassandra_db
```

---


## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

---

- **Data Science Academy** - Estrutura base do projeto

---

## 🙏 Agradecimentos

- [Portal Brasileiro de Dados Abertos](https://dados.gov.br)
- [SINESP](https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica)
- Apache Software Foundation
- Bitnami (imagens Docker)

---
