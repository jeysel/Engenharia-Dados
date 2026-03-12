# Como Usar o projeto Data Warehouse.

---
## 🚀 Configuração Inicial

### Pré-requisitos

- Docker Desktop instalado e rodando
- AirByte + DBT + BigQuery configurados
- Docker Compose disponível
- ~2GB de espaço livre em disco
- Conexão com internet para download de imagens e PDFs

---

## 🐳 Criação dos Containers Docker

### 1. Criar Container para executar o Airbyte localmente (Maquina com Windows 11)

Acessar o link: https://docs.airbyte.com/using-airbyte/getting-started/oss-quickstart?_gl=1*1uywmn1*_gcl_au*MTU0OTM4MDYyMi4xNzMyNzk5MTYx

Executar os passos em ordem:
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






