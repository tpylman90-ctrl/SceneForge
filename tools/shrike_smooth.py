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
    body.diffuse_color = (.29, .34, .39, 1)
    shader = body.node_tree.nodes['Principled BSDF']
    shader.inputs['Base Color'].default_value = body.diffuse_color
    shader.inputs['Metallic'].default_value = .24
    shader.inputs['Roughness'].default_value = .44
    shader.inputs['Coat Weight'].default_value = .18

    # Controllable independent plan, sill, crown and edge rails. These profiles
    # intentionally hold width beside the canopy and a wide squared-off rear.
    # Columns: longitudinal Z, half-width, lower edge, hood/deck, side height.
    # Blueprint cross-section stations: Z, half-width, lower sill,
    # low central hood/deck, outer shoulder height.
    # Front +Z: green fenders; center: cyan greenhouse; rear -Z:
    # orange haunches around a separate recessed engine deck.
    sections = [
        (-3.55, 1.30, .40, 1.13, .81),
        (-3.37, 1.43, .37, 1.19, .85),
        (-3.06, 1.51, .33, 1.24, .89),
        (-2.58, 1.56, .31, 1.30, .92),
        (-2.03, 1.54, .29, 1.34, .97),
        (-1.39, 1.51, .29, 1.30, .99),
        (-.65, 1.52, .28, 1.24, .98),
        (.20, 1.53, .27, 1.22, .96),
        (1.11, 1.56, .27, 1.19, .92),
        (1.78, 1.61, .27, 1.08, .80),
        (2.42, 1.63, .28, .94, .72),
        (2.92, 1.57, .30, .81, .63),
        (3.27, 1.45, .35, .68, .57),
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
        """Upper monocoque skin: recessed center, outboard fender, formed cheek."""
        w,bottom,crown,edge=lerp_profile(z)
        u=abs(t)
        front=gauss(z,2.28,.93)
        rear=gauss(z,-2.57,1.03)
        # Two true reference-defined outer fender volumes, not oval bubbles.
        shoulder=(.255*front+.235*rear)*gauss(u,.79,.145)
        channel=(.085*front+.065*rear)*gauss(u,.32,.21)
        top_rail=crown+shoulder-channel
        # A controlled sloping cheek outside the fender's sharp raised rail.
        blend=max(0.0,min(1.0,(u-.84)/.16))
        blend=blend*blend*(3-2*blend)
        top_rail=(1-blend)*top_rail+blend*edge
        return (w*t,top_rail,z)
    def side_surface(z,y,side=1):
        """Project a detail onto the OUTER cheek of the actual body skin.

        The old analytical side approximation was independent of the body
        surface and caused C-channel accents and air intakes to float.
        """
        w,low,crown,edge=lerp_profile(z)
        outboard_crest=surface(z,side*.79)[1]
        if y>edge:
            actual_y=min(y,outboard_crest-.004)
            lo,hi=.79,1.0
            for _ in range(18):
                mid=(lo+hi)*.5
                if surface(z,side*mid)[1]>actual_y:
                    lo=mid
                else:
                    hi=mid
            u=(lo+hi)*.5
            return (side*w*u,actual_y,z)
        # At and below the shoulder, the beltline uses genuine vertical
        # side rails. Lower undercut is reserved for the rocker.
        lower=max(0,min(1,(edge-y)/max(.01,edge-low)))
        return (side*w*(1-.025*lower),y,z)
    # Polygon rails run from right sill, across the upper hood to left sill,
    # then back underneath. All longitudinal sections use matching quad rings.
    top_t=[1,.96,.90,.83,.77,.69,.56,.42,.28,.14,0,
           -.14,-.28,-.42,-.56,-.69,-.77,-.83,-.90,-.96,-1]
    # Structural sidewall / rocker / underfloor rails. The former tube
    # had no explicit side body, so every view read like a balloon.
    lower_rails=[(-1,.89),(-1,.72),(-.99,.54),(-.96,.31),
                 (-.86,.06),(-.58,0),(-.29,0),(0,0),
                 (.29,0),(.58,0),(.86,.06),(.96,.31),
                 (.99,.54),(1,.72),(1,.89)]
    count=100
    ring_size=len(top_t)+len(lower_rails)
    verts=[]
    for i in range(count+1):
        z=sections[0][0]+(sections[-1][0]-sections[0][0])*i/count
        w,low,high,side_height=lerp_profile(z)
        for t in top_t:
            verts.append(surface(z,t))
        for t,level in lower_rails:
            # Side beltline is a modeled volume, rather than a missing wall.
            y=low+(side_height-low)*level
            x=t*w*(1-.045*(1-abs(t)))
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
        """Recessed faceted vent with a fitted outer lip and sloped inner wall."""
        cy=sum(y for z,y in coords)/len(coords)
        cz=sum(z for z,y in coords)/len(coords)
        outer=[]
        inner=[]
        for z,y in coords:
            x,yy,zz=side_surface(z,y,side)
            outer.append((x+side*.020,yy,zz))
            zi=cz+(z-cz)*.81
            yi=cy+(y-cy)*.79
            xi,yi,zi=side_surface(zi,yi,side)
            inner.append((xi-side*.032,yi,zi))
        p=outer+inner
        n=len(coords)
        quads=[(i,(i+1)%n,n+(i+1)%n,n+i) for i in range(n)]
        quads.append(tuple(range(n,2*n)))
        o=mesh(name,p,quads,material)
        return o
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
    # Roof roots are sampled from the actual sculpted body (no fixed,
    # arbitrary 1.24m glass base that floats above the hood).
    canopy_shape=[(-1.67,.62,1.34),(-1.40,.73,1.53),
                  (-.94,.79,1.65),(-.35,.81,1.72),
                  (.27,.80,1.69),(.89,.72,1.55),
                  (1.31,.57,1.33),(1.57,.43,1.17)]
    canopy=[]
    for z,w,high in canopy_shape:
        base=surface(z,min(.99,w/lerp_profile(z)[0]))[1]+.018
        canopy.append((z,w,base,max(base+.025,high)))
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
    # Full, curved, QUAD side glazing (no giant nonplanar n-gons).
    # Every longitudinal row shares a roof-seam vertex with the main glass;
    # the lower edge is tucked into the body's molded upper side shoulder.
    # This eliminates black triangle gaps behind the cockpit in Godot.
    for side in (-1,1):
        side_verts=[];side_quads=[]
        for z,w,base,high in canopy:
            # Glass crown blends down to the joined roof/side transition.
            crown_at_edge=base+(high-base)*max(0,1-.80*.80)**.63
            for x,y in [
                (side*(w+.27),base-.155),   # hidden beneath the body shoulder
                (side*(w+.07),base-.025),   # side glass lower rim
                (side*w,base),              # roof edge, same as roof band
                (side*w*.80,crown_at_edge)]:
                side_verts.append((x,y,z))
        for i in range(len(canopy)-1):
            for col in range(3):
                q=i*4+col
                side_quads.append((q,q+1,q+5,q+4))
        glazing=mesh('vehicle_glass_shrike_wrap_side',side_verts,side_quads,glass)
        for face in glazing.data.polygons:
            face.use_smooth=True
        # Narrow, body-colored formed glazing rails; no exposed roll cage.
        for rail_u in [0,1]:
            pp=[]
            for z,w,base,high in canopy:
                if rail_u==0:
                    pp.extend([(side*(w+.27),base-.158,z),
                               (side*(w+.22),base-.133,z)])
                else:
                    pp.extend([(side*w*.8,
                                base+(high-base)*max(0,1-.8*.8)**.63+.004,z),
                               (side*w*.86,
                                base+(high-base)*max(0,1-.86*.86)**.63+.009,z)])
            ff=[(2*i,2*i+1,2*i+3,2*i+2)
                for i in range(len(canopy)-1)]
            mesh('Shrike flush canopy perimeter rail',pp,ff,body)
        # Substantial but flush A/C-pillar quarter panels conceal the ends
        # of the windows and visually marry them to the silver monocoque.
        panel('Shrike front body A-sail',[
            (side*.80,1.06,1.48),(side*.91,1.05,1.25),
            (side*.86,1.34,.92),(side*.70,1.48,.93)],body)
        panel('Shrike integrated rear C-sail',[
            (side*.75,1.40,-1.01),(side*.88,1.28,-1.30),
            (side*1.19,1.18,-1.79),(side*.90,1.30,-1.58)],body)
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
        side_stroke('Shrike recessed C-channel',side,path,.30,carbon)
        side_stroke('Shrike orange C-channel core',side,path,.22,accent)
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

    # Sculpted fascia: a dark *recessed trapezoid* rather than a rectangular
    # radiator bumper floating forward of the monocoque. A narrow lower blade
    # runs the full opening, with restrained internal blades.
    nose_z=sections[-1][0]+.012
    fascia=mesh('Shrike formed front intake cavity',[
        (-.98,.51,nose_z),(.98,.51,nose_z),
        (.91,.76,nose_z),(.77,.84,nose_z),
        (-.77,.84,nose_z),(-.91,.76,nose_z)],
        [(0,1,2,3,4,5)],carbon)
    for a,b in [
        ((-.97,.50,nose_z+.012),(.97,.50,nose_z+.012)),
        ((-.91,.76,nose_z+.014),(-.77,.84,nose_z+.014)),
        ((.91,.76,nose_z+.014),(.77,.84,nose_z+.014))]:
        pipe('Shrike flush machined grille frame',a,b,.014,steel,10)
    for y,half in [(.585,.72),(.685,.77)]:
        pipe('Shrike horizontal air splitter',
             (-half,y,nose_z+.020),(half,y,nose_z+.020),
             .012,carbon,10)
    for side in (-1,1):
        pipe('Shrike blue intake eye',(side*.55,.535,nose_z+.028),
             (side*.78,.535,nose_z+.028),.016,glow,10)
    # Magenta engine-deck blueprint: an elongated black engine bay centered
    # between the two substantial orange rear fenders, ending just behind
    # the canopy rather than starting only at the tail bumper.
    skin_patch('Shrike recessed engine deck black insert',[
        (-3.36,[-.39,-.23,0,.23,.39]),
        (-3.13,[-.39,-.23,0,.23,.39]),
        (-2.85,[-.41,-.24,0,.24,.41]),
        (-2.50,[-.41,-.24,0,.24,.41]),
        (-2.12,[-.40,-.22,0,.22,.40]),
        (-1.82,[-.37,-.20,0,.20,.37])],carbon,.012)
    # Dedicated sculpted twin engine scoops rather than a flat painted box.
    for side in (-1,1):
        skin_patch('Shrike recessed aft engine induction',[
            (-3.18,[side*.09,side*.27]),
            (-2.94,[side*.09,side*.27]),
            (-2.75,[side*.10,side*.28])],steel,.027)
    for side in (-1,1):
        surface_stroke('Shrike rear dorsal accent',[
            (-3.25,side*.50),(-2.99,side*.54),
            (-2.74,side*.55)],.034,accent)

    # Tail face: continuous red lamp, two dark diffuser / vector ducts.
    red=mat('shrike_tail_lamp',(.95,.06,.025),.12,.25,1.5)
    panel('Shrike recessed rear aperture',[
        (-1.12,.69,-3.574),(1.12,.69,-3.574),
        (1.16,1.24,-3.574),(-1.16,1.24,-3.574)],carbon)
    rear_lamp=pipe('Shrike continuous rear light bar',
         (-1.15,1.26,-3.586),(1.15,1.26,-3.586),
         .037,red,16)
    # A separate red material is not in the main material join set.
    # Name it as a fleet node so kestrel_feedback.gd retains the mesh.
    rear_lamp.name='Kestrel_ShrikeRedTailLight'
    for side in (-1,1):
        pipe('Shrike rear vector duct', (side*.64,.80,-3.39),
             (side*.64,.80,-3.61),.21,steel,22)
        pipe('Shrike dark nozzle throat',(side*.64,.80,-3.54),
             (side*.64,.80,-3.63),.15,carbon,22)
        pipe('Shrike blue exhaust inner',(side*.64,.80,-3.61),
             (side*.64,.80,-3.65),.085,glow,18)
        pipe('Shrike tail outer accent',(side*1.30,.77,-3.57),
             (side*1.24,1.13,-3.57),.026,accent,10)
    # Reference-geometry acceptance gates: catch a regression to tubular
    # proportions before publishing the next Android or viewer build.
    assert lerp_profile(0)[0] > 1.43, 'Shrike cockpit waist too narrow'
    assert lerp_profile(-2.58)[0] > 1.50, 'Shrike rear haunches too narrow'
    assert surface(2.42,.77)[1]-surface(2.42,.38)[1] > .15, (
        'Shrike outboard fender crest missing')
    assert surface(-2.55,.79)[1]-surface(-2.55,0)[1] > .15, (
        'Shrike rear fender and recessed engine deck must be distinct')
    assert abs(surface(-.35,.79)[0]) > .75, 'Shrike cabin shoulder pinched'
    assert canopy[3][2] < canopy[3][3], 'Shrike canopy roof cannot be buried'
    assert len(quads) > 2000, 'Shrike continuous quad cage incomplete'
    print('SCENEFORGE_SHRIKE_REFERENCE_BODY_OK',len(quads))
    # Five unexposed rigged nozzle nodes are required by SceneForge animation.
    for i in range(5):
        before=set(bpy.context.scene.objects)
        x=(i-2)*.24
        pipe('Shrike hidden tail vector marker',(x,.73,-3.38),
             (x,.73,-3.41),.009,carbon,8)
        rig('Kestrel_Tail_%d'%i,since(before),(x,.73,-3.38))
