export type Role = "staff" | "manager" | "super_admin";
export type ProductStatus = "active" | "inactive" | "archived";
export type Weight = "250g" | "500g" | "1kg";
export const WEIGHTS: Weight[] = ["250g", "500g", "1kg"];

export interface Admin {
  id: string;
  email: string;
  full_name: string | null;
  role: Role;
  is_active: boolean;
  last_login_at: string | null;
}

export interface Category {
  id: string;
  slug: string;
  name: string;
  name_te: string | null;
  description: string | null;
  description_te: string | null;
  image_url: string | null;
  sort_order: number;
  is_active: boolean;
}

export interface Inventory {
  quantity: number;
  reserved: number;
  low_stock_threshold: number;
  available: number;
}

export interface Variant {
  id: string;
  product_id: string;
  weight: Weight;
  price: string;
  compare_at_price: string | null;
  discount_percent: number;
  sku: string | null;
  is_active: boolean;
  inventory: Inventory | null;
}

export interface ProductImage {
  id: string;
  url: string;
  card_url: string;
  thumb_url: string;
  alt_text: string | null;
  sort_order: number;
  is_primary: boolean;
}

export interface Product {
  id: string;
  slug: string;
  category_id: string;
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
  status: ProductStatus;
  is_featured: boolean;
  is_best_seller: boolean;
  is_new_arrival: boolean;
  seo_title: string | null;
  seo_description: string | null;
  sold_count: number;
  images: ProductImage[];
  variants: Variant[];
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface DashboardSummary {
  products_total: number;
  products_active: number;
  products_inactive: number;
  products_archived: number;
  categories_total: number;
  variants_out_of_stock: number;
  variants_low_stock: number;
}

export interface LowStockItem {
  variant_id: string;
  product_id: string;
  product_name: string;
  weight: Weight;
  quantity: number;
  reserved: number;
  available: number;
  low_stock_threshold: number;
}
