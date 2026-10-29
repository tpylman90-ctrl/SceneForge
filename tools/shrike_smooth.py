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
    stations=[(-3.55,.75,.51,1.39),(-3.35,.94,.44,1.53),
              (-3.03,1.10,.39,1.65),(-2.55,1.20,.36,1.72),
              (-2.05,1.23,.34,1.74),(-1.30,1.24,.32,1.70),
              (-.50,1.25,.30,1.54),(.40,1.25,.29,1.47),
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
            # Pinched waist and confident rear haunch are part of the actual shell.
            side=abs(math.cos(a))
            waist=.075*math.exp(-((z-.05)/.85)**2)
            haunch=.055*math.exp(-((z+2.25)/.75)**2)
            x=(w-waist+haunch)*math.cos(a)
            y=(low+high)/2+(high-low)*.5*math.sin(a)
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
    # Integrated engineering details follow the flowing body, without exposed hover barrels.
    # Two flush dark insets help judge bonnet curvature without hiding silhouette.
    panel('Shrike wide bonnet recess',[
       (-.40,1.19,1.86),(-.48,1.01,2.36),(-.42,.81,2.91),
       (.42,.81,2.91),(.48,1.01,2.36),(.40,1.19,1.86)],carbon)
    for side in (-1,1):
        # Short, flush orange shoulder motif; no protruding fins.
        pipe('Shrike shoulder visual datum',
             (side*1.20,1.04,.82),(side*1.11,.86,2.10),.012,accent,10)
    # Recessed full-width intake and broad blunt fascia.
    panel('Shrike recessed front grille',[
        (-.67,.49,3.405),(.67,.49,3.405),
        (.64,.60,3.408),(-.64,.60,3.408)],carbon)
    for k in range(7):
        x=(k-3)*.18
        pipe('Shrike front grille vertical vane',(x,.49,3.423),
             (x,.60,3.425),.012,steel,8)
    pipe('Shrike front luminous grille edge',(-.62,.62,3.412),
         (.62,.62,3.412),.018,glow,12)
    # Body-integrated nose cheeks, upper light recesses and raised fastback haunches.
    for side in (-1,1):
        panel('Shrike sculpted front cheek',[
            (side*.69,.64,3.35),(side*.88,.72,3.07),
            (side*.99,.84,2.70),(side*.83,.86,2.45),
            (side*.65,.65,2.95)],body)
        panel('Shrike front optical inset',[
            (side*.71,.79,3.16),(side*.92,.86,2.79),
            (side*.89,.89,2.62),(side*.66,.82,3.01)],carbon)
        pipe('Shrike front optic', (side*.71,.816,3.12),
             (side*.89,.90,2.76),.016,glow,10)
        # The C-shaped side accent follows the lifted rear quarter in a shallow inset.
        curve=[(side*1.19,1.02,.42),(side*1.23,1.08,-.18),
               (side*1.18,1.28,-.87),(side*1.04,1.49,-1.40),
               (side*.91,1.54,-2.20)]
        for a,b in zip(curve,curve[1:]):
            pipe('Shrike orange rear-quarter shoulder',a,b,.027,accent,12)
        panel('Shrike rear-quarter side intake',[
            (side*1.13,1.06,-1.88),(side*1.10,1.30,-2.48),
            (side*.98,1.29,-2.92),(side*1.13,.92,-2.50)],carbon)
        for j in range(4):
            z=-2.18-j*.13
            pipe('Shrike flush intake stator',(side*1.16,1.01,z),
                 (side*1.10,1.21,z-.055),.013,steel,8)
        # Repulsor glow is under the full-width shell, not around external pots.
        for x,z in [(side*.86,1.95),(side*.92,-1.70)]:
            ring('Shrike inset hover field',(x,.25,z),.27,.021,glow)
        # Broad rear lamp wrapping around raised shoulders.
        pipe('Shrike wraparound rear lamp',(side*.21,1.32,-3.52),
             (side*.76,1.37,-3.46),.037,accent,12)
        pipe('Shrike dark aft vent',(side*.69,.83,-3.28),
             (side*.69,.83,-3.50),.19,carbon,20)
    panel('Shrike raised rear central deck',[
        (-.76,1.46,-1.59),(-.69,1.62,-2.40),
        (-.56,1.46,-3.43),(.56,1.46,-3.43),
        (.69,1.62,-2.14),(.76,1.46,-1.59)],body)
    panel('Shrike dorsal rear thermal extractor',[
        (-.36,1.66,-2.12),(-.31,1.51,-2.89),
        (.31,1.51,-2.89),(.36,1.66,-2.12)],carbon)
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
        # Long curved side windows lie within the cockpit sculpt rather than
        # forming a separate vertical windshield box.
        panel('vehicle_glass_shrike_swept_side',[
            (side*.55,1.42,1.13),(side*.69,1.56,.62),
            (side*.73,1.64,-.02),(side*.69,1.67,-.73),
            (side*.61,1.62,-1.24),(side*.65,1.43,-1.43),
            (side*.77,1.36,-.77),(side*.74,1.34,.34)],glass)
        frame=[(side*w,1.385,z) for z,w,h in roof_sections[:7]]
        for x,y in zip(frame,frame[1:]):
            pipe('Shrike flush greenhouse lower seal',x,y,.013,carbon,10)
        # C-pillar becomes bodywork, gradually growing toward rear shoulders.
        panel('Shrike integrated sail pillar',[
            (side*.61,1.62,-1.22),(side*.68,1.69,-1.70),
            (side*.89,1.61,-2.48),(side*1.07,1.37,-3.12),
            (side*.82,1.37,-1.70)],body)

    # MK II reference-inspired hard surfaces, kept tight to the Shrike shell.
    # Rather than floating fins, these build an engineered shoulder, waist
    # undercut and integrated rear-wing root in the silver bodywork.
    for side in (-1,1):
        panel('Shrike front swept shoulder blade',[
            (side*.61,1.05,2.54),(side*.98,1.02,2.05),
            (side*1.22,1.08,1.01),(side*1.17,.89,.55),
            (side*.91,.78,1.23)],body)
        panel('Shrike sculpted waist relief',[
            (side*1.15,.74,1.10),(side*1.22,.70,.29),
            (side*1.10,.62,-.84),(side*1.20,.72,-1.75),
            (side*1.06,.57,-1.40),(side*.99,.57,-.32)],carbon)
        panel('Shrike curved midbody overpanel',[
            (side*1.19,1.03,.45),(side*1.24,1.14,-.26),
            (side*1.21,1.33,-1.12),(side*1.14,1.44,-2.12),
            (side*1.06,1.09,-1.84),(side*1.13,.86,-.56)],body)
        # Orange contour is recessed visually between upper shoulder and sill.
        shoulder=[(side*1.19,1.04,.48),(side*1.25,1.13,-.20),
                  (side*1.22,1.34,-1.12),(side*1.15,1.46,-2.10)]
        for a,b in zip(shoulder,shoulder[1:]):
            pipe('Shrike swept orange side channel',a,b,.023,accent,12)
        # Low-profile aft flares integrated with the fastback, not bird-like blades.
        panel('Shrike tail shoulder fairing',[
            (side*.72,1.66,-2.21),(side*1.08,1.51,-2.54),
            (side*1.12,1.39,-3.25),(side*.86,1.45,-3.45),
            (side*.65,1.63,-2.93)],body)
        panel('Shrike aft extractor pocket',[
            (side*.92,1.30,-2.53),(side*1.13,1.33,-2.81),
            (side*1.06,1.13,-3.31),(side*.86,1.15,-3.07)],carbon)
        # Three small close-coupled aerodynamic vanes remain within vehicle width.
        for index in range(3):
            z=-2.92-index*.16
            panel('Shrike close-coupled aft vane',[
                (side*.85,1.56,z+.18),(side*(.98+index*.045),1.64,z-.12),
                (side*.78,1.55,z-.04)],steel if index==0 else carbon)
        pipe('Shrike tail light blade',(side*.28,1.36,-3.53),
             (side*.79,1.41,-3.48),.028,glow,12)
    # Integrated dark aerodynamic roof spine / shallow cooling duct.
    panel('Shrike inset dorsal cooling spine',[
        (-.23,1.70,-2.02),(-.20,1.60,-2.60),
        (-.11,1.50,-3.13),(.11,1.50,-3.13),
        (.20,1.60,-2.60),(.23,1.70,-2.02)],carbon)
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
        pipe('Shrike embedded vector jet',(x,1.20,-3.25),
             (x,1.20,-3.51),.09,carbon,12)
        pipe('Shrike jet inner',(x,1.20,-3.48),(x,1.20,-3.54),.05,glow,12)
        rig('Kestrel_Tail_%d'%i,since(before),(x,1.20,-3.25))
