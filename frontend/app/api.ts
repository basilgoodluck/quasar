const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? ""
const MOCK_MODE = process.env.NEXT_PUBLIC_MOCK === "true"

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE"

interface RequestOptions {
  body?: unknown
  headers?: Record<string, string>
  signal?: AbortSignal
}

async function request<T>(
  method: HttpMethod,
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { body, headers = {}, signal } = options

  const res = await fetch(`${BASE_URL}${endpoint}`, {
    method,
    signal,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  })

  if (!res.ok) {
    const error = await res.text().catch(() => res.statusText)
    throw new Error(`${method} ${endpoint} failed [${res.status}]: ${error}`)
  }

  return res.json() as Promise<T>
}

async function loadMock<T>(file: string): Promise<T> {
  const mod = await import(`@/data/${file}.json`)
  return mod.default as T
}

function resolve<T>(file: string, endpoint: string): Promise<T> {
  return MOCK_MODE ? loadMock<T>(file) : request<T>("GET", endpoint)
}

export const api = {
  get: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>("GET", endpoint, options),

  post: <T>(endpoint: string, body: unknown, options?: RequestOptions) =>
    request<T>("POST", endpoint, { ...options, body }),

  put: <T>(endpoint: string, body: unknown, options?: RequestOptions) =>
    request<T>("PUT", endpoint, { ...options, body }),

  patch: <T>(endpoint: string, body: unknown, options?: RequestOptions) =>
    request<T>("PATCH", endpoint, { ...options, body }),

  delete: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>("DELETE", endpoint, options),

  dashboard: {
    status: () => resolve("status", "/api/dashboard/status"),
    trades: () => resolve("trades", "/api/dashboard/trades"),
    regime: () => resolve("regime", "/api/dashboard/regime"),
    risk: () => resolve("risk", "/api/dashboard/risk"),
    reputation: () => resolve("reputation", "/api/dashboard/reputation"),
    positions: () => resolve("positions", "/api/dashboard/positions"),
    publicStats: () => resolve("public-stats", "/api/public/stats"),
    updateConfig: (body: unknown) =>
      request("PATCH", "/api/dashboard/config", { body }),
  },
}