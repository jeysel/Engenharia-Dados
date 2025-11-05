"""
Extrator de Dados da SSP-SC com OCR - Versão 2
Versão melhorada que entende o formato de tabela: Município | Ano1 | Ano2 | Ano3...
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

# Lista de municípios de SC para validação (principais e mais comuns nos relatórios)
MUNICIPIOS_SC = [
    'FLORIANÓPOLIS', 'JOINVILLE', 'BLUMENAU', 'SÃO JOSÉ', 'CRICIÚMA',
    'CHAPECÓ', 'ITAJAÍ', 'JARAGUÁ DO SUL', 'LAGES', 'PALHOÇA',
    'BALNEÁRIO CAMBORIÚ', 'BRUSQUE', 'TUBARÃO', 'SÃO BENTO DO SUL',
    'CAÇADOR', 'CONCÓRDIA', 'CAMBORIÚ', 'NAVEGANTES', 'RIO DO SUL',
    'ARARANGUÁ', 'GASPAR', 'BIGUAÇU', 'INDAIAL', 'ITAPEMA',
    'MAFRA', 'CANOINHAS', 'IÇARA', 'VIDEIRA', 'RIO NEGRINHO',
    'IMBITUBA', 'SÃO MIGUEL DO OESTE', 'BARRA VELHA', 'XANXERÊ',
    'TIJUCAS', 'JOAÇABA', 'GUARAMIRIM', 'ARAQUARI', 'SCHROEDER',
    'ORLEANS', 'LAJEADO GRANDE', 'FORQUILHINHA', 'BRAÇO DO NORTE',
    'LAGUNA', 'JAGUARUNA', 'MONTE CARLO', 'PORTO BELO', 'PENHA',
    'ILHOTA', 'POMERODE', 'RIO DOS CEDROS', 'MASSARANDUBA',
    'TIMBÓ', 'RODEIO', 'ASCURRA', 'APIÚNA', 'PRESIDENTE GETÚLIO',
    'IBIRAMA', 'DONA EMMA', 'VITOR MEIRELES', 'WITMARSUM',
    'ITUPORANGA', 'AURORA', 'RIO DO OESTE', 'TAIÓ', 'MIRIM DOCE',
    'AGROLÂNDIA', 'AGRONÔMICA', 'TROMBUDO CENTRAL', 'POUSO REDONDO',
    'LAURENTINO', 'RIO DO CAMPO', 'SALETE', 'LONTRAS',
    'PRESIDENTE NEREU', 'IMBUIA', 'ATALANTA', 'PETROLÂNDIA',
    'CHAPADÃO DO LAGEADO', 'BRAÇO DO TROMBUDO', 'LEOBERTO LEAL'
]


class SSPSCExtractorOCRv2:
    """Extrator de dados da SSP-SC usando OCR - Versão melhorada"""

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
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
        return Image.fromarray(denoised)

    def extrair_texto_pdf_ocr(self, pdf_path: str) -> List[str]:
        """Extrai texto de PDF usando OCR"""
        textos_paginas = []

        try:
            logger.info(f"  Convertendo PDF em imagens...")
            images = convert_from_path(pdf_path, dpi=300)
            logger.info(f"  {len(images)} páginas para processar com OCR")

            for i, image in enumerate(images):
                logger.info(f"    Processando página {i+1}/{len(images)} com OCR...")
                processed_image = self.pre_processar_imagem(image)
                texto = pytesseract.image_to_string(
                    processed_image,
                    lang='por',
                    config='--psm 6'
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

    def validar_municipio(self, texto: str) -> bool:
        """Valida se o texto é um município válido"""
        texto_upper = texto.upper().strip()

        # Palavras que definitivamente NÃO são municípios
        palavras_invalidas = [
            'TOTAL', 'SUBTOTAL', 'MÉDIA', 'MEDIA', 'ESTADO', 'SC',
            'SANTA CATARINA', 'BOLETIM', 'MENSAL', 'INDICADORES',
            'CVLI', 'TAXA', 'POR', 'MIL', 'HABITANTES', 'ANO',
            'PERÍODO', 'PERIODO', 'ROUBO', 'FURTO', 'HOMICÍDIO',
            'HOMICIDIO', 'FEMINICÍDIO', 'FEMINICIDIO', 'LATROCÍNIO',
            'LATROCINIO', 'FONTE', 'DADOS', 'SEGURANÇA', 'SEGURANCA',
            'PÚBLICA', 'PUBLICA', 'BOLETIM MENSAL', 'DE MORTE',
            'POLÍCIA CIVIL', 'POLICIA CIVIL', 'POLÍCIA MILITAR', 'POLICIA MILITAR',
            'MORTE', 'CIVIL', 'MILITAR', 'LETAL', 'INTENCIONAL', 'CRIME',
            'VIOLENTO', 'VIOLENTA', 'INDICADOR', 'NÚMERO', 'NUMERO'
        ]

        # Verificar se contém alguma palavra inválida (exato ou contém)
        if texto_upper in palavras_invalidas:
            return False

        # Verificar se contém alguma palavra inválida como substring
        for palavra_inv in palavras_invalidas:
            if palavra_inv in texto_upper:
                return False

        # Deve ter pelo menos 3 letras
        if len(texto) < 3:
            return False

        # Deve conter letras
        if not any(c.isalpha() for c in texto):
            return False

        # Se parece com ano (4 dígitos)
        if re.match(r'^\d{4}$', texto):
            return False

        # Aceitar se está na lista de municípios conhecidos
        for mun in MUNICIPIOS_SC:
            if mun in texto_upper:
                return True

        # Se não está na lista de municípios conhecidos, rejeitar por segurança
        # (evita aceitar qualquer texto com mais de 3 letras)
        return False

    def processar_pdf_boletim_ocr(self, url: str, ano_boletim: int) -> Tuple[bool, str]:
        """Processa um PDF de boletim mensal usando OCR"""
        historico = HistoricoExecucao(
            data_hora_inicio=datetime.now(),
            tipo_dados='boletim_mensal_ocr_v2',
            fonte=url,
            anos_processados=str(ano_boletim)
        )

        try:
            nome_arquivo = url.split('/')[-1]
            mes = self.extrair_mes_do_nome_arquivo(nome_arquivo)

            logger.info(f"Processando: {nome_arquivo} (Boletim: {ano_boletim}, Mês: {mes})")

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

            # Processar página 1 (índice 0) - Roubo e Furto
            if len(textos_paginas) >= 1:
                registros = self._processar_texto_tabular(
                    textos_paginas[0], ano_boletim, mes, url, ['ROUBO', 'FURTO']
                )
                registros_inseridos += registros
                logger.info(f"  Página 1: {registros} registros (roubo/furto)")

            # Processar página 2 (índice 1) - Mortes Violentas / CVLI (dados estaduais)
            if len(textos_paginas) >= 2:
                registros = self._processar_texto_tabular(
                    textos_paginas[1], ano_boletim, mes, url, ['CVLI', 'MORTE']
                )
                registros_inseridos += registros
                logger.info(f"  Página 2: {registros} registros (mortes violentas - estadual)")

            # Processar páginas 4-11 (índices 3-10) - Dados municipais de homicídio
            total_homicidios = 0
            for i in range(3, min(11, len(textos_paginas))):  # Páginas 4-11 (índices 3-10)
                registros = self._processar_dados_municipais_homicidio(
                    textos_paginas[i], ano_boletim, mes, url
                )
                total_homicidios += registros
                if registros > 0:
                    logger.info(f"  Página {i+1}: {registros} registros (homicídios municipais)")

            registros_inseridos += total_homicidios
            logger.info(f"  Total de homicídios municipais: {total_homicidios} registros")

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

    def _processar_dados_municipais_homicidio(self, texto: str, ano_boletim: int, mes: Optional[int],
                                               fonte: str) -> int:
        """
        Processa dados municipais de homicídio das páginas 4-11.
        Formato: MUNICÍPIO col1 col2 col3 col4 col5 col6 col7
        Onde as colunas representam diferentes anos/períodos.

        Args:
            texto: Texto extraído do PDF
            ano_boletim: Ano do boletim (ex: 2025)
            mes: Mês do boletim
            fonte: URL do PDF
        """
        registros = 0

        try:
            linhas = texto.split('\n')

            # Anos que as colunas representam (baseado na análise da página 2)
            # Para um boletim de 2025, assumimos: últimos 5 anos completos + ano atual + período
            # As 7 colunas parecem ser: Ano-4, Ano-3, Ano-2, Ano-1, Ano-atual-acumulado, ?, Período
            # Vou usar apenas as primeiras 5 colunas que claramente representam anos
            anos = [ano_boletim - 4, ano_boletim - 3, ano_boletim - 2, ano_boletim - 1, ano_boletim]

            for linha in linhas:
                linha = linha.strip()

                if not linha or len(linha) < 5:
                    continue

                # Padrão: Nome do município seguido de números
                # Ex: "FLORIANÓPOLIS 40 37 26 43 38 27 34"
                match = re.match(r'^([A-ZÀÁÂÃÄÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜÝ\s\'\-]+?)\s+([\dO\)\s]+)$', linha, re.IGNORECASE)

                if match:
                    municipio_raw = match.group(1).strip()
                    numeros_str = match.group(2).strip()

                    # Validar município
                    if not self.validar_municipio(municipio_raw):
                        continue

                    # Extrair números (OCR pode confundir 0 com O ou com ))
                    numeros_str = numeros_str.replace('O)', '0').replace('O', '0').replace(')', '0')
                    numeros = re.findall(r'\d+', numeros_str)

                    if len(numeros) < 5:  # Precisamos de pelo menos 5 valores
                        continue

                    # Inserir um registro para cada um dos 5 primeiros anos
                    for i in range(min(5, len(numeros))):
                        try:
                            quantidade = int(numeros[i])
                            ano_dado = anos[i]

                            # Criar registro de homicídio
                            registro = Homicidio(
                                ano=ano_dado,
                                mes=mes,
                                municipio=municipio_raw,
                                tipo_homicidio='Homicídio',
                                quantidade=quantidade,
                                fonte=fonte
                            )
                            self.db_session.add(registro)
                            registros += 1

                        except (ValueError, IndexError):
                            continue

                    if registros > 0 and registros % 50 == 0:
                        self.db_session.commit()

            self.db_session.commit()

        except Exception as e:
            logger.error(f"Erro ao processar dados municipais: {e}")
            import traceback
            logger.error(traceback.format_exc())

        return registros

    def _processar_texto_tabular(self, texto: str, ano_boletim: int, mes: Optional[int],
                                 fonte: str, palavras_chave: List[str]) -> int:
        """
        Processa texto em formato tabular: Município | Ano1 | Ano2 | Ano3 | ... | Período

        Args:
            texto: Texto extraído do PDF
            ano_boletim: Ano do boletim (para referência)
            mes: Mês do boletim
            fonte: URL do PDF
            palavras_chave: Lista de palavras para identificar a seção (ex: ['ROUBO', 'FURTO'])
        """
        registros = 0

        try:
            linhas = texto.split('\n')

            # Detectar tipo de dados pela palavra-chave
            eh_roubo = any('ROUBO' in pk for pk in palavras_chave)
            eh_furto = any('FURTO' in pk for pk in palavras_chave)
            eh_cvli = any('CVLI' in pk or 'MORTE' in pk for pk in palavras_chave)

            # Procurar por linhas que começam com município seguido de números
            # Formato esperado: "FLORIANÓPOLIS 123 145 167 189 201"
            for linha in linhas:
                linha = linha.strip()

                if not linha or len(linha) < 5:
                    continue

                # Padrão: Nome (letras) seguido de múltiplos números separados por espaços
                # Captura: Nome + todos os números
                match = re.match(r'^([A-ZÀÁÂÃÄÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜÝ\s]+?)\s+((?:\d+\s*)+)', linha, re.IGNORECASE)

                if match:
                    municipio_raw = match.group(1).strip()
                    numeros_str = match.group(2).strip()

                    # Validar município
                    if not self.validar_municipio(municipio_raw):
                        continue

                    municipio = municipio_raw

                    # Extrair todos os números da linha
                    numeros = re.findall(r'\d+', numeros_str)

                    if not numeros:
                        continue

                    # Os números representam anos em ordem (geralmente 5 anos + período)
                    # Vamos usar apenas os primeiros números que representam anos
                    # Exemplo: [123, 145, 167, 189, 201] para anos 2020-2024

                    # Determinar os anos (últimos 5 anos a partir do ano do boletim)
                    anos = list(range(ano_boletim - 4, ano_boletim + 1))

                    # Para cada ano que temos dados
                    for i, numero_str in enumerate(numeros[:5]):  # Pegar no máximo 5 valores (5 anos)
                        try:
                            quantidade = int(numero_str)

                            # Validar quantidade (não pode ser ano ou valor muito grande)
                            if quantidade < 1 or quantidade > 10000:
                                continue

                            # Determinar o ano
                            if i < len(anos):
                                ano_dado = anos[i]
                            else:
                                continue  # Ignorar se passar dos 5 anos

                            # Inserir registro conforme o tipo
                            if eh_roubo:
                                registro = Roubo(
                                    ano=ano_dado,
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
                                    ano=ano_dado,
                                    mes=mes,
                                    municipio=municipio,
                                    tipo_furto='Furto',
                                    quantidade=quantidade,
                                    fonte=fonte
                                )
                                self.db_session.add(registro)
                                registros += 1

                            elif eh_cvli:
                                registro = MortesViolentas(
                                    ano=ano_dado,
                                    mes=mes,
                                    municipio=municipio,
                                    tipo_morte='CVLI - Crime Violento Letal Intencional',
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
            logger.error(f"Erro ao processar texto tabular: {e}")
            import traceback
            logger.error(traceback.format_exc())

        return registros

    def run(self, limpar_dados=False, limite_pdfs=None):
        """Executa o processo completo de extração com OCR"""
        logger.info("=" * 80)
        logger.info("Extrator SSP-SC - Versão com OCR v2 (Formato Tabular)")
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

    extractor = SSPSCExtractorOCRv2()

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
