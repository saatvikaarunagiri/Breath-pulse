"""
End-of-session privacy dialog.

Presents the four choices the project requires and returns the matching
storage.* constant. The caller then runs store.apply_choice(...), which actually
performs the keep/delete.
"""

import tkinter as tk
from tkinter import ttk

from . import theme
from . import storage

_OPTIONS = [
    ("Save this session only",
     "Keep what you made this time. Forget who you are (no identity kept).",
     storage.SAVE_SESSION_ONLY, "Lav.TButton"),
    ("Save my identity and this session",
     "Keep your profile (for faster setup next time) and this session's files.",
     storage.SAVE_BOTH, "Sage.TButton"),
    ("Save only my identity",
     "Keep your profile for next time, but delete this session's files.",
     storage.SAVE_IDENTITY_ONLY, "Primary.TButton"),
    ("Delete everything",
     "Wipe this session and your identity from this computer completely.",
     storage.DELETE_ALL, "Deny.TButton"),
]


def ask(app_name):
    """Show the dialog and return a storage.* choice constant (default DELETE_ALL
    if the window is closed, i.e. the most privacy-preserving option)."""
    result = {"value": storage.DELETE_ALL}

    root = tk.Tk()
    root.title(f"{app_name} — Before you go")
    fam, pal = theme.apply(root)
    root.resizable(False, False)

    wrap = ttk.Frame(root, padding=28, style="TFrame")
    wrap.grid()
    ttk.Label(wrap, text="What should we keep?",
              style="Title.TLabel").grid(sticky="w")
    ttk.Label(wrap, text="Everything stays on this computer, always.",
              style="Soft.TLabel").grid(sticky="w", pady=(6, 16))

    def choose(value):
        result["value"] = value
        root.destroy()

    for i, (title, desc, value, style_name) in enumerate(_OPTIONS):
        card = tk.Frame(wrap, bg=pal["surface"], highlightbackground=pal["line"],
                        highlightthickness=1)
        card.grid(sticky="ew", pady=5, ipady=4)
        card.columnconfigure(0, weight=1)
        tk.Label(card, text=title, bg=pal["surface"], fg=pal["text"],
                 font=(fam, 13, "bold"), anchor="w").grid(
            row=0, column=0, sticky="w", padx=12, pady=(8, 0))
        tk.Label(card, text=desc, bg=pal["surface"], fg=pal["text_soft"],
                 font=(fam, 10), anchor="w", justify="left",
                 wraplength=360).grid(row=1, column=0, sticky="w",
                                      padx=12, pady=(0, 8))
        ttk.Button(card, text="Choose", style=style_name,
                   command=lambda v=value: choose(v)).grid(
            row=0, column=1, rowspan=2, padx=12)

    root.protocol("WM_DELETE_WINDOW", lambda: choose(storage.DELETE_ALL))
    root.update_idletasks()
    w, h = root.winfo_width(), root.winfo_height()
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 3
    root.geometry(f"+{x}+{y}")
    root.mainloop()
    return result["value"]
