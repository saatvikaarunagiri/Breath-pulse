"""
Train the gesture classifier.

    python train.py --epochs 40

Loads collected data, trains GestureNet, tracks validation accuracy, keeps the
best-performing weights, and writes:
    ml/artifacts/gesture_model.pt     – best weights + label list + config
    ml/artifacts/history.png          – loss / accuracy curves

Uses the M-series GPU (MPS) automatically when available.
"""

import argparse
import os
import sys

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dataset import make_splits                      # noqa: E402
from features import LABELS                          # noqa: E402
from model import PulseQualityNet, pick_device       # noqa: E402

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")


def loaders(splits, batch=32):
    out = {}
    for name, (X, y) in splits.items():
        ds = TensorDataset(torch.from_numpy(X), torch.from_numpy(y))
        out[name] = DataLoader(ds, batch_size=batch,
                               shuffle=(name == "train"))
    return out


@torch.no_grad()
def evaluate(model, loader, device, criterion):
    model.eval()
    loss_sum, correct, n = 0.0, 0, 0
    for xb, yb in loader:
        xb, yb = xb.to(device), yb.to(device)
        out = model(xb)
        loss_sum += criterion(out, yb).item() * len(yb)
        correct += (out.argmax(1) == yb).sum().item()
        n += len(yb)
    return loss_sum / n, correct / n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    os.makedirs(ART, exist_ok=True)

    device = pick_device()
    print(f"device: {device}")

    splits = make_splits(seed=args.seed)
    for name, (X, y) in splits.items():
        print(f"  {name:5}: {len(y)} samples")
    dl = loaders(splits, batch=args.batch)

    model = PulseQualityNet().to(device)
    print(f"parameters: {sum(p.numel() for p in model.parameters()):,}")
    criterion = nn.CrossEntropyLoss()
    opt = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-4)

    hist = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}
    best_val, best_state = 0.0, None

    for epoch in range(1, args.epochs + 1):
        model.train()
        for xb, yb in dl["train"]:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            opt.step()

        tl, ta = evaluate(model, dl["train"], device, criterion)
        vl, va = evaluate(model, dl["val"], device, criterion)
        hist["train_loss"].append(tl); hist["val_loss"].append(vl)
        hist["train_acc"].append(ta); hist["val_acc"].append(va)
        if va >= best_val:
            best_val = va
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        if epoch % 5 == 0 or epoch == 1:
            print(f"epoch {epoch:3d}  train_acc {ta:.3f}  val_acc {va:.3f}")

    # save best
    out_path = os.path.join(ART, "gesture_model.pt")
    torch.save({"state_dict": best_state, "labels": LABELS,
                "best_val_acc": best_val}, out_path)  # pulse-quality model
    print(f"\nbest val acc: {best_val:.3f}")
    print(f"saved model -> {out_path}")

    _plot(hist)


def _plot(hist):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4))
    a1.plot(hist["train_loss"], label="train"); a1.plot(hist["val_loss"], label="val")
    a1.set_title("Loss"); a1.set_xlabel("epoch"); a1.legend()
    a2.plot(hist["train_acc"], label="train"); a2.plot(hist["val_acc"], label="val")
    a2.set_title("Accuracy"); a2.set_xlabel("epoch"); a2.legend()
    fig.tight_layout()
    p = os.path.join(ART, "history.png")
    fig.savefig(p, dpi=120)
    print(f"saved curves -> {p}")


if __name__ == "__main__":
    main()
