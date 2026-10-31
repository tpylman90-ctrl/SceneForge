"""Shrike MK I: reference-built automotive surface and production detail pass.

Godot design coordinates: X=width, Y=height, +Z=front.
Geometry is original and generated in Blender. Four-view reference is the
source of the proportions; no third-party mesh, texture or paid assets.
The principal shell uses continuous quad strips across authored hard-surface
rails, not the previous elliptical tube or bolt-on fender plates.
"""
def build_shrike(body, accent, carbon, steel, rubber, glow, glass):
    import math

    # Medium-silver finish avoids the previously clipped pure-white body.
    body.diffuse_color = (.40, .46, .50, 1)
    shader = body.node_tree.nodes['Principled BSDF']
    shader.inputs['Base Color'].default_value = body.diffuse_color
    shader.inputs['Metallic'].default_value = .32
    shader.inputs['Roughness'].default_value = .39
    shader.inputs['Coat Weight'].default_value = .18

    # Controllable independent plan, sill, crown and edge rails. These profiles
    # intentionally hold width beside the canopy and a wide squared-off rear.
    # Columns: longitudinal Z, half-width, lower edge, hood/deck, side height.
    sections = [
        (-3.55, 1.25, .44, 1.25, .83),
        (-3.37, 1.39, .40, 1.36, .86),
        (-3.06, 1.48, .34, 1.49, .90),
        (-2.58, 1.55, .31, 1.54, .93),
        (-2.03, 1.52, .29, 1.53, .94),
        (-1.39, 1.48, .29, 1.35, .98),
        (-.65, 1.47, .28, 1.25, .99),
        (.20, 1.48, .27, 1.21, .96),
        (1.11, 1.51, .27, 1.18, .90),
        (1.78, 1.54, .27, 1.07, .78),
        (2.42, 1.58, .28, .94, .71),
        (2.92, 1.52, .30, .80, .62),
        (3.27, 1.42, .34, .67, .57),
        (3.47, 1.28, .40, .62, .55)
    ]
    def lerp_profile(z):
        for k in range(len(sections)-1):
            a,b=sections[k],sections[k+1]
            if a[0] <= z <= b[0]:
                t=(z-a[0])/(b[0]-a[0]); t2=t*t; t3=t2*t
                p=sections[max(0,k-1)]
                q=sections[min(len(sections)-1,k+2)]
                values=[]
                for axis in range(1,len(a)):
                    v0=(b[axis]-p[axis])/(b[0]-p[0])
                    v1=(q[axis]-a[axis])/(q[0]-a[0])
                    span=b[0]-a[0]
                    values.append((2*t3-3*t2+1)*a[axis]+(t3-2*t2+t)*v0*span+
                                  (-2*t3+3*t2)*b[axis]+(t3-t2)*v1*span)
                return values
        return list(sections[0][1:] if z<sections[0][0] else sections[-1][1:])
    def gauss(z,mu,sigma):
        return math.exp(-((z-mu)/sigma)**2)
    def surface(z,t):
        """Top skin at normalized lateral position -1..1."""
        w,bottom,crown,edge=lerp_profile(z)
        u=abs(t)
        front=gauss(z,2.26,.97)
        rear=gauss(z,-2.72,1.06)
        # Three independent rails: center hood / strongly OUTWARD fender crest /
        # formed downward outer cheek. Peaks sit around 76% of half track.
        top_rail = crown + (.30*front+.145*rear)*gauss(u,.77,.145)
        # Low recessed bonnet immediately inboard of the fender peaks.
        top_rail -= (.11*front+.025*rear)*gauss(u,.36,.23)
        # Smooth shoulder face flows down toward the vertical wheel-housing side.
        fall=(max(0.0,(u-.81)/.19))**1.45
        top_rail=(1-fall)*top_rail+fall*edge
        return (w*t,top_rail,z)
    def side_surface(z,y,side=1):
        w,low,high,edge=lerp_profile(z)
        # Broad continuous side walls with a shaped lower concave rocker.
        undercut=.13*gauss(z,-.1,1.62)*gauss(y,.53,.20)
        return (side*(w-undercut),y,z)
    # Polygon rails run from right sill, across the upper hood to left sill,
    # then back underneath. All longitudinal sections use matching quad rings.
    top_t=[1,.96,.90,.83,.77,.69,.56,.42,.28,.14,0,
           -.14,-.28,-.42,-.56,-.69,-.77,-.83,-.90,-.96,-1]
    bottom_t=[-1,-.91,-.75,-.50,-.25,0,.25,.50,.75,.91,1]
    count=100
    ring_size=len(top_t)+len(bottom_t)
    verts=[]
    for i in range(count+1):
        z=sections[0][0]+(sections[-1][0]-sections[0][0])*i/count
        w,low,high,side_height=lerp_profile(z)
        for t in top_t:
            verts.append(surface(z,t))
        for t in bottom_t:
            # A tapered chine leads to a reasonably flat, shallow underfloor.
            u=abs(t)
            y=low+(side_height-low)*(u**3)
            x=t*w*(1-.05*(1-u))
            verts.append((x,y,z))
    quads=[]
    for k in range(count):
        z=(sections[0][0]+(sections[-1][0]-sections[0][0])*(k+.5)/count)
        for j in range(ring_size):
            # Under the greenhouse the central upper skin is an aperture
            # bounded by its body sills, not a square hole across the full deck.
            if -1.35<z<1.22 and 5<=j<=14:
                continue
            a=k*ring_size+j
            quads.append((a,k*ring_size+(j+1)%ring_size,
                          (k+1)*ring_size+(j+1)%ring_size,(k+1)*ring_size+j))
    quads.append(tuple(reversed(range(ring_size))))
    quads.append(tuple(count*ring_size+j for j in range(ring_size)))
    shell=mesh('Shrike original sculpted automotive body',verts,quads,body)
    for face in shell.data.polygons:
        face.use_smooth=True

    # High-level surface helpers: mesh ribbons follow the underlying skin.
    def skin_patch(name, rows, material, lift=.015):
        # rows: [(z, [lateral fractions])], each row with same fraction count.
        pp=[]; ff=[]
        cols=len(rows[0][1])
        for z,fractions in rows:
            for t in fractions:
                x,y,_=surface(z,t)
                pp.append((x,y+lift,z))
        for j in range(len(rows)-1):
            for k in range(cols-1):
                a=j*cols+k
                ff.append((a,a+1,a+1+cols,a+cols))
        o=mesh(name,pp,ff,material)
        for face in o.data.polygons:face.use_smooth=True
        return o
    def side_plate(name, side, coords, material):
        # side silhouette coords (z, y), surface-mounted at natural shoulder.
        pts=[side_surface(z,y,side) for z,y in coords]
        pts=[(x+side*.016,y,z) for x,y,z in pts]
        return panel(name,pts,material)
    def spline_points(ctrl,steps=5):
        out=[]
        for i in range(len(ctrl)-1):
            a=ctrl[max(0,i-1)]
            b=ctrl[i]
            c=ctrl[i+1]
            d=ctrl[min(len(ctrl)-1,i+2)]
            for k in range(steps):
                t=k/steps;t2=t*t;t3=t2*t
                out.append(tuple(.5*((2*b[j])+(-a[j]+c[j])*t+
                                  (2*a[j]-5*b[j]+4*c[j]-d[j])*t2+
                                  (-a[j]+3*b[j]-3*c[j]+d[j])*t3)
                                 for j in range(len(b))))
        return out+[ctrl[-1]]
    def surface_stroke(name,ctrl,width,material):
        # Sleek body-inset stripe; unlike separate pipes this is a formed quad ribbon.
        path=spline_points(ctrl,5)
        pp=[];faces=[]
        for z,t in path:
            for shift in [-width/2,width/2]:
                x,y,zz=surface(z,max(-.99,min(.99,t+shift)))
                pp.append((x,y+.017,zz))
        for i in range(len(path)-1):
            k=2*i
            faces.append((k,k+1,k+3,k+2))
        return mesh(name,pp,faces,material)
    def side_stroke(name, side, ctrl, thickness, material):
        path=spline_points(ctrl,5)
        pp=[];faces=[]
        for z,y in path:
            for off in [-thickness/2,thickness/2]:
                x,yy,zz=side_surface(z,y+off,side)
                pp.append((x+side*.026,yy,zz))
        for k in range(len(path)-1):
            i=2*k;faces.append((i,i+1,i+3,i+2))
        return mesh(name,pp,faces,material)

    # Long, panoramic greenhouse. The outer root of every glass cross-section
    # nests into the side shoulders, while the roof rises out of the windscreen.
    canopy=[(-1.60,.63,1.24,1.38),(-1.32,.72,1.26,1.55),
            (-.90,.79,1.24,1.66),(-.35,.81,1.22,1.72),
            (.30,.80,1.20,1.68),(.88,.70,1.15,1.52),
            (1.34,.55,1.13,1.30),(1.51,.43,1.13,1.17)]
    pp=[];ff=[]
    for z,w,base,high in canopy:
        for t in [-1,-.8,-.55,-.28,0,.28,.55,.8,1]:
            roof=base+(high-base)*max(0,1-t*t)**.63
            pp.append((w*t,roof,z))
    for i in range(len(canopy)-1):
        for j in range(8):
            k=i*9+j;ff.append((k,k+1,k+10,k+9))
    roof=mesh('vehicle_glass_shrike_panoramic_glazing',pp,ff,glass)
    for face in roof.data.polygons:face.use_smooth=True
    # Glazed side leaves are integrated within the A and C sail.
    for side in (-1,1):
        window=[(side*.52,1.18,1.33),(side*.72,1.42,.75),
                (side*.78,1.56,-.24),(side*.73,1.45,-1.17),
                (side*.62,1.26,-1.53),(side*.81,1.18,-.88),
                (side*.84,1.12,.25)]
        panel('vehicle_glass_shrike_side',window,glass)
        # A and C pillars grow out of the actual painted fender shoulders.
        pipe('Shrike flush A pillar',(side*.51,1.15,1.38),
             (side*.73,1.51,.76),.028,carbon,10)
        pipe('Shrike swept C pillar',(side*.76,1.53,-.95),
             (side*.91,1.31,-1.64),.038,body,10)
    # Interior remains functional in the driving camera.
    box('Shrike integrated two-seat tub',(0,.81,-.23),(1.30,.12,2.24),carbon,.06)
    for side in [-1,1]:
        box('Shrike sport seat',(side*.35,1.06,-.37),(.47,.33,.63),rubber,.05)
        box('Shrike sculpted seat back',(side*.35,1.37,-.75),(.43,.57,.14),carbon,.045)
        box('Shrike orange seat harness',(side*.35,1.37,-.65),(.055,.40,.025),accent,.006)
    # Common yoke pivot is required by the existing Godot fleet controls.
    before=set(bpy.context.scene.objects)
    for side in (-1,1):
        pipe('Shrike yoke grip',(side*.19,1.12,.87),
             (side*.19,1.34,.88),.032,steel,12)
    pipe('Shrike yoke grip bridge',(-.19,1.26,.88),(.19,1.26,.88),
         .026,carbon,12)
    rig('Kestrel_Yoke',since(before),(0,1.26,.88))

    # Reference's dark bonnet recess between two forged, OUTWARD flared fenders.
    skin_patch('Shrike central black bonnet',
               [(z,[-w,-w*.50,0,w*.50,w]) for z,w in
                [(1.59,.40),(1.85,.40),(2.25,.38),(2.72,.35),
                 (3.07,.31),(3.29,.25)]],carbon,.021)
    for side in (-1,1):
        # Flush headlamp pocket and luminous blade follow the outer brow.
        skin_patch('Shrike inset narrow headlight',[
            (2.41,[side*.72,side*.83]),(2.62,[side*.72,side*.86]),
            (2.86,[side*.70,side*.84]),(3.03,[side*.68,side*.77])],
            carbon,.027)
        surface_stroke('Shrike optic blade',[
            (2.46,side*.79),(2.66,side*.79),(2.88,side*.77)],
            .020,glow)
        # Orange front corners and dark side-facing intakes are fitted
        # flush to the widened fender body, never floating as exterior fins.
        skin_patch('Shrike orange front fender inlay',[
            (2.86,[side*.87,side*.98]),(3.08,[side*.84,side*.99]),
            (3.28,[side*.86,side*.99])],accent,.024)
        side_plate('Shrike front side induction recess',side,
                   [(3.18,.59),(2.87,.78),(2.62,.89),(2.72,.64)],
                   carbon)
        # Long inset C-channel with a deliberate upward sweep at the rear.
        path=[(1.94,.63),(1.12,.60),(.33,.64),(-.35,.82),
              (-.98,1.14),(-1.51,1.41),(-1.83,1.50)]
        side_stroke('Shrike recessed C-channel',side,path,.155,carbon)
        side_stroke('Shrike orange C-channel core',side,path,.088,accent)
        side_plate('Shrike aft swept extractor',side,
                   [(-2.16,1.29),(-2.80,1.27),(-3.18,1.04),
                    (-2.62,1.03)],carbon)
        side_stroke('Shrike extractor lip',side,
                    [(-2.18,1.32),(-2.80,1.29),(-3.17,1.07)],
                    .039,accent)
        # Low-profile magnetics beneath the enclosed outer haunch.
        for z,x in [(2.02,1.07),(-2.48,1.14)]:
            ring('Shrike embedded repulsor field',(side*x,.25,z),
                 .23,.028,glow)
            pipe('Shrike recessed induction cell',
                 (side*x,.30,z),(side*x,.41,z),.18,carbon,24)

    # Real front fascia depth and lower intake behind a rounded blunt bumper.
    panel('Shrike black front intake',[
        (-.99,.46,3.484),(.99,.46,3.484),
        (.96,.71,3.481),(-.96,.71,3.481)],carbon)
    pipe('Shrike intake upper rim',(-.98,.73,3.495),
         (.98,.73,3.495),.026,steel,12)
    pipe('Shrike blue lower intake blade',(-.86,.48,3.502),
         (.86,.48,3.502),.018,glow,12)
    for x in [-.68,-.34,0,.34,.68]:
        pipe('Shrike recessed grille support',(x,.47,3.51),
             (x,.69,3.51),.010,steel,8)

    # Raised but nearly level rear deck and inset cooling pack.
    skin_patch('Shrike recessed dorsal cooling deck',[
        (-3.31,[-.39,-.22,0,.22,.39]),
        (-3.04,[-.39,-.22,0,.22,.39]),
        (-2.79,[-.35,-.19,0,.19,.35]),
        (-2.55,[-.30,-.15,0,.15,.30])],carbon,.026)
    for side in (-1,1):
        surface_stroke('Shrike rear dorsal accent',[
            (-3.25,side*.50),(-2.99,side*.54),
            (-2.74,side*.55)],.034,accent)

    # Tail face: continuous red lamp, two dark diffuser / vector ducts.
    red=mat('shrike_tail_lamp',(.95,.06,.025),.12,.25,1.5)
    panel('Shrike recessed rear aperture',[
        (-1.12,.69,-3.574),(1.12,.69,-3.574),
        (1.16,1.24,-3.574),(-1.16,1.24,-3.574)],carbon)
    pipe('Shrike continuous rear light bar',
         (-1.15,1.26,-3.586),(1.15,1.26,-3.586),
         .037,red,16)
    for side in (-1,1):
        pipe('Shrike rear vector duct', (side*.64,.80,-3.39),
             (side*.64,.80,-3.61),.21,steel,22)
        pipe('Shrike dark nozzle throat',(side*.64,.80,-3.54),
             (side*.64,.80,-3.63),.15,carbon,22)
        pipe('Shrike blue exhaust inner',(side*.64,.80,-3.61),
             (side*.64,.80,-3.65),.085,glow,18)
        pipe('Shrike tail outer accent',(side*1.30,.77,-3.57),
             (side*1.24,1.13,-3.57),.026,accent,10)
    # Five unexposed rigged nozzle nodes are required by SceneForge animation.
    for i in range(5):
        before=set(bpy.context.scene.objects)
        x=(i-2)*.24
        pipe('Shrike hidden tail vector marker',(x,.73,-3.38),
             (x,.73,-3.41),.009,carbon,8)
        rig('Kestrel_Tail_%d'%i,since(before),(x,.73,-3.38))
