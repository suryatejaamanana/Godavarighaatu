import { expect, type Page } from "@playwright/test";

export const MANAGER = { email: "e2e-manager@example.com", password: "e2e-test-password-1" };
export const STAFF = { email: "e2e-staff@example.com", password: "e2e-test-password-1" };

export async function signIn(page: Page, user = MANAGER) {
  await page.goto("/admin/login");
  await page.getByLabel("Email").fill(user.email);
  await page.getByLabel("Password").fill(user.password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/admin\/dashboard/);
}

/** A valid 1×1 PNG, so uploads exercise the real image pipeline. */
export const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
  "base64",
);
export const unique = (prefix: string) => `${prefix} ${Date.now().toString(36)}`;
