#!/usr/bin/env python3
"""Fail CI if the SceneForge Godot game or its screenshot pipeline silently use OpenGL."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = (ROOT/"game/project.godot").read_text()
AUTHOR = (ROOT/"tools/serpent_terrain_editor/project.godot").read_text()

for line in (
    'renderer/rendering_method="mobile"',
    'renderer/rendering_method.mobile="mobile"',
    'rendering_device/driver="vulkan"',
    'rendering_device/driver.android="vulkan"',
    'rendering_device/driver.linuxbsd="vulkan"',
    'rendering_device/fallback_to_opengl3=false',
):
    assert GAME.splitlines().count(line) == 1, f"Game Vulkan setting missing or duplicated: {line}"
assert not any(line.startswith("rendering_device/fallback_to_opengl3=") and line != "rendering_device/fallback_to_opengl3=false" for line in GAME.splitlines()), (
    "Another source change has re-enabled OpenGL fallback"
)

for line in (
    'renderer/rendering_method="forward_plus"',
    'rendering_device/driver="vulkan"',
    'rendering_device/fallback_to_opengl3=false',
):
    assert line in AUTHOR.splitlines(), f"Terrain3D editor lost required Vulkan setting: {line}"

CAPTURE_FILES = [
    ".github/workflows/android.yml", ".github/workflows/viewer.yml",
    "tools/ci_capture_tracks.sh", "tools/ci_capture_fleet.sh",
]
for path in CAPTURE_FILES:
    content = (ROOT/path).read_text()
    assert "gl_compatibility" not in content, f"Legacy OpenGL override in {path}"
    for line in content.splitlines():
        if "xvfb-run" in line and "godot" in line:
            assert "--rendering-method mobile --rendering-driver vulkan" in line, (
                f"Preview isn't explicitly Mobile/Vulkan in {path}: {line}"
            )
assert "VK_ICD_FILENAMES" in (ROOT/".github/workflows/android.yml").read_text()
assert "VK_ICD_FILENAMES" in (ROOT/".github/workflows/viewer.yml").read_text()
print("SCENEFORGE_VULKAN_STANDARD_OK game=mobile/vulkan preview=mobile/vulkan authoring=forward_plus/vulkan")
