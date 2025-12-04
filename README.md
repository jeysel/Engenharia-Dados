# Engenharia-Dados
Projetos de engenharia de dados para estudo

---

## 📁 Conteiner Docker/Linux para utilizar todos os projetos
....
....
.....

## 🔐 Configuração de Segurança
**IMPORTANTE**: Este repositório contém projetos que utilizam APIs e credenciais.

### Antes de executar os projetos:

1. **Configure as variáveis de ambiente**:
   - Copie os arquivos `.env.example` para `.env` em cada projeto
   - Preencha as credenciais necessárias
   - **NUNCA** commite arquivos `.env` no Git

2. **Arquivos de exemplo disponíveis**:
   - `ETL-Real-Time/servidor/.env.example`
   - `search-ssp-sc/extrator/.env.example`
   - `search-ssp-sc/visualizacao/.env.example`

3. **Credenciais necessárias**:
   - **ETL-Real-Time**: Token JWT do dados.gov.br
   - **search-ssp-sc**: Credenciais PostgreSQL (ambiente Docker)

---

## 🚀 Como Começar

Consulte a documentação específica de cada projeto para instruções detalhadas de instalação e uso.


## 📁 Projetos

### 1. ETL-Real-Time
Pipeline ETL em tempo real para dados de segurança pública (SINESP) usando Apache Airflow, Kafka, Spark Streaming e Cassandra.

**Fonte**: [dados.gov.br](https://dados.gov.br/)
**Documentação**: [ETL-Real-Time\Guia-Execução.md](ETL-Real-Time\Guia-Execução.md)

### 2. search-ssp-sc
Sistema de extração de dados de segurança pública com OCR para processar relatórios em PDF da SSP/SC.

**Fonte**: [SSP/SC - Segurança em Números](https://ssp.sc.gov.br/segurancaemnumeros/)
**Documentação**: [search-ssp-sc\Como-Usar.md](search-ssp-sc\Como-Usar.md)

---



