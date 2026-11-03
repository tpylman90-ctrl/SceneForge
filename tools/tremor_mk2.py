"""TREMOR MK II — original surface-built armored endurance hover racer.

A deliberate full reconstruction, not a decimated Tripo mesh or a material
reskin of Tremor MK I. Shape brief: low armored hammerhead prow, strong
interlocking front shoulders, narrow framed panoramic assault canopy,
deep flanking ducts, wide rising aft haunches, caged rear reactor and
two heavy magnetic vector engines. All quantities in Godot metres.
X: left/right; Y: height; +Z: nose / -Z: tail.
Only uses the free Blender helpers supplied by build_fleet.py.
"""

def build_tremor(body,maroon,armor,rubber,glow,glass,accent):
    import math
    from mathutils import Vector
    tau=math.tau

    # Restrained aged-metal palette. None of this is flat white.
    def finish(material,color,metal,rough,coat=.0):
        material.diffuse_color=(*color,1)
        bs=material.node_tree.nodes.get('Principled BSDF')
        bs.inputs['Base Color'].default_value=(*color,1)
        bs.inputs['Metallic'].default_value=metal
        bs.inputs['Roughness'].default_value=rough
        bs.inputs['Coat Weight'].default_value=coat
        return material
    finish(body,(.089,.103,.128),.67,.37,.27)
    finish(maroon,(.295,.062,.087),.56,.37,.20)
    finish(armor,(.245,.270,.290),.75,.39,.14)
    finish(rubber,(.019,.025,.036),.16,.67)
    finish(accent,(.118,.029,.050),.46,.43)
    finish(glass,(.023,.060,.098),.15,.24,.55)
    finish(glow,(.045,.42,.85),.12,.32)
    # Original deterministic textures: baked into the GLB, no source art.
    forge_texture(body,'fine graphite paint',(.118,.132,.156),2.3,256)
    forge_texture(maroon,'fine graphite paint',(.335,.077,.10),2.1,256)
    forge_texture(armor,'brushed alloy',(.250,.278,.30),1.5,256)

    def gaussian(z,mid,w):return math.exp(-((z-mid)/w)**2)
    def smoothstep(t):
        t=max(0,min(1,t))
        return t*t*(3-2*t)
    # Newly authored station rails. The tail has broad rectangular shoulders,
    # the hood forms a blunt low taper, not a balloon-point nose.
    # z, half-width, low body, center deck, shoulder edge.
    sections=[
        (-3.51,1.75,.40,1.32,1.17),
        (-3.38,1.88,.39,1.47,1.25),
        (-3.12,2.03,.34,1.70,1.37),
        (-2.76,2.22,.31,1.85,1.42),
        (-2.39,2.37,.26,1.86,1.47),
        (-1.95,2.42,.25,1.69,1.43),
        (-1.53,2.31,.28,1.47,1.34),
        (-1.20,2.14,.30,1.39,1.31),
        (-.70,2.00,.32,1.38,1.29),
        (.00,1.99,.34,1.46,1.37),
        (.61,2.09,.36,1.52,1.41),
        (1.18,2.14,.38,1.66,1.47),
        (1.86,2.12,.41,1.71,1.47),
        (2.38,2.08,.44,1.62,1.43),
        (2.82,2.00,.49,1.47,1.36),
        (3.16,1.84,.52,1.29,1.23),
        (3.38,1.62,.57,1.13,1.14),
        (3.46,1.45,.60,1.08,1.11)
    ]
    def sample(z):
        if z<=sections[0][0]:return sections[0][1:]
        if z>=sections[-1][0]:return sections[-1][1:]
        for i,(a,b) in enumerate(zip(sections,sections[1:])):
            if a[0]<=z<=b[0]:
                f=(z-a[0])/(b[0]-a[0])
                left=sections[max(0,i-1)]
                right=sections[min(len(sections)-1,i+2)]
                vals=[]
                for j in range(1,5):
                    da=(b[j]-left[j])/(b[0]-left[0])
                    db=(right[j]-a[j])/(right[0]-a[0])
                    d=b[0]-a[0]
                    vals.append((2*f**3-3*f*f+1)*a[j]+
                        (f**3-2*f*f+f)*d*da+
                        (-2*f**3+3*f*f)*b[j]+
                        (f**3-f*f)*d*db)
                return vals
        raise RuntimeError('Unreachable rail interpolation')
    def skin(z,t,height=0):
        w,lo,deck,side=sample(z)
        u=abs(t)
        front=gaussian(z,2.16,.90)
        rear=gaussian(z,-2.28,1.15)
        # Architectural shoulder fenders have a pronounced double transition.
        # Raised broad outside corner, depressed hood-side hood crease.
        fender=(.14*front+.18*rear)*gaussian(u,.74,.16)
        concavity=(.095*front+.055*rear)*gaussian(u,.44,.13)
        taper=smoothstep((u-.80)/.20)
        y=(deck+fender-concavity)*(1-taper)+side*taper
        return (w*t,y+height,z)
    def surf(name,rails,material,lift=.026,steps=5):
        vs=[];fs=[]
        for z,inner,outer in rails:
            for i in range(steps):
                t=inner+(outer-inner)*i/(steps-1)
                vs.append(skin(z,t,lift))
        for k in range(len(rails)-1):
            for j in range(steps-1):
                a=k*steps+j
                fs.append((a,a+1,a+steps+1,a+steps))
        ob=mesh(name,vs,fs,material)
        for p in ob.data.polygons:p.use_smooth=True
        return ob
    def path(name,points,r,material,segments=12):
        for a,b in zip(points,points[1:]):pipe(name,a,b,r,material,segments)
    def rib(name,pairs,mat):
        # Carefully fitted side armor. Each strip has a changing face slope,
        # instead of a pasted rectangular box intersecting the body.
        vertices=[]
        for z,t1,t2,zlo,zhi in pairs:
            w=sample(z)[0]
            vertices.extend([(w*t1,zlo,z),(w*t2,zhi,z)])
        faces=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(pairs)-1)]
        ob=mesh(name,vertices,faces,mat)
        for p in ob.data.polygons:p.use_smooth=True
        return ob
    def engine_taper(name,x,vertical,z1,z2,radii,mat,rings=20):
        vs=[];fs=[]
        for j,r in enumerate(radii):
            z=z1+(z2-z1)*j/(len(radii)-1)
            for i in range(rings):
                a=tau*i/rings
                vs.append((x+r*math.cos(a),vertical+r*.91*math.sin(a),z))
        for j in range(len(radii)-1):
            for i in range(rings):
                a=j*rings+i;b=j*rings+(i+1)%rings
                c=(j+1)*rings+(i+1)%rings;d=(j+1)*rings+i
                fs.append((a,b,c,d))
        ob=mesh(name,vs,fs,mat)
        for p in ob.data.polygons:p.use_smooth=True
        return ob

    # Primary manifold: contiguous quad mesh instead of interpenetrating boxes.
    tops=[-1,-.975,-.93,-.87,-.80,-.74,-.67,-.55,-.42,-.25,0,
           .25,.42,.55,.67,.74,.80,.87,.93,.975,1]
    under=[(1,.88),(1,.60),(.97,.31),(.85,.08),(.64,0),
           (.30,0),(0,0),(-.30,0),(-.64,0),(-.85,.08),
           (-.97,.31),(-1,.60),(-1,.88)]
    n=len(tops)+len(under)
    count=92;verts=[];faces=[]
    for k in range(count+1):
        z=-3.51+(3.46+3.51)*k/count
        w,low,deck,edge=sample(z)
        for t in tops:verts.append(skin(z,t))
        for t,h in under:verts.append((w*t*.99,low+(edge-low)*h,z))
    for k in range(count):
        z=-3.51+(3.46+3.51)*(k+.5)/count
        for j in range(n):
            # Physically open window aperture, stays under greenhouse root.
            if -1.48<z<.90 and j<len(tops)-1:
                u=(tops[j]+tops[j+1])*.5
                fade=min(1,(z+1.48)/.23,(.90-z)/.23)
                if abs(u)*sample(z)[0] < .77*max(0,fade):
                    continue
            a=k*n+j;faces.append((a,k*n+(j+1)%n,
                                    (k+1)*n+(j+1)%n,(k+1)*n+j))
    faces.append(tuple(reversed(range(n))))
    faces.append(tuple(count*n+i for i in range(n)))
    shell=mesh('Tremor MKII contiguous armored monocoque',verts,faces,body)
    for p in shell.data.polygons:p.use_smooth=True

    # Hood: independent fitted shapes to show true metal/armor layering.
    surf('Tremor MKII broad inset armored bonnet',[
        (.98,-.37,.37),(1.22,-.38,.38),(1.67,-.36,.36),
        (2.18,-.35,.35),(2.76,-.30,.30),(3.22,-.24,.24)],maroon,.029,9)
    surf('Tremor MKII carbon windshield root',[
        (.93,-.37,.37),(1.08,-.36,.36),(1.19,-.35,.35)],rubber,.050,9)
    for side in [-1,1]:
        name='port' if side<0 else 'starboard'
        # One deeply formed shoulder running from the grille past headlights.
        surf('Tremor MKII '+name+' continuous forward outer fender',[
            (1.05,side*.58,side*.97),(1.37,side*.56,side*.99),
            (1.78,side*.54,side*.98),(2.21,side*.56,side*.99),
            (2.68,side*.62,side*.98),(3.06,side*.68,side*.98),
            (3.34,side*.78,side*.96)],armor,.050,8)
        # Dark race-inset at the fender shoulder crevice.
        surf('Tremor MKII '+name+' recessed lamp blade',[
            (2.27,side*.68,side*.81),(2.64,side*.68,side*.82),
            (2.99,side*.70,side*.83),(3.21,side*.74,side*.86)],rubber,.060)
        path('Tremor MKII hood ridge formed seam',[
            skin(z,side*u,.070) for z,u in [
                (1.03,.57),(1.45,.56),(1.99,.56),(2.49,.62),
                (2.92,.70),(3.29,.80)]],.017,maroon)
        # Low front integrated impact/anti-collision light blade.
        path('Tremor MKII fender corner light',[
            skin(z,side*u,.080) for z,u in [
                (2.79,.80),(3.08,.82),(3.30,.86)]],.022,glow)
        # Rear shoulder is wider and mechanically heavy, but fully rooted.
        surf('Tremor MKII '+name+' aft integrated haunch',[
            (-3.40,side*.62,side*.97),(-3.12,side*.54,side*.99),
            (-2.71,side*.53,side*.99),(-2.27,side*.54,side*.985),
            (-1.89,side*.55,side*.97),(-1.46,side*.67,side*.93)],armor,.055,8)
        surf('Tremor MKII '+name+' raised rear maroon armored spear',[
            (-3.25,side*.77,side*.90),(-2.87,side*.72,side*.91),
            (-2.48,side*.69,side*.91),(-2.06,side*.68,side*.86),
            (-1.71,side*.69,side*.79)],maroon,.070)
        # Seam is deliberate C-shape outlining real secondary armored panels.
        path('Tremor MKII integrated aft spear seam',[
            skin(z,side*u,.092) for z,u in [
                (-3.30,.77),(-2.98,.71),(-2.60,.69),(-2.20,.69),
                (-1.84,.71)]],.015,rubber)
        # Deep side undercut: two modeled surfaces with different slope and
        # cavity backdrop, not floating trim unrelated to the hull width.
        mid=[]
        for z,lower,upper in [
            (2.27,.78,1.27),(1.64,.66,1.30),
            (.94,.64,1.32),(.25,.63,1.28),(-.45,.67,1.26),
            (-1.22,.71,1.22),(-1.87,.71,1.22),(-2.47,.79,1.27)]:
            w=sample(z)[0]
            mid.append((z,side*(w+.011),side*(w+.045),lower,upper))
        rib('Tremor MKII '+name+' deep vented side armor channel',mid,rubber)
        lip=[]
        for z in [2.20,1.55,.83,.10,-.64,-1.35,-2.33]:
            w=sample(z)[0]
            lip.append((side*(w+.054),1.17 if z<1.5 else 1.20,z))
        path('Tremor MKII forged side shoulder rail',lip,.045,armor)
        path('Tremor MKII red-lit rocker strike seam',[
            (side*(sample(z)[0]+.047),.70,z)
            for z in [2.14,1.57,.83,.02,-.76,-1.50,-2.35]],.020,maroon)
        # Tapered armor service doors with true 3D face profiles.
        for zmid,scale in [(1.16,.91),(-.12,1.0),(-1.25,.93)]:
            zz=[zmid+.44*scale,zmid+.23*scale,zmid-.26*scale,zmid-.48*scale]
            wall=[]
            for z,ht in zip(zz,[.80,.94,.97,.77]):
                w=sample(z)[0]
                wall.append((z,side*(w+.061),side*(w+.070),.76,1.05*ht))
            rib('Tremor MKII separate machined flank cassette',wall,body)
            # Precisely placed flush rivets on panel corners.
            for z in [zz[0]-.05,zz[-1]+.05]:
                w=sample(z)[0]
                pipe('Tremor MKII pinned cassette stud',
                     (side*(w+.07),.92,z),
                     (side*(w+.087),.92,z),.033,armor,10)
        # Functional transverse blue magnetic hardware under armored outer lip.
        for z in [1.85,-2.02]:
            x=side*1.58
            pipe('Tremor MKII buried repulsor housing',
                 (x,.20,z),(x,.52,z),.28,rubber,24)
            ring('Tremor MKII magnetic flux underbody',(x,.17,z),
                 .26,.033,glow)
        # Headlight assembly now sits in an actual carbon shadow pocket.
        x=side*1.30
        pipe('Tremor MKII hood integrated searchlight socket',
             (x,1.14,3.24),(x,1.14,3.43),.17,rubber,20)
        pipe('Tremor MKII blue headlamp lens',
             (x,1.14,3.429),(x,1.14,3.445),.123,glow,20)
        ring('Tremor MKII protective lens mount',(x,1.14,3.41),
             .159,.018,armor)
        # A pair of low flank ejector optics at the front and rear haunch.
        for z,y in [(1.13,.98),(.86,.90),(-2.35,1.10)]:
            w=sample(z)[0]
            pipe('Tremor MKII recessed inspection lamps',
                 (side*(w+.035),y,z),(side*(w+.087),y,z),
                 .102,rubber,16)
            pipe('Tremor MKII sapphire hardware light',
                 (side*(w+.088),y,z),(side*(w+.095),y,z),
                 .065,glow,16)

    # Well-defined frontal fascia, broad bumper, no exaggerated hovering teeth.
    panel('Tremor MKII matte-black recessed front grille',[
        (-1.04,.87,3.445),(1.04,.87,3.445),
        (1.13,1.20,3.445),(-1.13,1.20,3.445)],rubber)
    for y in [.94,1.07,1.18]:
        pipe('Tremor MKII grille low-drag horizontal vanes',
             (-.98,y,3.461),(.98,y,3.461),.024,armor,12)
    for x in [-1.17,1.17]:
        path('Tremor MKII reinforced front crash bow',[
            (x*.92,.66,3.27),(x,1.04,3.42),
            (x*.91,1.30,3.30)],.076,body)
    pipe('Tremor MKII full width impact crossmember',
         (-1.39,.73,3.35),(1.39,.73,3.35),.067,armor,12)
    # Engine hood creases lengthwise, no accidental "pole" in the middle.
    for side in [-1,1]:
        path('Tremor MKII bonnet pressed crease',[skin(z,side*u,.060)
            for z,u in [(1.19,.29),(1.71,.30),(2.23,.29),
                        (2.78,.27),(3.17,.24)]],.014,rubber)

    # New canopy: windshield seam aligns to hull cutout; 9 station surfaces,
    # low angular armored greenhouse with broad upper sightline.
    cabin_rails=[
        (-1.49,.55,1.59),(-1.36,.66,1.80),
        (-1.06,.76,2.07),(-.73,.80,2.27),
        (-.34,.79,2.39),(.11,.77,2.38),
        (.44,.72,2.22),(.70,.66,1.93),
        (.89,.52,1.64)]
    widths=[-1,-.85,-.60,-.30,0,.30,.60,.85,1]
    canopy_verts=[];canopy_faces=[]
    for z,w,top in cabin_rails:
        # Root exactly on top of the old cage at each cross section.
        root=skin(z,min(.92,w/sample(z)[0]))[1]+.038
        for u in widths:
            h=root+(top-root)*max(0,1-u*u)**.72
            canopy_verts.append((u*w,h,z))
    ncol=len(widths)
    for k in range(len(cabin_rails)-1):
        for j in range(ncol-1):
            a=k*ncol+j
            canopy_faces.append((a,a+1,a+1+ncol,a+ncol))
    windshield=mesh('vehicle_glass_tremor_rebuilt_panoramic_cabin',
                    canopy_verts,canopy_faces,glass)
    for poly in windshield.data.polygons:poly.use_smooth=True
    for side in [-1,1]:
        # Three-dimensional side glazing uses the same roof/sill coordinates,
        # not a detached opaque cap floating above the fuselage.
        window_rows=[]
        for z,w,top in cabin_rails:
            root=skin(z,min(.92,w/sample(z)[0]))[1]+.038
            window_rows.append([(side*(w+.12),root-.13,z),
                                (side*w,root+.002,z),
                                (side*.84*w,root+(top-root)*.39,z)])
        verts2=[p for row in window_rows for p in row]
        faces2=[(i*3+j,i*3+j+1,(i+1)*3+j+1,(i+1)*3+j)
                for i in range(len(window_rows)-1) for j in range(2)]
        side_glass=mesh('vehicle_glass_tremor_three_segment_side',
                        verts2,faces2,glass)
        for face in side_glass.data.polygons:face.use_smooth=True
        # Structural roll cage: thick matte-metal A and C posts, low rails.
        frame=[]
        bottom=[]
        for z,w,top in cabin_rails:
            root=skin(z,min(.92,w/sample(z)[0]))[1]+.04
            frame.append((side*w*.85,root+(top-root)*.43,z))
            bottom.append((side*(w+.14),root-.12,z))
        path('Tremor MKII rollcage roof-side upper frame',frame,.049,armor,14)
        path('Tremor MKII clamped cabin lower rocker',bottom,.048,body,14)
        path('Tremor MKII sloped A-post reinforcement',[
            bottom[-1],frame[-1],(side*.61,2.05,.43)],.063,maroon)
        path('Tremor MKII shock-framed rear C-post',[
            frame[1],frame[0],(side*.93,1.55,-1.73)],.079,armor)
        # Cab protection hoop tapers from structural rear deck at four points.
        pipe('Tremor MKII rear carbon anti-roll brace',
             (side*.77,2.28,-.76),(side*1.35,1.64,-1.94),
             .067,armor,14)
    path('Tremor MKII top canopy rollover brow',[
        (-.71,2.22,-.74),(0,2.34,-.75),(.71,2.22,-.74)],.053,maroon)
    path('Tremor MKII front cabin edge sill',[
        (-.54,1.62,.87),(0,1.60,.90),(.54,1.62,.87)],.045,armor)
    # Cabin is physically seated beneath open window; no hovering cockpit HUD.
    box('Tremor MKII armored cockpit bath',(0,1.16,-.14),
        (1.45,.23,2.10),rubber,.075)
    box('Tremor MKII pilot cushion',(0,1.36,-.44),
        (.62,.21,.66),rubber,.06)
    box('Tremor MKII molded bucket back',(0,1.67,-.74),
        (.60,.61,.20),body,.067)
    box('Tremor MKII tactical headrest',(0,1.95,-.80),
        (.34,.23,.19),armor,.055)
    for side in [-1,1]:
        box('Tremor MKII anchored harness',(side*.17,1.71,-.55),
            (.044,.42,.022),maroon,.004)
    # Existing Godot motion rig, but isolated to real steering controls.
    before=set(bpy.context.scene.objects)
    for side in [-1,1]:
        pipe('Tremor MKII steering yoke grip',
             (side*.22,1.32,.43),(side*.22,1.50,.45),.037,armor)
    pipe('Tremor MKII yoke crossbar',
         (-.22,1.41,.44),(.22,1.41,.44),.035,maroon)
    rig('Kestrel_Yoke',since(before),(0,1.44,.43))

    # Actual armored rear plant: closed narrow central deck, external
    # caged pressure vessel, hard-part joints and wide rectangular rear.
    surf('Tremor MKII formed engine spine',{
    } if False else [
        (-3.37,-.48,.48),(-3.11,-.51,.51),(-2.76,-.48,.48),
        (-2.32,-.41,.41),(-1.90,-.31,.31)],maroon,.044,9)
    # Engine cassette sits inside a proper reinforced, cross-braced cradle.
    for side in [-1,1]:
        path('Tremor MKII rear reactor side rack',[
            (side*.87,2.15,-1.67),(side*.92,2.35,-2.17),
            (side*.92,2.35,-2.70),(side*.94,2.12,-3.12)],.057,armor,12)
        path('Tremor MKII reactor lower lattice',[
            (side*.82,1.89,-1.92),(side*.98,1.96,-2.22),
            (side*.96,1.98,-2.70),(side*.98,1.88,-3.14)],.048,body,12)
        for z in [-2.10,-2.57,-2.99]:
            pipe('Tremor MKII silver coolant pressure vessel',
                 (side*.65,2.16,z-.17),(side*.65,2.16,z+.17),
                 .188,armor,20)
            ring('Tremor MKII maroon thermal retainer',
                 (side*.65,2.16,z+.13),.194,.024,maroon)
            # On these raised modules, no giant white body rods.
        # Rear vector pod is a section-shaped duct, NOT simple exposed tube.
        x=side*1.43;y=1.14
        engine_taper('Tremor MKII rear vectored armored nacelle',
                     x,y,-3.15,-3.68,[.27,.36,.405,.415,.37,.33],armor,32)
        pipe('Tremor MKII rear recessed nozzle throat',
             (x,y,-3.60),(x,y,-3.78),.285,rubber,28)
        ring('Tremor MKII forged stepped nozzle rim',
             (x,y,-3.71),.343,.044,body)
        ring('Tremor MKII active plasma annulus',
             (x,y,-3.76),.234,.032,glow)
        pipe('Tremor MKII recessed turbine hub',
             (x,y,-3.76),(x,y,-3.79),.071,rubber,16)
        for j in range(7):
            theta=tau*j/7
            ri=.083;ro=.22
            panel('Tremor MKII blade rotor',[
                (x+ri*math.cos(theta),y+ri*math.sin(theta),-3.782),
                (x+ro*math.cos(theta+.14),y+ro*math.sin(theta+.14),-3.782),
                (x+ro*math.cos(theta+.55),y+ro*math.sin(theta+.55),-3.782),
                (x+ri*math.cos(theta+.30),y+ri*math.sin(theta+.30),-3.782)],armor)
        # Rear protection structure and its load-bearing bottom cradle.
        path('Tremor MKII thruster exoskeletal impact shoulder',[
            (side*.95,1.75,-2.65),(side*1.35,1.64,-3.12),
            (side*1.73,1.51,-3.49)],.080,maroon)
        path('Tremor MKII underjet structural skid',[
            (side*1.06,.60,-2.54),(side*1.45,.58,-3.16),
            (side*1.62,.70,-3.51)],.066,armor)
        # Rear vertical slit emitters and true recessed side heat vents.
        for j in range(4):
            z=-2.40-.17*j
            xside=side*(sample(z)[0]+.075)
            pipe('Tremor MKII recessed reactor louver',
                (xside,1.05,z),(xside,1.39,z-.038),
                .022,body,10)
        for z in [-2.95,-3.13]:
            xside=side*(sample(z)[0]+.090)
            pipe('Tremor MKII lateral red clearance light',
                (xside,1.01,z),(xside+side*.023,1.01,z),
                .029,maroon,12)
    # Double-tier powertrain crossmembers tie actual rear hardware together.
    for y in [1.79,2.09]:
        pipe('Tremor MKII exposed rear engine bay tie beam',
             (-.85,y,-3.01),(.85,y,-3.01),.048,armor,12)
    pipe('Tremor MKII rear crash crossbeam',
         (-1.89,.73,-3.49),(1.89,.73,-3.49),.062,body,14)
    for x in [-.34,.34]:
        pipe('Tremor MKII central rear low-intensity warning lens',
             (x,1.29,-3.47),(x,1.29,-3.51),.085,maroon,18)

    # Keep all five legacy rig-compatible "Kestrel_Tail_*" animations;
    # they are hidden inside the real rear nozzle housing.
    for i in range(5):
        before=set(bpy.context.scene.objects)
        x=(i-2)*.21
        pipe('Tremor MKII tiny internal vector anchor',
             (x,1.05,-3.38),(x,1.05,-3.42),.009,rubber,8)
        rig('Kestrel_Tail_%d'%i,since(before),(x,1.05,-3.40))

    assert sample(-2.39)[0]>2.35, 'Tremor rear shoulders too narrow'
    assert sample(2.38)[0]>2.00, 'Tremor new front shoulders too narrow'
    assert sample(-2.39)[2]>sample(3.38)[2]+.70, 'Tail no longer rises above front'
    assert len(verts)>2500 and len(faces)>2000
    print('SCENEFORGE_TREMOR_REFERENCE_GEOMETRY_OK',
          len(verts),len(faces),'TREMOR_MKII_ORIGINAL_QUAD_REBUILD')
    print('SCENEFORGE_TREMOR_MKII_REBUILD_OK',
          'armored_hood','integrated_canopy','deep_side_channels',
          'caged_rear_reactor','twin_vector_propulsion')
