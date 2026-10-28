"""
Load collected pulse windows into stratified train / val / test splits.

Augmentation is applied to the training split only; val/test stay untouched so
the reported numbers are honest.
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from features import (LABELS, LABEL_TO_ID, normalize_window,  # noqa: E402
                      augment_window)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def load_raw():
    X, y = [], []
    for name in LABELS:
        d = os.path.join(DATA_DIR, name)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".npy"):
                X.append(normalize_window(np.load(os.path.join(d, fn))))
                y.append(LABEL_TO_ID[name])
    if not X:
        raise RuntimeError(f"No data in {DATA_DIR}. Run collect_data.py or "
                           f"make_synthetic_data.py first.")
    return np.stack(X).astype(np.float32), np.array(y, dtype=np.int64)


def stratified_split(y, seed=42, val=0.15, test=0.15):
    rng = np.random.default_rng(seed)
    tr, va, te = [], [], []
    for cls in np.unique(y):
        idx = np.where(y == cls)[0]
        rng.shuffle(idx)
        n = len(idx)
        n_test = max(1, int(round(n * test)))
        n_val = max(1, int(round(n * val)))
        te += idx[:n_test].tolist()
        va += idx[n_test:n_test + n_val].tolist()
        tr += idx[n_test + n_val:].tolist()
    return np.array(tr), np.array(va), np.array(te)


def make_splits(seed=42, augment_factor=3):
    X, y = load_raw()
    tr, va, te = stratified_split(y, seed=seed)
    rng = np.random.default_rng(seed)
    Xtr, ytr = X[tr], y[tr]
    if augment_factor > 1:
        aug_X, aug_y = [Xtr], [ytr]
        for _ in range(augment_factor - 1):
            aug_X.append(np.stack([augment_window(w, rng) for w in Xtr]))
            aug_y.append(ytr)
        Xtr = np.concatenate(aug_X).astype(np.float32)
        ytr = np.concatenate(aug_y)
    return {"train": (Xtr, ytr), "val": (X[va], y[va]), "test": (X[te], y[te])}
