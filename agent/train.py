import os
import time
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset, random_split
from database.connection import get_connection
from agent.features import build_sequences, INTERVAL, WINDOW
from agent.model import get_model, save_model
from logger import get_logger

logger = get_logger(__name__)

MODEL_DIR        = "/app/models"
EPOCHS           = int(os.getenv("TRAIN_EPOCHS", "50"))
BATCH_SIZE       = int(os.getenv("TRAIN_BATCH_SIZE", "64"))
LR               = float(os.getenv("TRAIN_LR", "0.001"))
VAL_SPLIT        = float(os.getenv("TRAIN_VAL_SPLIT", "0.15"))
DEVICE           = "cuda" if torch.cuda.is_available() else "cpu"
RETRAIN_INTERVAL = int(os.getenv("RETRAIN_INTERVAL_SEC", "3600"))  # every hour


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


def load_data(symbols):
    all_X, all_y = [], []

    for symbol in symbols:
        X, y = build_sequences(symbol, interval=INTERVAL, window=WINDOW)
        if X is None or len(X) == 0:
            logger.warning(f"[{symbol}] not enough data, skipping")
            continue
        all_X.append(X)
        all_y.append(y)
        logger.info(f"[{symbol}] sequences={len(X)} feature_dim={X.shape[2]}")

    if not all_X:
        raise RuntimeError("No training data available across all symbols")

    X_all = np.concatenate(all_X)
    y_all = np.concatenate(all_y)

    # Log class distribution so we can see if labels are balanced
    unique, counts = np.unique(y_all, return_counts=True)
    class_names    = ["trending", "ranging", "volatile"]
    for u, c in zip(unique, counts):
        logger.info(f"  class {class_names[u]}: {c} ({100*c/len(y_all):.1f}%)")

    return X_all, y_all


def _compute_class_weights(y: np.ndarray, num_classes: int = 3) -> torch.Tensor:
    """Inverse frequency weighting so minority classes aren't ignored."""
    counts  = np.bincount(y, minlength=num_classes).astype(np.float32)
    counts  = np.where(counts == 0, 1.0, counts)  # avoid divide by zero
    weights = 1.0 / counts
    weights = weights / weights.sum() * num_classes  # normalize
    return torch.tensor(weights, dtype=torch.float32).to(DEVICE)


def train_one_model():
    symbols    = get_active_symbols()
    real_count = _count_real_labels()
    logger.info(f"Symbols: {symbols} | Real outcome labels: {real_count} | Interval: {INTERVAL} | Window: {WINDOW}")

    X, y = load_data(symbols)
    logger.info(f"Total sequences: {len(X)} | Feature dim: {X.shape[2]}")

    X_t = torch.tensor(X, dtype=torch.float32)
    y_t = torch.tensor(y, dtype=torch.long)

    dataset    = TensorDataset(X_t, y_t)
    val_size   = max(1, int(len(dataset) * VAL_SPLIT))
    train_size = len(dataset) - val_size
    train_ds, val_ds = random_split(dataset, [train_size, val_size])

    train_dl = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,  drop_last=False)
    val_dl   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False, drop_last=False)

    input_size    = X.shape[2]
    model         = get_model(input_size, DEVICE)
    optimizer     = torch.optim.Adam(model.parameters(), lr=LR)
    class_weights = _compute_class_weights(y)
    criterion     = nn.CrossEntropyLoss(weight=class_weights)
    scheduler     = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)

    best_val_loss = float("inf")
    model_path    = os.path.join(MODEL_DIR, "regime_lstm.pt")

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

        train_loss /= max(len(train_dl), 1)
        val_loss   /= max(len(val_dl), 1)
        scheduler.step(val_loss)

        if epoch % 10 == 0:
            logger.info(f"  epoch {epoch}/{EPOCHS} train={train_loss:.4f} val={val_loss:.4f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            os.makedirs(MODEL_DIR, exist_ok=True)
            save_model(model, model_path)

    _log_retrain_event(best_val_loss, real_count)
    logger.info(f"Retrain finished | best val loss: {best_val_loss:.4f} | model saved to {model_path}")


if __name__ == "__main__":
    while True:
        try:
            train_one_model()
        except Exception as e:
            logger.exception(f"Trainer crashed: {e}")
        logger.info(f"Sleeping {RETRAIN_INTERVAL}s before next retrain")
        time.sleep(RETRAIN_INTERVAL)