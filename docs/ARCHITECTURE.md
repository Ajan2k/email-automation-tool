# Architecture

```
Next.js (Vercel) ──HTTPS──▶ FastAPI (Render) ──▶ Supabase PostgreSQL
                                   │
                                   └──▶ Redis ──▶ Email Worker (Render) ──▶ SMTP
                                                       │
                              Recipient replies ──▶ Inbound webhook ──▶ LLM draft
                                                       │
                                            Human review → Approve → Queue → Send
```

## Components

| Component | Tech | Responsibility |
|---|---|---|
| `frontend/` | Next.js 14 (App Router) | Dashboard, contacts, imports, templates, campaigns, inbox, AI reply review |
| `backend/` | FastAPI + SQLAlchemy 2 | REST API, auth (JWT), campaign logic, tracking, webhooks, AI orchestration |
| `worker/` | RQ worker + scheduler thread | Sending, retries, scheduled campaign launch, follow-up scheduling |
| PostgreSQL | Supabase (prod) / Docker or SQLite (dev) | All persistent state |
| Redis | Render Key-Value (prod) / Docker (dev) | Job queue between API and worker |

## Data model

Core tables: `users`, `companies`, `contacts`, `import_jobs`, `templates`,
`campaigns`, `campaign_contacts`, `email_messages`, `email_events`,
`conversations`, `followup_sequences`, `followup_steps`, `ai_reply_drafts`,
`suppression_list`.

Key design decisions:

- **Event sourcing for email analytics** — `email_events` records
  sent/opened/clicked/bounced/replied/unsubscribed rows instead of mutating
  `email_messages`, which keeps analytics simple and auditable.
- **RFC 5322 threading** — outbound messages store `Message-ID`; inbound
  replies are matched via `In-Reply-To` / `References` first, sender address
  as fallback. Never subject matching alone.
- **Provider abstraction** — `app/email/providers/base.py` defines
  `EmailProvider`; `SMTPProvider` is the first implementation. SendGrid/SES
  can be added without touching campaign logic.
- **Human-in-the-loop enforced at the API level** — the ONLY code path that
  queues an AI reply for sending is `POST /api/ai-replies/{id}/approve`,
  which requires an authenticated human. There is no auto-send path.

## Email lifecycle

```
QUEUED → PROCESSING → SENT → (DELIVERED | BOUNCED)
             └→ retry (max 3) → FAILED
```

## AI reply pipeline

```
Inbound webhook → thread matching → conversation
     → LLM (structured JSON: classification, draft, reason, needs_human)
     → keyword safety net (legal/pricing/refund/unsubscribe → force human attention)
     → AIReplyDraft(status=DRAFT)
     → human edits/regenerates/rejects/approves in UI
     → approve → EmailMessage(QUEUED) → worker → SMTP
```
