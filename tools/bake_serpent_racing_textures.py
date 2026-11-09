#!/usr/bin/env python3
"""Bake one original sandstone atlas and one subtle asphalt map (512px each).

Pure Python stdlib: no on-device work, no external texture licenses, no normal
maps. Four atlas quadrants have 3px inset UV margins authored in Blender.
"""
from pathlib import Path
from math import sin, cos, pi
import hashlib
import struct
import zlib

SIZE = 512
HALF = SIZE // 2
TAU = 2.0 * pi

def chunk(kind: bytes, data: bytes) -> bytes:
    return (struct.pack(">I", len(data)) + kind + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))

def emit_png(path: Path, pixels: bytes) -> None:
    assert len(pixels) == SIZE * SIZE * 3
    compressor = zlib.compressobj(level=6)
    sections = []
    width = SIZE * 3
    for y in range(SIZE):
        part = compressor.compress(b"\x00" + pixels[y * width:(y + 1) * width])
        if part:
            sections.append(part)
    sections.append(compressor.flush())
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", b"".join(sections))
        + chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)
    print("SERPENT_512_ATLAS_OK", path.name, len(png),
          hashlib.sha256(png).hexdigest())

def sandstone_rgb(x: int, y: int) -> tuple[int, int, int]:
    tile = (x // HALF) + 2 * (y // HALF)
    u = (x % HALF) / HALF
    v = (y % HALF) / HALF
    palettes = ((168, 109, 77), (126, 77, 56),
                (190, 143, 101), (140, 95, 72))
    base = palettes[tile]
    # Seamless because every oscillation has whole-number tile periods.
    shelf = 0.045 * sin(TAU * (9 * v + 0.085 * sin(TAU * 2 * u)))
    sediment = 0.027 * sin(TAU * (20 * v + 0.042 * sin(TAU * 3 * u)))
    long_erosion = 0.052 * sin(TAU * (3 * u + 2 * v))
    crack = max(0.0, 0.082 - abs(sin(TAU * (6 * u + 0.055 * sin(TAU * 2 * v)))))
    grain = (0.014 * sin(TAU * (37 * u + 43 * v))
             + 0.008 * cos(TAU * (71 * u - 58 * v)))
    variation = 1.0 + shelf + sediment + long_erosion + grain - crack * 0.62
    # Light strips are baked, not another sampling pass in the mobile shader.
    if tile == 2:
        variation += 0.035
    elif tile == 1:
        variation -= 0.045
    return tuple(max(0, min(255, round(vv * variation))) for vv in base)

def asphalt_rgb(x: int, y: int) -> tuple[int, int, int]:
    u = x / SIZE
    v = y / SIZE
    # Deliberately subtle near-white tint multiplied with existing #464348
    # asphalt base and cross-road vertex colors.
    broad = sin(TAU * (3 * u + 2 * v)) * 0.024
    grain = sin(TAU * (39 * u + 43 * v)) * 0.012
    fine = cos(TAU * (73 * u - 67 * v)) * 0.009
    dark_fissure = max(0.0, 0.032 - abs(sin(TAU * (5 * u + 0.038 * sin(TAU * 4 * v))))) * 0.43
    t = max(0.82, min(1.0, 0.955 + broad + grain + fine - dark_fissure))
    value = round(t * 255)
    return value, round(value * 0.991), round(value * 0.986)

def make_pixels(fn) -> bytes:
    data = bytearray(SIZE * SIZE * 3)
    index = 0
    for y in range(SIZE):
        for x in range(SIZE):
            r, g, b = fn(x, y)
            data[index:index + 3] = bytes((r, g, b))
            index += 3
    return bytes(data)

def main():
    root = Path.cwd() / "game/tracks/serpent_textures"
    emit_png(root / "rock_atlas_512.png", make_pixels(sandstone_rgb))
    emit_png(root / "asphalt_512.png", make_pixels(asphalt_rgb))

if __name__ == "__main__":
    main()
