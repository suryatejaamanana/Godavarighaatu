import Link from "next/link";
import { cn } from "@/lib/utils";

function pageHref(base: string, params: Record<string, string>, page: number) {
  const sp = new URLSearchParams(params);
  if (page > 1) sp.set("page", String(page));
  const s = sp.toString();
  return s ? `${base}?${s}` : base;
}

export function Pagination({
  base,
  params,
  page,
  totalPages,
}: {
  base: string;
  params: Record<string, string>;
  page: number;
  totalPages: number;
}) {
  if (totalPages <= 1) return null;
  const pages = Array.from({ length: totalPages }, (_, i) => i + 1).filter(
    (n) => n === 1 || n === totalPages || Math.abs(n - page) <= 1,
  );
  const item = "inline-flex h-11 min-w-11 items-center justify-center rounded-lg border border-brand-brown/20 bg-white px-3 text-sm font-semibold hover:bg-brand-gold/30";
  return (
    <nav aria-label="Pagination" className="mt-10 flex flex-wrap items-center justify-center gap-2">
      {page > 1 && (
        <Link href={pageHref(base, params, page - 1)} rel="prev" className={item}>
          ← Previous
        </Link>
      )}
      {pages.map((n, i) => (
        <span key={n} className="flex items-center gap-2">
          {i > 0 && n - pages[i - 1] > 1 && <span aria-hidden="true">…</span>}
          <Link
            href={pageHref(base, params, n)}
            aria-current={n === page ? "page" : undefined}
            aria-label={`Page ${n}`}
            className={cn(item, n === page && "border-brand-red bg-brand-red text-brand-cream hover:bg-brand-red")}
          >
            {n}
          </Link>
        </span>
      ))}
      {page < totalPages && (
        <Link href={pageHref(base, params, page + 1)} rel="next" className={item}>
          Next →
        </Link>
      )}
    </nav>
  );
}
