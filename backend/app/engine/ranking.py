"""Ranking criteria: order the Eligible carriers. For every criterion a smaller key is better.

To add a criterion (e.g. reliability): write a class like these, add it to RANKING_CRITERIA,
and add its name to rules.yaml. Nothing else changes.
"""

from decimal import Decimal
from typing import Protocol

from app import messages
from app.engine.types import Candidate, OrderContext


class RankingCriterion(Protocol):
    name: str
    label: str

    def key(self, cand: Candidate) -> tuple:
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

    def key(self, cand: Candidate) -> tuple:
        return (cand.total_cost,)

    def explain_loss(self, cand: Candidate, winner: Candidate, ctx: OrderContext) -> str:
        return messages.cost_higher_by(cand.total_cost - winner.total_cost)

    def describe(self, cand: Candidate, ctx: OrderContext) -> str:
        return messages.money(cand.total_cost)


class HqProximityCriterion:
    """Distance from the carrier's HQ to the Order's origin. Unknown distances rank last."""

    name = "hq_proximity"
    label = "Merkez yakınlığı"

    def key(self, cand: Candidate) -> tuple:
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


RANKING_CRITERIA: dict[str, RankingCriterion] = {
    c.name: c for c in (TotalCostCriterion(), HqProximityCriterion())
}
