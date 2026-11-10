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
    """Offline four-palette sediment atlas: coherent layers, fractured oxide.

    Each tile is seeded separately but all its color variation is periodic
    within the tile. Do not stack textures on Android; the single imported
    ETC2 image includes the complete color/strata/weathering treatment.
    """
    tile = (x // HALF) + 2 * (y // HALF)
    u, v = (x % HALF) / HALF, (y % HALF) / HALF
    palettes = ((182, 121, 85), (140, 92, 69),
                (213, 165, 116), (157, 110, 79))
    base = palettes[tile]
    seed = 13 + tile * 23
    coarse = _seamless_noise(u, v, 3, seed)
    middle = _seamless_noise(u, v, 11, seed + 1)
    grit = _seamless_noise(u, v, 44, seed + 2)
    warp = 0.085 * _seamless_noise(u, v, 4, seed + 3)
    warp += 0.034 * sin(TAU * (2 * u + v))
    # Sediment planes are interrupted by large eroded, staggered deposits.
    beds = sin(TAU * (5 * v + warp))
    undercut = max(0.0, (0.25 - abs(beds)) / 0.25)
    oxidation = 0.095 * coarse + 0.048 * middle
    salt = 0.033 * sin(TAU * (3 * u + 2 * v))
    pore = 0.018 * grit
    seam = 0.10 * undercut * (0.72 + 0.28 * middle)
    scar_u = 3.0 * u + 0.078 * sin(TAU * (2 * v + warp))
    fracture = max(0.0, (0.13 - abs(sin(TAU * scar_u))) / 0.13)
    variation = 0.955 + oxidation + 0.050 * beds + salt + pore
    variation -= seam + 0.085 * fracture
    variation = max(0.67, min(1.16, variation))
    # Shade fissures toward warm iron rather than simply black.
    iron = max(0.0, coarse + middle * 0.5)
    r = base[0] * variation * (1.0 + 0.038 * iron)
    g = base[1] * variation * (1.0 - 0.028 * iron)
    b = base[2] * variation * (1.0 - 0.038 * iron)
    return tuple(max(0, min(255, round(n))) for n in (r, g, b))


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
    """Racing-grade sandstone surface: weathered, fine, and non-mechanical.

    This is COLOR baked entirely offline, not per-pixel shader noise.
    Half-tones stay light enough to multiply with the hand-tuned terrain
    vertex palette. The world UV mapping defines the visible rock scale.
    """
    u, v = x / SIZE, y / SIZE
    broad = _seamless_noise(u, v, 3, 8)
    large = _seamless_noise(u, v, 7, 17)
    mid = _seamless_noise(u, v, 19, 45)
    fine = _seamless_noise(u, v, 61, 124)
    grit = _seamless_noise(u, v, 127, 275)
    # Organic, winding sediment bands cross the whole atlas continuously.
    warp = 0.087 * _seamless_noise(u, v, 4, 91)
    warp += 0.032 * _seamless_noise(u, v, 9, 92)
    warp += 0.016 * sin(TAU * (3 * u - 2 * v))
    bed = sin(TAU * (5 * v + warp))
    thin_bed = sin(TAU * (17 * v + warp * 0.60 + 0.02 * mid))
    wash = max(0.0, (0.22 - abs(bed)) / 0.22)
    fracture_u = 3 * u + 0.035 * sin(TAU * (2 * v + warp))
    joint = max(0.0, (0.09 - abs(sin(TAU * fracture_u))) / 0.09)
    # Recessed crevices and rust-colored weathering separated by scale.
    rust = max(0.0, broad * 0.6 + large * 0.4 + 0.19)
    relief = 0.91 + 0.095 * broad + 0.067 * large + 0.037 * mid
    relief += 0.050 * bed + 0.024 * thin_bed + 0.025 * fine + 0.013 * grit
    relief -= 0.080 * wash + 0.068 * joint
    relief = max(0.69, min(1.055, relief))
    # Warm sandstone instead of grayscale multiplication: subtle and
    # pigment-aware, with pale chalk veins and richer weathered iron.
    r = 252 * relief * (1.0 + 0.036 * rust)
    g = 244 * relief * (1.0 - 0.023 * rust)
    b = 230 * relief * (1.0 - 0.050 * rust)
    return tuple(max(0, min(255, round(n))) for n in (r, g, b))

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
