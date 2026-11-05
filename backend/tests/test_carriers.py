"""Carrier management through the API, and its effect on the next selection."""

import pytest

from tests.conftest import select

NEW_CARRIER = {
    "name": "Z-Logistics",
    "headquarters_city": "Miami",
    "min_distance": None,
    "max_distance": None,
    "supported_container_sizes": [40],
    "supported_cargo_types": ["Dry"],
    "price_per_mile": "0.30",
    "is_active": True,
    "description": "Yeni ortak",
    "attributes": {"reliability": 0.9},
}


def carrier_id(client, name: str) -> int:
    return next(c["id"] for c in client.get("/carriers").json() if c["name"] == name)


def test_seeded_case_carriers_are_listed(client):
    carriers = client.get("/carriers").json()

    assert [c["name"] for c in carriers] == ["A-Logistics", "B-Logistics", "M-Logistics", "S-Logistics"]
    s = next(c for c in carriers if c["name"] == "S-Logistics")
    assert s["max_distance"] == 300
    assert s["price_per_mile"] == "0.40"


def test_new_carrier_is_used_in_the_next_selection(client):
    created = client.post("/carriers", json=NEW_CARRIER)
    assert created.status_code == 201
    assert created.json()["attributes"] == {"reliability": 0.9}

    result = select(client, "Miami", "Orlando", 40, "Dry")

    assert result["selected_carrier"]["name"] == "Z-Logistics"
    assert result["total_cost"] == "70.50"


def test_empty_max_distance_means_unlimited(client):
    client.post("/carriers", json=NEW_CARRIER)

    result = select(client, "Miami", "Houston", 40, "Dry")

    assert result["selected_carrier"]["name"] == "Z-Logistics"


def test_carrier_can_be_read_and_updated_including_its_note(client):
    s_id = carrier_id(client, "S-Logistics")
    carrier = client.get(f"/carriers/{s_id}").json()

    carrier["description"] = "Hafta sonu teslimat yapmıyoruz."
    carrier["price_per_mile"] = "0.50"
    updated = client.put(f"/carriers/{s_id}", json=carrier)

    assert updated.status_code == 200
    reread = client.get(f"/carriers/{s_id}").json()
    assert reread["description"] == "Hafta sonu teslimat yapmıyoruz."
    assert reread["price_per_mile"] == "0.50"
    assert select(client, "Miami", "Orlando", 40, "Dry")["total_cost"] == "117.50"


def test_inactive_carrier_is_rejected_as_inactive_and_never_selected(client):
    s_id = carrier_id(client, "S-Logistics")
    carrier = client.get(f"/carriers/{s_id}").json()
    client.put(f"/carriers/{s_id}", json={**carrier, "is_active": False})

    result = select(client, "Miami", "Orlando", 40, "Dry")

    assert result["selected_carrier"]["name"] == "M-Logistics"
    rejected = {c["name"]: c["reasons"] for c in result["rejected_carriers"]}
    assert "Firma pasif" in rejected["S-Logistics"]


def test_deleting_a_carrier_keeps_past_selections_readable(client):
    past = select(client, "Miami", "Orlando", 40, "Dry")
    s_id = carrier_id(client, "S-Logistics")

    assert client.delete(f"/carriers/{s_id}").status_code == 204

    assert "S-Logistics" not in [c["name"] for c in client.get("/carriers").json()]
    assert client.get(f"/carriers/{s_id}").status_code == 404
    reopened = client.get(f"/selections/{past['selection_id']}").json()
    assert reopened["response"]["selected_carrier"]["name"] == "S-Logistics"


def test_duplicate_name_is_a_conflict_on_create_and_update(client):
    duplicate = client.post("/carriers", json={**NEW_CARRIER, "name": "S-Logistics"})
    assert duplicate.status_code == 409

    b_id = carrier_id(client, "B-Logistics")
    b = client.get(f"/carriers/{b_id}").json()
    assert client.put(f"/carriers/{b_id}", json={**b, "name": "M-Logistics"}).status_code == 409


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_unknown_carrier_returns_404(client, method):
    kwargs = {"json": NEW_CARRIER} if method == "put" else {}

    assert getattr(client, method)("/carriers/999", **kwargs).status_code == 404


@pytest.mark.parametrize(
    "change",
    [
        {"name": "  "},
        {"headquarters_city": ""},
        {"price_per_mile": "0"},
        {"price_per_mile": "-1"},
        {"min_distance": 500, "max_distance": 100},
        {"min_distance": -5},
        {"supported_container_sizes": []},
        {"supported_container_sizes": [30]},
        {"supported_cargo_types": []},
        {"supported_cargo_types": ["Liquid"]},
    ],
)
def test_invalid_carrier_data_is_rejected_with_422(client, change):
    assert client.post("/carriers", json={**NEW_CARRIER, **change}).status_code == 422
