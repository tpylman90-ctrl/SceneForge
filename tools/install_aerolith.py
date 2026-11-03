"""Install the pinned, ORIGINAL AEROLITH Blender models from public Assetwright.

The immutable version-specific release is fetched and hash checked before
SceneForge imports the GLBs. The 31K-triangle LOD1 is for racing; the 58K
LOD0 is for garage/Fleet inspection. No Tripo or user-uploaded geometry is
used for AEROLITH and neither Shrike nor Tremor is changed by this installer.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import urllib.request
import shutil

ROOT=Path(__file__).resolve().parent.parent
RELEASE="aerolith-328d9de29b"
BASE=f"https://github.com/tpylman90-ctrl/Assetwright/releases/download/{RELEASE}"
ASSETS=[
    ("aerolith_ax01_lod1.glb", "game/assets/fleet/aerolith.glb",
     "938eb2c6d37ad568bcdb7338929f081a49481567de0ab333e8f4244bec5e7c7c",2902940),
    ("aerolith_ax01.glb", "game/assets/showroom/aerolith.glb",
     "7276a578572e7100c5c52a703a236945dc6c2a773905c13a40c49eb3922d04be",3527200)
]


def inspect_glb(path: Path) -> tuple[int,int]:
    with path.open("rb") as f:
        header=f.read(12)
        if len(header)!=12:
            raise ValueError("Truncated glTF header")
        magic,version,length=struct.unpack("<4sII",header)
        if magic!=b"glTF" or version!=2 or length!=path.stat().st_size:
            raise ValueError("GLB magic/version/length mismatch")
        size,kind=struct.unpack("<I4s",f.read(8))
        if kind!=b"JSON" or size>8_000_000:raise ValueError("Invalid GLB JSON")
        data=json.loads(f.read(size))
    if data.get("extensionsRequired"):
        raise ValueError("Unsupported mandatory glTF extension")
    names=[m.get("name","") for m in data.get("meshes",[])]
    if not names or not any("MONOCOQUE" in n for n in names):
        raise ValueError("Missing original AEROLITH monocoque")
    total=0
    for mesh in data.get("meshes",[]):
        for prim in mesh.get("primitives",[]):
            acc=prim.get("indices")
            count=data["accessors"][acc]["count"] if acc is not None else data["accessors"][prim["attributes"]["POSITION"]]["count"]
            if count%3:raise ValueError("Nontriangular GLB primitive")
            total+=count//3
    if not 20000<=total<=75000:
        raise ValueError(f"Unexpected AEROLITH polygon count: {total}")
    return total,len(names)


def install() -> None:
    for filename,target_name,expected,size in ASSETS:
        dest=ROOT/target_name
        dest.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=dest.parent,delete=False,
                                         suffix=".glb.tmp") as temporary:
            temp=Path(temporary.name)
        try:
            request=urllib.request.Request(f"{BASE}/{filename}",
                headers={"User-Agent":"SceneForge-Aerolith-Installer/1.0"})
            digest=hashlib.sha256()
            n=0
            with urllib.request.urlopen(request,timeout=90) as response, temp.open("wb") as stream:
                while block:=response.read(128*1024):
                    stream.write(block)
                    digest.update(block)
                    n+=len(block)
            if digest.hexdigest()!=expected or n!=size:
                raise ValueError(f"Downloaded model checksum/length mismatch: {filename}")
            triangles,meshes=inspect_glb(temp)
            temp.replace(dest)
            print("SCENEFORGE_AEROLITH_ASSET_OK",json.dumps({
                "asset":target_name,"triangles":triangles,"meshes":meshes,
                "sha256":expected,"source_release":RELEASE}),flush=True)
        finally:
            temp.unlink(missing_ok=True)


if __name__=="__main__":
    install()
