def test_register(client):
    r = client.post(
        "/auth/register",
        json={"email": "new@example.com", "fullname": "New", "password": "password123"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "new@example.com"
    assert "id" in body
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "password123"}
    assert client.post("/auth/register", json=payload).status_code == 201
    assert client.post("/auth/register", json=payload).status_code == 400


def test_register_short_password(client):
    r = client.post("/auth/register", json={"email": "s@example.com", "password": "short"})
    assert r.status_code == 422


def test_login(client):
    client.post("/auth/register", json={"email": "l@example.com", "password": "password123"})
    r = client.post("/auth/login", data={"username": "l@example.com", "password": "password123"})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


def test_login_wrong_password(client):
    client.post("/auth/register", json={"email": "w@example.com", "password": "password123"})
    r = client.post("/auth/login", data={"username": "w@example.com", "password": "wrongpass1"})
    assert r.status_code == 401


def test_protected_route_without_token(client):
    assert client.get("/categories").status_code == 401


def test_protected_route_with_bad_token(client):
    r = client.get("/categories", headers={"Authorization": "Bearer not.a.token"})
    assert r.status_code == 401