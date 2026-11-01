"""FORGE sparse master surfaces; metres, Godot +Z forward.
Mirror -> Catmull-Clark -> inward thickness. Shared hull/canopy boundary.
"""
FORGE_STATIONS=[(-2.70,.76,.65,1.20,1.20),(-2.62,.88,.60,1.28,1.28),(-2.10,1.08,.48,1.39,1.39),(-1.35,1.04,.40,1.40,1.40),(-1.10,.98,.36,1.35,1.76),(-.70,.92,.33,1.29,1.94),(-.15,.87,.30,1.23,1.96),(.45,.82,.28,1.16,1.80),(1.05,.76,.26,1.05,1.48),(1.50,.66,.25,.91,.91),(1.90,.56,.25,.79,.79),(2.40,.39,.26,.61,.61),(2.85,.20,.27,.44,.44),(3.12,.08,.28,.35,.35),(3.18,.06,.29,.33,.33)]

def forge_surface(name,points,faces,material,mirror=True,thickness=.025,subdivisions=2):
 obj=mesh(name,points,faces,material)
 assert all(len(p.vertices)==4 for p in obj.data.polygons),name
 if mirror:
  mod=obj.modifiers.new('Welded symmetry','MIRROR');mod.use_clip=True;mod.merge_threshold=.0001
 mod=obj.modifiers.new('Fair control cage','SUBSURF');mod.levels=subdivisions;mod.render_levels=subdivisions
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
  outline=[(side*.78,.36,3.48),(side*1.65,.98,1.35),
           (side*1.22,1.07,.85),(side*.84,.98,1.45),(side*1.02,.76,2.18)]
  ridge=(side*1.19,1.13,1.58)
  underside=[(side*.78,.26,3.48),(side*1.52,.31,1.35),
             (side*1.16,.34,.85),(side*.80,.30,1.45),(side*.97,.28,2.18)]
  verts=outline+[ridge]+underside
  facets=[(i,(i+1)%5,5) for i in range(5)]
  facets.append((10,9,8,7,6))
  for i in range(5):facets.append((i,(i+1)%5,(i+1)%5+6,i+6))
  fender=mesh('Forge_Triangular_Front_Fender',verts,facets,body,.025)
  assert abs(outline[1][0])-abs(outline[3][0])>.7
  # Broad sculpted root: follow the actual evaluated hull at the inboard edge
  # and ease down into the triangular fender. It also overlaps the aft shoulder.
  root_rows=[(.42,.60,1.02,1.08),(.52,.59,1.13,1.10),(.75,.57,1.25,1.10),
             (1.05,.53,1.40,1.08),(1.35,.47,1.47,1.05),
             (1.65,.41,1.30,.97),(1.90,.35,1.15,.86),(2.10,.29,1.07,.80),
             (2.20,.27,1.03,.75)]
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
  # Full-depth underside follows the belly, joining upper and lower hull.
  top_count=len(points)
  for z,inner,outer,edge_y in root_rows:
   hit,loc,normal,index=hull_master.ray_cast(Vector((side*inner,-z,-1)),Vector((0,0,1)))
   assert hit,'Fender underside must reach the belly'
   belly_y=loc.z+.012
   for i in range(width_steps):
    t=i/(width_steps-1);ease=t*t*(3-2*t)
    x=side*(inner+(outer-inner)*t)
    points.append((x,belly_y+(.30-belly_y)*ease,z))
  faces += [tuple(top_count+i for i in reversed(face)) for face in list(faces)]
  for r in range(len(root_rows)-1):
   for c in [0,width_steps-1]:
    a=r*width_steps+c;b=a+width_steps
    faces.append((a,b,b+top_count,a+top_count))
  for r in [0,len(root_rows)-1]:
   for c in range(width_steps-1):
    a=r*width_steps+c;faces.append((a,a+1,a+1+top_count,a+top_count))
  root=mesh('Continuous fender to hull fillet',points,faces,body)
  for face in root.data.polygons:face.use_smooth=True
  # Swept rear nacelle: pointed forward shoulder, broad aft housing and
  # relieved trailing corners, following the orange plan-view outline.
  outline=[(side*.65,1.25,-.55),(side*1.43,.96,-.20),
           (side*1.95,1.00,-2.95),(side*1.62,1.05,-2.73),
           (side*1.55,1.13,-3.10),(side*.64,1.26,-2.65)]
  ridge=(side*1.22,1.40,-1.85)
  underside=[(side*.65,.43,-.55),(side*1.32,.32,-.20),(side*1.80,.34,-2.95),(side*1.52,.35,-2.73),(side*1.46,.38,-3.10),(side*.64,.50,-2.65)]
  verts=outline+[ridge]+underside
  facets=[(i,(i+1)%6,6) for i in range(6)]
  facets.append(tuple(reversed(range(7,13))))
  for i in range(6):facets.append((i,(i+1)%6,(i+1)%6+7,i+7))
  rear_nacelle=mesh('Forge_Integrated_Rear_Nacelle',verts,facets,body,.025)
  # Full-depth rear root follows both skins of the original hull, blending
  # the nacelle into the deck and belly rather than supporting it as a wing.
  rear_rows=[(-.35,.55,1.12,1.03,.41),(-.55,.55,1.27,1.17,.42),
             (-.90,.56,1.45,1.28,.43),(-1.35,.57,1.60,1.34,.44),
             (-1.85,.59,1.67,1.34,.45),(-2.25,.59,1.65,1.30,.47),
             (-2.55,.57,1.55,1.25,.49),(-2.66,.55,1.38,1.23,.50)]
  points=[];faces=[];cols=9;rows_count=len(rear_rows)
  for layer in [0,1]:
   for z,inner,outer,top_edge,bottom_edge in rear_rows:
    origin=Vector((side*inner,-z,4 if layer==0 else -1))
    hit,loc,normal,index=hull_master.ray_cast(origin,Vector((0,0,-1 if layer==0 else 1)))
    assert hit,'Rear nacelle root must reach the hull'
    start=loc.z+(-.012 if layer==0 else .012)
    edge_hit,edge_loc,edge_normal,edge_index=rear_nacelle.ray_cast(Vector((side*outer,-z,4 if layer==0 else -1)),Vector((0,0,-1 if layer==0 else 1)))
    target=(edge_loc.z+(-.012 if layer==0 else .012)) if edge_hit else (top_edge if layer==0 else bottom_edge)
    for i in range(cols):
     t=i/(cols-1);ease=t*t*(3-2*t)
     points.append((side*(inner+(outer-inner)*t),start+(target-start)*ease,z))
  offset=cols*rows_count
  for r in range(rows_count-1):
   for c in range(cols-1):
    a=r*cols+c;face=(a,a+1,a+cols+1,a+cols)
    faces.append(face);faces.append(tuple(offset+i for i in reversed(face)))
   for c in [0,cols-1]:
    a=r*cols+c;b=a+cols;faces.append((a,b,b+offset,a+offset))
  for r in [0,rows_count-1]:
   for c in range(cols-1):
    a=r*cols+c;faces.append((a,a+1,a+1+offset,a+offset))
  rear_root=mesh('Forge_Continuous_Rear_Root',points,faces,body)
  for face in rear_root.data.polygons:face.use_smooth=True
 # The repulsor hardware is internal and has no external pod geometry.
 # A single molded fastback fairing grows from the greenhouse and tapers aft.
 sections=[(-.78,.55,1.90,1.48,1.12),(-.83,.56,1.90,1.48,1.12),
           (-1.10,.63,1.88,1.47,1.10),(-1.42,.58,1.79,1.44,1.09),
           (-1.85,.49,1.65,1.39,1.08),(-2.28,.38,1.51,1.32,1.05),
           (-2.72,.32,1.38,1.24,1.02),(-3.08,.32,1.28,1.16,.99),
           (-3.16,.32,1.25,1.14,.98)]
 us=[0,.20,.40,.60,.80,.95,1];cols=len(us);rows=len(sections)
 points=[];faces=[]
 for layer in [0,1]:
  for row,(z,width,crown,shoulder,belly) in enumerate(sections):
   for u in us:
    x=width*u
    y=belly if layer else shoulder+(crown-shoulder)*max(0,math.cos(u*math.pi/2))**.65
    if layer==0 and row<2:
     hit,loc,normal,index=canopy.ray_cast(Vector((x,-z,4)),Vector((0,0,-1)))
     assert hit,'Central fairing must fit the rear greenhouse'
     y=loc.z+.014
    points.append((x,y,z))
 offset=rows*cols
 for row in range(rows-1):
  for c in range(cols-1):
   a=row*cols+c;face=(a,a+1,a+cols+1,a+cols)
   faces.append(face);faces.append(tuple(offset+i for i in reversed(face)))
  a=row*cols+cols-1;b=a+cols;faces.append((a,b,b+offset,a+offset))
 for row in [0,rows-1]:
  for c in range(cols-1):
   a=row*cols+c;faces.append((a,a+1,a+1+offset,a+offset))
 central=forge_surface('Forge_Central_Fastback_Flare',points,faces,body,thickness=.018,subdivisions=1)
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
 # Layered rear flare accents grow out of the nacelle shoulders, with
 # broad buried roots and tapered tips framing the three exhaust positions.
 def rear_accent(name,outline,ridge,side):
  count=len(outline)
  lower=[(x-side*.025,1.18 if name=='Canopy_Shoulder' else y-.10,z+.015) for x,y,z in outline]
  lower_ridge=(ridge[0]-side*.025,1.18 if name=='Canopy_Shoulder' else ridge[1]-.10,ridge[2]+.015)
  points=outline+[ridge]+lower+[lower_ridge]
  faces=[(i,(i+1)%count,count) for i in range(count)]
  for i in range(count):faces.append((i+count+1,2*count+1,(i+1)%count+count+1))
  for i in range(count):faces.append((i,(i+1)%count,(i+1)%count+count+1,i+count+1))
  return mesh('Forge_Rear_Accent_'+name,points,faces,body,.014)
 for side in [-1,1]:
  rear_accent('Upper_Swept_Flare',[(side*1.14,1.19,-1.42),(side*1.59,1.30,-1.80),
               (side*2.12,1.68,-3.13),(side*1.40,1.29,-2.85)],(side*1.56,1.48,-2.30),side)
  rear_accent('Inner_Raised_Fin',[(side*.50,1.19,-1.50),(side*.78,1.28,-1.70),
               (side*.94,1.97,-2.95),(side*.62,1.27,-2.65)],(side*.70,1.49,-2.16),side)
  rear_accent('Lower_Exhaust_Chine',[(side*1.47,.52,-1.84),(side*1.83,.49,-2.28),
               (side*2.02,.36,-3.15),(side*1.53,.40,-2.90)],(side*1.76,.53,-2.62),side)
  # Rear canopy buttress: fitted to the actual glass crown and flared out
  # into the nacelle shoulders rather than sitting as a separate roof wing.
  inner=[]
  for x,z in [(side*.28,-.88),(side*.43,-.80)]:
   hit,loc,normal,index=canopy.ray_cast(Vector((x,-z,4)),Vector((0,0,-1)))
   assert hit,'Canopy shoulder must meet the glass'
   inner.append((x,loc.z+.012,z))
  rear_accent('Canopy_Shoulder',inner+[(side*.85,1.61,-1.10),
              (side*1.25,1.39,-1.75),(side*.78,1.28,-2.05),
              (side*.30,1.33,-1.28)],(side*.62,1.74,-1.15),side)
  path=[inner[1],(side*.65,1.74,-1.16),(side*1.18,1.43,-1.66)]
  for a,b in zip(path,path[1:]):pipe('Canopy shoulder flush trim',a,b,.013,accent,8)
  # Fine metal leading edges and restrained light channels articulate the new fins.
  pipe('Raised fin alloy leading edge',(side*.78,1.30,-1.74),(side*.94,1.97,-2.95),.018,accent,8)
  pipe('Rear flare light channel',(side*1.62,1.36,-1.98),(side*2.05,1.64,-3.02),.013,glow,8)
 # Continuous crown collar closes the gap between the paired buttresses.
 points=[];faces=[];cols=13
 for z in [-.91,-1.02,-1.16,-1.30]:
  for i in range(cols):
   x=-.39+.78*i/(cols-1)
   hit,loc,normal,index=canopy.ray_cast(Vector((x,-z,4)),Vector((0,0,-1)))
   assert hit,'Rear crown collar must sit on the canopy'
   points.append((x,loc.z+.014,z))
 for row in range(3):
  for i in range(cols-1):
   a=row*cols+i;faces.append((a,a+1,a+cols+1,a+cols))
 collar=mesh('Rear canopy crown collar',points,faces,body)
 mod=collar.modifiers.new('Crown collar thickness','SOLIDIFY');mod.thickness=.045;mod.offset=-1
 bpy.context.view_layer.objects.active=collar;bpy.ops.object.modifier_apply(modifier=mod.name)
 for face in collar.data.polygons:face.use_smooth=True
 # Weld the overlapping structural volumes; no hidden disconnected root panels.
 for prefix in ['Continuous fender to hull fillet','Forge_Triangular_Front_Fender','Forge_Continuous_Rear_Root','Forge_Integrated_Rear_Nacelle','Forge_Central_Fastback_Flare','Forge_Rear_Accent_']:
  for part in [o for o in list(bpy.context.scene.objects) if o.name.startswith(prefix)]:
   bpy.context.view_layer.objects.active=hull_master
   mod=hull_master.modifiers.new('Union sculpted fender root','BOOLEAN')
   mod.operation='UNION';mod.solver='EXACT';mod.object=part
   bpy.ops.object.modifier_apply(modifier=mod.name)
   bpy.data.objects.remove(part,do_unlink=True)
 # Bore real exhaust openings after the body volumes have been joined.
 for x,y,radius in [(-1.20,.98,.31),(0,1.00,.34),(1.20,.98,.31)]:
  cutter=pipe('Temporary exhaust bore',(x,y,-2.52),(x,y,-3.5),radius,steel,48)
  bpy.context.view_layer.objects.active=hull_master
  mod=hull_master.modifiers.new('Recessed nacelle exhaust aperture','BOOLEAN')
  mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
  bpy.ops.object.modifier_apply(modifier=mod.name)
  bpy.data.objects.remove(cutter,do_unlink=True)
 # Three rear-facing vector boosters sit inside the tail, with a larger
 # center throat and recessed alloy liners rather than exposed nacelle pods.
 for x,y,radius in [(-1.20,.98,.31),(0,1.00,.34),(1.20,.98,.31)]:
  points=[];faces=[];n=32
  for z,r in [(-2.53,radius*.74),(-3.08,radius),(-3.13,radius),(-3.13,radius*.88),(-2.56,radius*.66)]:
   for i in range(n):
    t=math.tau*i/n;points.append((x+r*math.cos(t),y+r*math.sin(t),z))
  for row in range(4):
   for i in range(n):
    a=row*n+i;b=row*n+(i+1)%n;faces.append((a,b,b+n,a+n))
  liner=mesh('Recessed triple-booster alloy liner',points,faces,steel)
  for f in liner.data.polygons:f.use_smooth=True
  pipe('Triple-booster dark throat',(x,y,-2.54),(x,y,-2.56),radius*.66,carbon,32)
  pipe('Triple-booster inset field',(x,y,-2.57),(x,y,-2.59),radius*.49,glow,32)
  for ring_z in [-2.95,-3.10]:
   for i in range(16):
    a=i*math.tau/16;b=a+math.tau/16*.72
    p=(x+radius*.91*math.cos(a),y+radius*.91*math.sin(a),ring_z)
    q=(x+radius*.91*math.cos(b),y+radius*.91*math.sin(b),ring_z)
    pipe('Triple-booster segmented retaining rim',p,q,.014,accent,6)
  for i in range(8):
   a=i*math.tau/8
   pipe('Triple-booster radial stator',(x+radius*.48*math.cos(a),y+radius*.48*math.sin(a),-2.72),
        (x+radius*.78*math.cos(a+.16),y+radius*.78*math.sin(a+.16),-2.98),.010,carbon,6)
 # First finish pass. All upper trim is projected onto the evaluated body.
 def surface_point(x,z,lift=.008):
  hit,loc,normal,index=hull_master.ray_cast(Vector((x,-z,4)),Vector((0,0,-1)))
  assert hit,('Finish panel must stay on the body',x,z)
  return (x,loc.z+lift,z)
 def fitted_ribbon(name,stations,material):
  # Finish the existing body faces directly: no overlapping armor sheets.
  if material.name not in hull_master.data.materials:hull_master.data.materials.append(material)
  slot=hull_master.data.materials.find(material.name)
  for face in hull_master.data.polygons:
   if face.normal.z<.25:continue
   centre=sum((hull_master.data.vertices[i].co for i in face.vertices),Vector())/len(face.vertices)
   x=centre.x;z=-centre.y
   for a,b in zip(stations,stations[1:]):
    if min(a[0],b[0])<=z<=max(a[0],b[0]):
     t=(z-a[0])/(b[0]-a[0]);inner=a[1]+(b[1]-a[1])*t;outer=a[2]+(b[2]-a[2])*t
     if min(inner,outer)<=x<=max(inner,outer):face.material_index=slot
     break
 # Automotive clearcoat and satin carbon separate broad surfaces in inspection.
 shader=body.node_tree.nodes.get('Principled BSDF')
 shader.inputs['Coat Weight'].default_value=.40
 shader.inputs['Coat Roughness'].default_value=.23
 glass.node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value=.65
 glass.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.16
 for side in [-1,1]:
  front=[]
  for i in range(13):
   t=i/12;front.append((1.18+1.60*t,side*(1.08-.12*t),side*(1.46-.42*t)))
  fitted_ribbon('Inset front carbon armor',front,carbon)
  rear=[]
  for i in range(13):
   t=i/12;rear.append((-.85-1.48*t,side*(1.04+.16*t),side*(1.51+.23*t)))
  fitted_ribbon('Inset nacelle carbon armor',rear,carbon)
  for name,stations in [('Front running light',front),('Rear shoulder energy channel',rear)]:
   path=[surface_point(outer,z,.018) for z,inner,outer in stations]
   for a,b in zip(path,path[1:]):pipe(name,a,b,.012,glow,8)
   # Opposite edge is a fine metal panel border rather than another neon stripe.
   path=[surface_point(inner,z,.016) for z,inner,outer in stations]
   for a,b in zip(path,path[1:]):pipe('Flush armor edge',a,b,.009,accent,6)
  # Side intake pockets are cut into the thick body; grille sits inside the recess.
  for z,y,length in [(-1.28,.77,.64),(1.25,.62,.36)]:
   hit,loc,normal,index=hull_master.ray_cast(Vector((side*3,-z,y)),Vector((-side,0,0)))
   assert hit,'Intake pocket must intersect a body flank'
   face_x=loc.x
   cutter=box('Temporary intake recess',(face_x-side*.065,y,z),(.24,.22,length),steel,.025)
   bpy.context.view_layer.objects.active=hull_master
   mod=hull_master.modifiers.new('Machined flank intake','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
   bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
   box('Intake recessed backing',(face_x-side*.172,y,z),(.016,.19,length-.035),carbon,.008)
   for i in range(5):
    zz=z-length*.36+i*length*.18
    pipe('Intake angled louvre',(face_x-side*.10,y-.074,zz-.025),(face_x-side*.07,y+.074,zz+.025),.014,steel,8)
  # Paired recessed utility-port clusters add depth to the rear shoulders.
  for z,y in [(-1.78,1.02),(-2.30,.93)]:
   hit,loc,normal,index=hull_master.ray_cast(Vector((side*3,-z,y)),Vector((-side,0,0)))
   assert hit,'Rear service port must sit on the body flank'
   face_x=loc.x
   cutter=box('Temporary rear service-port pocket',(face_x-side*.055,y,z),(.25,.23,.42),steel,.065)
   bpy.context.view_layer.objects.active=hull_master
   mod=hull_master.modifiers.new('Recessed rear service-port pocket','BOOLEAN')
   mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
   bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
   box('Inset service-port panel',(face_x-side*.17,y,z),(.018,.19,.36),carbon,.045)
   for offset_y in [-.055,0,.055]:
    pipe('Dark service-port socket',(face_x-side*.156,y+offset_y,z),(face_x-side*.19,y+offset_y,z),.035,carbon,12)
    pipe('Service-port indicator core',(face_x-side*.193,y+offset_y,z),(face_x-side*.199,y+offset_y,z),.018,glow,12)
  for z,x in [(1.24,1.12),(2.45,.94),(-1.0,1.20),(-2.18,1.35)]:
   x*=side;p=surface_point(x,z,.014)
   pipe('Flush service fastener',p,(p[0],p[1]+.010,p[2]),.022,steel,12)
   pipe('Fastener hex recess',(p[0],p[1]+.011,p[2]),(p[0],p[1]+.013,p[2]),.010,carbon,6)
  # Segmented exhaust retaining collars and radial guide vanes.
  for z in [-2.95,-3.10]:
   for i in range(16):
    a=i*math.tau/16;b=a+math.tau/16*.72
    p=(side*1.20+.285*math.cos(a),.98+.285*math.sin(a),z)
    q=(side*1.20+.285*math.cos(b),.98+.285*math.sin(b),z)
    pipe('Exhaust segmented retaining collar',p,q,.020,accent,6)
  for i in range(8):
   a=i*math.tau/8
   pipe('Exhaust inner stator',(side*1.20+.16*math.cos(a),.98+.16*math.sin(a),-2.72),(side*1.20+.25*math.cos(a+.16),.98+.25*math.sin(a+.16),-2.98),.012,carbon,6)
 # Recessed deck cooling bank: project each slat and follow the spine taper.
 for i in range(8):
  z=-1.45-i*.13;width=.32-i*.021
  path=[surface_point(-width+2*width*j/8,z,.014) for j in range(9)]
  for a,b in zip(path,path[1:]):pipe('Rear spine cooling louvre',a,b,.020,carbon,6)
 print('SCENEFORGE_FORGE_FITTED_DETAIL_OK')
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
  upper=hull_master.ray_cast(Vector((side*1.18,-1.40,4)),Vector((0,0,-1)))
  lower=hull_master.ray_cast(Vector((side*1.18,-1.40,-1)),Vector((0,0,1)))
  assert upper[0] and lower[0] and upper[1].z-lower[1].z>.60,'Front flare must have full body depth'
  upper=hull_master.ray_cast(Vector((side*1.60,1.95,4)),Vector((0,0,-1)))
  lower=hull_master.ray_cast(Vector((side*1.60,1.95,-1)),Vector((0,0,1)))
  assert upper[0] and lower[0] and upper[1].z-lower[1].z>.70,'Rear flare must have full body depth'
  assert any(side*hull_master.data.vertices[i].co.x>2.0 and hull_master.data.vertices[i].co.z>1.55 for i in seen),'Disconnected rear swept accent'
  assert any(.80<side*hull_master.data.vertices[i].co.x<1.10 and hull_master.data.vertices[i].co.z>1.85 for i in seen),'Disconnected rear raised fin'
  assert any(.50<side*hull_master.data.vertices[i].co.x<.80 and hull_master.data.vertices[i].co.z>1.65 and .95<hull_master.data.vertices[i].co.y<1.3 for i in seen),'Disconnected canopy shoulder'
 print('SCENEFORGE_FORGE_CANOPY_SHOULDER_OK')
 print('SCENEFORGE_FORGE_REAR_ACCENTS_OK')
 print('SCENEFORGE_FORGE_REAR_DEPTH_OK')
 print('SCENEFORGE_FORGE_VOLUMETRIC_FLARES_OK')
 print('SCENEFORGE_FORGE_CONNECTED_NACELLES_OK')
 print('SCENEFORGE_FORGE_CONNECTED_FENDERS_OK')
 print('SCENEFORGE_FORGE_MASTER_SURFACES_OK')
