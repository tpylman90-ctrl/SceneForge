"""Piledriver hero geometry. Executed inside build_fleet.py's authored-coordinate helpers."""
def build_piledriver(body,accent,carbon,steel,rubber,glow,glass):
 # Deep plum lacquer and aged brass, with baked fine surface variation.
 body.diffuse_color=(.105,.018,.24,1)
 p=body.node_tree.nodes['Principled BSDF']
 p.inputs['Base Color'].default_value=body.diffuse_color
 p.inputs['Roughness'].default_value=.29
 p.inputs['Coat Weight'].default_value=.38
 accent.diffuse_color=(.48,.30,.085,1)
 p=accent.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=accent.diffuse_color
 p.inputs['Roughness'].default_value=.30
 import numpy as np
 rng=np.random.default_rng(7107)
 for material in [body,accent,carbon]:
  n=256;pixels=np.ones((n,n,4),dtype=np.float32)
  base=np.array(material.diffuse_color[:3]);grain=rng.random((n,n))
  variation=.95+.10*grain
  if material==carbon:
   x,y=np.meshgrid(np.arange(n),np.arange(n));variation=.75+.3*((x//4+y//4)%4<2)+.08*np.sin((x%4)*math.pi/4)
  pixels[:,:,:3]=np.power(np.clip(base[None,None,:]*variation[:,:,None],0,1),1/2.2)
  image=bpy.data.images.new('Piledriver_'+material.name+'_finish',width=n,height=n,alpha=True)
  image.pixels.foreach_set(pixels.ravel());image.pack()
  tex=material.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
  material.node_tree.links.new(tex.outputs['Color'],material.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
 # Curved section loft: rounded chin, rising haunches and a genuine open cockpit.
 profile=[(-2.65,.60,.84,1.38),(-2.35,.96,.66,1.48),(-1.65,1.10,.35,1.43),(-.95,.80,.20,1.20),(.0,.73,.26,1.12),(1.20,.84,.40,1.24),(1.72,.94,.39,1.22),(2.25,.81,.30,1.01),(2.85,.58,.24,.73),(3.22,.35,.23,.49),(3.42,.22,.25,.40)]
 sections=[]
 for i in range(len(profile)-1):
  for step in range(4):
   t=step/4;u=t*t*(3-2*t)
   sections.append(tuple(profile[i][k]*(1-(t if k==0 else u))+profile[i+1][k]*(t if k==0 else u) for k in range(4)))
 sections.append(profile[-1])
 cross=[(-.66,0),(.66,0),(.93,.13),(1,.43),(.98,.70),(.84,.93),(.60,1),(-.60,1),(-.84,.93),(-.98,.70),(-1,.43),(-.93,.13)]
 points=[]
 for z,w,lo,hi in sections:
  points.extend([(x*w,lo+y*(hi-lo),z) for x,y in cross])
 faces=[tuple(reversed(range(12)))]
 for j in range(len(sections)-1):
  for k in range(12):
   if k==6 and sections[j][0]<1.4 and sections[j+1][0]>-1.2:continue
   faces.append((j*12+k,j*12+(k+1)%12,(j+1)*12+(k+1)%12,(j+1)*12+k))
 faces.append(tuple((len(sections)-1)*12+k for k in range(12)))
 shell=mesh('Sculpted plum monocoque',points,faces,body,.012)
 def dims(z):
  return tuple(float(np.interp(z,[s[0] for s in profile],[s[k] for s in profile])) for k in [1,2,3])
 def strip(name,path,r,material):
  for a,b in zip(path,path[1:]):pipe(name,a,b,r,material,12)
 # Brass panel outlines follow the actual body, rather than straight external bars.
 for side in [-1,1]:
  for factor,height in [(.96,.52),(.84,.94)]:
   path=[]
   for z in np.linspace(-2.35,3.2,32):
    w,lo,hi=dims(z);path.append((side*w*factor,lo+(hi-lo)*height+.008,z))
   strip('Fine brass body seam',path,.012,accent)
  # Layered flanks, carbon lower sills and flush maintenance hardware.
  # Deep waist, rising diffuser and an exposed forebody: no flat slab belly.
  sill=[]
  for z in [-2.4,-1.7,-1.0,-.3,.5,1.2,1.8,2.4,3.05]:
   w,lo,hi=dims(z);sill.append((side*w*.94,lo+.08,z))
  strip('Sculpted lower brass chine',sill,.021,accent)
  for za,zb in [(-2.35,-1.65),(-1.65,-.95),(-.95,0),(0,1.2),(1.2,2.25)]:
   wa,la,ha=dims(za);wb,lb,hb=dims(zb)
   panel('Recessed carbon undercut',[(side*wa*.94,la+.10,za),(side*wb*.94,lb+.10,zb),(side*wb*.99,lb+.24,zb),(side*wa*.99,la+.24,za)],carbon)
  for z in [-1.9,-1.65,-1.4]:
   pipe('Exposed sill cooling pipe',(side*.73,.43,z),(side*.86,.58,z-.24),.027,accent)
  panel('Raised rear purple haunch',[(side*.86,1.15,-.95),(side*1.16,1.37,-1.65),(side*.94,1.44,-2.35),(side*.61,1.26,-2.60),(side*.68,1.17,-1.45)],body)
  strip('Haunch brass edging',[(side*.86,1.17,-.95),(side*1.16,1.39,-1.65),(side*.94,1.46,-2.35),(side*.61,1.28,-2.60)],.014,accent)
  for z in [-2.22,-1.85,-1.48,.95,1.40,1.85,2.25]:
   w,lo,hi=dims(z)
   pipe('Flush panel rivet',(side*w*.97,lo+(hi-lo)*.69,z),(side*(w*.97+.012),lo+(hi-lo)*.69,z),.014,steel,8)
  # Rear extractor vent, slotted shield and secondary mechanical access covers.
  panel('Rear vent surround',[(side*1.13,1.28,-1.65),(side*.96,1.36,-2.12),(side*.88,1.04,-2.28),(side*1.13,.99,-1.75)],steel)
  for i in range(4):
   z=-1.75-i*.105
   pipe('Rear extractor slot',(side*1.14,1.07,z),(side*1.03,1.26,z-.03),.032,carbon,10)
  for z in [-1.55,-1.90]:
   pipe('Service cover',(side*1.05,.69,z),(side*1.12,.69,z),.105,steel,20)
   pipe('Service cover inset',(side*1.115,.69,z),(side*1.13,.69,z),.065,carbon,16)
  # Low forward skis: sculpted runners, two-axis joints and exposed actuators.
  ski=[(side*.51,.28,3.72),(side*.72,.28,3.55),(side*.77,.29,2.08),(side*.53,.29,2.0)]
  panel('Forward armored runner',ski,accent)
  strip('Runner wear rail',[(side*.62,.32,3.68),(side*.68,.34,3.42),(side*.65,.34,2.12)],.035,steel)
  for z in [2.25,2.80]:
   pipe('Runner suspension link',(side*.65,.35,z),(side*.72,.67,z-.15),.045,steel)
   pipe('Runner actuator',(side*.65,.35,z+.12),(side*.72,.60,z-.04),.024,accent)
   pipe('Runner joint',(side*.60,.39,z),(side*.70,.39,z),.065,carbon)
  # Smooth integrated hover fairings replace exposed cylindrical pots.
  for x,y,z in [(side*.48,.32,1.95),(side*.48,.25,-1.25)]:
   pipe('Repulsor core',(x,y-.12,z),(x,y+.05,z),.245,carbon,24)
   ring('Hidden magnetic halo',(x,y-.13,z),.225,.018,glow)
   bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=v((x,y+.08,z)))
   fair=bpy.context.object;fair.name='Integrated plum pod fairing';fair.scale=(.31,.46,.14);fair.data.materials.append(body)
   bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
   for face in fair.data.polygons:face.use_smooth=True
   pipe('Pod linkage',(x*.75,y+.12,z),(x,y,z),.055,steel)
   for zz in [-.15,0,.15]:box('Pod cooling slot',(x,y+.20,z+zz),(.16,.018,.035),carbon,.004)
  # Deep hollow turbine: bell mouth, internal stator, collar and heat shielding.
  cx=side*1.0;cy=.95
  verts=[]
  for z,r in [(-1.75,.24),(-2.35,.34),(-2.64,.30),(-2.68,.24),(-2.30,.23)]:
   for i in range(32):
    a=math.tau*i/32;verts.append((cx+r*math.cos(a),cy+r*math.sin(a),z))
  faces=[]
  for row in range(4):
   for i in range(32):faces.append((row*32+i,row*32+(i+1)%32,(row+1)*32+(i+1)%32,(row+1)*32+i))
  verts=[(x,y,z-.35) for x,y,z in verts]
  engine=mesh('Hollow rear turbine bell',verts,faces,steel)
  for face in engine.data.polygons:face.use_smooth=True
  pipe('Turbine dark throat',(cx,cy,-2.58),(cx,cy,-2.63),.225,carbon,32)
  pipe('Recessed plasma core',(cx,cy,-2.61),(cx,cy,-2.64),.085,glow,20)
  for i in range(8):
   a=math.tau*i/8
   pipe('Internal turbine stator',(cx+.11*math.cos(a),cy+.11*math.sin(a),-2.73),(cx+.235*math.cos(a+.18),cy+.235*math.sin(a+.18),-2.75),.014,accent,8)
  for z,r in [(-2.36,.34),(-2.60,.305)]:
   collar=ring('Machined turbine collar',(cx,cy,z-.35),r,.022,accent);collar.rotation_euler.x=math.pi/2
  pipe('Upper engine plumbing',(side*.60,1.13,-1.55),(side*.62,1.25,-2.1),.045,accent)
  # Swept tail feathers, layered across the rising shoulder.
  for i in range(3):
   panel('Swept purple tail vane',[(side*(.71+i*.12),1.32,-1.85),(side*(1.12+i*.18),1.56+i*.06,-3.05-i*.10),(side*(.86+i*.13),1.46,-2.86),(side*.65,1.26,-2.12)],body if i==0 else carbon)
  # Open low rim and a continuous swept roll frame; no tall glass screen.
  rim=[(side*.50,1.24,1.37),(side*.46,1.10,.70),(side*.44,1.04,-.40),(side*.48,1.24,-1.20)]
  strip('Carbon cockpit rim',rim,.045,carbon)
  strip('Cockpit brass rim seam',[(x,y+.038,z) for x,y,z in rim],.014,accent)
  rail=[(side*.53,1.21,2.00),(side*.58,1.43,1.45),(side*.56,1.86,.32),(side*.51,1.98,-.45),(side*.49,1.90,-.95),(side*.58,1.35,-1.62)]
  strip('Swept brass roll hoop',rail,.032,accent)
  # Seat, harness and console detail are visible in side and cockpit views.
  box('Seat hip bolster',(side*.27,.99,-.22),(.14,.28,.82),rubber,.055)
  box('Seat torso bolster',(side*.27,1.31,-.49),(.14,.53,.26),rubber,.055)
  box('Seat shoulder wing',(side*.30,1.54,-.55),(.17,.22,.29),carbon,.045)
  panel('Fitted cockpit inner wall',[(side*.46,1.10,.75),(side*.44,1.04,-.40),(side*.48,1.24,-1.20),(side*.33,.78,-.95),(side*.34,.78,.78)],carbon)
  box('Padded cockpit elbow rail',(side*.43,1.07,-.02),(.12,.12,.90),rubber,.04)
  panel('Wraparound side console',[(side*.34,.88,.20),(side*.45,1.07,.20),(side*.46,1.10,.82),(side*.30,.94,.92)],carbon)
  box('Gold shoulder harness',(side*.15,1.37,-.46),(.08,.56,.035),accent,.015)
  for z in [.1,.35,.6]:box('Console engraved switch',(side*.61,1.12,z),(.065,.04,.055),steel,.008)
 pipe('Swept top cross brace',(-.51,1.98,-.45),(.51,1.98,-.45),.028,accent)
 panel('Low polarized wind deflector',[(-.50,1.22,1.60),(.50,1.22,1.60),(.52,1.48,1.17),(-.52,1.48,1.17)],glass)
 box('Recessed cabin floor',(0,.73,.05),(1.22,.09,2.4),carbon)
 box('Contoured seat base',(0,.91,-.20),(.57,.18,.75),rubber,.065)
 back=box('Seat shell',(0,1.32,-.65),(.63,.85,.17),carbon,.06)
 box('Seat brass upholstery',(0,1.32,-.54),(.43,.64,.095),accent,.04)
 for y in [1.08,1.23,1.38,1.53]:box('Seat stitched segment',(0,y,-.482),(.40,.018,.012),rubber,.003)
 box('Head restraint',(0,1.81,-.67),(.38,.24,.20),rubber,.055)
 box('Harness buckle',(0,1.02,-.03),(.13,.07,.1),steel,.015)
 before=set(bpy.context.scene.objects)
 for side in [-1,1]:
  pipe('Contoured yoke grip',(side*.22,1.19,1.10),(side*.24,1.38,1.07),.035,rubber)
  box('Yoke brass control',(side*.24,1.40,1.07),(.065,.04,.08),accent,.01)
 pipe('Yoke metal crossbar',(-.22,1.24,1.1),(.22,1.24,1.1),.028,steel)
 rig('Kestrel_Yoke',since(before),(0,1.25,1.1))
 # Curved brass chin and segmented intake on top of the nose.
 for z in np.linspace(2.85,3.42,9):
  w,lo,hi=dims(z)
  pipe('Sculpted brass chin',(-w*.80,lo+.13,z),(w*.80,lo+.13,z),.045,accent,16)
 panel('Carbon hood intake',[(-.25,dims(1.67)[2]+.012,1.67),(.25,dims(1.67)[2]+.012,1.67),(.18,dims(2.25)[2]+.012,2.25),(-.18,dims(2.25)[2]+.012,2.25)],carbon)
 for i in range(8):
  z=1.72+i*.063;w,lo,hi=dims(z)
  pipe('Hood intake mesh',(-.20,hi+.025,z),(.20,hi+.025,z),.009,steel,8)
 # Racing livery is baked into mesh text, without floating labels at runtime.
 def marking(value,position,size):
  bpy.ops.object.text_add(location=v(position))
  obj=bpy.context.object;obj.name='Piledriver racing marking';obj.data.body=value;obj.data.size=size
  obj.data.extrude=.0005;obj.data.materials.append(accent)
  # Text local XY lies on a top-facing Godot XZ surface.
  obj.rotation_euler=(0,0,0)
  bpy.ops.object.convert(target='MESH')
 marking('07',(-.27,dims(1.70)[2]+.018,1.70),.17)
 marking('PYLDRIVER',(-.65,dims(1.93)[2]+.018,1.93),.075)
 # Preserve the five animated vector controls, integrated above turbine bodies.
 for i in range(5):
  before=set(bpy.context.scene.objects);x=(i-2)*.36
  pipe('Vector nozzle',(x,1.48,-1.83),(x,1.48,-2.34),.095,carbon,16)
  pipe('Vector plasma liner',(x,1.48,-2.29),(x,1.48,-2.35),.065,glow,16)
  panel('Layered tail vector',[(x-.11,1.53,-1.8),(x+.11,1.53,-1.8),(x+.13,1.61,-2.78),(x-.13,1.61,-2.78)],carbon)
  rig('Kestrel_Tail_%d'%i,since(before),(x,1.48,-1.83))

 # Deepen the racer silhouette with removable hard-shell armor that follows
 # the lofted surface rather than floating as flat trim.
 def side_surface(side,z,level=.54,offset=.022):
  w,lo,hi=dims(z)
  xfactor=1.0-.12*max(0.0,abs(level-.43)-.12)
  return (side*(w*xfactor+offset),lo+(hi-lo)*level,z)
 for side in [-1,1]:
  # Three overlapping flank shells give the long body engineered depth and
  # break the single-color hull into large, readable sculpted plates.
  plate_paths=[
   [(-2.43,.50),(-2.20,.76),(-1.62,.77),(-1.22,.55),(-1.48,.36),(-2.22,.36)],
   [(-1.28,.52),(-.98,.80),(-.20,.80),(.30,.65),(.03,.40),(-.91,.39)],
   [(.22,.54),(.63,.78),(1.42,.77),(2.18,.62),(2.60,.48),(1.88,.37),(.86,.39)],
  ]
  for index,path in enumerate(plate_paths):
   pts=[side_surface(side,z,level,.040) for z,level in path]
   panel("Layered plum flank shell",pts,body)
   edge_path=[side_surface(side,z,level,.061) for z,level in path[:4]]
   strip("Raised brass armor lip",edge_path,.020,accent)
   # Recessed fasteners sit along the cut edges of each removable plate.
   for z,level in path[::2]:
    a=side_surface(side,z,level,.070);b=(a[0]+side*.025,a[1],a[2])
    pipe("Flank armor captive pin",a,b,.023,steel,10)
  # Deep shoulder cheeks form a close protective tub around the driver.
  cockpit_outer=[
   (side*.49,.94,-.92),(side*.66,1.03,-.72),
   (side*.72,1.36,-.34),(side*.70,1.49,.34),
   (side*.58,1.38,.78),(side*.45,1.16,.70)
  ]
  panel("Driver shoulder armor shell",cockpit_outer,body)
  cockpit_inner=[
   (side*.44,.98,-.72),(side*.53,1.12,-.58),
   (side*.56,1.35,-.26),(side*.54,1.42,.28),
   (side*.48,1.30,.58),(side*.41,1.12,.56)
  ]
  panel("Cockpit padded inner cheek",cockpit_inner,carbon)
  strip("Cockpit shoulder brass rim",[
   (side*.50,1.50,.27),(side*.55,1.44,-.25),(side*.50,1.20,-.69)
  ],.023,accent)
  # Tall contoured bolsters, thigh clamps and cross-belts make the seating
  # envelope read as fitted around a driver instead of an empty chair.
  box("Racing seat hip clamp",(side*.285,1.02,-.20),(.18,.31,.66),rubber,.065)
  box("Racing seat shoulder clamp",(side*.29,1.42,-.50),(.20,.31,.35),carbon,.06)
  box("Brass shoulder harness anchor",(side*.385,1.48,-.43),(.055,.11,.12),accent,.018)
  pipe("Lower diagonal safety harness",(side*.34,1.28,-.08),(side*.12,1.05,-.45),.026,accent,10)
  # Split the undersill into a swept lower keel and armored ribs; this gives
  # the vehicle a deep, angled belly instead of a straight flat underside.
  keel=[]
  for z in np.linspace(-2.35,3.10,18):
   w,lo,hi=dims(z);keel.append((side*w*.58,lo+.055,z))
  strip("Swept carbon belly keel",keel,.052,carbon)
  for z in [-1.95,-1.25,-.50,.28,1.02,1.72,2.40]:
   w,lo,hi=dims(z)
   pipe("Angled belly cross rib",(side*w*.56,lo+.065,z),(side*w*.83,lo+.11,z-.14),.032,steel,10)
  # Layered cooling banks with individual vanes on the rear shoulders.
  vent_outline=[
   side_surface(side,-2.25,.60,.075),side_surface(side,-1.90,.79,.075),
   side_surface(side,-1.48,.77,.075),side_surface(side,-1.62,.57,.075)
  ]
  panel("Shoulder extractor recess",vent_outline,carbon)
  for i in range(5):
   z=-2.18+i*.13
   a=side_surface(side,z,.66,.10);b=side_surface(side,z-.055,.75,.10)
   pipe("Machined shoulder vent vane",a,b,.022,steel,8)
 # Raised dorsal nose armor and a faceted chin cap build the long racing beak.
 hood=[
  (-.30,dims(2.52)[2]+.035,2.52),
  (-.25,dims(3.18)[2]+.035,3.18),
  (0,dims(3.40)[2]+.040,3.40),
  (.25,dims(3.18)[2]+.035,3.18),
  (.30,dims(2.52)[2]+.035,2.52),
  (0,dims(2.37)[2]+.055,2.37)
 ]
 panel("Layered dorsal nose armor",hood,body)
 for side in [-1,1]:
  pts=[(side*.30,dims(2.44)[2]+.07,2.44),
       (side*.23,dims(3.18)[2]+.06,3.18),
       (side*.10,dims(3.36)[2]+.06,3.36),
       (side*.18,dims(2.70)[2]+.08,2.70)]
  panel("Brass-edged nose cheek",pts,accent)
  strip("Beak side seam",[(side*.24,dims(2.44)[2]+.075,2.44),
                           (side*.20,dims(2.90)[2]+.075,2.90),
                           (side*.10,dims(3.34)[2]+.075,3.34)],.014,steel)

 # Rear rises while the nose drops; curved belly was authored independently above.
 bpy.context.view_layer.update()
 def rake(world):
  z=-world.y
  return Vector((world.x,world.y,world.z-.065*z))
 for obj in list(bpy.context.scene.objects):
  if obj.type!='MESH':continue
  world=obj.matrix_world.copy();inverse=world.inverted()
  for vertex in obj.data.vertices:vertex.co=inverse@rake(world@vertex.co)
  obj.data.update()
