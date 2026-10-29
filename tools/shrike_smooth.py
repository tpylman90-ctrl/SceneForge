"""Shrike smooth-body redesign: integrated enclosed hovercar, original geometry."""
def build_shrike(body,accent,carbon,steel,rubber,glow,glass):
    import math
    from mathutils import Vector
    # Temporary shape-review clay: darker neutral graphite prevents sunlit clipping.
    # Revert to original silver/orange livery only after geometry approval.
    body.diffuse_color=(.23,.29,.35,1)
    bs=body.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value=body.diffuse_color
    bs.inputs['Roughness'].default_value=.52
    bs.inputs['Coat Weight'].default_value=.08
    # Continuous aerodynamic production-car shell.  Smooth oval loft, not an open deck.
    # Broad, blunt sports-car nose; rear (-Z), front (+Z).
    # First-order proportions only: keep this pass free of exposed aero appendages.
    stations=[(-3.55,.75,.51,1.39),(-3.35,.94,.44,1.53),
              (-3.03,1.10,.39,1.65),(-2.55,1.20,.36,1.72),
              (-2.05,1.23,.34,1.74),(-1.30,1.24,.32,1.70),
              (-.50,1.25,.30,1.54),(.40,1.25,.29,1.47),
              (1.18,1.27,.28,1.36),(1.82,1.31,.28,1.16),
              (2.40,1.32,.30,1.02),(2.83,1.27,.32,.90),
              (3.15,1.16,.36,.78),(3.40,.92,.40,.69)]
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
            # Pinched waist and confident rear haunch are part of the actual shell.
            side=abs(math.cos(a))
            waist=.075*math.exp(-((z-.05)/.85)**2)
            haunch=.055*math.exp(-((z+2.25)/.75)**2)
            front=math.exp(-((z-2.12)/.84)**2)
            rear=math.exp(-((z+2.36)/.99)**2)
            x=(w-waist+haunch+.15*front+.18*rear)*math.cos(a)
            y=(low+high)/2+(high-low)*.5*math.sin(a)
            # Raised paired front shoulders and rear wheel-arch haunches.
            # Recessed central hood and trunk result from the outer-only lift.
            outer=math.exp(-((abs(math.cos(a))-.75)/.18)**2)
            upper=max(0.0,math.sin(a))**1.2
            y+=outer*upper*(.29*front+.21*rear)
            # Soften the crown into a broad nearly level fastback, not a round dome.
            if z < -1.55 and math.sin(a)>.65:
                y-=.075*(math.sin(a)-.65)/.35
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
    # Form-only prototype: no trim, intakes, lights, hover rings or panel add-ons.
    # Unified greenhouse: long low windshield, swept side glass, and a molded
    # painted roof flowing continuously down into the raised rear haunches.
    # The old exposed, boxy blue cap is deliberately replaced.
    roof_sections=[
        (1.43,.48,1.31), (1.12,.61,1.46), (.65,.72,1.61),
        (.08,.75,1.71), (-.48,.72,1.75), (-.88,.67,1.75),
        (-1.30,.60,1.72), (-1.75,.65,1.70), (-2.25,.72,1.69),
        (-2.75,.76,1.67), (-3.18,.72,1.57), (-3.48,.49,1.42)]
    def roof_band(name,sections,material):
        vertices=[]
        for z,w,h in sections:
            vertices.extend([(-w,1.37,z),(-w*.81,h-.055,z),
                             (0,h,z),(w*.81,h-.055,z),(w,1.37,z)])
        faces=[]
        for row in range(len(sections)-1):
            for col in range(4):
                a=row*5+col
                faces.append((a,a+1,a+6,a+5))
        obj=mesh(name,vertices,faces,material)
        for face in obj.data.polygons: face.use_smooth=True
        return obj
    # Both bands share stations at z=-.88 and -1.30 so glass/paint meet.
    roof_band('vehicle_glass_shrike_windscreen_and_roof',roof_sections[:7],glass)
    roof_band('Shrike one-piece molded roof into rear deck',roof_sections[6:],body)
    for side in (-1,1):
        panel('vehicle_glass_shrike_swept_side',[
            (side*.55,1.42,1.13),(side*.69,1.56,.62),
            (side*.73,1.64,-.02),(side*.69,1.67,-.73),
            (side*.61,1.62,-1.24),(side*.65,1.43,-1.43),
            (side*.77,1.36,-.77),(side*.74,1.34,.34)],glass)
    # Fenders and rear flares are molded into the main shell, not separate meshes.
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
        pipe('Shrike hidden animation anchor',(x,1.10,-3.15),
             (x,1.10,-3.18),.012,carbon,8)
        rig('Kestrel_Tail_%d'%i,since(before),(x,1.20,-3.25))
