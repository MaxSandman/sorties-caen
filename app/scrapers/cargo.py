"""
Scraper for Le Cargö — https://lecargo.fr/programmation/

HTML structure (observed):
  ul.agenda > li (month group with h2 month name) > ul > li.agenda__list
    .agenda__day     — day number (e.g. "09")
    .agenda__cat     — category tag
    .agenda__title a — event link; span inside = title
    .agenda__ticket  — booking link
    figure img       — poster image
"""
from __future__ import annotations

import re
import logging
from datetime import datetime
from bs4 import BeautifulSoup

from .base import BaseScraper, RawEvent
from .theatre_ouest import _parse_french_date

logger = logging.getLogger(__name__)

MONTHS_FR = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12,
}


class CargoScraper(BaseScraper):
    venue_name     = "Le Cargö"
    venue_key      = "cargo"
    base_url       = "https://lecargo.fr"
    list_url       = "https://lecargo.fr/programmation/"
    use_playwright = False

    async def _scrape(self) -> list[RawEvent]:
        html = self._get_page_requests(self.list_url)
        soup = BeautifulSoup(html, "html.parser")
        events: list[RawEvent] = []

        today = datetime.utcnow()

        for month_li in soup.select("ul.agenda > li"):
            month_tag = month_li.find("h2")
            if not month_tag:
                continue
            month_str = month_tag.get_text(strip=True).lower()
            month_num = MONTHS_FR.get(month_str)
            if not month_num:
                continue

            # Determine year: if month already passed this year, use next year
            year = today.year
            if month_num < today.month:
                year += 1

            for item in month_li.select("li.agenda__list"):
                try:
                    day_el = item.select_one(".agenda__day")
                    if not day_el:
                        continue
                    day = int(re.search(r"\d+", day_el.get_text()).group())
                    dt = datetime(year, month_num, day)

                    title_el = item.select_one(".agenda__title a span")
                    if not title_el:
                        title_el = item.select_one(".agenda__title a")
                    if not title_el:
                        continue
                    title = title_el.get_text(strip=True)
                    if not title:
                        continue

                    # Event URL
                    link_el = item.select_one(".agenda__title a[href]")
                    event_url = None
                    if link_el:
                        href = link_el["href"]
                        event_url = href if href.startswith("http") else self.base_url + href

                    # Booking URL
                    ticket_el = item.select_one(".agenda__ticket a[href]")
                    booking_url = None
                    if ticket_el:
                        href = ticket_el["href"]
                        booking_url = href if href.startswith("http") else self.base_url + href
                    else:
                        booking_url = event_url

                    # Image
                    img_el = item.select_one("figure img")
                    image_url = None
                    if img_el:
                        src = img_el.get("src") or img_el.get("data-src") or img_el.get("data-lazy-src", "")
                        if src:
                            image_url = src if src.startswith("http") else self.base_url + src

                    # Category
                    cat_el = item.select_one(".agenda__cat")
                    category = cat_el.get_text(strip=True) if cat_el else "Musique"

                    events.append(RawEvent(
                        title=title,
                        venue=self.venue_name,
                        venue_key=self.venue_key,
                        date=dt,
                        event_url=event_url,
                        booking_url=booking_url,
                        image_url=image_url,
                        category=category,
                        external_id=self._make_external_id(title, dt.date()),
                    ))
                except Exception as exc:
                    logger.debug(f"[cargo] skip item: {exc}")
                    continue

        return events
