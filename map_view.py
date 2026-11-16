"""
map_view.py - The interactive metro map drawn on a Tkinter Canvas.
Owner: Member 1 (UI)

- draws both lines, stations and labels from metro_data.map_positions()
- clicking a station calls on_station_click(name)
- highlight(route) fades the network and draws the chosen route on top
"""
import tkinter as tk

import metro_data as md
from theme import BLUE_LINE, GREEN_LINE, TEXT, MUTED, GREEN, RED, f

PALE = {"Blue": "#C9DBF6", "Green": "#C6E9D1"}
COLOUR = {"Blue": BLUE_LINE, "Green": GREEN_LINE}


class MetroMap(tk.Canvas):
    def __init__(self, parent, on_station_click=None, **kw):
        super().__init__(parent, width=md.MAP_W, height=md.MAP_H, bg="white",
                         highlightthickness=0, **kw)
        self.pos = md.map_positions()
        self.on_station_click = on_station_click
        self.route = None
        self.draw()

    # ------------------------------------------------------------ drawing
    def _line_coords(self, line):
        coords = []
        for name, _ in md.LINES[line]:
            x, y, _ = self.pos[name]
            coords += [x, y]
        return coords

    def draw(self):
        self.delete("all")
        faded = self.route is not None
        for line in ("Green", "Blue"):
            self.create_line(*self._line_coords(line), fill=PALE[line] if faded else COLOUR[line],
                             width=6, capstyle="round", joinstyle="round")

        if self.route:
            for leg in self.route["legs"]:
                pts = []
                for st in leg["stations"]:
                    pts += list(self.pos[st][:2])
                if len(pts) >= 4:
                    self.create_line(*pts, fill=COLOUR[leg["line"]], width=10,
                                     capstyle="round", joinstyle="round")

        on_route = set(self.route["stations"]) if self.route else set()
        for name, (x, y, side) in self.pos.items():
            tag = "st_" + str(abs(hash(name)))
            inter = md.is_interchange(name)
            line = md.lines_at(name)[0]
            highlighted = name in on_route
            dim = faded and not highlighted
            r = 8 if inter else (6 if highlighted else 5)
            outline = "#9CA3AF" if dim else (TEXT if inter else COLOUR[line])
            self.create_oval(x - r, y - r, x + r, y + r, fill="white", outline=outline,
                             width=3 if inter else 2, tags=(tag, "station"))
            colour = "#B8BEC8" if dim else TEXT
            weight = "bold" if (inter or highlighted) else "normal"
            size = 8 if not inter else 9
            if side == "ne":   # label lifted above-right (avoids the track below it)
                self.create_text(x + 14, y - 11, text=name, anchor="w", fill=colour,
                                 font=f(size, weight), tags=(tag, "station"))
            elif side == "e":
                self.create_text(x + 14, y, text=name, anchor="w", fill=colour,
                                 font=f(size, weight), tags=(tag, "station"))
            elif side == "w":
                self.create_text(x - 14, y, text=name, anchor="e", fill=colour,
                                 font=f(size, weight), tags=(tag, "station"))
            else:   # angled label above a horizontal line
                self.create_text(x + 3, y - 10, text=name, anchor="w", angle=38, fill=colour,
                                 font=f(size, weight), tags=(tag, "station"))
            self.tag_bind(tag, "<Button-1>", lambda e, n=name: self._clicked(n))
            self.tag_bind(tag, "<Enter>", lambda e: self.config(cursor="hand2"))
            self.tag_bind(tag, "<Leave>", lambda e: self.config(cursor=""))

        if self.route:
            self._pin(self.route["from"], "A", GREEN)
            self._pin(self.route["to"], "B", RED)
        self._legend()

    def _pin(self, name, letter, colour):
        x, y, _ = self.pos[name]
        self.create_oval(x - 12, y - 12, x + 12, y + 12, fill=colour, outline="white", width=2)
        self.create_text(x, y, text=letter, fill="white", font=f(10, "bold"))

    def _legend(self):
        x, y = 24, md.MAP_H - 70
        self.create_text(x, y - 22, text="Chennai Metro", anchor="w", fill=TEXT, font=f(11, "bold"))
        for i, (line, col) in enumerate((("Blue Line", BLUE_LINE), ("Green Line", GREEN_LINE))):
            yy = y + i * 20
            self.create_line(x, yy, x + 26, yy, fill=col, width=6, capstyle="round")
            self.create_text(x + 36, yy, text=line, anchor="w", fill=MUTED, font=f(9))
        yy = y + 40
        self.create_oval(x + 6, yy - 7, x + 20, yy + 7, fill="white", outline=TEXT, width=3)
        self.create_text(x + 36, yy, text="Interchange", anchor="w", fill=MUTED, font=f(9))
        self.create_text(12, 12, text="Schematic map - not to scale. Click a station to pick it.",
                         anchor="nw", fill="#9CA3AF", font=f(8))

    # ------------------------------------------------------------ public
    def highlight(self, route):
        self.route = route
        self.draw()

    def clear(self):
        self.route = None
        self.draw()

    def _clicked(self, name):
        if self.on_station_click:
            self.on_station_click(name)
