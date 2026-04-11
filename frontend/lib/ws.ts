// lib/ws.ts
import { BASE_URL } from "@/lib/api"

const WS_BASE = BASE_URL.replace(/^http/, "ws")

export const createTradeWebSocket = (onMessage: (data: any) => void): WebSocket => {
  const ws = new WebSocket(`${WS_BASE}/ws/trades`)

  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data)
    onMessage(msg)
  }

  return ws
}

export const createBinanceWebSocket = (
  symbol: string,
  interval: string = "15m",
  onMessage: (data: any) => void
): WebSocket => {
  const ws = new WebSocket(`${WS_BASE}/ws/binance-stream?symbol=${symbol.toLowerCase()}&interval=${interval}`)

  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data)
    onMessage(msg)
  }

  return ws
}