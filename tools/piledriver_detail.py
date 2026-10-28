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
 profile=[(-2.65,.60,.57,1.15),(-2.35,.96,.48,1.30),(-1.65,1.14,.41,1.32),(-.95,.91,.40,1.18),(.0,.85,.38,1.13),(1.20,.93,.39,1.22),(1.72,.98,.42,1.28),(2.25,.86,.45,1.17),(2.85,.64,.49,.94),(3.22,.41,.52,.75),(3.42,.28,.54,.67)]
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
  panel('Inset carbon sill',[(side*.88,.48,1.2),(side*.82,.43,-.65),(side*1.08,.52,-1.55),(side*.98,.68,-1.9),(side*.88,.69,-.4),(side*.94,.66,1.3)],carbon)
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
  for x,y,z in [(side*1.0,.58,2.1),(side*1.12,.76,-.65)]:
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
  rim=[(side*.61,1.23,1.37),(side*.70,1.09,.70),(side*.71,1.02,-.40),(side*.64,1.22,-1.20)]
  strip('Carbon cockpit rim',rim,.045,carbon)
  strip('Cockpit brass rim seam',[(x,y+.038,z) for x,y,z in rim],.014,accent)
  rail=[(side*.53,1.21,2.00),(side*.58,1.43,1.45),(side*.56,1.86,.32),(side*.51,1.98,-.45),(side*.49,1.90,-.95),(side*.58,1.35,-1.62)]
  strip('Swept brass roll hoop',rail,.032,accent)
  # Seat, harness and console detail are visible in side and cockpit views.
  box('Seat side bolster',(side*.30,1.02,-.15),(.12,.24,.72),rubber,.055)
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
 panel('Carbon hood intake',[(-.25,1.275,1.67),(.25,1.275,1.67),(.18,1.17,2.25),(-.18,1.17,2.25)],carbon)
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
 marking('07',(-.27,1.286,1.70),.17)
 marking('PYLDRIVER',(-.74,1.25,1.93),.075)
 # Preserve the five animated vector controls, integrated above turbine bodies.
 for i in range(5):
  before=set(bpy.context.scene.objects);x=(i-2)*.36
  pipe('Vector nozzle',(x,1.48,-1.83),(x,1.48,-2.34),.095,carbon,16)
  pipe('Vector plasma liner',(x,1.48,-2.29),(x,1.48,-2.35),.065,glow,16)
  panel('Layered tail vector',[(x-.11,1.53,-1.8),(x+.11,1.53,-1.8),(x+.13,1.61,-2.78),(x-.13,1.61,-2.78)],carbon)
  rig('Kestrel_Tail_%d'%i,since(before),(x,1.48,-1.83))
