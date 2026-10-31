"""Reproducible neutral studio review of FORGE master surfaces."""
import os,runpy
os.environ['SCENEFORGE_ONLY_CRAFT']='forge'
runpy.run_path('tools/build_fleet.py',run_name='__main__')
import bpy
from mathutils import Vector
from pathlib import Path
scene=bpy.context.scene
# Neutral clay exposes surface waviness without distracting trim or glow.
for material in bpy.data.materials:
 if material.use_nodes and not os.environ.get('SCENEFORGE_PREVIEW_FINISH'):
  p=material.node_tree.nodes.get('Principled BSDF')
  if p:
   p.inputs['Base Color'].default_value=(.11,.16,.20,1) if 'glass' in material.name else ((.055,.065,.075,1) if 'carbon' in material.name else (.42,.46,.50,1))
   p.inputs['Metallic'].default_value=.25;p.inputs['Roughness'].default_value=.30
world=bpy.data.worlds.new('Review studio');scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.1,.1,.1,1)
for loc,power,size in [((2,-2,7),1800,5),((-4,1,4),1400,4),((1,5,3),1000,3)]:
 bpy.ops.object.light_add(type='AREA',location=loc);obj=bpy.context.object;obj.data.energy=power;obj.data.shape='RECTANGLE';obj.data.size=size;obj.data.size_y=1
 obj.rotation_euler=(Vector((0,0,1))-obj.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=7.3
scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True
scene.render.resolution_x=960;scene.render.resolution_y=960;scene.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(Path('build/Forge-body-review.blend').resolve()))
for name,loc in [('hero',(6,-9,5)),('side',(9,0,1)),('top',(0,0,10)),('front',(0,-10,2)),('rear-quarter',(6,9,4)),('rear',(0,10,2))]:
 cam.location=loc;cam.rotation_euler=(Vector((0,-.2,1))-cam.location).to_track_quat('-Z','Y').to_euler()
 if name=='top':cam.rotation_euler.z+=1.5707963267948966
 scene.render.filepath=str(Path('build/'+('Forge-canopy-shoulder-' if os.environ.get('SCENEFORGE_PREVIEW_FINISH') else 'Forge-body-')+name+'.png').resolve());bpy.ops.render.render(write_still=True)
