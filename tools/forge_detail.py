"""FORGE sparse master surfaces; metres, Godot +Z forward.
Mirror -> Catmull-Clark -> inward thickness. Shared hull/canopy boundary.
"""
FORGE_STATIONS=[(-2.70,.76,.65,1.20,1.20),(-2.62,.88,.60,1.28,1.28),(-2.10,1.08,.48,1.39,1.39),(-1.35,1.04,.40,1.40,1.40),(-1.10,.98,.36,1.35,1.82),(-.70,.92,.33,1.29,2.00),(-.15,.87,.30,1.23,2.02),(.45,.82,.28,1.16,1.89),(1.05,.76,.26,1.05,1.78),(1.50,.66,.25,.91,.91),(1.90,.56,.25,.79,.79),(2.40,.39,.26,.61,.61),(2.85,.20,.27,.44,.44),(3.12,.08,.28,.35,.35),(3.18,.06,.29,.33,.33)]

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
 forge_surface('Forge_Master_Monocoque',pts,faces,body,thickness=.035)
 # Glass uses the hull's aperture stations and sill coordinates.
 pts=[];faces=[]
 for z,w,lo,hi,crown in FORGE_STATIONS[3:10]:
  for u in [0,.25,.50,.75,.93,1]:pts.append((.62*w*u,hi+.012+(crown-hi)*math.cos(u*math.pi/2),z))
 for r in range(6):
  for c in range(5):
   a=r*6+c;faces.append((a,a+6,a+7,a+1))
 forge_surface('vehicle_glass_forge_master',pts,faces,glass,thickness=.018)
 rows=[(-2.50,.70,1.22,1.18),(-2.42,.73,1.27,1.22),(-1.65,.77,1.40,1.22),(-.7,.78,1.25,1.03),(.6,.70,1.12,.82),(1.7,.58,.93,.61),(2.7,.46,.70,.40),(3.35,.40,.45,.30),(3.42,.40,.43,.30)]
 for side in [-1,1]:
  pts=[];faces=[]
  for z,inner,outer,y in rows:
   for x,h in [(inner,y-.06),(inner+.035,y+.015),(inner+(outer-inner)*.55,y+.05),(outer-.025,y-.02),(outer,y-.08),(outer-.03,y-.15),(inner+.03,y-.15),(inner,y-.12)]:pts.append((side*x,h,z))
  for r in range(len(rows)-1):
   for c in range(8):
    a=r*8+c;b=r*8+(c+1)%8;faces.append((a,b,b+8,a+8))
  for off in [0,(len(rows)-1)*8]:
   for cap in [(0,1,2,3),(0,3,4,7),(4,5,6,7)]:faces.append(tuple(off+i for i in cap))
  forge_surface('Forge_Swept_Blade',pts,faces,body,mirror=False,thickness=.012)
  for z,y in [(1.8,.43),(-1.5,.61)]:
   x=side*(.88 if z>0 else 1.12)
   pipe('Recessed hover cell',(x,y-.12,z),(x,y,z),.24,carbon,32)
  pipe('Rear drive housing',(side*.82,.93,-2.10),(side*.82,.93,-2.82),.32,steel,32)
  pipe('Rear drive recess',(side*.82,.93,-2.83),(side*.82,.93,-2.85),.25,carbon,32)
 pipe('Central drive housing',(0,1.05,-2.18),(0,1.05,-2.90),.24,carbon,32)
 box('Cockpit floor',(0,.70,.1),(.94,.08,2.20),carbon,.025)
 box('Bucket cushion',(0,.91,-.30),(.50,.16,.68),rubber,.05)
 box('Seat back',(0,1.34,-.74),(.52,.78,.16),rubber,.05)
 box('Head restraint',(0,1.79,-.78),(.33,.20,.16),rubber,.04)
 before=set(bpy.context.scene.objects)
 pipe('Yoke bridge',(-.22,1.23,1.08),(.22,1.23,1.08),.03,steel)
 for s in [-1,1]:pipe('Yoke grip',(s*.22,1.18,1.08),(s*.23,1.38,1.05),.035,rubber)
 rig('Kestrel_Yoke',since(before),(0,1.25,1.08))
 for i in range(5):
  before=set(bpy.context.scene.objects);x=(i-2)*.25
  box('Rear vector vane',(x,1.40,-2.46),(.20,.045,.46),body,.012)
  rig('Kestrel_Tail_%d'%i,since(before),(x,1.40,-2.23))
 print('SCENEFORGE_FORGE_MASTER_SURFACES_OK')
