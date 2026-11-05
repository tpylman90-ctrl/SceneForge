"""SOLSTICE S-01: original connected-surface hover GT for SceneForge.

Standalone, free Blender 4.5 authoring experiment. Does not touch the roster
or overwrite any approved craft. World units are metres; Godot +Z forward,
+Y vertical. Blender coordinates are converted through cv().
"""
import bisect
import json
import math
import os
import struct
from pathlib import Path

import bpy
from mathutils import Vector

OUT = Path(os.environ.get("SCENEFORGE_ORIGINAL_OUT", "build/original-solstice"))
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# Each station specifies (Godot Z, half width, bottom Y, central deck Y).
# The fenders are analytical deformations OF the same vertex grid, not
# separate objects or joined islands. Smooth piecewise Hermite interpolation
# avoids Catmull-Rom overshoot near the nose and tail.
STATIONS = [
    (-3.82, .90, .35, .83), (-3.50, 1.28, .32, 1.04),
    (-2.65, 1.64, .35, 1.21), (-1.45, 1.26, .37, 1.17),
    (-.20, 1.19, .36, 1.15), (1.26, 1.29, .34, 1.17),
    (2.42, 1.59, .33, 1.11), (3.31, 1.26, .30, .97),
    (4.08, .49, .34, .74),
]
NZ = 92
NR = 72
APERTURE_Z = (-1.48, 1.27)
APERTURE_THETA = 0.49

# S-01.5 lowered/countersunk greenhouse. Distances are authored in metres.
# The roof is intentionally a low aerodynamic crown ABOVE the shoulder line
# instead of a separate tall cap sitting on a shallow deck.
CABIN_BELTLINE_Y = 1.31
CABIN_ROOF_BASE_Y = 1.69
CABIN_ROOF_FRONT_Z = .40
CABIN_ROOF_REAR_Z = -1.32
CABIN_WINDSCREEN_BASE_Z = 1.30
CABIN_REAR_SCREEN_END_Z = -1.85

def cv(p):
    """Godot (x, up, forward) to Blender (x, -forward, up)."""
    return (p[0], -p[2], p[1])

def gaussian(value, center, sigma):
    return math.exp(-((value - center) / sigma) ** 2)

def hermite_station(z, channel):
    zs = [row[0] for row in STATIONS]
    if z <= zs[0]:
        return STATIONS[0][channel]
    if z >= zs[-1]:
        return STATIONS[-1][channel]
    i = bisect.bisect_right(zs, z) - 1
    left, right = STATIONS[i], STATIONS[i + 1]
    h = right[0] - left[0]
    t = (z - left[0]) / h
    slopes = [(STATIONS[j + 1][channel] - STATIONS[j][channel]) /
              (zs[j + 1] - zs[j]) for j in range(len(STATIONS) - 1)]
    def tangent(k):
        if k == 0:
            return slopes[0]
        if k == len(STATIONS) - 1:
            return slopes[-1]
        a, b = slopes[k - 1], slopes[k]
        if a * b <= 0:
            return 0.
        return 2. * a * b / (a + b)
    m0, m1 = tangent(i), tangent(i + 1)
    return ((2*t**3-3*t*t+1)*left[channel] +
            (t**3-2*t*t+t)*h*m0 +
            (-2*t**3+3*t*t)*right[channel] +
            (t**3-t*t)*h*m1)

def shell_point(z, angle):
    width = hermite_station(z, 1)
    bottom = hermite_station(z, 2)
    deck = hermite_station(z, 3)
    a = math.acos(max(-1., min(1., math.cos(angle))))
    side = math.sin(angle)
    # Integrate fender volume into the underlying hull surface itself.
    front_flare = .24 * gaussian(z, 2.40, .92)
    rear_flare = .28 * gaussian(z, -2.55, 1.12)
    fender = (front_flare + rear_flare) * gaussian(a, 1.19, .55)
    carved_waist = .24 * gaussian(z, -.08, 1.60) * gaussian(a, 1.57, .35)
    x = side * (width + fender - carved_waist)
    upper = ((1. + math.cos(angle)) * .5) ** .80
    ridge = (.42 * gaussian(z, 2.38, .98) +
             .51 * gaussian(z, -2.54, 1.12)) * gaussian(a, .77, .31)
    lower_channel = .105 * gaussian(z, .1, 1.65) * gaussian(a, 2.23, .32)
    y = bottom + (deck - bottom) * upper + ridge + lower_channel
    # Twin recessed bonnet valleys and a raised center spine are formed in
    # the primary body surface: not overlaid painted stripes or stuck panels.
    y -= .155 * gaussian(z, 2.37, .93) * gaussian(a, .42, .18)
    y += .075 * gaussian(z, 2.47, 1.12) * gaussian(a, 0., .15)
    # A real continuous deep rocker/energy trench beneath the shoulder.
    y -= .115 * gaussian(z, .0, 1.85) * gaussian(a, 1.78, .28)

    # One continuous raised shoulder ring under the greenhouse. This is
    # integrated into the SAME body vertex grid: side windows sit down in
    # the body instead of attaching to a flat central deck like a truck cab.
    y += .31 * gaussian(z, -.06, 1.64) * gaussian(a, .53, .31)

    # A long, low fastback crown rises in the existing rear body surface,
    # meets the short rear windshield and gently fades into the trunk.
    # The rear cab is no longer terminated by a flat vertical bulkhead.
    y += .38 * gaussian(z, -1.90, .93) * gaussian(a, 0., .61)
    return (x, y, z)

def material(name, rgb, metallic=.0, roughness=.5, alpha=1., glow=0.):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.diffuse_color = (*rgb, alpha)
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*rgb, 1.)
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = roughness
    if alpha < 1.:
        p.inputs["Alpha"].default_value = alpha
        if hasattr(m, "surface_render_method"):
            m.surface_render_method = "DITHERED"
        m.use_nodes = True
    if glow > 0.:
        p.inputs["Emission Color"].default_value = (*rgb, 1.)
        p.inputs["Emission Strength"].default_value = glow
    return m

paint = material("SOLSTICE_Petrol_Teal_Clearcoat", (.058,.245,.263), .71, .24)
metal = material("SOLSTICE_Champagne_Bronze", (.57,.28,.135), .78, .30)
dark = material("SOLSTICE_Black_Graphite", (.034,.046,.055), .41, .43)
glass = material("SOLSTICE_Smoke_Teal_Glass", (.035,.155,.18), .08, .18, .39)
seatmat = material("SOLSTICE_Cockpit_Charcoal", (.056,.074,.082), .17, .78)
glow = material("SOLSTICE_Amber_Lift_Emitters", (.96,.41,.11), .05, .30, glow=2.)
ice = material("SOLSTICE_Ice_Accent", (.20,.74,.73), .06, .29, glow=1.6)
clay = material("SOLSTICE_Diagnostic_Clay", (.52,.56,.58), .0, .7)
exec((Path(__file__).parent / "solstice_pbr.py").read_text(),globals())
install_solstice_pbr(paint)

def geometry(name, points, faces, mat, smooth=True):
    data = bpy.data.meshes.new(name + "_Mesh")
    data.from_pydata([cv(p) for p in points], [], faces)
    data.validate(clean_customdata=False)
    data.update()
    if smooth:
        for face in data.polygons:
            face.use_smooth = True
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    data.materials.append(mat)
    return obj

# One continuous quad cage, with an actual opening for the glazed cockpit.
zs = [STATIONS[0][0] +
      (STATIONS[-1][0]-STATIONS[0][0])*i/(NZ-1) for i in range(NZ)]
angles = [2.*math.pi*j/NR for j in range(NR)]
hull_pts = [shell_point(z,a) for z in zs for a in angles]
hull_faces = []
hull_face_material = []
aperture_quads = 0
# Rectangular, indexed inset duct zones on both rear shoulders. The rim,
# recess floor and walls will SHARE the original body boundary vertices.
# No dark rectangle or raised block is glued to the car's side.
def index_at_z(value):
    return min(range(NZ), key=lambda i: abs(zs[i]-value))
def index_at_angle(value):
    return round(value*NR/(2*math.pi))
scoops=[]
for jstart,jend in [(index_at_angle(1.13),index_at_angle(1.64)),
                    (index_at_angle(2*math.pi-1.64),
                     index_at_angle(2*math.pi-1.13))]:
    scoops.append((index_at_z(-2.70),index_at_z(-1.68),jstart,jend))
front_extractors=[]
for jstart,jend in [(index_at_angle(.72),index_at_angle(1.02)),
                    (index_at_angle(2*math.pi-1.02),
                     index_at_angle(2*math.pi-.72))]:
    front_extractors.append((index_at_z(2.42),index_at_z(3.00),jstart,jend))
recesses=[(region,"rear") for region in scoops]+[
         (region,"hood") for region in front_extractors]
for k in range(NZ-1):
    middle_z = .5*(zs[k]+zs[k+1])
    for j in range(NR):
        next_j = (j+1) % NR
        mid_a = (j+.5)*2*math.pi/NR
        unsigned = math.acos(math.cos(mid_a))
        if APERTURE_Z[0] < middle_z < APERTURE_Z[1] and unsigned < APERTURE_THETA:
            aperture_quads += 1
            continue
        if any(k0<=k<k1 and j0<=j<j1
               for (k0,k1,j0,j1),kind in recesses):
            continue
        a=k*NR+j
        b=k*NR+next_j
        c=(k+1)*NR+j
        d=(k+1)*NR+next_j
        hull_faces.append((a,c,d,b))
        hull_face_material.append(0)
# Preserve continuous cylindrical UV coordinates through the body and all
# inner walls. Split the wrap per-face to avoid the 0/1 seam interpolation.
uv_seed={k*NR+j:(j/NR,k/(NZ-1))
         for k in range(NZ) for j in range(NR)}
# New hood extractors and existing rear coolers are REAL monocoque holes.
# Each rim shares its original shell indices; a second edge loop creates a
# rolled stamped lip before a dark cavity wall and an actual interior floor.
scoop_quads=0
extractor_quads=0
formed_lip_segments=0
for (k0,k1,j0,j1),kind in recesses:
    inner={}
    lip={}
    for k in range(k0,k1+1):
        for j in range(j0,j1+1):
            original=k*NR+j
            x,y,z=hull_pts[original]
            inward=.24 if kind=="rear" else .026
            down=.045 if kind=="rear" else .070
            inner[(k,j)]=len(hull_pts)
            hull_pts.append((x-math.copysign(inward,x),y-down,z))
            uv_seed[inner[(k,j)]]=uv_seed[original]
            if k in (k0,k1) or j in (j0,j1):
                lip[(k,j)]=len(hull_pts)
                hull_pts.append((x-math.copysign(
                    .028 if kind=="rear" else .007,x),
                    y-(.017 if kind=="rear" else .011),z))
                uv_seed[lip[(k,j)]]=uv_seed[original]
    for k in range(k0,k1):
        for j in range(j0,j1):
            hull_faces.append((inner[(k,j)],inner[(k+1,j)],
                               inner[(k+1,j+1)],inner[(k,j+1)]))
            hull_face_material.append(1)
            if kind=="rear":
                scoop_quads+=1
            else:
                extractor_quads+=1
    def wall(a,b):
        global formed_lip_segments
        a0=a[0]*NR+a[1]
        b0=b[0]*NR+b[1]
        hull_faces.append((a0,b0,lip[b],lip[a]))
        hull_face_material.append(0)
        hull_faces.append((lip[a],lip[b],inner[b],inner[a]))
        hull_face_material.append(1)
        formed_lip_segments+=1
    for j in range(j0,j1):
        wall((k0,j),(k0,j+1))
        wall((k1,j),(k1,j+1))
    for k in range(k0,k1):
        wall((k,j0),(k+1,j0))
        wall((k,j1),(k+1,j1))
# The stern is no longer a giant closed ngon with engines stuck on top.
# We replace its cap with a concentric annulus, precision-machined lip,
# recessed dark duct and sealed internal thrust bulkhead, all connected
# by COMMON vertex indices to the original monocoque end ring.
# The outer stern is 36cm shorter and its upper deck drops by 12cm.
rear_end_z=STATIONS[0][0]
rear_duct_y=.595
rear_ring_specs=[
    # radius X, radius Y, longitudinal Godot Z, material index for the
    # band connecting the previous ring to this ring.
    (.704,.174,rear_end_z-.006,0),  # rolled painted tail border
    (.666,.154,rear_end_z-.023,2),  # thin champagne-bronze bezel
    (.612,.132,rear_end_z+.034,1),  # flush recessed throat
    (.571,.118,rear_end_z+.285,1),  # deep graphite interior
]
outer_ring=list(range(NR))
prior_ring=outer_ring
rear_thrust_band_faces=0
rear_thrust_ring_vertex_count=0
for radius_x,radius_y,z_center,material_slot in rear_ring_specs:
    inner_ring=[]
    for j,ang in enumerate(angles):
        inner_ring.append(len(hull_pts))
        hull_pts.append((radius_x*math.sin(ang),
                         rear_duct_y+radius_y*math.cos(ang),z_center))
        uv_seed[inner_ring[-1]]=(j/NR,.003)
    for j in range(NR):
        nxt=(j+1)%NR
        hull_faces.append((prior_ring[j],prior_ring[nxt],
                           inner_ring[nxt],inner_ring[j]))
        hull_face_material.append(material_slot)
        rear_thrust_band_faces+=1
    rear_thrust_ring_vertex_count+=len(inner_ring)
    prior_ring=inner_ring
# The cavity ends on an actual internal, sealed graphite backplate.
hull_faces.append(tuple(prior_ring))
hull_face_material.append(1)
# Only the pointed *front* end stays solid; the rear duct is a real hole.
hull_faces.append(tuple((NZ-1)*NR+j for j in range(NR)))
hull_face_material.append(0)
hull = geometry("SOLSTICE_UNIFIED_OUTER_SKIN", hull_pts, hull_faces, paint)
hull.data.materials.append(dark)
hull.data.materials.append(metal)
assert len(hull.data.polygons)==len(hull_face_material)
for polygon,slot in zip(hull.data.polygons,hull_face_material):
    polygon.material_index=slot
uv_layer=hull.data.uv_layers.new(name="Solstice_Paint_Cylindrical_UV")
for polygon in hull.data.polygons:
    uv=[uv_seed[hull.data.loops[i].vertex_index] for i in polygon.loop_indices]
    wrap=max(x[0] for x in uv)-min(x[0] for x in uv)>.5
    for loop,(u,v) in zip(polygon.loop_indices,uv):
        uv_layer.data[loop].uv=(u+1 if wrap and u<.5 else u,v)
thickness = hull.modifiers.new("Stamped body skin 28 mm", "SOLIDIFY")
thickness.thickness = .028
thickness.offset = -1.
thickness.use_even_offset = True

def patch(name, nu, nv, point, mat, smooth=True):
    pts = [point(u/nu, v/nv) for v in range(nv+1)
           for u in range(nu+1)]
    faces = []
    for j in range(nv):
        for i in range(nu):
            a = j*(nu+1)+i
            faces.append((a, a+1, a+nu+2, a+nu+1))
    obj=geometry(name,pts,faces,mat,smooth)
    layer=obj.data.uv_layers.new(name="Parametric_UV")
    for polygon in obj.data.polygons:
        for loop in polygon.loop_indices:
            vertex=obj.data.loops[loop].vertex_index
            layer.data[loop].uv=((vertex%(nu+1))/nu,(vertex//(nu+1))/nv)
    return obj

# Independent fitted windshield, roof and side glazing.
# No glass polygon is baked into the painted monocoque material.
# All four windshield, roof and side-glass edges share the same
# numerical perimeter control, rather than approximating matching points.
def windshield_point(u,v):
    x01=2*u-1
    width=.68+(.49-.68)*v
    z=CABIN_WINDSCREEN_BASE_Z+(CABIN_ROOF_FRONT_Z-CABIN_WINDSCREEN_BASE_Z)*v
    # Windshield lower edge follows the hood crown rather than floating
    # uniformly above its center. Thin center, full-height shoulder corners.
    bottom=1.18+.13*abs(x01)**1.65
    top=CABIN_ROOF_BASE_Y+.045*(1-x01*x01)
    return (width*x01,(1-v)*bottom+v*top,z)
windshield=patch("SOLSTICE_FRONT_WINDSCREEN",20,12,windshield_point,glass)

def roof_point(u,v):
    x01=2*u-1
    z=CABIN_ROOF_FRONT_Z+(CABIN_ROOF_REAR_Z-CABIN_ROOF_FRONT_Z)*v
    return (x01*(.49+.030*math.sin(math.pi*v)),
            CABIN_ROOF_BASE_Y+.055*math.sin(math.pi*v)+
                .045*(1-x01*x01),z)
# The painted crown now reads as the shoulder's continuation rather than
# a contrasting floating dark/white lid.
roof=patch("SOLSTICE_STRUCTURAL_ROOF",18,22,roof_point,paint)

def side_window_point(side,u,v):
    zfront=CABIN_WINDSCREEN_BASE_Z+(
        CABIN_ROOF_FRONT_Z-CABIN_WINDSCREEN_BASE_Z)*u
    zrear=-1.59+(CABIN_ROOF_REAR_Z+1.59)*u
    z=zfront+(zrear-zfront)*v
    xl=.68+.032*math.sin(math.pi*v)
    xu=.49+.030*math.sin(math.pi*v)
    x=side*((1-u)*xl+u*xu+.014*math.sin(math.pi*u)*math.sin(math.pi*v))
    sill=CABIN_BELTLINE_Y+.020*math.sin(math.pi*v)
    roof_progress=max(0.,min(1.,(CABIN_ROOF_FRONT_Z-z)/
                               (CABIN_ROOF_FRONT_Z-CABIN_ROOF_REAR_Z)))
    top=CABIN_ROOF_BASE_Y+.055*math.sin(math.pi*roof_progress)
    y=(1-u)*sill+u*top+.012*math.sin(math.pi*u)*math.sin(math.pi*v)
    return (x,y,z)
for side,label in [(-1,"Port"),(1,"Starboard")]:
    patch("SOLSTICE_"+label+"_GLAZING",12,32,
          lambda u,v,s=side: side_window_point(s,u,v),glass)

def smoothstep(t):
    t=max(0.,min(1.,t))
    return t*t*(3.-2.*t)

def rear_windscreen_point(u,v):
    # Short sloping rear screen lands directly against the raised rear body.
    # Past this line the trunk is sculpted PAINT, not glass hovering over a
    # second opaque shell. This is a genuine fastback surface transition.
    x01=2*u-1
    z=CABIN_ROOF_REAR_Z+(CABIN_REAR_SCREEN_END_Z-CABIN_ROOF_REAR_Z)*v
    width=.49+.12*v
    start_y=CABIN_ROOF_BASE_Y+.045*(1-x01*x01)
    landing_y=shell_point(CABIN_REAR_SCREEN_END_Z,.45*abs(x01))[1]+.013
    b=smoothstep(v)
    y=(1-b)*start_y+b*landing_y+.016*math.sin(math.pi*v)*(1-x01*x01)
    return (width*x01,y,z)
patch("SOLSTICE_REAR_WINDSCREEN",18,16,rear_windscreen_point,glass)

def sail_point(side,u,v):
    # Formed quarter-panel bridge: each edge begins at the rear roof corner,
    # flares gradually alongside the rear screen, and lands inside the
    # existing raised haunch. Its end coordinates are sampled from the
    # actual primary shell rather than approximate hand-drawn fin points.
    z=CABIN_ROOF_REAR_Z+(-3.00-CABIN_ROOF_REAR_Z)*v
    root=shell_point(z,side*(.74+.025*v))
    rear_t=max(0.,min(1.,(CABIN_ROOF_REAR_Z-z)/
                        (CABIN_ROOF_REAR_Z-CABIN_REAR_SCREEN_END_Z)))
    glass_edge=rear_windscreen_point(0. if side==-1 else 1.,rear_t)
    bridge=smoothstep(v)
    inner=.009+.943*bridge**1.6
    outer=.075+.916*bridge**.65
    t=inner*(1-u)+outer*u
    x=glass_edge[0]+(root[0]-glass_edge[0])*t
    y=glass_edge[1]+(root[1]-glass_edge[1])*t
    y+=.021*math.sin(math.pi*u)*math.sin(math.pi*v)
    return (x,y,z)

for side,label in [(-1,"Port"),(1,"Starboard")]:
    sail=patch("SOLSTICE_"+label+"_Roof_to_Haunch_Buttress",
               10,32,lambda u,v,s=side: sail_point(s,u,v),paint)
    rolled=sail.modifiers.new("Formed rear sail hem","SOLIDIFY")
    rolled.thickness=.022
    rolled.offset=-1.

def check_glass_fit(a,b,tolerance=1e-5):
    distance=(Vector(a)-Vector(b)).length
    assert distance<tolerance, "Glazing seam mismatch %.7f m" % distance

for u in (0.,.25,.5,.75,1.):
    check_glass_fit(windshield_point(u,1.),roof_point(u,0.))
    check_glass_fit(rear_windscreen_point(u,0.),roof_point(u,1.))
for side in (-1,1):
    for t in (0.,.25,.5,.75,1.):
        edge_u=0. if side==-1 else 1.
        check_glass_fit(windshield_point(edge_u,t),side_window_point(side,t,0.))
    check_glass_fit(side_window_point(side,1.,1.),
                    roof_point(0. if side==-1 else 1.,1.))

# Proportion gate: sample the raised continuous shoulder at the cabin
# and the actual crown apex, rather than comparing arbitrary hardcoded
# heights. A floating truck-like cab will fail this ratio check.
shoulder_height=shell_point(0.,.53)[1]
roof_peak=max(roof_point(.5,i/24.)[1] for i in range(25))
exposed_greenhouse_height=roof_peak-shoulder_height
rear_windscreen_slope=(
    rear_windscreen_point(.5,0.)[1]-
    rear_windscreen_point(.5,1.)[1]) / (
    CABIN_ROOF_REAR_Z-CABIN_REAR_SCREEN_END_Z)
assert 1.27<shoulder_height<1.62, "Cabin shoulder sculpt lost"
assert .22<exposed_greenhouse_height<.49, "Cabin is standing proud of the body"
assert 0.<rear_windscreen_slope<.70, "Rear cabin ends like a vertical truck wall"
assert CABIN_ROOF_BASE_Y<1.75
print("SCENEFORGE_SOLSTICE_INTEGRATED_CABIN_OK",
      "shoulder_m",round(shoulder_height,3),
      "crown_m",round(roof_peak,3),
      "exposed_m",round(exposed_greenhouse_height,3),
      "rear_slope",round(rear_windscreen_slope,3))
print("SCENEFORGE_SOLSTICE_GREENHOUSE_SEAMS_OK")

# Bezier tubes are kept editable in the .blend source, then converted to
# evaluated meshes for glTF. They are separate manufactured trim pieces.
def spline_tube(name,points,radius,mat):
    path = bpy.data.curves.new(name+"_Path","CURVE")
    path.dimensions="3D"
    path.bevel_depth=radius
    # Small piping below 3 cm radius does not need screen-space invisible
    # 16x8 tessellation on an Android-scale vehicle review model.
    path.bevel_resolution=2
    path.resolution_u=10
    spline=path.splines.new("BEZIER")
    spline.bezier_points.add(len(points)-1)
    for handle,p in zip(spline.bezier_points,points):
        handle.co=cv(p)
        handle.handle_left_type="AUTO"
        handle.handle_right_type="AUTO"
    obj=bpy.data.objects.new(name,path)
    bpy.context.collection.objects.link(obj)
    path.materials.append(mat)
    return obj

for side,label in [(-1,"Port"),(1,"Starboard")]:
    edge_u=0. if side==-1 else 1.

    # Dark formed strips cover the actual glass perimeter. Bronze is thin
    # highlighting, not an exposed roll cage standing away from the cabin.
    patch("SOLSTICE_"+label+"_Formed_A_Pillar",3,16,
          lambda u,v,s=side,eu=edge_u: (
              windshield_point(eu,v)[0]+s*(u-.50)*.091,
              windshield_point(eu,v)[1]+.012,
              windshield_point(eu,v)[2]),dark)
    patch("SOLSTICE_"+label+"_Formed_Roof_Rail",3,22,
          lambda u,v,s=side,eu=edge_u: (
              roof_point(eu,v)[0]+s*(u-.50)*.086,
              roof_point(eu,v)[1]+.015,
              roof_point(eu,v)[2]),dark)
    patch("SOLSTICE_"+label+"_Formed_C_Pillar",3,15,
          lambda u,v,s=side: (
              side_window_point(s,v,1.)[0]+s*(u-.50)*.084,
              side_window_point(s,v,1.)[1]+.012,
              side_window_point(s,v,1.)[2]),dark)

    spline_tube("SOLSTICE_"+label+"_A_Pillar_Accent",
        [tuple(a+b for a,b in zip(windshield_point(edge_u,t),
                                 (side*.009,.015,0.)))
         for t in (0.,.18,.36,.54,.72,.9,1.)],.012,metal)
    spline_tube("SOLSTICE_"+label+"_Roof_Cantrail",
        [tuple(a+b for a,b in zip(roof_point(edge_u,t),
                                 (side*.011,.017,0.)))
         for t in (0.,.20,.40,.60,.80,1.)],.014,metal)
    spline_tube("SOLSTICE_"+label+"_C_Pillar_Accent",
        [tuple(a+b for a,b in zip(side_window_point(side,t,1.),
                                 (side*.009,.015,0.)))
         for t in (0.,.20,.40,.60,.80,1.)],.013,metal)
    spline_tube("SOLSTICE_"+label+"_Side_Glass_Seal",
        [side_window_point(side,0.,t) for t in
         (0.,.17,.34,.51,.68,.85,1.)],.015,dark)
    spline_tube("SOLSTICE_"+label+"_B_Pillar",
        [side_window_point(side,u,.58) for u in (0.,.25,.50,.75,1.)],
        .014,dark)

    shoulder=[shell_point(z,side*math.pi*.25)
              for z in [3.16,2.61,1.65,.5,-.55,-1.7,-2.5,-3.35]]
    spline_tube("SOLSTICE_"+label+"_Shoulder_Accent",
                shoulder,.010,metal)
    spline_tube("SOLSTICE_"+label+"_Rear_Sail_Landing",
        [sail_point(side,1.,t) for t in (0.,.16,.32,.48,.64,.80,1.)],
        .012,dark)

def rounded_block(name,position,dimensions,mat,bevel=.05):
    bpy.ops.mesh.primitive_cube_add(size=1,location=cv(position))
    obj=bpy.context.object
    obj.name=name
    # Blender axes X/right, Y/back, Z/up.
    obj.dimensions=(dimensions[0],dimensions[2],dimensions[1])
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.data.materials.append(mat)
    if bevel>0:
        mod=obj.modifiers.new("Controlled manufactured radius","BEVEL")
        mod.width=bevel
        mod.segments=3
        mod.limit_method="ANGLE"
    for face in obj.data.polygons:
        face.use_smooth=True
    return obj

# A restrained functional pilot space, visible through true glass.
rounded_block("SOLSTICE_Cockpit_Tub",(0,.74,-.10),(1.28,.18,2.73),dark,.085)
rounded_block("SOLSTICE_Pilot_Seat",(0,1.02,-.46),(.58,.24,.87),seatmat,.11)
rounded_block("SOLSTICE_Pilot_Backrest",(0,1.29,-.84),(.58,.61,.17),seatmat,.09)
rounded_block("SOLSTICE_Dashboard",(0,1.15,.84),(1.15,.22,.38),dark,.10)
rounded_block("SOLSTICE_Flight_Instruments",(0,1.28,.72),(.70,.045,.13),ice,.015)
rounded_block("SOLSTICE_Control_Yoke",(0,1.15,.44),(.53,.055,.075),metal,.03)

def torus(name,x,y,z,r,minor,mat,vertical=False):
    bpy.ops.mesh.primitive_torus_add(major_segments=24,minor_segments=6,
        location=cv((x,y,z)),major_radius=r,minor_radius=minor)
    obj=bpy.context.object
    obj.name=name
    obj.data.materials.append(mat)
    if vertical:
        obj.rotation_euler[0]=math.pi/2
    for p in obj.data.polygons:p.use_smooth=True
    return obj

def cylinder(name,x,y,z,r,depth,mat,axis="UP"):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=r,depth=depth,
                                       location=cv((x,y,z)))
    obj=bpy.context.object
    obj.name=name
    obj.data.materials.append(mat)
    if axis=="FORWARD":
        obj.rotation_euler[0]=math.pi/2
    for p in obj.data.polygons:p.use_smooth=True
    return obj

# Recessed magnetic field machinery is a distinct manufactured assembly.
# The fairing volume is already present in the ONE continuous body surface.
for z,position_name in [(2.32,"Front"),(-2.52,"Rear")]:
    for side,label in [(-1,"Port"),(1,"Starboard")]:
        x=side*(1.08 if z>0 else 1.17)
        prefix="SOLSTICE_"+position_name+"_"+label
        # A true half-buried fairing bridges the recessed field to the body.
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=10,
                                            location=cv((x,.42,z)))
        pod=bpy.context.object
        pod.name=prefix+"_Integrated_Hover_Fairing"
        pod.scale=(.53,.79,.17)  # X, Blender longitudinal Y, vertical Z
        pod.data.materials.append(paint)
        for face in pod.data.polygons:face.use_smooth=True
        # Formed cradle webs are tied to the underside and terminate inside
        # the partly embedded ovoid fairing, replacing an isolated disc look.
        for direction,bracket in [(-1,"Aft"),(1,"Forward")]:
            arm=patch(prefix+"_"+bracket+"_Structural_Cradle",3,12,
                lambda u,v,cx=x,cz=z,side_sign=side,d=direction: (
                    side_sign*(.67+(abs(cx)-.67)*v),
                    .51-.160*v+.036*math.sin(math.pi*v)-.018*math.sin(math.pi*u),
                    cz+d*(.47-.19*v)+(u-.5)*(.31-.08*v)
                ),dark)
            wall=arm.modifiers.new("Forged cradle wall","SOLIDIFY")
            wall.thickness=.037
            wall.offset=-1.
        cylinder(prefix+"_Magnetic_Deck",x,.325,z,.39,.065,dark)
        torus(prefix+"_Machined_Retainer",x,.304,z,.35,.038,metal)
        torus(prefix+"_Flux_Ring",x,.267,z,.285,.032,glow)
        cylinder(prefix+"_Field_Emitter",x,.265,z,.19,.010,ice)
# S-01.7: ONE integrated ducted-vector drive, not twin bolt-on cylinders.
# A thin asymmetric-section oval bezel follows the actual oval opening,
# inside which radial flow straighteners surround a restrained energy core.
def ellipse_tube(name,rx,ry,cz,cy,radius,mat,segments=48,cross=6):
    verts=[]
    faces=[]
    for i in range(segments):
        t=math.tau*i/segments
        for j in range(cross):
            p=math.tau*j/cross
            x=(rx+radius*math.cos(p))*math.sin(t)
            y=cy+(ry+radius*math.cos(p))*math.cos(t)
            z=cz+radius*math.sin(p)
            verts.append((x,y,z))
    for i in range(segments):
        for j in range(cross):
            a=i*cross+j
            b=i*cross+(j+1)%cross
            c=((i+1)%segments)*cross+(j+1)%cross
            dd=((i+1)%segments)*cross+j
            faces.append((a,b,c,dd))
    return geometry(name,verts,faces,mat)

def thrust_point(r,angle,z):
    return (.57*r*math.sin(angle),
            rear_duct_y+.115*r*math.cos(angle),z)

# Subtle machined glints inside the actual end-cap chamfer.
ellipse_tube("SOLSTICE_Thrust_Bezel_Bronze",.669,.154,
             rear_end_z-.020,rear_duct_y,.011,metal)
ellipse_tube("SOLSTICE_Thrust_Inner_Guide_Rail",.50,.105,
             rear_end_z+.105,rear_duct_y,.012,metal)

# Tapered blades follow a radial diffuser, each behind the mouth rather
# than protruding over the bodywork or obscuring the amber drive capsule.
rear_stator_count=14
for index in range(rear_stator_count):
    t=math.tau*index/rear_stator_count
    pts=[
        thrust_point(.40,t-.031,rear_end_z+.108),
        thrust_point(.88,t+.072,rear_end_z+.155),
        thrust_point(.87,t+.170,rear_end_z+.178),
        thrust_point(.42,t+.074,rear_end_z+.125),
    ]
    vane=geometry("SOLSTICE_Thrust_Diffuser_Vane_%02d"%index,
                  pts,[(0,1,2,3)],metal)
    stiffener=vane.modifiers.new("Recessed guide fin thickness","SOLIDIFY")
    stiffener.thickness=.009

# Two nested oval rings form the centered vector-field emitter. No giant
# flame cone: warm amber comes only from a precise, recessed capsule.
ellipse_tube("SOLSTICE_Thrust_Capsule_Surround",.289,.064,
             rear_end_z+.077,rear_duct_y,.018,dark)
ellipse_tube("SOLSTICE_Thrust_Amber_Capsule",.255,.048,
             rear_end_z+.074,rear_duct_y,.010,glow)
rounded_block("SOLSTICE_Thrust_Center_Optical_Diffuser",
              (0.,rear_duct_y,rear_end_z+.093),
              (.406,.038,.022),dark,.016)
assert rear_thrust_band_faces==4*NR
assert rear_stator_count>=12
# The rear intakes have real pockets. Small metal louvers are fitted inside
# the cavities instead of black shader stripes painted across the side.
for side,label in [(-1,"Port"),(1,"Starboard")]:
    for blade in range(3):
        z=-2.56+blade*.30
        x,y,_=shell_point(z,side*1.40)
        rounded_block("SOLSTICE_"+label+"_Intake_Louvre_"+str(blade),
            (x-side*.19,y-.035,z),(.037,.075,.22),metal,.018)

# Three recessed stators live inside each front hood extractor; these do
# not paint dark stripes over the original continuous metal surface.
for side,label in [(-1,"Port"),(1,"Starboard")]:
    for blade in range(2):
        z=2.60+.22*blade
        x,y,_=shell_point(z,side*.86)
        rounded_block("SOLSTICE_"+label+"_Front_Extractor_Stator_"+str(blade),
            (x-side*.014,y-.056,z),(.11,.013,.085),dark,.004)

# Flush, not floating: exterior lighting follows the vehicle's functional edges.
# Restrained narrow tail markers clear the oval thrust port.
for side,label in [(-1,"Port"),(1,"Starboard")]:
    rounded_block("SOLSTICE_"+label+"_Tail_Signature",
        (side*.79,.64,rear_end_z-.012),(.030,.042,.026),ice,.010)
for side,label in [(-1,"Port"),(1,"Starboard")]:
    rounded_block("SOLSTICE_"+label+"_Front_Light",
                  (side*.69,.82,3.61),(.54,.040,.035),ice,.014)

# An actual cockpit aperture is allowed, but no surface edge may have
# three or more incident faces. Check before Solidify and GLB triangulation.
import bmesh
bm=bmesh.new()
bm.from_mesh(hull.data)
ambiguous_edges=sum(1 for edge in bm.edges if len(edge.link_faces)>2)
boundary_edges=sum(1 for edge in bm.edges if edge.is_boundary)
assert ambiguous_edges==0, "Primary body has overlapping/nonmanifold topology"
assert boundary_edges<150, "Unexpected disconnected body seams"
bm.free()
assert aperture_quads>250, "Actual cockpit opening was not generated"
assert "SOLSTICE_Port_Formed_A_Pillar" in bpy.data.objects
assert "SOLSTICE_Starboard_Roof_to_Haunch_Buttress" in bpy.data.objects
assert "SOLSTICE_Front_Port_Aft_Structural_Cradle" in bpy.data.objects
expected_recess_vertices=sum(
    (k1-k0+1)*(j1-j0+1)+2*((k1-k0)+(j1-j0))
    for (k0,k1,j0,j1),kind in recesses)
assert len(hull.data.vertices)==NZ*NR+expected_recess_vertices+4*NR, "Unexpected body cage vertices"
assert rear_thrust_ring_vertex_count==4*NR
assert rear_thrust_band_faces==4*NR
assert "SOLSTICE_Thrust_Amber_Capsule" in bpy.data.objects
assert not any("_Rear_Nozzle_Lip" in o.name for o in bpy.data.objects)
assert scoop_quads>50, "Integrated shoulder intake geometry missing"
assert extractor_quads>=24, "True shared-hull hood extractor recesses missing"
assert formed_lip_segments>60, "Stamped lip geometry missing"
assert all(face.loop_total in (3,4,NR) for face in hull.data.polygons)
assert len(hull.data.polygons)>4500
assert len([o for o in bpy.data.objects if o.name=="SOLSTICE_UNIFIED_OUTER_SKIN"])==1
print("SCENEFORGE_SOLSTICE_CONNECTED_BODY_OK",len(hull.data.vertices),
      len(hull.data.polygons),"opening_quads",aperture_quads,
      "recessed_scoop_quads",scoop_quads)

authored=[o for o in bpy.data.objects if o.type in ("MESH","CURVE")]
# Render assets directly from Blender, not conceptual AI images.
scene=bpy.context.scene
world=bpy.data.worlds.new("Solstice Studio")
scene.world=world
world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(.13,.18,.21,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.8
scene.render.resolution_x=1100
scene.render.resolution_y=680
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False
scene.render.engine="BLENDER_WORKBENCH"
studio=scene.display.shading
studio.light="STUDIO"
studio.color_type="MATERIAL"
studio.show_shadows=True
studio.show_cavity=True
studio.background_type="WORLD"

camdata=bpy.data.cameras.new("Studio Orthographic Lens")
camera=bpy.data.objects.new("Studio_Camera",camdata)
bpy.context.collection.objects.link(camera)
scene.camera=camera
camdata.type="ORTHO"
camdata.ortho_scale=10.5

def stage_camera(pos,focus=(0,1.05,0),scale=10.5):
    camera.location=cv(pos)
    target=Vector(cv(focus))
    camera.rotation_euler=(target-camera.location).to_track_quat("-Z","Y").to_euler()
    camdata.ortho_scale=scale

# Save full editable vehicle, including bevel/solidify and spline controls.
bpy.ops.wm.save_as_mainfile(filepath=str((OUT/"Solstice_S01_Master.blend").resolve()))
views=[
    ("hero",(6.6,3.65,8.7),9.8),
    ("rear-quarter",(-6.7,3.6,-8.6),9.8),
    ("side",(11.4,2.45,0),9.5),
    ("front",(0,2.55,11.5),5.9),
    ("rear",(0,2.6,-11.5),5.9),
    ("top",(0,11.3,0),15.2),
    ("greenhouse",(4.5,4.15,3.35),6.7),
    ("rear-mechanics",(-5.2,2.8,-6.9),7.0),
    ("cabin-profile",(8.6,2.35,-.10),7.8),
    ("thrust-inspection",(-2.6,2.25,-6.8),6.6),
    ("rear-dead-on",(0,1.38,-8.25),5.4),
]
for name,pos,scale in views:
    stage_camera(pos,scale=scale)
    scene.render.filepath=str((OUT/("Solstice-"+name+".png")).resolve())
    bpy.ops.render.render(write_still=True)
    assert Path(scene.render.filepath).stat().st_size>2000
    print("SCENEFORGE_SOLSTICE_RENDER_OK",name)
# Same geometry, flat grey paint as a true surfacing diagnostic.
original_colors=[(m,m.diffuse_color[:]) for m in [paint,metal,dark]]
for m,c in original_colors:
    m.diffuse_color=(.55,.58,.61,1.)
studio.color_type="MATERIAL"
stage_camera((6.6,3.65,8.7),scale=9.8)
scene.render.filepath=str((OUT/"Solstice-clay.png").resolve())
bpy.ops.render.render(write_still=True)
for m,c in original_colors:m.diffuse_color=c

# Export only the actual vehicle. Convert editable manufacturing curves to
# evaluated mesh objects on the export copy (Blend master already saved).
for obj in authored:
    if obj.type=="CURVE":
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.convert(target="MESH")
bpy.ops.object.select_all(action="DESELECT")
for obj in authored:
    # Converting curves in place retains object identity.
    obj.select_set(True)
bpy.context.view_layer.objects.active=hull
gltf_path=OUT/"Solstice_S01.glb"
bpy.ops.export_scene.gltf(filepath=str(gltf_path.resolve()),
                          export_format="GLB",export_yup=True,
                          use_selection=True,export_apply=True)
raw=gltf_path.read_bytes()
assert raw[:4]==b"glTF"
json_length=struct.unpack_from("<I",raw,12)[0]
glb=json.loads(raw[20:20+json_length])
nodes={n.get("name") for n in glb["nodes"]}
assert "SOLSTICE_UNIFIED_OUTER_SKIN" in nodes
assert "SOLSTICE_FRONT_WINDSCREEN" in nodes
assert "SOLSTICE_STRUCTURAL_ROOF" in nodes
assert "SOLSTICE_Front_Port_Flux_Ring" in nodes
assert "SOLSTICE_Thrust_Amber_Capsule" in nodes
assert "SOLSTICE_Thrust_Diffuser_Vane_00" in nodes
assert not any("Rear_Nozzle_Lip" in n for n in nodes if n)
paint_mat=next(m for m in glb["materials"] if m.get("name")=="SOLSTICE_Petrol_Teal_Clearcoat")
assert "normalTexture" in paint_mat, "Paint normal map lost in glTF"
assert "metallicRoughnessTexture" in paint_mat["pbrMetallicRoughness"]
assert "baseColorTexture" in paint_mat["pbrMetallicRoughness"]
assert len(glb.get("images",[]))>=3, "Three original PBR texture images required"
body_mesh=next(x for x in glb["meshes"] if x["name"]=="SOLSTICE_UNIFIED_OUTER_SKIN_Mesh")
assert "TEXCOORD_0" in body_mesh["primitives"][0]["attributes"]
print("SCENEFORGE_SOLSTICE_PBR_MAPS_OK",len(glb["images"]))
triangles=0
for mesh_def in glb["meshes"]:
    for primitive in mesh_def["primitives"]:
        accessor=primitive.get("indices")
        if accessor is not None:
            triangles+=glb["accessors"][accessor]["count"]//3
assert triangles<75000, "Prototype triangle cap exceeded: %d" % triangles
assert triangles>8000, "Main hull/detail geometry missing"
report={
    "name":"SOLSTICE S-01",
    "status":"original, prototype only; not yet playable",
    "source":"Procedurally modeled in Blender from original analytic surface curves",
    "body_topology":"single connected quad hull with 28mm solidify and cockpit aperture",
    "length_m":STATIONS[-1][0]-rear_end_z,
    "estimated_width_m":3.40,
    "rear_end_z_m":rear_end_z,
    "rear_deck_end_height_m":STATIONS[0][3],
    "rear_thrust":{"type":"single recessed oval ducted-vector drive",
                   "mouth_width_m":2*.704,
                   "mouth_height_m":2*.174,
                   "recess_depth_m":.285,
                   "stator_count":rear_stator_count,
                   "integrated_quads":rear_thrust_band_faces,
                   "bezel_material":"champagne bronze",
                   "core_material":"restrained amber"},
    "triangles":triangles,"glb_bytes":len(raw),
    "open_cockpit_quads":aperture_quads,
    "recessed_scoop_quads":scoop_quads,
    "front_extractor_quads":extractor_quads,
    "formed_lip_segments":formed_lip_segments,
    "body_boundary_edges":boundary_edges,
    "body_nonmanifold_edges":ambiguous_edges,
    "greenhouse_seam_tolerance_mm":.01,
    "cabin_shoulder_height_m":round(shoulder_height,4),
    "roof_peak_height_m":round(roof_peak,4),
    "exposed_cabin_height_above_shoulder_m":round(exposed_greenhouse_height,4),
    "rear_glass_slope":round(rear_windscreen_slope,4),
    "structural_cradle_count":8,
    "rear_intake_louvre_count":6,
    "glazing":"independent mesh surfaces",
    "views":[x[0] for x in views]+["clay"],
}
(OUT/"geometry-report.json").write_text(json.dumps(report,indent=2))
print("SCENEFORGE_SOLSTICE_REAR_THRUST_OK",rear_thrust_band_faces,
      rear_stator_count,round(rear_end_z,3))
print("SCENEFORGE_SOLSTICE_EXPORT_OK",triangles,len(raw))
