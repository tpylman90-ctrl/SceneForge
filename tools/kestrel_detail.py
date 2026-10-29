"""Kestrel inspection-grade finish, authored in the existing Blender chassis frame."""
def polish_kestrel():
 def plate(name,points,material,door=False):
  obj=hero_mesh(name,points,[tuple(range(len(points)))],material)
  mod=obj.modifiers.new('Formed panel gauge','SOLIDIFY');mod.thickness=.018
  bpy.context.view_layer.objects.active=obj;bpy.ops.object.modifier_apply(modifier=mod.name)
  if door:obj['driver_door']=True
  return obj
 def line(name,points,r,material):
  for a,b in zip(points,points[1:]):pipe(name,a,b,r,material,12)
 # Contoured carbon undercuts and orange feather armor follow the narrowed waist.
 for side in [-1,1]:
  for y0,y1 in [(-2.45,-1.55),(-1.4,-.60),(-.55,.30),(.35,1.20),(1.25,1.95)]:
   points=[]
   for y,f,h in [(y0,.94,.40),(y1,.98,.45),(y1,.91,.12),(y0,.89,.12)]:
    w,lo,hi=dims(y);points.append((side*w*f,cy+y,lo+(hi-lo)*h))
   plate('Sculpted carbon lower chine',points,'kestrel_carbon',side==1 and y0>=-.55 and y1<=1.2)
  for yy in [-1.20,-.45,.30]:
   points=[]
   for y,f,h in [(yy,1.025,.84),(yy+.79,1.02,.86),(yy+.59,1.04,.48),(yy+.08,1.02,.39)]:
    w,lo,hi=dims(y);points.append((side*w*f,cy+y,lo+(hi-lo)*h))
   plate('Layered burnt orange shoulder armor',points,'kestrel_orange',side==1)
   # Dark panel gap beneath each feather; screws sit in the plate instead of floating.
   for a,b in zip(points[:2],points[1:2]):
    edge=pipe('Feather machined edge',a,b,.012,'steel',10)
    if side==1:edge['driver_door']=True
   for point in [points[0],points[2]]:
    x,y,z=point
    o=pipe('Captive armor screw',(x,y,z),(x+side*.012,y,z),.018,'steel',8)
    if side==1:o['driver_door']=True
  # Intake shoulders: thick lips, dark throat and closely spaced louvers.
  for y in [1.38,1.50,1.62,1.74]:
   w,lo,hi=dims(y)
   pipe('Shoulder extractor blade',(side*w*.85,cy+y,hi+.025),(side*w*1.01,cy+y+.07,hi-.12),.033,'trim',12)
  for yy in [1.56,1.88]:
   w,lo,hi=dims(yy)
   pipe('Recessed cooling port',(side*(w+.018),cy+yy,.92),(side*(w+.065),cy+yy,.92),.095,'trim',20)
   pipe('Port retaining collar',(side*(w+.058),cy+yy,.92),(side*(w+.075),cy+yy,.92),.066,'steel',20)
   pipe('Port core',(side*(w+.076),cy+yy,.92),(side*(w+.080),cy+yy,.92),.040,'kestrel_carbon',16)
  # Visible braided circuits with clamp collars route into the rear drive.
  path=[(side*.70,cy+.70,.64),(side*.80,cy+1.25,.73),(side*.64,cy+1.82,.87),(side*.42,cy+2.15,1.02)]
  line('Drive coolant hardline',path,.024,'steel')
  for x,y,z in path[1:-1]:box('Burnt orange coolant clamp',(x,y,z),(.11,.07,.07),'kestrel_orange',.009)
  # Integrated front winglet, carbon skid and replaceable metallic leading edge.
  pts=[(side*.44,cy-3.34,.54),(side*.80,cy-2.95,.55),(side*.86,cy-2.19,.58),(side*.61,cy-2.28,.59)]
  plate('Swept carbon foreplane',pts,'kestrel_carbon')
  line('Foreplane titanium edge',pts[:3],.021,'steel')
  plate('Orange foreplane endplate',[(side*.80,cy-2.94,.55),(side*.86,cy-2.23,.58),(side*.86,cy-2.44,.74),(side*.80,cy-2.89,.66)],'kestrel_orange')
  for yy in [-1.4,1.25]:
   x=side*(1.0 if yy<0 else 1.12)
   for dy in [-.27,0,.27]:
    box('Repulsor cooling recess',(x,cy+yy+dy,.846),(.15,.08,.017),'trim',.005)
   pipe('Repulsor upper tie rod',(side*.75,cy+yy,.84),(x,cy+yy,.75),.035,'steel',12)
 # Glazing follows the long rail profile, with slim mullions and black rubber seals.
 rail=[(-1.44,.50,1.19,.50,1.19),(-.48,.57,1.70,.73,1.25),(.47,.57,1.78,.73,1.28),(1.29,.48,1.61,.57,1.20),(1.67,.48,1.23,.48,1.18)]
 for a,b in zip(rail,rail[1:]):
  ya,wa,za,ba,sa=a;yb,wb,zb,bb,sb=b
  if ya>=-.48:
   plate('vehicle_glass_canopy_roof',[(-wa,cy+ya,za+.012),(wa,cy+ya,za+.012),(wb,cy+yb,zb+.012),(-wb,cy+yb,zb+.012)],'vehicle_glass')
  for side in [-1,1]:
   plate('vehicle_glass_canopy_side',[(side*wa,cy+ya,za),(side*wb,cy+yb,zb),(side*bb,cy+yb,sb),(side*ba,cy+ya,sa)],'vehicle_glass')
 for side in [-1,1]:
  line('Fitted canopy rubber seal',[(side*b,cy+y,s) for y,w,z,b,s in rail],.012,'trim')
 pipe('Canopy central crossmember',(-.57,cy+.47,1.78),(.57,cy+.47,1.78),.021,'trim',12)
 # Open turbine bell with an actual recessed throat, stators and a copper heat collar.
 vertices=[]
 for y,r in [(2.25,.27),(2.58,.34),(2.73,.31),(2.74,.25),(2.44,.22)]:
  for i in range(32):
   t=math.tau*i/32;vertices.append((r*math.cos(t),cy+y,1.03+r*math.sin(t)))
 faces=[]
 for j in range(4):
  for i in range(32):faces.append((j*32+i,j*32+(i+1)%32,(j+1)*32+(i+1)%32,(j+1)*32+i))
 bell=hero_mesh('Hollow plasma turbine bell',vertices,faces,'steel')
 for face in bell.data.polygons:face.use_smooth=True
 for i in range(8):
  t=math.tau*i/8
  pipe('Turbine stator',(.12*math.cos(t),cy+2.53,1.03+.12*math.sin(t)),(.23*math.cos(t+.2),cy+2.55,1.03+.23*math.sin(t+.2)),.018,'trim',8)
 # Inspection markings: small surface lettering and identity plate.
 bpy.ops.object.text_add(location=(-.28,cy-1.94,dims(-1.94)[2]+.035))
 label=bpy.context.object;label.name='Kestrel etched model designation';label.data.body='KESTREL';label.data.size=.105
 label.data.extrude=.0004;label.data.materials.append(M['steel'])
 bpy.ops.object.convert(target='MESH')
 for side in [-1,1]:
  for yy in [1.5,1.8]:
   w,lo,hi=dims(yy)
   box('Recessed service latch',(side*w*.63,cy+yy,hi+.025),(.12,.10,.028),'steel',.008)
   box('Latch release slot',(side*w*.63,cy+yy,hi+.041),(.075,.018,.008),'trim',.002)
polish_kestrel()
