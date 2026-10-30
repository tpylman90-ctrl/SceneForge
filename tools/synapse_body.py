"""Synapse hull with a fitted polar-glass canopy; interior and hardware remain pending."""
def build_synapse_body(material, glass, accent, carbon):
    # Godot axes: X spans the hull, Y is height, and +Z is forward.
    profile = [
        (-4.15,1.08,-.36,-.12,.29,.64),
        (-3.78,1.32,-.40,-.16,.39,.88),
        (-3.12,1.50,-.43,-.19,.46,1.02),
        (-2.35,1.48,-.44,-.18,.55,1.18),
        (-1.35,1.34,-.45,-.18,.58,1.24),
        (-.20,1.31,-.43,-.17,.55,1.20),
        (.85,1.23,-.36,-.14,.49,1.08),
        (1.80,1.30,-.26,-.08,.42,.96),
        (2.65,1.38,-.15,-.02,.33,.72),
        (3.30,1.12,-.06,.02,.23,.52),
        (3.86,.62,.03,.06,.16,.34),
        (4.30,.08,.08,.10,.08,.15),
    ]
    def catmull(points,t):
        scaled=t*(len(points)-1)
        i=min(int(scaled),len(points)-2)
        f=scaled-i
        f2=f*f;f3=f2*f
        out=[]
        for k in range(len(points[0])):
            p0=points[max(0,i-1)][k]
            p1=points[i][k]
            p2=points[i+1][k]
            p3=points[min(len(points)-1,i+2)][k]
            out.append(.5*((2*p1)+(-p0+p2)*f+(2*p0-5*p1+4*p2-p3)*f2+(-p0+3*p1-3*p2+p3)*f3))
        return tuple(out)
    # Broad canopy crown rises out of the nose-side shoulder, carries a
    # purposeful cockpit volume, then flows down in a long rearward sweep.
    canopy_profile=[
        (-3.70,.05,.02),
        (-3.48,.28,.08),
        (-3.15,.55,.18),
        (-2.75,.78,.32),
        (-2.25,.93,.48),
        (-1.65,1.0,.62),
        (-.90,.98,.72),
        (-.20,.90,.76),
        (.50,.78,.65),
        (1.10,.60,.46),
        (1.58,.36,.25),
        (1.92,.08,.02),
    ]
    def canopy_at_z(z):
        lo,hi=0.0,1.0
        for _ in range(28):
            t=(lo+hi)*.5
            p=catmull(canopy_profile,t)
            if p[0]<z:lo=t
            else:hi=t
        return catmull(canopy_profile,(lo+hi)*.5)
    def roof_at(z,x):
        lo,hi=0.0,1.0
        for _ in range(28):
            t=(lo+hi)*.5
            p=catmull(profile,t)
            if p[0]<z:lo=t
            else:hi=t
        _,rw,_,_,rshoulder,rcrown=catmull(profile,(lo+hi)*.5)
        edge=min(1.0,abs(x)/max(rw,1e-5))
        cap=max(0.0,1.0-edge*edge)**.68
        flare_weight=math.exp(-((z-2.35)/1.25)**2)
        shoulder_ridge=.28*flare_weight*math.exp(-((edge-.82)/.14)**2)
        return rshoulder+(rcrown-rshoulder)*cap+shoulder_ridge

    longitudinal=89
    across=33
    side_steps=4
    section_size=2*across+2*side_steps
    sections=[]
    for row in range(longitudinal):
        t=row/(longitudinal-1)
        z0,width,low,belly,shoulder,crown=catmull(profile,t)
        split=1.18*max(0.0,min(1.0,(t-.72)/.28))**1.45
        flank=.045+.065*max(0.0,1.0-abs(t-.34)/.32)
        section=[]
        for col in range(across):
            u=-1.0+2.0*col/(across-1)
            edge=abs(u)
            cap=max(0.0,1.0-edge*edge)**.68
            flare_weight=math.exp(-((z0-2.35)/1.25)**2)
            shoulder_ridge=.28*flare_weight*math.exp(-((edge-.82)/.14)**2)
            section.append((u*width,shoulder+(crown-shoulder)*cap+shoulder_ridge,z0-split*(1.0-edge)**1.2))
        for side in [1.0,-1.0]:
            for step in range(1,side_steps+1):
                f=step/(side_steps+1)
                y=(shoulder+(belly-shoulder)*f) if side>0 else (belly+(shoulder-belly)*f)
                x=side*width*(1.0+flank*math.sin(math.pi*f))
                edge=min(1.0,abs(x)/max(width,1e-5))
                section.append((x,y,z0-split*(1.0-edge)**1.2))
            if side>0:
                for col in range(across-1,-1,-1):
                    u=-1.0+2.0*col/(across-1)
                    edge=abs(u)
                    cap=max(0.0,1.0-edge*edge)**.68
                    section.append((u*width,belly+(low-belly)*cap,z0-split*(1.0-edge)**1.2))
        sections.append(section)
    verts=[point for section in sections for point in section]
    faces=[]
    for row in range(longitudinal-1):
        for col in range(section_size):
            a=row*section_size+col
            b=row*section_size+(col+1)%section_size
            faces.append((a,b,b+section_size,a+section_size))
    faces.append(tuple(range(section_size-1,-1,-1)))
    end=(longitudinal-1)*section_size
    faces.append(tuple(end+col for col in range(section_size)))
    hull_obj=mesh('SynapseHull',verts,faces,material)
    for polygon in hull_obj.data.polygons:
        polygon.use_smooth=True

    # Paired wedge flares grow directly out of the nose point, fan outward,
    # and disappear into the shoulder before the canopy begins. These are real
    # intersecting hull volumes, not raised decals or thin wing plates.
    flare_sections=[
        (4.22,.22,.50,.015,.012),
        (3.90,.24,.99,.065,.055),
        (3.55,.30,1.045,.16,.10),
        (3.18,.40,1.095,.27,.17),
        (2.78,.50,1.105,.34,.22),
        (2.38,.63,1.085,.29,.18),
        (2.02,.76,1.035,.17,.10),
        (1.72,.78,1.03,.145,.085),
        (1.35,.80,1.025,.115,.065),
        (.95,.82,1.01,.075,.040),
        (.55,.84,.98,.035,.018),
    ]
    flare_material=material
    flare_trace=mat('Synapse_FlareTrace',(.12,.20,.58),.52,.30,.30)
    for side in (-1.0,1.0):
        rings=[]
        top_steps=10
        for z,inner_ratio,outer_ratio,crest,lip in flare_sections:
            if z < -0.20:
                continue
            lo,hi=0.0,1.0
            for _ in range(28):
                t=(lo+hi)*.5
                p=catmull(profile,t)
                if p[0]<z:lo=t
                else:hi=t
            width=catmull(profile,(lo+hi)*.5)[1]
            inner=width*inner_ratio
            outer=width*outer_ratio
            section=[]
            for j in range(top_steps+1):
                f=j/top_steps
                flare_splay=.16*math.exp(-((z-3.90)/.55)**2)
                x=inner+(outer-inner)*f+flare_splay
                base=roof_at(z,x)
                smooth=f*f*(3.0-2.0*f)
                # Replace the soft pillow cross-section with a crisp shoulder
                # crease, a shallow aero channel, and a raised outer blade lip.
                ridge=crest*math.exp(-((f-.76)/.19)**2)
                channel=.08*crest*math.exp(-((f-.37)/.16)**2)
                lift=.040+ridge+lip*smooth-channel
                section.append((side*x,base+lift,z))
            outer_base=roof_at(z,outer)
            inner_base=roof_at(z,inner)
            # The hidden lower return overlaps the monocoque so the new skin
            # reads as broad, molded fender shoulders instead of floating wings.
            section.extend([
                (side*outer,outer_base-.16,z),
                (side*inner,inner_base-.18,z),
            ])
            rings.append(section)
        ring_size=top_steps+3
        flare_verts=[p for ring in rings for p in ring]
        flare_faces=[]
        for row in range(len(rings)-1):
            for col in range(ring_size):
                a=row*ring_size+col
                b=row*ring_size+(col+1)%ring_size
                flare_faces.append((a,b,b+ring_size,a+ring_size))
        flare_faces.append(tuple(range(ring_size-1,-1,-1)))
        last=(len(rings)-1)*ring_size
        flare_faces.append(tuple(last+i for i in range(ring_size)))
        flare=mesh('Synapse_NoseFlare_L' if side<0 else 'Synapse_NoseFlare_R',
                   flare_verts,flare_faces,flare_material)
        for polygon in flare.data.polygons:polygon.use_smooth=True

        # A fine violet light trace follows the raised shoulder crease from
        # the split beak, along the windshield rail, and into the bodywork.
        trace_points=[]
        for z,inner_ratio,outer_ratio,crest,lip in flare_sections:
            lo,hi=0.0,1.0
            for _ in range(28):
                t=(lo+hi)*.5
                p=catmull(profile,t)
                if p[0]<z:lo=t
                else:hi=t
            width=catmull(profile,(lo+hi)*.5)[1]
            f=.76
            ratio=inner_ratio+(outer_ratio-inner_ratio)*f
            flare_splay=.16*math.exp(-((z-3.90)/.55)**2)
            x=side*(width*ratio+flare_splay)
            smooth=f*f*(3.0-2.0*f)
            ridge=crest*math.exp(-((f-.76)/.19)**2)
            channel=.18*crest*math.exp(-((f-.37)/.16)**2)
            y=roof_at(z,x/side)+.040+ridge+lip*smooth-channel+.008
            trace_points.append((x,y,z))
        for a,b in zip(trace_points,trace_points[1:]):
            pipe('Synapse shoulder light seam',a,b,.009,flare_trace,8)

    # The paired front wedges flow into faceted side shoulders. Their
    # shallow C-channel scoops are shaped into the side skin and darkened below.
    side_kit_stations=[
        (3.98,.015),(3.58,.105),(3.10,.20),(2.45,.24),
        (1.70,.30),(.85,.34),(0.0,.42),(-.90,.55),
        (-1.80,.73),(-2.65,.92),(-3.35,.96),(-3.82,.78),(-4.06,.50),
    ]
    def sidekit_values(z,side,v,lift=0.0):
        for k in range(len(side_kit_stations)-1):
            if side_kit_stations[k][0]>=z>=side_kit_stations[k+1][0]:
                span=side_kit_stations[k][0]-side_kit_stations[k+1][0]
                f=(side_kit_stations[k][0]-z)/span
                bulge=side_kit_stations[k][1]*(1-f)+side_kit_stations[k+1][1]*f
                break
        lo,hi=0.0,1.0
        for _ in range(28):
            t=(lo+hi)*.5
            p=catmull(profile,t)
            if p[0]<z:lo=t
            else:hi=t
        t=(lo+hi)*.5
        _,width,_,belly,shoulder,_=catmull(profile,t)
        flank=.045+.065*max(0.0,1.0-abs(t-.34)/.32)
        base=width*(1.0+flank*math.sin(math.pi*v))
        long_fade=max(0.0,min(1.0,(3.98-z)/.25 if z>3.73 else (z+4.06)/.24 if z< -3.82 else 1.0))
        scoop_fade=max(0.0,1.0-((z+.35)/2.25)**2)
        rear_fade=math.exp(-((z+3.02)/1.22)**2)
        upper_rail=.14*math.exp(-((v-.26)/.16)**2)*long_fade
        lower_rail=.10*math.exp(-((v-.78)/.16)**2)*long_fade
        # Broad raised shoulder pods swell around each outer rear thruster.
        # Their tall upper shoulder and wide lower return read as one molded
        # rear fender instead of a small accent floating beside the hull.
        rear_lip=.30*math.exp(-((v-.16)/.21)**2)*rear_fade
        scoop=.19*math.exp(-((v-.40)/.20)**2)*scoop_fade
        x=side*(base+.025+bulge*math.sin(math.pi*v)+upper_rail+lower_rail+rear_lip-scoop+lift)
        rear_shoulder=.82*rear_fade*math.sin(math.pi*v)*math.exp(-((v-.19)/.36)**2)
        y=shoulder+(belly-shoulder)*v+rear_shoulder
        return (x,y,z)

    side_kit_steps=18
    for side in (-1.0,1.0):
        side_kit_rows=97
        side_kit_verts=[]
        for row in range(side_kit_rows):
            z=side_kit_stations[0][0]+(side_kit_stations[-1][0]-side_kit_stations[0][0])*row/(side_kit_rows-1)
            for col in range(side_kit_steps+1):
                v=col/side_kit_steps
                side_kit_verts.append(sidekit_values(z,side,v))
        side_kit_faces=[]
        for row in range(side_kit_rows-1):
            for col in range(side_kit_steps):
                a=row*(side_kit_steps+1)+col
                b=a+side_kit_steps+1
                side_kit_faces.append((a,b,b+1,a+1))
        side_kit=mesh('Synapse_SideKit_L' if side<0 else 'Synapse_SideKit_R',
                      side_kit_verts,side_kit_faces,material)
        for polygon in side_kit.data.polygons:
            polygon.use_smooth=True

        # Recessed dark insert follows the channel trough and pinches out at both ends.
        scoop_material=mat('Synapse_CChannel_Inset',(.012,.025,.075),.48,.22)
        scoop_rows=45
        scoop_steps=10
        scoop_verts=[]
        for row in range(scoop_rows):
            f=row/(scoop_rows-1)
            z=1.70-4.35*f
            fade=math.sin(math.pi*f)**.62
            half=.19*fade
            for col in range(scoop_steps+1):
                g=col/scoop_steps
                v=.40-half+2*half*g
                scoop_verts.append(sidekit_values(z,side,v,.006))
        scoop_faces=[]
        for row in range(scoop_rows-1):
            for col in range(scoop_steps):
                a=row*(scoop_steps+1)+col
                b=a+scoop_steps+1
                scoop_faces.append((a,b,b+1,a+1))
        scoop_obj=mesh('Synapse_SideScoop_L' if side<0 else 'Synapse_SideScoop_R',
                       scoop_verts,scoop_faces,scoop_material)
        for polygon in scoop_obj.data.polygons:
            polygon.use_smooth=True

    # Sculpt a pair of upper-side shoulders that broaden into the split nose.
    def hull_at(z):
        lo,hi=0.0,1.0
        for _ in range(28):
            t=(lo+hi)*.5
            p=catmull(profile,t)
            if p[0]<z:lo=t
            else:hi=t
        return catmull(profile,(lo+hi)*.5)

    # The widened forward hull section below carries these shoulders as one molded shell.
    # Matched dark induction channels follow the actual deformed hood surface,
    # including the split-nose retreat, so they sit on the shell beyond the canopy.
    intake_profile=[
        (1.98,.47,.025,.008),
        (2.25,.45,.060,.014),
        (2.66,.40,.092,.020),
        (3.06,.34,.105,.022),
        (3.42,.27,.070,.014),
        (3.72,.20,.010,.004),
    ]
    intake_material=mat('Synapse_induction',(.055,.035,.20),.55,.25)
    def intake_at_z(z):
        lo,hi=0.0,1.0
        for _ in range(28):
            t=(lo+hi)*.5
            p=catmull(intake_profile,t)
            if p[0]<z:lo=t
            else:hi=t
        return catmull(intake_profile,(lo+hi)*.5)
    def hood_point(z0,side,ratio,raise_y=.025):
        lo,hi=0.0,1.0
        for _ in range(28):
            t=(lo+hi)*.5
            p=catmull(profile,t)
            if p[0]<z0:lo=t
            else:hi=t
        t=(lo+hi)*.5
        _,width,_,_,shoulder,crown=catmull(profile,t)
        split=1.18*max(0.0,min(1.0,(t-.72)/.28))**1.45
        edge=abs(ratio)
        cap=max(0.0,1.0-edge*edge)**.68
        flare_weight=math.exp(-((z0-2.35)/1.25)**2)
        ridge=.28*flare_weight*math.exp(-((edge-.82)/.14)**2)
        z=z0-split*(1.0-edge)**1.2
        x=side*width*ratio
        y=shoulder+(crown-shoulder)*cap+ridge+raise_y
        return (x,y,z)

    intake_rows=57
    intake_across=13
    for side in [-1.0,1.0]:
        intake_verts=[]
        for row in range(intake_rows):
            z0,center,half,lift=catmull(intake_profile,row/(intake_rows-1))
            for col in range(intake_across):
                u=-1.0+2.0*col/(intake_across-1)
                ratio=center+half*u
                x,y,z=hood_point(z0,side,ratio,.030+lift*max(0.0,1.0-u*u)**.7)
                intake_verts.append((x,y,z))
        intake_faces=[]
        for row in range(intake_rows-1):
            for col in range(intake_across-1):
                a=row*intake_across+col
                b=(row+1)*intake_across+col
                intake_faces.append((a,a+1,b+1,b))
        intake=mesh('Synapse_InductionIntake_L' if side<0 else 'Synapse_InductionIntake_R',
                    intake_verts,intake_faces,intake_material)
        for polygon in intake.data.polygons:polygon.use_smooth=True
        # Fine bright baffles reveal the intake direction without crowding the beak.
        for z0 in (2.36,2.76,3.15):
            _,center,half,_=intake_at_z(z0)
            left=hood_point(z0,side,center-half*.78,.060)
            right=hood_point(z0,side,center+half*.78,.060)
            pipe('Synapse intake baffle',left,right,.012,accent,8)

    # Wrap the dark polar glass over a raised, broad crown. The roof-following
    # sill and swept rear edge make the canopy read as part of the body.
    glass_rows=89
    glass_across=33
    canopy_verts=[]
    for row in range(glass_rows):
        z,width,lift=catmull(canopy_profile,row/(glass_rows-1))
        base_y=roof_at(z,width)+.018
        top_y=base_y+lift
        for col in range(glass_across):
            u=-1.0+2.0*col/(glass_across-1)
            cap=max(0.0,1.0-u*u)**.46
            canopy_verts.append((u*width,base_y+(top_y-base_y)*cap,z))
    canopy_faces=[]
    for row in range(glass_rows-1):
        for col in range(glass_across-1):
            a=row*glass_across+col
            b=(row+1)*glass_across+col
            canopy_faces.append((a,a+1,b+1,b))
    canopy_faces.append(tuple(range(glass_across)))
    end=(glass_rows-1)*glass_across
    canopy_faces.append(tuple(end+col for col in range(glass_across)))
    canopy=mesh('SynapsePolarCanopy',canopy_verts,canopy_faces,glass)
    for polygon in canopy.data.polygons:
        polygon.use_smooth=True
    return hull_obj
