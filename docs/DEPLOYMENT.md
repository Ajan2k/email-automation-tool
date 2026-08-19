# Deployment (Vercel + Render + Supabase)

## 1. Supabase (PostgreSQL)
1. Create a project at supabase.com.
2. Copy the **connection pooling** URI (Transaction mode, port 6543) and set it
   as `DATABASE_URL` (replace `postgres://` with `postgresql+psycopg2://`).
3. Run migrations from your machine: `cd backend && alembic upgrade head`
   (or let `create_all` bootstrap on first boot, then switch to Alembic).

## 2. Redis
- Create a **Render Key-Value** instance (or Upstash). Copy `REDIS_URL`.

## 3. Render — FastAPI Web Service
- New Web Service → connect the GitHub repo → root directory `backend`, Docker.
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment: `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `SMTP_*`,
  `GROQ_API_KEY`, `PUBLIC_API_URL=https://<your-api>.onrender.com`,
  `CORS_ORIGINS=https://<your-app>.vercel.app`, `ENVIRONMENT=production`.

## 4. Render — Background Worker
- New **Background Worker** → same repo/Docker image.
- Start command: `python -m worker.main`
- Same environment variables as the API. **Never run the worker inside the
  API process in production.**

## 5. Vercel — Next.js
- Import the repo, root directory `frontend`.
- Environment: `API_PROXY_TARGET=https://<your-api>.onrender.com`
  (used by `next.config.mjs` rewrites so the browser only talks to Vercel).

## 6. Inbound email
Point your inbound provider (Mailgun Routes / SendGrid Inbound Parse /
Postmark Inbound) at:
```
POST https://<your-api>.onrender.com/api/webhooks/inbound-email
```
Add a shared-secret header check before going live.

## 7. Deliverability checklist (non-optional)
- SPF, DKIM, DMARC records for the sending domain
- Unsubscribe link in every template (`/api/track/unsubscribe/{tracking_id}`)
- Bounce webhook wired to `/api/webhooks/bounce`
- Warm up the domain slowly; respect `daily_limit` / `rate_per_minute`

## 8. Launch smoke test (do all 12 before real volume)
1. Import 10 contacts → 2. send 10 emails → 3. open one → 4. click a link →
5. force a bounce → 6. reply to one → 7. verify webhook received →
8. verify LLM draft appears → 9. edit draft → 10. approve →
11. verify worker sends the reply → 12. verify dashboard analytics updated.
