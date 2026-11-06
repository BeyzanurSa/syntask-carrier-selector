"""Known cities for the form's suggestions, and a "did you mean" check against typos reaching the geocoder."""

import pytest

from tests.conftest import FakeDistanceProvider, select


def check(client, name: str) -> dict:
    response = client.get("/cities/check", params={"name": name})
    assert response.status_code == 200
    return response.json()


def test_known_cities_cover_the_case_table_and_carrier_headquarters(client):
    cities = client.get("/cities").json()

    assert {"Miami", "Orlando", "Atlanta", "Savannah", "Tampa", "Jacksonville", "Houston", "Fort Lauderdale"} <= set(
        cities
    )
    assert cities == sorted(cities)


def test_new_hq_and_cached_route_cities_become_known(make_client):
    client = make_client(FakeDistanceProvider({("Miami", "Boston"): 1500}))
    client.post(
        "/carriers",
        json={
            "name": "Chi-Logistics",
            "headquarters_city": "Chicago",
            "supported_container_sizes": [40],
            "supported_cargo_types": ["Dry"],
            "price_per_mile": "1.00",
        },
    )
    select(client, "Miami", "Boston", 40, "Dry")

    assert {"Chicago", "Boston"} <= set(client.get("/cities").json())


@pytest.mark.parametrize(
    ("typed", "normalized"), [("miami", "Miami"), ("ft. lauderdale", "Fort Lauderdale"), ("  ORLANDO ", "Orlando")]
)
def test_known_city_is_recognised_after_normalization(client, typed, normalized):
    assert check(client, typed) == {"known": True, "normalized": normalized, "suggestion": None}


@pytest.mark.parametrize(("typo", "suggestion"), [("Miammi", "Miami"), ("Orlandoo", "Orlando"), ("Jaksonville", "Jacksonville")])
def test_close_typo_gets_a_suggestion(client, typo, suggestion):
    result = check(client, typo)

    assert result["known"] is False
    assert result["suggestion"] == suggestion


def test_genuinely_new_city_gets_no_suggestion(client):
    assert check(client, "Boston") == {"known": False, "normalized": "Boston", "suggestion": None}


def test_empty_name_is_rejected(client):
    assert client.get("/cities/check", params={"name": " "}).status_code == 422
