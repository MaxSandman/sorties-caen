"""
Scraper for Le BBC (Big Band Café) — https://bigbandcafe.com/concerts/

Real HTML structure observed:
  - Cards:   div.post-item
  - Title:   .post-item-description h2 a
  - Date:    span.span-caousel-home  →  "ven. 12 juin 2026 - 20:00"
  - Image:   .post-image img
  - URL:     .post-image a  or  h2 a
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


def _parse_bbc_date(text: str):
    """Parse 'ven. 12 juin 2026 - 20:00' → (datetime, '20:00')"""
    text = text.strip().lower()
    m = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", text)
    if not m:
        return None, None
    day, month_str, year = int(m.group(1)), m.group(2), int(m.group(3))
    month = MONTHS_FR.get(month_str)
    if not month:
        return None, None
    time_str = None
    tm = re.search(r"(\d{1,2}):(\d{2})", text)
    if tm:
        time_str = f"{tm.group(1)}h{tm.group(2)}"
    return datetime(year, month, day), time_str


class BBCScraper(BaseScraper):
    venue_name = "Le BBC (Big Band Café)"
    venue_key = "bbc"
    base_url = "https://bigbandcafe.com"
    list_url = "https://bigbandcafe.com/concerts/"

    async def _scrape(self) -> list[RawEvent]:
        html = await self._get_page(self.list_url)
        soup = BeautifulSoup(html, "html.parser")
        events = []

        for card in soup.select("div.post-item"):
            try:
                title_el = card.select_one(".post-item-description h2 a") or card.select_one("h2 a")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if len(title) < 2:
                    continue

                date_el = card.select_one("span.span-caousel-home")
                if not date_el:
                    continue
                date, time_str = _parse_bbc_date(date_el.get_text())
                if not date:
                    continue

                link_el = card.select_one(".post-image a") or card.select_one("h2 a")
                event_url = link_el["href"] if link_el else None

                img_el = card.select_one(".post-image img") or card.select_one("img")
                image_url = None
                if img_el:
                    src = (img_el.get("src") or img_el.get("data-src") or
                           img_el.get("data-lazy-src") or img_el.get("data-original") or "")
                    if src and not src.endswith(".svg") and "placeholder" not in src:
                        image_url = src if src.startswith("http") else self.base_url + src

                category_el = card.select_one(".post-meta-category")
                category = category_el.get_text(strip=True) if category_el else "Concert"

                events.append(RawEvent(
                    title=title,
                    venue=self.venue_name,
                    venue_key=self.venue_key,
                    date=date,
                    time=time_str,
                    event_url=event_url,
                    booking_url=event_url,
                    image_url=image_url,
                    category=category,
                    external_id=self._make_external_id(title, date.date()),
                ))
            except Exception:
                continue

        return events
