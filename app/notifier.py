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
_SUMMARY_LINES = 10


def _fmt_date(ev: "Event") -> str:
    day = _DAYS_FR[ev.date.weekday()]
    month = _MONTHS_FR[ev.date.month - 1]
    return f"{day} {ev.date.day} {month} {ev.date.year}"


def _rfc2047(s: str) -> str:
    return "=?utf-8?b?" + base64.b64encode(s.encode()).decode() + "?="


def _labels(ev: "Event") -> tuple[str, str | None]:
    """Same rule as eventLabels() in app.js: artist first, show title second."""
    title = (ev.title or "").strip()
    artist = (ev.artist or "").strip()
    if not artist or artist.lower() == title.lower():
        return title, None
    return artist, title


def _build_body(ev: "Event") -> str:
    lines = []
    _, secondary = _labels(ev)
    if secondary:
        lines.append(f"🎭 {secondary}")
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


def _send_summary(events: list["Event"], ntfy_endpoint: str, app_base: str) -> None:
    count = len(events)
    lines = []
    for ev in sorted(events, key=lambda e: e.date)[:_SUMMARY_LINES]:
        primary, _ = _labels(ev)
        lines.append(f"• {primary} — {ev.venue} — {ev.date.strftime('%d/%m')}")
    if count > _SUMMARY_LINES:
        lines.append(f"… et {count - _SUMMARY_LINES} autres")

    try:
        httpx.post(
            ntfy_endpoint,
            content="\n".join(lines).encode("utf-8"),
            headers={
                "Title": _rfc2047(f"🎵 {count} nouvelles dates à Caen"),
                "Priority": "default",
                "Tags": "ticket",
                "Actions": json.dumps([{"action": "view", "label": "Tout voir", "url": f"{app_base}/"}]),
            },
            timeout=10,
        )
        logger.info("ntfy summary notification sent: %d events", count)
    except Exception as exc:
        logger.warning("ntfy notification failed: %s", exc)


def send_new_events_notification(events: list["Event"]) -> None:
    """Send one ntfy notification per new event, or a single summary when
    there are too many (first run, database reset…) to avoid flooding.

    No-op if NTFY_TOPIC is not set or the list is empty.
    """
    topic = os.getenv("NTFY_TOPIC", "")
    if not topic or not events:
        return

    base_url = os.getenv("NTFY_URL", "https://ntfy.sh").rstrip("/")
    app_base = os.getenv("APP_BASE_URL", "http://localhost:8000").rstrip("/")
    max_individual = int(os.getenv("NTFY_MAX_INDIVIDUAL", "5"))

    if len(events) > max_individual:
        _send_summary(events, f"{base_url}/{topic}", app_base)
        return

    for ev in events:
        primary, _ = _labels(ev)
        headers = {
            "Title": _rfc2047(f"🎵 {primary}"),
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
