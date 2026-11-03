from decimal import Decimal

import pytest


def test_monthly_summary(client, auth_headers, seeded):
    r = client.get("/summary/monthly", headers=auth_headers)
    assert r.status_code == 200
    rows = r.json()
    assert [(x["year"], x["month"]) for x in rows] == [(2026, 10), (2026, 11)]
    assert Decimal(rows[0]["total"]) == Decimal("529.50")  # 149.50 + 60.00 + 320.00
    assert Decimal(rows[1]["total"]) == Decimal("296.00")  # 85.25 + 210.75


def test_by_category_summary(client, auth_headers, seeded):
    r = client.get("/summary/by-category", headers=auth_headers)
    assert r.status_code == 200
    rows = r.json()
    assert [x["category_name"] for x in rows] == ["Food", "Transport"]  # biggest first
    assert Decimal(rows[0]["total"]) == Decimal("680.25")
    assert Decimal(rows[1]["total"]) == Decimal("145.25")
    assert rows[0]["percent"] == pytest.approx(82.40, abs=0.01)
    assert rows[1]["percent"] == pytest.approx(17.60, abs=0.01)
    assert sum(x["percent"] for x in rows) == pytest.approx(100, abs=0.05)


def test_summaries_empty_for_new_user(client, auth_headers):
    assert client.get("/summary/monthly", headers=auth_headers).json() == []
    assert client.get("/summary/by-category", headers=auth_headers).json() == []


def test_summaries_are_scoped_to_user(client, other_auth_headers, seeded):
    assert client.get("/summary/monthly", headers=other_auth_headers).json() == []
    assert client.get("/summary/by-category", headers=other_auth_headers).json() == []


def test_summaries_require_login(client):
    assert client.get("/summary/monthly").status_code == 401
    assert client.get("/summary/by-category").status_code == 401