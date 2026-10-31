# Local Setup

Requirements: Node 22+, [uv](https://docs.astral.sh/uv/) (installs Python 3.13 automatically).

## Backend
```
cd backend
cp .env.example .env        # set JWT_SECRET (see below); Supabase values later
uv sync
uv run pytest               # tests
uv run ruff check .         # lint
uv run uvicorn app.main:app --reload --port 8000
curl localhost:8000/api/v1/health    # {"status":"ok"}
```
Alembic is configured (`alembic/env.py` reads `DATABASE_URL`, metadata from `app.models.base.Base`).
No migrations exist yet (Phase 3). For migrations use the Supabase *direct* connection string.

## Frontend
```
cd frontend
cp .env.example .env.local
npm install
npm run dev                 # http://localhost:3000
npm run lint && npx tsc --noEmit && npm run build
```
Stack: Next.js (App Router), TypeScript, Tailwind CSS v4, shadcn/ui (`components.json`), lucide-react,
Zustand, React Hook Form + Zod, TanStack Query. Brand palette tokens are in `app/globals.css`
(`brand-red/orange/gold/cream/brown`); brand name/tagline defaults in `lib/config.ts` are placeholders until
Phase 7 loads them from `website_settings`.

## Database migrations and DB tests (no Supabase needed)
Use any local PostgreSQL 13+ (needs the `pg_trgm` extension, included in standard contrib packages).
```
cd backend
export DATABASE_URL=postgresql+psycopg://USER@localhost:5432/DBNAME
uv run alembic upgrade head      # apply
uv run alembic check             # fails if models drifted from migrations
uv run alembic downgrade base    # roll back
TEST_DATABASE_URL=$DATABASE_URL uv run pytest   # DB tests; WARNING: drops and recreates the public schema
```
Without `TEST_DATABASE_URL`, the PostgreSQL tests are skipped. Use a throwaway database for tests.

## Admin login setup
```
cd backend
python3 -c "import secrets; print(secrets.token_urlsafe(48))"   # put the result in .env as JWT_SECRET
uv run alembic upgrade head
uv run python -m app.cli create-admin you@example.com --name "Your Name"   # prompts for a password (min 10 chars)
uv run python -m app.cli set-password you@example.com                       # reset; revokes all sessions
```
The first admin is created with the CLI (role `super_admin` by default); further admins are created in the API by a
super_admin. Try it with curl (note the `Origin` header and cookie jar):
```
curl -c jar -H "Origin: http://localhost:3000" -H "Content-Type: application/json" \
     -d '{"email":"you@example.com","password":"..."}' localhost:8000/api/v1/admin/auth/login
curl -b jar localhost:8000/api/v1/admin/auth/me
```
Production needs `APP_ENV=production`, `COOKIE_SECURE=true`, a 32+ character `JWT_SECRET` and explicit
`CORS_ORIGINS`; the app refuses to start otherwise. If the frontend and API are on different registrable domains
(not just different subdomains), `COOKIE_SAMESITE=none` is required; decide this at deployment (Phase 13).

## Image storage
Development: `STORAGE_BACKEND=local` (default) stores files under `backend/media/` (git-ignored) and the API serves them at
`/media`. Production: create a **public** Supabase Storage bucket, then set `STORAGE_BACKEND=supabase`, `SUPABASE_URL`,
`SUPABASE_SERVICE_ROLE_KEY` and `SUPABASE_STORAGE_BUCKET`. The service-role key must only ever be set on the backend.

## Admin UI
Start the backend (`uv run uvicorn app.main:app --reload`) and the frontend (`npm run dev`), then open
http://localhost:3000/admin/login. The login page talks to the API at `NEXT_PUBLIC_API_BASE_URL`
(default `http://localhost:8000/api/v1`); the allowed origin must match `CORS_ORIGINS`.

## Frontend tests
```
cd frontend
npm test                 # unit tests (API client: refresh, errors, uploads)
npm run typecheck && npm run lint && npm run build
```

## Browser tests (Playwright, real backend and database)
Use a **throwaway** database. Rate limiting is turned off for this run because the suite signs in many times
(the limiter itself is covered by backend tests).
```
cd backend
export DATABASE_URL=postgresql+psycopg://USER@localhost:5432/e2e_db JWT_SECRET=<32+ chars> RATE_LIMIT_ENABLED=false
uv run alembic upgrade head
uv run python -m scripts.seed_e2e_admins            # dev only: creates e2e-manager@ and e2e-staff@ admins
uv run uvicorn app.main:app --port 8000 &

cd ../frontend
npx playwright install chromium                     # once
npm run test:e2e                                    # starts the frontend dev server itself
```
The suite leaves its test products in that database; it uses unique names, so it can be re-run.
