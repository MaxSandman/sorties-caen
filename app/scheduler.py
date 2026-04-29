import asyncio
import logging
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


def _upsert_events(db: Session, raw_events: list[RawEvent], venue_key: str) -> int:
    """Insert new events, update existing ones. Returns count of newly added events."""
    added = 0
    for raw in raw_events:
        existing = None
        if raw.external_id:
            existing = db.query(Event).filter(Event.external_id == raw.external_id).first()
        if not existing:
            # Also check by title + date to avoid duplicates when external_id changes
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
            # Update mutable fields but keep first_seen and is_new
            existing.booking_url = raw.booking_url or existing.booking_url
            existing.event_url = raw.event_url or existing.event_url
            existing.image_url = raw.image_url or existing.image_url
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
                first_seen=datetime.utcnow(),
            )
            db.add(event)
            added += 1

    db.commit()
    return added


async def _run_scraper(scraper_class, venue_key: Optional[str] = None):
    """Run a single scraper and persist results."""
    scraper = scraper_class()
    if venue_key and scraper.venue_key != venue_key:
        return

    db: Session = SessionLocal()
    log = ScrapeLog(venue_key=scraper.venue_key, scraped_at=datetime.utcnow())
    try:
        raw_events = await scraper.scrape()
        added = _upsert_events(db, raw_events, scraper.venue_key)
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


def run_all_scrapers(venue_key: Optional[str] = None):
    """Entry point called by scheduler (sync) or API (async-wrapped)."""
    async def _run_all():
        tasks = [_run_scraper(cls, venue_key) for cls in ALL_SCRAPERS]
        await asyncio.gather(*tasks)

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
