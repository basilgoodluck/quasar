# Quasar

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=flat-square&logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-15-black?style=flat-square&logo=next.js)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square&logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)
![Exchange](https://img.shields.io/badge/Exchange-Kraken_Futures-5741d9?style=flat-square)
![Mode](https://img.shields.io/badge/Mode-Paper_%2F_Live-orange?style=flat-square)

> A fully automated crypto futures trading system. Quasar detects market regimes, sizes risk dynamically, gets an AI second opinion, places trades on Kraken Futures, and monitors them to close — all without human intervention.

---

### How it works

Quasar runs a continuous loop across 19 crypto pairs. For each symbol it classifies the current market regime using a trained model — if the market is ranging or purely chaotic, it skips. If a directional regime is detected, it checks two indicators (EMA and Fisher Transform) and validates that price is in a sensible position within its recent swing range. If everything lines up, it asks OpenAI for a second opinion. A veto kills the trade silently. Approval triggers a signed on-chain intent, an order on Kraken Futures, and a checkpoint posted to the chain. A separate monitor process then watches the open position every 30 seconds and closes it when the stop loss, take profit, or 1-hour timeout is hit.

---

### Quick start

```bash
# clone
git clone https://github.com/basilgoodluck/quasar.git
cd quasar

# set environment variables
cp .env.example .env
# edit .env with your keys

# start everything
docker compose up -d

# verify all containers are running
docker ps

# follow the agent
docker logs -f quasar-agent
```

To run in paper trading mode (no real money), set `KRAKEN_PAPER_MODE=true` in your `.env`. The paper account is initialised automatically with a $10,000 balance. Switch to `false` for live trading.

---

### Project structure

```
quasar/
├── agent/
│   ├── main.py               # trading loop — iterates symbols, calls strategy
│   ├── monitor.py            # watches open positions, triggers closes
│   ├── features.py           # OHLCV fetching
│   ├── regime.py             # regime detection
│   ├── reputation.py         # reputation score
│   ├── ai_advisor.py         # OpenAI trade review
│   ├── collector.py          # candle collection loop
│   ├── train.py              # regime model training
│   └── strategy/
│       ├── base.py           # BaseStrategy — open/close/exec
│       ├── arc.py            # ARC strategy — indicators + entry logic
│       └── risk.py           # Kelly sizing, drawdown, leverage
├── contracts/
│   ├── router.py             # trade intent signing
│   ├── validation.py         # checkpoint posting
│   └── vault.py              # available capital
├── database/
│   └── connection.py         # asyncpg pool
├── frontend/                 # Next.js dashboard
├── main.py                   # FastAPI backend
├── docker-compose.yml
└── docs/
    ├── architecture.md
    ├── strategy.md
    ├── risk.md
    ├── database.md
    ├── contracts.md
    ├── monitor.md
    ├── api.md
    └── deployment.md
```

---

### Stack

- **Agent** — Python, asyncio
- **Backend** — FastAPI
- **Frontend** — Next.js, TypeScript
- **Exchange** — Kraken Futures (paper + live)
- **Database** — PostgreSQL 15
- **Cache** — Redis 7
- **Infra** — Docker Compose

---

### Documentation

| Doc | What it covers |
|-----|---------------|
| [Architecture](docs/architecture.md) | How all services connect and data flows |
| [Strategy](docs/strategy.md) | ARC strategy — regime, Fisher, MA, structure |
| [Risk](docs/risk.md) | Kelly sizing, drawdown, leverage, concurrency |
| [Database](docs/database.md) | Schema, fields, what gets stored and when |
| [Contracts](docs/contracts.md) | On-chain intent signing and checkpoints |
| [Monitor](docs/monitor.md) | How open positions are watched and closed |
| [API](docs/api.md) | Backend endpoints and response shapes |
| [Deployment](docs/deployment.md) | Docker setup, env vars, running the system |