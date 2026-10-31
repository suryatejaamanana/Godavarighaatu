# Development Phases

Each phase ends with passing tests, updated docs, a run/verify guide and an honest report of anything incomplete.
No phase starts without the owner's approval.

| Phase | Scope | Status |
|---|---|---|
| 1 | Requirements, architecture, stack, DB plan, structure | Approved |
| 2 | Project init and dev environment | Complete, awaiting owner review |
| 3 | DB models, relationships, Alembic migrations | Not started |
| 4 | Backend APIs and business logic | Not started |
| 5 | Admin authentication and authorization | Not started |
| 6 | Admin dashboard and product management (incl. image upload) | Not started |
| 7 | Customer homepage and product browsing | Not started |
| 8 | Product details and cart | Not started |
| 9 | Checkout and order management | Not started |
| 10 | Offers, coupons, combos (incl. site-wide percentage offer) | Not started |
| 11 | WhatsApp and content pages | Not started |
| 12 | Testing, security, performance | Not started |
| 13 | Deployment preparation | Not started |

## Future (separate projects)
Payment gateway, shipping provider, OTP/SMS order verification (decision pending).

## Credentials needed later
Supabase project (DB URL, project URL, service-role key, Storage bucket), JWT secret, first admin credentials,
allowed frontend origins; later hosting, domain, payment, shipping, email/SMS providers.

## Missing business information (placeholders until supplied)
Product list, prices, ingredients, delivery regions, shipping charges, GST/invoice details,
contact details, WhatsApp number, policy text, logo (SVG), product photographs.

## Risks
- Order lookup without OTP is a weak check (D7): mitigated by rate limiting and generic errors.
- Stock overselling: row locks inside the order transaction.
- Fake or abandoned pay-later orders: manual admin confirmation, rate limits.
- Supabase connections: pooler for the app, direct connection for Alembic.
- SVG uploads can carry scripts: sanitize, admin-only.
