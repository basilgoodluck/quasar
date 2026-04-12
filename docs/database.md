# 🗄 Database

Quasar uses PostgreSQL 15. All services read and write to the same database.

---

### 📋 trade_outcomes

The central table. Every trade that gets opened writes a row here as `PENDING`, and the monitor updates it to `WIN` or `LOSS` when it closes.

| Column | Type | Description |
|--------|------|-------------|
| `intent_hash` | text (PK) | Unique hash from the on-chain trade intent |
| `pair` | text | Kraken pair in `PF_` format e.g. `PF_XBTUSD` |
| `action` | text | `LONG` or `SHORT` |
| `entry_price` | numeric | Price at the time the order was placed |
| `exit_price` | numeric | Price when the position was closed (null if PENDING) |
| `sl_price` | numeric | Calculated stop loss price |
| `tp_price` | numeric | Calculated take profit price |
| `rr_ratio` | numeric | Reward:risk ratio used for this trade |
| `amount_usd` | numeric | USD amount invested |
| `confidence_at_entry` | numeric | Regime confidence at time of entry |
| `reputation_at_entry` | numeric | Reputation score at time of entry |
| `checkpoint_hash` | text | On-chain checkpoint hash (or `PENDING`/`FAILED`) |
| `outcome_tx_hash` | text | On-chain hash for the close checkpoint |
| `status` | text | `PENDING`, `WIN`, or `LOSS` |
| `created_at` | int | Unix timestamp of trade open |
| `resolved_at` | int | Unix timestamp of trade close (null if PENDING) |

---

### 🔄 Row Lifecycle

```
open_position() called
       │
       ▼
INSERT status='PENDING', checkpoint_hash='PENDING'
       │
       ▼
Order placed on Kraken
       │
       ▼
UPDATE checkpoint_hash = on-chain hash (or 'FAILED')
       │
       ▼
monitor detects SL / TP / timeout
       │
       ▼
UPDATE exit_price, status='WIN'|'LOSS', resolved_at, outcome_tx_hash
```

---

### 📊 symbols

Tracks which symbols the agent should be trading.

| Column | Type | Description |
|--------|------|-------------|
| `symbol` | text (PK) | e.g. `BTCUSDT` |
| `active` | bool | Whether to include in the trading loop |
| `intervals` | text[] | Candle intervals used e.g. `{5m,30m}` |
| `asset_class` | text | e.g. `crypto` |

Seeded on startup with 19 default symbols. Adding a symbol here and setting `active=TRUE` is all that's needed to start trading it.

---

### 📈 Other Tables

| Table | Purpose |
|-------|---------|
| `candles` | Raw OHLCV data stored by the collector |
| `reputation` | Historical reputation score snapshots |
| `regime_log` | Regime classification history per symbol |
