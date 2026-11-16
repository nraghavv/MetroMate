"""
theme.py - Colours, fonts and ttk styles shared by every screen.
Owner: Member 1 (UI)
"""
import tkinter as tk
from tkinter import ttk, font as tkfont

# ---------- Colour palette ----------
BG = "#F4F6FB"          # app background
CARD = "#FFFFFF"        # card background
BORDER = "#E3E7EF"      # card border
SIDEBAR = "#13293D"     # sidebar background
SIDEBAR_HOVER = "#1D3A54"
SIDEBAR_ACTIVE = "#0E9F8E"
ACCENT = "#0E9F8E"      # primary teal (MetroMate accent)
ACCENT_DARK = "#0B7F72"
TEXT = "#1F2937"
MUTED = "#6B7280"
GREEN = "#22A06B"
AMBER = "#E8A33D"
RED = "#E5484D"
TEAL_SOFT = "#E1F4F1"

FONT = "Helvetica"      # replaced at start-up by pick_font()


def pick_font(root):
    """Choose the nicest font that exists on this computer."""
    global FONT
    families = set(tkfont.families(root))
    for name in ("Segoe UI", "Inter", "SF Pro Text", "Helvetica Neue", "Ubuntu", "DejaVu Sans"):
        if name in families:
            FONT = name
            break
    return FONT


def f(size=10, weight="normal"):
    """Shorthand for a font tuple."""
    return (FONT, size, weight)


BLUE_LINE = "#1E6FD9"    # Chennai Metro Blue Line
GREEN_LINE = "#1FA34A"   # Chennai Metro Green Line
LINE_COLOURS = {"Blue": BLUE_LINE, "Green": GREEN_LINE}


def setup_styles(root):
    pick_font(root)
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".", font=f(10), background=BG, foreground=TEXT)
    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=CARD)
    style.configure("TLabel", background=CARD, foreground=TEXT, font=f(10))
    style.configure("TCheckbutton", background=CARD, font=f(10))
    style.map("TCheckbutton", background=[("active", CARD)])

    # Buttons
    style.configure("Accent.TButton", background=ACCENT, foreground="white",
                    font=f(10, "bold"), borderwidth=0, padding=(14, 7))
    style.map("Accent.TButton", background=[("active", ACCENT_DARK), ("disabled", "#9ED8CF")])
    style.configure("Soft.TButton", background="#E1F4F1", foreground=ACCENT,
                    font=f(10, "bold"), borderwidth=0, padding=(12, 7))
    style.map("Soft.TButton", background=[("active", "#CDEDE8")])
    style.configure("Danger.TButton", background="#FDECEC", foreground=RED,
                    font=f(10, "bold"), borderwidth=0, padding=(12, 7))
    style.map("Danger.TButton", background=[("active", "#FAD9D9")])

    # Inputs
    for w in ("TEntry", "TSpinbox", "TCombobox"):
        style.configure(w, fieldbackground="white", bordercolor=BORDER,
                        lightcolor=BORDER, darkcolor=BORDER, padding=5)

    # Tables
    style.configure("Treeview", background="white", fieldbackground="white",
                    rowheight=28, font=f(10), bordercolor=BORDER, borderwidth=0)
    style.configure("Treeview.Heading", background="#EEF1F8", foreground=MUTED,
                    font=f(9, "bold"), relief="flat", padding=6)
    style.map("Treeview", background=[("selected", "#D3F0EB")],
              foreground=[("selected", TEXT)])
    style.map("Treeview.Heading", background=[("active", "#E3E8F5")])

    # Progress bars
    style.configure("Accent.Horizontal.TProgressbar", troughcolor="#E8ECF4",
                    background=ACCENT, bordercolor="#E8ECF4",
                    lightcolor=ACCENT, darkcolor=ACCENT, thickness=10)
    style.configure("Green.Horizontal.TProgressbar", troughcolor="#E8ECF4",
                    background=GREEN, bordercolor="#E8ECF4",
                    lightcolor=GREEN, darkcolor=GREEN, thickness=10)
    return style


class Card(tk.Frame):
    """A white rounded-looking panel with a thin border and optional title."""

    def __init__(self, parent, title=None, padx=16, pady=14, **kw):
        super().__init__(parent, bg=CARD, highlightthickness=1,
                         highlightbackground=BORDER, highlightcolor=BORDER, **kw)
        self.body = tk.Frame(self, bg=CARD)
        self.body.pack(fill="both", expand=True, padx=padx, pady=pady)
        if title:
            tk.Label(self.body, text=title, bg=CARD, fg=TEXT,
                     font=f(12, "bold")).pack(anchor="w", pady=(0, 8))
