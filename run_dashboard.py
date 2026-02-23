#!/usr/bin/env python3
"""
Inicializador do Dashboard de Marketing Renova Be.

Uso:
    python run_dashboard.py              # porta 8000 padrão
    python run_dashboard.py --port 8080  # porta personalizada
    python run_dashboard.py --reload     # hot-reload para dev
"""
import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Dashboard de Marketing Renova Be")
    parser.add_argument("--host",   default="0.0.0.0",  help="Host (padrão: 0.0.0.0)")
    parser.add_argument("--port",   default=8000, type=int, help="Porta (padrão: 8000)")
    parser.add_argument("--reload", action="store_true", help="Hot-reload para desenvolvimento")
    args = parser.parse_args()

    print(f"\n{'='*50}")
    print("  Renova Be – Dashboard de Marketing")
    print(f"  http://localhost:{args.port}")
    print(f"{'='*50}\n")

    uvicorn.run(
        "dashboard.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
