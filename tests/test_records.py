def test_create_and_list(client):
    r = client.post("/records", json={"name": "Jane", "email": "jane@example.com"})
    assert r.status_code == 201
    body = r.get_json()
    assert body["name"] == "Jane"
    assert body["id"] is not None

    r = client.get("/records")
    assert r.status_code == 200
    items = r.get_json()
    assert any(i["email"] == "jane@example.com" for i in items)


def test_duplicate_email(client):
    payload = {"name": "Dup", "email": "dup@example.com"}
    assert client.post("/records", json=payload).status_code == 201
    r = client.post("/records", json=payload)
    assert r.status_code == 409


def test_invalid_payload(client):
    assert client.post("/records", json={"name": ""}).status_code == 400
    assert client.post("/records", json={"email": "x@y.com"}).status_code == 400


def test_pagination_clamps(client):
    # Valores absurdos sao clampados (limit 1..100, offset >= 0), nunca 5xx.
    assert client.get("/records?limit=10000").status_code == 200
    assert client.get("/records?limit=0").status_code == 200
    assert client.get("/records?offset=-5").status_code == 200
    assert client.get("/records").status_code == 200