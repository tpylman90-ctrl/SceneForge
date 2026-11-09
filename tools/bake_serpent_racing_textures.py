#!/usr/bin/env python3
"""Offline bake: 1024px rock atlas, 512px road and 1024px terrain albedo.

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


def _lattice_hash(x: int, y: int, seed: int) -> float:
    """Deterministic 2D hash; used only during offline texture baking."""
    n = (x * 374761393 + y * 668265263 + seed * 1442695041) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return (((n ^ (n >> 16)) & 65535) / 32767.5) - 1.0


def _seamless_noise(u: float, v: float, period: int, seed: int) -> float:
    """Tileable smooth value noise, unlike fixed-frequency sinusoid stripes."""
    x, y = u * period, v * period
    ix, iy = int(x), int(y)
    fx, fy = x - ix, y - iy
    sx, sy = fx * fx * (3.0 - 2.0 * fx), fy * fy * (3.0 - 2.0 * fy)
    x0, x1 = ix % period, (ix + 1) % period
    y0, y1 = iy % period, (iy + 1) % period
    a = _lattice_hash(x0, y0, seed)
    b = _lattice_hash(x1, y0, seed)
    c = _lattice_hash(x0, y1, seed)
    d = _lattice_hash(x1, y1, seed)
    return ((a + (b - a) * sx) * (1.0 - sy)
            + (c + (d - c) * sx) * sy)


def terrain_sandstone_rgb(x: int, y: int) -> tuple[int, int, int]:
    """Original 1024px sandstone color relief. All layers baked, one GPU read.

    Broad oxidation bleeds, warped sediment layers, recessed wash lines and
    sand-grain breakup have distinct scales. Periodic noise ensures the texture
    wraps without a visible seam. Vertex colors still provide large canyon tint.
    """
    u, v = x / SIZE, y / SIZE
    macro = 0.085 * _seamless_noise(u, v, 3, 8)
    macro += 0.065 * _seamless_noise(u, v, 9, 17)
    warp = 0.050 * _seamless_noise(u, v, 4, 91)
    warp += 0.027 * sin(TAU * (2 * u + v))
    strata = sin(TAU * (7 * v + warp))
    fine_strata = sin(TAU * (23 * v + warp * 0.74 + 0.022 * sin(TAU * 3 * u)))
    silt = 0.037 * _seamless_noise(u, v, 38, 124)
    pores = 0.016 * _seamless_noise(u, v, 117, 275)
    weathered = 0.039 * sin(TAU * (3 * u + 2 * v))
    weathered += 0.021 * cos(TAU * (5 * u - 3 * v))
    fracture_warp = 0.045 * sin(TAU * (2 * v + u))
    fissure = abs(sin(TAU * (4 * u + fracture_warp)))
    fissure = 0.087 * max(0.0, (0.13 - fissure) / 0.13)
    soft_seam = 0.050 * max(0.0, (0.14 - abs(strata)) / 0.14)
    brightness = (0.920 + macro + 0.060 * strata + 0.026 * fine_strata
                  + weathered + silt + pores - fissure - soft_seam)
    brightness = max(0.67, min(1.0, brightness))
    value = max(0, min(255, round(255 * brightness)))
    return value, round(value * 0.979), round(value * 0.952)


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
    # The canyon gets a denser color *source*, still only one albedo fetch
    # per rendered pixel. ETC2/mipmaps are applied during Godot import.
    SIZE, HALF = 1024, 512
    emit_png(root / "terrain_sandstone_1024.png", make_pixels(terrain_sandstone_rgb))

if __name__ == "__main__":
    main()
