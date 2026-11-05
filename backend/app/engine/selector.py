"""The selection engine: Constraints → total cost → ranking → reasons. Pure and deterministic."""

from decimal import ROUND_HALF_UP, Decimal

from app import messages
from app.engine.constraints import CONSTRAINTS
from app.engine.ranking import RANKING_CRITERIA, RankingCriterion
from app.engine.types import (
    Candidate,
    CarrierSpec,
    EngineOutcome,
    OrderContext,
    Outranked,
    Rejection,
)

CENTS = Decimal("0.01")


def select_carrier(
    carriers: list[CarrierSpec],
    ctx: OrderContext,
    constraint_names: list[str],
    ranking_names: list[str],
) -> EngineOutcome:
    """Pick the best carrier for the Order in `ctx` using the given (already validated) rule names."""
    constraints = [CONSTRAINTS[name] for name in constraint_names]
    criteria = [RANKING_CRITERIA[name] for name in ranking_names]

    candidates: list[Candidate] = []
    rejected: list[Rejection] = []
    for carrier in carriers:
        reasons = [r for c in constraints if (r := c.check(carrier, ctx)) is not None]
        if reasons:
            rejected.append(Rejection(carrier, reasons))
        else:
            candidates.append(_to_candidate(carrier, ctx))

    if not candidates:
        return EngineOutcome(None, [], rejected, messages.NO_ELIGIBLE_CARRIER)

    # The carrier name is the last key, so the result never depends on insertion order.
    ranked = sorted(candidates, key=lambda c: (*(k for crit in criteria for k in crit.key(c)), c.carrier.name))
    winner, rest = ranked[0], ranked[1:]
    outranked = [Outranked(c, _explain_loss(c, winner, criteria, ctx)) for c in rest]
    reason = _explain_win(winner, rest[0] if rest else None, criteria, ctx)
    return EngineOutcome(winner, outranked, rejected, reason)


def _to_candidate(carrier: CarrierSpec, ctx: OrderContext) -> Candidate:
    total = (ctx.route_miles * carrier.price_per_mile).quantize(CENTS, rounding=ROUND_HALF_UP)
    return Candidate(carrier, total, ctx.hq_distance(carrier.headquarters_city, ctx.order.origin))


def _deciding_criterion(a: Candidate, b: Candidate, criteria: list[RankingCriterion]) -> RankingCriterion | None:
    """The first criterion on which a and b differ, or None if they tie on all of them."""
    return next((c for c in criteria if c.key(a) != c.key(b)), None)


def _explain_loss(cand: Candidate, winner: Candidate, criteria: list[RankingCriterion], ctx: OrderContext) -> str:
    deciding = _deciding_criterion(cand, winner, criteria)
    if deciding is None:
        return messages.LOST_ON_NAME
    return deciding.explain_loss(cand, winner, ctx)


def _explain_win(
    winner: Candidate,
    runner_up: Candidate | None,
    criteria: list[RankingCriterion],
    ctx: OrderContext,
) -> str:
    name = winner.carrier.name
    if runner_up is None:
        return messages.only_eligible(name, winner.total_cost)

    deciding = _deciding_criterion(winner, runner_up, criteria)
    ties = criteria[: criteria.index(deciding)] if deciding else criteria
    tie_parts = [messages.tie_on(c.label, c.describe(winner, ctx)) for c in ties]
    if deciding is None:
        return messages.won_on_name(name, runner_up.carrier.name, tie_parts)
    return messages.won_on(
        name,
        runner_up.carrier.name,
        deciding.label,
        deciding.describe(winner, ctx),
        deciding.describe(runner_up, ctx),
        tie_parts,
    )
