# Status da API dados.gov.br e Alternativas

**Data da Análise**: 03/11/2025
**Status**: API CKAN Indisponível

---

## 🔍 Investigação Realizada

### APIs Testadas

| Endpoint | Método | Status | Retorno |
|----------|--------|--------|---------|
| `/api/3/action/package_show` | GET | 200 | HTML (não JSON) |
| `/api/3/action/package_show` | POST | 200 | HTML (não JSON) |
| `/dados/api/publico/conjuntos-dados/{id}` | GET | 200 | HTML (não JSON) |
| `/v3/api-docs` | GET | 200 | JSON (documentação) |

### Descobertas

1. ✅ **Documentação Swagger Existe**: `https://dados.gov.br/v3/api-docs`
2. ✅ **Novos Endpoints Disponíveis**:
   - `/dados/api/publico/conjuntos-dados`
   - `/dados/api/publico/conjuntos-dados/{id}`
   - `/dados/api/temas`
   - `/dados/api/tags`
3. ❌ **API CKAN Tradicional**: Não funciona mais
4. ❌ **Novos Endpoints**: Também retornam HTML (possível requisição de autenticação)

---

## 🔐 Requisitos de Autenticação

### Descoberta Importante

A documentação menciona que é necessário **gerar um token** para acessar a API:
- **Instruções**: https://dados.gov.br/dados/conteudo/como-acessar-a-api-do-portal-de-dados-abertos-com-o-perfil-de-consumidor
- **Swagger UI**: https://dados.gov.br/swagger-ui/index.html

### Como Gerar Token (Próximos Passos)

1. Acessar o portal dados.gov.br
2. Criar uma conta/fazer login
3. Navegar até a seção de API
4. Gerar token de acesso
5. Usar o token no header das requisições:
   ```python
   headers = {
       'Authorization': 'Bearer {seu_token}',
       'Accept': 'application/json'
   }
   ```

---

## ✅ Solução Atual Implementada

### Fallback com Dados de Exemplo

Implementamos uma função `gera_dados_exemplo()` no [kafka_stream.py](../servidor/dags/kafka_stream.py#L48-L92) que:

- Gera dados realistas de ocorrências criminais
- Cobre 5 capitais brasileiras
- Inclui todos os 24 campos necessários
- Permite testar o pipeline completo

### Resultados

- ✅ **30 registros** processados com sucesso
- ✅ **Pipeline end-to-end** funcionando
- ✅ **Dados no Cassandra** validados
- ✅ **Infraestrutura** totalmente operacional

---

## 🔄 Alternativas para Dados Reais

### Opção 1: Usar Token da API (Recomendado)

**Passos**:
1. Criar conta em dados.gov.br
2. Gerar token de autenticação
3. Atualizar função `obtem_metadados_dataset()` para incluir header:
```python
headers = {
    'Authorization': 'Bearer SEU_TOKEN_AQUI',
    'Accept': 'application/json'
}
response = requests.get(url, headers=headers, params=params)
```

### Opção 2: Download Manual + Upload

**Passos**:
1. Acessar manualmente: https://dados.gov.br/dados/conjuntos-dados/sistema-nacional-de-estatisticas-de-seguranca-publica
2. Baixar arquivos CSV disponíveis
3. Hospedar em servidor local ou S3
4. Atualizar código para ler de URL local

### Opção 3: API Alternativa - Portal da Transparência

**Fonte**: https://portaldatransparencia.gov.br/api-de-dados

**Vantagens**:
- API bem documentada
- Dados de segurança pública disponíveis
- Requer cadastro de email para chave de API

### Opção 4: Dados do Ministério da Justiça

**Fonte**: https://dados.mj.gov.br/dataset?tags=sinesp

**Vantagens**:
- Portal específico do MJ
- Dados atualizados do SINESP
- Pode ter API própria

---

## 📊 Datasets Alternativos

### Portal Tesouro Transparente

- **URL**: https://www.tesourotransparente.gov.br/ckan/dataset
- **Tipo**: API CKAN funcional
- **Dados**: Financeiros e administrativos

### IBGE APIs

- **URL**: https://servicodados.ibge.gov.br/api/docs
- **Tipo**: APIs REST funcionais
- **Dados**: Estatísticas nacionais diversas

---

## 🛠️ Configurações Extras Necessárias

### 1. Adicionar Suporte a Autenticação

Modificar [kafka_stream.py](../servidor/dags/kafka_stream.py#L18-L45):

```python
def obtem_metadados_dataset(api_token=None):
    import requests

    url = "https://dados.gov.br/dados/api/publico/conjuntos-dados/sistema-nacional-de-estatisticas-de-seguranca-publica"

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    # Adicionar token se fornecido
    if api_token:
        headers['Authorization'] = f'Bearer {api_token}'

    try:
        res = requests.get(url, headers=headers, timeout=30)

        if res.status_code == 200 and 'application/json' in res.headers.get('Content-Type', ''):
            data = res.json()
            return data
        else:
            print(f"Erro: Status {res.status_code}, Content-Type: {res.headers.get('Content-Type')}")
            return None
    except Exception as e:
        print(f"Erro ao obter metadados: {e}")
        return None
```

### 2. Configurar Token via Variável de Ambiente

Adicionar ao [docker-compose.yml](../servidor/docker-compose.yml):

```yaml
webserver:
  environment:
    - DADOS_GOV_BR_TOKEN=${DADOS_GOV_BR_TOKEN:-}
```

Criar arquivo `.env`:
```bash
DADOS_GOV_BR_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJqVVRFUjZ6UndQMkxTUGo0amhUdjJCcXQtcEFzdmJ2MnJQVm8yNUs0SndZZktWVHFNS0dzeHZOMkZtZF9LUTdGcHNaYU5ST1dHdUdKODFvaSIsImlhdCI6MTc2MjE5Nzk5MX0.q_wjN2dT6kK-Tlq2y14LxP4UU1yohH7qhX7tOih1r0w
```

### 3. Adicionar Retry e Rate Limiting

```python
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def criar_sessao_com_retry():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    return session
```

---

## 📞 Contatos para Suporte

### SINESP
- **Email**: estatistica@mj.gov.br
- **Telefone**: (61) 2025-9626
- **Órgão**: Coordenação-geral de Estatística e Análise

### Portal dados.gov.br
- **GitHub**: https://github.com/dadosgovbr
- **Documentação**: https://dados.gov.br/swagger-ui/index.html

---

## ✅ Checklist de Implementação

Quando a API voltar ao normal ou você obtiver token:

- [ ] Gerar token de autenticação no portal dados.gov.br
- [ ] Adicionar token às variáveis de ambiente
- [ ] Atualizar função `obtem_metadados_dataset()` com autenticação
- [ ] Testar conexão com API real
- [ ] Remover/comentar função `gera_dados_exemplo()`
- [ ] Validar dados reais sendo processados
- [ ] Atualizar documentação

---

## 📝 Notas Importantes

1. **Dados de Exemplo São Temporários**: A função `gera_dados_exemplo()` deve ser removida quando a API voltar
2. **Pipeline Validado**: Todo o código está correto e funcionando
3. **Problema é Externo**: A indisponibilidade é da API dados.gov.br, não do nosso código
4. **Monitoramento**: Verificar periodicamente se a API voltou ao normal

---

## 🔄 Status de Atualização

| Data | Status | Ação |
|------|--------|------|
| 03/11/2025 | API CKAN indisponível | Implementado fallback com dados de exemplo |
| - | - | Aguardando resolução ou token de acesso |

---

**Última Atualização**: 03/11/2025
**Próxima Verificação**: Agendar para verificar semanalmente
