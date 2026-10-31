import { BRAND_DEFAULTS } from "@/lib/config";

// Placeholder wordmark until the real SVG logo is supplied (public/brand/).
export function Brand({ light = true }: { light?: boolean }) {
  return (
    <div className={light ? "text-brand-cream" : "text-brand-red"}>
      <div className="text-xl font-bold leading-tight">{BRAND_DEFAULTS.nameTe}</div>
      <div className="text-xs tracking-wide text-brand-gold">{BRAND_DEFAULTS.name} · Admin</div>
    </div>
  );
}
