"""
Generate SYNTHETIC pulse windows to dry-run the pipeline without a webcam.

  good : near-periodic waveform at a plausible heart rate (0.8-2.5 Hz) with
         harmonics and mild noise — what a clean rPPG pulse looks like.
  bad  : noise-dominated / baseline-wander / motion-spike signals — what you get
         when the subject moves or the lighting flickers.

NOT a substitute for real data; it just proves train/evaluate end to end.

    python make_synthetic_data.py --per-class 300
"""

import argparse
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from features import LABELS, FS, WIN_SEC, WINDOW            # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _good(rng):
    t = np.arange(WINDOW) / FS
    hr = rng.uniform(0.8, 2.5)                          # 48-150 bpm
    sig = np.sin(2 * np.pi * hr * t)
    sig += 0.3 * np.sin(2 * np.pi * 2 * hr * t + rng.uniform(0, 1))  # harmonic
    sig += 0.05 * np.sin(2 * np.pi * 0.2 * t)           # slight baseline
    sig += rng.normal(0, 0.15, WINDOW)                  # mild noise
    return sig


def _bad(rng):
    kind = rng.integers(0, 3)
    t = np.arange(WINDOW) / FS
    if kind == 0:                                       # broadband noise
        sig = rng.normal(0, 1, WINDOW)
    elif kind == 1:                                     # baseline wander + noise
        sig = 2.0 * np.sin(2 * np.pi * rng.uniform(0.05, 0.25) * t)
        sig += rng.normal(0, 0.6, WINDOW)
    else:                                               # motion spikes
        sig = rng.normal(0, 0.3, WINDOW)
        for _ in range(rng.integers(2, 6)):
            i = rng.integers(0, WINDOW)
            sig[i:i + 5] += rng.uniform(-4, 4)
    return sig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-class", type=int, default=300)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)

    gens = {"good": _good, "bad": _bad}
    for label in LABELS:
        d = os.path.join(DATA_DIR, label)
        os.makedirs(d, exist_ok=True)
        for i in range(args.per_class):
            sig = gens[label](rng).astype(np.float32)
            np.save(os.path.join(d, f"syn_{i}_{int(time.time()*1e6)%10**6}.npy"),
                    sig)
    print("Synthetic pulse data written:")
    for label in LABELS:
        print(f"  {label:5}: {len(os.listdir(os.path.join(DATA_DIR, label)))}")


if __name__ == "__main__":
    main()
