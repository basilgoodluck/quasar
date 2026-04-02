import os
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset, random_split
from database.connection import get_connection
from agent.features import build_sequences
from contracts.model import get_model, save_model
from logger import get_logger

logger = get_logger(__name__)

MODEL_DIR    = os.getenv("MODEL_DIR", "models")
INTERVAL     = os.getenv("TRAIN_INTERVAL", "15m")
WINDOW       = int(os.getenv("TRAIN_WINDOW", "96"))
EPOCHS       = int(os.getenv("TRAIN_EPOCHS", "50"))
BATCH_SIZE   = int(os.getenv("TRAIN_BATCH_SIZE", "64"))
LR           = float(os.getenv("TRAIN_LR", "0.001"))
VAL_SPLIT    = float(os.getenv("TRAIN_VAL_SPLIT", "0.15"))
DEVICE       = "cuda" if torch.cuda.is_available() else "cpu"


def get_active_symbols():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT symbol FROM symbols WHERE active = TRUE")
            return [r[0] for r in cur.fetchall()]


def load_data(symbols):
    all_X, all_y = [], []
    for symbol in symbols:
        logger.info(f"Building sequences for {symbol}")
        X, y = build_sequences(symbol, interval=INTERVAL, window=WINDOW)
        if X is None:
            logger.warning(f"Not enough data for {symbol}, skipping")
            continue
        all_X.append(X)
        all_y.append(y)
        logger.info(f"{symbol}: {len(X)} sequences")

    if not all_X:
        raise RuntimeError("No data available for training")

    return np.concatenate(all_X), np.concatenate(all_y)


def train():
    logger.info(f"Training on device: {DEVICE}")
    symbols = get_active_symbols()
    logger.info(f"Symbols: {symbols}")

    X, y = load_data(symbols)
    logger.info(f"Total sequences: {len(X)} | Feature dim: {X.shape[2]}")

    X_t = torch.tensor(X)
    y_t = torch.tensor(y)

    dataset  = TensorDataset(X_t, y_t)
    val_size = int(len(dataset) * VAL_SPLIT)
    train_size = len(dataset) - val_size
    train_ds, val_ds = random_split(dataset, [train_size, val_size])

    train_dl = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_dl   = DataLoader(val_ds,   batch_size=BATCH_SIZE)

    input_size = X.shape[2]
    model = get_model(input_size, DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.MSELoss()
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)

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

        logger.info(f"Epoch {epoch}/{EPOCHS} | train={train_loss:.6f} | val={val_loss:.6f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            save_model(model, os.path.join(MODEL_DIR, "regime_lstm.pt"))
            logger.info(f"Model saved (val={val_loss:.6f})")

    logger.info("Training complete")


if __name__ == "__main__":
    train()