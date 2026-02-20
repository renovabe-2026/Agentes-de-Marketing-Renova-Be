"""
Motor de Execução dos Agentes — faz a chamada ao Claude com o system prompt do agente.
"""

import logging
from anthropic import Anthropic

from config.settings import ANTHROPIC_API_KEY, CLAUDE_MODEL, CLAUDE_MAX_TOKENS
from src.agents.registry import AgentProfile

logger = logging.getLogger(__name__)

client = Anthropic(api_key=ANTHROPIC_API_KEY)


async def execute_agent(
    agent: AgentProfile,
    task: str,
    conversation_history: list[dict] | None = None,
) -> str:
    """
    Executa um agente com uma tarefa específica.

    Args:
        agent: Perfil do agente a ser executado
        task: Descrição da tarefa em linguagem natural
        conversation_history: Histórico de mensagens anteriores (opcional)

    Returns:
        Resposta do agente como string
    """
    messages = []

    # Adiciona histórico se existir
    if conversation_history:
        messages.extend(conversation_history)

    # Adiciona a tarefa atual
    messages.append({"role": "user", "content": task})

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            system=agent.system_prompt,
            messages=messages,
        )

        result = response.content[0].text
        logger.info(
            "Agente '%s' executou tarefa. Tokens: input=%d, output=%d",
            agent.slug,
            response.usage.input_tokens,
            response.usage.output_tokens,
        )
        return result

    except Exception as e:
        logger.error("Erro ao executar agente '%s': %s", agent.slug, e)
        raise
