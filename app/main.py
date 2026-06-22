import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from .database import get_db, init_db, Event, ScrapeLog
from .scheduler import start_scheduler, stop_scheduler, run_all_scrapers

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Sorties Caen", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


# ---------- Pydantic schemas ----------

class EventOut(BaseModel):
    id: int
    title: str
    artist: Optional[str]
    venue: str
    venue_key: str
    date: datetime
    time: Optional[str]
    description: Optional[str]
    image_url: Optional[str]
    booking_url: Optional[str]
    event_url: Optional[str]
    price: Optional[str]
    category: Optional[str]
    is_new: bool
    seen: bool
    first_seen: datetime
    first_seen_at: datetime  # alias for first_seen, for forward-compat

    class Config:
        from_attributes = True


class ScrapeLogOut(BaseModel):
    id: int
    venue_key: str
    scraped_at: datetime
    events_found: int
    events_added: int
    success: bool
    error_message: Optional[str]

    class Config:
        from_attributes = True


# ---------- Routes ----------

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("app/static/index.html", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), media_type="text/html; charset=utf-8")


@app.get("/api/events", response_model=list[EventOut])
def get_events(
    month: Optional[int] = None,
    year: Optional[int] = None,
    venue_key: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Event)

    if venue_key:
        query = query.filter(Event.venue_key == venue_key)

    if year and month:
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        query = query.filter(Event.date >= start, Event.date < end)
    elif year:
        query = query.filter(Event.date >= datetime(year, 1, 1), Event.date < datetime(year + 1, 1, 1))

    # Only show future events (and past 7 days)
    cutoff = datetime.utcnow() - timedelta(days=7)
    query = query.filter(Event.date >= cutoff)

    return query.order_by(Event.date.asc()).all()


@app.get("/api/events/new", response_model=list[EventOut])
def get_new_events(
    days: int = 7,
    db: Session = Depends(get_db),
):
    """Return events added (first_seen) in the last N days — the 'Dernières sorties' feed."""
    since = datetime.utcnow() - timedelta(days=days)
    return (
        db.query(Event)
        .filter(Event.first_seen >= since)
        .filter(Event.date >= datetime.utcnow())
        .order_by(Event.first_seen.desc())
        .all()
    )


@app.get("/api/events/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@app.get("/api/venues")
def get_venues(db: Session = Depends(get_db)):
    from sqlalchemy import distinct, func
    rows = (
        db.query(Event.venue_key, Event.venue, func.count(Event.id).label("count"))
        .group_by(Event.venue_key)
        .all()
    )
    return [{"key": r.venue_key, "name": r.venue, "count": r.count} for r in rows]


@app.post("/api/scrape")
async def trigger_scrape(
    venue_key: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    """Manually trigger a scrape (all venues or a specific one)."""
    background_tasks.add_task(run_all_scrapers, venue_key=venue_key)
    return {"status": "started", "venue_key": venue_key or "all"}


@app.get("/api/scrape/logs", response_model=list[ScrapeLogOut])
def get_scrape_logs(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(ScrapeLog).order_by(ScrapeLog.scraped_at.desc()).limit(limit).all()


class MarkSeenRequest(BaseModel):
    ids: Optional[List[int]] = None  # if None, mark all


@app.post("/api/events/mark-seen")
def mark_seen(body: MarkSeenRequest = None, db: Session = Depends(get_db)):
    """Mark specific events (by id list) or all events as seen."""
    q = db.query(Event)
    if body and body.ids:
        q = q.filter(Event.id.in_(body.ids))
    q.update({"seen": True, "is_new": False}, synchronize_session=False)
    db.commit()
    return {"status": "ok"}


@app.delete("/api/events/mark-seen")
def mark_all_seen_legacy(db: Session = Depends(get_db)):
    """Legacy endpoint — marks all events as seen."""
    db.query(Event).update({"seen": True, "is_new": False}, synchronize_session=False)
    db.commit()
    return {"status": "ok"}


@app.get("/api/new-count")
def get_new_count(db: Session = Depends(get_db)):
    """Return count of events not yet seen by the user."""
    count = db.query(Event).filter(Event.seen == False).filter(
        Event.date >= datetime.utcnow()
    ).count()
    return {"count": count}
