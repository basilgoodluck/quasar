// lib/api.ts
export const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:7052"

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

export const api = {
  get: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>("GET", endpoint, options),

  dashboard: {
    trades: () => api.get<any[]>("/api/dashboard/trades"),
  },

  binance: {
    klines: (symbol: string, interval: string = "15m", limit: number = 200) =>
      api.get<unknown[][]>(
        `/api/binance/klines?symbol=${symbol}&interval=${interval}&limit=${limit}`
      ),
  },
}