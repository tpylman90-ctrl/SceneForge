#!/usr/bin/env python3
"""Bake one original 1024px sandstone atlas and a lightweight 512px road map.

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
    tile = (x // HALF) + 2 * (y // HALF)
    u = (x % HALF) / HALF
    v = (y % HALF) / HALF
    palettes = ((190, 118, 76), (126, 71, 51),
                (216, 168, 109), (156, 97, 67))
    base = palettes[tile]
    # 2D sediment benches, variegated rusty oxide, deep fracture seams.
    # Multiple whole-number harmonics remain seamlessly tileable.
    warp = 0.093 * sin(TAU * 2 * u) + 0.021 * sin(TAU * (5 * u + 3 * v))
    bedding = sin(TAU * (11 * v + warp))
    sediment = 0.057 * sin(TAU * (23 * v + .045 * sin(TAU * 3 * u)))
    macro = 0.13 * sin(TAU * (3 * u + 2 * v))
    macro += 0.058 * cos(TAU * (4 * u - 3 * v))
    swash = 0.06 * sin(TAU * (2 * u + 7 * v))
    narrow_seam = max(0.0, (0.15 - abs(bedding))/0.15) * 0.17
    deep_scar = max(0.0, (0.105 - abs(sin(TAU * (6 * u + .075 * sin(TAU * 2 * v)))))/0.105)
    deep_scar *= (0.55 + 0.45 * sin(TAU * (3 * v + 2 * u)))
    chips = 0.021 * sin(TAU * (63 * u + 47 * v))
    chips += 0.014 * cos(TAU * (87 * u - 59 * v))
    variation = (0.94 + 0.075*bedding + sediment + macro + swash + chips
                 - narrow_seam - 0.24*deep_scar)
    if tile == 2:
        variation += 0.045
    elif tile == 1:
        variation -= 0.045
    variation=max(0.58,min(1.25,variation))
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
    global SIZE, HALF
    root = Path.cwd() / "game/tracks/serpent_textures"
    SIZE, HALF = 1024, 512
    emit_png(root / "rock_atlas_1024.png", make_pixels(sandstone_rgb))
    # Keep road sampling, memory footprint and capture budget unchanged.
    SIZE, HALF = 512, 256
    emit_png(root / "asphalt_512.png", make_pixels(asphalt_rgb))

if __name__ == "__main__":
    main()
