# Database Design (Phase 1 proposal)

Conventions: UUID primary keys, `created_at` / `updated_at` on every table, money as `NUMERIC(12,2)`,
translatable text as `x` + `x_te`.

| Group | Table | Key columns / constraints |
|---|---|---|
| Catalog | categories | slug (unique), name, name_te, sort_order, is_active |
| | products | slug (unique), category_id, name, name_te, description, ingredients, preparation, storage, shelf_life, is_featured, is_best_seller, status (active/inactive/archived), SEO fields |
| | product_images | product_id, url, alt, sort_order, is_primary |
| | product_variants | product_id, weight (250g/500g/1kg), price, compare_at_price, sku (unique), unique(product_id, weight) |
| | inventory | variant_id (unique), quantity, reserved, low_stock_threshold |
| People | admins | email (unique), password_hash, role, is_active |
| | customers | mobile (unique), name, email |
| | addresses | customer_id, house, street, village_city, district, state, pin_code |
| Orders | orders | order_number (unique), customer_id, address snapshot, subtotal, discount, total, order_status, payment_status, coupon_id, delivery_instructions |
| | order_items | order_id, product_id, variant_id, name/weight/unit_price snapshots, quantity, line_total |
| | order_status_history | order_id, from_status, to_status, changed_by (admin), note |
| Payment/shipping | payments | order_id, provider, method, amount, status, provider_reference, raw_payload (JSONB) |
| | shipments | order_id, carrier, tracking_number, tracking_url, status, provider_reference |
| Offers | coupons | code (unique), type (percent/fixed), value, min_purchase, usage_limit, used_count, starts_at, ends_at, is_active |
| | combo_offers | name, rule_type (fixed_products/any_n), n, price, is_available |
| | combo_offer_items | combo_id, product_id (and optional category_id for any-N rules) |
| Content | reviews | product_id, name, rating, comment, is_approved |
| | banners | title, title_te, image_url, link, sort_order, is_active, starts_at, ends_at |
| | website_settings | key (unique), value (JSONB): brand name, tagline, logo, contact, WhatsApp number, policies |

Not created (D1): `carts`, `cart_items`.

Order statuses: pending, confirmed, processing, packed, shipped, out_for_delivery, delivered, cancelled, returned.
Payment statuses: pending, paid, failed, refunded.

Indexes: foreign keys; orders(order_status, created_at); products(category_id, status);
trigram index on product name for search; unique indexes listed above.

## Implemented (Phase 3)

Models: `backend/app/models/` (`catalog`, `people`, `orders`, `offers`, `content`, plus `base`, `enums`, `types`).
Migration: `backend/alembic/versions/0001_initial_schema.py` (19 tables).

Choices made while implementing:
- Enums are stored as `VARCHAR` + `CHECK` (not native PG enums), so adding a status later is a simple migration.
- Constraint/index names follow a naming convention (`ix_`, `uq_`, `ck_`, `fk_`, `pk_`) for stable migrations.
- `gen_random_uuid()` is the server default for ids; the migration enables `pg_trgm` for product search.
- Extra product columns beyond the Phase 1 sketch: `short_description`, `badges`, `is_new_arrival`, `sold_count`
  (popularity sorting), `*_te` Telugu variants of every text field.
- Orders carry delivery-address snapshot columns (`ship_*`) so later customer edits never change past orders.
- `order_items.product_id` / `variant_id` become NULL if a product is deleted; name, weight and unit price remain.
- `reviews.product_id` is nullable so general (homepage) testimonials are possible.
- `combo_offer_items` holds either a product or a category (exactly one), covering fixed bundles and "any N" combos.
- No separate site-wide `offers` table yet. The poster's "10% off all pickles" will be added in Phase 10 (new migration).
- `admin_sessions` (migration 0002, Phase 5): one row per admin login (`admin_id`, hash of the current refresh token's
  jti, `expires_at`, `revoked_at`, `last_used_at`, `user_agent`). Total tables: 20. Expired sessions are never
  accepted; a periodic cleanup job is not implemented yet.
