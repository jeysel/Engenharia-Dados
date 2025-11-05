# 🔍 Como Conferir os Dados no Pipeline ETL

Este guia mostra como verificar se os dados estão fluindo corretamente em cada etapa do pipeline.

---

## 📊 Etapa 1: Verificar Status dos Containers

### Ver todos os containers rodando

```powershell
cd C:\Dev\Engenharia-Dados\ETL-Real-Time\servidor
docker-compose ps
```

**Esperado**: Todos os serviços devem estar "Up" e "healthy"

---

## 📋 Etapa 2: Verificar DAG do Airflow

### Listar DAGs disponíveis

```powershell
docker exec servidor-scheduler-1 airflow dags list
```

**Esperado**: Deve mostrar `real-time-etl-stack` com `is_paused = False`

### Ver execuções da DAG

```powershell
docker exec servidor-scheduler-1 airflow dags list-runs -d real-time-etl-stack --output table
```

**Esperado**: Deve mostrar execuções com `state = success`

### Trigger manual da DAG

```powershell
docker exec servidor-scheduler-1 airflow dags trigger real-time-etl-stack
```

### Ver logs da última execução

```powershell
docker logs servidor-scheduler-1 2>&1 | grep -A 20 "stream_from_api"
```

**Esperado**: Deve mostrar mensagens de sucesso sem erros

---

## 📨 Etapa 3: Verificar Tópicos Kafka

### Listar todos os tópicos

```powershell
docker exec broker kafka-topics --list --bootstrap-server localhost:9092
```

**Esperado**: Deve mostrar os tópicos:
- `sinesp_ocorrencias_municipio`
- `sinesp_ocorrencias_estado`
- `sinesp_ocorrencias_geral`

### Verificar se há mensagens em um tópico

```powershell
# Para tópico de municípios
docker exec broker kafka-run-class kafka.tools.GetOffsetShell --broker-list localhost:9092 --topic sinesp_ocorrencias_municipio

# Para tópico de estados
docker exec broker kafka-run-class kafka.tools.GetOffsetShell --broker-list localhost:9092 --topic sinesp_ocorrencias_estado

# Para tópico geral
docker exec broker kafka-run-class kafka.tools.GetOffsetShell --broker-list localhost:9092 --topic sinesp_ocorrencias_geral
```

**Esperado**: Deve mostrar offset maior que 0 se houver mensagens

### Consumir mensagens do tópico (ver dados)

```powershell
# Ver últimas 10 mensagens do tópico de municípios
docker exec broker kafka-console-consumer --bootstrap-server localhost:9092 --topic sinesp_ocorrencias_municipio --from-beginning --max-messages 10
```

**Esperado**: Deve mostrar dados JSON de ocorrências criminais

---

## 🔥 Etapa 4: Verificar Spark Consumer

### Ver status do consumer

```powershell
docker ps -a | findstr spark-consumer
```

**Esperado**: Deve mostrar "Up" (não "Exited")

### Ver logs do consumer em tempo real

```powershell
docker logs -f spark-consumer
```

**Esperado**: Deve mostrar mensagens como:
- `Keyspace criado com sucesso!`
- `Tabelas criadas com sucesso!`
- `Log - Spark Connection criada com sucesso!`
- `Log - Dataframe Kafka criado com sucesso`
- `Log - Streaming iniciado`
- `Log - Dados inseridos: <id> - <município/uf>`

### Reiniciar o consumer (se necessário)

```powershell
cd C:\Dev\Engenharia-Dados\ETL-Real-Time\servidor
docker-compose restart spark-consumer
```

---

## 💾 Etapa 5: Verificar Dados no Cassandra

### Acessar CQL Shell (console do Cassandra)

```powershell
docker exec -it cassandra cqlsh
```

### Comandos dentro do CQL Shell

```sql
-- Listar keyspaces
DESCRIBE KEYSPACES;

-- Usar o keyspace de dados de segurança pública
USE dados_seguranca_publica;

-- Listar tabelas
DESCRIBE TABLES;

-- Contar registros em cada tabela
SELECT COUNT(*) FROM tb_ocorrencias_municipio;
SELECT COUNT(*) FROM tb_ocorrencias_estado;
SELECT COUNT(*) FROM tb_ocorrencias_geral;

-- Ver primeiros 10 registros de municípios
SELECT * FROM tb_ocorrencias_municipio LIMIT 10;

-- Ver registros de um estado específico
SELECT * FROM tb_ocorrencias_estado WHERE uf = 'SP' LIMIT 5;

-- Ver registros por tipo de crime
SELECT municipio, uf, tipo_crime, ocorrencias
FROM tb_ocorrencias_municipio
WHERE municipio = 'São Paulo'
LIMIT 10;

-- Ver totais por UF
SELECT uf, uf_nome, COUNT(*) as total
FROM tb_ocorrencias_municipio
GROUP BY uf, uf_nome;

-- Sair do CQL Shell
EXIT;
```

---

## 🌐 Etapa 6: Monitoramento via Interface Web

### Airflow UI
- **URL**: http://localhost:8080
- **Usuário**: `admin`
- **Senha**: `jpb99`

**O que verificar**:
- Status da DAG (verde = sucesso)
- Logs de execução
- Próxima execução agendada

### Kafka Control Center
- **URL**: http://localhost:9021

**O que verificar**:
- Tópicos criados
- Número de mensagens
- Throughput
- Consumers ativos

### Spark UI
- **URL**: http://localhost:9090

**O que verificar**:
- Workers conectados
- Jobs executados
- Memória utilizada
- Tasks concluídas

---

## 🔧 Troubleshooting

### Problema: DAG não encontra dados

**Sintomas**:
```
Erro ao obter metadados: Expecting value: line 1 column 1
Nenhum dado de segurança pública encontrado
```

**Solução**:
1. Verificar se a API dados.gov.br está acessível
2. Testar manualmente:
```powershell
docker exec servidor-scheduler-1 python3 -c "import requests; r = requests.get('https://dados.gov.br/api/3/action/package_show?id=sistema-nacional-de-estatisticas-de-seguranca-publica'); print(r.status_code, r.headers.get('Content-Type'))"
```
3. Se retornar HTML, a API está indisponível ou mudou

### Problema: Tópicos Kafka não são criados

**Causa**: A DAG não conseguiu extrair dados da API

**Solução**:
1. Aguardar API voltar ao normal
2. Trigger manual da DAG quando API estiver funcionando

### Problema: Consumer não processa dados

**Sintomas**:
```
UnknownTopicOrPartitionException: This server does not host this topic-partition
```

**Solução**:
1. Verificar se os tópicos existem (Etapa 3)
2. Se não existem, executar a DAG primeiro
3. Reiniciar o consumer após os tópicos serem criados:
```powershell
docker-compose restart spark-consumer
```

### Problema: Cassandra sem dados

**Solução**:
1. Verificar se os tópicos Kafka têm mensagens (Etapa 3)
2. Verificar logs do consumer para erros
3. Verificar se o keyspace e tabelas foram criadas
4. Reiniciar o consumer

---

## 📈 Fluxo Completo de Dados

```
API dados.gov.br
    ↓ (DAG extrai)
Tópicos Kafka (3 tópicos criados)
    ↓ (mensagens enviadas)
Spark Consumer (processa streaming)
    ↓ (insere dados)
Cassandra (3 tabelas persistidas)
```

### Validação End-to-End

Execute estes comandos em sequência para validar o fluxo completo:

```powershell
# 1. Verificar última execução da DAG
docker exec servidor-scheduler-1 airflow dags list-runs -d real-time-etl-stack --output table | Select-Object -First 3

# 2. Verificar tópicos Kafka
docker exec broker kafka-topics --list --bootstrap-server localhost:9092 | findstr sinesp

# 3. Verificar mensagens no Kafka
docker exec broker kafka-run-class kafka.tools.GetOffsetShell --broker-list localhost:9092 --topic sinesp_ocorrencias_municipio

# 4. Verificar consumer rodando
docker logs spark-consumer --tail 20

# 5. Verificar dados no Cassandra
docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM dados_seguranca_publica.tb_ocorrencias_municipio;"
```

---

## ✅ Checklist de Validação

- [ ] Todos os containers estão rodando (docker-compose ps)
- [ ] DAG executada com sucesso (state = success)
- [ ] Tópicos Kafka criados (3 tópicos sinesp_*)
- [ ] Mensagens no Kafka (offset > 0)
- [ ] Consumer rodando sem erros
- [ ] Keyspace Cassandra criado (dados_seguranca_publica)
- [ ] Tabelas Cassandra criadas (3 tabelas)
- [ ] Dados inseridos no Cassandra (COUNT > 0)

---

## 📞 Suporte

Se todos os passos falharem:
1. Verificar logs: `docker-compose logs`
2. Verificar conectividade de rede
3. Verificar disponibilidade da API dados.gov.br
4. Reiniciar todo o ambiente: `docker-compose down && docker-compose up -d`
