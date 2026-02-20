"""
Bot do Telegram — interface principal para interação com os agentes.

Comandos:
    /start          — Mensagem de boas-vindas
    /agentes        — Lista todos os agentes disponíveis
    /tarefa <texto> — Envia tarefa (roteamento automático)
    /para <agente> <texto> — Envia tarefa para agente específico
    /status         — Mostra tarefas ativas
    /historico      — Últimas 10 tarefas
    /limpar <agente> — Limpa histórico de conversa com um agente
    /ajuda          — Mostra comandos disponíveis
"""

import logging

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode, ChatAction

from config.settings import TELEGRAM_BOT_TOKEN, AUTHORIZED_USERS
from src.agents.registry import AgentRegistry
from src.orchestrator.task_manager import process_task
from src.database.models import (
    get_active_tasks,
    get_user_tasks,
    clear_conversation_history,
    init_db,
)

logger = logging.getLogger(__name__)

# Registry global
registry = AgentRegistry()


def is_authorized(user_id: int) -> bool:
    """Verifica se o usuário está autorizado."""
    if not AUTHORIZED_USERS:
        return True  # Se nenhum ID configurado, permite todos
    return user_id in AUTHORIZED_USERS


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Acesso não autorizado.")
        return

    await update.message.reply_text(
        "Olá! Sou o *Orquestrador de Agentes* da Renova Be.\n\n"
        "Tenho *21 agentes especializados* prontos para trabalhar.\n\n"
        "Como usar:\n"
        "• Envie uma mensagem de texto e eu direciono ao agente certo\n"
        "• Use `/para agente-slug sua tarefa` para escolher o agente\n"
        "• Use `/agentes` para ver todos os agentes\n"
        "• Use `/ajuda` para ver todos os comandos\n\n"
        "Exemplo: _\"Crie 5 headlines para campanha de colágeno\"_",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_agentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    agent_list = registry.format_agent_list()
    await update.message.reply_text(
        f"*Agentes Disponíveis (21):*\n{agent_list}\n\n"
        "Use `/para <slug> <tarefa>` para enviar direto.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_tarefa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text(
            "Use: `/tarefa <descrição da tarefa>`\n"
            "Exemplo: `/tarefa Analise o ROAS da campanha de colágeno`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    task_text = " ".join(context.args)
    await _execute_and_reply(update, task_text)


async def cmd_para(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Use: `/para <slug-do-agente> <tarefa>`\n"
            "Exemplo: `/para copywriter-performance Crie 3 headlines para colágeno`\n\n"
            "Use `/agentes` para ver os slugs disponíveis.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    agent_slug = context.args[0]
    task_text = " ".join(context.args[1:])

    agent = registry.get(agent_slug)
    if not agent:
        # Tenta buscar por keyword
        matched = registry.search(agent_slug)
        if matched:
            agent = matched[0]
            agent_slug = agent.slug
        else:
            await update.message.reply_text(
                f"Agente `{agent_slug}` não encontrado.\n"
                "Use `/agentes` para ver os slugs disponíveis.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

    await _execute_and_reply(update, task_text, preferred_agent=agent_slug)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    tasks = get_active_tasks(update.effective_user.id)
    if not tasks:
        await update.message.reply_text("Nenhuma tarefa ativa no momento.")
        return

    lines = ["*Tarefas Ativas:*\n"]
    for t in tasks:
        status_icon = "⏳" if t["status"] == "pending" else "🔄"
        lines.append(
            f"{status_icon} #{t['id']} — `{t['agent_slug']}`\n"
            f"   {t['task_description'][:80]}..."
        )

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


async def cmd_historico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    tasks = get_user_tasks(update.effective_user.id, limit=10)
    if not tasks:
        await update.message.reply_text("Nenhuma tarefa encontrada.")
        return

    status_icons = {
        "completed": "✅",
        "failed": "❌",
        "pending": "⏳",
        "in_progress": "🔄",
        "cancelled": "🚫",
    }

    lines = ["*Últimas 10 Tarefas:*\n"]
    for t in tasks:
        icon = status_icons.get(t["status"], "❓")
        lines.append(
            f"{icon} #{t['id']} — `{t['agent_slug']}`\n"
            f"   {t['task_description'][:60]}..."
        )

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


async def cmd_limpar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    agent_slug = context.args[0] if context.args else None
    clear_conversation_history(update.effective_user.id, agent_slug)

    if agent_slug:
        await update.message.reply_text(
            f"Histórico de conversa com `{agent_slug}` limpo.",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await update.message.reply_text("Histórico de conversa com todos os agentes limpo.")


async def cmd_ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    await update.message.reply_text(
        "*Comandos Disponíveis:*\n\n"
        "💬 *Enviar Tarefas*\n"
        "• Envie texto direto — roteamento automático\n"
        "• `/tarefa <texto>` — mesmo que texto direto\n"
        "• `/para <agente> <texto>` — enviar para agente específico\n\n"
        "📋 *Consultas*\n"
        "• `/agentes` — listar todos os agentes\n"
        "• `/status` — tarefas ativas\n"
        "• `/historico` — últimas 10 tarefas\n\n"
        "🧹 *Manutenção*\n"
        "• `/limpar` — limpar todo histórico\n"
        "• `/limpar <agente>` — limpar histórico de um agente\n\n"
        "💡 *Dicas*\n"
        "• Seja específico na tarefa\n"
        "• Use `/para` quando souber qual agente usar\n"
        "• O sistema mantém contexto de conversa por agente",
        parse_mode=ParseMode.MARKDOWN,
    )


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para mensagens de texto livres — roteamento automático."""
    if not is_authorized(update.effective_user.id):
        return

    task_text = update.message.text
    if not task_text or task_text.startswith("/"):
        return

    await _execute_and_reply(update, task_text)


async def _execute_and_reply(
    update: Update,
    task_text: str,
    preferred_agent: str | None = None,
):
    """Executa tarefa e envia resultado de volta ao Telegram."""
    user_id = update.effective_user.id
    message_id = update.message.message_id

    # Indica que está processando
    await update.message.chat.send_action(ChatAction.TYPING)

    # Mensagem de confirmação
    if preferred_agent:
        agent = registry.get(preferred_agent)
        agent_name = agent.name if agent else preferred_agent
        status_msg = await update.message.reply_text(
            f"🔄 Enviando para *{agent_name}*...",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        status_msg = await update.message.reply_text(
            "🔄 Analisando tarefa e roteando para o agente adequado..."
        )

    try:
        results = await process_task(
            user_id=user_id,
            message_id=message_id,
            task_text=task_text,
            registry=registry,
            preferred_agent=preferred_agent,
        )

        # Deleta mensagem de status
        await status_msg.delete()

        for r in results:
            if r["error"]:
                await update.message.reply_text(
                    f"❌ *{r['agent_name']}* (#{r['task_id']})\n\n"
                    f"Erro: {r['error'][:500]}",
                    parse_mode=ParseMode.MARKDOWN,
                )
            else:
                result_text = r["result"] or ""
                # Telegram tem limite de 4096 chars por mensagem
                header = f"🤖 *{r['agent_name']}* (#{r['task_id']})\n\n"

                if len(header) + len(result_text) <= 4096:
                    await update.message.reply_text(
                        header + result_text,
                        parse_mode=ParseMode.MARKDOWN,
                    )
                else:
                    # Divide em partes
                    await update.message.reply_text(header, parse_mode=ParseMode.MARKDOWN)
                    for i in range(0, len(result_text), 4000):
                        chunk = result_text[i : i + 4000]
                        await update.message.reply_text(chunk)

    except Exception as e:
        logger.error("Erro ao processar tarefa: %s", e)
        await status_msg.edit_text(f"❌ Erro ao processar: {str(e)[:500]}")


def create_bot() -> Application:
    """Cria e configura o bot do Telegram."""
    init_db()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("agentes", cmd_agentes))
    app.add_handler(CommandHandler("tarefa", cmd_tarefa))
    app.add_handler(CommandHandler("para", cmd_para))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("historico", cmd_historico))
    app.add_handler(CommandHandler("limpar", cmd_limpar))
    app.add_handler(CommandHandler("ajuda", cmd_ajuda))

    # Mensagens de texto livres (roteamento automático)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    return app
