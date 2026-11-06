"""The reliability and return-leg (HQ → destination) Ranking criteria, switched on through the Rule set."""

import pytest

from tests.conftest import FakeDistanceProvider, select


def set_ranking(client, *names: str) -> None:
    rules = client.get("/rules").json()
    listed = [e["name"] for e in rules["ranking"]]
    ranking = [{"name": n, "enabled": True} for n in names]
    ranking += [{"name": n, "enabled": False} for n in listed if n not in names]
    response = client.put("/rules", json={"constraints": rules["constraints"], "ranking": ranking, "thresholds": rules["thresholds"]})
    assert response.status_code == 200, response.text


def set_reliability(client, name: str, value) -> None:
    carrier = next(c for c in client.get("/carriers").json() if c["name"] == name)
    body = {k: v for k, v in carrier.items() if k not in ("id", "created_at", "updated_at")}
    body["attributes"] = {**body["attributes"], "reliability": value}
    assert client.put(f"/carriers/{carrier['id']}", json=body).status_code == 200


def test_new_criteria_are_listed_but_off_by_default(client):
    ranking = client.get("/rules").json()["ranking"]

    assert ranking == [
        {"name": "total_cost", "enabled": True},
        {"name": "hq_proximity", "enabled": True},
        {"name": "reliability", "enabled": False},
        {"name": "hq_to_destination", "enabled": False},
    ]
    assert select(client, "Miami", "Orlando", 40, "Dry")["rules_used"] == ["total_cost", "hq_proximity"]


def test_more_reliable_carrier_wins_when_reliability_comes_first(client):
    set_reliability(client, "S-Logistics", 0.80)
    set_reliability(client, "M-Logistics", 0.95)
    set_ranking(client, "reliability", "total_cost")

    result = select(client, "Miami", "Orlando", 40, "Dry")

    assert result["selected_carrier"]["name"] == "M-Logistics"
    loser = result["eligible_carriers"][0]
    assert loser["name"] == "S-Logistics"
    assert "Güvenilirlik" in loser["lost_on"] and "15" in loser["lost_on"]
    assert "güvenilirlik" in result["reason"]


def test_carrier_without_a_reliability_score_ranks_last_on_it(client):
    set_reliability(client, "M-Logistics", 0.5)
    set_ranking(client, "reliability", "total_cost")

    result = select(client, "Miami", "Orlando", 40, "Dry")

    assert result["selected_carrier"]["name"] == "M-Logistics"
    assert "puanı yok" in result["eligible_carriers"][0]["lost_on"]


def test_return_leg_prefers_the_hq_closer_to_the_destination(make_client):
    # B and M tie on cost for Miami → Atlanta; Houston is closer to Atlanta than Fort Lauderdale here.
    client = make_client(
        FakeDistanceProvider({("Fort Lauderdale", "Atlanta"): 640, ("Houston", "Atlanta"): 500})
    )
    set_ranking(client, "total_cost", "hq_to_destination")

    result = select(client, "Miami", "Atlanta", 20, "Reefer")

    assert result["selected_carrier"]["name"] == "M-Logistics"
    assert "140" in result["eligible_carriers"][0]["lost_on"]
    assert "Atlanta" in result["eligible_carriers"][0]["lost_on"]


@pytest.mark.parametrize("value", [1.5, -0.1, "high"])
def test_reliability_must_be_a_number_between_0_and_1(client, value):
    carrier = client.get("/carriers").json()[0]
    body = {k: v for k, v in carrier.items() if k not in ("id", "created_at", "updated_at")}
    body["attributes"] = {"reliability": value}

    assert client.put(f"/carriers/{carrier['id']}", json=body).status_code == 422
