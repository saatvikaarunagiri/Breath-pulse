# Breath & Pulse Cam — User Guide & Manual

Step by step for **macOS, Windows, and Linux**. Not a medical device — a
learning/demo project. Stuck? → **saatvika22@outlook.com**

---

## Contents
1. [What you need](#1-what-you-need)
2. [Install](#2-install)
3. [Run the app](#3-run-the-app)
4. [Getting a good reading](#4-getting-a-good-reading)
5. [The ML model — train your own](#5-the-ml-model)
6. [Privacy](#6-privacy)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. What you need
- A computer with a **webcam**.
- **Python 3.10–3.12** (NOT 3.13 — mediapipe has no 3.13 build). Check: `python --version`.

## 2. Install

**Recommended — one conda environment (Python 3.12):**
```bash
conda create -n breathpulse python=3.12 -y
conda activate breathpulse

cd "/path/to/breath-pulse-cam"
pip install -r requirements.txt            # core app
pip install -r ml/requirements-ml.txt      # ML (PyTorch etc.)
```

Verify:
```bash
python -c "import cv2, mediapipe as mp; print('cv2 ok | solutions:', hasattr(mp,'solutions'))"
# want:  cv2 ok | solutions: True
```

**Linux only:** `sudo apt install python3-tk` (Fedora: `python3-tkinter` · Arch: `tk`).
**Voice (optional):** `pip install -r requirements-voice.txt` then `python download_model.py`.

> ⚠️ **One environment, always.** `conda activate breathpulse` every time. Mixing a
> `venv` and conda causes most "ModuleNotFoundError" issues.

## 3. Run the app
```bash
conda activate breathpulse
python app.py
```
Permission window first (**Always / Once / Deny**). Mic optional.

| Command | Mode |
|---|---|
| `python app.py` | Heart rate + breathing (confidence via threshold) |
| `python app.py --ml` | Learned good/bad verdict from the trained model |

> **First launch (macOS):** approve the Mac's own camera prompt. Missed it?
> System Settings → Privacy & Security → Camera → enable Terminal, then reopen it.

## 4. Getting a good reading
- Sit still, face the camera, keep upper chest in frame.
- **Steady, even light** on your face (daylight or a lamp). Avoid flickering
  overhead LEDs — they add noise.
- Wait ~6 s for the buffer bar, then read **HR**, **RR**, and the live pulse wave.
- Validate against a wrist pulse or smartwatch. The tag shows `ok`/`weak`
  (or the learned `good`/`bad` verdict with `--ml`).
- **Save readings** writes a `vitals_log.csv` to your session folder.

## 5. The ML model
Trains a neural net on pulse data **you collect** (`ml/requirements-ml.txt`, runs
on Apple-Silicon GPU automatically).

```bash
# 1) collect: sit still + good light = GOOD; move/talk/dim lights = BAD
python ml/collect_data.py          # g = save GOOD   b = save BAD   q = quit
#    aim for a few hundred of each
# 2) train            3) evaluate
python ml/train.py --epochs 30
python ml/evaluate.py              # accuracy + confusion matrix
# 4) use it live
python app.py --ml
```
*(Dry run without a webcam: `python ml/make_synthetic_data.py --per-class 300`,
then train/evaluate. Real data is needed for real use.)*

Details: [ml/README.md](ml/README.md).

## 6. Privacy
On-device only. **No video or audio is recorded or uploaded** — the pulse signal
is computed live and discarded; only the numbers you choose to save are written.
At the end you pick what to keep (session / identity / both / delete everything).

## 7. Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'cv2'` | Wrong env. `conda activate breathpulse`, then `pip install -r requirements.txt`. |
| `mediapipe ... has no attribute 'solutions'` | Python 3.13 — use the 3.12 conda env in [Install](#2-install). |
| No camera window / can't open webcam | Allow Camera for Terminal in OS settings; quit & reopen Terminal; close other camera apps. |
| numpy `_ARRAY_API` error | `pip install "numpy<2"` |
| `No module named 'tkinter'` (Linux) | `sudo apt install python3-tk` |
| HR reads "weak" / jumps around | More light, less motion, no flickering bulbs. Give it ~10 s to settle. |
| `--ml` does nothing | Train the model first — see [section 5](#5-the-ml-model). |

Still stuck, or found a bug? → **saatvika22@outlook.com**
