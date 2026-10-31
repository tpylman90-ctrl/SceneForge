"""FORGE sparse master surfaces; metres, Godot +Z forward.
Mirror -> Catmull-Clark -> inward thickness. Shared hull/canopy boundary.
"""
FORGE_STATIONS=[(-2.70,.76,.65,1.20,1.20),(-2.62,.88,.60,1.28,1.28),(-2.10,1.08,.48,1.39,1.39),(-1.35,1.04,.40,1.40,1.40),(-1.10,.98,.36,1.35,1.76),(-.70,.92,.33,1.29,1.94),(-.15,.87,.30,1.23,1.96),(.45,.82,.28,1.16,1.80),(1.05,.76,.26,1.05,1.48),(1.50,.66,.25,.91,.91),(1.90,.56,.25,.79,.79),(2.40,.39,.26,.61,.61),(2.85,.20,.27,.44,.44),(3.12,.08,.28,.35,.35),(3.18,.06,.29,.33,.33)]

def forge_surface(name,points,faces,material,mirror=True,thickness=.025):
 obj=mesh(name,points,faces,material)
 assert all(len(p.vertices)==4 for p in obj.data.polygons),name
 if mirror:
  mod=obj.modifiers.new('Welded symmetry','MIRROR');mod.use_clip=True;mod.merge_threshold=.0001
 mod=obj.modifiers.new('Fair control cage','SUBSURF');mod.levels=2;mod.render_levels=2
 mod=obj.modifiers.new('Inward skin','SOLIDIFY');mod.thickness=thickness;mod.offset=-1
 bpy.context.view_layer.objects.active=obj
 for mod in list(obj.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
 for p in obj.data.polygons:p.use_smooth=True
 assert all(math.isfinite(c) for vert in obj.data.vertices for c in vert.co),name
 return obj

def build_forge(body,accent,carbon,steel,rubber,glow,glass):
 pts=[];faces=[]
 for z,w,lo,hi,crown in FORGE_STATIONS:
  pts.extend([(0,lo,z),(.68*w,lo,z),(.94*w,lo+.07,z),(w,lo+(hi-lo)*.42,z),(.94*w,hi-.09,z),(.72*w,hi-.015,z),(.62*w,hi,z),(0,hi+.025,z)])
 for r in range(len(FORGE_STATIONS)-1):
  for c in range(7):
   if 3<=r<9 and c==6:continue
   a=r*8+c;faces.append((a,a+1,a+9,a+8))
 for off in [0,(len(FORGE_STATIONS)-1)*8]:
  for cap in [(0,1,6,7),(1,2,5,6),(2,3,4,5)]:faces.append(tuple(off+i for i in cap))
 hull_master=forge_surface('Forge_Master_Monocoque',pts,faces,body,thickness=.035)
 # Glass uses the hull's aperture stations and sill coordinates.
 pts=[];faces=[]
 for z,w,lo,hi,crown in FORGE_STATIONS[3:10]:
  for u in [0,.25,.50,.75,.93,1]:pts.append((.62*w*u,hi+.012+(crown-hi)*max(0,math.cos(u*math.pi/2))**.48,z))
 for r in range(6):
  for c in range(5):
   a=r*6+c;faces.append((a,a+6,a+7,a+1))
 canopy=forge_surface('vehicle_glass_forge_master',pts,faces,glass,thickness=.018)
 # A narrow rollover bow articulates roof and rear glass; sills track the master.
 z,w,lo,hi,crown=FORGE_STATIONS[5]
 for side in [-1,1]:
  path=[]
  for i in range(13):
   u=i/12;x=side*.62*w*u
   hit,loc,normal,index=canopy.ray_cast(Vector((x,-z,4)),Vector((0,0,-1)))
   if hit:path.append((x,loc.z+.009,z))
  for a,b in zip(path,path[1:]):pipe('Flush canopy rollover bow',a,b,.022,accent,8)
  sill=[(side*.62*w,hi+.012,z) for z,w,lo,hi,crown in FORGE_STATIONS[3:10]]
  for a,b in zip(sill,sill[1:]):pipe('Canopy lower seal',a,b,.018,carbon,8)
 for side in [-1,1]:
  # Integrated triangular front fender, traced from the user's green outline.
  # Broad aft chord, pointed leading tip and a relieved inner trailing edge.
  outline=[(side*.78,.34,3.48),(side*1.65,.76,1.35),
           (side*1.22,.91,.85),(side*.84,.78,1.45),(side*1.02,.58,2.18)]
  ridge=(side*1.19,.88,1.58)
  verts=outline+[ridge]+[(x,y-.10,z) for x,y,z in outline]
  facets=[(i,(i+1)%5,5) for i in range(5)]
  facets.append((10,9,8,7,6))
  for i in range(5):facets.append((i,(i+1)%5,(i+1)%5+6,i+6))
  fender=mesh('Forge_Triangular_Front_Fender',verts,facets,body,.008)
  assert abs(outline[1][0])-abs(outline[3][0])>.7
  # Broad sculpted root: follow the actual evaluated hull at the inboard edge
  # and ease down into the triangular fender. It also overlaps the aft shoulder.
  root_rows=[(.42,.60,1.02,.98),(.52,.59,1.13,.98),(.75,.57,1.25,.95),
             (1.05,.53,1.40,.88),(1.35,.47,1.47,.82),
             (1.65,.41,1.30,.75),(1.90,.35,1.15,.66),(2.10,.29,1.07,.60),
             (2.20,.27,1.03,.56)]
  points=[];faces=[];width_steps=9
  for z,inner,outer,edge_y in root_rows:
   hit,loc,normal,index=hull_master.ray_cast(Vector((side*inner,-z,4)),Vector((0,0,-1)))
   assert hit,'Fender root must reach the hull'
   hull_y=loc.z-.012
   for i in range(width_steps):
    t=i/(width_steps-1);ease=t*t*(3-2*t)
    x=side*(inner+(outer-inner)*t)
    y=hull_y+(edge_y-hull_y)*ease
    points.append((x,y,z))
  for r in range(len(root_rows)-1):
   for c in range(width_steps-1):
    a=r*width_steps+c;faces.append((a,a+1,a+width_steps+1,a+width_steps))
  root=mesh('Continuous fender to hull fillet',points,faces,body)
  mod=root.modifiers.new('Structural fender root thickness','SOLIDIFY');mod.thickness=.10;mod.offset=-1
  bpy.context.view_layer.objects.active=root;bpy.ops.object.modifier_apply(modifier=mod.name)
  for face in root.data.polygons:face.use_smooth=True
  # Swept rear nacelle: pointed forward shoulder, broad aft housing and
  # relieved trailing corners, following the orange plan-view outline.
  outline=[(side*.65,1.25,-.55),(side*1.43,.96,-.20),
           (side*1.95,1.00,-2.95),(side*1.62,1.05,-2.73),
           (side*1.55,1.13,-3.10),(side*.64,1.26,-2.65)]
  ridge=(side*1.22,1.40,-1.85)
  underside=[(side*.65,.90,-.55),(side*1.32,.74,-.20),(side*1.76,.72,-2.95),(side*1.48,.75,-2.73),(side*1.43,.81,-3.10),(side*.64,.94,-2.65)]
  verts=outline+[ridge]+underside
  facets=[(i,(i+1)%6,6) for i in range(6)]
  facets.append(tuple(reversed(range(7,13))))
  for i in range(6):facets.append((i,(i+1)%6,(i+1)%6+7,i+7))
  mesh('Forge_Integrated_Rear_Nacelle',verts,facets,body,.025)
  # Sculpted oval nacelles: stepped armour lip, recessed field and radial vanes.
  for z,y in [(1.8,.43),(-1.95,.61)]:
   x=side*(1.16 if z>0 else 1.40)
   points=[];faces=[];n=32
   for radius,height in [(.24,.12),(.32,.08),(.35,-.01),(.35,-.13),(.30,-.17),(.25,-.14),(.24,-.06)]:
    for i in range(n):
     t=math.tau*i/n;points.append((x+radius*math.cos(t),y+height,z+radius*1.75*math.sin(t)))
   for r in range(6):
    for i in range(n):
     a=r*n+i;b=r*n+(i+1)%n;faces.append((a,b,b+n,a+n))
   casing=mesh('Oval armoured repulsor duct',points,faces,steel)
   for f in casing.data.polygons:f.use_smooth=True
   # The dark recess remains above the luminous underside, never a solid puck.
   core=pipe('Recessed field core',(x,y-.05,z),(x,y-.08,z),.23,carbon,32);core.scale.y=1.75
   for i in range(12):
    t=math.tau*i/12
    pipe('Repulsor radial stator',(x+.10*math.cos(t),y-.11,z+.175*math.sin(t)),(x+.265*math.cos(t+.15),y-.13,z+.464*math.sin(t+.15)),.012,carbon,6)
   pts=[];fs=[]
   for radius,height in [(.307,-.151),(.327,-.151)]:
    for i in range(n):
     t=math.tau*i/n;pts.append((x+radius*math.cos(t),y+height,z+radius*1.75*math.sin(t)))
   for i in range(n):fs.append((i,(i+1)%n,(i+1)%n+n,i+n))
   mesh('Inset oval field emitter',pts,fs,glow)
   for dz in ([-.21,.21] if z<0 else []):
    pipe('Pod recessed suspension',(side*.70,y+.21,z+dz),(x,y+.05,z+dz),.045,carbon,12)
  # Recessed annular exhaust liner is open at the rear, inside the nacelle.
  points=[];faces=[];n=32
  for z,r in [(-2.53,.23),(-3.08,.30),(-3.13,.30),(-3.13,.265),(-2.56,.20)]:
   for i in range(n):
    t=math.tau*i/n;points.append((side*1.20+r*math.cos(t),.98+r*math.sin(t),z))
  for row in range(4):
   for i in range(n):
    a=row*n+i;b=row*n+(i+1)%n;faces.append((a,b,b+n,a+n))
  liner=mesh('Nacelle recessed exhaust liner',points,faces,steel)
  for f in liner.data.polygons:f.use_smooth=True
  pipe('Exhaust dark throat',(side*1.20,.98,-2.54),(side*1.20,.98,-2.56),.20,carbon,32)
  pipe('Exhaust inset field',(side*1.20,.98,-2.57),(side*1.20,.98,-2.59),.15,glow,32)
 # Tapered aft spine follows the red outline behind the cockpit.
 spine=[(-.52,1.38,-1.12),(.52,1.38,-1.12),(.17,1.19,-3.12),(-.17,1.19,-3.12)]
 vertices=spine+[(x,y-.24,z) for x,y,z in spine]
 mesh('Forge_Aft_Spine',vertices,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],body,.012)
 pipe('Central drive housing',(0,1.05,-2.18),(0,1.05,-2.90),.24,carbon,32)
 box('Cockpit floor',(0,.70,.1),(.94,.08,2.20),carbon,.025)
 box('Bucket cushion',(0,.91,-.30),(.50,.16,.68),rubber,.05)
 box('Seat back',(0,1.34,-.74),(.52,.78,.16),rubber,.05)
 box('Head restraint',(0,1.79,-.78),(.33,.20,.16),rubber,.04)
 before=set(bpy.context.scene.objects)
 pipe('Yoke bridge',(-.22,1.23,1.08),(.22,1.23,1.08),.03,steel)
 for s in [-1,1]:pipe('Yoke grip',(s*.22,1.18,1.08),(s*.23,1.38,1.05),.035,rubber)
 for obj in since(before):obj.location += v((0,0,-.28))
 rig('Kestrel_Yoke',since(before),(0,1.25,1.08))
 for i in range(5):
  before=set(bpy.context.scene.objects);x=(i-2)*.18
  box('Rear vector vane',(x,1.15,-2.70),(.15,.045,.38),body,.012)
  rig('Kestrel_Tail_%d'%i,since(before),(x,1.15,-2.51))
 # Weld the overlapping structural volumes; no hidden disconnected root panels.
 for prefix in ['Continuous fender to hull fillet','Forge_Triangular_Front_Fender','Forge_Integrated_Rear_Nacelle','Forge_Aft_Spine']:
  for part in [o for o in list(bpy.context.scene.objects) if o.name.startswith(prefix)]:
   bpy.context.view_layer.objects.active=hull_master
   mod=hull_master.modifiers.new('Union sculpted fender root','BOOLEAN')
   mod.operation='UNION';mod.solver='EXACT';mod.object=part
   bpy.ops.object.modifier_apply(modifier=mod.name)
   bpy.data.objects.remove(part,do_unlink=True)
 # Bore real exhaust openings after the body volumes have been joined.
 for side in [-1,1]:
  cutter=pipe('Temporary exhaust bore',(side*1.20,.98,-2.52),(side*1.20,.98,-3.5),.31,steel,48)
  bpy.context.view_layer.objects.active=hull_master
  mod=hull_master.modifiers.new('Recessed nacelle exhaust aperture','BOOLEAN')
  mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
  bpy.ops.object.modifier_apply(modifier=mod.name)
  bpy.data.objects.remove(cutter,do_unlink=True)
 # Both tips must belong to the same connected mesh component as the hull.
 adjacency=[[] for vertex in hull_master.data.vertices]
 for edge in hull_master.data.edges:
  a,b=edge.vertices;adjacency[a].append(b);adjacency[b].append(a)
 seen={0};pending=[0]
 while pending:
  for index in adjacency[pending.pop()]:
   if index not in seen:seen.add(index);pending.append(index)
 for side in [-1,1]:
  assert any(side*hull_master.data.vertices[i].co.x>.70 and hull_master.data.vertices[i].co.y < -3.35 for i in seen),'Disconnected front fender tip'
  assert any(side*hull_master.data.vertices[i].co.x>1.80 and hull_master.data.vertices[i].co.y>2.65 for i in seen),'Disconnected rear nacelle'
 print('SCENEFORGE_FORGE_CONNECTED_NACELLES_OK')
 print('SCENEFORGE_FORGE_CONNECTED_FENDERS_OK')
 print('SCENEFORGE_FORGE_MASTER_SURFACES_OK')
