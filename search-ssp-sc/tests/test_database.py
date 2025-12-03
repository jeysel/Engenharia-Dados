"""
Testes para operações de banco de dados

Testa schemas, queries e integridade dos dados
"""

import pytest
from datetime import datetime
from sqlalchemy import inspect
from extractor_autonomous import DadosSeguranca, Base


class TestDatabaseSchema:
    """Testes para schema do banco de dados"""

    def test_table_exists(self, db_engine):
        """Testa se tabela foi criada corretamente"""
        Base.metadata.create_all(db_engine)

        inspector = inspect(db_engine)
        tables = inspector.get_table_names()

        assert 'dados_seguranca' in tables

    def test_table_columns(self, db_engine):
        """Testa se todas as colunas existem"""
        Base.metadata.create_all(db_engine)

        inspector = inspect(db_engine)
        columns = [col['name'] for col in inspector.get_columns('dados_seguranca')]

        expected_columns = [
            'id',
            'data_coleta',
            'tipo_ocorrencia',
            'municipio',
            'regiao',
            'periodo',
            'quantidade',
            'ano',
            'mes',
            'dados_brutos'
        ]

        for col in expected_columns:
            assert col in columns

    def test_primary_key(self, db_engine):
        """Testa se primary key está configurada"""
        Base.metadata.create_all(db_engine)

        inspector = inspect(db_engine)
        pk = inspector.get_pk_constraint('dados_seguranca')

        assert 'id' in pk['constrained_columns']


class TestDataInsertion:
    """Testes para inserção de dados"""

    def test_insert_valid_record(self, db_session):
        """Testa inserção de registro válido"""
        dado = DadosSeguranca(
            tipo_ocorrencia='Homicídio Doloso',
            municipio='Florianópolis',
            regiao='Grande Florianópolis',
            periodo='2024-01',
            quantidade=5,
            ano=2024,
            mes=1,
            dados_brutos='{"test": "data"}'
        )

        db_session.add(dado)
        db_session.commit()

        # Verifica se foi inserido
        result = db_session.query(DadosSeguranca).first()
        assert result is not None
        assert result.tipo_ocorrencia == 'Homicídio Doloso'
        assert result.quantidade == 5

    def test_insert_multiple_records(self, db_session):
        """Testa inserção de múltiplos registros"""
        dados = [
            DadosSeguranca(
                tipo_ocorrencia=f'Crime {i}',
                municipio='Florianópolis',
                quantidade=i * 10,
                ano=2024
            )
            for i in range(1, 6)
        ]

        db_session.add_all(dados)
        db_session.commit()

        count = db_session.query(DadosSeguranca).count()
        assert count == 5

    def test_default_data_coleta(self, db_session):
        """Testa se data_coleta é preenchida automaticamente"""
        dado = DadosSeguranca(
            tipo_ocorrencia='Teste',
            municipio='Teste',
            quantidade=1,
            ano=2024
        )

        db_session.add(dado)
        db_session.commit()

        result = db_session.query(DadosSeguranca).first()
        assert result.data_coleta is not None
        assert isinstance(result.data_coleta, datetime)

    def test_nullable_fields(self, db_session):
        """Testa campos que podem ser NULL"""
        dado = DadosSeguranca(
            tipo_ocorrencia='Teste',
            municipio='Teste',
            quantidade=1,
            ano=2024,
            mes=None  # Mês pode ser NULL
        )

        db_session.add(dado)
        db_session.commit()

        result = db_session.query(DadosSeguranca).first()
        assert result.mes is None


class TestDataQuerying:
    """Testes para queries no banco"""

    @pytest.fixture
    def populated_db(self, db_session):
        """Popula banco com dados de teste"""
        dados = [
            DadosSeguranca(
                tipo_ocorrencia='Homicídio',
                municipio='Florianópolis',
                regiao='Grande Florianópolis',
                quantidade=5,
                ano=2024,
                mes=1
            ),
            DadosSeguranca(
                tipo_ocorrencia='Roubo',
                municipio='Joinville',
                regiao='Norte',
                quantidade=150,
                ano=2024,
                mes=2
            ),
            DadosSeguranca(
                tipo_ocorrencia='Homicídio',
                municipio='Blumenau',
                regiao='Vale do Itajaí',
                quantidade=3,
                ano=2024,
                mes=1
            ),
            DadosSeguranca(
                tipo_ocorrencia='Furto',
                municipio='Florianópolis',
                regiao='Grande Florianópolis',
                quantidade=89,
                ano=2023,
                mes=12
            )
        ]

        db_session.add_all(dados)
        db_session.commit()
        return db_session

    def test_query_by_municipio(self, populated_db):
        """Testa query por município"""
        results = populated_db.query(DadosSeguranca).filter(
            DadosSeguranca.municipio == 'Florianópolis'
        ).all()

        assert len(results) == 2

    def test_query_by_tipo_ocorrencia(self, populated_db):
        """Testa query por tipo de ocorrência"""
        results = populated_db.query(DadosSeguranca).filter(
            DadosSeguranca.tipo_ocorrencia == 'Homicídio'
        ).all()

        assert len(results) == 2

    def test_query_by_ano(self, populated_db):
        """Testa query por ano"""
        results = populated_db.query(DadosSeguranca).filter(
            DadosSeguranca.ano == 2024
        ).all()

        assert len(results) == 3

    def test_sum_quantidade_by_municipio(self, populated_db):
        """Testa agregação de quantidade por município"""
        from sqlalchemy import func

        result = populated_db.query(
            DadosSeguranca.municipio,
            func.sum(DadosSeguranca.quantidade).label('total')
        ).filter(
            DadosSeguranca.municipio == 'Florianópolis'
        ).group_by(
            DadosSeguranca.municipio
        ).first()

        assert result is not None
        assert result.total == 94  # 5 + 89

    def test_count_by_tipo(self, populated_db):
        """Testa contagem por tipo"""
        from sqlalchemy import func

        results = populated_db.query(
            DadosSeguranca.tipo_ocorrencia,
            func.count(DadosSeguranca.id).label('count')
        ).group_by(
            DadosSeguranca.tipo_ocorrencia
        ).all()

        assert len(results) == 3  # Homicídio, Roubo, Furto

    def test_order_by_quantidade(self, populated_db):
        """Testa ordenação por quantidade"""
        results = populated_db.query(DadosSeguranca).order_by(
            DadosSeguranca.quantidade.desc()
        ).all()

        assert results[0].quantidade == 150  # Maior quantidade
        assert results[-1].quantidade == 3   # Menor quantidade

    def test_filter_multiple_conditions(self, populated_db):
        """Testa filtro com múltiplas condições"""
        results = populated_db.query(DadosSeguranca).filter(
            DadosSeguranca.ano == 2024,
            DadosSeguranca.mes == 1
        ).all()

        assert len(results) == 2


class TestDataIntegrity:
    """Testes para integridade dos dados"""

    def test_duplicate_insertion(self, db_session):
        """Testa inserção de dados duplicados (permitido)"""
        dado1 = DadosSeguranca(
            tipo_ocorrencia='Homicídio',
            municipio='Florianópolis',
            quantidade=5,
            ano=2024
        )

        dado2 = DadosSeguranca(
            tipo_ocorrencia='Homicídio',
            municipio='Florianópolis',
            quantidade=5,
            ano=2024
        )

        db_session.add_all([dado1, dado2])
        db_session.commit()

        count = db_session.query(DadosSeguranca).count()
        assert count == 2  # Duplicatas são permitidas

    def test_string_length_limits(self, db_session):
        """Testa limites de tamanho de strings"""
        dado = DadosSeguranca(
            tipo_ocorrencia='A' * 200,  # Limite: 200
            municipio='B' * 200,
            regiao='C' * 100,
            periodo='D' * 100,
            quantidade=1,
            ano=2024
        )

        db_session.add(dado)
        db_session.commit()

        result = db_session.query(DadosSeguranca).first()
        assert len(result.tipo_ocorrencia) <= 200

    def test_negative_quantidade(self, db_session):
        """Testa inserção de quantidade negativa (deve ser evitado na aplicação)"""
        dado = DadosSeguranca(
            tipo_ocorrencia='Teste',
            municipio='Teste',
            quantidade=-1,  # Negativo
            ano=2024
        )

        # Banco permite, mas aplicação deve validar
        db_session.add(dado)
        db_session.commit()

        result = db_session.query(DadosSeguranca).first()
        assert result.quantidade == -1

    def test_json_dados_brutos(self, db_session):
        """Testa armazenamento de JSON em dados_brutos"""
        import json

        dados_json = json.dumps({
            'source': 'SSP-SC',
            'timestamp': '2024-01-01T10:00:00',
            'raw_data': {'test': 'value'}
        })

        dado = DadosSeguranca(
            tipo_ocorrencia='Teste',
            municipio='Teste',
            quantidade=1,
            ano=2024,
            dados_brutos=dados_json
        )

        db_session.add(dado)
        db_session.commit()

        result = db_session.query(DadosSeguranca).first()
        parsed = json.loads(result.dados_brutos)
        assert parsed['source'] == 'SSP-SC'


class TestDatabasePerformance:
    """Testes de performance básicos"""

    def test_bulk_insert_performance(self, db_session):
        """Testa performance de inserção em massa"""
        import time

        # Gera 1000 registros
        dados = [
            DadosSeguranca(
                tipo_ocorrencia=f'Crime {i}',
                municipio=f'Município {i % 10}',
                quantidade=i,
                ano=2024
            )
            for i in range(1000)
        ]

        start = time.time()
        db_session.add_all(dados)
        db_session.commit()
        duration = time.time() - start

        # Deve inserir 1000 registros em menos de 5 segundos
        assert duration < 5.0

        count = db_session.query(DadosSeguranca).count()
        assert count == 1000

    def test_query_performance(self, db_session):
        """Testa performance de queries"""
        import time

        # Insere dados
        dados = [
            DadosSeguranca(
                tipo_ocorrencia=f'Crime {i % 5}',
                municipio=f'Município {i % 10}',
                quantidade=i,
                ano=2024
            )
            for i in range(1000)
        ]
        db_session.add_all(dados)
        db_session.commit()

        # Query com filtro
        start = time.time()
        results = db_session.query(DadosSeguranca).filter(
            DadosSeguranca.municipio == 'Município 5'
        ).all()
        duration = time.time() - start

        # Query deve ser rápida (< 1 segundo)
        assert duration < 1.0
        assert len(results) == 100
