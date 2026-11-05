import shutil
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services.distance import DistanceProviderError

REPO_RULES = Path(__file__).resolve().parents[2] / "rules.yaml"


class FakeDistanceProvider:
    """In-memory stand-in for the road distance API. Unknown pairs return None."""

    name = "fake"

    def __init__(self, distances: dict[tuple[str, str], int] | None = None, fail: bool = False):
        self.distances = {frozenset(k): Decimal(v) for k, v in (distances or {}).items()}
        self.fail = fail
        self.calls: list[tuple[str, str]] = []

    def road_distance_miles(self, a: str, b: str) -> Decimal | None:
        self.calls.append((a, b))
        if self.fail:
            raise DistanceProviderError("provider down")
        return self.distances.get(frozenset((a, b)))

    def knows_city(self, city: str) -> bool:
        if self.fail:
            raise DistanceProviderError("provider down")
        return any(city in pair for pair in self.distances)


@pytest.fixture
def rules_path(tmp_path: Path) -> Path:
    target = tmp_path / "rules.yaml"
    shutil.copy(REPO_RULES, target)
    return target


@pytest.fixture
def make_client(rules_path: Path):
    """Build a test client on a fresh in-memory database, with an optional fake distance provider."""
    clients = []

    def _make(distance_provider: FakeDistanceProvider | None = None) -> TestClient:
        # The real distance API is never used in tests; a fake provider is passed in when needed.
        settings = Settings(database_url="sqlite://", rules_path=rules_path, distance_api_enabled=False)
        client = TestClient(create_app(settings, distance_provider=distance_provider))
        client.__enter__()  # runs startup: create tables + seed the case carriers
        clients.append(client)
        return client

    yield _make
    for client in clients:
        client.__exit__(None, None, None)


@pytest.fixture
def client(make_client) -> TestClient:
    return make_client()


def select(client: TestClient, origin: str, destination: str, size: int, cargo: str) -> dict:
    response = client.post(
        "/select-carrier",
        json={"origin": origin, "destination": destination, "container_size": size, "cargo_type": cargo},
    )
    assert response.status_code == 200, response.text
    return response.json()
