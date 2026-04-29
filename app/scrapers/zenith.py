"""
Scraper for Zénith de Caen — https://zenith-caen.fr/

The Zénith site typically lists concerts on its homepage or a /programmation page.
Selector notes:
  - Event cards:   .event-item  or  .concert-card  or  article
  - Title:         h2, h3, .event-title
  - Date:          time[datetime]  or  .event-date
  - Booking:       a[href*="ticketmaster"]  or  a[href*="fnac"]  or  a.btn-achat
"""

import re
from bs4 import BeautifulSoup
from datetime import datetime
from .base import BaseScraper, RawEvent
from .theatre_ouest import _parse_french_date

PROGRAMMATION_PATHS = ["/programmation", "/concerts", "/agenda", "/"]


class ZenithScraper(BaseScraper):
    venue_name = "Zénith de Caen"
    venue_key = "zenith"
    base_url = "https://zenith-caen.fr"

    async def _scrape(self) -> list[RawEvent]:
        # Try known paths to find the event listing
        html = ""
        for path in PROGRAMMATION_PATHS:
            try:
                html = await self._get_page(self.base_url + path, wait_for=".event, article, .concert")
                soup_test = BeautifulSoup(html, "html.parser")
                cards = (
                    soup_test.select(".event-item")
                    or soup_test.select(".concert-card")
                    or soup_test.select(".programmation-item")
                    or soup_test.select("article")
                )
                if len(cards) > 0:
                    break
            except Exception:
                continue

        soup = BeautifulSoup(html, "html.parser")
        events = []

        cards = (
            soup.select(".event-item")
            or soup.select(".concert-card")
            or soup.select(".programmation-item")
            or soup.select(".event")
            or soup.select("article")
        )

        for card in cards:
            try:
                title_el = (
                    card.select_one("h2")
                    or card.select_one("h3")
                    or card.select_one(".event-title")
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

                # Zénith often links to external ticketing (Ticketmaster, Fnac, etc.)
                booking_el = card.select_one(
                    "a[href*='ticketmaster'], a[href*='fnac'], "
                    "a[href*='digitick'], a[href*='billet'], "
                    "a.btn-achat, a.achat, a.billetterie"
                )
                booking_url = None
                if booking_el:
                    booking_url = booking_el["href"]
                elif event_url:
                    booking_url = event_url

                img_el = card.select_one("img[src]")
                image_url = None
                if img_el:
                    src = img_el.get("src") or img_el.get("data-src", "")
                    image_url = src if src.startswith("http") else self.base_url + src

                events.append(RawEvent(
                    title=title,
                    venue=self.venue_name,
                    venue_key=self.venue_key,
                    date=date,
                    time=time_str,
                    event_url=event_url,
                    booking_url=booking_url,
                    image_url=image_url,
                    category="Concert",
                    external_id=self._make_external_id(title, date.date()),
                ))
            except Exception:
                continue

        return events
