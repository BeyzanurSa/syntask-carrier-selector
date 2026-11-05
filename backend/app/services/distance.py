"""Road distances between cities. Never estimated (ADR 0003)."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal, Protocol

from sqlmodel import Session

from app.data.case_distances import CASE_DISTANCES
from app.database.models import DistanceCache
from app.services.cities import normalize_city

TENTH = Decimal("0.1")
CASE_CITIES = frozenset(city for pair in CASE_DISTANCES for city in pair)


class DistanceProviderError(Exception):
    """The distance provider could not answer (network error, timeout, bad response)."""


class DistanceProvider(Protocol):
    name: str

    def road_distance_miles(self, a: str, b: str) -> Decimal | None:
        """Road distance in miles, None if a city or route is unknown. Raises DistanceProviderError on failure."""
        ...

    def knows_city(self, city: str) -> bool:
        """Whether the provider can locate the city. Raises DistanceProviderError on failure."""
        ...


@dataclass(frozen=True)
class Distance:
    miles: Decimal
    source: Literal["table", "api"]


class DistanceService:
    """Case table → cache → provider. Returns None rather than guessing; only successful lookups are cached."""

    def __init__(self, provider: DistanceProvider | None = None, session: Session | None = None):
        self._provider = provider
        self._session = session

    def get(self, a: str, b: str) -> Distance | None:
        a, b = normalize_city(a), normalize_city(b)
        if a == b:
            return Distance(Decimal(0), "table")

        known = CASE_DISTANCES.get(frozenset((a, b)))
        if known is not None:
            return Distance(known, "table")

        key = tuple(sorted((a, b)))
        if self._session is not None:
            cached = self._session.get(DistanceCache, key)
            if cached is not None:
                return Distance(Decimal(cached.miles).quantize(TENTH), "api")

        if self._provider is None:
            return None
        try:
            miles = self._provider.road_distance_miles(a, b)
        except DistanceProviderError:
            return None
        if miles is None:
            return None
        miles = miles.quantize(TENTH, rounding=ROUND_HALF_UP)  # same precision as the cache

        if self._session is not None:
            self._session.add(DistanceCache(city_a=key[0], city_b=key[1], miles=miles, provider=self._provider.name))
            self._session.commit()
        return Distance(miles, "api")

    def can_measure_from(self, city: str) -> bool:
        """Whether distances from this city can be resolved at all (used to warn about a carrier's HQ)."""
        city = normalize_city(city)
        if city in CASE_CITIES:
            return True
        if self._provider is None:
            return False
        try:
            return self._provider.knows_city(city)
        except DistanceProviderError:
            return False
