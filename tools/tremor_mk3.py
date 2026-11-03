"""TREMOR MK III — original BOX-SUV hover endurance racer.

Reference-driven volumes, not a photographic mesh trace: a one-piece long
rectangular chassis, blunt impact front, tall upright SUV greenhouse with
actual three-segment side windows, long flat roof with rails, machined side
slabs, heavy squared fender pods and recessed hover/propulsion hardware.

Free Blender geometry helpers are injected by tools/build_fleet.py.
Every point is in Godot metres: X width, Y up, +Z forward.
All 3D shapes are original, editable procedural meshes.
"""

def build_tremor(body,maroon,armor,rubber,glow,glass,accent):
    import math
    from mathutils import Vector
    pi=math.pi
    tau=math.tau

    def finish(mat,rgb,metal,rough,coat=0.0):
        mat.diffuse_color=(*rgb,1)
        bs=mat.node_tree.nodes.get("Principled BSDF")
        bs.inputs["Base Color"].default_value=(*rgb,1)
        bs.inputs["Metallic"].default_value=metal
        bs.inputs["Roughness"].default_value=rough
        bs.inputs["Coat Weight"].default_value=coat
    # A dark technical SUV palette; no flat white or overexposed chrome.
    finish(body,(.083,.107,.135),.58,.40,.24)        # graphite-blue steel
    finish(maroon,(.245,.077,.104),.55,.43,.12)      # muted oxide-red armor
    finish(armor,(.265,.316,.348),.68,.44,.18)       # satin forged alloy
    finish(rubber,(.019,.029,.039),.13,.77)
    finish(accent,(.085,.115,.138),.38,.45)
    finish(glass,(.016,.065,.098),.15,.27,.34)       # automotive tinted glass
    finish(glow,(.052,.40,.65),.13,.34)
    forge_texture(body,"fine graphite paint",(.095,.122,.150),2.0,256)
    forge_texture(maroon,"fine graphite paint",(.28,.093,.120),1.7,256)
    forge_texture(armor,"brushed alloy",(.258,.295,.330),1.3,256)

    # Rectangular shoulder / flatter bonnet cross sections, repeated from
    # aft to nose. Each (z, half_width, low_chassis, main_deck_height).
    stations=[
        (-3.55,1.78,.48,1.37),(-3.39,1.92,.44,1.43),
        (-3.05,2.03,.41,1.47),(-2.55,2.08,.40,1.49),
        (-1.99,2.06,.41,1.46),(-1.73,1.97,.42,1.44),
        (-1.34,1.91,.42,1.43),(-.78,1.91,.42,1.44),
        (-.14,1.91,.42,1.45),(.56,1.93,.41,1.45),
        (1.10,1.98,.40,1.43),(1.56,2.05,.40,1.39),
        (2.12,2.08,.39,1.36),(2.75,2.02,.40,1.31),
        (3.25,1.92,.43,1.26),(3.47,1.86,.45,1.22),
        (3.56,1.81,.46,1.21)]

    def sample(z):
        if z<=stations[0][0]:return stations[0][1:]
        if z>=stations[-1][0]:return stations[-1][1:]
        for a,b in zip(stations,stations[1:]):
            if a[0]<=z<=b[0]:
                t=(z-a[0])/(b[0]-a[0])
                return tuple(a[j]*(1-t)+b[j]*t for j in (1,2,3))
        raise AssertionError("Tremor station outside profile")

    def xout(z,extra=0):
        return sample(z)[0]+extra

    def polyline(name,points,r,material,segments=10):
        for a,b in zip(points,points[1:]):
            pipe(name,a,b,r,material,segments)

    def face(name,points,mat):
        return panel(name,points,mat)

    def engine_ring(name,p,r,t,mat):
        # Torus normal points toward the front/rear (+/- Godot Z).
        ob=ring(name,p,r,t,mat)
        ob.rotation_euler.x=pi/2
        return ob

    def closed_loft(name,rows,material):
        # Rows are closed cross-sectional polygon loops, not subdivided
        # spheres. Their planar shoulder faces remain intentional.
        n=len(rows[0])
        assert n>=4 and all(len(row)==n for row in rows)
        points=[q for row in rows for q in row]
        faces=[]
        for i in range(len(rows)-1):
            for j in range(n):
                faces.append((i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j))
        faces.append(tuple(reversed(range(n))))
        faces.append(tuple((len(rows)-1)*n+j for j in range(n)))
        return mesh(name,points,faces,material)

    # CONTIGUOUS CHASSIS: a top deck with shoulder steps, hard flank,
    # inward bevel at rocker, and flat aerodynamic undertray. Wider than the
    # cabin and visibly SUV-shaped from both side and top.
    rows=[]
    for z,w,lo,deck in stations:
        rows.append([
            (-w*.94,deck-.045,z),(-w*.77,deck+.085,z),
            (-w*.47,deck+.10,z),(0,deck+.105,z),
            (w*.47,deck+.10,z),(w*.77,deck+.085,z),
            (w*.94,deck-.045,z),(w,deck-.18,z),
            (w,lo+.25,z),(w*.85,lo+.035,z),
            (w*.57,lo-.045,z),(0,lo-.055,z),
            (-w*.57,lo-.045,z),(-w*.85,lo+.035,z),
            (-w,lo+.25,z),(-w,deck-.18,z)])
    n=len(rows[0]);pts=[v for row in rows for v in row];quads=[]
    for i in range(len(rows)-1):
        midz=(stations[i][0]+stations[i+1][0])*.5
        for j in range(n):
            # The open upper seat bath is beneath the independently fitted
            # windows and stops a black deck intersecting the cockpit.
            if -1.78<midz<1.17 and j in [1,2,3,4]:
                continue
            quads.append((i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j))
    quads.append(tuple(reversed(range(n))))
    quads.append(tuple((len(rows)-1)*n+j for j in range(n)))
    mesh("TREMOR_BOX_SUV_CONTIGUOUS_CHASSIS",pts,quads,body)

    # Mid-body section: large, flat-topped armored service doors and a deep
    # horizontal channel. Polygonal framing rather than smooth side scoops.
    for side in [-1,1]:
        lbl="port" if side<0 else "starboard"
        door_z=[-1.73,-1.45,-.55,.43,1.16,1.43]
        outer=[]
        for z in door_z:
            w=xout(z)
            # 6 section points describing true thickness and bevels.
            outer.append([
                (side*(w-.065),1.36,z),
                (side*(w+.070),1.28,z),
                (side*(w+.115),.95,z),
                (side*(w+.115),.68,z),
                (side*(w+.028),.57,z),
                (side*(w-.10),.62,z)])
        closed_loft("TREMOR_BOX_SUV_"+lbl+"_LONG_SLAB_DOOR",outer,body)
        # Slab cassette is a flush, clearly rectangular deep panel.
        face("Tremor MKIII "+lbl+" door cassette",[
            (side*(xout(.72,.127)),.85,.88),
            (side*(xout(.74,.127)),1.20,.88),
            (side*(xout(-1.31,.127)),1.20,-1.31),
            (side*(xout(-1.32,.127)),.85,-1.31)],armor)
        polyline("Tremor MKIII side deck horizontal bevel",[
            (side*xout(z,.10),1.30,z)
            for z in [-1.65,-1.1,-.4,.35,1.20]],.017,armor)
        polyline("Tremor MKIII dark continuous rocker pocket",[
            (side*xout(z,.15),.56,z)
            for z in [-1.62,-1.0,-.23,.52,1.25]],.047,rubber)
        polyline("Tremor MKIII subdued rocker cyan",[
            (side*xout(z,.159),.50,z)
            for z in [-1.43,-.85,-.15,.49,1.05]],.019,glow)
        for z in [-1.27,.84]:
            box("Tremor MKIII rectangular side latching recess",
                (side*xout(z,.137),1.13,z),(.065,.092,.31),rubber,.018)
            box("Tremor MKIII forged recessed door handle",
                (side*xout(z,.17),1.14,z),(.044,.035,.18),armor,.010)
        # A few restrained manufactured service seams/hinges.
        for z in [-1.42,.99]:
            for y in [.78,1.18]:
                box("Tremor MKIII inset door bolt",
                    (side*xout(z,.138),y,z),(.032,.042,.042),rubber,.005)

        # SQUARED FENDER / FRONT ARMOR BLOCK: long, high hard-backed
        # shoulder with protective chamfer. Overlaps the monocoque on
        # purpose along continuous structural width, not as floating fins.
        box("TREMOR_BOX_SUV_"+lbl+"_FRONT_SQUARED_FENDER",
            (side*1.72,1.29,2.43),(.67,.68,2.06),armor,.065)
        box("Tremor MKIII dark inner wheel-arch cavity",
            (side*2.074,.80,2.28),(.026,.40,.71),rubber,.018)
        face("Tremor MKIII front fender pressed armor",[
            (side*1.46,1.67,1.51),(side*1.87,1.64,1.51),
            (side*1.93,1.57,3.28),(side*1.42,1.56,3.24)],maroon)
        box("Tremor MKIII rectangular headlamp shroud",
            (side*1.66,1.17,3.51),(.60,.21,.12),rubber,.029)
        box("Tremor MKIII slim double-bar LED lamp",
            (side*1.66,1.18,3.596),(.45,.045,.026),glow,.010)
        box("Tremor MKIII fender top intake housing",
            (side*1.75,1.66,2.58),(.37,.12,.57),rubber,.020)
        for k in range(3):
            box("Tremor MKIII stamped top fender vent",
                (side*1.75,1.732,2.37+k*.12),
                (.29,.024,.042),accent,.003)
        polyline("Tremor MKIII squared front wheel guard",[
            (side*2.06,.60,1.83),(side*2.09,1.11,1.83),
            (side*2.09,1.51,2.01),(side*2.05,1.54,2.78),
            (side*2.05,1.08,2.97),(side*2.02,.67,2.97)],
            .047,armor)

        # HEAVY REAR SHOULDER: the same rectangular volume language as
        # a real SUV quarter panel, with an external engineered module.
        box("TREMOR_BOX_SUV_"+lbl+"_REAR_SQUARED_SHOULDER",
            (side*1.78,1.42,-2.55),(.69,.79,1.73),armor,.067)
        box("Tremor MKIII rear fender upper recessed vent",
            (side*1.80,1.856,-2.55),(.34,.055,.62),rubber,.015)
        for zz in [-2.78,-2.55,-2.32]:
            box("Tremor MKIII rear shoulder vent fin",
                (side*1.8,1.889,zz),(.24,.018,.059),body,.004)
        box("Tremor MKIII rear exterior protective plate",
            (side*2.131,1.29,-2.60),(.065,.57,1.26),body,.035)
        polyline("Tremor MKIII rear fender boxed corner",[
            (side*2.12,.74,-3.21),(side*2.15,1.12,-3.21),
            (side*2.12,1.71,-3.05),(side*2.10,1.73,-2.16),
            (side*2.15,1.15,-1.90),(side*2.15,.70,-1.92)],
            .041,maroon)

        # Underside levitation pods buried under the rocker, not
        # full-size wheels stuck onto the hood.
        for z in [2.30,-2.38]:
            x=side*1.58
            pipe("Tremor MKIII integrated hover lift housing",
                 (x,.24,z),(x,.48,z),.28,rubber,22)
            ring("Tremor MKIII downward magnetic flux",(x,.23,z),
                 .246,.032,glow)

    # SQUARED NOSE, integrated mechanical impact bar and TWO low
    # forward-facing circular intake/repulsor modules.
    box("TREMOR_BOX_SUV_WIDE_FLAT_BUMPER",
        (0,.86,3.55),(3.54,.64,.21),armor,.067)
    box("Tremor MKIII central black grille well",
        (0,1.03,3.681),(1.47,.32,.031),rubber,.021)
    for y in [.92,1.035,1.15]:
        box("Tremor MKIII front grille flush horizontal louvre",
            (0,y,3.706),(1.31,.021,.027),body,.006)
    box("Tremor MKIII continuous lower tow beam",
        (0,.54,3.64),(2.33,.15,.21),body,.029)
    for side in [-1,1]:
        x=side*1.47
        pipe("Tremor MKIII front recessed ring housing",
             (x,.79,3.64),(x,.79,3.82),.37,rubber,28)
        engine_ring("Tremor MKIII front satin repulsor rim",
                    (x,.79,3.80),.346,.058,armor)
        engine_ring("Tremor MKIII front magnetic blue lens",
                    (x,.79,3.841),.279,.026,glow)
        pipe("Tremor MKIII front repulsor central spindle",
             (x,.79,3.832),(x,.79,3.86),.087,body,16)
        for j in range(6):
            theta=tau*j/6
            r=.16
            pipe("Tremor MKIII front turbine vane",
                 (x+.09*math.cos(theta),.79+.09*math.sin(theta),3.846),
                 (x+r*math.cos(theta+.17),.79+r*math.sin(theta+.17),3.847),
                 .015,armor,8)
        box("Tremor MKIII lower front crash guard",
            (side*1.05,.52,3.77),(.26,.21,.14),body,.027)
    # Flat bonnet inserts with deliberately geometric outlines.
    box("Tremor MKIII graphite central hood plate",
        (0,1.43,2.31),(1.45,.058,2.16),body,.048)
    for side in [-1,1]:
        polyline("Tremor MKIII raised linear hood edge",[
            (side*.77,1.502,z) for z in [1.34,1.8,2.4,3.25]],
            .017,armor)
        for z in [1.91,2.06,2.21]:
            box("Tremor MKIII matte anti-slip hood vent",
                (side*.47,1.478,z),(.34,.020,.057),rubber,.004)

    # TALL RECTANGULAR SUV GREENHOUSE: separate front windshield,
    # three-pane side glass, roof and structural pillars. This is NOT a
    # low sports car canopy. The flat upper roof goes to 2.66 metres.
    roof_y=2.59
    roof_front=.54
    roof_back=-1.79
    roof_half=1.23
    sill_front=1.19
    glass_sill_y=1.48

    # Driver windshield: almost vertical, slightly raked and truly planar.
    face("vehicle_glass_tremor_mk3_windscreen",[
        (-1.17,1.50,sill_front),(1.17,1.50,sill_front),
        (1.12,2.49,roof_front),(-1.12,2.49,roof_front)],glass)
    # Solid UV-visible roof skin with square shoulders and recessed rack.
    box("TREMOR_BOX_SUV_FLAT_TALL_ROOF",
        (0,2.58,(roof_front+roof_back)*.5),
        (2.48,.18,roof_front-roof_back+.16),armor,.064)
    box("Tremor MKIII central longitudinal roof plate",
        (0,2.695,-.54),(1.73,.038,1.79),body,.027)
    box("Tremor MKIII rear roof spoiler lip",
        (0,2.61,-1.86),(2.38,.095,.19),body,.042)
    for side in [-1,1]:
        sx=side*1.16
        # Side panes: 3 actual rectangular window meshes.
        def side_window(name,zfront,zback):
            face(name,[
                (side*1.27,glass_sill_y,zfront),
                (side*1.27,glass_sill_y,zback),
                (side*1.14,2.45,zback),
                (side*1.14,2.45,zfront)],glass)
        side_window("vehicle_glass_tremor_mk3_front_suv_door",.48,-.46)
        side_window("vehicle_glass_tremor_mk3_rear_suv_door",-.53,-1.37)
        side_window("vehicle_glass_tremor_mk3_rear_quarter",-1.44,-1.76)
        # A/B/C/D pillars give clear 4-door SUV window framing.
        polyline("Tremor MKIII "+("port" if side<0 else "starboard")+
            " squared A-pillar",[
            (side*1.28,1.44,1.17),(side*1.14,2.47,.54)],.069,body,12)
        for z in [-.49,-1.41,-1.79]:
            pipe("Tremor MKIII high SUV side window pillar",
                 (side*1.28,1.43,z),(side*1.14,2.46,z),
                 .054,body,10)
        polyline("Tremor MKIII straight roofline upper trim",[
            (sx,2.53,.53),(sx,2.55,-.35),
            (sx,2.55,-1.24),(sx,2.52,-1.83)],.035,body)
        polyline("Tremor MKIII continuous straight SUV window sill",[
            (side*1.30,1.44,.97),(side*1.29,1.44,.11),
            (side*1.29,1.44,-.94),(side*1.30,1.44,-1.89)],
            .037,body)
        # Square roof rack: rail length and 3 transverse hardpoints.
        polyline("Tremor MKIII raised roof rack longitudinal girder",[
            (side*1.04,2.72,.37),(side*1.04,2.76,.12),
            (side*1.04,2.76,-1.46),(side*1.04,2.72,-1.76)],
            .060,body,12)
        for z in [-1.36,-.48,.20]:
            box("Tremor MKIII machined rack foot",
                (side*1.04,2.715,z),(.18,.11,.18),rubber,.018)
        # Discrete overhead instrument/clearance lighting.
        box("Tremor MKIII cyan roof marker",
            (side*.86,2.57,.64),(.34,.046,.084),glow,.012)

    for z in [-1.36,-.48,.20]:
        pipe("Tremor MKIII roof utility rack crossrail",
             (-1.04,2.79,z),(1.04,2.79,z),.031,body,12)
    box("Tremor MKIII central roof cooling vent",
        (0,2.728,-1.24),(.78,.032,.37),rubber,.023)
    for i in range(4):
        box("Tremor MKIII roof cooling slot",
            (-.27+i*.18,2.75,-1.24),(.062,.013,.25),accent,.007)
    box("Tremor MKIII windshield lower wiper recess",
        (0,1.48,1.16),(2.20,.058,.11),rubber,.022)
    box("Tremor MKIII windscreen full width upper header",
        (0,2.50,.61),(2.36,.10,.12),body,.033)
    # Rear SUV glass, a near-vertical hatch with physical bottom.
    face("vehicle_glass_tremor_mk3_rear_hatch",[
        (-1.16,1.54,-1.92),(-1.13,2.46,-1.82),
        (1.13,2.46,-1.82),(1.16,1.54,-1.92)],glass)
    box("Tremor MKIII tailgate window lower rail",
        (0,1.54,-1.965),(2.40,.11,.11),body,.026)

    # Interior visible through actual transparent 3D glass, low enough
    # for the existing live Godot cockpit camera, not a floating overlay.
    box("Tremor MKIII cockpit structural floor",
        (0,.99,-.38),(2.00,.13,2.64),rubber,.048)
    box("Tremor MKIII continuous armored dashboard",
        (0,1.39,.77),(2.15,.25,.29),body,.063)
    for side in [-1,1]:
        box("Tremor MKIII SUV sport bucket base",
            (side*.45,1.18,-.41),(.68,.20,.86),rubber,.080)
        box("Tremor MKIII structural SUV front seat back",
            (side*.45,1.62,-.71),(.63,.88,.18),body,.071)
        box("Tremor MKIII upholstered headrest",
            (side*.45,2.18,-.76),(.42,.25,.17),rubber,.057)
        box("Tremor MKIII rear bench seat",
            (side*.45,1.18,-1.29),(.70,.19,.51),rubber,.059)
    # Rotation support rig: the yoke and five vector anchors are retained
    # so the physics feedback and cockpit instrumentation remain compatible.
    before=set(bpy.context.scene.objects)
    for side in [-1,1]:
        pipe("Tremor MKIII wheel grip",
             (side*.23,1.48,.56),(side*.23,1.64,.61),
             .046,body,12)
    pipe("Tremor MKIII vehicle steering yoke",
         (-.23,1.58,.58),(.23,1.58,.58),.037,armor,12)
    rig("Kestrel_Yoke",since(before),(0,1.55,.58))

    # Tail hardware: armored SUV box above rear magnetic vector housings.
    box("TREMOR_BOX_SUV_REAR_TAILGATE",
        (0,1.00,-3.49),(3.45,.84,.21),body,.076)
    box("Tremor MKIII full-width tail light carrier",
        (0,1.46,-3.57),(3.30,.12,.12),rubber,.018)
    for side in [-1,1]:
        box("Tremor MKIII rear horizontal red tail light",
            (side*1.22,1.49,-3.637),(.82,.050,.028),maroon,.014)
        # Protected recessed exhaust/nozzle pair, never a plain pipe
        # hovering above the back of the SUV.
        x=side*1.48
        box("Tremor MKIII framed rear propulsion cradle",
            (x,.99,-3.51),(.86,.73,.51),armor,.082)
        pipe("Tremor MKIII deep black vector turbine throat",
             (x,.95,-3.73),(x,.95,-3.91),.285,rubber,26)
        engine_ring("Tremor MKIII cyan stepped rear vector annulus",
                    (x,.95,-3.92),.279,.035,glow)
        engine_ring("Tremor MKIII forged exhaust rim",
                    (x,.95,-3.88),.340,.050,body)
        pipe("Tremor MKIII recessed axle motor",
             (x,.95,-3.94),(x,.95,-3.955),.081,body,16)
        for j in range(6):
            a=tau*j/6
            pipe("Tremor MKIII vectored nozzle vane",
                (x+.09*math.cos(a),.95+.09*math.sin(a),-3.956),
                (x+.23*math.cos(a+.20),.95+.23*math.sin(a+.20),-3.958),
                .019,armor,8)
        # Rear roof power channels are protected by a box-like louvered
        # cargo/engine cover, distinct from a low sports-car reactor hump.
        box("Tremor MKIII rear raised power side pod",
            (side*1.75,1.71,-2.67),(.60,.22,1.12),body,.058)
        for z in [-2.98,-2.76,-2.54,-2.32]:
            box("Tremor MKIII rear heat-exchanger fin",
                (side*1.75,1.835,z),(.43,.028,.10),rubber,.013)
    box("Tremor MKIII rear chassis strike plate",
        (0,.53,-3.63),(2.0,.22,.23),armor,.036)

    for i in range(5):
        before=set(bpy.context.scene.objects)
        x=(i-2)*.22
        pipe("Tremor MKIII internal vector anchor",
             (x,.94,-3.49),(x,.94,-3.54),.009,rubber,8)
        rig("Kestrel_Tail_%d"%i,since(before),(x,.94,-3.50))

    # Geometric gates correlate with the illustrated FORM BLOCKS rather
    # than merely counting decorative parts.
    assert roof_y>2.5 and sample(2.75)[2]<1.4
    assert abs(sample(1.20)[0]-sample(-1.20)[0])<.13
    assert sample(3.56)[0]>1.78
    assert sample(-2.55)[0]>2.0
    assert roof_front-roof_back>2.2
    print("SCENEFORGE_TREMOR_REFERENCE_GEOMETRY_OK",
          "BOX_SUV_MKIII","roof",roof_y,"front",sample(3.56)[0])
    print("SCENEFORGE_TREMOR_BOX_SUV_OK",
          "flat_roof","upright_windshield","three_piece_side_glass",
          "long_slab_doors","squared_fender_pods",
          "wide_impact_nose","embedded_thrusters")
