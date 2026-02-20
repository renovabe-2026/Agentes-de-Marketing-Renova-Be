"""
Configurações centrais do sistema de agentes Renova Be.
"""

import os
from pathlib import Path

# Diretórios
BASE_DIR = Path(__file__).resolve().parent.parent
AGENTS_DIR = BASE_DIR  # Os .md ficam na raiz do repo
DATABASE_DIR = BASE_DIR / "data"
DATABASE_DIR.mkdir(exist_ok=True)

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# IDs de usuários autorizados no Telegram (separados por vírgula)
# Ex: "123456789,987654321"
AUTHORIZED_USERS = [
    int(uid.strip())
    for uid in os.getenv("AUTHORIZED_USERS", "").split(",")
    if uid.strip().isdigit()
]

# Claude
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
CLAUDE_MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "4096"))

# Database
DATABASE_PATH = DATABASE_DIR / "agentes.db"

# Mapeamento dos arquivos .md para slugs de agentes
AGENT_FILES = {
    "head-marketing-cmo": "head-marketing-cmo.md",
    "gerente-projetos-pmo": "gerente-projetos-pmo.md",
    "coordenador-performance": "coordenador-performance.md",
    "gestor-midia-paga": "gestor-midia-paga.md",
    "analista-midia-paga": "analista-midia-paga.md",
    "copywriter-performance": "copywriter-performance.md",
    "analista-bi-data": "analista-bi-data.md",
    "analista-crm-automacao": "analista-crm-automacao.md",
    "designer-grafico-senior": "designer-grafico-senior.md",
    "designer-grafico": "designer-grafico.md",
    "designer-uiux-ecommerce": "designer-uiux-ecommerce.md",
    "editor-video-senior": "editor-video-senior.md",
    "desenvolvedor-frontend": "desenvolvedor-frontend.md",
    "analista-social-media": "analista-social-media.md",
    "copywriter-conteudo-community": "copywriter-conteudo-community.md",
    "analista-influencer-marketing": "analista-influencer-marketing.md",
    "analista-marketplace-senior": "analista-marketplace-senior.md",
    "assistente-marketplace": "assistente-marketplace.md",
    "coordenador-nutricao": "coordenador-nutricao.md",
    "nutricionista-conteudo": "nutricionista-conteudo.md",
    "analista-prescritores": "analista-prescritores.md",
}

# Áreas funcionais para agrupamento
AREAS = {
    "performance": {
        "nome": "Performance & Growth",
        "agentes": [
            "coordenador-performance",
            "gestor-midia-paga",
            "analista-midia-paga",
            "copywriter-performance",
            "analista-bi-data",
            "analista-crm-automacao",
        ],
    },
    "criacao": {
        "nome": "Criação & Branding",
        "agentes": [
            "designer-grafico-senior",
            "designer-grafico",
            "designer-uiux-ecommerce",
            "editor-video-senior",
            "desenvolvedor-frontend",
        ],
    },
    "social": {
        "nome": "Social Media & Conteúdo",
        "agentes": [
            "analista-social-media",
            "copywriter-conteudo-community",
            "analista-influencer-marketing",
        ],
    },
    "marketplace": {
        "nome": "Marketplace",
        "agentes": [
            "analista-marketplace-senior",
            "assistente-marketplace",
        ],
    },
    "nutricao": {
        "nome": "Nutrição & Conteúdo Técnico",
        "agentes": [
            "coordenador-nutricao",
            "nutricionista-conteudo",
            "analista-prescritores",
        ],
    },
    "pmo": {
        "nome": "PMO & Liderança",
        "agentes": [
            "gerente-projetos-pmo",
            "head-marketing-cmo",
        ],
    },
}
