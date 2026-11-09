export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000").replace(/\/$/, "");

// Built-in fallbacks. Every value here can be overridden from the database (website_settings,
// exposed by GET /site-settings); the admin screen for editing them arrives in Phase 11.
export const BRAND_DEFAULTS = {
  name: "Godavari Ghaatu",
  nameTe: "గోదావరి ఘాటు",
  tagline: "Authentic Andhra Spice in Every Spoon",
  label: "Home Made Pickles",
  announcement: "Home delivery available!",
  announcementTe: "హోమ్ డెలివరీ అందుబాటులో ఉంది!",
  heroHeadline: "Taste it once, and you will know real Andhra flavour",
  heroHeadlineTe: "ఒక్కసారి తింటేనే తెలుస్తుంది అసలైన ఆంధ్ర రుచి",
  about:
    "Godavari Ghaatu makes traditional Andhra pickles the homemade way, with the authentic village-style taste of the Godavari region.",
  aboutTe: "",
};
