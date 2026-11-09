#!/usr/bin/env python3
"""Offline bake: one 1024px rock atlas, 512px road and 512px terrain map.

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
    print("SERPENT_RACING_TEXTURE_OK", path.name, len(png),
          hashlib.sha256(png).hexdigest())

def sandstone_rgb(x: int, y: int) -> tuple[int, int, int]:
    """Four warm, softly banded sandstone variations, UV sampled just once."""
    tile = (x // HALF) + 2 * (y // HALF)
    u = (x % HALF) / HALF
    v = (y % HALF) / HALF
    palettes = ((177, 112, 79), (128, 82, 63),
                (203, 155, 109), (157, 111, 81))
    base = palettes[tile]
    # Gently warped sediment beds; broad oxidation patches and erosion
    # seams are all pre-baked. Whole-number harmonics tile in both axes.
    warping = .075*sin(TAU*2*u) + .035*sin(TAU*(3*u+v))
    bed = sin(TAU*(5*v + warping))
    fine_bed = sin(TAU*(17*v + .027*sin(TAU*(4*u+v))))
    oxide = .068*sin(TAU*(2*u+v)) + .040*cos(TAU*(3*u-2*v))
    mottling = .035*sin(TAU*(4*u+5*v))
    grain = .018*sin(TAU*(49*u+53*v)) + .012*cos(TAU*(71*u-63*v))
    seam = max(0.0, (0.15-abs(bed))/.15)
    fracture = max(0.0, (0.09-abs(sin(TAU*(3*u+.04*sin(TAU*2*v)))))/.09)
    variation = .97 + .060*bed + .031*fine_bed + oxide + mottling + grain
    variation -= .071*seam + .064*fracture
    if tile == 1:
        variation -= .027
    elif tile == 2:
        variation += .020
    variation = max(.77,min(1.16,variation))
    return tuple(max(0,min(255,round(ch*variation))) for ch in base)


def terrain_sandstone_rgb(x: int, y: int) -> tuple[int, int, int]:
    """Single 512px material for the *whole* canyon: strata without triplanar."""
    u = x / SIZE
    v = y / SIZE
    warped = .058*sin(TAU*2*u)+.021*sin(TAU*(5*u+v))
    band = sin(TAU*(5*v+warped))
    thin = sin(TAU*(19*v+.034*sin(TAU*3*u)))
    broad = .085*sin(TAU*(2*u+v))+.045*cos(TAU*(3*u-2*v))
    pock = .018*sin(TAU*(41*u+37*v))+.011*cos(TAU*(59*u-53*v))
    strata = .086*band+.025*thin
    seam = max(0.0, (.15-abs(band))/.15)*.085
    contrast = max(.73,min(1.03,.92+strata+broad+pock-seam))
    value = round(255*contrast)
    return value, round(value*.989), round(value*.976)

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
    global SIZE, HALF
    root = Path.cwd() / "game/tracks/serpent_textures"
    SIZE, HALF = 1024, 512
    emit_png(root / "rock_atlas_1024.png", make_pixels(sandstone_rgb))
    # Keep road sampling, memory footprint and capture budget unchanged.
    SIZE, HALF = 512, 256
    emit_png(root / "asphalt_512.png", make_pixels(asphalt_rgb))
    emit_png(root / "terrain_sandstone_512.png", make_pixels(terrain_sandstone_rgb))

if __name__ == "__main__":
    main()
