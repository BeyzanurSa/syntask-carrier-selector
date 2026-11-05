"""Carrier notes raise Note warnings through Jev, but never change the decision (ADR 0001)."""

from tests.conftest import FakeInterpreter, select

NOTE = "Hafta sonu teslimat yapmıyoruz; Orlando hattında araç sıkıntısı var."


def set_note(client, name: str, note: str | None) -> None:
    carrier = next(c for c in client.get("/carriers").json() if c["name"] == name)
    body = {k: v for k, v in carrier.items() if k not in ("id", "created_at", "updated_at")}
    assert client.put(f"/carriers/{carrier['id']}", json={**body, "description": note}).status_code == 200


def test_relevant_note_raises_a_warning_without_changing_the_selection(make_client):
    interpreter = FakeInterpreter(note_probabilities={"S-Logistics": 0.91})
    client = make_client(interpreter=interpreter)
    set_note(client, "S-Logistics", NOTE)

    result = select(client, "Miami", "Orlando", 40, "Dry")

    assert result["selected_carrier"]["name"] == "S-Logistics"
    assert result["total_cost"] == "94.00"
    assert result["warnings"] == [{"carrier": "S-Logistics", "note": NOTE, "probability": 0.91}]
    assert result["notes_checked"] is True


def test_note_below_the_threshold_raises_no_warning(make_client):
    client = make_client(interpreter=FakeInterpreter(note_probabilities={"S-Logistics": 0.4}))
    set_note(client, "S-Logistics", NOTE)

    result = select(client, "Miami", "Orlando", 40, "Dry")

    assert result["warnings"] == []
    assert result["notes_checked"] is True


def test_only_eligible_carriers_with_notes_are_sent_to_jev(make_client):
    interpreter = FakeInterpreter()
    client = make_client(interpreter=interpreter)
    set_note(client, "S-Logistics", NOTE)
    set_note(client, "A-Logistics", "Sadece Jacksonville çıkışlı.")  # A is rejected for this Order

    select(client, "Miami", "Orlando", 40, "Dry")

    order, notes = interpreter.note_calls[0]
    assert notes == {"S-Logistics": NOTE}
    assert order == {"origin": "Miami", "destination": "Orlando", "container_size": 40, "cargo_type": "Dry"}


def test_no_notes_means_no_jev_call_and_nothing_left_unchecked(make_client):
    interpreter = FakeInterpreter()
    client = make_client(interpreter=interpreter)

    result = select(client, "Miami", "Orlando", 40, "Dry")

    assert interpreter.note_calls == []
    assert result["warnings"] == []
    assert result["notes_checked"] is True


def test_failed_note_check_still_selects_and_says_notes_were_not_checked(make_client):
    client = make_client(interpreter=FakeInterpreter(notes_fail=True))
    set_note(client, "S-Logistics", NOTE)

    result = select(client, "Miami", "Orlando", 40, "Dry")

    assert result["status"] == "selected"
    assert result["warnings"] == []
    assert result["notes_checked"] is False


def test_notes_are_not_checked_without_an_interpreter(client):
    set_note(client, "S-Logistics", NOTE)

    result = select(client, "Miami", "Orlando", 40, "Dry")

    assert result["selected_carrier"]["name"] == "S-Logistics"
    assert result["notes_checked"] is False


def test_note_warning_threshold_comes_from_rules_yaml(make_client):
    client = make_client(interpreter=FakeInterpreter(note_probabilities={"S-Logistics": 0.5}))
    set_note(client, "S-Logistics", NOTE)
    rules = client.get("/rules").json()
    rules["thresholds"]["note_warning"] = 0.5
    client.put("/rules", json={k: rules[k] for k in ("constraints", "ranking", "thresholds")})

    assert [w["carrier"] for w in select(client, "Miami", "Orlando", 40, "Dry")["warnings"]] == ["S-Logistics"]


def test_outranked_carriers_notes_are_checked_too(make_client):
    interpreter = FakeInterpreter(note_probabilities={"M-Logistics": 0.8})
    client = make_client(interpreter=interpreter)
    set_note(client, "M-Logistics", "Florida içinde ek ücret uyguluyoruz.")

    result = select(client, "Miami", "Orlando", 40, "Dry")

    assert result["selected_carrier"]["name"] == "S-Logistics"
    assert [w["carrier"] for w in result["warnings"]] == ["M-Logistics"]
