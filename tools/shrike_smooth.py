"""Shrike smooth-body redesign: integrated enclosed hovercar, original geometry."""
def build_shrike(body,accent,carbon,steel,rubber,glow,glass):
    import math
    from mathutils import Vector
    body.diffuse_color=(.71,.76,.80,1)
    bs=body.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value=body.diffuse_color
    bs.inputs['Roughness'].default_value=.22
    bs.inputs['Coat Weight'].default_value=.42
    # Continuous aerodynamic production-car shell.  Smooth oval loft, not an open deck.
    # Broad, blunt sports-car nose; rear (-Z), front (+Z).
    # First-order proportions only: keep this pass free of exposed aero appendages.
    stations=[(-2.85,.76,.48,1.03),(-2.60,.97,.43,1.20),
              (-2.05,1.17,.36,1.39),(-1.30,1.24,.32,1.47),
              (-.50,1.25,.30,1.50),(.40,1.25,.29,1.47),
              (1.18,1.21,.28,1.36),(1.82,1.15,.28,1.16),
              (2.40,1.06,.30,.98),(2.83,.97,.32,.81),
              (3.15,.87,.36,.72),(3.40,.75,.40,.65)]
    segments=[]
    for a,b in zip(stations,stations[1:]):
        for i in range(5):
            t=i/5
            segments.append(tuple(a[k]*(1-t)+b[k]*t for k in range(4)))
    segments.append(stations[-1])
    n=20;points=[]
    for z,w,low,high in segments:
        for j in range(n):
            a=2*math.pi*j/n
            x=w*math.cos(a)
            y=(low+high)/2+(high-low)*.5*math.sin(a)
            points.append((x,y,z))
    faces=[]
    for k in range(len(segments)-1):
        for j in range(n):
            # Remove roof over cockpit so glazing isn't buried beneath opaque bodywork.
            mid=(segments[k][0]+segments[k+1][0])*.5
            if -1.56 < mid < 1.36 and 2 <= j <= 8: continue
            faces.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
    faces.extend([tuple(reversed(range(n))),tuple((len(segments)-1)*n+j for j in range(n))])
    shell=mesh('Shrike seamless flowing body',points,faces,body,.009)
    for face in shell.data.polygons:face.use_smooth=True
    # Body-only iteration: avoid floating skirts, spear blades and exposed pods.
    # Two flush dark insets help judge bonnet curvature without hiding silhouette.
    panel('Shrike wide bonnet recess',[
       (-.40,1.19,1.86),(-.48,1.01,2.36),(-.42,.81,2.91),
       (.42,.81,2.91),(.48,1.01,2.36),(.40,1.19,1.86)],carbon)
    for side in (-1,1):
        # Short, flush orange shoulder motif; no protruding fins.
        pipe('Shrike shoulder visual datum',
             (side*1.20,1.04,.82),(side*1.11,.86,2.10),.012,accent,10)
    # Integrated rounded canopy visible in top and cockpit views.
    canopy=[(1.35,.50,1.29),(.95,.68,1.59),(.30,.70,1.83),
            (-.45,.69,1.89),(-1.08,.61,1.76),(-1.54,.39,1.55)]
    cp=[]
    for z,w,h in canopy:
        cp.extend([(-w,1.39,z),(-w*.76,h,z),(0,h+.05,z),
                   (w*.76,h,z),(w,1.39,z)])
    cf=[]
    for i in range(len(canopy)-1):
        for j in range(4):
            cf.append((i*5+j,i*5+j+1,(i+1)*5+j+1,(i+1)*5+j))
    mesh('vehicle_glass_shrike_roof',cp,cf,glass)
    for s in [-1,1]:
        frame=[(s*w,1.41,z) for z,w,h in canopy]
        for a,b in zip(frame,frame[1:]):
            pipe('Shrike subtle canopy seal',a,b,.019,carbon,10)
    box('Shrike sealed cockpit seat',(0,1.04,-.40),(.55,.46,.76),rubber,.06)
    box('Shrike driver seat back',(0,1.42,-.78),(.56,.64,.17),carbon,.06)
    before=set(bpy.context.scene.objects)
    for s in [-1,1]:
        pipe('Shrike steering yoke',(s*.20,1.18,.91),(s*.20,1.34,.89),.035,steel)
    pipe('Shrike steering crossbar',(-.20,1.22,.90),(.20,1.22,.90),.034,carbon)
    rig('Kestrel_Yoke',since(before),(0,1.22,.90))
    # Preserve existing five animation-controlled tail rig names.
    for i in range(5):
        before=set(bpy.context.scene.objects)
        x=(i-2)*.25
        pipe('Shrike embedded vector jet',(x,1.20,-2.65),
             (x,1.20,-2.91),.09,carbon,12)
        pipe('Shrike jet inner',(x,1.20,-2.88),(x,1.20,-2.94),.05,glow,12)
        rig('Kestrel_Tail_%d'%i,since(before),(x,1.20,-2.65))
