import os
import numpy as np
import pandas as pd
from database.connection import get_connection

INTERVAL  = "5m"
WINDOW    = 24
MODEL_DIR = "/app/models"


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


def _fetch_liquidations_timeseries(symbol, limit):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT side, quantity, trade_time
                FROM liquidations
                WHERE symbol = %s
                ORDER BY trade_time DESC LIMIT %s
            """, (symbol, limit))
            rows = cur.fetchall()
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=["side", "quantity", "trade_time"])
    df["quantity"]   = df["quantity"].astype(float)
    df["trade_time"] = df["trade_time"].astype(int)
    return df.sort_values("trade_time").reset_index(drop=True)


def _fetch_agg_trades_timeseries(symbol, limit):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT price, quantity, is_buyer_mm, trade_time
                FROM agg_trades
                WHERE symbol = %s
                ORDER BY trade_time DESC LIMIT %s
            """, (symbol, limit))
            rows = cur.fetchall()
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=["price", "quantity", "is_buyer_mm", "trade_time"])
    df["price"]      = df["price"].astype(float)
    df["quantity"]   = df["quantity"].astype(float)
    df["trade_time"] = df["trade_time"].astype(int)
    return df.sort_values("trade_time").reset_index(drop=True)


def _fetch_real_labels(symbol: str) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT created_at, status
                FROM trade_outcomes
                WHERE pair = %s AND status IN ('WIN', 'LOSS', 'NEUTRAL')
            """, (symbol,))
            rows = cur.fetchall()
    mapping = {}
    for created_at, status in rows:
        label = 0 if status == "WIN" else (1 if status == "LOSS" else 2)
        mapping[int(created_at)] = label
    return mapping


def _align_funding_to_candles(df, funding_df):
    if funding_df is None or len(funding_df) == 0:
        return np.zeros(len(df), dtype=np.float32)
    funding_times = funding_df["funding_time"].values
    funding_rates = funding_df["funding_rate"].values
    result = np.zeros(len(df), dtype=np.float32)
    for i, ot in enumerate(df["open_time"].values):
        idx = np.searchsorted(funding_times, ot, side="right") - 1
        if idx >= 0:
            result[i] = float(np.clip(funding_rates[idx] / 0.005, -1.0, 1.0))
    return result


def _align_oi_to_candles(df, oi_df):
    if oi_df is None or len(oi_df) < 5:
        return np.zeros(len(df), dtype=np.float32)
    oi_times  = oi_df["timestamp"].values
    oi_values = oi_df["open_interest"].values
    result    = np.zeros(len(df), dtype=np.float32)
    for i, ot in enumerate(df["open_time"].values):
        idx = np.searchsorted(oi_times, ot, side="right") - 1
        if idx >= 4:
            change   = (oi_values[idx] - oi_values[idx - 4]) / (oi_values[idx - 4] + 1e-9)
            result[i] = float(np.clip(change, -1.0, 1.0))
    return result


def _align_liquidations_to_candles(df, liq_df, candle_ms=300000):
    long_liq_arr  = np.zeros(len(df), dtype=np.float32)
    short_liq_arr = np.zeros(len(df), dtype=np.float32)
    if liq_df is None or len(liq_df) == 0:
        return long_liq_arr, short_liq_arr
    for i, ot in enumerate(df["open_time"].values):
        mask        = (liq_df["trade_time"] >= ot) & (liq_df["trade_time"] < ot + candle_ms)
        candle_liqs = liq_df[mask]
        if len(candle_liqs) == 0:
            continue
        long_liq  = candle_liqs[candle_liqs["side"] == "SELL"]["quantity"].sum()
        short_liq = candle_liqs[candle_liqs["side"] == "BUY"]["quantity"].sum()
        total     = long_liq + short_liq + 1e-9
        long_liq_arr[i]  = long_liq / total
        short_liq_arr[i] = short_liq / total
    return long_liq_arr, short_liq_arr


def _align_agg_trades_to_candles(df, agg_df, candle_ms=300000):
    large_trade_ratio_arr = np.zeros(len(df), dtype=np.float32)
    buy_aggression_arr    = np.zeros(len(df), dtype=np.float32)
    if agg_df is None or len(agg_df) == 0:
        return large_trade_ratio_arr, buy_aggression_arr
    for i, ot in enumerate(df["open_time"].values):
        mask          = (agg_df["trade_time"] >= ot) & (agg_df["trade_time"] < ot + candle_ms)
        candle_trades = agg_df[mask]
        if len(candle_trades) == 0:
            continue
        large_threshold          = candle_trades["quantity"].quantile(0.80)
        total_vol                = candle_trades["quantity"].sum() + 1e-9
        large_vol                = candle_trades[candle_trades["quantity"] >= large_threshold]["quantity"].sum()
        buy_agg_vol              = candle_trades[~candle_trades["is_buyer_mm"]]["quantity"].sum()
        large_trade_ratio_arr[i] = large_vol / total_vol
        buy_aggression_arr[i]    = buy_agg_vol / total_vol
    return large_trade_ratio_arr, buy_aggression_arr


def _compute_features(df, cvd_df, funding_df, oi_df, liq_df, agg_df):
    n        = len(df)
    features = pd.DataFrame(index=df.index)

    features["log_return"]   = np.log(df["close"] / df["close"].shift(1))
    features["hl_range"]     = (df["high"] - df["low"]) / df["close"]
    features["vol_ratio"]    = df["volume"] / (df["volume"].rolling(20, min_periods=1).mean() + 1e-9)
    features["buy_ratio"]    = df["taker_buy_volume"] / (df["volume"] + 1e-9)
    features["realized_vol"] = features["log_return"].rolling(12, min_periods=1).std() * np.sqrt(365 * 24 * 12)

    if cvd_df is not None and len(cvd_df) >= n:
        cvd_s   = pd.Series(cvd_df["cvd"].values[-n:])
        delta_s = pd.Series(cvd_df["delta"].values[-n:])
        features["cvd_norm"]   = cvd_s.pct_change().fillna(0).values
        features["delta_norm"] = (delta_s / (df["volume"].values + 1e-9))
        features["cvd_accel"]  = cvd_s.pct_change().diff().fillna(0).values
    else:
        features["cvd_norm"]   = 0.0
        features["delta_norm"] = 0.0
        features["cvd_accel"]  = 0.0

    features["funding"]          = _align_funding_to_candles(df, funding_df)
    features["oi_change"]        = _align_oi_to_candles(df, oi_df)

    long_liq, short_liq          = _align_liquidations_to_candles(df, liq_df)
    features["long_liq_ratio"]   = long_liq
    features["short_liq_ratio"]  = short_liq

    large_trade_ratio, buy_aggression = _align_agg_trades_to_candles(df, agg_df)
    features["large_trade_ratio"] = large_trade_ratio
    features["buy_aggression"]    = buy_aggression

    return features.fillna(0.0)


def build_sequences(symbol, interval=INTERVAL, window=WINDOW, limit=1000):
    df      = _fetch_ohlcv(symbol, interval, limit)
    cvd_df  = _fetch_cvd(symbol, interval, limit)
    fund_df = _fetch_funding(symbol, limit=200)
    oi_df   = _fetch_oi(symbol, interval, limit=200)
    liq_df  = _fetch_liquidations_timeseries(symbol, limit=2000)
    agg_df  = _fetch_agg_trades_timeseries(symbol, limit=10000)

    if df is None or len(df) < window + 10:
        return None, None

    features   = _compute_features(df, cvd_df, fund_df, oi_df, liq_df, agg_df)
    arr        = features.values.astype(np.float32)
    closes     = df["close"].values
    open_times = df["open_time"].values
    real_labels = _fetch_real_labels(symbol)

    symbol_vol       = float(np.std(np.diff(closes) / (closes[:-1] + 1e-9)))
    trending_thresh  = symbol_vol * 1.5
    volatile_thresh  = symbol_vol * 1.0

    X, y     = [], []
    fwd_window = 8

    for i in range(window, len(arr) - fwd_window):
        X.append(arr[i - window:i])
        ts = int(open_times[i])

        if ts in real_labels:
            y.append(real_labels[ts])
            continue

        fwd_closes  = closes[i:i + fwd_window]
        fwd_returns = np.diff(fwd_closes) / (fwd_closes[:-1] + 1e-9)
        fwd_total   = (fwd_closes[-1] - fwd_closes[0]) / (fwd_closes[0] + 1e-9)
        fwd_std     = float(np.std(fwd_returns))
        fwd_abs     = float(abs(fwd_total))

        if fwd_abs > trending_thresh and fwd_std < fwd_abs * 2:
            label = 0
        elif fwd_std > volatile_thresh and fwd_abs < trending_thresh:
            label = 2
        else:
            label = 1

        y.append(label)

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int64)


def build_live_sequence(symbol, interval=INTERVAL, window=WINDOW):
    fetch_limit = window + 50
    df      = _fetch_ohlcv(symbol, interval, fetch_limit)
    cvd_df  = _fetch_cvd(symbol, interval, fetch_limit)
    fund_df = _fetch_funding(symbol, limit=50)
    oi_df   = _fetch_oi(symbol, interval, limit=50)
    liq_df  = _fetch_liquidations_timeseries(symbol, limit=500)
    agg_df  = _fetch_agg_trades_timeseries(symbol, limit=2000)

    if df is None or len(df) < window:
        return None

    features = _compute_features(df, cvd_df, fund_df, oi_df, liq_df, agg_df)
    if len(features) < window:
        return None

    scaler_path = os.path.join(MODEL_DIR, f"scaler_{symbol}.npy")
    if not os.path.exists(scaler_path):
        return None

    arr = features.values.astype(np.float32)
    return arr[-window:][np.newaxis, :, :].astype(np.float32)