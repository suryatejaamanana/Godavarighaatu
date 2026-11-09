// Shapes returned by the public storefront API (GET /products, /categories, /site-settings).
export interface ShopCategory {
  id: string;
  slug: string;
  name: string;
  name_te: string | null;
  description: string | null;
  image_url: string | null;
}

export interface ShopImage {
  id: string;
  url: string; // 1920px
  card_url: string; // 600px
  thumb_url: string; // 200px
  alt_text: string | null;
  is_primary: boolean;
}

export interface ShopVariant {
  id: string;
  weight: "250g" | "500g" | "1kg";
  price: string;
  compare_at_price: string | null;
  discount_percent: number;
  in_stock: boolean;
  available_quantity: number;
}

export interface ShopProduct {
  id: string;
  slug: string;
  name: string;
  name_te: string | null;
  short_description: string | null;
  short_description_te: string | null;
  description: string | null;
  description_te: string | null;
  ingredients: string | null;
  ingredients_te: string | null;
  preparation: string | null;
  preparation_te: string | null;
  storage_instructions: string | null;
  storage_instructions_te: string | null;
  shelf_life: string | null;
  badges: string[];
  is_featured: boolean;
  is_best_seller: boolean;
  is_new_arrival: boolean;
  seo_title: string | null;
  seo_description: string | null;
  category: ShopCategory;
  images: ShopImage[];
  variants: ShopVariant[];
  in_stock: boolean;
  min_price: string | null;
  max_discount_percent: number;
}

export interface ShopPage<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export type ProductSort = "newest" | "popular" | "price_asc" | "price_desc";
export interface ProductQuery {
  q?: string;
  category?: string;
  featured?: boolean;
  best_seller?: boolean;
  new_arrival?: boolean;
  sort?: ProductSort;
  page?: number;
  page_size?: number;
}
