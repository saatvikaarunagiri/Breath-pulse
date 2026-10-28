"""
Feature engineering for pulse-signal quality classification.

The app already extracts a 1-D rPPG pulse waveform (POS algorithm, bandpassed).
A *window* of that waveform is the input to the classifier. The job: decide
whether this window is a trustworthy pulse ("good") or junk dominated by motion
/ lighting noise ("bad") — i.e. learn the confidence judgement the app currently
makes with a hand-tuned threshold.

Each window is resampled to a fixed length and z-normalised (zero mean, unit
variance) so the model keys on *shape*, not absolute amplitude. Pure numpy and
unit-testable.
"""

import numpy as np

FS = 30                      # Hz the pulse signal is sampled at
WIN_SEC = 8                  # seconds of waveform per sample
WINDOW = FS * WIN_SEC        # 240 samples

# Two classes: is this pulse window usable?
LABELS = ["good", "bad"]
LABEL_TO_ID = {name: i for i, name in enumerate(LABELS)}


def normalize_window(sig):
    """1-D waveform -> fixed-length (WINDOW,) z-normalised float32."""
    sig = np.asarray(sig, dtype=np.float32).ravel()
    if len(sig) < 2:
        return np.zeros(WINDOW, dtype=np.float32)
    if len(sig) != WINDOW:                       # resample time axis
        src = np.linspace(0, 1, len(sig))
        dst = np.linspace(0, 1, WINDOW)
        sig = np.interp(dst, src, sig).astype(np.float32)
    sig = sig - sig.mean()
    sig = sig / (sig.std() + 1e-6)
    return sig.astype(np.float32)


def spectral_features(sig, fs=FS):
    """A few interpretable numbers (handy for debugging / the writeup), not fed
    to the CNN: dominant frequency in the HR band and its prominence."""
    sig = np.asarray(sig, float)
    sig = sig - sig.mean()
    spec = np.abs(np.fft.rfft(sig * np.hanning(len(sig))))
    freqs = np.fft.rfftfreq(len(sig), 1 / fs)
    band = (freqs >= 0.7) & (freqs <= 4.0)
    if not band.any() or spec[band].sum() == 0:
        return {"peak_hz": 0.0, "prominence": 0.0}
    peak = freqs[band][spec[band].argmax()]
    prom = spec[band].max() / (spec[band].mean() + 1e-9)
    return {"peak_hz": float(peak), "prominence": float(prom)}


def augment_window(sig, rng, noise=0.05, amp=0.1, shift=5):
    """Light augmentation for the training split only."""
    w = sig.copy()
    w = w + rng.normal(0, noise, w.shape).astype(np.float32)
    w = w * (1.0 + rng.uniform(-amp, amp))
    s = int(rng.integers(-shift, shift + 1))
    if s:
        w = np.roll(w, s)
    return w.astype(np.float32)
