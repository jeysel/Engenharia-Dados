# Dados de Segurança Pública Disponíveis no Portal dados.gov.br

**Data do Levantamento**: 03/11/2025
**Fonte**: Portal Brasileiro de Dados Abertos (dados.gov.br)

---

## Visão Geral

Este documento apresenta um levantamento dos principais datasets de segurança pública disponibilizados pelo governo brasileiro através do Portal de Dados Abertos. Os dados são gerenciados principalmente pelo Ministério da Justiça e Segurança Pública (MJSP) através do Sistema Nacional de Estatísticas de Segurança Pública (SINESP).

---

## Principais Datasets Disponíveis

### 1. Ocorrências Criminais - SINESP (Principal Dataset)

**URL**: https://dados.gov.br/dataset/sistema-nacional-de-estatisticas-de-seguranca-publica

**Organização Responsável**: Ministério da Justiça e Segurança Pública (MJSP) - Secretaria Nacional de Segurança Pública (SENASP)

**Descrição**:
Sistema Nacional de Estatísticas de Segurança Pública que consolida dados extraídos das soluções SinespJC e Sinesp Integração. Contém informações sobre ocorrências criminais e vítimas registradas em todo o território nacional.

**Indicadores Disponíveis**:
- Estupro (total de ocorrências e vítimas)
- Furto de veículos
- Homicídio doloso
- Lesão corporal seguida de morte
- Roubo a instituição financeira
- Roubo de carga
- Roubo de veículos
- Roubo seguido de morte (latrocínio)

**Formatos dos Dados**:
- CSV (Comma-Separated Values)
- JSON (JavaScript Object Notation)

**Granularidade dos Dados**:
- **Por Município**: Indicadores de segurança pública desagregados por município brasileiro
- **Por Unidade da Federação**: Indicadores agregados por estado

**Recursos Disponíveis**:
- Dados Nacionais de Segurança Pública - Municípios
- Dados Nacionais de Segurança Pública - Unidades da Federação
- Dicionários de Dados

**Observações**:
- Os dados refletem o nível de alimentação e consolidação de cada Unidade da Federação nas soluções SinespJC e Sinesp Integração na data de extração
- Atualizações podem ocorrer após a publicação inicial
- Dados coletados desde 2001 pela SENASP

---

### 2. Indicadores sobre Segurança Pública

**URL**: https://dados.gov.br/dataset/seguranca-publica

**Descrição**:
Conjunto de indicadores gerais sobre segurança pública no Brasil, complementando os dados específicos do SINESP.

**Conteúdo**:
- Indicadores agregados de segurança pública
- Estatísticas gerais sobre criminalidade
- Dados complementares ao SINESP

---

### 3. Atlas da Violência

**URL**: https://dados.gov.br/dataset/atlas-da-violencia

**Organização Responsável**:
- IPEA (Instituto de Pesquisa Econômica Aplicada)
- Fórum Brasileiro de Segurança Pública

**Descrição**:
Publicação anual que apresenta análises abrangentes sobre violência no Brasil, com séries históricas e análises estatísticas detalhadas.

**Conteúdo**:
- Dados históricos sobre violência
- Análises estatísticas e tendências
- Indicadores de violência por região
- Estudos sobre causas e impactos da violência

---

### 4. Força Nacional de Segurança Pública

**URL**: https://dados.gov.br/dataset/forca-nacional-de-seguranca-publica

**Descrição**:
Indicadores sobre a atuação da Força Nacional de Segurança Pública em operações de apoio aos estados e municípios.

**Conteúdo**:
- Dados sobre operações realizadas
- Indicadores de desempenho
- Estatísticas de atuação

---

### 5. Peças, Tabelas e Fluxogramas de Polícia Judiciária

**URL**: https://dados.gov.br/dataset/pecas-de-policia-judiciaria

**Descrição**:
Documentação padronizada de procedimentos de polícia judiciária, incluindo modelos de peças processuais, tabelas de referência e fluxogramas de processos.

**Conteúdo**:
- Modelos de documentos oficiais
- Procedimentos padronizados
- Fluxogramas de processos investigativos

---

## Portais Alternativos

### Portal do Ministério da Justiça

**URL**: https://dados.mj.gov.br

**Descrição**: Portal específico do Ministério da Justiça que hospeda os mesmos datasets disponíveis no dados.gov.br, com foco em dados de segurança pública e justiça.

**Vantagens**:
- Interface especializada para dados de segurança pública
- Mesmos dados do SINESP
- Acesso direto aos datasets do MJSP

---

## Acesso aos Dados

### API CKAN

O Portal Brasileiro de Dados Abertos utiliza a plataforma CKAN (Comprehensive Knowledge Archive Network) para gerenciamento e distribuição dos dados.

**URL Base da API**: `https://dados.gov.br/api/3/action/`

**Principais Endpoints**:

1. **package_search** - Buscar datasets
   ```
   GET https://dados.gov.br/api/3/action/package_search?q=segurança+pública
   ```

2. **package_show** - Obter detalhes de um dataset específico
   ```
   GET https://dados.gov.br/api/3/action/package_show?id={dataset_id}
   ```

3. **resource_show** - Obter detalhes de um recurso específico
   ```
   GET https://dados.gov.br/api/3/action/resource_show?id={resource_id}
   ```

**Formato de Resposta**: JSON

**Parâmetros Comuns**:
- `q`: Termo de busca
- `rows`: Número de resultados por página
- `start`: Offset para paginação
- `fq`: Filtros adicionais

---

## APIs Comunitárias

Como não existe uma API oficial específica para consulta direta aos dados de ocorrências criminais do SINESP, a comunidade de desenvolvedores criou APIs próprias baseadas nos arquivos CSV/JSON disponibilizados:

### 1. API Segurança Pública (rayonnunes)

**Repositório**: https://github.com/rayonnunes/api_seguranca_publica

**Descrição**:
WebAPI criada com base nos dados abertos de ocorrências criminais do programa SINESP.

**Características**:
- Retorna dados em formato JSON
- Campos disponíveis: ano, tipo de crime, mês, município, ocorrências, região, estado
- Permite consultas filtradas

### 2. API Documentação (sousaellen)

**Repositório**: https://github.com/sousaellen/API-documentacao

**Descrição**:
Documentação de uma API sobre ocorrências criminais no Brasil com vários endpoints para consulta de estatísticas criminais.

**Características**:
- Endpoints estruturados para diferentes tipos de consulta
- Filtros por ano, estado, município e tipo de crime
- Documentação completa da API

---

## Contexto Legal e Histórico

### Lei nº 13.675/2018

A Lei nº 13.675 de 11 de junho de 2018 estabeleceu:
- Sistema Único de Segurança Pública (SUSP)
- Sistema Nacional de Informações de Segurança Pública (SINESP)

### Histórico da Coleta de Dados

- **2001**: Início da coleta de dados pela SENASP
- **2018**: Formalização legal do sistema nacional de informações
- **2023**: Lançamento do Sinesp Validador de Dados Estatísticos (VDE)

### Sinesp VDE (2023)

Lançado em maio de 2023, o Sinesp Validador de Dados Estatísticos permite:
- Coleta de 28 indicadores nacionais de segurança pública
- Consolidação e validação dos dados
- Acompanhamento mais rápido dos indicadores
- Validação em até 30 dias

---

## Considerações Técnicas

### Qualidade dos Dados

**Importante**: Os dados refletem o nível de alimentação e consolidação de cada Unidade da Federação. Isso significa que:
- A completude dos dados varia por estado
- Alguns estados podem ter dados mais atualizados que outros
- É necessário verificar metadados para avaliar a cobertura temporal

### Formatos Disponíveis

**CSV (Comma-Separated Values)**:
- Mais comum para datasets grandes
- Fácil importação em ferramentas de análise
- Compatível com Excel, Python, R, etc.

**JSON (JavaScript Object Notation)**:
- Estrutura hierárquica de dados
- Ideal para APIs e aplicações web
- Facilita integração com sistemas modernos

### Limitações

1. **Sem API REST direta para dados**: A API CKAN fornece apenas metadados. Para acessar os dados reais, é necessário:
   - Baixar os arquivos CSV/JSON
   - Utilizar APIs comunitárias
   - Implementar parser próprio

2. **Atualização variável**: A frequência de atualização depende de cada estado

3. **Dados agregados**: O SINESP disponibiliza dados agregados (estatísticas), não dados individuais de ocorrências

---

## Recomendações de Uso

### Para Análise de Dados

1. **Download direto**: Para análises pontuais, baixe os arquivos CSV/JSON diretamente do portal
2. **API CKAN**: Para automação da descoberta de datasets e verificação de atualizações
3. **APIs comunitárias**: Para integração em tempo real com filtros específicos

### Para ETL (Extract, Transform, Load)

O código implementado em [kafka_stream.py](../servidor/dags/kafka_stream.py) está configurado para:

1. **Extração**: Buscar metadados dos datasets via API CKAN
2. **Transformação**: Formatar informações sobre os datasets disponíveis
3. **Carga**: Enviar para tópico Kafka `kafka_topic_seguranca_publica`

**Próximos passos sugeridos**:
- Adicionar extração dos arquivos CSV/JSON dos recursos
- Implementar parser para os dados de ocorrências criminais
- Criar processamento para diferentes granularidades (município vs estado)

---

## Links Úteis

### Portais Oficiais
- Portal Brasileiro de Dados Abertos: https://dados.gov.br
- Portal de Dados do MJSP: https://dados.mj.gov.br
- Estatísticas de Segurança Pública: https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica

### Documentação
- API CKAN do dados.gov.br: https://dados.gov.br/swagger-ui/index.html
- Documentação CKAN oficial: https://docs.ckan.org/en/latest/api/

### Repositórios Comunitários
- API Segurança Pública: https://github.com/rayonnunes/api_seguranca_publica
- API Documentação: https://github.com/sousaellen/API-documentacao
- SINESP Client: https://github.com/victor-torres/sinesp-client

---

## Contato e Suporte

**Suporte Dados Abertos**: suporte.dadosabertos@cgu.gov.br

---

**Última Atualização**: 03/11/2025
**Versão**: 1.0
