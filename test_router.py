"""
test_router.py - Automated tests for routing, fares and the database.
Run:  python -m unittest test_router -v
Owner: Member 3 (Screens & Testing)
"""
import unittest

import metro_data as md
import router
from database import Database


class RouterTests(unittest.TestCase):
    def test_station_counts(self):
        self.assertEqual(len(md.BLUE), 26)
        self.assertEqual(len(md.GREEN), 17)
        self.assertEqual(len(md.stations()), 41)          # Central and Alandur counted once

    def test_line_lengths(self):
        self.assertAlmostEqual(sum(k for _, k in md.BLUE if k), 32.6, places=1)
        self.assertAlmostEqual(sum(k for _, k in md.GREEN if k), 22.0, places=1)

    def test_same_line_no_change(self):
        r = router.find_route("Guindy", "Chennai Airport")
        self.assertEqual(r["changes"], 0)
        self.assertEqual(r["stops"], 4)

    def test_change_at_alandur(self):
        r = router.find_route("Koyambedu", "Chennai Airport")
        self.assertEqual(r["changes"], 1)
        self.assertEqual(r["legs"][0]["stations"][-1], "Alandur")

    def test_change_at_central(self):
        r = router.find_route("Egmore", "High Court")
        self.assertEqual([l["line"] for l in r["legs"]], ["Green", "Blue"])
        self.assertEqual(r["legs"][1]["stations"][0], "Chennai Central")

    def test_route_is_symmetric(self):
        a = router.find_route("Vadapalani", "Washermanpet")
        b = router.find_route("Washermanpet", "Vadapalani")
        self.assertEqual(a["minutes"], b["minutes"])
        self.assertEqual(a["km"], b["km"])

    def test_fastest_beats_alternative(self):
        # Ekkattuthangal -> Guindy: via Alandur is far shorter than going round via Central
        r = router.find_route("Ekkattuthangal", "Guindy")
        self.assertIn("Alandur", r["stations"])
        self.assertNotIn("Chennai Central", r["stations"])

    def test_same_station_rejected(self):
        with self.assertRaises(ValueError):
            router.find_route("Guindy", "Guindy")

    def test_fare_slabs(self):
        self.assertEqual(router.fare_for(1.5), 10)
        self.assertEqual(router.fare_for(4), 20)
        self.assertEqual(router.fare_for(12), 30)
        self.assertEqual(router.fare_for(20), 40)
        self.assertEqual(router.fare_for(32.6), 50)
        self.assertEqual(router.fare_for(32.6, card=True), 40)

    def test_every_pair_reachable(self):
        names = md.stations()
        for a in names:
            for b in names:
                if a != b:
                    self.assertIsNotNone(router.find_route(a, b))

    def test_favourites_no_duplicates(self):
        db = Database(":memory:")
        self.assertTrue(db.add_favourite("Home", "Guindy", "Egmore"))
        self.assertFalse(db.add_favourite("Again", "Guindy", "Egmore"))
        self.assertEqual(len(db.get_favourites()), 1)


if __name__ == "__main__":
    unittest.main()
