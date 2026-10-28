"""
Pulse-quality classifier: a small 1-D CNN over the rPPG waveform.

Input : (batch, 1, WINDOW)   -- one normalised pulse window
Output: (batch, num_classes) -- good / bad logits

A clean pulse is near-periodic; a bad one is broadband noise or baseline
wander. A 1-D CNN picks up those shape differences directly from the waveform.
Tiny (~30k params): trains in seconds, runs instantly.
"""

import torch
import torch.nn as nn

from features import WINDOW, LABELS


class PulseQualityNet(nn.Module):
    def __init__(self, num_classes=len(LABELS)):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(1, 16, kernel_size=7, padding=3),
            nn.BatchNorm1d(16), nn.ReLU(), nn.MaxPool1d(2),
            nn.Conv1d(16, 32, kernel_size=5, padding=2),
            nn.BatchNorm1d(32), nn.ReLU(), nn.MaxPool1d(2),
            nn.Conv1d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64), nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
        )
        self.head = nn.Sequential(
            nn.Flatten(), nn.Dropout(0.3), nn.Linear(64, num_classes))

    def forward(self, x):
        # accept (batch, WINDOW) or (batch, 1, WINDOW)
        if x.dim() == 2:
            x = x.unsqueeze(1)
        return self.head(self.net(x))


def pick_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")
