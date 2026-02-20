# 🤖 Agentes de Marketing — Renova Be (Código Python)

Sistema de agentes de IA executáveis via SDK Anthropic, baseados no organograma de marketing da Renova Be.

**19 agentes** | **6 áreas** | **Operação R$250M/ano**

---

## 🚀 Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sua-chave-aqui"
```

---

## 📋 Uso

### Listar todos os agentes
```bash
python run_agent.py --list
```

### Executar agente (modo interativo)
```bash
python run_agent.py --agent copywriter-performance
```

### Executar agente (mensagem única)
```bash
python run_agent.py --agent copywriter-performance --message "Escreva 3 headlines para Colágeno Verisol"
```

### Exportar system prompt de um agente
```bash
python run_agent.py --agent coordenador-performance --export
```

---

## 📁 Estrutura

```
agentes-code/
├── run_agent.py          # CLI runner principal
├── agents.py             # Registro dos 19 agentes (prompts + metadata)
├── brand_context.py      # Contexto de marca compartilhado (tom de voz, pilares, etc.)
├── requirements.txt
└── README.md
```

---

## 🤖 Agentes Disponíveis

| Slug | Nome | Área | Nível |
|------|------|------|-------|
| `coordenador-performance` | Coordenador(a) de Performance | Performance & Growth | Coordenação |
| `gestor-midia-paga` | Gestor(a) de Mídia Paga | Performance & Growth | Sênior |
| `analista-midia-paga` | Analista de Mídia Paga | Performance & Growth | Pleno |
| `copywriter-performance` | Copywriter de Performance | Performance & Growth | Pleno |
| `analista-crm-automacao` | Analista de CRM & Automação | Performance & Growth | Pleno |
| `analista-bi-data` | Analista de BI & Data | Performance & Growth | Pleno |
| `designer-grafico-senior` | Designer Gráfico Sênior | Criação & Branding | Sênior |
| `designer-grafico` | Designer Gráfico | Criação & Branding | Pleno |
| `designer-uiux-ecommerce` | Designer UI/UX E-commerce | Criação & Branding | Sênior |
| `editor-video-senior` | Editor(a) de Vídeo Sênior | Criação & Branding | Sênior |
| `desenvolvedor-frontend` | Desenvolvedor(a) Front-End | Criação & Branding | Pleno |
| `analista-social-media` | Analista de Social Media | Social Media & Conteúdo | Pleno |
| `analista-influencer-marketing` | Analista de Influencer Marketing | Social Media & Conteúdo | Pleno |
| `copywriter-conteudo-community` | Copywriter de Conteúdo | Social Media & Conteúdo | Pleno |
| `analista-marketplace-senior` | Analista de Marketplace Sr. | Marketplace | Sênior |
| `assistente-marketplace` | Assistente de Marketplace | Marketplace | Júnior |
| `coordenador-nutricao` | Coordenador(a) de Nutrição | Nutrição & Conteúdo Técnico | Coordenação |
| `nutricionista-conteudo` | Nutricionista de Conteúdo | Nutrição & Conteúdo Técnico | Pleno |
| `analista-prescritores` | Analista de Prescritores | Nutrição & Conteúdo Técnico | Pleno |
| `gerente-projetos-pmo` | Gerente de Projetos (PMO) | PMO | Sênior |
| `head-marketing-cmo` | Head de Marketing / CMO | PMO | C-Level |

---

## 🧬 Arquitetura

- **`brand_context.py`** — Módulo central com toda a identidade da marca (Brand Pulse, tom de voz, manifesto, regulamentação). Compartilhado por todos os agentes para garantir consistência.

- **`agents.py`** — Define cada agente com identidade, DO'S, DON'TS e instruções. A função `build_system_prompt()` combina o contexto do cargo com o contexto da marca.

- **`run_agent.py`** — CLI para listar, executar (interativo ou single-shot) e exportar prompts dos agentes.

### Agentes com Tom de Voz completo
Os agentes de **copy e conteúdo** recebem o guia completo de tom de voz (diretrizes 1 e 2, palavras-chave, manifesto, checklist):
- `copywriter-performance`
- `analista-social-media`
- `copywriter-conteudo-community`
- `nutricionista-conteudo`

---

## 📄 Licença

Uso interno Renova Be / Vitabe Group.
