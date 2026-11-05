"""Road distances between cities. Never estimated (ADR 0003)."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal, Protocol

from app.data.case_distances import CASE_DISTANCES
from app.services.cities import normalize_city


class DistanceProviderError(Exception):
    """The distance provider could not answer (network error, timeout, bad response)."""


class DistanceProvider(Protocol):
    def road_distance_miles(self, a: str, b: str) -> Decimal | None:
        """Road distance in miles, None if a city is unknown. Raises DistanceProviderError on failure."""
        ...


@dataclass(frozen=True)
class Distance:
    miles: Decimal
    source: Literal["table", "api"]


class DistanceService:
    """Resolves a distance from the case table first, then the provider. Returns None rather than guessing."""

    def __init__(self, provider: DistanceProvider | None = None):
        self._provider = provider

    def get(self, a: str, b: str) -> Distance | None:
        a, b = normalize_city(a), normalize_city(b)
        if a == b:
            return Distance(Decimal(0), "table")

        known = CASE_DISTANCES.get(frozenset((a, b)))
        if known is not None:
            return Distance(known, "table")

        if self._provider is None:
            return None
        try:
            miles = self._provider.road_distance_miles(a, b)
        except DistanceProviderError:
            return None
        return Distance(miles, "api") if miles is not None else None
