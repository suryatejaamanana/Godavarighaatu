"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Minus, Plus } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { adjustInventory, setInventory } from "@/services/admin";
import type { Variant } from "@/types/api";

export function StockEditor({ variant, label }: { variant: Variant; label?: string }) {
  const queryClient = useQueryClient();
  const inv = variant.inventory;
  const [value, setValue] = useState(String(inv?.quantity ?? 0));
  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["products"] });
    queryClient.invalidateQueries({ queryKey: ["product"] });
    queryClient.invalidateQueries({ queryKey: ["low-stock"] });
    queryClient.invalidateQueries({ queryKey: ["summary"] });
  };
  const onError = (e: Error) => {
    toast.error(e.message);
    setValue(String(inv?.quantity ?? 0));
  };
  const set = useMutation({
    mutationFn: (q: number) => setInventory(variant.id, q),
    onSuccess: (v) => {
      toast.success("Stock updated");
      setValue(String(v.inventory?.quantity ?? 0));
      refresh();
    },
    onError,
  });
  const adjust = useMutation({
    mutationFn: (d: number) => adjustInventory(variant.id, d),
    onSuccess: (v) => {
      setValue(String(v.inventory?.quantity ?? 0));
      refresh();
    },
    onError,
  });
  const busy = set.isPending || adjust.isPending;
  const name = label ?? variant.weight;
  const parsed = Number(value);
  const valid = value.trim() !== "" && Number.isInteger(parsed) && parsed >= 0;

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button variant="outline" size="icon" disabled={busy || (inv?.quantity ?? 0) <= 0} aria-label={`Decrease stock of ${name}`} onClick={() => adjust.mutate(-1)}>
        <Minus />
      </Button>
      <Input
        type="number"
        min={0}
        inputMode="numeric"
        aria-label={`Stock quantity of ${name}`}
        className="h-8 w-20 text-center"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && valid && set.mutate(parsed)}
      />
      <Button variant="outline" size="icon" disabled={busy} aria-label={`Increase stock of ${name}`} onClick={() => adjust.mutate(1)}>
        <Plus />
      </Button>
      <Button size="sm" disabled={busy || !valid || parsed === inv?.quantity} onClick={() => set.mutate(parsed)}>
        Save
      </Button>
      {inv && inv.reserved > 0 && <span className="text-xs text-muted-foreground">{inv.reserved} reserved</span>}
    </div>
  );
}
