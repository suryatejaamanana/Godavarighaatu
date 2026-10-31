import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api, ApiError, errorMessage } from "@/lib/api";

const json = (status: number, body?: unknown) =>
  new Response(body === undefined ? null : JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

let fetchMock: ReturnType<typeof vi.fn>;
const location = { pathname: "/admin/products", href: "" };

beforeEach(() => {
  fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
  vi.stubGlobal("window", { location });
  location.pathname = "/admin/products";
  location.href = "";
});
afterEach(() => vi.unstubAllGlobals());

const calls = () => fetchMock.mock.calls.map(([url, init]) => `${init?.method ?? "GET"} ${new URL(url).pathname}`);

describe("api()", () => {
  it("sends cookies, JSON bodies and query parameters", async () => {
    fetchMock.mockResolvedValue(json(200, { ok: true }));
    await api("/admin/products", { method: "POST", json: { name: "x" }, query: { q: "a b", page: 2, empty: "", none: undefined } });
    const [url, init] = fetchMock.mock.calls[0];
    expect(init.credentials).toBe("include");
    expect(init.headers).toEqual({ "Content-Type": "application/json" });
    expect(init.body).toBe('{"name":"x"}');
    expect(new URL(url).search).toBe("?q=a+b&page=2"); // empty/undefined are dropped
  });

  it("does not set a JSON content type for FormData (the browser adds the multipart boundary)", async () => {
    fetchMock.mockResolvedValue(json(201, {}));
    const form = new FormData();
    form.append("file", new Blob(["x"]), "a.png");
    await api("/admin/products/1/images", { method: "POST", body: form });
    expect(fetchMock.mock.calls[0][1].headers).toBeUndefined();
  });

  it("returns undefined for 204", async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }));
    await expect(api("/admin/categories/1", { method: "DELETE" })).resolves.toBeUndefined();
  });

  it("refreshes once on 401 and retries the original request", async () => {
    fetchMock
      .mockResolvedValueOnce(json(401, { detail: "Invalid or expired token." }))
      .mockResolvedValueOnce(json(200, {})) // refresh
      .mockResolvedValueOnce(json(200, { items: [] }));
    await expect(api("/admin/products")).resolves.toEqual({ items: [] });
    expect(calls()).toEqual(["GET /api/v1/admin/products", "POST /api/v1/admin/auth/refresh", "GET /api/v1/admin/products"]);
    expect(location.href).toBe("");
  });

  it("shares one refresh between parallel 401s (refresh tokens rotate)", async () => {
    let refreshes = 0;
    fetchMock.mockImplementation(async (url: string) => {
      const path = new URL(url).pathname;
      if (path.endsWith("/auth/refresh")) {
        refreshes++;
        await new Promise((r) => setTimeout(r, 10));
        return json(200, {});
      }
      return refreshes === 0 ? json(401, { detail: "expired" }) : json(200, { path });
    });
    const results = await Promise.all([api("/admin/a"), api("/admin/b"), api("/admin/c")]);
    expect(refreshes).toBe(1);
    expect(results).toHaveLength(3);
  });

  it("sends the user to the login page when the refresh fails", async () => {
    fetchMock.mockResolvedValueOnce(json(401, { detail: "x" })).mockResolvedValueOnce(json(401, { detail: "x" })).mockResolvedValueOnce(json(401, { detail: "x" }));
    await expect(api("/admin/products")).rejects.toMatchObject({ status: 401 });
    expect(location.href).toBe("/admin/login");
  });

  it("does not redirect when already on the login page", async () => {
    location.pathname = "/admin/login";
    fetchMock.mockResolvedValue(json(401, { detail: "x" }));
    await expect(api("/admin/auth/me")).rejects.toBeInstanceOf(ApiError);
    expect(location.href).toBe("");
  });

  it("never tries to refresh for login/refresh/logout themselves", async () => {
    fetchMock.mockResolvedValue(json(401, { detail: "Invalid email or password." }));
    await expect(api("/admin/auth/login", { method: "POST", json: {} })).rejects.toThrow("Invalid email or password.");
    expect(calls()).toEqual(["POST /api/v1/admin/auth/login"]);
  });

  it("does not refresh for non-401 errors", async () => {
    fetchMock.mockResolvedValue(json(403, { detail: "You do not have permission to perform this action." }));
    await expect(api("/admin/categories", { method: "POST", json: {} })).rejects.toMatchObject({ status: 403 });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("turns network failures into a friendly error", async () => {
    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));
    await expect(api("/admin/products")).rejects.toMatchObject({ status: 0, message: expect.stringContaining("Cannot reach the server") });
  });

  it("handles non-JSON error bodies", async () => {
    fetchMock.mockResolvedValue(new Response("<html>Bad gateway</html>", { status: 502 }));
    await expect(api("/admin/products")).rejects.toMatchObject({ status: 502, message: "Request failed (502)" });
  });
});

describe("errorMessage()", () => {
  it("uses string details", () => expect(errorMessage({ detail: "Nope" }, "fallback")).toBe("Nope"));
  it("formats FastAPI validation errors with field names", () => {
    const detail = [
      { loc: ["body", "variants", 0, "price"], msg: "Input should be greater than or equal to 0" },
      { loc: ["body"], msg: "Field required" },
    ];
    expect(errorMessage({ detail }, "x")).toBe("variants.0.price: Input should be greater than or equal to 0; Field required");
  });
  it("falls back when there is no detail", () => expect(errorMessage(null, "fallback")).toBe("fallback"));
});
