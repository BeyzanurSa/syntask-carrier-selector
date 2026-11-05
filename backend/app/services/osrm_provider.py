"""Road distances from OpenStreetMap: Nominatim for geocoding, OSRM for driving routes. No API key.

Both are public servers without an SLA, so every failure becomes DistanceProviderError and the
caller answers "unknown route" instead of guessing (ADR 0003). Nominatim's usage policy asks for
a descriptive User-Agent and at most one request per second.
"""

import threading
import time
from decimal import ROUND_HALF_UP, Decimal

import httpx

from app.services.distance import DistanceProviderError

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving/"
USER_AGENT = "CarrierSelector/0.1 (case study; local demo)"
METERS_PER_MILE = Decimal("1609.344")


class OsrmNominatimProvider:
    name = "osrm"

    def __init__(self, country_codes: str = "us", timeout: float = 5.0, min_geocode_interval: float = 1.0):
        self._client = httpx.Client(timeout=timeout, headers={"User-Agent": USER_AGENT})
        self._country_codes = country_codes
        self._min_interval = min_geocode_interval
        self._last_geocode = 0.0
        self._lock = threading.Lock()
        self._coordinates: dict[str, tuple[str, str] | None] = {}

    def road_distance_miles(self, a: str, b: str) -> Decimal | None:
        start, end = self._locate(a), self._locate(b)
        if start is None or end is None:
            return None
        (lat1, lon1), (lat2, lon2) = start, end
        data = self._get_json(f"{OSRM_URL}{lon1},{lat1};{lon2},{lat2}", params={"overview": "false"})
        if data.get("code") != "Ok" or not data.get("routes"):
            return None
        meters = Decimal(str(data["routes"][0]["distance"]))
        return (meters / METERS_PER_MILE).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

    def knows_city(self, city: str) -> bool:
        return self._locate(city) is not None

    def _locate(self, city: str) -> tuple[str, str] | None:
        """(lat, lon) of a city, remembered for the life of the process (cities don't move)."""
        if city not in self._coordinates:
            with self._lock:
                wait = self._last_geocode + self._min_interval - time.monotonic()
                if wait > 0:
                    time.sleep(wait)
                self._last_geocode = time.monotonic()
                results = self._get_json(
                    NOMINATIM_URL,
                    params={"q": city, "format": "jsonv2", "limit": "1", "countrycodes": self._country_codes},
                )
            self._coordinates[city] = (results[0]["lat"], results[0]["lon"]) if results else None
        return self._coordinates[city]

    def _get_json(self, url: str, params: dict[str, str]):
        try:
            response = self._client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise DistanceProviderError(str(error)) from error
