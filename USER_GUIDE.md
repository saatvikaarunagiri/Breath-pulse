# Breath & Pulse Cam — User Guide

A friendly, step-by-step guide for **macOS, Windows, and Linux**. If you get stuck
on something this guide doesn't fix, email **saatvika22@outlook.com**.

---

## 1. What you need first

- A computer with a **webcam**.
- **Python 3.10, 3.11, or 3.12.** (Avoid 3.13 for now — some libraries don't have
  installers for it yet.) Check with `python3 --version`.
  - Don't have Python? Get it from https://www.python.org/downloads/ (tick
    *"Add Python to PATH"* on Windows).

## 2. Download the app

**Option A — download the ZIP:** on the GitHub page click the green **Code**
button → **Download ZIP**, then unzip it.

**Option B — git:**
```bash
git clone https://github.com/<your-username>/breath-pulse-cam.git
```

Then open a terminal **inside the unzipped `breath-pulse-cam` folder**:
- **macOS:** right-click the folder → *New Terminal at Folder*.
- **Windows:** open the folder, click the address bar, type `cmd`, press Enter.
- **Linux:** right-click → *Open Terminal Here* (varies by distro).

## 3. Set up (once)

Copy–paste these one block at a time.

**macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Windows**
```bat
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Linux only — one extra package** (the app's windows need it):
```bash
sudo apt install python3-tk        # Debian/Ubuntu
# Fedora: sudo dnf install python3-tkinter   ·   Arch: sudo pacman -S tk
```

## 4. Run it

```bash
python app.py
```

The **permission window** appears first. Choose **Always allow**, **Allow once**,
or **Deny** (Deny closes the app). The microphone is optional — untick it if you
don't want voice.

> **First run on macOS:** your Mac will *also* pop its own "allow camera/
> microphone?" box. You must click **OK** there — the app can't see the camera
> until you do. If you miss it: System Settings → Privacy & Security → Camera (and
> Microphone) → turn on your Terminal / IDE, then fully quit and reopen it.

## Using Breath & Pulse Cam

1. Sit still and face the camera with **steady, even light** on your face.
2. Wait ~6 s for the buffer bar to fill — then **HR** and **RR** appear with a live
   pulse waveform and an *ok / weak* confidence tag.
3. Click **Save readings** to export a `vitals_log.csv` of your numbers over time.
4. Ask **Buddy** (type or speak) if a reading looks off or you need tips.

Reminder: this is a demo, **not a medical device** — validate against a smartwatch
or a finger on your wrist.

## 5. Voice features (optional)

Want to talk to the app and have Buddy reply out loud?
```bash
pip install -r requirements-voice.txt
python download_model.py
```
This downloads a small (~40 MB) **offline** voice model once. If it won't run,
voice simply stays off and everything else still works.

## 6. Ending a session & your privacy

When you close the app you're asked **what to keep**, all on your own computer:
- **Save this session only** — keep what you made, forget who you are.
- **Save my identity and this session** — keep both.
- **Save only my identity** — keep your profile for next time, delete this session.
- **Delete everything** — wipe it all from this computer.

Nothing is ever uploaded. No video or audio is recorded.

## 7. Troubleshooting (the five usual suspects)

| Problem | Fix |
| --- | --- |
| **No camera window / "Could not open the webcam"** | A permission block. Allow Camera for your terminal in your OS privacy settings, then **quit and reopen** the terminal and rerun. Close Zoom/FaceTime/Photo Booth if they're holding the camera. |
| **`module 'mediapipe' has no attribute 'solutions'`** | `pip install mediapipe==0.10.14` (already pinned in requirements.txt — this means an older/newer one slipped in). |
| **numpy / "_ARRAY_API" error on import** | `pip install "numpy<2"` |
| **`pip install mediapipe` fails** | You're probably on Python 3.13+. Make the venv with 3.12: `python3.12 -m venv venv` and reinstall. |
| **`ModuleNotFoundError: No module named 'tkinter'` (Linux)** | Install it: `sudo apt install python3-tk` (see step 3). |

Still stuck, or found a bug, or just want to reach out? **saatvika22@outlook.com**


