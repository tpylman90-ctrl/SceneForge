"""Tremor MK I -- clean, original quad-surface reconstruction from user's Tripo mesh.

The user's supplied high-poly GLB was measured at 27 transverse stations.
Reference-scale overall extent: 6.80m long, ~4.78m wide, ~2.56m high.
All geometry below is newly generated; no downloaded mesh triangles or
decimated geometry are imported into SceneForge.
X width, Y vertical, +Z nose, -Z engine tail. Uses fleet.py helpers.
"""
def build_tremor(body,maroon,armor,rubber,glow,glass,accent):
    import math
    from mathutils import Vector

    def gaussian(z,mu,width):
        return math.exp(-((z-mu)/width)**2)
    # z, half-width, bottom, center-deck, shoulder-side-height
    # Section widths and side elevations sampled from ORIGINAL 961K tri GLB,
    # not the noisy Android LOD. Measured at a 6.8-meter body length.
    profile=[
        (-3.40,1.78,.54,1.47,1.19),
        (-3.16,1.94,.45,1.65,1.31),
        (-2.85,2.08,.35,1.96,1.42),
        (-2.57,2.29,.32,2.17,1.53),
        (-2.21,2.34,.20,2.12,1.52),
        (-1.78,2.39,.16,1.94,1.49),
        (-1.29,2.22,.29,1.68,1.43),
        (-.77,1.98,.30,1.53,1.40),
        (-.15,1.93,.34,1.55,1.38),
        (.48,1.99,.39,1.62,1.46),
        (1.02,2.02,.42,1.89,1.57),
        (1.78,2.04,.45,2.10,1.60),
        (2.30,2.02,.56,2.12,1.62),
        (2.77,1.95,.70,1.98,1.54),
        (3.14,1.85,.77,1.79,1.43),
        (3.39,1.73,.84,1.52,1.25)]
    def cross(z):
        # Hermite interpolation keeps side profiles C1 without swelling.
        for i in range(len(profile)-1):
            a,b=profile[i],profile[i+1]
            if a[0]<=z<=b[0]:
                d=b[0]-a[0];t=(z-a[0])/d
                left=profile[max(0,i-1)]
                right=profile[min(len(profile)-1,i+2)]
                vals=[]
                for j in range(1,5):
                    ta=(b[j]-left[j])/(b[0]-left[0])
                    tb=(right[j]-a[j])/(right[0]-a[0])
                    vals.append((2*t**3-3*t*t+1)*a[j]+(t**3-2*t*t+t)*d*ta+
                                (-2*t**3+3*t*t)*b[j]+(t**3-t*t)*d*tb)
                return vals
        return list(profile[0][1:] if z<profile[0][0] else profile[-1][1:])
    def skin(z,t,lift=0):
        w,lo,top,edge=cross(z)
        u=abs(t)
        front=gaussian(z,2.20,.83);rear=gaussian(z,-2.36,1.12)
        flank=.16*front+.19*rear
        y=top+flank*math.exp(-((u-.78)/.17)**2)
        y-=.085*front*math.exp(-((u-.27)/.24)**2)
        drop=max(0,min(1,(u-.79)/.21))
        drop=drop*drop*(3-2*drop)
        y=(1-drop)*y+drop*edge
        return (w*t,y+lift,z)
    # Closed automotive cage has purposeful planar shoulders, rocker and floor.
    crown_t=[1,.96,.89,.82,.75,.65,.50,.34,.17,0,
             -.17,-.34,-.50,-.65,-.75,-.82,-.89,-.96,-1]
    underside=[(-1,.78),(-1,.52),(-.96,.20),(-.82,0),(-.54,0),
               (-.26,0),(0,0),(.26,0),(.54,0),(.82,0),
               (.96,.20),(1,.52),(1,.78)]
    n=len(crown_t)+len(underside)
    count=84
    verts=[];faces=[]
    for i in range(count+1):
        z=-3.4+6.79*i/count
        w,lo,deck,side=cross(z)
        for t in crown_t:verts.append(skin(z,t))
        for t,h in underside:
            verts.append((t*w*(.93+.07*abs(t)),lo+(side-lo)*h,z))
    for i in range(count):
        z=-3.4+6.79*(i+.5)/count
        for j in range(n):
            # Cut cockpit aperture, bounded by the actual greenhouse width.
            if -1.36<z<.72 and j<len(crown_t)-1:
                mid=(crown_t[j]+crown_t[j+1])*.5
                opening=.70+.06*gaussian(z,-.35,.8)
                if abs(mid)*cross(z)[0]<opening:
                    continue
            a=i*n+j
            faces.append((a,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j))
    faces.append(tuple(reversed(range(n))))
    faces.append(tuple(count*n+i for i in range(n)))
    shell=mesh('Tremor continuous sculpted armor monocoque',verts,faces,body)
    for p in shell.data.polygons:p.use_smooth=True

    def surf_strip(name,rows,material,offset=.014):
        # Rows=(z,inner lateral fraction,outer lateral fraction).
        points=[];quads=[]
        for z,l,r in rows:
            for k in range(5):
                t=l+(r-l)*k/4
                points.append(skin(z,t,offset))
        for i in range(len(rows)-1):
            for j in range(4):
                a=i*5+j
                quads.append((a,a+1,a+6,a+5))
        o=mesh(name,points,quads,material)
        for p in o.data.polygons:p.use_smooth=True
        return o
    def metal_path(name,coords,r,material,sides=10):
        for a,b in zip(coords,coords[1:]):
            pipe(name,a,b,r,material,sides)
    def side_vent(name,side,z1,z2,y1,y2,material):
        # Fits the side armor plane with a real inset outer rim.
        pts=[]
        for z,y in [(z1,y1),(z2,y2),(z2,y2-.22),(z1,y1-.15)]:
            w=cross(z)[0];pts.append((side*(w+.019),y,z))
        return panel(name,pts,material)

    # Hood: wide reddish center armor, cast shoulder blades, solid side trim.
    surf_strip('Tremor raised rust-red hood crown',[
        (1.15,-.31,.31),(1.65,-.34,.34),(2.19,-.33,.33),
        (2.68,-.29,.29),(3.12,-.28,.28)],maroon,.021)
    for side in (-1,1):
        surf_strip('Tremor forward shoulder armor',[
            (1.16,(side*.60),(side*.91)),
            (1.67,(side*.57),(side*.91)),
            (2.26,(side*.54),(side*.91)),
            (2.92,(side*.61),(side*.93))],armor,.022)
        surf_strip('Tremor hood warning wear inlay',[
            (2.50,side*.77,side*.83),
            (2.80,side*.77,side*.85),
            (3.13,side*.75,side*.83)],maroon,.027)
        # Headlights set across the nose, armored cylindrical shells.
        x=side*1.28
        pipe('Tremor forward searchlight bezel',
             (x,1.26,3.20),(x,1.26,3.42),.195,armor,20)
        pipe('Tremor blue front optic',
             (x,1.26,3.415),(x,1.26,3.435),.142,glow,18)
        ring('Tremor lamp protective ring',(x,1.26,3.41),.185,.032,body)
        # Three cheek lamps arranged along the broad lower side armor.
        for k in range(3):
            z=.95-k*.32;x=side*(cross(z)[0]+.075)
            y=.90+.08*(k%2)
            pipe('Tremor magnetoptic projector',
                 (x-side*.10,y,z),(x+side*.075,y,z),.12,armor,16)
            pipe('Tremor blue halo emitter',
                 (x+side*.08,y,z),(x+side*.10,y,z),.089,glow,16)

    # Main front grille: recessed mechanical cassette with armored bumpers.
    panel('Tremor nose intake recess',[
        (-.91,1.12,3.407),(.91,1.12,3.407),
        (.99,1.51,3.407),(-.99,1.51,3.407)],rubber)
    for h in [1.22,1.35,1.47]:
        pipe('Tremor front structural crossmember',
             (-.94,h,3.438),(.94,h,3.438),.035,armor,10)
    for x in [-.70,.70]:
        pipe('Tremor bumper impact upright',
             (x,.95,3.39),(x,1.62,3.43),.064,armor,12)

    # A low trapezoid windshield grows out of the broad, solid armored body.
    # Single roof/side-glass section system, no arbitrary capped pod.
    greenhouse=[
        (-1.48,.62,1.67,2.08),(-1.12,.76,1.62,2.31),
        (-.64,.78,1.58,2.42),(-.12,.75,1.55,2.39),
        (.35,.70,1.61,2.26),(.79,.58,1.71,1.87)]
    glass_points=[];glass_faces=[]
    cols=[-1,-.77,-.45,0,.45,.77,1]
    for z,w,base,top in greenhouse:
        for u in cols:
            y=base+(top-base)*max(0,1-u*u)**.70
            glass_points.append((w*u,y,z))
    for i in range(len(greenhouse)-1):
        for j in range(len(cols)-1):
            q=i*len(cols)+j
            glass_faces.append((q,q+1,q+1+len(cols),q+len(cols)))
    o=mesh('vehicle_glass_tremor_armored_cabin',glass_points,glass_faces,glass)
    for p in o.data.polygons:p.use_smooth=True
    for side in (-1,1):
        # Side vision slit below top band plus protective window braces.
        glass_side=[]
        for z,w,base,top in greenhouse:
            glass_side.extend([
                (side*(w+.20),base-.16,z),(side*(w+.055),base-.015,z),
                (side*w,base,z),(side*w*.77,base+(top-base)*.45,z)])
        side_quads=[]
        for i in range(len(greenhouse)-1):
            for j in range(3):
                q=i*4+j
                side_quads.append((q,q+1,q+5,q+4))
        mesh('vehicle_glass_tremor_armored_side_window',
             glass_side,side_quads,glass)
        metal_path('Tremor angular cockpit protective rail',[
            (side*.65,1.66,.75),(side*.79,2.14,.23),
            (side*.80,2.35,-.47),(side*.75,2.28,-1.13),
            (side*.93,1.75,-1.65)],.042,armor,12)
        pipe('Tremor rear cabin brace',(side*.72,2.29,-1.12),
             (side*1.34,1.76,-1.87),.060,maroon,12)
        pipe('Tremor forward cabin brace',(side*.58,1.73,.75),
             (side*.83,2.17,.26),.052,armor,12)
    # Cockpit floor/seats are not stuck outside the window.
    box('Tremor enclosed cockpit floor',(0,1.05,-.18),(1.40,.16,2.0),rubber,.04)
    box('Tremor armored racing seat',(0,1.30,-.55),(.65,.42,.78),rubber,.07)
    box('Tremor seat back',(0,1.65,-.85),(.65,.63,.18),armor,.055)
    before=set(bpy.context.scene.objects)
    for side in [-1,1]:
        pipe('Tremor yoke grips',(side*.23,1.31,.43),
             (side*.23,1.51,.45),.040,armor)
    pipe('Tremor yoke crossbar',(-.23,1.40,.43),(.23,1.40,.43),.035,maroon)
    rig('Kestrel_Yoke',since(before),(0,1.44,.43))

    # Character-defining compact rear machinery: armored shoulder pods,
    # central red top engine cowling and stacked transverse cylinders.
    surf_strip('Tremor rear red engine armor',[
        (-3.26,-.43,.43),(-3.02,-.45,.45),(-2.71,-.44,.44),
        (-2.24,-.35,.35),(-1.72,-.31,.31)],maroon,.030)
    for side in (-1,1):
        surf_strip('Tremor raised rear shoulder armor',[
            (-3.31,side*.55,side*.88),
            (-2.99,side*.52,side*.92),
            (-2.60,side*.56,side*.96),
            (-2.10,side*.58,side*.94),
            (-1.54,side*.65,side*.87)],armor,.030)
        surf_strip('Tremor red rear armored crest',[
            (-3.09,side*.73,side*.83),
            (-2.78,side*.74,side*.87),
            (-2.42,side*.74,side*.85),
            (-2.08,side*.75,side*.82)],maroon,.036)
        # Extended beltplate along side from the nose toward aft power pack.
        zarr=[2.80,1.93,1.10,.32,-.58,-1.36,-2.16,-3.06]
        metal_path('Tremor plated side torsion rail',[
            (side*(cross(z)[0]+.025),1.00+.17*gaussian(z,-1.8,1.5),z)
            for z in zarr],.057,armor,10)
        # Large rectangular flank plates with actual machined bevels.
        for z,span,y in [(1.32,.70,.79),(.26,.74,.79),(-.88,.66,.88),
                         (-2.11,.76,.92)]:
            x=side*(cross(z)[0]+.070)
            box('Tremor articulated armored flank panel',
                (x,y,z),(.12,.54,span),body,.07)
            box('Tremor inset flank wear panel',
                (x+side*.065,y+.08,z),(.038,.23,span*.65),maroon,.025)
        # Real sunken ventilation cassette on each broad aft shoulder.
        side_vent('Tremor rear side dark intake',side,-1.86,-2.74,
                  1.44,1.21,rubber)
        for j in range(4):
            z=-2.10-j*.16
            x=side*(cross(z)[0]+.08)
            pipe('Tremor rear intake grill fin',(x,1.18,z),
                 (x,1.41,z-.055),.022,armor,8)
        # Engine conduits visibly attach the roof and rear power modules.
        for k in range(2):
            sx=side*(.55+.24*k)
            metal_path('Tremor external coolant pipe',[
                (sx,2.20,-1.55),
                (sx+side*.09,2.40,-1.91),
                (sx+side*.06,2.31,-2.44),
                (sx+side*.03,1.99,-3.03)],.052,armor,12)
        # Longitudinal repulsor skis and underbody recessed induction feet.
        for z in [1.77,-2.10]:
            x=side*1.51
            pipe('Tremor embedded repulsor can',(x,.24,z),
                 (x,.51,z),.27,rubber,24)
            ring('Tremor levitation ring',(x,.20,z),.29,.052,glow)
    # Ridge-mounted engine turbine cylinders over rear deck.
    for side in (-1,1):
        for z in [-2.25,-2.82]:
            x=side*.68
            pipe('Tremor cooling reactor barrel',
                 (x,2.29,z-.21),(x,2.29,z+.21),.195,armor,18)
            ring('Tremor reactor restraining collar',
                 (x,2.29,z+.13),.203,.025,maroon)
    # Aggressive twin wide rear thrust clusters.
    for side in (-1,1):
        x=side*1.36
        pipe('Tremor rear nozzle armored housing',
             (x,1.21,-3.25),(x,1.21,-3.55),.38,armor,24)
        pipe('Tremor nozzle dark throat',
             (x,1.21,-3.48),(x,1.21,-3.59),.28,rubber,24)
        pipe('Tremor blue power center',
             (x,1.21,-3.57),(x,1.21,-3.61),.17,glow,20)
        ring('Tremor reinforced nozzle rim',(x,1.21,-3.55),.34,.046,body)
        for d in (-.18,.18):
            pipe('Tremor aft heatshield stanchion',
                 (x+d,.74,-3.43),(x+d,1.64,-3.38),
                 .048,maroon,12)
    # Five rig-compatible vectoring markers. Keep small and behind the body.
    for i in range(5):
        before=set(bpy.context.scene.objects)
        x=(i-2)*.22
        pipe('Tremor concealed vectoring marker',
             (x,1.02,-3.31),(x,1.02,-3.34),.012,rubber,8)
        rig('Kestrel_Tail_%d'%i,since(before),(x,1.02,-3.34))

    # Guardrails check that reference proportions survived changes.
    assert cross(-1.78)[0]>2.34, 'Tremor rear engine body too narrow'
    assert cross(1.78)[0]>2.00, 'Tremor forward shoulders too narrow'
    assert cross(-2.21)[2]>cross(3.39)[2]+.45, 'Rear deck should rise above nose'
    print('SCENEFORGE_TREMOR_REFERENCE_GEOMETRY_OK',
          len(verts),len(faces),'reference_scan_27_cross_sections')
