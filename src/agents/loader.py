"""Carrega as definições dos agentes a partir dos arquivos Markdown."""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AgentDefinition:
    """Representa um agente carregado do Markdown."""

    slug: str
    name: str
    level: str
    area: str
    content: str
    responsibilities: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)


def _extract_field(content: str, pattern: str) -> str:
    match = re.search(pattern, content)
    return match.group(1).strip() if match else ""


def _extract_responsibilities(content: str) -> list[str]:
    section = re.search(
        r"## Responsabilidades\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL
    )
    if not section:
        return []
    return [
        line.lstrip("- ").strip()
        for line in section.group(1).strip().splitlines()
        if line.strip().startswith("-")
    ]


def _build_keywords(agent: AgentDefinition) -> list[str]:
    """Gera palavras-chave para matching de tarefas com agentes."""
    keywords: list[str] = []

    area_map = {
        "Performance & Growth": [
            "performance", "mídia", "media", "ads", "roas", "cac", "ltv",
            "campanha", "anúncio", "crm", "automação", "bi", "dados",
            "dashboard", "copy", "copywriting", "landing page", "email",
            "whatsapp", "funil", "conversão",
        ],
        "Criação & Branding": [
            "design", "criação", "branding", "visual", "identidade",
            "layout", "figma", "ui", "ux", "shopify", "front-end",
            "frontend", "vídeo", "video", "edição", "reels", "tiktok",
            "youtube", "thumbnail",
        ],
        "Social Media & Conteúdo": [
            "social media", "redes sociais", "instagram", "conteúdo",
            "post", "editorial", "engajamento", "comunidade", "influencer",
            "influenciador", "creator",
        ],
        "Marketplace": [
            "marketplace", "mercado livre", "amazon", "shopee", "magalu",
            "anúncio marketplace", "bling", "estoque", "precificação",
        ],
        "Nutrição & Conteúdo Técnico": [
            "nutrição", "anvisa", "claim", "prescritor", "nutricionista",
            "suplemento", "técnico", "regulatório",
        ],
        "PMO": [
            "projeto", "sprint", "clickup", "gestão", "planejamento",
            "okr", "kpi", "estratégia", "p&l",
        ],
    }

    for area, kws in area_map.items():
        if area.lower() in agent.area.lower():
            keywords.extend(kws)

    keywords.extend(
        word.lower()
        for resp in agent.responsibilities
        for word in resp.split()
        if len(word) > 4
    )

    return list(set(keywords))


def load_agents(agents_dir: str | None = None) -> list[AgentDefinition]:
    """Carrega todos os agentes dos arquivos .md no diretório raiz do projeto."""
    if agents_dir is None:
        agents_dir = str(Path(__file__).resolve().parent.parent.parent)

    agents: list[AgentDefinition] = []

    for filename in sorted(os.listdir(agents_dir)):
        if not filename.endswith(".md"):
            continue

        filepath = os.path.join(agents_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        slug = filename.replace(".md", "")

        name_match = re.search(r"^#\s+Agente:\s*(.+)", content, re.MULTILINE)
        name = name_match.group(1).strip() if name_match else slug

        level = _extract_field(content, r"\*\*Nível:\*\*\s*(.+)")
        area = _extract_field(content, r"\*\*Área:\*\*\s*(.+)")
        responsibilities = _extract_responsibilities(content)

        agent = AgentDefinition(
            slug=slug,
            name=name,
            level=level,
            area=area,
            content=content,
            responsibilities=responsibilities,
        )
        agent.keywords = _build_keywords(agent)
        agents.append(agent)

    return agents
