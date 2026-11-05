#!/usr/bin/env python3
"""Bake original tileable 2K sandstone albedo and OpenGL normal PNG maps.

Standard library only. GitHub CI runs this *before* Godot's import step,
so mobile devices never execute millions of texture-generation operations.
No native plugins, external downloads, licensing constraints, or added mesh.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from math import pi, sin, sqrt
from pathlib import Path
import struct
import zlib

SIZE = 2048
TAU = 2.0 * pi


def _chunk(kind: bytes, data: bytes) -> bytes:
    body = kind + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))


def write_png(destination: Path, pixels: bytes | bytearray, channels: int) -> None:
    """Build an RGB PNG with built-in DEFLATE, no Pillow dependency."""
    if len(pixels) != SIZE * SIZE * channels:
        raise ValueError("Invalid texture buffer dimensions")
    destination.parent.mkdir(parents=True, exist_ok=True)
    compressor = zlib.compressobj(level=6)
    chunks = []
    row_size = SIZE * channels
    for y in range(SIZE):
        row = pixels[y * row_size: (y + 1) * row_size]
        packet = compressor.compress(b"\x00" + row)
        if packet:
            chunks.append(packet)
    chunks.append(compressor.flush())
    image = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", b"".join(chunks))
        + _chunk(b"IEND", b"")
    )
    destination.write_bytes(image)


def bake(output: Path) -> None:
    """Two tileable 2K maps sharing the same erosion and fracture profile."""
    out_color = output / "serpent_sandstone_albedo.png"
    out_normal = output / "serpent_sandstone_normal.png"
    heights = bytearray(SIZE * SIZE)
    albedo = bytearray(SIZE * SIZE * 3)
    x_macro = [sin(TAU * (6 * x / SIZE)) for x in range(SIZE)]
    x_cut = [sin(TAU * (17 * x / SIZE)) for x in range(SIZE)]
    x_warp = [sin(TAU * (3 * x / SIZE)) for x in range(SIZE)]
    x_grain = [sin(TAU * (49 * x / SIZE)) for x in range(SIZE)]
    for y in range(SIZE):
        v = y / SIZE
        y_macro = sin(TAU * 4 * v)
        y_warp = sin(TAU * 5 * v)
        y_cut = sin(TAU * (2 * v + 0.1 * y_macro))
        y_grain = sin(TAU * 47 * v)
        row = y * SIZE
        for x in range(SIZE):
            u = x / SIZE
            macro = 0.60 * x_macro[x] * y_macro + 0.40 * sin(TAU * (2 * u + 3 * v))
            bed = sin(TAU * (26 * v + 0.12 * x_warp[x] + 0.04 * y_macro))
            micro = 0.65 * x_grain[x] * y_grain + 0.35 * sin(TAU * (85 * u + 92 * v))
            crack_line = abs(sin(TAU * (11 * u + 0.05 * y_warp + 0.012 * y_cut)))
            fracture = max(0.0, (0.052 - crack_line) / 0.052)
            fracture *= max(0.0, 0.4 + 0.6 * sin(TAU * (5 * v + 0.15 * x_cut[x])))
            relief = 0.50 + 0.16 * macro + 0.13 * bed + 0.055 * micro - 0.19 * fracture
            idx = row + x
            heights[idx] = max(0, min(255, int(relief * 255 + 0.5)))
            intensity = max(0.56, min(1.0,
                0.89 + 0.055 * macro + 0.025 * bed + 0.024 * micro - 0.16 * fracture
            ))
            c = int(intensity * 255 + 0.5)
            k = idx * 3
            albedo[k:k + 3] = bytes((c, int(c * 0.985), int(c * 0.969)))
    normal = bytearray(SIZE * SIZE * 3)
    for y in range(SIZE):
        up = ((y - 1) % SIZE) * SIZE
        down = ((y + 1) % SIZE) * SIZE
        row = y * SIZE
        for x in range(SIZE):
            left = (x - 1) % SIZE
            right = (x + 1) % SIZE
            dx = (heights[row + right] - heights[row + left]) * 0.026
            dy = (heights[down + x] - heights[up + x]) * 0.026
            length = sqrt(dx * dx + dy * dy + 1.0)
            k = (row + x) * 3
            normal[k] = int(max(0, min(255, 127.5 * (-dx / length + 1))))
            normal[k + 1] = int(max(0, min(255, 127.5 * (-dy / length + 1))))
            normal[k + 2] = int(max(0, min(255, 127.5 * (1 / length + 1))))
    write_png(out_color, albedo, 3)
    write_png(out_normal, normal, 3)
    for path in (out_color, out_normal):
        print("SERPENT_TEXTURE_BAKE_OK", path, path.stat().st_size,
              sha256(path.read_bytes()).hexdigest())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("game/tracks/serpent_textures"))
    args = parser.parse_args()
    bake(args.output)


if __name__ == "__main__":
    main()
