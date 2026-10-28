"""
Live inference wrapper — classifies the current pulse window as good/bad.

The app calls classify(pulse_window) each time it recomputes the heart rate and
uses the result as a *learned* trust signal instead of the hand-tuned threshold.
Fails soft: if torch or the model is missing, available=False and the app keeps
its original confidence heuristic.
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from features import normalize_window, LABELS            # noqa: E402

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")


class SignalClassifier:
    def __init__(self):
        self.available = False
        self.labels = LABELS
        self.status = "not loaded"
        self._torch = None
        self._model = None
        self._device = None
        self._load()

    def _load(self):
        try:
            import torch
            from model import PulseQualityNet, pick_device
            path = os.path.join(ART, "gesture_model.pt")  # same filename convention
            if not os.path.exists(path):
                self.status = "no model file (train first)"
                return
            self._torch = torch
            self._device = pick_device()
            ckpt = torch.load(path, map_location=self._device)
            self.labels = ckpt.get("labels", LABELS)
            self._model = PulseQualityNet(num_classes=len(self.labels)).to(self._device)
            self._model.load_state_dict(ckpt["state_dict"])
            self._model.eval()
            self.available = True
            self.status = "ready"
        except Exception as e:
            self.status = f"unavailable ({type(e).__name__})"

    def classify(self, pulse_window):
        """Return (label, confidence) or (None, 0.0) if unavailable."""
        if not self.available:
            return None, 0.0
        w = normalize_window(pulse_window)
        with self._torch.no_grad():
            x = self._torch.from_numpy(w[None]).to(self._device)
            probs = self._torch.softmax(self._model(x), dim=1)[0].cpu().numpy()
        cls = int(probs.argmax())
        return self.labels[cls], float(probs[cls])
