# Como Usar - Sistema de Extração SSP-SC

Guia rápido de comandos para operação do sistema de extração de dados da SSP-SC com OCR.

---

## 📋 Índice

1. [Configuração Inicial](#configuração-inicial)
2. [Criação dos Containers Docker](#criação-dos-containers-docker)
3. [Execução da Extração](#execução-da-extração)
4. [Consulta de Dados](#consulta-de-dados)
5. [Manutenção e Troubleshooting](#manutenção-e-troubleshooting)

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
docker-compose -f docker-compose_new.yml up -d --build
```

**O que este comando faz:**
- Cria e inicia 3 containers: PostgreSQL, Extrator e Visualização
- Instala todas as dependências (incluindo Tesseract OCR)
- Cria o banco de dados e tabelas
- Tempo estimado: ~5-10 minutos

### 2. Verificar se os Containers Estão Rodando

```bash
docker-compose -f docker-compose_new.yml ps
```

**Saída esperada:**
```
NAME                       STATUS              PORTS
ssp-sc-postgres-new        Up (healthy)        0.0.0.0:5432->5432/tcp
ssp-sc-extrator-new        Up
ssp-sc-visualizacao-new    Up                  0.0.0.0:5000->5000/tcp
```

### 3. Verificar Logs (Se houver problemas)

```bash
# Logs do PostgreSQL
docker logs ssp-sc-postgres-new --tail 50

# Logs do Extrator
docker logs ssp-sc-extrator-new --tail 50

# Logs da Visualização
docker logs ssp-sc-visualizacao-new --tail 50

# Logs em tempo real
docker logs ssp-sc-extrator-new -f
```

---

## 🔄 Execução da Extração

### Extração TOTAL (Todos os PDFs)

```bash
docker exec ssp-sc-extrator-new python extractor_ocr_v2.py --limpar
```

**Detalhes:**
- Processa todos os 32 PDFs disponíveis (10 de 2025 + 22 de 2024)
- Limpa dados existentes antes de começar (`--limpar`)
- Tempo estimado: **~24 minutos**
- Registros esperados: **~9.280 registros**
- Usa OCR para extrair dados de todas as páginas

**Quando usar:**
- ✅ Primeira execução do sistema
- ✅ Atualização mensal completa
- ✅ Após correções no código
- ✅ Para popular banco de dados vazio

---

### Extração PARCIAL (Teste/Desenvolvimento)

#### Extrair apenas 5 PDFs (Teste Rápido)

```bash
docker exec ssp-sc-extrator-new python extractor_ocr_v2.py --limpar --limite=5
```

**Detalhes:**
- Processa apenas os primeiros 5 PDFs
- Tempo estimado: **~3-4 minutos**
- Registros esperados: **~1.450 registros**

**Quando usar:**
- ✅ Testar funcionamento do sistema
- ✅ Validar alterações no código
- ✅ Desenvolvimento/debugging

---

#### Extrair 10 PDFs

```bash
docker exec ssp-sc-extrator-new python extractor_ocr_v2.py --limpar --limite=10
```

**Detalhes:**
- Tempo estimado: **~7-8 minutos**
- Registros esperados: **~2.900 registros**

---

#### Extrair apenas 1 PDF (Debug)

```bash
docker exec ssp-sc-extrator-new python extractor_ocr_v2.py --limpar --limite=1
```

**Detalhes:**
- Tempo estimado: **~45 segundos**
- Registros esperados: **~290 registros**

**Quando usar:**
- ✅ Debugging detalhado
- ✅ Testar alterações específicas
- ✅ Verificar estrutura dos dados

---

### Extração SEM Limpar Dados Existentes

```bash
# Processar apenas novos PDFs (não limpa o banco)
docker exec ssp-sc-extrator-new python extractor_ocr_v2.py

# Com limite
docker exec ssp-sc-extrator-new python extractor_ocr_v2.py --limite=5
```

**Quando usar:**
- ✅ Atualização incremental
- ✅ Adicionar novos PDFs sem perder histórico
- ⚠️ Cuidado: pode gerar duplicatas

---

## 📊 Consulta de Dados

### Dashboard Web

```bash
# Acessar via navegador
http://localhost:5000
```

**Recursos disponíveis:**
- 📈 Gráficos interativos
- 🔍 Filtros por município, ano, categoria
- 📊 Estatísticas gerais
- 📜 Histórico de execuções

---

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
```

---

#### Dados de Homicídios

```bash
# Todos os dados
curl http://localhost:5000/api/dados?categoria=homicidio

# Com limite
curl "http://localhost:5000/api/dados?categoria=homicidio&limite=10"
```

---

#### Filtros Disponíveis

```bash
curl http://localhost:5000/api/filtros
```

---

### Consultas SQL Diretas

#### Contar Registros

```bash
docker exec ssp-sc-postgres-new psql -U user -d ssp_sc_db -c "
SELECT 'homicidio' as tabela, COUNT(*) FROM homicidio
UNION ALL SELECT 'roubo', COUNT(*) FROM roubo
UNION ALL SELECT 'furto', COUNT(*) FROM furto
UNION ALL SELECT 'mortes_violentas', COUNT(*) FROM mortes_violentas;
"
```

---

#### Ver Dados de um Município Específico

```bash
docker exec ssp-sc-postgres-new psql -U user -d ssp_sc_db -c "
SELECT municipio, ano, quantidade
FROM homicidio
WHERE municipio = 'FLORIANÓPOLIS'
ORDER BY ano;
"
```

---

#### Top 10 Municípios com Mais Homicídios

```bash
docker exec ssp-sc-postgres-new psql -U user -d ssp_sc_db -c "
SELECT municipio, SUM(quantidade) as total_vitimas
FROM homicidio
GROUP BY municipio
ORDER BY total_vitimas DESC
LIMIT 10;
"
```

---

#### Ver Amostras dos Dados

```bash
docker exec ssp-sc-postgres-new psql -U user -d ssp_sc_db -c "
SELECT * FROM homicidio LIMIT 20;
"
```

---

#### Estatísticas por Ano

```bash
docker exec ssp-sc-postgres-new psql -U user -d ssp_sc_db -c "
SELECT ano, COUNT(DISTINCT municipio) as municipios, SUM(quantidade) as total_vitimas
FROM homicidio
GROUP BY ano
ORDER BY ano;
"
```

---

## 🛠️ Manutenção e Troubleshooting

### Reiniciar Containers

```bash
# Reiniciar todos
docker-compose -f docker-compose_new.yml restart

# Reiniciar apenas um
docker restart ssp-sc-extrator-new
docker restart ssp-sc-postgres-new
docker restart ssp-sc-visualizacao-new
```

---

### Parar Containers

```bash
docker-compose -f docker-compose_new.yml stop
```

---

### Remover Containers (Mantém dados)

```bash
docker-compose -f docker-compose_new.yml down
```

---

### Remover TUDO (Inclui volumes/dados)

```bash
# ⚠️ CUIDADO: Remove todos os dados do banco!
docker-compose -f docker-compose_new.yml down -v
```

---

### Rebuild Completo (Após alterações no código)

```bash
# Parar containers
docker-compose -f docker-compose_new.yml down

# Rebuild
docker-compose -f docker-compose_new.yml build

# Iniciar
docker-compose -f docker-compose_new.yml up -d
```

---

### Limpar Dados do Banco (Sem remover containers)

```bash
docker exec ssp-sc-postgres-new psql -U user -d ssp_sc_db -c "
TRUNCATE TABLE roubo, furto, mortes_violentas, homicidio, violencia_domestica, historico_execucao CASCADE;
"
```

---

### Entrar no Container para Debug

```bash
# Container do Extrator
docker exec -it ssp-sc-extrator-new bash

# Container do PostgreSQL
docker exec -it ssp-sc-postgres-new psql -U user -d ssp_sc_db

# Container da Visualização
docker exec -it ssp-sc-visualizacao-new bash
```

---

### Ver Histórico de Execuções

```bash
docker exec ssp-sc-postgres-new psql -U user -d ssp_sc_db -c "
SELECT
    id,
    tipo_dados,
    status,
    registros_inseridos,
    data_hora_inicio,
    data_hora_fim,
    mensagem
FROM historico_execucao
ORDER BY data_hora_inicio DESC
LIMIT 10;
"
```

---

### Backup do Banco de Dados

```bash
# Criar backup
docker exec ssp-sc-postgres-new pg_dump -U user ssp_sc_db > backup_ssp_sc_$(date +%Y%m%d).sql

# Restaurar backup
docker exec -i ssp-sc-postgres-new psql -U user -d ssp_sc_db < backup_ssp_sc_20251105.sql
```

---

## 📝 Comandos Úteis Resumidos

### Setup Inicial (Primeira vez)

```bash
cd search-ssp-sc
docker-compose -f docker-compose_new.yml up -d --build
docker exec ssp-sc-extrator-new python extractor_ocr_v2.py --limpar --limite=5
```

---

### Uso Diário

```bash
# Verificar status
docker-compose -f docker-compose_new.yml ps

# Extrair dados (teste)
docker exec ssp-sc-extrator-new python extractor_ocr_v2.py --limpar --limite=5

# Acessar dashboard
http://localhost:5000

# Ver dados
curl http://localhost:5000/api/estatisticas
```

---

### Atualização Mensal

```bash
# Extração completa
docker exec ssp-sc-extrator-new python extractor_ocr_v2.py --limpar

# Verificar resultado
curl http://localhost:5000/api/estatisticas
```

---

### Debug

```bash
# Ver logs
docker logs ssp-sc-extrator-new -f

# Extrair 1 PDF
docker exec ssp-sc-extrator-new python extractor_ocr_v2.py --limpar --limite=1

# Entrar no container
docker exec -it ssp-sc-extrator-new bash
```

---

## 🎯 Fluxo de Trabalho Recomendado

### 1️⃣ Primeira Execução

```bash
# 1. Criar containers
cd search-ssp-sc
docker-compose -f docker-compose_new.yml up -d --build

# 2. Aguardar containers subirem (~2 min)
docker-compose -f docker-compose_new.yml ps

# 3. Teste com 5 PDFs
docker exec ssp-sc-extrator-new python extractor_ocr_v2.py --limpar --limite=5

# 4. Verificar resultado
curl http://localhost:5000/api/estatisticas

# 5. Acessar dashboard
http://localhost:5000

# 6. Extração completa (se teste OK)
docker exec ssp-sc-extrator-new python extractor_ocr_v2.py --limpar
```

---

### 2️⃣ Uso Regular

```bash
# Verificar status
docker-compose -f docker-compose_new.yml ps

# Extração completa mensal
docker exec ssp-sc-extrator-new python extractor_ocr_v2.py --limpar

# Acessar dados
http://localhost:5000
```

---

### 3️⃣ Desenvolvimento/Teste

```bash
# Rebuild após alteração
docker-compose -f docker-compose_new.yml build extrator
docker-compose -f docker-compose_new.yml up -d extrator

# Teste rápido
docker exec ssp-sc-extrator-new python extractor_ocr_v2.py --limpar --limite=1

# Ver logs
docker logs ssp-sc-extrator-new -f
```

---

## 📞 Suporte

### Logs Completos

```bash
# Extrator
docker logs ssp-sc-extrator-new > extrator.log

# PostgreSQL
docker logs ssp-sc-postgres-new > postgres.log

# Visualização
docker logs ssp-sc-visualizacao-new > visualizacao.log
```

---

### Informações do Sistema

```bash
# Versão do Docker
docker --version

# Espaço em disco
docker system df

# Containers rodando
docker ps

# Imagens disponíveis
docker images | grep ssp-sc
```

---

## ⚠️ Avisos Importantes

1. **Sempre use `--limpar` na primeira extração** para garantir dados limpos
2. **Extração completa demora ~24 minutos** - seja paciente
3. **Não interrompa extração no meio** - pode gerar dados inconsistentes
4. **Dashboard está em http://localhost:5000** - não https://
5. **Backup regular** do banco de dados é recomendado


