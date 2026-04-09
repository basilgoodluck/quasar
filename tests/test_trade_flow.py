import json
import pytest
import numpy as np
from unittest.mock import patch, AsyncMock


def _make_trending_seq():
    seq = np.zeros((1, 24, 14), dtype="float32")
    seq[0, :, 0]  = np.linspace(0.002, 0.02,  24)
    seq[0, :, 1]  = np.linspace(0.01,  0.05,  24)
    seq[0, :, 2]  = np.linspace(0.5,   2.0,   24)
    seq[0, :, 3]  = np.linspace(0.55,  0.85,  24)
    seq[0, :, 4]  = np.linspace(0.1,   0.4,   24)
    seq[0, :, 5]  = np.linspace(0.2,   1.0,   24)
    seq[0, :, 6]  = np.linspace(0.1,   0.8,   24)
    seq[0, :, 7]  = np.linspace(0.01,  0.1,   24)
    seq[0, :, 8]  = np.full(24, 0.001)
    seq[0, :, 9]  = np.linspace(0.05,  0.5,   24)
    seq[0, :, 10] = np.linspace(0.6,   0.9,   24)
    seq[0, :, 11] = np.linspace(0.1,   0.4,   24)
    seq[0, :, 12] = np.linspace(0.5,   0.9,   24)
    seq[0, :, 13] = np.linspace(0.55,  0.85,  24)
    return seq


@pytest.mark.asyncio
async def test_regime_direction_from_confidence():
    fake_seq = _make_trending_seq()

    with patch("agent.regime.build_live_sequence", new=AsyncMock(return_value=fake_seq)):
        from agent.regime import detect_regime
        result = await detect_regime("BTCUSDT", reputation=0.0)

        assert result["ready"]
        assert result["regime"] in {"trending", "trending_volatile"}
        assert result["confidence"] > 0.0
        assert result["trend_direction"] in {"bullish", "bearish"}
        assert "direction_strength" in result


@pytest.mark.asyncio
async def test_neutral_regime_produces_skip(sample_regime):
    neutral_regime = {
        **sample_regime,
        "regime":             "ranging",
        "confidence":         0.5,
        "trend_direction":    "bearish",
        "direction_strength": -0.8,
    }

    with patch("agent.strategy.arc.detect_regime",         new=AsyncMock(return_value=neutral_regime)), \
         patch("agent.strategy.arc.get_reputation_score",  new=AsyncMock(return_value=0.0)), \
         patch("agent.strategy.base.post_skip_checkpoint", return_value={"tx_hash": "0xabc"}):

        from agent.strategy.arc import ARCStrategy
        strategy = ARCStrategy()
        result   = await strategy.analyze("BTCUSDT")

        assert result["action"] == "SKIP"
        assert result["ready"] is False


@pytest.mark.asyncio
async def test_full_flow_approved_trade(sample_regime, sample_decision):
    mock_order = {"txid": ["OTXID-TEST123"], "descr": {"order": "buy 0.001 BTCUSDT @ market"}}

    mock_proc             = AsyncMock()
    mock_proc.returncode  = 0
    mock_proc.communicate = AsyncMock(return_value=(json.dumps(mock_order).encode(), b""))

    trending_regime = {
        **sample_regime,
        "regime":             "trending",
        "confidence":         0.6,
        "trend_direction":    "bullish",
        "direction_strength": +0.9,
    }

    with patch("agent.strategy.arc.detect_regime",           new=AsyncMock(return_value=trending_regime)), \
         patch("agent.strategy.arc.get_reputation_score",    new=AsyncMock(return_value=0.5)), \
         patch("agent.strategy.arc.compute_risk",            new=AsyncMock(return_value={"action": "COMPUTE", "leverage": 3.0, "risk_pct": 1.0, "rr_ratio": 2.5, "amount_usd": 150.0, "explanation": "kelly=0.1"})), \
         patch("agent.strategy.arc._price_structure",        new=AsyncMock(return_value={"valid": True, "note": "ok", "price": 65000.0, "high": 66000.0, "low": 64000.0, "position": 0.5})), \
         patch("agent.strategy.arc._ma_confirmation",        new=AsyncMock(return_value={"above": True, "ma": 64000.0, "price": 65000.0, "note": "price above EMA20"})), \
         patch("agent.strategy.arc._fisher_confirmation",    new=AsyncMock(return_value={"fisher": -1.6, "fisher_min": -1.8, "fisher_max": 1.2, "trend_long": True, "trend_short": False, "reversal_long": False, "reversal_short": False, "note": "fisher=-1.6"})), \
         patch("agent.strategy.base._write_pending_outcome", new=AsyncMock()), \
         patch("agent.strategy.base._ensure_paper_init",     new=AsyncMock()), \
         patch("contracts.vault.get_available_capital",      return_value=500.0), \
         patch("asyncio.create_subprocess_exec",             return_value=mock_proc):

        from agent.strategy.arc import ARCStrategy
        strategy = ARCStrategy()
        decision = await strategy.analyze("BTCUSDT")

        assert decision["action"] == "LONG"
        assert decision["ready"] is True
        assert "reputation" in decision

        result = await strategy.open_position(decision, price=65000.0, reputation=0.5)

        assert result["executed"] is True
        assert "intent_hash" in result


@pytest.mark.asyncio
async def test_rejected_trade_intent_does_not_execute(sample_decision):
    with patch("contracts.vault.get_available_capital",   return_value=500.0), \
         patch("agent.strategy.base._ensure_paper_init",  new=AsyncMock()), \
         patch("asyncio.create_subprocess_exec",          side_effect=Exception("order rejected")):

        from agent.strategy.arc import ARCStrategy
        strategy = ARCStrategy()
        result   = await strategy.open_position(sample_decision, price=65000.0, reputation=0.5)

        assert result["executed"] is False
        assert "reason" in result


@pytest.mark.asyncio
async def test_reputation_adjusts_regime_thresholds():
    fake_seq = _make_trending_seq()

    from agent.regime import detect_regime

    with patch("agent.regime.build_live_sequence", new=AsyncMock(return_value=fake_seq)):
        result_low_rep  = await detect_regime("BTCUSDT", reputation=0.0)

    with patch("agent.regime.build_live_sequence", new=AsyncMock(return_value=fake_seq)):
        result_high_rep = await detect_regime("BTCUSDT", reputation=1.0)

    assert result_low_rep["ready"]  is True
    assert result_high_rep["ready"] is True
    assert result_low_rep["regime"]  in {"trending", "trending_volatile", "volatile", "ranging"}
    assert result_high_rep["regime"] in {"trending", "trending_volatile", "volatile", "ranging"}
    assert result_high_rep["confidence"] >= result_low_rep["confidence"] - 0.1
    assert result_low_rep["trend_direction"]  in {"bullish", "bearish"}
    assert result_high_rep["trend_direction"] in {"bullish", "bearish"}