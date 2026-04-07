import os
import torch
import torch.nn as nn


# Regime classes
REGIMES = ["trending", "ranging", "volatile"]


class RegimeLSTM(nn.Module):
    def __init__(self, input_size, hidden_size=128, num_layers=2, dropout=0.3):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.dropout = nn.Dropout(dropout)
        self.head = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 3),  # trending, ranging, volatile
        )

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.dropout(out[:, -1, :])
        return torch.softmax(self.head(out), dim=-1)  # [p_trending, p_ranging, p_volatile]


def get_model(input_size, device="cpu"):
    return RegimeLSTM(input_size=input_size).to(device)


def save_model(model, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save(model.state_dict(), path)


def load_model(path, input_size, device="cpu"):
    model = get_model(input_size, device)
    model.load_state_dict(torch.load(path, map_location=device))
    model.eval()
    return model