import Link from "next/link";
import type { ShopCategory } from "@/types/shop";

const TONES = [
  "bg-brand-red text-brand-cream",
  "bg-[#C8431B] text-white", // brand orange, deepened so white text passes WCAG AA
  "bg-brand-gold text-brand-brown",
  "bg-brand-brown text-brand-cream",
];

export function CategoryTiles({ categories }: { categories: ShopCategory[] }) {
  return (
    <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 lg:grid-cols-5">
      {categories.map((c, i) => (
        <li key={c.slug}>
          <Link
            href={`/category/${c.slug}`}
            className={`flex min-h-28 flex-col items-start justify-end gap-0.5 rounded-2xl p-4 shadow-sm transition-transform hover:-translate-y-1 hover:shadow-lg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-orange ${TONES[i % TONES.length]}`}
          >
            <span className="font-display text-xl font-semibold uppercase leading-tight tracking-wide">{c.name}</span>
            {c.name_te && <span className="text-sm">{c.name_te}</span>}
          </Link>
        </li>
      ))}
    </ul>
  );
}
