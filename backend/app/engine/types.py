"""Plain data the engine works on. No database or HTTP types here, so the engine stays pure."""

from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal

CONTAINER_SIZES = (20, 40, 45)
CARGO_TYPES = ("Dry", "Reefer", "Hazardous")


@dataclass(frozen=True)
class CarrierSpec:
    id: int
    name: str
    headquarters_city: str
    min_distance: int | None
    max_distance: int | None
    supported_container_sizes: tuple[int, ...]
    supported_cargo_types: tuple[str, ...]
    price_per_mile: Decimal
    is_active: bool = True
    attributes: dict = field(default_factory=dict)


@dataclass(frozen=True)
class OrderSpec:
    origin: str
    destination: str
    container_size: int
    cargo_types: tuple[str, ...]


# Distance in miles between two cities, or None when it cannot be measured.
HqDistanceLookup = Callable[[str, str], Decimal | None]


@dataclass(frozen=True)
class OrderContext:
    order: OrderSpec
    route_miles: Decimal
    hq_distance: HqDistanceLookup


@dataclass(frozen=True)
class Candidate:
    """An Eligible carrier with the values the Ranking criteria need."""

    carrier: CarrierSpec
    total_cost: Decimal
    hq_miles: Decimal | None


@dataclass(frozen=True)
class Rejection:
    carrier: CarrierSpec
    reasons: list[str]


@dataclass(frozen=True)
class Outranked:
    candidate: Candidate
    lost_on: str


@dataclass(frozen=True)
class EngineOutcome:
    winner: Candidate | None
    outranked: list[Outranked]
    rejected: list[Rejection]
    reason: str
