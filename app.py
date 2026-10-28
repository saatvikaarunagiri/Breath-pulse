"""
Breath & Pulse Cam — contactless heart-rate & respiration, pastel desktop app
with consent gating, offline voice assistant, and local-only session storage.

NOT a medical device. Run:  python app.py
"""

import os
import sys
import tkinter as tk
from tkinter import ttk

import cv2
from PIL import Image, ImageTk

from core import consent, storage, session_end, theme
from core.camera import CameraThread
from core.voice import Listener, Speaker
from core.assistant import Assistant
from faq import FAQ
from vitals import VitalsProcessor

APP_ID = "breath_pulse_cam"
APP_NAME = "Breath & Pulse Cam"
VIDEO_W = 640
QUESTION_CUES = ("?", "how ", "what ", "why ", "buddy", "help", "hey")


def load_classifier():
    """Try to load the trained pulse-quality model from ml/. Returns a
    classifier or None; never raises."""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "ml"))
        from signal_classifier import SignalClassifier
        c = SignalClassifier()
        return c if c.available else None
    except Exception:
        return None


class App:
    def __init__(self, root, store, consent_rec, use_ml=False):
        self.root = root
        self.store = store
        self.mic_on = bool(consent_rec.get("mic"))
        self.session_dir = store.new_session_dir()

        classifier = load_classifier() if use_ml else None
        profile = store.load_profile()
        self.proc = VitalsProcessor(profile=profile, classifier=classifier)
        self.assistant = Assistant(FAQ)
        self.speaker = Speaker()

        self.fam, self.pal = theme.apply(root)
        root.title(APP_NAME)
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, minsize=320)
        root.rowconfigure(0, weight=1)

        left = ttk.Frame(root, padding=14, style="TFrame")
        left.grid(row=0, column=0, sticky="nsew")
        self.video = tk.Label(left, bg=self.pal["surface_2"], bd=0)
        self.video.pack()

        self._build_sidebar(root)

        self.cam = CameraThread(self.proc.process)
        self.cam.start()

        self.listener = None
        if self.mic_on:
            self.listener = Listener(self._on_voice_text)
            self.listener.start()

        base = profile.get("resting_hr") if profile else None
        hello = "Hi! 🤍 Sit still and face the camera. Ask me anything."
        if base:
            hello += f"  (last baseline: {base} bpm)"
        self._log("Buddy", hello)
        root.protocol("WM_DELETE_WINDOW", self.end_session)
        self._tick()

    def _build_sidebar(self, root):
        pal, fam = self.pal, self.fam
        side = ttk.Frame(root, padding=(16, 14), style="TFrame")
        side.grid(row=0, column=1, sticky="nsew")
        side.rowconfigure(6, weight=1)

        ttk.Label(side, text=APP_NAME, style="Title.TLabel").grid(sticky="w")
        ttk.Label(side, text="not a medical device · learning demo",
                  style="Soft.TLabel").grid(sticky="w", pady=(0, 2))
        self.status = ttk.Label(side, text="Starting…", style="Soft.TLabel",
                                wraplength=290)
        self.status.grid(sticky="w", pady=(6, 12))

        row = ttk.Frame(side, style="TFrame"); row.grid(sticky="ew")
        ttk.Button(row, text="Save readings", style="Sage.TButton",
                   command=self.save).grid(row=0, column=0, padx=3)
        ttk.Button(row, text="End session", style="Deny.TButton",
                   command=self.end_session).grid(row=0, column=1, padx=3)

        mic_txt = "🎙️ voice on" if self.mic_on else "🎙️ voice off (mic not allowed)"
        ttk.Label(side, text=mic_txt, style="Soft.TLabel").grid(
            sticky="w", pady=(10, 4))

        ttk.Label(side, text="Ask Buddy", style="Card.TLabel").grid(
            sticky="w", pady=(8, 2))
        self.chat = tk.Text(side, height=13, width=34, wrap="word", bd=0,
                            bg=pal["surface"], fg=pal["text"], font=(fam, 10),
                            padx=10, pady=8, highlightthickness=1,
                            highlightbackground=pal["line"], state="disabled")
        self.chat.grid(sticky="nsew", pady=(0, 6))

        er = ttk.Frame(side, style="TFrame"); er.grid(sticky="ew")
        er.columnconfigure(0, weight=1)
        self.entry = tk.Entry(er, bd=0, bg=pal["surface_2"], fg=pal["text"],
                              font=(fam, 11), highlightthickness=1,
                              highlightbackground=pal["line"])
        self.entry.grid(row=0, column=0, sticky="ew", ipady=6, padx=(0, 6))
        self.entry.bind("<Return>", lambda e: self._send_typed())
        ttk.Button(er, text="Send", style="Primary.TButton",
                   command=self._send_typed).grid(row=0, column=1)

    def _tick(self):
        if not self.cam.ok:
            self.status.config(text=self.cam.error or "Camera error")
        frame = self.cam.latest()
        if frame is not None:
            h, w = frame.shape[:2]
            disp = cv2.resize(frame, (VIDEO_W, int(VIDEO_W * h / w)))
            self._imgtk = ImageTk.PhotoImage(
                Image.fromarray(cv2.cvtColor(disp, cv2.COLOR_BGR2RGB)))
            self.video.config(image=self._imgtk)
            self.status.config(text=self.proc.status)
        self.root.after(33, self._tick)

    def _log(self, sender, text):
        self.chat.config(state="normal")
        tag = "me" if sender == "You" else "bot"
        self.chat.insert("end", f"{sender}: ", (tag,))
        self.chat.insert("end", text + "\n\n")
        self.chat.tag_config("me", foreground=self.pal["pink_dk"],
                             font=(self.fam, 10, "bold"))
        self.chat.tag_config("bot", foreground=self.pal["lavender"],
                             font=(self.fam, 10, "bold"))
        self.chat.see("end")
        self.chat.config(state="disabled")

    def _send_typed(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, "end")
        self._ask(text, speak=False)

    def _ask(self, text, speak):
        self._log("You", text)
        reply = self.assistant.reply(text)
        self._log("Buddy", reply)
        if speak:
            self.speaker.say(reply)

    def _on_voice_text(self, text):
        self.root.after(0, lambda: self._handle_voice(text))

    def _handle_voice(self, text):
        if any(cue in text.lower() for cue in QUESTION_CUES):
            self._ask(text, speak=True)

    def save(self):
        if not self.proc.log:
            self.status.config(text="No readings yet — wait for a measurement")
            return
        out = os.path.join(self.session_dir, "vitals_log.csv")
        n = self.proc.save_log(out)
        self.status.config(text=f"Saved {n} readings ✓")
        self._log("Buddy", f"Saved {n} readings to this session. 🤍")

    def end_session(self):
        self.cam.stop()
        if self.listener:
            self.listener.stop()
        self.speaker.stop()
        self.proc.close()
        self.root.destroy()
        choice = session_end.ask(APP_NAME)
        summary = self.store.apply_choice(
            choice, profile=self.proc.session_profile(),
            session_dir=self.session_dir)
        print(summary)


def main():
    import argparse
    ap = argparse.ArgumentParser(description=APP_NAME)
    ap.add_argument("--ml", action="store_true",
                    help="use the trained pulse-quality classifier (ml/) for the "
                         "good/bad verdict; falls back to the threshold if no model")
    args = ap.parse_args()

    store = storage.Store(APP_ID)
    rec = consent.ensure_consent(store, APP_NAME, uses_mic=True)
    if not rec:
        print("No permission given — Breath & Pulse Cam will not start.")
        sys.exit(0)
    root = tk.Tk()
    App(root, store, rec, use_ml=args.ml)
    root.mainloop()


if __name__ == "__main__":
    main()
