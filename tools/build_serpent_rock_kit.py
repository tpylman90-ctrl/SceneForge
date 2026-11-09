"""Original Blender 4.5 Crimson Serpent cliff kit, generated before Godot import.

No paid services, imported meshes, AI models, runtime modifiers or texture
baking on Android. All six source meshes are exported as reusable UV-mapped GLBs.
"""
import bpy
import json
import math
import random
import struct
from pathlib import Path

ROOT = Path.cwd()
DEST = ROOT / "game/assets/scenery/serpent"
REPORT = ROOT / "build/serpent-kit-report.json"
DEST.mkdir(parents=True, exist_ok=True)
REPORT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# width X, face thickness Y, upright Z (export_yup converts Z to Godot Y).
SPEC = {
    "wall_a": (19.0, 17.0, 3.0, 17, 0),
    "wall_b": (25.0, 21.0, 4.2, 31, 1),
    "wall_c": (16.0, 15.0, 3.1, 49, 2),
    "ledge_a": (11.5, 4.2, 4.5, 73, 2),
    "ledge_b": (14.0, 3.6, 5.1, 101, 3),
}
BUDGET = {"wall_a": 750, "wall_b": 750, "wall_c": 750,
          "ledge_a": 750, "ledge_b": 750, "boulder_a": 150}

def atlas_uv(tile, u, v):
    # A 3 pixel bleed guard at 512px resolution: no adjacent atlas tiles.
    px, py = tile % 2, tile // 2
    return (px * 0.5 + 0.008 + 0.484 * min(1, max(0, u)),
            py * 0.5 + 0.008 + 0.484 * min(1, max(0, v)))

def rock_piece(name, width, height, depth, seed, tile):
    rng = random.Random(seed)
    ledge = name.startswith("ledge")
    nx, nz = (10, 6) if ledge else (12, 8)
    vertices, uv_by_index = [], []
    # Front rock surface and recessed back surface form a solid, closed mesh.
    for side in range(2):
        for j in range(nz + 1):
            v = j / nz
            for i in range(nx + 1):
                u = i / nx
                corner_noise = 0.26 * math.sin(i * 1.63 + j * 0.83 + seed)
                x = width * (u - 0.5)
                x += (0.19 if ledge else 0.45) * math.sin(v * 8.8 + seed * 0.7) * math.sin(math.pi * u)
                z = height * v + corner_noise * v * (1.0 - v)
                bedding = 0.34 * math.sin(v * 22 + seed * 0.11) + 0.18 * math.cos(v * 34 + u * 11)
                fissure = -0.86 * math.exp(-((u - (0.27 + 0.075 * math.sin(v * 7 + seed))) / 0.065) ** 2)
                fissure += -0.62 * math.exp(-((u - (0.69 + 0.045 * math.cos(v * 10 + seed))) / 0.06) ** 2)
                terraces = (0.48 if v < 0.39 else (-0.30 if v < 0.69 else 0.12))
                if ledge:
                    terraces = (1.85 if v > 0.54 else 0.48)
                face = 0.16 * depth + terraces + bedding + fissure
                face += 0.28 * math.sin(i * 0.9 + j * 1.7 + seed)
                y = (-depth + 0.05 * math.sin(j + i)) if side else face
                vertices.append((x, y, z))
                uv_by_index.append(atlas_uv(tile, u, v))
    stride = (nx + 1) * (nz + 1)
    def vert(side, i, j):
        return side * stride + j * (nx + 1) + i
    faces = []
    for j in range(nz):
        for i in range(nx):
            a, b = vert(0, i, j), vert(0, i + 1, j)
            c, d = vert(0, i + 1, j + 1), vert(0, i, j + 1)
            faces.extend(((a, c, b), (a, d, c)))
            e, f = vert(1, i, j), vert(1, i + 1, j)
            g, h = vert(1, i + 1, j + 1), vert(1, i, j + 1)
            faces.extend(((e, f, g), (e, g, h)))
    # Close perimeter and underside. No paper-thin / vanishing cliff faces.
    for j in range(nz):
        for i in (0, nx):
            a, b = vert(0, i, j), vert(0, i, j + 1)
            c, d = vert(1, i, j + 1), vert(1, i, j)
            faces.extend(((a, b, c), (a, c, d)))
    for i in range(nx):
        for j in (0, nz):
            a, b = vert(0, i, j), vert(0, i + 1, j)
            c, d = vert(1, i + 1, j), vert(1, i, j)
            faces.extend(((a, b, c), (a, c, d)))
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for polygon in mesh.polygons:
        polygon.use_smooth = False
        for loop_id in polygon.loop_indices:
            vid = mesh.loops[loop_id].vertex_index
            uv_layer.data[loop_id].uv = uv_by_index[vid]
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj

def boulder(name):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0)
    obj = bpy.context.object
    obj.name = name
    mesh = obj.data
    for i, vert in enumerate(mesh.vertices):
        angle = i * 2.3999632
        scale = 0.83 + 0.16 * math.sin(i * 2.1) + 0.075 * math.cos(i * 4.2)
        vert.co.x *= scale * 1.28
        vert.co.y *= scale * 0.92
        vert.co.z *= scale * 0.76
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        poly.use_smooth = False
        for l in poly.loop_indices:
            v = mesh.vertices[mesh.loops[l].vertex_index].co
            u = (math.atan2(v.y, v.x) / (2.0 * math.pi) + 0.5) % 1.0
            vv = max(0.0, min(1.0, 0.5 + 0.46 * v.z))
            uv_layer.data[l].uv = atlas_uv(3, u, vv)
    return obj

objects = [rock_piece(key, *values) for key, values in SPEC.items()]
objects.append(boulder("boulder_a"))
report = []
for obj in objects:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    dest = DEST / (obj.name + ".glb")
    bpy.ops.export_scene.gltf(
        filepath=str(dest), export_format="GLB", use_selection=True,
        export_yup=True, export_texcoords=True, export_normals=True,
        export_materials="NONE", export_animations=False
    )
    triangles = sum(len(face.vertices) - 2 for face in obj.data.polygons)
    assert 12 < triangles < BUDGET[obj.name], (obj.name, triangles)
    assert dest.stat().st_size > 400, dest
    raw = dest.read_bytes()
    assert raw[:4] == b"glTF" and struct.unpack_from("<I", raw, 8)[0] == len(raw)
    report.append({"asset": obj.name, "triangles": triangles,
                   "bytes": dest.stat().st_size, "mesh_instances": 1})
    print("SERPENT_BLENDER_ASSET_OK", obj.name, triangles, dest.stat().st_size)
assert sum(x["triangles"] for x in report) < 3500
REPORT.write_text(json.dumps({"asset_family": "Crimson Serpent rock modules",
    "license": "Original authored procedural Blender work",
    "source": "tools/build_serpent_rock_kit.py", "assets": report,
    "total_unique_triangles": sum(x["triangles"] for x in report),
    "blender_version": bpy.app.version_string}, indent=2))
print("SERPENT_BLENDER_KIT_OK", len(report), sum(x["triangles"] for x in report))
