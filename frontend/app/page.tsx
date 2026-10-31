import { BRAND_DEFAULTS } from "@/lib/config";

export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-3 bg-gradient-to-b from-brand-red to-brand-orange p-8 text-center text-white">
      <h1 className="text-5xl font-bold">{BRAND_DEFAULTS.nameTe}</h1>
      <p className="text-xl">{BRAND_DEFAULTS.name}</p>
      <p className="text-brand-gold">{BRAND_DEFAULTS.tagline}</p>
      <p className="text-sm opacity-80">Setup placeholder (Phase 2). Storefront arrives in Phase 7.</p>
    </main>
  );
}
