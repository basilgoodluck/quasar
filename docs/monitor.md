# 👁 Monitor

The monitor runs as a background loop alongside the agent. It watches all `PENDING` trades and closes them when an exit condition is met.

---

### 🔁 Loop

Polls every **30 seconds**. On each tick:

1. Fetches all rows from `trade_outcomes` where `status = 'PENDING'`
2. For each trade, fetches the current price from Binance
3. Checks exit conditions
4. If a condition is met → calls `close_position()` on the strategy

---

### 🚪 Exit Conditions

Checked in this order:

| Condition | LONG | SHORT |
|-----------|------|-------|
| **Timeout** | Trade open ≥ 1 hour | Same |
| **Stop Loss** | `current_price ≤ sl_price` | `current_price ≥ sl_price` |
| **Take Profit** | `current_price ≥ tp_price` | `current_price ≤ tp_price` |

Timeout is always checked first regardless of direction.

---

### 📐 SL / TP Calculation

Set at open time in `base.py` using a fixed 2% stop loss (`SL_PCT`):

```
# LONG
sl_price = entry × (1 − 0.02)
tp_price = entry × (1 + 0.02 × rr_ratio)

# SHORT
sl_price = entry × (1 + 0.02)
tp_price = entry × (1 − 0.02 × rr_ratio)
```

With a minimum RR of 1.5, take profit is always at least 3% away from entry.

---

### 📦 On Close

When an exit condition triggers:

1. A sell/buy order is placed on Kraken to close the position
2. A `CLOSE` intent is signed on-chain
3. A close checkpoint is posted on-chain
4. The DB row is updated:
   - `exit_price` — actual close price
   - `status` — `WIN` or `LOSS`
   - `resolved_at` — unix timestamp
   - `outcome_tx_hash` — on-chain checkpoint hash

**WIN/LOSS logic:**
```
LONG  → WIN if exit_price > entry_price
SHORT → WIN if exit_price < entry_price
```

---

### ⚠️ Symbol Conversion

The DB stores pairs in Kraken's `PF_` format (e.g. `PF_XBTUSD`). The monitor converts these back to Binance format (e.g. `BTCUSDT`) to fetch the current price, then uses the `PF_` format when placing the close order on Kraken.
