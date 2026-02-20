"""Orquestrador que seleciona os agentes relevantes e coordena a execução."""

import anthropic

from src.agents.loader import AgentDefinition, load_agents
from src.agents.executor import execute_agent


def select_agents(
    client: anthropic.Anthropic,
    task: str,
    agents: list[AgentDefinition],
    model: str = "claude-sonnet-4-20250514",
) -> list[AgentDefinition]:
    """Usa o Claude para selecionar quais agentes devem atuar na tarefa."""

    agent_list = "\n".join(
        f"- **{a.slug}**: {a.name} | Área: {a.area} | Nível: {a.level}"
        for a in agents
    )

    prompt = (
        "Você é o roteador de tarefas da equipe de marketing da Renova Be.\n"
        "Sua função é analisar a tarefa abaixo e selecionar os agentes mais "
        "adequados para executá-la.\n\n"
        f"## Tarefa\n{task}\n\n"
        f"## Agentes disponíveis\n{agent_list}\n\n"
        "## Instruções\n"
        "- Selecione de 1 a 5 agentes mais relevantes para esta tarefa.\n"
        "- Responda APENAS com os slugs dos agentes selecionados, um por linha.\n"
        "- Não inclua explicações, apenas os slugs.\n"
        "- Exemplo de resposta:\n"
        "coordenador-performance\n"
        "analista-bi-data\n"
    )

    response = client.messages.create(
        model=model,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )

    selected_slugs = [
        line.strip()
        for line in response.content[0].text.strip().splitlines()
        if line.strip()
    ]

    slug_map = {a.slug: a for a in agents}
    selected = [slug_map[s] for s in selected_slugs if s in slug_map]

    if not selected:
        selected = _fallback_keyword_match(task, agents)

    return selected


def _fallback_keyword_match(
    task: str, agents: list[AgentDefinition]
) -> list[AgentDefinition]:
    """Fallback: seleciona agentes por correspondência de palavras-chave."""
    task_lower = task.lower()
    scored: list[tuple[int, AgentDefinition]] = []

    for agent in agents:
        score = sum(1 for kw in agent.keywords if kw in task_lower)
        if score > 0:
            scored.append((score, agent))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [agent for _, agent in scored[:3]]


def run_task(
    task: str,
    anthropic_api_key: str,
    model: str = "claude-sonnet-4-20250514",
) -> dict[str, str]:
    """Executa a tarefa completa: seleciona agentes, executa cada um, retorna resultados."""
    client = anthropic.Anthropic(api_key=anthropic_api_key)
    agents = load_agents()

    selected = select_agents(client, task, agents, model)

    results: dict[str, str] = {}
    for agent in selected:
        result = execute_agent(client, agent, task, model)
        results[agent.name] = result

    return results
