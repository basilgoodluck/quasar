// In your config file (e.g. config/index.ts or lib/config.ts)
export const config = {
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:7052",
  NEXT_PUBLIC_TRADE_WS_URL: process.env.NEXT_PUBLIC_TRADE_WS_URL ?? "ws://localhost:7052/ws/trade/ws",
  // ... other configs
}