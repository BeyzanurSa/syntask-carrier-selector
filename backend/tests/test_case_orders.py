"""The seven test Orders given in the case, with their expected results."""

import pytest

from tests.conftest import select


@pytest.mark.parametrize(
    ("origin", "destination", "size", "cargo", "carrier", "cost"),
    [
        ("Miami", "Fort Lauderdale", 40, "Reefer", "M-Logistics", "30.00"),
        ("Miami", "Orlando", 40, "Dry", "S-Logistics", "94.00"),
        ("Miami", "Atlanta", 20, "Reefer", "B-Logistics", "660.00"),
        ("Jacksonville", "Savannah", 45, "Hazardous", "A-Logistics", "280.00"),
        ("Tampa", "Jacksonville", 45, "Dry", "S-Logistics", "80.00"),
        ("Tampa", "Orlando", 20, "Hazardous", "M-Logistics", "85.00"),
    ],
)
def test_case_order_selects_expected_carrier(client, origin, destination, size, cargo, carrier, cost):
    result = select(client, origin, destination, size, cargo)

    assert result["status"] == "selected"
    assert result["selected_carrier"]["name"] == carrier
    assert result["total_cost"] == cost
    assert result["distance"]["source"] == "table"


def test_case_order_3_tie_on_cost_goes_to_closer_headquarters(client):
    result = select(client, "Miami", "Atlanta", 20, "Reefer")

    assert result["selected_carrier"]["name"] == "B-Logistics"
    assert result["selected_carrier"]["hq_distance"] == "30"
    runner_up = result["eligible_carriers"][0]
    assert runner_up["name"] == "M-Logistics"
    assert runner_up["total_cost"] == "660.00"
    assert runner_up["hq_distance"] == "1190"
    assert "Merkez" in runner_up["lost_on"]


def test_case_order_6_has_no_eligible_carrier_and_explains_every_rejection(client):
    result = select(client, "Miami", "Houston", 45, "Reefer")

    assert result["status"] == "no_carrier"
    assert result["selected_carrier"] is None
    assert result["total_cost"] is None
    assert result["eligible_carriers"] == []
    rejected = {c["name"]: c["reasons"] for c in result["rejected_carriers"]}
    assert set(rejected) == {"S-Logistics", "B-Logistics", "A-Logistics", "M-Logistics"}
    # All failed Constraints are listed, not only the first: S takes 45 ft but fails distance and cargo.
    assert len(rejected["S-Logistics"]) == 2
    assert any("45 ft" in reason for reason in rejected["M-Logistics"])
    assert any("Reefer" in reason for reason in rejected["A-Logistics"])


def test_outranked_carrier_shows_why_it_lost_on_cost(client):
    result = select(client, "Miami", "Orlando", 40, "Dry")

    outranked = {c["name"]: c for c in result["eligible_carriers"]}
    assert outranked["M-Logistics"]["total_cost"] == "235.00"
    assert "141.00" in outranked["M-Logistics"]["lost_on"]
