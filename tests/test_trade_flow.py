import json
import numpy as np
from unittest.mock import patch, MagicMock


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


def _make_trending_seq():
    seq = np.zeros((1, 24, 14), dtype="float32")
    seq[0, :, 0]  = np.linspace(0.002, 0.02,  24)   # log_return strong upslope
    seq[0, :, 1]  = np.linspace(0.01,  0.05,  24)   # hl_range growing
    seq[0, :, 2]  = np.linspace(0.5,   2.0,   24)   # vol_ratio rising
    seq[0, :, 3]  = np.linspace(0.55,  0.85,  24)   # buy_ratio strong
    seq[0, :, 4]  = np.linspace(0.1,   0.4,   24)   # realized_vol moderate
    seq[0, :, 5]  = np.linspace(0.2,   1.0,   24)   # cvd_norm strong upslope
    seq[0, :, 6]  = np.linspace(0.1,   0.8,   24)   # delta_norm
    seq[0, :, 7]  = np.linspace(0.01,  0.1,   24)   # cvd_accel
    seq[0, :, 8]  = np.full(24, 0.001)               # funding neutral
    seq[0, :, 9]  = np.linspace(0.05,  0.5,   24)   # oi_change rising
    seq[0, :, 10] = np.linspace(0.6,   0.9,   24)   # long_liq_ratio one-sided
    seq[0, :, 11] = np.linspace(0.1,   0.4,   24)   # short_liq_ratio low
    seq[0, :, 12] = np.linspace(0.5,   0.9,   24)   # large_trade rising
    seq[0, :, 13] = np.linspace(0.55,  0.85,  24)   # buy_aggression strong
    return seq


@patch("agent.reputation.get_connection")
@patch("agent.features.get_connection")
def test_regime_direction_from_confidence(mock_feat_conn, mock_rep_conn):
    mock_feat_conn.return_value = _mock_db_conn()
    mock_rep_conn.return_value  = _mock_db_conn()

    fake_seq = _make_trending_seq()

    with patch("agent.regime.build_live_sequence", return_value=fake_seq):
        from agent.regime import detect_regime
        result = detect_regime("BTCUSDT", reputation=0.0)

        assert result["ready"]
        assert result["regime"] in {"trending", "trending_volatile"}
        assert result["confidence"] > 0.0


@patch("agent.reputation.get_connection")
@patch("agent.features.get_connection")
def test_neutral_regime_produces_skip(mock_feat_conn, mock_rep_conn, sample_regime):
    mock_feat_conn.return_value = _mock_db_conn()
    mock_rep_conn.return_value  = _mock_db_conn()

    neutral_regime = {**sample_regime, "regime": "ranging", "confidence": 0.5}

    with patch("agent.strategy.arc.detect_regime", return_value=neutral_regime), \
         patch("agent.strategy.arc.get_reputation_score", return_value=0.0), \
         patch("agent.strategy.base.post_skip_checkpoint", return_value={"tx_hash": "0xabc"}):

        from agent.strategy.arc import ARCStrategy
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

    with patch("agent.strategy.arc.detect_regime",        return_value=sample_regime), \
         patch("agent.strategy.arc.get_reputation_score", return_value=0.5), \
         patch("agent.strategy.arc._price_structure",     return_value={"valid": True, "note": "ok", "price": 65000.0, "high": 66000.0, "low": 64000.0, "position": 0.5}), \
         patch("agent.strategy.arc._ma_confirmation",     return_value={"confirmed": True, "note": "above MA", "ma": 64000.0}), \
         patch("agent.strategy.arc._fisher_confirmation", return_value={"confirmed": True, "note": "fisher=-1.6", "fisher": -1.6}), \
         patch("agent.strategy.arc.get_trade_params",     return_value={"action": "LONG", "leverage": 3.0, "risk_pct": 1.0, "rr_ratio": 2.5, "explanation": "Strong momentum"}), \
         patch("agent.strategy.base.submit_trade_intent", return_value={"approved": True, "intent_hash": "0xdeadbeef", "tx_hash": "0xabc"}), \
         patch("contracts.vault.get_available_capital",   return_value=500.0), \
         patch("agent.strategy.base.post_checkpoint",     return_value={"checkpoint_hash": "0xcafe", "tx_hash": "0xdef"}), \
         patch("agent.strategy.base._write_pending_outcome"), \
         patch("subprocess.check_output",                 return_value=json.dumps(mock_order).encode()):

        from agent.strategy.arc import ARCStrategy
        strategy = ARCStrategy()
        decision = strategy.analyze("BTCUSDT")

        assert decision["action"] == "LONG"
        assert decision["ready"] is True
        assert "reputation" in decision

        result = strategy.open_position(decision, price=65000.0, reputation=0.5)

        assert result["executed"] is True
        assert "intent_hash" in result


@patch("agent.reputation.get_connection")
@patch("agent.features.get_connection")
def test_rejected_trade_intent_does_not_execute(mock_feat_conn, mock_rep_conn, sample_decision):
    mock_feat_conn.return_value = _mock_db_conn()
    mock_rep_conn.return_value  = _mock_db_conn()

    with patch("agent.strategy.base.submit_trade_intent", return_value={"approved": False, "reason": "Exceeds maxPositionSize"}), \
         patch("contracts.vault.get_available_capital",   return_value=500.0):

        from agent.strategy.arc import ARCStrategy
        strategy = ARCStrategy()
        result   = strategy.open_position(sample_decision, price=65000.0, reputation=0.5)

        assert result["executed"] is False
        assert "reason" in result


@patch("agent.reputation.get_connection")
@patch("agent.features.get_connection")
def test_reputation_adjusts_regime_thresholds(mock_feat_conn, mock_rep_conn):
    mock_feat_conn.return_value = _mock_db_conn()
    mock_rep_conn.return_value  = _mock_db_conn()

    fake_seq = _make_trending_seq()

    from agent.regime import detect_regime

    with patch("agent.regime.build_live_sequence", return_value=fake_seq):
        result_low_rep  = detect_regime("BTCUSDT", reputation=0.0)

    with patch("agent.regime.build_live_sequence", return_value=fake_seq):
        result_high_rep = detect_regime("BTCUSDT", reputation=1.0)

    assert result_low_rep["ready"]  is True
    assert result_high_rep["ready"] is True
    assert result_low_rep["regime"]  in {"trending", "trending_volatile", "volatile", "ranging"}
    assert result_high_rep["regime"] in {"trending", "trending_volatile", "volatile", "ranging"}
    assert result_high_rep["confidence"] >= result_low_rep["confidence"] - 0.1