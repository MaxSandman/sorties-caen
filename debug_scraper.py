"""
Script de debug pour tester et ajuster les scrapers.

Usage :
    python debug_scraper.py                    # teste tous les scrapers
    python debug_scraper.py --venue cargo      # teste seulement Le Cargö
    python debug_scraper.py --html cargo       # affiche le HTML brut (pour ajuster les sélecteurs)

Clés de salles disponibles :
    theatre_ouest, zenith, cargo, bbc, palais_sports, caen_evenements
"""

import asyncio
import argparse
import sys
from app.scrapers import ALL_SCRAPERS


async def test_scraper(scraper_class, show_html=False):
    scraper = scraper_class()
    print(f"\n{'='*60}")
    print(f"  {scraper.venue_name}  ({scraper.venue_key})")
    print(f"{'='*60}")

    if show_html:
        url = getattr(scraper, 'list_url', scraper.base_url)
        print(f"  URL: {url}")
        html = await scraper._get_page(url)
        # Print first 3000 chars of body
        start = html.find('<body')
        print(html[start:start+3000] if start >= 0 else html[:3000])
        return

    events = await scraper._scrape()
    if not events:
        print("  ⚠  Aucun événement trouvé — les sélecteurs CSS sont probablement à ajuster.")
        print(f"     → Relancez avec: python debug_scraper.py --html {scraper.venue_key}")
    else:
        print(f"  ✓  {len(events)} événements trouvés\n")
        for ev in events[:5]:
            print(f"  • {ev.date.strftime('%d/%m/%Y')} | {ev.title}")
            print(f"    Résa: {ev.booking_url}")
        if len(events) > 5:
            print(f"  … et {len(events) - 5} autres")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--venue', help='Clé de salle à tester')
    parser.add_argument('--html',  help='Affiche le HTML brut pour une salle')
    args = parser.parse_args()

    scrapers = ALL_SCRAPERS
    if args.venue or args.html:
        key = args.venue or args.html
        scrapers = [s for s in ALL_SCRAPERS if s.venue_key == key]
        if not scrapers:
            print(f"Salle inconnue: {key}")
            print("Clés valides:", ', '.join(s.venue_key for s in ALL_SCRAPERS))
            sys.exit(1)

    for cls in scrapers:
        await test_scraper(cls, show_html=bool(args.html))

asyncio.run(main())
