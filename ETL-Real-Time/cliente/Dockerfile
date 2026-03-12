# Usa imagem oficial do Apache Spark
FROM apache/spark:3.5.0

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
RUN chmod -R 755 /app

# Configura diretório de trabalho
WORKDIR /app

# Define variáveis de ambiente
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

# Comando padrão (será sobrescrito pelo docker-compose)
CMD ["/opt/spark/bin/spark-submit", "--help"]