from __future__ import annotations

import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar, Dict, Optional, Type

logger = logging.getLogger(__name__)

# Auto-registry: populated by __init_subclass__ on every concrete scraper
_SCRAPER_REGISTRY: Dict[str, Type[BaseScraper]] = {}


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
    duration:    Optional[str] = None
    placement:   Optional[str] = None
    doors_open:  Optional[str] = None
    access_info: Optional[str] = None
    address:     Optional[str] = None

    def dedup_key(self) -> str:
        """Stable key for deduplication: external_id when available, else hash of core fields."""
        if self.external_id:
            return self.external_id
        raw = f"{self.venue_key}|{self.title.lower().strip()}|{self.date.date()}"
        return hashlib.sha1(raw.encode()).hexdigest()


class BaseScraper(ABC):
    venue_name: str = ""
    venue_key: str = ""
    base_url: str = ""
    # Set to False in subclasses that only need requests + BeautifulSoup
    use_playwright: ClassVar[bool] = True

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.venue_key:
            _SCRAPER_REGISTRY[cls.venue_key] = cls

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

    async def _get_html(self, url: str, wait_for: Optional[str] = None) -> str:
        """Dispatch to Playwright or requests depending on use_playwright."""
        if self.use_playwright:
            return await self._get_page(url, wait_for)
        return self._get_page_requests(url)

    def _get_page_requests(self, url: str) -> str:
        import requests as req
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = req.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        return resp.text

    async def _get_page(self, url: str, wait_for: Optional[str] = None) -> str:
        """Fetch a page with Playwright, optionally waiting for a CSS selector."""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            if wait_for:
                try:
                    await page.wait_for_selector(wait_for, timeout=20000)
                except Exception:
                    pass
            content = await page.content()
            await browser.close()
            return content

    def _make_external_id(self, *parts) -> str:
        return f"{self.venue_key}_" + "_".join(str(p) for p in parts if p)
