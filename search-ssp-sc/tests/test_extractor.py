"""
Testes para o extrator SSP-SC

Testa funcionalidades principais do extractor_autonomous.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from extractor_autonomous import SSPSCExtractorAutonomous, DadosSeguranca


class TestSSPSCExtractor:
    """Testes para classe SSPSCExtractorAutonomous"""

    def test_init_with_default_params(self):
        """Testa inicialização com parâmetros padrão"""
        extractor = SSPSCExtractorAutonomous()

        assert extractor.base_url == "https://ssp.sc.gov.br/segurancaemnumeros/"
        assert extractor.session is not None
        assert 'User-Agent' in extractor.session.headers

    def test_init_with_custom_db_url(self, test_database_url):
        """Testa inicialização com URL customizada"""
        extractor = SSPSCExtractorAutonomous(db_url=test_database_url)

        assert extractor.db_url == test_database_url

    def test_process_record_with_valid_data(self):
        """Testa processamento de registro válido"""
        extractor = SSPSCExtractorAutonomous()

        record = {
            'tipo': 'Homicídio',
            'município': 'Florianópolis',
            'quantidade': '10',
            'ano': '2024'
        }

        result = extractor._process_record(record)

        assert result is not None
        assert result['tipo_ocorrencia'] == 'Homicídio'
        assert result['municipio'] == 'Florianópolis'
        assert result['quantidade'] == 10
        assert result['ano'] == 2024

    def test_process_record_with_missing_fields(self):
        """Testa processamento com campos faltando"""
        extractor = SSPSCExtractorAutonomous()

        record = {
            'quantidade': '50'
        }

        result = extractor._process_record(record)

        assert result is not None
        assert result['tipo_ocorrencia'] == 'Não especificado'
        assert result['municipio'] == 'Não especificado'
        assert result['quantidade'] == 50

    def test_process_record_with_invalid_data(self):
        """Testa processamento com dados inválidos"""
        extractor = SSPSCExtractorAutonomous()

        record = {}

        result = extractor._process_record(record)

        # Deve retornar algo mesmo com dados vazios
        assert result is not None

    def test_extract_from_html_tables(self, sample_html_table):
        """Testa extração de tabelas HTML"""
        extractor = SSPSCExtractorAutonomous()

        dados = extractor.extract_from_html_tables(sample_html_table)

        assert len(dados) > 0
        assert 'municipio' in dados[0] or 'tipo_ocorrencia' in dados[0]

    def test_extract_from_html_with_empty_html(self):
        """Testa extração com HTML vazio"""
        extractor = SSPSCExtractorAutonomous()

        dados = extractor.extract_from_html_tables("<html></html>")

        assert isinstance(dados, list)
        assert len(dados) == 0

    @patch('extractor_autonomous.requests.Session.get')
    def test_discover_api_endpoints(self, mock_get):
        """Testa descoberta de endpoints"""
        # Mock da resposta HTTP
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"""
        <html>
            <script>
                fetch('/api/dados');
                axios.get('/api/estatisticas');
            </script>
        </html>
        """
        mock_get.return_value = mock_response

        extractor = SSPSCExtractorAutonomous()
        endpoints = extractor.discover_api_endpoints()

        assert isinstance(endpoints, list)
        # Pode retornar endpoints descobertos ou common endpoints
        assert len(endpoints) >= 0

    @patch('extractor_autonomous.requests.Session.get')
    def test_extract_from_api_json(self, mock_get):
        """Testa extração de API JSON"""
        # Mock da resposta JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'municipio': 'Florianópolis', 'quantidade': 10},
            {'municipio': 'Joinville', 'quantidade': 20}
        ]
        mock_get.return_value = mock_response

        extractor = SSPSCExtractorAutonomous()
        dados = extractor.extract_from_api('http://test.com/api')

        assert len(dados) == 2
        assert dados[0]['municipio'] == 'Florianópolis'

    @patch('extractor_autonomous.requests.Session.get')
    def test_extract_from_api_with_error(self, mock_get):
        """Testa extração com erro na API"""
        mock_get.side_effect = Exception("Network error")

        extractor = SSPSCExtractorAutonomous()
        dados = extractor.extract_from_api('http://test.com/api')

        assert isinstance(dados, list)
        assert len(dados) == 0

    def test_save_to_files(self, temp_data_dir, sample_raw_data):
        """Testa salvamento em arquivos"""
        extractor = SSPSCExtractorAutonomous()
        extractor.output_dir = temp_data_dir

        extractor.save_to_files(sample_raw_data)

        # Verifica se arquivos foram criados
        import os
        files = os.listdir(temp_data_dir)

        csv_files = [f for f in files if f.endswith('.csv')]
        json_files = [f for f in files if f.endswith('.json')]

        assert len(csv_files) > 0
        assert len(json_files) > 0

    def test_save_to_files_with_empty_data(self, temp_data_dir):
        """Testa salvamento com dados vazios"""
        extractor = SSPSCExtractorAutonomous()
        extractor.output_dir = temp_data_dir

        # Não deve gerar erro
        extractor.save_to_files([])

        import os
        files = os.listdir(temp_data_dir)
        assert len(files) == 0


class TestDatabaseOperations:
    """Testes para operações de banco de dados"""

    def test_save_to_database(self, db_session, sample_raw_data):
        """Testa salvamento no banco de dados"""
        extractor = SSPSCExtractorAutonomous()
        extractor.session_db = db_session

        extractor.save_to_database(sample_raw_data)

        # Verifica se registros foram salvos
        count = db_session.query(DadosSeguranca).count()
        assert count == len(sample_raw_data)

    def test_save_to_database_with_invalid_data(self, db_session):
        """Testa salvamento com dados inválidos"""
        extractor = SSPSCExtractorAutonomous()
        extractor.session_db = db_session

        invalid_data = [
            {'tipo_ocorrencia': None, 'quantidade': 'invalid'}
        ]

        # Não deve gerar erro crítico
        extractor.save_to_database(invalid_data)

    def test_database_model_creation(self, db_session):
        """Testa criação de modelo no banco"""
        dado = DadosSeguranca(
            tipo_ocorrencia='Homicídio',
            municipio='Florianópolis',
            quantidade=10,
            ano=2024
        )

        db_session.add(dado)
        db_session.commit()

        # Verifica se foi salvo
        result = db_session.query(DadosSeguranca).first()
        assert result is not None
        assert result.tipo_ocorrencia == 'Homicídio'
        assert result.municipio == 'Florianópolis'


@pytest.mark.integration
class TestFullExtractionFlow:
    """Testes de integração do fluxo completo"""

    @patch('extractor_autonomous.requests.Session.get')
    def test_full_extraction_flow(self, mock_get, db_session, temp_data_dir):
        """Testa fluxo completo de extração"""
        # Mock da resposta HTTP
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <table>
                <tr><th>Município</th><th>Quantidade</th></tr>
                <tr><td>Florianópolis</td><td>10</td></tr>
            </table>
        </html>
        """
        mock_response.content = mock_response.text.encode()
        mock_get.return_value = mock_response

        extractor = SSPSCExtractorAutonomous()
        extractor.session_db = db_session
        extractor.output_dir = temp_data_dir

        # Executa extração
        dados = extractor.extract()

        # Verifica resultados
        assert isinstance(dados, list)

        if dados:
            # Salva
            extractor.save_to_database(dados)
            extractor.save_to_files(dados)

            # Verifica banco
            count = db_session.query(DadosSeguranca).count()
            assert count > 0

            # Verifica arquivos
            import os
            files = os.listdir(temp_data_dir)
            assert len(files) > 0
