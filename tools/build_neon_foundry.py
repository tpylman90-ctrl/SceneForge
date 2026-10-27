"""SceneForge original geometry. Free tools; no external assets. Units: meters."""
import bpy, math, random, json
from pathlib import Path
from mathutils import Vector
random.seed(42)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
M={}
def material(name,color,metal=0,rough=.5,emission=0):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
 if emission:
  p.inputs['Emission Color'].default_value=(*color,1); p.inputs['Emission Strength'].default_value=emission
 M[name]=m
material('asphalt',(.035,.055,.07),.3,.24)
material('concrete',(.21,.24,.25),0,.85)
material('wall',(.12,.19,.22),.55,.48)
material('trim',(.035,.06,.075),.7,.35)
material('steel',(.3,.38,.4),.8,.3)
material('rust',(.3,.12,.055),.4,.8)
material('orange',(.95,.27,.045),.4,.43)
material('amber', (1,.5,.12),.1,.3,3)
material('cyan',(.08,.8,1),.1,.3,3)
material('white',(.7,.8,.82),.2,.55)
material('rubber',(.017,.025,.03),0,.85)
material('puddle',(.055,.1,.13),.65,.09)

# Original seamless PBR texture maps, built offline with Blender's bundled NumPy.
# Each material gets albedo, roughness and tangent-space normals exported in GLB.
import numpy as np
N=512
rng=np.random.default_rng(95)
def noise_grid(cells):
    grid=rng.random((cells,cells))
    coords=np.arange(N)*cells/N
    idx=coords.astype(int); frac=coords-idx; frac=frac*frac*(3-2*frac)
    a=grid[idx[:,None]%cells,idx[None,:]%cells]
    c=grid[(idx[:,None]+1)%cells,idx[None,:]%cells]
    d=grid[idx[:,None]%cells,(idx[None,:]+1)%cells]
    e=grid[(idx[:,None]+1)%cells,(idx[None,:]+1)%cells]
    return (a*(1-frac[:,None])+c*frac[:,None])*(1-frac[None,:])+(d*(1-frac[:,None])+e*frac[:,None])*frac[None,:]
def image_map(name,arr,color=False):
    im=bpy.data.images.new(name,width=N,height=N,alpha=True)
    rgba=np.ones((N,N,4),dtype=np.float32)
    if arr.ndim==2: rgba[:,:,:3]=arr[:,:,None]
    else: rgba[:,:,:3]=arr
    if not color: im.colorspace_settings.name='Non-Color'
    im.pixels.foreach_set(rgba.ravel())
    im.pack()
    return im
for name in ['asphalt','concrete','wall','trim','steel','rust','orange']:
    mat=M[name]; nodes=mat.node_tree.nodes; links=mat.node_tree.links; p=nodes.get('Principled BSDF')
    coarse=noise_grid(8); medium=noise_grid(40); grain=rng.random((N,N))
    height=.5*coarse+.3*medium+.2*grain
    dirt=np.clip((coarse-.42)*2,0,1)
    base=np.array(mat.diffuse_color[:3])
    albedo=np.clip(base[None,None,:]*(.68+.5*height[:,:,None]),0,1)
    rough=np.clip(float(p.inputs['Roughness'].default_value)+.22*(height-.5),.1,.95)
    if name in ['wall','orange','trim']:
        scratches=(rng.random((N,N))>.998)
        for i in range(1,9): scratches |= np.roll(scratches,1,axis=1) & (rng.random((N,N))>.4)
        albedo[scratches]=np.array([.23,.27,.28])
        albedo*=1-.28*dirt[:,:,None]
    if name=='asphalt':
        albedo*=.9
        rough=np.clip(.28+.5*medium,.22,.85)
    dy,dx=np.gradient(height)
    normal=np.dstack((-dx*1.5,-dy*1.5,np.ones_like(height)))
    normal/=np.linalg.norm(normal,axis=2)[:,:,None]
    for label,data,socket,col in [('Albedo',albedo,'Base Color',True),('Roughness',rough,'Roughness',False),('Normal',normal*.5+.5,None,False)]:
        tex=nodes.new('ShaderNodeTexImage');tex.image=image_map(name+'_'+label,data,col)
        tex.extension='REPEAT'
        if socket:links.new(tex.outputs['Color'],p.inputs[socket])
        else:
            nm=nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.6
            links.new(tex.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],p.inputs['Normal'])

def box(n,loc,scale,mat,bevel=.025):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.name=n; o.dimensions=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(M[mat])
 if bevel:
  mod=o.modifiers.new('engineered edges','BEVEL'); mod.width=bevel; mod.segments=2
  bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=mod.name)
 return o

def pipe(n,a,b,r,mat='steel',vertices=12):
 a,b=Vector(a),Vector(b); d=b-a
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=d.length,location=(a+b)/2)
 o=bpy.context.object; o.name=n; o.rotation_euler=d.to_track_quat('Z','Y').to_euler(); o.data.materials.append(M[mat]); return o

def text(s,loc,size,mat='white'):
 bpy.ops.object.text_add(location=loc,rotation=(math.pi/2,0,0)); o=bpy.context.object; o.name='lettering_'+s; o.data.body=s; o.data.size=size; o.data.extrude=.002; o.data.materials.append(M[mat]); bpy.ops.object.convert(target='MESH')

# Street: building facade faces south (-Y), Godot maps this to +Z.
box('road',(0,-2,-.17),(28,19,.3),'asphalt')
for x in [-8,8]:
 box('raised sidewalk',(x,0,-.035),(3,16,.24),'concrete')
 for y in range(-7,8):
  box('curb section',(x+(-1.48 if x>0 else 1.48),y,.04),(.15,.95,.25),'steel',.012)
for x in range(-6,7,2):
 box('lane dash',(x,-5,.002),(.9,.08,.008),'orange',0)
for i in range(20):
 x=random.uniform(-6,6); y=random.uniform(-9,3)
 bpy.ops.mesh.primitive_circle_add(vertices=24,radius=1,fill_type='NGON',location=(x,y,.008))
 o=bpy.context.object;o.name='irregular wet patch';o.scale=(random.uniform(.3,.9),random.uniform(.15,.4),1);o.data.materials.append(M['puddle'])
 for v in o.data.vertices:v.co*=random.uniform(.8,1.12)
for x in [-5.8,5.8]:
 for y in [-6,-2,2]:
  box('drain surround',(x,y,.01),(.5,1,.03),'trim')
  for j in range(9):box('drain slat',(x,y-.4+j*.1,.035),(.43,.025,.025),'steel',.003)
# Main repair bay, genuine doorway and accessible interior.
box('left structural pier',(-4.5,4,2.5),(5,1,5),'wall')
box('right structural pier',(4.5,4,2.5),(5,1,5),'wall')
box('shop lintel',(0,4,4.45),(4,1,1.1),'trim')
box('interior floor',(0,6,.03),(5,5,.08),'concrete')
box('shop back wall',(0,8.5,2),(6,.3,4),'wall')
for x in [-2.7,2.7]:box('shop side',(x,6,2),(.3,5,4),'trim')
box('shop roof',(0,6,4.1),(6,5,.2),'trim')
for x in [-2.1,2.1]:
 box('door frame',(x,3.38,1.95),(.23,.24,3.9),'steel')
 for z in [.3,1.2,2.1,3.1]:
  box('frame bracket',(x,3.21,z),(.4,.08,.14),'orange')
  for dx in [-.13,.13]:pipe('fastener',(x+dx,3.15,z),(x+dx,3.22,z),.035,'steel',8)
for z in [3.5,3.65,3.8]:box('rolled shutter',(0,3.5,z),(4,.3,.12),'steel')
box('sign backing',(0,3.28,4.5),(5.4,.22,.8),'trim')
text('NEON FOUNDRY',(-2.38,3.13,4.28),.48,'cyan')
text('REPAIR / REFIT / RECOVER',(-1.8,3.13,4.02),.15,'white')
box('canopy',(0,2.9,3.95),(6,2,.15),'trim')
for x in [-2.5,0,2.5]:box('canopy light',(x,2.25,3.83),(.85,.16,.04),'amber')
# Paneled walls, inset ribs, vents, utility routing and serial labels.
for side in [-1,1]:
 for k in range(4):
  x=side*(2.65+k*1.1)
  box('facade panel',(x,3.43,2.1),(1.04,.12,3.7),'wall')
  box('panel seam',(x+.46,3.32,2.1),(.035,.035,3.4),'steel',.003)
  for z in [.45,3.7]:
   for dx in [-.38,.38]:pipe('panel bolt',(x+dx,3.32,z),(x+dx,3.39,z),.023,'steel',8)
 for z in [4.85,5.05]:pipe('service main',(side*2.8,3.2,z),(side*7,3.2,z),.09)
 for x in [side*4.5,side*6.4]:
  pipe('conduit',(x,3.17,.5),(x,3.17,4.8),.045,'rust')
  for z in [1,2,3,4]:box('pipe clamp',(x,3.1,z),(.23,.08,.055),'steel')
box('vent housing',(-4.5,3.1,2.4),(1.7,.45,1.25),'trim')
for j in range(10):box('vent blade',(-4.5,2.84,1.9+j*.1),(1.5,.12,.045),'steel',.006)
box('junction unit',(3.3,3.06,1.4),(.8,.6,1.25),'orange')
box('junction inset',(3.3,2.74,1.6),(.58,.03,.5),'trim')
for x in [3.12,3.3,3.48]:box('status indicator',(x,2.71,1.65),(.05,.02,.15),'cyan')
text('DANGER',(2.96,2.72,1.1),.12)
# Workbench and equipment in the bay.
box('bench',(0,7.5,.95),(3.4,.85,.18),'steel')
for x in [-1.5,1.5]:box('bench legs',(x,7.5,.45),(.12,.7,.9),'trim')
for x in [-1.15,0,1.15]:
 box('drawer',(x,7.3,.65),(.95,.6,.35),'orange')
 box('drawer pull',(x,6.97,.7),(.4,.06,.04),'steel')
for i in range(8):box('hanging tools',(-1.6+i*.43,8.27,1.7),(.08,.08,.5+(i%3)*.08),'steel')
box('tool wall rail',(0,8.2,2.1),(3.8,.1,.1),'orange')
box('terminal',(1.2,7.4,1.3),(.6,.4,.5),'trim')
box('terminal screen',(1.2,7.18,1.35),(.48,.02,.3),'cyan')
# Central power assembly on maintenance stand.
for x in [-.55,.55]:box('stand foot',(x,5.5,.15),(.2,1.1,.3),'orange')
pipe('reactor casing',(-.9,5.5,1.15),(.9,5.5,1.15),.48,'steel',32)
for x in [-.85,-.65,.65,.85]:
 pipe('reactor rib',(x-.035,5.5,1.15),(x+.035,5.5,1.15),.54,'trim',32)
for a in range(0,360,45):
 ang=math.radians(a); y=5.5+math.cos(ang)*.49; z=1.15+math.sin(ang)*.49
 pipe('reactor luminous rail',(-.58,y,z),(.58,y,z),.025,'cyan')
# Street props and adjacent buildings.
for x,y in [(-3,1.5),(3.8,.7),(5.2,1.2)]:
 box('cargo crate',(x,y,.42),(.8,.8,.84),'orange')
 for dx in [-.32,.32]:box('crate band',(x+dx,y,.43),(.06,.84,.9),'trim')
for x in [-6,6]:
 for y in [-1,1]:
  pipe('bollard',(x,y,0),(x,y,.9),.1,'trim'); pipe('bollard marker',(x,y,.65),(x,y,.78),.105,'amber')
for side in [-1,1]:
 for y in [-7,-1,6]:
  box('neighbor mass',(side*10,y,4),(4,5.5,8),'wall')
  for z in [2.5,5.5]:
   for yy in [y-1.5,y,y+1.5]:
    box('window recess',(side*7.96,yy,z),(.08,1.1,1.3),'trim')
    box('lit window',(side*7.9,yy,z),(.02,.85,.8),'amber' if yy==y else 'steel')
for y in [-6,0]:
 pipe('lamp post',(-6.4,y,0),(-6.4,y,4.3),.065,'steel')
 pipe('lamp arm',(-6.4,y,4.3),(-5.4,y,4.3),.06)
 box('lamp head',(-5.4,y,4.23),(.7,.3,.12),'trim');box('lamp lens',(-5.4,y,4.15),(.55,.2,.02),'cyan')
# Batch geometry by material to keep draw calls bounded.
for mat in M.values():
 obs=[o for o in bpy.context.scene.objects if o.type=='MESH' and len(o.data.materials) and o.data.materials[0]==mat]
 if not obs:continue
 bpy.ops.object.select_all(action='DESELECT')
 for o in obs:o.select_set(True)
 bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();obs[0].name='Foundry_'+mat.name
# UV cube projection in world scale after batching keeps surface grain consistent.
for o in bpy.context.scene.objects:
 if o.type!='MESH': continue
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
 bpy.ops.uv.cube_project(cube_size=2.0,correct_aspect=True)
 bpy.ops.object.mode_set(mode='OBJECT')
 # Weighted normals preserve broad planar faces and smooth the beveled edges.
 mod=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL');mod.keep_sharp=True;mod.weight=50
 bpy.ops.object.modifier_apply(modifier=mod.name)
root=Path.cwd();dest=root/'game/assets';dest.mkdir(parents=True,exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(dest/'neon_foundry.glb'),export_format='GLB',use_selection=False,export_yup=True,export_normals=True,export_texcoords=True)
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes)
assert triangles<180000,triangles
assert len(meshes)<=16,len(meshes)
(root/'build').mkdir(exist_ok=True)
(root/'build/asset-report.json').write_text(json.dumps({'asset':'Neon Foundry corner','license':'CC0-1.0','source':'Original Blender script; no external assets','triangles':triangles,'mesh_batches':len(meshes),'blender':bpy.app.version_string},indent=2))
print('SCENEFORGE_ASSET_VALIDATED',triangles,len(meshes))
# Source preview: CPU Cycles requires no GPU.
world=bpy.context.scene.world or bpy.data.worlds.new('Dusk');bpy.context.scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.2,.32,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35
for loc,color,power,size in [((0,1,7),(.5,.7,1),1600,8),((0,5.5,3.4),(1,.5,.2),1000,3),((-4,-3,5),(.1,.65,1),900,4)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.color=color;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,4,1))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(8,-11,6));cam=bpy.context.object;cam.rotation_euler=(Vector((0,4,2))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=32
s=bpy.context.scene;s.camera=cam;s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True;s.render.resolution_x=960;s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.filepath=str(root/'build/NeonFoundry-preview.png');bpy.ops.wm.save_as_mainfile(filepath=str(root/'build/NeonFoundry.blend'));bpy.ops.render.render(write_still=True)
