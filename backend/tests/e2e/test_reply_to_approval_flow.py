"""The critical E2E path: outbound email → inbound reply → conversation →
AI draft → human edit → approve → outbound reply queued."""
from unittest.mock import patch

from app.models import (
    AIReplyStatus,
    Contact,
    EmailDirection,
    EmailMessage,
    EmailStatus,
    User,
)


def test_full_reply_flow(client, auth_headers, db_session):
    user = db_session.query(User).first()
    contact = Contact(owner_id=user.id, email="sarah@abc.ai", first_name="Sarah")
    db_session.add(contact)
    db_session.flush()
    outbound = EmailMessage(
        owner_id=user.id,
        contact_id=contact.id,
        direction=EmailDirection.OUTBOUND,
        status=EmailStatus.SENT,
        subject="AI collaboration",
        to_email="sarah@abc.ai",
        from_email="me@platform.io",
        message_id_header="<msg-1@platform.io>",
        tracking_id="trk1",
    )
    db_session.add(outbound)
    db_session.commit()

    fake_llm = {
        "classification": "interested",
        "draft_reply": "Thanks Sarah, happy to schedule a call next week.",
        "reason": "Positive response asking about collaboration.",
        "requires_human_attention": False,
    }
    with patch("app.services.ai_reply_service._call_llm", return_value=fake_llm):
        r = client.post(
            "/api/webhooks/inbound-email",
            json={
                "from_email": "sarah@abc.ai",
                "to_email": "me@platform.io",
                "subject": "Re: AI collaboration",
                "body": "Thanks for reaching out, I'd love to hear more!",
                "message_id": "<reply-1@abc.ai>",
                "in_reply_to": "<msg-1@platform.io>",
                "references": "<msg-1@platform.io>",
            },
        )
    assert r.status_code == 200
    conversation_id = r.json()["conversation_id"]

    # conversation contains both messages
    r = client.get(f"/api/conversations/{conversation_id}", headers=auth_headers)
    assert len(r.json()["messages"]) == 2

    # AI draft exists and is pending review
    r = client.get("/api/ai-replies?status=draft", headers=auth_headers)
    drafts = r.json()
    assert len(drafts) == 1
    draft = drafts[0]
    assert "schedule a call" in draft["draft_body"]

    # human edits the draft
    r = client.patch(
        f"/api/ai-replies/{draft['id']}",
        json={"edited_body": "Thanks Sarah — how about Tuesday 2pm?"},
        headers=auth_headers,
    )
    assert r.json()["edited_body"].startswith("Thanks Sarah")

    # human approves → email queued (never auto-sent)
    with patch("app.services.ai_reply_service.enqueue_send_email") as mock_enqueue:
        r = client.post(f"/api/ai-replies/{draft['id']}/approve", headers=auth_headers)
    assert r.status_code == 200
    mock_enqueue.assert_called_once()

    queued = (
        db_session.query(EmailMessage)
        .filter(
            EmailMessage.direction == EmailDirection.OUTBOUND,
            EmailMessage.status == EmailStatus.QUEUED,
        )
        .one()
    )
    assert queued.body.startswith("Thanks Sarah — how about Tuesday 2pm?")
    assert queued.in_reply_to == "<reply-1@abc.ai>"

    # approving twice is blocked
    r = client.post(f"/api/ai-replies/{draft['id']}/approve", headers=auth_headers)
    assert r.status_code == 409
