import type { Metadata } from "next";
import Link from "next/link";
import { CategoryTiles } from "@/components/shop/category-tiles";
import { Hero } from "@/components/shop/hero";
import { JsonLd } from "@/components/shop/json-ld";
import { ProductGrid } from "@/components/shop/product-card";
import { SectionHeading } from "@/components/shop/section-heading";
import { ValueProps } from "@/components/shop/value-props";
import { absoluteUrl, metaDescription } from "@/lib/seo";
import { getCategories, getProducts } from "@/lib/shop-api";
import { getSiteSettings } from "@/lib/site";

export async function generateMetadata(): Promise<Metadata> {
  const s = await getSiteSettings();
  const title = `${s.name} | ${s.nameTe} – ${s.label}`;
  const description = metaDescription(`${s.tagline}. ${s.about}`, s.tagline);
  return {
    title: { absolute: title },
    description,
    alternates: { canonical: "/" },
    openGraph: { title, description, url: "/", type: "website" },
  };
}

export default async function HomePage() {
  const [settings, categories, featured, bestSellers, newArrivals, latest] = await Promise.all([
    getSiteSettings(),
    getCategories(),
    getProducts({ featured: true, page_size: 4 }),
    getProducts({ best_seller: true, page_size: 8 }),
    getProducts({ new_arrival: true, page_size: 8 }),
    getProducts({ sort: "newest", page_size: 8 }),
  ]);
  // Prefer a product that has a photo; fall back to any featured / best-selling / latest product.
  const candidates = [...featured.items, ...bestSellers.items, ...latest.items];
  const spotlight = candidates.find((p) => p.images.length > 0) ?? candidates[0] ?? null;
  const noProducts = latest.total === 0;

  return (
    <>
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "Organization",
          name: settings.name,
          alternateName: settings.nameTe,
          url: absoluteUrl("/"),
          slogan: settings.tagline,
        }}
      />
      <Hero settings={settings} spotlight={spotlight} />

      <div className="mx-auto max-w-7xl space-y-14 px-4 py-10 sm:space-y-16 sm:px-6 sm:py-14">
        {categories.length > 0 && (
          <section id="categories" aria-labelledby="cat-h" className="scroll-mt-32">
            <SectionHeading title="Shop by category" titleTe="వర్గాల వారీగా" href="/products" linkLabel="All pickles" />
            <h2 id="cat-h" className="sr-only">
              Categories
            </h2>
            <CategoryTiles categories={categories} />
          </section>
        )}

        {bestSellers.items.length > 0 && (
          <section aria-label="Best sellers">
            <SectionHeading title="Best sellers" titleTe="ఎక్కువగా అమ్ముడయ్యేవి" href="/products?best_seller=true" />
            <ProductGrid products={bestSellers.items} />
          </section>
        )}

        {newArrivals.items.length > 0 && (
          <section aria-label="New arrivals">
            <SectionHeading title="New arrivals" titleTe="కొత్తగా వచ్చినవి" href="/products?new_arrival=true" />
            <ProductGrid products={newArrivals.items} />
          </section>
        )}

        {bestSellers.items.length === 0 && newArrivals.items.length === 0 && latest.items.length > 0 && (
          <section aria-label="Our pickles">
            <SectionHeading title="Our pickles" href="/products" />
            <ProductGrid products={latest.items} />
          </section>
        )}

        {noProducts && (
          <section className="rounded-2xl border-2 border-dashed border-brand-brown/20 p-10 text-center">
            <h2 className="font-display text-2xl font-semibold uppercase text-brand-red">Our pickles are on their way</h2>
            <p className="mt-2 text-muted-foreground">We are stocking the shelves. Please check back soon.</p>
          </section>
        )}

        <section aria-labelledby="why-h">
          <SectionHeading title="Why Godavari Ghaatu" titleTe="ఎందుకు గోదావరి ఘాటు" />
          <h2 id="why-h" className="sr-only">
            Why choose us
          </h2>
          <ValueProps />
        </section>

        <section aria-labelledby="about-h" className="rounded-3xl bg-brand-red p-6 text-brand-cream sm:p-10">
          <h2 id="about-h" className="font-display text-3xl font-semibold uppercase tracking-wide text-brand-gold">
            About us
          </h2>
          <p className="mt-3 max-w-3xl text-base leading-relaxed sm:text-lg">{settings.about}</p>
          {settings.aboutTe && <p className="mt-2 max-w-3xl text-base leading-relaxed text-brand-cream/90">{settings.aboutTe}</p>}
          <Link href="/products" className="mt-6 inline-flex h-11 items-center rounded-full bg-brand-gold px-6 font-bold text-brand-brown hover:bg-white">
            Explore our pickles
          </Link>
        </section>
      </div>
    </>
  );
}
