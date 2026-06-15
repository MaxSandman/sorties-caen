# Import all scraper modules so their classes register themselves via __init_subclass__
from . import theatre_ouest, zenith, cargo, bbc, palais_sports, caen_evenements, demo  # noqa: F401
from .base import _SCRAPER_REGISTRY

ALL_SCRAPERS = list(_SCRAPER_REGISTRY.values())
