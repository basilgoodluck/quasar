# 🔗 On-Chain Contracts

Quasar posts trade activity on-chain for auditability. Every opened position is signed as an intent and checkpointed. Closes are checkpointed too.

---

### 🧾 What Goes On-Chain

| Event | What's posted | Why |
|-------|--------------|-----|
| Trade open | `submit_trade_intent` + `post_checkpoint` | Proves the decision was made before execution |
| Trade close | `post_checkpoint` (CLOSE) | Audit trail for the exit |
| Skip | ~~`post_skip_checkpoint`~~ | Removed — not worth the gas for throwaway signals |

---

### ✍️ Trade Intent (`submit_trade_intent`)

Called before every order is placed. Signs the intent with:
- `symbol` — e.g. `BTCUSDT`
- `action` — `LONG`, `SHORT`, or `CLOSE`
- `amount` — USD amount (0 for closes)

Returns:
- `approved` — bool. If false, the trade is cancelled entirely.
- `intent_hash` — unique identifier used to link the DB row to the on-chain record
- `reason` — rejection reason if not approved

The `intent_hash` is stored in `trade_outcomes` and used to match the close checkpoint later.

---

### 📌 Checkpoint (`post_checkpoint`)

Posted after a successful order. Records:
- `action` — `LONG`, `SHORT`, or `CLOSE`
- `pair` — symbol
- `amount_usd` — position size
- `price` — execution price
- `reasoning` — full explanation string from the strategy
- `confidence` — regime confidence at entry
- `intent_hash` — links back to the intent

Returns a `checkpoint_hash` stored in `trade_outcomes.checkpoint_hash`.

If the checkpoint call fails, `checkpoint_hash` is set to `FAILED` in the DB — the trade still proceeds, the on-chain record is just missing.

---

### 💰 Vault (`get_available_capital`)

`contracts/vault.py` exposes `get_available_capital()` which returns the USD amount available for trading. Risk sizing in `risk.py` uses this as the base capital figure.
