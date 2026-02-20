"""
Ponto de entrada do sistema de agentes Renova Be.
Inicia o bot do Telegram com polling.
"""

import logging
import sys
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

from config.settings import TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY
from src.telegram.bot import create_bot

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def main():
    # Validações
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN não configurado. Defina no .env")
        sys.exit(1)

    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY não configurado. Defina no .env")
        sys.exit(1)

    logger.info("Iniciando Orquestrador de Agentes Renova Be...")

    bot = create_bot()

    logger.info("Bot do Telegram iniciado. Aguardando mensagens...")
    bot.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
