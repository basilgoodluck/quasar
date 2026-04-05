from web3 import Web3
import json

w3 = Web3(Web3.HTTPProvider("https://ethereum-sepolia-rpc.publicnode.com"))

with open("contracts/abi/AgentRegistry.json") as f:
    abi = json.load(f)

registry = w3.eth.contract(
    address="0x97b07dDc405B0c28B17559aFFE63BdB3632d0ca3",
    abi=abi
)

operator_wallet = "YOUR_NEW_ADDRESS"
operator_private_key = "YOUR_PRIVATE_KEY"
agent_wallet = "YOUR_NEW_ADDRESS"

tx = registry.functions.register(
    agent_wallet,
    "My Agent",
    "A trustless trading agent",
    ["trading", "eip712-signing"],
    "https://my-agent-metadata.json"
).build_transaction({
    "from": operator_wallet,
    "nonce": w3.eth.get_transaction_count(operator_wallet),
    "gas": 300000,
    "gasPrice": w3.eth.gas_price,
})

signed = w3.eth.account.sign_transaction(tx, private_key=operator_private_key)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

agent_id = registry.events.AgentRegistered().process_receipt(receipt)[0]["args"]["agentId"]
print("agentId:", agent_id)