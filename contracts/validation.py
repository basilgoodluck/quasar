import json
import time
from web3 import Web3
from config import (
    SEPOLIA_RPC_URL,
    VALIDATION_REGISTRY_ADDRESS,
    AGENT_WALLET_PRIVATE_KEY,
    AGENT_ID,
)

_w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC_URL))

with open("contracts/abi/ValidationRegistry.json") as f:
    _abi = json.load(f)

_registry = _w3.eth.contract(address=Web3.to_checksum_address(VALIDATION_REGISTRY_ADDRESS), abi=_abi)
_account  = _w3.eth.account.from_key(AGENT_WALLET_PRIVATE_KEY)


def _build_checkpoint_hash(
    action: str,
    pair: str,
    amount_usd: float,
    price: float,
    reasoning: str,
    confidence: float,
    intent_hash: str,
) -> bytes:
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
    return _w3.keccak(encoded)


def post_checkpoint(
    action: str,
    pair: str,
    amount_usd: float,
    price: float,
    reasoning: str,
    confidence: float,
    intent_hash: str,
) -> dict:
    checkpoint_hash = _build_checkpoint_hash(action, pair, amount_usd, price, reasoning, confidence, intent_hash)
    signed          = _account.sign_message(_w3.eth.account.sign_hash(checkpoint_hash))
    signature       = signed.signature

    tx = _registry.functions.postCheckpoint(AGENT_ID, checkpoint_hash, signature).build_transaction({
        "from":     _account.address,
        "nonce":    _w3.eth.get_transaction_count(_account.address),
        "gas":      200000,
        "gasPrice": _w3.eth.gas_price,
    })

    signed_tx = _w3.eth.account.sign_transaction(tx, AGENT_WALLET_PRIVATE_KEY)
    tx_hash   = _w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    _w3.eth.wait_for_transaction_receipt(tx_hash)

    return {
        "checkpoint_hash": checkpoint_hash.hex(),
        "tx_hash":         tx_hash.hex(),
    }