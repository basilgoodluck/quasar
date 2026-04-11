import time
from web3 import Web3
from config import (
    SEPOLIA_RPC_URL,
    VALIDATION_REGISTRY_ADDRESS,
    VALIDATION_REGISTRY_ABI,
    AGENT_WALLET_PRIVATE_KEY,
    AGENT_ID,
)

_w3       = Web3(Web3.HTTPProvider(SEPOLIA_RPC_URL))
_registry = None
_account  = None


def _get_registry():
    global _registry, _account
    if _registry is None:
        _registry = _w3.eth.contract(address=Web3.to_checksum_address(VALIDATION_REGISTRY_ADDRESS), abi=VALIDATION_REGISTRY_ABI)
        _account  = _w3.eth.account.from_key(AGENT_WALLET_PRIVATE_KEY)
    return _registry, _account


def post_checkpoint(
    action: str,
    pair: str,
    amount_usd: float,
    price: float,
    reasoning: str,
    confidence: float,
    intent_hash: str,
) -> dict:
    registry, account = _get_registry()

    reasoning_hash = _w3.keccak(text=reasoning)
    encoded = _w3.codec.encode(
        ["uint256", "string", "string", "uint256", "uint256", "bytes32", "uint256", "bytes32", "uint256"],
        [
            AGENT_ID,
            action,
            pair,
            int(amount_usd * 100),
            int(price * 100),
            reasoning_hash,
            int(confidence * 1000),
            bytes.fromhex(intent_hash.replace("0x", "")),
            int(time.time()),
        ],
    )
    checkpoint_hash = _w3.keccak(encoded)

    tx = registry.functions.postAttestation(
        AGENT_ID,
        checkpoint_hash,
        int(confidence * 100),
        1,          # ProofType.EIP712
        b"",        # empty proof bytes
        reasoning
    ).build_transaction({
        "from":     account.address,
        "nonce":    _w3.eth.get_transaction_count(account.address),
        "gasPrice": _w3.eth.gas_price,
    })

    signed_tx = _w3.eth.account.sign_transaction(tx, AGENT_WALLET_PRIVATE_KEY)
    tx_hash   = _w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    _w3.eth.wait_for_transaction_receipt(tx_hash)

    return {
        "checkpoint_hash": checkpoint_hash.hex(),
        "tx_hash":         tx_hash.hex(),
        "type":            "TRADE",
    }


def post_skip_checkpoint(
    pair: str,
    reason: str,
    confidence: float,
) -> dict:
    registry, account = _get_registry()

    reasoning_hash = _w3.keccak(text=reason)
    encoded = _w3.codec.encode(
        ["uint256", "string", "string", "bytes32", "uint256", "uint256"],
        [
            AGENT_ID,
            "SKIP",
            pair,
            reasoning_hash,
            int(confidence * 1000),
            int(time.time()),
        ],
    )
    checkpoint_hash = _w3.keccak(encoded)

    tx = registry.functions.postAttestation(
        AGENT_ID,
        checkpoint_hash,
        int(confidence * 100),
        1,          # ProofType.EIP712
        b"",        # empty proof bytes
        reason
    ).build_transaction({
        "from":     account.address,
        "nonce":    _w3.eth.get_transaction_count(account.address),
        "gasPrice": _w3.eth.gas_price,
    })

    signed_tx = _w3.eth.account.sign_transaction(tx, AGENT_WALLET_PRIVATE_KEY)
    tx_hash   = _w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    _w3.eth.wait_for_transaction_receipt(tx_hash)

    return {
        "checkpoint_hash": checkpoint_hash.hex(),
        "tx_hash":         tx_hash.hex(),
        "type":            "SKIP",
        "reason":          reason,
    }


def post_outcome_checkpoint(
    pair: str,
    action: str,
    outcome: str,
    original_intent_hash: str,
    entry_price: float,
    exit_price: float,
    confidence_at_entry: float,
) -> dict:
    registry, account = _get_registry()

    pnl_pct = ((exit_price - entry_price) / entry_price) if action == "LONG" else ((entry_price - exit_price) / entry_price)

    encoded = _w3.codec.encode(
        ["uint256", "string", "string", "string", "bytes32", "int256", "uint256"],
        [
            AGENT_ID,
            "OUTCOME",
            pair,
            outcome,
            bytes.fromhex(original_intent_hash.replace("0x", "")),
            int(pnl_pct * 10000),
            int(time.time()),
        ],
    )
    checkpoint_hash = _w3.keccak(encoded)

    tx = registry.functions.postAttestation(
        AGENT_ID,
        checkpoint_hash,
        int(confidence_at_entry * 100),
        1,          # ProofType.EIP712
        b"",        # empty proof bytes
        f"Outcome: {outcome}, PnL: {round(pnl_pct * 100, 4)}%"
    ).build_transaction({
        "from":     account.address,
        "nonce":    _w3.eth.get_transaction_count(account.address),
        "gasPrice": _w3.eth.gas_price,
    })

    signed_tx = _w3.eth.account.sign_transaction(tx, AGENT_WALLET_PRIVATE_KEY)
    tx_hash   = _w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    _w3.eth.wait_for_transaction_receipt(tx_hash)

    return {
        "checkpoint_hash":      checkpoint_hash.hex(),
        "tx_hash":              tx_hash.hex(),
        "type":                 "OUTCOME",
        "outcome":              outcome,
        "pnl_pct":              round(pnl_pct * 100, 4),
        "original_intent_hash": original_intent_hash,
        "confidence_at_entry":  confidence_at_entry,
    }