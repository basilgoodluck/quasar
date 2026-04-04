import json
from web3 import Web3
from config import (
    SEPOLIA_RPC_URL,
    HACKATHON_VAULT_ADDRESS,
    AGENT_ID,
)

_w3    = Web3(Web3.HTTPProvider(SEPOLIA_RPC_URL))
_vault = None


def _get_vault():
    global _vault
    if _vault is None:
        with open("contracts/abi/HackathonVault.json") as f:
            _abi = json.load(f)
        _vault = _w3.eth.contract(address=Web3.to_checksum_address(HACKATHON_VAULT_ADDRESS), abi=_abi)
    return _vault


def get_allocated_capital() -> float:
    return _get_vault().functions.getAllocatedCapital(AGENT_ID).call() / 100


def get_used_capital() -> float:
    return _get_vault().functions.getUsedCapital(AGENT_ID).call() / 100


def get_available_capital() -> float:
    return get_allocated_capital() - get_used_capital()