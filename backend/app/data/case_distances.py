"""Distances given in the case (approximate road miles). Symmetric; these always win over any other source."""

from decimal import Decimal

CASE_DISTANCES: dict[frozenset[str], Decimal] = {
    frozenset(pair): Decimal(miles)
    for pair, miles in [
        (("Miami", "Fort Lauderdale"), 30),
        (("Miami", "Orlando"), 235),
        (("Miami", "Atlanta"), 660),
        (("Jacksonville", "Savannah"), 140),
        (("Tampa", "Jacksonville"), 200),
        (("Miami", "Houston"), 1190),
        (("Tampa", "Orlando"), 85),
    ]
}
