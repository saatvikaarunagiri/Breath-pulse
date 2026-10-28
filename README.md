# Breath and Pulse Cam

**See your heart rate and breathing from a plain webcam, privately, on your own computer!**

Sit still and the app reads your pulse from tiny colour changes in your skin (rPPG) and your breathing from the gentle motion of your chest: no watch, no strap, no contact. Nothing is uploaded, and *you* decide at the end what (if anything) is kept.

> **WARNING: THIS IS NOT A MEDICAL DEVICE** This is a demo project. Do not use it for diagnosis or any health decision.
>
> The in-app permission popup is an **informed-consent layer**, not a replacement for your operating system's own camera/mic permission — your OS still asks separately the first time. See the [User Guide](USER_GUIDE.md).

---

## What it does? 

- **Consent first.** Asks permission on launch (Always / Once / Deny) and explains what's used. Deny = it won't start. Mic is optional.
- **Heart rate (rPPG)** from forehead + cheek skin colour, via the POS algorithm.
- **Respiration rate** from chest motion (optical flow).
- **Live pulse waveform** and a confidence tag (ok / weak).
- **Offline help assistant** ("Buddy") answers questions by voice or text, only about this app, and refuses anything off-topic or unsafe.
- **Your choice at the end.** Save this session only · save identity + session · save only identity · delete everything. "Delete" really deletes, locally.


You collect the dataset, design/train the network, and evaluate with real metrics (accuracy, precision/recall/F1, confusion matrix). Full guide in **[ml/README.md](ml/README.md)**; example outputs in [ml/examples/](ml/examples/).

```bash
pip install -r ml/requirements-ml.txt
python ml/make_synthetic_data.py --per-class 300   #or collect_data.py for real data
python ml/train.py --epochs 30
python ml/evaluate.py
python app.py --ml                                 #use the trained model live
```

Everything else below is the classical signal-processing side of the app.

## How it works?

```
                 ┌─ forehead + cheek skin ─> mean RGB ─▶ POS ─> 0.7–4 Hz ─> FFT ─> Heart rate
webcam -> face ──┤
          mesh   └─ chest motion (optical flow) ─> integrate ─> 0.1–0.5 Hz ─> FFT ─> Respiration
```

Signals are resampled onto a clean 30 Hz grid from real timestamps before the FFT, because webcam frame rate wobbles.

## Quickstart!

```bash
git clone https://github.com/<your-username>/breath-pulse-cam.git
cd breath-pulse-cam
python3 -m venv venv && source venv/bin/activate   #Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Voice is optional: `pip install -r requirements-voice.txt` then `python download_model.py` once.

**Full step by step for macOS / Windows / Linux, including camera permissions and fixes for every common error, is in [USER_GUIDE.md](USER_GUIDE.md).**

## Getting a good reading

Sit still, face the camera, use **steady even light** (daylight or a lamp; avoid
flickering overhead LEDs). Wait ~6 s for the buffer bar, then validate against a
wrist pulse or smartwatch.

## Privacy

- Camera and microphone are used **only while the app is open**.
- **No video or audio is ever recorded or uploaded.** Voice is transcribed on-
  device and discarded immediately. Only the numbers you choose to save are written.

## Known limitations

- Sensitive to motion and lighting; readings degrade if you move or talk.
- rPPG performs differently across skin tones and lighting.
- A 10-second window gives coarse frequency resolution (~a few bpm for HR, and
  respiration lands in ~3/min steps) — fine for a demo, not for clinical precision.

## Contact

Hit a wall you can't solve, or just want to say hi? **saatvika22@outlook.com**

## License

MIT — see [LICENSE](LICENSE). Built with MediaPipe, OpenCV, SciPy, Vosk & pyttsx3.
