# ⚖️ Risk Management

Quasar sizes every trade dynamically based on market regime, confidence, win rate history, reputation, and current drawdown. No fixed position sizes.

---

### 📏 Constants

| Parameter | Value | Meaning |
|-----------|-------|---------|
| `MAX_DRAWDOWN` | 5% | Drawdown limit before cooldown kicks in |
| `DRAWDOWN_COOLDOWN_SECS` | 3600s | 1 hour cooldown after hitting drawdown limit |
| `MAX_CONCURRENT` | 3 | Max open positions at top reputation |
| `BASE_CONCURRENT` | 1 | Max open positions at low reputation |
| `MAX_TRADE_USD` | $1,000 | Hard cap per trade |
| `MIN_RISK_PCT` | 0.5% | Floor on risk per trade |
| `MAX_RISK_PCT` | 2% | Ceiling on risk per trade |
| `MIN_LEVERAGE` | 2x | Minimum leverage |
| `MAX_LEVERAGE` | 5x | Maximum leverage |
| `MIN_RR` | 1.5 | Minimum reward:risk ratio |
| `MAX_RR` | 3.0 | Maximum reward:risk ratio |
| `SL_PCT` | 2% | Stop loss distance from entry |

---

### 🎲 Kelly Sizing

Position size starts with a fractional Kelly formula:

```
kelly = (win_rate × rr − (1 − win_rate)) / rr
risk  = kelly × 0.25  (quarter Kelly — conservative)
```

Until 10 trades have resolved, win rate defaults to `0.45`.

---

### 📈 Regime Scaling

Leverage and RR ratio are scaled by regime and confidence:

| Regime | Base Leverage | Base RR |
|--------|--------------|---------|
| `trending` | 3x | 2.0 |
| `trending_volatile` | 4x | 2.5 |
| `volatile` | 2x | 1.5 |

Both are then multiplied by `confidence` and clamped to their min/max bounds.

---

### 🏆 Reputation Scaling

Reputation (0–1) scales how much of the Kelly fraction is actually used:

```
rep_scale  = 0.2 + (0.8 × reputation)
raw_risk   = kelly × confidence × rep_scale
```

Low reputation → small positions. High reputation → closer to full Kelly.

---

### 👥 Concurrent Position Limits

| Reputation | Win Rate | Max Open |
|------------|----------|----------|
| ≥ 0.7 | ≥ 0.6 | 3 |
| ≥ 0.4 | ≥ 0.5 | 2 |
| below | below | 1 |

---

### 🛑 Drawdown Cooldown

When total losses / available capital hits 5%, a 1-hour cooldown starts. The system skips all trades during this window. After the hour, it resumes — it does not hard-stop permanently. The cooldown resets on process restart.

---

### 💰 Final Amount

```
amount_usd = min(capital × risk_pct × leverage, $1,000)
```

Capital comes from the on-chain vault via `get_available_capital()`.
