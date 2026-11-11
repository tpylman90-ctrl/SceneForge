"""Guard the Android Vulkan/loader wiring against accidental regression.

These cheap source-level checks complement (not replace) Godot import/smoke
and Android device testing in the existing pipeline.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GAME = ROOT / "game"


class TrackLoadingWiringTest(unittest.TestCase):
    def test_mobile_vulkan_and_autoload(self):
        project = (GAME / "project.godot").read_text()
        self.assertIn('renderer/rendering_method="mobile"', project)
        self.assertIn('renderer/rendering_method.mobile="mobile"', project)
        self.assertIn('rendering_device/driver.android="vulkan"', project)
        self.assertIn('TrackLoader="*res://track_loader.gd"', project)

    def test_scene_is_loaded_before_gameplay_resume(self):
        source = (GAME / "track_loader.gd").read_text()
        for token in (
            "ResourceLoader.load_threaded_request",
            "ResourceLoader.load_threaded_get_status",
            "ResourceLoader.load_threaded_get",
            "get_tree().change_scene_to_packed",
            "await get_tree().scene_changed",
            "active_scene.set_physics_process(false)",
            "active_scene.finish_track_load()",
        ):
            with self.subTest(token=token):
                self.assertIn(token, source)
        self.assertLess(source.index("active_scene.set_physics_process(false)"),
                        source.index("active_scene.finish_track_load()"))

    def test_every_interactive_race_entry_uses_loader(self):
        for path in ("foundry.gd", "fleet_hangar.gd", "city_loop.gd"):
            with self.subTest(path=path):
                self.assertIn("TrackLoader.begin(", (GAME / path).read_text())


if __name__ == "__main__":
    unittest.main()
