# Local Setup

Requirements: Node 22+, [uv](https://docs.astral.sh/uv/) (installs Python 3.13 automatically).

## Backend
```
cd backend
cp .env.example .env        # fill in Supabase values later (not needed for health check / tests)
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
