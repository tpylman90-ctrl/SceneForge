"""Original SceneForge fleet. Author in Godot metres (+Z forward); export via Blender.
Reference images guide silhouette/color only; no third-party mesh or texture bytes.
"""
import bpy, math, json, struct
from pathlib import Path
from mathutils import Vector

ROOT=Path.cwd()
OUT=ROOT/'game/assets/fleet'
OUT.mkdir(parents=True,exist_ok=True)
REPORT=[]
def v(p): return Vector((p[0],-p[2],p[1]))
def mat(name,color,metal=.5,rough=.4,glow=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
 p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if glow:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=glow
 return m
def mesh(name,points,faces,material,bevel=0):
 data=bpy.data.meshes.new(name);data.from_pydata([v(p) for p in points],[],faces);data.update()
 obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj);data.materials.append(material)
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
 if bevel:
  mod=obj.modifiers.new('Edge highlights','BEVEL');mod.width=bevel;mod.segments=2;bpy.ops.object.modifier_apply(modifier=mod.name)
 return obj
def box(name,p,s,m,bevel=.012):
 pts=[(p[0]+x*s[0]/2,p[1]+y*s[1]/2,p[2]+z*s[2]/2) for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
 return mesh(name,pts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)],m,bevel)
def panel(name,pts,m):
 obj=mesh(name,pts,[tuple(range(len(pts)))],m)
 mod=obj.modifiers.new('Panel thickness','SOLIDIFY');mod.thickness=.025
 bpy.context.view_layer.objects.active=obj;bpy.ops.object.modifier_apply(modifier=mod.name)
 return obj
def pipe(name,a,b,r,m,sides=12):
 aa,bb=v(a),v(b);d=bb-aa
 bpy.ops.mesh.primitive_cylinder_add(vertices=sides,radius=r,depth=d.length,location=(aa+bb)/2)
 obj=bpy.context.object;obj.name=name;obj.rotation_euler=d.to_track_quat('Z','Y').to_euler();obj.data.materials.append(m)
 return obj
def ring(name,p,major,minor,m):
 bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=24,minor_segments=6,location=v(p))
 obj=bpy.context.object;obj.name=name;obj.data.materials.append(m);return obj
def rig(name,objects,pivot):
 root=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(root);root.location=v(pivot)
 bpy.context.view_layer.update()
 for obj in objects:
  world=obj.matrix_world.copy();obj.parent=root;obj.matrix_world=world
 return root
def since(before):return [o for o in bpy.context.scene.objects if o.type=='MESH' and o not in before]
def hull(profile,m):
 pts=[]
 for z,w,lo,hi in profile:
  pts.extend([(-w*.7,lo,z),(w*.7,lo,z),(w,lo+.14,z),(w*.86,hi,z),(-w*.86,hi,z),(-w,lo+.14,z)])
 faces=[tuple(reversed(range(6)))]
 for j in range(len(profile)-1):
  for k in range(6):
   # Open top through the cockpit, rather than a seat placed on a solid deck.
   if k==3 and profile[j][0]<1.35 and profile[j+1][0]>-.9:continue
   faces.append((j*6+k,j*6+(k+1)%6,(j+1)*6+(k+1)%6,(j+1)*6+k))
 faces.append(tuple((len(profile)-1)*6+k for k in range(6)))
 mesh('Monocoque',pts,faces,m,.018)

exec((ROOT/'tools/piledriver_detail.py').read_text())

exec((ROOT/'tools/forge_detail.py').read_text())
exec((ROOT/'tools/shrike_smooth.py').read_text())

SPECS=[
 ('forge',(.045,.055,.065),(.65,.32,.07),(1.0,.28,.025),'Graphite precision racer / amber induction core'),
 ('piledriver',(0.20,.035,.40),(.72,.43,.08),(.65,.06,1.0),'Heavy framed racer / purple and brass'),
 ('shrike',(.40,.46,.49),(.83,.22,.055),(.15,.75,1.0),'Feather-fin interceptor / silver and orange'),
 ('mantis',(.18,.27,.12),(.38,.46,.25),(.44,1.0,.42),'Fork-nose utility racer / olive'),
 ('aurora',(.025,.09,.26),(.65,.28,.12),(.12,.48,1.0),'Low swept speedster / midnight blue and copper')]
for ident,color,accent_color,light_color,description in SPECS:
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 body=mat(ident+'_body',color,.65,.36);accent=mat(ident+'_accent',accent_color,.75,.3)
 carbon=mat(ident+'_carbon',(.025,.032,.04),.45,.5);steel=mat(ident+'_alloy',(.22,.28,.31),.8,.3)
 rubber=mat(ident+'_padding',(.02,.025,.03),0,.8);glow=mat(ident+'_glow',light_color,.1,.3,2)
 glass=mat('vehicle_glass_'+ident,(.025,.065,.095),.25,.15)
 if ident=='forge':
  build_forge(body,accent,carbon,steel,rubber,glow,glass)
 elif ident=='piledriver':
  build_piledriver(body,accent,carbon,steel,rubber,glow,glass)
 elif ident=='shrike':
  build_shrike(body,accent,carbon,steel,rubber,glow,glass)
 else:
  if ident=='piledriver':
   profile=[(-2.45,.65,.55,1.05),(-1.6,1.18,.48,1.24),(-.5,1.12,.45,1.24),(1.25,.91,.40,1.15),(2.4,.66,.38,.95),(3.4,.18,.40,.66)]
  elif ident=='shrike':
   profile=[(-2.7,.55,.62,1.12),(-1.5,1.02,.55,1.30),(-.4,1.02,.48,1.27),(1.3,.85,.40,1.16),(2.7,.43,.36,.85),(3.85,.025,.38,.47)]
  elif ident=='mantis':
   profile=[(-2.2,.88,.56,1.05),(-1.2,1.03,.45,1.26),(-.3,.91,.42,1.27),(1.35,.72,.40,1.1),(2.5,.38,.40,.73),(3.1,.12,.42,.56)]
  else:
   profile=[(-2.6,.85,.52,.99),(-1.4,1.15,.42,1.20),(-.3,1.08,.40,1.24),(1.3,.83,.38,1.1),(2.7,.68,.32,.72),(3.7,.025,.34,.42)]
  hull(profile,body)
  # Common ergonomic bay, compatible with the existing live dashboard and camera.
  box('Cockpit floor',(0,.75,.2),(1.28,.10,2.35),carbon)
  box('Seat cushion',(0,.92,-.18),(.57,.16,.65),rubber,.055)
  box('Seat back',(0,1.30,-.61),(.62,.78,.16),carbon,.055)
  box('Back pad',(0,1.32,-.50),(.48,.61,.10),rubber,.045)
  box('Headrest',(0,1.76,-.64),(.39,.25,.18),rubber,.05)
  for side in [-1,1]:
   box('Harness',(side*.17,1.31,-.435),(.055,.52,.025),accent,.005)
   box('Cockpit sill',(side*.71,1.13,.15),(.17,.20,2.0),carbon,.025)
   pipe('Sill trim',(side*.73,1.25,-.8),(side*.73,1.25,1.25),.025,accent)
   rail=[(side*.55,1.18,1.62),(side*.58,1.94,.52),(side*.50,1.97,-.65),(side*.49,1.32,-1.28)]
   for a,b in zip(rail,rail[1:]):pipe('Open cockpit frame',a,b,.045 if ident=='piledriver' else .032,accent if ident in ['piledriver','mantis'] else steel)
   pipe('Frame light',(side*.58,1.955,.49),(side*.53,1.985,-.40),.009,glow,8)
   for z in [-.6,-.1,.4,.9]:
    pipe('Sill fastener',(side*.79,1.19,z),(side*.81,1.19,z),.018,steel,8)
  pipe('Rollover beam',(-.5,1.97,-.65),(.5,1.97,-.65),.04,accent)
  panel('vehicle_glass_windshield',[(-.55,1.18,1.62),(.55,1.18,1.62),(.58,1.82,.70),(-.58,1.82,.70)],glass)
  before=set(bpy.context.scene.objects)
  for side in [-1,1]:
   pipe('Grip',(side*.22,1.18,1.12),(side*.22,1.38,1.10),.035,rubber)
   box('Thumb switch',(side*.22,1.40,1.10),(.065,.04,.07),accent)
  pipe('Yoke bridge',(-.22,1.22,1.12),(.22,1.22,1.12),.032,steel)
  rig('Kestrel_Yoke',since(before),(0,1.25,1.12))
  # Four real pod housings with mechanical collars and luminous undersides.
  for x,y,z in [(1.0,.58,2.10),(-1.0,.58,2.10),(1.12,.76,-.65),(-1.12,.76,-.65)]:
   pipe('Pod strut',(x*.72,y+.15,z),(x,y,z),.075,steel)
   pipe('Repulsor casing',(x,y-.15,z),(x,y+.17,z),.29,carbon,20)
   ring('Pod armored rim',(x,y+.17,z),.28,.045,accent)
   ring('Repulsor field',(x,y-.16,z),.27,.025,glow)
   for angle in range(0,360,90):
    a=math.radians(angle);box('Pod bolt',(x+.23*math.cos(a),y+.2,z+.23*math.sin(a)),(.04,.04,.04),steel,.003)
  # Deliberately different body silhouettes, not only paint variants.
  for side in [-1,1]:
   if ident=='piledriver':
    pipe('Brass side cage',(side*1.1,.72,2.65),(side*1.24,1.42,-1.65),.065,accent)
    box('Forward racing ski',(side*.43,.31,3.0),(.16,.12,1.65),accent,.035)
    pipe('Ski suspension',(side*.43,.36,2.7),(side*.62,.65,2.25),.06,steel)
    panel('Purple shoulder',[(side*.82,1.17,1.2),(side*1.30,1.33,-.95),(side*1.22,.75,-1.5),(side*.98,.72,.75)],body)
    pipe('Rear turbine',(side*.91,1.06,-1.5),(side*.91,1.06,-2.35),.29,carbon,24)
    ring('Turbine collar',(side*.91,1.06,-2.2),.22,.045,accent)
   elif ident=='shrike':
    panel('Blade flank',[(side*.83,1.15,1.25),(side*1.55,1.18,-1.4),(side*.95,.69,-1.9)],accent)
    for fin in range(3):
     panel('Swept feather',[(side*(.74+fin*.17),1.14,-.75-fin*.3),(side*(1.15+fin*.23),1.37,-2.65-fin*.12),(side*.75,1.05,-1.95)],carbon)
    panel('Split beak chine',[(side*.13,.61,3.75),(side*.72,.90,2.05),(side*.47,.60,1.7)],steel)
   elif ident=='mantis':
    box('Utility shoulder',(side*1.15,.97,-.70),(.52,.54,1.35),body,.055)
    box('Fork runner',(side*.43,.47,3.05),(.22,.16,1.35),carbon,.02)
    pipe('Fork tie',(side*.43,.5,2.65),(side*.63,.78,1.9),.07,steel)
    panel('Upright stabilizer',[(side*.73,1.1,-1.4),(side*.82,2.1,-2.25),(side*.43,2.1,-2.0),(side*.45,1.1,-1.15)],accent)
    for vent in range(5):box('Shoulder vent',(side*1.42,1.02,-1.15+vent*.20),(.025,.23,.06),carbon,.003)
   else:
    panel('Low delta wing',[(side*.60,.78,2.75),(side*1.67,.81,-1.15),(side*1.12,.66,-2.5),(side*.75,.76,.4)],body)
    pipe('Wing copper seam',(side*.62,.80,2.68),(side*1.63,.84,-1.1),.018,accent,8)
    for i in range(4):box('Blue running light',(side*(.45+i*.09),.74,2.60-i*.18),(.06,.035,.12),glow,.006)
    panel('Rear foil',[(side*.55,1.1,-1.7),(side*1.2,1.60,-2.5),(side*1.35,1.60,-2.6),(side*.72,1.1,-2.2)],accent)
   # Flank panel gaps, small intake stacks and maintenance fittings.
   for z in [-.7,-.4,-.1,.2]:box('Intake gill',(side*1.0,1.12,z),(.035,.13,.065),carbon,.003)
   for i in range(3):box('Flank armor fastener',(side*1.0,.79,.6-i*.5),(.045,.045,.045),steel,.004)
  # Carbon nose spine and independently vectoring five-nozzle tail.
  panel('Nose carbon inset',[(-.31,1.15,1.36),(.31,1.15,1.36),(.07,.57,3.25),(-.07,.57,3.25)],carbon)
  for i in range(5):
   before=set(bpy.context.scene.objects);x=(i-2)*.42
   pipe('Vector nozzle',(x,1.65,-1.8),(x,1.65,-2.32),.13,carbon,16)
   pipe('Nozzle liner',(x,1.65,-2.28),(x,1.65,-2.35),.095,glow,16)
   panel('Tail feather',[(x-.14,1.68,-1.8),(x+.14,1.68,-1.8),(x+.18,1.75,-2.6),(x-.18,1.75,-2.6)],accent)
   rig('Kestrel_Tail_%d'%i,since(before),(x,1.65,-1.8))
 if ident=='shrike':
  detail_shrike(body,accent,carbon,steel,rubber,glow,glass)
 # Join static parts per material; preserve control/nozzle transforms.
 for material in [body,accent,carbon,steel,rubber,glow,glass]:
  objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.parent is None and o.data.materials[0]==material]
  if not objects:continue
  bpy.ops.object.select_all(action='DESELECT')
  for o in objects:o.select_set(True)
  bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();objects[0].name='Kestrel_'+material.name
 # UVs and explicit vertex-color contract, with subtle underside shading.
 for obj in bpy.context.scene.objects:
  if obj.type!='MESH':continue
  bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
  bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.cube_project();bpy.ops.object.mode_set(mode='OBJECT')
  colors=obj.data.color_attributes.new(name='ContactAO',type='FLOAT_COLOR',domain='CORNER');obj.data.color_attributes.active_color=colors
  for loop in obj.data.loops:
   normal=obj.matrix_world.to_3x3()@obj.data.vertices[loop.vertex_index].normal
   a=.82+.18*max(0,normal.z);colors.data[loop.index].color=(a,a,a,1)
  mod=obj.modifiers.new('Weighted manufactured normals','WEIGHTED_NORMAL');mod.keep_sharp=True;bpy.ops.object.modifier_apply(modifier=mod.name)
 # Guard against publishing a stale pointed Shrike mesh in the Android package.
 if ident=='shrike':
  front=[o.matrix_world@vertex.co for o in bpy.context.scene.objects if o.type=='MESH' and o.name=='Kestrel_shrike_body' for vertex in o.data.vertices]
  assert front and any(p.y < -3.35 and abs(p.x) > .60 for p in front), 'Shrike rounded wide-nose geometry missing'
  print('SCENEFORGE_SHRIKE_ROUNDED_NOSE_OK')
 path=OUT/(ident+'.glb')
 bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',export_yup=True,export_vertex_color='ACTIVE',export_all_vertex_colors=False)
 data=path.read_bytes();n=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+n])
 names={n.get('name') for n in g['nodes']}
 assert {'Kestrel_Yoke',*['Kestrel_Tail_%d'%i for i in range(5)]}.issubset(names)
 triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in bpy.context.scene.objects if o.type=='MESH')
 assert triangles<40000,triangles
 assert all('COLOR_0' in p['attributes'] for m in g['meshes'] for p in m['primitives'])
 REPORT.append({'id':ident,'description':description,'triangles':triangles,'bytes':len(data),'license':'CC0-1.0','source':'Original procedural Blender geometry; user-supplied visual reference, no imported art'})
 print('SCENEFORGE_FLEET_ASSET_OK',ident,triangles)
(ROOT/'build/fleet-report.json').write_text(json.dumps(REPORT,indent=2))
