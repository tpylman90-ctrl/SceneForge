"""Shrike smooth-body redesign: integrated enclosed hovercar, original geometry."""
def build_shrike(body,accent,carbon,steel,rubber,glow,glass):
    import math
    from mathutils import Vector
    # Temporary shape-review clay: darker neutral graphite prevents sunlit clipping.
    # Revert to original silver/orange livery only after geometry approval.
    body.diffuse_color=(.23,.29,.35,1)
    bs=body.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value=body.diffuse_color
    bs.inputs['Roughness'].default_value=.65
    bs.inputs['Metallic'].default_value=.16
    bs.inputs['Coat Weight'].default_value=.08
    # Reference-led controlled cross-section loft. Each ring has independent
    # waist width, hood crown, shoulder height, sill and rear deck control.
    # Positive Z = nose; negative Z = tail. No applied fender attachments.
    stations=[(-3.55,.80,.51,1.39),(-3.35,.96,.44,1.53),
              (-3.03,1.09,.39,1.60),(-2.55,1.20,.36,1.65),
              (-2.05,1.22,.34,1.66),(-1.30,1.20,.32,1.68),
              (-.50,1.18,.30,1.54),(.40,1.18,.29,1.47),
              (1.18,1.23,.28,1.36),(1.82,1.28,.28,1.16),
              (2.40,1.29,.30,1.00),(2.83,1.24,.32,.89),
              (3.15,1.10,.36,.77),(3.40,.89,.40,.68)]
    # Synapse-style cubic profile blending, parameterized by actual distance.
    # Unlike smoothstep, this retains a continuous nonzero tangent at each
    # station; flat spots in side reflections are no longer baked into the loft.
    def profile(z):
        for k in range(len(stations)-1):
            a,b=stations[k:k+2]
            if a[0] <= z <= b[0]:
                span=b[0]-a[0]
                t=(z-a[0])/span
                t2=t*t
                t3=t2*t
                before=stations[max(0,k-1)]
                after=stations[min(len(stations)-1,k+2)]
                result=[]
                for axis in range(1,4):
                    left=(b[axis]-before[axis])/(b[0]-before[0])
                    right=(after[axis]-a[axis])/(after[0]-a[0])
                    value=((2*t3-3*t2+1)*a[axis]
                           +(t3-2*t2+t)*span*left
                           +(-2*t3+3*t2)*b[axis]
                           +(t3-t2)*span*right)
                    result.append(value)
                return result
        return list(stations[0][1:] if z<stations[0][0] else stations[-1][1:])
    segment_count=84
    n=24
    points=[]
    for k in range(segment_count+1):
        z=-3.55+6.95*k/segment_count
        w,low,high=profile(z)
        front=math.exp(-((z-2.20)/.79)**2)
        rear=math.exp(-((z+2.35)/.95)**2)
        waist=math.exp(-((z-.05)/1.1)**2)
        # Sidewalls and top have authored independent contours.
        max_width=w+.17*front+.20*rear-.055*waist
        for j in range(n):
            angle=math.tau*j/n
            u=abs(math.cos(angle))
            sin_a=math.sin(angle)
            x=max_width*math.cos(angle)
            if sin_a>=0:
                # Raised shoulders at 70-85% of half-width, with an
                # unobstructed lower center hood / flat rear deck.
                shoulder=math.exp(-((u-.77)/.17)**2)
                top_curve=(1-u*u)**.55
                central=high-.09*front-.075*rear
                side_level=(high+low)*.5+.055
                y=side_level+(central-side_level)*top_curve
                y+=shoulder*(.27*front+.20*rear)*(sin_a**.65)
                # Flatter trunk surface without an exaggerated rear hump.
                y-=.035*rear*(1-u)**2
            else:
                side_level=(high+low)*.5+.055
                bottom_curve=(1-u*u)**.80
                y=side_level+(low-side_level)*bottom_curve
            points.append((x,y,z))
    faces=[]
    for k in range(segment_count):
        z_mid=-3.55+6.95*(k+.5)/segment_count
        for j in range(n):
            # Cockpit is genuinely open beneath the roof glazing.
            if -1.56<z_mid<1.36 and 2<=j<=10:
                continue
            a=k*n+j
            faces.append((a,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
    faces.append(tuple(reversed(range(n))))
    faces.append(tuple(segment_count*n+j for j in range(n)))
    shell=mesh('Shrike seamless flowing body',points,faces,body,0)
    for face in shell.data.polygons:
        face.use_smooth=True
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
