"""
Scraper for Zénith de Caen — https://zenith-caen.fr/

Real HTML structure observed:
  - Cards:    li.spectacle-item-wrapper
  - Title:    div.spectacle-infos h4
  - Artist:   div.spectacle-infos h5
  - Date:     p.date  →  "Samedi 13 Juin 2026 à 20h"
  - Image:    div.figure img[src]
  - Booking:  a.button-white  (external ticketing)
  - URL:      a.button-dark   ("En savoir plus")
"""

import re
from bs4 import BeautifulSoup
from datetime import datetime
from .base import BaseScraper, RawEvent

MONTHS_FR = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12,
}


def _parse_zenith_date(text: str):
    """Parse 'Samedi 13 Juin 2026 à 20h30' → (datetime, '20h30')"""
    text = text.lower()
    m = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", text)
    if not m:
        return None, None
    day, month_str, year = int(m.group(1)), m.group(2), int(m.group(3))
    month = MONTHS_FR.get(month_str)
    if not month:
        return None, None
    tm = re.search(r"(\d{1,2}h\d*)", text)
    time_str = tm.group(1) if tm else None
    return datetime(year, month, day), time_str


class ZenithScraper(BaseScraper):
    venue_name = "Zénith de Caen"
    venue_key = "zenith"
    base_url = "https://zenith-caen.fr"

    async def _scrape(self) -> list[RawEvent]:
        html = await self._get_page(self.base_url + "/")
        soup = BeautifulSoup(html, "html.parser")
        events = []

        for card in soup.select("li.spectacle-item-wrapper"):
            try:
                infos = card.select_one("div.spectacle-infos")
                if not infos:
                    continue

                h4 = infos.select_one("h4")
                if not h4:
                    continue
                title = h4.get_text(strip=True)
                if not title:
                    continue

                h5 = infos.select_one("h5")
                artist = h5.get_text(strip=True) if h5 else None

                date_el = infos.select_one("p.date")
                if not date_el:
                    continue
                date, time_str = _parse_zenith_date(date_el.get_text())
                if not date:
                    continue

                detail_el = card.select_one("a.button-dark")
                _detail_href = detail_el["href"] if detail_el else None
                event_url = (
                    _detail_href if _detail_href and _detail_href.startswith("http")
                    else (self.base_url + _detail_href if _detail_href else None)
                )

                booking_el = card.select_one("a.button-white")
                _book_href = booking_el["href"] if booking_el else None
                if _book_href:
                    booking_url = _book_href if _book_href.startswith("http") else self.base_url + _book_href
                else:
                    booking_url = event_url

                img_el = card.select_one("div.figure img")
                image_url = None
                if img_el:
                    src = img_el.get("src") or img_el.get("data-src", "")
                    if src:
                        image_url = src if src.startswith("http") else self.base_url + src

                events.append(RawEvent(
                    title=title,
                    artist=artist,
                    venue=self.venue_name,
                    venue_key=self.venue_key,
                    date=date,
                    time=time_str,
                    event_url=event_url,
                    booking_url=booking_url,
                    image_url=image_url,
                    category="Concert / Spectacle",
                    external_id=self._make_external_id(title, date.date()),
                ))
            except Exception:
                continue

        return events
