import { defineConfig, devices } from "@playwright/test";

// Needs the backend running on :8000 with the test admins seeded
// (see docs/setup.md "Browser tests"). The frontend dev server is started automatically.
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  use: { baseURL: "http://localhost:3000", trace: "retain-on-failure" },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] }, testIgnore: /mobile/ },
    { name: "mobile", use: { ...devices["Pixel 7"] }, testMatch: /mobile/ },
  ],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000/admin/login",
    reuseExistingServer: true,
    timeout: 120_000,
  },
});
