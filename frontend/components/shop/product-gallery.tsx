"use client";

import { useState } from "react";
import { ProductImage } from "@/components/shop/product-image";
import { cn } from "@/lib/utils";
import type { ShopImage } from "@/types/shop";

export function ProductGallery({ images, name }: { images: ShopImage[]; name: string }) {
  const [index, setIndex] = useState(0);
  const current = images[index] ?? null;
  return (
    <div>
      <div className="aspect-square overflow-hidden rounded-2xl bg-brand-cream ring-1 ring-brand-brown/10">
        <ProductImage image={current} alt={name} priority sizes="(min-width: 768px) 50vw, 100vw" />
      </div>
      {images.length > 1 && (
        <ul className="mt-3 flex gap-2 overflow-x-auto pb-1" aria-label="Product photos">
          {images.map((img, i) => (
            <li key={img.id} className="shrink-0">
              <button
                type="button"
                onClick={() => setIndex(i)}
                aria-label={`Show photo ${i + 1} of ${images.length}`}
                aria-current={i === index}
                className={cn("size-16 overflow-hidden rounded-lg ring-2 ring-transparent sm:size-20", i === index && "ring-brand-red")}
              >
                {/* eslint-disable-next-line @next/next/no-img-element -- tiny pre-sized WebP thumbnail */}
                <img src={img.thumb_url} alt="" width={200} height={200} loading="lazy" decoding="async" className="size-full object-cover" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
