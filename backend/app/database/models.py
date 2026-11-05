from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.now(UTC)


class Carrier(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    headquarters_city: str
    min_distance: int | None = None  # miles, inclusive; None = no lower bound
    max_distance: int | None = None  # miles, inclusive; None = unlimited
    supported_container_sizes: list[int] = Field(sa_column=Column(JSON, nullable=False))
    supported_cargo_types: list[str] = Field(sa_column=Column(JSON, nullable=False))
    price_per_mile: Decimal = Field(max_digits=10, decimal_places=2)
    is_active: bool = True
    description: str | None = None  # Carrier note; never a Constraint
    attributes: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class Selection(SQLModel, table=True):
    """Immutable record of one decision. `response` is the full API response, so it never needs recomputing."""

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=_now, index=True)
    input_kind: str  # "structured" (free text arrives with ticket 07)
    input: dict = Field(sa_column=Column(JSON, nullable=False))
    status: str
    selected_carrier_name: str | None = None
    total_cost: Decimal | None = Field(default=None, max_digits=12, decimal_places=2)
    route_miles: Decimal | None = Field(default=None, max_digits=10, decimal_places=1)
    ranking_used: list[str] = Field(sa_column=Column(JSON, nullable=False))
    response: dict = Field(sa_column=Column(JSON, nullable=False))
