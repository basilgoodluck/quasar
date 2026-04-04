import os
from dotenv import load_dotenv

load_dotenv()

# Agent
AGENT_ID                    = int(os.getenv("AGENT_ID", "0"))
AGENT_REGISTRY_ADDRESS      = os.getenv("AGENT_REGISTRY_ADDRESS", "")
AGENT_WALLET_ADDRESS        = os.getenv("AGENT_WALLET_ADDRESS", "")
AGENT_WALLET_PRIVATE_KEY    = os.getenv("AGENT_WALLET_PRIVATE_KEY", "")

# ARC settings
ARC_EMA_FAST                = int(os.getenv("ARC_EMA_FAST", "9"))
ARC_EMA_SLOW                = int(os.getenv("ARC_EMA_SLOW", "21"))
ARC_FISHER_PERIOD           = int(os.getenv("ARC_FISHER_PERIOD", "10"))
ARC_LIMIT_ORDER_EXPIRY      = int(os.getenv("ARC_LIMIT_ORDER_EXPIRY", "5"))

# Backtesting & data
BACKFILL_DAYS               = int(os.getenv("BACKFILL_DAYS", "730"))
COLLECT_LOOP_SLEEP          = int(os.getenv("COLLECT_LOOP_SLEEP", "60"))
STRUCTURE_LOOKBACK          = int(os.getenv("STRUCTURE_LOOKBACK", "20"))
OUTCOME_LOOKBACK_CANDLES    = int(os.getenv("OUTCOME_LOOKBACK_CANDLES", "20"))

# Discord / Telegram
DISCORD_WEBHOOK_URL         = os.getenv("DISCORD_WEBHOOK_URL", "")
TELEGRAM_BOT_TOKEN          = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID            = os.getenv("TELEGRAM_CHAT_ID", "")

# Frontend
FRONTEND_URL                = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Kraken
KRAKEN_API_KEY              = os.getenv("KRAKEN_API_KEY", "")
KRAKEN_API_SECRET           = os.getenv("KRAKEN_API_SECRET", "")
KRAKEN_CLI_PATH             = os.getenv("KRAKEN_CLI_PATH", "kraken")
KRAKEN_PAPER_MODE           = os.getenv("KRAKEN_PAPER_MODE", "true").lower() == "true"

# Hackathon & vault
HACKATHON_VAULT_ADDRESS     = os.getenv("HACKATHON_VAULT_ADDRESS", "")
RISK_ROUTER_ADDRESS         = os.getenv("RISK_ROUTER_ADDRESS", "")
VALIDATION_REGISTRY_ADDRESS = os.getenv("VALIDATION_REGISTRY_ADDRESS", "")

# Leverage & risk
MAX_LEVERAGE                = float(os.getenv("MAX_LEVERAGE", "10.0"))
MIN_LEVERAGE                = float(os.getenv("MIN_LEVERAGE", "2.0"))
MAX_RISK_PCT                = float(os.getenv("MAX_RISK_PCT", "1.5"))
MIN_RISK_PCT                = float(os.getenv("MIN_RISK_PCT", "0.25"))
MAX_RR                      = float(os.getenv("MAX_RR", "4.0"))
MIN_RR                      = float(os.getenv("MIN_RR", "1.5"))

# Models & training
MODEL_PATH                  = os.getenv("MODEL_PATH", "models/regime_lstm.pt")
TRAIN_INTERVAL              = os.getenv("TRAIN_INTERVAL", "15m")
TRAIN_WINDOW                = int(os.getenv("TRAIN_WINDOW", "96"))

# OpenAI
OPENAI_API_KEY              = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL                = os.getenv("OPENAI_MODEL", "gpt-4o")

# Postgres
POSTGRES_DB                 = os.getenv("POSTGRES_DB", "quasar")
POSTGRES_HOST               = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PASSWORD           = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_PORT               = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_USER               = os.getenv("POSTGRES_USER", "postgres")

# Regime thresholds
REGIME_BEAR_THRESHOLD       = float(os.getenv("REGIME_BEAR_THRESHOLD", "0.4"))
REGIME_BULL_THRESHOLD       = float(os.getenv("REGIME_BULL_THRESHOLD", "0.6"))

# Reputation
REPUTATION_CONFIDENCE_BOOST = float(os.getenv("REPUTATION_CONFIDENCE_BOOST", "0.1"))
REPUTATION_MIN_TRADES       = int(os.getenv("REPUTATION_MIN_TRADES", "10"))
RETRAIN_EVERY_N_TRADES      = int(os.getenv("RETRAIN_EVERY_N_TRADES", "50"))

# Secret key
SECRET_KEY                  = os.getenv("SECRET_KEY", "changeme")

# Google OAuth
GOOGLE_CLIENT_ID            = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET        = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI         = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:4000/auth/google/callback")