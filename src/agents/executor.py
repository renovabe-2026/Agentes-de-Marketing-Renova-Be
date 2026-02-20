"""Executa um agente (via Claude API) para realizar uma tarefa específica."""

import anthropic

from .loader import AgentDefinition


def execute_agent(
    client: anthropic.Anthropic,
    agent: AgentDefinition,
    task: str,
    model: str = "claude-sonnet-4-20250514",
) -> str:
    """Executa o agente com a tarefa fornecida e retorna a resposta."""

    system_prompt = (
        f"{agent.content}\n\n"
        "---\n\n"
        "INSTRUÇÕES ADICIONAIS:\n"
        "- Você é este agente e deve responder estritamente dentro do seu escopo.\n"
        "- Responda em português brasileiro.\n"
        "- Seja objetivo e entregue resultados acionáveis.\n"
        "- Estruture sua resposta com seções claras.\n"
        "- Se a tarefa estiver fora do seu escopo, diga isso claramente.\n"
    )

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": task}],
    )

    return response.content[0].text
