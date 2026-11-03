from decimal import Decimal


def body(category_id, **overrides):
    data = {
        "amount": "149.50",
        "description": "Lunch",
        "spent_on": "2026-11-02",
        "category_id": category_id,
    }
    data.update(overrides)
    return data


def create(client, headers, category_id, **overrides):
    r = client.post("/expenses", json=body(category_id, **overrides), headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


# ---------- create ----------

def test_create_expense(client, auth_headers, category_id):
    e = create(client, auth_headers, category_id, payment_method="UPI")
    assert Decimal(e["amount"]) == Decimal("149.50")
    assert e["payment_method"] == "UPI"
    assert "id" in e and "created_at" in e
    assert "user_id" not in e


def test_create_without_payment_method(client, auth_headers, category_id):
    assert create(client, auth_headers, category_id)["payment_method"] is None


def test_create_negative_amount(client, auth_headers, category_id):
    r = client.post("/expenses", json=body(category_id, amount="-5"), headers=auth_headers)
    assert r.status_code == 422


def test_create_zero_amount(client, auth_headers, category_id):
    r = client.post("/expenses", json=body(category_id, amount="0"), headers=auth_headers)
    assert r.status_code == 422


def test_create_missing_category(client, auth_headers):
    r = client.post("/expenses", json=body(9999), headers=auth_headers)
    assert r.status_code == 400


def test_create_with_other_users_category(client, other_auth_headers, category_id):
    r = client.post("/expenses", json=body(category_id), headers=other_auth_headers)
    assert r.status_code == 400


def test_create_requires_login(client, category_id):
    assert client.post("/expenses", json=body(category_id)).status_code == 401


# ---------- get ----------

def test_get_expense(client, auth_headers, category_id):
    e = create(client, auth_headers, category_id)
    r = client.get(f"/expenses/{e['id']}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["description"] == "Lunch"


def test_get_missing_expense(client, auth_headers):
    assert client.get("/expenses/9999", headers=auth_headers).status_code == 404


def test_get_other_users_expense(client, auth_headers, other_auth_headers, category_id):
    e = create(client, auth_headers, category_id)
    assert client.get(f"/expenses/{e['id']}", headers=other_auth_headers).status_code == 404


# ---------- patch ----------

def test_patch_only_amount(client, auth_headers, category_id):
    e = create(client, auth_headers, category_id)
    r = client.patch(f"/expenses/{e['id']}", json={"amount": "200.00"}, headers=auth_headers)
    assert r.status_code == 200
    got = client.get(f"/expenses/{e['id']}", headers=auth_headers).json()
    assert Decimal(got["amount"]) == Decimal("200.00")
    assert got["description"] == "Lunch"
    assert got["spent_on"] == "2026-11-02"
    assert got["category_id"] == category_id


def test_patch_empty_body_changes_nothing(client, auth_headers, category_id):
    e = create(client, auth_headers, category_id)
    r = client.patch(f"/expenses/{e['id']}", json={}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["description"] == "Lunch"


def test_patch_payment_method(client, auth_headers, category_id):
    e = create(client, auth_headers, category_id, payment_method="UPI")
    r = client.patch(f"/expenses/{e['id']}", json={"payment_method": "Cash"}, headers=auth_headers)
    assert r.json()["payment_method"] == "Cash"


def test_patch_null_amount_rejected(client, auth_headers, category_id):
    e = create(client, auth_headers, category_id)
    r = client.patch(f"/expenses/{e['id']}", json={"amount": None}, headers=auth_headers)
    assert r.status_code == 422


def test_patch_null_description_allowed(client, auth_headers, category_id):
    e = create(client, auth_headers, category_id)
    r = client.patch(f"/expenses/{e['id']}", json={"description": None}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["description"] is None


def test_patch_to_other_users_category(client, auth_headers, other_auth_headers, category_id):
    other_cat = client.post("/categories", json={"name": "Work"}, headers=other_auth_headers).json()["id"]
    e = create(client, auth_headers, category_id)
    r = client.patch(f"/expenses/{e['id']}", json={"category_id": other_cat}, headers=auth_headers)
    assert r.status_code == 400


def test_other_user_cannot_patch(client, auth_headers, other_auth_headers, category_id):
    e = create(client, auth_headers, category_id)
    r = client.patch(f"/expenses/{e['id']}", json={"amount": "1.00"}, headers=other_auth_headers)
    assert r.status_code == 404


# ---------- delete ----------

def test_delete_expense(client, auth_headers, category_id):
    e = create(client, auth_headers, category_id)
    assert client.delete(f"/expenses/{e['id']}", headers=auth_headers).status_code == 204
    assert client.get(f"/expenses/{e['id']}", headers=auth_headers).status_code == 404


def test_delete_missing_expense(client, auth_headers):
    assert client.delete("/expenses/9999", headers=auth_headers).status_code == 404


def test_other_user_cannot_delete(client, auth_headers, other_auth_headers, category_id):
    e = create(client, auth_headers, category_id)
    assert client.delete(f"/expenses/{e['id']}", headers=other_auth_headers).status_code == 404
    assert client.get(f"/expenses/{e['id']}", headers=auth_headers).status_code == 200


# ---------- list: filters and pagination ----------

def test_list_all_newest_first(client, auth_headers, seeded):
    items = client.get("/expenses", headers=auth_headers).json()
    assert len(items) == 5
    dates = [i["spent_on"] for i in items]
    assert dates == sorted(dates, reverse=True)
    assert items[0]["description"] == "Dinner with friends"


def test_list_date_range(client, auth_headers, seeded):
    r = client.get(
        "/expenses",
        params={"start_date": "2026-10-29", "end_date": "2026-10-31"},
        headers=auth_headers,
    )
    assert sorted(i["description"] for i in r.json()) == ["Auto to office", "Groceries"]


def test_list_by_category(client, auth_headers, seeded):
    r = client.get("/expenses", params={"category_id": seeded["food"]}, headers=auth_headers)
    assert len(r.json()) == 3
    assert all(i["category_id"] == seeded["food"] for i in r.json())


def test_list_min_amount(client, auth_headers, seeded):
    r = client.get("/expenses", params={"min_amount": "100"}, headers=auth_headers)
    assert len(r.json()) == 3


def test_list_max_amount(client, auth_headers, seeded):
    r = client.get("/expenses", params={"max_amount": "100"}, headers=auth_headers)
    assert len(r.json()) == 2


def test_list_amount_range(client, auth_headers, seeded):
    r = client.get("/expenses", params={"min_amount": "100", "max_amount": "200"}, headers=auth_headers)
    assert [i["description"] for i in r.json()] == ["Lunch"]


def test_list_combined_filters(client, auth_headers, seeded):
    r = client.get(
        "/expenses",
        params={"category_id": seeded["food"], "start_date": "2026-10-30"},
        headers=auth_headers,
    )
    assert sorted(i["description"] for i in r.json()) == ["Dinner with friends", "Groceries"]


def test_list_min_greater_than_max(client, auth_headers, seeded):
    r = client.get("/expenses", params={"min_amount": "200", "max_amount": "100"}, headers=auth_headers)
    assert r.status_code == 422


def test_list_pagination_no_overlap(client, auth_headers, seeded):
    p1 = client.get("/expenses", params={"limit": 2, "offset": 0}, headers=auth_headers).json()
    p2 = client.get("/expenses", params={"limit": 2, "offset": 2}, headers=auth_headers).json()
    p3 = client.get("/expenses", params={"limit": 2, "offset": 4}, headers=auth_headers).json()
    assert [len(p1), len(p2), len(p3)] == [2, 2, 1]
    ids = [i["id"] for i in p1 + p2 + p3]
    assert len(set(ids)) == 5


def test_list_limit_bounds(client, auth_headers, seeded):
    assert client.get("/expenses", params={"limit": 0}, headers=auth_headers).status_code == 422
    assert client.get("/expenses", params={"limit": 101}, headers=auth_headers).status_code == 422
    assert client.get("/expenses", params={"offset": -1}, headers=auth_headers).status_code == 422


def test_list_is_scoped_to_user(client, other_auth_headers, seeded):
    assert client.get("/expenses", headers=other_auth_headers).json() == []