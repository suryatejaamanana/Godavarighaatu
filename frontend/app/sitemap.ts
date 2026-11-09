import type { MetadataRoute } from "next";
import { absoluteUrl } from "@/lib/seo";
import { getAllProductSlugs, getCategories } from "@/lib/shop-api";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const [categories, slugs] = await Promise.all([getCategories(), getAllProductSlugs()]);
  return [
    { url: absoluteUrl("/"), changeFrequency: "daily", priority: 1 },
    { url: absoluteUrl("/products"), changeFrequency: "daily", priority: 0.9 },
    ...categories.map((c) => ({ url: absoluteUrl(`/category/${c.slug}`), changeFrequency: "weekly" as const, priority: 0.8 })),
    ...slugs.map((slug) => ({ url: absoluteUrl(`/products/${slug}`), changeFrequency: "weekly" as const, priority: 0.7 })),
  ];
}
