from __future__ import annotations
"""
Scraper de démonstration — renvoie des données fictives sans aucun accès réseau.
Utile pour tester l'interface, le pipeline d'upsert et les notifications ntfy.

Activé uniquement si la variable d'environnement DEMO_SCRAPER=1 est définie.
"""

import os
from datetime import datetime, timedelta

from .base import BaseScraper, RawEvent

_ENABLED = os.getenv("DEMO_SCRAPER", "0") == "1"

_FAKE_EVENTS = [
    {
        "title": "Concert Jazz Fictif",
        "artist": "The Demo Quartet",
        "category": "Jazz",
        "days_from_now": 3,
    },
    {
        "title": "Soirée Électro Demo",
        "artist": "DJ Placeholder",
        "category": "Électronique",
        "days_from_now": 7,
    },
    {
        "title": "Théâtre — Pièce Test",
        "artist": None,
        "category": "Théâtre",
        "days_from_now": 14,
    },
]


class DemoScraper(BaseScraper):
    venue_name = "Salle Démo"
    venue_key = "demo" if _ENABLED else ""   # empty key = non enregistré si inactif
    base_url = "http://localhost:8000"
    use_playwright = False

    async def _scrape(self) -> list[RawEvent]:
        now = datetime.now()
        events = []
        for i, e in enumerate(_FAKE_EVENTS):
            date = (now + timedelta(days=e["days_from_now"])).replace(
                hour=20, minute=30, second=0, microsecond=0
            )
            events.append(
                RawEvent(
                    title=e["title"],
                    artist=e["artist"],
                    venue=self.venue_name,
                    venue_key=self.venue_key,
                    date=date,
                    time="20h30",
                    description="Événement de démonstration généré automatiquement.",
                    image_url=None,
                    booking_url="http://localhost:8000",
                    category=e["category"],
                    external_id=self._make_external_id("demo", i),
                )
            )
        return events
