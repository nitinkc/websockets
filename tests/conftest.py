import pytest
from fastapi.testclient import TestClient

from backend import store, ticker
from backend.main import app
from backend.ws import hub


@pytest.fixture
def client() -> TestClient:
    # Context-managed so the app lifespan runs — the ticker only ticks
    # while the market_loop task is alive.
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_state():
    store.events.clear()
    hub.connections.clear()
    ticker.hub.connections.clear()
