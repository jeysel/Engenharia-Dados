"""
Agendador de Extração - Executa extrator em intervalos regulares
Funciona como daemon/serviço
"""

import time
import signal
import sys
import os
import logging
from datetime import datetime
from extractor_autonomous import SSPSCExtractorAutonomous

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/ssp-sc-scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Variável global para controle de shutdown graceful
running = True


def signal_handler(signum, frame):
    """Handler para sinais de sistema (SIGTERM, SIGINT)"""
    global running
    logger.info(f"Sinal recebido: {signum}. Encerrando gracefully...")
    running = False


def run_extraction():
    """Executa uma extração"""
    try:
        logger.info("=" * 80)
        logger.info(f"Iniciando extração agendada - {datetime.now()}")
        logger.info("=" * 80)

        extractor = SSPSCExtractorAutonomous()
        extractor.run()

        logger.info("Extração agendada concluída com sucesso")

    except Exception as e:
        logger.error(f"Erro durante extração agendada: {e}", exc_info=True)


def main():
    """Função principal do scheduler"""
    global running

    # Registrar handlers para sinais
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Intervalo entre extrações (em segundos)
    interval = int(os.getenv('EXTRACTION_INTERVAL', 3600))  # Padrão: 1 hora

    logger.info("=" * 80)
    logger.info("SSP-SC Scheduler - Iniciado")
    logger.info(f"Intervalo de extração: {interval} segundos ({interval/3600:.1f} horas)")
    logger.info("=" * 80)

    # Executar imediatamente na inicialização
    logger.info("Executando primeira extração...")
    run_extraction()

    # Loop principal
    last_run = time.time()

    while running:
        try:
            current_time = time.time()
            elapsed = current_time - last_run

            if elapsed >= interval:
                # Hora de executar nova extração
                run_extraction()
                last_run = current_time
            else:
                # Aguardar
                remaining = interval - elapsed
                if remaining > 60:
                    logger.info(f"Próxima extração em {remaining/60:.1f} minutos...")

                # Sleep em pequenos intervalos para responder rapidamente a sinais
                time.sleep(min(60, remaining))

        except KeyboardInterrupt:
            logger.info("Interrompido pelo usuário")
            break
        except Exception as e:
            logger.error(f"Erro no loop principal: {e}", exc_info=True)
            time.sleep(60)  # Aguardar 1 minuto antes de tentar novamente

    logger.info("Scheduler encerrado")
    sys.exit(0)


if __name__ == '__main__':
    main()
