"""
Kade v06 — MakeHuman base with authored facial and physical hair mesh for SceneForge.
Real continuous human mesh and MakeHuman body-shape target deltas.
Blender (CI currently 4.0.2) -> GLB -> Godot 4.5.1 import/render preview.
Not a final identity sculpt or a rigged avatar.

Source: https://github.com/makehumancommunity/makehuman
Asset license: CC0 https://www.makehumancommunity.org/about/license.html
"""
import bpy
from mathutils import Vector
from pathlib import Path
import math, json, os, hashlib, urllib.request

OUT = Path(os.getenv("KADE_OUTPUT", "build/kade-v06"))
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = "https://raw.githubusercontent.com/makehumancommunity/makehuman/master/makehuman/data/"
BODY = SOURCE + "3dobjs/base.obj"
TARGETS = [
    # MakeHuman averageweight is an intentionally empty neutral morph.
    ("macrodetails/caucasian-female-young.target", 0.60),
    ("macrodetails/african-female-young.target", 0.40),
    ("macrodetails/universal-female-young-averagemuscle-maxweight.target", 0.40),
    ("macrodetails/universal-female-young-maxmuscle-averageweight.target", 0.30),
    ("bodyshapes/bodyshapes-elvs-fem-full-hourglass.target", 0.42),
    ("hip/hip-scale-horiz-incr.target", 0.18),
    ("head/head-round.target", 0.10),
    # More proportional bust volume, while preserving the approved V02 waist/hips.
    ("breast/female-young-averagemuscle-maxweight-maxcup-averagefirmness.target", 0.29),
    # V04: localized sculpt refinements on the SAME continuous anatomical mesh.
    # Low weights retain the approved V03 body mass and bust dimensions.
    ("torso/torso-muscle-pectoral-incr.target", 0.11),
    ("torso/torso-muscle-dorsi-incr.target", 0.07),
    ("stomach/stomach-tone-incr.target", 0.10),
    ("pelvis/pelvis-tone-incr.target", 0.09),
    ("buttocks/buttocks-volume-incr.target", 0.06),
    ("armslegs/l-upperarm-shoulder-muscle-incr.target", 0.09),
    ("armslegs/r-upperarm-shoulder-muscle-incr.target", 0.09),
    ("armslegs/l-upperarm-muscle-incr.target", 0.06),
    ("armslegs/r-upperarm-muscle-incr.target", 0.06),
    ("armslegs/l-upperleg-muscle-incr.target", 0.08),
    ("armslegs/r-upperleg-muscle-incr.target", 0.08),
    ("armslegs/l-lowerleg-muscle-incr.target", 0.10),
    ("armslegs/r-lowerleg-muscle-incr.target", 0.10),
    ("cheek/l-cheek-bones-incr.target", 0.12),
    ("cheek/r-cheek-bones-incr.target", 0.12),
    ("cheek/l-cheek-volume-incr.target", 0.09),
    ("cheek/r-cheek-volume-incr.target", 0.09),
    ("mouth/mouth-upperlip-volume-incr.target", 0.11),
    ("mouth/mouth-lowerlip-volume-incr.target", 0.07),
    ("nose/nose-width2-decr.target", 0.06),
    ("chin/chin-width-decr.target", 0.06),
    # V05: targeted facial identity changes, no change to V04 body mass.
    ("eyes/l-eye-scale-incr.target", 0.10),
    ("eyes/r-eye-scale-incr.target", 0.10),
    ("mouth/mouth-angles-up.target", 0.07),
    ("nose/nose-point-width-decr.target", 0.08),
]
def fetch(url, file):
    if not file.exists():
        with urllib.request.urlopen(url, timeout=90) as resp:
            file.write_bytes(resp.read())
    return file

def smoothstep(a,b,x):
    t=max(0.,min(1.,(x-a)/(b-a)))
    return t*t*(3.-2.*t)

# Start from true MakeHuman base connectivity, not primitive assembly.
print("KADE_SOURCE_FETCH_START", flush=True)
objfile=fetch(BODY,OUT/"MakeHuman_base_CC0.obj")
base=[]
faces=[]
for line in objfile.read_text(errors="replace").splitlines():
    if line.startswith("v "):
        parts=line.split()
        base.append([float(parts[1]),float(parts[2]),float(parts[3])])
    elif line.startswith("f "):
        face=[int(p.split("/")[0])-1 for p in line.split()[1:]]
        if len(face)>=3 and len(set(face))==len(face):
            faces.append(face)
assert len(base)>14000 and len(faces)>12000, (len(base),len(faces))
print("KADE_SOURCE_VERTS",len(base),"FACES",len(faces),flush=True)
morph_log=[]
for rel,w in TARGETS:
    p=fetch(SOURCE+"targets/"+rel,OUT/(rel.replace("/","__")))
    changed=0
    for ln in p.read_text(errors="replace").splitlines():
        ln=ln.strip()
        if not ln or ln.startswith("#"): continue
        f=ln.split()
        if len(f)!=4: continue
        try:
            ix=int(f[0]); offsets=list(map(float,f[1:]))
        except ValueError: continue
        if 0<=ix<len(base):
            for j in range(3): base[ix][j]+=w*offsets[j]
            changed+=1
    assert changed>20, (rel,changed)
    morph_log.append({"target":rel,"weight":w,"modified_vertices":changed})
    print("KADE_TARGET_APPLIED",rel,changed,flush=True)

# Source hm08 includes joint cubes, hair proxies, tights and skirt helpers.
# Only vertex IDs 0..13379 are the actual visible anatomical body (CC0).
# Preserve full target index space until ALL morphs have been applied.
BODY_END=13380
visible_faces=[f for f in faces if all(0<=i<BODY_END for i in f)]
print("KADE_VISIBLE_BODY_FACES",len(visible_faces),"REMOVED_HELPER_FACES",len(faces)-len(visible_faces),flush=True)
assert len(visible_faces)>10000 and len(faces)-len(visible_faces)>1000
faces=visible_faces
base=base[:BODY_END]

# MakeHuman uses Y-up in OBJ; rotate to Blender Z-up and normalize to 1.68m.
# Auto-detection preserves compatibility with source revisions.
mins=[min(v[i] for v in base) for i in range(3)]
maxs=[max(v[i] for v in base) for i in range(3)]
up=1  # MakeHuman base.obj is explicitly Y-up, regardless of arm span
if up==1:
    raw=[(v[0],-v[2],v[1]) for v in base]
elif up==2:
    raw=[(v[0],v[1],v[2]) for v in base]
else:
    raise RuntimeError("Unexpected MakeHuman vertical axis "+str(up))
x_mid=(min(v[0] for v in raw)+max(v[0] for v in raw))*.5
y_mid=(min(v[1] for v in raw)+max(v[1] for v in raw))*.5
z_lo=min(v[2] for v in raw)
z_hi=max(v[2] for v in raw)
scale=1.68/(z_hi-z_lo)
verts=[]
for x,y,z in raw:
    xx=(x-x_mid)*scale
    yy=(y-y_mid)*scale
    zz=(z-z_lo)*scale
    # Kade's fuller but athletic build, continuous changes to existing topology
    hip=.070*math.exp(-((zz-.91)/.16)**2)
    thigh=.052*math.exp(-((zz-.68)/.19)**2)
    waist=.035*math.exp(-((zz-1.12)/.16)**2)
    weight=hip+thigh+waist
    xx *= (1.+weight)
    # Small soft depth adjustment, keeping the mesh watertight/connected.
    yy *= (1.+weight*.60)
    verts.append((xx,yy,zz))

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
mesh=bpy.data.meshes.new("Kade_Continuous_MakeHuman_Topology")
mesh.from_pydata(verts,[],faces)
mesh.update()
body=bpy.data.objects.new("Kade_Anatomical_Base_CC0",mesh)
bpy.context.collection.objects.link(body)
for p in mesh.polygons: p.use_smooth=True

def material(name,color,rough=.48,metal=0):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*color,1)
    bs.inputs["Roughness"].default_value=rough
    bs.inputs["Metallic"].default_value=metal
    return m
# Anatomical sculpting base: one neutral, warm skin-tone material across the
# entire surface. V03's gray "bodysuit" was purely a polygon-material mask;
# there are no clothing polygons to remove and no new seams are introduced.
skin=material("Kade_V05_Warm_Tan_Skin",(0.44,0.225,0.14),.66)
body.data.materials.clear()
body.data.materials.append(skin)
for poly in mesh.polygons:
    poly.material_index=0
assert len(body.data.materials)==1
print("KADE_V06_GRAY_BODYSUIT_REMOVED",flush=True)

# Build true 3D hair, goggles, eyes, brows, freckles and metal jewelry.
import sys
sys.path.insert(0, str(Path(__file__).parent))
from kade_identity_details_v06 import build_kade_identity
identity_parts = build_kade_identity(body, material)
assert 15 <= len(identity_parts) <= 200
assert all(o.type=="MESH" for o in identity_parts)
print("KADE_V06_HAIR_GEOMETRY_BUILT",len(identity_parts),flush=True)

# Export anatomical body + separate identity mesh elements (no studio props).
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
for o in identity_parts:
    o.select_set(True)
bpy.context.view_layer.objects.active=body
out_glb=OUT/"Kade_FaceHair_Assembly_v06.glb"
bpy.ops.export_scene.gltf(filepath=str(out_glb),export_format="GLB",
    use_selection=True,export_apply=True,export_materials="EXPORT",
    export_normals=True,export_texcoords=True)
assert out_glb.is_file() and out_glb.stat().st_size>100000
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"Kade_FaceHair_Assembly_v06.blend"))
print("KADE_V06_GLB_EXPORT_OK",out_glb.stat().st_size,flush=True)

world=bpy.context.scene.world
world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(.17,.19,.24,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.6
def light(name,xyz,power,shape,size):
    data=bpy.data.lights.new(name,'AREA')
    data.energy=power
    data.shape=shape
    data.size=size
    ob=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(ob)
    ob.location=xyz
    direction=Vector((0,0,1.0))-ob.location
    ob.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
light("StudioKey",(-2.7,-3.1,3.6),420,'DISK',4.0)
light("StudioFill",(2.1,-1.2,2.0),250,'DISK',3.5)
light("StudioRim",(1.8,2.2,3.8),350,'DISK',3.0)
bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-0.027))
floor=bpy.context.object
floor.name="Studio_Floor_NOT_EXPORTED"
floor.data.materials.append(material("Matte_Floor",(0.09,.105,.125),.80))
cam_data=bpy.data.cameras.new("Inspection_Orthographic")
cam=bpy.data.objects.new("Inspection_Orthographic",cam_data)
bpy.context.collection.objects.link(cam)
cam_data.type='ORTHO'
cam_data.ortho_scale=2.23
scene=bpy.context.scene
scene.camera=cam
scene.render.engine='CYCLES'
scene.cycles.samples=int(os.getenv('KADE_SAMPLES','28'))
scene.cycles.use_denoising=False  # distro Blender lacks OpenImageDenoise
scene.render.resolution_x=750
scene.render.resolution_y=1050
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'

def render(name,loc):
    cam.location=loc
    look=Vector((0,0,0.92))-cam.location
    cam.rotation_euler=look.to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OUT/name)
    bpy.ops.render.render(write_still=True)
    assert (OUT/name).stat().st_size>10000
    print("KADE_V06_RENDER_OK",name,flush=True)

render("Kade_Base_Front.png",(0,-3.9,1.25))
render("Kade_Base_ThreeQuarter.png",(3.0,-3.7,1.35))
render("Kade_Base_Back.png",(0,3.9,1.25))

# Orthographic close-up renders of the actual modeled face and hair.
cam_data.ortho_scale=.49
def face_render(name,position):
    cam.location=position
    look=Vector((0,0,1.555))-cam.location
    cam.rotation_euler=look.to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OUT/name)
    bpy.ops.render.render(write_still=True)
    print("KADE_V06_FACE_RENDER_OK",name,flush=True)
face_render("Kade_Face_Front.png",(0,-3.8,1.7))
face_render("Kade_Face_ThreeQuarter.png",(2.7,-3.6,1.7))
face_render("Kade_Hair_Rear.png",(0,3.8,1.7))
triangles=sum(len(p.vertices)-2 for p in mesh.polygons)
bounds=[[min(p[i] for p in verts),max(p[i] for p in verts)] for i in range(3)]
report={
 "version":"Kade v06 approved body + facial and hair 3D geometry", "source":"makehumancommunity/makehuman base.obj",
 "asset_license":"CC0", "source_sha256":hashlib.sha256(objfile.read_bytes()).hexdigest(),
 "vertex_count":len(verts),"polygon_count":len(faces),
 "triangles":triangles,"meshes_exported":len(identity_parts)+1,"height_m":1.68,
 "continuous_makehuman_base_topology":True,"rigged":False,"fitted_suit_material_only":False,"gray_material_removed":True,"material_count":len(body.data.materials),"sculpt_morph_count":len(TARGETS)-8,"identity_mesh_count":len(identity_parts),"includes_hair":True,"includes_goggles":True,"includes_freckles":True,
 "identity_sculpt_complete":False,"source_vertical_axis":up,
 "targets":morph_log,"bounds":bounds,
 "exports":[out_glb.name,"Kade_FaceHair_Assembly_v06.blend",
            "Kade_Base_Front.png","Kade_Base_Back.png","Kade_Base_ThreeQuarter.png",
            "Kade_Face_Front.png","Kade_Face_ThreeQuarter.png","Kade_Hair_Rear.png"]
}
(OUT/"Kade_v06_Report.json").write_text(json.dumps(report,indent=2))
print("KADE_V06_PASS",json.dumps({"verts":len(verts),"body_triangles":triangles,"glb_bytes":out_glb.stat().st_size,"parts":len(identity_parts),"sculpt_morphs":len(TARGETS)-8}),flush=True)
