# 🏗 Architecture

Quasar runs as a set of Docker containers that each own a single responsibility. They share a PostgreSQL database and a Redis cache but otherwise operate independently.

---

### 🔄 Services

| Container | Role |
|-----------|------|
| `quasar-agent` | Main trading loop — analyzes symbols, opens positions |
| `quasar-monitor` | Watches open positions, closes on SL / TP / timeout |
| `quasar-collector` | Fetches and stores OHLCV candle data |
| `quasar-trainer` | Retrains the regime classification model on a schedule |
| `quasar-backend` | FastAPI — serves the dashboard and WebSocket feeds |
| `quasar-postgres` | Persistent storage for trades, candles, reputation |
| `quasar-redis` | Caching layer for fast reads |

---

### 🌊 Data Flow

```
Binance (OHLCV)
      │
      ▼
  collector ──► postgres (candles)
                    │
                    ▼
                 trainer ──► regime model (updated weights)
                    │
                    ▼
                  agent
                    │
          ┌─────────┴──────────┐
          ▼                    ▼
     analyze(symbol)      reputation score
          │
          ▼
     detect_regime()
          │
          ▼
     compute_risk()
          │
          ▼
     ARC indicators
     (MA, Fisher, structure)
          │
          ▼
     ai_trade_review()  ◄── OpenAI
          │
          ▼
     open_position()
          │
     ┌────┴────┐
     ▼         ▼
  Kraken    postgres
  Futures   (PENDING)
               │
               ▼
            monitor
               │
        ┌──────┴──────┐
        ▼             ▼
    SL/TP/timeout   Kraken
    triggered       close order
        │
        ▼
    postgres (WIN/LOSS)
        │
        ▼
    backend ──► frontend (WebSocket)
```

---

### 🔗 Shared Resources

- **PostgreSQL** — all containers read/write trades, candles, symbols, reputation
- **Redis** — backend uses it for caching dashboard queries and WebSocket fan-out
- **Kraken CLI** — agent and monitor both shell out to it for order execution
