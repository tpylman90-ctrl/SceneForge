"""Synapse racer hull with integrated rear flares, cockpit, and ion thrusters."""
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
    side_kit_stations=[
        (3.98,.015),(3.58,.105),(3.10,.20),(2.45,.24),
        (1.70,.32),(.85,.38),(0.0,.48),(-.90,.64),
        (-1.80,.86),(-2.65,1.08),(-3.35,1.12),(-3.82,.94),(-4.15,.015),
    ]
    def sidekit_bulge_at_z(z):
        for k in range(len(side_kit_stations)-1):
            if side_kit_stations[k][0]>=z>=side_kit_stations[k+1][0]:
                span=side_kit_stations[k][0]-side_kit_stations[k+1][0]
                f=(side_kit_stations[k][0]-z)/span
                return side_kit_stations[k][1]*(1-f)+side_kit_stations[k+1][1]*f
        return 0.0

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
    side_steps=10
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
                v=f if side>0 else 1.0-f
                rear_fade=math.exp(-((z0+3.02)/1.22)**2)
                scoop_fade=max(0.0,1.0-((z0+.35)/2.25)**2)
                base_x=width*(1.0+flank*math.sin(math.pi*f))
                flare=sidekit_bulge_at_z(z0)*math.sin(math.pi*v)
                channel=.20*math.exp(-((v-.40)/.20)**2)*scoop_fade*math.sin(math.pi*v)
                x=side*(base_x+flare-channel)
                rear_lift=1.22*rear_fade*math.sin(math.pi*v)*math.exp(-((v-.19)/.36)**2)
                y=(shoulder+(belly-shoulder)*v)+rear_lift
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
            # Leave a real cockpit opening beneath the fitted canopy.
            if col < across-1:
                u_mid=-1.0+2.0*(col+.5)/(across-1)
                z_mid=(sections[row][col][2]+sections[row+1][col][2])*.5
                if -3.55<z_mid<1.65:
                    t_mid=(row+.5)/(longitudinal-1)
                    hull_width=catmull(profile,t_mid)[1]
                    canopy_width=canopy_at_z(z_mid)[1]
                    opening_ratio=min(.86,.84*canopy_width/max(hull_width,1e-5))
                    if abs(u_mid)<opening_ratio:
                        continue
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

    # Rear flares are sculpted into SynapseHull itself; only the recessed
    # C-channel remains a separate insert, so the rear shoulders cannot gap.
    def sidekit_values(z,side,v,lift=0.0):
        lo,hi=0.0,1.0
        for _ in range(28):
            t=(lo+hi)*.5
            p=catmull(profile,t)
            if p[0]<z:lo=t
            else:hi=t
        t=(lo+hi)*.5
        _,width,_,belly,shoulder,_=catmull(profile,(lo+hi)*.5)
        flank=.045+.065*max(0.0,1.0-abs(t-.34)/.32)
        f=v if side>0 else 1.0-v
        side_divisions=side_steps+1
        scaled_f=f*side_divisions
        segment=min(int(scaled_f),side_divisions-1)
        segment_f=scaled_f-segment
        f0=segment/side_divisions
        f1=(segment+1)/side_divisions
        rear_fade=math.exp(-((z+3.02)/1.22)**2)
        scoop_fade=max(0.0,1.0-((z+.35)/2.25)**2)
        bulge=sidekit_bulge_at_z(z)
        def sample_side(fraction):
            v_side=fraction if side>0 else 1.0-fraction
            base_x=width*(1.0+flank*math.sin(math.pi*fraction))
            flare=bulge*math.sin(math.pi*v_side)
            channel=.20*math.exp(-((v_side-.40)/.20)**2)*scoop_fade*math.sin(math.pi*v_side)
            rear_lift=1.22*rear_fade*math.sin(math.pi*v_side)*math.exp(-((v_side-.19)/.36)**2)
            y_side=shoulder+(belly-shoulder)*v_side+rear_lift
            return side*(base_x+flare-channel),y_side
        x0,y0=sample_side(f0)
        x1,y1=sample_side(f1)
        return (x0*(1.0-segment_f)+x1*segment_f+side*lift,
                y0*(1.0-segment_f)+y1*segment_f,z)

    for side in (-1.0,1.0):
        # The dark C-channel follows the integrated flare and is tucked just
        # above its surface to avoid z-fighting.
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
                scoop_verts.append(sidekit_values(z,side,v,.035))
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
    titanium=mat('Synapse_Titanium',(.24,.31,.40),.84,.25)
    hot_ceramic=mat('Synapse_ThrusterCeramic',(.035,.045,.095),.68,.28)
    core_glow=mat('Synapse_ThrusterCore',(.14,.28,.92),.10,.22,.9)
    service_glow=mat('Synapse_ServiceLight',(.12,.48,.95),.14,.28,.65)
    # Visible cockpit hardware sits below the polar glass, inside the hull.
    box('Synapse cockpit floor',(0,-.08,-.05),(1.08,.11,2.20),carbon,.025)
    box('Synapse seat pan',(0,.10,-.30),(.64,.16,.66),rubber,.07)
    box('Synapse seat shell',(0,.49,-.63),(.68,.90,.20),carbon,.075)
    box('Synapse seat cushion',(0,.43,-.50),(.52,.58,.10),rubber,.055)
    box('Synapse headrest',(0,.94,-1.03),(.42,.25,.17),carbon,.055)
    for side in (-1.0,1.0):
        pipe('Synapse seat harness',(side*.20,.78,-.50),(side*.13,.17,.02),.026,accent,10)
        pipe('Synapse seat support',(side*.25,.12,-.52),(side*.31,-.04,-.52),.04,titanium,10)
    panel('Synapse cockpit control shelf',
          [(-.50,.05,.62),(.50,.05,.62),(.42,.35,1.02),(-.42,.35,1.02)],carbon)
    hudmat=mat('Synapse_HoloDisplay',(.04,.42,.88),.03,.22,.55)
    panel('Synapse holographic HUD glass',
          [(-.29,.52,1.08),(.29,.52,1.08),(.24,.77,1.00),(-.24,.77,1.00)],hudmat)
    # Simple luminous telemetry strokes read through the dark canopy.
    for side in (-1.0,1.0):
        pipe('Synapse HUD speed arc',(side*.20,.58,1.084),(side*.10,.70,1.035),.012,service_glow,8)
    pipe('Synapse HUD horizon line',(-.08,.66,1.045),(.08,.66,1.045),.010,core_glow,8)
    for x in (-.22,-.12,0.0,.12,.22):
        pipe('Synapse HUD tick',(x,.55,1.09),(x,.58,1.08),.008,service_glow,6)

    # Rear propulsion cluster: three nested, rear-facing vector bells.
    def rear_ring(name,x,y,z,major,minor,material):
        obj=ring(name,(x,y,z),major,minor,material)
        # The shared ring helper starts in the XZ plane; turn it to face aft.
        obj.rotation_euler[0]=math.pi/2
        return obj
    for label,x,y,radius in [('Port',-.73,.34,.225),('Center',0.0,.43,.315),('Starboard',.73,.34,.225)]:
        pipe('Synapse '+label+' thrust bell',(x,y,-3.88),(x,y,-4.56),radius,hot_ceramic,28)
        pipe('Synapse '+label+' alloy throat',(x,y,-4.34),(x,y,-4.61),radius*.79,titanium,28)
        pipe('Synapse '+label+' luminous core',(x,y,-4.56),(x,y,-4.62),radius*.58,core_glow,28)
        rear_ring('Synapse '+label+' outer turbine lip',x,y,-4.48,radius*1.04,.045,accent)
        rear_ring('Synapse '+label+' inner ion ring',x,y,-4.60,radius*.78,.025,service_glow)
        rear_ring('Synapse '+label+' ceramic gasket',x,y,-4.36,radius*.91,.026,titanium)
    # A deep molded aft valance wraps around the complete three-nozzle
    # cluster. The apertures let the bells project through it, joining the
    # broad shoulder flares to one continuous rear body.
    aft_fairing=mat('Synapse_AftFairing',(.055,.075,.19),.72,.24)
    aft_center_y=.36
    aft_segments=64
    aft_loops=[]
    for rx,ry,z in [
        (1.47,.78,-3.98), (1.14,.55,-3.98),
        (1.47,.78,-4.20), (1.14,.55,-4.20),
    ]:
        loop=[]
        for index in range(aft_segments):
            angle=2*math.pi*index/aft_segments
            cx=math.cos(angle); sy=math.sin(angle)
            # A softly squared oval gives the rear housing a broad, planted stance.
            x=rx*(1 if cx>=0 else -1)*abs(cx)**.88
            y=aft_center_y+ry*(1 if sy>=0 else -1)*abs(sy)**.88
            loop.append((x,y,z))
        aft_loops.append(loop)
    aft_verts=[point for loop in aft_loops for point in loop]
    aft_faces=[]
    for index in range(aft_segments):
        nxt=(index+1)%aft_segments
        # Outer and inner depth walls, plus the forward and aft annular faces.
        aft_faces.extend([
            (index,nxt,2*aft_segments+nxt,2*aft_segments+index),
            (aft_segments+index,3*aft_segments+index,
             3*aft_segments+nxt,aft_segments+nxt),
            (index,aft_segments+index,aft_segments+nxt,nxt),
            (2*aft_segments+index,2*aft_segments+nxt,
             3*aft_segments+nxt,3*aft_segments+index),
        ])
    aft_shell=mesh('Synapse_Integrated_AftThrustFairing',
                   aft_verts,aft_faces,aft_fairing)
    for polygon in aft_shell.data.polygons:
        polygon.use_smooth=True
    # Four corner fasteners anchor the broad molded rear surround.
    for x,y in [(-1.24,.86),(1.24,.86),(-1.24,-.14),(1.24,-.14)]:
        pipe('Synapse aft fairing fastener',
             (x,y,-4.205),(x,y,-4.245),.034,titanium,10)

    # A shallow rear manifold ties the three thrust modules into the wide shell.
    pipe('Synapse rear thrust manifold',(-.92,.40,-4.02),(.92,.40,-4.02),.055,carbon,12)
    for x in (-.92,-.46,0.0,.46,.92):
        pipe('Synapse manifold fastener',(x,.40,-4.02),(x,.40,-4.055),.028,titanium,10)

    # Thin illuminated rails trace the sculpted C-channels and raised shoulders.
    for side in (-1.0,1.0):
        for v_line,material,radius,name in [
            (.215,accent,.017,'Synapse channel upper rail'),
            (.585,titanium,.013,'Synapse channel lower rail'),
            (.145,service_glow,.010,'Synapse shoulder tracer'),
        ]:
            pts=[sidekit_values(1.45-4.65*i/32,side,v_line,.045) for i in range(33)]
            for a,b in zip(pts,pts[1:]):
                pipe(name,a,b,radius,material,8)
        # Small slotted louvers sit in the side channel near the rear quarter.
        for z in (-1.95,-2.25,-2.55):
            a=sidekit_values(z,side,.31,.055)
            b=sidekit_values(z-.12,side,.51,.055)
            pipe('Synapse side-channel louver',a,b,.026,titanium,8)
            p=sidekit_values(z,side,.41,.072)
            pipe('Synapse louver pin',(p[0],p[1],p[2]),(p[0]+side*.025,p[1],p[2]),.018,service_glow,8)
        # Layered carbon armor follows the rear shoulder surface, without a
        # detached wing plate or exposed seam at its root.
        armor_rows=17
        armor_cols=5
        armor_verts=[]
        for row in range(armor_rows):
            z=-1.55-2.05*row/(armor_rows-1)
            for col in range(armor_cols):
                v=.12+.22*col/(armor_cols-1)
                armor_verts.append(sidekit_values(z,side,v,.024))
        armor_faces=[]
        for row in range(armor_rows-1):
            for col in range(armor_cols-1):
                a=row*armor_cols+col
                b=a+armor_cols
                armor_faces.append((a,a+1,b+1,b))
        armor=mesh('Synapse rear shoulder carbon inlay',armor_verts,armor_faces,carbon)
        for poly in armor.data.polygons:poly.use_smooth=True
        # Three flush maintenance fasteners mark the molded shoulder panel.
        for z in (-2.0,-2.65,-3.25):
            p=sidekit_values(z,side,.30,.055)
            pipe('Synapse shoulder fastener',(p[0],p[1],p[2]),(p[0]+side*.035,p[1],p[2]),.022,titanium,10)

    # Heat-extraction gills sit flush on the aft deck behind the canopy.
    deck_vent=mat('Synapse_DeckVent',(.018,.025,.060),.62,.33)
    for index,z in enumerate((-1.95,-2.28,-2.61,-2.94)):
        z_back=z-.16
        points=[
            (-.34,roof_at(z,-.34)+.035,z),
            (.34,roof_at(z,.34)+.035,z),
            (.27,roof_at(z_back,.27)+.035,z_back),
            (-.27,roof_at(z_back,-.27)+.035,z_back),
        ]
        panel('Synapse aft deck heat extractor',points,deck_vent)
        for side in (-1.0,1.0):
            x=side*.23
            pipe('Synapse vent lip',(x,roof_at(z,x)+.055,z),(x*.82,roof_at(z_back,x*.82)+.055,z_back),.012,service_glow,8)

    # A fine metal reveal frames the polar-glass canopy edge.
    canopy_edge=mat('Synapse_CanopyFrame',(.18,.27,.42),.78,.24)
    for side in (-1.0,1.0):
        frame_pts=[]
        for row in range(25):
            z,width,lift=catmull(canopy_profile,row/24)
            y=roof_at(z,width)+.045
            frame_pts.append((side*width,y,z))
        for a,b in zip(frame_pts,frame_pts[1:]):
            pipe('Synapse canopy perimeter frame',a,b,.024,canopy_edge,10)
    for z in (-2.15,-.55,.95,1.52):
        _,width,lift=canopy_at_z(z)
        y=roof_at(z,width)+.04
        pipe('Synapse canopy cross tie',(-width*.92,y,z),(width*.92,y,z),.018,titanium,10)

    return hull_obj
