import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { Price } from "@/components/shop/price";
import { ProductImage } from "@/components/shop/product-image";
import { primaryImage } from "@/lib/seo";
import type { SiteSettings } from "@/lib/site";
import type { ShopProduct } from "@/types/shop";

export function Hero({ settings, spotlight }: { settings: SiteSettings; spotlight: ShopProduct | null }) {
  const cheapest = spotlight?.variants.find((v) => v.in_stock) ?? spotlight?.variants[0];
  return (
    <section
      aria-labelledby="hero-title"
      className="relative overflow-hidden bg-gradient-to-b from-brand-red via-[#c2391b] to-brand-orange text-white"
    >
      <div className="pointer-events-none absolute -right-24 -top-24 size-96 rounded-full bg-brand-gold/20 blur-3xl" aria-hidden="true" />
      <div className="mx-auto grid max-w-7xl items-center gap-8 px-4 py-10 sm:px-6 sm:py-14 lg:grid-cols-[1.1fr_0.9fr] lg:py-20">
        <div className="text-center lg:text-left">
          <p
            className="mx-auto mb-5 w-fit bg-[#7d1712] px-8 py-1.5 font-display text-sm font-semibold uppercase tracking-[0.2em] shadow-md lg:mx-0"
            style={{ clipPath: "polygon(0 0,100% 0,96% 50%,100% 100%,0 100%,4% 50%)" }}
          >
            {settings.label}
          </p>
          <h1 id="hero-title" className="text-4xl font-extrabold leading-tight sm:text-5xl lg:text-6xl">
            {settings.heroHeadlineTe}
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-base text-white/90 sm:text-lg lg:mx-0">{settings.heroHeadline}</p>
          <p className="mt-2 font-display text-lg font-medium uppercase tracking-widest text-brand-gold">{settings.tagline}</p>
          <div className="mt-7 flex flex-wrap justify-center gap-3 lg:justify-start">
            <Link
              href="/products"
              className="inline-flex h-12 items-center gap-2 rounded-full bg-brand-gold px-7 text-base font-bold text-brand-brown shadow-lg transition-transform hover:scale-105"
            >
              Shop pickles <ArrowRight className="size-5" aria-hidden="true" />
            </Link>
            <Link
              href="#categories"
              className="inline-flex h-12 items-center rounded-full border-2 border-white/70 px-7 text-base font-semibold hover:bg-white/10"
            >
              Browse categories
            </Link>
          </div>
        </div>

        {spotlight && (
          <Link
            href={`/products/${spotlight.slug}`}
            className="group mx-auto block w-full max-w-md rounded-3xl bg-white/10 p-3 ring-1 ring-white/25 backdrop-blur-sm transition-transform hover:-translate-y-1"
          >
            <div className="aspect-[4/3] overflow-hidden rounded-2xl bg-brand-cream">
              <ProductImage image={primaryImage(spotlight)} alt={spotlight.name} priority sizes="(min-width: 1024px) 28rem, 90vw" />
            </div>
            <div className="p-3">
              <p className="font-display text-sm font-medium uppercase tracking-widest text-brand-gold">Our special</p>
              <h2 className="text-xl font-bold leading-snug">{spotlight.name}</h2>
              {spotlight.name_te && <p className="text-sm text-white/80">{spotlight.name_te}</p>}
              {cheapest && (
                <div className="mt-2 flex items-center justify-between">
                  <Price price={cheapest.price} compareAt={cheapest.compare_at_price} prefix="From" className="[&_span]:!text-brand-gold [&_span.text-xs]:!text-white/70 [&_s]:!text-white/60" />
                  <span className="text-sm font-semibold underline-offset-4 group-hover:underline">View details →</span>
                </div>
              )}
            </div>
          </Link>
        )}
      </div>
    </section>
  );
}
