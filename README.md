# Breath & Pulse Cam 💓🫁

**See your heart rate & breathing from a plain webcam — no contact, no wearable.**

A real-time **computer-vision + signal-processing** app that reads your pulse from
tiny skin-color changes (rPPG) and your breathing from chest motion — plus a
**neural net I trained from scratch** that judges whether a reading is trustworthy.

> ⚠️ Not a medical device — a learning/demo project.

```bash
conda activate breathpulse
pip install -r requirements.txt
python app.py          # sit still, good light, wait ~6s
```

| | |
|---|---|
| 💓 **Heart rate** | forehead/cheek skin color → POS algorithm → FFT |
| 🫁 **Breathing** | chest optical flow → bandpass → FFT |
| 🤖 **ML** | 1-D CNN classifies pulse quality (good / noisy) |
| 🔒 **Private** | on-device only; no video or audio recorded |

**Run with ML:** `python app.py --ml` · **Train the model + full setup:** see **[USER_GUIDE.md](USER_GUIDE.md)**

<sub>Python · PyTorch · MediaPipe · OpenCV · SciPy · MIT License · questions → saatvika22@outlook.com</sub>
