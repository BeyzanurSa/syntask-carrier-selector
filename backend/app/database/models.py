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
