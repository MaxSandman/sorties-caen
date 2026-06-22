from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from .database import SessionLocal, Event, ScrapeLog
from .scrapers import ALL_SCRAPERS
from .scrapers.base import RawEvent

logger = logging.getLogger(__name__)
_scheduler = BackgroundScheduler(timezone="Europe/Paris")

_NTFY_TOPIC = os.getenv("NTFY_TOPIC", "")
_NTFY_URL = os.getenv("NTFY_URL", "https://ntfy.sh")

_DAYS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
_MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


def _rfc2047(s: str) -> str:
    import base64
    return "=?utf-8?b?" + base64.b64encode(s.encode()).decode() + "?="


def _fmt_date_fr(ev: "Event") -> str:
    return f"{_DAYS_FR[ev.date.weekday()]} {ev.date.day} {_MONTHS_FR[ev.date.month - 1]} {ev.date.year}"


def _send_ntfy(event: "Event") -> None:
    """Envoie une notification ntfy pour un nouvel événement.

    Le titre apparaît dans la notif ntfy. Le bouton "Reserver" ouvre
    directement l'URL de réservation (pas localhost).
    Sans effet si NTFY_TOPIC n'est pas défini.
    """
    if not _NTFY_TOPIC:
        return
    try:
        import requests
        title = f"Nouveau spectacle — {event.venue}"

        parts: list[str] = []
        if event.artist:
            parts.append(event.artist)
        parts.append(_fmt_date_fr(event))
        if event.time:
            parts.append(event.time)
        body = " • ".join(parts) if parts else event.title

        action_url = event.booking_url or event.event_url
        headers: dict[str, str] = {
            "Title": _rfc2047(title),
            "Priority": "default",
            "Tags": "ticket",
        }
        if action_url:
            headers["Actions"] = f"view, Reserver, {action_url}, clear=true"
        if event.image_url:
            headers["Attach"] = event.image_url

        requests.post(
            f"{_NTFY_URL.rstrip('/')}/{_NTFY_TOPIC}",
            data=body.encode("utf-8"),
            headers=headers,
            timeout=10,
        )
        logger.info("ntfy envoyé : %s", event.title)
    except Exception as exc:
        logger.warning("ntfy échec pour %s : %s", event.title, exc)


_CAT_NORM: dict[str, str] = {
    'concert': 'Musique', 'musique': 'Musique', 'rock': 'Musique', 'jazz': 'Musique',
    'blues': 'Musique', 'jazz / blues': 'Musique', 'jazz/blues': 'Musique',
    'pop': 'Musique', 'électro': 'Musique', 'electro': 'Musique', 'rap': 'Musique',
    'hip-hop': 'Musique', 'hip hop': 'Musique', 'metal': 'Musique', 'folk': 'Musique',
    'classique': 'Musique', 'lyrique': 'Musique', 'chanson': 'Musique',
    'théâtre': 'Théâtre', 'theatre': 'Théâtre', 'comédie': 'Théâtre', 'comedie': 'Théâtre',
    'cirque': 'Théâtre', 'spectacle': 'Théâtre',
    'humour': 'Humour', 'stand-up': 'Humour', 'stand up': 'Humour',
    'improvisation': 'Humour', 'impro': 'Humour', 'cabaret': 'Humour',
    "plateau d'humoristes": 'Humour', 'magie': 'Humour',
    'danse': 'Danse', 'dance': 'Danse', 'ballet': 'Danse',
    'expo': 'Expo', 'exposition': 'Expo',
    'enfants': 'Enfants', 'famille': 'Enfants', 'jeune public': 'Enfants',
    'spectacle pour enfants': 'Enfants',
    'sport': 'Sport',
    'marché': 'Marché', 'marche': 'Marché', 'salon': 'Marché', 'foire': 'Marché',
}

_VENUE_DEFAULT_CAT: dict[str, str] = {
    'cargo':         'Musique',
    'bbc':           'Musique',
    'zenith':        'Musique',
    'theatre_ouest': 'Humour',
}


def _normalize_category(raw: Optional[str], venue_key: str = '', title: str = '') -> str:
    if raw:
        normalized = _CAT_NORM.get(raw.lower().strip())
        if normalized:
            return normalized
    if venue_key in _VENUE_DEFAULT_CAT:
        return _VENUE_DEFAULT_CAT[venue_key]
    if title:
        tl = title.lower()
        for kw, cat in _CAT_NORM.items():
            if kw in tl:
                return cat
    if raw:
        logger.debug(f"[category] unclassified: {raw!r} (venue={venue_key})")
    return 'Autre'


def _upsert_events(db: Session, raw_events: list[RawEvent], venue_key: str) -> list[Event]:
    """Insert new events, update existing ones. Returns list of newly created Event rows."""
    new_events: list[Event] = []

    for raw in raw_events:
        dedup = raw.dedup_key()
        existing = None

        # Look up by external_id first, then by dedup hash stored as external_id
        if raw.external_id:
            existing = db.query(Event).filter(Event.external_id == raw.external_id).first()
        if not existing and dedup != raw.external_id:
            existing = db.query(Event).filter(Event.external_id == dedup).first()
        if not existing:
            # Legacy fallback: title + date + venue
            existing = (
                db.query(Event)
                .filter(
                    Event.venue_key == venue_key,
                    Event.title == raw.title,
                    Event.date == raw.date,
                )
                .first()
            )

        if existing:
            existing.booking_url = raw.booking_url or existing.booking_url
            existing.event_url = raw.event_url or existing.event_url
            existing.image_url = raw.image_url or existing.image_url
            existing.price = raw.price or existing.price
            existing.last_updated = datetime.utcnow()
            if existing.category in (None, 'Événement', 'Autre', 'Concert'):
                existing.category = _normalize_category(raw.category, venue_key, raw.title)
        else:
            event = Event(
                title=raw.title,
                artist=raw.artist,
                venue=raw.venue,
                venue_key=raw.venue_key,
                date=raw.date,
                time=raw.time,
                description=raw.description,
                image_url=raw.image_url,
                booking_url=raw.booking_url,
                event_url=raw.event_url,
                price=raw.price,
                category=_normalize_category(raw.category, venue_key, raw.title),
                external_id=dedup,
                is_new=True,
                first_seen=datetime.utcnow(),
                duration=raw.duration,
                placement=raw.placement,
                doors_open=raw.doors_open,
                access_info=raw.access_info,
                address=raw.address,
            )
            db.add(event)
            new_events.append(event)

    db.commit()
    # Refresh to get assigned IDs
    for ev in new_events:
        db.refresh(ev)
    return new_events


async def _run_scraper(scraper_class, venue_key: Optional[str] = None):
    """Run a single scraper and persist results. A failure is logged, not raised."""
    scraper = scraper_class()
    if venue_key and scraper.venue_key != venue_key:
        return

    db: Session = SessionLocal()
    log = ScrapeLog(venue_key=scraper.venue_key, scraped_at=datetime.utcnow())
    try:
        raw_events = await scraper.scrape()
        new_events = _upsert_events(db, raw_events, scraper.venue_key)
        log.events_found = len(raw_events)
        log.events_added = len(new_events)
        log.success = True
        logger.info(f"[{scraper.venue_key}] {len(raw_events)} found, {len(new_events)} new")

        for ev in new_events:
            _send_ntfy(ev)

    except Exception as e:
        log.success = False
        log.error_message = str(e)
        logger.error(f"[{scraper.venue_key}] Error: {e}", exc_info=True)
    finally:
        db.add(log)
        db.commit()
        db.close()


def run_all_scrapers(venue_key: Optional[str] = None):
    """Entry point called by scheduler (sync) or CLI."""
    async def _run_all():
        # Run sequentially: each Playwright scraper launches its own Chromium,
        # and several concurrent browsers starve each other of CPU/shared memory
        # in the container, so JS-rendered pages don't finish rendering in time.
        for cls in ALL_SCRAPERS:
            await _run_scraper(cls, venue_key)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run_all())
    finally:
        loop.close()


def start_scheduler():
    _scheduler.add_job(
        run_all_scrapers,
        trigger=CronTrigger(hour="7,19", minute=0),
        id="scrape_all",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler started — scraping at 07:00 and 19:00 (Europe/Paris)")

    import threading
    t = threading.Thread(target=run_all_scrapers, daemon=True)
    t.start()


def stop_scheduler():
    if _scheduler.running:
        _scheduler.shutdown()
