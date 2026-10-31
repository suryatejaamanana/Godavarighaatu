import { api } from "@/lib/api";
import type {
  Admin,
  Category,
  DashboardSummary,
  LowStockItem,
  Page,
  Product,
  ProductImage,
  ProductStatus,
  Variant,
  Weight,
} from "@/types/api";

// ---- auth ----
export const login = (email: string, password: string) =>
  api<Admin>("/admin/auth/login", { method: "POST", json: { email, password } });
export const logout = () => api("/admin/auth/logout", { method: "POST" });
export const getMe = () => api<Admin>("/admin/auth/me");

// ---- dashboard ----
export const getSummary = () => api<DashboardSummary>("/admin/dashboard/summary");

// ---- categories ----
export type CategoryInput = Partial<Omit<Category, "id" | "slug">> & { name: string; slug?: string };
export const listCategories = () => api<Category[]>("/admin/categories");
export const createCategory = (data: CategoryInput) => api<Category>("/admin/categories", { method: "POST", json: data });
export const updateCategory = (id: string, data: Partial<CategoryInput>) =>
  api<Category>(`/admin/categories/${id}`, { method: "PATCH", json: data });
export const deleteCategory = (id: string) => api(`/admin/categories/${id}`, { method: "DELETE" });

// ---- products ----
export interface ProductFilters {
  q?: string;
  category_id?: string;
  status?: ProductStatus | "";
  page?: number;
  page_size?: number;
}
export type ProductInput = Partial<
  Omit<Product, "id" | "slug" | "sold_count" | "images" | "variants">
> & { name: string; category_id: string; slug?: string };
export interface NewVariant {
  weight: Weight;
  price: string;
  compare_at_price?: string | null;
  sku?: string | null;
  is_active?: boolean;
  quantity?: number;
  low_stock_threshold?: number;
}

export const listProducts = (filters: ProductFilters = {}) =>
  api<Page<Product>>("/admin/products", { query: { ...filters } });
export const getProduct = (id: string) => api<Product>(`/admin/products/${id}`);
export const createProduct = (data: ProductInput & { variants?: NewVariant[] }) =>
  api<Product>("/admin/products", { method: "POST", json: data });
export const updateProduct = (id: string, data: Partial<ProductInput>) =>
  api<Product>(`/admin/products/${id}`, { method: "PATCH", json: data });
export const archiveProduct = (id: string) => api<Product>(`/admin/products/${id}/archive`, { method: "POST" });
export const restoreProduct = (id: string) => api<Product>(`/admin/products/${id}/restore`, { method: "POST" });

// ---- variants & inventory ----
export const createVariant = (productId: string, data: NewVariant) =>
  api<Variant>(`/admin/products/${productId}/variants`, { method: "POST", json: data });
export const updateVariant = (
  id: string,
  data: { price?: string; compare_at_price?: string | null; sku?: string | null; is_active?: boolean },
) => api<Variant>(`/admin/variants/${id}`, { method: "PATCH", json: data });
export const deleteVariant = (id: string) => api(`/admin/variants/${id}`, { method: "DELETE" });
export const setInventory = (variantId: string, quantity: number, low_stock_threshold?: number) =>
  api<Variant>(`/admin/variants/${variantId}/inventory`, { method: "PUT", json: { quantity, low_stock_threshold } });
export const adjustInventory = (variantId: string, delta: number) =>
  api<Variant>(`/admin/variants/${variantId}/inventory/adjustments`, { method: "POST", json: { delta } });
export const listLowStock = () => api<LowStockItem[]>("/admin/inventory/low-stock");

// ---- images ----
export const uploadImage = (productId: string, file: File, altText?: string) => {
  const form = new FormData();
  form.append("file", file);
  if (altText) form.append("alt_text", altText);
  return api<ProductImage>(`/admin/products/${productId}/images`, { method: "POST", body: form });
};
export const updateImage = (id: string, data: { alt_text?: string | null; is_primary?: boolean }) =>
  api<ProductImage>(`/admin/images/${id}`, { method: "PATCH", json: data });
export const deleteImage = (id: string) => api(`/admin/images/${id}`, { method: "DELETE" });
export const reorderImages = (productId: string, ids: string[]) =>
  api<ProductImage[]>(`/admin/products/${productId}/images/order`, { method: "PUT", json: { ids } });
