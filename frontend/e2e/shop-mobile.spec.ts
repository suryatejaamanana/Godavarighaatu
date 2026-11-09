import { expect, test } from "@playwright/test";

const PAGES = ["/", "/products", "/category/veg-pickles", "/products/sample-boneless-gongura-chicken-pickle", "/products?q=zzz"];

test("storefront fits a phone screen: no sideways scrolling anywhere", async ({ page }) => {
  for (const path of PAGES) {
    await page.goto(path);
    await expect(page.getByRole("main")).toBeVisible();
    await page.waitForLoadState("load");
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow, `${path} scrolls sideways`).toBeLessThanOrEqual(1);
  }
});

test("search is always visible on a phone and menu reaches every category", async ({ page }) => {
  await page.goto("/");
  const search = page.getByRole("searchbox", { name: "Search pickles" }).and(page.locator(":visible"));
  await expect(search).toBeVisible();
  expect((await search.boundingBox())!.height).toBeGreaterThanOrEqual(44); // comfortable touch target

  await page.getByRole("button", { name: "Open menu" }).click();
  const menu = page.getByRole("navigation", { name: "Mobile" });
  await expect(menu.getByRole("link")).toHaveCount(2 + 9); // Home, All pickles + 9 categories
  await menu.getByRole("link", { name: /Fish Pickles/ }).click();
  await expect(page).toHaveURL(/\/category\/fish-pickles/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Fish Pickles");
  await expect(menu).toBeHidden(); // menu closes after navigating
});

test("a customer can browse from home to a product and pick a size by tapping", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("region", { name: "Best sellers" }).getByRole("article").first().getByRole("link").first().click();
  await expect(page).toHaveURL(/\/products\/sample-/);
  const buy = page.locator("fieldset").locator("xpath=..");
  await page.getByText("500g", { exact: true }).tap();
  await expect(buy).toContainText("₹290");
  for (const label of await page.locator("fieldset label").all()) {
    expect((await label.boundingBox())!.height).toBeGreaterThanOrEqual(44); // touch-friendly size buttons
  }
});

test("product grid shows two columns on a phone", async ({ page }) => {
  await page.goto("/products");
  await expect(page.locator("article").nth(1)).toBeVisible(); // product cards stream in after load
  const first = await page.locator("article").nth(0).boundingBox();
  const second = await page.locator("article").nth(1).boundingBox();
  expect(Math.abs(first!.y - second!.y)).toBeLessThan(5); // same row
});
