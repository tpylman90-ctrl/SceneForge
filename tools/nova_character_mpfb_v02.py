"""Nova v0.2 anatomical base — isolated SceneForge Blender/MPFB proof of concept.

Uses MPFB's CC0 human basemesh instead of hand-built spheres/cylinders.
This is a production base, NOT an approved character likeness or final outfit.
Never touches SceneForge game/ or generated runtime assets.
"""
import bpy
import json
import math
import random
import os
from pathlib import Path
from mathutils import Vector

ROOT = Path("build/nova-mpfb-v02")
ROOT.mkdir(parents=True, exist_ok=True)
random.seed(26)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# This add-on is installed from MakeHumanCommunity source by the CI workflow.
import addon_utils
addon_utils.enable("mpfb", default_set=False, persistent=False)
from mpfb.services.humanservice import HumanService
from mpfb.services.targetservice import TargetService
from mpfb.entities.objectproperties import HumanObjectProperties

body = HumanService.create_human(feet_on_ground=True)
body.name = "Nova_MakeHuman_CC0_Body"
bpy.context.view_layer.objects.active = body
body.select_set(True)
for name, value in (
    ("gender", 1.0), ("age", 0.50), ("muscle", 0.57),
    ("weight", 0.55), ("height", 0.52),
    ("african", 0.0), ("asian", 0.0), ("caucasian", 0.0),
):
    try:
        HumanObjectProperties.set_value(name, value, entity_reference=body)
    except Exception as ex:
        print("OPTIONAL_PHENOTYPE_SKIP", name, str(ex)[:100])
TargetService.reapply_macro_details(body)

# Normalize the generated anatomical human to meters without modifying mesh topology.
zs = [v.co.z for v in body.data.vertices]
bottom, top = min(zs), max(zs)
original_height = top - bottom
assert original_height > 0
s = 1.73 / original_height
for v in body.data.vertices:
    v.co = (v.co.x*s, v.co.y*s, (v.co.z-bottom)*s)
body.data.update()
for face in body.data.polygons:
    face.use_smooth = True

def mat(name, color, metallic=0.0, roughness=.44):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*color,1)
    bs.inputs["Metallic"].default_value=metallic
    bs.inputs["Roughness"].default_value=roughness
    return m
skin=mat("Skin_warm_stylized",(.65,.355,.25),0,.54)
cyan=mat("Racing_Cyan_PBR",(.012,.71,.9),.23,.23)
violet=mat("Racing_Violet_PBR",(.36,.045,.83),.25,.23)
black=mat("Racing_Black_PBR",(.028,.03,.055),.23,.3)
silver=mat("Metal_Chrome",(.6,.64,.76),.8,.2)
blonde=mat("Hair_Warm_Blonde",(.8,.62,.35),.0,.51)
blonde_hi=mat("Hair_Highlights",(.98,.84,.58),0,.48)
body.data.materials.clear()
body.data.materials.append(skin)

# Anatomically conformal garment sections — duplicate the human surface, not primitives.
def shell(name, filter_fn, material, offset=.009):
    verts=[]
    faces=[]
    idx={}
    for f in body.data.polygons:
        c=f.center
        if not filter_fn(c.x,c.y,c.z):
            continue
        new_face=[]
        for vi in f.vertices:
            vi=int(vi)
            if vi not in idx:
                idx[vi]=len(verts)
                v=body.data.vertices[vi]
                verts.append(tuple(v.co + v.normal*offset))
            new_face.append(idx[vi])
        faces.append(new_face)
    if not faces:
        print("WARN_NO_FACES", name)
        return None
    me=bpy.data.meshes.new(name+"Mesh")
    me.from_pydata(verts,[],faces)
    me.update()
    obj=bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    for f in me.polygons: f.use_smooth=True
    solid=obj.modifiers.new("Cloth thickness","SOLIDIFY")
    solid.thickness=.004
    return obj

# MPFB produces an upright character. Keep her body in A-pose for future rig work.
shell("Nova_Cyan_Jacket_Upper",lambda x,y,z: 1.17<z<1.43 and abs(x)<.36 and y>.005,cyan)
shell("Nova_Violet_Jacket_RightSleeve",lambda x,y,z: 1.12<z<1.46 and x>.27, violet)
shell("Nova_Cyan_Jacket_LeftSleeve",lambda x,y,z: 1.12<z<1.46 and x<-.27, cyan)
shell("Nova_Crosscheck_Top",lambda x,y,z: 1.26<z<1.43 and abs(x)<.30 and y<.03, black)

# Pleated asymmetric racing skirt: separate engineered panels, not a mesh blob.
def skirt():
    segments=24
    for j in range(segments):
        t0=j*2*math.pi/segments
        t1=(j+1)*2*math.pi/segments
        verts=[]
        for z,r,t in [(1.015,.265,t0),(1.015,.265,t1),(.825,.355,t1+.018),(.825,.355,t0-.018)]:
            verts.append((r*math.cos(t),r*math.sin(t),z))
        me=bpy.data.meshes.new("PleatMesh")
        me.from_pydata(verts,[],[(0,1,2,3)])
        me.update()
        ob=bpy.data.objects.new(f"Nova_Skirt_Pleat_{j:02d}",me)
        bpy.context.collection.objects.link(ob)
        ob.data.materials.append([cyan,violet,black,silver][j%4])
        mod=ob.modifiers.new("Pleat thickness","SOLIDIFY")
        mod.thickness=.008
        bevel=ob.modifiers.new("Hem softness","BEVEL")
        bevel.width=.004;bevel.segments=2
skirt()

def tube(name, coords, radius, material):
    cu=bpy.data.curves.new(name,"CURVE")
    cu.dimensions="3D"
    cu.bevel_depth=radius
    cu.bevel_resolution=2
    sp=cu.splines.new("BEZIER")
    sp.bezier_points.add(len(coords)-1)
    for p,co in zip(sp.bezier_points,coords):
        p.co=co
        p.handle_left_type="AUTO";p.handle_right_type="AUTO"
    ob=bpy.data.objects.new(name,cu)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(material)
    return ob

# Flowing, layered ponytail cards/strands. Not procedural spheres or solid hair 'ropes'.
for j in range(55):
    a=random.uniform(0,2*math.pi)
    rr=random.uniform(0.012,0.095)
    x=.03+rr*math.cos(a); y=.04+rr*math.sin(a)
    h=random.uniform(0.25,.48)
    tube(f"Nova_Hair_Ponytail_{j:02d}",[
        (x,y,1.66),
        (x+.16,y+.095,1.75),
        (x+.26+.03*math.sin(a),y+.16,h+1.10),
        (x+.28+.06*math.sin(a),y+.12,1.10-random.uniform(0,.19))
    ],random.uniform(.004,.008),blonde if j%4 else blonde_hi)

# Boots, glove cuffs, racing accents as small surface pieces.
shell("Boots_lower_leg_black",lambda x,y,z: .06<z<.36,black, .018)
shell("Gloves_black",lambda x,y,z: .83<z<1.20 and abs(x)>.47,black,.012)
shell("Waist_belt_black",lambda x,y,z: .94<z<1.025 and abs(x)<.32,black,.012)

def scene_obj(name):
    return bpy.data.objects.get(name)

bpy.ops.object.select_all(action="DESELECT")
# Exclude the human mask helper geometry through evaluated output, where possible.
chars=[o for o in bpy.context.scene.objects if o.type in ("MESH","CURVE")]
for o in chars: o.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.wm.save_as_mainfile(filepath=str((ROOT/"Nova_v02_MakeHuman_Master.blend").resolve()))
bpy.ops.export_scene.gltf(filepath=str((ROOT/"Nova_v02_MakeHuman.glb").resolve()),export_format="GLB",use_selection=True,export_apply=True)

# Render an honest Blender material-color inspection in an orthographic studio.
bpy.ops.object.select_all(action="DESELECT")
cam_data=bpy.data.cameras.new("Inspection camera")
cam=bpy.data.objects.new("Inspection Camera",cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera=cam
cam_data.type="ORTHO";cam_data.ortho_scale=2.23
sc=bpy.context.scene
sc.render.engine="BLENDER_WORKBENCH"
sc.display.shading.light="STUDIO"
sc.display.shading.color_type="MATERIAL"
sc.display.shading.show_cavity=True
sc.render.resolution_x=780
sc.render.resolution_y=940
sc.render.resolution_percentage=100
sc.render.image_settings.file_format="PNG"
for label,pos in [("front",(0,-4,1.18)),("quarter",(2.5,-3.7,1.18)),("side",(4,0,1.18)),("back",(0,4,1.18))]:
    cam.location=pos
    direct=Vector((0,0,1.0))-cam.location
    cam.rotation_euler=direct.to_track_quat("-Z","Y").to_euler()
    sc.render.filepath=str((ROOT/f"Nova_v02_{label}.png").resolve())
    bpy.ops.render.render(write_still=True)
report={
    "source":"MPFB 2 CC0 anatomical mesh",
    "blender":bpy.app.version_string,
    "prototype_stage":"A-pose geometry and clothing fit study; no approved facial likeness",
    "height_m":round(max(v.co.z for v in body.data.vertices)-min(v.co.z for v in body.data.vertices),3),
    "body_vertices":len(body.data.vertices),
    "objects":len(chars),
    "mesh_triangles":sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in chars if o.type=="MESH"),
    "notes":"Blender-rendered reference GLB, not phone runtime-tested; no skin rig or animations yet."
}
(ROOT/"report.json").write_text(json.dumps(report,indent=2))
print("NOVA_MPFB_V02_EXPORT_OK",json.dumps(report))
