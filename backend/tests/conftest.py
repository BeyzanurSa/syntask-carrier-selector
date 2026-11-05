import shutil
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services.distance import DistanceProviderError
from app.services.interpreter import FieldReading, Interpretation, InterpreterUnavailable

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


def reading(value: str | None, confidence: float | None = 0.95) -> FieldReading:
    return FieldReading(value=value, confidence=confidence)


class FakeInterpreter:
    """Scripted stand-in for Jev: returns the given Interpretation and records what it was asked."""

    def __init__(self, interpretation: Interpretation | None = None, fail: bool = False):
        self.interpretation = interpretation
        self.fail = fail
        self.calls: list[tuple[str, list[str]]] = []

    def interpret(self, text: str, known_cities: list[str]) -> Interpretation:
        self.calls.append((text, known_cities))
        if self.fail:
            raise InterpreterUnavailable("Jev down")
        return self.interpretation


def interpretation(origin="Miami", destination="Orlando", container_size="40", cargo_type="Dry") -> Interpretation:
    """A confident Interpretation; pass a value or a full reading, e.g. container_size=reading("40", 0.4)."""

    def as_reading(value: str | FieldReading) -> FieldReading:
        return value if isinstance(value, FieldReading) else reading(value)

    return Interpretation(
        origin=as_reading(origin),
        destination=as_reading(destination),
        container_size=as_reading(container_size),
        cargo_type=as_reading(cargo_type),
    )


@pytest.fixture
def rules_path(tmp_path: Path) -> Path:
    target = tmp_path / "rules.yaml"
    shutil.copy(REPO_RULES, target)
    return target


@pytest.fixture
def make_client(rules_path: Path):
    """Build a test client on a fresh in-memory database, with an optional fake distance provider."""
    clients = []

    def _make(
        distance_provider: FakeDistanceProvider | None = None, interpreter: FakeInterpreter | None = None
    ) -> TestClient:
        # Neither the real distance API nor the real Jev is used in tests; fakes are passed in when needed.
        settings = Settings(
            database_url="sqlite://", rules_path=rules_path, distance_api_enabled=False, jev_enabled=False
        )
        client = TestClient(create_app(settings, distance_provider=distance_provider, interpreter=interpreter))
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
