// Centralized API client for the existing FastAPI backend.
// The base URL always comes from VITE_API_BASE_URL — never hardcoded.

export const API_BASE_URL = (
  (import.meta.env["VITE_API_BASE_URL"] as string | undefined) ?? ""
).replace(/\/$/, "");

export const TOKEN_STORAGE_KEY = "firstwatch.access_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  try {
    if (token) window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
    else window.localStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch {
    /* storage unavailable */
  }
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/** Listeners notified when the backend rejects our session (401). */
const unauthorizedListeners = new Set<() => void>();
export function onUnauthorized(fn: () => void) {
  unauthorizedListeners.add(fn);
  return () => {
    unauthorizedListeners.delete(fn);
  };
}

function humanMessage(status: number, detail?: string): string {
  if (detail && detail.trim()) return detail.trim();
  switch (status) {
    case 400:
      return "That request wasn't valid.";
    case 401:
      return "Your session has expired. Please sign in again.";
    case 403:
      return "You don't have access to this.";
    case 404:
      return "We couldn't find that.";
    case 409:
      return "That already exists.";
    case 422:
      return "Some of the details provided weren't accepted.";
    case 429:
      return "Too many requests. Please wait a moment.";
    default:
      return status >= 500
        ? "The service is having trouble right now. Please try again."
        : "Something went wrong.";
  }
}

function extractDetail(body: unknown): string | undefined {
  if (!body || typeof body !== "object") return undefined;
  const detail = (body as Record<string, unknown>)["detail"];
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const parts = detail
      .map((d) => {
        if (d && typeof d === "object" && typeof (d as any).msg === "string") {
          const loc = Array.isArray((d as any).loc)
            ? (d as any).loc.filter((l: unknown) => typeof l === "string" && l !== "body").join(" ")
            : "";
          return loc ? `${loc}: ${(d as any).msg}` : (d as any).msg;
        }
        return typeof d === "string" ? d : null;
      })
      .filter(Boolean);
    if (parts.length) return parts.join(". ");
  }
  const message = (body as Record<string, unknown>)["message"];
  if (typeof message === "string") return message;
  return undefined;
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  auth?: boolean;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, auth = true } = options;

  if (!API_BASE_URL) {
    throw new ApiError(
      0,
      "The backend address isn't configured yet. Set VITE_API_BASE_URL to your FastAPI URL.",
    );
  }

  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
  } catch {
    throw new ApiError(
      0,
      "We couldn't reach the service. Check your connection and that the backend is running.",
    );
  }

  const text = await response.text();
  let parsed: unknown = undefined;
  if (text) {
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = undefined;
    }
  }

  if (!response.ok) {
    if (response.status === 401) {
      unauthorizedListeners.forEach((fn) => fn());
    }
    throw new ApiError(response.status, humanMessage(response.status, extractDetail(parsed)));
  }

  return (parsed as T) ?? (undefined as T);
}

export const api = {
  register: (email: string, password: string) =>
    apiRequest<unknown>("/api/auth/register", {
      method: "POST",
      body: { email, password },
      auth: false,
    }),
  login: (email: string, password: string) =>
    apiRequest<Record<string, unknown>>("/api/auth/login", {
      method: "POST",
      body: { email, password },
      auth: false,
    }),
  me: () => apiRequest<Record<string, unknown>>("/api/auth/me"),

  companies: () => apiRequest<unknown[]>("/api/watchlist/companies"),
  addCompany: (payload: Record<string, unknown>) =>
    apiRequest<unknown>("/api/watchlist/companies", { method: "POST", body: payload }),
  removeCompany: (id: number | string) =>
    apiRequest<unknown>(`/api/watchlist/companies/${id}`, { method: "DELETE" }),

  themes: () => apiRequest<unknown[]>("/api/watchlist/themes"),
  addTheme: (name: string, keyword: string) =>
    apiRequest<unknown>("/api/watchlist/themes", { method: "POST", body: { name, keyword } }),
  removeTheme: (id: number | string) =>
    apiRequest<unknown>(`/api/watchlist/themes/${id}`, { method: "DELETE" }),

  tracking: () => apiRequest<unknown>("/api/tracking"),
  trackingFor: (ticker: string) => apiRequest<unknown>(`/api/tracking/${ticker}`),
  refreshTracking: () => apiRequest<unknown>("/api/tracking/refresh", { method: "POST" }),

  signals: () => apiRequest<unknown>("/api/signals"),
  signal: (id: number | string) => apiRequest<unknown>(`/api/signals/${id}`),
  refreshSignals: () => apiRequest<unknown>("/api/signals/refresh", { method: "POST" }),
  notifications: () => apiRequest<unknown>("/api/notifications"),
  readNotification: (id: number | string) =>
    apiRequest<unknown>(`/api/notifications/${id}/read`, { method: "POST" }),
};

/** Backends sometimes wrap lists in {items:[...]} / {results:[...]}; unwrap safely. */
export function asList<T>(value: unknown): T[] {
  if (Array.isArray(value)) return value as T[];
  if (value && typeof value === "object") {
    for (const key of ["items", "results", "data", "companies", "themes", "signals", "tracking"]) {
      const inner = (value as Record<string, unknown>)[key];
      if (Array.isArray(inner)) return inner as T[];
    }
  }
  return [];
}
