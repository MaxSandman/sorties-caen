import logging
import os
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from .database import Event

logger = logging.getLogger(__name__)


def send_new_events_notification(events: list["Event"]) -> None:
    """Send a grouped ntfy notification for newly scraped events.

    No-op if NTFY_TOPIC is not set or the list is empty.
    """
    topic = os.getenv("NTFY_TOPIC", "")
    if not topic or not events:
        return

    base_url = os.getenv("NTFY_URL", "https://ntfy.sh").rstrip("/")
    app_base = os.getenv("APP_BASE_URL", "http://localhost:8000").rstrip("/")

    count = len(events)
    title = f"{count} nouvelle{'s' if count > 1 else ''} date{'s' if count > 1 else ''} à Caen"

    lines = []
    for ev in events[:5]:
        date_str = ev.date.strftime("%d/%m/%Y")
        lines.append(f"• {ev.title} — {ev.venue} — {date_str}")

    body = "\n".join(lines)

    try:
        httpx.post(
            f"{base_url}/{topic}",
            content=body.encode(),
            headers={
                "Title": title,
                "Priority": "default",
                "Tags": "ticket",
                "Click": f"{app_base}/?tab=new",
            },
            timeout=10,
        )
        logger.info(f"ntfy notification sent: {title}")
    except Exception as exc:
        logger.warning(f"ntfy notification failed: {exc}")
