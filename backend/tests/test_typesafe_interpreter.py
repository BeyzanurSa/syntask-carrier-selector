"""Adapter test for the Jev interpreter, with the SDK client stubbed (no network, no key)."""

import pytest
from typesafe_sdk import Choice, SystemOneResponse, TypeSafeAPIConnectionError, TypeSafeAPITimeoutError

from app.services.interpreter import FieldReading, InterpreterUnavailable
from app.services.typesafe_interpreter import TypeSafeInterpreter

CITIES = ["Atlanta", "Miami", "Orlando"]


def choice(label: str, confidence: float) -> dict:
    return {"type": "choice", "choice": label, "confidence": confidence, "probabilities": {label: confidence}}


class StubClient:
    def __init__(self, answers: dict | None = None, error: Exception | None = None):
        self.answers = answers or {}
        self.error = error
        self.requests: list[dict] = []

    def system_one(self, state, questions):
        self.requests.append({"state": state, "questions": questions})
        if self.error:
            raise self.error
        return SystemOneResponse.model_validate(
            {"model": "jev-test", "usage": {"input_tokens": 1, "output_tokens": 1}, "answers": self.answers}
        )


def test_one_request_with_one_choice_question_per_field():
    client = StubClient(
        {
            "origin": choice("Miami", 0.98),
            "destination": choice("Orlando", 0.97),
            "container_size": choice("40", 0.81),
            "cargo_type": choice("Dry", 0.9),
        }
    )

    result = TypeSafeInterpreter(client).interpret("Miami'den Orlando'ya 40'lık kuru yük", CITIES)

    assert result.origin == FieldReading("Miami", 0.98)
    assert result.container_size == FieldReading("40", 0.81)
    assert len(client.requests) == 1
    request = client.requests[0]
    assert request["state"] == "Miami'den Orlando'ya 40'lık kuru yük"
    questions = request["questions"]
    assert set(questions) == {"origin", "destination", "container_size", "cargo_type"}
    assert all(isinstance(q, Choice) for q in questions.values())


def test_every_question_offers_unspecified_and_cities_also_offer_other_city():
    client = StubClient({})
    TypeSafeInterpreter(client).interpret("text", CITIES)

    questions = client.requests[0]["questions"]
    assert set(questions["origin"].criteria) == {*CITIES, "other_city", "unspecified"}
    assert set(questions["container_size"].criteria) == {"20", "40", "45", "unspecified"}
    assert set(questions["cargo_type"].criteria) == {"Dry", "Reefer", "Hazardous", "unspecified"}


def test_missing_answer_becomes_a_reading_without_value_or_confidence():
    result = TypeSafeInterpreter(StubClient({"origin": choice("Miami", 0.9)})).interpret("text", CITIES)

    assert result.destination == FieldReading(None, None)


@pytest.mark.parametrize("error", [TypeSafeAPIConnectionError("no network"), TypeSafeAPITimeoutError(20.0)])
def test_sdk_errors_become_interpreter_unavailable(error):
    with pytest.raises(InterpreterUnavailable):
        TypeSafeInterpreter(StubClient(error=error)).interpret("text", CITIES)
