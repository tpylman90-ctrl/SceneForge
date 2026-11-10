#!/usr/bin/env python3
"""Determine the minimum useful screenshots for a SceneForge Android CI run.

All gameplay/vehicle smoke tests run independently of this optional visual plan.
Keep this script dependency-free so GitHub Actions can execute it before Godot.
"""
from __future__ import annotations

import argparse
from pathlib import Path

FLEET = tuple(range(10))
TRACKS = tuple(range(8))
CRIMSON = (4, 5, 6)
ACTIVE_CRAFT = (0, 2, 7, 9)  # Current Kestrel fairing and other active bodywork
NAMES = {
    0: ("kestrel",),
    1: ("piledriver", "pyldriver"),
    2: ("shrike",),
    3: ("mantis",),
    4: ("aurora",),
    5: ("forge",),
    6: ("synapse",),
    7: ("tremor",),
    8: ("aerolith",),
    9: ("solstice",),
}


def choose_captures(paths: list[str], scope: str = "auto") -> tuple[bool, tuple[int, ...], tuple[int, ...]]:
    """Return (foundry, circuit IDs, craft IDs). No captures means no render jobs."""
    if scope == "full":
        return True, TRACKS, FLEET
    if scope == "active":
        return False, CRIMSON, ACTIVE_CRAFT
    if scope == "none":
        return False, (), ()
    if scope != "auto":
        raise ValueError(f"Invalid screenshot scope: {scope}")

    foundry = False
    tracks: set[int] = set()
    craft: set[int] = set()
    for raw in paths:
        path = raw.strip().lower().replace("\\", "/")
        if not path:
            continue
        if path in {"game/tracks/skyfall_run.gd", "game/tracks/skyfall_flight_world.gd",
                    "game/tests/skyfall_run_test.gd", "tools/ci_capture_tracks.sh",
                    "tools/ci_capture_plan.py"}:
            tracks.add(7)
        elif (path.startswith("game/tracks/serpent_sculpt/")
                or path.startswith("game/tracks/serpent_textures/")
                or path.startswith("game/assets/scenery/serpent/")
                or path in {"game/tracks/serpent_canyon.gd", "game/tracks/serpent_rock_kit.gd",
                            "tools/build_serpent_rock_kit.py", "tools/build_serpent_landmarks.py",
                            "tools/bake_serpent_racing_textures.py",
                            "tools/ensure_serpent_texture_import.py"}):
            # Dedicated sculpt passes never require Red Mesa / Devil's Gate captures.
            tracks.add(4)
        elif path.startswith("game/tracks/") and not path.endswith(".md"):
            tracks.update(CRIMSON)
        if path in {"game/city_loop.gd", "game/city_loop.tscn"}:
            tracks.update(TRACKS)
        if path in {"game/main.tscn", "game/foundry.tscn", "tools/build_neon_foundry.py"}:
            foundry = True
        if path in {
            "game/foundry.gd", "game/fleet_hangar.gd", "game/fleet_hangar.tscn",
            "game/vehicles/fleet_catalog.gd", "game/vehicles/chassis_definition.gd",
            "game/vehicles/cockpit_telemetry.gd", "tools/build_fleet.py",
        }:
            foundry = True
            craft.update(FLEET)
        if (path.startswith("game/assets/")
                and not path.startswith(("game/assets/fleet/", "game/assets/scenery/serpent/"))):
            foundry = True
        if path in {"tools/kestrel_surface_pass.py", "tools/install_kestrel_upgrade.py",
                    "tools/refine_kestrel_upgrade.py"}:
            # A visible Kestrel body repair must be reviewed in the Foundry
            # as well as the craft-only capture; skip unrelated fleet shots.
            foundry = True
            craft.add(0)
        is_specific_asset = path.startswith(("game/vehicles/", "tools/", "showroom_sources/", "game/assets/fleet/"))
        if is_specific_asset:
            found_match = False
            for craft_id, aliases in NAMES.items():
                # Avoid mapping unrelated files that happen to contain a craft word
                # outside a vehicle/tool/asset path.
                if any(alias in Path(path).name for alias in aliases):
                    craft.add(craft_id)
                    found_match = True
            # Unknown vehicle runtime modules can affect every craft.
            if path.startswith("game/vehicles/") and not found_match and path != "game/vehicles/performance_parts.gd":
                craft.update(FLEET)
        # Renderer settings and scene-wide lighting can change all previews.
        if path == "game/project.godot":
            tracks.add(7)  # Vulkan evaluation: isolate the new visual target
    return foundry, tuple(sorted(tracks)), tuple(sorted(craft))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--changes", required=True, type=Path)
    parser.add_argument("--scope", choices=("auto", "active", "full", "none"), default="auto")
    parser.add_argument("--env-file", required=True, type=Path)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()
    changes = args.changes.read_text(encoding="utf-8").splitlines()
    foundry, tracks, craft = choose_captures(changes, args.scope)
    values = {
        "CAPTURE_FOUNDRY": "1" if foundry else "0",
        "CAPTURE_TRACKS": " ".join(map(str, tracks)),
        "CAPTURE_FLEET": " ".join(map(str, craft)),
    }
    with args.env_file.open("a", encoding="utf-8") as out:
        for key, value in values.items():
            out.write(f"{key}={value}\n")
    summary = (
        f"### Screenshot selection ({args.scope})\n\n"
        f"- Foundry: {'yes' if foundry else 'skip'}\n"
        f"- Tracks: {', '.join(map(str, tracks)) or 'skip'}\n"
        f"- Craft: {', '.join(map(str, craft)) or 'skip'}\n"
        "- Fleet, race, collision and export checks still run for every build.\n"
    )
    print(summary)
    if args.summary:
        with args.summary.open("a", encoding="utf-8") as out:
            out.write(summary + "\n")


if __name__ == "__main__":
    main()
