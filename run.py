"""
Lancement de l'application Sorties Caen.

Usage :
    python run.py                               # démarre sur http://localhost:8000
    python run.py --port 8080                   # port personnalisé
    python run.py --scrape-only                 # scrape toutes les salles et quitte
    python run.py --scrape-only --venue cargo   # scrape une salle précise
    python run.py --scrape-only --demo          # scrape uniquement le scraper démo (données fictives)
"""

import argparse
import os


def main():
    parser = argparse.ArgumentParser(description="Sorties Caen")
    parser.add_argument("--host",        default="127.0.0.1")
    parser.add_argument("--port",        type=int, default=8000)
    parser.add_argument("--reload",      action="store_true", help="Mode développement avec rechargement auto")
    parser.add_argument("--scrape-only", action="store_true", help="Lance le scraping et quitte")
    parser.add_argument("--venue",       default=None, help="Clé de salle à scraper (ex: cargo, zenith…)")
    parser.add_argument("--demo",        action="store_true", help="Active le scraper de démonstration (données fictives)")
    args = parser.parse_args()

    if args.demo:
        os.environ["DEMO_SCRAPER"] = "1"

    if args.scrape_only:
        from app.database import init_db
        from app.scheduler import run_all_scrapers
        init_db()
        venue = args.venue or ("demo" if args.demo else None)
        label = venue or "toutes les salles"
        print(f"Scraping en cours — {label}…")
        run_all_scrapers(venue_key=venue)
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
