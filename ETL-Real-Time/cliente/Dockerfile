# Usa imagem oficial do Bitnami Spark que já tem tudo configurado
FROM bitnami/spark:3.5.4

# Muda para usuário root para instalar dependências
USER root

# Instala dependências Python adicionais necessárias para o consumer
RUN pip install --no-cache-dir \
    kafka-python==2.0.2 \
    cassandra-driver==3.29.2

# Cria diretório de trabalho
RUN mkdir -p /app

# Copia o script consumer para o container
COPY consumer_stream.py /app/consumer_stream.py

# Define permissões corretas
RUN chown -R 1001:1001 /app

# Volta para o usuário padrão do Spark
USER 1001

# Configura diretório de trabalho
WORKDIR /app

# Define variáveis de ambiente
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

# Comando padrão (será sobrescrito pelo docker-compose)
CMD ["spark-submit", "--help"]