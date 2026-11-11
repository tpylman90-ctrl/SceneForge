import unittest

from tools.ci_capture_plan import ACTIVE_CRAFT, CRIMSON, FLEET, TRACKS, choose_captures


class CapturePlanTests(unittest.TestCase):
    def test_scenery_only_skips_approved_fleet(self):
        self.assertEqual(choose_captures(["game/tracks/canyon_scenery.gd"]), (False, CRIMSON, ()))

    def test_sculpted_serpent_isolated(self):
        self.assertEqual(
            choose_captures(["game/tracks/serpent_canyon.gd", "game/tracks/serpent_sculpt/height.r16"]),
            (False, (4,), ()),
        )

    def test_canyon_documentation_skips_images(self):
        self.assertEqual(choose_captures(["game/tracks/CRIMSON_DIVIDE.md"]), (False, (), ()))

    def test_256px_sandstone_only_captures_serpent(self):
        self.assertEqual(
            choose_captures(["game/tracks/serpent_textures/serpent_breakup_256.png"]),
            (False, (4,), ()),
        )

    def test_blender_canyon_kit_only_captures_serpent(self):
        self.assertEqual(
            choose_captures(["tools/build_serpent_rock_kit.py",
                             "tools/bake_serpent_racing_textures.py",
                             "game/tracks/serpent_rock_kit.gd"]),
            (False, (4,), ()),
        )
        self.assertEqual(
            choose_captures(["game/assets/scenery/serpent/wall_a.glb"]),
            (False, (4,), ()),
        )

    def test_hero_landmark_source_only_captures_serpent(self):
        self.assertEqual(
            choose_captures(["tools/build_serpent_landmarks.py"]),
            (False, (4,), ()),
        )

    def test_shrike_only(self):
        self.assertEqual(choose_captures(["game/vehicles/shrike_windshield.gd"]), (False, (), (2,)))

    def test_tremor_only(self):
        self.assertEqual(choose_captures(["tools/tremor_mk3.py"]), (False, (), (7,)))

    def test_shared_fleet_logic_requests_full_gallery(self):
        self.assertEqual(choose_captures(["game/vehicles/fleet_catalog.gd"]), (True, (), FLEET))

    def test_shared_track_logic(self):
        self.assertEqual(choose_captures(["game/city_loop.gd"]), (False, TRACKS, ()))

    def test_vulkan_standard_captures_three_styles_and_foundry(self):
        self.assertEqual(choose_captures(["game/project.godot"]), (True, (0,4,7), ()))
        self.assertEqual(choose_captures(["tools/verify_vulkan_pipeline.py"]), (True, (0,4,7), ()))

    def test_docs_only_skips_images(self):
        self.assertEqual(choose_captures(["README.md", "docs/notes.md"]), (False, (), ()))

    def test_manual_capture_scopes(self):
        self.assertEqual(choose_captures([], "full"), (True, TRACKS, FLEET))
        self.assertEqual(choose_captures([], "active"), (False, CRIMSON, ACTIVE_CRAFT))
        self.assertEqual(choose_captures(["game/vehicles/fleet_catalog.gd"], "none"), (False, (), ()))


if __name__ == "__main__":
    unittest.main()
