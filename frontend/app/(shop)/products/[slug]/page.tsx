import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { JsonLd } from "@/components/shop/json-ld";
import { ProductGrid } from "@/components/shop/product-card";
import { ProductGallery } from "@/components/shop/product-gallery";
import { SectionHeading } from "@/components/shop/section-heading";
import { ProductSkeleton } from "@/components/shop/skeletons";
import { VariantPicker } from "@/components/shop/variant-picker";
import { absoluteUrl, metaDescription, primaryImage, productJsonLd } from "@/lib/seo";
import { getAllProductSlugs, getProduct, getRelatedProducts } from "@/lib/shop-api";
import { getSiteSettings } from "@/lib/site";
import type { ShopProduct } from "@/types/shop";

export async function generateStaticParams() {
  const slugs = await getAllProductSlugs();
  // an empty list would make Next treat the route as having no static params; keep at least one entry
  return (slugs.length ? slugs : ["_"]).slice(0, 100).map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: PageProps<"/products/[slug]">): Promise<Metadata> {
  const { slug } = await params;
  const p = await getProduct(slug);
  if (!p) return { title: "Product not found", robots: { index: false } };
  const description = metaDescription(p.seo_description ?? p.short_description ?? p.description, `${p.name} – ${p.category.name}`);
  const title = p.seo_title || p.name;
  const image = primaryImage(p);
  return {
    title,
    description,
    alternates: { canonical: `/products/${p.slug}` },
    openGraph: {
      title,
      description,
      url: `/products/${p.slug}`,
      type: "website",
      ...(image && { images: [{ url: image.url, alt: image.alt_text || p.name }] }),
    },
    twitter: { card: image ? "summary_large_image" : "summary", title, description },
  };
}

const DETAIL_SECTIONS: { key: keyof ShopProduct; keyTe: keyof ShopProduct; title: string }[] = [
  { key: "description", keyTe: "description_te", title: "About this pickle" },
  { key: "ingredients", keyTe: "ingredients_te", title: "Ingredients" },
  { key: "preparation", keyTe: "preparation_te", title: "How it is made" },
  { key: "storage_instructions", keyTe: "storage_instructions_te", title: "Storage" },
];

function Details({ p }: { p: ShopProduct }) {
  const sections = DETAIL_SECTIONS.filter((s) => p[s.key] || p[s.keyTe]);
  return (
    <div className="mt-8 divide-y rounded-2xl border border-brand-brown/10 bg-white">
      {sections.map((s, i) => (
        <details key={s.title} open={i === 0} className="group p-4 sm:p-5">
          <summary className="flex min-h-11 cursor-pointer list-none items-center justify-between font-display text-lg font-semibold uppercase tracking-wide text-brand-red">
            {s.title}
            <span className="text-2xl transition-transform group-open:rotate-45" aria-hidden="true">
              +
            </span>
          </summary>
          <div className="mt-2 space-y-2 whitespace-pre-line text-brand-brown/90">
            {p[s.key] ? <p>{String(p[s.key])}</p> : null}
            {p[s.keyTe] ? <p lang="te">{String(p[s.keyTe])}</p> : null}
          </div>
        </details>
      ))}
      {p.shelf_life && (
        <div className="p-4 sm:p-5">
          <span className="font-display text-lg font-semibold uppercase tracking-wide text-brand-red">Shelf life: </span>
          {p.shelf_life}
        </div>
      )}
    </div>
  );
}

async function ProductContent({ params }: Pick<PageProps<"/products/[slug]">, "params">) {
  const { slug } = await params;
  const [product, settings] = await Promise.all([getProduct(slug), getSiteSettings()]);
  if (!product) notFound();
  const related = await getRelatedProducts(slug);
  const badges = [product.is_best_seller && "Best seller", product.is_new_arrival && "New", ...product.badges].filter(Boolean) as string[];

  return (
    <>
      <JsonLd data={productJsonLd(product, settings.name)} />
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "BreadcrumbList",
          itemListElement: [
            { "@type": "ListItem", position: 1, name: "Home", item: absoluteUrl("/") },
            { "@type": "ListItem", position: 2, name: product.category.name, item: absoluteUrl(`/category/${product.category.slug}`) },
            { "@type": "ListItem", position: 3, name: product.name, item: absoluteUrl(`/products/${product.slug}`) },
          ],
        }}
      />
      <nav aria-label="Breadcrumb" className="mb-4 text-sm text-brand-brown/70">
        <ol className="flex flex-wrap items-center gap-1.5">
          <li>
            <Link href="/" className="hover:underline">
              Home
            </Link>
          </li>
          <li aria-hidden="true">/</li>
          <li>
            <Link href={`/category/${product.category.slug}`} className="hover:underline">
              {product.category.name}
            </Link>
          </li>
          <li aria-hidden="true">/</li>
          <li aria-current="page" className="font-medium text-brand-brown">
            {product.name}
          </li>
        </ol>
      </nav>

      <div className="grid gap-8 md:grid-cols-2 lg:gap-12">
        <ProductGallery images={product.images} name={product.name} />
        <div>
          {badges.length > 0 && (
            <ul className="mb-2 flex flex-wrap gap-1.5">
              {badges.map((b) => (
                <li key={b} className="rounded-full bg-brand-gold px-3 py-0.5 text-xs font-bold uppercase tracking-wide text-brand-brown">
                  {b}
                </li>
              ))}
            </ul>
          )}
          <h1 className="text-3xl font-bold leading-tight sm:text-4xl">{product.name}</h1>
          {product.name_te && <p className="mt-1 text-xl text-brand-brown/70">{product.name_te}</p>}
          {(product.short_description || product.short_description_te) && (
            <div className="mt-3 space-y-1 text-brand-brown/80">
              {product.short_description && <p>{product.short_description}</p>}
              {product.short_description_te && <p lang="te">{product.short_description_te}</p>}
            </div>
          )}
          <div className="mt-6 rounded-2xl bg-white p-4 ring-1 ring-brand-brown/10 sm:p-5">
            <VariantPicker variants={product.variants} />
          </div>
          <Details p={product} />
        </div>
      </div>

      {related.length > 0 && (
        <section className="mt-14" aria-label="Related pickles">
          <SectionHeading title="You may also like" titleTe="మీకు నచ్చవచ్చు" href={`/category/${product.category.slug}`} linkLabel={`More ${product.category.name}`} />
          <ProductGrid products={related} />
        </section>
      )}
    </>
  );
}

export default function ProductPage(props: PageProps<"/products/[slug]">) {
  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-8">
      <Suspense fallback={<ProductSkeleton />}>
        <ProductContent params={props.params} />
      </Suspense>
    </div>
  );
}
