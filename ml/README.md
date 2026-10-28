# 🤖 Pulse Signal-Quality Classifier (the ML part)

This is the machine-learning component of Breath & Pulse Cam: a classifier **you
train yourself** that decides whether a heart-rate reading is **trustworthy
(`good`)** or **junk dominated by motion/lighting noise (`bad`)** — learning the
judgement the app currently makes with a hand-tuned confidence threshold.

Unlike the rest of the app (which *uses* a pretrained face model), here **you**
collect the dataset, design the network, train, and measure it — a genuine
end-to-end ML project.

> **Why signal quality and not arrhythmia?** Arrhythmia detection needs
> clinically-labelled data you can't collect at home, so any claim there would be
> dishonest. Signal quality is labelled trivially (sit still = good; move around =
> bad), it's genuinely useful, and the architecture extends to other labels later.

## The pipeline

```
collect_data.py ─▶ ml/data/<good|bad>/*.npy      (label live pulse windows)
make_synthetic_data.py (optional dry run) ──────┘
      │
  dataset.py   ─▶ normalise + stratified split + augmentation
      │
  train.py     ─▶ PulseQualityNet (1-D CNN over the waveform) ─▶ artifacts/gesture_model.pt
      │                                                           artifacts/history.png
  evaluate.py  ─▶ accuracy, precision/recall/F1, confusion_matrix.png (TEST set)
      │
signal_classifier.py ─▶ live inference, used by the app
```

## How to run it

From the project root, in your activated venv:

```bash
pip install -r ml/requirements-ml.txt

# 1. get data — synthetic dry run:
python ml/make_synthetic_data.py --per-class 300
#    …or real data (recommended): sit still for GOOD, move/dim lights for BAD
python ml/collect_data.py

# 2. train (uses the M-series GPU automatically)
python ml/train.py --epochs 30

# 3. evaluate on the held-out test set
python ml/evaluate.py

# 4. use it live — the learned good/bad verdict replaces the threshold
python app.py --ml
```

If no trained model is found, `--ml` silently falls back to the original
confidence heuristic, so the app never breaks.

## Design notes (for your writeup)

- **The model reads the waveform shape.** Each sample is an 8-second pulse window,
  resampled to a fixed length and z-normalised, so the CNN keys on periodicity vs
  noise rather than absolute amplitude. (`features.py`)
- **Honest evaluation.** Stratified, held-out test set; augmentation on train only.
- **It closes the loop.** The classifier consumes the exact rPPG waveform the app
  already produces, and its verdict feeds straight back into the UI.

## Limitations

- Synthetic data only proves the plumbing; real webcam data makes it meaningful.
- Two classes today. Add one (e.g. `low_light`) by extending `features.LABELS`,
  collecting data, and retraining.
- Still **not a medical device.**
