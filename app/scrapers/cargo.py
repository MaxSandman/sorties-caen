"""
Scraper for Le Cargö — https://lecargo.fr/programmation/

HTML structure (observed, JS-rendered):
  section > div.programmation--full > li.o-grid
    div.col-7 > a[href][title]
      figure > img[data-src|src]
    div.content
      span.bubble   — category ("Clubbing", "Concert", ...)
      span.date     — "Dimanche 21 juin 2026"
      h2            — title
      span.place    — room ("Club", "Grande salle", ...)
      span.hour     — "23:59"
      span.prices   — "Entrée libre" / "12 €"
      span.btn > a[href]  — booking / detail link
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


def _parse_cargo_date(date_text: str, hour_text: str = "") -> tuple[datetime | None, str | None]:
    """Parse 'Dimanche 21 juin 2026' + '23:59' → (datetime, '23:59')."""
    m = re.search(r"(\d{1,2})\s+([a-zûéè]+)\s+(\d{4})", date_text.strip(), re.IGNORECASE)
    if not m:
        return None, None
    day = int(m.group(1))
    month = MONTHS_FR.get(m.group(2).lower())
    year = int(m.group(3))
    if not month:
        return None, None

    hour, minute = 20, 0
    time_str = None
    hm = re.search(r"(\d{1,2})[h:](\d{0,2})", hour_text)
    if hm:
        hour = int(hm.group(1))
        minute = int(hm.group(2)) if hm.group(2) else 0
        time_str = f"{hour:02d}:{minute:02d}"

    try:
        return datetime(year, month, day, hour, minute), time_str
    except ValueError:
        return None, None


class CargoScraper(BaseScraper):
    venue_name     = "Le Cargö"
    venue_key      = "cargo"
    base_url       = "https://lecargo.fr"
    list_url       = "https://lecargo.fr/programmation/"
    use_playwright = True

    async def _scrape(self) -> list[RawEvent]:
        html = await self._get_page(self.list_url, wait_for=".programmation--full li.o-grid")
        soup = BeautifulSoup(html, "html.parser")
        events: list[RawEvent] = []

        for item in soup.select(".programmation--full li.o-grid"):
            try:
                content = item.select_one(".content")
                if not content:
                    continue

                title_el = content.select_one("h2")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title:
                    continue

                date_el = content.select_one("span.date")
                hour_el = content.select_one("span.hour")
                dt, time_str = _parse_cargo_date(
                    date_el.get_text(strip=True) if date_el else "",
                    hour_el.get_text(strip=True) if hour_el else "",
                )
                if not dt:
                    continue

                # Event URL — main link in the image column
                link_el = item.select_one(".col-7 a[href]") or item.select_one("a[href]")
                event_url = None
                if link_el:
                    href = link_el["href"]
                    event_url = href if href.startswith("http") else self.base_url + href

                # Booking URL — button link
                booking_url = None
                booking_el = content.select_one("span.btn a[href]")
                if booking_el:
                    href = booking_el["href"]
                    booking_url = href if href.startswith("http") else self.base_url + href
                else:
                    booking_url = event_url

                # Image
                img_el = item.select_one("figure img")
                image_url = None
                if img_el:
                    src = img_el.get("data-src") or img_el.get("src") or img_el.get("data-lazy-src", "")
                    if src:
                        image_url = src if src.startswith("http") else self.base_url + src

                cat_el = content.select_one("span.bubble")
                category = cat_el.get_text(strip=True) if cat_el else "Musique"

                place_el = content.select_one("span.place")
                placement = place_el.get_text(strip=True) if place_el else None

                price_el = content.select_one("span.prices")
                price = price_el.get_text(strip=True) if price_el else None

                events.append(RawEvent(
                    title=title,
                    venue=self.venue_name,
                    venue_key=self.venue_key,
                    date=dt,
                    time=time_str,
                    event_url=event_url,
                    booking_url=booking_url,
                    image_url=image_url,
                    category=category,
                    price=price,
                    placement=placement,
                    external_id=self._make_external_id(title, dt.date()),
                ))
            except Exception as exc:
                logger.debug(f"[cargo] skip item: {exc}")
                continue

        return events
