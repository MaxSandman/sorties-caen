import base64
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


def send_new_events_notification(events: list["Event"]) -> None:
    """Send one ntfy notification per new event.

    No-op if NTFY_TOPIC is not set or the list is empty.
    """
    topic = os.getenv("NTFY_TOPIC", "")
    if not topic or not events:
        return

    base_url = os.getenv("NTFY_URL", "https://ntfy.sh").rstrip("/")

    for ev in events:
        title = f"🎵 Nouveau spectacle — {ev.venue}"

        parts = []
        if ev.artist:
            parts.append(ev.artist)
        parts.append(_fmt_date(ev))
        if ev.time:
            parts.append(ev.time.replace("h", "h"))
        body = " • ".join(parts)

        action_url = ev.booking_url or ev.event_url
        headers = {
            "Title": _rfc2047(title),
            "Priority": "default",
            "Tags": "ticket",
        }
        if action_url:
            headers["Actions"] = f"view, Réserver, {action_url}, clear=true"
        if ev.image_url:
            headers["Attach"] = ev.image_url

        try:
            httpx.post(
                f"{base_url}/{topic}",
                content=body.encode("utf-8"),
                headers=headers,
                timeout=10,
            )
            logger.info("ntfy notification sent: %s", ev.title)
        except Exception as exc:
            logger.warning("ntfy notification failed: %s", exc)
