import numpy as np
import pandas as pd
from database.connection import get_connection


def _fetch_ohlcv(symbol, interval, limit):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT open_time, open, high, low, close, volume, taker_buy_volume
                FROM market_data
                WHERE symbol = %s AND interval = %s
                ORDER BY open_time DESC LIMIT %s
            """, (symbol, interval, limit))
            rows = cur.fetchall()
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=["open_time", "open", "high", "low", "close", "volume", "taker_buy_volume"])
    return df.sort_values("open_time").reset_index(drop=True).astype({
        "open": float, "high": float, "low": float,
        "close": float, "volume": float, "taker_buy_volume": float
    })


def _fetch_cvd(symbol, interval, limit):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT open_time, delta, cvd
                FROM cvd_history
                WHERE symbol = %s AND interval = %s
                ORDER BY open_time DESC LIMIT %s
            """, (symbol, interval, limit))
            rows = cur.fetchall()
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=["open_time", "delta", "cvd"])
    return df.sort_values("open_time").reset_index(drop=True).astype({"delta": float, "cvd": float})


def _fetch_funding(symbol, limit):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT funding_time, funding_rate
                FROM funding_rates
                WHERE symbol = %s
                ORDER BY funding_time DESC LIMIT %s
            """, (symbol, limit))
            rows = cur.fetchall()
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=["funding_time", "funding_rate"])
    return df.sort_values("funding_time").reset_index(drop=True).astype({"funding_rate": float})


def _fetch_oi(symbol, period, limit):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT timestamp, open_interest
                FROM oi_history
                WHERE symbol = %s AND period = %s
                ORDER BY timestamp DESC LIMIT %s
            """, (symbol, period, limit))
            rows = cur.fetchall()
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=["timestamp", "open_interest"])
    return df.sort_values("timestamp").reset_index(drop=True).astype({"open_interest": float})


def _fetch_liquidations(symbol, limit):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT side, quantity
                FROM liquidations
                WHERE symbol = %s
                ORDER BY trade_time DESC LIMIT %s
            """, (symbol, limit))
            return cur.fetchall()


def _fetch_real_labels(symbol: str) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT created_at, outcome
                FROM trade_outcomes
                WHERE pair = %s AND status IN ('WIN', 'LOSS', 'NEUTRAL')
            """, (symbol,))
            rows = cur.fetchall()
    mapping = {}
    for created_at, outcome in rows:
        label = 1.0 if outcome == "WIN" else (0.0 if outcome == "LOSS" else 0.5)
        mapping[int(created_at)] = label
    return mapping


def _compute_features(df, cvd_df, funding_df, oi_df, liq_rows):
    features = pd.DataFrame(index=df.index)

    # price action
    features["log_return"] = np.log(df["close"] / df["close"].shift(1))
    features["hl_range"]   = (df["high"] - df["low"]) / df["close"]
    features["vol_ratio"]  = df["volume"] / df["volume"].rolling(20).mean()
    features["buy_ratio"]  = df["taker_buy_volume"] / (df["volume"] + 1e-9)

    # realized volatility
    features["realized_vol"] = features["log_return"].rolling(20).std() * np.sqrt(365 * 24 * 4)

    # CVD and delta
    if cvd_df is not None and len(cvd_df) >= len(df):
        cvd_aligned   = cvd_df["cvd"].values[-len(df):]
        delta_aligned = cvd_df["delta"].values[-len(df):]
        features["cvd_norm"]   = pd.Series(cvd_aligned).pct_change().fillna(0).values
        features["delta_norm"] = pd.Series(delta_aligned) / (df["volume"] + 1e-9)
    else:
        features["cvd_norm"]   = 0.0
        features["delta_norm"] = 0.0

    # funding rate — directionally meaningful: positive = overleveraged long, negative = overleveraged short
    if funding_df is not None and len(funding_df) > 0:
        avg_funding = funding_df["funding_rate"].rolling(8, min_periods=1).mean().iloc[-1]
        features["funding"] = float(np.clip(avg_funding / 0.005, -1.0, 1.0))
    else:
        features["funding"] = 0.0

    # OI change — rising = new participation, falling = unwinding
    if oi_df is not None and len(oi_df) > 4:
        oi_vals   = oi_df["open_interest"].values
        oi_change = (oi_vals[-1] - oi_vals[-5]) / (oi_vals[-5] + 1e-9)
        features["oi_change"] = float(np.clip(oi_change, -1.0, 1.0))
    else:
        features["oi_change"] = 0.0

    # liquidations — long_liq = forced selling (potential bottom), short_liq = forced buying (potential top)
    if liq_rows:
        long_liq  = sum(float(q) for s, q in liq_rows if s == "SELL")
        short_liq = sum(float(q) for s, q in liq_rows if s == "BUY")
        total     = long_liq + short_liq + 1e-9
        features["long_liq_ratio"]  = long_liq / total
        features["short_liq_ratio"] = short_liq / total
    else:
        features["long_liq_ratio"]  = 0.0
        features["short_liq_ratio"] = 0.0

    return features.dropna()


def _normalize(features: pd.DataFrame) -> np.ndarray:
    arr  = features.values.astype(np.float32)
    mean = arr.mean(axis=0)
    std  = arr.std(axis=0) + 1e-9
    return (arr - mean) / std


def build_sequences(symbol, interval="15m", window=96, limit=5000):
    df       = _fetch_ohlcv(symbol, interval, limit)
    cvd_df   = _fetch_cvd(symbol, interval, limit)
    fund_df  = _fetch_funding(symbol, limit=500)
    oi_df    = _fetch_oi(symbol, interval, limit)
    liq_rows = _fetch_liquidations(symbol, limit=200)

    if df is None or len(df) < window + 10:
        return None, None

    features    = _compute_features(df, cvd_df, fund_df, oi_df, liq_rows)
    normed      = _normalize(features)
    real_labels = _fetch_real_labels(symbol)
    closes      = df["close"].values[-len(features):]
    open_times  = df["open_time"].values[-len(features):]

    X, y = [], []
    for i in range(window, len(normed)):
        X.append(normed[i - window:i])
        ts = int(open_times[i])

        if ts in real_labels:
            label = real_labels[ts]
        else:
            fwd_return = (closes[i] - closes[i - 1]) / (closes[i - 1] + 1e-9)
            label      = float(np.clip((fwd_return + 0.05) / 0.1, 0.0, 1.0))

        y.append(label)

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


def build_live_sequence(symbol, interval="15m", window=96):
    df       = _fetch_ohlcv(symbol, interval, window + 60)
    cvd_df   = _fetch_cvd(symbol, interval, window + 60)
    fund_df  = _fetch_funding(symbol, limit=100)
    oi_df    = _fetch_oi(symbol, interval, limit=50)
    liq_rows = _fetch_liquidations(symbol, limit=50)

    if df is None or len(df) < window:
        return None

    features = _compute_features(df, cvd_df, fund_df, oi_df, liq_rows)
    if len(features) < window:
        return None

    normed = _normalize(features)
    return normed[-window:][np.newaxis, :, :].astype(np.float32)