import os
from dotenv import load_dotenv

load_dotenv()

AGENT_ID                    = int(os.getenv("AGENT_ID", "0"))
AGENT_REGISTRY_ADDRESS      = os.getenv("AGENT_REGISTRY_ADDRESS", "0x97b07dDc405B0c28B17559aFFE63BdB3632d0ca3")
AGENT_WALLET_ADDRESS        = os.getenv("AGENT_WALLET_ADDRESS", "")
AGENT_WALLET_PRIVATE_KEY    = os.getenv("AGENT_WALLET_PRIVATE_KEY", "")

AGENT_REGISTRY_ABI = [
    {
        "name": "register",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "agentWallet",   "type": "address"},
            {"name": "name",          "type": "string"},
            {"name": "description",   "type": "string"},
            {"name": "capabilities",  "type": "string[]"},
            {"name": "agentURI",      "type": "string"}
        ],
        "outputs": [{"name": "agentId", "type": "uint256"}]
    },
    {
        "name": "isRegistered",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "agentId", "type": "uint256"}],
        "outputs": [{"name": "", "type": "bool"}]
    },
    {
        "name": "getAgent",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "agentId", "type": "uint256"}],
        "outputs": [
            {
                "name": "",
                "type": "tuple",
                "components": [
                    {"name": "operatorWallet", "type": "address"},
                    {"name": "agentWallet",    "type": "address"},
                    {"name": "name",           "type": "string"},
                    {"name": "description",    "type": "string"},
                    {"name": "capabilities",   "type": "string[]"},
                    {"name": "registeredAt",   "type": "uint256"},
                    {"name": "active",         "type": "bool"}
                ]
            }
        ]
    },
    {
        "name": "getSigningNonce",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "agentId", "type": "uint256"}],
        "outputs": [{"name": "", "type": "uint256"}]
    },
    {
        "anonymous": False,
        "name": "AgentRegistered",
        "type": "event",
        "inputs": [
            {"indexed": True,  "name": "agentId",        "type": "uint256"},
            {"indexed": True,  "name": "operatorWallet",  "type": "address"},
            {"indexed": True,  "name": "agentWallet",     "type": "address"},
            {"indexed": False, "name": "name",            "type": "string"}
        ]
    }
]

ARC_EMA_FAST                = int(os.getenv("ARC_EMA_FAST", "9"))
ARC_EMA_SLOW                = int(os.getenv("ARC_EMA_SLOW", "21"))
ARC_FISHER_PERIOD           = int(os.getenv("ARC_FISHER_PERIOD", "10"))
ARC_LIMIT_ORDER_EXPIRY      = int(os.getenv("ARC_LIMIT_ORDER_EXPIRY", "5"))

BACKFILL_DAYS               = int(os.getenv("BACKFILL_DAYS", "730"))

CHAIN_ID                    = int(os.getenv("CHAIN_ID", "11155111"))
COLLECT_LOOP_SLEEP          = int(os.getenv("COLLECT_LOOP_SLEEP", "60"))

DISCORD_WEBHOOK_URL         = os.getenv("DISCORD_WEBHOOK_URL", "")

FRONTEND_URL                = os.getenv("FRONTEND_URL", "http://localhost:3000")

GOOGLE_CLIENT_ID            = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET        = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI         = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:4000/auth/google/callback")

HACKATHON_VAULT_ADDRESS     = os.getenv("HACKATHON_VAULT_ADDRESS", "0x0E7CD8ef9743FEcf94f9103033a044caBD45fC90")

HACKATHON_VAULT_ABI = [
    {
        "name": "claimAllocation",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "agentId", "type": "uint256"}],
        "outputs": []
    },
    {
        "name": "getBalance",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "agentId", "type": "uint256"}],
        "outputs": [{"name": "", "type": "uint256"}]
    },
    {
        "name": "hasClaimed",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "agentId", "type": "uint256"}],
        "outputs": [{"name": "", "type": "bool"}]
    },
    {
        "name": "allocationPerTeam",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}]
    }
]

KRAKEN_API_KEY              = os.getenv("KRAKEN_API_KEY", "")
KRAKEN_API_SECRET           = os.getenv("KRAKEN_API_SECRET", "")
KRAKEN_CLI_PATH             = os.getenv("KRAKEN_CLI_PATH", "kraken")
KRAKEN_PAPER_MODE           = os.getenv("KRAKEN_PAPER_MODE", "true").lower() == "true"

MAX_LEVERAGE                = float(os.getenv("MAX_LEVERAGE", "10.0"))
MAX_RISK_PCT                = float(os.getenv("MAX_RISK_PCT", "1.5"))
MAX_RR                      = float(os.getenv("MAX_RR", "4.0"))
MIN_LEVERAGE                = float(os.getenv("MIN_LEVERAGE", "2.0"))
MIN_RISK_PCT                = float(os.getenv("MIN_RISK_PCT", "0.25"))
MIN_RR                      = float(os.getenv("MIN_RR", "1.5"))
MODEL_PATH                  = os.getenv("MODEL_PATH", "models/regime_lstm.pt")

OPENAI_API_KEY              = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL                = os.getenv("OPENAI_MODEL", "gpt-4o")
OPERATOR_WALLET_ADDRESS     = os.getenv("OPERATOR_WALLET_ADDRESS", "")
OPERATOR_PRIVATE_KEY        = os.getenv("OPERATOR_PRIVATE_KEY", "")

OUTCOME_LOOKBACK_CANDLES    = int(os.getenv("OUTCOME_LOOKBACK_CANDLES", "20"))

POSTGRES_DB                 = os.getenv("POSTGRES_DB", "quasar")
POSTGRES_HOST               = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PASSWORD           = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_PORT               = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_USER               = os.getenv("POSTGRES_USER", "postgres")

REGIME_BEAR_THRESHOLD       = float(os.getenv("REGIME_BEAR_THRESHOLD", "0.4"))
REGIME_BULL_THRESHOLD       = float(os.getenv("REGIME_BULL_THRESHOLD", "0.6"))
REPUTATION_CONFIDENCE_BOOST = float(os.getenv("REPUTATION_CONFIDENCE_BOOST", "0.1"))
REPUTATION_MIN_TRADES       = int(os.getenv("REPUTATION_MIN_TRADES", "10"))
REPUTATION_REGISTRY_ADDRESS = "0x423a9904e39537a9997fbaF0f220d79D7d545763"

REPUTATION_REGISTRY_ABI = [
    {
        "name": "submitFeedback",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "agentId",      "type": "uint256"},
            {"name": "score",        "type": "uint8"},
            {"name": "outcomeRef",   "type": "bytes32"},
            {"name": "comment",      "type": "string"},
            {"name": "feedbackType", "type": "uint8"}
        ],
        "outputs": []
    },
    {
        "name": "getAverageScore",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "agentId", "type": "uint256"}],
        "outputs": [{"name": "", "type": "uint256"}]
    }
]

RETRAIN_EVERY_N_TRADES      = int(os.getenv("RETRAIN_EVERY_N_TRADES", "50"))
RISK_ROUTER_ADDRESS         = os.getenv("RISK_ROUTER_ADDRESS", "0xd6A6952545FF6E6E6681c2d15C59f9EB8F40FdBC")

RISK_ROUTER_ABI = [
    {
        "name": "submitTradeIntent",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {
                "name": "intent",
                "type": "tuple",
                "components": [
                    {"name": "agentId",         "type": "uint256"},
                    {"name": "agentWallet",      "type": "address"},
                    {"name": "pair",             "type": "string"},
                    {"name": "action",           "type": "string"},
                    {"name": "amountUsdScaled",  "type": "uint256"},
                    {"name": "maxSlippageBps",   "type": "uint256"},
                    {"name": "nonce",            "type": "uint256"},
                    {"name": "deadline",         "type": "uint256"}
                ]
            },
            {"name": "signature", "type": "bytes"}
        ],
        "outputs": [
            {"name": "approved",   "type": "bool"},
            {"name": "intentHash", "type": "bytes32"}
        ]
    },
    {
        "name": "simulateIntent",
        "type": "function",
        "stateMutability": "view",
        "inputs": [
            {
                "name": "intent",
                "type": "tuple",
                "components": [
                    {"name": "agentId",         "type": "uint256"},
                    {"name": "agentWallet",      "type": "address"},
                    {"name": "pair",             "type": "string"},
                    {"name": "action",           "type": "string"},
                    {"name": "amountUsdScaled",  "type": "uint256"},
                    {"name": "maxSlippageBps",   "type": "uint256"},
                    {"name": "nonce",            "type": "uint256"},
                    {"name": "deadline",         "type": "uint256"}
                ]
            }
        ],
        "outputs": [
            {"name": "valid",  "type": "bool"},
            {"name": "reason", "type": "string"}
        ]
    },
    {
        "name": "getIntentNonce",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "agentId", "type": "uint256"}],
        "outputs": [{"name": "", "type": "uint256"}]
    },
    {
        "anonymous": False,
        "name": "TradeApproved",
        "type": "event",
        "inputs": [
            {"indexed": True,  "name": "agentId",         "type": "uint256"},
            {"indexed": True,  "name": "intentHash",       "type": "bytes32"},
            {"indexed": False, "name": "amountUsdScaled",  "type": "uint256"}
        ]
    },
    {
        "anonymous": False,
        "name": "TradeRejected",
        "type": "event",
        "inputs": [
            {"indexed": True,  "name": "agentId",    "type": "uint256"},
            {"indexed": True,  "name": "intentHash",  "type": "bytes32"},
            {"indexed": False, "name": "reason",      "type": "string"}
        ]
    }
]

SEPOLIA_RPC_URL             = os.getenv("SEPOLIA_RPC_URL", "https://ethereum-sepolia-rpc.publicnode.com")
STRUCTURE_LOOKBACK          = int(os.getenv("STRUCTURE_LOOKBACK", "20"))

TELEGRAM_BOT_TOKEN          = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID            = os.getenv("TELEGRAM_CHAT_ID", "")
TRAIN_INTERVAL              = os.getenv("TRAIN_INTERVAL", "15m")
TRAIN_WINDOW                = int(os.getenv("TRAIN_WINDOW", "96"))

VALIDATION_REGISTRY_ADDRESS = os.getenv("VALIDATION_REGISTRY_ADDRESS", "0x92bF63E5C7Ac6980f237a7164Ab413BE226187F1")

VALIDATION_REGISTRY_ABI = [
    {
        "name": "postEIP712Attestation",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "agentId",        "type": "uint256"},
            {"name": "checkpointHash", "type": "bytes32"},
            {"name": "score",          "type": "uint8"},
            {"name": "notes",          "type": "string"}
        ],
        "outputs": []
    },
    {
        "name": "getAverageValidationScore",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "agentId", "type": "uint256"}],
        "outputs": [{"name": "", "type": "uint256"}]
    }
]