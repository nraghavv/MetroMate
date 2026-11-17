"""
screens.py - All four screens of MetroMate.
Owner: Member 1 (UI)  -  PlannerScreen, StationsScreen
       Member 3 (Screens & Testing) -  SavedScreen, FareScreen
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import metro_data as md
import router
from map_view import MetroMap
from theme import (BG, CARD, TEXT, MUTED, ACCENT, GREEN, RED, AMBER, BORDER, TEAL_SOFT,
                   LINE_COLOURS, Card, f)

ARROW = "→"


class Screen(tk.Frame):
    title = ""
    subtitle = ""

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.db = app.db
        head = tk.Frame(self, bg=BG)
        head.pack(fill="x", padx=26, pady=(18, 10))
        tk.Label(head, text=self.title, bg=BG, fg=TEXT, font=f(19, "bold")).pack(anchor="w")
        tk.Label(head, text=self.subtitle, bg=BG, fg=MUTED, font=f(10)).pack(anchor="w")
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(fill="both", expand=True, padx=26, pady=(0, 18))

    def refresh(self):
        pass

    def on_show(self):
        self.refresh()


def line_chip(parent, line, bg=CARD):
    return tk.Label(parent, text=f" {line} Line ", bg=LINE_COLOURS[line], fg="white",
                    font=f(8, "bold"), padx=4, pady=1)


def make_tree(parent, columns, height=10):
    """columns: list of (id, heading, width, anchor, stretch)."""
    frame = tk.Frame(parent, bg=CARD)
    tree = ttk.Treeview(frame, columns=[c[0] for c in columns], show="headings",
                        height=height, selectmode="browse")
    for cid, head, width, anchor, stretch in columns:
        tree.heading(cid, text=head)
        tree.column(cid, width=width, anchor=anchor, stretch=stretch)
    sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)
    return frame, tree


# =====================================================================
#  PLAN A TRIP
# =====================================================================
class PlannerScreen(Screen):
    title = "Plan a Trip"
    subtitle = "Choose where you are and where you're going - MetroMate finds the fastest route."

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.route = None
        self.pick_next = "from"
        names = md.stations()

        self.content.columnconfigure(1, weight=1)
        self.content.rowconfigure(0, weight=1)
        left = tk.Frame(self.content, bg=BG, width=350)
        left.grid(row=0, column=0, sticky="nsw", padx=(0, 14))
        left.grid_propagate(False)
        left.pack_propagate(False)

        # ---------------- journey form
        form = Card(left, title="Your journey", pady=12)
        form.pack(fill="x")
        body = tk.Frame(form.body, bg=CARD)
        body.pack(fill="x")
        body.columnconfigure(0, weight=1)
        self.from_var = tk.StringVar()
        self.to_var = tk.StringVar()
        tk.Label(body, text="From", bg=CARD, fg=MUTED, font=f(9)).grid(row=0, column=0, sticky="w")
        self.from_cb = ttk.Combobox(body, textvariable=self.from_var, values=names, font=f(10))
        self.from_cb.grid(row=1, column=0, sticky="ew")
        ttk.Button(body, text="Swap", style="Soft.TButton", width=6, command=self.swap).grid(
            row=1, column=1, rowspan=3, padx=(8, 0))
        tk.Label(body, text="To", bg=CARD, fg=MUTED, font=f(9)).grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.to_cb = ttk.Combobox(body, textvariable=self.to_var, values=names, font=f(10))
        self.to_cb.grid(row=3, column=0, sticky="ew")
        for cb in (self.from_cb, self.to_cb):
            cb.bind("<KeyRelease>", self._filter)
            cb.bind("<Return>", lambda e: self.find())

        opts = tk.Frame(form.body, bg=CARD)
        opts.pack(fill="x", pady=(10, 0))
        self.ticket = tk.StringVar(value=self.db.get_setting("ticket", "token"))
        ttk.Radiobutton(opts, text="Token", value="token", variable=self.ticket,
                        command=self._ticket_changed).pack(side="left")
        ttk.Radiobutton(opts, text="Card / QR (20% off)", value="card", variable=self.ticket,
                        command=self._ticket_changed).pack(side="left", padx=10)
        pax = tk.Frame(form.body, bg=CARD)
        pax.pack(fill="x", pady=(8, 0))
        tk.Label(pax, text="Passengers", bg=CARD, fg=MUTED, font=f(9)).pack(side="left")
        self.pax = tk.StringVar(value="1")
        ttk.Spinbox(pax, from_=1, to=10, textvariable=self.pax, width=4,
                    command=self._ticket_changed).pack(side="left", padx=8)

        btns = tk.Frame(form.body, bg=CARD)
        btns.pack(fill="x", pady=(12, 0))
        ttk.Button(btns, text="Find route", style="Accent.TButton", command=self.find).pack(
            side="left", fill="x", expand=True)
        ttk.Button(btns, text="Clear", style="Soft.TButton", command=self.clear).pack(side="left", padx=(8, 0))

        # ---------------- result
        self.result = Card(left, pady=12)
        self.result.pack(fill="both", expand=True, pady=(12, 0))
        self.res = self.result.body

        # ---------------- map
        map_card = Card(self.content, padx=6, pady=6)
        map_card.grid(row=0, column=1, sticky="nsew")
        self.map = MetroMap(map_card.body, on_station_click=self.map_click)
        self.map.pack(expand=True)
        self.show_empty()

    # ------------------------------------------------------------ helpers
    def _filter(self, event):
        if event.keysym in ("Return", "Up", "Down", "Escape", "Tab"):
            return
        cb = event.widget
        text = cb.get().strip().lower()
        cb["values"] = [s for s in md.stations() if text in s.lower()] or md.stations()

    def _ticket_changed(self):
        self.db.set_setting("ticket", self.ticket.get())
        if self.route:
            self.show_result(self.route)

    def _passengers(self):
        try:
            return max(1, min(10, int(self.pax.get())))
        except ValueError:
            return 1

    def swap(self):
        a, b = self.from_var.get(), self.to_var.get()
        self.from_var.set(b)
        self.to_var.set(a)
        if a and b:
            self.find()

    def map_click(self, name):
        if self.pick_next == "from" or not self.from_var.get():
            self.from_var.set(name)
            self.to_var.set("")
            self.pick_next = "to"
            self.route = None
            self.map.clear()
            self.show_empty(f"Start: {name}. Now click your destination.")
        else:
            if name == self.from_var.get():
                return
            self.to_var.set(name)
            self.pick_next = "from"
            self.find()

    def set_route(self, start, end):
        """Used by other screens (Stations, Saved) to open a route here."""
        self.app.show("planner")
        self.from_var.set(start)
        self.to_var.set(end)
        self.find()

    def set_station(self, which, name):
        self.app.show("planner")
        (self.from_var if which == "from" else self.to_var).set(name)
        if self.from_var.get() and self.to_var.get() and self.from_var.get() != self.to_var.get():
            self.find()

    # ------------------------------------------------------------ actions
    def find(self):
        start, end = self.from_var.get().strip(), self.to_var.get().strip()
        names = md.stations()
        match = lambda t: next((s for s in names if s.lower() == t.lower()), None)
        start, end = match(start), match(end)
        if not start or not end:
            messagebox.showwarning("Choose stations", "Please pick both stations from the list.")
            return
        if start == end:
            messagebox.showwarning("Same station", "Start and destination are the same station.")
            return
        self.from_var.set(start)
        self.to_var.set(end)
        self.route = router.find_route(start, end)
        self.db.add_history(start, end, self.route["minutes"], self.route["fare"])
        self.map.highlight(self.route)
        self.show_result(self.route)

    def clear(self):
        self.from_var.set("")
        self.to_var.set("")
        self.route = None
        self.pick_next = "from"
        self.map.clear()
        self.show_empty()

    def save(self):
        if not self.route:
            return
        name = simpledialog.askstring("Save route", "Give this route a name:",
                                      initialvalue=f"{self.route['from']} {ARROW} {self.route['to']}",
                                      parent=self)
        if not name:
            return
        if self.db.add_favourite(name.strip(), self.route["from"], self.route["to"]):
            self.app.notify(f"Saved '{name.strip()}'")
        else:
            messagebox.showinfo("Already saved", "This route is already in your favourites.")

    # ------------------------------------------------------------ result panel
    def _clear_res(self):
        for w in self.res.winfo_children():
            w.destroy()

    def show_empty(self, msg=None):
        self._clear_res()
        tk.Label(self.res, text="Route details", bg=CARD, fg=TEXT, font=f(12, "bold")).pack(anchor="w")
        tk.Label(self.res, text=msg or "Pick a start and a destination to see the fastest route, "
                 "travel time, fare and where to change trains.\n\nTip: you can also click two "
                 "stations on the map.", bg=CARD, fg=MUTED, font=f(10),
                 wraplength=300, justify="left").pack(anchor="w", pady=(6, 0))
        tops = self.db.top_stations(3)
        if tops and not msg:
            tk.Label(self.res, text="YOUR FREQUENT STATIONS", bg=CARD, fg=MUTED,
                     font=f(8, "bold")).pack(anchor="w", pady=(16, 4))
            for r in tops:
                b = tk.Label(self.res, text="•  " + r["st"], bg=CARD, fg=ACCENT, font=f(10, "bold"),
                             cursor="hand2")
                b.pack(anchor="w", pady=1)
                b.bind("<Button-1>", lambda e, s=r["st"]: (self.from_var.set(s), self.to_cb.focus_set()))

    def show_result(self, r):
        self._clear_res()
        card = self.ticket.get() == "card"
        fare = router.fare_for(r["km"], card)
        pax = self._passengers()

        top = tk.Frame(self.res, bg=CARD)
        top.pack(fill="x")
        tk.Label(top, text=f"{r['minutes']} min", bg=CARD, fg=TEXT, font=f(24, "bold")).pack(side="left")
        tk.Label(top, text=f"₹{fare * pax}", bg=CARD, fg=ACCENT, font=f(20, "bold")).pack(side="right")
        sub = (f"Arrive around {router.arrival_time(r['minutes'])} if you leave now"
               if router.is_running() else f"Trains run {md.FIRST_TRAIN} - {md.LAST_TRAIN}. No service right now.")
        subrow = tk.Frame(self.res, bg=CARD)
        subrow.pack(fill="x")
        tk.Label(subrow, text=sub, bg=CARD, fg=MUTED if router.is_running() else RED,
                 font=f(9)).pack(side="left")
        save = tk.Label(subrow, text="+ Save", bg=CARD, fg=ACCENT, font=f(9, "bold"), cursor="hand2")
        save.pack(side="right")
        save.bind("<Button-1>", lambda e: self.save())
        fare_txt = f"₹{fare} x {pax} passengers" if pax > 1 else f"₹{fare} {'card/QR' if card else 'token'} fare"

        chips = tk.Frame(self.res, bg=CARD)
        chips.pack(fill="x", pady=(10, 8))
        for txt in (f"{r['stops']} stops", f"{r['km']} km",
                    "No change" if not r["changes"] else f"{r['changes']} change", fare_txt):
            tk.Label(chips, text=txt, bg=TEAL_SOFT, fg="#0B7F72", font=f(8, "bold"),
                     padx=7, pady=3).pack(side="left", padx=(0, 5))

        steps = tk.Frame(self.res, bg=CARD)
        steps.pack(fill="both", expand=True)
        for i, leg in enumerate(r["legs"]):
            row = tk.Frame(steps, bg=CARD)
            row.pack(fill="x", pady=(4, 0))
            bar = tk.Frame(row, bg=LINE_COLOURS[leg["line"]], width=5)
            bar.pack(side="left", fill="y", padx=(2, 10))
            txt = tk.Frame(row, bg=CARD)
            txt.pack(side="left", fill="x")
            n = len(leg["stations"]) - 1
            tk.Label(txt, text=leg["stations"][0], bg=CARD, fg=TEXT, font=f(10, "bold")).pack(anchor="w")
            tk.Label(txt, text=f"{leg['line']} Line towards {leg['towards']}", bg=CARD,
                     fg=LINE_COLOURS[leg["line"]], font=f(9, "bold")).pack(anchor="w")
            mid = leg["stations"][1:-1]
            via = f"{n} stop{'s' if n != 1 else ''}" + (f"  (via {mid[0]}{', ...' if len(mid) > 1 else ''})" if mid else "")
            tk.Label(txt, text=via, bg=CARD, fg=MUTED, font=f(9)).pack(anchor="w")
            if i < len(r["legs"]) - 1:
                tk.Label(steps, text=f"   Change trains at {leg['stations'][-1]}  (~{md.CHANGE_MIN} min)",
                         bg="#FFF6E5", fg="#9A6100", font=f(9, "bold"), anchor="w", pady=3).pack(fill="x", pady=(6, 2))
        end = tk.Frame(steps, bg=CARD)
        end.pack(fill="x", pady=(6, 0))
        tk.Label(end, text="•", bg=CARD, fg=RED, font=f(10)).pack(side="left", padx=(0, 8))
        tk.Label(end, text=f"Arrive at {r['to']}", bg=CARD, fg=TEXT, font=f(10, "bold")).pack(side="left")



# =====================================================================
#  STATIONS
# =====================================================================
class StationsScreen(Screen):
    title = "Stations"
    subtitle = "Every station on the Blue and Green Lines - search, check what's nearby, and start a trip."

    def __init__(self, parent, app):
        super().__init__(parent, app)
        bar = tk.Frame(self.content, bg=BG)
        bar.pack(fill="x", pady=(0, 10))
        tk.Label(bar, text="Search", bg=BG, fg=MUTED, font=f(9)).pack(side="left")
        self.q = tk.StringVar()
        self.q.trace_add("write", lambda *a: self.refresh())
        ttk.Entry(bar, textvariable=self.q, width=30).pack(side="left", padx=(6, 16))
        tk.Label(bar, text="Line", bg=BG, fg=MUTED, font=f(9)).pack(side="left")
        self.line = tk.StringVar(value="All lines")
        cb = ttk.Combobox(bar, textvariable=self.line, values=["All lines", "Blue", "Green", "Interchanges"],
                          state="readonly", width=12)
        cb.pack(side="left", padx=6)
        cb.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        self.count = tk.Label(bar, text="", bg=BG, fg=MUTED, font=f(9))
        self.count.pack(side="right")

        body = tk.Frame(self.content, bg=BG)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2, minsize=330)
        body.rowconfigure(0, weight=1)

        tcard = Card(body, padx=0, pady=0)
        tcard.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        frame, self.tree = make_tree(tcard.body, [
            ("no", "#", 40, "center", False), ("name", "Station", 200, "w", True),
            ("line", "Line", 100, "center", False), ("near", "Nearby", 260, "w", True)], height=18)
        frame.pack(fill="both", expand=True)
        self.tree.tag_configure("Blue", foreground="#1550A8")
        self.tree.tag_configure("Green", foreground="#157A37")
        self.tree.tag_configure("both", foreground=TEXT, font=f(10, "bold"))
        self.tree.bind("<<TreeviewSelect>>", self.show_detail)
        self.tree.bind("<Double-1>", lambda e: self.use("from"))

        self.detail = Card(body)
        self.detail.grid(row=0, column=1, sticky="nsew")

    def refresh(self):
        q = self.q.get().strip().lower()
        flt = self.line.get()
        self.tree.delete(*self.tree.get_children())
        n = 0
        for name in md.stations():
            lines = md.lines_at(name)
            if q and q not in name.lower() and q not in md.LANDMARKS.get(name, "").lower():
                continue
            if flt in ("Blue", "Green") and flt not in lines:
                continue
            if flt == "Interchanges" and len(lines) < 2:
                continue
            n += 1
            tag = "both" if len(lines) > 1 else lines[0]
            self.tree.insert("", "end", iid=name, tags=(tag,),
                             values=(n, name, " + ".join(lines), md.LANDMARKS.get(name, "")))
        self.count.config(text=f"{n} of {len(md.stations())} stations")
        kids = self.tree.get_children()
        if kids:
            self.tree.selection_set(kids[0])
        else:
            self._fill_detail(None)

    def show_detail(self, _e=None):
        sel = self.tree.selection()
        self._fill_detail(sel[0] if sel else None)

    def _fill_detail(self, name):
        for w in self.detail.body.winfo_children():
            w.destroy()
        if not name:
            tk.Label(self.detail.body, text="No station matches your search.", bg=CARD, fg=MUTED).pack(anchor="w")
            return
        b = self.detail.body
        tk.Label(b, text=name, bg=CARD, fg=TEXT, font=f(17, "bold"), wraplength=300,
                 justify="left").pack(anchor="w")
        chips = tk.Frame(b, bg=CARD)
        chips.pack(anchor="w", pady=(6, 0))
        for ln in md.lines_at(name):
            line_chip(chips, ln).pack(side="left", padx=(0, 6))
        if md.is_interchange(name):
            tk.Label(chips, text=" Interchange ", bg="#FFF6E5", fg="#9A6100", font=f(8, "bold"),
                     padx=4, pady=1).pack(side="left")
        if name in md.LANDMARKS:
            tk.Label(b, text="NEARBY", bg=CARD, fg=MUTED, font=f(8, "bold")).pack(anchor="w", pady=(14, 2))
            tk.Label(b, text=md.LANDMARKS[name], bg=CARD, fg=TEXT, font=f(10), wraplength=300,
                     justify="left").pack(anchor="w")

        tk.Label(b, text="QUICK TRIPS FROM HERE", bg=CARD, fg=MUTED, font=f(8, "bold")).pack(anchor="w", pady=(14, 4))
        for dest in ("Chennai Central", "Chennai Airport", "Koyambedu", "Guindy"):
            if dest == name:
                continue
            r = router.find_route(name, dest)
            row = tk.Frame(b, bg=CARD)
            row.pack(fill="x", pady=2)
            lbl = tk.Label(row, text=dest, bg=CARD, fg=ACCENT, font=f(10, "bold"), cursor="hand2")
            lbl.pack(side="left")
            lbl.bind("<Button-1>", lambda e, d=dest: self.app.screens["planner"].set_route(name, d))
            tk.Label(row, text=f"{r['minutes']} min  -  ₹{r['fare']}", bg=CARD, fg=MUTED,
                     font=f(9)).pack(side="right")

        within = [s for s in md.stations() if s != name and router.find_route(name, s)["minutes"] <= 15]
        tk.Label(b, text=f"{len(within)} stations are within 15 minutes of {name}.", bg=CARD, fg=MUTED,
                 font=f(9), wraplength=300, justify="left").pack(anchor="w", pady=(10, 0))

        btn = tk.Frame(b, bg=CARD)
        btn.pack(fill="x", side="bottom")
        ttk.Button(btn, text="Start from here", style="Accent.TButton",
                   command=lambda: self.use("from")).pack(side="left")
        ttk.Button(btn, text="Go here", style="Soft.TButton",
                   command=lambda: self.use("to")).pack(side="left", padx=8)

    def use(self, which):
        sel = self.tree.selection()
        if sel:
            self.app.screens["planner"].set_station(which, sel[0])


# =====================================================================
#  SAVED ROUTES & HISTORY
# =====================================================================
class SavedScreen(Screen):
    title = "Saved & History"
    subtitle = "Your favourite routes and recent searches. Double-click any row to open it on the map."

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)
        self.content.rowconfigure(1, weight=1)

        fav = Card(self.content, title="Favourite routes")
        fav.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 14))
        frame, self.fav = make_tree(fav.body, [
            ("name", "Name", 200, "w", True), ("route", "Route", 330, "w", True),
            ("time", "Time", 80, "center", False), ("fare", "Fare", 70, "center", False),
            ("chg", "Changes", 80, "center", False)], height=6)
        fb = tk.Frame(fav.body, bg=CARD)
        fb.pack(fill="x", side="bottom", pady=(8, 0))
        ttk.Button(fb, text="Open on map", style="Accent.TButton", command=self.open_fav).pack(side="left")
        ttk.Button(fb, text="Rename", style="Soft.TButton", command=self.rename_fav).pack(side="left", padx=8)
        ttk.Button(fb, text="Delete", style="Danger.TButton", command=self.delete_fav).pack(side="left")
        self.fav_empty = tk.Label(fb, text="", bg=CARD, fg=MUTED, font=f(9))
        self.fav_empty.pack(side="right")
        frame.pack(fill="both", expand=True)
        self.fav.bind("<Double-1>", lambda e: self.open_fav())

        hist = Card(self.content, title="Recent searches")
        hist.grid(row=1, column=0, sticky="nsew", padx=(0, 14))
        frame, self.hist = make_tree(hist.body, [
            ("when", "When", 130, "w", False), ("from", "From", 180, "w", True),
            ("to", "To", 180, "w", True), ("time", "Time", 70, "center", False),
            ("fare", "Fare", 60, "center", False)], height=6)
        hb = tk.Frame(hist.body, bg=CARD)
        hb.pack(fill="x", side="bottom", pady=(8, 0))
        ttk.Button(hb, text="Open on map", style="Accent.TButton", command=self.open_hist).pack(side="left")
        ttk.Button(hb, text="Clear history", style="Danger.TButton", command=self.clear_hist).pack(side="left", padx=8)
        frame.pack(fill="both", expand=True)
        self.hist.bind("<Double-1>", lambda e: self.open_hist())

        self.stats = Card(self.content, title="Your travel stats")
        self.stats.grid(row=1, column=1, sticky="nsew")
        self.stats.configure(width=280)

    def refresh(self):
        self.fav.delete(*self.fav.get_children())
        favs = self.db.get_favourites()
        for r in favs:
            route = router.find_route(r["from_st"], r["to_st"])
            self.fav.insert("", "end", iid=str(r["id"]), values=(
                r["nickname"], f"{r['from_st']}  {ARROW}  {r['to_st']}", f"{route['minutes']} min",
                f"₹{route['fare']}", route["changes"]))
        self.fav_empty.config(text="" if favs else "No favourites yet - plan a trip and press 'Save'.")

        self.hist.delete(*self.hist.get_children())
        hist = self.db.get_history()
        for r in hist:
            self.hist.insert("", "end", iid=str(r["id"]), values=(
                r["searched_at"][5:].replace("-", "/", 1), r["from_st"], r["to_st"],
                f"{r['minutes']} min", f"₹{r['fare']}"))

        for w in self.stats.body.winfo_children()[1:]:
            w.destroy()
        b = self.stats.body
        total = len(self.db.get_history(10000))
        mins = sum(r["minutes"] for r in self.db.get_history(10000))
        for big, small in ((str(total), "routes searched"), (f"{mins // 60}h {mins % 60}m", "of metro time planned")):
            row = tk.Frame(b, bg=CARD)
            row.pack(anchor="w", pady=2)
            tk.Label(row, text=big, bg=CARD, fg=ACCENT, font=f(16, "bold")).pack(side="left")
            tk.Label(row, text="  " + small, bg=CARD, fg=MUTED, font=f(9)).pack(side="left")
        tops = self.db.top_stations(4)
        if tops:
            tk.Label(b, text="MOST USED STATIONS", bg=CARD, fg=MUTED, font=f(8, "bold")).pack(anchor="w", pady=(10, 4))
            mx = tops[0]["n"]
            for r in tops:
                row = tk.Frame(b, bg=CARD)
                row.pack(fill="x", pady=2)
                tk.Label(row, text=r["st"], bg=CARD, fg=TEXT, font=f(9), width=17, anchor="w").pack(side="left")
                c = tk.Canvas(row, width=90, height=10, bg=CARD, highlightthickness=0)
                c.pack(side="left")
                c.create_rectangle(0, 1, 90 * r["n"] / mx, 9, fill=ACCENT, outline="")
                tk.Label(row, text=str(r["n"]), bg=CARD, fg=MUTED, font=f(9)).pack(side="left", padx=4)

    def _sel(self, tree):
        s = tree.selection()
        if not s:
            messagebox.showinfo("Select a row", "Select a row first.")
            return None
        return s[0]

    def open_fav(self):
        i = self._sel(self.fav)
        if i:
            r = next(x for x in self.db.get_favourites() if str(x["id"]) == i)
            self.app.screens["planner"].set_route(r["from_st"], r["to_st"])

    def rename_fav(self):
        i = self._sel(self.fav)
        if i:
            new = simpledialog.askstring("Rename", "New name:", initialvalue=self.fav.set(i, "name"), parent=self)
            if new and new.strip():
                self.db.rename_favourite(int(i), new.strip())
                self.refresh()

    def delete_fav(self):
        i = self._sel(self.fav)
        if i and messagebox.askyesno("Delete", f"Delete '{self.fav.set(i, 'name')}'?"):
            self.db.delete_favourite(int(i))
            self.refresh()

    def open_hist(self):
        i = self._sel(self.hist)
        if i:
            self.app.screens["planner"].set_route(self.hist.set(i, "from"), self.hist.set(i, "to"))

    def clear_hist(self):
        if messagebox.askyesno("Clear history", "Delete all recent searches?"):
            self.db.clear_history()
            self.refresh()


# =====================================================================
#  FARES & TIMINGS
# =====================================================================
class FareScreen(Screen):
    title = "Fares & Timings"
    subtitle = "Chennai Metro fares depend on distance. Pick a station to see the fare and time to every other station."

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.content.columnconfigure(1, weight=1)
        self.content.rowconfigure(0, weight=1)
        left = tk.Frame(self.content, bg=BG, width=360)
        left.grid(row=0, column=0, sticky="nsw", padx=(0, 14))
        left.pack_propagate(False)

        slab = Card(left, title="Fare chart")
        slab.pack(fill="x")
        c = tk.Canvas(slab.body, width=320, height=170, bg=CARD, highlightthickness=0)
        c.pack()
        labels = ["0-2 km", "2-5 km", "5-12 km", "12-21 km", "21+ km"]
        for i, ((_, fare), lab) in enumerate(zip(md.FARE_SLABS, labels)):
            x = 14 + i * 62
            h = fare * 2.4
            card_h = router.fare_for([1, 4, 10, 20, 30][i], True) * 2.4
            c.create_rectangle(x, 140 - h, x + 22, 140, fill=ACCENT, outline="")
            c.create_rectangle(x + 24, 140 - card_h, x + 46, 140, fill="#9ED8CF", outline="")
            c.create_text(x + 11, 134 - h, text=f"₹{fare}", anchor="s", font=f(8, "bold"), fill=TEXT)
            c.create_text(x + 23, 156, text=lab, font=f(8), fill=MUTED)
        c.create_rectangle(14, 4, 24, 12, fill=ACCENT, outline="")
        c.create_text(30, 8, text="Token", anchor="w", font=f(8), fill=MUTED)
        c.create_rectangle(80, 4, 90, 12, fill="#9ED8CF", outline="")
        c.create_text(96, 8, text="Card / QR (20% off)", anchor="w", font=f(8), fill=MUTED)

        info = Card(left, title="Train timings")
        info.pack(fill="both", expand=True, pady=(12, 0))
        running = router.is_running()
        self.status = tk.Label(info.body, text="", bg=CARD, font=f(10, "bold"))
        self.status.pack(anchor="w")
        for line in (f"First train  {md.FIRST_TRAIN}   -   Last train  {md.LAST_TRAIN}",
                     "Trains every 5-7 min at peak hours, 10-15 min otherwise",
                     "Interchanges: Chennai Central and Alandur",
                     "Fares are by distance; the longest trip costs ₹50",
                     "Times and gaps between stations are approximate"):
            tk.Label(info.body, text="•  " + line, bg=CARD, fg=MUTED, font=f(9), wraplength=310,
                     justify="left").pack(anchor="w", pady=2)

        right = Card(self.content)
        right.grid(row=0, column=1, sticky="nsew")
        top = tk.Frame(right.body, bg=CARD)
        top.pack(fill="x", pady=(0, 8))
        tk.Label(top, text="Fares from", bg=CARD, fg=TEXT, font=f(12, "bold")).pack(side="left")
        self.origin = tk.StringVar(value="Chennai Central")
        cb = ttk.Combobox(top, textvariable=self.origin, values=md.stations(), state="readonly", width=24)
        cb.pack(side="left", padx=10)
        cb.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        frame, self.tree = make_tree(right.body, [
            ("to", "To", 190, "w", True), ("line", "Line", 115, "center", False),
            ("time", "Time", 70, "center", False), ("km", "Km", 60, "center", False),
            ("tok", "Token", 70, "center", False), ("card", "Card/QR", 70, "center", False)], height=16)
        frame.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self._open)

    def _open(self, _e):
        s = self.tree.selection()
        if s:
            self.app.screens["planner"].set_route(self.origin.get(), s[0])

    def refresh(self):
        running = router.is_running()
        self.status.config(text="•  Trains are running now" if running else "•  Metro is closed now",
                           fg=GREEN if running else RED)
        o = self.origin.get()
        self.tree.delete(*self.tree.get_children())
        rows = []
        for s in md.stations():
            if s != o:
                r = router.find_route(o, s)
                rows.append((r["minutes"], s, r))
        for _, s, r in sorted(rows):
            lines = " + ".join(dict.fromkeys(l["line"] for l in r["legs"]))
            self.tree.insert("", "end", iid=s, values=(s, lines, f"{r['minutes']} min", r["km"],
                                                       f"₹{r['fare']}", f"₹{router.fare_for(r['km'], True)}"))
