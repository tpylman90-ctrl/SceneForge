"""Real physically based Blender Cycles reviews of the original Solstice master."""
from pathlib import Path
import bpy
from mathutils import Vector

out=Path("build/original-solstice").resolve()
master=out/"Solstice_S01_Master.blend"
assert master.exists(),master
bpy.ops.wm.open_mainfile(filepath=str(master))
scene=bpy.context.scene
camera=bpy.data.objects["Studio_Camera"]
world=scene.world
world.node_tree.nodes["Background"].inputs["Color"].default_value=(.14,.18,.21,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.37

def cv(p):
    return Vector((p[0],-p[2],p[1]))
def softbox(name,pos,energy,size,shape_y,colour):
    data=bpy.data.lights.new(name,"AREA")
    obj=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    obj.location=cv(pos)
    obj.rotation_euler=(cv((0,1.,0))-obj.location).to_track_quat("-Z","Y").to_euler()
    data.energy=energy
    data.shape="RECTANGLE"
    data.size=size
    data.size_y=shape_y
    data.color=colour
softbox("Left sculpting softbox",(4.6,7.3,5.5),2000,6.0,2.7,(.89,.96,1.))
softbox("Right warm rim",(-5.,6.1,-3.1),2450,6.5,2.,(1.,.84,.72))
softbox("Front windscreen",(-2.1,6.8,8.0),1900,3.4,2.,(.84,1.,.99))
softbox("High overhead",(0,9.,-1.),1700,7.8,3.7,(1.,1.,1.))
ground=bpy.data.materials.new("Studio graphite floor")
ground.use_nodes=True
shader=ground.node_tree.nodes.get("Principled BSDF")
shader.inputs["Base Color"].default_value=(.045,.058,.067,1)
shader.inputs["Roughness"].default_value=.69
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,.12))
bpy.context.object.name="Studio ground not in GLB"
bpy.context.object.data.materials.append(ground)
scene.render.engine="CYCLES"
scene.cycles.samples=20
scene.render.resolution_x=1280
scene.render.resolution_y=780
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False
scene.view_settings.view_transform="AgX"
camera.data.type="ORTHO"

def shot(name,pos,scale):
    camera.location=cv(pos)
    camera.rotation_euler=(cv((0,1.05,0))-camera.location).to_track_quat("-Z","Y").to_euler()
    camera.data.ortho_scale=scale
    scene.render.filepath=str(out/("Solstice-studio-"+name+".png"))
    bpy.ops.render.render(write_still=True)
    assert Path(scene.render.filepath).stat().st_size>5000
    print("SCENEFORGE_SOLSTICE_STUDIO_RENDER_OK",name)
shot("hero",(6.8,3.5,8.7),9.7)
shot("rear-quarter",(-6.8,3.5,-8.7),9.7)
shot("profile",(11.4,2.35,-.1),9.2)
shot("thrust",(-2.9,2.30,-7.1),6.5)
