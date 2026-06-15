"""
Scraper for Théâtre à l'Ouest — https://theatrealouest.com/caen/spectacle/liste?sort=date-ASC

Selector notes (adjust if the site structure changes):
  - Event cards:   .spectacle-item  or  article.card  or  .show-item
  - Title:         .spectacle-item .title  or  h2, h3 inside card
  - Date:          .spectacle-item .date  or  time[datetime]
  - Link:          a[href] on the card
  - Image:         img[src] inside card
  - Booking:       a.btn-reserver  or  a[href*="reservation"]
"""

import re
from bs4 import BeautifulSoup
from datetime import datetime
from .base import BaseScraper, RawEvent

MONTHS_FR = {
    "janvier": 1, "février": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12,
}


def _parse_french_date(text: str) -> datetime | None:
    text = text.strip().lower()
    # "vendredi 14 mars 2025" or "14 mars 2025"
    m = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", text)
    if m:
        day, month_str, year = int(m.group(1)), m.group(2), int(m.group(3))
        month = MONTHS_FR.get(month_str)
        if month:
            return datetime(year, month, day)
    # ISO format fallback
    try:
        return datetime.fromisoformat(text[:10])
    except Exception:
        return None


class TheatreOuestScraper(BaseScraper):
    venue_name = "Théâtre à l'Ouest"
    venue_key = "theatre_ouest"
    base_url = "https://theatrealouest.com"
    list_url = "https://theatrealouest.com/caen/spectacle/liste?sort=date-ASC"

    async def _scrape(self) -> list[RawEvent]:
        html = await self._get_page(self.list_url, wait_for=".spectacle-item, article, .show-list")
        soup = BeautifulSoup(html, "html.parser")
        events = []

        # Try multiple card selectors — adjust to whatever class the real site uses
        cards = (
            soup.select(".spectacle-item")
            or soup.select("article.spectacle")
            or soup.select(".show-card")
            or soup.select("li.event")
            or soup.select("article")
        )

        for card in cards:
            try:
                # Title
                title_el = (
                    card.select_one("h2")
                    or card.select_one("h3")
                    or card.select_one(".title")
                    or card.select_one(".spectacle-title")
                )
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)

                # Date — prefer <time datetime="...">
                date = None
                time_el = card.select_one("time[datetime]")
                if time_el:
                    date = _parse_french_date(time_el["datetime"])
                if not date:
                    date_el = card.select_one(".date, .spectacle-date, .event-date")
                    if date_el:
                        date = _parse_french_date(date_el.get_text())
                if not date:
                    continue

                # Time (hour)
                time_str = None
                if time_el:
                    t = time_el.get_text(strip=True)
                    m = re.search(r"\d{1,2}[h:]\d{0,2}", t)
                    if m:
                        time_str = m.group(0)

                # Event URL
                link_el = card.select_one("a[href]")
                event_url = None
                if link_el:
                    href = link_el["href"]
                    event_url = href if href.startswith("http") else self.base_url + href

                # Booking URL — look for a dedicated booking/réservation link
                booking_el = card.select_one(
                    "a[href*='reservation'], a[href*='billet'], a.btn-reserver, a.reserver"
                )
                booking_url = None
                if booking_el:
                    href = booking_el["href"]
                    booking_url = href if href.startswith("http") else self.base_url + href
                elif event_url:
                    booking_url = event_url

                # Image
                img_el = card.select_one("img[src]")
                image_url = None
                if img_el:
                    src = img_el.get("src") or img_el.get("data-src", "")
                    image_url = src if src.startswith("http") else self.base_url + src

                # Category
                cat_el = card.select_one(".category, .genre, .type-spectacle")
                category = cat_el.get_text(strip=True) if cat_el else "Spectacle"

                events.append(RawEvent(
                    title=title,
                    venue=self.venue_name,
                    venue_key=self.venue_key,
                    date=date,
                    time=time_str,
                    event_url=event_url,
                    booking_url=booking_url,
                    image_url=image_url,
                    category=category,
                    external_id=self._make_external_id(title, date.date()),
                ))
            except Exception:
                continue

        return events
