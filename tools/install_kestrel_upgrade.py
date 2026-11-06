"""Install the user-supplied Kestrel 3D upgrade without replacing its cockpit rig.

Source is a preserved uploaded original and a prepared, rotated, metrically
scaled racing GLB stored in the repository as a compact XZ archive. The game
loads the standard glTF 2.0 binary, not the Meshopt-only uploader original.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import lzma
import struct
from pathlib import Path
from refine_kestrel_upgrade import refine

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "showroom_sources/Kestrel_User_Upgrade_GameReady.glb.xz"
RAW_SOURCE = ROOT / "showroom_sources/Kestrel_User_Upgrade_Source_Meshopt.glb"
DEST = ROOT / "game/assets/showroom/kestrel_user_upgrade.glb"
SOURCE_SHA256 = "2a436ee1e67b6e3df51d70033cb7546f531bf719fd940ef28020b8bd5a0d88aa"
PREPARED_SHA256 = "06d6b9f6dc1147296aa7bdb4a78a8d2b5aaa421f1319d20a5dfcef11ddbcc9c9"
EXPECTED_TRIANGLES = 39464
EXPECTED_VERTEX_COUNT = 20955


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inspect_gltf(data: bytes) -> dict:
    assert data[:4] == b"glTF", "Expected genuine GLB signature"
    version, declared_length = struct.unpack_from("<II", data, 4)
    assert version == 2 and declared_length == len(data)
    json_len, chunk_type = struct.unpack_from("<I4s", data, 12)
    assert chunk_type == b"JSON"
    info = json.loads(data[20:20 + json_len].decode("utf-8"))
    assert "EXT_meshopt_compression" not in info.get("extensionsRequired", []), (
        "Meshopt-only GLB cannot import in Godot 4.5; use prepared standard asset")
    assert len(info.get("meshes", [])) == 1
    mesh = info["meshes"][0]
    prim = mesh["primitives"]
    assert len(prim) == 1
    assert prim[0].get("mode", 4) == 4
    accessors = info["accessors"]
    triangles = accessors[prim[0]["indices"]]["count"] // 3
    vertices = accessors[prim[0]["attributes"]["POSITION"]]["count"]
    assert triangles == EXPECTED_TRIANGLES and vertices == EXPECTED_VERTEX_COUNT, (
        "Kestrel geometry counts no longer match uploaded user model")
    assert "COLOR_0" in prim[0]["attributes"], "Kestrel body tint vertex colors missing"
    p = accessors[prim[0]["attributes"]["POSITION"]]
    extent = [b-a for a,b in zip(p["min"],p["max"])]
    assert 3.4 < extent[0] < 3.8 and 6.7 < extent[2] < 6.9
    assert p["min"][1] > 0.25 and p["max"][1] < 2.35
    assert mesh.get("name") == "Kestrel_User_Upgrade_Exterior"
    return {"triangles": triangles, "vertices": vertices, "bounds_m": extent}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--required", action="store_true")
    args = parser.parse_args()
    if not ARCHIVE.is_file():
        if args.required:
            raise FileNotFoundError(ARCHIVE)
        print("SCENEFORGE_KESTREL_UPGRADE_NOT_INSTALLED")
        return
    if RAW_SOURCE.is_file():
        assert sha256(RAW_SOURCE.read_bytes()) == SOURCE_SHA256, (
            "Original Kestrel source SHA mismatch")
    standard = lzma.decompress(ARCHIVE.read_bytes())
    assert sha256(standard) == PREPARED_SHA256, (
        "Prepared Kestrel GLB was changed without review")
    report = inspect_gltf(standard)
    # Repair shading and glass, but never overwrite or mutate the original
    # user source, compressed input or its SHA-pinned game-ready baseline.
    polished, quality = refine(standard)
    assert 36000 < quality["triangles"] < EXPECTED_TRIANGLES
    assert quality["glass_triangles"] > 4000
    assert quality["source_islands"] >= 100
    assert quality["rear_tip_z"] > -3.2
    assert quality["smooth_vertex_normals"]
    assert quality["transparent_glass_surface"]
    repaired, _ = __import__("refine_kestrel_upgrade").unpack_glb(polished)
    components = repaired["meshes"][0]["primitives"]
    assert len(components) == 2
    assert all("NORMAL" in part["attributes"] for part in components)
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_bytes(polished)
    assert DEST.stat().st_size > 600_000
    print("SCENEFORGE_KESTREL_MESH_REFINEMENT_OK",quality)
    print("SCENEFORGE_KESTREL_USER_UPGRADE_OK", DEST, report)


if __name__ == "__main__":
    main()
