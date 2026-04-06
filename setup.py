from web3 import Web3
from config import (
    SEPOLIA_RPC_URL,
    AGENT_ID,
    VALIDATION_REGISTRY_ABI,
    VALIDATION_REGISTRY_ADDRESS,
)

w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC_URL))


# ─── Step 1: Register agent ───────────────────────────────────────────────────
# Run once. Save the agentId printed to your .env as AGENT_ID, then comment this out.

# registry = w3.eth.contract(
#     address=Web3.to_checksum_address(AGENT_REGISTRY_ADDRESS),
#     abi=AGENT_REGISTRY_ABI
# )

# tx = registry.functions.register(
#     Web3.to_checksum_address(AGENT_WALLET_ADDRESS),
#     "Quasar",
#     "Quasar is a trustless AI trading agent that executes verifiable, risk-controlled strategies, generates explainable insights for every decision, and continuously learns to refine its future actions.",
#     ["trading", "ai-agent", "defi", "automation", "quant", "onchain", "risk-management", "eip712-signing", "erc-8004"],
#     "https://gist.githubusercontent.com/basilgoodluck/2375fa1b3e1597cb83c1bb3909d4b36a/raw/96abaae02464abd3d45538379e3ce4bd140c0279/quasar-agent.json"
# ).build_transaction({
#     "from": OPERATOR_WALLET_ADDRESS,
#     "nonce": w3.eth.get_transaction_count(OPERATOR_WALLET_ADDRESS),
#     "gasPrice": w3.eth.gas_price,
# })

# signed = w3.eth.account.sign_transaction(tx, private_key=OPERATOR_PRIVATE_KEY)
# tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
# receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

# print("tx hash:", tx_hash.hex())
# print("status:", receipt.status)

# if receipt.status == 0:
#     print("Transaction reverted")
# else:
#     agent_id = registry.events.AgentRegistered().process_receipt(receipt)[0]["args"]["agentId"]
#     print("agentId:", agent_id)
#     print("Save this as AGENT_ID in your .env")


# ─── Step 2: Claim allocation ─────────────────────────────────────────────────
# Run after saving AGENT_ID to .env

# vault = w3.eth.contract(
#     address=Web3.to_checksum_address(HACKATHON_VAULT_ADDRESS),
#     abi=HACKATHON_VAULT_ABI
# )

# tx = vault.functions.claimAllocation(AGENT_ID).build_transaction({
#     "from": OPERATOR_WALLET_ADDRESS,
#     "nonce": w3.eth.get_transaction_count(OPERATOR_WALLET_ADDRESS),
#     "gasPrice": w3.eth.gas_price,
# })

# signed = w3.eth.account.sign_transaction(tx, private_key=OPERATOR_PRIVATE_KEY)
# tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
# receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

# print("tx hash:", tx_hash.hex())
# print("status:", receipt.status)

# if receipt.status == 1:
#     balance = vault.functions.getBalance(AGENT_ID).call()
#     print("allocated balance:", w3.from_wei(balance, "ether"), "ETH")
# else:
#     print("Transaction reverted")


# ─── Step 3: Verify agent registration ────────────────────────────────────────
# Optional sanity check after step 1

# registry = w3.eth.contract(
#     address=Web3.to_checksum_address(AGENT_REGISTRY_ADDRESS),
#     abi=AGENT_REGISTRY_ABI
# )

# is_registered = registry.functions.isRegistered(AGENT_ID).call()
# agent = registry.functions.getAgent(AGENT_ID).call()

# print("isRegistered:", is_registered)
# print("name:", agent[2])
# print("operatorWallet:", agent[0])
# print("agentWallet:", agent[1])
# print("active:", agent[6])


# ─── Step 4: Verify vault balance ─────────────────────────────────────────────
# Optional sanity check after step 2

# vault = w3.eth.contract(
#     address=Web3.to_checksum_address(HACKATHON_VAULT_ADDRESS),
#     abi=HACKATHON_VAULT_ABI
# )

# has_claimed = vault.functions.hasClaimed(AGENT_ID).call()
# balance = vault.functions.getBalance(AGENT_ID).call()

# print("hasClaimed:", has_claimed)
# print("balance:", w3.from_wei(balance, "ether"), "ETH")


# ─── Step 5: Verify RiskRouter nonce ──────────────────────────────────────────
# Confirms your agent is known to the RiskRouter before submitting trade intents

# router = w3.eth.contract(
#     address=Web3.to_checksum_address(RISK_ROUTER_ADDRESS),
#     abi=RISK_ROUTER_ABI
# )

# nonce = router.functions.getIntentNonce(AGENT_ID).call()
# print("current intent nonce:", nonce)


# ─── Step 6: Verify ValidationRegistry ───────────────────────────────────────
# Confirms your agent has a score slot in the ValidationRegistry

validation = w3.eth.contract(
    address=Web3.to_checksum_address(VALIDATION_REGISTRY_ADDRESS),
    abi=VALIDATION_REGISTRY_ABI
)

score = validation.functions.getAverageValidationScore(AGENT_ID).call()
print("average validation score:", score)