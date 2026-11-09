# Decisions Log

Approved by the project owner at the end of Phase 1.

| # | Decision | Notes |
|---|----------|-------|
| D1 | Guest cart is **browser-only** (localStorage via Zustand `persist`). | No `carts` / `cart_items` tables for now. Cart survives refresh; no login needed. |
| D2 | **Server is the source of truth for money.** | At checkout the backend re-fetches variants, recalculates prices, discounts, coupons and validates quantities/stock. Client totals are display-only. |
| D3 | Initial brand name: **Godavari Ghaatu (గోదావరి ఘాటు)**. | Taken from the poster. Name, tagline, logo, badges are stored in `website_settings`, never hardcoded. |
| D4 | Tagline: "Authentic Andhra Spice in Every Spoon"; label "Home Made Pickles". | Configurable. |
| D5 | Visual identity from the poster: red-orange gradient, golden-yellow condensed headings, white Telugu display type, dark-red ribbon labels, rounded cards. | Palette: #A51F18, #F15A24, #FFC928, #FFF8ED, #35251E. |
| D6 | Product images (Full HD) and SVG brand assets arrive later. | Admin upload to Supabase Storage; resized WebP variants generated; SVG only for admin-uploaded brand assets, sanitized. Placeholders marked clearly until supplied. |
| D7 | **Order lookup = order number + mobile number match.** No OTP/SMS yet. | Rate limited; generic error for any mismatch. Verification method to be decided later (see risks). |
| D8 | Telugu + English content: translatable fields use `name` / `name_te` style columns. | Products, categories, banners, FAQ. |
| D9 | No payment gateway or shipping provider integration. | `integrations/` defines interfaces with manual implementations only. Payment status starts Pending, never auto-Paid. |
| D10 | Target Python 3.12/3.13 for the backend (dev machine has 3.14). | Avoids library compatibility problems. Confirmed 3.13 by owner. |
| D11 | Product and banner fields are bilingual English/Telugu. | Confirmed by owner at start of Phase 2. |
| D12 | Admin auth: JWT access (15 min) + rotating refresh (7 days) in httpOnly cookies, backed by an `admin_sessions` table. | Owner requested JWT access/refresh tokens. Server-side sessions give real logout and replay detection. Tokens are not returned in JSON. |
| D13 | Roles: staff = read + stock; manager = catalog writes; super_admin = also manages admins. | Proposed by the assistant in Phase 5; adjust if the business wants different permissions. |
| D14 | First admin is created via CLI (`python -m app.cli create-admin`), never via a public endpoint or seed password. | |
| D15 | Product photos: JPEG/PNG/WebP only, re-encoded to WebP (1920/600/200px). SVG is not accepted for product photos. | SVG can contain scripts. SVG brand assets (logo) will be added as static files in `frontend/public/brand/` by the developer, not through uploads. |
| D16 | Image storage is pluggable (`local` for development, `supabase` for production). | Supabase path is unit-tested with a mocked HTTP transport only; it has not run against a real bucket. |
| D17 | Admin UI: client-side rendered pages that call the API with cookies; the API remains the only security boundary. | The frontend cannot read the API's httpOnly cookies, so the guard is a `/admin/auth/me` check. Hiding buttons by role is a convenience only. |
| D18 | Admin dashboard shows catalog and stock statistics only. | Order and revenue figures need Phase 9; no placeholder numbers are shown. |
| D19 | Storefront uses Next.js Cache Components: API reads are `"use cache"` functions (`lib/shop-api.ts`, `lib/site.ts`) with a 1-minute revalidate / 1-hour expiry. | Admin changes appear on the storefront within about a minute (stale-while-revalidate), not instantly. On-demand revalidation can be added with Phase 13 deployment. The API must be reachable at build time. |
| D20 | Unknown product/category URLs stream a friendly 404 page with `noindex`, status 200; unmatched routes return a real 404. | This is the documented Cache Components behaviour for pages that stream. A hard 404 status for missing products would need a Proxy check. |
| D21 | Product photos are served straight from the API/Supabase as the pre-generated WebP sizes (srcset 200/600/1920), not through the Next.js image optimizer. | Avoids double processing and the optimizer's private-IP restrictions in development. |
| D22 | Phase 7 deliberately has no cart, offers, combos, testimonials, FAQ, WhatsApp button or policy pages. | They need backend features from later phases (cart: 8, offers/combos: 10, content/WhatsApp/policies/FAQ: 11). No inactive buttons or invented reviews are shown. |
| D23 | Brand text (name, tagline, announcement, hero, about) comes from `website_settings` with built-in defaults from the poster. About and value-proposition copy are neutral placeholders limited to facts in the brief. | Owner to supply final copy; editable in Phase 11. |
