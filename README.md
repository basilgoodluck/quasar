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

---

### Stack

- **Agent** — Python, asyncio
- **Backend** — FastAPI
- **Frontend** — Next.js, TypeScript
- **Exchange** — Kraken Futures (paper + live)
- **Database** — PostgreSQL 15
- **Cache** — Redis 7
- **Infra** — Docker Compose