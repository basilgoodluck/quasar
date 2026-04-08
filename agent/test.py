import asyncio
import aiohttp
import numpy as np
import pandas as pd
import subprocess
import json
from logger import get_logger

logger = get_logger(__name__)

BINANCE_BASE = "https://fapi.binance.com"
INTERVAL     = "5m"
WINDOW       = 24
KRAKEN_CLI   = "/root/.cargo/bin/kraken"

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "DOGEUSDT", "AVAXUSDT", "LINKUSDT", "ARBUSDT", "ORDIUSDT",
]


async def _get(session, url, params):
    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as r:
        r.raise_for_status()
        return await r.json()


async def fetch_klines(session, symbol):
    data = await _get(session, f"{BINANCE_BASE}/fapi/v1/klines", {
        "symbol": symbol, "interval": INTERVAL, "limit": 150
    })
    df = pd.DataFrame(data, columns=[
        "open_time","open","high","low","close","volume",
        "close_time","quote_vol","trades","taker_buy_volume","taker_buy_quote","ignore"
    ])
    for col in ["open","high","low","close","volume","taker_buy_volume"]:
        df[col] = df[col].astype(float)
    df["open_time"] = df["open_time"].astype(int)
    return df


async def fetch_funding(session, symbol):
    data = await _get(session, f"{BINANCE_BASE}/fapi/v1/fundingRate", {
        "symbol": symbol, "limit": 20
    })
    return pd.DataFrame([{
        "funding_time": int(f["fundingTime"]),
        "funding_rate": float(f["fundingRate"])
    } for f in data])


async def fetch_oi(session, symbol):
    data = await _get(session, f"{BINANCE_BASE}/futures/data/openInterestHist", {
        "symbol": symbol, "period": INTERVAL, "limit": 50
    })
    return pd.DataFrame([{
        "timestamp":     int(o["timestamp"]),
        "open_interest": float(o["sumOpenInterest"])
    } for o in data])


async def fetch_price(session, symbol):
    data = await _get(session, f"{BINANCE_BASE}/fapi/v1/ticker/price", {"symbol": symbol})
    return float(data["price"])


async def fetch_all(session, symbol):
    return await asyncio.gather(
        fetch_klines(session, symbol),
        fetch_funding(session, symbol),
        fetch_oi(session, symbol),
        fetch_price(session, symbol),
    )


def align_funding(df, funding_df):
    if funding_df is None or len(funding_df) == 0:
        return np.zeros(len(df), dtype=np.float32)
    ft, fr = funding_df["funding_time"].values, funding_df["funding_rate"].values
    result = np.zeros(len(df), dtype=np.float32)
    for i, ot in enumerate(df["open_time"].values):
        idx = np.searchsorted(ft, ot, side="right") - 1
        if idx >= 0:
            result[i] = float(np.clip(fr[idx] / 0.005, -1.0, 1.0))
    return result


def align_oi(df, oi_df):
    if oi_df is None or len(oi_df) < 5:
        return np.zeros(len(df), dtype=np.float32)
    ot, ov = oi_df["timestamp"].values, oi_df["open_interest"].values
    result = np.zeros(len(df), dtype=np.float32)
    for i, t in enumerate(df["open_time"].values):
        idx = np.searchsorted(ot, t, side="right") - 1
        if idx >= 4:
            chg = (ov[idx] - ov[idx - 4]) / (ov[idx - 4] + 1e-9)
            result[i] = float(np.clip(chg, -1.0, 1.0))
    return result


def detect_regime(df, funding_df, oi_df) -> dict:
    w = df.tail(WINDOW).copy().reset_index(drop=True)

    buy_vol    = w["taker_buy_volume"]
    sell_vol   = w["volume"] - buy_vol
    delta      = buy_vol - sell_vol
    cvd        = delta.cumsum()
    buy_ratio  = (buy_vol / (w["volume"] + 1e-9)).values
    delta_norm = (delta / (w["volume"] + 1e-9)).values
    cvd_pct    = pd.Series(cvd.values).pct_change().fillna(0).values
    cvd_accel  = pd.Series(cvd_pct).diff().fillna(0).values
    log_ret    = np.log(w["close"].values / np.roll(w["close"].values, 1))
    log_ret[0] = 0
    rvol       = float(np.std(log_ret) * np.sqrt(365 * 24 * 12))

    funding_arr  = align_funding(w, funding_df)
    oi_arr       = align_oi(w, oi_df)

    closes       = w["close"].values
    fwd_total    = (closes[-1] - closes[0]) / (closes[0] + 1e-9)

    oi_trending  = float(np.mean(oi_arr))
    oi_volatile  = float(np.std(oi_arr))
    funding_mean = float(np.mean(funding_arr))
    funding_flip = int(np.sum(np.diff(np.sign(funding_arr)) != 0))
    delta_trend  = float(np.mean(delta_norm))
    cvd_chaos    = float(np.std(cvd_accel))
    long_liq     = float(np.mean(buy_ratio < 0.35))
    short_liq    = float(np.mean(buy_ratio > 0.65))
    liq_one_side = long_liq - short_liq
    liq_both     = long_liq + short_liq

    scores = {"trending": 0, "ranging": 0, "volatile": 0}

    if abs(oi_trending) > 0.02:
        scores["trending"] += 2
    if funding_flip <= 2:
        scores["trending"] += 1
    if abs(funding_mean) > 0.3:
        scores["trending"] += 1
    if abs(liq_one_side) > 0.2:
        scores["trending"] += 2
    if abs(delta_trend) > 0.05:
        scores["trending"] += 2
    if abs(fwd_total) > 0.005:
        scores["trending"] += 1

    if oi_volatile > 0.05:
        scores["volatile"] += 2
    if liq_both > 0.4:
        scores["volatile"] += 2
    if cvd_chaos > 0.5:
        scores["volatile"] += 2
    if rvol > 2.0:
        scores["volatile"] += 1
    if funding_flip >= 4:
        scores["volatile"] += 1

    if abs(oi_trending) < 0.01:
        scores["ranging"] += 2
    if funding_flip >= 3:
        scores["ranging"] += 1
    if abs(funding_mean) < 0.15:
        scores["ranging"] += 1
    if liq_both < 0.2 and abs(liq_one_side) < 0.1:
        scores["ranging"] += 2
    if abs(delta_trend) < 0.02:
        scores["ranging"] += 2
    if abs(fwd_total) < 0.002:
        scores["ranging"] += 1

    total      = sum(scores.values()) or 1
    regime     = max(scores, key=scores.get)
    confidence = round(scores[regime] / total, 4)

    if scores["trending"] >= 3 and scores["volatile"] >= 3:
        regime     = "trending_volatile"
        confidence = round((scores["trending"] + scores["volatile"]) / (total * 1.5), 4)

    direction = None
    if regime in ("trending", "trending_volatile"):
        direction = "LONG" if (oi_trending > 0 and delta_trend > 0) else "SHORT"

    return {
        "regime":     regime,
        "confidence": min(confidence, 0.99),
        "direction":  direction,
        "scores":     scores,
    }


def ensure_paper_init():
    try:
        subprocess.check_output(
            [KRAKEN_CLI, "futures", "paper", "status", "-o", "json"],
            timeout=10, stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        subprocess.check_output(
            [KRAKEN_CLI, "futures", "paper", "init", "--balance", "10000", "-o", "json"],
            timeout=10
        )
        logger.info("[paper] initialised with $10,000")


def paper_exec(side, symbol, volume, leverage=2):
    pair = symbol if symbol.startswith("PF_") else f"PF_{symbol}"
    cmd  = [
        KRAKEN_CLI, "futures", "paper",
        side, pair, str(volume),
        "--leverage", str(leverage),
        "--type", "market",
        "-o", "json"
    ]
    raw = subprocess.check_output(cmd, timeout=15, stderr=subprocess.DEVNULL)
    return json.loads(raw)


TRADEABLE = {"trending", "trending_volatile"}
MIN_CONF  = 0.50
RISK_USD  = 100
LEVERAGE  = 2


async def run_once():
    ensure_paper_init()

    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(
            *[fetch_all(session, sym) for sym in SYMBOLS],
            return_exceptions=True
        )

    for sym, result in zip(SYMBOLS, results):
        if isinstance(result, Exception):
            logger.error(f"[{sym}] fetch error: {result}")
            continue

        klines, funding, oi, price = result

        if klines is None or len(klines) < WINDOW:
            logger.warning(f"[{sym}] not enough candles")
            continue

        regime = detect_regime(klines, funding, oi)
        logger.info(
            f"[{sym}] regime={regime['regime']} conf={regime['confidence']} "
            f"dir={regime['direction']} scores={regime['scores']}"
        )

        if regime["regime"] not in TRADEABLE:
            logger.info(f"[{sym}] skip — {regime['regime']}")
            continue

        if regime["confidence"] < MIN_CONF:
            logger.info(f"[{sym}] skip — low conf {regime['confidence']}")
            continue

        direction = regime["direction"]
        if not direction:
            continue

        side   = "buy" if direction == "LONG" else "sell"
        volume = round((RISK_USD * LEVERAGE) / price, 6)

        try:
            order = paper_exec(side, sym, volume, LEVERAGE)
            logger.info(f"[{sym}] {direction} | price={price} vol={volume} | {order}")
        except Exception as e:
            logger.error(f"[{sym}] order failed: {e}")


async def run_paper_trading():
    logger.info(f"test.py starting | {len(SYMBOLS)} pairs | {INTERVAL}")
    while True:
        await run_once()
        logger.info("sleeping 5m...")
        await asyncio.sleep(300)


if __name__ == "__main__":
    asyncio.run(run_paper_trading())