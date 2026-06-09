"""
Théâtre à l'Ouest — API JSON https://api.theatrealouest.com
Endpoint: GET /shows/areas/{AREA_ID}?slots:to[min]=DATE&sort=slots:from|ASC&enabled=true&page=N
Auth: POST /login {username, password} -> {token}
"""

import os
import re as _re
import logging
import httpx
from datetime import datetime, date
from .base import BaseScraper, RawEvent

logger = logging.getLogger(__name__)

CAEN_AREA_ID = "5e4e0cb9-ac24-40a9-8a79-216ec1b0b3f4"
API_BASE = "https://api.theatrealouest.com"
SITE_BASE = "https://theatrealouest.com"

# Generic placeholder titles to discard
_GENERIC_TITLES = {"nouveau spectacle", "coming soon", "à venir", "spectacle à venir"}

_MONTHS_FR = {
    "janvier": 1, "février": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12,
}


def _parse_french_date(text: str) -> datetime | None:
    text = text.strip().lower()
    m = _re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", text)
    if m:
        day, month_str, year = int(m.group(1)), m.group(2), int(m.group(3))
        month = _MONTHS_FR.get(month_str)
        if month:
            return datetime(year, month, day)
    try:
        return datetime.fromisoformat(text[:10])
    except Exception:
        return None


def _clean_title(title: str) -> str:
    """Strip extra whitespace and stray guillemets spacing."""
    title = _re.sub(r"\s{2,}", " ", title).strip()
    return title


class TheatreOuestScraper(BaseScraper):
    venue_name = "Théâtre à l'Ouest"
    venue_key = "theatre_ouest"

    async def _scrape(self) -> list[RawEvent]:
        email = os.getenv("THEATRE_OUEST_EMAIL", "")
        password = os.getenv("THEATRE_OUEST_PASSWORD", "")
        if not email or not password:
            logger.warning("THEATRE_OUEST_EMAIL/PASSWORD not set, skipping")
            return []

        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        async with httpx.AsyncClient(headers=headers, timeout=30) as client:
            resp = await client.post(f"{API_BASE}/login",
                                     json={"username": email, "password": password})
            resp.raise_for_status()
            token = resp.json()["token"]
            client.headers["Authorization"] = f"Bearer {token}"

            today = date.today().isoformat() + "T00:00:00"
            events: list[RawEvent] = []
            page = 1
            total_pages = 1

            while page <= total_pages:
                params = {
                    "slots:to[min]": today,
                    "sort": "slots:from|ASC",
                    "enabled": "true",
                    "page": str(page),
                }
                resp = await client.get(
                    f"{API_BASE}/shows/areas/{CAEN_AREA_ID}",
                    params=params,
                )
                if resp.status_code >= 500:
                    logger.warning("API returned %s on page %d, stopping pagination", resp.status_code, page)
                    break
                resp.raise_for_status()
                data = resp.json()

                pagination = data.get("pagination", {})
                total_pages = pagination.get("totalPages", 1)
                members = data.get("members", [])

                for show in members:
                    show_events = self._parse_show(show)
                    events.extend(show_events)

                page += 1

        return events

    def _parse_show(self, show: dict) -> list[RawEvent]:
        title = _clean_title(show.get("title", ""))
        if not title or title.lower() in _GENERIC_TITLES:
            return []

        show_id = show.get("id", "")
        slug = show.get("slug", "")

        # Artist / company name (separate from title in the API)
        artists_raw = show.get("artists", "") or ""
        artist = artists_raw.strip() or None

        # Event page URL
        event_url = f"{SITE_BASE}/caen/spectacle/{slug}" if slug else None

        # Booking URL: Angular router uses /reserver-places/{slug} for ticketing.
        booking_url = f"{SITE_BASE}/caen/spectacle/reserver-places/{slug}" if slug else event_url

        media = show.get("media")
        if isinstance(media, dict):
            image_url = media.get("url") or media.get("src") or media.get("path") or None
        elif isinstance(media, str) and media.startswith("http"):
            image_url = media
        elif isinstance(media, str) and media:
            image_url = f"{API_BASE}/{media.lstrip('/')}"
        else:
            image_url = None

        category = (
            show.get("category", {}).get("name", "Spectacle")
            if show.get("category")
            else "Spectacle"
        )

        slots = show.get("slots")
        if not slots or not isinstance(slots, dict):
            return []

        slot_from = slots.get("from")
        if not slot_from:
            return []

        try:
            dt = datetime.strptime(slot_from, "%Y-%m-%d %H:%M:%S")
            event_date = datetime(dt.year, dt.month, dt.day)
            time_str = dt.strftime("%Hh%M") if (dt.hour or dt.minute) else None
        except Exception:
            return []

        return [RawEvent(
            title=title,
            artist=artist,
            venue=self.venue_name,
            venue_key=self.venue_key,
            date=event_date,
            time=time_str,
            event_url=event_url,
            booking_url=booking_url,
            image_url=image_url,
            category=category,
            external_id=self._make_external_id(show_id or title, event_date.date()),
        )]
