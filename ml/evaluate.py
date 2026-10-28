"""
Evaluate the trained model on the held-out TEST split with real metrics.

    python evaluate.py

Prints a full classification report (precision / recall / F1 per gesture) and
overall accuracy, and writes a confusion-matrix image to
ml/artifacts/confusion_matrix.png. The test split is never seen during training.
"""

import os
import sys

import numpy as np
import torch
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dataset import make_splits                      # noqa: E402
from features import LABELS                          # noqa: E402
from model import PulseQualityNet, pick_device       # noqa: E402

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")


def load_model(device):
    path = os.path.join(ART, "gesture_model.pt")
    if not os.path.exists(path):
        raise RuntimeError("No trained model. Run train.py first.")
    ckpt = torch.load(path, map_location=device)
    model = PulseQualityNet(num_classes=len(ckpt["labels"])).to(device)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    return model, ckpt["labels"]


@torch.no_grad()
def main():
    device = pick_device()
    model, labels = load_model(device)

    # rebuild the SAME splits (same seed) and evaluate on test only
    splits = make_splits(seed=42)
    Xte, yte = splits["test"]
    preds = model(torch.from_numpy(Xte).to(device)).argmax(1).cpu().numpy()

    acc = accuracy_score(yte, preds)
    print(f"\nTEST accuracy: {acc:.3f}  ({len(yte)} samples)\n")
    print(classification_report(yte, preds, target_names=labels,
                                labels=list(range(len(labels))), zero_division=0))

    cm = confusion_matrix(yte, preds, labels=list(range(len(labels))))
    _plot_cm(cm, labels, acc)


def _plot_cm(cm, labels, acc):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="PuRd",
                xticklabels=labels, yticklabels=labels, cbar=False, ax=ax)
    ax.set_xlabel("predicted"); ax.set_ylabel("true")
    ax.set_title(f"Confusion matrix — test acc {acc:.2f}")
    fig.tight_layout()
    p = os.path.join(ART, "confusion_matrix.png")
    fig.savefig(p, dpi=120)
    print(f"saved confusion matrix -> {p}")


if __name__ == "__main__":
    main()
