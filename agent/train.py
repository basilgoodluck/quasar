import os
import time
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset, random_split
from database.connection import get_connection
from agent.features import build_sequences
from agent.model import get_model, save_model
from logger import get_logger

logger = get_logger(__name__)

MODEL_DIR  = "/app/models"  # MUST match your Docker volume
INTERVAL   = os.getenv("TRAIN_INTERVAL", "15m")
WINDOW     = int(os.getenv("TRAIN_WINDOW", "96"))
EPOCHS     = int(os.getenv("TRAIN_EPOCHS", "50"))
BATCH_SIZE = int(os.getenv("TRAIN_BATCH_SIZE", "64"))
LR         = float(os.getenv("TRAIN_LR", "0.001"))
VAL_SPLIT  = float(os.getenv("TRAIN_VAL_SPLIT", "0.15"))
DEVICE     = "cuda" if torch.cuda.is_available() else "cpu"
RETRAIN_INTERVAL = int(os.getenv("RETRAIN_INTERVAL_SEC", 3600))  # retrain every hour

LONG_THRESHOLD  = float(os.getenv("LONG_THRESHOLD", "0.015"))
SHORT_THRESHOLD = float(os.getenv("SHORT_THRESHOLD", "-0.015"))

def get_active_symbols():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT symbol FROM symbols WHERE active = TRUE")
            return [r[0] for r in cur.fetchall()]

def _count_real_labels():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM trade_outcomes WHERE status IN ('WIN','LOSS','NEUTRAL')")
            return cur.fetchone()[0]

def _log_retrain_event(val_loss: float, real_label_count: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO retrain_log (val_loss, real_label_count, trained_at)
                VALUES (%s, %s, EXTRACT(EPOCH FROM NOW())::BIGINT)
            """, (val_loss, real_label_count))
            conn.commit()

def _convert_to_classes(y_continuous: np.ndarray, real_labels: dict, open_times: np.ndarray, window: int) -> np.ndarray:
    y_class = []
    for i, val in enumerate(y_continuous):
        ts = int(open_times[window + i]) if open_times is not None else None
        if ts and ts in real_labels:
            outcome = real_labels[ts]
            if outcome == "WIN":
                y_class.append(0)
            elif outcome == "LOSS":
                y_class.append(1)
            else:
                y_class.append(2)
        else:
            fwd = (val - 0.5) * 0.1
            if fwd > LONG_THRESHOLD:
                y_class.append(0)
            elif fwd < SHORT_THRESHOLD:
                y_class.append(1)
            else:
                y_class.append(2)
    return np.array(y_class, dtype=np.int64)

def load_data(symbols):
    all_X, all_y = [], []
    for symbol in symbols:
        X, y = build_sequences(symbol, interval=INTERVAL, window=WINDOW)
        if X is None:
            logger.warning(f"Not enough data for {symbol}, skipping")
            continue
        y_class = _convert_to_classes(y, {}, None, WINDOW)
        all_X.append(X)
        all_y.append(y_class)

    if not all_X:
        raise RuntimeError("No data available for training")

    return np.concatenate(all_X), np.concatenate(all_y)

def train_one_model():
    symbols = get_active_symbols()
    logger.info(f"Symbols: {symbols}")
    real_count = _count_real_labels()
    logger.info(f"Real outcome labels available: {real_count}")

    X, y = load_data(symbols)
    logger.info(f"Total sequences: {len(X)} | Feature dim: {X.shape[2]}")

    X_t = torch.tensor(X, dtype=torch.float32)
    y_t = torch.tensor(y, dtype=torch.long)

    dataset    = TensorDataset(X_t, y_t)
    val_size   = int(len(dataset) * VAL_SPLIT)
    train_size = len(dataset) - val_size
    train_ds, val_ds = random_split(dataset, [train_size, val_size])

    train_dl = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_dl   = DataLoader(val_ds, batch_size=BATCH_SIZE)

    input_size = X.shape[2]
    model      = get_model(input_size, DEVICE)
    optimizer  = torch.optim.Adam(model.parameters(), lr=LR)
    criterion  = nn.CrossEntropyLoss()
    scheduler  = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)

    best_val_loss = float("inf")

    for epoch in range(1, EPOCHS + 1):
        model.train()
        train_loss = 0.0
        for xb, yb in train_dl:
            xb, yb = xb.to(DEVICE), yb.to(DEVICE)
            optimizer.zero_grad()
            pred = model(xb)
            loss = criterion(pred, yb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_loss += loss.item()

        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for xb, yb in val_dl:
                xb, yb = xb.to(DEVICE), yb.to(DEVICE)
                val_loss += criterion(model(xb), yb).item()

        train_loss /= len(train_dl)
        val_loss   /= len(val_dl)
        scheduler.step(val_loss)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            os.makedirs(MODEL_DIR, exist_ok=True)
            save_model(model, os.path.join(MODEL_DIR, "regime_lstm.pt"))

    _log_retrain_event(best_val_loss, real_count)
    logger.info(f"Retrain finished, best val loss: {best_val_loss}")

if __name__ == "__main__":
    while True:
        try:
            train_one_model()
        except Exception as e:
            logger.exception(f"Trainer crashed: {e}")
        logger.info(f"Sleeping {RETRAIN_INTERVAL}s before next retrain")
        time.sleep(RETRAIN_INTERVAL)