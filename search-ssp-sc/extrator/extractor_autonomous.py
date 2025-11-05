"""
Extrator Autônomo de Dados da SSP-SC
Sistema leve sem dependência de navegador/Selenium
Funciona como serviço no Ubuntu
"""

import os
import time
import json
import logging
import urllib3
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Desabilitar avisos SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/ssp-sc-extractor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

Base = declarative_base()


class DadosSeguranca(Base):
    """Modelo de dados para armazenar informações de segurança"""
    __tablename__ = 'dados_seguranca'

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_coleta = Column(DateTime, default=datetime.now)
    tipo_ocorrencia = Column(String(200))
    municipio = Column(String(200))
    regiao = Column(String(100))
    periodo = Column(String(100))
    quantidade = Column(Integer)
    ano = Column(Integer)
    mes = Column(Integer, nullable=True)
    dados_brutos = Column(Text)


class SSPSCExtractorAutonomous:
    """Extrator autônomo - sem Selenium, apenas HTTP requests"""

    def __init__(self, db_url: str = None):
        """
        Inicializa o extrator autônomo

        Args:
            db_url: URL de conexão com o banco de dados PostgreSQL
        """
        self.base_url = "https://ssp.sc.gov.br/segurancaemnumeros/"
        self.api_endpoints = []  # Descobrir durante análise
        self.db_url = db_url or os.getenv(
            'DATABASE_URL',
            'postgresql://user:password@localhost:5432/ssp_sc_db'
        )
        self.output_dir = os.getenv('DATA_DIR', '/app/data')

        # Criar diretório de saída
        os.makedirs(self.output_dir, exist_ok=True)

        # Configurar sessão HTTP
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })

        # Inicializar banco de dados
        self._init_database()

    def _init_database(self):
        """Inicializa conexão com banco de dados"""
        try:
            self.engine = create_engine(self.db_url)
            Base.metadata.create_all(self.engine)
            Session = sessionmaker(bind=self.engine)
            self.session_db = Session()
            logger.info("✓ Conexão com banco de dados estabelecida")
        except Exception as e:
            logger.error(f"✗ Erro ao conectar ao banco de dados: {e}")
            self.session_db = None

    def discover_api_endpoints(self) -> List[str]:
        """
        Descobre endpoints de API analisando o HTML/JavaScript da página

        Returns:
            Lista de endpoints descobertos
        """
        endpoints = []

        try:
            logger.info(f"Analisando página: {self.base_url}")
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Procurar por scripts que fazem chamadas de API
            scripts = soup.find_all('script')

            for script in scripts:
                if script.string:
                    content = script.string

                    # Procurar padrões comuns de API
                    import re

                    # Padrão 1: fetch('/api/...') ou fetch("api/...")
                    fetch_patterns = re.findall(r'fetch\([\'"]([^\'"]+)[\'"]', content)
                    endpoints.extend(fetch_patterns)

                    # Padrão 2: axios.get('/api/...') ou $.ajax({url: '...'})
                    axios_patterns = re.findall(r'(?:axios\.get|url:\s*)[\'"]([^\'"]+)[\'"]', content)
                    endpoints.extend(axios_patterns)

                    # Padrão 3: XMLHttpRequest com URLs
                    xhr_patterns = re.findall(r'\.open\([\'"]GET[\'"],\s*[\'"]([^\'"]+)[\'"]', content)
                    endpoints.extend(xhr_patterns)

            # Filtrar apenas endpoints relevantes
            api_endpoints = []
            for endpoint in set(endpoints):
                if any(keyword in endpoint.lower() for keyword in ['api', 'dados', 'data', 'ocorrencia', 'estatistica']):
                    if endpoint.startswith('/'):
                        full_url = f"https://ssp.sc.gov.br{endpoint}"
                    elif endpoint.startswith('http'):
                        full_url = endpoint
                    else:
                        full_url = f"{self.base_url.rstrip('/')}/{endpoint}"

                    api_endpoints.append(full_url)
                    logger.info(f"  Endpoint descoberto: {full_url}")

            # Se não encontrar APIs, tentar URLs comuns
            if not api_endpoints:
                common_endpoints = [
                    f"{self.base_url}api/dados",
                    f"{self.base_url}api/estatisticas",
                    f"{self.base_url}api/ocorrencias",
                    f"{self.base_url}dados.json",
                    f"https://ssp.sc.gov.br/api/seguranca/dados",
                ]
                api_endpoints = common_endpoints

            return api_endpoints

        except Exception as e:
            logger.error(f"Erro ao descobrir endpoints: {e}")
            return []

    def extract_from_html_tables(self, html_content: str) -> List[Dict]:
        """
        Extrai dados de tabelas HTML

        Args:
            html_content: Conteúdo HTML

        Returns:
            Lista de dicionários com dados
        """
        dados_extraidos = []

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            tabelas = soup.find_all('table')

            logger.info(f"  Encontradas {len(tabelas)} tabelas HTML")

            for idx, tabela in enumerate(tabelas):
                try:
                    # Usar pandas para extrair tabela
                    df = pd.read_html(str(tabela))[0]

                    if len(df) == 0:
                        continue

                    # Normalizar nomes de colunas
                    df.columns = [str(col).strip().lower() for col in df.columns]

                    # Converter para lista de dicionários
                    registros = df.to_dict('records')

                    # Processar cada registro
                    for registro in registros:
                        # Tentar identificar colunas relevantes
                        dado_processado = self._process_record(registro)
                        if dado_processado:
                            dados_extraidos.append(dado_processado)

                    logger.info(f"    Tabela {idx}: {len(registros)} registros extraídos")

                except Exception as e:
                    logger.warning(f"    Erro ao processar tabela {idx}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Erro ao extrair tabelas HTML: {e}")

        return dados_extraidos

    def _process_record(self, record: Dict) -> Optional[Dict]:
        """
        Processa um registro bruto e normaliza

        Args:
            record: Registro bruto

        Returns:
            Registro normalizado ou None
        """
        try:
            # Mapear colunas comuns para formato padrão
            mapping = {
                'tipo': 'tipo_ocorrencia',
                'tipo de ocorrência': 'tipo_ocorrencia',
                'tipo de crime': 'tipo_ocorrencia',
                'ocorrência': 'tipo_ocorrencia',
                'crime': 'tipo_ocorrencia',

                'município': 'municipio',
                'cidade': 'municipio',
                'local': 'municipio',

                'região': 'regiao',
                'area': 'regiao',

                'quantidade': 'quantidade',
                'qtd': 'quantidade',
                'total': 'quantidade',
                'valor': 'quantidade',
                'numero': 'quantidade',

                'ano': 'ano',
                'year': 'ano',

                'mês': 'mes',
                'mes': 'mes',
                'month': 'mes',

                'período': 'periodo',
                'periodo': 'periodo',
                'date': 'periodo',
            }

            processed = {}

            # Aplicar mapeamento
            for key, value in record.items():
                key_lower = str(key).strip().lower()
                mapped_key = mapping.get(key_lower, key_lower)
                processed[mapped_key] = value

            # Garantir campos obrigatórios
            if 'tipo_ocorrencia' not in processed:
                processed['tipo_ocorrencia'] = 'Não especificado'

            if 'municipio' not in processed:
                processed['municipio'] = 'Não especificado'

            if 'quantidade' not in processed:
                # Tentar encontrar algum valor numérico
                for value in processed.values():
                    try:
                        processed['quantidade'] = int(value)
                        break
                    except:
                        continue

                if 'quantidade' not in processed:
                    processed['quantidade'] = 1

            # Extrair ano se não estiver presente
            if 'ano' not in processed:
                processed['ano'] = datetime.now().year

            return processed

        except Exception as e:
            logger.debug(f"Erro ao processar registro: {e}")
            return None

    def extract_from_api(self, endpoint: str) -> List[Dict]:
        """
        Tenta extrair dados de um endpoint de API

        Args:
            endpoint: URL do endpoint

        Returns:
            Lista de dados extraídos
        """
        dados = []

        try:
            logger.info(f"  Tentando API: {endpoint}")
            response = self.session.get(endpoint, timeout=30)

            if response.status_code != 200:
                logger.warning(f"    Status {response.status_code}")
                return dados

            # Tentar parsear como JSON
            try:
                json_data = response.json()

                # Se for lista diretamente
                if isinstance(json_data, list):
                    dados = json_data
                # Se for objeto com dados aninhados
                elif isinstance(json_data, dict):
                    for key in ['data', 'dados', 'results', 'records', 'items']:
                        if key in json_data and isinstance(json_data[key], list):
                            dados = json_data[key]
                            break

                    # Se não encontrou lista, usar o próprio objeto
                    if not dados:
                        dados = [json_data]

                logger.info(f"    ✓ {len(dados)} registros via JSON")

            except json.JSONDecodeError:
                # Se não for JSON, tentar como HTML
                dados = self.extract_from_html_tables(response.text)

        except Exception as e:
            logger.warning(f"    Erro: {e}")

        return dados

    def extract(self) -> List[Dict]:
        """
        Executa extração completa de dados

        Returns:
            Lista de dados extraídos
        """
        logger.info("=" * 60)
        logger.info("Iniciando extração de dados SSP-SC")
        logger.info("=" * 60)

        todos_dados = []

        try:
            # 1. Descobrir endpoints de API
            logger.info("\n[1] Descobrindo endpoints de API...")
            endpoints = self.discover_api_endpoints()

            # 2. Tentar extrair de cada endpoint
            if endpoints:
                logger.info(f"\n[2] Tentando {len(endpoints)} endpoints...")
                for endpoint in endpoints:
                    dados_endpoint = self.extract_from_api(endpoint)
                    if dados_endpoint:
                        todos_dados.extend(dados_endpoint)

            # 3. Se não conseguiu via API, tentar HTML direto
            if not todos_dados:
                logger.info("\n[3] Tentando extração via HTML da página principal...")
                response = self.session.get(self.base_url, timeout=30)
                dados_html = self.extract_from_html_tables(response.text)
                todos_dados.extend(dados_html)

            # 4. Processar e normalizar dados
            logger.info(f"\n[4] Processando {len(todos_dados)} registros...")
            dados_processados = []

            for dado in todos_dados:
                dado_proc = self._process_record(dado) if isinstance(dado, dict) else None
                if dado_proc:
                    dados_processados.append(dado_proc)

            logger.info(f"\n✓ Total de {len(dados_processados)} registros extraídos e processados")

            return dados_processados

        except Exception as e:
            logger.error(f"✗ Erro durante extração: {e}", exc_info=True)
            return []

    def save_to_database(self, dados: List[Dict]):
        """Salva dados no banco de dados"""
        if not self.session_db:
            logger.warning("Sessão de banco de dados não disponível")
            return

        try:
            contador = 0
            for dado in dados:
                try:
                    registro = DadosSeguranca(
                        tipo_ocorrencia=str(dado.get('tipo_ocorrencia', 'Não especificado')),
                        municipio=str(dado.get('municipio', 'Não especificado')),
                        regiao=str(dado.get('regiao', 'Não especificado')),
                        periodo=str(dado.get('periodo', 'Não especificado')),
                        quantidade=int(dado.get('quantidade', 0)),
                        ano=int(dado.get('ano', datetime.now().year)),
                        mes=int(dado.get('mes')) if dado.get('mes') else None,
                        dados_brutos=json.dumps(dado, ensure_ascii=False)
                    )
                    self.session_db.add(registro)
                    contador += 1
                except Exception as e:
                    logger.debug(f"Erro ao processar registro: {e}")
                    continue

            self.session_db.commit()
            logger.info(f"✓ {contador} registros salvos no banco de dados")

        except Exception as e:
            logger.error(f"✗ Erro ao salvar no banco: {e}")
            self.session_db.rollback()

    def save_to_files(self, dados: List[Dict]):
        """Salva dados em arquivos CSV e JSON"""
        if not dados:
            logger.warning("Nenhum dado para salvar em arquivos")
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        try:
            # CSV
            df = pd.DataFrame(dados)
            csv_path = os.path.join(self.output_dir, f'dados_ssp_sc_{timestamp}.csv')
            df.to_csv(csv_path, index=False, encoding='utf-8')
            logger.info(f"✓ CSV salvo: {csv_path}")

            # JSON
            json_path = os.path.join(self.output_dir, f'dados_ssp_sc_{timestamp}.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
            logger.info(f"✓ JSON salvo: {json_path}")

        except Exception as e:
            logger.error(f"✗ Erro ao salvar arquivos: {e}")

    def run(self):
        """Executa processo completo de extração"""
        inicio = time.time()

        try:
            # Extrair dados
            dados = self.extract()

            if dados:
                # Salvar em múltiplos destinos
                self.save_to_database(dados)
                self.save_to_files(dados)
            else:
                logger.warning("⚠ Nenhum dado extraído")

        except Exception as e:
            logger.error(f"✗ Erro fatal: {e}", exc_info=True)

        finally:
            duracao = time.time() - inicio
            logger.info("=" * 60)
            logger.info(f"Extração concluída em {duracao:.2f} segundos")
            logger.info("=" * 60)


def main():
    """Função principal"""
    logger.info("SSP-SC Extrator Autônomo - Iniciando...")

    extractor = SSPSCExtractorAutonomous()
    extractor.run()


if __name__ == '__main__':
    main()
