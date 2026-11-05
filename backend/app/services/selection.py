"""SelectionService: the one entry point for "pick a carrier for this Order"."""

from decimal import Decimal

from sqlmodel import Session, select

from app import messages
from app.database.models import Carrier
from app.engine.selector import select_carrier
from app.engine.types import CarrierSpec, OrderContext, OrderSpec
from app.schemas.selection import (
    DistanceOut,
    OutrankedCarrierOut,
    RejectedCarrierOut,
    SelectedCarrierOut,
    SelectionResponse,
    StructuredOrder,
)
from app.services.cities import normalize_city
from app.services.distance import DistanceService
from app.services.rules_store import RulesStore


class SelectionService:
    def __init__(self, session: Session, distances: DistanceService, rules: RulesStore):
        self._session = session
        self._distances = distances
        self._rules = rules

    def run(self, order: StructuredOrder) -> SelectionResponse:
        order = order.model_copy(
            update={"origin": normalize_city(order.origin), "destination": normalize_city(order.destination)}
        )
        if order.origin == order.destination:
            return SelectionResponse(status="invalid_order", order=order, reason=messages.SAME_CITY)

        route = self._distances.get(order.origin, order.destination)
        if route is None:
            return SelectionResponse(
                status="unknown_route",
                order=order,
                reason=messages.unknown_route(order.origin, order.destination),
            )

        rules = self._rules.load()
        ctx = OrderContext(
            order=OrderSpec(order.origin, order.destination, order.container_size, order.cargo_type),
            route_miles=route.miles,
            hq_distance=self._hq_distance,
        )
        outcome = select_carrier(self._load_carriers(), ctx, rules.constraints, rules.enabled_ranking)

        response = SelectionResponse(
            status="selected" if outcome.winner else "no_carrier",
            order=order,
            distance=DistanceOut(miles=route.miles, source=route.source),
            reason=outcome.reason,
            eligible_carriers=[
                OutrankedCarrierOut(
                    name=o.candidate.carrier.name,
                    total_cost=o.candidate.total_cost,
                    hq_distance=o.candidate.hq_miles,
                    lost_on=o.lost_on,
                )
                for o in outcome.outranked
            ],
            rejected_carriers=[RejectedCarrierOut(name=r.carrier.name, reasons=r.reasons) for r in outcome.rejected],
        )
        if outcome.winner:
            winner = outcome.winner
            response.total_cost = winner.total_cost
            response.selected_carrier = SelectedCarrierOut(
                id=winner.carrier.id,
                name=winner.carrier.name,
                headquarters_city=winner.carrier.headquarters_city,
                hq_distance=winner.hq_miles,
            )
        return response

    def _hq_distance(self, hq_city: str, origin: str) -> Decimal | None:
        distance = self._distances.get(hq_city, origin)
        return distance.miles if distance else None

    def _load_carriers(self) -> list[CarrierSpec]:
        rows = self._session.exec(select(Carrier).order_by(Carrier.name)).all()
        return [
            CarrierSpec(
                id=row.id,
                name=row.name,
                headquarters_city=normalize_city(row.headquarters_city),
                min_distance=row.min_distance,
                max_distance=row.max_distance,
                supported_container_sizes=tuple(row.supported_container_sizes),
                supported_cargo_types=tuple(row.supported_cargo_types),
                price_per_mile=Decimal(row.price_per_mile),
                is_active=row.is_active,
                attributes=dict(row.attributes),
            )
            for row in rows
        ]
