"""
Gerenciador de Tarefas — coordena a execução completa de uma tarefa.
"""

import logging

from src.agents.registry import AgentRegistry
from src.agents.engine import execute_agent
from src.orchestrator.router import route_task
from src.database.models import (
    create_task,
    update_task_status,
    get_conversation_history,
    save_conversation_message,
    TaskStatus,
)

logger = logging.getLogger(__name__)


async def process_task(
    user_id: int,
    message_id: int | None,
    task_text: str,
    registry: AgentRegistry,
    preferred_agent: str | None = None,
) -> list[dict]:
    """
    Processa uma tarefa completa: roteia, executa e salva resultado.

    Args:
        user_id: ID do usuário no Telegram
        message_id: ID da mensagem no Telegram
        task_text: Texto da tarefa
        registry: Registry de agentes
        preferred_agent: Slug de agente específico (opcional)

    Returns:
        Lista de resultados, um por agente acionado:
        [{"agent_slug": str, "agent_name": str, "task_id": int, "result": str, "error": str|None}]
    """
    # 1. Roteia a tarefa
    routing = await route_task(task_text, registry, preferred_agent)
    results = []

    for agent_slug in routing["agents"]:
        agent = registry.get(agent_slug)
        if not agent:
            continue

        specific_task = routing["task_for_each"].get(agent_slug, task_text)

        # 2. Cria registro no banco
        task_id = create_task(user_id, message_id, agent_slug, specific_task)
        update_task_status(task_id, TaskStatus.IN_PROGRESS)

        try:
            # 3. Carrega histórico de conversa
            history = get_conversation_history(user_id, agent_slug, limit=6)

            # 4. Executa o agente
            result = await execute_agent(agent, specific_task, history)

            # 5. Salva resultado e histórico
            update_task_status(task_id, TaskStatus.COMPLETED, result=result)
            save_conversation_message(user_id, agent_slug, "user", specific_task)
            save_conversation_message(user_id, agent_slug, "assistant", result)

            results.append({
                "agent_slug": agent_slug,
                "agent_name": agent.name,
                "task_id": task_id,
                "result": result,
                "error": None,
            })

        except Exception as e:
            error_msg = str(e)
            update_task_status(task_id, TaskStatus.FAILED, error=error_msg)
            logger.error("Falha ao executar agente '%s': %s", agent_slug, error_msg)

            results.append({
                "agent_slug": agent_slug,
                "agent_name": agent.name,
                "task_id": task_id,
                "result": None,
                "error": error_msg,
            })

    return results
