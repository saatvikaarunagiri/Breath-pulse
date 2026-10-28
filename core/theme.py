"""
Pastel "soft" theme for the Tkinter UI.

One palette, used everywhere, so both apps look like one cohesive thing.
Edit PALETTE to re-skin the whole app.
"""

# tkinter is imported lazily inside the functions that need it, so the colour
# constants below can be used by the OpenCV HUD even where Tk isn't installed.

# Warm off-white / beige background with a soft pastel accent set.
PALETTE = {
    "bg":        "#FBF7F4",   # warm off-white (main background)
    "surface":   "#FFFFFF",   # cards / panels
    "surface_2": "#F3ECE6",   # subtle raised areas
    "text":      "#5A5056",   # muted plum-grey (primary text)
    "text_soft": "#9A8F94",   # secondary text
    "pink":      "#E8B4B8",   # dusty rose (primary accent)
    "pink_dk":   "#D99AA0",   # pressed/hover rose
    "sage":      "#A9C5A0",   # sage green (confirm / healthy)
    "lavender":  "#C9B6E4",   # lavender (secondary accent)
    "butter":    "#F3D9A4",   # soft butter (warnings, gentle)
    "coral":     "#E6A4A4",   # muted coral (deny / stop)
    "line":      "#EADFD8",   # hairline borders
}

# OpenCV draws in BGR; expose the accents in BGR too for the camera HUD.
def _hex_to_bgr(h):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (b, g, r)

BGR = {k: _hex_to_bgr(v) for k, v in PALETTE.items()}

# Preferred fonts, in order; the first one installed wins.
_FONT_PREFS = ["Avenir Next", "Avenir", "Segoe UI", "Nunito",
               "Helvetica Neue", "Helvetica", "Arial"]


def pick_font(root):
    from tkinter import font as tkfont
    available = set(tkfont.families(root))
    for name in _FONT_PREFS:
        if name in available:
            return name
    return "TkDefaultFont"


def apply(root):
    """Apply the theme to a Tk root and return (font_family, PALETTE)."""
    import tkinter as tk
    from tkinter import ttk
    fam = pick_font(root)
    root.configure(bg=PALETTE["bg"])

    style = ttk.Style(root)
    try:
        style.theme_use("clam")          # the most restyle-able built-in theme
    except tk.TclError:
        pass

    style.configure(".", background=PALETTE["bg"], foreground=PALETTE["text"],
                    font=(fam, 12))
    style.configure("TFrame", background=PALETTE["bg"])
    style.configure("Card.TFrame", background=PALETTE["surface"])
    style.configure("TLabel", background=PALETTE["bg"], foreground=PALETTE["text"])
    style.configure("Card.TLabel", background=PALETTE["surface"],
                    foreground=PALETTE["text"])
    style.configure("Title.TLabel", font=(fam, 20, "bold"),
                    foreground=PALETTE["text"])
    style.configure("Soft.TLabel", foreground=PALETTE["text_soft"])

    # Rounded-ish flat buttons via clam
    for name, color, pressed in [
        ("Primary.TButton", PALETTE["pink"], PALETTE["pink_dk"]),
        ("Sage.TButton",    PALETTE["sage"], "#95B38B"),
        ("Lav.TButton",     PALETTE["lavender"], "#B59FD6"),
        ("Deny.TButton",    PALETTE["coral"], "#D68F8F"),
    ]:
        style.configure(name, background=color, foreground="#4A4047",
                        font=(fam, 12, "bold"), borderwidth=0, focusthickness=0,
                        padding=(16, 10))
        style.map(name, background=[("active", pressed), ("pressed", pressed)])

    style.configure("TCheckbutton", background=PALETTE["bg"],
                    foreground=PALETTE["text"])
    style.map("TCheckbutton", background=[("active", PALETTE["bg"])])
    return fam, PALETTE
