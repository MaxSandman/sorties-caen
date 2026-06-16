"""
Scraper for Zénith de Caen — https://zenith-caen.fr

HTML structure (observed):
  section#home-spectacles > div.home-spectacles-content > div.accordeon-bloc
    h3 (month label)
    div.accordeon-content > ul.spectacles-list > li.spectacle-item-wrapper
      div.spectacle-item
        div.figure > figure > img
        div.links.desktop-only
        div.spectacle-infos
          h4          — artiste
          h5          — sous-titre / titre secondaire
          p.date > time[datetime]  — "Vendredi 19 Juin 2026 à 20h30"
        div.mobile-only.links
"""
from __future__ import annotations

import re
import logging
from datetime import datetime
from bs4 import BeautifulSoup

from .base import BaseScraper, RawEvent

logger = logging.getLogger(__name__)

MONTHS_FR = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12,
}


def _parse_zenith_date(time_el) -> tuple[datetime | None, str | None]:
    """Parse <time datetime="...">Vendredi 19 Juin 2026 à 20h30</time>."""
    # Try datetime attribute first (ISO)
    attr = time_el.get("datetime", "")
    text = time_el.get_text(strip=True)

    # Parse from text: "Vendredi 19 Juin 2026 à 20h30"
    m = re.search(
        r"(\d{1,2})\s+(\w+)\s+(\d{4})(?:\s+[àa]\s+(\d{1,2})h(\d{0,2}))?",
        text, re.IGNORECASE
    )
    if m:
        day = int(m.group(1))
        month = MONTHS_FR.get(m.group(2).lower())
        year = int(m.group(3))
        hour = int(m.group(4)) if m.group(4) else 20
        minute = int(m.group(5)) if m.group(5) else 0
        if month:
            dt = datetime(year, month, day, hour, minute)
            time_str = f"{hour:02d}:{minute:02d}" if m.group(4) else None
            return dt, time_str

    # ISO fallback from datetime attribute
    try:
        dt = datetime.fromisoformat(attr)
        return dt, dt.strftime("%H:%M")
    except Exception:
        pass

    return None, None


class ZenithScraper(BaseScraper):
    venue_name     = "Zénith de Caen"
    venue_key      = "zenith"
    base_url       = "https://zenith-caen.fr"
    list_url       = "https://zenith-caen.fr"
    use_playwright = True

    async def _scrape(self) -> list[RawEvent]:
        html = await self._get_page(self.list_url, wait_for="li.spectacle-item-wrapper")
        soup = BeautifulSoup(html, "html.parser")
        events: list[RawEvent] = []

        for item in soup.select("li.spectacle-item-wrapper"):
            try:
                infos = item.select_one(".spectacle-infos")
                if not infos:
                    continue

                # Title: h4 = artiste, h5 = sous-titre
                h4 = infos.select_one("h4")
                h5 = infos.select_one("h5")
                title = h4.get_text(strip=True) if h4 else ""
                subtitle = h5.get_text(strip=True) if h5 else ""
                if not title:
                    title = subtitle
                if not title:
                    continue

                # Date
                time_el = infos.select_one("time")
                if not time_el:
                    continue
                dt, time_str = _parse_zenith_date(time_el)
                if not dt:
                    continue

                # Event URL (from links div)
                event_url = None
                link_el = item.select_one(".links a[href]")
                if link_el:
                    href = link_el["href"]
                    event_url = href if href.startswith("http") else self.base_url + href

                # Booking URL — prefer external ticketing link
                booking_url = None
                booking_el = item.select_one(
                    "a[href*='ticketmaster'], a[href*='fnac'], a[href*='digitick'],"
                    " a[href*='billet'], a.btn-achat, a.achat"
                )
                if booking_el:
                    booking_url = booking_el["href"]
                else:
                    booking_url = event_url

                # Image
                img_el = item.select_one("figure img")
                image_url = None
                if img_el:
                    src = img_el.get("src") or img_el.get("data-src") or img_el.get("data-lazy-src", "")
                    if src:
                        image_url = src if src.startswith("http") else self.base_url + src

                events.append(RawEvent(
                    title=title,
                    artist=subtitle if subtitle and subtitle != title else None,
                    venue=self.venue_name,
                    venue_key=self.venue_key,
                    date=dt,
                    time=time_str,
                    event_url=event_url,
                    booking_url=booking_url,
                    image_url=image_url,
                    category="Concert",
                    external_id=self._make_external_id(title, dt.date()),
                ))
            except Exception as exc:
                logger.debug(f"[zenith] skip item: {exc}")
                continue

        return events
