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
material('window_warm',(.25,.17,.09),0,.65,.32)
material('window_cool',(.07,.14,.18),0,.55,.2)
material('grime',(.045,.055,.052),0,.98)
material('vehicle_glass',(.025,.065,.085),.6,.16)

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
for name in ['concrete','wall','trim','steel','rust','orange']:
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
    normal=np.dstack((-dx*.5,-dy*.5,np.ones_like(height)))
    normal/=np.linalg.norm(normal,axis=2)[:,:,None]
    for label,data,socket,col in [('Albedo',albedo,'Base Color',True),('Roughness',rough,'Roughness',False),('Normal',normal*.5+.5,None,False)]:
        if col: data=np.power(np.clip(data,0,1),1/2.2)
        tex=nodes.new('ShaderNodeTexImage');tex.image=image_map(name+'_'+label,data,col)
        tex.extension='REPEAT'
        if socket:links.new(tex.outputs['Color'],p.inputs[socket])
        else:
            nm=nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.35
            links.new(tex.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],p.inputs['Normal'])

# Unique road atlas: dry aggregate and water share one opaque surface.
# No repeated road UVs, raised water polygons, alpha blending or extra draw pass.
N=1024
road_rng=np.random.default_rng(2026)
xx,yy=np.meshgrid(np.linspace(-14,14,N),np.linspace(-11.5,7.5,N))
macro=.55*noise_grid(7)+.3*noise_grid(19)+.15*noise_grid(47)
aggregate=road_rng.random((N,N))
wet=np.zeros((N,N))
for i in range(26):
    cx=road_rng.uniform(-6.2,6.2);cy=road_rng.uniform(-9,3)
    rx=road_rng.uniform(.3,1.3);ry=road_rng.uniform(.17,.55)
    angle=road_rng.uniform(-math.pi,math.pi)
    px=(xx-cx)*math.cos(angle)+(yy-cy)*math.sin(angle)
    py=-(xx-cx)*math.sin(angle)+(yy-cy)*math.cos(angle)
    distance=(px/rx)**2+(py/ry)**2
    boundary=distance+.12*np.sin(xx*9+yy*7)+.08*np.sin(xx*19-yy*12)
    falloff=np.clip((1.2-boundary)/.5,0,1)
    falloff=falloff*falloff*(3-2*falloff)
    wet=np.maximum(wet,falloff)
road_base=np.array([.045,.058,.067])
albedo=road_base[None,None,:]*(.9+.14*macro[:,:,None]+.1*(aggregate[:,:,None]-.5))
albedo*=1-.24*wet[:,:,None]
rough=np.clip(.78+.12*(macro-.5)-.63*wet,.12,.9)
height=(aggregate-.5)*.025*(1-wet)
dy,dx=np.gradient(height)
normal=np.dstack((-dx,-dy,np.ones_like(height)))
normal/=np.linalg.norm(normal,axis=2)[:,:,None]
mat=M['asphalt'];p=mat.node_tree.nodes.get('Principled BSDF')
p.inputs['Metallic'].default_value=.03
for label,data,socket,col in [('Albedo',np.power(albedo,1/2.2),'Base Color',True),('Roughness',rough,'Roughness',False),('Normal',normal*.5+.5,None,False)]:
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image=image_map('RoadAtlas_'+label,data,col);tex.extension='EXTEND'
    if socket:mat.node_tree.links.new(tex.outputs['Color'],p.inputs[socket])
    else:
        nm=mat.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.3
        mat.node_tree.links.new(tex.outputs['Color'],nm.inputs['Color'])
        mat.node_tree.links.new(nm.outputs['Normal'],p.inputs['Normal'])
N=512

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
# Wet areas are baked into the road material; no floating puddle meshes.
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
    lit=(int(y+7)+int(z*2)+int(yy*2)+side)%4
    backing='window_warm' if lit==0 else ('window_cool' if lit==1 else 'trim')
    box('dim interior',(side*7.91,yy,z),(.03,.88,.95),backing,.003)
    box('window mullion',(side*7.83,yy,z),(.1,.035,1.05),'trim',.003)
    box('window sill',(side*7.78,yy,z-.56),(.3,1.16,.1),'steel',.01)
    box('window rail',(side*7.83,yy,z+.52),(.08,1.07,.06),'trim',.003)
    if lit in [0,1]:
     box('interior shelf',(side*7.85,yy+.17,z-.19),(.06,.46,.045),'trim',.003)
     box('interior silhouette',(side*7.84,yy+.27,z-.06),(.07,.13,.23),'trim',.003)
    if lit!=1:
     for slat in range(5 if lit==0 else 9):
      box('venetian blind',(side*7.81,yy,z+.43-slat*.09),(.06,.91,.028),'steel' if lit==0 else 'trim',.002)
for y in [-6,0]:
 pipe('lamp post',(-6.4,y,0),(-6.4,y,4.3),.065,'steel')
 pipe('lamp arm',(-6.4,y,4.3),(-5.4,y,4.3),.06)
 box('lamp head',(-5.4,y,4.23),(.7,.3,.12),'trim');box('lamp lens',(-5.4,y,4.15),(.55,.2,.02),'cyan')

# Original service props; opaque materials, no added lights.
def hose(name,points,radius=.025):
 curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.resolution_u=1
 spline=curve.splines.new('POLY');spline.points.add(len(points)-1)
 for p,co in zip(spline.points,points):p.co=(*co,1)
 curve.bevel_depth=radius;curve.bevel_resolution=2
 obj=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(obj);obj.data.materials.append(M['rubber'])
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.object.convert(target='MESH')
box('reel bracket',(-3.05,3.12,1.25),(.75,.12,.8),'trim')
for i in range(4):
 hose('coiled air line',[(-3.05+(.23+i*.018)*math.cos(t),2.99-i*.035,1.25+(.23+i*.018)*math.sin(t)) for t in np.linspace(0,math.tau,41)],.023)
pipe('reel spindle',(-3.05,2.9,1.25),(-3.05,3.2,1.25),.06,'steel')
hose('loose air hose',[(-3.05,2.85,.99),(-2.9,2.8,.6),(-2.8,2.7,.12),(-2.4,2.4,.045),(-2,2.5,.045)],.026)
pipe('air coupler',(-2,2.5,.045),(-1.87,2.55,.045),.045,'steel')
box('field case base',(-4.05,1.75,.16),(1.05,.65,.3),'trim')
box('case liner',(-4.05,1.75,.325),(.94,.55,.045),'rubber')
lid=box('open case lid',(-4.05,2.05,.59),(1.05,.08,.59),'orange');lid.rotation_euler.x=-.24
for x in [-4.35,-4.05,-3.75]:
 box('case divider',(x,1.75,.35),(.025,.5,.08),'steel',.003)
 pipe('socket tool',(x+.08,1.59,.38),(x+.08,1.92,.38),.025,'steel',8)
 box('tool grip',(x+.08,1.65,.38),(.055,.12,.055),'orange',.008)
for x in [-4.43,-3.67]:box('case clasp',(x,1.39,.18),(.1,.06,.12),'steel')
for x in [-.94,.94]:
 pipe('end flange',(x-.03,5.5,1.15),(x+.03,5.5,1.15),.55,'steel',32)
 for a in range(0,360,60):
  t=math.radians(a);y=5.5+.47*math.cos(t);z=1.15+.47*math.sin(t)
  pipe('flange fastener',(x-.065,y,z),(x+.065,y,z),.025,'trim',8)
pipe('pressure feed',(-.45,5.5,1.61),(-.45,5.5,1.82),.07,'steel')
pipe('feed elbow',(-.45,5.5,1.82),(-.45,6,1.82),.065,'steel')
hose('supply cable',[(-.45,6,1.82),(-1.1,6.3,1.5),(-1.3,6.5,.15),(-1.4,7.3,.1),(-1.4,7.5,.8)],.033)
box('service badge',(0,4.99,1.15),(.46,.025,.16),'orange',.006)
text('NF-07',(-.19,4.97,1.11),.085,'trim')
box('vise base',(-1.05,7.2,1.1),(.34,.28,.1),'trim')
for x in [-1.14,-.96]:box('vise jaw',(x,7.2,1.24),(.065,.27,.2),'steel')
pipe('vise screw',(-1.35,7.2,1.18),(-.8,7.2,1.18),.025,'steel')
for i in range(4):pipe('spare coupling',(-.5+i*.18,7.5,1.09),(-.5+i*.18,7.5,1.22),.055,'steel',12)
pipe('stool seat',(1.85,6.35,.65),(1.85,6.35,.73),.26,'trim',20)
for dx,dy in [(-.17,-.17),(.17,-.17),(.17,.17),(-.17,.17)]:
 pipe('stool leg',(1.85+dx,6.35+dy,.68),(1.85+dx*1.2,6.35+dy*1.2,.08),.025,'steel')
for x in [-6.4,-4.5,4.5,6.4]:
 box('pipe termination',(x,3.25,.43),(.23,.12,.23),'steel')
 for j in range(3):
  length=.23+j*.18
  box('rain runoff',(x+(j-1)*.065,3.355,.8-length/2),(.035+j*.018,.005,length),'grime',0)
for x,s,z in [(-6.1,'BAY 07',2.4),(4.25,'AUTHORIZED',2.4),(4.25,'SERVICE ACCESS',2.17)]:
 box('label plate',(x+.47,3.3,z+.05),(1.1,.04,.27),'trim',.008)
 text(s,(x,3.27,z-.02),.12,'white')
for x in [-1.8,-1.25,-.6,.4,1.2,1.8]:
 box('threshold scuff',(x,3.46,.085),(.23,.06,.012),'steel',.002)
text('KEEP CLEAR',(-.78,3.18,.2),.16,'orange')


# Architecture pass: layered rooflines, service access and a bounded district backdrop.
for side in [-1,1]:
 for index,y in enumerate([-7,-1,6]):
  street_x=side*7.92
  box('facade plinth',(street_x,y,.26),(.2,5.5,.42),'trim')
  box('floor belt',(street_x,y,4.05),(.18,5.5,.16),'steel')
  box('roof fascia',(side*9.9,y,7.98),(4.35,5.75,.28),'trim')
  box('roof cap',(side*9.9,y,8.15),(4.4,5.8,.1),'steel')
  for yy in [y-2.62,y+2.62]:
   box('facade edge pier',(side*7.82,yy,4),(.2,.16,7.8),'trim')
  # Opaque door panel is mounted at the building face.
  dy=y+.85
  box('service door frame',(side*7.81,dy,1.15),(.22,1.12,2.3),'trim')
  box('service door',(side*7.68,dy,1.1),(.08,.89,2.1),'wall')
  box('door kick plate',(side*7.62,dy,.25),(.025,.85,.25),'steel')
  box('door pull',(side*7.57,dy-.3,1.12),(.1,.04,.22),'steel')
  box('door transom',(side*7.61,dy,2.02),(.025,.65,.12),'window_warm' if index%2 else 'window_cool')
  box('door canopy',(side*7.49,dy,2.4),(.9,1.3,.1),'trim')
  # Downpipe and its visible elbows connect roof to the curb.
  pipe('downpipe',(side*7.7,y-2.35,.4),(side*7.7,y-2.35,7.85),.06,'rust')
  pipe('roof downpipe elbow',(side*7.7,y-2.35,7.85),(side*8.1,y-2.35,7.85),.06,'rust')
  for z in [1.2,3.8,6.4]:box('downpipe saddle',(side*7.74,y-2.35,z),(.2,.2,.07),'steel')
  box('roof HVAC',(side*10,y,8.65),(1.7,2,1),'wall')
  box('HVAC cap',(side*10,y,9.18),(1.85,2.15,.12),'trim')
  for j in range(6):box('HVAC side grille',(side*9.1,y-.7+j*.26,8.7),(.06,.08,.6),'steel',.003)
# Repair shop parapet and seams finish the exposed upper edge.
box('shop coping',(0,4,5.17),(14.25,1.25,.15),'steel')
box('shop parapet',(0,4.15,5.48),(14,.4,.5),'trim')
for x in [-5,-2.5,0,2.5,5]:
 box('parapet cap seam',(x,4.15,5.76),(.045,.55,.045),'steel',.003)
# Overhead utility spine: pipe collars at the building connections.
for yy,z in [(-2,6.7),(-1.7,6.95)]:
 pipe('cross street utility',(-8,yy,z),(8,yy,z),.085,'steel',12)
 for x in [-7.7,-7.35,7.35,7.7]:
  pipe('utility collar',(x-.045,yy,z),(x+.045,yy,z),.115,'trim',12)
for x in [-7.7,7.7]:
 box('utility support',(x,-1.85,6.62),(.3,.65,.15),'orange')
hose('overhead cable',[(-7.8+15.6*t,-2.35,6.7-.55*math.sin(math.pi*t)) for t in np.linspace(0,1,33)],.025)
# Background uses one separately batched copy so distant silhouettes do not cast near-field shadows.
M['skyline']=M['wall'].copy();M['skyline'].name='skyline'
# Background masses stay outside the walkable scene and use existing materials.
for x,y,width,height in [(-10,15,4.2,12),(-4,17,4,10),(2,16,4.5,13.5),(9,15,4,11.5)]:
 box('distant district',(x,y,height/2),(width,4,height),'skyline',.05)
 box('distant roof',(x,y,height+.08),(width+.15,4.15,.16),'skyline')
 for z in [7,9,11]:
  if z>height-.5:continue
  for dx in [-.9,0,.9]:
   box('distant window',(x+dx,y-2.025,z),(.45,.025,.6),'window_warm' if (int(x)+int(z))%3 else 'window_cool',.003)
# The rear of the review space terminates at a utility fence rather than open void.
for x in range(-7,8):
 pipe('fence post',(x,-11.35,0),(x,-11.35,2.2),.035,'trim',8)
for z in [.4,1.1,1.8]:pipe('fence rail',(-7,-11.35,z),(7,-11.35,z),.025,'steel',8)
for x in [-10,-4,3,10]:
 box('rear district mass',(x,-18,4.5),(5,5,9),'skyline')
 box('rear roof',(x,-18,9.1),(5.2,5.2,.2),'skyline')



# Kestrel hero rebuild: original swept coupe, 6.2 m long. No paid assets.
vehicle_before=set(bpy.context.scene.objects)
material('kestrel_slate',(.18,.215,.24),.65,.42)
material('kestrel_orange',(.58,.145,.035),.5,.34)
material('kestrel_carbon',(.025,.032,.038),.65,.3)
material('repulsor_glow',(.04,.42,.62),.1,.22,1.7)
M['vehicle_glass'].node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.12
M['vehicle_glass'].node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value=.38
M['vehicle_glass'].node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value=.5
# Subtle original 2x2 twill weave, baked maps rather than a runtime pattern shader.
gx,gy=np.meshgrid(np.arange(N),np.arange(N))
warp=((gx//8+gy//8)%4)<2
thread=.78+.14*np.sin((gx%8)/8*math.pi)+.08*np.sin((gy%8)/8*math.pi)
weave=(.035+.012*warp)*thread
carbon=M['kestrel_carbon'];pn=carbon.node_tree.nodes['Principled BSDF']
tx=carbon.node_tree.nodes.new('ShaderNodeTexImage');tx.image=image_map('Kestrel_twill',np.power(np.dstack((weave*.83,weave*.94,weave)),1/2.2),True)
carbon.node_tree.links.new(tx.outputs['Color'],pn.inputs['Base Color'])
cx,cy=0,-.8
def hero_mesh(name,verts,faces,mat,bevel=0):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
 obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj);obj.data.materials.append(M[mat])
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
 if bevel:
  mod=obj.modifiers.new('Manufactured edge radius','BEVEL');mod.width=bevel;mod.segments=3;bpy.ops.object.modifier_apply(modifier=mod.name)
 return obj
profile=[(-3.15,.035,.54,.65),(-2.8,.34,.55,.81),(-2.0,.84,.58,1.03),(-1.0,1.12,.64,1.24),(.2,1.28,.68,1.32),(1.25,1.14,.73,1.26),(2.05,.8,.74,1.1),(2.5,.55,.78,1.0)]
def dims(y):
 return tuple(float(np.interp(y,[p[0] for p in profile],[p[k] for p in profile])) for k in [1,2,3])
cross=[(-.7,0),(.7,0),(.96,.15),(1,.46),(.92,.78),(.7,1),(-.7,1),(-.92,.78),(-1,.46),(-.96,.15)]
verts=[]
ys=np.linspace(-3.15,2.5,49)
for y in ys:
 w,lo,hi=dims(y)
 for xx,zz in cross:verts.append((cx+xx*w,cy+y,lo+zz*(hi-lo)))
faces=[tuple(reversed(range(10)))]
for j in range(len(ys)-1):
 for i in range(10):faces.append((j*10+i,j*10+(i+1)%10,(j+1)*10+(i+1)%10,(j+1)*10+i))
faces.append(tuple((len(ys)-1)*10+i for i in range(10)))
hero_mesh('Swept slate monocoque',verts,faces,'kestrel_slate',.015)
# Carbon hood inset follows the descending beak, with a slender raised center ridge.
verts=[];ys=np.linspace(-2.92,-.65,28)
for y in ys:
 w,lo,hi=dims(y)
 for f in np.linspace(-1,1,9):
  verts.append((cx+f*w*.54,cy+y,hi+.012+.035*(1-f*f)))
faces=[]
for j in range(len(ys)-1):
 for i in range(8):faces.append((j*9+i,j*9+i+1,(j+1)*9+i+1,(j+1)*9+i))
hero_mesh('Carbon beak inset',verts,faces,'kestrel_carbon')
# Swept flank panels taper like overlapping flight feathers.
for side in [-1,1]:
 for i in range(3):
  y=-1.35+i*.67
  pts=[]
  for yy,f,zf in [(y,1.01,.7),(y+.92,1.01,.75),(y+.7,1.015,.4),(y+.08,1.015,.42)]:
   w,lo,hi=dims(yy);pts.append((cx+side*w*f,cy+yy,lo+(hi-lo)*zf))
  hero_mesh('Burnt orange flight panel',pts,[(0,1,2,3)],'kestrel_orange')
  a,bp=pts[0],pts[1];pipe('Flank rust pinstripe',a,bp,.012,'rust',8)
 # Vented side intake recessed behind the canopy shoulder.
 for i in range(7):
  yy=.55+i*.095;w,lo,hi=dims(yy)
  o=box('Side intake louver',(cx+side*(w+.012),cy+yy,1.03),(.025,.045,.15),'trim',.003);o.rotation_euler.x=-.25
 # Slim swept mirrors rather than rectangular stalk-mounted boxes.
 pipe('Mirror arm',(cx+side*.83,cy-.65,1.35),(cx+side*1.24,cy-.82,1.35),.024,'trim')
 o=box('Camera mirror',(cx+side*1.25,cy-.87,1.37),(.22,.32,.065),'kestrel_slate',.025);o.rotation_euler.z=side*.3
# Continuous teardrop canopy: curved in both directions, opaque polarized finish.
verts=[];canopy_rows=33;canopy_cols=33
for j,t in enumerate(np.linspace(0,1,canopy_rows)):
 y=-.92+2.53*t
 w=.83*(math.sin(math.pi*t)**.55)*(1-.25*t)+.012
 h=.88*(math.sin(math.pi*t)**.7)
 base=1.2+.02*math.sin(math.pi*t)
 for a in np.linspace(0,math.pi,canopy_cols):
  verts.append((cx+w*math.cos(a),cy+y,base+h*math.sin(a)))
faces=[]
for j in range(canopy_rows-1):
 for i in range(canopy_cols-1):faces.append((j*canopy_cols+i,j*canopy_cols+i+1,(j+1)*canopy_cols+i+1,(j+1)*canopy_cols+i))
canopy=hero_mesh('Polarized teardrop canopy',verts,faces,'vehicle_glass')
for p in canopy.data.polygons:p.use_smooth=True
for side in [-1,1]:
 points=[]
 for t in np.linspace(0,1,49):
  y=-.92+2.53*t;w=.83*(math.sin(math.pi*t)**.55)*(1-.25*t)+.012
  points.append((cx+side*w,cy+y,1.2+.02*math.sin(math.pi*t)))
 # A thin continuous seal preserves the seamless glass silhouette.
 hose('Canopy seal',points,.018)
 # Side door latch and inset split line.
 pipe('Door seam',(cx+side*1.03,cy-.5,1.21),(cx+side*1.2,cy+.5,1.26),.01,'trim',8)
 box('Flush door latch',(cx+side*1.17,cy+.57,1.2),(.025,.2,.035),'steel',.008)
# Four downward magnetic repulsors, fairings and visible suspension connections.
for side in [-1,1]:
 for yy in [-1.4,1.25]:
  x=cx+side*(1.0 if yy<0 else 1.12)
  pipe('Repulsor arm',(cx+side*.65,cy+yy,.7),(x,cy+yy,.66),.09,'trim',16)
  bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=(x,cy+yy,.64))
  fair=bpy.context.object;fair.name='Swept repulsor fairing';fair.scale=(.38,.64,.24);fair.data.materials.append(M['kestrel_slate'])
  bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
  for p in fair.data.polygons:p.use_smooth=True
  pipe('Recessed magnetic bell',(x,cy+yy,.31),(x,cy+yy,.59),.29,'trim',32)
  bpy.ops.mesh.primitive_torus_add(major_radius=.27,minor_radius=.028,major_segments=32,minor_segments=8,location=(x,cy+yy,.315))
  ring=bpy.context.object;ring.name='Magnetic repulsor halo';ring.data.materials.append(M['repulsor_glow'])
  pipe('Bell inner core',(x,cy+yy,.325),(x,cy+yy,.36),.19,'steel',24)
  for angle in range(0,360,60):
   t=math.radians(angle)
   pipe('Repulsor radial vane',(x+.12*math.cos(t),cy+yy+.12*math.sin(t),.33),(x+.25*math.cos(t),cy+yy+.25*math.sin(t),.33),.012,'steel',6)
# Narrow raptor-eye running lights follow the beak.
for side in [-1,1]:
 for i in range(9):
  t=i/8;y=-2.55+.55*t;w,lo,hi=dims(y)
  point=(cx+side*w*.86,cy+y,hi-.035)
  pipe('Raptor eye light',point,(point[0]+side*.035,point[1]+.065,point[2]+.012),.017,'repulsor_glow',8)
# Air-breathing intake and compact drive behind the cockpit.
box('Plasma drive spine',(cx,cy+1.96,1.17),(.8,.85,.23),'trim',.06)
for i in range(9):
 box('Plasma intake slat',(cx-.31+i*.077,cy+1.88,1.31),(.026,.48,.035),'steel',.004)
pipe('Plasma drive core',(cx,cy+2.0,1.03),(cx,cy+2.55,1.03),.24,'steel',32)
pipe('Plasma drive throat',(cx,cy+2.48,1.03),(cx,cy+2.62,1.03),.17,'repulsor_glow',24)
# Tail feathers remain separate named components for independent vectoring.
for i in range(5):
 x=(i-2)*.24;fan=(i-2)*.18
 length=.86-abs(i-2)*.06
 pts=[(cx+x-.095,cy+2.38,1.08),(cx+x+.095,cy+2.38,1.08),
      (cx+x+.18+fan,cy+2.38+length,1.13),(cx+x+fan,cy+2.55+length,1.1),
      (cx+x-.18+fan,cy+2.38+length,1.13)]
 blade=hero_mesh('TailVector_%d'%i,pts,[(0,1,2,3,4)],'kestrel_carbon')
 blade['tail_vector']=i+1
 # Segmented metallic nozzle edges and amber plasma slit.
 pipe('Tail nozzle edge',pts[1],pts[2],.025,'steel',8)
 pipe('Tail nozzle edge',pts[4],pts[0],.025,'steel',8)
 pipe('Tail plasma slit',(cx+x+fan-.09,cy+2.4+length,1.125),(cx+x+fan+.09,cy+2.4+length,1.125),.018,'amber',8)
# Small inset service hardware, not raised block lettering.
box('Nose service badge',(cx,cy-2.65,.805),(.18,.15,.012),'steel',.004)
for side in [-1,1]:
 for yy in [-1.8,-1.1,.0,1.2]:
  w,lo,hi=dims(yy)
  pipe('Flush panel fastener',(cx+side*w*.72,cy+yy,hi+.004),(cx+side*w*.72,cy+yy,hi+.015),.013,'steel',8)
# Aggressive idle stance: rigid, perfectly still, pitched nose-down by 6 degrees.
vehicle_objects=[o for o in bpy.context.scene.objects if o not in vehicle_before and o.type=='MESH']
from mathutils import Matrix
pitch=Matrix.Rotation(math.radians(6),3,'X')
for obj in vehicle_objects:
 bpy.context.view_layer.objects.active=obj
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True)
 bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
 for v in obj.data.vertices:
  local=obj.matrix_world @ v.co-Vector((cx,cy,0))
  v.co=pitch @ local+Vector((cx,cy,.2))
 obj.location=(0,0,0);obj.rotation_euler=(0,0,0);obj.scale=(1,1,1)
 obj['is_vehicle']=True
# Car's low idle hum is original synthesized audio, generated with Python's standard library.
import wave,array
audio_dir=Path.cwd()/'game/assets';audio_dir.mkdir(parents=True,exist_ok=True)
rate=22050
pcm=array.array('h')
for i in range(rate*2):
 t=i/rate;value=(math.sin(math.tau*220*t)*.5+math.sin(math.tau*660*t)*.16+math.sin(math.tau*880*t)*.045)
 pcm.append(int(value*6500))
with wave.open(str(audio_dir/'kestrel_hum.wav'),'wb') as stream:
 stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(rate);stream.writeframes(pcm.tobytes())

# Rear service yard: continuous ground and detailed visible warehouse fronts.
box('rear yard ground',(0,-18.5,-.12),(40,14,.12),'skyline',.01)
for index,x in enumerate([-10,-4,3,10]):
 height=9.0
 # Street-facing loading shutters are on the +Y side of the rear warehouses.
 box('loading opening',(x,-15.43,1.55),(3.2,.15,3.1),'trim')
 box('loading shutter',(x,-15.32,1.5),(2.9,.08,2.9),'steel')
 for z in [.3,.65,1,1.35,1.7,2.05,2.4,2.75]:
  box('shutter rib',(x,-15.26,z),(2.83,.06,.035),'trim',.003)
 box('loading canopy',(x,-15.0,3.3),(3.5,1.1,.15),'trim')
 box('loading threshold',(x,-15.05,.11),(3.4,.7,.22),'concrete')
 for z in [4.6,6.6]:
  for dx in [-1.4,-.45,.45,1.4]:
   box('rear window frame',(x+dx,-15.43,z),(.7,.12,1),'trim')
   box('rear window',(x+dx,-15.35,z),(.55,.025,.8),'window_warm' if (index+int(dx*3))%3==0 else 'window_cool')
 box('warehouse roof coping',(x,-15.45,9.05),(5.2,.32,.22),'trim')
 pipe('yard downpipe',(x+2.1,-15.3,.25),(x+2.1,-15.3,8.8),.065,'rust')
 for z in [2,5,8]:box('yard pipe clamp',(x+2.1,-15.24,z),(.2,.1,.07),'steel')
 # No new lights: a dim panel suggests an occupied warehouse.
 box('loading number plate',(x,-15.27,3.75),(.8,.05,.35),'orange')
 for dx in [-1.7,1.7]:
  pipe('yard safety bollard',(x+dx,-14.65,0),(x+dx,-14.65,.85),.09,'trim',10)
  pipe('yard bollard band',(x+dx,-14.65,.6),(x+dx,-14.65,.72),.095,'orange',10)
# Stacked yard cargo and low separation wall hide the ground horizon.
for x,y in [(-7,-13.3),(6,-13.5),(11,-14)]:
 box('yard cargo',(x,y,.6),(1.4,1,.0+1.2),'wall')
 box('yard cargo upper',(x+.12,y,.0+1.65),(1.1,.8,.9),'trim')
box('yard retaining wall',(0,-24.5,1),(38,.35,2),'skyline')

# Batch scenery and vehicle separately; keep tail panels independently addressable.
for mat in M.values():
 for vehicle in [False,True]:
  obs=[o for o in bpy.context.scene.objects if o.type=='MESH' and len(o.data.materials) and o.data.materials[0]==mat and bool(o.get('is_vehicle',False))==vehicle and not o.get('tail_vector',0)]
  if not obs:continue
  bpy.ops.object.select_all(action='DESELECT')
  for o in obs:o.select_set(True)
  bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();obs[0].name=('Kestrel_' if vehicle else 'Foundry_')+mat.name
# UV cube projection in world scale after batching keeps surface grain consistent.
for o in bpy.context.scene.objects:
 if o.type!='MESH': continue
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
 bpy.ops.uv.cube_project(cube_size=2.0,correct_aspect=True)
 bpy.ops.object.mode_set(mode='OBJECT')
 if o.data.materials[0]==M['asphalt']:
  uv=o.data.uv_layers.active.data
  for face in o.data.polygons:
   for li in face.loop_indices:
    world=o.matrix_world @ o.data.vertices[o.data.loops[li].vertex_index].co
    uv[li].uv=((world.x+14)/28,(world.y+11.5)/19)
 if o.data.materials[0]==M['kestrel_carbon']:
  for uv in o.data.uv_layers.active.data:uv.uv*=8
 # Weighted normals preserve broad planar faces and smooth the beveled edges.
 mod=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL');mod.keep_sharp=True;mod.weight=50
 bpy.ops.object.modifier_apply(modifier=mod.name)

# Offline contact occlusion using Blender's BVH ray queries.
# Exported vertex colors add no texture fetch or runtime AO pass.
from mathutils.bvhtree import BVHTree
vertices=[];faces=[]
for obj in bpy.context.scene.objects:
 if obj.type!='MESH':continue
 offset=len(vertices)
 vertices.extend([obj.matrix_world @ v.co for v in obj.data.vertices])
 faces.extend([tuple(offset+i for i in p.vertices) for p in obj.data.polygons])
tree=BVHTree.FromPolygons(vertices,faces,all_triangles=False)
ray_count=12
for obj in bpy.context.scene.objects:
 if obj.type!='MESH':continue
 mesh=obj.data
 colors=mesh.color_attributes.new(name='ContactAO',type='FLOAT_COLOR',domain='CORNER')
 mesh.color_attributes.active_color=colors
 name=obj.data.materials[0].name
 factors=[]
 for v in mesh.vertices:
  if name in ['asphalt','amber','cyan','window_warm','window_cool']:
   factors.append(1.0);continue
  n=(obj.matrix_world.to_3x3() @ v.normal).normalized()
  tangent=n.cross(Vector((0,0,1)))
  if tangent.length<.01:tangent=n.cross(Vector((0,1,0)))
  tangent.normalize();bitangent=n.cross(tangent).normalized()
  origin=(obj.matrix_world @ v.co)+n*.018
  blocked=0.0
  for i in range(ray_count):
   z=(i+.5)/ray_count;angle=i*2.3999632297
   r=math.sqrt(1-z*z)
   direction=(tangent*(math.cos(angle)*r)+bitangent*(math.sin(angle)*r)+n*z).normalized()
   hit,normal,index,distance=tree.ray_cast(origin,direction,1.1)
   if hit is not None:blocked+=1-distance/1.1
  factors.append(max(.62,1-.65*blocked/ray_count))
 for loop in mesh.loops:
  a=factors[loop.vertex_index];colors.data[loop.index].color=(a,a,a,1)
print('SCENEFORGE_CONTACT_AO_BAKED',ray_count)

root=Path.cwd();dest=root/'game/assets';dest.mkdir(parents=True,exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(dest/'neon_foundry.glb'),export_format='GLB',use_selection=False,export_yup=True,export_normals=True,export_texcoords=True,export_vertex_color='ACTIVE',export_all_vertex_colors=False)
# Confirm the exported GLB actually carries the baked shading attribute.
import struct
payload=(dest/'neon_foundry.glb').read_bytes()
json_length=struct.unpack_from('<I',payload,12)[0]
gltf=json.loads(payload[20:20+json_length])
assert all('COLOR_0' in p['attributes'] for m in gltf['meshes'] for p in m['primitives'])
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes)
assert triangles<220000,triangles
assert len(meshes)<=48,len(meshes)
(root/'build').mkdir(exist_ok=True)
(root/'build/asset-report.json').write_text(json.dumps({'asset':'Neon Foundry corner','license':'CC0-1.0','source':'Original Blender script; no external assets','triangles':triangles,'mesh_batches':len(meshes),'blender':bpy.app.version_string},indent=2))
print('SCENEFORGE_ASSET_VALIDATED',triangles,len(meshes))
# Source preview: CPU Cycles requires no GPU.
world=bpy.context.scene.world or bpy.data.worlds.new('Dusk');bpy.context.scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.2,.32,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35
for loc,color,power,size in [((0,1,7),(.5,.7,1),1600,8),((0,5.5,3.4),(1,.5,.2),1000,3),((-4,-3,5),(.1,.65,1),900,4)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.color=color;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,4,1))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(8,-11,6));cam=bpy.context.object;cam.rotation_euler=(Vector((0,4,2))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=32
s=bpy.context.scene;s.camera=cam;s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True;s.render.resolution_x=960;s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.filepath=str(root/'build/NeonFoundry-preview.png');bpy.ops.wm.save_as_mainfile(filepath=str(root/'build/NeonFoundry.blend'));bpy.ops.render.render(write_still=True)
