#!/usr/bin/env python3
"""Enforce and verify Android 3D texture imports for Crimson Serpent.

Usage:
  python3 tools/ensure_serpent_texture_import.py configure
  godot --headless --path game --editor --import
  python3 tools/ensure_serpent_texture_import.py verify

Godot first creates valid .png.import remap/dependency paths. We change only
its [params] and invalidate the three pre-existing derived .ctex/.md5 files.
The second editor import then generates S3TC for desktop and ETC2 for Android
with mipmaps. No image decompression/texture baking occurs in the APK.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "game"
ASSETS = (
    ("rock_atlas_1024.png", 1024),
    ("terrain_sandstone_1024.png", 1024),
    ("asphalt_512.png", 512),
)
SOURCE = ROOT / "tracks" / "serpent_textures"
IMPORT_DIR = ROOT / ".godot" / "imported"

# Godot 4.5 ResourceImporterTexture: VRAM Compressed = 2; disable ASTC/BC7
# because SceneForge intentionally retains the GL Compatibility renderer.
OPTIONS = {
    "compress/mode": "2",
    "compress/high_quality": "false",
    "mipmaps/generate": "true",
    "detect_3d/compress_to": "1",
}

def import_config(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"Godot did not generate import configuration: {path}")
    source = path.read_text(encoding="utf-8")
    if '[remap]' not in source or '[params]' not in source:
        raise AssertionError(f"Invalid .import sidecar: {path}")
    return source

def setting(data: str, key: str) -> str | None:
    result = re.search(r"^" + re.escape(key) + r"\s*=\s*([^\r\n]+)",
                       data, re.MULTILINE)
    return result.group(1).strip() if result else None

def configure() -> None:
    IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    for name, _dimension in ASSETS:
        source = SOURCE / name
        if not source.is_file():
            raise AssertionError(f"Missing offline-baked texture: {source}")
        path = SOURCE / (name + ".import")
        config = import_config(path)
        for key, value in OPTIONS.items():
            pattern = re.compile(r"^" + re.escape(key) + r"\s*=\s*[^\r\n]+", re.MULTILINE)
            entry = f"{key}={value}"
            if pattern.search(config):
                config = pattern.sub(entry, config, count=1)
            else:
                config = config.replace("[params]\n", "[params]\n" + entry + "\n", 1)
        path.write_text(config, encoding="utf-8")
        # Force Godot to rebuild with our options, rather than continuing to
        # use an old lossless .ctex produced by the initial import.
        invalidated = 0
        for derived in IMPORT_DIR.glob(name + "-*"):
            if derived.suffix in (".ctex", ".md5"):
                derived.unlink()
                invalidated += 1
        print("SERPENT_TEXTURE_IMPORT_CONFIGURED", name, invalidated)

def verify() -> None:
    for name, dimension in ASSETS:
        path = SOURCE / (name + ".import")
        data = import_config(path)
        for key, value in OPTIONS.items():
            actual = setting(data, key)
            if actual != value:
                raise AssertionError(f"{name} {key}={actual!r}, expected {value!r}")
        if '"vram_texture": true' not in data:
            raise AssertionError(f"{name} was not imported as a GPU texture")
        match = re.search(r'^path\.etc2="(res://[^"]+\.etc2\.ctex)"', data, re.MULTILINE)
        if not match:
            raise AssertionError(f"{name} has no Android ETC2 import variant")
        rel = match.group(1).removeprefix("res://")
        etc2 = ROOT / rel
        if not etc2.is_file() or etc2.stat().st_size < 64:
            raise AssertionError(f"{name} ETC2 asset missing or empty: {etc2}")
        png = SOURCE / name
        with png.open("rb") as f:
            header = f.read(24)
        if header[:8] != b"\x89PNG\r\n\x1a\n":
            raise AssertionError(f"{name} is not a PNG")
        if (int.from_bytes(header[16:20], "big"),
            int.from_bytes(header[20:24], "big")) != (dimension, dimension):
            raise AssertionError(f"{name} dimensions changed unexpectedly")
        print("SERPENT_ETC2_MIPMAP_OK", name, dimension,
              "etc2_bytes", etc2.stat().st_size, "source_bytes", png.stat().st_size)

if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("command", choices=("configure", "verify"))
    args = cli.parse_args()
    (configure if args.command == "configure" else verify)()
