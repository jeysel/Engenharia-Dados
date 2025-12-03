"""
DAG do Airflow para Extração de Dados SSP-SC

Substitui o scheduler.py com orquestração profissional.
Executa extração automática em intervalos configuráveis.
"""

import sys
import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.dates import days_ago

# Adiciona o diretório do extrator ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../extrator'))

# Configurações padrão da DAG
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30),
}


def extract_data(**context):
    """
    Executa extração de dados da SSP-SC

    Args:
        context: Contexto do Airflow com informações da execução
    """
    from extractor_autonomous import SSPSCExtractorAutonomous
    import logging

    logger = logging.getLogger(__name__)
    execution_date = context['execution_date']

    logger.info(f"Iniciando extração - Execution Date: {execution_date}")

    try:
        # Inicializa o extrator
        extractor = SSPSCExtractorAutonomous()

        # Executa extração
        dados = extractor.extract()

        if dados:
            logger.info(f"Extração concluída: {len(dados)} registros")

            # Salva em múltiplos destinos
            extractor.save_to_database(dados)
            extractor.save_to_files(dados)

            # Retorna métricas via XCom
            return {
                'registros_extraidos': len(dados),
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            }
        else:
            logger.warning("Nenhum dado extraído")
            return {
                'registros_extraidos': 0,
                'timestamp': datetime.now().isoformat(),
                'status': 'no_data'
            }

    except Exception as e:
        logger.error(f"Erro na extração: {e}", exc_info=True)
        raise


def validate_extraction(**context):
    """
    Valida se a extração foi bem-sucedida

    Args:
        context: Contexto do Airflow
    """
    import logging

    logger = logging.getLogger(__name__)

    # Puxa métricas da task anterior via XCom
    ti = context['task_instance']
    metrics = ti.xcom_pull(task_ids='extract_data')

    if not metrics:
        raise ValueError("Nenhuma métrica recebida da extração")

    registros = metrics.get('registros_extraidos', 0)
    status = metrics.get('status', 'unknown')

    logger.info(f"Validação - Registros: {registros}, Status: {status}")

    # Validações básicas
    if status == 'success' and registros > 0:
        logger.info(f"✓ Validação OK: {registros} registros extraídos")
    elif status == 'no_data':
        logger.warning("⚠ Nenhum dado extraído - verificar fonte")
    else:
        raise ValueError(f"Extração falhou: {status}")


def send_metrics(**context):
    """
    Envia métricas para monitoramento (placeholder)

    Args:
        context: Contexto do Airflow
    """
    import logging

    logger = logging.getLogger(__name__)
    ti = context['task_instance']
    metrics = ti.xcom_pull(task_ids='extract_data')

    if metrics:
        logger.info(f"Métricas prontas para envio: {metrics}")
        # Aqui você pode integrar com CloudWatch, Prometheus, etc.
        # Exemplo: cloudwatch.put_metric_data(...)
    else:
        logger.warning("Nenhuma métrica disponível para envio")


# Definição da DAG
with DAG(
    dag_id='ssp_sc_extraction',
    default_args=default_args,
    description='Extração automática de dados SSP-SC',
    schedule_interval='@hourly',  # Executa a cada hora (pode ajustar)
    start_date=days_ago(1),
    catchup=False,  # Não executa datas passadas
    tags=['extraction', 'ssp-sc', 'public-safety'],
    max_active_runs=1,  # Apenas 1 execução por vez
) as dag:

    # Task inicial (documentação)
    start = EmptyOperator(
        task_id='start',
        doc="""
        Início do pipeline de extração SSP-SC.

        Este DAG orquestra a extração automática de dados
        de segurança pública de Santa Catarina.
        """
    )

    # Task de extração
    extract = PythonOperator(
        task_id='extract_data',
        python_callable=extract_data,
        provide_context=True,
        doc="""
        Extrai dados da SSP-SC usando extractor_autonomous.py

        Output: Métricas via XCom
        - registros_extraidos: int
        - timestamp: str (ISO format)
        - status: str (success/no_data/error)
        """
    )

    # Task de validação
    validate = PythonOperator(
        task_id='validate_extraction',
        python_callable=validate_extraction,
        provide_context=True,
        doc="""
        Valida se a extração foi bem-sucedida.

        Verifica:
        - Número de registros extraídos
        - Status da extração
        """
    )

    # Task de métricas
    metrics = PythonOperator(
        task_id='send_metrics',
        python_callable=send_metrics,
        provide_context=True,
        trigger_rule='all_done',  # Executa mesmo se validate falhar
        doc="""
        Envia métricas para sistema de monitoramento.

        Integração futura com:
        - AWS CloudWatch
        - Prometheus
        - DataDog
        """
    )

    # Task final
    end = EmptyOperator(
        task_id='end',
        trigger_rule='all_done',
        doc="Fim do pipeline de extração"
    )

    # Definição do fluxo (DAG Graph)
    start >> extract >> validate >> metrics >> end


# Informações da DAG para documentação
dag.doc_md = """
# Pipeline de Extração SSP-SC

## Objetivo
Extrai dados de segurança pública do site da SSP-SC de forma automatizada e confiável.

## Schedule
- **Frequência**: A cada hora (`@hourly`)
- **Alternativos**:
  - `@daily` - Uma vez por dia
  - `@weekly` - Uma vez por semana
  - `0 */6 * * *` - A cada 6 horas

## Tasks

1. **start**: Marca início do pipeline
2. **extract_data**: Executa extração de dados
3. **validate_extraction**: Valida qualidade dos dados
4. **send_metrics**: Envia métricas para monitoramento
5. **end**: Marca fim do pipeline

## Dados Extraídos
- Origem: https://ssp.sc.gov.br/segurancaemnumeros/
- Formato: JSON, CSV
- Destinos: PostgreSQL + arquivos locais

## Alertas
- Falha na extração: Task `extract_data` falha
- Sem dados: Task `validate_extraction` gera warning
- Métricas sempre enviadas via `send_metrics` (trigger_rule='all_done')

## Configuração

### Ajustar frequência:
Edite `schedule_interval` no código:
```python
schedule_interval='@daily'  # Para uma vez por dia
```

### Configurar alertas:
Edite `default_args`:
```python
'email_on_failure': True,
'email': ['seu-email@example.com']
```

## Monitoramento
- Airflow UI: http://localhost:8080/dags/ssp_sc_extraction
- Logs: Task logs na UI do Airflow
- Métricas: XCom values em cada task

## Troubleshooting

### Extração falha constantemente
1. Verificar conectividade com SSP-SC
2. Verificar conexão com PostgreSQL
3. Checar logs da task `extract_data`

### Sem dados extraídos
1. Site da SSP-SC pode estar offline
2. Estrutura HTML do site mudou
3. Verificar logs para detalhes

### Task travando
- Timeout configurado: 30 minutos
- Após timeout, task falha automaticamente
"""
