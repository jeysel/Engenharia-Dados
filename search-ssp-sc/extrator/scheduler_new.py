"""
Scheduler para execução periódica do novo extrator SSP-SC
"""

import os
import time
import signal
import sys
import logging
from datetime import datetime
from extractor_new import SSPSCExtractorNew

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/data/scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Variável global para controlar shutdown graceful
shutdown_requested = False


def signal_handler(signum, frame):
    """Handler para sinais de shutdown"""
    global shutdown_requested
    logger.info(f"Sinal {signum} recebido. Iniciando shutdown graceful...")
    shutdown_requested = True


def main():
    """Função principal do scheduler"""
    # Registrar handlers de sinal
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Intervalo de execução em segundos (padrão: 6 horas)
    intervalo = int(os.getenv('EXTRACTOR_INTERVAL', 21600))

    logger.info("=" * 80)
    logger.info("Scheduler do Extrator SSP-SC iniciado")
    logger.info(f"Intervalo de execução: {intervalo} segundos ({intervalo/3600:.1f} horas)")
    logger.info("=" * 80)

    # Executar imediatamente na primeira vez
    logger.info("\nExecutando extração inicial...")
    try:
        extractor = SSPSCExtractorNew()
        extractor.run()
        logger.info("Extração inicial concluída com sucesso")
    except Exception as e:
        logger.error(f"Erro na extração inicial: {e}")
        import traceback
        logger.error(traceback.format_exc())

    # Loop principal
    while not shutdown_requested:
        try:
            logger.info(f"\nPróxima execução em {intervalo/3600:.1f} horas...")
            logger.info(f"Próxima execução: {datetime.fromtimestamp(time.time() + intervalo).strftime('%Y-%m-%d %H:%M:%S')}")

            # Aguardar intervalo (verificando shutdown a cada 60 segundos)
            tempo_decorrido = 0
            while tempo_decorrido < intervalo and not shutdown_requested:
                time.sleep(min(60, intervalo - tempo_decorrido))
                tempo_decorrido += 60

            if shutdown_requested:
                break

            # Executar extração
            logger.info("\n" + "=" * 80)
            logger.info(f"Iniciando extração agendada - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 80)

            try:
                extractor = SSPSCExtractorNew()
                extractor.run()
                logger.info("Extração agendada concluída com sucesso")
            except Exception as e:
                logger.error(f"Erro na extração agendada: {e}")
                import traceback
                logger.error(traceback.format_exc())

        except Exception as e:
            logger.error(f"Erro no loop principal: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Aguardar um pouco antes de tentar novamente
            time.sleep(300)  # 5 minutos

    logger.info("\n" + "=" * 80)
    logger.info("Scheduler finalizado")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
