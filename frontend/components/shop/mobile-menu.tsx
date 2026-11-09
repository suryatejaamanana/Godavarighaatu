"use client";

import { Menu } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";

export function MobileMenu({ categories, brand }: { categories: { slug: string; name: string; name_te: string | null }[]; brand: string }) {
  const [open, setOpen] = useState(false);
  const close = () => setOpen(false);
  const link = "block rounded-lg px-3 py-3 text-base font-medium hover:bg-brand-gold/30";
  return (
    <>
      <Button variant="ghost" size="icon" className="size-11 lg:hidden" aria-label="Open menu" onClick={() => setOpen(true)}>
        <Menu className="size-6" />
      </Button>
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent side="left" className="w-[85%] max-w-xs overflow-y-auto bg-brand-cream p-0">
          <SheetTitle className="border-b bg-brand-red p-4 font-display text-xl uppercase tracking-wide text-brand-cream">{brand}</SheetTitle>
          <nav aria-label="Mobile" className="p-3">
            <Link href="/" onClick={close} className={link}>
              Home
            </Link>
            <Link href="/products" onClick={close} className={link}>
              All pickles
            </Link>
            <p className="px-3 pb-1 pt-4 text-xs font-bold uppercase tracking-widest text-brand-brown/60">Shop by category</p>
            {categories.map((c) => (
              <Link key={c.slug} href={`/category/${c.slug}`} onClick={close} className={link}>
                {c.name}
                {c.name_te && <span className="ml-2 text-sm text-brand-brown/60">{c.name_te}</span>}
              </Link>
            ))}
          </nav>
        </SheetContent>
      </Sheet>
    </>
  );
}
