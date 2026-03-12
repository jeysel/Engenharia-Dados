# Como Usar o projeto Data Warehouse.

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


## 📦 Componentes

### 1. Procedure

### 2. Functions

### 3. Relatórios

### 4. SCDS



## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.




