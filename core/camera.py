"""
Background camera thread.

Reads frames, hands each one to an app-supplied processor callback (which does
the MediaPipe work and draws the HUD), and keeps the latest annotated frame
available for the UI to display. Keeps heavy work off the Tkinter main thread.
"""

import threading

import cv2


def open_capture(index=0):
    """Open the webcam, trying the macOS backend first, then the default."""
    for args in ((index, cv2.CAP_AVFOUNDATION), (index,)):
        cap = cv2.VideoCapture(*args)
        if cap.isOpened():
            return cap
    return None


class CameraThread(threading.Thread):
    def __init__(self, processor, index=0):
        super().__init__(daemon=True)
        self.processor = processor          # fn(frame_bgr) -> annotated_bgr
        self.index = index
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._latest = None
        self.ok = True
        self.error = None

    def run(self):
        cap = open_capture(self.index)
        if cap is None:
            self.ok = False
            self.error = "Could not open the webcam."
            return
        while not self._stop.is_set():
            ret, frame = cap.read()
            if not ret:
                continue
            frame = cv2.flip(frame, 1)      # selfie view
            try:
                annotated = self.processor(frame)
            except Exception:
                annotated = frame
            with self._lock:
                self._latest = annotated
        cap.release()

    def latest(self):
        with self._lock:
            return None if self._latest is None else self._latest.copy()

    def stop(self):
        self._stop.set()
