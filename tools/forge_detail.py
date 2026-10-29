"""FORGE: original graphite / amber precision racer, authored in metres."""
def build_forge(body,accent,carbon,steel,rubber,glow,glass):
 # Broad rear power shoulders feed two tapered, separated forward spars.
 hull([(-2.65,.65,.70,1.32),(-2.0,1.02,.48,1.45),(-.9,.80,.30,1.25),(.4,.69,.28,1.14),(1.4,.64,.30,1.08),(2.3,.36,.27,.74),(3.15,.035,.30,.39)],body)
 def line(name,pts,r,m):
  for a,b in zip(pts,pts[1:]):pipe(name,a,b,r,m,12)
 for side in [-1,1]:
  # Forged blade spars: chamfered structural rails with recessed amber channels.
  profile=[(-2.4,.20,.67,1.32),(-1.8,.35,.44,1.28),(-.5,.27,.31,.96),(1.1,.18,.25,.76),(2.5,.11,.23,.49),(3.25,.02,.25,.32)]
  before=set(bpy.context.scene.objects)
  hull(profile,steel)
  for obj in since(before):obj.location.x=side*.98
  line('Amber spar inlay',[(side*1.0,.81,-1.6),(side*1.0,.64,-.4),(side*1.0,.47,1.3),(side*.98,.34,2.8)],.018,glow)
  for z in [-1.7,-1.1,-.5,.1,.7,1.3]:
   y=.70-.11*z
   box('Structural spar clamp',(side*.99,y,z),(.31,.055,.08),carbon,.015)
   pipe('Spar titanium fastener',(side*1.15,y,z),(side*1.17,y,z),.025,accent,10)
  panel('Shoulder armor',[(side*.55,1.18,-.7),(side*1.28,1.18,-1.55),(side*1.15,1.39,-2.4),(side*.60,1.47,-2.35)],body)
  for i in range(7):
   box('Heat exchanger fin',(side*.94,1.30,-1.45-i*.11),(.42,.035,.045),steel,.008)
  # Hollow exhaust bells, with separate outer skin and recessed hot throat.
  cx=side*.91;cy=.92;verts=[]
  for z,r in [(-1.85,.28),(-2.60,.39),(-2.84,.34),(-2.84,.28),(-2.45,.23)]:
   for i in range(32):
    a=i*math.tau/32;verts.append((cx+r*math.cos(a),cy+r*math.sin(a),z))
  faces=[]
  for row in range(4):
   for i in range(32):faces.append((row*32+i,row*32+(i+1)%32,(row+1)*32+(i+1)%32,(row+1)*32+i))
  engine=mesh('Split induction exhaust',verts,faces,steel)
  for f in engine.data.polygons:f.use_smooth=True
  pipe('Exhaust throat',(cx,cy,-2.44),(cx,cy,-2.46),.23,carbon,24)
  pipe('Amber exhaust iris',(cx,cy,-2.46),(cx,cy,-2.48),.15,glow,24)
  for i in range(8):
   a=i*math.tau/8
   pipe('Exhaust radial vane',(cx+.17*math.cos(a),cy+.17*math.sin(a),-2.50),(cx+.28*math.cos(a+.18),cy+.28*math.sin(a+.18),-2.76),.018,carbon,8)
  for z,r in [(-2.58,.39),(-2.81,.34)]:
   obj=ring('Exhaust retaining ring',(cx,cy,z),r,.025,accent);obj.rotation_euler.x=math.pi/2
  for x,y,z in [(side*1.0,.58,2.1),(side*1.12,.76,-.65)]:
   pipe('Ducted levitation cell',(x,y-.12,z),(x,y+.05,z),.23,carbon,24)
   ring('Amber field emitter',(x,y-.13,z),.21,.018,glow)
   panel('Pod aero shroud',[(x-.27,y+.06,z-.35),(x+.27,y+.06,z-.35),(x+.19,y+.17,z+.30),(x,y+.12,z+.48),(x-.19,y+.17,z+.30)],body)
  # Enclosed cockpit has a framed glazed roof with a central sight channel.
  rim=[(side*.48,1.08,1.2),(side*.45,1.03,.2),(side*.46,1.20,-.85)]
  line('Cockpit sill',rim,.07,carbon)
  frame=[(side*.49,1.10,1.5),(side*.43,1.98,.30),(side*.42,2.02,-.55),(side*.53,1.30,-1.2)]
  line('Canopy titanium frame',frame,.035,steel)
  panel('vehicle_glass_forge_side',[(side*.49,1.10,1.5),(side*.43,1.98,.30),(side*.42,2.02,-.55),(side*.53,1.30,-1.2),(side*.46,1.03,.2)],glass)
  box('Contoured hip cushion',(side*.26,.99,-.36),(.14,.23,.78),rubber,.05)
  box('Shoulder restraint',(side*.28,1.40,-.69),(.15,.37,.23),rubber,.05)
  line('Core coolant conduit',[(side*.35,1.23,-1.05),(side*.51,1.45,-1.60),(side*.65,1.3,-2.1)],.035,accent)
 panel('vehicle_glass_forge_windscreen',[(-.49,1.10,1.5),(.49,1.10,1.5),(.43,1.98,.30),(-.43,1.98,.30)],glass)
 panel('Canopy roof',[(-.43,1.98,.30),(.43,1.98,.30),(.42,2.02,-.55),(-.42,2.02,-.55)],body)
 box('Recessed cockpit floor',(0,.73,.0),(.85,.08,2.25),carbon)
 box('Bucket seat',(0,.90,-.35),(.48,.15,.72),rubber,.06)
 box('Seat back',(0,1.34,-.76),(.52,.80,.16),rubber,.06)
 box('Head restraint',(0,1.80,-.79),(.35,.23,.18),rubber,.05)
 for side in [-1,1]:box('Amber harness',(side*.13,1.32,-.66),(.06,.55,.025),accent,.01)
 before=set(bpy.context.scene.objects)
 pipe('Yoke bridge',(-.22,1.23,1.08),(.22,1.23,1.08),.03,steel)
 for side in [-1,1]:pipe('Yoke grip',(side*.22,1.18,1.08),(side*.23,1.38,1.05),.035,rubber)
 rig('Kestrel_Yoke',since(before),(0,1.25,1.08))
 # Exposed stacked reactor: a contained warm heart beneath a protective spine.
 pipe('Reactor housing',(0,1.35,-1.35),(0,1.35,-2.35),.30,carbon,24)
 for z in [-1.45,-1.65,-1.85,-2.05,-2.25]:
  obj=ring('Visible reactor induction loop',(0,1.35,z),.27,.025,glow);obj.rotation_euler.x=math.pi/2
 line('Reactor spine',[(0,1.66,-1.25),(0,1.70,-2.1),(0,1.53,-2.55)],.055,steel)
 for i in range(5):
  x=(i-2)*.31;before=set(bpy.context.scene.objects)
  panel('Active exhaust guide',[(x-.11,1.46,-2.05),(x+.11,1.46,-2.05),(x+.10,1.65,-2.91),(x-.10,1.65,-2.91)],body)
  pipe('Guide amber trailing edge',(x-.09,1.65,-2.91),(x+.09,1.65,-2.91),.012,glow,8)
  rig('Kestrel_Tail_%d'%i,since(before),(x,1.46,-2.05))
 # Layered nose cheeks and a recessed central intake break up the broad foredeck.
 for side in [-1,1]:
  cheek=[(side*.07,.43,3.01),(side*.30,.70,2.30),(side*.52,.94,1.70),(side*.30,1.02,1.56),(side*.13,.80,2.12)]
  panel('Floating nose armor cheek',cheek,steel)
  line('Nose precision seam',cheek[:3],.012,accent)
  panel('Nose intake recess',[(side*.06,1.025,1.57),(side*.22,1.025,1.57),(side*.15,.80,2.18),(side*.04,.80,2.18)],carbon)
  for i in range(6):
   z=1.63+i*.085;y=1.025-(z-1.57)*.225/.61
   pipe('Intake slotted grille',(side*.065,y+.012,z),(side*(.21-(z-1.57)*.10),y+.012,z),.012,steel,8)
  # Canopy seals, hinge barrels and armoured lower door panels.
  line('Canopy rubber gasket',[(side*.49,1.09,1.48),(side*.43,1.97,.30),(side*.42,2.01,-.55),(side*.53,1.29,-1.19)],.047,carbon)
  line('Canopy bright outer edge',[(side*.49,1.11,1.48),(side*.43,1.99,.30),(side*.42,2.03,-.55)],.018,steel)
  for z in [-.55,-.35]:pipe('Canopy hinge',(side*.44,2.025,z),(side*.44,2.025,z+.11),.034,accent,12)
  panel('Door lower armor',[(side*.53,1.10,.95),(side*.64,.74,.75),(side*.72,.73,-.5),(side*.60,1.18,-.85)],body)
  line('Door recessed perimeter',[(side*.54,1.08,.92),(side*.63,.76,.73),(side*.70,.75,-.48),(side*.60,1.16,-.82)],.014,steel)
  box('Flush canopy latch',(side*.63,1.05,-.55),(.04,.065,.19),accent,.015)
  # Electrical bus cabling, ceramic isolators and shielded reactor feed.
  line('Braided power feed',[(side*.40,1.25,-1.1),(side*.63,1.16,-1.45),(side*.71,1.08,-2.0)],.052,carbon)
  for i in range(6):
   z=-1.4-i*.10
   pipe('Power feed collar',(side*.64,1.18,z),(side*.64,1.18,z-.035),.065,accent,12)
  for i in range(9):
   z=-1.9-i*.08
   pipe('Turbine longitudinal rib',(side*.91+.31,1.03,z),(side*.91+.32,1.11,z-.06),.021,carbon,8)
  for z in [-1.85,-2.23]:
   for a in [0,math.pi/2,math.pi,3*math.pi/2]:
    x=side*.91+.32*math.cos(a);y=.92+.32*math.sin(a)
    pipe('Engine captive bolt',(x,y,z),(x,y,z-.045),.025,accent,10)
  for x,y,z in [(side*1.0,.58,2.1),(side*1.12,.76,-.65)]:
   line('Pod suspension wishbone',[(x*.72,y+.12,z-.20),(x,y+.02,z),(x*.72,y+.12,z+.20)],.035,steel)
   for i in range(4):box('Pod heat vent',(x,y+.13,z-.20+i*.08),(.25,.018,.025),carbon,.004)
  for z in [-1.6,-.8,.0,.8]:
   pipe('Sill inset fastener',(side*.74,.55,z),(side*.77,.55,z),.022,accent,10)
 # Rear bulkhead seals the cockpit behind the head restraint.
 panel('Rear cockpit bulkhead',[(-.51,1.25,-1.18),(.51,1.25,-1.18),(.41,1.98,-.58),(-.41,1.98,-.58)],carbon)
 for x in [-.24,0,.24]:
  line('Rear bulkhead stiffener',[(x,1.29,-1.18),(x,1.93,-.64)],.022,steel)
 for z in [-1.48,-1.88,-2.25]:
  pipe('Reactor transverse brace',(-.43,1.56,z),(.43,1.56,z),.025,steel)
 # Small raised identity plate, visible in top and nose inspection views.
 box('Forge nose badge backing',(0,.83,2.05),(.13,.025,.22),carbon,.015)
 for z in [2.00,2.06,2.12]:box('Forge three-bar insignia',(0,.85,z),(.08,.01,.018),accent,.003)
