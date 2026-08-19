def _make_contact(client, headers, email="sarah@abc.ai"):
    return client.post(
        "/api/contacts",
        json={
            "email": email,
            "first_name": "Sarah",
            "company_name": "ABC AI",
            "industry": "AI",
        },
        headers=headers,
    ).json()


def test_template_render_preview(client, auth_headers):
    contact = _make_contact(client, auth_headers)
    r = client.post(
        "/api/templates",
        json={
            "name": "Outreach V1",
            "subject": "AI collaboration for {{company_name}}",
            "body": "Hi {{first_name}}, saw {{company_name}} works in {{industry}}.",
        },
        headers=auth_headers,
    )
    template_id = r.json()["id"]
    r = client.post(
        f"/api/templates/{template_id}/preview",
        json={"contact_id": contact["id"]},
        headers=auth_headers,
    )
    assert r.json()["subject"] == "AI collaboration for ABC AI"
    assert "Hi Sarah" in r.json()["body"]


def test_campaign_create_and_stats(client, auth_headers):
    contact = _make_contact(client, auth_headers, "john@xyz.dev")
    template = client.post(
        "/api/templates",
        json={"name": "T", "subject": "Hello {{first_name}}", "body": "Body"},
        headers=auth_headers,
    ).json()
    r = client.post(
        "/api/campaigns",
        json={
            "name": "Test Campaign",
            "template_id": template["id"],
            "contact_ids": [contact["id"]],
        },
        headers=auth_headers,
    )
    assert r.status_code == 201
    campaign = r.json()
    assert campaign["status"] == "DRAFT" or campaign["status"] == "draft"

    r = client.get(f"/api/campaigns/{campaign['id']}/stats", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["total_contacts"] == 1
