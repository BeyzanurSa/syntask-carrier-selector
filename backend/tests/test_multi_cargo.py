"""One container can need several cargo properties (e.g. refrigerated hazardous goods); a carrier must support all."""

import pytest
from sqlmodel import Session

from app.database.models import Selection


def select_types(client, origin, destination, size, cargo_types) -> dict:
    response = client.post(
        "/select-carrier",
        json={"origin": origin, "destination": destination, "container_size": size, "cargo_types": cargo_types},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_carrier_must_support_every_requested_cargo_type(client):
    result = select_types(client, "Miami", "Fort Lauderdale", 20, ["Reefer", "Hazardous"])

    # Only M-Logistics takes 20 ft with both Reefer and Hazardous.
    assert result["selected_carrier"]["name"] == "M-Logistics"
    assert result["order"]["cargo_types"] == ["Reefer", "Hazardous"]
    rejected = {c["name"]: c["reasons"] for c in result["rejected_carriers"]}
    assert any("Hazardous yük tipi desteklenmiyor" in r for r in rejected["B-Logistics"])
    assert not any(r.startswith("Reefer") for r in rejected["B-Logistics"])


def test_every_missing_cargo_type_is_its_own_reason(client):
    result = select_types(client, "Miami", "Fort Lauderdale", 40, ["Reefer", "Hazardous"])

    rejected = {c["name"]: c["reasons"] for c in result["rejected_carriers"]}
    s_reasons = [r for r in rejected["S-Logistics"] if "yük tipi" in r]
    assert len(s_reasons) == 2


def test_single_cargo_type_field_is_still_accepted(client):
    response = client.post(
        "/select-carrier",
        json={"origin": "Miami", "destination": "Orlando", "container_size": 40, "cargo_type": "Dry"},
    )

    assert response.json()["selected_carrier"]["name"] == "S-Logistics"
    assert response.json()["order"]["cargo_types"] == ["Dry"]


def test_duplicate_cargo_types_are_merged(client):
    result = select_types(client, "Miami", "Orlando", 40, ["Dry", "Dry"])

    assert result["order"]["cargo_types"] == ["Dry"]


@pytest.mark.parametrize("cargo_types", [[], ["Liquid"], ["Dry", "Liquid"]])
def test_empty_or_unknown_cargo_types_are_rejected(client, cargo_types):
    response = client.post(
        "/select-carrier",
        json={"origin": "Miami", "destination": "Orlando", "container_size": 40, "cargo_types": cargo_types},
    )

    assert response.status_code == 422


def test_snapshots_stored_with_the_old_single_cargo_field_still_open(client):
    old_order = {"origin": "Miami", "destination": "Orlando", "container_size": 40, "cargo_type": "Dry"}
    with Session(client.app.state.db_engine) as session:
        row = Selection(
            input_kind="structured",
            input=old_order,
            status="selected",
            selected_carrier_name="S-Logistics",
            ranking_used=["total_cost", "hq_proximity"],
            response={"selection_id": 1, "status": "selected", "order": old_order, "reason": "eski kayıt"},
        )
        session.add(row)
        session.commit()
        selection_id = row.id

    record = client.get(f"/selections/{selection_id}").json()
    assert record["response"]["order"]["cargo_types"] == ["Dry"]
    assert client.get("/selections").json()[0]["cargo_types"] == ["Dry"]
