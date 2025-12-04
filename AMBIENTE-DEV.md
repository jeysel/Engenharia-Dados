# Ambiente de Desenvolvimento Ubuntu

Este é um ambiente Docker completo baseado em Ubuntu para desenvolvimento de todos os projetos de Engenharia de Dados.

## Características

- **Ubuntu 22.04** como base
- **Python 3** com pip e bibliotecas comuns (requests, pandas, flask, etc)
- **Node.js e npm** para projetos web
- **Docker-in-Docker** - Execute containers de projetos específicos de dentro do container
- **Git configurado** para commits e push para GitHub
- **Acesso completo** ao repositório montado como volume
- **Persistência** de cache pip e histórico bash

## Pré-requisitos

- Docker Desktop instalado no Windows
- Git configurado localmente

## Configuração Inicial

### 1. Configure suas credenciais

Copie o arquivo de exemplo e edite com suas informações:

```bash
copy .env.example .env
notepad .env
```

Configure:
- `GIT_USER_NAME`: Seu nome completo
- `GIT_USER_EMAIL`: Seu email do GitHub
- `GITHUB_TOKEN`: (Opcional) Token de acesso pessoal do GitHub

**Como gerar o GitHub Token:**
1. Acesse: https://github.com/settings/tokens
2. Clique em "Generate new token (classic)"
3. Selecione as permissões: `repo` (todas)
4. Gere e copie o token
5. Cole no arquivo `.env`

### 2. Construa e inicie o ambiente

```bash
docker-compose -f docker-compose.dev.yml up -d --build
```

Este comando irá:
- Construir a imagem Docker com todas as ferramentas
- Iniciar o container
- Montar o repositório dentro do container

### 3. Acesse o ambiente Ubuntu

```bash
docker exec -it engenharia-dados-dev bash
```

## Uso Diário

### Iniciar o ambiente

```bash
docker-compose -f docker-compose.dev.yml up -d
```

### Acessar o terminal Ubuntu

```bash
docker exec -it engenharia-dados-dev bash
```

### Parar o ambiente

```bash
docker-compose -f docker-compose.dev.yml down
```

### Ver logs do container

```bash
docker-compose -f docker-compose.dev.yml logs -f
```

## Trabalhando com Projetos

### Executar um projeto existente

```bash
# Dentro do container Ubuntu
cd search-ssp-sc
docker-compose -f docker-compose-autonomous.yml up -d
docker-compose logs -f
```

### Criar um novo projeto

```bash
# Dentro do container Ubuntu
mkdir meu-novo-projeto
cd meu-novo-projeto

# Crie seus arquivos
nano app.py
nano Dockerfile
nano docker-compose.yml

# Execute o projeto
docker-compose up -d
```

### Trabalhar com Git

```bash
# Ver status
git status

# Adicionar arquivos
git add .

# Commitar
git commit -m "Descrição das alterações"

# Enviar para GitHub
git push origin main

# Criar novo branch
git checkout -b feature/nova-funcionalidade

# Enviar novo branch
git push -u origin feature/nova-funcionalidade
```

### Instalar pacotes Python

```bash
# Instalar no ambiente global do container
pip3 install nome-do-pacote

# Ou usar venv para projetos específicos
cd meu-projeto
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Estrutura de Pastas

```
Engenharia-Dados/
├── Dockerfile.dev              # Imagem Ubuntu personalizada
├── docker-compose.dev.yml      # Configuração do ambiente dev
├── .env                        # Suas credenciais (não commitado)
├── .env.example                # Modelo de configuração
├── search-ssp-sc/             # Projeto exemplo
│   ├── docker-compose-autonomous.yml
│   └── ...
└── [outros projetos]/
```

## Comandos Úteis

### Docker

```bash
# Ver containers rodando
docker ps

# Ver logs de um container
docker logs nome-do-container -f

# Parar um projeto
docker-compose down

# Reconstruir imagens
docker-compose build --no-cache
```

### Sistema

```bash
# Ver uso de disco
df -h

# Ver processos
ps aux

# Limpar cache pip
rm -rf ~/.cache/pip/*
```

## Solução de Problemas

### Container não inicia

```bash
# Ver logs
docker-compose -f docker-compose.dev.yml logs

# Reconstruir
docker-compose -f docker-compose.dev.yml up --build
```

### Git não está autenticando

1. Verifique se o `.env` está configurado corretamente
2. Recrie o container:
   ```bash
   docker-compose -f docker-compose.dev.yml down
   docker-compose -f docker-compose.dev.yml up -d --build
   ```
3. Teste: `git config --list` dentro do container

### Docker-in-Docker não funciona

Certifique-se de que o Docker Desktop está rodando no Windows e que o socket está montado corretamente no `docker-compose.dev.yml`.

### Problemas de permissão

No Windows com WSL2, pode haver problemas de permissão. Dentro do container:

```bash
# Dar permissão de execução
chmod +x arquivo.sh

# Mudar proprietário se necessário
chown -R root:root /workspace/pasta
```

## Dicas

1. **Use o histórico persistente**: O histórico do bash é salvo entre sessões
2. **Cache do pip**: Pacotes instalados são cacheados, reinstalações são rápidas
3. **Rede compartilhada**: Todos os projetos usam a mesma rede Docker
4. **Hot reload**: Alterações no código são refletidas imediatamente (volume montado)
5. **Múltiplos terminais**: Você pode abrir várias sessões:
   ```bash
   docker exec -it engenharia-dados-dev bash
   ```

## Próximos Passos

1. Configure o arquivo `.env` com suas credenciais:
   ```bash
   copy .env.example .env
   notepad .env
   ```

2. Construa e inicie o container:
   ```bash
   docker-compose -f docker-compose.dev.yml up -d --build
   ```

3. Entre no ambiente Ubuntu:
   ```bash
   docker exec -it engenharia-dados-dev bash
   ```

4. Navegue pelos projetos e comece a desenvolver!

## Manutenção

### Atualizar imagem base

```bash
# No Windows
docker-compose -f docker-compose.dev.yml build --no-cache
docker-compose -f docker-compose.dev.yml up -d
```

### Limpar volumes não utilizados

```bash
docker volume prune
```

### Fazer backup

Os dados importantes estão no repositório (montado como volume), então basta fazer commit e push regularmente.
