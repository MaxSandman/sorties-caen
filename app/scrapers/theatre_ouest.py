"""
Théâtre à l'Ouest — API JSON https://api.theatrealouest.com
Endpoint: GET /shows/areas/{AREA_ID}?slots:to[min]=DATE&sort=slots:from|ASC&enabled=true&page=N
Auth: POST /login {username, password} -> {token}
"""

import os
import httpx
from datetime import datetime, date
from .base import BaseScraper, RawEvent

CAEN_AREA_ID = "5e4e0cb9-ac24-40a9-8a79-216ec1b0b3f4"
API_BASE = "https://api.theatrealouest.com"
SITE_BASE = "https://theatrealouest.com"


class TheatreOuestScraper(BaseScraper):
    venue_name = "Théâtre à l'Ouest"
    venue_key = "theatre_ouest"

    async def _scrape(self) -> list[RawEvent]:
        email = os.getenv("THEATRE_OUEST_EMAIL", "")
        password = os.getenv("THEATRE_OUEST_PASSWORD", "")
        if not email or not password:
            self.logger.warning("THEATRE_OUEST_EMAIL/PASSWORD not set, skipping")
            return []

        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        async with httpx.AsyncClient(headers=headers, timeout=30) as client:
            # Authenticate
            resp = await client.post(f"{API_BASE}/login",
                                     json={"username": email, "password": password})
            resp.raise_for_status()
            token = resp.json()["token"]
            client.headers["Authorization"] = f"Bearer {token}"

            # Fetch all pages of upcoming shows in Caen
            today = date.today().isoformat() + "T00:00:00"
            events: list[RawEvent] = []
            page = 1
            total_pages = 1

            while page <= total_pages:
                params = {
                    "slots:to[min]": today,
                    "sort": "slots:from|ASC",
                    "enabled": "true",
                    "page": str(page),
                }
                resp = await client.get(
                    f"{API_BASE}/shows/areas/{CAEN_AREA_ID}",
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()

                pagination = data.get("pagination", {})
                total_pages = pagination.get("totalPages", 1)
                members = data.get("members", [])

                for show in members:
                    show_events = self._parse_show(show)
                    events.extend(show_events)

                page += 1

        return events

    def _parse_show(self, show: dict) -> list[RawEvent]:
        title = show.get("title", "").strip()
        if not title:
            return []

        show_id = show.get("id", "")
        slug = show.get("slug", "")
        event_url = f"{SITE_BASE}/caen/spectacle/{slug}" if slug else None
        image_url = show.get("media")
        category = show.get("category", {}).get("name", "Spectacle") if show.get("category") else "Spectacle"
        artists = show.get("artists", "")
        if artists:
            title = f"{title} — {artists}" if artists not in title else title

        # Each slot is a session/date
        slots = show.get("slots", [])
        events = []

        if not slots or (len(slots) == 1 and not slots[0].get("from")):
            # No slot data — create a placeholder without a date (skip)
            return []

        for slot in slots:
            slot_from = slot.get("from")
            if not slot_from:
                continue
            try:
                dt = datetime.fromisoformat(slot_from.replace("Z", "+00:00"))
                event_date = datetime(dt.year, dt.month, dt.day)
                time_str = dt.strftime("%Hh%M") if (dt.hour or dt.minute) else None
            except Exception:
                continue

            booking_url = slot.get("bookingUrl") or slot.get("url") or event_url

            events.append(RawEvent(
                title=title,
                venue=self.venue_name,
                venue_key=self.venue_key,
                date=event_date,
                time=time_str,
                event_url=event_url,
                booking_url=booking_url,
                image_url=image_url,
                category=category,
                external_id=self._make_external_id(
                    show_id or title, event_date.date()
                ),
            ))

        return events
