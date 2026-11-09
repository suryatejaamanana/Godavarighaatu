import { cacheLife } from "next/cache";
import { API_BASE_URL, BRAND_DEFAULTS } from "@/lib/config";

export interface SiteSettings {
  name: string;
  nameTe: string;
  tagline: string;
  label: string;
  announcement: string;
  announcementTe: string;
  heroHeadline: string;
  heroHeadlineTe: string;
  about: string;
  aboutTe: string;
}

const KEYS: Record<keyof SiteSettings, string> = {
  name: "brand_name",
  nameTe: "brand_name_te",
  tagline: "brand_tagline",
  label: "brand_label",
  announcement: "announcement",
  announcementTe: "announcement_te",
  heroHeadline: "hero_headline",
  heroHeadlineTe: "hero_headline_te",
  about: "about_text",
  aboutTe: "about_text_te",
};

/** Merge database settings over the built-in defaults. Never throws: the site must render without them. */
export function mergeSettings(raw: Record<string, unknown> | null): SiteSettings {
  const result = { ...BRAND_DEFAULTS } as SiteSettings;
  for (const [field, key] of Object.entries(KEYS) as [keyof SiteSettings, string][]) {
    const value = raw?.[key];
    if (typeof value === "string" && value.trim()) result[field] = value.trim();
  }
  return result;
}

export async function getSiteSettings(): Promise<SiteSettings> {
  "use cache";
  cacheLife("minutes");
  try {
    const res = await fetch(`${API_BASE_URL}/site-settings`);
    return mergeSettings(res.ok ? await res.json() : null);
  } catch {
    return mergeSettings(null);
  }
}
