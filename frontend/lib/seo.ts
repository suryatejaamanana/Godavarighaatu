import { SITE_URL } from "@/lib/config";
import type { ShopProduct } from "@/types/shop";

export const absoluteUrl = (path: string) => `${SITE_URL}${path.startsWith("/") ? path : `/${path}`}`;

/** Plain-text meta description of at most ~155 characters, cut at a word boundary. */
export function metaDescription(text: string | null | undefined, fallback: string, max = 155): string {
  const clean = (text ?? "").replace(/\s+/g, " ").trim() || fallback;
  if (clean.length <= max) return clean;
  const cut = clean.slice(0, max - 1);
  return `${cut.slice(0, cut.lastIndexOf(" ") > 60 ? cut.lastIndexOf(" ") : cut.length)}…`;
}

export const primaryImage = (p: ShopProduct) => p.images.find((i) => i.is_primary) ?? p.images[0] ?? null;

/** schema.org Product with an offer range across sizes. Only facts we actually have; no ratings. */
export function productJsonLd(p: ShopProduct, brandName: string) {
  const prices = p.variants.map((v) => Number(v.price));
  const image = p.images.map((i) => i.url);
  return {
    "@context": "https://schema.org",
    "@type": "Product",
    name: p.name,
    description: metaDescription(p.description ?? p.short_description, p.name, 5000),
    url: absoluteUrl(`/products/${p.slug}`),
    category: p.category.name,
    brand: { "@type": "Brand", name: brandName },
    ...(image.length > 0 && { image }),
    ...(prices.length > 0 && {
      offers: {
        "@type": prices.length > 1 ? "AggregateOffer" : "Offer",
        priceCurrency: "INR",
        ...(prices.length > 1
          ? { lowPrice: Math.min(...prices).toFixed(2), highPrice: Math.max(...prices).toFixed(2), offerCount: prices.length }
          : { price: prices[0].toFixed(2) }),
        availability: p.in_stock ? "https://schema.org/InStock" : "https://schema.org/OutOfStock",
        url: absoluteUrl(`/products/${p.slug}`),
      },
    }),
  };
}

/** JSON for a <script type="application/ld+json">. Escapes "<" so content can never close the script tag. */
export const jsonLdString = (data: unknown) => JSON.stringify(data).replace(/</g, "\\u003c");
