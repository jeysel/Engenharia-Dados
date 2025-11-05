# Alterações Implementadas no kafka_stream.py

**Data**: 03/11/2025
**Arquivo**: [kafka_stream.py](../servidor/dags/kafka_stream.py)
**Objetivo**: Implementar extração e processamento de dados reais de ocorrências criminais do SINESP

---

## Resumo das Alterações

O arquivo foi completamente refatorado para consumir dados reais de ocorrências criminais do Sistema Nacional de Estatísticas de Segurança Pública (SINESP) ao invés de apenas metadados. As principais melhorias incluem:

1. Extração de dados reais de arquivos CSV do portal dados.gov.br
2. Parser robusto para diferentes formatos de dados
3. Processamento diferenciado por granularidade (município vs estado)
4. Roteamento inteligente para tópicos Kafka específicos

---

## Funções Implementadas

### 1. `obtem_metadados_dataset()` (Nova)

**Localização**: Linhas 17-45

**Descrição**:
Função dedicada a obter os metadados do dataset SINESP através da API CKAN.

**Características**:
- Usa o endpoint `package_show` para buscar dataset específico
- ID fixo: `sistema-nacional-de-estatisticas-de-seguranca-publica`
- Timeout configurado: 30 segundos
- Tratamento de exceções robusto

**Retorno**:
- Dicionário com metadados completos do dataset
- `None` em caso de erro

```python
def obtem_metadados_dataset():
    url = "https://dados.gov.br/api/3/action/package_show"
    params = {"id": "sistema-nacional-de-estatisticas-de-seguranca-publica"}
    # ... requisição e tratamento
```

---

### 2. `extrai_dados_api()` (Refatorada)

**Localização**: Linhas 48-112

**Mudanças Principais**:

#### Antes:
- Buscava apenas metadados do dataset
- Retornava informações sobre o dataset

#### Depois:
- **Obtém metadados** do dataset via `obtem_metadados_dataset()`
- **Identifica recursos CSV** disponíveis (prioriza dados de municípios)
- **Faz download** do arquivo CSV completo
- **Parseia o CSV** usando delimitador `;` (padrão dados.gov.br)
- **Retorna lote de dados** (limitado a 10 registros por requisição)

**Características Técnicas**:
- Encoding: `utf-8-sig` (suporta BOM)
- Delimitador CSV: `;` (ponto e vírgula)
- Limite por lote: 10 registros
- Timeout download: 60 segundos

**Estrutura de Retorno**:
```python
{
    "resource_name": "Nome do Recurso",
    "resource_id": "ID do Recurso",
    "resource_format": "CSV",
    "dataset_id": "ID do Dataset",
    "dataset_name": "Nome do Dataset",
    "dados": [
        {"campo1": "valor1", "campo2": "valor2", ...},
        {"campo1": "valor1", "campo2": "valor2", ...}
    ]
}
```

**Priorização de Recursos**:
1. CSV de municípios (preferencial)
2. Qualquer CSV disponível
3. Retorna `None` se não houver CSV

---

### 3. `formata_dados()` (Refatorada Completamente)

**Localização**: Linhas 114-192

**Mudanças Principais**:

#### Antes:
- Formatava metadados do dataset
- Retornava um único dicionário

#### Depois:
- **Processa múltiplos registros** de ocorrências criminais
- **Detecta granularidade** automaticamente (município/estado)
- **Extrai campos com fallback** (múltiplas variações de nomes)
- **Retorna lista de registros** formatados

**Campos Extraídos**:

| Categoria | Campos |
|-----------|--------|
| **Metadados** | `id`, `dataset_id`, `resource_id`, `granularidade` |
| **Temporais** | `ano`, `mes`, `mes_ano` |
| **Localização** | `uf`, `uf_nome`, `codigo_municipio`*, `municipio`*, `regiao`* |
| **Crime** | `tipo_crime`, `vitimas`, `ocorrencias` |
| **Homicídios** | `homicidio_doloso`, `lesao_corp_morte`, `latrocinio` |
| **Roubos** | `roubo_veiculo`, `roubo_carga`, `roubo_inst_financeira` |
| **Furtos** | `furto_veiculo` |
| **Sexual** | `estupro` |
| **Processamento** | `data_extracao` (timestamp ISO 8601) |

\* Apenas para granularidade "município"

**Detecção de Granularidade**:
```python
granularidade = "municipio" if "municip" in resource_name.lower() else "estado"
```

**Fallback Múltiplo**:
O parser aceita diferentes variações de nomes de campos:
```python
data["ano"] = registro.get("ano", registro.get("Ano", ""))
data["mes"] = registro.get("mes", registro.get("Mês", registro.get("mês", "")))
```

**ID Único**:
Cada registro recebe um UUID único:
```python
data["id"] = uuid.uuid4().hex
```

---

### 4. `stream_dados()` (Refatorada)

**Localização**: Linhas 194-295

**Mudanças Principais**:

#### Novo: Contador de Registros
```python
total_registros = 0
```

#### Novo: Roteamento Inteligente para Tópicos Kafka

**Antes**: Tópico fixo `kafka_topic_seguranca_publica`

**Depois**: Tópicos dinâmicos baseados na granularidade:

| Granularidade | Tópico Kafka |
|---------------|--------------|
| Município | `sinesp_ocorrencias_municipio` |
| Estado | `sinesp_ocorrencias_estado` |
| Indefinido | `sinesp_ocorrencias_geral` |

```python
granularidade = registros_formatados[0].get("granularidade", "indefinido")

if granularidade == "municipio":
    topico = "sinesp_ocorrencias_municipio"
elif granularidade == "estado":
    topico = "sinesp_ocorrencias_estado"
else:
    topico = "sinesp_ocorrencias_geral"
```

#### Novo: Envio Individual de Registros

**Antes**: Enviava um único objeto JSON

**Depois**: Envia cada registro individualmente

```python
for registro in registros_formatados:
    mensagem = json.dumps(registro, ensure_ascii=False).encode("utf-8")
    producer.send(topico, mensagem)
    total_registros += 1
```

**Vantagens**:
- Processamento independente de cada registro
- Facilita consumo downstream
- Permite particionamento eficiente no Kafka

#### Melhorias no Logging

**Log de Envio**:
```python
logging.info(f" Log - {len(registros_formatados)} registros de segurança pública enviados para tópico '{topico}'. Total: {total_registros}")
```

**Log de Erro Aprimorado**:
```python
logging.error(f" Log - Um erro ocorreu: {e}")
import traceback
logging.error(f" Log - Traceback: {traceback.format_exc()}")
```

**Log Final**:
```python
logging.info(f" Log - Streaming finalizado. Total de registros enviados: {total_registros}")
```

---

## Fluxo de Dados Completo

```
┌─────────────────────────────────────────────────────────────┐
│ 1. obtem_metadados_dataset()                                │
│    └─> API CKAN: package_show                               │
│        └─> Metadados do dataset SINESP                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. extrai_dados_api()                                       │
│    ├─> Identifica recursos CSV (prioriza municípios)       │
│    ├─> Download do arquivo CSV                              │
│    ├─> Parse com delimiter ';'                              │
│    └─> Retorna lote de 10 registros + metadados            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. formata_dados()                                          │
│    ├─> Detecta granularidade (município/estado)            │
│    ├─> Extrai campos com fallback múltiplo                 │
│    ├─> Gera UUID único para cada registro                  │
│    ├─> Adiciona timestamp de processamento                 │
│    └─> Retorna lista de registros formatados               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. stream_dados()                                           │
│    ├─> Determina tópico Kafka baseado na granularidade     │
│    │   • municipio → sinesp_ocorrencias_municipio          │
│    │   • estado → sinesp_ocorrencias_estado                │
│    │   • outro → sinesp_ocorrencias_geral                  │
│    ├─> Envia cada registro individualmente                 │
│    ├─> Incrementa contador                                 │
│    └─> Loga estatísticas de envio                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Kafka Broker (broker:29092)                                │
│    ├─> Tópico: sinesp_ocorrencias_municipio                │
│    ├─> Tópico: sinesp_ocorrencias_estado                   │
│    └─> Tópico: sinesp_ocorrencias_geral                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Configurações e Parâmetros

### Timeouts

| Operação | Timeout |
|----------|---------|
| Obter metadados | 30 segundos |
| Download CSV | 60 segundos |
| Conexão Kafka | 5000 ms |

### Limites

| Parâmetro | Valor | Razão |
|-----------|-------|-------|
| Registros por lote | 10 | Evitar sobrecarga de memória |
| Tempo de execução | 60 segundos | Definido pela DAG original |
| Intervalo entre lotes | 10 segundos | Evitar sobrecarga da API |
| Intervalo após erro | 5 segundos | Retry com backoff |

### Encoding e Delimitadores

| Configuração | Valor | Observação |
|--------------|-------|------------|
| Encoding CSV | `utf-8-sig` | Suporta BOM (Byte Order Mark) |
| Delimitador CSV | `;` | Padrão dados.gov.br |
| Encoding JSON | `utf-8` | Com `ensure_ascii=False` |

---

## Tratamento de Erros

### Níveis de Tratamento

1. **Nível 1 - Função Individual**:
   - Try-except em cada função
   - Retorna `None` em caso de erro
   - Print de erro para debug

2. **Nível 2 - Validação de Dados**:
   - Verifica se dados não são `None`
   - Verifica se lista não está vazia
   - Continue para próxima iteração se inválido

3. **Nível 3 - Loop Principal**:
   - Try-except no loop de streaming
   - Log de erro com traceback completo
   - Sleep antes de retry

### Exemplo de Tratamento:
```python
try:
    # Operação
except Exception as e:
    logging.error(f" Log - Um erro ocorreu: {e}")
    import traceback
    logging.error(f" Log - Traceback: {traceback.format_exc()}")
    time.sleep(5)
    continue
```

---

## Compatibilidade Docker

### Dependências Python Necessárias

O arquivo utiliza as seguintes bibliotecas (devem estar no `requirements.txt` do container):

```
airflow
kafka-python
requests
```

### Variáveis de Ambiente

| Variável | Valor Padrão | Descrição |
|----------|--------------|-----------|
| KAFKA_BROKER | `broker:29092` | Endereço do broker Kafka |

### Volumes Necessários

Nenhum volume adicional é necessário, pois os dados são obtidos diretamente da API.

### Portas

| Porta | Serviço |
|-------|---------|
| 29092 | Kafka Broker (interno ao Docker) |
| 9092 | Kafka Broker (externo - se necessário) |

---

## Próximas Melhorias Sugeridas

### Curto Prazo

1. **Cache Local de CSV**:
   - Evitar download repetido do mesmo arquivo
   - Implementar verificação de hash/ETag

2. **Paginação de Registros**:
   - Processar arquivo CSV completo em chunks
   - Manter offset de leitura

3. **Configuração Dinâmica**:
   - Permitir configurar limite de registros via variável de ambiente
   - Configurar intervalo de sleep via parâmetro

### Médio Prazo

4. **Processamento de Múltiplos Recursos**:
   - Processar tanto dados de município quanto de estado
   - Alternar entre diferentes recursos

5. **Métricas e Monitoramento**:
   - Exportar métricas para Prometheus
   - Dashboard com estatísticas de processamento

6. **Validação de Dados**:
   - Implementar schema validation (ex: Pydantic)
   - Rejeitar registros inválidos

### Longo Prazo

7. **Persistência de Estado**:
   - Salvar último offset processado
   - Permitir retomada após falha

8. **Enriquecimento de Dados**:
   - Adicionar dados geográficos (lat/long)
   - Cruzar com outras fontes de dados

9. **API REST Própria**:
   - Criar API para consulta dos dados processados
   - Implementar cache e agregações

---

## Testes Recomendados

### Teste 1: Conexão com API
```bash
curl "https://dados.gov.br/api/3/action/package_show?id=sistema-nacional-de-estatisticas-de-seguranca-publica"
```

### Teste 2: Download de CSV
Verificar se os recursos CSV estão acessíveis e no formato esperado.

### Teste 3: Kafka Consumer
```bash
# Criar consumer de teste para verificar mensagens
docker exec -it <kafka-container> kafka-console-consumer \
  --bootstrap-server broker:29092 \
  --topic sinesp_ocorrencias_municipio \
  --from-beginning
```

### Teste 4: Airflow DAG
Verificar se a DAG é detectada e pode ser executada manualmente no Airflow UI.

---

## Referências

- **Documentação API CKAN**: https://docs.ckan.org/en/latest/api/
- **Portal dados.gov.br**: https://dados.gov.br
- **Dataset SINESP**: https://dados.gov.br/dataset/sistema-nacional-de-estatisticas-de-seguranca-publica
- **Kafka Python Client**: https://kafka-python.readthedocs.io/
- **Airflow Docs**: https://airflow.apache.org/docs/

---

## Changelog

| Data | Versão | Alteração |
|------|--------|-----------|
| 03/11/2025 | 2.0 | Implementação completa de extração de dados reais |
| 03/11/2025 | 1.0 | Versão inicial (apenas metadados) |

---

**Autor**: Claude (Anthropic)
**Última Atualização**: 03/11/2025
**Status**: Implementado e Documentado
