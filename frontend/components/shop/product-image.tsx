import { PlaceholderArt } from "@/components/shop/placeholder-art";
import type { ShopImage } from "@/types/shop";

/**
 * The API already stores each photo as WebP at 200/600/1920px, so we offer them as a srcset
 * and let the browser choose; no extra image server is needed. Below-the-fold images are lazy.
 */
export function ProductImage({
  image,
  alt,
  sizes,
  priority = false,
  className = "size-full object-cover",
}: {
  image: ShopImage | null | undefined;
  alt: string;
  sizes: string;
  priority?: boolean;
  className?: string;
}) {
  if (!image) return <PlaceholderArt label={`${alt} (photo coming soon)`} />;
  return (
    // eslint-disable-next-line @next/next/no-img-element -- pre-sized WebP variants from our own API
    <img
      src={image.card_url}
      srcSet={`${image.thumb_url} 200w, ${image.card_url} 600w, ${image.url} 1920w`}
      sizes={sizes}
      alt={image.alt_text || alt}
      width={600}
      height={600}
      loading={priority ? "eager" : "lazy"}
      fetchPriority={priority ? "high" : "auto"}
      decoding="async"
      className={className}
    />
  );
}
