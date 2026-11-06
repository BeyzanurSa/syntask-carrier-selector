"""Ranking criteria: order the Eligible carriers. For every criterion a smaller key is better.

To add a criterion: write a class like these, add it to RANKING_CRITERIA, and add its name to
rules.yaml (or switch it on in the Kurallar page). Nothing else changes; extra carrier data such
as reliability lives in the carrier's `attributes`, so no schema change is needed either.
Unknown values always rank last on their criterion instead of being guessed.
"""

from decimal import Decimal
from typing import Protocol

from app import messages
from app.engine.types import Candidate, OrderContext


class RankingCriterion(Protocol):
    name: str
    label: str

    def key(self, cand: Candidate, ctx: OrderContext) -> tuple:
        """Sort key; smaller ranks higher."""
        ...

    def explain_loss(self, cand: Candidate, winner: Candidate, ctx: OrderContext) -> str:
        """Why `cand` ranked below `winner` on this criterion."""
        ...

    def describe(self, cand: Candidate, ctx: OrderContext) -> str:
        """The candidate's value on this criterion, for reason texts."""
        ...


class TotalCostCriterion:
    name = "total_cost"
    label = "Toplam ücret"

    def key(self, cand: Candidate, ctx: OrderContext) -> tuple:
        return (cand.total_cost,)

    def explain_loss(self, cand: Candidate, winner: Candidate, ctx: OrderContext) -> str:
        return messages.cost_higher_by(cand.total_cost - winner.total_cost)

    def describe(self, cand: Candidate, ctx: OrderContext) -> str:
        return messages.money(cand.total_cost)


class HqProximityCriterion:
    """Distance from the carrier's HQ to the Order's origin. Unknown distances rank last."""

    name = "hq_proximity"
    label = "Merkez yakınlığı"

    def key(self, cand: Candidate, ctx: OrderContext) -> tuple:
        unknown = cand.hq_miles is None
        return (unknown, cand.hq_miles if not unknown else Decimal(0))

    def explain_loss(self, cand: Candidate, winner: Candidate, ctx: OrderContext) -> str:
        if cand.hq_miles is None:
            return messages.HQ_DISTANCE_UNKNOWN
        return messages.hq_farther_by(ctx.order.origin, cand.hq_miles - winner.hq_miles)

    def describe(self, cand: Candidate, ctx: OrderContext) -> str:
        if cand.hq_miles is None:
            return messages.HQ_DISTANCE_UNKNOWN_SHORT
        return messages.miles(cand.hq_miles)


class ReliabilityCriterion:
    """The carrier's reliability score (attributes["reliability"], 0–1). Higher is better; no score ranks last."""

    name = "reliability"
    label = "Güvenilirlik"

    @staticmethod
    def _score(cand: Candidate) -> float | None:
        value = cand.carrier.attributes.get("reliability")
        return float(value) if isinstance(value, int | float) else None

    def key(self, cand: Candidate, ctx: OrderContext) -> tuple:
        score = self._score(cand)
        return (score is None, -(score or 0.0))

    def explain_loss(self, cand: Candidate, winner: Candidate, ctx: OrderContext) -> str:
        score = self._score(cand)
        if score is None:
            return messages.RELIABILITY_MISSING
        return messages.reliability_lower_by(self._score(winner) - score)

    def describe(self, cand: Candidate, ctx: OrderContext) -> str:
        score = self._score(cand)
        return messages.RELIABILITY_MISSING_SHORT if score is None else messages.percent(score)


class HqToDestinationCriterion:
    """Distance from the carrier's HQ to the Order's destination: a short empty return leg. Unknown ranks last."""

    name = "hq_to_destination"
    label = "Dönüş yakınlığı"

    @staticmethod
    def _miles(cand: Candidate, ctx: OrderContext) -> Decimal | None:
        return ctx.hq_distance(cand.carrier.headquarters_city, ctx.order.destination)

    def key(self, cand: Candidate, ctx: OrderContext) -> tuple:
        miles = self._miles(cand, ctx)
        return (miles is None, miles if miles is not None else Decimal(0))

    def explain_loss(self, cand: Candidate, winner: Candidate, ctx: OrderContext) -> str:
        miles = self._miles(cand, ctx)
        if miles is None:
            return messages.return_distance_unknown(ctx.order.destination)
        return messages.return_farther_by(ctx.order.destination, miles - self._miles(winner, ctx))

    def describe(self, cand: Candidate, ctx: OrderContext) -> str:
        miles = self._miles(cand, ctx)
        return messages.HQ_DISTANCE_UNKNOWN_SHORT if miles is None else messages.miles(miles)


RANKING_CRITERIA: dict[str, RankingCriterion] = {
    c.name: c
    for c in (TotalCostCriterion(), HqProximityCriterion(), ReliabilityCriterion(), HqToDestinationCriterion())
}
