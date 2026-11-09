import Link from "next/link";
import { Price } from "@/components/shop/price";
import { ProductImage } from "@/components/shop/product-image";
import { primaryImage } from "@/lib/seo";
import type { ShopProduct } from "@/types/shop";

function cardBadges(p: ShopProduct): string[] {
  const out: string[] = [];
  if (p.is_best_seller) out.push("Best seller");
  if (p.is_new_arrival) out.push("New");
  if (p.is_featured && out.length === 0) out.push("Featured");
  for (const b of p.badges) if (!out.includes(b) && out.length < 3) out.push(b);
  return out.slice(0, 3);
}

export function ProductCard({ product: p, priority = false }: { product: ShopProduct; priority?: boolean }) {
  // Show the cheapest in-stock size when possible, so "From ₹X" is something the customer can actually buy.
  const buyable = p.variants.filter((v) => v.in_stock);
  const cheapest = (buyable.length ? buyable : p.variants)[0];
  const single = p.variants.length === 1;
  const badges = cardBadges(p);

  return (
    <article className="group relative flex flex-col overflow-hidden rounded-2xl border border-brand-brown/10 bg-white shadow-sm transition-shadow focus-within:ring-2 focus-within:ring-brand-orange hover:shadow-lg">
      <div className="relative aspect-square overflow-hidden bg-brand-cream">
        <div className="size-full transition-transform duration-500 group-hover:scale-105">
          <ProductImage
            image={primaryImage(p)}
            alt={p.name}
            priority={priority}
            sizes="(min-width: 1024px) 25vw, (min-width: 640px) 33vw, 50vw"
          />
        </div>
        {badges.length > 0 && (
          <ul className="absolute left-2 top-2 flex flex-col items-start gap-1">
            {badges.map((b) => (
              <li key={b} className="rounded-full bg-brand-gold px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide text-brand-brown">
                {b}
              </li>
            ))}
          </ul>
        )}
        {p.max_discount_percent > 0 && p.in_stock && (
          <span className="absolute right-2 top-2 rounded-full bg-brand-red px-2.5 py-1 text-xs font-bold text-white">
            {p.max_discount_percent}% OFF
          </span>
        )}
        {!p.in_stock && (
          <span className="absolute inset-x-0 bottom-0 bg-brand-brown/85 py-1.5 text-center text-xs font-semibold uppercase tracking-wide text-brand-cream">
            Sold out
          </span>
        )}
      </div>

      <div className="flex flex-1 flex-col gap-1.5 p-3 sm:p-4">
        <h3 className="font-semibold leading-snug">
          {/* the whole card is clickable through this link's ::after */}
          <Link href={`/products/${p.slug}`} className="after:absolute after:inset-0 after:content-[''] focus:outline-none">
            {p.name}
          </Link>
        </h3>
        {p.name_te && <p className="-mt-1 text-sm text-brand-brown/70">{p.name_te}</p>}
        {p.short_description && <p className="line-clamp-2 text-sm text-muted-foreground">{p.short_description}</p>}
        <div className="mt-auto pt-2">
          {cheapest ? (
            <Price price={cheapest.price} compareAt={cheapest.compare_at_price} prefix={single ? `${cheapest.weight}` : "From"} />
          ) : (
            <p className="text-sm text-muted-foreground">Price coming soon</p>
          )}
          <span className="mt-2 inline-flex h-9 w-full items-center justify-center rounded-lg bg-brand-red text-sm font-semibold text-brand-cream transition-colors group-hover:bg-brand-orange">
            View details
          </span>
        </div>
      </div>
    </article>
  );
}

export function ProductGrid({ products, priorityCount = 0 }: { products: ShopProduct[]; priorityCount?: number }) {
  return (
    <ul className="grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-4">
      {products.map((p, i) => (
        <li key={p.id}>
          <ProductCard product={p} priority={i < priorityCount} />
        </li>
      ))}
    </ul>
  );
}
