"""Install a user-supplied, already oriented Shrike GLB for showroom-only usage.

The source file is deliberately outside game/assets, so the Actions asset cache
cannot overwrite it. It is copied unchanged after any generated vehicle builds.

Usage:
    python tools/install_showroom_shrike.py
    python tools/install_showroom_shrike.py --required

Expected source: showroom_sources/shrike_uploaded.glb
Game destination: game/assets/showroom/shrike_uploaded.glb
"""
import argparse
import hashlib
import json
import shutil
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "showroom_sources" / "shrike_uploaded.glb"
DST = ROOT / "game" / "assets" / "showroom" / "shrike_uploaded.glb"
REQUIRED = {"Kestrel_Hull", "Kestrel_Yoke"} | {
    f"Kestrel_Tail_{i}" for i in range(5)
}


def check_glb(path: Path) -> dict:
    with path.open("rb") as stream:
        head = stream.read(12)
        if len(head) != 12:
            raise ValueError("GLB header truncated")
        magic, version, total = struct.unpack("<4sII", head)
        if magic != b"glTF" or version != 2 or total != path.stat().st_size:
            raise ValueError("Not a valid glTF 2.0 binary")
        json_length, chunk_type = struct.unpack("<I4s", stream.read(8))
        if chunk_type != b"JSON" or json_length > 8_000_000:
            raise ValueError("Missing reasonable glTF JSON section")
        doc = json.loads(stream.read(json_length))
    nodes = {node.get("name") for node in doc.get("nodes", [])}
    missing = REQUIRED - nodes
    if missing:
        raise ValueError(f"Required SceneForge rig nodes missing: {sorted(missing)}")
    if not doc.get("meshes") or not doc.get("materials"):
        raise ValueError("Missing textured car geometry")
    if doc.get("extensionsRequired"):
        raise ValueError("GLB uses unsupported required compression extension")
    pos = doc["meshes"][0]["primitives"][0]["attributes"]["POSITION"]
    a = doc["accessors"][pos]
    span = [hi - lo for lo, hi in zip(a["min"], a["max"])]
    if not (3.0 < span[0] < 4.4 and 1.0 < span[1] < 3.0 and 5.0 < span[2] < 8.0):
        raise ValueError(f"Unexpected Shrike width/height/length: {span}")
    return {"nodes": len(nodes), "meshes": len(doc["meshes"]),
            "dimensions": [round(x, 3) for x in span],
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--required", action="store_true",
                        help="fail if the user GLB was not supplied")
    args = parser.parse_args()
    if not SRC.is_file():
        if args.required:
            raise SystemExit(f"Missing source GLB: {SRC}")
        print("SCENEFORGE_SHRIKE_SHOWROOM_NOT_INSTALLED: using procedural fallback")
        return
    report = check_glb(SRC)
    DST.parent.mkdir(parents=True, exist_ok=True)
    tmp = DST.with_suffix(".glb.tmp")
    shutil.copyfile(SRC, tmp)
    tmp.replace(DST)
    print("SCENEFORGE_SHRIKE_SHOWROOM_INSTALLED", json.dumps(report))


if __name__ == "__main__":
    main()
