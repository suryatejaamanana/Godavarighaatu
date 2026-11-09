"use client";

import { useState } from "react";
import { Price } from "@/components/shop/price";
import { cn } from "@/lib/utils";
import type { ShopVariant } from "@/types/shop";

const LOW_STOCK_AT = 5;

/** Choose a size; price, discount and availability follow the selection. */
export function VariantPicker({ variants }: { variants: ShopVariant[] }) {
  const firstBuyable = variants.find((v) => v.in_stock) ?? variants[0];
  const [selectedId, setSelectedId] = useState(firstBuyable?.id);
  const selected = variants.find((v) => v.id === selectedId) ?? firstBuyable;

  if (!selected) return <p className="text-muted-foreground">Prices coming soon.</p>;

  return (
    <div>
      <div aria-live="polite" className="mb-4">
        <Price price={selected.price} compareAt={selected.compare_at_price} className="[&_span]:!text-3xl" />
        <p className="mt-1 flex items-center gap-2 text-sm">
          {selected.discount_percent > 0 && (
            <span className="rounded-full bg-brand-red px-2.5 py-0.5 text-xs font-bold text-white">{selected.discount_percent}% OFF</span>
          )}
          {!selected.in_stock ? (
            <span className="font-semibold text-destructive">Out of stock</span>
          ) : selected.available_quantity <= LOW_STOCK_AT ? (
            <span className="font-semibold text-brand-orange">Only {selected.available_quantity} left</span>
          ) : (
            <span className="font-semibold text-green-700">In stock</span>
          )}
        </p>
      </div>

      <fieldset>
        <legend className="mb-2 text-sm font-semibold">Choose size</legend>
        <div className="flex flex-wrap gap-2" role="radiogroup">
          {variants.map((v) => {
            const active = v.id === selected.id;
            return (
              <label
                key={v.id}
                className={cn(
                  "relative flex min-h-14 min-w-24 cursor-pointer flex-col items-center justify-center rounded-xl border-2 px-4 py-2 text-center transition-colors focus-within:ring-2 focus-within:ring-brand-orange",
                  active ? "border-brand-red bg-brand-red/5" : "border-brand-brown/20 bg-white hover:border-brand-orange",
                  !v.in_stock && "opacity-60",
                )}
              >
                <input
                  type="radio"
                  name="size"
                  value={v.id}
                  checked={active}
                  onChange={() => setSelectedId(v.id)}
                  className="sr-only"
                />
                <span className="font-display text-lg font-semibold">{v.weight}</span>
                <span className="text-xs text-muted-foreground">{v.in_stock ? "" : "Sold out"}</span>
              </label>
            );
          })}
        </div>
      </fieldset>
    </div>
  );
}
