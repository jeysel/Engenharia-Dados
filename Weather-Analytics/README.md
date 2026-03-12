# Projeto: Weather Analytics Pipeline
# Open-Meteo API → collector.py (PostgreSQL) → Airbyte → BigQuery → dbt → BigQuery DW

## Estrutura

```
Weather-Analytics/
├── postgresql/     # Container Ubuntu 24.04 + PostgreSQL 17 + app coletor
├── airbyte/        # Guia de configuração: Source PostgreSQL → Destination BigQuery
├── dbt/            # Transformações: staging → marts (dev: Postgres, prod: BigQuery)
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


```



