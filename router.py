"""
router.py - Finds the fastest route between two stations (Dijkstra's algorithm)
and works out the fare. No Tkinter code here, so it can be unit-tested.
Owner: Member 2 (Data & Logic)

How it works, in one line: the metro is stored as a network where each
station is a point and each track between neighbouring stations has a
travel time; Dijkstra's algorithm always expands the closest unvisited
point next, so the first time it reaches the destination, that route is
the fastest one.
"""
import heapq
from datetime import datetime, timedelta

import metro_data as md


# ---------------------------------------------------------------- build the network
def build_graph():
    """
    Adjacency list. A 'node' is (station, line) so that changing lines can cost extra time.
    graph[node] = list of (neighbour_node, minutes, km)
    """
    graph = {}

    def add(a, b, minutes, km):
        graph.setdefault(a, []).append((b, minutes, km))
        graph.setdefault(b, []).append((a, minutes, km))

    for line, data in md.LINES.items():
        for i in range(len(data) - 1):
            (s1, km), (s2, _) = data[i], data[i + 1]
            add((s1, line), (s2, line), km * md.MIN_PER_KM + md.DWELL_MIN, km)
    # interchange: same station, different line
    for st in md.stations():
        lines = md.lines_at(st)
        for i in range(len(lines)):
            for j in range(i + 1, len(lines)):
                add((st, lines[i]), (st, lines[j]), md.CHANGE_MIN, 0)
    return graph


GRAPH = build_graph()


# ---------------------------------------------------------------- Dijkstra
def find_route(start, end):
    """
    Returns a dict with the path and totals, or None if no route exists.
    path = list of (station, line) from start to end.
    """
    if start == end:
        raise ValueError("Start and destination are the same station")
    if start not in md.stations() or end not in md.stations():
        raise ValueError("Unknown station")

    dist = {}          # best known time to reach each node
    prev = {}          # where we came from (to rebuild the path)
    heap = []          # priority queue of (time, km, node)
    for line in md.lines_at(start):
        node = (start, line)
        dist[node] = 0
        heapq.heappush(heap, (0, 0, node))

    visited = set()
    goal = None
    while heap:
        time, km, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        if node[0] == end:          # first time we reach the destination = fastest
            goal = node
            break
        for nxt, minutes, step_km in GRAPH[node]:
            new_time = time + minutes
            if new_time < dist.get(nxt, float("inf")):
                dist[nxt] = new_time
                prev[nxt] = (node, step_km)
                heapq.heappush(heap, (new_time, km + step_km, nxt))

    if goal is None:
        return None

    # walk backwards from the destination to rebuild the path
    path, km_total, node = [goal], 0.0, goal
    while node in prev:
        node, step_km = prev[node]
        km_total += step_km
        path.append(node)
    path.reverse()
    # drop a pointless "change" at the very start or end
    while len(path) > 1 and path[0][0] == path[1][0]:
        path.pop(0)
    while len(path) > 1 and path[-1][0] == path[-2][0]:
        path.pop()

    legs = make_legs(path)
    return {
        "from": start, "to": end, "path": path, "legs": legs,
        "stations": [p[0] for i, p in enumerate(path) if i == 0 or p[0] != path[i - 1][0]],
        "minutes": round(dist[goal]), "km": round(km_total, 1),
        "stops": sum(len(l["stations"]) - 1 for l in legs),
        "changes": len(legs) - 1,
        "fare": fare_for(km_total),
    }


def make_legs(path):
    """Group the path into legs: one leg per line ridden."""
    legs = []
    for station, line in path:
        if legs and legs[-1]["line"] == line:
            legs[-1]["stations"].append(station)
        else:
            legs.append({"line": line, "stations": [station]})
    for leg in legs:
        data = [n for n, _ in md.LINES[leg["line"]]]
        a, b = data.index(leg["stations"][0]), data.index(leg["stations"][-1])
        leg["towards"] = data[-1] if b > a else data[0]
    return legs


# ---------------------------------------------------------------- fares & times
def fare_for(km, card=False):
    """Distance-based fare in rupees; card/QR tickets get a 20% discount."""
    for limit, fare in md.FARE_SLABS:
        if km <= limit:
            return round(fare * (1 - md.CARD_DISCOUNT)) if card else fare
    return md.FARE_SLABS[-1][1]


def arrival_time(minutes, leave=None):
    leave = leave or datetime.now()
    return (leave + timedelta(minutes=minutes)).strftime("%I:%M %p").lstrip("0")


def is_running(now=None):
    now = (now or datetime.now()).strftime("%H:%M")
    return md.FIRST_TRAIN <= now <= md.LAST_TRAIN


def directions(route):
    """Plain-English step-by-step directions."""
    steps = []
    for i, leg in enumerate(route["legs"]):
        n = len(leg["stations"]) - 1
        verb = "Board" if i == 0 else "Change to"
        steps.append(f"{verb} the {leg['line']} Line at {leg['stations'][0]} "
                     f"(towards {leg['towards']})")
        steps.append(f"Ride {n} stop{'s' if n != 1 else ''} to {leg['stations'][-1]}")
    steps.append(f"Exit at {route['to']}")
    return steps
