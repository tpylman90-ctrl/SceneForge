import unittest

from tools.ci_capture_plan import ACTIVE_CRAFT, CRIMSON, FLEET, TRACKS, choose_captures


class CapturePlanTests(unittest.TestCase):
    def test_scenery_only_skips_approved_fleet(self):
        self.assertEqual(choose_captures(["game/tracks/canyon_scenery.gd"]), (False, CRIMSON, ()))

    def test_shrike_only(self):
        self.assertEqual(choose_captures(["game/vehicles/shrike_windshield.gd"]), (False, (), (2,)))

    def test_tremor_only(self):
        self.assertEqual(choose_captures(["tools/tremor_mk3.py"]), (False, (), (7,)))

    def test_shared_fleet_logic_requests_full_gallery(self):
        self.assertEqual(choose_captures(["game/vehicles/fleet_catalog.gd"]), (True, (), FLEET))

    def test_shared_track_logic(self):
        self.assertEqual(choose_captures(["game/city_loop.gd"]), (False, TRACKS, ()))

    def test_docs_only_skips_images(self):
        self.assertEqual(choose_captures(["README.md", "docs/notes.md"]), (False, (), ()))

    def test_manual_capture_scopes(self):
        self.assertEqual(choose_captures([], "full"), (True, TRACKS, FLEET))
        self.assertEqual(choose_captures([], "active"), (False, CRIMSON, ACTIVE_CRAFT))
        self.assertEqual(choose_captures(["game/vehicles/fleet_catalog.gd"], "none"), (False, (), ()))


if __name__ == "__main__":
    unittest.main()
