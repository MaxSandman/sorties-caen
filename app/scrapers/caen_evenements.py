from __future__ import annotations
"""
Scraper for Caen Événements (Centre des Congrès) — https://www.caen-evenements.com/agenda/

This site aggregates events for the Caen congress center and other venues.
Selector notes:
  - Event cards:   .event, article, .agenda-item
  - Title:         h2, h3, .event-title
  - Date:          time[datetime], .event-date, .date
  - Booking:       a[href*='reservation'], a.btn
"""

import re
from bs4 import BeautifulSoup
from .base import BaseScraper, RawEvent
from .theatre_ouest import _parse_french_date


class CaenEvenementsScraper(BaseScraper):
    venue_name = "Centre des Congrès de Caen"
    venue_key = "caen_evenements"
    base_url = "https://www.caen-evenements.com"
    list_url = "https://www.caen-evenements.com/agenda/"

    async def _scrape(self) -> list[RawEvent]:
        html = await self._get_page(self.list_url, wait_for=".event, article, .agenda")
        soup = BeautifulSoup(html, "html.parser")
        events = []

        cards = (
            soup.select(".event-item")
            or soup.select(".agenda-item")
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
                    date_el = card.select_one(".date, .event-date, .date-event")
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
                    "a[href*='ticketmaster'], a[href*='fnac'], "
                    "a.btn-reservation, a.reserver"
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
                    src = img_el.get("src") or img_el.get("data-src", "")
                    if src:
                        image_url = src if src.startswith("http") else self.base_url + src

                # Venue info may be present on aggregator
                venue_el = card.select_one(".venue, .lieu, .location")
                venue_extra = venue_el.get_text(strip=True) if venue_el else ""
                display_venue = (
                    f"{self.venue_name} — {venue_extra}" if venue_extra else self.venue_name
                )

                events.append(RawEvent(
                    title=title,
                    venue=display_venue,
                    venue_key=self.venue_key,
                    date=date,
                    time=time_str,
                    event_url=event_url,
                    booking_url=booking_url,
                    image_url=image_url,
                    category="Événement",
                    external_id=self._make_external_id(title, date.date()),
                ))
            except Exception:
                continue

        return events
