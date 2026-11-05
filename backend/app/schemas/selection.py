from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

ContainerSize = Literal[20, 40, 45]
CargoType = Literal["Dry", "Reefer", "Hazardous"]
SelectionStatus = Literal["selected", "no_carrier", "unknown_route", "invalid_order"]


class StructuredOrder(BaseModel):
    origin: str = Field(min_length=1, examples=["Miami"])
    destination: str = Field(min_length=1, examples=["Orlando"])
    container_size: ContainerSize = Field(examples=[40])
    cargo_type: CargoType = Field(examples=["Dry"])


class DistanceOut(BaseModel):
    miles: Decimal
    source: Literal["table", "api"]


class SelectedCarrierOut(BaseModel):
    id: int
    name: str
    headquarters_city: str
    hq_distance: Decimal | None


class OutrankedCarrierOut(BaseModel):
    name: str
    total_cost: Decimal
    hq_distance: Decimal | None
    lost_on: str


class RejectedCarrierOut(BaseModel):
    name: str
    reasons: list[str]


class SelectionResponse(BaseModel):
    selection_id: int | None = None
    status: SelectionStatus
    order: StructuredOrder
    selected_carrier: SelectedCarrierOut | None = None
    distance: DistanceOut | None = None
    total_cost: Decimal | None = None
    reason: str
    eligible_carriers: list[OutrankedCarrierOut] = []  # Outranked carriers, in rank order
    rejected_carriers: list[RejectedCarrierOut] = []


class SelectionSummary(BaseModel):
    """One row of the Selection history list."""

    id: int
    created_at: datetime
    status: SelectionStatus
    origin: str
    destination: str
    container_size: ContainerSize
    cargo_type: CargoType
    selected_carrier_name: str | None
    total_cost: Decimal | None


class SelectionRecord(BaseModel):
    """A stored Selection: what was asked, which ranking was used, and the response exactly as returned."""

    id: int
    created_at: datetime
    input_kind: Literal["structured"]
    input: StructuredOrder
    ranking_used: list[str]
    status: SelectionStatus
    response: SelectionResponse
