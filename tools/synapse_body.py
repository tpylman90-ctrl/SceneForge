"""Body-only Synapse silhouette study: sculpted low shell, no cockpit or hardware."""
def build_synapse_body(material):
    # Godot axes: X spans the hull, Y is height, and +Z is forward.
    # Fuller shoulder volume and a raised rear deck give the shell depth
    # without turning the teardrop wedge into a rounded capsule.
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
    top=[]
    bottom=[]
    for row in range(longitudinal):
        t=row/(longitudinal-1)
        z0,width,low,belly,shoulder,crown=sample(t)
        split=.90*max(0.0,min(1.0,(t-.72)/.28))**1.45
        for col in range(across):
            u=-1.0+2.0*col/(across-1)
            edge=abs(u)
            z=z0-split*(1.0-edge)**1.2
            x=u*width
            # Softly rounded transverse sections with a flatter upper deck.
            cap=max(0.0,1.0-edge*edge)**.68
            top.append((x,shoulder+(crown-shoulder)*cap,z))
            bottom.append((x,belly+(low-belly)*cap,z))
    verts=top+bottom
    offset=len(top)
    faces=[]
    for row in range(longitudinal-1):
        for col in range(across-1):
            a=row*across+col
            b=(row+1)*across+col
            faces.append((a,a+1,b+1,b))
            faces.append((offset+a,offset+b,offset+b+1,offset+a+1))
        left=row*across
        left_next=(row+1)*across
        right=left+across-1
        right_next=left_next+across-1
        faces.append((left,left_next,offset+left_next,offset+left))
        faces.append((right,offset+right,offset+right_next,right_next))
    for row in [0,longitudinal-1]:
        upper=list(range(row*across,(row+1)*across))
        lower=[offset+i for i in reversed(upper)]
        faces.append(tuple(upper+lower))
    hull_obj=mesh('SynapseHull',verts,faces,material)
    for polygon in hull_obj.data.polygons:
        polygon.use_smooth=True
    return hull_obj
