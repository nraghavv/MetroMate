"""
MetroMate - Chennai Metro Route Planner
A Tkinter desktop application.

Run:   python main.py

Owner of this file: Member 1 (UI) - main window, sidebar navigation, notifications.
"""
import tkinter as tk

import theme
from theme import SIDEBAR, SIDEBAR_HOVER, SIDEBAR_ACTIVE, BG, f
from database import Database
from screens import PlannerScreen, StationsScreen, SavedScreen, FareScreen

NAV = [
    ("planner", "Plan a Trip", PlannerScreen),
    ("stations", "Stations", StationsScreen),
    ("saved", "Saved & History", SavedScreen),
    ("fares", "Fares & Timings", FareScreen),
]


class App(tk.Tk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.title("MetroMate - Chennai Metro Route Planner")
        self.geometry("1300x800")
        self.minsize(1220, 760)
        self.configure(bg=BG)
        style = theme.setup_styles(self)
        style.configure("TRadiobutton", background=theme.CARD, font=f(10))
        style.map("TRadiobutton", background=[("active", theme.CARD)])

        side = tk.Frame(self, bg=SIDEBAR, width=210)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        logo = tk.Frame(side, bg=SIDEBAR)
        logo.pack(fill="x", padx=20, pady=(24, 4))
        tk.Label(logo, text="Metro", bg=SIDEBAR, fg="white", font=f(19, "bold")).pack(side="left")
        tk.Label(logo, text="Mate", bg=SIDEBAR, fg="#5EE0CC", font=f(19, "bold")).pack(side="left")
        tk.Label(side, text="Chennai Metro route planner", bg=SIDEBAR, fg="#8FA3B8",
                 font=f(9)).pack(anchor="w", padx=20, pady=(0, 24))

        self.nav_btns = {}
        for key, label, _ in NAV:
            b = tk.Label(side, text="   " + label, bg=SIDEBAR, fg="#C9D4E2", font=f(11),
                         anchor="w", padx=14, pady=10, cursor="hand2")
            b.pack(fill="x", padx=12, pady=2)
            b.bind("<Button-1>", lambda e, k=key: self.show(k))
            b.bind("<Enter>", lambda e, k=key: self._hover(k, True))
            b.bind("<Leave>", lambda e, k=key: self._hover(k, False))
            self.nav_btns[key] = b

        lines = tk.Frame(side, bg=SIDEBAR)
        lines.pack(side="bottom", fill="x", padx=20, pady=(0, 18))
        for name, col, txt in (("Blue Line", theme.BLUE_LINE, "Wimco Nagar - Airport"),
                               ("Green Line", theme.GREEN_LINE, "Central - St. Thomas Mount")):
            row = tk.Frame(lines, bg=SIDEBAR)
            row.pack(fill="x", pady=3)
            tk.Frame(row, bg=col, width=4, height=30).pack(side="left", padx=(0, 8))
            t = tk.Frame(row, bg=SIDEBAR)
            t.pack(side="left")
            tk.Label(t, text=name, bg=SIDEBAR, fg="white", font=f(9, "bold")).pack(anchor="w")
            tk.Label(t, text=txt, bg=SIDEBAR, fg="#8FA3B8", font=f(8)).pack(anchor="w")
        self.toast = tk.Label(side, text="", bg=SIDEBAR, fg="#5EE0CC", font=f(9),
                              wraplength=180, justify="left")
        self.toast.pack(side="bottom", fill="x", padx=20, pady=(0, 14))
        self._toast_job = None

        container = tk.Frame(self, bg=BG)
        container.pack(side="left", fill="both", expand=True)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        self.screens = {}
        self.current = None
        for key, _, cls in NAV:
            scr = cls(container, self)
            scr.grid(row=0, column=0, sticky="nsew")
            self.screens[key] = scr
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.show("planner")

    def show(self, key):
        self.current = key
        for k, b in self.nav_btns.items():
            active = k == key
            b.config(bg=SIDEBAR_ACTIVE if active else SIDEBAR, fg="white" if active else "#C9D4E2",
                     font=f(11, "bold") if active else f(11))
        self.screens[key].tkraise()
        self.screens[key].on_show()

    def _hover(self, key, inside):
        if key != self.current:
            self.nav_btns[key].config(bg=SIDEBAR_HOVER if inside else SIDEBAR)

    def notify(self, message):
        self.toast.config(text="• " + message)
        if self._toast_job:
            self.after_cancel(self._toast_job)
        self._toast_job = self.after(4000, lambda: self.toast.config(text=""))

    def on_close(self):
        self.db.conn.close()
        self.destroy()


def main():
    App(Database()).mainloop()


if __name__ == "__main__":
    main()
