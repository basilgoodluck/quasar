import json
from web3 import Web3
from contracts.signer import sign_trade_intent
from config import (
    SEPOLIA_RPC_URL,
    RISK_ROUTER_ADDRESS,
    RISK_ROUTER_ABI,
    AGENT_WALLET_PRIVATE_KEY,
    AGENT_ID,
)

_w3      = Web3(Web3.HTTPProvider(SEPOLIA_RPC_URL))
_router  = None
_account = None


def _get_router():
    global _router, _account
    if _router is None:
        _router  = _w3.eth.contract(address=Web3.to_checksum_address(RISK_ROUTER_ADDRESS), abi=RISK_ROUTER_ABI)
        _account = _w3.eth.account.from_key(AGENT_WALLET_PRIVATE_KEY)
    return _router, _account


def get_nonce() -> int:
    router, _ = _get_router()
    return router.functions.getIntentNonce(AGENT_ID).call()


def submit_trade_intent(pair: str, action: str, amount_usd: float) -> dict:
    router, account = _get_router()
    nonce  = get_nonce()
    signed = sign_trade_intent(pair, action, amount_usd, nonce)

    intent    = signed["intent"]
    signature = bytes.fromhex(signed["signature"].replace("0x", ""))

    intent_tuple = (
        intent["agentId"],
        Web3.to_checksum_address(intent["agentWallet"]),
        intent["pair"],
        intent["action"],
        intent["amountUsdScaled"],
        intent["maxSlippageBps"],
        intent["nonce"],
        intent["deadline"],
    )

    tx = router.functions.submitTradeIntent(intent_tuple, signature).build_transaction({
        "from":     account.address,
        "nonce":    _w3.eth.get_transaction_count(account.address),
        "gasPrice": _w3.eth.gas_price,
    })

    signed_tx = _w3.eth.account.sign_transaction(tx, AGENT_WALLET_PRIVATE_KEY)
    tx_hash   = _w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt   = _w3.eth.wait_for_transaction_receipt(tx_hash)

    approved    = False
    intent_hash = None

    for log in receipt.logs:
        try:
            event       = router.events.TradeApproved().process_log(log)
            approved    = True
            intent_hash = event["args"]["intentHash"].hex()
            break
        except Exception:
            pass

    if not approved:
        for log in receipt.logs:
            try:
                event = router.events.TradeRejected().process_log(log)
                return {
                    "approved": False,
                    "reason":   event["args"]["reason"],
                    "tx_hash":  tx_hash.hex(),
                }
            except Exception:
                pass

    return {
        "approved":      approved,
        "intent_hash":   intent_hash,
        "tx_hash":       tx_hash.hex(),
        "signed_intent": signed,
    }