#!/usr/bin/env python3
"""Prepare the isolated Crimson Serpent Terrain3D sculpting studio.

Run from any directory: python tools/serpent_terrain_editor/setup.py
Add --install-terrain3d to download the pinned MIT-licensed editor plugin.
This never modifies the Android/game project's plugins.
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path
import shutil
from urllib.request import urlopen
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / "game" / "tracks" / "serpent_sculpt"
VERSION = "v1.1.0-stable"
DOWNLOAD = (
    f"https://github.com/TokisanGames/Terrain3D/releases/download/{VERSION}/"
    "Terrain3D_v1.1.0-stable.zip"
)


def install_plugin() -> None:
    target = HERE / "addons" / "terrain_3d"
    if (target / "plugin.cfg").is_file():
        print("Pinned editor plugin already present:", target)
        return
    print("Downloading Terrain3D", VERSION)
    with urlopen(DOWNLOAD, timeout=90) as request:
        payload = request.read()
    count = 0
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        for member in archive.infolist():
            name = member.filename.replace("\\", "/")
            needle = "addons/terrain_3d/"
            start = name.find(needle)
            if start < 0 or member.is_dir():
                continue
            relative = Path(name[start + len(needle):])
            if not relative.parts or ".." in relative.parts:
                raise ValueError(f"Unsafe Terrain3D entry: {name}")
            dest = target / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, dest.open("wb") as output:
                shutil.copyfileobj(source, output)
            count += 1
    if not (target / "plugin.cfg").is_file():
        raise RuntimeError("Terrain3D archive did not include addons/terrain_3d/plugin.cfg")
    print(f"Installed {count} authoring-only Terrain3D files into {target}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--install-terrain3d", action="store_true")
    args = parser.parse_args()
    height = SOURCE / "height.r16"
    route = SOURCE / "route.json"
    if not height.is_file() or height.stat().st_size != 1024 * 512 * 2:
        raise RuntimeError("First sync game/tracks/serpent_sculpt/height.r16 from SceneForge")
    HERE.joinpath("heightmaps").mkdir(exist_ok=True)
    shutil.copyfile(height, HERE / "heightmaps" / "serpent_seed.r16")
    shutil.copyfile(route, HERE / "serpent_route.json")
    if args.install_terrain3d:
        install_plugin()
    print("Prepared 1-meter sculpt source and guide route.")
    print("Open tools/serpent_terrain_editor/project.godot in Godot 4.5.")
    print("Terrain3D authoring is editor-only; the game and Android APK stay plugin-free.")


if __name__ == "__main__":
    main()
