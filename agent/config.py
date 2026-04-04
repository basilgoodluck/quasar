import os
from dotenv import load_dotenv

load_dotenv()

SEPOLIA_RPC_URL             = os.getenv("SEPOLIA_RPC_URL", "")
CHAIN_ID                    = int(os.getenv("CHAIN_ID", "11155111"))

AGENT_ID                    = int(os.getenv("AGENT_ID", "0"))
AGENT_WALLET_ADDRESS        = os.getenv("AGENT_WALLET_ADDRESS", "")
AGENT_WALLET_PRIVATE_KEY    = os.getenv("AGENT_WALLET_PRIVATE_KEY", "")

AGENT_REGISTRY_ADDRESS      = os.getenv("AGENT_REGISTRY_ADDRESS", "")
RISK_ROUTER_ADDRESS         = os.getenv("RISK_ROUTER_ADDRESS", "")
HACKATHON_VAULT_ADDRESS     = os.getenv("HACKATHON_VAULT_ADDRESS", "")
VALIDATION_REGISTRY_ADDRESS = os.getenv("VALIDATION_REGISTRY_ADDRESS", "")

KRAKEN_API_KEY              = os.getenv("KRAKEN_API_KEY", "")
KRAKEN_API_SECRET           = os.getenv("KRAKEN_API_SECRET", "")
KRAKEN_PAPER_MODE           = os.getenv("KRAKEN_PAPER_MODE", "true").lower() == "true"
KRAKEN_CLI_PATH             = os.getenv("KRAKEN_CLI_PATH", "kraken")

OPENAI_API_KEY              = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL                = os.getenv("OPENAI_MODEL", "gpt-4o")

MODEL_PATH                  = os.getenv("MODEL_PATH", "models/regime_lstm.pt")
TRAIN_INTERVAL              = os.getenv("TRAIN_INTERVAL", "15m")
TRAIN_WINDOW                = int(os.getenv("TRAIN_WINDOW", "96"))

MAX_LEVERAGE                = float(os.getenv("MAX_LEVERAGE", "10.0"))
MIN_LEVERAGE                = float(os.getenv("MIN_LEVERAGE", "2.0"))
MAX_RISK_PCT                = float(os.getenv("MAX_RISK_PCT", "1.5"))
MIN_RISK_PCT                = float(os.getenv("MIN_RISK_PCT", "0.25"))
MIN_RR                      = float(os.getenv("MIN_RR", "1.5"))
MAX_RR                      = float(os.getenv("MAX_RR", "4.0"))

REGIME_BULL_THRESHOLD       = float(os.getenv("REGIME_BULL_THRESHOLD", "0.6"))
REGIME_BEAR_THRESHOLD       = float(os.getenv("REGIME_BEAR_THRESHOLD", "0.4"))

ARC_EMA_FAST                = int(os.getenv("ARC_EMA_FAST", "9"))
ARC_EMA_SLOW                = int(os.getenv("ARC_EMA_SLOW", "21"))
ARC_FISHER_PERIOD           = int(os.getenv("ARC_FISHER_PERIOD", "10"))
ARC_LIMIT_ORDER_EXPIRY      = int(os.getenv("ARC_LIMIT_ORDER_EXPIRY", "5"))

COLLECT_LOOP_SLEEP          = int(os.getenv("COLLECT_LOOP_SLEEP", "60"))
BACKFILL_DAYS               = int(os.getenv("BACKFILL_DAYS", "730"))
STRUCTURE_LOOKBACK          = int(os.getenv("STRUCTURE_LOOKBACK", "20"))

OUTCOME_LOOKBACK_CANDLES    = int(os.getenv("OUTCOME_LOOKBACK_CANDLES", "20"))
RETRAIN_EVERY_N_TRADES      = int(os.getenv("RETRAIN_EVERY_N_TRADES", "50"))
REPUTATION_MIN_TRADES       = int(os.getenv("REPUTATION_MIN_TRADES", "10"))
REPUTATION_CONFIDENCE_BOOST = float(os.getenv("REPUTATION_CONFIDENCE_BOOST", "0.1"))

POSTGRES_USER               = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD           = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB                 = os.getenv("POSTGRES_DB", "quasar")
POSTGRES_HOST               = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT               = int(os.getenv("POSTGRES_PORT", "5432"))