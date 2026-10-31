"""Shrike MK I: reference-built automotive surface and production detail pass.

Godot design coordinates: X=width, Y=height, +Z=front.
Geometry is original and generated in Blender. Four-view reference is the
source of the proportions; no third-party mesh, texture or paid assets.
The principal shell uses continuous quad strips across authored hard-surface
rails, not the previous elliptical tube or bolt-on fender plates.
"""
def build_shrike(body, accent, carbon, steel, rubber, glow, glass, purple):
    import math

    # Shrike livery: satin silver body, neon-lime architectural features,
    # deep-purple accent recesses. Independent from Kestrel's orange.
    body.diffuse_color = (.31, .34, .38, 1)
    shader = body.node_tree.nodes['Principled BSDF']
    shader.inputs['Base Color'].default_value = body.diffuse_color
    shader.inputs['Metallic'].default_value = .24
    shader.inputs['Roughness'].default_value = .44
    shader.inputs['Coat Weight'].default_value = .24
    # Make actual Blender export materials match the color-approved concept.
    lime=(.57,.91,.022,1)
    accent.diffuse_color=lime
    accent_shader=accent.node_tree.nodes['Principled BSDF']
    accent_shader.inputs['Base Color'].default_value=lime
    accent_shader.inputs['Metallic'].default_value=.32
    accent_shader.inputs['Roughness'].default_value=.30
    midnight=(.105,.021,.185,1)
    purple.diffuse_color=midnight
    purple_shader=purple.node_tree.nodes['Principled BSDF']
    purple_shader.inputs['Base Color'].default_value=midnight
    purple_shader.inputs['Roughness'].default_value=.33
    glass.diffuse_color=(.012,.023,.044,1)
    glass.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=glass.diffuse_color
    glass.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.20

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
        shoulder=(.305*front+.24*rear)*gauss(u,.79,.145)
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
            # Greenhouse aperture follows the CYAN cockpit's actual plan
            # outline. The old constant 5..14 deletion cut far beyond the
            # glass sides and created visible black triangular gaps.
            if -1.35<z<1.22 and j<len(top_t)-1:
                plan=[(-1.67,.62),(-1.40,.73),(-.94,.79),
                      (-.35,.81),(.27,.80),(.89,.72),
                      (1.31,.57),(1.57,.43)]
                aperture_width=plan[0][1]
                for q in range(len(plan)-1):
                    za,wa=plan[q]
                    zb,wb=plan[q+1]
                    if za<=z<=zb:
                        aperture_width=wa+(wb-wa)*(z-za)/(zb-za)
                        break
                t_mid=(top_t[j]+top_t[j+1])*.5
                if abs(t_mid)*lerp_profile(z)[0]<aperture_width+.055:
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

    # UNIFIED GREENHOUSE. The previous independent roof panels, side n-gons,
    # body-colored sail triangles and separated roof rails produced visible
    # glass gaps, prongs and floating white shards. This single parameterized
    # canopy uses one row of design stations shared by windshield, roof,
    # left/right glass and lower perimeter trim.
    # Front +Z; rear -Z. Roof is low and elongated in side elevation.
    canopy_shape=[
        (-1.66,.62,1.34),(-1.37,.70,1.51),
        (-.96,.77,1.61),(-.48,.79,1.68),
        (.22,.77,1.66),(.76,.71,1.54),
        (1.18,.59,1.35),(1.53,.44,1.18)]
    canopy=[]
    for z,w,high in canopy_shape:
        shell_at_root=surface(z,min(.97,w/lerp_profile(z)[0]))[1]
        base=shell_at_root+.018
        canopy.append((z,w,base,max(high,base+.022)))
    def greenhouse_height(base,high,u):
        return base+(high-base)*max(0,1-u*u)**.70
    # Curved greenhouse crown extends continuously to side seams.
    roof_cols=[-1,-.86,-.65,-.38,0,.38,.65,.86,1]
    roof_vertices=[]
    for z,w,base,high in canopy:
        for u in roof_cols:
            roof_vertices.append((w*u,greenhouse_height(base,high,u),z))
    roof_faces=[]
    for r in range(len(canopy)-1):
        for c in range(len(roof_cols)-1):
            a=r*len(roof_cols)+c
            roof_faces.append((a,a+1,a+len(roof_cols)+1,a+len(roof_cols)))
    canopy_glass=mesh('vehicle_glass_shrike_one_piece_canopy',
                      roof_vertices,roof_faces,glass)
    for p in canopy_glass.data.polygons: p.use_smooth=True

    # Two contiguous side windows, stitched to the canopy crown. Each station
    # has an *exactly shared* roof-edge coordinate and a body-sampled sill.
    for side in (-1,1):
        side_vertices=[]
        for z,w,base,high in canopy:
            full_width=lerp_profile(z)[0]
            side_root_u=min(.96,(w+.20)/full_width)
            sill=surface(z,side*side_root_u)
            side_vertices.extend([
                (sill[0],sill[1]-.020,z),     # buried glass lip
                (side*(w+.075),base-.026,z),
                (side*w,base,z),              # exact roof glass edge
                (side*w*.86,greenhouse_height(base,high,.86),z)])
        side_quads=[]
        for row in range(len(canopy)-1):
            for col in range(3):
                a=row*4+col
                side_quads.append((a,a+1,a+5,a+4))
        window=mesh('vehicle_glass_shrike_flush_side',
                    side_vertices,side_quads,glass)
        for p in window.data.polygons: p.use_smooth=True

        # Narrow, flush gasket at the actual sill. No raised add-on A-pillar.
        rubber_vertices=[]
        for z,w,base,high in canopy:
            unit=min(.97,(w+.20)/lerp_profile(z)[0])
            x,y,_=surface(z,side*unit)
            rubber_vertices.extend([
                (x+side*.008,y+.004,z),
                (x-side*.032,y+.007,z)])
        gasket_faces=[(2*j,2*j+1,2*j+3,2*j+2)
                      for j in range(len(canopy)-1)]
        mesh('Shrike integrated glass base weather seal',
             rubber_vertices,gasket_faces,rubber)

        # One narrow, integrated C-pillar slopes rearward into the molded
        # haunch rather than projecting into the air as a triangulated flag.
        root_z=-1.63
        tail_z=-2.23
        root_w=canopy[0][1]
        root_y=canopy[0][3]-.035
        shoulder_x=lerp_profile(tail_z)[0]*.73
        shoulder_y=surface(tail_z,side*.73)[1]
        pillar_points=[
            (side*root_w*.92,root_y,root_z),
            (side*root_w*.75,root_y-.015,root_z),
            (side*shoulder_x*.78,shoulder_y+.014,tail_z),
            (side*shoulder_x,shoulder_y+.003,tail_z)]
        pillar=mesh('Shrike molded rear sail',
                    pillar_points,[(0,1,2,3)],body)
        for p in pillar.data.polygons:p.use_smooth=True

    # The windshield is the FRONT section of this continuous canopy.
    # No detached roof cap, separate windshield panel or external HUD pieces.
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
    skin_patch('Shrike deep purple central bonnet',
               [(z,[-w,-w*.50,0,w*.50,w]) for z,w in
                [(1.61,.39),(1.88,.39),(2.27,.37),(2.69,.33),
                 (3.05,.28),(3.26,.23)]],purple,.014)
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
        skin_patch('Shrike formed lime outer brow',[
            (2.57,[side*.79,side*.85]),(2.82,[side*.80,side*.87]),
            (3.04,[side*.77,side*.84]),(3.27,[side*.73,side*.78])],accent,.019)
        side_plate('Shrike front side induction recess',side,
                   [(3.18,.59),(2.87,.78),(2.62,.89),(2.72,.64)],
                   carbon)
        # Long inset C-channel with a deliberate upward sweep at the rear.
        path=[(1.94,.63),(1.12,.60),(.33,.64),(-.35,.82),
              (-.98,1.14),(-1.51,1.41),(-1.83,1.50)]
        side_stroke('Shrike deep purple C-channel recess',side,path,.30,purple)
        side_stroke('Shrike lime C-channel core',side,path,.21,accent)
        side_plate('Shrike aft swept extractor',side,
                   [(-2.16,1.29),(-2.80,1.27),(-3.18,1.04),
                    (-2.62,1.03)],carbon)
        side_stroke('Shrike purple extractor lip',side,
                    [(-2.18,1.32),(-2.80,1.29),(-3.17,1.07)],
                    .039,purple)
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
    skin_patch('Shrike purple engine deck recess',[
        (-3.36,[-.39,-.23,0,.23,.39]),
        (-3.13,[-.39,-.23,0,.23,.39]),
        (-2.85,[-.41,-.24,0,.24,.41]),
        (-2.50,[-.41,-.24,0,.24,.41]),
        (-2.12,[-.40,-.22,0,.22,.40]),
        (-1.82,[-.37,-.20,0,.20,.37])],purple,.012)
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
    assert lerp_profile(.20)[0] > 1.50, 'Shrike top plan body pinched'
    assert len(lower_rails) >= 13, 'Shrike formed rocker rails missing'
    assert len(quads) > 2000, 'Shrike continuous quad cage incomplete'
    print('SCENEFORGE_SHRIKE_REFERENCE_BODY_OK',len(quads))
    # Five unexposed rigged nozzle nodes are required by SceneForge animation.
    for i in range(5):
        before=set(bpy.context.scene.objects)
        x=(i-2)*.24
        pipe('Shrike hidden tail vector marker',(x,.73,-3.38),
             (x,.73,-3.41),.009,carbon,8)
        rig('Kestrel_Tail_%d'%i,since(before),(x,.73,-3.38))
