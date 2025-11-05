# Importa o módulo sys para manipulação de argumentos e interação com o sistema
import sys

# Importa o módulo logging para registro de logs
import logging

# Importa o módulo json para manipulação de dados no formato JSON
import json

# Importa o módulo re para manipulação de expressões regulares
import re

# Importa o módulo argparse para manipulação de argumentos da linha de comando
import argparse

# Importa a classe Cluster do Cassandra para criar conexões ao banco de dados
from cassandra.cluster import Cluster

# Importa o módulo SparkSession para criar sessões Spark
from pyspark.sql import SparkSession

# Importa funções do PySpark para manipulação de dados com Spark
from pyspark.sql.functions import from_json, col

# Importa tipos de dados estruturados do PySpark
from pyspark.sql.types import StructType, StructField, StringType

# Configura o logger para exibir mensagens de log com nível INFO
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Função para criar um keyspace no Cassandra
def cria_keyspace(session):

    # Executa a instrução a partir da sessão recebida como argumento
    session.execute(
        """
        CREATE KEYSPACE IF NOT EXISTS dados_seguranca_publica
        WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'};
        """
    )

    print("Keyspace criado com sucesso!")

# Função para criar tabelas no Cassandra para dados de segurança pública
def cria_tabela(session):

    # Tabela para ocorrências por município
    session.execute(
        """
        CREATE TABLE IF NOT EXISTS dados_seguranca_publica.tb_ocorrencias_municipio (
            id TEXT PRIMARY KEY,
            dataset_id TEXT,
            resource_id TEXT,
            granularidade TEXT,
            ano TEXT,
            mes TEXT,
            mes_ano TEXT,
            uf TEXT,
            uf_nome TEXT,
            codigo_municipio TEXT,
            municipio TEXT,
            regiao TEXT,
            tipo_crime TEXT,
            vitimas TEXT,
            ocorrencias TEXT,
            homicidio_doloso TEXT,
            lesao_corp_morte TEXT,
            latrocinio TEXT,
            roubo_veiculo TEXT,
            roubo_carga TEXT,
            roubo_inst_financeira TEXT,
            furto_veiculo TEXT,
            estupro TEXT,
            data_extracao TEXT
        );
        """
    )

    # Tabela para ocorrências por estado
    session.execute(
        """
        CREATE TABLE IF NOT EXISTS dados_seguranca_publica.tb_ocorrencias_estado (
            id TEXT PRIMARY KEY,
            dataset_id TEXT,
            resource_id TEXT,
            granularidade TEXT,
            ano TEXT,
            mes TEXT,
            mes_ano TEXT,
            uf TEXT,
            uf_nome TEXT,
            tipo_crime TEXT,
            vitimas TEXT,
            ocorrencias TEXT,
            homicidio_doloso TEXT,
            lesao_corp_morte TEXT,
            latrocinio TEXT,
            roubo_veiculo TEXT,
            roubo_carga TEXT,
            roubo_inst_financeira TEXT,
            furto_veiculo TEXT,
            estupro TEXT,
            data_extracao TEXT
        );
        """
    )

    # Tabela geral para outros tipos de dados
    session.execute(
        """
        CREATE TABLE IF NOT EXISTS dados_seguranca_publica.tb_ocorrencias_geral (
            id TEXT PRIMARY KEY,
            dataset_id TEXT,
            resource_id TEXT,
            granularidade TEXT,
            ano TEXT,
            mes TEXT,
            mes_ano TEXT,
            uf TEXT,
            uf_nome TEXT,
            tipo_crime TEXT,
            vitimas TEXT,
            ocorrencias TEXT,
            data_extracao TEXT
        );
        """
    )

    print("Tabelas criadas com sucesso!")

# Função para formatar strings antes de inseri-las no Cassandra
def formata_string_cassandra(text: str):
    return re.sub(r"'", r"''", text)

# Função para inserir dados de ocorrências criminais no Cassandra
def insere_dados(session, row):

    # Formata e extrai campos comuns do registro
    record_id       = formata_string_cassandra(row.id)
    dataset_id      = formata_string_cassandra(row.dataset_id)
    resource_id     = formata_string_cassandra(row.resource_id)
    granularidade   = formata_string_cassandra(row.granularidade)
    ano             = formata_string_cassandra(row.ano)
    mes             = formata_string_cassandra(row.mes)
    mes_ano         = formata_string_cassandra(row.mes_ano)
    uf              = formata_string_cassandra(row.uf)
    uf_nome         = formata_string_cassandra(row.uf_nome)
    tipo_crime      = formata_string_cassandra(row.tipo_crime)
    vitimas         = formata_string_cassandra(row.vitimas)
    ocorrencias     = formata_string_cassandra(row.ocorrencias)
    data_extracao   = formata_string_cassandra(row.data_extracao)

    # Campos de indicadores específicos
    homicidio_doloso        = formata_string_cassandra(row.homicidio_doloso)
    lesao_corp_morte        = formata_string_cassandra(row.lesao_corp_morte)
    latrocinio              = formata_string_cassandra(row.latrocinio)
    roubo_veiculo           = formata_string_cassandra(row.roubo_veiculo)
    roubo_carga             = formata_string_cassandra(row.roubo_carga)
    roubo_inst_financeira   = formata_string_cassandra(row.roubo_inst_financeira)
    furto_veiculo           = formata_string_cassandra(row.furto_veiculo)
    estupro                 = formata_string_cassandra(row.estupro)

    try:
        # Determina a tabela com base na granularidade
        if granularidade == "municipio":
            # Campos adicionais para município
            codigo_municipio = formata_string_cassandra(row.codigo_municipio)
            municipio        = formata_string_cassandra(row.municipio)
            regiao           = formata_string_cassandra(row.regiao)

            # Query para tabela de municípios
            query = f"""
                INSERT INTO dados_seguranca_publica.tb_ocorrencias_municipio(
                    id, dataset_id, resource_id, granularidade, ano, mes, mes_ano, uf, uf_nome,
                    codigo_municipio, municipio, regiao, tipo_crime, vitimas, ocorrencias,
                    homicidio_doloso, lesao_corp_morte, latrocinio, roubo_veiculo, roubo_carga,
                    roubo_inst_financeira, furto_veiculo, estupro, data_extracao
                ) VALUES (
                    '{record_id}', '{dataset_id}', '{resource_id}', '{granularidade}', '{ano}', '{mes}', '{mes_ano}',
                    '{uf}', '{uf_nome}', '{codigo_municipio}', '{municipio}', '{regiao}', '{tipo_crime}',
                    '{vitimas}', '{ocorrencias}', '{homicidio_doloso}', '{lesao_corp_morte}', '{latrocinio}',
                    '{roubo_veiculo}', '{roubo_carga}', '{roubo_inst_financeira}', '{furto_veiculo}',
                    '{estupro}', '{data_extracao}'
                )
            """

        elif granularidade == "estado":
            # Query para tabela de estados
            query = f"""
                INSERT INTO dados_seguranca_publica.tb_ocorrencias_estado(
                    id, dataset_id, resource_id, granularidade, ano, mes, mes_ano, uf, uf_nome,
                    tipo_crime, vitimas, ocorrencias, homicidio_doloso, lesao_corp_morte, latrocinio,
                    roubo_veiculo, roubo_carga, roubo_inst_financeira, furto_veiculo, estupro, data_extracao
                ) VALUES (
                    '{record_id}', '{dataset_id}', '{resource_id}', '{granularidade}', '{ano}', '{mes}', '{mes_ano}',
                    '{uf}', '{uf_nome}', '{tipo_crime}', '{vitimas}', '{ocorrencias}', '{homicidio_doloso}',
                    '{lesao_corp_morte}', '{latrocinio}', '{roubo_veiculo}', '{roubo_carga}',
                    '{roubo_inst_financeira}', '{furto_veiculo}', '{estupro}', '{data_extracao}'
                )
            """

        else:
            # Query para tabela geral
            query = f"""
                INSERT INTO dados_seguranca_publica.tb_ocorrencias_geral(
                    id, dataset_id, resource_id, granularidade, ano, mes, mes_ano, uf, uf_nome,
                    tipo_crime, vitimas, ocorrencias, data_extracao
                ) VALUES (
                    '{record_id}', '{dataset_id}', '{resource_id}', '{granularidade}', '{ano}', '{mes}', '{mes_ano}',
                    '{uf}', '{uf_nome}', '{tipo_crime}', '{vitimas}', '{ocorrencias}', '{data_extracao}'
                )
            """

        # Insere dados formatados na tabela apropriada do Cassandra
        session.execute(query)

        if granularidade == "municipio":
            logging.info(f" Log - Dados inseridos: {record_id} - {municipio}/{uf} - {tipo_crime} - {ocorrencias} ocorrências")
        else:
            logging.info(f" Log - Dados inseridos: {record_id} - {uf} - {tipo_crime} - {ocorrencias} ocorrências")

    except Exception as e:
        # Exibe erro no caso de falha ao inserir os dados
        logging.error(f" Log - Os dados não podem ser inseridos devido ao erro: {e}")
        print(f" Log - Esta é a query:\n{query}")

# Função para criar uma conexão Spark
def cria_spark_connection():

    try:
        # Configura e cria a conexão com o Spark
        s_conn = (
            SparkSession.builder.appName("Projeto")
            .master("spark://spark-master:7077")
            .config(
                "spark.jars.packages",
                "com.datastax.spark:spark-cassandra-connector_2.12:3.4.1,"
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1",
            )
            .config("spark.cassandra.connection.host", "cassandra")
            .config("spark.cassandra.connection.port", "9042")
            .config("spark.executor.memory", "1g")
            .config("spark.executor.cores", "1")
            .config("spark.cores.max", "2")
            .getOrCreate()
        )

        # Define o nível de log
        s_conn.sparkContext.setLogLevel("ERROR")
        logging.info(" Log - Spark Connection criada com sucesso!")
        return s_conn
    except Exception as e:
        logging.error(f" Log - Não foi possível criar a Spark Connection devido ao erro: {e}")
        return None

# Função para criar uma conexão com o Kafka no Spark
def cria_kafka_connection(spark_conn, stream_mode, topicos):

    try:
        # Configura e cria um DataFrame Spark para leitura de dados do Kafka
        # Subscreve múltiplos tópicos separados por vírgula
        spark_df = (
            spark_conn.readStream.format("kafka")
            .option("kafka.bootstrap.servers", "broker:29092")
            .option("subscribe", topicos)  # Múltiplos tópicos
            .option("startingOffsets", stream_mode)
            .load()
        )
        logging.info(f" Log - Dataframe Kafka criado com sucesso para tópicos: {topicos}")
        return spark_df
    except Exception as e:
        # Exibe um aviso no caso de falha ao criar o DataFrame Kafka
        logging.warning(f" Log - O dataframe Kafka não pôde ser criado devido ao erro: {e}")
        return None

# Função para criar um DataFrame estruturado a partir dos dados do Kafka
def cria_df_from_kafka(spark_df):

    # Define o esquema dos dados de segurança pública recebidos no formato JSON
    schema = StructType(
        [
            StructField("id", StringType(), True),
            StructField("dataset_id", StringType(), True),
            StructField("resource_id", StringType(), True),
            StructField("granularidade", StringType(), True),
            StructField("ano", StringType(), True),
            StructField("mes", StringType(), True),
            StructField("mes_ano", StringType(), True),
            StructField("uf", StringType(), True),
            StructField("uf_nome", StringType(), True),
            StructField("codigo_municipio", StringType(), True),
            StructField("municipio", StringType(), True),
            StructField("regiao", StringType(), True),
            StructField("tipo_crime", StringType(), True),
            StructField("vitimas", StringType(), True),
            StructField("ocorrencias", StringType(), True),
            StructField("homicidio_doloso", StringType(), True),
            StructField("lesao_corp_morte", StringType(), True),
            StructField("latrocinio", StringType(), True),
            StructField("roubo_veiculo", StringType(), True),
            StructField("roubo_carga", StringType(), True),
            StructField("roubo_inst_financeira", StringType(), True),
            StructField("furto_veiculo", StringType(), True),
            StructField("estupro", StringType(), True),
            StructField("data_extracao", StringType(), True),
        ]
    )

    # Processa os dados do Kafka para extrair os registros de segurança pública
    return (
        spark_df.selectExpr("CAST(value AS STRING)")            # Converte os dados para string
        .select(from_json(col("value"), schema).alias("data"))  # Converte JSON para colunas estruturadas
        .select("data.*")                                       # Extrai todas as colunas do campo "data"
        .filter(col("id").isNotNull())                          # Filtra registros com ID válido
    )

# Função para criar uma conexão com o Cassandra
def cria_cassandra_connection():

    try:
        # Cria um cluster e retorna a sessão de conexão com o Cassandra
        cluster = Cluster(["cassandra"])
        return cluster.connect()
    except Exception as e:
        # Exibe um erro no caso de falha ao conectar ao Cassandra
        logging.error(f" Log - Não foi possível criar a conexão Cassandra devido ao erro: {e}")
        return None

# Ponto de entrada principal do programa
if __name__ == "__main__":
    
    # Configura o parser para argumentos de linha de comando
    parser = argparse.ArgumentParser(description = "Real Time ETL.")
    
    # Adiciona o argumento para o modo de consumo dos dados
    parser.add_argument(
        "--mode",
        required=True,
        help="Modo de consumo dos dados",
        choices=["initial", "append"],
        default="append",
    )

    # Analisa os argumentos fornecidos
    args = parser.parse_args()

    # Define o modo de consumo com base no argumento fornecido
    stream_mode = "earliest" if args.mode == "initial" else "latest"

    # Define os tópicos Kafka para consumir dados de segurança pública
    # TEMPORÁRIO: Consumindo apenas município enquanto testa com dados de exemplo
    topicos_kafka = "sinesp_ocorrencias_municipio"

    # Cria conexões com o Cassandra e Spark
    session = cria_cassandra_connection()
    spark_conn = cria_spark_connection()

    # Se tiver sessão criada
    if session and spark_conn:

        # Cria o keyspace e as tabelas no Cassandra
        cria_keyspace(session)
        cria_tabela(session)

        # Cria uma conexão com o Kafka e obtém um DataFrame
        kafka_df = cria_kafka_connection(spark_conn, stream_mode, topicos_kafka)

        if kafka_df:

            # Cria um DataFrame estruturado a partir dos dados do Kafka
            structured_df = cria_df_from_kafka(kafka_df)

            # Função para processar lotes de dados de segurança pública
            def process_batch(batch_df, batch_id):

                # Loga informações sobre o lote
                logging.info(f" Log - Processando batch {batch_id} com {batch_df.count()} registros")

                # Itera sobre as linhas do lote e insere os dados no Cassandra
                for row in batch_df.collect():
                    insere_dados(session, row)

            # Configura o processamento contínuo do DataFrame estruturado
            query = (
                structured_df.writeStream
                .foreachBatch(process_batch)  # Define o processamento por lote
                .start()                      # Inicia o processamento
            )

            logging.info(" Log - Streaming iniciado. Aguardando dados de segurança pública...")

            # Aguarda a conclusão do fluxo
            query.awaitTermination()

