"""Art-directed landmarks for Crimson Serpent; executed by build_serpent_rock_kit.

Three distinctive mesh families with deliberately oversized silhouettes:
Sunstone Fangs, Strata Buttress, and Split Chimneys. Every tower is composed
of separate irregular rock masses and real recessed gashes. No normal map
or paid model input; offline vertex shading and one UV atlas.
"""

def ringed_landmark(name, masses, tile, seed):
    vertices, uv, faces = [], [], []
    sides, layers = 18, 11
    for mass_index, (cx, cy, base_z, width, depth, height, lean) in enumerate(masses):
        start = len(vertices)
        for row in range(layers + 1):
            t = row / layers
            # Stepped erosion profiles change the silhouette, not a shader.
            shelf = 1.20 if row in (3, 7) else 0.80 if row in (4, 8) else 1.0
            taper = (1 - 0.39 * t) * shelf * (0.47 if row == layers else 1.0)
            for side in range(sides):
                angle = math.tau * side / sides
                facets = 1 + 0.115 * math.sin(5 * angle + .23 * seed + row * .19)
                facets += .065 * math.cos(9 * angle - seed * .31 + row * .17)
                scar_at = math.pi / 2 + .23 * math.sin(8 * t + seed)
                delta = math.atan2(math.sin(angle - scar_at), math.cos(angle - scar_at))
                cleft = .36 * math.exp(-(delta / .29) ** 2)
                radial = max(.31, (facets - cleft) * taper)
                x = cx + .5 * width * radial * math.cos(angle) + lean * t
                x += .46 * math.sin(t * 7.8 + seed + mass_index)
                y = cy + .5 * depth * radial * math.sin(angle)
                y += .28 * math.cos(3 * angle + 2 * t)
                z = base_z + height * t + .32 * math.sin(4 * angle + row * .43 + seed)
                vertices.append((x,y,z))
                uv.append(atlas_uv(tile, side / sides, t))
        for row in range(layers):
            for side in range(sides):
                a = start + row * sides + side
                b = start + row * sides + (side + 1) % sides
                c = start + (row + 1) * sides + (side + 1) % sides
                d = start + (row + 1) * sides + side
                faces.extend(((a,b,c),(a,c,d)))
        # Physical stone cap/foot: the gap between masses remains open.
        for side in range(1,sides-1):
            faces.append((start,start+side+1,start+side))
            top = start + layers*sides
            faces.append((top,top+side,top+side+1))
    mesh=bpy.data.meshes.new(name+"_mesh")
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    tex=mesh.uv_layers.new(name="UVMap")
    for polygon in mesh.polygons:
        polygon.use_smooth=False
        for lid in polygon.loop_indices:
            tex.data[lid].uv=uv[mesh.loops[lid].vertex_index]
    rock=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(rock)
    return rock

def make_landmarks():
    # Large shapes intended to reach ABOVE a 25-45m canyon rim.
    # Deliberate open slots, uneven height, stepped beds, leaning pinnacles.
    return [
        ringed_landmark("sunstone_fang", [
            (-2.0,-1.6,0.0,10.6,10.5,47.0,4.3),
            (8.1,-2.4,0.0,5.8,7.3,27.0,-1.9),
        ],2,211),
        ringed_landmark("strata_buttress", [
            (-7.4,-1.5,0.0,12.0,10.0,34.0,1.6),
            (3.7,-2.1,0.0,15.0,13.0,43.0,-2.8),
            (14.0,-1.4,0.0,8.0,8.0,26.0,-1.5),
        ],0,277),
        ringed_landmark("split_chimney", [
            (-5.6,-1.4,0.0,8.0,9.0,52.0,-2.7),
            (7.0,-3.3,0.0,8.4,9.6,42.0,3.8),
        ],1,339),
    ]

def bake_rock_color(obj):
    """Baked sediment illumination and dark undersides; zero GPU AO reads."""
    mesh=obj.data
    data=mesh.color_attributes.new(name="BakedGeology",type="FLOAT_COLOR",domain="CORNER")
    highest=max(vertex.co.z for vertex in mesh.vertices)
    for face in mesh.polygons:
        n=face.normal
        for lid in face.loop_indices:
            v=mesh.vertices[mesh.loops[lid].vertex_index].co
            height=v.z/max(.001,highest)
            strata=math.sin(height*35.0 + v.x*.21)
            seam=max(0.0,0.7-math.cos(height*51.0))*.07
            shade=.80+.11*max(0.0,n.y)+.075*height+.035*strata-seam
            if n.z < -.45:
                shade*=.73
            shade=max(.55,min(.99,shade))
            data.data[lid].color=(shade,shade*.973,shade*.947,1.0)
