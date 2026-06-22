import asyncio
import logging
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from .database import SessionLocal, Event, ScrapeLog
from .notifier import send_new_events_notification
from .scrapers import ALL_SCRAPERS
from .scrapers.base import RawEvent

logger = logging.getLogger(__name__)
_scheduler = BackgroundScheduler(timezone="Europe/Paris")


def _upsert_events(db: Session, raw_events: list[RawEvent], venue_key: str) -> tuple[int, list[Event]]:
    """Insert new events, update existing ones. Returns (count, list) of newly added events."""
    new_events: list[Event] = []
    for raw in raw_events:
        existing = None
        if raw.external_id:
            existing = db.query(Event).filter(Event.external_id == raw.external_id).first()
        if not existing:
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
            existing.artist = raw.artist or existing.artist
            existing.price = raw.price or existing.price
            existing.last_updated = datetime.utcnow()
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
                category=raw.category,
                external_id=raw.external_id,
                is_new=True,
                seen=False,
                first_seen=datetime.utcnow(),
            )
            db.add(event)
            new_events.append(event)

    db.commit()
    return len(new_events), new_events


async def _run_scraper(scraper_class, venue_key: Optional[str] = None) -> list[Event]:
    """Run a single scraper, persist results, return list of newly inserted events."""
    scraper = scraper_class()
    if venue_key and scraper.venue_key != venue_key:
        return []

    db: Session = SessionLocal()
    log = ScrapeLog(venue_key=scraper.venue_key, scraped_at=datetime.utcnow())
    new_events: list[Event] = []
    try:
        raw_events = await scraper.scrape()
        added, new_events = _upsert_events(db, raw_events, scraper.venue_key)
        log.events_found = len(raw_events)
        log.events_added = added
        log.success = True
        logger.info(f"[{scraper.venue_key}] {len(raw_events)} found, {added} new")
    except Exception as e:
        log.success = False
        log.error_message = str(e)
        logger.error(f"[{scraper.venue_key}] Error: {e}", exc_info=True)
    finally:
        db.add(log)
        db.commit()
        db.close()
    return new_events


def run_all_scrapers(venue_key: Optional[str] = None):
    """Entry point called by scheduler (sync) or API (async-wrapped)."""
    async def _run_all():
        results = await asyncio.gather(
            *[_run_scraper(cls, venue_key) for cls in ALL_SCRAPERS]
        )
        all_new: list[Event] = [ev for batch in results for ev in batch]
        if all_new:
            send_new_events_notification(all_new)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run_all())
    finally:
        loop.close()


def start_scheduler():
    # Run every day at 7:00 and 19:00 (Paris time)
    _scheduler.add_job(
        run_all_scrapers,
        trigger=CronTrigger(hour="7,19", minute=0),
        id="scrape_all",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler started — scraping at 07:00 and 19:00 (Europe/Paris)")

    # Run an initial scrape on startup in background
    import threading
    t = threading.Thread(target=run_all_scrapers, daemon=True)
    t.start()


def stop_scheduler():
    if _scheduler.running:
        _scheduler.shutdown()
