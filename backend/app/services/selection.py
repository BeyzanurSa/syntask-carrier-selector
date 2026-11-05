"""SelectionService: the one entry point for "pick a carrier for this Order"."""

from decimal import Decimal

from sqlmodel import Session, select

from app import messages
from app.database.models import Carrier, DistanceCache, Selection
from app.engine.selector import select_carrier
from app.engine.types import CarrierSpec, OrderContext, OrderSpec
from app.schemas.selection import (
    ConfidenceOut,
    DistanceOut,
    FieldConfidenceOut,
    NoteWarningOut,
    OutrankedCarrierOut,
    RejectedCarrierOut,
    ReviewOut,
    SelectCarrierRequest,
    SelectedCarrierOut,
    SelectionResponse,
    StructuredOrder,
)
from app.services.cities import normalize_city
from app.services.distance import CASE_CITIES, DistanceService
from app.services.interpreter import SENTINELS, Interpretation, Interpreter, InterpreterUnavailable
from app.services.rules_store import RuleSet, RulesStore


class SelectionService:
    def __init__(
        self,
        session: Session,
        distances: DistanceService,
        rules: RulesStore,
        interpreter: Interpreter | None = None,
    ):
        self._session = session
        self._distances = distances
        self._rules = rules
        self._interpreter = interpreter
        self._notes: dict[str, str] = {}

    def run(self, request: SelectCarrierRequest) -> SelectionResponse:
        """Decide (interpreting free text first, if given), then store the decision as a Selection snapshot."""
        rules = self._rules.load()
        if request.text is None:
            response = self._decide(request.structured, rules)
        else:
            response = self._interpret_then_decide(request.text, rules)
        response.rules_used = rules.enabled_ranking
        return self._record(request, rules, response)

    def _interpret_then_decide(self, text: str, rules: RuleSet) -> SelectionResponse:
        unavailable = SelectionResponse(
            status="jev_unavailable", reason=messages.JEV_UNAVAILABLE, confidence=ConfidenceOut(source="text")
        )
        if self._interpreter is None:
            return unavailable
        try:
            interpretation = self._interpreter.interpret(text, self._known_cities())
        except InterpreterUnavailable:
            return unavailable

        confidence, uncertain = _review_gate(interpretation, rules.thresholds.field_confidence)
        if uncertain:
            readings = interpretation.fields()
            return SelectionResponse(
                status="needs_review",
                reason=messages.NEEDS_REVIEW,
                confidence=confidence,
                review=ReviewOut(
                    fields=uncertain,
                    suggestions={n: r.value for n, r in readings.items() if r.value and r.value not in SENTINELS},
                    question=messages.review_question({n: readings[n].value for n in uncertain}),
                ),
            )

        order = StructuredOrder(
            origin=interpretation.origin.value,
            destination=interpretation.destination.value,
            container_size=int(interpretation.container_size.value),
            cargo_type=interpretation.cargo_type.value,
        )
        response = self._decide(order, rules)
        response.confidence = confidence
        return response

    def _decide(self, order: StructuredOrder, rules: RuleSet) -> SelectionResponse:
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

        ctx = OrderContext(
            order=OrderSpec(order.origin, order.destination, order.container_size, order.cargo_type),
            route_miles=route.miles,
            hq_distance=self._hq_distance,
        )
        carriers = self._load_carriers()
        outcome = select_carrier(carriers, ctx, rules.constraints, rules.enabled_ranking)

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

        eligible = [outcome.winner.carrier.name] if outcome.winner else []
        eligible += [o.candidate.carrier.name for o in outcome.outranked]
        response.warnings, response.notes_checked = self._check_notes(order, eligible, rules)
        return response

    def _check_notes(
        self, order: StructuredOrder, eligible: list[str], rules: RuleSet
    ) -> tuple[list[NoteWarningOut], bool]:
        """Ask Jev whether each Eligible carrier's note matters for this Order. Informational only."""
        notes = {name: self._notes[name] for name in eligible if self._notes.get(name)}
        if not notes:
            return [], True
        if self._interpreter is None:
            return [], False
        try:
            probabilities = self._interpreter.assess_notes(order.model_dump(), notes)
        except InterpreterUnavailable:
            return [], False
        threshold = rules.thresholds.note_warning
        warnings = [
            NoteWarningOut(carrier=name, note=notes[name], probability=p)
            for name, p in probabilities.items()
            if name in notes and p >= threshold
        ]
        return warnings, True

    def _record(self, request: SelectCarrierRequest, rules: RuleSet, response: SelectionResponse) -> SelectionResponse:
        row = Selection(
            input_kind="structured" if request.text is None else "text",
            input=request.model_dump(mode="json", exclude_none=True),
            status=response.status,
            selected_carrier_name=response.selected_carrier.name if response.selected_carrier else None,
            total_cost=response.total_cost,
            route_miles=response.distance.miles if response.distance else None,
            ranking_used=rules.enabled_ranking,
            response={},
        )
        self._session.add(row)
        self._session.flush()  # assigns row.id, which the stored response must carry too
        response.selection_id = row.id
        row.response = response.model_dump(mode="json")
        self._session.commit()
        return response

    def _known_cities(self) -> list[str]:
        """Cities Jev may choose from: the case table, every carrier HQ and every cached route end."""
        cities = set(CASE_CITIES)
        cities.update(normalize_city(c) for c in self._session.exec(select(Carrier.headquarters_city)).all())
        for a, b in self._session.exec(select(DistanceCache.city_a, DistanceCache.city_b)).all():
            cities.update((a, b))
        return sorted(cities)

    def _hq_distance(self, hq_city: str, origin: str) -> Decimal | None:
        distance = self._distances.get(hq_city, origin)
        return distance.miles if distance else None

    def _load_carriers(self) -> list[CarrierSpec]:
        rows = self._session.exec(select(Carrier).order_by(Carrier.name)).all()
        # Carrier notes stay out of the engine (they are never Constraints); only _check_notes reads them.
        self._notes = {row.name: (row.description or "").strip() for row in rows}
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


def _review_gate(interpretation: Interpretation, threshold: float) -> tuple[ConfidenceOut, list[str]]:
    """Deterministic: a field is accepted only with a concrete value and a confidence at or above the threshold."""
    fields: dict[str, FieldConfidenceOut] = {}
    uncertain: list[str] = []
    for name, r in interpretation.fields().items():
        accepted = (
            r.value is not None and r.value not in SENTINELS and r.confidence is not None and r.confidence >= threshold
        )
        fields[name] = FieldConfidenceOut(value=r.value, confidence=r.confidence, accepted=accepted)
        if not accepted:
            uncertain.append(name)
    confidences = [f.confidence for f in fields.values()]
    weakest = None if any(c is None for c in confidences) else min(confidences)
    return ConfidenceOut(source="text", min=weakest, fields=fields), uncertain
