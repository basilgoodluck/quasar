import numpy as np
import pandas as pd
from unittest.mock import patch


def _make_ohlcv(n=200):
    np.random.seed(42)
    closes = 60000 + np.cumsum(np.random.randn(n) * 100)
    df = pd.DataFrame({
        "open_time":        np.arange(n) * 900000,
        "open":             closes - 50,
        "high":             closes + 200,
        "low":              closes - 200,
        "close":            closes,
        "volume":           np.random.uniform(100, 500, n),
        "taker_buy_volume": np.random.uniform(50, 250, n),
    })
    return df.astype({
        "open": float, "high": float, "low": float,
        "close": float, "volume": float, "taker_buy_volume": float,
    })


def _make_cvd(n=200):
    deltas = np.random.randn(n) * 10
    return pd.DataFrame({
        "open_time": np.arange(n) * 900000,
        "delta":     deltas,
        "cvd":       np.cumsum(deltas),
    })


@patch("agent.features.get_connection")
def test_compute_features_returns_dataframe(mock_conn):
    from agent.features import _compute_features
    df     = _make_ohlcv()
    cvd_df = _make_cvd()
    result = _compute_features(df, cvd_df, None, None, [])
    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0


@patch("agent.features.get_connection")
def test_feature_columns_present(mock_conn):
    from agent.features import _compute_features
    df     = _make_ohlcv()
    cvd_df = _make_cvd()
    result = _compute_features(df, cvd_df, None, None, [])
    expected = [
        "log_return", "hl_range", "vol_ratio", "buy_ratio",
        "ema_8_dist", "ema_20_dist", "ema_50_dist",
        "realized_vol", "atr_pct", "cvd_norm", "delta_norm",
        "funding", "oi_change", "long_liq_ratio", "short_liq_ratio",
    ]
    for col in expected:
        assert col in result.columns, f"Missing column: {col}"


@patch("agent.features.get_connection")
def test_normalize_zero_mean_unit_std(mock_conn):
    from agent.features import _normalize
    df     = _make_ohlcv()
    cvd_df = _make_cvd()
    from agent.features import _compute_features
    features = _compute_features(df, cvd_df, None, None, [])
    normed   = _normalize(features)
    assert normed.shape[1] == features.shape[1]
    assert normed.dtype == np.float32


@patch("agent.features.get_connection")
def test_build_live_sequence_shape(mock_conn):
    from agent.features import _compute_features, _normalize
    df     = _make_ohlcv(200)
    cvd_df = _make_cvd(200)
    features = _compute_features(df, cvd_df, None, None, [])
    normed   = _normalize(features)
    window   = 96
    seq      = normed[-window:][np.newaxis, :, :].astype(np.float32)
    assert seq.shape == (1, window, features.shape[1])


@patch("agent.features.get_connection")
def test_no_nan_in_normalized_output(mock_conn):
    from agent.features import _compute_features, _normalize
    df     = _make_ohlcv(200)
    cvd_df = _make_cvd(200)
    features = _compute_features(df, cvd_df, None, None, [])
    normed   = _normalize(features)
    assert not np.isnan(normed).any()


@patch("agent.features.get_connection")
def test_liquidation_ratios_sum_to_one(mock_conn):
    from agent.features import _compute_features
    df      = _make_ohlcv(200)
    liq_rows = [("SELL", 10.0), ("BUY", 5.0), ("SELL", 3.0)]
    result  = _compute_features(df, None, None, None, liq_rows)
    last    = result.iloc[-1]
    total   = last["long_liq_ratio"] + last["short_liq_ratio"]
    assert abs(total - 1.0) < 1e-6
