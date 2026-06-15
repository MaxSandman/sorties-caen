"""
Scraper for Le BBC (Big Band Café) — https://bigbandcafe.com/concerts/

Le BBC is a jazz/blues venue. The site is likely WordPress with an events plugin.
Selector notes:
  - Event cards:   .event, .tribe-event, article  or  .concert-item
  - Title:         h2, h3, .tribe-event-title  or  .entry-title
  - Date:          time[datetime]  or  .tribe-event-schedule-details  or  .event-date
  - Booking:       a[href*='reservation']  or  a.tribe-event-url
"""

import re
from bs4 import BeautifulSoup
from .base import BaseScraper, RawEvent
from .theatre_ouest import _parse_french_date


class BBCScraper(BaseScraper):
    venue_name = "Le BBC (Big Band Café)"
    venue_key = "bbc"
    base_url = "https://bigbandcafe.com"
    list_url = "https://bigbandcafe.com/concerts/"

    async def _scrape(self) -> list[RawEvent]:
        html = await self._get_page(self.list_url, wait_for=".event, article, .tribe-events-loop")
        soup = BeautifulSoup(html, "html.parser")
        events = []

        # The Events Calendar (WordPress plugin) uses .tribe-* classes
        cards = (
            soup.select(".tribe-events-loop .tribe-event")
            or soup.select(".tribe-events-loop article")
            or soup.select("article.type-tribe_events")
            or soup.select(".event-item")
            or soup.select(".concert-item")
            or soup.select("article")
        )

        for card in cards:
            try:
                title_el = (
                    card.select_one(".tribe-event-title")
                    or card.select_one(".entry-title")
                    or card.select_one("h2")
                    or card.select_one("h3")
                    or card.select_one(".event-title")
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
                    date_el = card.select_one(
                        ".tribe-event-schedule-details, .event-date, "
                        ".date, abbr[title]"
                    )
                    if date_el:
                        raw = date_el.get("title") or date_el.get_text()
                        date = _parse_french_date(raw)
                if not date:
                    continue

                time_str = None
                if time_el:
                    t = time_el.get_text(strip=True)
                    m = re.search(r"\d{1,2}[h:]\d{0,2}", t)
                    if m:
                        time_str = m.group(0)

                link_el = (
                    card.select_one("a.tribe-event-url")
                    or card.select_one(".tribe-event-title a")
                    or card.select_one("a[href]")
                )
                event_url = None
                if link_el:
                    href = link_el["href"]
                    event_url = href if href.startswith("http") else self.base_url + href

                booking_el = card.select_one(
                    "a[href*='reservation'], a[href*='billet'], "
                    "a[href*='weezevent'], a[href*='helloasso']"
                )
                booking_url = None
                if booking_el:
                    booking_url = booking_el["href"]
                elif event_url:
                    booking_url = event_url

                img_el = card.select_one("img")
                image_url = None
                if img_el:
                    src = img_el.get("src") or img_el.get("data-src", "")
                    if src and not src.endswith(".svg"):
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
                    category="Jazz / Blues",
                    external_id=self._make_external_id(title, date.date()),
                ))
            except Exception:
                continue

        return events
