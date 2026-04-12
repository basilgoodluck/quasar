export type Regime = "bull" | "bear" | "neutral"
export type Decision = "approved" | "rejected" | "skipped"
export type Side = "BUY" | "SELL"

export interface AgentStatus {
  equity: number
  pnl: number
  win_rate: number
  trades_this_hour: number
  drawdown_percent: number
  drawdown_limit: number
}

export interface Trade {
  id: string
  timestamp: string
  symbol: string
  side: Side
  entry_price: number
  exit_price: number
  pnl: number
  confidence: number
  decision: Decision
  volume: number
  hour: number
}

export interface RegimePoint {
  timestamp: string
  confidence: number
  regime: Regime
  hour_of_day: number
}

export interface RiskPoint {
  timestamp: string
  equity: number
  peak_equity: number
  drawdown: number
  trade_id: string
  pnl: number
  is_win: boolean
}

export interface ReputationPoint {
  timestamp: string
  reputation_score: number
  validation_score: number
  checkpoint_posted: boolean
}

export interface PositionPoint {
  timestamp: string
  position_size: number
  risk_percent: number
  confidence: number
}

export interface PublicStats {
  total_pnl: number
  win_rate: number
  total_trades: number
  equity_history: Array<{
    timestamp: string
    equity: number
  }>
  trade_outcomes: Array<{
    label: string
    wins: number
    losses: number
  }>
}

export interface Candle {
  time: number
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface TradeMarker {
  time: number
  position: "aboveBar" | "belowBar"
  color: string
  shape: "arrowUp" | "arrowDown"
  text: string
  id: string
}

export interface BinanceKlineMessage {
  e: string
  E: number
  s: string
  k: {
    t: number
    T: number
    s: string
    i: string
    o: string
    c: string
    h: string
    l: string
    v: string
    x: boolean
  }
}

export interface Config {
  telegram_bot_token: string
  discord_webhook_url: string
  max_drawdown_percent: number
  max_trades_per_hour: number
  risk_per_trade_percent: number
}