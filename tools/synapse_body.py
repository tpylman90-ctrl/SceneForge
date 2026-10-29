"""First-pass Synapse body silhouette. No cockpit, hardware, lighting strips, or trim."""
def build_synapse_body(material):
    # Godot axes: X spans the hull, Y is height, and +Z is forward.
    profile = [
        (-3.95,.72,-.16,-.08,.02,.16),
        (-3.55,1.02,-.24,-.13,.08,.25),
        (-3.00,1.27,-.31,-.17,.14,.39),
        (-2.35,1.36,-.35,-.19,.18,.50),
        (-1.45,1.38,-.36,-.19,.20,.64),
        (-.45,1.33,-.35,-.17,.20,.74),
        (.45,1.29,-.33,-.15,.20,.86),
        (1.35,1.12,-.27,-.11,.16,.67),
        (2.30,.83,-.17,-.05,.12,.36),
        (3.10,.56,-.06,.01,.12,.25),
        (3.75,.34,.02,.06,.12,.20),
        (4.22,.28,.07,.09,.11,.15),
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
    longitudinal=73
    across=25
    top=[]
    bottom=[]
    for row in range(longitudinal):
        t=row/(longitudinal-1)
        z0,width,low,belly,shoulder,crown=sample(t)
        split=.82*max(0.0,min(1.0,(t-.72)/.28))**1.5
        for col in range(across):
            u=-1.0+2.0*col/(across-1)
            edge=abs(u)
            z=z0-split*(1.0-edge)**1.25
            x=u*width
            cap=(1.0-edge)**.7
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
