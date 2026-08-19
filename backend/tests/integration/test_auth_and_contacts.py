def test_register_login_me(client):
    r = client.post(
        "/api/auth/register",
        json={"email": "a@b.co", "password": "pw123456", "full_name": "A"},
    )
    assert r.status_code == 201
    r = client.post("/api/auth/login", data={"username": "a@b.co", "password": "pw123456"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "a@b.co"


def test_contacts_require_auth(client):
    assert client.get("/api/contacts").status_code == 401


def test_contact_crud(client, auth_headers):
    r = client.post(
        "/api/contacts",
        json={"email": "sarah@abc.ai", "first_name": "Sarah", "company_name": "ABC AI"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    contact_id = r.json()["id"]

    # duplicate rejected
    r = client.post("/api/contacts", json={"email": "sarah@abc.ai"}, headers=auth_headers)
    assert r.status_code == 409

    r = client.get("/api/contacts", headers=auth_headers)
    assert r.json()["total"] == 1

    r = client.patch(
        f"/api/contacts/{contact_id}", json={"job_title": "CTO"}, headers=auth_headers
    )
    assert r.json()["job_title"] == "CTO"
