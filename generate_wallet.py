from eth_account import Account

acct = Account.create()

print("address:", acct.address)
print("private_key:", acct.key.hex())