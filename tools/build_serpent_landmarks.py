"""Cohesive, wind-eroded sandstone escarpments for Crimson Serpent.

Invoked inside tools/build_serpent_rock_kit.py; uses its Blender session,
UV atlas helper, and original export contract. These are continuous rounded
cliff masses, NOT stacks of square prisms or detached stone columns.
"""
import math

def eroded_wall(name, width, height, depth, tile, seed, ridges):
    nx, nz = 23, 15
    verts, uv, faces = [], [], []
    stride = (nx+1)*(nz+1)

    def ridge_field(u, v):
        # Several broad erosion folds, with asymmetric widths and waviness.
        value = 0.0
        for offset, spread, power in ridges:
            path = offset + 0.04*math.sin(7.1*v + seed*.13 + offset*4)
            value += power*math.exp(-((u-path)/spread)**2)
        return value

    for back in range(2):
        for j in range(nz+1):
            v = j/nz
            # Change silhouette at several stratigraphic horizons without
            # forcing periodic, mechanical ring/terrace steps.
            taper = (1.0 - .15*v)
            for i in range(nx+1):
                u = i/nx
                rim = abs(2*u-1)
                edge_fade = max(0.0, (1-rim*rim))**1.45
                x = width*(u-.5)*taper
                x += (.75*math.sin(5.0*v+seed) +
                      .40*math.sin(10.0*v+seed*.7))*edge_fade
                crown = 1.0-.10*(rim**2)-.045*math.sin(9.1*u+seed*.16)**2
                z = height*v*crown
                z += .33*math.sin(u*12.0 + v*9.0 + seed)*v*(1-v)
                fold = ridge_field(u,v)
                sediment = .43*math.sin(2*math.pi*(4.3*v+.16*math.sin(u*7.0+seed)))
                sediment += .24*math.cos(2*math.pi*(7.7*v+.09*math.sin(u*13.0)))
                # A smooth shelf blends into the face over >1 m of height,
                # unlike the former 1.2 / 0.8 jagged ring alternations.
                lip = 1.20*math.tanh((v-.28)*22)
                lip += .73*math.tanh((v-.68)*20)
                fracture = -.95*math.exp(-((u-(.37+.06*math.sin(v*7+seed)))/.043)**2)
                front = (.23*depth + .68*depth*fold + lip + sediment
                         + fracture + .25*math.sin(u*21+v*12+seed))
                front = -depth*.72 + (front+depth*.72)*edge_fade
                front *= (0.24+0.76*min(1.0,v/.14))
                y = (-depth-1.8) if back else front
                verts.append((x,y,z))
                uv.append(atlas_uv(tile,u,v))
    def index(back,i,j):
        return back*stride + j*(nx+1) + i
    for j in range(nz):
        for i in range(nx):
            a,b,c,d = index(0,i,j),index(0,i+1,j),index(0,i+1,j+1),index(0,i,j+1)
            e,f,g,h = index(1,i,j),index(1,i+1,j),index(1,i+1,j+1),index(1,i,j+1)
            faces.extend(((a,c,b),(a,d,c),(e,f,g),(e,g,h)))
    for j in range(nz):
        for i in (0,nx):
            a,b,c,d = index(0,i,j),index(0,i,j+1),index(1,i,j+1),index(1,i,j)
            faces.extend(((a,b,c),(a,c,d)))
    for i in range(nx):
        for j in (0,nz):
            a,b,c,d=index(0,i,j),index(0,i+1,j),index(1,i+1,j),index(1,i,j)
            faces.extend(((a,b,c),(a,c,d)))
    mesh=bpy.data.meshes.new(name+"_mesh")
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    uv_layer=mesh.uv_layers.new(name="UVMap")
    for p in mesh.polygons:
        p.use_smooth=True
        for loop_id in p.loop_indices:
            uv_layer.data[loop_id].uv=uv[mesh.loops[loop_id].vertex_index]
    obj=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    return obj

def make_landmarks():
    # One continuous rock face per archetype; 3 total landmark placements.
    # Lower and wider profiles blend with the existing Terrain3D relief.
    return [
        eroded_wall("sunstone_fang",38.0,33.0,8.8,2,211,
                    [(.23,.21,.80),(.71,.18,.70)]),
        eroded_wall("strata_buttress",48.0,31.0,10.2,0,277,
                    [(.17,.17,.48),(.53,.26,.95),(.82,.16,.40)]),
        eroded_wall("split_chimney",41.0,35.0,9.5,1,339,
                    [(.27,.19,.83),(.77,.14,.90)]),
    ]

def bake_rock_color(obj):
    """Offline diffuse + cavity tint. No mobile AO/normal shader reads."""
    mesh=obj.data
    colors=mesh.color_attributes.new(name="BakedGeology",type="FLOAT_COLOR",domain="CORNER")
    highest=max(v.co.z for v in mesh.vertices)
    for p in mesh.polygons:
        n=p.normal
        for l in p.loop_indices:
            v=mesh.vertices[mesh.loops[l].vertex_index].co
            height=v.z/max(.001,highest)
            strata=math.sin(height*16.0+v.x*.13)
            # Smooth color; cavity creases still show, avoiding patchwork facets.
            shade=.88+.075*max(0.0,n.y)+.045*height+.028*strata
            shade-=.035*max(0.0,-n.y)
            if n.z<-.45:
                shade*=.82
            shade=max(.68,min(1.0,shade))
            colors.data[l].color=(shade,shade*.985,shade*.964,1.0)
