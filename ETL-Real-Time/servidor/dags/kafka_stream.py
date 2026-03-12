# Importa o módulo `uuid` para gerar identificadores únicos universais
import uuid

# Importa classes relacionadas a data e hora
from datetime import datetime, timedelta

# Importa as classes principais do Airflow para criar DAGs
from airflow import DAG

# Importa o operador Python do Airflow para execução de funções Python como tarefas
from airflow.operators.python import PythonOperator

# Define os argumentos padrão da DAG, incluindo o proprietário e a data de início
default_args = {"owner": "Engenharia de Dados",
                "start_date": datetime(2025, 1, 9, 8, 10)}

# Define a função que obtém metadados do dataset SINESP
def obtem_metadados_dataset(api_token=None):

    # Importa o módulo `requests` para fazer requisições HTTP
    import requests
    import os

    # URL da nova API do dados.gov.br (API atualizada)
    url = "https://dados.gov.br/dados/api/publico/conjuntos-dados/sistema-nacional-de-estatisticas-de-seguranca-publica"

    # Define os headers da requisição
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    # Adicionar token se fornecido via parâmetro ou variável de ambiente
    if api_token:
        headers['Authorization'] = f'Bearer {api_token}'
    elif os.getenv('DADOS_GOV_BR_TOKEN'):
        headers['Authorization'] = f'Bearer {os.getenv("DADOS_GOV_BR_TOKEN")}'

    try:
        # Faz uma requisição GET para obter metadados do dataset SINESP
        res = requests.get(url, headers=headers, timeout=30)

        # Verifica se o retorno é JSON válido
        if res.status_code == 200 and 'application/json' in res.headers.get('Content-Type', ''):
            data = res.json()
            return data
        else:
            print(f"Erro: Status {res.status_code}, Content-Type: {res.headers.get('Content-Type')}")
            return None
    except Exception as e:
        print(f"Erro ao obter metadados: {e}")
        return None


# Define a função que gera dados de exemplo para testes (fallback quando API falha)
def gera_dados_exemplo():
    import random

    # Lista de UFs e municípios de exemplo
    exemplos = [
        {"uf": "SP", "uf_nome": "São Paulo", "municipio": "São Paulo", "codigo_municipio": "3550308", "regiao": "Sudeste"},
        {"uf": "RJ", "uf_nome": "Rio de Janeiro", "municipio": "Rio de Janeiro", "codigo_municipio": "3304557", "regiao": "Sudeste"},
        {"uf": "MG", "uf_nome": "Minas Gerais", "municipio": "Belo Horizonte", "codigo_municipio": "3106200", "regiao": "Sudeste"},
        {"uf": "BA", "uf_nome": "Bahia", "municipio": "Salvador", "codigo_municipio": "2927408", "regiao": "Nordeste"},
        {"uf": "PR", "uf_nome": "Paraná", "municipio": "Curitiba", "codigo_municipio": "4106902", "regiao": "Sul"},
    ]

    dados = []
    for exemplo in exemplos[:5]:  # Gera 5 registros de exemplo
        registro = {
            "ano": "2024",
            "mes": str(random.randint(1, 12)),
            "mes_ano": f"{random.randint(1, 12)}/2024",
            "uf": exemplo["uf"],
            "uf_nome": exemplo["uf_nome"],
            "municipio": exemplo["municipio"],
            "codigo_municipio": exemplo["codigo_municipio"],
            "regiao": exemplo["regiao"],
            "tipo_crime": "Roubo",
            "vitimas": str(random.randint(50, 500)),
            "ocorrencias": str(random.randint(100, 1000)),
            "homicidio_doloso": str(random.randint(10, 100)),
            "lesao_corp_morte": str(random.randint(5, 50)),
            "latrocinio": str(random.randint(1, 20)),
            "roubo_veiculo": str(random.randint(100, 500)),
            "roubo_carga": str(random.randint(20, 100)),
            "roubo_inst_financeira": str(random.randint(1, 10)),
            "furto_veiculo": str(random.randint(50, 300)),
            "estupro": str(random.randint(5, 50)),
        }
        dados.append(registro)

    return {
        "resource_name": "dados_exemplo_municipio",
        "resource_id": "exemplo_001",
        "resource_format": "CSV",
        "dataset_id": "sistema-nacional-de-estatisticas-de-seguranca-publica",
        "dados": dados
    }

# Define a função que extrai dados reais de ocorrências criminais dos recursos CSV/JSON
def extrai_dados_api():

    # Importa os módulos necessários
    import requests
    import csv
    import io
    import logging
    import os

    # Obtém os metadados do dataset
    dataset = obtem_metadados_dataset()

    if dataset is None:
        # Loga erro detalhado quando a API falhar
        logging.error(" Log - ERRO: Falha ao obter metadados do dataset da API dados.gov.br")
        logging.error(" Log - Verifique se o token de autenticação está configurado corretamente")
        logging.error(" Log - Token atual: %s", "Configurado" if os.getenv('DADOS_GOV_BR_TOKEN') else "Não configurado")
        return None

    # Procura por recursos CSV ou JSON disponíveis
    resources = dataset.get("resources", [])

    if not resources:
        logging.error(" Log - ERRO: Nenhum recurso encontrado no dataset")
        return None

    # Filtra recursos de municípios em formato CSV (prioridade)
    csv_resources = [r for r in resources if r.get("format", "").upper() == "CSV"
                     and "municip" in r.get("name", "").lower()]

    if not csv_resources:
        # Se não encontrar CSV de municípios, tenta qualquer CSV
        csv_resources = [r for r in resources if r.get("format", "").upper() == "CSV"]

    if not csv_resources:
        logging.error(" Log - ERRO: Nenhum recurso CSV encontrado no dataset")
        logging.error(" Log - Recursos disponíveis: %s", [r.get("format") for r in resources])
        return None

    # Seleciona o primeiro recurso CSV disponível
    resource = csv_resources[0]
    resource_url = resource.get("url", "")

    if not resource_url:
        logging.error(" Log - ERRO: URL do recurso CSV não encontrada")
        return None

    try:
        # Faz o download do arquivo CSV
        logging.info(f" Log - Baixando dados do recurso: {resource.get('name', 'desconhecido')}")
        response = requests.get(resource_url, timeout=60)
        response.raise_for_status()

        # Decodifica o conteúdo CSV
        csv_content = response.content.decode('utf-8-sig')
        csv_reader = csv.DictReader(io.StringIO(csv_content), delimiter=';')

        # Converte para lista de dicionários e retorna os primeiros registros
        # Limita a 10 registros por requisição para não sobrecarregar o sistema
        dados = []
        for i, row in enumerate(csv_reader):
            if i >= 10:  # Limita a 10 registros por vez
                break
            dados.append(row)

        if not dados:
            logging.warning(" Log - AVISO: Arquivo CSV baixado está vazio ou sem dados válidos")
            return None

        # Retorna os dados junto com metadados do recurso
        logging.info(f" Log - {len(dados)} registros extraídos com sucesso do CSV")
        return {
            "resource_name": resource.get("name", ""),
            "resource_id": resource.get("id", ""),
            "resource_format": resource.get("format", ""),
            "dataset_id": dataset.get("id", ""),
            "dataset_name": dataset.get("name", ""),
            "dados": dados
        }

    except requests.exceptions.RequestException as e:
        logging.error(f" Log - ERRO: Falha na requisição HTTP ao baixar CSV: {e}")
        return None
    except Exception as e:
        logging.error(f" Log - ERRO: Falha ao processar dados do CSV: {e}")
        import traceback
        logging.error(f" Log - Traceback: {traceback.format_exc()}")
        return None

# Define a função que formata os dados de ocorrências criminais
def formata_dados(res):

    # Verifica se res é None ou não contém dados
    if res is None or "dados" not in res:
        return None

    # Lista para armazenar todos os registros formatados
    registros_formatados = []

    # Obtém metadados do recurso
    resource_name = res.get("resource_name", "")
    resource_id = res.get("resource_id", "")
    dataset_id = res.get("dataset_id", "")

    # Determina a granularidade baseado no nome do recurso
    granularidade = "municipio" if "municip" in resource_name.lower() else "estado"

    # Processa cada registro de ocorrência criminal
    dados = res.get("dados", [])

    for registro in dados:
        # Cria um dicionário para armazenar o registro formatado
        data = {}

        # Gera um ID único para o registro
        data["id"] = uuid.uuid4().hex

        # Armazena informações de metadados
        data["dataset_id"] = dataset_id
        data["resource_id"] = resource_id
        data["granularidade"] = granularidade

        # Extrai campos comuns (os nomes podem variar, então usa .get() com fallback)
        # Campos temporais
        data["ano"] = registro.get("ano", registro.get("Ano", ""))
        data["mes"] = registro.get("mes", registro.get("Mês", registro.get("mês", "")))
        data["mes_ano"] = registro.get("mes_ano", registro.get("Mês-Ano", ""))

        # Localização
        data["uf"] = registro.get("uf", registro.get("UF", registro.get("sigla_uf", "")))
        data["uf_nome"] = registro.get("uf_nome", registro.get("UF Nome", ""))

        if granularidade == "municipio":
            data["codigo_municipio"] = registro.get("codigo_municipio", registro.get("Código Município", ""))
            data["municipio"] = registro.get("municipio", registro.get("Município", ""))
            data["regiao"] = registro.get("regiao", registro.get("Região", ""))

        # Tipo de crime/ocorrência
        data["tipo_crime"] = registro.get("tipo_crime", registro.get("Tipo Crime", ""))
        data["vitimas"] = registro.get("vitimas", registro.get("Vítimas", registro.get("vítimas", "")))
        data["ocorrencias"] = registro.get("ocorrencias", registro.get("Ocorrências",
                                          registro.get("ocorrências", registro.get("quantidade", ""))))

        # Indicadores específicos (podem variar conforme o dataset)
        # Homicídios
        data["homicidio_doloso"] = registro.get("homicidio_doloso", "")
        data["lesao_corp_morte"] = registro.get("lesao_corp_morte", "")
        data["latrocinio"] = registro.get("latrocinio", "")

        # Roubos
        data["roubo_veiculo"] = registro.get("roubo_veiculo", "")
        data["roubo_carga"] = registro.get("roubo_carga", "")
        data["roubo_inst_financeira"] = registro.get("roubo_inst_financeira", "")

        # Furtos
        data["furto_veiculo"] = registro.get("furto_veiculo", "")

        # Crimes sexuais
        data["estupro"] = registro.get("estupro", "")

        # Timestamp de processamento
        data["data_extracao"] = datetime.now().isoformat()

        # Adiciona o registro formatado à lista
        registros_formatados.append(data)

    # Retorna a lista de registros formatados
    return registros_formatados

# Define a função que faz o streaming de dados para o Kafka
def stream_dados():

    # Importa o módulo `json` para manipular dados JSON
    import json

    # Importa o produtor do Kafka
    from kafka import KafkaProducer

    # Importa o módulo `time` para gerenciar intervalos de tempo
    import time

    # Importa o módulo `logging` para registrar mensagens
    import logging

    try:

        # Cria uma conexão com o broker Kafka
        producer = KafkaProducer(bootstrap_servers = ["broker:29092"], max_block_ms = 5000)

        # Aguarda 5 segundos antes de iniciar o streaming
        time.sleep(5)

        # Loga o sucesso da conexão com o broker Kafka
        logging.info(" Log - Produtor Kafka conectado com sucesso.")

    except Exception as e:

        # Loga qualquer erro ao tentar conectar ao broker Kafka
        logging.error(f" Log - Falha ao conectar ao corretor Kafka: {e}")
        return

    # Define o tempo inicial
    curr_time = time.time()

    # Contador de registros enviados
    total_registros = 0

    # Executa o loop de streaming por 60 segundos
    while True:

        # Verifica se 60 segundos já se passaram
        if time.time() > curr_time + 60:  # 1 minute
            break
        try:

            # Obtém dados de ocorrências criminais da API
            res = extrai_dados_api()

            # Verifica se os dados foram obtidos com sucesso
            if res is None:
                logging.warning(" Log - Nenhum dado de segurança pública encontrado.")
                time.sleep(5)  # Aguarda antes de tentar novamente
                continue

            # Formata os dados extraídos
            registros_formatados = formata_dados(res)

            # Verifica se os dados foram formatados com sucesso
            if registros_formatados is None or len(registros_formatados) == 0:
                logging.warning(" Log - Erro ao formatar dados de segurança pública ou nenhum registro encontrado.")
                time.sleep(5)  # Aguarda antes de tentar novamente
                continue

            # Determina o tópico Kafka baseado na granularidade dos dados
            granularidade = registros_formatados[0].get("granularidade", "indefinido")

            if granularidade == "municipio":
                topico = "sinesp_ocorrencias_municipio"
            elif granularidade == "estado":
                topico = "sinesp_ocorrencias_estado"
            else:
                topico = "sinesp_ocorrencias_geral"

            # Envia cada registro individualmente para o tópico Kafka apropriado
            for registro in registros_formatados:
                # Serializa o registro para JSON
                mensagem = json.dumps(registro, ensure_ascii=False).encode("utf-8")

                # Envia para o tópico Kafka
                producer.send(topico, mensagem)

                # Incrementa o contador
                total_registros += 1

            # Loga o sucesso do envio
            logging.info(f" Log - {len(registros_formatados)} registros de segurança pública enviados para tópico '{topico}'. Total: {total_registros}")

            # Aguarda antes de processar novo lote
            time.sleep(10)

        except Exception as e:

            # Loga qualquer erro durante o streaming de dados
            logging.error(f" Log - Um erro ocorreu: {e}")
            import traceback
            logging.error(f" Log - Traceback: {traceback.format_exc()}")
            time.sleep(5)  # Aguarda antes de tentar novamente
            continue

    # Loga o total de registros processados
    logging.info(f" Log - Streaming finalizado. Total de registros enviados: {total_registros}")

# Define a DAG do Airflow
with DAG("real-time-etl-stack",
         # Define os argumentos padrão da DAG
         default_args=default_args,
         # Define o agendamento da DAG como uma vez por dia
         schedule=timedelta(days=1),
         # Impede a execução retroativa da DAG
         catchup=False,
) as dag:
    # Define a tarefa que faz o streaming de dados
    streaming_task = PythonOperator(task_id="stream_from_api", 
                                    python_callable=stream_dados)




