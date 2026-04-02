import json
from web3 import Web3
from contracts.signer import sign_trade_intent
from config import (
    SEPOLIA_RPC_URL,
    RISK_ROUTER_ADDRESS,
    AGENT_WALLET_PRIVATE_KEY,
    AGENT_ID,
)

_w3     = Web3(Web3.HTTPProvider(SEPOLIA_RPC_URL))

with open("contracts/abi/RiskRouter.json") as f:
    _abi = json.load(f)

_router  = _w3.eth.contract(address=Web3.to_checksum_address(RISK_ROUTER_ADDRESS), abi=_abi)
_account = _w3.eth.account.from_key(AGENT_WALLET_PRIVATE_KEY)


def get_nonce() -> int:
    return _router.functions.getNonce(AGENT_ID).call()


def submit_trade_intent(pair: str, action: str, amount_usd: float) -> dict:
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

    tx = _router.functions.submitTradeIntent(intent_tuple, signature).build_transaction({
        "from":     _account.address,
        "nonce":    _w3.eth.get_transaction_count(_account.address),
        "gas":      300000,
        "gasPrice": _w3.eth.gas_price,
    })

    signed_tx = _w3.eth.account.sign_transaction(tx, AGENT_WALLET_PRIVATE_KEY)
    tx_hash   = _w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt   = _w3.eth.wait_for_transaction_receipt(tx_hash)

    approved    = False
    intent_hash = None

    for log in receipt.logs:
        try:
            event       = _router.events.TradeApproved().process_log(log)
            approved    = True
            intent_hash = event["args"]["intentHash"].hex()
            break
        except Exception:
            pass

    if not approved:
        for log in receipt.logs:
            try:
                event = _router.events.TradeRejected().process_log(log)
                return {
                    "approved": False,
                    "reason":   event["args"]["reason"],
                    "tx_hash":  tx_hash.hex(),
                }
            except Exception:
                pass

    return {
        "approved":     approved,
        "intent_hash":  intent_hash,
        "tx_hash":      tx_hash.hex(),
        "signed_intent": signed,
    }