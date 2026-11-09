import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { ProductListing, parseListingParams } from "@/components/shop/product-listing";
import { ListingSkeleton } from "@/components/shop/skeletons";
import { metaDescription } from "@/lib/seo";
import { getCategories } from "@/lib/shop-api";

export async function generateStaticParams() {
  return (await getCategories()).map((c) => ({ slug: c.slug }));
}

export async function generateMetadata({ params, searchParams }: PageProps<"/category/[slug]">): Promise<Metadata> {
  const { slug } = await params;
  const category = (await getCategories()).find((c) => c.slug === slug);
  if (!category) return { title: "Category not found", robots: { index: false } };
  const p = parseListingParams(await searchParams);
  return {
    title: category.name,
    description: metaDescription(category.description, `Shop ${category.name} – traditional Andhra homemade pickles.`),
    alternates: { canonical: `/category/${slug}` },
    robots: p.q || p.page || p.sort ? { index: false, follow: true } : undefined,
  };
}

async function CategoryContent({ params, searchParams }: Pick<PageProps<"/category/[slug]">, "params" | "searchParams">) {
  const { slug } = await params;
  const category = (await getCategories()).find((c) => c.slug === slug);
  if (!category) notFound();
  return (
    <>
      <h1 className="font-display text-4xl font-semibold uppercase tracking-wide text-brand-red">{category.name}</h1>
      {category.name_te && <p className="text-brand-brown/70">{category.name_te}</p>}
      {category.description && <p className="mt-2 max-w-3xl text-muted-foreground">{category.description}</p>}
      <div className="mt-6">
        <ProductListing categorySlug={slug} params={parseListingParams(await searchParams)} />
      </div>
    </>
  );
}

export default function CategoryPage(props: PageProps<"/category/[slug]">) {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      <Suspense fallback={<ListingSkeleton />}>
        <CategoryContent params={props.params} searchParams={props.searchParams} />
      </Suspense>
    </div>
  );
}
