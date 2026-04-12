# 🚀 Deployment

Quasar runs entirely in Docker Compose. One command starts everything.

---

### ⚙️ Requirements

- Docker + Docker Compose
- A Kraken Futures account (paper or live)
- Kraken CLI installed and authenticated
- OpenAI API key (for AI trade review)

---

### 🏃 Running

```bash
# start everything
docker compose up -d

# check all containers are healthy
docker ps

# tail agent logs
docker logs -f quasar-agent

# tail monitor logs
docker logs -f quasar-monitor
```

---

### 🗂 Services Overview

| Container | Image | What it does |
|-----------|-------|-------------|
| `quasar-postgres` | `postgres:15` | Database — starts first, health checked |
| `quasar-redis` | `redis:7-alpine` | Cache |
| `quasar-collector` | `noblebasil/quasar-collector` | Fetches OHLCV candles |
| `quasar-trainer` | `noblebasil/quasar-trainer` | Retrains regime model |
| `quasar-agent` | `noblebasil/quasar-agent` | Main trading loop |
| `quasar-backend` | `noblebasil/quasar-backend` | API + WebSocket, port `7052` |
| `quasar-outcome-tracker` | `noblebasil/quasar-outcome-tracker` | Outcome tracking |

---

### 🔑 Environment Variables

| Variable | Used by | Description |
|----------|---------|-------------|
| `KRAKEN_CLI_PATH` | agent, monitor | Path to the Kraken CLI binary |
| `KRAKEN_PAPER_MODE` | agent, monitor | `true` for paper trading, `false` for live |
| `OPENAI_API_KEY` | agent | AI trade review |
| `DATABASE_URL` | all | PostgreSQL connection string |
| `REDIS_URL` | backend | Redis connection string |
| `TRAIN_INTERVAL` | agent, collector | Candle interval for price fetching |
| `COLLECT_LOOP_SLEEP` | agent | Seconds between symbol scan cycles |
| `STRUCTURE_LOOKBACK` | agent | Candles to look back for price structure |
| `ARC_FISHER_PERIOD` | agent | Period for Fisher Transform calculation |

---

### 🗃 Database

PostgreSQL is exposed on port `5432`. To inspect directly:

```bash
docker exec quasar-postgres psql -U postgres -d quasar -c "SELECT * FROM trade_outcomes ORDER BY created_at DESC LIMIT 10;"
```

---

### 📄 Paper vs Live

Set `KRAKEN_PAPER_MODE=true` to run in paper trading mode. The agent will call `kraken futures paper` commands instead of live order commands. Paper accounts are initialised automatically with a $10,000 balance if not already set up.
