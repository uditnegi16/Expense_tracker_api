def test_create_category(client, auth_headers):
    r = client.post("/categories", json={"name": "Food"}, headers=auth_headers)
    assert r.status_code == 201
    assert r.json()["name"] == "Food"
    assert "id" in r.json()
    assert "user_id" not in r.json()


def test_create_duplicate_category(client, auth_headers):
    client.post("/categories", json={"name": "Food"}, headers=auth_headers)
    r = client.post("/categories", json={"name": "Food"}, headers=auth_headers)
    assert r.status_code == 409


def test_same_name_allowed_for_different_users(client, auth_headers, other_auth_headers):
    assert client.post("/categories", json={"name": "Food"}, headers=auth_headers).status_code == 201
    assert client.post("/categories", json={"name": "Food"}, headers=other_auth_headers).status_code == 201


def test_empty_name_rejected(client, auth_headers):
    r = client.post("/categories", json={"name": ""}, headers=auth_headers)
    assert r.status_code == 422


def test_list_only_own_categories(client, auth_headers, other_auth_headers):
    client.post("/categories", json={"name": "Transport"}, headers=auth_headers)
    client.post("/categories", json={"name": "Food"}, headers=auth_headers)
    client.post("/categories", json={"name": "Work"}, headers=other_auth_headers)
    a = client.get("/categories", headers=auth_headers).json()
    b = client.get("/categories", headers=other_auth_headers).json()
    assert [c["name"] for c in a] == ["Food", "Transport"]  # ordered by name
    assert [c["name"] for c in b] == ["Work"]


def test_get_category(client, auth_headers, category_id):
    r = client.get(f"/categories/{category_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["name"] == "Food"


def test_get_missing_category(client, auth_headers):
    assert client.get("/categories/9999", headers=auth_headers).status_code == 404


def test_get_other_users_category(client, auth_headers, other_auth_headers, category_id):
    r = client.get(f"/categories/{category_id}", headers=other_auth_headers)
    assert r.status_code == 404


def test_rename_category(client, auth_headers, category_id):
    r = client.patch(f"/categories/{category_id}", json={"name": "Groceries"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["name"] == "Groceries"


def test_rename_to_existing_name(client, auth_headers, category_id):
    other = client.post("/categories", json={"name": "Transport"}, headers=auth_headers).json()["id"]
    r = client.patch(f"/categories/{other}", json={"name": "Food"}, headers=auth_headers)
    assert r.status_code == 409


def test_other_user_cannot_rename(client, auth_headers, other_auth_headers, category_id):
    r = client.patch(f"/categories/{category_id}", json={"name": "Hacked"}, headers=other_auth_headers)
    assert r.status_code == 404


def test_delete_category(client, auth_headers, category_id):
    assert client.delete(f"/categories/{category_id}", headers=auth_headers).status_code == 204
    assert client.get(f"/categories/{category_id}", headers=auth_headers).status_code == 404


def test_delete_category_with_expenses(client, auth_headers, category_id):
    client.post(
        "/expenses",
        json={"amount": "10.00", "spent_on": "2026-11-02", "category_id": category_id},
        headers=auth_headers,
    )
    r = client.delete(f"/categories/{category_id}", headers=auth_headers)
    assert r.status_code == 409
    assert client.get(f"/categories/{category_id}", headers=auth_headers).status_code == 200