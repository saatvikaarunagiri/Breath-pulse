"""
Breath & Pulse Cam vision core: contactless heart rate (rPPG / POS) and
respiration rate (chest optical flow), as a UI-agnostic processor.

`VitalsProcessor.process(frame_bgr)` is handed to the camera thread and returns
the annotated frame. The app reads self.hr / self.rr / self.status off it and
can log readings to a CSV for the session.

NOT a medical device.
"""

import threading
import time

import cv2
import numpy as np
from scipy.signal import butter, filtfilt

from core.theme import BGR

WINDOW_SEC = 10
FS = 30
UPDATE_EVERY = 0.5


# ---------------- signal helpers (unit-testable) --------------------------

def bandpass(sig, fs, lo, hi, order=3):
    nyq = 0.5 * fs
    b, a = butter(order, [max(lo / nyq, 1e-4), min(hi / nyq, 0.999)],
                  btype="band")
    return filtfilt(b, a, sig)


def pos_signal(rgb):
    mean = rgb.mean(axis=0) + 1e-9
    Cn = rgb / mean
    S1 = Cn[:, 1] - Cn[:, 2]
    S2 = Cn[:, 1] + Cn[:, 2] - 2 * Cn[:, 0]
    alpha = np.std(S1) / (np.std(S2) + 1e-9)
    h = S1 + alpha * S2
    return h - h.mean()


def dominant_bpm(sig, fs, lo_hz, hi_hz):
    if len(sig) < fs * 3:
        return None, 0.0
    sig = sig - sig.mean()
    spec = np.abs(np.fft.rfft(sig * np.hanning(len(sig))))
    freqs = np.fft.rfftfreq(len(sig), 1 / fs)
    mask = (freqs >= lo_hz) & (freqs <= hi_hz)
    if not mask.any():
        return None, 0.0
    band = np.where(mask, spec, 0)
    idx = band.argmax()
    conf = band[idx] / (spec[mask].sum() + 1e-9)
    return freqs[idx] * 60.0, float(conf)


def resample_uniform(t, x, fs):
    t = np.asarray(t, float)
    if len(t) < 2 or t[-1] <= t[0]:
        return None
    grid = np.arange(t[0], t[-1], 1 / fs)
    return np.interp(grid, t, np.asarray(x, float))


def _create_face():
    import mediapipe as mp
    if not hasattr(mp, "solutions"):
        raise RuntimeError(
            "This mediapipe build has no 'solutions' API. Install the pinned "
            "version:  pip install mediapipe==0.10.14")
    return mp.solutions.face_mesh.FaceMesh(
        max_num_faces=1, refine_landmarks=False,
        min_detection_confidence=0.5, min_tracking_confidence=0.5)


# ---------------- the processor -------------------------------------------

class VitalsProcessor:
    def __init__(self, profile=None, create_face=True, classifier=None):
        self._face = _create_face() if create_face else None
        self._lock = threading.Lock()

        # Optional trained signal-quality classifier (ml/). When available, its
        # verdict replaces the hand-tuned confidence threshold.
        self.classifier = classifier
        self.ml_quality = None                   # "good" / "bad" / None
        self.ml_mode = bool(classifier and getattr(classifier, "available", False))
        self.t0 = time.time()
        self.times, self.R, self.G, self.B = [], [], [], []
        self.resp_t, self.resp_v = [], []
        self._prev_chest = None
        self._last_update = 0.0
        self._hr_wave = np.zeros(1)

        self.hr = None
        self.rr = None
        self.conf = 0.0
        self.status = "Look at the camera and hold still…"
        self.log = []                       # (t, hr, rr)
        self.baseline = profile.get("resting_hr") if profile else None

    # ---- public ----
    def session_profile(self):
        hrs = [hr for _, hr, _ in self.log if hr]
        return {"resting_hr": round(float(np.median(hrs)), 1)} if hrs else {}

    def save_log(self, path):
        with open(path, "w") as f:
            f.write("seconds,heart_rate_bpm,resp_rate_per_min\n")
            for t, hr, rr in self.log:
                f.write(f"{t:.1f},{hr if hr else ''},{rr if rr else ''}\n")
        return len(self.log)

    # ---- per-frame ----
    def process(self, frame):
        h, w = frame.shape[:2]
        now = time.time() - self.t0
        res = self._face.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        found = bool(res.multi_face_landmarks)

        if found:
            lm = res.multi_face_landmarks[0].landmark
            xs = np.array([p.x for p in lm]) * w
            ys = np.array([p.y for p in lm]) * h
            x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
            fw, fh = x1 - x0, y1 - y0

            rois = [
                (x0 + 0.30*fw, y0 + 0.08*fh, x0 + 0.70*fw, y0 + 0.20*fh),
                (x0 + 0.12*fw, y0 + 0.55*fh, x0 + 0.34*fw, y0 + 0.72*fh),
                (x0 + 0.66*fw, y0 + 0.55*fh, x0 + 0.88*fw, y0 + 0.72*fh),
            ]
            vals = []
            for ax, ay, bx, by in rois:
                ax, ay = max(0, int(ax)), max(0, int(ay))
                bx, by = min(w, int(bx)), min(h, int(by))
                if bx - ax > 4 and by - ay > 4:
                    vals.append(frame[ay:by, ax:bx][..., ::-1].reshape(-1, 3)
                                .mean(axis=0))
                    cv2.rectangle(frame, (ax, ay), (bx, by), BGR["sage"], 1)
            if vals:
                r, g, b = np.mean(vals, axis=0)
                self.times.append(now); self.R.append(r)
                self.G.append(g); self.B.append(b)

            cx0, cx1 = int(max(0, x0 - 0.3*fw)), int(min(w, x1 + 0.3*fw))
            cy0, cy1 = int(min(h-2, y1 + 0.2*fh)), int(min(h, y1 + 1.5*fh))
            if cx1 - cx0 > 10 and cy1 - cy0 > 10:
                cv2.rectangle(frame, (cx0, cy0), (cx1, cy1), BGR["lavender"], 1)
                chest = cv2.resize(cv2.cvtColor(frame[cy0:cy1, cx0:cx1],
                                   cv2.COLOR_BGR2GRAY), (64, 64))
                if self._prev_chest is not None:
                    flow = cv2.calcOpticalFlowFarneback(
                        self._prev_chest, chest, None, 0.5, 2, 15, 2, 5, 1.2, 0)
                    self.resp_t.append(now)
                    self.resp_v.append(float(flow[..., 1].mean()))
                self._prev_chest = chest

        self._trim(now)
        if now - self._last_update > UPDATE_EVERY and len(self.times) > FS * 5:
            self._analyze(now)

        self._overlay(frame, w, h, found)
        return frame

    def _trim(self, now):
        for ts, arrs in ((self.times, (self.R, self.G, self.B)),
                         (self.resp_t, (self.resp_v,))):
            while ts and ts[0] < now - WINDOW_SEC:
                ts.pop(0)
                for a in arrs:
                    a.pop(0)

    def _analyze(self, now):
        self._last_update = now
        r = resample_uniform(self.times, self.R, FS)
        g = resample_uniform(self.times, self.G, FS)
        b = resample_uniform(self.times, self.B, FS)
        if r is not None and len(r) > FS * 3:
            pulse = bandpass(pos_signal(np.stack([r, g, b], axis=1)),
                             FS, 0.7, 4.0)
            bpm, conf = dominant_bpm(pulse, FS, 0.7, 4.0)
            if self.ml_mode:
                label, _ = self.classifier.classify(pulse)
                self.ml_quality = label
            if bpm:
                self.hr, self.conf = bpm, conf
                self._hr_wave = pulse[-FS * 3:]
        if len(self.resp_t) > FS * 5:
            rv = resample_uniform(self.resp_t, self.resp_v, FS)
            if rv is not None and len(rv) > FS * 4:
                rv = bandpass(np.cumsum(rv - rv.mean()), FS, 0.1, 0.5)
                rpm, _ = dominant_bpm(rv, FS, 0.1, 0.5)
                if rpm:
                    self.rr = rpm
        if self.hr:
            self.log.append((now, round(self.hr, 1),
                             round(self.rr, 1) if self.rr else None))

    def _overlay(self, frame, w, h, found):
        bar = frame.copy()
        cv2.rectangle(bar, (0, 0), (w, 70), BGR["bg"], -1)
        cv2.addWeighted(bar, 0.55, frame, 0.45, 0, frame)

        hr_txt = (f"HR {self.hr:.0f} bpm" if self.hr else "HR --")
        if self.ml_mode and self.hr:
            tag = f"  [{self.ml_quality or '...'}]"       # learned verdict
        elif self.hr:
            tag = "  ok" if self.conf > 0.25 else "  weak"
        else:
            tag = ""
        rr_txt = (f"RR {self.rr:.1f}/min" if self.rr else "RR --")
        cv2.putText(frame, hr_txt + tag, (14, 28), cv2.FONT_HERSHEY_DUPLEX,
                    0.7, BGR["pink_dk"], 1, cv2.LINE_AA)
        cv2.putText(frame, rr_txt, (14, 56), cv2.FONT_HERSHEY_DUPLEX,
                    0.6, BGR["text"], 1, cv2.LINE_AA)
        if not found:
            cv2.putText(frame, "no face", (w - 110, 28),
                        cv2.FONT_HERSHEY_DUPLEX, 0.6, BGR["coral"], 1, cv2.LINE_AA)

        filled = min(len(self.times) / (FS * 6), 1.0)
        cv2.rectangle(frame, (14, h - 24), (14 + int(200 * filled), h - 12),
                      BGR["sage"], -1)
        cv2.rectangle(frame, (14, h - 24), (214, h - 12), (255, 255, 255), 1)
        self.status = ("Measuring…" if filled >= 1 else
                       "Hold still — buffering…")

        if len(self._hr_wave) > 2:
            ww = 240
            wv = self._hr_wave[-ww:]
            wv = (wv - wv.min()) / (np.ptp(wv) + 1e-9)
            xb, yb = w - ww - 20, 110
            for i in range(1, len(wv)):
                cv2.line(frame, (xb + i - 1, int(yb - wv[i-1] * 34)),
                         (xb + i, int(yb - wv[i] * 34)), BGR["pink"], 1,
                         cv2.LINE_AA)

    def close(self):
        if self._face is not None:
            self._face.close()
