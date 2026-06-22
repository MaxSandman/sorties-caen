"""
Scraper for Caen Événements — https://www.caen-evenements.com/agenda/

Real HTML structure observed:
  - Cards:   a.ce_events-item  (the card IS the link)
  - URL:     a.ce_events-item[href]
  - Title:   h2.ce_events-item-text-desc
  - Date:    time[itemprop="startDate"][content]  →  "2026-06-25"  (ISO)
  - Image:   div.ce_image img[src]
  - Venue:   p.ce_events-item-text-place span[itemprop="name"]
"""

from bs4 import BeautifulSoup
from datetime import datetime
from .base import BaseScraper, RawEvent


class CaenEvenementsScraper(BaseScraper):
    venue_name = "Parc des Expos / Congrès de Caen"
    venue_key = "caen_evenements"
    base_url = "https://www.caen-evenements.com"
    list_url = "https://www.caen-evenements.com/agenda/"

    async def _scrape(self) -> list[RawEvent]:
        html = await self._get_page(self.list_url)
        soup = BeautifulSoup(html, "html.parser")
        events = []

        for card in soup.select("a.ce_events-item"):
            try:
                title_el = card.select_one("h2.ce_events-item-text-desc")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title:
                    continue

                time_el = card.select_one("time[itemprop='startDate']")
                if not time_el:
                    continue
                content = time_el.get("content", "")
                try:
                    date = datetime.fromisoformat(content[:10])
                except Exception:
                    continue

                event_url = card.get("href")
                if event_url and not event_url.startswith("http"):
                    event_url = self.base_url + event_url

                img_el = card.select_one("div.ce_image img")
                image_url = None
                if img_el:
                    src = img_el.get("src") or img_el.get("data-src", "")
                    if src:
                        image_url = src if src.startswith("http") else self.base_url + src

                venue_el = card.select_one("p.ce_events-item-text-place span[itemprop='name']")
                venue_name = venue_el.get_text(strip=True) if venue_el else self.venue_name

                events.append(RawEvent(
                    title=title,
                    venue=venue_name,
                    venue_key=self.venue_key,
                    date=date,
                    event_url=event_url,
                    booking_url=event_url,
                    image_url=image_url,
                    category="Événement",
                    external_id=self._make_external_id(title, date.date()),
                ))
            except Exception:
                continue

        return events
