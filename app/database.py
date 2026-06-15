from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

import os
_db_path = os.getenv("DATABASE_PATH", "./sorties_caen.db")
DATABASE_URL = f"sqlite:///{_db_path}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=True)
    venue = Column(String, nullable=False)
    venue_key = Column(String, nullable=False)  # slug: theatre_ouest, zenith, etc.
    date = Column(DateTime, nullable=False)
    time = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    booking_url = Column(String, nullable=True)
    event_url = Column(String, nullable=True)
    price = Column(String, nullable=True)
    category = Column(String, nullable=True)
    external_id = Column(String, nullable=True)  # unique ID from source site
    is_new = Column(Boolean, default=True)        # flagged for "Dernières sorties"
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    duration    = Column(String, nullable=True)
    placement   = Column(String, nullable=True)
    doors_open  = Column(String, nullable=True)
    access_info = Column(String, nullable=True)
    address     = Column(String, nullable=True)


class ScrapeLog(Base):
    __tablename__ = "scrape_logs"

    id = Column(Integer, primary_key=True, index=True)
    venue_key = Column(String, nullable=False)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    events_found = Column(Integer, default=0)
    events_added = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_db():
    import sqlite3
    conn = sqlite3.connect(_db_path)
    cursor = conn.cursor()
    for col, typ in [
        ("duration",    "TEXT"),
        ("placement",   "TEXT"),
        ("doors_open",  "TEXT"),
        ("access_info", "TEXT"),
        ("address",     "TEXT"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE events ADD COLUMN {col} {typ}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    migrate_db()
