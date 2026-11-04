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
    (-4.18, .55, .33, .84), (-3.68, 1.17, .32, 1.01),
    (-2.65, 1.47, .35, 1.19), (-1.45, 1.47, .37, 1.20),
    (-.20, 1.52, .36, 1.19), (1.26, 1.51, .34, 1.15),
    (2.42, 1.40, .33, 1.09), (3.31, 1.13, .30, .92),
    (4.08, .41, .34, .68),
]
NZ = 92
NR = 72
APERTURE_Z = (-1.48, 1.27)
APERTURE_THETA = 0.49

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
    front_flare = .16 * gaussian(z, 2.33, .87)
    rear_flare = .23 * gaussian(z, -2.52, 1.02)
    fender = (front_flare + rear_flare) * gaussian(a, 1.25, .55)
    carved_waist = .115 * gaussian(z, -.08, 1.5) * gaussian(a, 1.59, .29)
    x = side * (width + fender - carved_waist)
    upper = ((1. + math.cos(angle)) * .5) ** .80
    ridge = (.18 * gaussian(z, 2.35, 1.03) +
             .26 * gaussian(z, -2.55, 1.25)) * gaussian(a, .83, .29)
    lower_channel = .075 * gaussian(z, .1, 1.65) * gaussian(a, 2.23, .32)
    y = bottom + (deck - bottom) * upper + ridge + lower_channel
    # A real, continuous deep rocker/energy trench beneath the shoulder.
    y -= .07 * gaussian(z, .0, 1.85) * gaussian(a, 1.78, .27)
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
aperture_quads = 0
for k in range(NZ-1):
    middle_z = .5*(zs[k]+zs[k+1])
    for j in range(NR):
        next_j = (j+1) % NR
        mid_a = (j+.5)*2*math.pi/NR
        unsigned = math.acos(math.cos(mid_a))
        if APERTURE_Z[0] < middle_z < APERTURE_Z[1] and unsigned < APERTURE_THETA:
            aperture_quads += 1
            continue
        a=k*NR+j
        b=k*NR+next_j
        c=(k+1)*NR+j
        d=(k+1)*NR+next_j
        hull_faces.append((a,c,d,b))
# End caps intentionally seal the pointed nose and flat rear; central opening
# remains open for cockpit visibility (Solidify will give it a proper rim).
hull_faces.append(tuple(reversed(range(NR))))
hull_faces.append(tuple((NZ-1)*NR+j for j in range(NR)))
hull = geometry("SOLSTICE_UNIFIED_OUTER_SKIN", hull_pts, hull_faces, paint)
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
    return geometry(name,pts,faces,mat,smooth)

# Independent fitted windshield, roof and side glazing.
# No glass polygon is baked into the painted monocoque material.
def windshield_point(u,v):
    x01 = 2*u-1
    z = 1.30-.70*v
    width = .68-.16*v
    return (width*x01, 1.23+.73*v+.060*(1-x01*x01),z)
windshield = patch("SOLSTICE_FRONT_WINDSCREEN",20,12,windshield_point,glass)

def roof_point(u,v):
    x01 = 2*u-1
    z = .60-1.75*v
    return (x01*(.52+.030*math.sin(math.pi*v)),
            1.96+.070*math.sin(math.pi*v)+.038*(1-x01*x01),z)
roof = patch("SOLSTICE_STRUCTURAL_ROOF",18,22,roof_point,dark)

def side_window_point(side,u,v):
    z = 1.27-2.72*v
    fade = min(1., max(.07, min(1.27-z,z+1.45)/.60))
    roof_y = 1.94+.07*math.sin(math.pi*v)
    sill_y = 1.28+.08*gaussian(z,-.8,1.)
    height = (roof_y-sill_y)*fade
    x = side*(.70-(.13*fade)*u)
    return (x, sill_y+height*u, z)
for side,side_name in [(-1,"Port"),(1,"Starboard")]:
    patch("SOLSTICE_"+side_name+"_GLAZING",5,28,
          lambda u,v,s=side: side_window_point(s,u,v),glass)

patch("SOLSTICE_REAR_WINDSCREEN",18,12,
      lambda u,v: ((2*u-1)*(.52+.16*v),
                   1.99-.68*v+.035*(1-(2*u-1)**2),
                   -1.15-.39*v),glass)

# Bezier tubes are kept editable in the .blend source, then converted to
# evaluated meshes for glTF. They are separate manufactured trim pieces.
def spline_tube(name,points,radius,mat):
    path = bpy.data.curves.new(name+"_Path","CURVE")
    path.dimensions="3D"
    path.bevel_depth=radius
    path.bevel_resolution=3
    path.resolution_u=16
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
    spline_tube("SOLSTICE_"+label+"_A_Pillar",
        [(side*.69,1.26,1.30),(side*.64,1.51,1.05),
         (side*.53,1.94,.60)],.026,metal)
    spline_tube("SOLSTICE_"+label+"_Roof_Cantrail",
        [(side*.53,1.96,.60),(side*.55,2.04,-.17),
         (side*.52,1.96,-1.15)],.025,metal)
    spline_tube("SOLSTICE_"+label+"_C_Pillar",
        [(side*.52,1.96,-1.15),(side*.62,1.62,-1.38),
         (side*.71,1.28,-1.55)],.033,metal)
    spline_tube("SOLSTICE_"+label+"_Beltline",
        [(side*.70,1.29,1.30),(side*.70,1.31,-.20),
         (side*.70,1.27,-1.53)],.019,dark)
    # The chrome graphic traces the actual continuous shoulder surface.
    shoulder = [shell_point(z,side*math.pi*.25 if side>0 else
                           2*math.pi-math.pi*.25)
                for z in [3.16,2.61,1.65,.5,-.55,-1.7,-2.5,-3.35]]
    spline_tube("SOLSTICE_"+label+"_Shoulder_Accent",
                shoulder,.011,metal)

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
rounded_block("SOLSTICE_Pilot_Backrest",(0,1.32,-.84),(.58,.64,.17),seatmat,.09)
rounded_block("SOLSTICE_Dashboard",(0,1.15,.84),(1.15,.22,.38),dark,.10)
rounded_block("SOLSTICE_Flight_Instruments",(0,1.28,.72),(.70,.045,.13),ice,.015)
rounded_block("SOLSTICE_Control_Yoke",(0,1.15,.44),(.53,.055,.075),metal,.03)

def torus(name,x,y,z,r,minor,mat,vertical=False):
    bpy.ops.mesh.primitive_torus_add(major_segments=30,minor_segments=8,
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
        cylinder(prefix+"_Magnetic_Deck",x,.285,z,.41,.075,dark)
        torus(prefix+"_Machined_Retainer",x,.265,z,.37,.045,metal)
        torus(prefix+"_Flux_Ring",x,.227,z,.28,.040,glow)
        cylinder(prefix+"_Field_Emitter",x,.215,z,.20,.016,ice)
# Twin actual propulsion tubes behind the broad structural tail.
for side,label in [(-1,"Port"),(1,"Starboard")]:
    x=side*.81
    cylinder("SOLSTICE_"+label+"_Rear_Thruster",x,.76,-3.83,.34,.29,dark,"FORWARD")
    torus("SOLSTICE_"+label+"_Rear_Nozzle_Lip",x,.76,-4.01,.295,.033,metal,True)
    cylinder("SOLSTICE_"+label+"_Plasma_Core",x,.76,-4.025,.215,.018,glow,"FORWARD")
# Flush, not floating: exterior lighting follows the vehicle's functional edges.
rounded_block("SOLSTICE_Thin_Tail_Lightbar",(0,1.07,-4.11),
              (1.19,.035,.025),ice,.014)
for side,label in [(-1,"Port"),(1,"Starboard")]:
    rounded_block("SOLSTICE_"+label+"_Front_Light",
                  (side*.69,.82,3.61),(.54,.040,.035),ice,.014)

# Validate on the original source before any export operator can change it.
assert aperture_quads>250, "Actual cockpit opening was not generated"
assert len(hull.data.vertices)==NZ*NR, "Unexpected disconnected hull vertices"
assert all(face.loop_total in (3,4,NR) for face in hull.data.polygons)
assert len(hull.data.polygons)>4500
assert len([o for o in bpy.data.objects if o.name=="SOLSTICE_UNIFIED_OUTER_SKIN"])==1
print("SCENEFORGE_SOLSTICE_CONNECTED_BODY_OK",len(hull.data.vertices),
      len(hull.data.polygons),"opening_quads",aperture_quads)

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
    ("hero",(6.6,3.65,8.7),11.5),
    ("rear-quarter",(-6.7,3.6,-8.6),11.5),
    ("side",(11.4,2.45,0),10.8),
    ("front",(0,2.55,11.5),7.4),
    ("rear",(0,2.6,-11.5),7.4),
    ("top",(0,11.3,0),10.5),
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
stage_camera((6.6,3.65,8.7),scale=11.5)
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
    "length_m":8.26,"estimated_width_m":3.40,
    "triangles":triangles,"glb_bytes":len(raw),
    "open_cockpit_quads":aperture_quads,
    "glazing":"independent mesh surfaces",
    "views":[x[0] for x in views]+["clay"],
}
(OUT/"geometry-report.json").write_text(json.dumps(report,indent=2))
print("SCENEFORGE_SOLSTICE_EXPORT_OK",triangles,len(raw))
