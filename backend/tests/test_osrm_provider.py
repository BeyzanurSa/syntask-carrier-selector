"""Adapter test for the real distance provider, with HTTP mocked (no network)."""

from decimal import Decimal

import httpx
import pytest
import respx

from app.services.distance import DistanceProviderError
from app.services.osrm_provider import NOMINATIM_URL, OSRM_URL, OsrmNominatimProvider

MIAMI = {"lat": "25.7617", "lon": "-80.1918"}
BOSTON = {"lat": "42.3601", "lon": "-71.0589"}


def provider() -> OsrmNominatimProvider:
    return OsrmNominatimProvider(min_geocode_interval=0)


def mock_geocode(router: respx.Router, places: dict[str, dict | None]) -> respx.Route:
    def respond(request: httpx.Request) -> httpx.Response:
        place = places.get(request.url.params["q"])
        return httpx.Response(200, json=[place] if place else [])

    return router.get(NOMINATIM_URL).mock(side_effect=respond)


@respx.mock
def test_road_distance_is_converted_from_meters_to_miles():
    geocode = mock_geocode(respx.mock, {"Miami": MIAMI, "Boston": BOSTON})
    route = respx.get(url__startswith=OSRM_URL).mock(
        return_value=httpx.Response(200, json={"code": "Ok", "routes": [{"distance": 2414016}]})
    )

    miles = provider().road_distance_miles("Miami", "Boston")

    assert miles == Decimal("1500.0")
    assert "-80.1918,25.7617;-71.0589,42.3601" in str(route.calls.last.request.url)
    assert "CarrierSelector" in geocode.calls.last.request.headers["user-agent"]


@respx.mock
def test_unknown_city_gives_no_distance():
    mock_geocode(respx.mock, {"Miami": MIAMI})

    assert provider().road_distance_miles("Miami", "Atlantis") is None
    assert provider().knows_city("Atlantis") is False


@respx.mock
def test_no_road_route_gives_no_distance():
    mock_geocode(respx.mock, {"Miami": MIAMI, "Boston": BOSTON})
    respx.get(url__startswith=OSRM_URL).mock(return_value=httpx.Response(200, json={"code": "NoRoute", "routes": []}))

    assert provider().road_distance_miles("Miami", "Boston") is None


@respx.mock
def test_timeout_is_a_provider_error():
    respx.get(NOMINATIM_URL).mock(side_effect=httpx.ConnectTimeout("timed out"))

    with pytest.raises(DistanceProviderError):
        provider().road_distance_miles("Miami", "Boston")


@respx.mock
def test_http_error_is_a_provider_error():
    mock_geocode(respx.mock, {"Miami": MIAMI, "Boston": BOSTON})
    respx.get(url__startswith=OSRM_URL).mock(return_value=httpx.Response(503))

    with pytest.raises(DistanceProviderError):
        provider().road_distance_miles("Miami", "Boston")


@respx.mock
def test_geocoding_is_remembered_per_city():
    geocode = mock_geocode(respx.mock, {"Miami": MIAMI})
    p = provider()

    assert p.knows_city("Miami") and p.knows_city("Miami")
    assert geocode.call_count == 1
