"""
metro_data.py - The Chennai Metro network (Phase 1: Blue Line + Green Line).
Owner: Member 2 (Data & Logic)

Each line is a list of (station name, km to the NEXT station).
Line lengths match the published figures (Blue 32.6 km, 26 stations;
Green 22 km, 17 stations). Individual gaps between stations are approximate.
"""

BLUE = [
    ("Wimco Nagar Depot", 1.0), ("Wimco Nagar", 1.1), ("Thiruvottriyur", 1.0),
    ("Thiruvottriyur Theradi", 1.2), ("Kaladipet", 1.1), ("Tollgate", 1.0),
    ("New Washermanpet", 1.0), ("Tondiarpet", 1.1), ("Sir Theagaraya College", 1.0),
    ("Washermanpet", 1.5), ("Mannadi", 0.9), ("High Court", 1.2),
    ("Chennai Central", 1.6), ("Government Estate", 1.0), ("LIC", 0.9),
    ("Thousand Lights", 1.0), ("AG-DMS", 1.0), ("Teynampet", 1.2),
    ("Nandanam", 1.9), ("Saidapet", 1.1), ("Little Mount", 1.3),
    ("Guindy", 2.2), ("Alandur", 2.1), ("Nanganallur Road", 2.6),
    ("Meenambakkam", 1.6), ("Chennai Airport", None),
]

GREEN = [
    ("Chennai Central", 1.6), ("Egmore", 1.0), ("Nehru Park", 1.3), ("Kilpauk", 1.1),
    ("Pachaiyappa's College", 1.2), ("Shenoy Nagar", 1.3), ("Anna Nagar East", 1.2),
    ("Anna Nagar Tower", 1.1), ("Thirumangalam", 1.4), ("Koyambedu", 0.9),
    ("CMBT", 1.1), ("Arumbakkam", 1.4), ("Vadapalani", 1.6), ("Ashok Nagar", 1.8),
    ("Ekkattuthangal", 2.7), ("Alandur", 1.3), ("St. Thomas Mount", None),
]

LINES = {"Blue": BLUE, "Green": GREEN}

# Fare slabs (distance in km -> fare in rupees), CMRL distance-based fares
FARE_SLABS = [(2, 10), (5, 20), (12, 30), (21, 40), (999, 50)]
CARD_DISCOUNT = 0.20          # travel card / QR ticket discount

# Timing assumptions used by the route finder
MIN_PER_KM = 1.8              # average running time (about 33 km/h)
DWELL_MIN = 0.5               # stop time at each intermediate station
CHANGE_MIN = 5                # time to change lines at an interchange (walk + wait)
FIRST_TRAIN, LAST_TRAIN = "05:00", "23:00"

# Nearby places shown on the Stations screen
LANDMARKS = {
    "Chennai Central": "MGR Central railway station, Ripon Building",
    "Egmore": "Egmore railway station, Government Museum",
    "Chennai Airport": "Domestic & international terminals",
    "Alandur": "Interchange; Butt Road, Alandur court",
    "Guindy": "Guindy National Park, IIT Madras (nearby), Olympia Tech Park",
    "AG-DMS": "Gemini flyover, DMS campus",
    "Thousand Lights": "Spencer Plaza, Express Avenue (nearby)",
    "Government Estate": "Anna Salai, Omandurar Estate",
    "High Court": "Madras High Court, Parry's Corner",
    "Koyambedu": "Koyambedu market",
    "CMBT": "Chennai Mofussil Bus Terminus",
    "Vadapalani": "Vadapalani Murugan temple, Forum Vijaya Mall",
    "Anna Nagar Tower": "Anna Nagar Tower Park",
    "St. Thomas Mount": "St. Thomas Mount suburban station",
    "Saidapet": "Saidapet railway station, Panagal Maaligai",
    "Teynampet": "Anna Arivalayam, Cathedral Road (nearby)",
    "Nandanam": "YMCA grounds, Nandanam Arts College",
    "LIC": "LIC building, Anna Salai",
    "Little Mount": "Little Mount shrine",
    "Washermanpet": "Washermanpet market",
    "Wimco Nagar Depot": "Metro depot, Thiruvottriyur",
    "Meenambakkam": "Meenambakkam suburban station",
    "Ashok Nagar": "Ashok Pillar",
    "Kilpauk": "Kilpauk Medical College",
    "Pachaiyappa's College": "Pachaiyappa's College, Chetpet",
    "Shenoy Nagar": "Shenoy Nagar, Ayanavaram",
    "Thirumangalam": "VR Mall (nearby)",
    "Arumbakkam": "Arumbakkam, NSK Nagar",
    "Ekkattuthangal": "Guindy Industrial Estate",
    "Nehru Park": "Poonamallee High Road",
    "Anna Nagar East": "Anna Nagar 2nd Avenue",
    "Mannadi": "Parry's Corner, Burma Bazaar",
    "Tondiarpet": "Tondiarpet",
    "Nanganallur Road": "Nanganallur, Pazhavanthangal",
}


def stations():
    """All unique station names, Blue Line order first, then Green-only stations."""
    seen = []
    for line in (BLUE, GREEN):
        for name, _ in line:
            if name not in seen:
                seen.append(name)
    return seen


def lines_at(station):
    return [ln for ln, data in LINES.items() if any(n == station for n, _ in data)]


def is_interchange(station):
    return len(lines_at(station)) > 1


# ------------------------------------------------------------------ schematic map layout
MAP_W, MAP_H = 640, 660


def map_positions():
    """
    Hand-designed schematic coordinates for every station on the Canvas.
    Returns {station: (x, y, label_side)} where label_side is 'e', 'w' or 'n'.
    """
    pos = {}
    # Blue north: Wimco Nagar Depot .. Chennai Central (vertical, labels on the right)
    for i in range(13):
        pos[BLUE[i][0]] = (450, 30 + i * 19.5, "e")
    cx, cy = pos["Chennai Central"][:2]
    # Blue south: Central -> Alandur (diagonal)
    ax, ay = 340, 520
    for i in range(1, 11):
        t = i / 10
        pos[BLUE[12 + i][0]] = (cx + (ax - cx) * t, cy + (ay - cy) * t, "e")
    # Blue after Alandur: down to the Airport
    for i, name in enumerate(["Nanganallur Road", "Meenambakkam", "Chennai Airport"], 1):
        pos[name] = (ax + 22 * i, ay + 38 * i, "e")
    # Green west: Central -> Thirumangalam (horizontal, angled labels above)
    for i in range(1, 9):
        pos[GREEN[i][0]] = (cx - i * 46, cy, "n")
    tx = pos["Thirumangalam"][0]
    # Green south: Koyambedu .. Ekkattuthangal (vertical, labels on the right)
    for i in range(1, 7):
        pos[GREEN[8 + i][0]] = (tx, cy + i * 36, "e")
    x, y, _ = pos["Ekkattuthangal"]
    pos["Ekkattuthangal"] = (x, y, "ne")
    # St. Thomas Mount below-left of Alandur
    pos["St. Thomas Mount"] = (ax - 70, ay + 52, "w")
    return pos
