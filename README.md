# MetroMate - Chennai Metro Route Planner

A Tkinter desktop app that finds the fastest route between any two Chennai Metro stations,
shows it on an interactive map, and tells you the travel time, stops, changes and fare.

## Run
Only Python 3 is needed (Tkinter and SQLite come with it). No pip installs.

    python main.py

(If `python` is not recognised on Windows, use `py main.py`.)

## Tests

    python -m unittest test_router -v

## Files
| File | What it does | Owner |
|---|---|---|
| main.py | Main window, sidebar, switching screens | N. Raghav |
| theme.py | Colours, fonts, styles | N. Raghav |
| map_view.py | Interactive metro map on a Canvas | N. Raghav |
| screens.py | Plan a Trip, Stations (Raghav); Saved & History, Fares (Adwiti) | Both |
| metro_data.py | Stations, distances, fares, timings, landmarks | Adwiti Sharma |
| router.py | Dijkstra's shortest path, fares, directions | Adwiti Sharma |
| database.py | SQLite favourites, history, settings | Adwiti Sharma |
| test_router.py | 11 unit tests | Adwiti Sharma |
