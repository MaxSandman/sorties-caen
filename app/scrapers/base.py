import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}


@dataclass
class RawEvent:
    title: str
    venue: str
    venue_key: str
    date: datetime
    artist: Optional[str] = None
    time: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    booking_url: Optional[str] = None
    event_url: Optional[str] = None
    price: Optional[str] = None
    category: Optional[str] = None
    external_id: Optional[str] = None


class BaseScraper(ABC):
    venue_name: str = ""
    venue_key: str = ""
    base_url: str = ""

    async def scrape(self) -> list[RawEvent]:
        try:
            events = await self._scrape()
            logger.info(f"[{self.venue_key}] Scraped {len(events)} events")
            return events
        except Exception as e:
            logger.error(f"[{self.venue_key}] Scrape failed: {e}", exc_info=True)
            return []

    @abstractmethod
    async def _scrape(self) -> list[RawEvent]:
        pass

    async def _get_page(self, url: str, wait_for: Optional[str] = None) -> str:
        """Fetch a page with httpx (fast). wait_for is ignored — kept for API compat."""
        async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=30) as client:
            r = await client.get(url)
            r.raise_for_status()
            return r.text

    async def _get_page_js(self, url: str, wait_for: Optional[str] = None) -> str:
        """Fetch a page with Playwright for sites that require JavaScript rendering."""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=_HEADERS["User-Agent"])
            page = await context.new_page()
            await page.goto(url, wait_until="load", timeout=60000)
            if wait_for:
                try:
                    await page.wait_for_selector(wait_for, timeout=10000)
                except Exception:
                    pass
            content = await page.content()
            await browser.close()
            return content

    def _make_external_id(self, *parts) -> str:
        return f"{self.venue_key}_" + "_".join(str(p) for p in parts if p)
