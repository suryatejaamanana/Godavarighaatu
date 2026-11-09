import { cacheLife } from "next/cache";
import { API_BASE_URL } from "@/lib/config";
import type { ProductQuery, ShopCategory, ShopPage, ShopProduct } from "@/types/shop";

// Server-side data access for the storefront. Every function is cached ("use cache") so pages are
// fast and the API is not hit on every visit; changes made in the admin appear within a few minutes.
// A failing API throws (the route's error.tsx handles it) instead of caching an empty catalogue.

async function get<T>(path: string): Promise<T | null> {
  const res = await fetch(`${API_BASE_URL}${path}`, { headers: { Accept: "application/json" } });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Storefront API ${res.status} for ${path}`);
  return (await res.json()) as T;
}

function qs(params: Record<string, string | number | boolean | undefined>): string {
  const sp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "" && value !== false) sp.set(key, String(value));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

export async function getCategories(): Promise<ShopCategory[]> {
  "use cache";
  cacheLife("minutes");
  return (await get<ShopCategory[]>("/categories")) ?? [];
}

export async function getProducts(query: ProductQuery = {}): Promise<ShopPage<ShopProduct>> {
  "use cache";
  cacheLife("minutes");
  const page = await get<ShopPage<ShopProduct>>(`/products${qs({ ...query })}`);
  return page ?? { items: [], total: 0, page: 1, page_size: query.page_size ?? 12 };
}

export async function getProduct(slug: string): Promise<ShopProduct | null> {
  "use cache";
  cacheLife("minutes");
  return get<ShopProduct>(`/products/${encodeURIComponent(slug)}`);
}

export async function getRelatedProducts(slug: string): Promise<ShopProduct[]> {
  "use cache";
  cacheLife("minutes");
  return (await get<ShopProduct[]>(`/products/${encodeURIComponent(slug)}/related`)) ?? [];
}

/** Every active product slug (for sitemap and static params). Pages through the API. */
export async function getAllProductSlugs(): Promise<string[]> {
  "use cache";
  cacheLife("hours");
  const slugs: string[] = [];
  for (let page = 1; page <= 50; page++) {
    const result = await get<ShopPage<ShopProduct>>(`/products${qs({ page, page_size: 60 })}`);
    if (!result || result.items.length === 0) break;
    slugs.push(...result.items.map((p) => p.slug));
    if (slugs.length >= result.total) break;
  }
  return slugs;
}
