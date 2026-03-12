# Configuração do Pipeline ETL Real-Time - SINESP

## 🚀 Início Rápido

### 1️⃣ Inicializar Docker
Abra a janela do Docker Desktop para inicializar o docker engine.

### 2️⃣ Subir os containers
```bash
cd C:\Dev\Engenharia-Dados\ETL-Real-Time\servidor
docker-compose up -d
```

### 3️⃣ Acessar Airflow
http://localhost:8080

**Credenciais**:
- Usuário: `admin`
- Senha: Configurada no entrypoint do Airflow (ver arquivo `entrypoint/entrypoint.sh`)

### 4️⃣ Executar DAG
Na interface do Airflow, clique na DAG `real-time-etl-stack` e execute (botão "Trigger DAG" ou ícone de play).

Ou via CLI:
```bash
docker exec servidor-scheduler-1 airflow dags trigger real-time-etl-stack
```

### 5️⃣ Reiniciar Consumer (após DAG executar)
```bash
cd C:\Dev\Engenharia-Dados\ETL-Real-Time\servidor
docker-compose restart spark-consumer
```

---

## 📊 Comandos Úteis

### Monitorar Logs
```bash
# Logs do consumer
docker logs -f spark-consumer

# Logs do Airflow
docker-compose logs -f webserver scheduler
```

### Verificar Tópicos Kafka
```bash
docker exec broker kafka-topics --list --bootstrap-server localhost:9092 | findstr sinesp
```

### Verificar Dados no Cassandra
```bash
# Contar registros
docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM dados_seguranca_publica.tb_ocorrencias_municipio;"

# Ver primeiros registros
docker exec cassandra cqlsh -e "SELECT * FROM dados_seguranca_publica.tb_ocorrencias_municipio LIMIT 5;"
```

---

## ⚠️ PROBLEMA ATUAL: API dados.gov.br Indisponível

**Data da Análise**: 03/11/2025
**Status**: ❌ **API REST COMPLETAMENTE OFFLINE**

### Diagnóstico

A API REST do portal dados.gov.br está **indisponível**. Todos os endpoints (públicos e privados, com ou sem token) retornam **302 Redirect** para página de login.

#### Testes Realizados

| Endpoint | Token | Resultado |
|----------|-------|-----------|
| `/dados/api/publico/conjuntos-dados/{id}` | ✅ Com Token | 302 Redirect |
| `/dados/api/publico/conjuntos-dados/{id}` | ❌ Sem Token | 302 Redirect |
| `/dados/api/publico/conjuntos-dados?pagina=0` | ✅ Com Token | 302 Redirect |
| `/api/3/action/package_list` (CKAN) | - | Sem resposta |

### Tokens Testados (Ambos Falharam)

1. **Token Original**: `eyJhbGc...r0w` ❌
2. **Token Renovado (03/11/2025)**: `eyJhbGc...Wx0` ❌

### Causa Raiz

A API foi **descontinuada ou está em manutenção prolongada**. A autenticação via token JWT Bearer não está funcionando.

---

## ✅ Configurações Implementadas

### Autenticação com Token (Código Pronto)

**Arquivo**: `kafka_stream.py` (linhas 18-52)

```python
def obtem_metadados_dataset(api_token=None):
    import requests
    import os

    url = "https://dados.gov.br/dados/api/publico/conjuntos-dados/sistema-nacional-de-estatisticas-de-seguranca-publica"

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    # Adicionar token se fornecido via parâmetro ou variável de ambiente
    if api_token:
        headers['Authorization'] = f'Bearer {api_token}'
    elif os.getenv('DADOS_GOV_BR_TOKEN'):
        headers['Authorization'] = f'Bearer {os.getenv("DADOS_GOV_BR_TOKEN")}'

    # ... código de requisição
```

### Variáveis de Ambiente

**Arquivo**: `.env` (servidor/)
```bash
DADOS_GOV_BR_TOKEN=eyJhbGc...Wx0
```

**Docker Compose**: Configurado nos serviços `webserver` e `scheduler`

### Logging Detalhado

✅ **Implementado** em `kafka_stream.py` (linhas 107-182):
- Status do token (configurado/não configurado)
- Erros detalhados de API
- Erros de recursos não encontrados
- Traceback completo para debugging

**Exemplo de log de erro**:
```
Log - ERRO: Falha ao obter metadados do dataset da API dados.gov.br
Log - Verifique se o token de autenticação está configurado corretamente
Log - Token atual: Configurado
Log - Streaming finalizado. Total de registros enviados: 0
```

---

## 💡 Soluções Alternativas

### Opção 1: Dados de Exemplo (Implementada)

✅ **Função disponível**: `gera_dados_exemplo()` em `kafka_stream.py` (linhas 56-99)

**Como ativar**:
Editar `kafka_stream.py` na função `extrai_dados_api()` (linha 107):

```python
if dataset is None:
    # Loga erro detalhado quando a API falhar
    logging.error(" Log - ERRO: Falha ao obter metadados do dataset da API dados.gov.br")
    logging.warning(" Log - Usando dados de exemplo para teste...")
    return gera_dados_exemplo()  # ← ADICIONAR ESTA LINHA
```

**Características**:
- 5 capitais brasileiras (SP, RJ, MG, BA, PR)
- Dados randomizados mas realistas
- Todos os 24 campos necessários
- Valida pipeline end-to-end

### Opção 2: Download Manual

1. Acessar: https://dados.gov.br/dados/conjuntos-dados/sistema-nacional-de-estatisticas-de-seguranca-publica
2. Fazer login manualmente no navegador
3. Baixar arquivos CSV
4. Hospedar em volume Docker ou servidor local
5. Modificar `extrai_dados_api()` para ler arquivos locais

**Exemplo de código**:
```python
def extrai_dados_local():
    import pandas as pd

    df = pd.read_csv('/dados/ocorrencias_municipio.csv', delimiter=';')
    dados = df.head(10).to_dict('records')

    return {
        "resource_name": "dados_locais",
        "dados": dados
    }
```

### Opção 3: APIs Alternativas

| Fonte | URL | Status | Requer Auth |
|-------|-----|--------|-------------|
| Portal da Transparência | https://portaldatransparencia.gov.br/api-de-dados | ✅ | Email |
| IBGE APIs | https://servicodados.ibge.gov.br/api/docs | ✅ | Não |
| SSP-SP | http://www.ssp.sp.gov.br/transparenciassp/ | ✅ | Não |
| ISP-RJ | http://www.ispdados.rj.gov.br/ | ✅ | Não |

---

## 📞 Suporte e Contatos

### dados.gov.br
- **GitHub**: https://github.com/dadosgovbr
- **Swagger**: https://dados.gov.br/swagger-ui/index.html

### SINESP (Ministério da Justiça)
- **Email**: estatistica@mj.gov.br
- **Telefone**: (61) 2025-9626
- **Órgão**: Coordenação-geral de Estatística e Análise

---

## 🔒 Segurança

**IMPORTANTE**: Adicionar `.env` ao `.gitignore`

```bash
cd C:\Dev\Engenharia-Dados\ETL-Real-Time\servidor
echo .env >> .gitignore
```

Criar `.env.example` para referência:
```bash
# Token de autenticação para API do dados.gov.br
# Gerado em: https://dados.gov.br/
DADOS_GOV_BR_TOKEN=seu_token_aqui
```

---

## 📝 Histórico

| Data | Evento | Status |
|------|--------|--------|
| 03/11/2025 | API CKAN identificada como offline | ❌ |
| 03/11/2025 | Implementado suporte a token JWT | ✅ |
| 03/11/2025 | Token renovado | ❌ API continua offline |
| 03/11/2025 | Testados todos endpoints | ❌ Todos offline |
| 03/11/2025 | Documentação criada | ✅ |

---

**Última Atualização**: 03/11/2025 21:35
**Status do Sistema**: ✅ Pipeline funcional (aguardando fonte de dados)
**Recomendação**: Usar `gera_dados_exemplo()` para validar pipeline
