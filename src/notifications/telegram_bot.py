"""Bot do Telegram para receber tarefas e enviar resultados."""

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from src.orchestrator.task_router import run_task

logger = logging.getLogger(__name__)

# Tamanho máximo de mensagem do Telegram
MAX_MESSAGE_LENGTH = 4096


def _split_message(text: str) -> list[str]:
    """Divide mensagens longas respeitando o limite do Telegram."""
    if len(text) <= MAX_MESSAGE_LENGTH:
        return [text]

    parts: list[str] = []
    while text:
        if len(text) <= MAX_MESSAGE_LENGTH:
            parts.append(text)
            break
        split_at = text.rfind("\n", 0, MAX_MESSAGE_LENGTH)
        if split_at == -1:
            split_at = MAX_MESSAGE_LENGTH
        parts.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return parts


def _format_results(task: str, results: dict[str, str]) -> str:
    """Formata os resultados dos agentes para envio."""
    header = f"📋 *Tarefa:* {task}\n\n"
    body = ""
    for agent_name, result in results.items():
        body += f"🤖 *{agent_name}*\n\n{result}\n\n{'─' * 30}\n\n"
    return header + body


async def _handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Olá! Sou o bot da equipe de marketing da Renova Be.\n\n"
        "Envie uma tarefa em texto e eu vou acionar os agentes certos "
        "para executá-la. Você receberá o resultado aqui mesmo.\n\n"
        "Exemplo: \"Crie 3 copies para um anúncio de whey protein no Instagram\""
    )


async def _handle_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    task_text = update.message.text
    api_key = context.bot_data.get("anthropic_api_key", "")

    if not api_key:
        await update.message.reply_text(
            "Erro: ANTHROPIC_API_KEY não configurada."
        )
        return

    await update.message.reply_text(
        "⏳ Analisando tarefa e acionando agentes... Aguarde."
    )

    try:
        results = run_task(task_text, api_key)
        formatted = _format_results(task_text, results)

        for part in _split_message(formatted):
            await update.message.reply_text(part, parse_mode="Markdown")

    except Exception as e:
        logger.exception("Erro ao executar tarefa")
        await update.message.reply_text(f"Erro ao processar tarefa: {e}")


async def send_result_to_chat(
    bot_token: str,
    chat_id: str | int,
    task: str,
    results: dict[str, str],
) -> None:
    """Envia resultados para um chat específico (uso programático)."""
    from telegram import Bot

    bot = Bot(token=bot_token)
    formatted = _format_results(task, results)

    for part in _split_message(formatted):
        await bot.send_message(
            chat_id=chat_id, text=part, parse_mode="Markdown"
        )


def create_bot(bot_token: str, anthropic_api_key: str) -> Application:
    """Cria e configura o bot do Telegram."""
    app = Application.builder().token(bot_token).build()
    app.bot_data["anthropic_api_key"] = anthropic_api_key

    app.add_handler(CommandHandler("start", _handle_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _handle_task))

    return app
