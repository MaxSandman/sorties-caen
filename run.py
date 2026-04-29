"""
Lancement de l'application Sorties Caen.

Usage :
    python run.py               # démarre sur http://localhost:8000
    python run.py --port 8080   # port personnalisé
    python run.py --scrape-only # lance uniquement le scraping et quitte
"""

import argparse
import asyncio
import sys

def main():
    parser = argparse.ArgumentParser(description="Sorties Caen")
    parser.add_argument("--host",        default="127.0.0.1")
    parser.add_argument("--port",        type=int, default=8000)
    parser.add_argument("--reload",      action="store_true", help="Mode développement avec rechargement auto")
    parser.add_argument("--scrape-only", action="store_true", help="Lance le scraping et quitte")
    args = parser.parse_args()

    if args.scrape_only:
        from app.database import init_db
        from app.scheduler import run_all_scrapers
        init_db()
        print("Scraping en cours…")
        run_all_scrapers()
        print("Scraping terminé.")
        return

    import uvicorn
    print(f"\n  ✓ Sorties Caen  →  http://{args.host}:{args.port}\n")
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )

if __name__ == "__main__":
    main()
