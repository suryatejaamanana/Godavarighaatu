"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/admin/confirm-dialog";
import { Field } from "@/components/admin/field";
import { StockEditor } from "@/components/admin/stock-editor";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { useCan } from "@/hooks/use-admin";
import { createVariant, deleteVariant, updateVariant } from "@/services/admin";
import { WEIGHTS, type Product, type Variant, type Weight } from "@/types/api";

const MONEY = /^\d{1,8}(\.\d{1,2})?$/;

function useRefresh(productId: string) {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ["product", productId] });
    queryClient.invalidateQueries({ queryKey: ["products"] });
    queryClient.invalidateQueries({ queryKey: ["low-stock"] });
    queryClient.invalidateQueries({ queryKey: ["summary"] });
  };
}

function VariantRow({ variant, productId, canEdit }: { variant: Variant; productId: string; canEdit: boolean }) {
  const refresh = useRefresh(productId);
  const [price, setPrice] = useState(variant.price);
  const [compare, setCompare] = useState(variant.compare_at_price ?? "");
  const [sku, setSku] = useState(variant.sku ?? "");
  const [confirmDelete, setConfirmDelete] = useState(false);

  const priceOk = MONEY.test(price.trim());
  const compareOk = compare.trim() === "" || MONEY.test(compare.trim());
  const dirty = price !== variant.price || compare !== (variant.compare_at_price ?? "") || sku !== (variant.sku ?? "");

  const save = useMutation({
    mutationFn: () =>
      updateVariant(variant.id, {
        price: price.trim(),
        compare_at_price: compare.trim() || null,
        sku: sku.trim() || null,
      }),
    onSuccess: () => {
      toast.success(`${variant.weight} saved`);
      refresh();
    },
    onError: (e: Error) => toast.error(e.message),
  });
  const toggle = useMutation({
    mutationFn: (is_active: boolean) => updateVariant(variant.id, { is_active }),
    onSuccess: refresh,
    onError: (e: Error) => toast.error(e.message),
  });
  const remove = useMutation({
    mutationFn: () => deleteVariant(variant.id),
    onSuccess: () => {
      toast.success(`${variant.weight} removed`);
      refresh();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="space-y-3 rounded-lg border bg-card p-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="text-lg font-semibold">{variant.weight}</div>
        {variant.discount_percent > 0 && <Badge>{variant.discount_percent}% off</Badge>}
        {!variant.is_active && <Badge variant="secondary">Hidden</Badge>}
        {canEdit && (
          <div className="ml-auto flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm">
              <Switch checked={variant.is_active} onCheckedChange={(v) => toggle.mutate(v)} aria-label={`${variant.weight} on sale`} />
              On sale
            </label>
            <Button variant="destructive" size="icon" aria-label={`Delete ${variant.weight} variant`} onClick={() => setConfirmDelete(true)}>
              <Trash2 />
            </Button>
          </div>
        )}
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <Field label="Price (₹)" htmlFor={`price-${variant.id}`} error={priceOk ? undefined : "Enter an amount like 350 or 350.50"}>
          <Input id={`price-${variant.id}`} inputMode="decimal" disabled={!canEdit} value={price} onChange={(e) => setPrice(e.target.value)} />
        </Field>
        <Field label="Original price (₹)" htmlFor={`compare-${variant.id}`} hint="Optional; shows a discount" error={compareOk ? undefined : "Invalid amount"}>
          <Input id={`compare-${variant.id}`} inputMode="decimal" disabled={!canEdit} value={compare} onChange={(e) => setCompare(e.target.value)} />
        </Field>
        <Field label="SKU" htmlFor={`sku-${variant.id}`} hint="Optional">
          <Input id={`sku-${variant.id}`} disabled={!canEdit} value={sku} onChange={(e) => setSku(e.target.value)} />
        </Field>
      </div>
      {canEdit && (
        <Button size="sm" disabled={!dirty || !priceOk || !compareOk || save.isPending} onClick={() => save.mutate()}>
          {save.isPending ? "Saving…" : "Save price"}
        </Button>
      )}
      <div className="border-t pt-3">
        <div className="mb-2 text-sm font-medium">Stock</div>
        <StockEditor variant={variant} label={`${variant.weight}`} />
      </div>
      <ConfirmDialog
        open={confirmDelete}
        onOpenChange={setConfirmDelete}
        title={`Delete the ${variant.weight} variant?`}
        description="Past orders keep their own record of this size and price. To pause selling temporarily, switch it off instead."
        onConfirm={() => remove.mutate()}
      />
    </div>
  );
}

function AddVariant({ product, missing }: { product: Product; missing: Weight[] }) {
  const refresh = useRefresh(product.id);
  const [weight, setWeight] = useState<Weight>(missing[0]);
  const [price, setPrice] = useState("");
  const [quantity, setQuantity] = useState("0");
  const valid = MONEY.test(price.trim()) && /^\d+$/.test(quantity.trim());

  const add = useMutation({
    mutationFn: () => createVariant(product.id, { weight, price: price.trim(), quantity: Number(quantity) }),
    onSuccess: () => {
      toast.success(`${weight} added`);
      setPrice("");
      setQuantity("0");
      refresh();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <form
      className="grid items-end gap-3 rounded-lg border border-dashed p-4 sm:grid-cols-[8rem_1fr_1fr_auto]"
      onSubmit={(e) => {
        e.preventDefault();
        add.mutate();
      }}
    >
      <Field label="Size" htmlFor="new-weight">
        <select id="new-weight" className="h-9 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm" value={weight} onChange={(e) => setWeight(e.target.value as Weight)}>
          {missing.map((w) => (
            <option key={w}>{w}</option>
          ))}
        </select>
      </Field>
      <Field label="Price (₹)" htmlFor="new-price">
        <Input id="new-price" inputMode="decimal" value={price} onChange={(e) => setPrice(e.target.value)} />
      </Field>
      <Field label="Stock" htmlFor="new-qty">
        <Input id="new-qty" inputMode="numeric" value={quantity} onChange={(e) => setQuantity(e.target.value)} />
      </Field>
      <Button type="submit" disabled={!valid || add.isPending}>
        Add size
      </Button>
    </form>
  );
}

export function VariantsPanel({ product }: { product: Product }) {
  const canEdit = useCan("manager");
  const sorted = [...product.variants].sort((a, b) => WEIGHTS.indexOf(a.weight) - WEIGHTS.indexOf(b.weight));
  const missing = WEIGHTS.filter((w) => !product.variants.some((v) => v.weight === w));

  return (
    <div className="space-y-4">
      {sorted.length === 0 && <p className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">No sizes yet. Add 250g, 500g or 1kg below; each has its own price and stock.</p>}
      {sorted.map((v) => (
        <VariantRow key={v.id} variant={v} productId={product.id} canEdit={canEdit} />
      ))}
      {canEdit && missing.length > 0 && <AddVariant key={missing.join()} product={product} missing={missing} />}
    </div>
  );
}
