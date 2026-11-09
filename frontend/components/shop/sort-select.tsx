"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";

const OPTIONS = [
  { value: "newest", label: "Newest" },
  { value: "popular", label: "Most popular" },
  { value: "price_asc", label: "Price: low to high" },
  { value: "price_desc", label: "Price: high to low" },
];

export function SortSelect({ value }: { value: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  return (
    <label className="flex items-center gap-2 text-sm font-medium">
      <span className="whitespace-nowrap">Sort by</span>
      <select
        value={value}
        onChange={(e) => {
          const sp = new URLSearchParams(params.toString());
          sp.set("sort", e.target.value);
          sp.delete("page"); // a new ordering starts from page 1
          router.push(`${pathname}?${sp.toString()}`);
        }}
        className="h-11 rounded-lg border border-brand-brown/20 bg-white px-3 text-sm sm:h-10"
      >
        {OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}
