# API (Phase 4: catalog and inventory)

Base path `/api/v1`. Interactive docs: `/docs` when the server runs. Errors are `{"detail": "..."}`
(404 not found, 409 conflict, 422 validation/business rule, 503 unavailable).

## Admin protection (IMPORTANT)
All `/api/v1/admin/*` routes use the `require_admin` dependency (`app/api/deps.py`). Real JWT auth arrives in
Phase 5. Until then these routes work **only when `APP_ENV=development`** and return 503 otherwise. Never deploy
before Phase 5.

## Storefront (public)
| Method | Path | Notes |
|---|---|---|
| GET | `/categories` | active categories |
| GET | `/products` | `q`, `category` (slug), `sort` (newest, popular, price_asc, price_desc), `page`, `page_size` (max 60). Active products in active categories only |
| GET | `/products/{slug}` | active variants only; availability (`in_stock`, `available_quantity`), no raw stock or status |
| GET | `/products/{slug}/related` | up to 4 from the same category |

## Admin
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

Not in this phase: image upload (Phase 6), admin auth (Phase 5), cart/checkout/orders (Phase 9), coupons and combos (Phase 10).
