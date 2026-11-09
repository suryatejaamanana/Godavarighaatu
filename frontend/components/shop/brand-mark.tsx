import Link from "next/link";
import { cn } from "@/lib/utils";

// Text wordmark until the real SVG logo is supplied (drop it in public/brand/ and swap here).
export function BrandMark({ name, nameTe, className, light }: { name: string; nameTe: string; className?: string; light?: boolean }) {
  return (
    <Link href="/" className={cn("shrink-0 whitespace-nowrap leading-none", className)}>
      <span className={cn("block text-2xl font-bold tracking-tight sm:text-3xl", light ? "text-white" : "text-brand-red")}>{nameTe}</span>
      <span className={cn("mt-0.5 block font-display text-[11px] font-medium uppercase tracking-[0.2em]", light ? "text-brand-gold" : "text-brand-brown/70")}>
        {name}
      </span>
    </Link>
  );
}
