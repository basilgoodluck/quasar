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


def _send_attestation_tx(func_call, pair: str, tx_type: str):
    """Helper to send transaction with detailed revert logging"""
    try:
        tx = func_call.build_transaction({
            "from":     _account.address,
            "nonce":    _w3.eth.get_transaction_count(_account.address),
            "gas":      500000,
            "gasPrice": _w3.eth.gas_price,
        })

        signed_tx = _w3.eth.account.sign_transaction(tx, AGENT_WALLET_PRIVATE_KEY)
        tx_hash   = _w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt   = _w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

        return {
            "tx_hash": tx_hash.hex(),
            "status":  receipt.status,
        }

    except Exception as e:
        error_msg = str(e)
        print(f"[{pair}] {tx_type} failed: {error_msg}")

        # Try to extract revert reason
        if "execution reverted" in error_msg.lower():
            try:
                if hasattr(e, 'args') and len(e.args) > 1:
                    revert_data = e.args[1]
                    print(f"[{pair}] Revert data: {revert_data}")

                if "0x" in error_msg:
                    print(f"[{pair}] Raw revert: {error_msg.split('0x')[-1]}")
            except Exception:
                pass

        # Static call to get better error
        try:
            func_call.call({"from": _account.address})
        except Exception as static_e:
            print(f"[{pair}] Static call failed with: {static_e}")

        raise


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
            bytes.fromhex(intent_hash.replace("0x", "")) if intent_hash.startswith("0x") else bytes.fromhex(intent_hash),
            int(time.time()),
        ],
    )
    checkpoint_hash = _w3.keccak(encoded)

    tx_info = _send_attestation_tx(
        registry.functions.postEIP712Attestation(
            AGENT_ID,
            checkpoint_hash,
            int(confidence * 100),
            reasoning
        ),
        pair=pair,
        tx_type="post_checkpoint"
    )

    return {
        "checkpoint_hash": checkpoint_hash.hex(),
        "tx_hash":         tx_info.get("tx_hash"),
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

    tx_info = _send_attestation_tx(
        registry.functions.postEIP712Attestation(
            AGENT_ID,
            checkpoint_hash,
            int(confidence * 100),
            reason
        ),
        pair=pair,
        tx_type="post_skip_checkpoint"
    )

    return {
        "checkpoint_hash": checkpoint_hash.hex(),
        "tx_hash":         tx_info.get("tx_hash"),
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
            bytes.fromhex(original_intent_hash.replace("0x", "")) if original_intent_hash.startswith("0x") else bytes.fromhex(original_intent_hash),
            int(pnl_pct * 10000),
            int(time.time()),
        ],
    )
    checkpoint_hash = _w3.keccak(encoded)

    tx_info = _send_attestation_tx(
        registry.functions.postEIP712Attestation(
            AGENT_ID,
            checkpoint_hash,
            int(confidence_at_entry * 100),
            f"Outcome: {outcome}, PnL: {round(pnl_pct * 100, 4)}%"
        ),
        pair=pair,
        tx_type="post_outcome_checkpoint"
    )

    return {
        "checkpoint_hash":      checkpoint_hash.hex(),
        "tx_hash":              tx_info.get("tx_hash"),
        "type":                 "OUTCOME",
        "outcome":              outcome,
        "pnl_pct":              round(pnl_pct * 100, 4),
        "original_intent_hash": original_intent_hash,
        "confidence_at_entry":  confidence_at_entry,
    }