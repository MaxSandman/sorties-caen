"""
Scraper for Le Cargö — https://lecargo.fr/programmation/

Real HTML structure observed:
  - Cards:    li.o-grid  inside  div.programmation--full ul
  - Title:    div.content h2  (small = subtitle/artist)
  - Date:     span.date  →  "Jeudi 11 juin 2026"
  - Hour:     span.hour  →  "19:00"
  - Category: span.bubble (first)
  - URL:      div.col-7 a  or  span.btn a
  - Booking:  span.btn--dark a
  - Image:    img[data-src]
  - Price:    span.prices
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


def _parse_cargo_date(text: str) -> datetime | None:
    """Parse 'Jeudi 11 juin 2026' → datetime"""
    text = text.strip().lower()
    m = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", text)
    if not m:
        return None
    day, month_str, year = int(m.group(1)), m.group(2), int(m.group(3))
    month = MONTHS_FR.get(month_str)
    if not month:
        return None
    return datetime(year, month, day)


class CargoScraper(BaseScraper):
    venue_name = "Le Cargö"
    venue_key = "cargo"
    base_url = "https://lecargo.fr"
    list_url = "https://lecargo.fr/programmation/"

    async def _scrape(self) -> list[RawEvent]:
        html = await self._get_page(self.list_url)
        soup = BeautifulSoup(html, "html.parser")
        events = []

        for card in soup.select("div.programmation--full ul li.o-grid"):
            try:
                content = card.select_one("div.content")
                if not content:
                    continue

                h2 = content.select_one("h2")
                if not h2:
                    continue
                small = h2.select_one("small")
                artist = small.get_text(strip=True) if small else None
                if small:
                    small.extract()
                title = h2.get_text(strip=True)
                if not title:
                    continue

                date_el = content.select_one("span.date")
                if not date_el:
                    continue
                date = _parse_cargo_date(date_el.get_text())
                if not date:
                    continue

                hour_el = content.select_one("span.hour")
                time_str = hour_el.get_text(strip=True) if hour_el else None

                cat_el = content.select_one("span.bubble")
                category = cat_el.get_text(strip=True) if cat_el else "Concert"

                price_el = content.select_one("span.prices")
                price = price_el.get_text(strip=True) if price_el else None

                link_el = card.select_one("div.col-7 a, div.tcol-5 a")
                event_url = None
                if link_el:
                    href = link_el.get("href", "")
                    event_url = href if href.startswith("http") else self.base_url + href

                booking_el = content.select_one("span.btn--dark a")
                booking_url = None
                if booking_el:
                    href = booking_el.get("href", "")
                    booking_url = href if href.startswith("http") else self.base_url + href
                elif event_url:
                    booking_url = event_url

                img_el = card.select_one("img[data-src]")
                image_url = img_el.get("data-src") if img_el else None

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
                    category=category,
                    price=price,
                    external_id=self._make_external_id(title, date.date()),
                ))
            except Exception:
                continue

        return events
