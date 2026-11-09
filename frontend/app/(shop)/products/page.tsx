import type { Metadata } from "next";
import { Suspense } from "react";
import { ProductListing, parseListingParams } from "@/components/shop/product-listing";
import { ListingSkeleton } from "@/components/shop/skeletons";

export async function generateMetadata({ searchParams }: PageProps<"/products">): Promise<Metadata> {
  const p = parseListingParams(await searchParams);
  const searching = !!p.q;
  return {
    title: searching ? `Search: ${p.q}` : "All pickles",
    description: "Browse all our traditional Andhra homemade pickles.",
    alternates: { canonical: "/products" },
    // Search results and filtered/paged variants shouldn't compete with the main listing in search engines.
    robots: searching || p.page || p.sort || p.best_seller || p.new_arrival || p.featured ? { index: false, follow: true } : undefined,
  };
}

async function Listing({ searchParams }: Pick<PageProps<"/products">, "searchParams">) {
  return <ProductListing params={parseListingParams(await searchParams)} />;
}

export default function ProductsPage(props: PageProps<"/products">) {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      <h1 className="mb-1 font-display text-4xl font-semibold uppercase tracking-wide text-brand-red">All pickles</h1>
      <p className="mb-6 text-brand-brown/70">అన్ని పచ్చళ్ళు · Traditional Andhra homemade pickles</p>
      <Suspense fallback={<ListingSkeleton />}>
        <Listing searchParams={props.searchParams} />
      </Suspense>
    </div>
  );
}
