"""Nova V0.3 — SceneForge Blender + MPFB anatomical and facial-quality benchmark.

A real MakeHuman continuous body mesh, native facial/body targets, free CC0 skin,
eye/eyelash/eyebrow/hair system assets and neutral anatomical review suit.
No final racing clothing until the base has been inspected. Not rigged.
Does NOT touch SceneForge game assets, APK or main branch.
"""
import bpy
import math
import json
import os
from pathlib import Path
from mathutils import Vector
import addon_utils

OUT=Path("build/nova-anatomy-v03").resolve()
OUT.mkdir(parents=True,exist_ok=True)
ASSETS=Path("/tmp/mpfb-system-assets")
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
addon_utils.enable("bl_ext.user_default.mpfb",default_set=False,persistent=False)
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
from bl_ext.user_default.mpfb.services.locationservice import LocationService
from bl_ext.user_default.mpfb.entities.objectproperties import HumanObjectProperties

body=HumanService.create_human(feet_on_ground=True)
body.name="Nova_Continuous_Anatomical_Basemesh"
bpy.context.view_layer.objects.active=body
body.select_set(True)
# Grown-up, athletic/slightly stylized geometry, not the unmodified generic MakeHuman default.
macros={
    "gender": 1.0,
    "age": .46,
    "muscle": .57,
    "weight": .52,
    "height": .54,
    "proportions": .54,
    "african": 0.0, "asian": 0.0, "caucasian": 0.0
}
for name,value in macros.items():
    try:
        HumanObjectProperties.set_value(name,value,entity_reference=body)
    except Exception as exc:
        print("MACRO_OPTIONAL_SKIPPED",name,str(exc)[:160])
TargetService.reapply_macro_details(body)

# These are actual MPFB deform targets applied as native editable shape keys.
# Conservative strengths deliberately avoid caricature and preserve plausible anatomy.
targets_root=Path(LocationService.get_mpfb_data("targets"))
targets={
    "head/head-oval":.34,
    "head/head-age-decr":.14,
    "head/head-scale-horiz-decr":.10,
    "chin/chin-width-decr":.18,
    "chin/chin-prominent-decr":.08,
    "cheek/l-cheek-bones-incr":.19,
    "cheek/r-cheek-bones-incr":.17,
    "cheek/l-cheek-volume-incr":.08,
    "cheek/r-cheek-volume-incr":.07,
    "eyes/l-eye-scale-incr":.19,
    "eyes/r-eye-scale-incr":.19,
    "eyes/l-eye-corner2-up":.13,
    "eyes/r-eye-corner2-up":.12,
    "eyebrows/eyebrows-angle-up":.06,
    "nose/nose-volume-decr":.12,
    "nose/nose-point-up":.10,
    "nose/nose-width1-decr":.10,
    "mouth/mouth-upperlip-volume-incr":.14,
    "mouth/mouth-lowerlip-volume-incr":.12,
    "mouth/mouth-cupidsbow-incr":.10,
    "mouth/mouth-angles-up":.09,
    "hip/hip-scale-horiz-incr":.21,
    "torso/measure-waist-circ-decr":.14,
    "legs/l-upperleg-muscle-incr":.11,
    "legs/r-upperleg-muscle-incr":.11,
    "legs/l-lowerleg-muscle-incr":.08,
    "legs/r-lowerleg-muscle-incr":.08,
}
applied={}
for target,weight in targets.items():
    fp=targets_root/(target+".target.gz")
    if not fp.is_file():
        print("TARGET_MISSING",target)
        continue
    try:
        TargetService.load_target(body,str(fp),weight=weight)
        applied[target]=weight
    except Exception as exc:
        print("TARGET_FAILED",target,str(exc)[:180])
assert len(applied)>=22, "Too few real MPFB facial and anatomical shape targets loaded"

# Import official CC0 system skin and proper facial pieces, rather than drawing them.
from bl_ext.user_default.mpfb.services.assetservice import AssetService
def find_asset(filename):
    possible=list(ASSETS.rglob(filename))
    # Prefer exact matching human system asset.
    possible=[p for p in possible if p.is_file()]
    if not possible:
        raise RuntimeError("Required MakeHuman CC0 asset not installed: "+filename)
    return str(sorted(possible,key=lambda p:len(str(p)))[0])
skin_path=find_asset("young_caucasian_female.mhmat")
HumanService.set_character_skin(skin_path,body,skin_type="GAMEENGINE")
assets=[]
for category,file,assettype in [
    ("eyes","low-poly.mhclo","Eyes"),
    ("brows","eyebrow001.mhclo","Eyebrows"),
    ("lashes","eyelashes01.mhclo","Eyelashes"),
]:
    asset=HumanService.add_mhclo_asset(find_asset(file),body,asset_type=assettype,material_type="GAMEENGINE")
    assets.append((category,file,str(getattr(asset,"name",asset))))
# Original approved Nova has a high, voluminous blond ponytail.
# Use an actual fitted MakeHuman ponytail mesh rather than invented tube strands.
hair_candidates=[]
for pattern in ["*ponytail*.mhclo","*pony*.mhclo","long01.mhclo","long02.mhclo"]:
    for hit in ASSETS.rglob(pattern):
        if hit.is_file():
            hair_candidates.append(hit)
    if hair_candidates:break
if not hair_candidates:
    raise RuntimeError("MPFB system hair mesh not found")
hair_path=str(sorted(hair_candidates,key=lambda p:len(str(p)))[0])
hair_ob=HumanService.add_mhclo_asset(hair_path,body,asset_type="Hair",material_type="GAMEENGINE")
assets.append(("hair",hair_path,str(getattr(hair_ob,"name",hair_ob))))

# Obtain all character mesh objects before building review studio.
objects=[o for o in bpy.context.scene.objects if o.type=="MESH"]
assert len(objects)>=4, "Missing system eyes, eyebrows, lashes or hair"
for obj in objects:
    for poly in obj.data.polygons:poly.use_smooth=True

def mat(name,col,rough=.7,metal=0.0):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*col,1)
    m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*col,1)
    bs.inputs["Roughness"].default_value=rough
    bs.inputs["Metallic"].default_value=metal
    return m
outfit=mat("Neutral_Anatomical_Review_Bodysuit",(.20,.24,.29),.88,.0)
trim=mat("Warm_Gray_Anatomy_Seams",(.33,.35,.37),.85)
blonde=mat("Nova_Hair_Blonde",(.72,.52,.28),.55)
# On this inspection version, retain actual skin in face, hands and feet.
# A continuous body-fitted review suit replaces the disconnected V0.2 panels.
skin_count=len(body.data.materials)
body.data.materials.append(outfit)
body.data.materials.append(trim)
body_mat_idx=skin_count
trim_idx=skin_count+1
for face in body.data.polygons:
    x,y,z=face.center
    if (z>1.41) or (z<.11) or (abs(x)>.38 and .95<z<1.32):
        continue
    face.material_index=body_mat_idx
# Body material actually follows continuous MPFB geometry, no disconnected clothing!
# Preserve the original textured and alpha-masked MPFB hair material.
# V0.3's first attempt replaced it with an opaque flat material, which made
# hair look like a plastic helmet. Multiply its albedo by warm blonde instead.
if hair_ob is not None and getattr(hair_ob,"type",None)=="MESH":
    for slot in hair_ob.material_slots:
        original=slot.material
        if not original: continue
        material=original.copy()
        slot.material=material
        if not material.use_nodes: continue
        bs=next((n for n in material.node_tree.nodes if n.type=="BSDF_PRINCIPLED"),None)
        if not bs: continue
        input_socket=bs.inputs.get("Base Color")
        if input_socket is None:continue
        original_link=input_socket.links[0] if input_socket.is_linked else None
        if original_link:
            multiply=material.node_tree.nodes.new("ShaderNodeMixRGB")
            multiply.blend_type="MULTIPLY"
            multiply.inputs[0].default_value=.50
            multiply.inputs[2].default_value=(.92,.69,.39,1)
            material.node_tree.links.new(original_link.from_socket,multiply.inputs[1])
            material.node_tree.links.new(multiply.outputs[0],input_socket)
        else:
            input_socket.default_value=(.74,.55,.32,1)
# Warm the CC0 skin slightly while preserving its RGB texture and pore detail.
for material in body.data.materials[:skin_count]:
    if not material or not material.use_nodes:continue
    bs=next((n for n in material.node_tree.nodes if n.type=="BSDF_PRINCIPLED"),None)
    if not bs:continue
    base=bs.inputs.get("Base Color")
    if base is None or not base.is_linked:continue
    existing=base.links[0].from_socket
    tint=material.node_tree.nodes.new("ShaderNodeMixRGB")
    tint.blend_type="MULTIPLY"
    tint.inputs[0].default_value=.35
    tint.inputs[2].default_value=(.92,.72,.56,1)
    material.node_tree.links.new(existing,tint.inputs[1])
    material.node_tree.links.new(tint.outputs[0],base)

# Group and normalize output scale together. Do not deform MPFB shape key deltas.
zs=[v.co.z for v in body.data.vertices]
bottom,top=min(zs),max(zs)
target_height=1.73
scale=target_height/(top-bottom)
for ob in objects:
    ob.scale=(ob.scale.x*scale,ob.scale.y*scale,ob.scale.z*scale)
    ob.location.z-=bottom*scale
# MPFB's bundled eye/eyelash/eyebrow proxies are fitted against the neutral
# human basis. Facial shape keys change socket location; align accessories to
# the *evaluated* face instead of leaving eyes floating on the forehead.
# Distances are in normalized model meters, measured from first PBR QC.
for ob in objects:
    if ob==body:continue
    name=ob.name.lower()
    if "low-poly" in name:
        ob.location.z-=.077
        ob.location.y-=.021
    elif "eyelashes" in name:
        ob.location.z-=.071
        ob.location.y-=.023
    elif "eyebrow" in name:
        ob.location.z-=.039
        ob.location.y-=.016
    elif "ponytail" in name:
        ob.location.z-=.030
# Existing object scale/transform remains editable and unbaked.
bpy.context.view_layer.update()

# Select only actual character mesh, no studio assets.
bpy.ops.object.select_all(action="DESELECT")
for ob in objects:ob.select_set(True)
bpy.context.view_layer.objects.active=body

# Master first, with source shape keys, image assets, and editable mesh.
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"Nova_V03_Anatomy_Master.blend"))
# Export neutral anatomy to GLB for Android viewer.
bpy.ops.export_scene.gltf(
    filepath=str(OUT/"Nova_V03_Anatomy_Review.glb"),
    export_format="GLB",use_selection=True,export_apply=False,
    export_image_format="AUTO"
)

# Studio for independently inspectable previews; do not export it.
def look_at(obj,target):
    direction=Vector(target)-obj.location
    obj.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
world=bpy.context.scene.world
world.color=(.25,.25,.25)
world.use_nodes=True
bg=world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value=(.22,.24,.27,1)
bg.inputs["Strength"].default_value=.9

def area(name,pos,power,size,color):
    data=bpy.data.lights.new(name,"AREA")
    obj=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    obj.location=pos;data.energy=power;data.shape="DISK";data.size=size
    data.color=color;look_at(obj,(0,0,1.02))
area("Main softbox",(-2.2,-3.0,3.2),230,4.0,(1,1,1))
area("Fill softbox",(2.5,-1.8,2.4),135,3.0,(.83,.90,1.0))
area("Hair edge",(1.0,2.0,2.7),185,2.0,(1.0,.87,.76))
cam_data=bpy.data.cameras.new("Camera")
cam=bpy.data.objects.new("Camera",cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera=cam
cam_data.type="ORTHO"
sc=bpy.context.scene
sc.render.resolution_percentage=100
sc.render.image_settings.file_format="PNG"
sc.render.film_transparent=False

def render(name,pos,target,scale,width,height,engine="BLENDER_WORKBENCH"):
    cam.location=pos
    look_at(cam,target)
    cam_data.ortho_scale=scale
    sc.render.resolution_x=width;sc.render.resolution_y=height
    sc.render.engine=engine
    if engine=="BLENDER_WORKBENCH":
        sc.display.shading.light="STUDIO"
        sc.display.shading.color_type="MATERIAL"
        sc.display.shading.show_cavity=True
        sc.display.shading.cavity_type="BOTH"
    else:
        sc.render.image_settings.color_mode="RGBA"
        sc.view_settings.view_transform="AgX"
    sc.render.filepath=str(OUT/(name+".png"))
    bpy.ops.render.render(write_still=True)
for name,campos in [
    ("Nova_V03_front",(0,-3.4,1.05)),
    ("Nova_V03_three_quarter",(2.55,-3.15,1.15)),
    ("Nova_V03_side",(3.5,0,1.05)),
    ("Nova_V03_rear",(0,3.4,1.05)),
]:
    render(name,campos,(0,0,.90),2.06,750,960)
# Require one real material/texture-lit closeup before declaring success.
render("Nova_V03_face_pbr",(0,-2.1,1.62),(0,0,1.56),.42,800,800,engine="BLENDER_EEVEE_NEXT")
render("Nova_V03_full_pbr",(1.2,-3.2,1.40),(0,0,.98),2.0,750,960,engine="BLENDER_EEVEE_NEXT")

report={
    "prototype":"Nova v0.3 actual MPFB body and face study",
    "blender_version":bpy.app.version_string,
    "mpfb_source":"MakeHumanCommunity MPFB 2 extension",
    "system_asset_license":"MakeHuman official system assets CC0",
    "source_height_m":round(top-bottom,3),
    "normalized_height_m":round((top-bottom)*scale,3),
    "body_vertices":len(body.data.vertices),
    "morph_targets_requested":len(targets),
    "morph_targets_loaded":len(applied),
    "morph_names":list(applied.keys()),
    "system_assets":assets,
    "mesh_objects":len(objects),
    "triangle_count_source":sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects),
    "status":"unrigged, neutral body study, not approved Nova likeness",
}
(OUT/"Nova_V03_build_report.json").write_text(json.dumps(report,indent=2))
assert report["body_vertices"]>=15000
assert report["morph_targets_loaded"]>=22
assert len(assets)==4
assert (OUT/"Nova_V03_Anatomy_Review.glb").stat().st_size>200000
assert (OUT/"Nova_V03_face_pbr.png").stat().st_size>100000
print("NOVA_V03_REAL_MPFB_ANATOMY_OK",json.dumps({k:report[k] for k in ("body_vertices","morph_targets_loaded","mesh_objects","triangle_count_source","normalized_height_m")}))
