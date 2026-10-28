# Breath and Pulse Cam

**See your heart rate & breathing from a plain webcam - no contact, no wearable.**

A real-time **computer-vision + signal-processing** app that reads your pulse from
tiny skin-color changes (rPPG) and your breathing from chest motion, plus a
**neural net I trained from scratch** that judges whether a reading is trustworthy.

> WARNING: THIS IS NOT A MEDICAL DEVICE This is a demo project. Do not use it for diagnosis or any health decision.

```bash
conda activate breathpulse
pip install -r requirements.txt
python app.py        
```

| | |
|---|---|
| **Heart rate** | forehead/cheek skin color → POS algorithm → FFT |
| **Breathing** | chest optical flow → bandpass → FFT |
| **ML** | 1-D CNN classifies pulse quality (good / noisy) |
| **Private** | on-device only; no video or audio recorded |

**Run with ML:** `python app.py --ml` · **Train the model + full setup:** see **[USER_GUIDE.md](USER_GUIDE.md)**

<sub>Python | PyTorch | MediaPipe | OpenCV | SciPy | MIT License | questions -> saatvika22@outlook.com</sub>
