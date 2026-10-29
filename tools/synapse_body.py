"""Body-only Synapse silhouette study: sculpted teardrop shell, no cockpit or hardware."""
def build_synapse_body(material):
    # Godot axes: X spans the hull, Y is height, and +Z is forward.
    # A broad, low deck and softly rolled shoulder sections give the hull
    # dimension without breaking the continuous wedge silhouette.
    profile = [
        (-4.15,.45,-.18,-.08,.08,.20),
        (-3.78,.78,-.32,-.13,.25,.58),
        (-3.12,1.10,-.40,-.16,.42,.95),
        (-2.35,1.31,-.44,-.18,.55,1.18),
        (-1.35,1.39,-.45,-.18,.58,1.24),
        (-.20,1.38,-.43,-.17,.55,1.20),
        (.85,1.28,-.36,-.14,.49,1.08),
        (1.80,1.02,-.26,-.08,.36,.88),
        (2.65,.72,-.15,-.02,.25,.62),
        (3.30,.45,-.06,.02,.16,.40),
        (3.86,.25,.03,.06,.11,.25),
        (4.30,.12,.08,.10,.08,.15),
    ]
    def sample(t):
        scaled=t*(len(profile)-1)
        i=min(int(scaled),len(profile)-2)
        f=scaled-i
        f2=f*f;f3=f2*f
        result=[]
        for k in range(6):
            p0=profile[max(0,i-1)][k]
            p1=profile[i][k]
            p2=profile[i+1][k]
            p3=profile[min(len(profile)-1,i+2)][k]
            result.append(.5*((2*p1)+(-p0+p2)*f+(2*p0-5*p1+4*p2-p3)*f2+(-p0+3*p1-3*p2+p3)*f3))
        return tuple(result)
    longitudinal=89
    across=33
    side_steps=4
    section_size=2*across+2*side_steps
    sections=[]
    for row in range(longitudinal):
        t=row/(longitudinal-1)
        z0,width,low,belly,shoulder,crown=sample(t)
        split=.90*max(0.0,min(1.0,(t-.72)/.28))**1.45
        flank=.045+.065*max(0.0,1.0-abs(t-.34)/.32)
        section=[]
        for col in range(across):
            u=-1.0+2.0*col/(across-1)
            edge=abs(u)
            cap=max(0.0,1.0-edge*edge)**.68
            section.append((u*width,shoulder+(crown-shoulder)*cap,z0-split*(1.0-edge)**1.2))
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
    return hull_obj
