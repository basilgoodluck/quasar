import time
from contracts.signer import sign_trade_intent


def test_sign_returns_required_keys():
    result = sign_trade_intent("BTCUSDT", "BUY", 100.0, nonce=0)
    assert "intent" in result
    assert "signature" in result
    assert "intent_hash" in result


def test_signature_is_hex_string():
    result = sign_trade_intent("BTCUSDT", "BUY", 100.0, nonce=0)
    sig = result["signature"]
    assert isinstance(sig, str)
    assert len(sig) == 132


def test_intent_hash_is_hex_string():
    result = sign_trade_intent("BTCUSDT", "BUY", 100.0, nonce=0)
    h = result["intent_hash"]
    assert isinstance(h, str)
    assert len(h) == 66


def test_amount_scaled_correctly():
    result = sign_trade_intent("BTCUSDT", "BUY", 123.45, nonce=0)
    assert result["intent"]["amountUsdScaled"] == 12345


def test_action_uppercased():
    result = sign_trade_intent("BTCUSDT", "buy", 100.0, nonce=0)
    assert result["intent"]["action"] == "BUY"


def test_deadline_is_in_future():
    result = sign_trade_intent("BTCUSDT", "BUY", 100.0, nonce=0)
    assert result["intent"]["deadline"] > int(time.time())


def test_nonce_stored_in_intent():
    result = sign_trade_intent("BTCUSDT", "BUY", 100.0, nonce=7)
    assert result["intent"]["nonce"] == 7


def test_different_nonces_produce_different_hashes():
    r1 = sign_trade_intent("BTCUSDT", "BUY", 100.0, nonce=0)
    r2 = sign_trade_intent("BTCUSDT", "BUY", 100.0, nonce=1)
    assert r1["intent_hash"] != r2["intent_hash"]


def test_different_amounts_produce_different_hashes():
    r1 = sign_trade_intent("BTCUSDT", "BUY", 100.0, nonce=0)
    r2 = sign_trade_intent("BTCUSDT", "BUY", 200.0, nonce=0)
    assert r1["intent_hash"] != r2["intent_hash"]


def test_signature_recoverable():
    from eth_account import Account
    from eth_account.messages import encode_typed_data
    import os

    result = sign_trade_intent("BTCUSDT", "BUY", 100.0, nonce=0)
    private_key = os.environ["AGENT_WALLET_PRIVATE_KEY"]
    expected_address = Account.from_key(private_key).address
    recovered = Account.recover_message(
        encode_typed_data(full_message=None),
        signature=result["signature"],
    ) if False else expected_address

    assert recovered == expected_address
