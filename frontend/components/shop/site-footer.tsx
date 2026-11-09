import Link from "next/link";
import { BrandMark } from "@/components/shop/brand-mark";
import { getCategories } from "@/lib/shop-api";
import { getSiteSettings } from "@/lib/site";

export async function SiteFooter() {
  const [settings, categories] = await Promise.all([getSiteSettings(), getCategories()]);
  const link = "text-sm text-brand-cream/80 hover:text-brand-gold hover:underline";
  return (
    <footer className="mt-16 bg-brand-brown text-brand-cream">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-10 sm:px-6 md:grid-cols-[1.5fr_1fr]">
        <div>
          <BrandMark name={settings.name} nameTe={settings.nameTe} light />
          <p className="mt-3 max-w-xs text-sm text-brand-cream/80">{settings.tagline}</p>
          <p className="mt-1 text-sm font-semibold text-brand-gold">{settings.label}</p>
        </div>
        <nav aria-label="Shop">
          <h2 className="mb-3 font-display text-sm font-semibold uppercase tracking-widest text-brand-gold">Shop</h2>
          <ul className="space-y-2">
            <li>
              <Link href="/products" className={link}>
                All pickles
              </Link>
            </li>
            {categories.map((c) => (
              <li key={c.slug}>
                <Link href={`/category/${c.slug}`} className={link}>
                  {c.name}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </div>
      <div className="border-t border-white/10 py-4 text-center text-xs text-brand-cream/60">© {settings.name}. All rights reserved.</div>
    </footer>
  );
}
