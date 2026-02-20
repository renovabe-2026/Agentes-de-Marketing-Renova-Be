"""
Registry de agentes — carrega os .md e mantém o catálogo disponível.
"""

from dataclasses import dataclass, field
from pathlib import Path

from config.settings import AGENTS_DIR, AGENT_FILES, AREAS


@dataclass
class AgentProfile:
    slug: str
    name: str
    level: str
    area: str
    system_prompt: str
    raw_markdown: str
    keywords: list[str] = field(default_factory=list)


def _extract_name(markdown: str) -> str:
    """Extrai o nome do agente da primeira linha do markdown."""
    first_line = markdown.strip().split("\n")[0]
    # Remove "# Agente: " prefix e " — Renova Be" suffix
    name = first_line.replace("# Agente: ", "").replace("# ", "")
    name = name.split(" — ")[0].strip()
    return name


def _extract_field(markdown: str, field_name: str) -> str:
    """Extrai um campo como **Nível:** ou **Área:** do markdown."""
    for line in markdown.split("\n"):
        if f"**{field_name}:**" in line:
            return line.split(f"**{field_name}:**")[-1].strip()
    return ""


def _build_system_prompt(markdown: str, slug: str) -> str:
    """Transforma o markdown do agente em um system prompt para Claude."""
    return (
        f"Você é um agente de IA da Renova Be. Sua identidade e instruções completas "
        f"estão descritas abaixo. Siga rigorosamente suas responsabilidades, DO'S e "
        f"DON'TS. Responda sempre em português brasileiro.\n\n"
        f"Ao receber uma tarefa:\n"
        f"1. Analise o que está sendo pedido\n"
        f"2. Execute de acordo com suas instruções de operação\n"
        f"3. Seja específico e acionável nas respostas\n"
        f"4. Se precisar de informações adicionais, pergunte\n"
        f"5. Mantenha o tom de voz da marca Renova Be\n\n"
        f"---\n\n"
        f"{markdown}"
    )


def _build_keywords(slug: str, name: str, area: str) -> list[str]:
    """Gera keywords para facilitar o roteamento de tarefas."""
    keyword_map = {
        "head-marketing-cmo": ["estratégia", "budget", "p&l", "cmo", "head", "liderança", "meta anual"],
        "gerente-projetos-pmo": ["projeto", "sprint", "clickup", "prazo", "cronograma", "pmo", "automação", "make"],
        "coordenador-performance": ["performance", "roas", "cac", "ltv", "mídia", "aquisição", "retenção"],
        "gestor-midia-paga": ["mídia paga", "meta ads", "google ads", "tiktok ads", "campanha", "orçamento", "media buyer"],
        "analista-midia-paga": ["anúncio", "criativo", "bid", "cpa", "ctr", "pixel", "upload"],
        "copywriter-performance": ["copy", "headline", "landing page", "anúncio texto", "aida", "pas", "cta"],
        "analista-bi-data": ["bi", "dashboard", "dados", "relatório", "cohort", "analytics", "métricas"],
        "analista-crm-automacao": ["crm", "email", "whatsapp", "automação", "fluxo", "segmentação", "nextags"],
        "designer-grafico-senior": ["design", "key visual", "identidade visual", "packaging", "banner", "mockup"],
        "designer-grafico": ["design", "peça", "social media", "stories", "youtube thumbnail", "adaptação"],
        "designer-uiux-ecommerce": ["ui", "ux", "ecommerce", "shopify", "figma", "landing page design", "pdp"],
        "editor-video-senior": ["vídeo", "reels", "tiktok", "youtube", "edição", "corte", "legenda", "hook"],
        "desenvolvedor-frontend": ["frontend", "shopify", "liquid", "html", "css", "javascript", "core web vitals"],
        "analista-social-media": ["social media", "instagram", "post", "stories", "engajamento", "calendário editorial"],
        "copywriter-conteudo-community": ["conteúdo", "comunidade", "texto social", "editorial", "tom de voz", "série"],
        "analista-influencer-marketing": ["influencer", "creator", "parceria", "cpe", "collab", "embaixador"],
        "analista-marketplace-senior": ["marketplace", "mercado livre", "amazon", "shopee", "magalu", "fba", "pricing"],
        "assistente-marketplace": ["kit", "combo", "bling", "listagem", "preço", "estoque", "operação marketplace"],
        "coordenador-nutricao": ["nutrição", "anvisa", "claim", "cartilha", "prescritor", "conteúdo técnico"],
        "nutricionista-conteudo": ["colágeno", "creatina", "omega", "suplemento", "cartilha", "nutricional"],
        "analista-prescritores": ["prescritor", "programa", "gmv", "portal", "win-back", "nutricionista parceiro"],
    }
    base = [slug, name.lower(), area.lower()]
    return base + keyword_map.get(slug, [])


class AgentRegistry:
    """Carrega e gerencia todos os 21 agentes."""

    def __init__(self):
        self._agents: dict[str, AgentProfile] = {}
        self._load_all()

    def _load_all(self):
        for slug, filename in AGENT_FILES.items():
            filepath = AGENTS_DIR / filename
            if not filepath.exists():
                continue

            markdown = filepath.read_text(encoding="utf-8")
            name = _extract_name(markdown)
            level = _extract_field(markdown, "Nível")
            area = _extract_field(markdown, "Área")

            self._agents[slug] = AgentProfile(
                slug=slug,
                name=name,
                level=level,
                area=area,
                system_prompt=_build_system_prompt(markdown, slug),
                raw_markdown=markdown,
                keywords=_build_keywords(slug, name, area),
            )

    def get(self, slug: str) -> AgentProfile | None:
        return self._agents.get(slug)

    def list_all(self) -> list[AgentProfile]:
        return list(self._agents.values())

    def search(self, query: str) -> list[AgentProfile]:
        """Busca agentes por keywords relevantes à query."""
        query_lower = query.lower()
        scored = []
        for agent in self._agents.values():
            score = sum(1 for kw in agent.keywords if kw in query_lower)
            if score > 0:
                scored.append((score, agent))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [agent for _, agent in scored]

    def list_by_area(self, area_key: str) -> list[AgentProfile]:
        """Lista agentes de uma área específica."""
        area = AREAS.get(area_key)
        if not area:
            return []
        return [
            self._agents[slug]
            for slug in area["agentes"]
            if slug in self._agents
        ]

    def get_area_for_agent(self, slug: str) -> str | None:
        """Retorna a chave da área de um agente."""
        for area_key, area in AREAS.items():
            if slug in area["agentes"]:
                return area_key
        return None

    def format_agent_list(self) -> str:
        """Formata a lista de agentes para exibição."""
        lines = []
        for area_key, area in AREAS.items():
            lines.append(f"\n📁 *{area['nome']}*")
            for slug in area["agentes"]:
                agent = self._agents.get(slug)
                if agent:
                    lines.append(f"  • `{slug}` — {agent.name} ({agent.level})")
        return "\n".join(lines)
