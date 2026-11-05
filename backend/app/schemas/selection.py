from datetime import datetime
from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

ContainerSize = Literal[20, 40, 45]
CargoType = Literal["Dry", "Reefer", "Hazardous"]
SelectionStatus = Literal[
    "selected", "no_carrier", "unknown_route", "invalid_order", "needs_review", "jev_unavailable"
]


class StructuredOrder(BaseModel):
    origin: str = Field(min_length=1, examples=["Miami"])
    destination: str = Field(min_length=1, examples=["Orlando"])
    container_size: ContainerSize = Field(examples=[40])
    cargo_type: CargoType = Field(examples=["Dry"])


class SelectCarrierRequest(BaseModel):
    """Exactly one form: free `text` (interpreted by Jev), or all four structured fields (Jev is skipped)."""

    text: str | None = Field(default=None, max_length=2000, examples=[None])
    origin: str | None = Field(default=None, min_length=1, examples=["Miami"])
    destination: str | None = Field(default=None, min_length=1, examples=["Orlando"])
    container_size: ContainerSize | None = Field(default=None, examples=[40])
    cargo_type: CargoType | None = Field(default=None, examples=["Dry"])

    @model_validator(mode="after")
    def exactly_one_form(self) -> Self:
        structured = [self.origin, self.destination, self.container_size, self.cargo_type]
        has_text = self.text is not None
        if has_text and any(v is not None for v in structured):
            raise ValueError("Ya serbest metin ya da yapılandırılmış alanlar gönderin, ikisini birden değil")
        if has_text and not self.text.strip():
            raise ValueError("Sipariş metni boş olamaz")
        if not has_text and any(v is None for v in structured):
            raise ValueError("Çıkış, varış, konteyner boyutu ve yük tipi birlikte gönderilmeli")
        return self

    @property
    def structured(self) -> StructuredOrder | None:
        if self.text is not None:
            return None
        return StructuredOrder(
            origin=self.origin,
            destination=self.destination,
            container_size=self.container_size,
            cargo_type=self.cargo_type,
        )


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


class FieldConfidenceOut(BaseModel):
    value: str | None
    confidence: float | None
    accepted: bool


class ConfidenceOut(BaseModel):
    source: Literal["text", "structured"] = "structured"
    min: float | None = None  # the weakest field's confidence
    fields: dict[str, FieldConfidenceOut] = {}


class ReviewOut(BaseModel):
    fields: list[str]  # Order fields the operator must confirm
    suggestions: dict[str, str]  # Jev's reading for every field that has a concrete value
    question: str


class SelectionResponse(BaseModel):
    selection_id: int | None = None
    status: SelectionStatus
    order: StructuredOrder | None = None  # None when the text could not be turned into an Order
    selected_carrier: SelectedCarrierOut | None = None
    distance: DistanceOut | None = None
    total_cost: Decimal | None = None
    reason: str
    eligible_carriers: list[OutrankedCarrierOut] = []  # Outranked carriers, in rank order
    rejected_carriers: list[RejectedCarrierOut] = []
    rules_used: list[str] = []  # enabled Ranking criteria, in priority order
    confidence: ConfidenceOut = ConfidenceOut()
    review: ReviewOut | None = None


class SelectionSummary(BaseModel):
    """One row of the Selection history list."""

    id: int
    created_at: datetime
    status: SelectionStatus
    input_text: str | None
    origin: str | None
    destination: str | None
    container_size: ContainerSize | None
    cargo_type: CargoType | None
    selected_carrier_name: str | None
    total_cost: Decimal | None


class SelectionRecord(BaseModel):
    """A stored Selection: what was asked, which ranking was used, and the response exactly as returned."""

    id: int
    created_at: datetime
    input_kind: Literal["structured", "text"]
    input: dict  # the request body as sent: {"text": ...} or the four structured fields
    ranking_used: list[str]
    status: SelectionStatus
    response: SelectionResponse
