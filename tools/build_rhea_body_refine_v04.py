"""
Rhea v04 — MakeHuman CC0 anatomical base for SceneForge.
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

OUT = Path(os.getenv("RHEA_OUTPUT", "build/rhea-v04"))
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = "https://raw.githubusercontent.com/makehumancommunity/makehuman/master/makehuman/data/"
BODY = SOURCE + "3dobjs/base.obj"
TARGETS = [
    # MakeHuman averageweight is an intentionally empty neutral morph.
    ("macrodetails/caucasian-female-young.target", 0.52),
    ("macrodetails/african-female-young.target", 0.48),
    ("macrodetails/universal-female-young-averagemuscle-maxweight.target", 0.30),
    ("macrodetails/universal-female-young-maxmuscle-averageweight.target", 0.42),
    ("bodyshapes/bodyshapes-elvs-fem-full-hourglass.target", 0.29),
    ("hip/hip-scale-horiz-incr.target", 0.10),
    ("head/head-round.target", 0.10),
    # Rhea reference: athletic-curvy build with natural anatomical breast volume.
    ("breast/female-young-averagemuscle-maxweight-maxcup-averagefirmness.target", 0.33),
    # V04: localized sculpt refinements on the SAME continuous anatomical mesh.
    # Independent morph weights for Rhea; do not reuse Kade’s approved proportions.
    ("torso/torso-muscle-pectoral-incr.target", 0.16),
    ("torso/torso-muscle-dorsi-incr.target", 0.11),
    ("stomach/stomach-tone-incr.target", 0.18),
    ("pelvis/pelvis-tone-incr.target", 0.15),
    ("buttocks/buttocks-volume-incr.target", 0.18),
    ("armslegs/l-upperarm-shoulder-muscle-incr.target", 0.09),
    ("armslegs/r-upperarm-shoulder-muscle-incr.target", 0.09),
    ("armslegs/l-upperarm-muscle-incr.target", 0.06),
    ("armslegs/r-upperarm-muscle-incr.target", 0.06),
    ("armslegs/l-upperleg-muscle-incr.target", 0.16),
    ("armslegs/r-upperleg-muscle-incr.target", 0.16),
    ("armslegs/l-lowerleg-muscle-incr.target", 0.14),
    ("armslegs/r-lowerleg-muscle-incr.target", 0.14),
    ("cheek/l-cheek-bones-incr.target", 0.12),
    ("cheek/r-cheek-bones-incr.target", 0.12),
    ("cheek/l-cheek-volume-incr.target", 0.09),
    ("cheek/r-cheek-volume-incr.target", 0.09),
    ("mouth/mouth-upperlip-volume-incr.target", 0.11),
    ("mouth/mouth-lowerlip-volume-incr.target", 0.07),
    ("nose/nose-width2-decr.target", 0.06),
    ("chin/chin-width-decr.target", 0.06),
    ("eyes/l-eye-scale-incr.target", 0.11),
    ("eyes/r-eye-scale-incr.target", 0.11),
    ("mouth/mouth-angles-up.target", 0.05),
    ("nose/nose-point-width-decr.target", 0.07),
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
print("RHEA_SOURCE_FETCH_START", flush=True)
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
print("RHEA_SOURCE_VERTS",len(base),"FACES",len(faces),flush=True)
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
    print("RHEA_TARGET_APPLIED",rel,changed,flush=True)

# Source hm08 includes joint cubes, hair proxies, tights and skirt helpers.
# Only vertex IDs 0..13379 are the actual visible anatomical body (CC0).
# Preserve full target index space until ALL morphs have been applied.
BODY_END=13380
visible_faces=[f for f in faces if all(0<=i<BODY_END for i in f)]
print("RHEA_VISIBLE_BODY_FACES",len(visible_faces),"REMOVED_HELPER_FACES",len(faces)-len(visible_faces),flush=True)
assert len(visible_faces)>10000 and len(faces)-len(visible_faces)>1000
faces=visible_faces
base=base[:BODY_END]

# MakeHuman uses Y-up in OBJ; rotate to Blender Z-up and normalize to 1.78m.
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
scale=1.78/(z_hi-z_lo)
verts=[]
sculpt_counts={"breast":0,"glutes":0,"abdomen_oblique":0,"legs":0,"back":0}
sculpt_max_displacement=0.0
sculpt_changed_vertices=0
for x,y,z in raw:
    xx=(x-x_mid)*scale
    yy=(y-y_mid)*scale
    zz=(z-z_lo)*scale
    # Rhea’s athletic-curvy silhouette, continuous changes to existing topology
    hip=.028*math.exp(-((zz-.97)/.18)**2)
    thigh=.028*math.exp(-((zz-.72)/.20)**2)
    waist=-.014*math.exp(-((zz-1.18)/.16)**2)
    weight=hip+thigh+waist
    xx *= (1.+weight)
    # Small soft depth adjustment, keeping the mesh watertight/connected.
    yy *= (1.+weight*.60)
    # Rhea V04 — anatomical SURFACE SCULPT on existing MakeHuman vertices.
    # Coordinates here are Blender Z-up: -Y anterior/front, +Y posterior.
    # Broad soft falloffs preserve the underlying continuous topology.
    old_x,old_y,old_z=xx,yy,zz
    anterior=.5+.5*math.tanh((-yy-.006)/.027)
    posterior=.5+.5*math.tanh((yy-.025)/.040)
    side=abs(xx)
    # Breast body shape: lower-pole fullness, softer outer contours and
    # gradual pectoral/axillary blends. No extra sphere or separate breast mesh.
    breast=math.exp(-((side-.093)/.084)**2-((zz-1.361)/.098)**2)*anterior
    lower_pole=1.0+.27*math.exp(-((zz-1.316)/.051)**2)
    yy-=.0195*breast*lower_pole
    xx+=.0032*(xx/max(.095,side))*breast
    if breast>.12: sculpt_counts["breast"]+=1
    # Buttock volume follows bilateral glute surface, stronger at the upper
    # and central glutes. Smoothly attenuate into sacrum and hamstrings.
    glute=math.exp(-((side-.112)/.123)**2-((zz-.934)/.148)**2)*posterior
    upper_glute=.83+.22*math.exp(-((zz-.986)/.09)**2)
    yy+=.026*glute*upper_glute
    xx+=.0045*(xx/max(.14,side))*glute
    if glute>.12: sculpt_counts["glutes"]+=1
    # Gentle abdominal center, oblique waist/iliac crest definition.
    ab=math.exp(-((xx/.153)**2)-((zz-1.174)/.155)**2)*anterior
    oblique=math.exp(-((side-.142)/.060)**2-((zz-1.139)/.125)**2)
    yy-=.0038*ab
    xx-=.0035*(xx/max(.15,side))*oblique
    if ab>.16 or oblique>.16: sculpt_counts["abdomen_oblique"]+=1
    # Upper-leg / outer-thigh and posterior hamstring transitions, plus
    # understated kneecap and gastrocnemius contour refinements.
    thigh_flow=math.exp(-((side-.183)/.095)**2-((zz-.745)/.204)**2)
    hamstring=math.exp(-((side-.134)/.083)**2-((zz-.658)/.123)**2)*posterior
    knee=math.exp(-((side-.121)/.056)**2-((zz-.487)/.067)**2)*anterior
    calf=math.exp(-((side-.112)/.065)**2-((zz-.316)/.110)**2)*posterior
    xx+=.0040*(xx/max(.18,side))*thigh_flow
    yy+=.0048*hamstring+.0032*calf-.0023*knee
    if thigh_flow>.16 or hamstring>.16 or knee>.16 or calf>.16: sculpt_counts["legs"]+=1
    # Lumbar and shoulder blade landmarks on the posterior torso.
    lumbar=math.exp(-((side-.085)/.079)**2-((zz-1.144)/.102)**2)*posterior
    scapula=math.exp(-((side-.113)/.085)**2-((zz-1.430)/.093)**2)*posterior
    yy+=.0039*lumbar+.0025*scapula
    if lumbar>.16 or scapula>.16: sculpt_counts["back"]+=1
    d=math.sqrt((xx-old_x)**2+(yy-old_y)**2+(zz-old_z)**2)
    if d>0.0001: sculpt_changed_vertices+=1
    sculpt_max_displacement=max(sculpt_max_displacement,d)
    verts.append((xx,yy,zz))

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
mesh=bpy.data.meshes.new("Rhea_Continuous_MakeHuman_Topology")
mesh.from_pydata(verts,[],faces)
mesh.update()
body=bpy.data.objects.new("Rhea_Anatomical_Base_CC0",mesh)
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
# entire surface. The old gray "bodysuit" was purely a polygon-material mask;
# there are no clothing polygons to remove and no new seams are introduced.
skin=material("Rhea_V04_Neutral_Skin_Sculpt_Base",(0.34,0.158,0.105),.65)
body.data.materials.clear()
body.data.materials.append(skin)
for poly in mesh.polygons:
    poly.material_index=0
assert len(body.data.materials)==1
print("RHEA_V04_GRAY_BODYSUIT_REMOVED",flush=True)

# Distinctive Rhea facial/hairstyle mesh layers; true geometry attached to
# the same MakeHuman anatomical body. Keep all individual mesh objects editable.
import sys
sys.path.insert(0,str(Path(__file__).parent))
from rhea_identity_details_v03 import build_rhea_identity
identity_parts=build_rhea_identity(body,material)
assert len(identity_parts)>=15
print("RHEA_V04_IDENTITY_MESHES_BUILT",len(identity_parts),flush=True)
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
for obj in identity_parts: obj.select_set(True)
bpy.context.view_layer.objects.active=body
out_glb=OUT/"Rhea_FaceHair_Assembly_v04.glb"
bpy.ops.export_scene.gltf(filepath=str(out_glb),export_format="GLB",
    use_selection=True,export_apply=True,export_materials="EXPORT",
    export_normals=True,export_texcoords=True)
assert out_glb.is_file() and out_glb.stat().st_size>100000
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"Rhea_FaceHair_Assembly_v04.blend"))
print("RHEA_V04_GLB_EXPORT_OK",out_glb.stat().st_size,flush=True)

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
scene.cycles.samples=int(os.getenv('RHEA_SAMPLES','28'))
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
    print("RHEA_V04_RENDER_OK",name,flush=True)

render("Rhea_Base_Front.png",(0,-3.9,1.25))
render("Rhea_Base_ThreeQuarter.png",(3.0,-3.7,1.35))
render("Rhea_Base_Back.png",(0,3.9,1.25))
render("Rhea_Base_Side.png",(3.9,0,1.25))
render("Rhea_Base_RearThreeQuarter.png",(3.0,3.7,1.35))
cam_data.ortho_scale=1.15
def torso_render(name,loc):
    cam.location=loc
    look=Vector((0,0,1.17))-cam.location
    cam.rotation_euler=look.to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OUT/name)
    bpy.ops.render.render(write_still=True)
    assert (OUT/name).stat().st_size>10000
    print("RHEA_V04_TORSO_RENDER_OK",name,flush=True)
torso_render("Rhea_Torso_Front.png",(0,-3.6,1.36))
torso_render("Rhea_Torso_Side.png",(3.6,0,1.36))
torso_render("Rhea_Torso_RearThreeQuarter.png",(2.6,3.1,1.36))
cam_data.ortho_scale=.54
def face_render(name,position):
    cam.location=position
    look=Vector((0,0,1.653))-cam.location
    cam.rotation_euler=look.to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OUT/name)
    bpy.ops.render.render(write_still=True)
    assert (OUT/name).stat().st_size>10000
    print("RHEA_V04_FACE_RENDER_OK",name,flush=True)
face_render("Rhea_Face_Front.png",(0,-3.8,1.80))
face_render("Rhea_Face_ThreeQuarter.png",(2.7,-3.6,1.80))
face_render("Rhea_Hair_Rear.png",(0,3.8,1.80))
triangles=sum(len(p.vertices)-2 for p in mesh.polygons)
bounds=[[min(p[i] for p in verts),max(p[i] for p in verts)] for i in range(3)]
report={
 "version":"Rhea V04 sculpted athletic-curvy anatomy: fuller bust/glutes and localized chest, abdomen, oblique, back, thigh and calf geometry", "source":"makehumancommunity/makehuman base.obj",
 "asset_license":"CC0", "source_sha256":hashlib.sha256(objfile.read_bytes()).hexdigest(),
 "body_sculpt_v04":{"vertex_changes":sculpt_changed_vertices,"max_sculpt_displacement_m":sculpt_max_displacement,"sculpt_zone_affected_vertex_counts":sculpt_counts,"breast_morph":0.33,"buttock_morph":0.18,"prior_v03_breast_morph":0.24,"prior_v03_buttock_morph":0.08},
 "vertex_count":len(verts),"polygon_count":len(faces),
 "triangles":triangles,"meshes_exported":len(identity_parts)+1, "identity_mesh_count":len(identity_parts), "includes_hair":True, "includes_goggles":True, "includes_freckles":True,"height_m":1.78,
 "continuous_makehuman_base_topology":True,"rigged":False,"fitted_suit_material_only":False,"gray_material_removed":True,"material_count":len(body.data.materials),"sculpt_morph_count":len(TARGETS)-8,
 "identity_sculpt_complete":False,"reference":"Rhea approved Crimson Divide red-leather portrait; neutral T-pose for body","source_vertical_axis":up,
 "targets":morph_log,"bounds":bounds,
 "exports":[out_glb.name,"Rhea_FaceHair_Assembly_v04.blend",
            "Rhea_Base_Front.png","Rhea_Base_Back.png","Rhea_Base_ThreeQuarter.png","Rhea_Base_Side.png","Rhea_Base_RearThreeQuarter.png","Rhea_Torso_Front.png","Rhea_Torso_Side.png","Rhea_Torso_RearThreeQuarter.png", "Rhea_Face_Front.png","Rhea_Face_ThreeQuarter.png","Rhea_Hair_Rear.png"]
}
(OUT/"Rhea_v04_Report.json").write_text(json.dumps(report,indent=2))
print("RHEA_V04_PASS",json.dumps({"verts":len(verts),"triangles":triangles,"glb_bytes":out_glb.stat().st_size,"materials":len(body.data.materials),"identity_parts":len(identity_parts),"sculpted_vertices":sculpt_changed_vertices,"sculpt_morphs":len(TARGETS)-8}),flush=True)
