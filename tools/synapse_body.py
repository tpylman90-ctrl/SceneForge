"""Synapse hull with a fitted polar-glass canopy; interior and hardware remain pending."""
def build_synapse_body(material, glass, accent, carbon):
    # Godot axes: X spans the hull, Y is height, and +Z is forward.
    profile = [
        (-4.15,.62,-.30,-.16,.22,.48),
        (-3.78,.98,-.39,-.18,.34,.79),
        (-3.12,1.44,-.43,-.19,.46,1.02),
        (-2.35,1.48,-.44,-.18,.55,1.18),
        (-1.35,1.34,-.45,-.18,.58,1.24),
        (-.20,1.31,-.43,-.17,.55,1.20),
        (.85,1.23,-.36,-.14,.49,1.08),
        (1.80,1.12,-.26,-.08,.36,.88),
        (2.65,1.14,-.15,-.02,.25,.62),
        (3.30,.84,-.06,.02,.16,.40),
        (3.86,.46,.03,.06,.11,.25),
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
        return rshoulder+(rcrown-rshoulder)*cap

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
