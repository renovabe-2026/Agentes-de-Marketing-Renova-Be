"""
Agentes de Marketing - Renova Be
=================================

Modos de uso:

1. Bot Telegram (fica escutando mensagens):
   python -m src.main telegram

2. Executar tarefa via CLI e enviar resultado por email:
   python -m src.main email "Crie 3 copies para anúncio de whey protein"

3. Executar tarefa via CLI e enviar por Telegram + Email:
   python -m src.main all "Crie 3 copies para anúncio de whey protein"

4. Apenas executar e imprimir no terminal:
   python -m src.main run "Crie 3 copies para anúncio de whey protein"
"""

import argparse
import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _get_env(key: str) -> str:
    value = os.getenv(key, "")
    if not value:
        logger.error("Variável de ambiente %s não definida. Verifique o .env", key)
        sys.exit(1)
    return value


def cmd_run(task: str) -> dict[str, str]:
    """Executa a tarefa e retorna os resultados."""
    from src.orchestrator.task_router import run_task

    api_key = _get_env("ANTHROPIC_API_KEY")
    logger.info("Executando tarefa: %s", task[:80])
    results = run_task(task, api_key)
    return results


def cmd_email(task: str) -> None:
    """Executa a tarefa e envia por email."""
    from src.notifications.email_sender import send_email

    results = cmd_run(task)

    send_email(
        task=task,
        results=results,
        smtp_host=_get_env("SMTP_HOST"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_user=_get_env("SMTP_USER"),
        smtp_password=_get_env("SMTP_PASSWORD"),
        email_from=_get_env("EMAIL_FROM"),
        email_to=_get_env("EMAIL_TO"),
    )
    logger.info("Resultado enviado por email.")


def cmd_telegram_send(task: str, results: dict[str, str]) -> None:
    """Envia resultados para o Telegram (chat configurado no .env)."""
    from src.notifications.telegram_bot import send_result_to_chat

    bot_token = _get_env("TELEGRAM_BOT_TOKEN")
    chat_id = _get_env("TELEGRAM_CHAT_ID")

    asyncio.run(send_result_to_chat(bot_token, chat_id, task, results))
    logger.info("Resultado enviado para o Telegram.")


def cmd_telegram_bot() -> None:
    """Inicia o bot do Telegram (modo escuta)."""
    from src.notifications.telegram_bot import create_bot

    bot_token = _get_env("TELEGRAM_BOT_TOKEN")
    api_key = _get_env("ANTHROPIC_API_KEY")

    logger.info("Iniciando bot do Telegram... Envie uma mensagem para ele!")
    app = create_bot(bot_token, api_key)
    app.run_polling()


def cmd_all(task: str) -> None:
    """Executa a tarefa e envia por Telegram + Email."""
    results = cmd_run(task)

    # Imprimir no terminal
    for agent_name, result in results.items():
        print(f"\n{'=' * 50}")
        print(f">> {agent_name}")
        print(f"{'=' * 50}")
        print(result)

    # Enviar por email
    try:
        from src.notifications.email_sender import send_email

        send_email(
            task=task,
            results=results,
            smtp_host=_get_env("SMTP_HOST"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=_get_env("SMTP_USER"),
            smtp_password=_get_env("SMTP_PASSWORD"),
            email_from=_get_env("EMAIL_FROM"),
            email_to=_get_env("EMAIL_TO"),
        )
        logger.info("Email enviado.")
    except Exception as e:
        logger.error("Falha ao enviar email: %s", e)

    # Enviar por Telegram
    try:
        cmd_telegram_send(task, results)
    except Exception as e:
        logger.error("Falha ao enviar no Telegram: %s", e)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Agentes de Marketing - Renova Be",
    )
    parser.add_argument(
        "mode",
        choices=["telegram", "email", "all", "run"],
        help=(
            "telegram: inicia o bot; "
            "email: executa e envia por email; "
            "all: executa e envia por Telegram + Email; "
            "run: executa e imprime no terminal"
        ),
    )
    parser.add_argument(
        "task",
        nargs="?",
        default=None,
        help="Texto da tarefa (obrigatório exceto no modo telegram)",
    )

    args = parser.parse_args()

    if args.mode == "telegram":
        cmd_telegram_bot()
    elif args.mode in ("email", "all", "run") and not args.task:
        parser.error(f"O modo '{args.mode}' requer uma tarefa. Ex: python -m src.main {args.mode} \"sua tarefa aqui\"")
    elif args.mode == "email":
        cmd_email(args.task)
    elif args.mode == "all":
        cmd_all(args.task)
    elif args.mode == "run":
        results = cmd_run(args.task)
        for agent_name, result in results.items():
            print(f"\n{'=' * 50}")
            print(f">> {agent_name}")
            print(f"{'=' * 50}")
            print(result)


if __name__ == "__main__":
    main()
