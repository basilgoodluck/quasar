# 📐 Strategy — ARC

ARC (Adaptive Regime Classification) is the core trading strategy. It only trades when the market regime is clearly directional, confirms with two indicators, checks price structure, and then asks an AI for a second opinion before placing any order.

---

### 🧠 Regime Detection

The first gate. Every symbol analysis starts here. The regime classifier outputs one of four states:

| Regime | Meaning |
|--------|---------|
| `trending` | Clear directional move, low noise |
| `trending_volatile` | Directional but with high volatility |
| `volatile` | Chaotic, no trend anchor — **not tradeable** |
| `ranging` | Sideways, no edge — **not tradeable** |

Along with the regime, it outputs:
- `confidence` — how strongly the model believes the classification (0–1)
- `trend_direction` — `bullish` or `bearish`
- `direction_strength` — signed float, magnitude of the directional move
- `p_trending`, `p_ranging`, `p_volatile` — raw class probabilities

Only `trending` and `trending_volatile` pass through to the next stage.

---

### 📊 Indicators

Two indicators must agree before an entry is considered.

#### EMA20 (Typical Price)
Calculated on `(high + low + close) / 3` with a 20-period EMA.

- **LONG** requires price above EMA
- **SHORT** requires price below EMA

#### Fisher Transform
Normalises price into a Gaussian distribution to identify extremes.

- Period set by `ARC_FISHER_PERIOD` in config
- Reversal signals checked over `REVERSAL_LOOKBACK` (100 candles)

| Signal | Condition |
|--------|-----------|
| Oversold reversal | Fisher < -1.5 AND at/near 100-candle low |
| Overbought reversal | Fisher > +1.5 AND at/near 100-candle high |
| Trend long | Fisher < 0 |
| Trend short | Fisher > 0 |

---

### 🚦 Entry Logic

Two entry types, checked in order:

**Reversal** (checked first — stronger signal)
- `LONG` → Fisher oversold reversal + price below EMA
- `SHORT` → Fisher overbought reversal + price above EMA

**Trend following** (regime must agree)
- `LONG` → regime bullish + price above EMA + Fisher trend long
- `SHORT` → regime bearish + price below EMA + Fisher trend short

If neither condition is met → SKIP.

---

### 🏗 Price Structure

After an entry direction is confirmed, price must be in a sensible position within its recent swing range (lookback set by `STRUCTURE_LOOKBACK`).

| Direction | Requirement |
|-----------|-------------|
| LONG | Price in the lower 60% of the swing range |
| SHORT | Price in the upper 60% of the swing range (above 40%) |

This prevents buying at the top or selling at the bottom of a move.

---

### 🤖 AI Review

Final gate before execution. All rule-based checks have passed at this point. The AI (OpenAI) receives the full context — regime, indicators, structure, risk params, reputation — and returns:

- `approve` — bool
- `confidence_adjustment` — float added to signal strength
- `reason` — plain text explanation

A veto here skips the trade silently (no on-chain write, no gas cost). If the AI is unavailable, it defaults to `approve=True` with `adjustment=0.0` so the system keeps running.
