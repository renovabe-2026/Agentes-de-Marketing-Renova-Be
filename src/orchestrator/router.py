"""
Orquestrador de Tarefas — roteia tarefas para os agentes corretos usando Claude.
"""

import logging
import json
from anthropic import Anthropic

from config.settings import ANTHROPIC_API_KEY, CLAUDE_MODEL, AREAS
from src.agents.registry import AgentRegistry

logger = logging.getLogger(__name__)

client = Anthropic(api_key=ANTHROPIC_API_KEY)

ROUTER_SYSTEM_PROMPT = """Você é o orquestrador de tarefas da Renova Be.
Sua função é analisar uma tarefa em linguagem natural e decidir qual(is) agente(s)
devem executá-la.

Aqui estão os agentes disponíveis e suas áreas:

{agent_catalog}

REGRAS:
1. Analise a tarefa e identifique o(s) agente(s) mais adequado(s)
2. Se a tarefa envolve múltiplas áreas, liste múltiplos agentes
3. Se a tarefa é genérica/estratégica, direcione ao head-marketing-cmo
4. Se a tarefa é sobre gestão/processos, direcione ao gerente-projetos-pmo

Responda APENAS com JSON válido no formato:
{{
    "agents": ["slug-do-agente-1", "slug-do-agente-2"],
    "reasoning": "Explicação curta de por que esses agentes foram escolhidos",
    "task_for_each": {{
        "slug-do-agente-1": "Tarefa específica para este agente",
        "slug-do-agente-2": "Tarefa específica para este agente"
    }}
}}
"""


def _build_agent_catalog(registry: AgentRegistry) -> str:
    """Monta o catálogo de agentes para o prompt do router."""
    lines = []
    for area_key, area in AREAS.items():
        lines.append(f"\n## {area['nome']}")
        for slug in area["agentes"]:
            agent = registry.get(slug)
            if agent:
                lines.append(f"- `{slug}`: {agent.name} ({agent.level}) — Área: {agent.area}")
                # Adiciona keywords para ajudar no roteamento
                keywords = [kw for kw in agent.keywords if kw != slug and kw != agent.name.lower()]
                if keywords:
                    lines.append(f"  Keywords: {', '.join(keywords[:8])}")
    return "\n".join(lines)


async def route_task(
    task: str,
    registry: AgentRegistry,
    preferred_agent: str | None = None,
) -> dict:
    """
    Analisa uma tarefa e determina quais agentes devem executá-la.

    Args:
        task: Descrição da tarefa em linguagem natural
        registry: Registry de agentes carregados
        preferred_agent: Slug de um agente específico (bypass do roteamento)

    Returns:
        Dict com agents, reasoning e task_for_each
    """
    # Se um agente específico foi indicado, pula o roteamento
    if preferred_agent:
        agent = registry.get(preferred_agent)
        if agent:
            return {
                "agents": [preferred_agent],
                "reasoning": f"Agente '{agent.name}' selecionado diretamente pelo usuário.",
                "task_for_each": {preferred_agent: task},
            }

    catalog = _build_agent_catalog(registry)
    system = ROUTER_SYSTEM_PROMPT.format(agent_catalog=catalog)

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": task}],
        )

        raw = response.content[0].text.strip()

        # Tenta extrair JSON mesmo se vier com markdown
        if "```" in raw:
            raw = raw.split("```json")[-1].split("```")[0].strip()
            if not raw:
                raw = response.content[0].text.strip()
                raw = raw.split("```")[-2].strip()

        result = json.loads(raw)

        # Valida que os agentes existem
        valid_agents = [s for s in result.get("agents", []) if registry.get(s)]
        if not valid_agents:
            # Fallback para o PMO
            return {
                "agents": ["gerente-projetos-pmo"],
                "reasoning": "Nenhum agente específico identificado. Direcionando ao PMO.",
                "task_for_each": {"gerente-projetos-pmo": task},
            }

        result["agents"] = valid_agents
        return result

    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.error("Erro no roteamento: %s", e)
        # Fallback: tenta keyword matching
        matched = registry.search(task)
        if matched:
            best = matched[0]
            return {
                "agents": [best.slug],
                "reasoning": f"Roteamento por keywords: {best.name}",
                "task_for_each": {best.slug: task},
            }

        return {
            "agents": ["gerente-projetos-pmo"],
            "reasoning": "Fallback para PMO — roteamento não conseguiu identificar agente.",
            "task_for_each": {"gerente-projetos-pmo": task},
        }
