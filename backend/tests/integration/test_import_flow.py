CSV = b"""first_name,last_name,email,company,job_title
Sarah,Chen,sarah@abc.ai,ABC AI,CTO
John,Doe,john@xyz.dev,XYZ Labs,Founder
Bad,Row,not-an-email,Nowhere,
Sarah,Chen,sarah@abc.ai,ABC AI,CTO
"""


def test_preview_then_import(client, auth_headers):
    r = client.post(
        "/api/imports/preview",
        files={"file": ("contacts.csv", CSV, "text/csv")},
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 4
    assert data["valid"] == 2
    assert data["invalid"] == 1
    assert data["duplicates"] == 1

    r = client.post(
        "/api/imports/run",
        files={"file": ("contacts.csv", CSV, "text/csv")},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["imported"] == 2

    r = client.get("/api/contacts", headers=auth_headers)
    assert r.json()["total"] == 2
