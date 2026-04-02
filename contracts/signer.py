import time
from eth_account import Account
from config import (
    AGENT_WALLET_PRIVATE_KEY,
    AGENT_WALLET_ADDRESS,
    RISK_ROUTER_ADDRESS,
    AGENT_ID,
    CHAIN_ID,
)

_domain = {
    "name": "AITradingAgent",
    "version": "1",
    "chainId": CHAIN_ID,
    "verifyingContract": RISK_ROUTER_ADDRESS,
}

_types = {
    "EIP712Domain": [
        {"name": "name",             "type": "string"},
        {"name": "version",          "type": "string"},
        {"name": "chainId",          "type": "uint256"},
        {"name": "verifyingContract","type": "address"},
    ],
    "TradeIntent": [
        {"name": "agentId",          "type": "uint256"},
        {"name": "agentWallet",      "type": "address"},
        {"name": "pair",             "type": "string"},
        {"name": "action",           "type": "string"},
        {"name": "amountUsdScaled",  "type": "uint256"},
        {"name": "maxSlippageBps",   "type": "uint256"},
        {"name": "nonce",            "type": "uint256"},
        {"name": "deadline",         "type": "uint256"},
    ],
}


def sign_trade_intent(
    pair: str,
    action: str,
    amount_usd: float,
    nonce: int,
    max_slippage_bps: int = 50,
    deadline_seconds: int = 300,
) -> dict:
    amount_scaled = int(amount_usd * 100)
    deadline      = int(time.time()) + deadline_seconds

    message = {
        "agentId":         AGENT_ID,
        "agentWallet":     AGENT_WALLET_ADDRESS,
        "pair":            pair,
        "action":          action.upper(),
        "amountUsdScaled": amount_scaled,
        "maxSlippageBps":  max_slippage_bps,
        "nonce":           nonce,
        "deadline":        deadline,
    }

    structured_data = {
        "types":       _types,
        "domain":      _domain,
        "primaryType": "TradeIntent",
        "message":     message,
    }

    signed = Account.sign_typed_data(AGENT_WALLET_PRIVATE_KEY, structured_data)

    return {
        "intent":      message,
        "signature":   signed.signature.hex(),
        "intent_hash": signed.messageHash.hex(),
    }