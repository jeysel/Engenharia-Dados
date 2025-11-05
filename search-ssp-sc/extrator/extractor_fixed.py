"""
Extrator Corrigido de Dados da SSP-SC
Versão melhorada com análise mais precisa dos PDFs
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


class SSPSCExtractorFixed:
    """Extrator corrigido de dados da SSP-SC"""

    def __init__(self, db_url: str = None):
        """Inicializa o extrator"""
        self.base_url = "https://ssp.sc.gov.br/segurancaemnumeros/"
        self.db_url = db_url or os.getenv(
            'DATABASE_URL',
            'postgresql://user:password@postgres:5432/ssp_sc_db'
        )
        self.output_dir = '/app/data'
        os.makedirs(self.output_dir, exist_ok=True)

        # Configurar sessão HTTP
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
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

    def limpar_dados_existentes(self):
        """Limpa todos os dados existentes das tabelas"""
        try:
            logger.info("Limpando dados existentes...")

            with self.engine.connect() as conn:
                conn.execute(text("TRUNCATE TABLE roubo CASCADE"))
                conn.execute(text("TRUNCATE TABLE furto CASCADE"))
                conn.execute(text("TRUNCATE TABLE mortes_violentas CASCADE"))
                conn.execute(text("TRUNCATE TABLE homicidio CASCADE"))
                conn.execute(text("TRUNCATE TABLE violencia_domestica CASCADE"))
                conn.execute(text("TRUNCATE TABLE historico_execucao CASCADE"))
                conn.commit()

            logger.info("✓ Dados existentes limpos")
        except Exception as e:
            logger.error(f"Erro ao limpar dados: {e}")

    def descobrir_links_boletins(self) -> Dict[int, List[str]]:
        """Descobre todos os links de boletins mensais disponíveis por ano"""
        boletins = {}

        try:
            logger.info(f"Acessando {self.base_url}")
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            links = soup.find_all('a', href=True)

            for link in links:
                href = link['href']
                texto = link.get_text().strip()

                if '.pdf' in href.lower():
                    match_ano = re.search(r'20\d{2}', href) or re.search(r'20\d{2}', texto)

                    if match_ano:
                        ano = int(match_ano.group())

                        if any(term in texto.lower() or term in href.lower()
                               for term in ['boletim', 'mensal', 'indicador', 'janeiro', 'fevereiro',
                                           'março', 'abril', 'maio', 'junho', 'julho', 'agosto',
                                           'setembro', 'outubro', 'novembro', 'dezembro', 'relatorio']):

                            url_completa = href if href.startswith('http') else f"https://ssp.sc.gov.br{href}"

                            if ano not in boletins:
                                boletins[ano] = []

                            if url_completa not in boletins[ano]:
                                boletins[ano].append(url_completa)

            logger.info(f"Total de anos encontrados: {len(boletins)}")
            for ano, links in boletins.items():
                logger.info(f"Ano {ano}: {len(links)} boletins")

        except Exception as e:
            logger.error(f"Erro ao descobrir boletins: {e}")

        return boletins

    def extrair_mes_do_nome_arquivo(self, nome_arquivo: str) -> Optional[int]:
        """Extrai o número do mês do nome do arquivo"""
        meses = {
            'janeiro': 1, 'jan': 1, 'fevereiro': 2, 'fev': 2, 'março': 3, 'marco': 3, 'mar': 3,
            'abril': 4, 'abr': 4, 'maio': 5, 'mai': 5, 'junho': 6, 'jun': 6,
            'julho': 7, 'jul': 7, 'agosto': 8, 'ago': 8, 'setembro': 9, 'set': 9,
            'outubro': 10, 'out': 10, 'novembro': 11, 'nov': 11, 'dezembro': 12, 'dez': 12
        }

        nome_lower = nome_arquivo.lower()
        for mes_nome, mes_num in meses.items():
            if mes_nome in nome_lower:
                return mes_num

        # Tentar extrair número (01-12)
        match = re.search(r'[-_](\d{2})[-_.]', nome_arquivo)
        if match:
            mes = int(match.group(1))
            if 1 <= mes <= 12:
                return mes

        return None

    def processar_pdf_boletim(self, url: str, ano: int) -> Tuple[bool, str]:
        """Processa um PDF de boletim mensal"""
        historico = HistoricoExecucao(
            data_hora_inicio=datetime.now(),
            tipo_dados='boletim_mensal',
            fonte=url,
            anos_processados=str(ano)
        )

        try:
            nome_arquivo = url.split('/')[-1]
            mes = self.extrair_mes_do_nome_arquivo(nome_arquivo)

            logger.info(f"Processando: {nome_arquivo} (Ano: {ano}, Mês: {mes})")

            # Baixar PDF
            response = self.session.get(url, timeout=60)
            response.raise_for_status()

            # Salvar temporariamente
            temp_path = os.path.join(self.output_dir, f'temp_{nome_arquivo}')
            with open(temp_path, 'wb') as f:
                f.write(response.content)

            registros_inseridos = 0

            with pdfplumber.open(temp_path) as pdf:
                logger.info(f"  PDF com {len(pdf.pages)} páginas")

                # Processar página 1 - Roubo e Furto
                if len(pdf.pages) >= 1:
                    registros = self._processar_pagina1_melhorado(pdf.pages[0], ano, mes, url)
                    registros_inseridos += registros
                    logger.info(f"  Página 1: {registros} registros")

                # Processar página 2 - Mortes Violentas
                if len(pdf.pages) >= 2:
                    registros = self._processar_pagina2_melhorado(pdf.pages[1], ano, mes, url)
                    registros_inseridos += registros
                    logger.info(f"  Página 2: {registros} registros")

            # Remover arquivo temporário
            if os.path.exists(temp_path):
                os.remove(temp_path)

            msg = f"PDF processado: {registros_inseridos} registros"

            historico.status = 'sucesso'
            historico.mensagem = msg
            historico.registros_inseridos = registros_inseridos
            historico.data_hora_fim = datetime.now()
            self.db_session.add(historico)
            self.db_session.commit()

            return True, msg

        except Exception as e:
            msg = f"Erro ao processar {url}: {e}"
            logger.error(msg)
            import traceback
            logger.error(traceback.format_exc())

            historico.status = 'erro'
            historico.mensagem = msg
            historico.data_hora_fim = datetime.now()
            self.db_session.add(historico)
            self.db_session.commit()

            return False, msg

    def _processar_pagina1_melhorado(self, page, ano: int, mes: Optional[int], fonte: str) -> int:
        """Processa página 1 - Roubo e Furto de forma melhorada"""
        registros = 0

        try:
            # Extrair texto para identificar seções
            texto_pagina = page.extract_text()

            # Extrair tabelas
            tabelas = page.extract_tables()

            for idx_tabela, tabela in enumerate(tabelas):
                if not tabela or len(tabela) < 2:
                    continue

                # Analisar cabeçalho para determinar tipo
                header_str = ' '.join([str(cell).lower() if cell else '' for cell in tabela[0]])

                # Determinar se é roubo ou furto
                eh_roubo = 'roubo' in header_str
                eh_furto = 'furto' in header_str

                if not eh_roubo and not eh_furto:
                    continue

                # Processar linhas de dados (pular cabeçalho)
                for row_idx in range(1, len(tabela)):
                    row = tabela[row_idx]

                    # Procurar por município e quantidade
                    municipio = None
                    quantidade = None

                    for cell in row:
                        if not cell or str(cell).strip() == '':
                            continue

                        cell_str = str(cell).strip()

                        # Tentar identificar se é município (texto com letras)
                        if any(c.isalpha() for c in cell_str) and len(cell_str) > 2:
                            # Verificar se não é um cabeçalho
                            if cell_str.upper() not in ['TOTAL', 'SUBTOTAL', 'MUNICÍPIO', 'MUNICIPIO']:
                                if not municipio:
                                    municipio = cell_str

                        # Tentar identificar quantidade (apenas números)
                        if cell_str.replace('.', '').replace(',', '').isdigit():
                            try:
                                # Limpar e converter
                                valor = int(cell_str.replace('.', '').replace(',', ''))
                                if valor > 0 and valor < 100000:  # Validação básica
                                    quantidade = valor
                            except:
                                pass

                    # Inserir se tiver dados válidos
                    if municipio and quantidade and quantidade > 0:
                        if eh_roubo:
                            registro = Roubo(
                                ano=ano,
                                mes=mes,
                                municipio=municipio,
                                tipo_roubo='Roubo',
                                quantidade=quantidade,
                                fonte=fonte
                            )
                            self.db_session.add(registro)
                            registros += 1
                        elif eh_furto:
                            registro = Furto(
                                ano=ano,
                                mes=mes,
                                municipio=municipio,
                                tipo_furto='Furto',
                                quantidade=quantidade,
                                fonte=fonte
                            )
                            self.db_session.add(registro)
                            registros += 1

            if registros > 0:
                self.db_session.commit()

        except Exception as e:
            logger.error(f"Erro ao processar página 1: {e}")
            import traceback
            logger.error(traceback.format_exc())

        return registros

    def _processar_pagina2_melhorado(self, page, ano: int, mes: Optional[int], fonte: str) -> int:
        """Processa página 2 - Mortes Violentas de forma melhorada"""
        registros = 0

        try:
            tabelas = page.extract_tables()

            for idx_tabela, tabela in enumerate(tabelas):
                if not tabela or len(tabela) < 2:
                    continue

                # Verificar se é tabela de mortes violentas
                header_str = ' '.join([str(cell).lower() if cell else '' for cell in tabela[0]])

                if not any(term in header_str for term in ['morte', 'violenta', 'homicid', 'cvli']):
                    continue

                # Processar linhas
                for row_idx in range(1, len(tabela)):
                    row = tabela[row_idx]

                    municipio = None
                    tipo_morte = None
                    quantidade = None

                    for cell in row:
                        if not cell or str(cell).strip() == '':
                            continue

                        cell_str = str(cell).strip()

                        # Pular totais e cabeçalhos
                        if cell_str.upper() in ['TOTAL', 'SUBTOTAL', 'MUNICÍPIO', 'MUNICIPIO', 'CVLI']:
                            continue

                        # Identificar município (texto longo com letras)
                        if any(c.isalpha() for c in cell_str) and len(cell_str) > 3:
                            # Verificar se não é tipo de morte
                            if not any(termo in cell_str.upper() for termo in ['HOMICID', 'FEMINIC', 'LATROC', 'LESÃO', 'CONFRONTO']):
                                if not municipio:
                                    municipio = cell_str
                            else:
                                if not tipo_morte:
                                    tipo_morte = cell_str

                        # Identificar quantidade
                        if cell_str.replace('.', '').replace(',', '').isdigit():
                            try:
                                valor = int(cell_str.replace('.', '').replace(',', ''))
                                if valor > 0 and valor < 100000:
                                    quantidade = valor
                            except:
                                pass

                    # Inserir se tiver município e quantidade
                    if municipio and quantidade and quantidade > 0:
                        registro = MortesViolentas(
                            ano=ano,
                            mes=mes,
                            municipio=municipio,
                            tipo_morte=tipo_morte or 'Morte violenta',
                            quantidade=quantidade,
                            fonte=fonte
                        )
                        self.db_session.add(registro)
                        registros += 1

                    # Ou se tiver tipo de morte e quantidade (total por tipo)
                    elif tipo_morte and quantidade and quantidade > 0 and not municipio:
                        registro = MortesViolentas(
                            ano=ano,
                            mes=mes,
                            tipo_morte=tipo_morte,
                            quantidade=quantidade,
                            fonte=fonte
                        )
                        self.db_session.add(registro)
                        registros += 1

            if registros > 0:
                self.db_session.commit()

        except Exception as e:
            logger.error(f"Erro ao processar página 2: {e}")
            import traceback
            logger.error(traceback.format_exc())

        return registros

    def run(self, limpar_dados=False):
        """Executa o processo completo de extração"""
        logger.info("=" * 80)
        logger.info("Extrator SSP-SC - Versão Corrigida")
        logger.info("=" * 80)

        if limpar_dados:
            self.limpar_dados_existentes()

        # Descobrir boletins
        logger.info("\n1. Descobrindo boletins mensais...")
        boletins = self.descobrir_links_boletins()

        # Processar boletins (limitar a alguns para teste)
        logger.info("\n2. Processando boletins...")
        total_sucesso = 0
        total_erro = 0

        for ano in sorted(boletins.keys(), reverse=True):
            logger.info(f"\nAno {ano}:")
            for url in boletins[ano][:3]:  # Processar apenas os 3 primeiros de cada ano para teste
                sucesso, msg = self.processar_pdf_boletim(url, ano)
                if sucesso:
                    total_sucesso += 1
                else:
                    total_erro += 1

        logger.info(f"\n✓ Boletins processados: {total_sucesso} sucesso, {total_erro} erros")
        logger.info("=" * 80)


def main():
    """Função principal"""
    import sys

    extractor = SSPSCExtractorFixed()

    # Verificar se deve limpar dados
    limpar = '--limpar' in sys.argv

    extractor.run(limpar_dados=limpar)


if __name__ == '__main__':
    main()
