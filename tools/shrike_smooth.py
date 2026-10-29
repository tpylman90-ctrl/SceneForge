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
    stations=[(-2.85,.58,.63,1.12),(-2.55,.94,.47,1.31),
              (-1.9,1.16,.38,1.53),(-1.15,1.27,.34,1.58),
              (-.35,1.28,.31,1.54),(.50,1.21,.29,1.51),
              (1.22,1.10,.29,1.38),(1.85,.94,.28,1.22),
              (2.52,.69,.28,.94),(3.04,.42,.30,.70),
              (3.37,.24,.33,.53),(3.56,.08,.37,.45)]
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
            faces.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
    faces.extend([tuple(reversed(range(n))),tuple((len(segments)-1)*n+j for j in range(n))])
    shell=mesh('Shrike seamless flowing body',points,faces,body,.009)
    for face in shell.data.polygons:face.use_smooth=True
    # Broad recessed dark bonnet, flush headlights, and organic side crease.
    panel('Shrike hood black sculpted insert',[
       (-.38,1.28,1.75),(-.27,.98,2.65),(-.10,.55,3.40),
       (.10,.55,3.40),(.27,.98,2.65),(.38,1.28,1.75)],carbon)
    for s in [-1,1]:
        panel('Shrike sculpted orange side sweep',[
           (s*1.02,1.23,1.57),(s*1.20,1.06,.65),
           (s*1.23,.82,-.40),(s*1.02,.72,-1.57),
           (s*1.14,.82,-1.04),(s*1.30,1.01,.20)],accent)
        panel('Shrike continuous lower dark rocker',[
           (s*.96,.51,1.70),(s*1.19,.43,.51),
           (s*1.19,.42,-1.32),(s*.93,.53,-2.20)],carbon)
        panel('Shrike front slim optical blade',[
           (s*.32,.71,3.07),(s*.57,.77,2.75),
           (s*.72,.80,2.47),(s*.48,.79,2.64)],carbon)
        pipe('Shrike optical LED',(s*.38,.77,3.01),(s*.67,.85,2.52),.016,glow,10)
        # Flush hover propulsion hidden in underside rather than exposed barrels.
        for x,z in [(s*.94,1.95),(s*1.08,-1.22)]:
            ring('Shrike flush lower repulsor',(x,.265,z),.28,.035,carbon)
            ring('Shrike cyan repulsor halo',(x,.24,z),.23,.018,glow)
        # Rear brake light integrated with the haunch.
        pipe('Shrike rear light',(s*.35,1.23,-2.71),(s*.78,1.11,-2.55),.025,accent,12)
        # Side glazing as dark flush shapes; no exposed cage.
        panel('vehicle_glass_shrike_side',[
            (s*.64,1.50,1.02),(s*.84,1.54,.26),
            (s*.86,1.49,-.91),(s*.65,1.48,-1.49),
            (s*.60,1.66,-.75),(s*.58,1.69,.20)],glass)
        for z in [-1.70,-2.08]:
            pipe('Shrike recessed jet outlet',(s*.54,.99,z),
                 (s*.54,.99,z-.19),.12,carbon,20)
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
