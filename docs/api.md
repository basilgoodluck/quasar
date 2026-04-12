# 🌐 API

The backend runs FastAPI on port `7052`. It serves the dashboard frontend and exposes WebSocket feeds for live updates.

---

### 📡 Endpoints

#### Trades

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/trades` | All trades (resolved + pending) |
| `GET` | `/trades/symbols` | List of active trading symbols |
| `WS` | `/ws/trades` | Live feed — emits `initial` on connect, `new_trade` on each new position |

#### Dashboard

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/dashboard/trades` | Formatted trade list for the UI |
| `GET` | `/dashboard/stats` | Agent status — equity, PnL, win rate, drawdown |

#### Market Data

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/binance/klines` | Proxied Binance kline data for the chart |

---

### 📦 Trade Response Shape

```json
{
  "id": "4",
  "symbol": "PF_ARBUSD",
  "side": "BUY",
  "entry_price": 0.1091,
  "exit_price": 0.0,
  "pnl": 0.0,
  "confidence": 0.8542,
  "decision": "approved",
  "timestamp": "2026-04-12T09:05:12+00:00",
  "hour": 9,
  "volume": 1000.0
}
```

> `exit_price` and `pnl` are `0.0` for pending trades — check `exit_price` truthiness in the frontend to detect pending.

---

### 🔌 WebSocket Messages

**On connect:**
```json
{ "type": "initial", "data": [ ...trades ] }
```

**On new trade:**
```json
{ "type": "new_trade", "data": { ...trade } }
```
