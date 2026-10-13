import base64
import json
import logging
import os
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from .database import Event

logger = logging.getLogger(__name__)

_DAYS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
_MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


def _fmt_date(ev: "Event") -> str:
    day = _DAYS_FR[ev.date.weekday()]
    month = _MONTHS_FR[ev.date.month - 1]
    return f"{day} {ev.date.day} {month} {ev.date.year}"


def _rfc2047(s: str) -> str:
    return "=?utf-8?b?" + base64.b64encode(s.encode()).decode() + "?="


def _build_body(ev: "Event") -> str:
    lines = []
    # Scrapers store the headliner in `title`; `artist` is an optional extra
    # (company, support act…) shown only when it adds information.
    if ev.artist and ev.artist.strip().lower() != ev.title.strip().lower():
        lines.append(f"🎤 {ev.artist}")
    lines.append(f"📍 {ev.venue}")
    when = _fmt_date(ev)
    if ev.time:
        when += f" • {ev.time}"
    lines.append(f"📅 {when}")
    if ev.price:
        lines.append(f"💶 {ev.price}")
    return "\n".join(lines)


def _build_actions(ev: "Event", app_base: str) -> list[dict]:
    actions = []
    page_url = ev.event_url or ev.booking_url or f"{app_base}/"
    actions.append({"action": "view", "label": "Voir l'événement", "url": page_url})
    if ev.booking_url and ev.booking_url != page_url:
        actions.append({"action": "view", "label": "Réserver", "url": ev.booking_url, "clear": True})
    return actions


def send_new_events_notification(events: list["Event"]) -> None:
    """Send one ntfy notification per new event.

    No-op if NTFY_TOPIC is not set or the list is empty.
    """
    topic = os.getenv("NTFY_TOPIC", "")
    if not topic or not events:
        return

    base_url = os.getenv("NTFY_URL", "https://ntfy.sh").rstrip("/")
    app_base = os.getenv("APP_BASE_URL", "http://localhost:8000").rstrip("/")

    for ev in events:
        headers = {
            "Title": _rfc2047(f"🎵 {ev.title}"),
            "Priority": "default",
            "Tags": "ticket",
            # JSON form escapes non-ASCII (HTTP headers must be ASCII) and is
            # safe for URLs containing commas or semicolons.
            "Actions": json.dumps(_build_actions(ev, app_base)),
        }
        if ev.image_url:
            headers["Attach"] = ev.image_url

        try:
            httpx.post(
                f"{base_url}/{topic}",
                content=_build_body(ev).encode("utf-8"),
                headers=headers,
                timeout=10,
            )
            logger.info("ntfy notification sent: %s", ev.title)
        except Exception as exc:
            logger.warning("ntfy notification failed: %s", exc)
