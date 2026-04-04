import os
from dotenv import load_dotenv

load_dotenv()

POSTGRES_HOST     = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT     = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB       = os.getenv("POSTGRES_DB", "quasar")
POSTGRES_USER     = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

SECRET_KEY           = os.getenv("SECRET_KEY", "changeme")
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI  = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:4000/auth/google/callback")
FRONTEND_URL         = os.getenv("FRONTEND_URL", "http://localhost:3000")

DISCORD_WEBHOOK_URL  = os.getenv("DISCORD_WEBHOOK_URL", "")
TELEGRAM_BOT_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID     = os.getenv("TELEGRAM_CHAT_ID", "")

KRAKEN_CLI_PATH  = os.getenv("KRAKEN_CLI_PATH", "kraken")
KRAKEN_PAPER_MODE = os.getenv("KRAKEN_PAPER_MODE", "true").lower() == "true"

AGENT_WALLET_ADDRESS     = os.getenv("AGENT_WALLET_ADDRESS", "")
AGENT_ID                 = os.getenv("AGENT_ID", "0")
AGENT_REGISTRY_ADDRESS   = os.getenv("AGENT_REGISTRY_ADDRESS", "")
CHAIN_ID                 = os.getenv("CHAIN_ID", "11155111")
