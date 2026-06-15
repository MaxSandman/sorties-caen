from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from .database import get_db, init_db, Event, ScrapeLog
from .scheduler import start_scheduler, stop_scheduler, run_all_scrapers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Sorties Caen",
    description="Agenda culturel agrégé des salles de Caen.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    artist: Optional[str] = None
    venue: str
    venue_key: str
    date: datetime
    time: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    booking_url: Optional[str] = None
    event_url: Optional[str] = None
    price: Optional[str] = None
    category: Optional[str] = None
    is_new: bool
    first_seen: datetime
    last_updated: Optional[datetime] = None


class PaginatedEvents(BaseModel):
    items: List[EventOut]
    total: int
    page: int
    page_size: int
    pages: int


class VenueOut(BaseModel):
    key: str
    name: str
    count: int


class CategoryOut(BaseModel):
    name: str
    count: int


class CalendarDay(BaseModel):
    date: str          # YYYY-MM-DD
    events: List[EventOut]


class StatsOut(BaseModel):
    total: int
    count_new_7d: int
    last_scrape_at: Optional[datetime] = None
    last_scrape_success: Optional[bool] = None


class ScrapeLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    venue_key: str
    scraped_at: datetime
    events_found: int
    events_added: int
    success: bool
    error_message: Optional[str] = None


class ScrapeRunOut(BaseModel):
    status: str
    venue_key: str


# ── Helpers ───────────────────────────────────────────────────────────────────

_FREE_KEYWORDS = {"gratuit", "free", "0", "0€", "0 €", "entrée libre", "libre"}


def _is_free(price: Optional[str]) -> bool:
    if price is None:
        return False
    return price.strip().lower() in _FREE_KEYWORDS


def _apply_common_filters(query, category, venue, free, date_from, date_to, search):
    if category:
        query = query.filter(func.lower(Event.category) == category.lower())
    if venue:
        query = query.filter(Event.venue_key == venue)
    if free:
        # SQLite: LOWER(price) IN (...)
        free_vals = list(_FREE_KEYWORDS)
        query = query.filter(
            func.lower(Event.price).in_(free_vals)
        )
    if date_from:
        query = query.filter(Event.date >= date_from)
    if date_to:
        # include the full last day
        end = datetime.combine(date_to, datetime.max.time())
        query = query.filter(Event.date <= end)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            Event.title.ilike(pattern) | Event.venue.ilike(pattern) | Event.artist.ilike(pattern)
        )
    return query


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    with open("app/static/index.html", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), media_type="text/html; charset=utf-8")


@app.get(
    "/api/events",
    response_model=PaginatedEvents,
    summary="Liste des événements",
    tags=["Événements"],
)
def get_events(
    category: Optional[str] = Query(None, description="Filtrer par catégorie"),
    venue: Optional[str] = Query(None, description="Clé de salle (ex: cargo, zenith)"),
    free: bool = Query(False, description="Uniquement les événements gratuits"),
    date_from: Optional[date] = Query(None, description="Date de début (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Date de fin (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Recherche dans titre/artiste/lieu"),
    sort: str = Query("date", description="Tri : 'date' ou 'added'"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    cutoff = datetime.utcnow() - timedelta(days=7)
    query = db.query(Event).filter(Event.date >= cutoff)
    query = _apply_common_filters(query, category, venue, free, date_from, date_to, search)

    if sort == "added":
        query = query.order_by(Event.first_seen.desc())
    else:
        query = query.order_by(Event.date.asc())

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedEvents(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, -(-total // page_size)),  # ceil division
    )


@app.get(
    "/api/events/new",
    response_model=List[EventOut],
    summary="Événements récemment ajoutés",
    tags=["Événements"],
)
def get_new_events(
    days: int = Query(7, ge=1, le=90, description="Nombre de jours depuis l'ajout"),
    since: Optional[datetime] = Query(None, description="Date ISO minimale de first_seen"),
    db: Session = Depends(get_db),
):
    threshold = since or (datetime.utcnow() - timedelta(days=days))
    return (
        db.query(Event)
        .filter(Event.first_seen >= threshold)
        .filter(Event.date >= datetime.utcnow())
        .order_by(Event.first_seen.desc())
        .all()
    )


@app.get(
    "/api/events/weekend",
    response_model=List[EventOut],
    summary="Événements du prochain week-end",
    tags=["Événements"],
)
def get_weekend_events(db: Session = Depends(get_db)):
    today = datetime.utcnow().date()
    # Next Friday (weekday 4); if today is Fri/Sat/Sun, use this week's Friday
    days_until_friday = (4 - today.weekday()) % 7
    if days_until_friday == 0 and datetime.utcnow().hour >= 0:
        pass  # today is Friday, start now
    friday_start = datetime.combine(today + timedelta(days=days_until_friday), datetime.min.time())
    sunday_end = datetime.combine(friday_start.date() + timedelta(days=2), datetime.max.time())

    return (
        db.query(Event)
        .filter(Event.date >= friday_start, Event.date <= sunday_end)
        .order_by(Event.date.asc())
        .all()
    )


@app.get(
    "/api/events/{event_id}",
    response_model=EventOut,
    summary="Détail d'un événement",
    tags=["Événements"],
)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Événement introuvable")
    return event


@app.get(
    "/api/categories",
    response_model=List[CategoryOut],
    summary="Catégories avec compteurs",
    tags=["Référentiels"],
)
def get_categories(db: Session = Depends(get_db)):
    cutoff = datetime.utcnow() - timedelta(days=7)
    rows = (
        db.query(Event.category, func.count(Event.id).label("count"))
        .filter(Event.date >= cutoff, Event.category.isnot(None))
        .group_by(Event.category)
        .order_by(func.count(Event.id).desc())
        .all()
    )
    return [CategoryOut(name=r.category, count=r.count) for r in rows]


@app.get(
    "/api/venues",
    response_model=List[VenueOut],
    summary="Salles avec compteurs",
    tags=["Référentiels"],
)
def get_venues(db: Session = Depends(get_db)):
    cutoff = datetime.utcnow() - timedelta(days=7)
    rows = (
        db.query(Event.venue_key, Event.venue, func.count(Event.id).label("count"))
        .filter(Event.date >= cutoff)
        .group_by(Event.venue_key)
        .order_by(func.count(Event.id).desc())
        .all()
    )
    return [VenueOut(key=r.venue_key, name=r.venue, count=r.count) for r in rows]


@app.get(
    "/api/calendar",
    response_model=List[CalendarDay],
    summary="Événements groupés par jour pour un mois",
    tags=["Calendrier"],
)
def get_calendar(
    month: str = Query(..., description="Mois au format YYYY-MM", examples=["2025-06"]),
    venue: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    try:
        year, m = map(int, month.split("-"))
        start = datetime(year, m, 1)
        end = datetime(year + 1, 1, 1) if m == 12 else datetime(year, m + 1, 1)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=422, detail="Format attendu : YYYY-MM")

    query = db.query(Event).filter(Event.date >= start, Event.date < end)
    if venue:
        query = query.filter(Event.venue_key == venue)
    if category:
        query = query.filter(func.lower(Event.category) == category.lower())
    events = query.order_by(Event.date.asc()).all()

    grouped: Dict[str, List[Event]] = {}
    for ev in events:
        key = ev.date.strftime("%Y-%m-%d")
        grouped.setdefault(key, []).append(ev)

    return [CalendarDay(date=k, events=v) for k, v in sorted(grouped.items())]


@app.get(
    "/api/stats",
    response_model=StatsOut,
    summary="Statistiques globales",
    tags=["Référentiels"],
)
def get_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Event.id)).scalar() or 0
    since_7d = datetime.utcnow() - timedelta(days=7)
    count_new_7d = (
        db.query(func.count(Event.id)).filter(Event.first_seen >= since_7d).scalar() or 0
    )
    last_log = (
        db.query(ScrapeLog).order_by(ScrapeLog.scraped_at.desc()).first()
    )
    return StatsOut(
        total=total,
        count_new_7d=count_new_7d,
        last_scrape_at=last_log.scraped_at if last_log else None,
        last_scrape_success=last_log.success if last_log else None,
    )


@app.post(
    "/api/scrape/run",
    response_model=ScrapeRunOut,
    summary="Déclenche un scrape manuel",
    tags=["Admin"],
)
async def trigger_scrape(
    request: Request,
    venue_key: Optional[str] = Query(None, description="Limiter à une salle (clé)"),
    background_tasks: BackgroundTasks = None,
):
    client_host = request.client.host if request.client else ""
    if client_host not in ("127.0.0.1", "::1", "localhost"):
        raise HTTPException(status_code=403, detail="Scrape manuel réservé au réseau local")
    import os as _os
    scrapers_enabled = _os.getenv("SCRAPERS_ENABLED", "1").strip().lower() not in ("0", "false", "no")
    if not scrapers_enabled:
        raise HTTPException(status_code=503, detail="Scrapers désactivés (SCRAPERS_ENABLED=0)")
    background_tasks.add_task(run_all_scrapers, venue_key=venue_key)
    return ScrapeRunOut(status="started", venue_key=venue_key or "all")


# ── Compat routes (ancienne API) ──────────────────────────────────────────────

@app.get("/api/scrape/logs", response_model=List[ScrapeLogOut], include_in_schema=False)
def get_scrape_logs(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(ScrapeLog).order_by(ScrapeLog.scraped_at.desc()).limit(limit).all()


@app.delete("/api/events/mark-seen", include_in_schema=False)
def mark_all_seen(db: Session = Depends(get_db)):
    db.query(Event).filter(Event.is_new == True).update({"is_new": False})
    db.commit()
    return {"status": "ok"}
