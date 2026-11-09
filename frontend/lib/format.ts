export function formatPrice(value: string | number): string {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 2 }).format(Number(value));
}

/** Whole rupees when there are no paise (₹350), otherwise two decimals (₹350.50). Used on the storefront. */
export function formatRupees(value: string | number): string {
  const n = Number(value);
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: Number.isInteger(n) ? 0 : 2,
    maximumFractionDigits: 2,
  }).format(n);
}
