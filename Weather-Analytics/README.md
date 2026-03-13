# Projeto: Weather Analytics Pipeline
# Open-Meteo API → collector.py (PostgreSQL) → Airbyte → BigQuery → dbt → BigQuery DW
teste
## Estrutura

```
Weather-Analytics/
├── postgresql/     # Container Ubuntu 24.04 + PostgreSQL 17 + app coletor
├── airbyte/        # Guia de configuração: Source PostgreSQL → Destination BigQuery
├── dbt/            # Transformações: staging → marts (dev: Postgres, prod: BigQuery)
├── evidence/       # Dashboards interativos gerados a partir dos marts do dbt
└── docs/           # Arquitetura e decisões
```

---
## 🚀 Configuração Inicial

### Pré-requisitos

- Docker Desktop instalado e rodando
- Docker Compose disponível
- ~8GB de espaço livre em disco
- Conexão com internet para download de imagens e integração com APIs

---

## 🐳 Criar Container Docker para executar o Airbyte localmente (Maquina com Windows 11)

* Acessar o link: https://docs.airbyte.com/using-airbyte/getting-started/oss-quickstart?_gl=1*1uywmn1*_gcl_au*MTU0OTM4MDYyMi4xNzMyNzk5MTYx

* Executar os passos em ordem:

```
1- "Overview" -> Install ABCTL
2- Overview/Install abctl Passsos do sistema operacional (Aba Windows)
3- Download ABCTL, opção: "Download windows"
4- Extrair o conteúdo em c:\airbyte (Sugestão)
5- Acessar: Environment Variables
6- System variables 
7- Path (Edit)
8- New (Colar o caminho da pasta dos arquivos extraidos, passo 4) - Selecionar OK
9- No PowerShell digitar: abctl version  (Tem que retornar a versão)
10- No PowerShell executar: abctl local install --port 9000   (Docker deve estar em execução)
11- No PowerShell, será exibido o link: http://localhost:9000/setup  
12- No PowerShell, Informar um endereço de email, organização e selecionar "Get started"
13- No PowerShell, executar: abctl local credentials
14- Será gerado uma senha, copiar a senha gerada, exemplo: zJomffmttWEF5FL0afTGAs59wQdangpu
15- Acessar o endereço: http://localhost:9000/ e informar o email e a senha gerada
16- Para desinstalar o airbyte local, Abra PowerShell de digite: abctl local uninstall --persisted 

```

## Weather Analytics Pipeline - Arquitetura em camadas

| Camada | Tecnologia | O que faz |
|--------|-----------|-----------|
| Coleta | `collector.py` (Python no container) | Busca API Open-Meteo → grava em `raw.*` |
| Staging | PostgreSQL 17 | Armazena dados raw e serve como Source para o Airbyte |
| Ingest | Airbyte (conector nativo PostgreSQL → BigQuery) | Replica `raw.*` para BigQuery `weather_raw` |
| Transform | dbt | Lê `weather_raw` (prod) ou `raw` (dev) → materializa marts |
| Warehouse | BigQuery | Dataset `weather_dw` com tabelas analíticas finais |
| Visualização | Evidence.dev | Dashboards interativos gerados a partir dos marts do dbt |

## Pré-requisitos

- Docker + Docker Compose
- Airbyte já instalado e rodando em `http://localhost:9000`
- Conta GCP com BigQuery e um Service Account com roles:
  `BigQuery Data Editor` + `BigQuery Job User`

## Ordem de execução

```bash
# 1. Subir e configurar o PostgreSQL (ver postgresql/README.md)
cd postgresql && docker compose up -d postgres
# Siga o guia: Weather-Analytics\postgresql\README.md

# 2. Configurar o Airbyte (ver airbyte/README.md)
# Acesse http://localhost:9000 e siga o guia: Weather-Analytics\airbyte\README.md

# 3. Executar o dbt
# Siga o guia: Weather-Analytics\dbt\README.md
cd ../dbt
docker compose run --rm dbt-seed
docker compose run --rm dbt-build            # dev (PostgreSQL)
DBT_TARGET=prod docker compose run --rm dbt-build  # prod (BigQuery)

# 4. Visualizar os dashboards (ver evidence/README.md)
cd ../evidence
npm install
npm run sources
npm run dev                                  # http://localhost:3000
```

---

## 📊 Dashboards — Evidence.dev

Camada de visualização que consome diretamente os marts materializados pelo dbt.
Não requer nenhuma ferramenta de BI externa — os dashboards são gerados como
site estático a partir de queries SQL sobre o BigQuery (prod) ou PostgreSQL (dev).

### Pré-requisitos

- Node.js 18 ou superior instalado
- dbt já executado com dados materializados nos marts
- Para prod: Service Account GCP com as roles `BigQuery Data Viewer` e `BigQuery Job User`
  (o mesmo arquivo JSON usado pelo dbt)

### Configuração

**1. Instalar dependências**

```bash
cd evidence
npm install
```

**2. Configurar variáveis de ambiente**

```bash
cp .env.example .env
# Edite o .env com os valores do seu ambiente
```

Variáveis obrigatórias para prod (BigQuery):

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `GCP_PROJECT_ID` | ID do projeto GCP | `meu-projeto-gcp` |
| `BQ_MARTS_DATASET` | Dataset gerado pelo dbt | `weather_dw_marts` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Caminho do arquivo JSON da Service Account | `/home/user/sa.json` |

Para dev (PostgreSQL local), use as mesmas credenciais do `postgresql/.env`.
Veja o arquivo `evidence/.env.example` para a lista completa.

**3. Carregar as fontes e iniciar**

```bash
npm run sources   # Evidence.dev lê o schema das tabelas
npm run dev       # Abre em http://localhost:3000
```

### Páginas disponíveis

| Página | URL | Conteúdo |
|--------|-----|----------|
| Visão Geral | `/` | KPIs do pipeline, temperatura nacional, alertas por região |
| Temperatura | `/temperatura` | Série temporal, anomalias rolling 30d, ranking de cidades |
| Precipitação | `/precipitacao` | Acumulados, classificação de chuva, anomalias por região |
| Alertas | `/alertas` | Eventos extremos, evolução diária, cidades mais afetadas |
| Cidade | `/cidades/[location_id]` | Drill-down completo por localidade |

Exemplo de URL para drill-down: `http://localhost:3000/cidades/florianopolis`

### Gerar site estático para publicação

```bash
npm run build
# Conteúdo gerado em: evidence/build/
# Pode ser publicado no GitHub Pages, Netlify ou Vercel
```

> Guia completo: `evidence/README.md`



