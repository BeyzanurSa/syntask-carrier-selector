"""Constraint boundaries, tie-breaking, unknown routes and invalid Orders, through the HTTP API."""

import pytest

from tests.conftest import FakeDistanceProvider, select


def names(carriers: list[dict]) -> set[str]:
    return {c["name"] for c in carriers}


def eligible_names(result: dict) -> set[str]:
    winner = {result["selected_carrier"]["name"]} if result["selected_carrier"] else set()
    return winner | names(result["eligible_carriers"])


# --- Inclusive distance bounds -------------------------------------------------------------

def test_exactly_200_miles_is_within_a_200_mile_maximum(client):
    # Tampa → Jacksonville is 200 miles; A-Logistics accepts up to 200.
    result = select(client, "Tampa", "Jacksonville", 45, "Dry")

    assert "A-Logistics" in eligible_names(result)
    assert "A-Logistics" not in names(result["rejected_carriers"])


@pytest.mark.parametrize(("miles", "eligible"), [(249, False), (250, True)])
def test_250_mile_minimum_is_inclusive(make_client, miles, eligible):
    client = make_client(FakeDistanceProvider({("Testville", "Farville"): miles}))

    result = select(client, "Testville", "Farville", 20, "Dry")

    assert ("B-Logistics" in eligible_names(result)) is eligible


@pytest.mark.parametrize(("miles", "eligible"), [(300, True), (301, False)])
def test_300_mile_maximum_is_inclusive(make_client, miles, eligible):
    client = make_client(FakeDistanceProvider({("Testville", "Farville"): miles}))

    result = select(client, "Testville", "Farville", 40, "Dry")

    assert ("S-Logistics" in eligible_names(result)) is eligible
    if eligible:
        assert result["selected_carrier"]["name"] == "S-Logistics"
        assert result["total_cost"] == "120.00"


# --- Mismatches ------------------------------------------------------------------------------

def test_container_size_mismatch_rejects_carrier_with_reason(client):
    result = select(client, "Miami", "Orlando", 20, "Dry")

    rejected = {c["name"]: c["reasons"] for c in result["rejected_carriers"]}
    assert any("20 ft" in r for r in rejected["S-Logistics"])


def test_cargo_type_mismatch_rejects_carrier_with_reason(client):
    result = select(client, "Tampa", "Orlando", 40, "Hazardous")

    rejected = {c["name"]: c["reasons"] for c in result["rejected_carriers"]}
    assert any("Hazardous" in r for r in rejected["S-Logistics"])
    assert result["selected_carrier"]["name"] == "M-Logistics"


# --- Ties ------------------------------------------------------------------------------------

def test_tie_on_cost_and_hq_distance_goes_to_carrier_name(make_client):
    # B and M both charge $1.00/mile; both HQs are 100 miles from the origin.
    client = make_client(
        FakeDistanceProvider(
            {
                ("Testville", "Farville"): 400,
                ("Fort Lauderdale", "Testville"): 100,
                ("Houston", "Testville"): 100,
            }
        )
    )

    result = select(client, "Testville", "Farville", 20, "Dry")

    assert result["selected_carrier"]["name"] == "B-Logistics"
    assert result["eligible_carriers"][0]["name"] == "M-Logistics"
    assert "isim" in result["eligible_carriers"][0]["lost_on"]


def test_hq_in_the_origin_city_has_zero_hq_distance(client):
    result = select(client, "Tampa", "Jacksonville", 45, "Dry")

    assert result["selected_carrier"]["name"] == "S-Logistics"
    assert result["selected_carrier"]["hq_distance"] == "0"


def test_unknown_hq_distance_ranks_last_on_proximity(make_client):
    # Equal cost; Fort Lauderdale → Testville is unknown, Houston → Testville is known.
    client = make_client(
        FakeDistanceProvider({("Testville", "Farville"): 400, ("Houston", "Testville"): 900})
    )

    result = select(client, "Testville", "Farville", 20, "Dry")

    assert result["selected_carrier"]["name"] == "M-Logistics"
    loser = result["eligible_carriers"][0]
    assert loser["name"] == "B-Logistics"
    assert loser["hq_distance"] is None
    assert "bilinmiyor" in loser["lost_on"]


# --- Routes and input ------------------------------------------------------------------------

def test_route_outside_the_table_without_a_provider_is_unknown(client):
    result = select(client, "Miami", "Boston", 40, "Dry")

    assert result["status"] == "unknown_route"
    assert result["selected_carrier"] is None
    assert result["distance"] is None


def test_provider_failure_gives_unknown_route_not_an_estimate(make_client):
    client = make_client(FakeDistanceProvider(fail=True))

    result = select(client, "Miami", "Boston", 40, "Dry")

    assert result["status"] == "unknown_route"


def test_route_from_provider_reports_api_source(make_client):
    client = make_client(FakeDistanceProvider({("Miami", "Boston"): 1500}))

    result = select(client, "Miami", "Boston", 20, "Dry")

    assert result["distance"] == {"miles": "1500", "source": "api"}
    assert result["selected_carrier"]["name"] == "B-Logistics"


def test_city_names_are_matched_case_insensitively_and_by_alias(client):
    result = select(client, "  miami ", "ft. lauderdale", 40, "Reefer")

    assert result["status"] == "selected"
    assert result["order"]["destination"] == "Fort Lauderdale"
    assert result["distance"]["source"] == "table"


def test_same_origin_and_destination_is_an_invalid_order(client):
    result = select(client, "Miami", "miami", 40, "Dry")

    assert result["status"] == "invalid_order"
    assert result["selected_carrier"] is None


@pytest.mark.parametrize(
    "body",
    [
        {"origin": "Miami", "destination": "Orlando", "container_size": 30, "cargo_type": "Dry"},
        {"origin": "Miami", "destination": "Orlando", "container_size": 40, "cargo_type": "Liquid"},
        {"origin": "", "destination": "Orlando", "container_size": 40, "cargo_type": "Dry"},
        {"destination": "Orlando", "container_size": 40, "cargo_type": "Dry"},
    ],
)
def test_malformed_or_unsupported_order_fields_are_rejected_with_422(client, body):
    response = client.post("/select-carrier", json=body)

    assert response.status_code == 422
