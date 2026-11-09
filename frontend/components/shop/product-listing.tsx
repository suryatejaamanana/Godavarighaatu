import Link from "next/link";
import { Suspense } from "react";
import { Pagination } from "@/components/shop/pagination";
import { ProductGrid } from "@/components/shop/product-card";
import { SortSelect } from "@/components/shop/sort-select";
import { getCategories, getProducts } from "@/lib/shop-api";
import { cn } from "@/lib/utils";
import type { ProductSort } from "@/types/shop";

const PAGE_SIZE = 12;
const SORTS: ProductSort[] = ["newest", "popular", "price_asc", "price_desc"];

export interface ListingParams {
  q?: string;
  sort?: string;
  page?: string;
  best_seller?: string;
  new_arrival?: string;
  featured?: string;
}

export function parseListingParams(raw: Record<string, string | string[] | undefined>): ListingParams {
  const one = (k: string) => (Array.isArray(raw[k]) ? raw[k][0] : (raw[k] as string | undefined));
  return {
    q: one("q")?.slice(0, 100),
    sort: one("sort"),
    page: one("page"),
    best_seller: one("best_seller"),
    new_arrival: one("new_arrival"),
    featured: one("featured"),
  };
}

/** Product grid with category pills, search summary, sorting and pagination. Reads only API data. */
export async function ProductListing({ categorySlug, params }: { categorySlug?: string; params: ListingParams }) {
  const sort = (SORTS as string[]).includes(params.sort ?? "") ? (params.sort as ProductSort) : "newest";
  const page = Math.max(1, Math.min(500, Number.parseInt(params.page ?? "1", 10) || 1));
  const [categories, result] = await Promise.all([
    getCategories(),
    getProducts({
      q: params.q?.trim() || undefined,
      category: categorySlug,
      best_seller: params.best_seller === "true",
      new_arrival: params.new_arrival === "true",
      featured: params.featured === "true",
      sort,
      page,
      page_size: PAGE_SIZE,
    }),
  ]);
  const totalPages = Math.max(1, Math.ceil(result.total / PAGE_SIZE));
  const keep: Record<string, string> = {};
  if (params.q) keep.q = params.q;
  if (sort !== "newest") keep.sort = sort;
  for (const k of ["best_seller", "new_arrival", "featured"] as const) if (params[k] === "true") keep[k] = "true";
  const base = categorySlug ? `/category/${categorySlug}` : "/products";
  const pill = "inline-flex h-10 shrink-0 items-center rounded-full border border-brand-brown/20 bg-white px-4 text-sm font-semibold hover:bg-brand-gold/30";

  return (
    <>
      <nav aria-label="Categories" className="-mx-4 mb-5 flex gap-2 overflow-x-auto px-4 pb-2 sm:mx-0 sm:flex-wrap sm:px-0">
        <Link href="/products" aria-current={!categorySlug ? "page" : undefined} className={cn(pill, !categorySlug && "border-brand-red bg-brand-red text-brand-cream hover:bg-brand-red")}>
          All
        </Link>
        {categories.map((c) => (
          <Link
            key={c.slug}
            href={`/category/${c.slug}`}
            aria-current={c.slug === categorySlug ? "page" : undefined}
            className={cn(pill, c.slug === categorySlug && "border-brand-red bg-brand-red text-brand-cream hover:bg-brand-red")}
          >
            {c.name}
          </Link>
        ))}
      </nav>

      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground" aria-live="polite">
          {result.total === 0
            ? "No pickles found"
            : `${result.total} pickle${result.total === 1 ? "" : "s"}`}
          {params.q && (
            <>
              {" "}
              for “<strong>{params.q}</strong>”
            </>
          )}
        </p>
        <Suspense>
          <SortSelect value={sort} />
        </Suspense>
      </div>

      {result.items.length === 0 ? (
        <div className="rounded-2xl border-2 border-dashed border-brand-brown/20 p-10 text-center">
          <p className="font-display text-2xl font-semibold uppercase text-brand-red">Nothing here yet</p>
          <p className="mt-2 text-muted-foreground">
            {params.q ? "Try a different word, or browse all our pickles." : "Please check back soon, or browse another category."}
          </p>
          <Link href="/products" className="mt-5 inline-flex h-11 items-center rounded-full bg-brand-red px-6 font-semibold text-brand-cream">
            See all pickles
          </Link>
        </div>
      ) : (
        <ProductGrid products={result.items} priorityCount={4} />
      )}
      <Pagination base={base} params={keep} page={page} totalPages={totalPages} />
    </>
  );
}
