import { Search } from "lucide-react";
import Link from "next/link";
import { BrandMark } from "@/components/shop/brand-mark";
import { MobileMenu } from "@/components/shop/mobile-menu";
import { getSiteSettings } from "@/lib/site";
import { getCategories } from "@/lib/shop-api";

function SearchForm({ className }: { className?: string }) {
  return (
    <form role="search" action="/products" method="get" className={className}>
      <label htmlFor="site-search" className="sr-only">
        Search pickles
      </label>
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-brand-brown/50" aria-hidden="true" />
        <input
          id="site-search"
          name="q"
          type="search"
          maxLength={100}
          placeholder="Search pickles…"
          className="h-11 w-full rounded-full border border-brand-brown/15 bg-white pl-9 pr-4 text-base outline-none placeholder:text-brand-brown/50 focus:border-brand-orange focus:ring-2 focus:ring-brand-orange/30 sm:h-10 sm:text-sm"
        />
      </div>
    </form>
  );
}

export async function SiteHeader() {
  const [settings, categories] = await Promise.all([getSiteSettings(), getCategories()]);
  const nav = "whitespace-nowrap rounded-full px-3 py-2 text-sm font-semibold text-brand-brown hover:bg-brand-gold/40";
  return (
    <header className="sticky top-0 z-30 border-b border-brand-brown/10 bg-brand-cream/95 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center gap-2 px-3 py-2 sm:px-6 lg:gap-6">
        <MobileMenu categories={categories} brand={settings.name} />
        <BrandMark name={settings.name} nameTe={settings.nameTe} />
        <nav aria-label="Main" className="ml-2 hidden items-center gap-0.5 xl:ml-4 lg:flex">
          <Link href="/products" className={nav}>
            All pickles
          </Link>
          {categories.slice(0, 4).map((c) => (
            <Link key={c.slug} href={`/category/${c.slug}`} className={nav}>
              {c.name}
            </Link>
          ))}
        </nav>
        <SearchForm className="ml-auto hidden w-64 sm:block lg:w-72" />
      </div>
      <SearchForm className="px-3 pb-2 sm:hidden" />
    </header>
  );
}
