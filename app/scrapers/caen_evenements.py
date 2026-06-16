"""
Scraper for Caen Événements (Palais des Congrès) — https://www.caen-evenements.com

HTML structure (observed, schema.org markup):
  div.ce_results-list > div.row > div.col-md-4 >
    div[itemscope itemtype="//schema.org/Event"]
      a.ce-events-item[href]
        div.ce-image > img[src]
        div.ce-events-item-text
          div.ce-events-item-text-date
            span.is-date           — "25 <span>Juin</span>"
            time[itemprop=startDate][content="2026-06-25"]
          h2.ce-events-item-text-desc[itemprop=name]   — title
          p.ce-events-item-text-place
            span[itemprop=name]    — venue name
"""
from __future__ import annotations

import logging
from datetime import datetime
from bs4 import BeautifulSoup

from .base import BaseScraper, RawEvent

logger = logging.getLogger(__name__)


class CaenEvenementsScraper(BaseScraper):
    venue_name     = "Caen Événements"
    venue_key      = "caen_evenements"
    base_url       = "https://www.caen-evenements.com"
    list_url       = "https://www.caen-evenements.com/evenements/"
    use_playwright = True

    async def _scrape(self) -> list[RawEvent]:
        html = await self._get_page(self.list_url, wait_for="div[itemscope]")
        soup = BeautifulSoup(html, "html.parser")
        events: list[RawEvent] = []

        for card in soup.select("div[itemscope][itemtype*='schema.org/Event']"):
            try:
                # Title
                title_el = card.select_one("h2[itemprop=name]") or card.select_one("h2")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True).strip('" ')
                if not title:
                    continue

                # Date — prefer ISO content attribute
                time_el = card.select_one("time[itemprop=startDate][content]")
                if not time_el:
                    time_el = card.select_one("time[content]")
                if not time_el:
                    continue
                content = time_el.get("content", "")
                try:
                    dt = datetime.fromisoformat(content)
                except Exception:
                    continue

                # Event URL
                link_el = card.select_one("a.ce-events-item[href]")
                event_url = None
                if link_el:
                    href = link_el["href"]
                    event_url = href if href.startswith("http") else self.base_url + href

                # Image
                img_el = card.select_one("div.ce-image img")
                image_url = None
                if img_el:
                    src = img_el.get("src") or img_el.get("data-src") or img_el.get("data-lazy-src", "")
                    if src:
                        image_url = src if src.startswith("http") else self.base_url + src

                # Venue name from schema
                venue_el = card.select_one("span[itemprop=name]")
                venue_name = venue_el.get_text(strip=True) if venue_el else self.venue_name

                events.append(RawEvent(
                    title=title,
                    venue=venue_name or self.venue_name,
                    venue_key=self.venue_key,
                    date=dt,
                    event_url=event_url,
                    booking_url=event_url,
                    image_url=image_url,
                    category="Événement",
                    external_id=self._make_external_id(title, dt.date()),
                ))
            except Exception as exc:
                logger.debug(f"[caen_evenements] skip item: {exc}")
                continue

        return events
