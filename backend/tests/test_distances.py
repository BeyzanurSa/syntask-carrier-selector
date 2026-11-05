"""Distance resolution through the API: case table first, then the cache, then the provider (ADR 0003)."""

from decimal import Decimal

from tests.conftest import FakeDistanceProvider, select
from tests.test_carriers import NEW_CARRIER


def test_provider_distance_is_cached_for_the_next_order_in_either_direction(make_client):
    provider = FakeDistanceProvider({("Miami", "Boston"): 1500})
    client = make_client(provider)

    first = select(client, "Miami", "Boston", 20, "Dry")
    provider.calls.clear()
    second = select(client, "Boston", "Miami", 20, "Dry")

    assert first["distance"] == {"miles": "1500.0", "source": "api"}
    assert second["distance"] == {"miles": "1500.0", "source": "api"}
    assert ("Miami", "Boston") not in provider.calls and ("Boston", "Miami") not in provider.calls


def test_case_table_wins_over_the_provider(make_client):
    provider = FakeDistanceProvider({("Miami", "Orlando"): 999})
    client = make_client(provider)

    result = select(client, "Miami", "Orlando", 40, "Dry")

    assert result["distance"] == {"miles": "235", "source": "table"}
    assert ("Miami", "Orlando") not in provider.calls


def test_failed_lookups_are_not_cached(make_client):
    provider = FakeDistanceProvider(fail=True)
    client = make_client(provider)
    assert select(client, "Miami", "Boston", 20, "Dry")["status"] == "unknown_route"

    provider.fail = False
    provider.distances[frozenset(("Miami", "Boston"))] = Decimal(1500)

    assert select(client, "Miami", "Boston", 20, "Dry")["status"] == "selected"


def test_carrier_with_an_unmeasurable_hq_is_saved_with_a_warning(client):
    response = client.post("/carriers", json={**NEW_CARRIER, "headquarters_city": "Nowhereville"})

    assert response.status_code == 201
    assert response.json()["headquarters_city"] == "Nowhereville"
    assert any("mesafe" in w.lower() for w in response.json()["warnings"])


def test_carrier_with_a_known_hq_has_no_warning(client):
    response = client.post("/carriers", json={**NEW_CARRIER, "headquarters_city": "Tampa"})

    assert response.json()["warnings"] == []


def test_carrier_hq_known_to_the_provider_has_no_warning(make_client):
    client = make_client(FakeDistanceProvider({("Boston", "Miami"): 1500}))

    response = client.post("/carriers", json={**NEW_CARRIER, "headquarters_city": "Boston"})

    assert response.json()["warnings"] == []


def test_updating_a_carrier_reports_the_hq_warning_too(client):
    created = client.post("/carriers", json=NEW_CARRIER).json()

    updated = client.put(f"/carriers/{created['id']}", json={**NEW_CARRIER, "headquarters_city": "Nowhereville"})

    assert updated.status_code == 200
    assert updated.json()["warnings"]
