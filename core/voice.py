"""
Optional, fully-offline voice input/output.

  • Speech-to-text: Vosk (a small local model, no internet, nothing uploaded).
  • Text-to-speech:  pyttsx3 (uses your OS's built-in voices, also offline).

Everything here is best-effort. If the packages aren't installed, the mic isn't
available, or the Vosk model folder is missing, the feature simply switches off
and the rest of the app keeps working. Nothing is ever recorded to disk.
"""

import os
import queue
import threading

# Where the user unzips the Vosk model (see USER_GUIDE.md).
DEFAULT_MODEL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models", "vosk-model-small-en-us")


class Speaker:
    """Text-to-speech on a background thread so speaking never blocks the UI."""

    def __init__(self):
        self._q = queue.Queue()
        self.available = False
        self._thread = None
        try:
            import pyttsx3  # noqa: F401
            self.available = True
        except Exception:
            self.available = False
        if self.available:
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def _run(self):
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", 175)
        except Exception:
            self.available = False
            return
        while True:
            text = self._q.get()
            if text is None:
                break
            try:
                engine.say(text)
                engine.runAndWait()
            except Exception:
                pass

    def say(self, text):
        if self.available and text:
            self._q.put(text)

    def stop(self):
        if self.available:
            self._q.put(None)


class Listener(threading.Thread):
    """Continuous offline speech-to-text. Calls on_text(str) for each phrase."""

    def __init__(self, on_text, model_dir=None, samplerate=16000):
        super().__init__(daemon=True)
        self.on_text = on_text
        self.model_dir = model_dir or DEFAULT_MODEL_DIR
        self.samplerate = samplerate
        self._stop = threading.Event()
        self.available = False
        self.status = "off"

    def _check(self):
        try:
            import sounddevice  # noqa: F401
            import vosk          # noqa: F401
        except Exception:
            self.status = "missing packages (vosk, sounddevice)"
            return False
        if not os.path.isdir(self.model_dir):
            self.status = "missing Vosk model folder"
            return False
        return True

    def run(self):
        if not self._check():
            return
        try:
            import json
            import sounddevice as sd
            import vosk

            model = vosk.Model(self.model_dir)
            rec = vosk.KaldiRecognizer(model, self.samplerate)
            self.available = True
            self.status = "listening"
            q = queue.Queue()

            def cb(indata, frames, time_, status):
                q.put(bytes(indata))

            with sd.RawInputStream(samplerate=self.samplerate, blocksize=8000,
                                   dtype="int16", channels=1, callback=cb):
                while not self._stop.is_set():
                    data = q.get()
                    if rec.AcceptWaveform(data):
                        text = json.loads(rec.Result()).get("text", "").strip()
                        if text:
                            self.on_text(text)
        except Exception as e:
            self.available = False
            self.status = f"error: {e}"

    def stop(self):
        self._stop.set()
