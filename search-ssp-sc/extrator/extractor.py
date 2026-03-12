"""
Novo Extrator de Dados da SSP-SC
Extrai dados de PDFs (Boletim Mensal) e arquivos XLS (Violência Doméstica)
"""

import os
import io
import re
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import pandas as pd
import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pdfplumber
import urllib3

from database_models import Base, Roubo, Furto, MortesViolentas, Homicidio, ViolenciaDomestica, HistoricoExecucao

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Desabilitar avisos SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class SSPSCExtractorNew:
    """Novo extrator de dados da SSP-SC"""

    def __init__(self, db_url: str = None):
        """
        Inicializa o extrator

        Args:
            db_url: URL de conexão com o banco de dados PostgreSQL
        """
        self.base_url = "https://ssp.sc.gov.br/segurancaemnumeros/"
        self.db_url = db_url or os.getenv(
            'DATABASE_URL',
            'postgresql://user:password@postgres:5432/ssp_sc_db'
        )
        self.output_dir = '/app/data'

        # Criar diretório de saída se não existir
        os.makedirs(self.output_dir, exist_ok=True)

        # Configurar sessão HTTP
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9',
        })
        self.session.verify = False

        # Inicializar banco de dados
        self._init_database()

    def _init_database(self):
        """Inicializa conexão com banco de dados"""
        try:
            self.engine = create_engine(self.db_url)
            Base.metadata.create_all(self.engine)
            Session = sessionmaker(bind=self.engine)
            self.db_session = Session()
            logger.info("Conexão com banco de dados estabelecida")
        except Exception as e:
            logger.error(f"Erro ao conectar ao banco de dados: {e}")
            self.db_session = None

    def descobrir_links_boletins(self) -> Dict[int, List[str]]:
        """
        Descobre todos os links de boletins mensais disponíveis por ano

        Returns:
            Dicionário com ano -> lista de URLs dos PDFs
        """
        boletins = {}

        try:
            logger.info(f"Acessando {self.base_url} para descobrir boletins")
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Procurar por links de PDFs do boletim mensal
            links = soup.find_all('a', href=True)

            for link in links:
                href = link['href']
                texto = link.get_text().strip()

                # Verificar se é um boletim mensal (PDF)
                if '.pdf' in href.lower():
                    ano = None

                    # Primeiro, verificar padrão específico: 23.MM_ indica 2023
                    match_23 = re.search(r'23\.\d{2}_', href)
                    if match_23:
                        ano = 2023
                    # Caso contrário, tentar extrair ano completo (20YY) do final do filename ou texto
                    else:
                        # Tentar no nome do arquivo primeiro (após a última barra)
                        filename = href.split('/')[-1]
                        match_ano = re.search(r'20\d{2}', filename)
                        if match_ano:
                            ano = int(match_ano.group())
                        else:
                            # Tentar no texto do link
                            match_ano = re.search(r'20\d{2}', texto)
                            if match_ano:
                                ano = int(match_ano.group())

                    if ano:
                        # Verificar se parece ser boletim mensal
                        if any(term in texto.lower() or term in href.lower()
                               for term in ['boletim', 'mensal', 'indicador', 'janeiro', 'fevereiro',
                                           'março', 'abril', 'maio', 'junho', 'julho', 'agosto',
                                           'setembro', 'outubro', 'novembro', 'dezembro']):

                            # URL completa
                            if href.startswith('http'):
                                url_completa = href
                            else:
                                url_completa = f"https://ssp.sc.gov.br{href}" if href.startswith('/') else href

                            if ano not in boletins:
                                boletins[ano] = []

                            if url_completa not in boletins[ano]:
                                boletins[ano].append(url_completa)
                                logger.info(f"Boletim encontrado: {ano} - {url_completa}")

            logger.info(f"Total de anos encontrados: {len(boletins)}")
            for ano, links in boletins.items():
                logger.info(f"Ano {ano}: {len(links)} boletins")

        except Exception as e:
            logger.error(f"Erro ao descobrir boletins: {e}")

        # Nota: Os boletins históricos de 2021 e 2022 não estão disponíveis publicamente
        # Os boletins de 2023 já são detectados pelo scraping da página principal (padrão 23.MM_monthname.pdf)
        logger.info("Boletins de 2021 e 2022 não disponíveis. Boletins de 2023 detectados pelo scraping da página.")

        return boletins

    def descobrir_links_violencia_domestica(self) -> List[Dict]:
        """
        Descobre todos os links de arquivos de violência doméstica (XLS/CSV)

        Returns:
            Lista de dicionários com informações dos arquivos
        """
        arquivos = []

        try:
            logger.info("Procurando arquivos de violência doméstica")
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            links = soup.find_all('a', href=True)

            for link in links:
                href = link['href']
                texto = link.get_text().strip()

                # Verificar se é arquivo XLS/CSV
                if any(ext in href.lower() for ext in ['.xls', '.xlsx', '.csv']):
                    # Verificar se é sobre violência doméstica
                    if any(term in texto.lower() or term in href.lower()
                           for term in ['violencia', 'domestica', 'doméstica', 'mulher', 'feminicidio']):

                        # URL completa
                        if href.startswith('http'):
                            url_completa = href
                        else:
                            url_completa = f"https://ssp.sc.gov.br{href}" if href.startswith('/') else href

                        # Tentar extrair ano e semestre
                        ano_match = re.search(r'20\d{2}', texto) or re.search(r'20\d{2}', href)
                        semestre_match = re.search(r'[12]º?\s*semestre|semestre\s*[12]', texto.lower())

                        info = {
                            'url': url_completa,
                            'texto': texto,
                            'ano': int(ano_match.group()) if ano_match else None,
                            'semestre': None
                        }

                        if semestre_match:
                            sem_text = semestre_match.group()
                            info['semestre'] = 1 if '1' in sem_text else 2

                        arquivos.append(info)
                        logger.info(f"Arquivo violência doméstica encontrado: {url_completa}")

            logger.info(f"Total de arquivos de violência doméstica: {len(arquivos)}")

        except Exception as e:
            logger.error(f"Erro ao descobrir arquivos de violência doméstica: {e}")

        return arquivos

    def extrair_mes_do_nome_arquivo(self, nome_arquivo: str) -> Optional[int]:
        """Extrai o número do mês do nome do arquivo"""
        meses = {
            'janeiro': 1, 'fevereiro': 2, 'março': 3, 'marco': 3,
            'abril': 4, 'maio': 5, 'junho': 6,
            'julho': 7, 'agosto': 8, 'setembro': 9,
            'outubro': 10, 'novembro': 11, 'dezembro': 12,
            'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
            'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12
        }

        nome_lower = nome_arquivo.lower()
        for mes_nome, mes_num in meses.items():
            if mes_nome in nome_lower:
                return mes_num

        # Tentar extrair número do mês (01-12)
        match = re.search(r'[-_](\d{2})[-_.]', nome_arquivo)
        if match:
            mes = int(match.group(1))
            if 1 <= mes <= 12:
                return mes

        return None

    def processar_pdf_boletim(self, url: str, ano: int) -> Tuple[bool, str]:
        """
        Processa um PDF de boletim mensal

        Args:
            url: URL do PDF
            ano: Ano do boletim

        Returns:
            (sucesso, mensagem)
        """
        historico = HistoricoExecucao(
            data_hora_inicio=datetime.now(),
            tipo_dados='boletim_mensal',
            fonte=url,
            anos_processados=str(ano)
        )

        try:
            # Verificar se já existe dados deste arquivo
            nome_arquivo = url.split('/')[-1]
            mes = self.extrair_mes_do_nome_arquivo(nome_arquivo)

            if self._dados_ja_existem(ano, mes):
                msg = f"Dados de {ano}/{mes if mes else 'ano'} já existem. Pulando..."
                logger.info(msg)
                historico.status = 'ignorado'
                historico.mensagem = msg
                historico.registros_ignorados = 1
                historico.data_hora_fim = datetime.now()
                self.db_session.add(historico)
                self.db_session.commit()
                return True, msg

            logger.info(f"Baixando PDF: {url}")
            response = self.session.get(url, timeout=60)
            response.raise_for_status()

            # Salvar temporariamente
            temp_path = os.path.join(self.output_dir, f'temp_{nome_arquivo}')
            with open(temp_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"Processando PDF: {nome_arquivo}")

            registros_inseridos = 0

            with pdfplumber.open(temp_path) as pdf:
                logger.info(f"PDF com {len(pdf.pages)} páginas")

                # Página 1: Roubo e Furto
                if len(pdf.pages) >= 1:
                    registros_inseridos += self._processar_pagina_roubo_furto(
                        pdf.pages[0], ano, mes, url
                    )

                # Página 2: Mortes Violentas
                if len(pdf.pages) >= 2:
                    registros_inseridos += self._processar_pagina_mortes_violentas(
                        pdf.pages[1], ano, mes, url
                    )

                # Procurar por dados de homicídio em todas as páginas
                for page_num, page in enumerate(pdf.pages):
                    registros_inseridos += self._processar_pagina_homicidio(
                        page, ano, mes, url, page_num
                    )

            # Remover arquivo temporário
            if os.path.exists(temp_path):
                os.remove(temp_path)

            msg = f"PDF processado com sucesso: {registros_inseridos} registros inseridos"
            logger.info(msg)

            historico.status = 'sucesso'
            historico.mensagem = msg
            historico.registros_inseridos = registros_inseridos
            historico.data_hora_fim = datetime.now()
            self.db_session.add(historico)
            self.db_session.commit()

            return True, msg

        except Exception as e:
            msg = f"Erro ao processar PDF {url}: {e}"
            logger.error(msg)
            import traceback
            logger.debug(traceback.format_exc())

            historico.status = 'erro'
            historico.mensagem = msg
            historico.data_hora_fim = datetime.now()
            self.db_session.add(historico)
            self.db_session.commit()

            return False, msg

    def _dados_ja_existem(self, ano: int, mes: Optional[int] = None) -> bool:
        """Verifica se já existem dados para o período especificado"""
        try:
            # Verificar em cada tabela
            for tabela in [Roubo, Furto, MortesViolentas, Homicidio]:
                query = self.db_session.query(tabela).filter(tabela.ano == ano)
                if mes:
                    query = query.filter(tabela.mes == mes)

                if query.count() > 0:
                    return True

            return False
        except Exception as e:
            logger.warning(f"Erro ao verificar dados existentes: {e}")
            return False

    def _processar_pagina_roubo_furto(self, page, ano: int, mes: Optional[int], fonte: str) -> int:
        """
        Processa página 1 com dados ESTADUAIS de roubo e furto

        Estrutura esperada da tabela:
        Linha com 'ROUBO' seguida de valores numéricos
        Linha com 'FURTO' seguida de valores numéricos
        """
        registros = 0

        try:
            logger.info(f"Processando página de roubo/furto (ano={ano}, mes={mes})")

            # Extrair tabelas da página
            tabelas = page.extract_tables()
            logger.debug(f"  Encontradas {len(tabelas)} tabelas")

            for idx_tabela, tabela in enumerate(tabelas):
                if not tabela or len(tabela) < 2:
                    continue

                logger.debug(f"  Analisando tabela {idx_tabela + 1} ({len(tabela)} linhas)")

                # Procurar por linhas com ROUBO ou FURTO
                for idx_linha, linha in enumerate(tabela):
                    try:
                        # Converter linha para string para análise
                        linha_str = ' '.join([str(cell) if cell else '' for cell in linha]).upper()

                        # Verificar se é linha de ROUBO
                        if 'ROUBO' in linha_str and 'FURTO' not in linha_str:
                            logger.debug(f"    Linha {idx_linha} identificada como ROUBO: {linha}")

                            # Extrair o valor mais recente (última coluna não vazia com número)
                            quantidade = self._extrair_quantidade_da_linha(linha)

                            if quantidade > 0:
                                registro = Roubo(
                                    ano=ano,
                                    mes=mes,
                                    municipio='Santa Catarina',  # Dado estadual
                                    regiao='Estado',
                                    tipo_roubo='Roubo',
                                    quantidade=quantidade,
                                    fonte=fonte,
                                    dados_brutos=json.dumps({'linha': linha}, ensure_ascii=False)
                                )
                                self.db_session.add(registro)
                                registros += 1
                                logger.info(f"    ✓ ROUBO: {quantidade} ocorrências")

                        # Verificar se é linha de FURTO
                        elif 'FURTO' in linha_str and 'ROUBO' not in linha_str:
                            logger.debug(f"    Linha {idx_linha} identificada como FURTO: {linha}")

                            quantidade = self._extrair_quantidade_da_linha(linha)

                            if quantidade > 0:
                                registro = Furto(
                                    ano=ano,
                                    mes=mes,
                                    municipio='Santa Catarina',  # Dado estadual
                                    regiao='Estado',
                                    tipo_furto='Furto',
                                    quantidade=quantidade,
                                    fonte=fonte,
                                    dados_brutos=json.dumps({'linha': linha}, ensure_ascii=False)
                                )
                                self.db_session.add(registro)
                                registros += 1
                                logger.info(f"    ✓ FURTO: {quantidade} ocorrências")

                    except Exception as e:
                        logger.debug(f"    Erro ao processar linha {idx_linha}: {e}")
                        continue

            if registros > 0:
                self.db_session.commit()
                logger.info(f"✓ Página roubo/furto: {registros} registros inseridos")
            else:
                logger.warning(f"⚠ Nenhum dado de roubo/furto encontrado")

        except Exception as e:
            logger.error(f"✗ Erro ao processar página de roubo/furto: {e}")
            import traceback
            logger.debug(traceback.format_exc())

        return registros

    def _extrair_quantidade_da_linha(self, linha: List) -> int:
        """
        Extrai a quantidade de ocorrências de uma linha da tabela
        Procura pelo último valor numérico válido (geralmente o período mais recente)
        """
        # Percorrer linha de trás para frente procurando número válido
        for cell in reversed(linha):
            if cell is None:
                continue

            cell_str = str(cell).strip()

            # Remover pontos de milhares e tentar converter
            cell_clean = cell_str.replace('.', '').replace(',', '')

            if cell_clean.isdigit():
                return int(cell_clean)

        return 0

    def _limpar_nome_municipio(self, nome: str) -> str:
        """
        Limpa nome de município removendo números e caracteres especiais entre parênteses

        Exemplos:
        'CAMPOS NOVOS (2 — 6)' -> 'CAMPOS NOVOS'
        'CHAPECÓ (11 — 19)' -> 'CHAPECÓ'
        """
        import re

        if not nome:
            return nome

        # Remover tudo entre parênteses que contenha números
        nome_limpo = re.sub(r'\s*\([^)]*\d[^)]*\)', '', nome)

        # Remover espaços extras
        nome_limpo = nome_limpo.strip()

        return nome_limpo

    def _processar_pagina_mortes_violentas(self, page, ano: int, mes: Optional[int], fonte: str) -> int:
        """Processa página 2 com dados de mortes violentas"""
        registros = 0

        try:
            tabelas = page.extract_tables()

            for tabela in tabelas:
                if not tabela or len(tabela) < 2:
                    continue

                df = pd.DataFrame(tabela[1:], columns=tabela[0])

                for idx, row in df.iterrows():
                    try:
                        municipio = None
                        regiao = None
                        quantidade = 0
                        tipo_morte = None

                        for col_idx, valor in enumerate(row):
                            if pd.isna(valor) or str(valor).strip() == '':
                                continue

                            valor_str = str(valor).strip()

                            if any(c.isalpha() for c in valor_str) and len(valor_str) > 3:
                                if not municipio:
                                    # Limpar nome do município
                                    municipio = self._limpar_nome_municipio(valor_str)
                                elif not tipo_morte and any(term in valor_str.lower()
                                                           for term in ['homicidio', 'latrocinio', 'morte']):
                                    tipo_morte = valor_str

                            if valor_str.isdigit():
                                quantidade = int(valor_str)

                        if quantidade > 0 and municipio:
                            registro = MortesViolentas(
                                ano=ano,
                                mes=mes,
                                municipio=municipio,
                                regiao=regiao,
                                tipo_morte=tipo_morte or 'Morte violenta',
                                quantidade=quantidade,
                                fonte=fonte,
                                dados_brutos=json.dumps(row.to_dict(), ensure_ascii=False)
                            )
                            self.db_session.add(registro)
                            registros += 1

                    except Exception as e:
                        logger.debug(f"Erro ao processar linha: {e}")
                        continue

            if registros > 0:
                self.db_session.commit()
                logger.info(f"Página mortes violentas: {registros} registros inseridos")

        except Exception as e:
            logger.error(f"Erro ao processar página de mortes violentas: {e}")

        return registros

    def _processar_pagina_homicidio(self, page, ano: int, mes: Optional[int],
                                    fonte: str, page_num: int) -> int:
        """Processa página buscando dados específicos de homicídio"""
        registros = 0

        try:
            # Extrair texto da página
            texto = page.extract_text()

            # Verificar se tem informação de homicídio
            if not any(term in texto.lower() for term in ['homicidio', 'homicídio', 'feminicidio']):
                return 0

            tabelas = page.extract_tables()

            for tabela in tabelas:
                if not tabela or len(tabela) < 2:
                    continue

                # Verificar se a tabela tem dados de homicídio
                header_text = ' '.join([str(h).lower() for h in tabela[0]])
                if 'homicid' not in header_text:
                    continue

                df = pd.DataFrame(tabela[1:], columns=tabela[0])

                for idx, row in df.iterrows():
                    try:
                        municipio = None
                        regiao = None
                        quantidade = 0
                        tipo_homicidio = None

                        for col_idx, valor in enumerate(row):
                            if pd.isna(valor) or str(valor).strip() == '':
                                continue

                            valor_str = str(valor).strip()

                            if any(c.isalpha() for c in valor_str) and len(valor_str) > 3:
                                if not municipio:
                                    municipio = valor_str
                                elif any(term in valor_str.lower()
                                        for term in ['doloso', 'culposo', 'feminicidio']):
                                    tipo_homicidio = valor_str

                            if valor_str.isdigit():
                                quantidade = int(valor_str)

                        if quantidade > 0:
                            registro = Homicidio(
                                ano=ano,
                                mes=mes,
                                municipio=municipio,
                                regiao=regiao,
                                tipo_homicidio=tipo_homicidio or 'Homicídio',
                                quantidade=quantidade,
                                fonte=fonte,
                                dados_brutos=json.dumps(row.to_dict(), ensure_ascii=False)
                            )
                            self.db_session.add(registro)
                            registros += 1

                    except Exception as e:
                        logger.debug(f"Erro ao processar linha: {e}")
                        continue

            if registros > 0:
                self.db_session.commit()
                logger.info(f"Página {page_num} homicídios: {registros} registros inseridos")

        except Exception as e:
            logger.debug(f"Erro ao processar homicídios na página {page_num}: {e}")

        return registros

    def processar_arquivo_violencia_domestica(self, info: Dict) -> Tuple[bool, str]:
        """
        Processa arquivo de violência doméstica (XLS/CSV)

        Estrutura esperada:
        - Coluna 0: Município
        - Coluna 1: Fato Comunicado (tipo de violência)
        - Colunas seguintes: Meses com quantidades

        Args:
            info: Dicionário com informações do arquivo

        Returns:
            (sucesso, mensagem)
        """
        url = info['url']
        ano = info.get('ano')
        semestre = info.get('semestre')

        historico = HistoricoExecucao(
            data_hora_inicio=datetime.now(),
            tipo_dados='violencia_domestica',
            fonte=url,
            anos_processados=str(ano) if ano else 'desconhecido'
        )

        try:
            logger.info(f"Baixando arquivo de violência doméstica: {url}")
            response = self.session.get(url, timeout=60)
            response.raise_for_status()

            # Determinar tipo de arquivo e ler
            if '.csv' in url.lower():
                df = pd.read_csv(io.BytesIO(response.content), encoding='utf-8', errors='ignore')
            else:
                df = pd.read_excel(io.BytesIO(response.content))

            logger.info(f"Arquivo lido: {len(df)} linhas x {len(df.columns)} colunas")

            registros_inseridos = 0

            # Identificar colunas
            col_municipio = df.columns[0]  # Primeira coluna: município
            col_tipo = df.columns[1]       # Segunda coluna: tipo de fato

            # Colunas de meses (geralmente da terceira em diante)
            colunas_meses = df.columns[2:]

            logger.debug(f"  Coluna município: {col_municipio}")
            logger.debug(f"  Coluna tipo: {col_tipo}")
            logger.debug(f"  Colunas de dados: {list(colunas_meses)}")

            # Pular primeira linha se for cabeçalho de meses (jan, fev, etc.)
            df_dados = df[1:] if str(df.iloc[0][col_municipio]).lower() in ['nan', 'none', ''] else df

            # Mapear nome do mês para número
            meses_map = {
                'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
                'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12,
                'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4, 'maio': 5, 'junho': 6,
                'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
            }

            # Processar cada linha
            for idx, row in df_dados.iterrows():
                try:
                    municipio = str(row[col_municipio]).strip()
                    tipo_violencia = str(row[col_tipo]).strip()

                    # Pular linhas sem município válido
                    if pd.isna(row[col_municipio]) or municipio.lower() in ['nan', 'none', '']:
                        continue

                    # Processar cada mês
                    for col_mes in colunas_meses:
                        try:
                            valor = row[col_mes]

                            # Tentar converter para número
                            if pd.isna(valor):
                                continue

                            valor_str = str(valor).strip()
                            if not valor_str or valor_str.lower() in ['nan', 'none', '']:
                                continue

                            # Tentar extrair quantidade
                            quantidade = 0
                            try:
                                quantidade = int(float(valor_str))
                            except:
                                continue

                            if quantidade <= 0:
                                continue

                            # Tentar identificar o mês
                            mes = None

                            # Primeira linha pode ter nome do mês
                            if idx > 0:
                                nome_mes = str(df.iloc[0][col_mes]).lower().strip()
                                mes = meses_map.get(nome_mes)

                            # Se não conseguiu, tentar extrair do nome da coluna
                            if not mes:
                                col_mes_str = str(col_mes).lower()
                                for nome, num in meses_map.items():
                                    if nome in col_mes_str:
                                        mes = num
                                        break

                            # Criar registro
                            registro = ViolenciaDomestica(
                                ano=ano or 2025,  # Ano padrão se não especificado
                                mes=mes,
                                semestre=semestre,
                                municipio=municipio,
                                tipo_violencia=tipo_violencia,
                                quantidade=quantidade,
                                fonte=url,
                                dados_brutos=json.dumps({
                                    'municipio': municipio,
                                    'tipo': tipo_violencia,
                                    'mes_col': str(col_mes),
                                    'quantidade': quantidade
                                }, ensure_ascii=False)
                            )
                            self.db_session.add(registro)
                            registros_inseridos += 1

                        except Exception as e:
                            logger.debug(f"Erro ao processar coluna {col_mes} da linha {idx}: {e}")
                            continue

                except Exception as e:
                    logger.debug(f"Erro ao processar linha {idx}: {e}")
                    continue

            self.db_session.commit()

            msg = f"Arquivo processado: {registros_inseridos} registros inseridos"
            logger.info(msg)

            historico.status = 'sucesso'
            historico.mensagem = msg
            historico.registros_inseridos = registros_inseridos
            historico.data_hora_fim = datetime.now()
            self.db_session.add(historico)
            self.db_session.commit()

            return True, msg

        except Exception as e:
            msg = f"Erro ao processar arquivo {url}: {e}"
            logger.error(msg)
            import traceback
            logger.error(traceback.format_exc())

            historico.status = 'erro'
            historico.mensagem = msg
            historico.data_hora_fim = datetime.now()
            self.db_session.add(historico)
            self.db_session.commit()

            return False, msg

    def limpar_tabelas_antigas(self):
        """Remove tabelas antigas e seus dados"""
        try:
            logger.info("Removendo tabela antiga 'dados_seguranca'...")

            with self.engine.connect() as conn:
                conn.execute(text("DROP TABLE IF EXISTS dados_seguranca CASCADE"))
                conn.commit()

            logger.info("Tabela antiga removida com sucesso")

        except Exception as e:
            logger.error(f"Erro ao remover tabelas antigas: {e}")

    def run(self):
        """Executa o processo completo de extração"""
        logger.info("=" * 80)
        logger.info("Iniciando novo extrator SSP-SC")
        logger.info("=" * 80)

        # 1. Descobrir todos os boletins disponíveis
        logger.info("\n1. Descobrindo boletins mensais...")
        boletins = self.descobrir_links_boletins()

        # 2. Processar cada boletim
        logger.info("\n2. Processando boletins mensais...")
        total_sucesso = 0
        total_erro = 0

        for ano in sorted(boletins.keys(), reverse=True):
            logger.info(f"\nProcessando ano {ano}...")
            for url in boletins[ano]:
                sucesso, msg = self.processar_pdf_boletim(url, ano)
                if sucesso:
                    total_sucesso += 1
                else:
                    total_erro += 1

        logger.info(f"\nBoletins processados: {total_sucesso} sucesso, {total_erro} erros")

        # 3. Descobrir e processar arquivos de violência doméstica
        logger.info("\n3. Processando arquivos de violência doméstica...")
        arquivos_vd = self.descobrir_links_violencia_domestica()

        total_vd_sucesso = 0
        total_vd_erro = 0

        for info in arquivos_vd:
            sucesso, msg = self.processar_arquivo_violencia_domestica(info)
            if sucesso:
                total_vd_sucesso += 1
            else:
                total_vd_erro += 1

        logger.info(f"\nArquivos de violência doméstica: {total_vd_sucesso} sucesso, {total_vd_erro} erros")

        # 4. Resumo final
        logger.info("\n" + "=" * 80)
        logger.info("RESUMO DA EXECUÇÃO")
        logger.info("=" * 80)
        logger.info(f"Boletins mensais: {total_sucesso} sucesso, {total_erro} erros")
        logger.info(f"Violência doméstica: {total_vd_sucesso} sucesso, {total_vd_erro} erros")
        logger.info("=" * 80)

        logger.info("\nExtração concluída!")


def main():
    """Função principal"""
    extractor = SSPSCExtractorNew()

    # Opção para limpar tabelas antigas
    import sys
    if '--limpar-antigas' in sys.argv:
        extractor.limpar_tabelas_antigas()

    extractor.run()


if __name__ == '__main__':
    main()
