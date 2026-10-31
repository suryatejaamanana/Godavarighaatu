"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { PageHeader } from "@/components/admin/page-header";
import { EmptyState, ErrorState, LoadingRows } from "@/components/admin/query-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { StockEditor } from "@/components/admin/stock-editor";
import { listProducts } from "@/services/admin";

export default function InventoryPage() {
  const [lowOnly, setLowOnly] = useState(false);
  const products = useQuery({
    queryKey: ["products", "inventory"],
    queryFn: () => listProducts({ status: "active", page_size: 100 }),
  });

  const rows =
    products.data?.items.flatMap((p) =>
      p.variants
        .filter((v) => v.is_active)
        .map((v) => ({ product: p, variant: v })),
    ) ?? [];
  const shown = lowOnly ? rows.filter((r) => r.variant.inventory && r.variant.inventory.available <= r.variant.inventory.low_stock_threshold) : rows;

  return (
    <>
      <PageHeader
        title="Inventory"
        description="Stock for every active variant. Use − / + for quick changes, or type a number and Save."
        actions={
          <Button variant={lowOnly ? "default" : "outline"} onClick={() => setLowOnly((v) => !v)} aria-pressed={lowOnly}>
            Low stock only
          </Button>
        }
      />
      {products.isPending ? (
        <LoadingRows />
      ) : products.isError ? (
        <ErrorState error={products.error} onRetry={() => products.refetch()} />
      ) : shown.length === 0 ? (
        <EmptyState
          title={lowOnly ? "Nothing is running low" : "No stock to manage yet"}
          hint={lowOnly ? undefined : "Add variants (250g / 500g / 1kg) to your active products first."}
        />
      ) : (
        <ul className="divide-y rounded-lg border bg-card">
          {shown.map(({ product, variant }) => {
            const inv = variant.inventory;
            const low = inv && inv.available <= inv.low_stock_threshold;
            return (
              <li key={variant.id} className="flex flex-wrap items-center gap-x-4 gap-y-2 p-3 sm:p-4">
                <div className="min-w-0 flex-1 basis-48">
                  <Link href={`/admin/products/${product.id}`} className="font-medium hover:underline">
                    {product.name}
                  </Link>
                  <div className="text-xs text-muted-foreground">{variant.weight}</div>
                </div>
                {low && <Badge variant={inv.available <= 0 ? "destructive" : "secondary"}>{inv.available <= 0 ? "Out of stock" : "Low"}</Badge>}
                <StockEditor variant={variant} label={`${product.name} ${variant.weight}`} />
              </li>
            );
          })}
        </ul>
      )}
    </>
  );
}
