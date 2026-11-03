import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine

from config.config import settings
import models  # registers the tables

if not settings.test_database_url:
    raise RuntimeError("TEST_DATABASE_URL is not set in .env")
if settings.test_database_url == settings.database_url:
    raise RuntimeError("Test database must differ from the real database")

from data.data import get_session
from main import app

test_engine = create_engine(settings.test_database_url)


@pytest.fixture
def session():
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture
def client(session):
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)  # no "with": that would run the app's startup code
    app.dependency_overrides.clear()


def make_auth_headers(client, email, password="password123"):
    r = client.post(
        "/auth/register",
        json={"email": email, "fullname": "Test User", "password": password},
    )
    assert r.status_code == 201, r.text
    r = client.post("/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def auth_headers(client):
    return make_auth_headers(client, "a@example.com")


@pytest.fixture
def other_auth_headers(client):
    return make_auth_headers(client, "b@example.com")


@pytest.fixture
def category_id(client, auth_headers):
    r = client.post("/categories", json={"name": "Food"}, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


@pytest.fixture
def seeded(client, auth_headers):
    """User A with 2 categories and 5 expenses across Oct and Nov 2026."""
    food = client.post("/categories", json={"name": "Food"}, headers=auth_headers).json()["id"]
    transport = client.post("/categories", json={"name": "Transport"}, headers=auth_headers).json()["id"]
    rows = [
        ("149.50", "Lunch", "2026-10-28", food),
        ("60.00", "Auto to office", "2026-10-29", transport),
        ("320.00", "Groceries", "2026-10-31", food),
        ("85.25", "Metro card recharge", "2026-11-01", transport),
        ("210.75", "Dinner with friends", "2026-11-02", food),
    ]
    for amount, desc, day, cat in rows:
        r = client.post(
            "/expenses",
            json={"amount": amount, "description": desc, "spent_on": day, "category_id": cat},
            headers=auth_headers,
        )
        assert r.status_code == 201, r.text
    return {"food": food, "transport": transport}