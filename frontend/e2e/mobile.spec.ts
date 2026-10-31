import { expect, test } from "@playwright/test";
import { signIn } from "./helpers";

test("admin is usable on a phone: menu, navigation, no horizontal scroll", async ({ page }) => {
  await signIn(page);
  await expect(page.getByRole("heading", { name: /Welcome/ })).toBeVisible();
  await page.getByRole("button", { name: "Open menu" }).click();
  await page.getByRole("link", { name: "Products" }).click();
  await expect(page).toHaveURL(/\/admin\/products$/);
  for (const path of ["/admin/dashboard", "/admin/products", "/admin/products/new", "/admin/categories", "/admin/inventory"]) {
    await page.goto(path);
    await expect(page.getByRole("main")).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow, `${path} scrolls horizontally`).toBeLessThanOrEqual(1);
  }
});
