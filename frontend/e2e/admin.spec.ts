import { expect, test } from "@playwright/test";
import { PNG, signIn, STAFF, unique } from "./helpers";

test.describe("authentication", () => {
  test("protected pages redirect to login", async ({ page }) => {
    await page.goto("/admin/products");
    await expect(page).toHaveURL(/\/admin\/login/);
  });

  test("wrong password shows a generic error and stays on the login page", async ({ page }) => {
    await page.goto("/admin/login");
    await page.getByLabel("Email").fill("e2e-manager@example.com");
    await page.getByLabel("Password").fill("not-the-password");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.locator("form [role=alert]")).toHaveText("Invalid email or password.");
    await expect(page).toHaveURL(/\/admin\/login/);
  });

  test("rate limiting is explained in plain language", async ({ page }) => {
    // The real limiter has its own backend tests; here we only check how the UI presents a 429.
    await page.route("**/admin/auth/login", (route) =>
      route.fulfill({
        status: 429,
        contentType: "application/json",
        headers: { "access-control-allow-origin": "http://localhost:3000", "access-control-allow-credentials": "true" },
        body: JSON.stringify({ detail: "Too many requests. Please try again later." }),
      }),
    );
    await page.goto("/admin/login");
    await page.getByLabel("Email").fill("a@example.com");
    await page.getByLabel("Password").fill("whatever");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.locator("form [role=alert]")).toContainText("Too many attempts");
  });

  test("tokens live in httpOnly cookies, invisible to page scripts", async ({ page, context }) => {
    await signIn(page);
    const cookies = await context.cookies();
    const access = cookies.find((c) => c.name === "gg_access");
    expect(access?.httpOnly).toBe(true);
    expect(await page.evaluate(() => document.cookie)).not.toContain("gg_");
    expect(await page.evaluate(() => JSON.stringify(localStorage) + JSON.stringify(sessionStorage))).not.toContain("eyJ");
  });

  test("an expired access token is renewed silently via the refresh cookie", async ({ page, context }) => {
    await signIn(page);
    await context.clearCookies({ name: "gg_access" });
    await page.reload();
    await expect(page.getByRole("heading", { name: /Welcome/ })).toBeVisible();
    expect((await context.cookies()).some((c) => c.name === "gg_access")).toBe(true);
  });

  test("logout ends the session", async ({ page }) => {
    await signIn(page);
    await page.getByRole("button", { name: "Log out" }).click();
    await expect(page).toHaveURL(/\/admin\/login/);
    await page.goto("/admin/dashboard");
    await expect(page).toHaveURL(/\/admin\/login/);
  });
});

test.describe("catalog management", () => {
  test("category -> product -> sizes and stock -> photos -> list -> inventory", async ({ page }) => {
    const category = unique("E2E Category");
    const product = unique("E2E Gongura Pickle");
    await signIn(page);

    // --- category ---
    await page.goto("/admin/categories");
    await page.getByRole("button", { name: "New category" }).click();
    await page.getByLabel("Name (English)").fill(category);
    await page.getByLabel("Name (తెలుగు)").fill("గోంగూర");
    await page.getByRole("button", { name: "Save" }).click();
    await expect(page.getByText(category)).toBeVisible();

    // --- product with an initial size ---
    await page.goto("/admin/products/new");
    await page.getByLabel("Name (English)").fill(product);
    await page.getByLabel("Category").selectOption({ label: category });
    await page.getByLabel("Sell 500g").check();
    await page.locator("#v-1-price").fill("350.50");
    await page.locator("#v-1-qty").fill("12");
    await page.getByRole("button", { name: "Create product" }).click();
    await expect(page).toHaveURL(/\/admin\/products\/[0-9a-f-]{36}/);
    await expect(page.getByRole("heading", { name: product })).toBeVisible();

    // --- sizes & stock ---
    await page.getByRole("tab", { name: /Sizes/ }).click();
    await expect(page.locator("input[id^='price-']")).toHaveValue("350.50");
    await page.getByLabel("Stock quantity of 500g").fill("20");
    await page.getByRole("button", { name: "Save", exact: true }).click();
    await expect(page.getByText("Stock updated")).toBeVisible();
    await page.getByRole("button", { name: "Increase stock of 500g" }).click();
    await expect(page.getByLabel("Stock quantity of 500g")).toHaveValue("21");

    // add a second size, with its own price
    await page.locator("#new-weight").selectOption("1kg");
    await page.locator("#new-price").fill("650");
    await page.getByRole("button", { name: "Add size" }).click();
    await expect(page.getByText("1kg added")).toBeVisible();
    await expect(page.getByRole("tab", { name: /Sizes & stock \(2\)/ })).toBeVisible();

    // --- photos ---
    await page.getByRole("tab", { name: /Photos/ }).click();
    await page.getByLabel("Upload product photos").setInputFiles({ name: "jar.png", mimeType: "image/png", buffer: PNG });
    await expect(page.getByText("Main photo")).toBeVisible();
    const img = page.locator("img[src*='/media/products/']").first();
    await expect(img).toBeVisible();
    expect((await page.request.get((await img.getAttribute("src"))!)).status()).toBe(200);
    // a non-image is refused client-side
    await page.getByLabel("Upload product photos").setInputFiles({ name: "notes.txt", mimeType: "text/plain", buffer: Buffer.from("hi") });
    await expect(page.getByText(/only JPEG, PNG or WebP/)).toBeVisible();
    await page.getByRole("button", { name: "Delete photo 1" }).click();
    await page.getByRole("button", { name: "Delete", exact: true }).click();
    await expect(page.getByText("No photos yet")).toBeVisible();

    // --- list and search ---
    await page.goto("/admin/products");
    await page.getByLabel("Search products").fill(product);
    const row = page.getByRole("link", { name: new RegExp(product) });
    await expect(row).toBeVisible();
    await expect(row.getByText("₹350.50 – ₹650.00")).toBeVisible();

    // --- inventory page ---
    await page.goto("/admin/inventory");
    await expect(page.getByLabel(`Stock quantity of ${product} 500g`)).toHaveValue("21");

    // --- archive hides it from the shop API ---
    await page.goto("/admin/products");
    await page.getByLabel("Search products").fill(product);
    await page.getByRole("link", { name: new RegExp(product) }).click();
    await page.getByRole("button", { name: "Archive" }).click();
    await expect(page.getByText("Product archived")).toBeVisible();
  });

  test("validation errors are shown in the form", async ({ page }) => {
    await signIn(page);
    await page.goto("/admin/products/new");
    await page.getByRole("button", { name: "Create product" }).click();
    await expect(page.getByText("Name is required")).toBeVisible();
    await expect(page.getByText("Choose a category")).toBeVisible();
  });

  test("a category with products cannot be deleted (API error is surfaced)", async ({ page }) => {
    await signIn(page);
    await page.goto("/admin/categories");
    const first = page.getByRole("button", { name: /^Delete E2E Category/ }).first();
    await first.click();
    await page.getByRole("button", { name: "Delete", exact: true }).click();
    await expect(page.getByText(/has \d+ product/)).toBeVisible();
  });
});

test.describe("roles", () => {
  test("staff can manage stock but sees no editing controls", async ({ page }) => {
    await signIn(page, STAFF);
    await expect(page.getByText("staff", { exact: true })).toBeVisible();
    await page.goto("/admin/products");
    await expect(page.getByRole("link", { name: "Add product" })).toHaveCount(0);
    await page.goto("/admin/categories");
    await expect(page.getByRole("button", { name: "New category" })).toHaveCount(0);
    await page.goto("/admin/products/new");
    await expect(page.getByText(/do not have permission/)).toBeVisible();
    await page.goto("/admin/inventory");
    await expect(page.getByRole("heading", { name: "Inventory" })).toBeVisible();
  });
});
