"""
Scraper for Palais des Sports de Caen — https://caenlamer.fr/palais-des-sports

Institutional site. Events may be on a sub-page or embedded agenda widget.
Selector notes:
  - Agenda section: .agenda, .events-list, .programmation
  - Event cards:    .event-item, article, .agenda-item
  - Title:          h2, h3, .event-title
  - Date:           time[datetime], .event-date, .date
"""

import re
from bs4 import BeautifulSoup
from .base import BaseScraper, RawEvent
from .theatre_ouest import _parse_french_date

CANDIDATE_URLS = [
    "https://caenlamer.fr/palais-des-sports",
    "https://caenlamer.fr/palais-des-sports/agenda",
    "https://caenlamer.fr/palais-des-sports/programmation",
    "https://caenlamer.fr/agenda?lieu=palais-des-sports",
]


class PalaisSportsScraper(BaseScraper):
    venue_name = "Palais des Sports de Caen"
    venue_key = "palais_sports"
    base_url = "https://caenlamer.fr"

    async def _scrape(self) -> list[RawEvent]:
        html = ""
        for url in CANDIDATE_URLS:
            try:
                html = await self._get_page(url, wait_for=".event, article, .agenda")
                soup_test = BeautifulSoup(html, "html.parser")
                cards = (
                    soup_test.select(".event-item")
                    or soup_test.select(".agenda-item")
                    or soup_test.select("article")
                )
                if cards:
                    break
            except Exception:
                continue

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
                    date_el = card.select_one(".date, .event-date")
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
                    "a[href*='ticketmaster'], a[href*='fnac']"
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

                events.append(RawEvent(
                    title=title,
                    venue=self.venue_name,
                    venue_key=self.venue_key,
                    date=date,
                    time=time_str,
                    event_url=event_url,
                    booking_url=booking_url,
                    image_url=image_url,
                    category="Sport / Spectacle",
                    external_id=self._make_external_id(title, date.date()),
                ))
            except Exception:
                continue

        return events
