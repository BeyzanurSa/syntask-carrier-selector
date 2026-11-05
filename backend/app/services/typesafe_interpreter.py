"""Interpreter adapter for Jev (TypeSafe System One). See ADR 0001.

One `system_one` request per Order, with one Choice question per field (the "fan-out" pattern
from the TypeSafe docs). Every question offers `unspecified`, so Jev can say the text does not
mention a field instead of being forced to pick a value; city questions also offer `other_city`.
This adapter only reports Jev's choice and confidence; the review gate lives in SelectionService.

Carrier notes are checked with one Noul question per note ("does this note matter for this
Order?"); the yes-probability is returned as is and SelectionService compares it to the threshold.
"""

from typesafe_sdk import Choice, Noul, TypeSafeClient, TypeSafeError

from app.core.config import Settings
from app.services.interpreter import (
    OTHER_CITY,
    UNSPECIFIED,
    FieldReading,
    Interpretation,
    InterpreterUnavailable,
)

_UNSPECIFIED_TEXT = "The order does not say this."

SIZE_CRITERIA = {
    "20": "A 20-foot container (also written 20', 20 ft, 20'lik, twenty-foot).",
    "40": "A 40-foot container (also written 40', 40 ft, 40'lık, forty-foot).",
    "45": "A 45-foot container (also written 45', 45 ft, 45'lik).",
    UNSPECIFIED: _UNSPECIFIED_TEXT,
}

CARGO_CRITERIA = {
    "Dry": "General dry cargo, no temperature control (kuru yük, genel kargo).",
    "Reefer": "Refrigerated or temperature-controlled cargo (soğutmalı, frigorifik, reefer).",
    "Hazardous": "Dangerous goods (tehlikeli madde, ADR/IMO, hazmat).",
    UNSPECIFIED: _UNSPECIFIED_TEXT,
}

INSTRUCTIONS = {
    "origin": "This is a container transport order, possibly in Turkish. Which city does the shipment start from?",
    "destination": "This is a container transport order, possibly in Turkish. Which city is the shipment going to?",
    "container_size": "This is a container transport order, possibly in Turkish. What container size is requested?",
    "cargo_type": "This is a container transport order, possibly in Turkish. What type of cargo is it?",
}


def build_questions(known_cities: list[str]) -> dict[str, Choice]:
    city_criteria = {city: None for city in known_cities}
    city_criteria[OTHER_CITY] = "The order names a city that is not in this list."
    city_criteria[UNSPECIFIED] = _UNSPECIFIED_TEXT
    return {
        "origin": Choice(instructions=INSTRUCTIONS["origin"], criteria=city_criteria),
        "destination": Choice(instructions=INSTRUCTIONS["destination"], criteria=city_criteria),
        "container_size": Choice(instructions=INSTRUCTIONS["container_size"], criteria=SIZE_CRITERIA),
        "cargo_type": Choice(instructions=INSTRUCTIONS["cargo_type"], criteria=CARGO_CRITERIA),
    }


def describe_order(order: dict) -> str:
    return (
        f"Container transport order: from {order['origin']} to {order['destination']}, "
        f"{order['container_size']}-foot container, {order['cargo_type']} cargo."
    )


def note_question(note: str) -> Noul:
    return Noul(
        instructions=(
            "A carrier wrote this note about its service (it may be in Turkish): "
            f"\"{note}\". Does the note state a restriction, exclusion, extra charge or operational risk "
            "that applies to the order described in the state?"
        )
    )


class TypeSafeInterpreter:
    def __init__(self, client: TypeSafeClient):
        self._client = client

    @classmethod
    def from_settings(cls, settings: Settings) -> "TypeSafeInterpreter":
        return cls(
            TypeSafeClient(
                api_key=settings.typesafe_api_key.get_secret_value(),
                model=settings.jev_model,
                timeout=settings.jev_timeout_seconds,
            )
        )

    def interpret(self, text: str, known_cities: list[str]) -> Interpretation:
        try:
            response = self._client.system_one(state=text, questions=build_questions(known_cities))
        except TypeSafeError as error:
            # Never include the error text: it may echo request details. The type is enough to debug.
            raise InterpreterUnavailable(type(error).__name__) from error

        def read(name: str) -> FieldReading:
            answer = response.choices.get(name)
            if answer is None:
                return FieldReading(value=None, confidence=None)
            return FieldReading(value=answer.choice, confidence=answer.confidence)

        return Interpretation(
            origin=read("origin"),
            destination=read("destination"),
            container_size=read("container_size"),
            cargo_type=read("cargo_type"),
        )

    def assess_notes(self, order: dict, notes: dict[str, str]) -> dict[str, float]:
        # Question keys must be simple ids; map them back to carrier names afterwards.
        keys = {f"note_{i}": name for i, name in enumerate(notes)}
        questions = {key: note_question(notes[name]) for key, name in keys.items()}
        try:
            response = self._client.system_one(state=describe_order(order), questions=questions)
        except TypeSafeError as error:
            raise InterpreterUnavailable(type(error).__name__) from error
        return {name: response.nouls[key].noul for key, name in keys.items() if key in response.nouls}
