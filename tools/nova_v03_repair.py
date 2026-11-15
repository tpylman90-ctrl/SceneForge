"""Repair Nova v0.3 anatomical benchmark from the verified packed MPFB master.

Keeps native MPFB shape keys and system-asset meshes; fixes eye/eyebrow/eyelash
alignment after facial morphs, improves skin illumination and hair surface.
No asset pack download. Saves an editable corrected .blend and a phone GLB.
"""
import os, bpy, math, json
import numpy as np
from pathlib import Path
from mathutils import Vector

SOURCE=Path(os.environ.get("NOVA_SOURCE_BLEND","build/source-v03/Nova_V03_Anatomy_Master.blend")).resolve()
OUT=Path("build/nova-anatomy-v03b").resolve()
OUT.mkdir(parents=True,exist_ok=True)
assert SOURCE.is_file(),str(SOURCE)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body=bpy.data.objects.get("Nova_Continuous_Anatomical_Basemesh")
assert body is not None
items=[ob for ob in bpy.context.scene.objects if ob.type=="MESH"]
print("SOURCE_SCENE_MESHES",[(o.name,str(o.parent)) for o in items])
print("SOURCE_MATERIALS",[m.name for m in bpy.data.materials])
print("SOURCE_IMAGES",[im.name for im in bpy.data.images])

def match(substr):
    hits=[o for o in items if substr.lower() in o.name.lower()]
    if len(hits)!=1:raise RuntimeError("Missing or ambiguous human attached asset "+substr+": "+str([h.name for h in hits]))
    return hits[0]
eye=match("low-poly")
lashes=match("eyelashes01")
brows=match("eyebrow001")
hair=match("ponytail01")

def move_world(obj,x=0,y=0,z=0):
    obj.matrix_world.translation += Vector((x,y,z))
    bpy.context.view_layer.update()

# Adjust accessory placement to the final, morph-deformed facial landmarks.
move_world(eye,y=-.022,z=-.079)
move_world(lashes,y=-.025,z=-.073)
move_world(brows,y=-.016,z=-.041)
move_world(hair,z=-.027)

# Keep morphs editable. Restore CC0 hair's original alpha texture if present.
hair_candidates=[m for m in bpy.data.materials if "ponytail" in m.name.lower()]
if hair_candidates:
    hm=hair_candidates[0].copy()
    hm.name="Nova_Cropped_Blonde_HairCard_Material"
    hair.data.materials.clear()
    hair.data.materials.append(hm)
else:
    # If Blender removed the unused hair material, generate a packed strand-albedo image.
    # This preserves real editable ponytail geometry and produces a glTF-compatible texture.
    material=bpy.data.materials.new("Nova_Blonde_Ponytail_PBR")
    material.use_nodes=True
    bs=material.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Roughness"].default_value=.48
    w=h=512
    xs=np.linspace(0,1,w,dtype=np.float32)[None,:]
    ys=np.linspace(0,1,h,dtype=np.float32)[:,None]
    stripe=np.sin(xs*2*math.pi*42+np.sin(ys*2*math.pi*2)*.75)
    stripe2=np.sin(xs*2*math.pi*71+np.cos(ys*2*math.pi*3)*.43)
    shine=.84+.075*stripe+.035*stripe2+.045*np.sin(ys*2*math.pi)
    rgba=np.zeros((h,w,4),dtype=np.float32)
    for c,v in enumerate([.85,.64,.38]):
        rgba[:,:,c]=np.clip(v*shine,.0,1.0)
    rgba[:,:,3]=1.0
    img=bpy.data.images.new("Nova_Ponytail_Strands_Albedo",width=w,height=h,alpha=True,float_buffer=False)
    img.pixels.foreach_set(rgba.ravel())
    img.pack()
    tex=material.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image=img
    material.node_tree.links.new(tex.outputs["Color"],bs.inputs["Base Color"])
    hair.data.materials.clear()
    hair.data.materials.append(material)
# Tint hair but preserve its actual image alpha and strand pattern.
for mat in list(hair.data.materials):
    if not mat:continue
    if not mat.use_nodes:continue
    bs=next((n for n in mat.node_tree.nodes if n.type=="BSDF_PRINCIPLED"),None)
    if not bs:continue
    base=bs.inputs["Base Color"]
    original=base.links[0].from_socket if base.is_linked else None
    if original is not None:
        mix=mat.node_tree.nodes.new("ShaderNodeMixRGB")
        mix.blend_type="MULTIPLY"
        mix.inputs[0].default_value=.35
        mix.inputs[2].default_value=(.97,.78,.46,1)
        mat.node_tree.links.new(original,mix.inputs[1])
        mat.node_tree.links.new(mix.outputs[0],base)
    else:
        base.default_value=(.8,.59,.36,1)
    bs.inputs["Roughness"].default_value=.60

# Color-match brows to natural blonde (darker than hair for face contrast).
for mat in list(brows.data.materials):
    if not mat or not mat.use_nodes:continue
    bs=next((n for n in mat.node_tree.nodes if n.type=="BSDF_PRINCIPLED"),None)
    if not bs:continue
    inp=bs.inputs["Base Color"]
    if inp.is_linked:
        src=inp.links[0].from_socket
        mult=mat.node_tree.nodes.new("ShaderNodeMixRGB")
        mult.blend_type="MULTIPLY"
        mult.inputs[0].default_value=.4
        mult.inputs[2].default_value=(.5,.38,.26,1)
        mat.node_tree.links.new(src,mult.inputs[1])
        mat.node_tree.links.new(mult.outputs[0],inp)

# Skin material is original MakeHuman CC0 PBR texture, with slightly warmer tint.
for mat in list(body.data.materials):
    if not mat or "body" not in mat.name.lower() or not mat.use_nodes:continue
    bs=next((n for n in mat.node_tree.nodes if n.type=="BSDF_PRINCIPLED"),None)
    if not bs:continue
    inp=bs.inputs["Base Color"]
    if inp.is_linked:
        src=inp.links[0].from_socket
        mult=mat.node_tree.nodes.new("ShaderNodeMixRGB")
        mult.blend_type="MULTIPLY"
        mult.inputs[0].default_value=.45
        mult.inputs[2].default_value=(.95,.72,.56,1)
        mat.node_tree.links.new(src,mult.inputs[1])
        mat.node_tree.links.new(mult.outputs[0],inp)
    bs.inputs["Roughness"].default_value=.72

# Geometric QC: accessory bounds must follow the face, not float on forehead.
def bounds_world(obj):
    corners=[obj.matrix_world@Vector(c) for c in obj.bound_box]
    return {
      "min": [min(v[i] for v in corners) for i in range(3)],
      "max": [max(v[i] for v in corners) for i in range(3)]
    }
bounds={n:bounds_world(ob) for n,ob in [("eyes",eye),("eyelashes",lashes),("eyebrows",brows),("hair",hair)]}
print("WORLD_ASSET_BOUNDS",bounds)
for name in ("eyes","eyelashes"):
    b=bounds[name]
    centerz=(b["min"][2]+b["max"][2])*.5
    assert 1.42<centerz<1.55,(name,centerz)

# Export only model objects in GLB; no studio lighting.
bpy.ops.object.select_all(action="DESELECT")
for ob in items:ob.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"Nova_V03B_Anatomy_Master.blend"))
bpy.ops.export_scene.gltf(
    filepath=str(OUT/"Nova_V03B_Anatomy_Review.glb"),
    export_format="GLB",use_selection=True,export_apply=False,
    export_image_format="AUTO"
)

# Independent portrait and full-body Blender render inspection.
def point_at(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()
world=bpy.context.scene.world
world.use_nodes=True
bg=world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value=(.13,.16,.20,1)
bg.inputs["Strength"].default_value=.65
def light(name,pos,energy,size,color):
    data=bpy.data.lights.new(name,"AREA")
    ob=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(ob)
    ob.location=pos
    data.energy=energy;data.size=size;data.shape="DISK";data.color=color
    point_at(ob,(0,0,1.15))
light("Face beauty softbox",(-2.0,-3.0,2.8),230,3.0,(1,.93,.86))
light("Face cool fill",(2,-2.1,1.9),125,2.5,(.83,.91,1))
light("Hair edge highlight",(1.3,2.4,2.7),210,2.0,(1,.83,.65))
camdata=bpy.data.cameras.new("Camera")
cam=bpy.data.objects.new("Camera",camdata)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera=cam
camdata.type="ORTHO"
scene=bpy.context.scene
scene.render.image_settings.file_format="PNG"
scene.render.resolution_percentage=100
scene.render.engine="BLENDER_EEVEE_NEXT"
scene.view_settings.view_transform="AgX"
def render(name,location,target,ortho,width,height):
    cam.location=location
    point_at(cam,target)
    camdata.ortho_scale=ortho
    scene.render.resolution_x=width;scene.render.resolution_y=height
    scene.render.filepath=str(OUT/(name+".png"))
    bpy.ops.render.render(write_still=True)
render("Nova_V03B_face",(.0,-1.8,1.61),(.0,0,1.54),.44,900,900)
render("Nova_V03B_full",(1.4,-3.5,1.45),(.0,0,.96),2.02,750,960)
render("Nova_V03B_three_quarter",(2.3,-2.8,1.45),(.0,0,.96),2.0,750,960)

report={
  "prototype":"Nova V0.3B corrected anatomy and facial attachments",
  "input_master":str(SOURCE),
  "blender":bpy.app.version_string,
  "source":"MakeHuman MPFB facial morphs and CC0 asset pack meshes",
  "body_vertices":len(body.data.vertices),
  "head_shape_keys":len(body.data.shape_keys.key_blocks) if body.data.shape_keys else 0,
  "model_mesh_objects":len(items),
  "eye_asset_world_bounds":bounds["eyes"],
  "eyebrow_asset_world_bounds":bounds["eyebrows"],
  "hair_asset_world_bounds":bounds["hair"],
  "limitations":["not a likeness-approved final head","no game rig","hair still initial MPFB asset"],
}
(OUT/"Nova_V03B_report.json").write_text(json.dumps(report,indent=2))
assert len(items)==5
assert report["head_shape_keys"]>=20
assert (OUT/"Nova_V03B_Anatomy_Review.glb").stat().st_size>1000000
assert (OUT/"Nova_V03B_face.png").stat().st_size>100000
print("NOVA_V03B_REPAIRED_MPFB_FACE_OK",json.dumps({k:report[k] for k in ("head_shape_keys","model_mesh_objects","body_vertices")}))
