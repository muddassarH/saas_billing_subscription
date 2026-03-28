# SaaS Billing & Subscription System

Production-style full-stack SaaS billing system with Django, DRF, Stripe, Celery, Redis, PostgreSQL, and Next.js.

## Run with Docker Compose

1. Copy env template:

```bash
cp .env.docker.example .env
```

2. Update Stripe keys and secret values in `.env`.

3. Build and run:

```bash
docker compose up --build
```

4. Open:
- App: `http://localhost`
- Django admin: `http://localhost/admin`
- API base: `http://localhost/api`

## Services

- `nginx` (port 80): reverse proxy to frontend/backend + static/media
- `frontend`: Next.js production server
- `backend`: Django + Gunicorn
- `celery`: background jobs/webhook processing
- `redis`: broker/result backend
- `db`: PostgreSQL

## Notes

- Backend entrypoint runs: migrations, `collectstatic`, and `seed_plans`.
- Webhook endpoint is available at `POST /api/webhook/stripe/`.
- Default compose setup uses `SECURE_SSL_REDIRECT=false` for local HTTP.
