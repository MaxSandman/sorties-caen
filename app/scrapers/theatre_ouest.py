"""
Scraper for Théâtre à l'Ouest (Caen) — JSON API
https://api.theatrealouest.com/shows/areas/{AREA_ID}
"""
from __future__ import annotations

import logging
from datetime import datetime, date

import requests

from .base import BaseScraper, RawEvent

logger = logging.getLogger(__name__)

_AREA_ID  = "5e4e0cb9-ac24-40a9-8a79-216ec1b0b3f4"
_API_BASE = f"https://api.theatrealouest.com/shows/areas/{_AREA_ID}"
_SHOW_BASE = "https://theatrealouest.com/caen/spectacle/reserver-places"

_CAT_MAP = {
    "stand up": "humour", "humour": "humour", "comédie": "humour",
    "comedie": "humour", "cabaret": "humour",
    "plateau d'humoristes": "humour", "spectacle pour enfants": "enfants",
    "magie": "humour", "improvisation": "humour",
}


import re

MONTHS_FR = {
    "janvier": 1, "février": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12,
}


def _parse_french_date(text: str) -> datetime | None:
    text = text.strip().lower()
    m = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", text)
    if m:
        day, month_str, year = int(m.group(1)), m.group(2), int(m.group(3))
        month = MONTHS_FR.get(month_str)
        if month:
            return datetime(year, month, day)
    try:
        return datetime.fromisoformat(text[:10])
    except Exception:
        return None


def _map_cat(raw: str) -> str:
    return _CAT_MAP.get(raw.lower().strip(), "spectacle")


def _parse_dt(s: str) -> datetime | None:
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except (ValueError, TypeError):
            continue
    return None


class TheatreOuestScraper(BaseScraper):
    venue_name     = "Théâtre à l'Ouest"
    venue_key      = "theatre_ouest"
    base_url       = "https://theatrealouest.com"
    list_url       = _API_BASE
    use_playwright = False

    async def _scrape(self) -> list[RawEvent]:
        today = date.today().isoformat()
        events: list[RawEvent] = []
        page = 1
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; SortiesCaen/1.0)",
            "Accept": "application/json",
            "Origin": "https://theatrealouest.com",
            "Referer": "https://theatrealouest.com/",
        }

        while True:
            params = {
                "slots:to[min]": f"{today}T00:00:00",
                "sort": "slots:from|ASC",
                "enabled": "true",
                "page": page,
            }
            try:
                resp = requests.get(_API_BASE, params=params, headers=headers, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:
                logger.error(f"[theatre_ouest] API error page {page}: {exc}")
                break

            members = data.get("members", [])
            pagination = data.get("pagination", {})

            for show in members:
                if not show.get("enabled"):
                    continue

                title = (show.get("title") or "").strip()
                if not title:
                    continue

                # Each show may have multiple slots; emit one event per slot
                slots = show.get("slots") or []
                if isinstance(slots, dict):
                    slots = [slots]
                if not slots:
                    continue

                cat_raw = (show.get("category") or {}).get("name", "")
                slug = show.get("slug", "")
                event_url = f"{_SHOW_BASE}/{slug}" if slug else None

                # Best-effort image extraction
                image_url = None
                media = show.get("media")
                if isinstance(media, str) and media.startswith("http"):
                    image_url = media
                elif isinstance(media, dict):
                    image_url = media.get("url") or media.get("contentUrl")
                if not image_url:
                    refs = show.get("mediaRefs") or []
                    if refs and isinstance(refs[0], dict):
                        m = refs[0].get("media") or {}
                        image_url = m.get("url") or m.get("contentUrl") if isinstance(m, dict) else None

                for slot in slots:
                    if isinstance(slot, dict):
                        slot_from = slot.get("from", "")
                    else:
                        slot_from = str(slot)
                    dt = _parse_dt(slot_from)
                    if not dt:
                        continue

                    events.append(RawEvent(
                        title=title,
                        artist=None,
                        venue=self.venue_name,
                        venue_key=self.venue_key,
                        date=dt,
                        time=dt.strftime("%H:%M"),
                        description=(show.get("description") or "").strip() or None,
                        image_url=image_url,
                        event_url=event_url,
                        booking_url=event_url,
                        category=_map_cat(cat_raw),
                        external_id=show.get("id"),
                    ))

            total_pages = pagination.get("totalPages", 1)
            if page >= total_pages:
                break
            page += 1

        return events
