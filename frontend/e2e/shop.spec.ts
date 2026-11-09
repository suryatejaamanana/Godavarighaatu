import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

// Note: after a client-side navigation Next keeps the previous page in the DOM (hidden), so counts use :visible.
// Runs against the development sample catalogue (backend/scripts/seed_dev_catalog.py):
// 9 categories, 15 "Sample ..." products; only some have photos; "Sample Prawn Pickle" is sold out.

const meta = async (page: Page, selector: string) => {
  const found = page.locator(selector);
  return (await found.count()) ? found.first().getAttribute("content") : null;
};
const jsonLd = async (page: Page) =>
  (await page.locator('script[type="application/ld+json"]').allTextContents()).map((t) => JSON.parse(t));
const prices = async (page: Page) =>
  (await page.locator("article:visible p span.font-display").allTextContents()).map((t) =>
    Number(t.replace(/[^\d.]/g, "")),
  );

test.describe("homepage", () => {
  test("shows the brand, hero, categories and live products", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Home delivery available!").first()).toBeVisible();
    await expect(page.getByRole("heading", { level: 1 })).toContainText("ఒక్కసారి తింటేనే తెలుస్తుంది అసలైన ఆంధ్ర రుచి");
    await expect(page.getByText("Authentic Andhra Spice in Every Spoon").first()).toBeVisible();
    await expect(page.getByRole("region", { name: "Categories" }).or(page.locator("#categories")).getByRole("link")).toHaveCount(9 + 1); // 9 tiles + "All pickles"
    await expect(page.getByRole("region", { name: "Best sellers" }).getByRole("article").first()).toBeVisible();
    await expect(page.getByRole("region", { name: "New arrivals" }).getByRole("article").first()).toBeVisible();
    await expect(page.getByRole("heading", { name: "Why Godavari Ghaatu" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "About us" })).toBeVisible();
  });

  test("has complete SEO metadata and structured data", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/Godavari Ghaatu/);
    expect(await meta(page, 'meta[name="description"]')).toContain("Authentic Andhra Spice");
    await expect(page.locator('link[rel="canonical"]')).toHaveAttribute("href", /^http:\/\/localhost:3000\/?$/);
    expect(await meta(page, 'meta[property="og:title"]')).toContain("Godavari Ghaatu");
    expect(await meta(page, 'meta[property="og:type"]')).toBe("website");
    await expect(page.locator("html")).toHaveAttribute("lang", "en");
    const org = (await jsonLd(page)).find((d) => d["@type"] === "Organization");
    expect(org.name).toBe("Godavari Ghaatu");
  });

  test("product images load, are responsive and lazy below the fold", async ({ page }) => {
    await page.goto("/");
    const img = page.getByRole("region", { name: "Best sellers" }).locator("img").first();
    await img.scrollIntoViewIfNeeded();
    await expect.poll(() => img.evaluate((el: HTMLImageElement) => el.complete && el.naturalWidth > 0)).toBe(true);
    await expect(img).toHaveAttribute("srcset", /200w.*600w.*1920w/);
    await expect(img).toHaveAttribute("loading", "lazy");
    await expect(img).toHaveAttribute("alt", /.+/);
  });

  test("products without a photo show a placeholder, not a broken image", async ({ page }) => {
    await page.goto("/products/sample-mutton-pickle");
    await expect(page.getByRole("img", { name: /photo coming soon/i }).first()).toBeVisible();
    await expect(page.locator("img[src='']")).toHaveCount(0);
  });
});

test.describe("navigation and browsing", () => {
  test("category tile leads to a category page that lists only that category", async ({ page }) => {
    await page.goto("/");
    await page.locator("#categories").getByRole("link", { name: /Mango Pickles/ }).click();
    await expect(page).toHaveURL(/\/category\/mango-pickles$/);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("Mango Pickles");
    await expect(page.getByRole("navigation", { name: "Categories" }).getByRole("link", { name: "Mango Pickles" })).toHaveAttribute("aria-current", "page");
    await expect(page.locator("article:visible")).toHaveCount(2); // waits for the new page's results to arrive
    const names = await page.locator("article:visible h3").allTextContents();
    expect(names.join(" ")).toMatch(/Mango Avakaya.*Magaya|Magaya.*Mango Avakaya/);
    await expect(page).toHaveTitle("Mango Pickles | Godavari Ghaatu");
  });

  test("search finds products, escapes odd input and explains empty results", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("searchbox", { name: "Search pickles" }).first().fill("gongura");
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/\/products\?q=gongura/);
    await expect(page.getByText(/^\d+ pickles? for/)).toBeVisible(); // results have rendered
    const names = await page.locator("article:visible h3").allTextContents();
    expect(names.length).toBeGreaterThanOrEqual(3);
    for (const n of names) expect(n.toLowerCase()).toContain("gongura");
    // search result pages are kept out of search engines
    expect(await meta(page, 'meta[name="robots"]')).toContain("noindex");

    await page.goto("/products?q=" + encodeURIComponent("<script>alert(1)</script>%_"));
    await expect(page.getByText("Nothing here yet")).toBeVisible();
    await expect(page.locator("strong", { hasText: "<script>" })).toBeVisible(); // shown as text, not executed
  });

  test("sorting by price orders the grid and is reflected in the URL", async ({ page }) => {
    await page.goto("/category/veg-pickles");
    await page.getByLabel("Sort by").selectOption("price_asc");
    await expect(page).toHaveURL(/sort=price_asc/);
    const asc = await prices(page);
    expect(asc.length).toBeGreaterThan(1);
    expect(asc).toEqual([...asc].sort((a, b) => a - b));
    await page.getByLabel("Sort by").selectOption("price_desc");
    await expect(page).toHaveURL(/sort=price_desc/);
    const desc = await prices(page);
    expect(desc).toEqual([...desc].sort((a, b) => b - a));
  });

  test("pagination splits 15 products into 12 + 3 with crawler hints", async ({ page }) => {
    await page.goto("/products");
    await expect(page.locator("article:visible")).toHaveCount(12);
    await expect(page.locator('a[rel="next"]')).toBeVisible();
    expect(await meta(page, 'meta[name="robots"]')).toBeNull(); // the first page is indexable
    await page.getByRole("link", { name: "Next →" }).click();
    await expect(page).toHaveURL(/page=2/);
    await expect(page.locator("article:visible")).toHaveCount(3);
    await expect(page.getByRole("link", { name: "← Previous" })).toBeVisible();
    expect(await meta(page, 'meta[name="robots"]')).toContain("noindex");
    await page.goto("/products?page=999");
    await expect(page.getByText("Nothing here yet")).toBeVisible();
    await page.goto("/products?page=abc&sort=nonsense");
    await expect(page.locator("article:visible")).toHaveCount(12); // invalid input falls back to defaults
  });

  test("product cards show price, discount, availability and a details link", async ({ page }) => {
    await page.goto("/products?q=Boneless");
    const card = page.locator("article", { hasText: "Sample Boneless Gongura Chicken Pickle" });
    await expect(card).toContainText("From");
    await expect(card).toContainText("₹150");
    await expect(card).toContainText("Best seller");
    await expect(card).toContainText("View details");
    await page.goto("/products?q=Prawn");
    await expect(page.locator("article", { hasText: "Sample Prawn Pickle" })).toContainText("Sold out");
  });
});

test.describe("product detail page", () => {
  const url = "/products/sample-boneless-gongura-chicken-pickle";

  test("shows details, switches size and updates price and stock", async ({ page }) => {
    await page.goto(url);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("Sample Boneless Gongura Chicken Pickle");
    await expect(page.getByText("బోన్‌లెస్ గోంగూర చికెన్ పచ్చడి").first()).toBeVisible();
    const buy = page.locator("fieldset").locator("xpath=..");
    await expect(buy).toContainText("₹150");
    await expect(buy).toContainText("In stock");

    await page.getByRole("radio", { name: /500g/ }).check({ force: true });
    await expect(buy).toContainText("₹290");
    await expect(buy.locator("s")).toHaveText("₹320"); // original price struck through
    await expect(buy).toContainText("9% OFF");

    await page.getByRole("radio", { name: /1kg/ }).check({ force: true });
    await expect(buy).toContainText("₹560");
    await expect(buy).toContainText("Only 3 left");
  });

  test("gallery thumbnails change the main photo", async ({ page }) => {
    await page.goto(url);
    const main = page.locator("main img").first();
    const before = await main.getAttribute("src");
    await page.getByRole("button", { name: "Show photo 2 of 2" }).click();
    await expect.poll(() => main.getAttribute("src")).not.toBe(before);
  });

  test("details, related products and breadcrumb are present", async ({ page }) => {
    await page.goto(url);
    await expect(page.getByRole("navigation", { name: "Breadcrumb" })).toContainText("Chicken Pickles");
    await expect(page.getByText("Sample ingredients (placeholder).")).toBeHidden(); // collapsed
    await page.locator("summary", { hasText: "Ingredients" }).click();
    await expect(page.getByText("Sample ingredients (placeholder).")).toBeVisible();
    await expect(page.getByRole("region", { name: "Related pickles" }).getByRole("article")).toHaveCount(1);
  });

  test("sold-out products say so and cannot be mistaken for available", async ({ page }) => {
    await page.goto("/products/sample-prawn-pickle");
    await expect(page.getByText("Out of stock")).toBeVisible();
    await expect(page.getByText("Sold out").first()).toBeVisible();
  });

  test("has product SEO: title, description, Open Graph image, canonical, JSON-LD", async ({ page }) => {
    await page.goto(url);
    await expect(page).toHaveTitle("Sample Boneless Gongura Chicken Pickle | Godavari Ghaatu");
    expect(await meta(page, 'meta[name="description"]')).toContain("Sample product for development");
    await expect(page.locator('link[rel="canonical"]')).toHaveAttribute("href", /\/products\/sample-boneless-gongura-chicken-pickle$/);
    expect(await meta(page, 'meta[property="og:image"]')).toMatch(/\/media\/products\/.*detail\.webp$/);
    expect(await meta(page, 'meta[name="twitter:card"]')).toBe("summary_large_image");
    const docs = await jsonLd(page);
    const product = docs.find((d) => d["@type"] === "Product");
    expect(product.name).toBe("Sample Boneless Gongura Chicken Pickle");
    expect(product.offers).toMatchObject({ "@type": "AggregateOffer", priceCurrency: "INR", lowPrice: "150.00", highPrice: "560.00" });
    expect(product.image.length).toBe(2);
    expect(docs.find((d) => d["@type"] === "BreadcrumbList").itemListElement).toHaveLength(3);
  });

  test("unknown products and categories show a friendly not-found page that search engines skip", async ({ page }) => {
    for (const path of ["/products/does-not-exist", "/category/does-not-exist"]) {
      await page.goto(path);
      await expect(page.getByText(/could not find that page/i)).toBeVisible();
      expect(await meta(page, 'meta[name="robots"]')).toContain("noindex");
    }
    const res = await page.goto("/definitely/not/a/page");
    expect(res?.status()).toBe(404);
  });
});

test.describe("crawlers", () => {
  test("robots.txt blocks the admin and points to the sitemap", async ({ request }) => {
    const text = await (await request.get("/robots.txt")).text();
    expect(text).toMatch(/Disallow: \/admin/);
    expect(text).toMatch(/Sitemap: .*\/sitemap\.xml/);
  });

  test("sitemap lists home, listing, every category and every product", async ({ request }) => {
    const xml = await (await request.get("/sitemap.xml")).text();
    expect(xml).toContain("<loc>http://localhost:3000/</loc>");
    expect(xml).toContain("/products</loc>");
    expect((xml.match(/\/category\//g) ?? []).length).toBe(9);
    expect((xml.match(/\/products\/sample-/g) ?? []).length).toBe(15);
    expect(xml).not.toContain("/admin");
  });

  test("the admin login page is not indexable", async ({ page }) => {
    await page.goto("/admin/login");
    expect(await meta(page, 'meta[name="robots"]')).toContain("noindex");
  });
});

test.describe("accessibility (axe: WCAG 2 A/AA)", () => {
  for (const [name, path] of [
    ["home", "/"],
    ["listing", "/products"],
    ["category", "/category/veg-pickles"],
    ["product", "/products/sample-boneless-gongura-chicken-pickle"],
  ] as const) {
    test(`${name} has no serious violations`, async ({ page }) => {
      await page.goto(path);
      await page.waitForLoadState("networkidle");
      const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
      const serious = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
      expect(serious.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).slice(0, 3).join(" | ")}`)).toEqual([]);
    });
  }

  test("skip link and keyboard focus work", async ({ page }) => {
    await page.goto("/");
    await page.keyboard.press("Tab");
    await expect(page.getByRole("link", { name: "Skip to content" })).toBeFocused();
  });
});
