# API (Phases 4-5: catalog, inventory, admin auth)

Base path `/api/v1`. Interactive docs: `/docs` when the server runs. Errors are `{"detail": "..."}`
(404 not found, 409 conflict, 422 validation/business rule, 503 unavailable).

## Admin authentication and roles (Phase 5)
Every `/api/v1/admin/*` route requires a logged-in admin, except `auth/login`, `auth/refresh` and `auth/logout`.

- **Tokens:** a short-lived access JWT (15 min) and a refresh JWT (7 days, sliding, 30-day absolute cap), both in
  `httpOnly` cookies (`gg_access` for `/api/v1`, `gg_refresh` only for `/api/v1/admin/auth`). Tokens are never
  returned in response bodies, so page JavaScript cannot read them. Cookies are `Secure` outside development.
- **Server-side sessions:** each login creates a row in `admin_sessions`. Logout, deactivation and password reset
  revoke it, so a copied access token stops working immediately. On every request the admin and session are loaded
  from the database, so role changes and deactivation apply at once.
- **Refresh rotation:** each refresh issues a new refresh token. Replaying an old one revokes the whole session.
- **CSRF:** cookies are `SameSite=Lax`, and cookie-authenticated unsafe requests (POST/PUT/PATCH/DELETE, including
  login) must carry an `Origin` header from `CORS_ORIGINS`. Browsers do this automatically; `curl` needs
  `-H "Origin: http://localhost:3000"`.
- **Passwords:** Argon2id, minimum 10 characters. Login errors are identical for unknown email, wrong password and
  inactive account, and unknown emails cost the same time as wrong passwords.
- **Rate limits (per IP):** login 5/minute, refresh 30/minute (`LOGIN_RATE_LIMIT`, `REFRESH_RATE_LIMIT`).
- **Fails closed:** with no `JWT_SECRET` login returns 503; outside development the app refuses to start with a weak
  secret, non-secure cookies or a wildcard CORS origin.

Roles (higher includes lower): `staff` < `manager` < `super_admin`.

| Role | Can do |
|---|---|
| staff | read all catalog data, view and change stock (set, adjust, low-stock) |
| manager | everything staff can, plus create, edit, archive and delete categories, products and variants |
| super_admin | everything manager can, plus manage admin accounts |

New admin routes must declare a role (`require_staff`, `require_manager` or `require_super_admin` from
`app/api/deps.py`). Tests fail if an admin route is unauthenticated or missing from the role matrix.

| Method | Path | Role | Notes |
|---|---|---|---|
| POST | `/admin/auth/login` | public | `{email, password}`; sets cookies; returns the admin profile |
| POST | `/admin/auth/refresh` | refresh cookie | rotates both tokens |
| POST | `/admin/auth/logout` | any | revokes the session, clears cookies; idempotent |
| GET | `/admin/auth/me` | staff | current admin |
| GET/POST | `/admin/users` | super_admin | list / create admins |
| PATCH | `/admin/users/{id}` | super_admin | name, role, active, password. Cannot change your own role or active status. Deactivating or resetting a password ends that admin's sessions |

Errors: 401 not authenticated or invalid token, 403 wrong role or origin, 429 rate limited.

## Storefront (public)
| Method | Path | Notes |
|---|---|---|
| GET | `/categories` | active categories |
| GET | `/products` | `q`, `category` (slug), `sort` (newest, popular, price_asc, price_desc), `page`, `page_size` (max 60). Active products in active categories only |
| GET | `/products/{slug}` | active variants only; availability (`in_stock`, `available_quantity`), no raw stock or status |
| GET | `/products/{slug}/related` | up to 4 from the same category |

## Admin catalog (role: staff reads, manager writes, staff may change stock)
| Method | Path | Notes |
|---|---|---|
| GET/POST | `/admin/categories` | create generates slug from name if omitted |
| GET/PATCH/DELETE | `/admin/categories/{id}` | delete refused (409) while it has products |
| GET/POST | `/admin/products` | list filters: `q`, `category_id`, `status`, `sort`; create accepts nested `variants` with initial stock |
| GET/PATCH | `/admin/products/{id}` | PATCH: omitted fields unchanged; required fields cannot be null |
| POST | `/admin/products/{id}/archive`, `/restore` | restore sets status to `inactive` |
| GET/POST | `/admin/products/{id}/variants` | one variant per weight (250g, 500g, 1kg); price per variant |
| GET/PATCH/DELETE | `/admin/variants/{id}` | weight is immutable; `compare_at_price >= price` |
| PUT | `/admin/variants/{id}/inventory` | set quantity and low-stock threshold |
| POST | `/admin/variants/{id}/inventory/adjustments` | `{delta}`; row-locked; never below 0 or below reserved |
| GET | `/admin/inventory/low-stock` | available <= threshold |

Not yet implemented: image upload (Phase 6), cart/checkout/orders (Phase 9), coupons and combos (Phase 10).
