"""
Scraper for Le BBC (Big Band Café) — https://bigbandcafe.com

HTML structure (observed):
  div.col-md-3.col-12 > div.post-item > div.post-item-wrap > div.row
    div.post-image > a[href]  — event URL + img
    div.post-item-description
      h2.MB0 > a[href]        — title
      span.span-caousel-home  — date text "jeu. 18 juin 2026 - 20:00"
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


def _parse_bbc_date(text: str) -> tuple[datetime | None, str | None]:
    """Parse 'jeu. 18 juin 2026 - 20:00' → (datetime, '20:00')."""
    text = text.strip()
    m = re.search(
        r"(\d{1,2})\s+(\w+)\s+(\d{4})(?:\s*[-–]\s*(\d{1,2})[h:](\d{2}))?",
        text, re.IGNORECASE
    )
    if not m:
        return None, None
    day = int(m.group(1))
    month_str = m.group(2).lower()
    year = int(m.group(3))
    hour = int(m.group(4)) if m.group(4) else 20
    minute = int(m.group(5)) if m.group(5) else 0
    month = MONTHS_FR.get(month_str)
    if not month:
        return None, None
    dt = datetime(year, month, day, hour, minute)
    time_str = f"{hour:02d}:{minute:02d}" if m.group(4) else None
    return dt, time_str


class BBCScraper(BaseScraper):
    venue_name     = "Le BBC (Big Band Café)"
    venue_key      = "bbc"
    base_url       = "https://bigbandcafe.com"
    list_url       = "https://bigbandcafe.com/programmation/"
    use_playwright = True

    async def _scrape(self) -> list[RawEvent]:
        html = await self._get_page(self.list_url, wait_for="div.post-item")
        soup = BeautifulSoup(html, "html.parser")
        events: list[RawEvent] = []

        for card in soup.select("div.post-item"):
            try:
                # Title
                title_el = card.select_one(".post-item-description h2 a")
                if not title_el:
                    title_el = card.select_one(".post-item-description h2")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title:
                    continue

                # Date
                date_el = card.select_one(".span-caousel-home")
                if not date_el:
                    continue
                dt, time_str = _parse_bbc_date(date_el.get_text())
                if not dt:
                    continue

                # Event URL
                link_el = card.select_one(".post-image a[href]") or card.select_one(".post-item-description h2 a[href]")
                event_url = None
                if link_el:
                    href = link_el["href"]
                    event_url = href if href.startswith("http") else self.base_url + href

                # Image
                img_el = card.select_one(".post-image img")
                image_url = None
                if img_el:
                    src = img_el.get("src") or img_el.get("data-src") or img_el.get("data-lazy-src", "")
                    if src:
                        image_url = src if src.startswith("http") else self.base_url + src

                events.append(RawEvent(
                    title=title,
                    venue=self.venue_name,
                    venue_key=self.venue_key,
                    date=dt,
                    time=time_str,
                    event_url=event_url,
                    booking_url=event_url,
                    image_url=image_url,
                    category="Musique",
                    external_id=self._make_external_id(title, dt.date()),
                ))
            except Exception as exc:
                logger.debug(f"[bbc] skip item: {exc}")
                continue

        return events
