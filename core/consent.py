"""
Startup consent gate.

Shows a pastel modal dialog explaining exactly what the app accesses and how
data is handled, with the three choices the project requires:
    • Always allow   (remembered, skipped next time)
    • Allow once     (asked again next launch)
    • Deny           (app does not start)

Microphone is optional (a checkbox): the camera is required to run, the mic is
only used for voice narration / the assistant, and the app runs fine without it.

NOTE: This is an informed-consent + data-handling layer. Your operating system
still shows its OWN camera/microphone permission prompt the first time, and the
hardware stays blocked until you allow it there too.
"""

import tkinter as tk
from tkinter import ttk

from . import theme
from . import storage

_CONSENT_TEXT = (
    "This app uses your devices only while it is open, and only on this "
    "computer. Nothing is recorded, uploaded, or sent anywhere. You choose at "
    "the end what (if anything) is saved to your own machine."
)


def ensure_consent(store: storage.Store, app_name: str, uses_mic=True):
    """Return a consent dict, or None if the user denied / closed the dialog.

    dict = {"action": "always"|"once", "camera": True, "mic": bool}
    If a remembered 'always' consent exists, returns it without showing UI.
    """
    remembered = store.load_consent()
    if remembered and remembered.get("action") == "always" and remembered.get("camera"):
        return remembered

    result = {"value": None}

    root = tk.Tk()
    root.title(f"{app_name} — Permissions")
    fam, pal = theme.apply(root)
    root.resizable(False, False)

    wrap = ttk.Frame(root, padding=28, style="TFrame")
    wrap.grid()

    ttk.Label(wrap, text="🤍  Your privacy comes first",
              style="Title.TLabel").grid(sticky="w")
    ttk.Label(wrap, text=f"{app_name} would like to use:",
              style="Soft.TLabel").grid(sticky="w", pady=(10, 6))

    cam_var = tk.BooleanVar(value=True)
    mic_var = tk.BooleanVar(value=uses_mic)

    cam = ttk.Checkbutton(wrap, text="📷  Camera  (required)", variable=cam_var,
                          state="disabled")
    cam.grid(sticky="w")
    if uses_mic:
        ttk.Checkbutton(wrap, text="🎙️  Microphone  (optional — voice & assistant)",
                        variable=mic_var).grid(sticky="w", pady=(4, 0))

    msg = tk.Message(wrap, text=_CONSENT_TEXT, width=380,
                     bg=pal["bg"], fg=pal["text_soft"], font=(fam, 10))
    msg.grid(sticky="w", pady=(14, 18))

    btns = ttk.Frame(wrap, style="TFrame")
    btns.grid(sticky="e")

    def choose(action):
        if action == "deny":
            result["value"] = None
        else:
            result["value"] = {"action": action, "camera": True,
                               "mic": bool(mic_var.get())}
            if action == "always":
                store.save_consent(result["value"])
        root.destroy()

    ttk.Button(btns, text="Deny", style="Deny.TButton",
               command=lambda: choose("deny")).grid(row=0, column=0, padx=6)
    ttk.Button(btns, text="Allow once", style="Lav.TButton",
               command=lambda: choose("once")).grid(row=0, column=1, padx=6)
    ttk.Button(btns, text="Always allow", style="Sage.TButton",
               command=lambda: choose("always")).grid(row=0, column=2, padx=6)

    root.protocol("WM_DELETE_WINDOW", lambda: choose("deny"))
    root.update_idletasks()
    # center on screen
    w, h = root.winfo_width(), root.winfo_height()
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 3
    root.geometry(f"+{x}+{y}")
    root.mainloop()

    return result["value"]
