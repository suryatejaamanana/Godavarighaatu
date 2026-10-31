"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, Boxes, Package, PackageX, Tags } from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/admin/page-header";
import { ErrorState, LoadingRows } from "@/components/admin/query-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAdmin } from "@/hooks/use-admin";
import { getSummary, listLowStock } from "@/services/admin";

function Stat({ label, value, icon: Icon, tone }: { label: string; value: number; icon: typeof Package; tone?: "warn" }) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 p-4">
        <div className={`rounded-lg p-2.5 ${tone === "warn" ? "bg-brand-orange/15 text-brand-orange" : "bg-brand-red/10 text-brand-red"}`}>
          <Icon className="size-5" />
        </div>
        <div>
          <div className="text-2xl font-semibold leading-none">{value}</div>
          <div className="mt-1 text-sm text-muted-foreground">{label}</div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { data: admin } = useAdmin();
  const summary = useQuery({ queryKey: ["summary"], queryFn: getSummary });
  const lowStock = useQuery({ queryKey: ["low-stock"], queryFn: listLowStock });

  return (
    <>
      <PageHeader
        title={`Welcome${admin?.full_name ? `, ${admin.full_name}` : ""}`}
        description="Overview of your catalog and stock."
        actions={
          <Button render={<Link href="/admin/products/new" />} nativeButton={false}>
            Add product
          </Button>
        }
      />

      {summary.isPending ? (
        <LoadingRows rows={2} />
      ) : summary.isError ? (
        <ErrorState error={summary.error} onRetry={() => summary.refetch()} />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <Stat label="Products" value={summary.data.products_total} icon={Package} />
          <Stat label="Active (on sale)" value={summary.data.products_active} icon={Package} />
          <Stat label="Categories" value={summary.data.categories_total} icon={Tags} />
          <Stat label="Hidden / archived" value={summary.data.products_inactive + summary.data.products_archived} icon={Boxes} />
          <Stat label="Out of stock" value={summary.data.variants_out_of_stock} icon={PackageX} tone="warn" />
          <Stat label="Low stock" value={summary.data.variants_low_stock} icon={AlertTriangle} tone="warn" />
        </div>
      )}

      <Card className="mt-6">
        <CardHeader>
          <div className="flex items-center justify-between gap-3">
            <CardTitle>Needs restocking</CardTitle>
            <Button variant="outline" size="sm" render={<Link href="/admin/inventory" />} nativeButton={false}>
              Manage inventory
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {lowStock.isPending ? (
            <LoadingRows rows={3} />
          ) : lowStock.isError ? (
            <ErrorState error={lowStock.error} onRetry={() => lowStock.refetch()} />
          ) : lowStock.data.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">Everything is well stocked.</p>
          ) : (
            <ul className="divide-y">
              {lowStock.data.slice(0, 8).map((item) => (
                <li key={item.variant_id} className="flex items-center justify-between gap-3 py-2.5 text-sm">
                  <Link href={`/admin/products/${item.product_id}`} className="font-medium hover:underline">
                    {item.product_name} <span className="text-muted-foreground">· {item.weight}</span>
                  </Link>
                  <Badge variant={item.available <= 0 ? "destructive" : "secondary"}>
                    {item.available <= 0 ? "Out of stock" : `${item.available} left`}
                  </Badge>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <p className="mt-6 text-xs text-muted-foreground">
        Order and revenue statistics will appear here once customer ordering is built.
      </p>
    </>
  );
}
