import pytest
import json
from unittest.mock import patch, MagicMock, call


def _mock_db_conn():
    mock_conn = MagicMock()
    mock_cur  = MagicMock()
    mock_cur.fetchall.return_value = []
    mock_cur.fetchone.return_value = (500.0,)
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__  = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
    mock_conn.cursor.return_value.__exit__  = MagicMock(return_value=False)
    return mock_conn


@patch("agent.reputation.get_connection")
@patch("agent.features.get_connection")
def test_regime_direction_from_confidence(mock_feat_conn, mock_rep_conn):
    mock_feat_conn.return_value = _mock_db_conn()
    mock_rep_conn.return_value  = _mock_db_conn()

    import torch
    from unittest.mock import patch as p

    fake_seq = torch.zeros((1, 96, 15))

    with p("agent.regime.build_live_sequence", return_value=fake_seq.numpy()), \
         p("agent.regime.load_model") as mock_model_loader:

        mock_model        = MagicMock()
        mock_model.return_value = torch.tensor([0.75])
        mock_model_loader.return_value = mock_model

        from agent.regime import detect_regime
        result = detect_regime("BTCUSDT", reputation=0.0)

        assert result["ready"]
        assert result["direction"] == "long"
        assert result["confidence"] == 0.75


@patch("agent.reputation.get_connection")
@patch("agent.features.get_connection")
def test_neutral_regime_produces_skip(mock_feat_conn, mock_rep_conn, sample_regime):
    mock_feat_conn.return_value = _mock_db_conn()
    mock_rep_conn.return_value  = _mock_db_conn()

    neutral_regime = {**sample_regime, "direction": "neutral", "confidence": 0.5}

    with patch("agent.arc.detect_regime", return_value=neutral_regime), \
         patch("agent.arc.get_reputation_score", return_value=0.0), \
         patch("contracts.validation.post_skip_checkpoint", return_value={"tx_hash": "0xabc"}):

        from agent.arc import ARCStrategy
        strategy = ARCStrategy()
        result   = strategy.analyze("BTCUSDT")

        assert result["action"] == "SKIP"
        assert result["ready"] is False


@patch("agent.reputation.get_connection")
@patch("agent.features.get_connection")
def test_full_flow_approved_trade(mock_feat_conn, mock_rep_conn, sample_regime, sample_decision):
    mock_feat_conn.return_value = _mock_db_conn()
    mock_rep_conn.return_value  = _mock_db_conn()

    mock_order = {"txid": ["OTXID-TEST123"], "descr": {"order": "buy 0.001 BTCUSDT @ market"}}

    with patch("agent.arc.detect_regime",       return_value=sample_regime), \
         patch("agent.arc.get_reputation_score", return_value=0.5), \
         patch("agent.arc._price_structure",     return_value={"valid": True, "note": "ok", "price": 65000.0, "high": 66000.0, "low": 64000.0, "position": 0.5}), \
         patch("agent.arc._ma_confirmation",     return_value={"confirmed": True, "note": "above MA", "ma": 64000.0}), \
         patch("agent.arc._fisher_confirmation", return_value={"confirmed": True, "note": "fisher=-1.6", "fisher": -1.6}), \
         patch("agent.openai.get_trade_params",  return_value={"action": "LONG", "leverage": 3.0, "risk_pct": 1.0, "rr_ratio": 2.5, "explanation": "Strong momentum"}), \
         patch("contracts.router.submit_trade_intent", return_value={"approved": True, "intent_hash": "0xdeadbeef", "tx_hash": "0xabc"}), \
         patch("contracts.vault.get_available_capital", return_value=500.0), \
         patch("contracts.validation.post_checkpoint",  return_value={"checkpoint_hash": "0xcafe", "tx_hash": "0xdef"}), \
         patch("agent.base._write_pending_outcome"), \
         patch("subprocess.check_output",        return_value=json.dumps(mock_order).encode()):

        from agent.arc import ARCStrategy
        strategy = ARCStrategy()
        decision = strategy.analyze("BTCUSDT")

        assert decision["action"] == "LONG"
        assert decision["ready"] is True
        assert "reputation" in decision

        from agent.base import BaseStrategy
        result = strategy.open_position(decision, price=65000.0, reputation=0.5)

        assert result["executed"] is True
        assert "intent_hash" in result


@patch("agent.reputation.get_connection")
@patch("agent.features.get_connection")
def test_rejected_trade_intent_does_not_execute(mock_feat_conn, mock_rep_conn, sample_decision):
    mock_feat_conn.return_value = _mock_db_conn()
    mock_rep_conn.return_value  = _mock_db_conn()

    with patch("contracts.router.submit_trade_intent", return_value={"approved": False, "reason": "Exceeds maxPositionSize"}), \
         patch("contracts.vault.get_available_capital", return_value=500.0):

        from agent.arc import ARCStrategy
        strategy = ARCStrategy()
        result   = strategy.open_position(sample_decision, price=65000.0, reputation=0.5)

        assert result["executed"] is False
        assert "reason" in result


@patch("agent.reputation.get_connection")
@patch("agent.features.get_connection")
def test_reputation_adjusts_regime_thresholds(mock_feat_conn, mock_rep_conn):
    mock_feat_conn.return_value = _mock_db_conn()
    mock_rep_conn.return_value  = _mock_db_conn()

    import torch
    import numpy as np

    fake_seq = np.zeros((1, 96, 15), dtype="float32")

    with patch("agent.regime.build_live_sequence", return_value=fake_seq), \
         patch("agent.regime.load_model") as mock_loader:

        mock_model        = MagicMock()
        mock_model.return_value = torch.tensor([0.58])
        mock_loader.return_value = mock_model

        from agent.regime import detect_regime

        result_low_rep  = detect_regime("BTCUSDT", reputation=0.0)
        result_high_rep = detect_regime("BTCUSDT", reputation=1.0)

        assert result_low_rep["direction"]  == "neutral"
        assert result_high_rep["direction"] == "long"
