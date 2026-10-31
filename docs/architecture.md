# Architecture (Phase 1)

```
Browser -> Next.js (App Router, TypeScript, Tailwind, shadcn/ui, Lucide)
              |  REST/JSON
              v
           FastAPI (Pydantic, SQLAlchemy 2.x, Alembic)
              |                 \
              v                  v
      Supabase PostgreSQL   Supabase Storage (images)
```

## Frontend
- Server-rendered shop pages for SEO (metadata, Open Graph, sitemap, robots).
- Cart: Zustand store persisted to localStorage; prices shown are re-validated by the API.
- Forms: React Hook Form + Zod. Admin data fetching: TanStack Query.
- No secrets in frontend code; only the public API base URL.

## Backend layers
`api/` (routers, dependencies) -> `services/` (business rules) -> `repositories/` (SQLAlchemy queries) -> `models/`.
`schemas/` holds Pydantic request/response models. `core/` holds config, security, rate limiting.
`integrations/payments` and `integrations/shipping` define `PaymentProvider` / `ShippingProvider`
interfaces with manual implementations; real providers are added later without changing services.

## Key flows
- **Checkout:** one DB transaction: validate items -> lock inventory -> recompute totals and coupon ->
  create order with snapshots of name, weight, unit price -> write first `order_status_history` row ->
  payment status `pending`.
- **Order lookup:** order number + mobile must match; identical generic response on any failure; rate limited.
- **Admin auth:** Argon2 password hashing, short-lived JWT in httpOnly/Secure/SameSite cookies with refresh,
  roles `super_admin` / `manager` / `staff` enforced by API dependencies.
- **Images:** admin uploads via backend; service-role key stays server-side; WebP sizes (thumb/card/detail) generated.

## Security
Input validation (Pydantic), parameterised queries (SQLAlchemy), CORS allow-list, rate limits on login,
order lookup, coupon validation and order creation, secrets only in environment variables, no card data stored,
RLS enabled on Supabase tables with no public policies (backend is the only DB client).

## Planned dependencies (beyond the approved stack)
Zustand, React Hook Form, Zod, TanStack Query, Playwright, uv, pytest, httpx, slowapi, argon2-cffi, pydantic-settings.
