#!/usr/bin/env python3
"""
Renova Be — Agent Runner
=========================
Carrega e executa qualquer agente de marketing via CLI.

Uso:
    python run_agent.py --list                          # Lista todos os agentes
    python run_agent.py --agent copywriter-performance  # Executa agente específico
    python run_agent.py --agent copywriter-performance --export  # Exporta prompt

Requer:
    pip install anthropic
"""

import argparse
import sys
from agents import AGENT_REGISTRY


def list_agents():
    print("\n🤖 Agentes de Marketing — Renova Be")
    print("=" * 60)
    for area, agents in _group_by_area().items():
        print(f"\n📁 {area}")
        for slug, agent in agents:
            print(f"   → {slug:<40} [{agent['level']}]")
    print(f"\nTotal: {len(AGENT_REGISTRY)} agentes\n")


def _group_by_area() -> dict:
    groups = {}
    for slug, agent in AGENT_REGISTRY.items():
        area = agent["area"]
        if area not in groups:
            groups[area] = []
        groups[area].append((slug, agent))
    return groups


def export_prompt(slug: str):
    if slug not in AGENT_REGISTRY:
        print(f"❌ Agente '{slug}' não encontrado. Use --list para ver disponíveis.")
        sys.exit(1)

    agent = AGENT_REGISTRY[slug]
    prompt = agent["build_prompt"]()
    filename = f"prompt_{slug}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(prompt)
    print(f"✅ Prompt exportado para: {filename}")


def run_agent(slug: str, user_message: str = None):
    if slug not in AGENT_REGISTRY:
        print(f"❌ Agente '{slug}' não encontrado. Use --list para ver disponíveis.")
        sys.exit(1)

    try:
        from anthropic import Anthropic
    except ImportError:
        print("❌ SDK Anthropic não instalado. Execute: pip install anthropic")
        sys.exit(1)

    agent = AGENT_REGISTRY[slug]
    system_prompt = agent["build_prompt"]()

    client = Anthropic()

    print(f"\n🤖 Agente: {agent['name']}")
    print(f"📁 Área: {agent['area']}")
    print(f"📊 Nível: {agent['level']}")
    print("=" * 60)

    if user_message:
        # Modo single-shot
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        print(f"\n{response.content[0].text}\n")
    else:
        # Modo interativo
        print("💬 Modo interativo. Digite 'sair' para encerrar.\n")
        messages = []
        while True:
            user_input = input("Você: ").strip()
            if user_input.lower() in ("sair", "exit", "quit"):
                print("\n👋 Até mais!")
                break
            if not user_input:
                continue

            messages.append({"role": "user", "content": user_input})

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=system_prompt,
                messages=messages,
            )

            assistant_text = response.content[0].text
            messages.append({"role": "assistant", "content": assistant_text})
            print(f"\n🤖: {assistant_text}\n")


def main():
    parser = argparse.ArgumentParser(
        description="🤖 Renova Be — Agent Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python run_agent.py --list
  python run_agent.py --agent copywriter-performance
  python run_agent.py --agent copywriter-performance --message "Escreva 3 headlines para Colágeno"
  python run_agent.py --agent coordenador-performance --export
        """,
    )
    parser.add_argument("--list", action="store_true", help="Lista todos os agentes disponíveis")
    parser.add_argument("--agent", type=str, help="Slug do agente para executar")
    parser.add_argument("--message", type=str, help="Mensagem única (modo single-shot)")
    parser.add_argument("--export", action="store_true", help="Exporta system prompt do agente")

    args = parser.parse_args()

    if args.list:
        list_agents()
    elif args.agent and args.export:
        export_prompt(args.agent)
    elif args.agent:
        run_agent(args.agent, args.message)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
