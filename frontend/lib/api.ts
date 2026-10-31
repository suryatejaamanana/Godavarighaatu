import { API_BASE_URL } from "@/lib/config";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

interface Options {
  method?: string;
  json?: unknown;
  body?: FormData;
  query?: Record<string, string | number | boolean | null | undefined>;
}

const AUTH_PATHS = ["/admin/auth/login", "/admin/auth/refresh", "/admin/auth/logout"];

function buildUrl(path: string, query?: Options["query"]) {
  const url = new URL(`${API_BASE_URL}${path}`);
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, String(value));
  }
  return url.toString();
}

function send(path: string, { method = "GET", json, body, query }: Options) {
  return fetch(buildUrl(path, query), {
    method,
    credentials: "include", // httpOnly auth cookies; the browser adds the Origin header itself
    headers: json !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: json !== undefined ? JSON.stringify(json) : body,
  });
}

let refreshing: Promise<boolean> | null = null;

/** One refresh at a time: parallel 401s share the same attempt (refresh tokens rotate, so doubles would log out). */
function refreshSession(): Promise<boolean> {
  refreshing ??= send("/admin/auth/refresh", { method: "POST" })
    .then((r) => r.ok)
    .catch(() => false)
    .finally(() => {
      refreshing = null;
    });
  return refreshing;
}

export function errorMessage(data: unknown, fallback: string): string {
  const detail = (data as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d: { loc?: unknown[]; msg?: string }) => {
        const field = (d.loc ?? []).filter((p) => p !== "body").join(".");
        return field ? `${field}: ${d.msg}` : (d.msg ?? "Invalid input");
      })
      .join("; ");
  }
  return fallback;
}

export async function api<T = void>(path: string, options: Options = {}): Promise<T> {
  let res = await send(path, options).catch(() => {
    throw new ApiError(0, "Cannot reach the server. Check your connection and try again.");
  });

  if (res.status === 401 && !AUTH_PATHS.includes(path)) {
    if (await refreshSession()) {
      res = await send(path, options);
    }
    if (res.status === 401 && typeof window !== "undefined" && !window.location.pathname.startsWith("/admin/login")) {
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination -- full reload clears cached admin data
      window.location.href = "/admin/login";
    }
  }

  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new ApiError(res.status, errorMessage(data, `Request failed (${res.status})`));
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
