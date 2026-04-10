// lib/ws.ts
import { config } from "@/config"

export const createTradeWebSocket = (onMessage: (data: any) => void) => {
  const ws = new WebSocket(config.NEXT_PUBLIC_TRADE_WS_URL)

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
) => {
  const wsUrl = `${config.NEXT_PUBLIC_API_URL.replace(/^http/, "ws")}/ws/binance-stream?symbol=${symbol.toLowerCase()}&interval=${interval}`
  const ws = new WebSocket(wsUrl)

  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data)
    onMessage(msg)
  }

  return ws
}