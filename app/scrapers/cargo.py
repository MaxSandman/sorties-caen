"""
Scraper for Le Cargö — https://lecargo.fr/programmation/

Le Cargö is a well-known music venue. Their site uses event cards in a grid.
Selector notes (update after first run):
  - Event cards:   .event-card  or  .concert  or  article.programmation-item
  - Title:         .event-title  or  h2/h3
  - Date:          time[datetime]  or  .date
  - Booking:       a.btn  or  a[href*='reservation']
"""

import re
from bs4 import BeautifulSoup
from datetime import datetime
from .base import BaseScraper, RawEvent
from .theatre_ouest import _parse_french_date


class CargoScraper(BaseScraper):
    venue_name = "Le Cargö"
    venue_key = "cargo"
    base_url = "https://lecargo.fr"
    list_url = "https://lecargo.fr/programmation/"

    async def _scrape(self) -> list[RawEvent]:
        html = await self._get_page(self.list_url, wait_for=".event, article, .concert-card")
        soup = BeautifulSoup(html, "html.parser")
        events = []

        cards = (
            soup.select(".event-card")
            or soup.select("article.event")
            or soup.select(".concert-card")
            or soup.select(".programmation-item")
            or soup.select("article")
            or soup.select(".event")
        )

        for card in cards:
            try:
                title_el = (
                    card.select_one("h2")
                    or card.select_one("h3")
                    or card.select_one(".event-title")
                    or card.select_one(".artist")
                    or card.select_one(".title")
                )
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if len(title) < 2:
                    continue

                date = None
                time_el = card.select_one("time[datetime]")
                if time_el:
                    date = _parse_french_date(time_el.get("datetime", ""))
                if not date:
                    date_el = card.select_one(".date, .event-date, .concert-date")
                    if date_el:
                        date = _parse_french_date(date_el.get_text())
                if not date:
                    continue

                time_str = None
                if time_el:
                    t = time_el.get_text(strip=True)
                    m = re.search(r"\d{1,2}[h:]\d{0,2}", t)
                    if m:
                        time_str = m.group(0)

                link_el = card.select_one("a[href]")
                event_url = None
                if link_el:
                    href = link_el["href"]
                    event_url = href if href.startswith("http") else self.base_url + href

                booking_el = card.select_one(
                    "a[href*='reservation'], a[href*='billet'], "
                    "a[href*='ticketmaster'], a[href*='weezevent'], "
                    "a.btn-billet, a.reserver"
                )
                booking_url = None
                if booking_el:
                    href = booking_el["href"]
                    booking_url = href if href.startswith("http") else self.base_url + href
                elif event_url:
                    booking_url = event_url

                img_el = card.select_one("img")
                image_url = None
                if img_el:
                    src = img_el.get("src") or img_el.get("data-src") or img_el.get("data-lazy-src", "")
                    if src:
                        image_url = src if src.startswith("http") else self.base_url + src

                # Le Cargö does genre/category tags
                cat_el = card.select_one(".genre, .category, .tag, .style")
                category = cat_el.get_text(strip=True) if cat_el else "Musique"

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
