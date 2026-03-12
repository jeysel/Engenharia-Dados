# Como Usar - Sistema de Extração SSP-SC

Guia rápido de comandos para operação do sistema de extração de dados da SSP-SC com OCR.

---
## 🚀 Quick Start

### Pré-requisitos

- Docker & Docker Compose
- Python 3.10+
- PostgreSQL 16 (ou use Docker)
- AWS Account (para Terraform - opcional)

### Instalação Local

```bash
cd search-ssp-sc

# Inicie os serviços com Docker Compose
docker-compose up -d

# Destruir APENAS os containers deste projeto (search-ssp-sc)
docker stop ssp-sc-extrator ssp-sc-postgres ssp-sc-visualizacao 2>$null;
docker rm ssp-sc-extrator ssp-sc-postgres ssp-sc-visualizacao 2>$null;
docker network rm search-ssp-sc_ssp-network 2>$null

# Acesse o dashboard

Linux/Unix: open http://localhost:5000
Windows (PowerShell/CMD): start http://localhost:5000
```

### Execução Manual da Extração

```bash
# Extração completa (recomendado - extrai boletins mensais de 2023, 2024 e 2025)
docker exec ssp-sc-extrator python extractor.py

# Extração com OCR completo (mais lento, para todas as páginas)
docker exec ssp-sc-extrator python extractor_ocr_v2.py --limpar --limite=5
```

## 📦 Componentes

### 1. Extrator (`extrator/`)

Extrai dados da SSP-SC usando:
- BeautifulSoup para parsing HTML
- Tesseract OCR para extração de PDFs
- SQLAlchemy para persistência

**Arquivos principais:**
- `extractor_autonomous.py` - Extrator principal
- `scheduler.py` - Scheduler legado (substituído por Airflow)

### 2. Airflow DAGs (`airflow/dags/`)

Orquestração do pipeline com Apache Airflow:
- `extract_ssp_sc_dag.py` - DAG principal de extração
- Schedule: `@hourly` (personalizável)
- Validação automática de dados
- Envio de métricas

### 3. Visualização (`visualizacao/`)

Dashboard Flask com:
- Gráficos interativos (Plotly)
- API REST
- Filtros dinâmicos
- Estatísticas em tempo real

### 4. Terraform (`terraform/`)

Infraestrutura AWS como código:
- **S3 Data Lake** - Armazenamento escalável
- **RDS PostgreSQL** - Banco de dados gerenciado
- **VPC** - Rede isolada
- **CloudWatch** - Monitoramento e alertas

## 🧪 Testes

### Executar Testes Localmente

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
Linux/Unix: . venv/bin/activate
PowerShell: .\venv\Scripts\Activate.ps1

# Instalar dependências de teste
pip install -r requirements-test.txt

# Executar todos os testes
pytest tests/ -v

# Executar com coverage
pytest tests/ --cov=extrator --cov-report=html

# Ver relatório de coverage
open htmlcov/index.html
```

### Tipos de Testes

- ✅ **Unit Tests** - Testa funções isoladas
- ✅ **Integration Tests** - Testa integração com banco
- ✅ **Database Tests** - Testa schemas e queries
- ✅ **Performance Tests** - Testa inserção em massa


## ☁️ Deploy em Produção (AWS)

### 1. Configurar Terraform: /terraform/README.md


## 🔧 Configuração

### Variáveis de Ambiente

Crie um arquivo `.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ssp_sc_db

# Extração
EXTRACTION_INTERVAL=3600  # segundos
DATA_DIR=/app/data

# AWS (para S3)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name

# Airflow
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres:5432/airflow
AIRFLOW_WEBSERVER_SECRET_KEY=your_secret_key
```

## 📊 Monitoramento

### CloudWatch Alarms (AWS)

Terraform cria automaticamente alarmes para:
- ⚠️ CPU > 80%
- ⚠️ Storage < 5GB
- ⚠️ Conexões > 80

### Métricas do Airflow

Acesse: `http://localhost:8080/dags/ssp_sc_extraction`

- Task duration
- Success/failure rate
- XCom values (registros extraídos)

### Logs

```bash
# Logs do extrator
docker logs ssp-sc-extrator -f

# Logs do Airflow
docker logs airflow-webserver -f

# Logs do PostgreSQL
docker logs ssp-sc-postgres -f
```

## 🔐 Segurança

### ⚠️ IMPORTANTE: Configuração Segura

**ANTES de iniciar o projeto, configure as credenciais corretamente:**

```bash
# 1. Copie o arquivo de exemplo
cp .env.example .env

# 2. Edite com suas credenciais REAIS
nano .env

# 3. NUNCA commite o arquivo .env
# (já está configurado no .gitignore)
```

**Estrutura do arquivo `.env`:**
```env
# Database - USE SENHAS FORTES!
POSTGRES_USER=seu_usuario_aqui
POSTGRES_PASSWORD=SenhaForte123!@#ComMaisDe16Caracteres
POSTGRES_DB=ssp_sc_db
DATABASE_URL=postgresql://seu_usuario:SenhaForte123@postgres:5432/ssp_sc_db

# Flask
FLASK_ENV=production
FLASK_DEBUG=False
EXTRACTION_INTERVAL=3600
```

### Recursos de Segurança Implementados

- ✅ Criptografia em repouso (S3 + RDS)
- ✅ Variáveis de ambiente (sem credenciais hardcoded)
- ✅ Secrets via AWS Secrets Manager (recomendado para produção)
- ✅ VPC com subnets privadas
- ✅ Security Groups restritivos (apenas VPC interna por padrão)
- ✅ Backup automático (RDS)
- ✅ Versionamento (S3)
- ✅ `.gitignore` configurado para prevenir commit de secrets

### 🚨 Nunca Commite

- ❌ Arquivos `.env` (exceto `.env.example`)
- ❌ Arquivos `terraform.tfstate`
- ❌ Arquivos `terraform.tfvars` (exceto `.tfvars.example`)
- ❌ Tokens, senhas ou API keys
- ❌ Credenciais AWS

**Leia o guia completo:** [SECURITY.md](../SECURITY.md)


## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/amazing`)
3. Commit suas mudanças (`git commit -m 'Add amazing feature'`)
4. Push para a branch (`git push origin feature/amazing`)
5. Abra um Pull Request

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

## ✨ Agradecimentos

- Secretaria de Segurança Pública de Santa Catarina (SSP-SC)
- Comunidade open source de Data Engineering
- Apache Airflow, Terraform e pytest

---

**Desenvolvido para Portfolio de Engenharia de Dados** 🚀

Para dúvidas, abra uma [issue](https://github.com/jeysel/search-ssp-sc/issues) ou entre em contato!

---

## 🚀 Configuração Inicial

### Pré-requisitos

- Docker Desktop instalado e rodando
- Docker Compose disponível
- ~2GB de espaço livre em disco
- Conexão com internet para download de imagens e PDFs

---

## 🐳 Criação dos Containers Docker

### 1. Criar Containers do Zero (Primeira vez)

```bash
cd search-ssp-sc
docker-compose -f docker-compose.yml up -d --build
```

### 2. Verificar se os Containers Estão Rodando

```bash
docker-compose -f docker-compose.yml ps
```

**Saída esperada:**
```
NAME                       STATUS              PORTS
ssp-sc-postgres        Up (healthy)        0.0.0.0:5432->5432/tcp
ssp-sc-extrator        Up
ssp-sc-visualizacao    Up                  0.0.0.0:5000->5000/tcp
```

### 3. Verificar Logs (Se houver problemas)

```bash
# Logs do PostgreSQL
docker logs ssp-sc-postgres --tail 50

# Logs do Extrator
docker logs ssp-sc-extrator --tail 50

# Logs da Visualização
docker logs ssp-sc-visualizacao --tail 50

# Logs em tempo real
docker logs ssp-sc-extrator -f
```

---

## 🔄 Execução da Extração

### Extração TOTAL (Todos os PDFs)

```bash
docker exec ssp-sc-extrator python extractor_ocr_v2.py --limpar
```
### Extração PARCIAL (Teste/Desenvolvimento)

#### Extrair apenas 5 PDFs (Teste Rápido)

```bash
docker exec ssp-sc-extrator python extractor_ocr_v2.py --limpar --limite=5
```

#### Extrair 10 PDFs

```bash
docker exec ssp-sc-extrator python extractor_ocr_v2.py --limpar --limite=10
```

#### Extrair apenas 1 PDF (Debug)

```bash
docker exec ssp-sc-extrator python extractor_ocr_v2.py --limpar --limite=1
```

### Extração SEM Limpar Dados Existentes

```bash
# Processar apenas novos PDFs (não limpa o banco)
docker exec ssp-sc-extrator python extractor_ocr_v2.py

# Com limite
docker exec ssp-sc-extrator python extractor_ocr_v2.py --limite=5
```

### Dashboard Web

```bash
# Acessar via navegador
http://localhost:5000
```
### Como Usar o Dashboard

#### 1. Visualizar Dados no Dashboard

```bash
# 1. Abrir navegador
http://localhost:5000

# 2. Clicar na aba "Dashboard"
# 3. Selecionar filtros desejados
# 4. Visualizar gráficos interativos
```

#### 2. Gerar Relatório Tabular

```bash
# 1. Clicar na aba "Relatórios"
# 2. Configurar filtros:
#    - Categoria: Todas (para ver tudo) ou específica
#    - Município: Selecionar ou deixar "Todos"
#    - Ano: 2025, 2024, etc.
#    - Mês: Opcional
# 3. Clicar em "Gerar Relatório"
```

#### 3. Exportar Relatório

**Para Excel/Análise:**
```bash
# 1. Gerar relatório (conforme acima)
# 2. Clicar em "Exportar CSV"
# 3. Arquivo baixado: relatorio_ssp_sc_YYYY-MM-DDTHH-MM-SS.csv
# 4. Abrir no Excel ou Google Sheets
```

**Para Impressão/Apresentação:**
```bash
# 1. Gerar relatório (conforme acima)
# 2. Clicar em "Exportar PDF"
# 3. Arquivo baixado: relatorio_ssp_sc_YYYY-MM-DDTHH-MM-SS.pdf
# 4. Abrir com Adobe Reader ou navegador
```

### API REST

#### Health Check

```bash
curl http://localhost:5000/health
```

**Resposta esperada:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-05T14:30:00"
}
```

---

#### Estatísticas Gerais

```bash
curl http://localhost:5000/api/estatisticas
```

**Resposta:**
```json
{
  "estatisticas": {
    "total_registros": 1445,
    "total_ocorrencias": 5797,
    "municipios_afetados": 58,
    "media_por_municipio": 99.95
  }
}


