"""
Extrator de Dados da SSP-SC com OCR
Versão com reconhecimento óptico de caracteres para extrair dados de PDFs visuais
"""

import os
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
import urllib3

# Imports para OCR
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import cv2
import numpy as np

from database_models import Base, Roubo, Furto, MortesViolentas, Homicidio, ViolenciaDomestica, HistoricoExecucao

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Desabilitar avisos SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class SSPSCExtractorOCR:
    """Extrator de dados da SSP-SC usando OCR"""

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

    def pre_processar_imagem(self, image):
        """Pré-processa a imagem para melhorar OCR"""
        # Converter PIL Image para numpy array
        img_array = np.array(image)

        # Converter para escala de cinza
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # Aplicar threshold para binarização
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Remover ruído
        denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)

        return Image.fromarray(denoised)

    def extrair_texto_pdf_ocr(self, pdf_path: str) -> List[str]:
        """
        Extrai texto de PDF usando OCR

        Args:
            pdf_path: Caminho do arquivo PDF

        Returns:
            Lista de textos, um por página
        """
        textos_paginas = []

        try:
            logger.info(f"  Convertendo PDF em imagens...")
            # Converter PDF em imagens (uma por página)
            images = convert_from_path(pdf_path, dpi=300)

            logger.info(f"  {len(images)} páginas para processar com OCR")

            for i, image in enumerate(images):
                logger.info(f"    Processando página {i+1}/{len(images)} com OCR...")

                # Pré-processar imagem
                processed_image = self.pre_processar_imagem(image)

                # Aplicar OCR
                texto = pytesseract.image_to_string(
                    processed_image,
                    lang='por',
                    config='--psm 6'  # Assume um único bloco de texto uniforme
                )

                textos_paginas.append(texto)

        except Exception as e:
            logger.error(f"Erro ao extrair texto com OCR: {e}")
            import traceback
            logger.error(traceback.format_exc())

        return textos_paginas

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
            for ano, links_ano in boletins.items():
                logger.info(f"Ano {ano}: {len(links_ano)} boletins")

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

        match = re.search(r'[-_](\d{2})[-_.]', nome_arquivo)
        if match:
            mes = int(match.group(1))
            if 1 <= mes <= 12:
                return mes

        return None

    def processar_pdf_boletim_ocr(self, url: str, ano: int) -> Tuple[bool, str]:
        """Processa um PDF de boletim mensal usando OCR"""
        historico = HistoricoExecucao(
            data_hora_inicio=datetime.now(),
            tipo_dados='boletim_mensal_ocr',
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

            # Extrair texto com OCR
            textos_paginas = self.extrair_texto_pdf_ocr(temp_path)

            if not textos_paginas:
                msg = "Nenhum texto extraído do PDF"
                logger.warning(msg)
                historico.status = 'erro'
                historico.mensagem = msg
                historico.data_hora_fim = datetime.now()
                self.db_session.add(historico)
                self.db_session.commit()
                return False, msg

            registros_inseridos = 0

            # Processar página 1 (índices 0) - Roubo e Furto
            if len(textos_paginas) >= 1:
                registros = self._processar_texto_roubo_furto(textos_paginas[0], ano, mes, url)
                registros_inseridos += registros
                logger.info(f"  Página 1: {registros} registros (roubo/furto)")

            # Processar página 2 (índice 1) - Mortes Violentas
            if len(textos_paginas) >= 2:
                registros = self._processar_texto_mortes_violentas(textos_paginas[1], ano, mes, url)
                registros_inseridos += registros
                logger.info(f"  Página 2: {registros} registros (mortes violentas)")

            # Remover arquivo temporário
            if os.path.exists(temp_path):
                os.remove(temp_path)

            msg = f"PDF processado com OCR: {registros_inseridos} registros"

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

    def _processar_texto_roubo_furto(self, texto: str, ano: int, mes: Optional[int], fonte: str) -> int:
        """Processa texto extraído da página 1 buscando por roubo e furto"""
        registros = 0

        try:
            # Buscar padrões de linhas com município e números
            # Exemplo: "FLORIANÓPOLIS 123 456"

            linhas = texto.split('\n')

            # Identificar seção de roubo
            em_secao_roubo = False
            em_secao_furto = False

            for linha in linhas:
                linha = linha.strip()

                if not linha:
                    continue

                # Detectar início de seções
                if 'roubo' in linha.lower() and not 'furto' in linha.lower():
                    em_secao_roubo = True
                    em_secao_furto = False
                    continue
                elif 'furto' in linha.lower():
                    em_secao_furto = True
                    em_secao_roubo = False
                    continue

                # Tentar extrair município e quantidade
                # Padrão: texto seguido de números
                match = re.match(r'([A-ZÀÁÂÃÄÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜÝ\s]+)\s+(\d+)', linha, re.IGNORECASE)

                if match:
                    municipio = match.group(1).strip()
                    quantidade_str = match.group(2)

                    # Validar município (não deve ser "TOTAL", etc)
                    if municipio.upper() in ['TOTAL', 'SUBTOTAL', 'ESTADO', 'SC', 'SANTA CATARINA']:
                        continue

                    try:
                        quantidade = int(quantidade_str)

                        if quantidade > 0:
                            if em_secao_roubo:
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
                            elif em_secao_furto:
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
                    except ValueError:
                        continue

            if registros > 0:
                self.db_session.commit()

        except Exception as e:
            logger.error(f"Erro ao processar texto roubo/furto: {e}")

        return registros

    def _processar_texto_mortes_violentas(self, texto: str, ano: int, mes: Optional[int], fonte: str) -> int:
        """Processa texto extraído da página 2 buscando por mortes violentas"""
        registros = 0

        try:
            linhas = texto.split('\n')

            for linha in linhas:
                linha = linha.strip()

                if not linha:
                    continue

                # Buscar por município e número
                match = re.match(r'([A-ZÀÁÂÃÄÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜÝ\s]+)\s+(\d+)', linha, re.IGNORECASE)

                if match:
                    municipio = match.group(1).strip()
                    quantidade_str = match.group(2)

                    # Validar
                    if municipio.upper() in ['TOTAL', 'SUBTOTAL', 'ESTADO', 'SC', 'CVLI']:
                        continue

                    # Verificar se é tipo de morte
                    eh_tipo_morte = any(termo in municipio.upper()
                                       for termo in ['HOMICID', 'FEMINIC', 'LATROC', 'LESÃO', 'CONFRONTO'])

                    try:
                        quantidade = int(quantidade_str)

                        if quantidade > 0:
                            if eh_tipo_morte:
                                # É um total por tipo
                                registro = MortesViolentas(
                                    ano=ano,
                                    mes=mes,
                                    tipo_morte=municipio,
                                    quantidade=quantidade,
                                    fonte=fonte
                                )
                            else:
                                # É um município
                                registro = MortesViolentas(
                                    ano=ano,
                                    mes=mes,
                                    municipio=municipio,
                                    tipo_morte='Morte violenta',
                                    quantidade=quantidade,
                                    fonte=fonte
                                )

                            self.db_session.add(registro)
                            registros += 1
                    except ValueError:
                        continue

            if registros > 0:
                self.db_session.commit()

        except Exception as e:
            logger.error(f"Erro ao processar texto mortes violentas: {e}")

        return registros

    def run(self, limpar_dados=False, limite_pdfs=None):
        """Executa o processo completo de extração com OCR"""
        logger.info("=" * 80)
        logger.info("Extrator SSP-SC - Versão com OCR")
        logger.info("=" * 80)

        if limpar_dados:
            self.limpar_dados_existentes()

        # Descobrir boletins
        logger.info("\n1. Descobrindo boletins mensais...")
        boletins = self.descobrir_links_boletins()

        # Processar boletins
        logger.info("\n2. Processando boletins com OCR...")
        total_sucesso = 0
        total_erro = 0
        total_processados = 0

        for ano in sorted(boletins.keys(), reverse=True):
            logger.info(f"\nAno {ano}:")
            for url in boletins[ano]:
                if limite_pdfs and total_processados >= limite_pdfs:
                    logger.info(f"\nLimite de {limite_pdfs} PDFs atingido")
                    break

                sucesso, msg = self.processar_pdf_boletim_ocr(url, ano)
                if sucesso:
                    total_sucesso += 1
                else:
                    total_erro += 1

                total_processados += 1

            if limite_pdfs and total_processados >= limite_pdfs:
                break

        logger.info(f"\n✓ Boletins processados: {total_sucesso} sucesso, {total_erro} erros")
        logger.info("=" * 80)


def main():
    """Função principal"""
    import sys

    extractor = SSPSCExtractorOCR()

    # Verificar argumentos
    limpar = '--limpar' in sys.argv

    # Verificar se há limite de PDFs (para testes)
    limite = None
    for arg in sys.argv:
        if arg.startswith('--limite='):
            limite = int(arg.split('=')[1])

    extractor.run(limpar_dados=limpar, limite_pdfs=limite)


if __name__ == '__main__':
    main()
