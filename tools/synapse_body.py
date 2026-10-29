"""Body-only Synapse silhouette study: fuller swept shell, no cockpit or hardware."""
def build_synapse_body(material):
    # Godot axes: X spans the hull, Y is height, and +Z is forward.
    # The profile carries real shoulder and rear-haunch volume while keeping
    # the split beak low and narrow.
    profile = [
        (-4.15,.55,-.25,-.11,.10,.25),
        (-3.78,.91,-.42,-.15,.37,.78),
        (-3.12,1.24,-.52,-.19,.60,1.13),
        (-2.28,1.48,-.58,-.22,.72,1.42),
        (-1.25,1.60,-.59,-.23,.75,1.54),
        (-.05,1.61,-.56,-.21,.72,1.50),
        (.95,1.48,-.48,-.17,.65,1.36),
        (1.82,1.19,-.35,-.11,.53,1.13),
        (2.60,.83,-.20,-.04,.37,.82),
        (3.28,.52,-.07,.01,.24,.54),
        (3.86,.29,.03,.06,.15,.32),
        (4.30,.14,.08,.10,.10,.17),
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
            # Rounded transverse sections create a broad, continuous shell
            # instead of the pinched diamond profile of the first study.
            cap=max(0.0,1.0-edge*edge)**.58
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
