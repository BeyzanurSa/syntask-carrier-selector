"""The Interpreter port: reads a free-text Order into its fields (ADR 0001).

An Interpreter only reports what it read and how sure it is. Deciding whether that is good
enough (the review gate) is deterministic code in SelectionService, never the adapter.
"""

from dataclasses import dataclass
from typing import Protocol

UNSPECIFIED = "unspecified"  # the text does not say
OTHER_CITY = "other_city"  # the text names a city outside the known list
SENTINELS = frozenset({UNSPECIFIED, OTHER_CITY})

ORDER_FIELDS = ("origin", "destination", "container_size", "cargo_type")


class InterpreterUnavailable(Exception):
    """The interpreter could not be reached or failed (network, auth, rate limit, bad response)."""


@dataclass(frozen=True)
class FieldReading:
    value: str | None  # one of the offered options, or a sentinel
    confidence: float | None  # None when the interpreter gave no confidence


@dataclass(frozen=True)
class Interpretation:
    origin: FieldReading
    destination: FieldReading
    container_size: FieldReading  # "20" | "40" | "45" | sentinel
    cargo_type: FieldReading

    def fields(self) -> dict[str, FieldReading]:
        return {name: getattr(self, name) for name in ORDER_FIELDS}


class Interpreter(Protocol):
    def interpret(self, text: str, known_cities: list[str]) -> Interpretation:
        """Read the Order fields from text. Cities are chosen from `known_cities`. Raises InterpreterUnavailable."""
        ...
