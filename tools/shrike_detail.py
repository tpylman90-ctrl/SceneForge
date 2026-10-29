"""Shrike MK I hard-surface refinement. Original procedural meshes, Godot coordinates."""
def detail_shrike(body,accent,carbon,steel,rubber,glow,glass):
    # These plates layer over the existing monocoque, preserving cockpit and rig anchors.
    for side in (-1,1):
        # Swept shoulder bridge and deep faceted side armor.
        panel('Shrike upper titanium shoulder',[
            (side*.72,1.30,1.30),(side*.96,1.34,.70),
            (side*1.12,1.30,-.50),(side*.98,1.26,-1.62),
            (side*.71,1.29,-1.82),(side*.66,1.25,-.50)],body)
        panel('Shrike inset flank armor',[
            (side*.88,1.12,1.05),(side*1.06,.87,.40),
            (side*1.11,.75,-1.37),(side*.94,.94,-1.75),
            (side*.83,1.12,-.48)],steel)
        panel('Shrike carbon side intake recess',[
            (side*1.11,1.16,-.45),(side*1.23,1.01,-1.18),
            (side*1.04,.82,-1.57),(side*.96,1.10,-.70)],carbon)
        for n in range(5):
            z=-.66-n*.16
            pipe('Shrike intake stator',
                 (side*1.19,.91,z),(side*1.12,1.10,z-.07),.020,steel,8)
        # Raised trim follows the actual aerodynamic panel contour.
        edge=[(side*.76,1.34,1.26),(side*.99,1.38,.66),
              (side*1.15,1.34,-.52),(side*1.00,1.30,-1.59)]
        for a,b in zip(edge,edge[1:]):
            pipe('Shrike orange shoulder seam',a,b,.014,accent,10)
        # Sharp layered nose chine, without copying Piledriver skis.
        panel('Shrike split spear wing',[
            (side*.06,.52,3.82),(side*.36,.66,3.16),
            (side*.65,.76,2.19),(side*.32,.65,2.46)],body)
        panel('Shrike nose carbon inset',[
            (side*.14,.57,3.46),(side*.37,.71,2.69),
            (side*.42,.73,2.24),(side*.25,.75,2.70)],carbon)
        pipe('Shrike nose accent', (side*.16,.61,3.43),
             (side*.43,.78,2.24),.013,accent,10)
        # Hover pod fairings: original moving hardware remains unobstructed.
        for x,y,z in [(side*1.0,.58,2.10),(side*1.12,.76,-.65)]:
            panel('Shrike repulsor mount wing',[
                (side*.76,y+.31,z+.46),(x,y+.25,z+.25),
                (side*(abs(x)+.18),y+.13,z-.27),
                (side*.76,y+.26,z-.34)],body)
            pipe('Shrike mount actuator',
                 (side*.79,y+.30,z+.27),(x,y+.14,z),.035,steel,12)
            ring('Shrike upper halo accent',(x,y+.23,z),.315,.012,glow)
            for k in range(6):
                a=math.tau*k/6
                box('Shrike rim bolt',
                    (x+.29*math.cos(a),y+.21,z+.29*math.sin(a)),
                    (.027,.022,.027),steel,.003)
        # Winglets and independent stabilizer rails.
        panel('Shrike swept aft wing',[
            (side*.90,1.19,-1.30),(side*1.48,1.23,-2.12),
            (side*1.71,1.36,-2.67),(side*1.08,1.24,-2.39)],body)
        pipe('Shrike orange wing edge',
             (side*1.08,1.27,-2.37),(side*1.68,1.39,-2.67),
             .014,accent,10)
        for n in range(3):
            panel('Shrike layered aft fin',[
                (side*(.75+n*.13),1.55,-1.78),
                (side*(1.04+n*.17),1.66,-2.58),
                (side*(.80+n*.13),1.55,-2.45)],carbon)
        # Rear extractor, heat shields, mechanical hoses.
        for n in range(4):
            z=-1.61-n*.17
            pipe('Shrike extractor vane',(side*.88,1.12,z),
                 (side*1.02,1.23,z-.055),.026,steel,10)
        pipe('Shrike cooling line',(side*.71,.70,-1.08),
             (side*.90,.91,-2.09),.028,accent,12)
        for z in [-1.15,-1.55,-1.95]:
            box('Shrike hardline clip',(side*.81,.82,z),
                (.085,.06,.055),carbon,.008)
        # Tight sporty interior around existing seat and wheel.
        panel('Shrike fitted cockpit cheek',[
            (side*.46,.90,.81),(side*.65,1.13,.75),
            (side*.66,1.34,-.30),(side*.51,1.25,-1.06),
            (side*.39,.84,-.74)],carbon)
        box('Shrike seat side bolster',
            (side*.29,1.11,-.25),(.17,.28,.78),rubber,.05)
        box('Shrike shoulder clamp',
            (side*.31,1.42,-.53),(.17,.35,.29),carbon,.04)
        for z in [-.90,-.50,-.10,.30]:
            box('Shrike flush service head',
                (side*1.07,.81,z),(.028,.035,.035),accent,.003)
    # Separate rear heat diffuser and sculpted longitudinal dorsal hood.
    panel('Shrike dorsal crest',[
        (-.34,1.18,1.36),(-.24,1.02,2.30),(0,.53,3.80),
        (.24,1.02,2.30),(.34,1.18,1.36)],body)
    for side in (-1,1):
        pipe('Shrike hood blade edge',
             (side*.29,1.18,1.37),(side*.12,.73,3.15),.012,accent,10)
    box('Shrike rear heat shield',(0,1.25,-2.28),(1.20,.12,.52),carbon,.04)
    for x in [-.46,-.23,0,.23,.46]:
        box('Shrike diffuser vent',(x,1.33,-2.37),(.14,.03,.33),steel,.008)
