import os
import pytest
import asyncio

os.environ.setdefault("SEPOLIA_RPC_URL", "http://localhost:8545")
os.environ.setdefault("CHAIN_ID", "11155111")
os.environ.setdefault("AGENT_ID", "0")
os.environ.setdefault("AGENT_WALLET_ADDRESS", "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266")
os.environ.setdefault("AGENT_WALLET_PRIVATE_KEY", "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80")
os.environ.setdefault("RISK_ROUTER_ADDRESS", "0x0000000000000000000000000000000000000001")
os.environ.setdefault("HACKATHON_VAULT_ADDRESS", "0x0000000000000000000000000000000000000002")
os.environ.setdefault("VALIDATION_REGISTRY_ADDRESS", "0x0000000000000000000000000000000000000003")
os.environ.setdefault("AGENT_REGISTRY_ADDRESS", "0x0000000000000000000000000000000000000004")
os.environ.setdefault("REPUTATION_REGISTRY_ADDRESS", "0x0000000000000000000000000000000000000005")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("KRAKEN_API_KEY", "test-key")
os.environ.setdefault("KRAKEN_API_SECRET", "test-secret")
os.environ.setdefault("KRAKEN_PAPER_MODE", "true")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_USER", "quasar")
os.environ.setdefault("POSTGRES_PASSWORD", "quasar")
os.environ.setdefault("POSTGRES_DB", "quasar_test")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_market_data():
    return {
        "pair":   "BTCUSDT",
        "price":  65000.0,
        "high":   66000.0,
        "low":    64000.0,
        "volume": 1200.0,
        "vwap":   65100.0,
        "bid":    64990.0,
        "ask":    65010.0,
    }


@pytest.fixture
def sample_regime():
    return {
        "symbol":     "BTCUSDT",
        "p_trending": 0.72,
        "p_ranging":  0.15,
        "p_volatile": 0.13,
        "regime":     "trending",
        "confidence": 0.72,
        "ready":      True,
    }


@pytest.fixture
def sample_decision():
    return {
        "symbol":      "BTCUSDT",
        "action":      "LONG",
        "leverage":    3.0,
        "risk_pct":    1.0,
        "rr_ratio":    2.5,
        "explanation": "Upward momentum confirmed by MA and Fisher.",
        "regime": {
            "confidence": 0.72,
            "direction":  "long",
        },
        "reputation": 0.6,
        "ready":       True,
    }