# ✉️ AI Email Automation Platform

A production-style **AI Email Automation & Human-in-the-Loop Reply Platform** — not just an SMTP sender.

Excel/CSV contact import → PostgreSQL → templated campaigns → async queue + worker → SMTP delivery → open/click/bounce tracking → follow-up automation → inbound reply detection → conversation inbox → **LLM-generated reply drafts with mandatory human approval** → analytics.

```
Next.js (Vercel) ──▶ FastAPI (Render) ──▶ Supabase PostgreSQL
                          │
                          └──▶ Redis ──▶ Email Worker (Render) ──▶ SMTP
                                              │
                     Recipient reply ──▶ Webhook ──▶ LLM draft ──▶ HUMAN REVIEW ──▶ Send
```

## Features

- 📥 **Excel/CSV import** — supports the `Decision_Makers.xlsx` layout (work_email preference, semicolon email lists, float phone artifacts, linkedin_url, skills, countries) and simple layouts; validation, duplicate detection, preview, bulk insert
- 👤 **Contact & company management** — server-side pagination, search, filters
- 📝 **Templates** — `{{first_name}}`, `{{company_name}}`, … variable substitution with live preview
- 🚀 **Campaigns** — draft → scheduled → running → completed, daily limits, rate control
- ⚙️ **Queue + worker** — Redis (RQ), retries, backend-owned scheduling
- 📈 **Event-based tracking** — open pixel, click redirect, bounce handling, suppression list
- 🔁 **Follow-up engine** — multi-step sequences that stop on reply/unsubscribe/bounce
- 💬 **Conversation inbox** — inbound replies matched via RFC 5322 headers (`In-Reply-To` / `References`)
- 🤖 **LLM reply drafts (Groq)** — `llama-3.3-70b-versatile` via Groq's OpenAI-compatible API; structured output (classification, draft, reason, needs-human flag) with keyword safety net
- ✋ **Human-in-the-loop** — the AI **never** sends. The only send path is an authenticated human clicking *Approve & Send*
- 📊 **Analytics dashboard** — delivery/open/click/reply/bounce rates
- 🔐 **JWT auth**, structured JSON logging, tests (unit/integration/e2e), Docker, CI

## Monorepo layout

```
backend/    FastAPI app (api / models / schemas / services / email / queue / utils) + tests
frontend/   Next.js 14 App Router UI
worker/     RQ worker + scheduler (campaign launch, retries, follow-ups)
docs/       ARCHITECTURE.md · API.md · DEPLOYMENT.md
scripts/    sample data generators
.github/    CI workflows (backend tests, frontend build)
```

## Quick start (local)

**Option A — Docker (Postgres + Redis + API + worker):**

```bash
cp .env.example .env    # fill in SMTP + LLM keys (optional for a first look)
docker compose up --build
```

**Option B — bare metal (SQLite, no Redis needed to explore the UI):**

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload            # http://localhost:8000/docs

# frontend (separate terminal)
cd frontend
npm install
npm run dev                              # http://localhost:3000

# worker (separate terminal, needs Redis)
cd backend && source .venv/bin/activate
python -m worker.main
```

Generate test data:

```bash
python scripts/generate_sample_contacts.py 500 > contacts.csv           # simple layout
python scripts/generate_decision_makers_sample.py 500 dm_sample.xlsx    # Decision_Makers layout
# then upload either on the /imports page
```

## Run tests

```bash
cd backend && python -m pytest
```

17 tests including the signature E2E flow:
`outbound email → inbound reply webhook → conversation → AI draft → human edit → approve → queued reply with correct threading headers`.

## The human-approval pipeline (signature feature)

```
Incoming reply → LLM → AI draft (status=DRAFT, saved to DB)
    → user reviews in UI → edit / regenerate / reject
    → Approve → status=APPROVED → Redis queue → worker → SMTP → status=SENT
```

Safety rules: drafts touching legal, pricing, contracts, refunds, complaints,
security or unsubscribe topics are force-flagged **NEEDS HUMAN ATTENTION** even
if the LLM says otherwise.

## Deployment

Vercel (frontend) + Render (API + background worker) + Supabase (PostgreSQL) + Render Key-Value (Redis).
Full runbook: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — including the SPF/DKIM/DMARC deliverability checklist and the 12-step launch smoke test.

## Docs

- [Architecture & data model](docs/ARCHITECTURE.md)
- [API reference](docs/API.md)
- [Deployment runbook](docs/DEPLOYMENT.md)

## Roadmap (post-MVP)

- Follow-up sequence builder UI · webhook signature verification · multi-tenant organizations
- Provider adapters (SendGrid / SES / Mailgun) · IMAP polling as inbound fallback
- Sentry wiring · rate-limit middleware · Alembic-first migrations
- A/B testing, lead scoring, CRM integrations (deliberately deferred)
