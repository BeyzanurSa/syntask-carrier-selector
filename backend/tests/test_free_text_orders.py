"""Free-text Orders: Jev interprets, deterministic code applies the review gate (ADR 0001)."""

import pytest

from tests.conftest import FakeInterpreter, interpretation, reading, select

TEXT = "Miami'den Orlando'ya 40'lık kuru yük konteyneri taşınacak."


def select_text(client, text: str = TEXT) -> dict:
    response = client.post("/select-carrier", json={"text": text})
    assert response.status_code == 200, response.text
    return response.json()


def test_confident_interpretation_selects_a_carrier_and_reports_field_confidence(make_client):
    interpreter = FakeInterpreter(interpretation(container_size=reading("40", 0.81)))
    client = make_client(interpreter=interpreter)

    result = select_text(client)

    assert result["status"] == "selected"
    assert result["selected_carrier"]["name"] == "S-Logistics"
    assert result["order"] == {"origin": "Miami", "destination": "Orlando", "container_size": 40, "cargo_type": "Dry"}
    assert result["confidence"]["source"] == "text"
    assert result["confidence"]["min"] == 0.81
    assert result["confidence"]["fields"]["container_size"] == {"value": "40", "confidence": 0.81, "accepted": True}
    assert result["review"] is None
    assert interpreter.calls[0][0] == TEXT


def test_low_confidence_field_sends_the_order_to_review_without_assigning(make_client):
    client = make_client(interpreter=FakeInterpreter(interpretation(container_size=reading("40", 0.4))))

    result = select_text(client)

    assert result["status"] == "needs_review"
    assert result["selected_carrier"] is None
    assert result["order"] is None
    assert result["review"]["fields"] == ["container_size"]
    assert result["review"]["suggestions"] == {
        "origin": "Miami",
        "destination": "Orlando",
        "container_size": "40",
        "cargo_type": "Dry",
    }
    assert "Konteyner" in result["review"]["question"]
    assert result["confidence"]["fields"]["container_size"]["accepted"] is False


def test_unspecified_field_goes_to_review_even_with_high_confidence(make_client):
    client = make_client(interpreter=FakeInterpreter(interpretation(container_size=reading("unspecified", 0.99))))

    result = select_text(client)

    assert result["status"] == "needs_review"
    assert result["review"]["fields"] == ["container_size"]
    assert "container_size" not in result["review"]["suggestions"]


def test_city_outside_the_known_list_goes_to_review(make_client):
    client = make_client(interpreter=FakeInterpreter(interpretation(origin=reading("other_city", 0.97))))

    result = select_text(client, "Tallahassee'den Orlando'ya 40'lık kuru yük")

    assert result["status"] == "needs_review"
    assert result["review"]["fields"] == ["origin"]


def test_missing_confidence_is_treated_as_low(make_client):
    client = make_client(interpreter=FakeInterpreter(interpretation(cargo_type=reading("Dry", None))))

    result = select_text(client)

    assert result["status"] == "needs_review"
    assert result["review"]["fields"] == ["cargo_type"]


def test_threshold_comes_from_rules_yaml(make_client):
    client = make_client(interpreter=FakeInterpreter(interpretation(container_size=reading("40", 0.4))))
    rules = client.get("/rules").json()
    rules["thresholds"]["field_confidence"] = 0.3
    client.put("/rules", json={k: rules[k] for k in ("constraints", "ranking", "thresholds")})

    assert select_text(client)["status"] == "selected"


def test_interpreter_failure_reports_jev_unavailable_but_structured_orders_still_work(make_client):
    client = make_client(interpreter=FakeInterpreter(fail=True))

    result = select_text(client)

    assert result["status"] == "jev_unavailable"
    assert result["selected_carrier"] is None
    assert select(client, "Miami", "Orlando", 40, "Dry")["status"] == "selected"


def test_text_order_without_a_configured_interpreter_is_jev_unavailable(client):
    assert select_text(client)["status"] == "jev_unavailable"


def test_structured_orders_report_structured_confidence(client):
    result = select(client, "Miami", "Orlando", 40, "Dry")

    assert result["confidence"] == {"source": "structured", "min": None, "fields": {}}


def test_known_cities_include_carrier_headquarters(make_client):
    interpreter = FakeInterpreter(interpretation())
    client = make_client(interpreter=interpreter)
    client.post(
        "/carriers",
        json={
            "name": "Bos-Logistics",
            "headquarters_city": "Boston",
            "supported_container_sizes": [40],
            "supported_cargo_types": ["Dry"],
            "price_per_mile": "1.00",
        },
    )

    select_text(client)

    known = interpreter.calls[0][1]
    assert {"Miami", "Orlando", "Houston", "Boston"} <= set(known)


def test_text_selection_is_recorded_with_its_text_input(make_client):
    client = make_client(interpreter=FakeInterpreter(interpretation(container_size=reading("40", 0.4))))

    result = select_text(client)

    record = client.get(f"/selections/{result['selection_id']}").json()
    assert record["input_kind"] == "text"
    assert record["input"] == {"text": TEXT}
    summary = client.get("/selections").json()[0]
    assert summary["status"] == "needs_review"
    assert summary["input_text"] == TEXT


@pytest.mark.parametrize(
    "body",
    [
        {"text": TEXT, "origin": "Miami", "destination": "Orlando", "container_size": 40, "cargo_type": "Dry"},
        {},
        {"text": "   "},
        {"origin": "Miami", "destination": "Orlando"},
    ],
)
def test_request_must_be_exactly_one_complete_form(client, body):
    assert client.post("/select-carrier", json=body).status_code == 422
