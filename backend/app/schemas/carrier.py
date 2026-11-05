from datetime import datetime
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.selection import CargoType, ContainerSize
from app.services.cities import normalize_city


class CarrierIn(BaseModel):
    """Carrier data as created or fully replaced (PUT). Guards the engine against bad data."""

    name: str = Field(min_length=1, max_length=100)
    headquarters_city: str = Field(min_length=1, max_length=100)
    min_distance: int | None = Field(default=None, ge=0, description="Miles, inclusive. Empty = no lower bound.")
    max_distance: int | None = Field(default=None, ge=0, description="Miles, inclusive. Empty = unlimited.")
    supported_container_sizes: list[ContainerSize] = Field(min_length=1)
    supported_cargo_types: list[CargoType] = Field(min_length=1)
    price_per_mile: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    is_active: bool = True
    description: str | None = Field(default=None, max_length=2000, description="Carrier note. Never a Constraint.")
    attributes: dict = Field(default_factory=dict, description="Extra data for future ranking criteria.")

    @field_validator("name", "description")
    @classmethod
    def strip(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        if not value:
            raise ValueError("Firma adı boş olamaz")
        return value

    @field_validator("headquarters_city")
    @classmethod
    def normalize_hq(cls, value: str) -> str:
        city = normalize_city(value)
        if not city:
            raise ValueError("Merkez şehir boş olamaz")
        return city

    @field_validator("supported_container_sizes", "supported_cargo_types")
    @classmethod
    def deduplicate(cls, values: list) -> list:
        return list(dict.fromkeys(values))

    @model_validator(mode="after")
    def min_not_above_max(self) -> Self:
        if self.min_distance is not None and self.max_distance is not None and self.min_distance > self.max_distance:
            raise ValueError("Minimum mesafe maksimum mesafeden büyük olamaz")
        return self


class CarrierOut(CarrierIn):
    id: int
    created_at: datetime
    updated_at: datetime
