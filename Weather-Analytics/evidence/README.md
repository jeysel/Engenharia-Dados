# Evidence.dev — Weather Analytics Dashboard

Camada de visualização do pipeline **Weather Analytics**.
Consome os marts do dbt materializados no BigQuery (prod) ou PostgreSQL (dev)
e gera um site estático com dashboards interativos.

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Fonte (prod) | BigQuery — dataset `weather_dw_marts` |
| Fonte (dev)  | PostgreSQL — schema `dbt_dev_marts` |
| Framework    | [Evidence.dev](https://evidence.dev) |
| Deploy       | GitHub Pages / Netlify / Vercel |

## Páginas

| Página | Rota | Descrição |
|--------|------|-----------|
| Visão Geral | `/` | KPIs do pipeline, temperatura nacional, alertas e resumo por região |
| Temperatura | `/temperatura` | Série temporal, anomalias e ranking por cidade |
| Precipitação | `/precipitacao` | Acumulados, classificação e anomalias por região |
| Alertas | `/alertas` | Eventos extremos detectados, evolução e cidades mais afetadas |
| Cidade (dinâmica) | `/cidades/[location_id]` | Drill-down completo para cada localidade |

## Pré-requisitos

- Node.js 18+ instalado
- Pipeline dbt executado (`dbt build`) com dados materializados
- Para prod: Service Account GCP com roles `BigQuery Data Viewer` e `BigQuery Job User`

## Configuração

### 1. Instalar dependências

```bash
cd evidence
npm install
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Edite o .env com seus valores
```

**Para prod (BigQuery):**

```env
GCP_PROJECT_ID=seu-projeto-gcp
BQ_MARTS_DATASET=weather_dw_marts
GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/service-account.json
```

> O dataset `weather_dw_marts` é gerado automaticamente pelo dbt quando
> `+schema: marts` está configurado no `dbt_project.yml` com target `prod`.
> Se o seu projeto usar um nome diferente, ajuste a variável.

**Para dev (PostgreSQL local):**

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=weather_staging
POSTGRES_USER=weather_user
POSTGRES_PASSWORD=weather_pass
PG_MARTS_SCHEMA=dbt_dev_marts
```

> Nas páginas `.md`, substitua `weather_dw` por `weather_pg` nas queries SQL
> para usar a fonte PostgreSQL.

### 3. Carregar as fontes de dados

```bash
npm run sources
```

### 4. Iniciar o servidor de desenvolvimento

```bash
npm run dev
# Acesse: http://localhost:3000
```

## Deploy

### GitHub Pages (gratuito)

```bash
npm run build
# Faça upload da pasta build/ para a branch gh-pages
# ou configure GitHub Actions conforme a documentação do Evidence.dev
```

### Netlify / Vercel

Configure as variáveis de ambiente no painel da plataforma e aponte o
build command para `npm run build` com publish directory `build/`.

## Estrutura dos arquivos

```
evidence/
├── package.json
├── evidence.plugins.yaml          # plugins de conexão habilitados
├── .env.example                   # template de variáveis de ambiente
├── .gitignore
├── sources/
│   ├── weather_dw/
│   │   └── connection.yaml        # BigQuery (prod)
│   └── weather_pg/
│       └── connection.yaml        # PostgreSQL (dev)
└── pages/
    ├── index.md                   # visão geral
    ├── temperatura.md             # análise de temperatura
    ├── precipitacao.md            # análise de precipitação
    ├── alertas.md                 # alertas climáticos
    └── cidades/
        └── [cidade].md            # página dinâmica por location_id
```

## Referências

- [Evidence.dev — Documentação](https://docs.evidence.dev)
- [BigQuery connector](https://docs.evidence.dev/core-concepts/data-sources/#bigquery)
- [PostgreSQL connector](https://docs.evidence.dev/core-concepts/data-sources/#postgresql)
- [Rotas dinâmicas](https://docs.evidence.dev/core-concepts/routing/#dynamic-pages)
