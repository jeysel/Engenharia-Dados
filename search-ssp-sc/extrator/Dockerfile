FROM python:3.11-slim

# Instalar dependências mínimas do sistema
RUN apt-get update && apt-get install -y \
    curl \
    default-jre \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar diretório para dados
RUN mkdir -p /app/data

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Comando padrão - mantém container rodando para execuções manuais
CMD ["tail", "-f", "/dev/null"]
