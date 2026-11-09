import { describe, expect, it, vi } from "vitest";
import { jsonLdString, metaDescription, primaryImage, productJsonLd } from "@/lib/seo";
import { mergeSettings } from "@/lib/site";
import { formatRupees } from "@/lib/format";
import { BRAND_DEFAULTS } from "@/lib/config";
import type { ShopProduct } from "@/types/shop";

vi.mock("next/cache", () => ({ cacheLife: () => undefined }));

const image = (id: string, primary = false) => ({
  id, url: `https://cdn/${id}/detail.webp`, card_url: `https://cdn/${id}/card.webp`,
  thumb_url: `https://cdn/${id}/thumb.webp`, alt_text: null, is_primary: primary,
});
const variant = (weight: "250g" | "500g" | "1kg", price: string, in_stock = true) => ({
  id: weight, weight, price, compare_at_price: null, discount_percent: 0, in_stock, available_quantity: in_stock ? 10 : 0,
});
const product = (over: Partial<ShopProduct> = {}): ShopProduct => ({
  id: "1", slug: "mango-avakaya", name: "Mango Avakaya", name_te: null, short_description: "Tangy", short_description_te: null,
  description: "A long description", description_te: null, ingredients: null, ingredients_te: null, preparation: null,
  preparation_te: null, storage_instructions: null, storage_instructions_te: null, shelf_life: null, badges: [],
  is_featured: false, is_best_seller: false, is_new_arrival: false, seo_title: null, seo_description: null,
  category: { id: "c", slug: "mango", name: "Mango Pickles", name_te: null, description: null, image_url: null },
  images: [], variants: [variant("250g", "150.00"), variant("500g", "290.00")], in_stock: true, min_price: "150.00",
  max_discount_percent: 0, ...over,
});

describe("metaDescription", () => {
  it("collapses whitespace and returns short text unchanged", () => {
    expect(metaDescription("  Tangy \n  mango   pickle ", "x")).toBe("Tangy mango pickle");
  });
  it("uses the fallback for empty text", () => {
    expect(metaDescription("   ", "Fallback")).toBe("Fallback");
    expect(metaDescription(null, "Fallback")).toBe("Fallback");
  });
  it("cuts long text at a word boundary with an ellipsis, within the limit", () => {
    const out = metaDescription("word ".repeat(100), "x");
    expect(out.length).toBeLessThanOrEqual(155);
    expect(out.endsWith("…")).toBe(true);
    expect(out).not.toMatch(/wor…$/);
  });
});

type LD = {
  "@type": string;
  url: string;
  brand: { name: string };
  image?: string[];
  offers?: Record<string, unknown>;
  aggregateRating?: unknown;
};

describe("productJsonLd", () => {
  it("describes a multi-size product as an AggregateOffer in INR", () => {
    const ld = productJsonLd(product(), "Godavari Ghaatu") as unknown as LD;
    expect(ld["@type"]).toBe("Product");
    expect(ld.offers).toMatchObject({ "@type": "AggregateOffer", priceCurrency: "INR", lowPrice: "150.00", highPrice: "290.00", offerCount: 2 });
    expect(ld.offers?.availability).toBe("https://schema.org/InStock");
    expect(ld.brand.name).toBe("Godavari Ghaatu");
    expect(ld.url).toMatch(/\/products\/mango-avakaya$/);
  });
  it("uses a plain Offer for a single size and reports out of stock", () => {
    const ld = productJsonLd(product({ variants: [variant("1kg", "560.00", false)], in_stock: false }), "B") as unknown as LD;
    expect(ld.offers).toMatchObject({ "@type": "Offer", price: "560.00", availability: "https://schema.org/OutOfStock" });
  });
  it("omits offers and images when there are none, and never invents ratings", () => {
    const ld = productJsonLd(product({ variants: [] }), "B") as unknown as LD;
    expect(ld.offers).toBeUndefined();
    expect(ld.image).toBeUndefined();
    expect(ld.aggregateRating).toBeUndefined();
    expect(productJsonLd(product({ images: [image("a", true)] }), "B")).toHaveProperty("image", ["https://cdn/a/detail.webp"]);
  });
});

describe("jsonLdString", () => {
  it("escapes < so data cannot close the script tag", () => {
    const out = jsonLdString({ name: "</script><script>alert(1)</script>" });
    expect(out).not.toContain("<");
    expect(JSON.parse(out).name).toBe("</script><script>alert(1)</script>");
  });
});

describe("primaryImage", () => {
  it("prefers the primary image, else the first, else null", () => {
    expect(primaryImage(product({ images: [image("a"), image("b", true)] }))?.id).toBe("b");
    expect(primaryImage(product({ images: [image("a"), image("b")] }))?.id).toBe("a");
    expect(primaryImage(product())).toBeNull();
  });
});

describe("mergeSettings", () => {
  it("falls back to built-in defaults", () => {
    expect(mergeSettings(null).name).toBe(BRAND_DEFAULTS.name);
    expect(mergeSettings({}).tagline).toBe(BRAND_DEFAULTS.tagline);
  });
  it("applies database values, trimmed, and ignores blank or non-string values", () => {
    const s = mergeSettings({ brand_name: "  New Name ", announcement: "", brand_tagline: 42, hero_headline: "Hi" });
    expect(s.name).toBe("New Name");
    expect(s.announcement).toBe(BRAND_DEFAULTS.announcement);
    expect(s.tagline).toBe(BRAND_DEFAULTS.tagline);
    expect(s.heroHeadline).toBe("Hi");
  });
});

describe("formatRupees", () => {
  it("drops .00 for whole rupees and keeps paise otherwise", () => {
    expect(formatRupees("350.00")).toBe("₹350");
    expect(formatRupees("350.50")).toBe("₹350.50");
    expect(formatRupees(1200)).toBe("₹1,200");
  });
});
