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
