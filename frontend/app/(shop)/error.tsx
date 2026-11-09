"use client";

import { Button } from "@/components/ui/button";

export default function ShopError({ reset }: { error: Error; reset: () => void }) {
  return (
    <div className="mx-auto max-w-xl px-4 py-20 text-center" role="alert">
      <h1 className="font-display text-3xl font-semibold uppercase text-brand-red">Something went wrong</h1>
      <p className="mt-3 text-muted-foreground">We could not load this page right now. Please try again in a moment.</p>
      <Button onClick={reset} className="mt-6 h-11 bg-brand-red px-6 text-brand-cream hover:bg-brand-orange">
        Try again
      </Button>
    </div>
  );
}
