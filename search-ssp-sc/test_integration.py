"""
Script de teste de integração para a nova versão do SSP-SC
Valida a estrutura do banco de dados e funcionalidade básica
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_database_connection(db_url):
    """Testa conexão com banco de dados"""
    logger.info("Testando conexão com banco de dados...")
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("✓ Conexão com banco de dados OK")
            return engine
    except Exception as e:
        logger.error(f"✗ Erro ao conectar ao banco de dados: {e}")
        return None


def test_tables_exist(engine):
    """Verifica se as tabelas necessárias existem"""
    logger.info("\nVerificando tabelas do banco de dados...")

    tabelas_esperadas = [
        'roubo',
        'furto',
        'mortes_violentas',
        'homicidio',
        'violencia_domestica',
        'historico_execucao'
    ]

    inspector = inspect(engine)
    tabelas_existentes = inspector.get_table_names()

    todas_ok = True
    for tabela in tabelas_esperadas:
        if tabela in tabelas_existentes:
            logger.info(f"✓ Tabela '{tabela}' existe")

            # Verificar colunas
            colunas = [col['name'] for col in inspector.get_columns(tabela)]
            logger.info(f"  Colunas: {', '.join(colunas)}")
        else:
            logger.error(f"✗ Tabela '{tabela}' NÃO existe")
            todas_ok = False

    return todas_ok


def test_old_table_removed(engine):
    """Verifica se a tabela antiga foi removida"""
    logger.info("\nVerificando remoção de tabelas antigas...")

    inspector = inspect(engine)
    tabelas_existentes = inspector.get_table_names()

    if 'dados_seguranca' in tabelas_existentes:
        logger.warning("⚠ Tabela antiga 'dados_seguranca' ainda existe")
        logger.info("  Execute: python extractor_new.py --limpar-antigas")
        return False
    else:
        logger.info("✓ Tabela antiga 'dados_seguranca' removida")
        return True


def test_data_exists(engine):
    """Verifica se há dados nas tabelas"""
    logger.info("\nVerificando dados nas tabelas...")

    tabelas = ['roubo', 'furto', 'mortes_violentas', 'homicidio', 'violencia_domestica']

    with engine.connect() as conn:
        for tabela in tabelas:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {tabela}"))
                count = result.scalar()
                if count > 0:
                    logger.info(f"✓ Tabela '{tabela}': {count} registros")
                else:
                    logger.warning(f"⚠ Tabela '{tabela}': 0 registros")
            except Exception as e:
                logger.error(f"✗ Erro ao consultar '{tabela}': {e}")


def test_historico_execucao(engine):
    """Verifica histórico de execuções"""
    logger.info("\nVerificando histórico de execuções...")

    with engine.connect() as conn:
        try:
            result = conn.execute(text("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'sucesso' THEN 1 ELSE 0 END) as sucessos,
                    SUM(CASE WHEN status = 'erro' THEN 1 ELSE 0 END) as erros
                FROM historico_execucao
            """))

            row = result.fetchone()
            total, sucessos, erros = row

            logger.info(f"  Total de execuções: {total}")
            logger.info(f"  Sucessos: {sucessos}")
            logger.info(f"  Erros: {erros}")

            if total > 0:
                logger.info("✓ Histórico de execuções existe")

                # Mostrar últimas 5 execuções
                result = conn.execute(text("""
                    SELECT
                        data_hora_inicio,
                        status,
                        tipo_dados,
                        registros_inseridos
                    FROM historico_execucao
                    ORDER BY data_hora_inicio DESC
                    LIMIT 5
                """))

                logger.info("\n  Últimas 5 execuções:")
                for row in result:
                    logger.info(f"    {row[0]} | {row[1]} | {row[2]} | {row[3]} registros")

            else:
                logger.warning("⚠ Nenhuma execução registrada")

        except Exception as e:
            logger.error(f"✗ Erro ao consultar histórico: {e}")


def test_indexes(engine):
    """Verifica se os índices foram criados"""
    logger.info("\nVerificando índices...")

    inspector = inspect(engine)
    tabelas_indices = {
        'roubo': ['idx_roubo_ano_mes', 'idx_roubo_municipio'],
        'furto': ['idx_furto_ano_mes', 'idx_furto_municipio'],
        'mortes_violentas': ['idx_mortes_ano_mes', 'idx_mortes_municipio'],
        'homicidio': ['idx_homicidio_ano_mes', 'idx_homicidio_municipio'],
        'violencia_domestica': ['idx_violencia_ano_semestre', 'idx_violencia_municipio', 'idx_violencia_tipo_registro'],
        'historico_execucao': ['idx_historico_data', 'idx_historico_tipo']
    }

    for tabela, indices_esperados in tabelas_indices.items():
        try:
            indices = inspector.get_indexes(tabela)
            indices_nomes = [idx['name'] for idx in indices]

            for idx_nome in indices_esperados:
                if idx_nome in indices_nomes:
                    logger.info(f"✓ Índice '{idx_nome}' existe na tabela '{tabela}'")
                else:
                    logger.warning(f"⚠ Índice '{idx_nome}' NÃO existe na tabela '{tabela}'")

        except Exception as e:
            logger.error(f"✗ Erro ao verificar índices de '{tabela}': {e}")


def test_api_endpoints():
    """Testa endpoints da API (se disponível)"""
    logger.info("\nTestando endpoints da API...")

    try:
        import requests

        base_url = os.getenv('VISUALIZACAO_URL', 'http://localhost:5000')

        endpoints = [
            '/health',
            '/api/filtros',
            '/api/estatisticas',
            '/api/historico'
        ]

        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    logger.info(f"✓ Endpoint '{endpoint}': OK")
                else:
                    logger.warning(f"⚠ Endpoint '{endpoint}': Status {response.status_code}")
            except requests.exceptions.ConnectionError:
                logger.warning(f"⚠ Endpoint '{endpoint}': Serviço não disponível")
            except Exception as e:
                logger.error(f"✗ Endpoint '{endpoint}': Erro {e}")

    except ImportError:
        logger.warning("⚠ Biblioteca 'requests' não disponível. Pulando teste de API.")


def main():
    """Função principal"""
    logger.info("=" * 80)
    logger.info("TESTE DE INTEGRAÇÃO - SSP-SC Nova Versão")
    logger.info("=" * 80)

    # Obter URL do banco de dados
    db_url = os.getenv(
        'DATABASE_URL',
        'postgresql://user:password@localhost:5432/ssp_sc_db'
    )

    logger.info(f"\nURL do banco: {db_url.replace(db_url.split('@')[0].split('//')[1], '***')}")

    # Executar testes
    engine = test_database_connection(db_url)

    if not engine:
        logger.error("\nTestes abortados: não foi possível conectar ao banco de dados")
        sys.exit(1)

    tabelas_ok = test_tables_exist(engine)
    test_old_table_removed(engine)
    test_data_exists(engine)
    test_historico_execucao(engine)
    test_indexes(engine)
    test_api_endpoints()

    # Resumo
    logger.info("\n" + "=" * 80)
    logger.info("RESUMO DOS TESTES")
    logger.info("=" * 80)

    if tabelas_ok:
        logger.info("✓ Estrutura do banco de dados: OK")
    else:
        logger.error("✗ Estrutura do banco de dados: FALHOU")

    logger.info("\nPara executar o extrator:")
    logger.info("  docker exec ssp-sc-extrator-new python extractor_new.py")

    logger.info("\nPara acessar o dashboard:")
    logger.info("  http://localhost:5000")

    logger.info("\n" + "=" * 80)


if __name__ == '__main__':
    main()
