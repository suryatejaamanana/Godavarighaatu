"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { ImageIcon, Plus, Search } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { PageHeader } from "@/components/admin/page-header";
import { EmptyState, ErrorState, LoadingRows } from "@/components/admin/query-state";
import { StatusBadge } from "@/components/admin/status-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { NativeSelect } from "@/components/ui/native-select";
import { useCan } from "@/hooks/use-admin";
import { useDebounced } from "@/hooks/use-debounced";
import { formatPrice } from "@/lib/format";
import { listCategories, listProducts } from "@/services/admin";
import type { Product, ProductStatus } from "@/types/api";

const PAGE_SIZE = 20;

function priceRange(p: Product) {
  const prices = p.variants.filter((v) => v.is_active).map((v) => Number(v.price));
  if (prices.length === 0) return "No prices";
  const [min, max] = [Math.min(...prices), Math.max(...prices)];
  return min === max ? formatPrice(min) : `${formatPrice(min)} – ${formatPrice(max)}`;
}

function stockSummary(p: Product) {
  const active = p.variants.filter((v) => v.is_active);
  if (active.length === 0) return <Badge variant="secondary">No variants</Badge>;
  const out = active.filter((v) => (v.inventory?.available ?? 0) <= 0).length;
  if (out === active.length) return <Badge variant="destructive">Out of stock</Badge>;
  if (out > 0) return <Badge variant="secondary">{out} sold out</Badge>;
  return <Badge variant="outline">In stock</Badge>;
}

export default function ProductsPage() {
  const canEdit = useCan("manager");
  const [search, setSearch] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [status, setStatus] = useState<ProductStatus | "">("");
  const [page, setPage] = useState(1);
  const q = useDebounced(search);

  const categories = useQuery({ queryKey: ["categories"], queryFn: listCategories });
  const products = useQuery({
    queryKey: ["products", { q, categoryId, status, page }],
    queryFn: () => listProducts({ q, category_id: categoryId, status, page, page_size: PAGE_SIZE }),
    placeholderData: keepPreviousData,
  });
  const totalPages = products.data ? Math.max(1, Math.ceil(products.data.total / PAGE_SIZE)) : 1;
  const categoryName = (id: string) => categories.data?.find((c) => c.id === id)?.name ?? "—";
  const resetPage = <T,>(set: (v: T) => void) => (v: T) => {
    set(v);
    setPage(1);
  };

  return (
    <>
      <PageHeader
        title="Products"
        actions={
          canEdit && (
            <Button render={<Link href="/admin/products/new" />} nativeButton={false}>
              <Plus /> Add product
            </Button>
          )
        }
      />

      <div className="mb-4 grid gap-2 sm:grid-cols-[1fr_12rem_10rem]">
        <div className="relative">
          <Search className="pointer-events-none absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
          <Input
            aria-label="Search products"
            placeholder="Search by name…"
            className="h-9 pl-8"
            value={search}
            onChange={(e) => resetPage(setSearch)(e.target.value)}
          />
        </div>
        <NativeSelect aria-label="Filter by category" value={categoryId} onChange={(e) => resetPage(setCategoryId)(e.target.value)}>
          <option value="">All categories</option>
          {categories.data?.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </NativeSelect>
        <NativeSelect aria-label="Filter by status" value={status} onChange={(e) => resetPage(setStatus)(e.target.value as ProductStatus | "")}>
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Hidden</option>
          <option value="archived">Archived</option>
        </NativeSelect>
      </div>

      {products.isPending ? (
        <LoadingRows />
      ) : products.isError ? (
        <ErrorState error={products.error} onRetry={() => products.refetch()} />
      ) : products.data.items.length === 0 ? (
        <EmptyState
          title={q || categoryId || status ? "No products match your filters" : "No products yet"}
          hint={q || categoryId || status ? "Try clearing the search or filters." : "Add your first pickle to start selling."}
          action={!q && !categoryId && !status && canEdit && <Button render={<Link href="/admin/products/new" />} nativeButton={false}>Add product</Button>}
        />
      ) : (
        <>
          <ul className="divide-y rounded-lg border bg-card">
            {products.data.items.map((p) => {
              const image = p.images.find((i) => i.is_primary) ?? p.images[0];
              return (
                <li key={p.id}>
                  <Link href={`/admin/products/${p.id}`} className="flex items-center gap-3 p-3 transition-colors hover:bg-muted/50 sm:gap-4 sm:p-4">
                    <div className="flex size-14 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-muted">
                      {image ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={image.thumb_url} alt="" className="size-full object-cover" loading="lazy" />
                      ) : (
                        <ImageIcon className="size-5 text-muted-foreground" aria-label="No image" />
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="truncate font-medium">
                        {p.name} {p.name_te && <span className="text-muted-foreground">· {p.name_te}</span>}
                      </div>
                      <div className="truncate text-xs text-muted-foreground">
                        {categoryName(p.category_id)} · {priceRange(p)}
                      </div>
                      <div className="mt-1.5 flex flex-wrap gap-1.5 sm:hidden">
                        <StatusBadge status={p.status} />
                        {stockSummary(p)}
                      </div>
                    </div>
                    <div className="hidden items-center gap-2 sm:flex">
                      {p.is_featured && <Badge variant="outline">Featured</Badge>}
                      {p.is_best_seller && <Badge variant="outline">Best seller</Badge>}
                      {stockSummary(p)}
                      <StatusBadge status={p.status} />
                    </div>
                  </Link>
                </li>
              );
            })}
          </ul>
          <div className="mt-4 flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              {products.data.total} product{products.data.total === 1 ? "" : "s"}
            </span>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                Previous
              </Button>
              <span>
                Page {page} of {totalPages}
              </span>
              <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
                Next
              </Button>
            </div>
          </div>
        </>
      )}
    </>
  );
}
