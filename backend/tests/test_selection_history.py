"""Every selection is stored as an immutable Selection snapshot that can be listed and reopened."""

from tests.conftest import select


def test_each_selection_is_recorded_and_can_be_reopened(client):
    result = select(client, "Miami", "Orlando", 40, "Dry")

    assert isinstance(result["selection_id"], int)
    stored = client.get(f"/selections/{result['selection_id']}").json()
    assert stored["id"] == result["selection_id"]
    assert stored["status"] == "selected"
    assert stored["input"] == {
        "origin": "Miami",
        "destination": "Orlando",
        "container_size": 40,
        "cargo_types": ["Dry"],
    }
    assert stored["response"] == result
    assert stored["ranking_used"] == ["total_cost", "hq_proximity"]


def test_outcomes_without_a_carrier_are_recorded_too(client):
    no_carrier = select(client, "Miami", "Houston", 45, "Reefer")
    invalid = select(client, "Miami", "Miami", 40, "Dry")

    listed = {s["id"]: s["status"] for s in client.get("/selections").json()}
    assert listed[no_carrier["selection_id"]] == "no_carrier"
    assert listed[invalid["selection_id"]] == "invalid_order"


def test_selections_are_listed_newest_first_with_a_limit(client):
    first = select(client, "Miami", "Orlando", 40, "Dry")
    second = select(client, "Tampa", "Orlando", 20, "Hazardous")
    third = select(client, "Miami", "Atlanta", 20, "Reefer")

    listed = client.get("/selections", params={"limit": 2}).json()

    assert [s["id"] for s in listed] == [third["selection_id"], second["selection_id"]]
    assert listed[0]["selected_carrier_name"] == "B-Logistics"
    assert listed[0]["total_cost"] == "660.00"
    assert listed[0]["origin"] == "Miami"
    assert listed[0]["destination"] == "Atlanta"
    assert first["selection_id"] not in [s["id"] for s in listed]


def test_unknown_selection_returns_404(client):
    assert client.get("/selections/999").status_code == 404


def test_stored_selection_does_not_change_when_the_rules_change(client, rules_path):
    original = select(client, "Miami", "Orlando", 40, "Dry")
    assert original["selected_carrier"]["name"] == "S-Logistics"

    # Put HQ proximity before cost. Houston → Miami is known (1190 mi), Tampa → Miami is not,
    # so M-Logistics now wins the same Order.
    rules_path.write_text(
        rules_path.read_text(encoding="utf-8").replace(
            "  - name: total_cost\n    enabled: true\n  - name: hq_proximity\n    enabled: true",
            "  - name: hq_proximity\n    enabled: true\n  - name: total_cost\n    enabled: true",
        ),
        encoding="utf-8",
    )
    rerun = select(client, "Miami", "Orlando", 40, "Dry")

    assert rerun["selected_carrier"]["name"] == "M-Logistics"
    assert rerun["selection_id"] != original["selection_id"]
    reopened = client.get(f"/selections/{original['selection_id']}").json()
    assert reopened["response"]["selected_carrier"]["name"] == "S-Logistics"
    assert reopened["ranking_used"] == ["total_cost", "hq_proximity"]
