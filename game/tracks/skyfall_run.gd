extends RefCounted

# Skyfall Run — original point-to-point hover stage.  192 evenly spaced samples
# keep it compatible with the shared steering, garage and checkpoint controller.
# No third-party meshes or procedural work at import time.
const ID := 7
const COUNT := 192
const GAP_START := 32
const GAP_END := 36
const FLIGHT_START := 127
const FLIGHT_END := 185
const FINISH_INDEX := 188

const WAYPOINTS := [
	Vector3(0,42,0), Vector3(15,42,180), Vector3(35,44,350),
	Vector3(40,48,545), Vector3(95,55,660), Vector3(190,80,740),
	Vector3(340,120,760), Vector3(480,170,690), Vector3(620,205,760),
	Vector3(755,250,690), Vector3(910,305,740), Vector3(1050,370,680),
	Vector3(1160,426,820), Vector3(1260,425,910),
	Vector3(1390,350,1110), Vector3(1460,275,1330),
	Vector3(1510,180,1540), Vector3(1650,80,1700),
	Vector3(1740,52,1890)
]

static func route_points(count: int = COUNT) -> PackedVector3Array:
	var curve := Curve3D.new()
	curve.bake_interval = 4.0
	for i in range(WAYPOINTS.size()):
		var point: Vector3 = WAYPOINTS[i]
		var prev: Vector3 = WAYPOINTS[maxi(0,i-1)]
		var next: Vector3 = WAYPOINTS[mini(WAYPOINTS.size()-1,i+1)]
		var tangent: Vector3 = (next-prev).normalized()
		var before: float = point.distance_to(prev)
		var after: float = point.distance_to(next)
		var inward: Vector3 = -tangent*before*0.29 if i>0 else Vector3.ZERO
		var outward: Vector3 = tangent*after*0.29 if i<WAYPOINTS.size()-1 else Vector3.ZERO
		curve.add_point(point,inward,outward)
	var baked: PackedVector3Array = PackedVector3Array()
	var length: float = curve.get_baked_length()
	for sample in range(count):
		baked.append(curve.sample_baked(length*float(sample)/float(count-1),true))
	return baked

static func half_width(index: int) -> float:
	if index < 37:
		return 15.5
	if index < FLIGHT_START:
		return 37.0
	if index < FLIGHT_END:
		return 70.0
	return 25.0

static func sector(index: int) -> String:
	if index < GAP_START: return "THE ORDINARY ROAD / APPROACH"
	if index < GAP_END: return "BRIDGE GONE / GLIDE"
	if index < 45: return "MOUNTAIN GATE"
	if index < 115: return "TREE & STONE SLALOM"
	if index < FLIGHT_START: return "SUMMIT / SKY REVEAL"
	if index < FLIGHT_END: return "OPEN AIR / CONTROLLED DESCENT"
	return "VALLEY RUNOUT / FINISH"

static func paint(hex: String, roughness: float = 0.88) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(hex)
	m.roughness = roughness
	m.metallic = 0.0
	return m

static func tangent_at(path: PackedVector3Array, index: int) -> Vector3:
	var a: Vector3 = path[maxi(0,index-1)]
	var b: Vector3 = path[mini(path.size()-1,index+1)]
	return Vector3(b.x-a.x,0,b.z-a.z).normalized()

static func _triangle(surface: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, tint: Color) -> void:
	var normal: Vector3 = (b-a).cross(c-a).normalized()
	surface.set_color(tint)
	surface.set_normal(normal)
	surface.add_vertex(a)
	surface.set_color(tint)
	surface.set_normal(normal)
	surface.add_vertex(b)
	surface.set_color(tint)
	surface.set_normal(normal)
	surface.add_vertex(c)

static func _quad(surface: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3, tint: Color) -> void:
	_triangle(surface,a,c,b,tint)
	_triangle(surface,a,d,c,tint)

# The driving surface is viewed from above. Godot's SurfaceTool expects
# clockwise front-facing triangles; generic terrain triangles are wound for
# the opposite side and only appear because terrain disables face culling.
# Keep road winding and lighting normals explicit so Vulkan does not cull it.
static func _road_triangle(surface: SurfaceTool, a: Vector3, b: Vector3, c: Vector3) -> void:
	var top_normal: Vector3=(c-a).cross(b-a).normalized()
	for vertex in [a,b,c]:
		surface.set_normal(top_normal)
		surface.add_vertex(vertex)

static func _road_quad(surface: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3) -> void:
	_road_triangle(surface,a,b,c)
	_road_triangle(surface,a,c,d)

# Local vertex tinting is baked once on the CPU. It needs neither large
# textures nor an expensive per-pixel procedural terrain shader on Android.
static func _shaded_triangle(surface: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, ca: Color, cb: Color, cc: Color) -> void:
	var normal: Vector3=(b-a).cross(c-a).normalized()
	for vertex in [a,b,c]:
		var tint: Color=ca if vertex==a else (cb if vertex==b else cc)
		surface.set_normal(normal)
		surface.set_color(tint)
		surface.add_vertex(vertex)

static func _shaded_quad(surface: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3, ca: Color, cb: Color, cc: Color, cd: Color) -> void:
	_shaded_triangle(surface,a,c,b,ca,cc,cb)
	_shaded_triangle(surface,a,d,c,ca,cd,cc)

static func _valley_height(x: float, z: float, noise: FastNoiseLite) -> float:
	return -11.0+noise.get_noise_2d(x,z)*6.0

static func _valley_tint(x: float, z: float, noise: FastNoiseLite) -> Color:
	var n: float=noise.get_noise_2d(x+970.0,z-310.0)
	var k: float=clampf(0.48+n*0.60,0.0,1.0)
	return Color("455d4b").lerp(Color("7b795d"),k)

static func _slope_vertex(p: Vector3, normal: Vector3, side: float, width: float, distance: float, noise: FastNoiseLite) -> Vector3:
	var pos: Vector3=p+normal*side*(width+0.35+distance)
	var altitude_factor: float=clampf((p.y-30.0)/250.0,0.25,1.0)
	var descent: float=0.6+distance*0.17+pow(distance/255.0,1.35)*100.0*altitude_factor
	var breakup: float=noise.get_noise_2d(pos.x,pos.z)*minf(9.0,distance*0.11)
	pos.y-=descent+breakup
	return pos

static func _slope_tint(p: Vector3, distance: float, noise: FastNoiseLite) -> Color:
	var n: float=noise.get_noise_2d(p.x+310.0,p.z+810.0)
	var rockiness: float=clampf((distance-18.0)/178.0+absf(n)*0.30,0.0,1.0)
	var base: Color=Color("47644d").lerp(Color("69685b"),rockiness)
	return base.lerp(Color("857864"),clampf(0.12+0.16*n+rockiness*0.15,0.0,0.35))

static func _instance_mesh(root: Node3D, mesh: Mesh, mat: Material, transforms: Array[Transform3D], name: String) -> void:
	if transforms.is_empty():
		return
	var group := MultiMesh.new()
	group.transform_format = MultiMesh.TRANSFORM_3D
	group.mesh = mesh
	group.instance_count = transforms.size()
	for i in range(transforms.size()):
		group.set_instance_transform(i,transforms[i])
	var node := MultiMeshInstance3D.new()
	node.name = name
	node.multimesh = group
	node.material_override = mat
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(node)

static func populate(root: Node3D, path: PackedVector3Array) -> Array[Vector3]:
	var asphalt := paint("30383b",0.90)
	var chalk := paint("d4cdb7")
	var warning := paint("e3a354")
	var slab := paint("656d69")
	var dark_rock := paint("3c4040")
	var grass := paint("ffffff")
	grass.vertex_color_use_as_albedo=true
	var pine := paint("304b3a")
	var pine_mid := paint("3a5a42")
	var pine_light := paint("456447")
	var bark := paint("4d4032")
	var rocky := paint("66645e")
	var water := paint("436c7f",0.24)
	water.metallic = 0.18

	# The old giant flat plane was plainly visible from above. Replace it
	# with an undulating valley floor using a single gradient-colored mesh.
	var valley_noise := FastNoiseLite.new()
	valley_noise.seed=11547
	valley_noise.noise_type=FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	valley_noise.frequency=0.008
	valley_noise.fractal_type=FastNoiseLite.FRACTAL_FBM
	valley_noise.fractal_octaves=3
	var floor_builder := SurfaceTool.new()
	floor_builder.begin(Mesh.PRIMITIVE_TRIANGLES)
	for row in range(42):
		for column in range(48):
			var x0: float=-1100.0+float(column)*85.0
			var x1: float=x0+85.0
			var z0: float=-750.0+float(row)*88.0
			var z1: float=z0+88.0
			var a: Vector3=Vector3(x0,_valley_height(x0,z0,valley_noise),z0)
			var b: Vector3=Vector3(x1,_valley_height(x1,z0,valley_noise),z0)
			var c: Vector3=Vector3(x1,_valley_height(x1,z1,valley_noise),z1)
			var d: Vector3=Vector3(x0,_valley_height(x0,z1,valley_noise),z1)
			_shaded_quad(floor_builder,a,b,c,d,_valley_tint(x0,z0,valley_noise),_valley_tint(x1,z0,valley_noise),
				_valley_tint(x1,z1,valley_noise),_valley_tint(x0,z1,valley_noise))
	var valley_node := MeshInstance3D.new()
	valley_node.name="LowlandBase"
	valley_node.mesh=floor_builder.commit()
	valley_node.material_override=grass
	valley_node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(valley_node)

	# Below the fractured span: a genuine open gorge, with reflective blue
	# water well below the hovercraft. One low-cost opaque mesh, no SSR.
	var basin := PlaneMesh.new()
	basin.size=Vector2(730,720)
	basin.material=water
	var basin_node := MeshInstance3D.new()
	basin_node.name="BrokenBridgeGorgeWater"
	basin_node.mesh=basin
	basin_node.position=Vector3(130,0.35,670)
	basin_node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(basin_node)

	var road := SurfaceTool.new()
	road.begin(Mesh.PRIMITIVE_TRIANGLES)
	var terrain := SurfaceTool.new()
	terrain.begin(Mesh.PRIMITIVE_TRIANGLES)
	var relief_noise := FastNoiseLite.new()
	relief_noise.seed=73019
	relief_noise.noise_type=FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	relief_noise.frequency=0.023
	relief_noise.fractal_type=FastNoiseLite.FRACTAL_FBM
	relief_noise.fractal_octaves=3
	var rock_material := paint("ffffff")
	rock_material.vertex_color_use_as_albedo = true
	rock_material.cull_mode = BaseMaterial3D.CULL_DISABLED
	rock_material.roughness = 0.95
	for i in range(path.size()-1):
		var p: Vector3 = path[i]
		var q: Vector3 = path[i+1]
		var n: Vector3 = Vector3(tangent_at(path,i).z,0,-tangent_at(path,i).x)
		var n2: Vector3 = Vector3(tangent_at(path,i+1).z,0,-tangent_at(path,i+1).x)
		var w: float = half_width(i)
		var w2: float = half_width(i+1)
		var flight: bool = i>=FLIGHT_START and i<FLIGHT_END
		var bridge: bool = i>=GAP_START and i<GAP_END
		if not flight and not bridge:
			var a: Vector3 = p-n*w
			var b: Vector3 = p+n*w
			var c: Vector3 = q+n2*w2
			var d: Vector3 = q-n2*w2
			# Road follows genuine altitude changes, rather than a flat ribbon.
			_road_quad(road,a,b,c,d)
			if i<37 or i>=FLIGHT_END:
				var angle: float = atan2(tangent_at(path,i).x,tangent_at(path,i).z)
				var pitch: float = -atan2(q.y-p.y,Vector2(q.x-p.x,q.z-p.z).length())
				for side in [-1.0,1.0]:
					root.call("block",(p+q)*0.5+n*side*(w+0.45)+Vector3.UP*0.25,
						Vector3(0.7,0.5,p.distance_to(q)),slab,angle,pitch)
				if i%3==0:
					root.call("block",(p+q)*0.5+Vector3.UP*0.075,Vector3(0.28,0.06,1.6),chalk,angle,pitch)
			elif i%4==0:
				var angle2: float = atan2(tangent_at(path,i).x,tangent_at(path,i).z)
				for side2 in [-1.0,1.0]:
					root.call("block",(p+q)*0.5+n*side2*(w-1.0)+Vector3.UP*0.05,
						Vector3(0.35,0.08,9.0),warning,angle2)
		# Contoured mountain shoulders: tighter subdivisions near the course
		# and irregular downhill strata. No immense pale three-strip slabs.
		if i>=37 and i<FLIGHT_START:
			var distances := PackedFloat32Array([0.0,7.0,18.0,36.0,62.0,96.0,138.0,190.0,255.0])
			for side3 in [-1.0,1.0]:
				for ring in range(distances.size()-1):
					var low: float=distances[ring]
					var high: float=distances[ring+1]
					var p0: Vector3=_slope_vertex(p,n,side3,w,low,relief_noise)
					var p1: Vector3=_slope_vertex(p,n,side3,w,high,relief_noise)
					var q0: Vector3=_slope_vertex(q,n2,side3,w2,low,relief_noise)
					var q1: Vector3=_slope_vertex(q,n2,side3,w2,high,relief_noise)
					_shaded_quad(terrain,p0,p1,q1,q0,
						_slope_tint(p0,low,relief_noise),_slope_tint(p1,high,relief_noise),
						_slope_tint(q1,high,relief_noise),_slope_tint(q0,low,relief_noise))

	var road_mesh := MeshInstance3D.new()
	road_mesh.name = "SkyfallDriveSurface"
	road_mesh.mesh = road.commit()
	road_mesh.material_override = asphalt
	road_mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(road_mesh)
	var terrain_mesh := MeshInstance3D.new()
	terrain_mesh.name = "SculptedMountainRibbons"
	terrain_mesh.mesh = terrain.commit()
	terrain_mesh.material_override = rock_material
	root.add_child(terrain_mesh)

	# Rock obstacles are *inside* the unusually wide climb; other vegetation
	# stays out of the player's actual racing envelope.
	var rng := RandomNumberGenerator.new()
	rng.seed=721933
	var cone := CylinderMesh.new()
	cone.top_radius = 0.4
	cone.bottom_radius = 3.5
	cone.height = 6.5
	cone.radial_segments = 7
	var trunk := CylinderMesh.new()
	trunk.top_radius = 0.55
	trunk.bottom_radius = 0.68
	trunk.height = 4.5
	trunk.radial_segments = 7
	var stone := SphereMesh.new()
	stone.radius = 3.0
	stone.height = 5.5
	stone.radial_segments = 8
	stone.rings = 4
	var cone_transforms: Array[Transform3D] = []
	var crown_transforms: Array[Transform3D] = []
	var tip_transforms: Array[Transform3D] = []
	var trunk_transforms: Array[Transform3D] = []
	var rock_transforms: Array[Transform3D] = []
	var hazards: Array[Vector3] = []
	for i in range(39,FLIGHT_START,2):
		var p: Vector3 = path[i]
		var n: Vector3 = Vector3(tangent_at(path,i).z,0,-tangent_at(path,i).x)
		for side in [-1.0,1.0]:
			for line in range(3):
				if rng.randf()>0.67: continue
				var offset: float=8.0+float(line)*22.0+rng.randf_range(-5,5)
				var place: Vector3=_slope_vertex(p,n,side,half_width(i),offset,relief_noise)
				var height_scale: float=rng.randf_range(0.9,1.65)
				var basis: Basis=Basis(Vector3.UP,rng.randf_range(0.0,TAU))
				cone_transforms.append(Transform3D(basis.scaled(Vector3.ONE*height_scale),place+Vector3.UP*6.0*height_scale))
				crown_transforms.append(Transform3D(basis.scaled(Vector3.ONE*height_scale*0.78),place+Vector3.UP*9.0*height_scale))
				tip_transforms.append(Transform3D(basis.scaled(Vector3.ONE*height_scale*0.54),place+Vector3.UP*11.7*height_scale))
				trunk_transforms.append(Transform3D(basis.scaled(Vector3.ONE*height_scale),place+Vector3.UP*2.1*height_scale))
		if i>=46 and i<117 and i%5==1:
			var lane: float = (-1.0 if i%2==0 else 1.0)*rng.randf_range(9.0,23.0)
			var rock_pos: Vector3 = p+n*lane
			hazards.append(rock_pos)
			rock_transforms.append(Transform3D(Basis(Vector3.UP,rng.randf_range(0,TAU)).scaled(Vector3(rng.randf_range(1.4,2.0),1.1,rng.randf_range(1.0,1.7))),rock_pos+Vector3.UP*1.8))
	_instance_mesh(root,cone,pine,cone_transforms,"InstancedPineCanopies")
	_instance_mesh(root,cone,pine_mid,crown_transforms,"InstancedPineCrowns")
	_instance_mesh(root,cone,pine_light,tip_transforms,"InstancedPineTips")
	_instance_mesh(root,trunk,bark,trunk_transforms,"InstancedPineTrunks")
	_instance_mesh(root,stone,rocky,rock_transforms,"SlalomBoulders")

	# Distant ridge cards have opaque, jagged top edges. The fog makes these
	# inexpensive 3D silhouettes read as much deeper landscape.
	for band in range(3):
		var skyline := SurfaceTool.new()
		skyline.begin(Mesh.PRIMITIVE_TRIANGLES)
		var haze: Color = Color("647681").lerp(Color("a3aeb1"),float(band)/2.0)
		for section in range(28):
			var x0: float = -550.0+float(section)*115.0
			var x1: float = x0+115.0
			var z: float = 2100.0+float(band)*240.0
			var y0: float = 145.0+66.0*sin(float(section)*0.7+float(band))+32*sin(float(section)*1.9)
			var y1: float = 145.0+66.0*sin(float(section+1)*0.7+float(band))+32*sin(float(section+1)*1.9)
			_quad(skyline,Vector3(x0,0,z),Vector3(x0,y0,z),Vector3(x1,y1,z),Vector3(x1,0,z),haze)
		var ridge := MeshInstance3D.new()
		ridge.name = "DistantRidge_%d"%band
		ridge.mesh = skyline.commit()
		ridge.material_override = rock_material
		ridge.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		root.add_child(ridge)

	# The first half minute deliberately looks like ordinary motorsport.
	var tower := paint("687078")
	var roof := paint("424e55")
	for i in range(5,30,4):
		var p: Vector3 = path[i]
		var n: Vector3 = Vector3(tangent_at(path,i).z,0,-tangent_at(path,i).x)
		for side in [-1.0,1.0]:
			var pos: Vector3 = p+n*side*(49.0+rng.randf_range(0.0,22.0))
			var height: float = rng.randf_range(13,29)
			root.call("block",pos+Vector3.UP*(height/2.0-4),Vector3(23,height,22),tower)
			root.call("block",pos+Vector3.UP*(height-4),Vector3(24,0.7,23),roof)
	# The broken bridge must be visually unmistakable, with a clear landing.
	for id in [GAP_START-1,GAP_END]:
		var p: Vector3 = path[id]
		var n: Vector3 = Vector3(tangent_at(path,id).z,0,-tangent_at(path,id).x)
		var forward: Vector3 = tangent_at(path,id)
		var angle: float = atan2(forward.x,forward.z)
		for side in [-1.0,1.0]:
			root.call("block",p+n*side*17.8-Vector3.UP*8,Vector3(1.2,16,2.5),slab,angle)
		root.call("block",p-Vector3.UP*0.2,Vector3(29,0.45,1.3),warning,angle)
	# Rooftop-like summit marker, aerial entry lights and prominent finish.
	for id in [FLIGHT_START,144,160,178,FLIGHT_END]:
		var p: Vector3 = path[id]
		var n: Vector3 = Vector3(tangent_at(path,id).z,0,-tangent_at(path,id).x)
		for side in [-1.0,1.0]:
			var post := MeshInstance3D.new()
			var beacon_mesh := SphereMesh.new()
			beacon_mesh.radius=2.2
			beacon_mesh.height=4.4
			post.mesh=beacon_mesh
			post.material_override=warning
			post.position=p+n*side*half_width(id)+Vector3.UP*5
			root.add_child(post)
	var finish: Vector3 = path[FINISH_INDEX]
	var tangent: Vector3 = tangent_at(path,FINISH_INDEX)
	var normal: Vector3 = Vector3(tangent.z,0,-tangent.x)
	var yaw: float = atan2(tangent.x,tangent.z)
	for side in [-1.0,1.0]:
		root.call("block",finish+normal*side*23.0+Vector3.UP*5,Vector3(1.4,10,1.4),warning,yaw)
	root.call("block",finish+Vector3.UP*10.2,Vector3(47,1.2,1.6),roof,yaw)
	var label := Label3D.new()
	label.text = "SKYFALL RUN  /  FINISH"
	label.font_size = 94
	label.pixel_size = 0.010
	label.position = finish+Vector3.UP*11.0
	label.rotation.y = yaw
	root.add_child(label)
	return hazards
