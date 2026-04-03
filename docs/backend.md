## Core API Endpoints

### Auth / Users
- POST   /users                     → create user
- GET    /users/:id                 → get user
- GET    /users/:id/profiles        → linked accounts (discord/telegram)

---

### Social Linking (Discord / Telegram)
- POST   /profiles/link             → link discord/telegram
- GET    /profiles/:user_id         → get all linked profiles
- DELETE /profiles/:id              → unlink account

---

### Agents
- POST   /agents                    → register/save agent (off-chain record)
- GET    /agents/:id                → get agent
- GET    /agents/user/:user_id      → get all user agents

---

### Signals (PRISM)
- POST   /signals                   → store incoming signal
- GET    /signals                   → list signals
- GET    /signals/:symbol           → signals by symbol

---

### Trades
- POST   /trades                    → log new trade (before execution)
- PATCH  /trades/:id/status         → update status (EXECUTED/FAILED)
- GET    /trades/agent/:agent_id    → agent trade history

---

### Positions
- GET    /positions/:agent_id       → current positions
- POST   /positions/update          → update position after trade

---

### Execution
- POST   /execute                   → trigger trade (agent decision → kraken)
- POST   /execute/simulate          → simulate trade (paper mode)

---

### Blockchain (Contracts)
- POST   /contracts/trade-intent    → submit signed trade intent
- GET    /contracts/agent/:id       → fetch on-chain agent data
- GET    /contracts/events          → fetch contract events (optional)

---

### Logs (Discord / Telegram / System)
- POST   /logs                      → store log message
- GET    /logs/:agent_id            → get logs for agent

---

### Health / Debug
- GET    /health                    → check API status
- GET    /metrics                   → basic stats (PnL, trades count)