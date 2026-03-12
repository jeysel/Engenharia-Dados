"""
Configuração de fixtures do pytest

Fixtures compartilhadas entre todos os testes
"""

import pytest
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys

# Adiciona o diretório do extrator ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../extrator'))


@pytest.fixture(scope="session", autouse=True)
def setup_log_directory():
    """Cria diretório de logs para testes (compatível com Windows/Linux)"""
    import platform

    if platform.system() == 'Windows':
        log_dir = r'C:\var\log'
    else:
        log_dir = '/var/log'

    os.makedirs(log_dir, exist_ok=True)

    # Garante que os arquivos de log existam
    log_files = [
        os.path.join(log_dir, 'ssp-sc-extractor.log'),
        os.path.join(log_dir, 'ssp-sc-scheduler.log')
    ]

    for log_file in log_files:
        if not os.path.exists(log_file):
            open(log_file, 'a').close()

    yield

    # Cleanup opcional (descomente se quiser remover os logs após os testes)
    # for log_file in log_files:
    #     if os.path.exists(log_file):
    #         os.remove(log_file)


@pytest.fixture(scope="session")
def test_database_url():
    """URL do banco de dados de teste"""
    return os.getenv(
        'TEST_DATABASE_URL',
        'postgresql://user:password@localhost:5432/ssp_sc_test_db'
    )


@pytest.fixture(scope="function")
def db_engine(test_database_url):
    """Cria engine de banco de dados para testes"""
    engine = create_engine(test_database_url)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Cria sessão de banco de dados com rollback automático"""
    from extractor_autonomous import Base

    # Cria tabelas
    Base.metadata.create_all(db_engine)

    # Cria sessão
    Session = sessionmaker(bind=db_engine)
    session = Session()

    yield session

    # Rollback e cleanup
    session.rollback()
    session.close()
    Base.metadata.drop_all(db_engine)


@pytest.fixture
def temp_data_dir():
    """Diretório temporário para testes"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_raw_data():
    """Dados de exemplo para testes"""
    return [
        {
            'tipo_ocorrencia': 'Homicídio Doloso',
            'municipio': 'Florianópolis',
            'regiao': 'Grande Florianópolis',
            'periodo': '2024-01',
            'quantidade': 5,
            'ano': 2024,
            'mes': 1
        },
        {
            'tipo_ocorrencia': 'Roubo',
            'municipio': 'Joinville',
            'regiao': 'Norte',
            'periodo': '2024-02',
            'quantidade': 150,
            'ano': 2024,
            'mes': 2
        },
        {
            'tipo_ocorrencia': 'Furto',
            'municipio': 'Blumenau',
            'regiao': 'Vale do Itajaí',
            'periodo': '2024-03',
            'quantidade': 89,
            'ano': 2024,
            'mes': 3
        }
    ]


@pytest.fixture
def sample_html_table():
    """HTML de tabela de exemplo para testes"""
    return """
    <html>
        <body>
            <table>
                <tr>
                    <th>Município</th>
                    <th>Tipo</th>
                    <th>Quantidade</th>
                    <th>Ano</th>
                </tr>
                <tr>
                    <td>Florianópolis</td>
                    <td>Homicídio</td>
                    <td>10</td>
                    <td>2024</td>
                </tr>
                <tr>
                    <td>Joinville</td>
                    <td>Roubo</td>
                    <td>200</td>
                    <td>2024</td>
                </tr>
            </table>
        </body>
    </html>
    """


@pytest.fixture
def mock_ssp_response():
    """Mock de resposta da API SSP-SC"""
    return {
        'data': [
            {'municipio': 'Florianópolis', 'tipo': 'Homicídio', 'quantidade': 5},
            {'municipio': 'Joinville', 'tipo': 'Roubo', 'quantidade': 100}
        ]
    }
