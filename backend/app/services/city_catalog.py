"""The cities the system already knows, and a deterministic "did you mean" check against them.

A typo such as "Miammi" would otherwise go to the geocoder as a new city and might resolve to the
wrong place. The check only suggests; the operator decides (an unknown city still goes to the
distance API if they keep it).
"""

import difflib

from sqlmodel import Session, select

from app.database.models import Carrier, DistanceCache
from app.services.cities import normalize_city
from app.services.distance import CASE_CITIES

SIMILARITY_CUTOFF = 0.8


def known_cities(session: Session) -> list[str]:
    """Case table cities, every carrier HQ and both ends of every cached route, sorted."""
    cities = set(CASE_CITIES)
    cities.update(normalize_city(c) for c in session.exec(select(Carrier.headquarters_city)).all())
    for a, b in session.exec(select(DistanceCache.city_a, DistanceCache.city_b)).all():
        cities.update((a, b))
    return sorted(cities)


def check_city(name: str, known: list[str]) -> tuple[bool, str, str | None]:
    """(known?, normalized name, closest known city if the name looks like a typo of one)."""
    normalized = normalize_city(name)
    if normalized in known:
        return True, normalized, None
    by_lower = {city.lower(): city for city in known}
    matches = difflib.get_close_matches(normalized.lower(), list(by_lower), n=1, cutoff=SIMILARITY_CUTOFF)
    return False, normalized, by_lower[matches[0]] if matches else None
