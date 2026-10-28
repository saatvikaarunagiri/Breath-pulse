"""
Data collection harness for pulse-quality classification.

Runs the real rPPG pipeline (the same POS extraction the app uses), keeps a
rolling window of the live pulse waveform, and lets you label windows:

    g = save current window as GOOD   (sit still, good even light)
    b = save current window as BAD    (move, talk, or dim/flickering light)
    q = quit

Aim for a few hundred of each. To get BAD samples, deliberately move around,
look away, or dim the lights while recording.

Privacy: saves only the 1-D numeric pulse waveform — never video or images.
Everything stays in ml/data/ on your computer.
"""

import os
import sys
import time
from collections import deque

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from features import FS, WIN_SEC, WINDOW, LABELS           # noqa: E402
from vitals import pos_signal, bandpass, resample_uniform  # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _face():
    import mediapipe as mp
    if not hasattr(mp, "solutions"):
        raise RuntimeError("Install mediapipe==0.10.14 (this build lacks "
                           "the 'solutions' API).")
    return mp.solutions.face_mesh.FaceMesh(
        max_num_faces=1, refine_landmarks=False,
        min_detection_confidence=0.5, min_tracking_confidence=0.5)


def counts():
    out = {}
    for name in LABELS:
        d = os.path.join(DATA_DIR, name)
        out[name] = len(os.listdir(d)) if os.path.isdir(d) else 0
    return out


def main():
    for name in LABELS:
        os.makedirs(os.path.join(DATA_DIR, name), exist_ok=True)

    face = _face()
    cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam (check camera permission).")

    times, R, G, B = [], [], [], []
    t0 = time.time()
    print("g = save GOOD   b = save BAD   q = quit")

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        now = time.time() - t0
        res = face.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        if res.multi_face_landmarks:
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
                    vals.append(frame[ay:by, ax:bx][..., ::-1]
                                .reshape(-1, 3).mean(axis=0))
                    cv2.rectangle(frame, (ax, ay), (bx, by), (160, 197, 169), 1)
            if vals:
                r, g, b = np.mean(vals, axis=0)
                times.append(now); R.append(r); G.append(g); B.append(b)

        # keep ~WIN_SEC seconds
        while times and times[0] < now - WIN_SEC:
            times.pop(0); R.pop(0); G.pop(0); B.pop(0)

        ready = len(times) > FS * (WIN_SEC - 1)
        key = cv2.waitKey(1) & 0xFF
        c = chr(key) if key != 255 else ""

        if c in ("g", "b") and ready:
            rr = resample_uniform(times, R, FS)
            gg = resample_uniform(times, G, FS)
            bb = resample_uniform(times, B, FS)
            if rr is not None and len(rr) > FS * 3:
                pulse = bandpass(pos_signal(np.stack([rr, gg, bb], axis=1)),
                                 FS, 0.7, 4.0)
                label = "good" if c == "g" else "bad"
                fn = os.path.join(DATA_DIR, label, f"{int(time.time()*1000)}.npy")
                np.save(fn, pulse.astype(np.float32))
        elif c == "q":
            break

        cnts = counts()
        cv2.putText(frame, f"good:{cnts['good']}  bad:{cnts['bad']}",
                    (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (90, 80, 86), 2)
        cv2.putText(frame, "g=GOOD  b=BAD  q=quit" + ("" if ready else
                    "   (buffering...)"), (10, h - 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (154, 143, 148), 1)
        cv2.imshow("Pulse-quality data collection", frame)

    cap.release()
    cv2.destroyAllWindows()
    face.close()
    print("Final counts:", counts())


if __name__ == "__main__":
    main()
