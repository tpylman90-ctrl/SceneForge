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
	var asphalt := paint("343c40",0.91)
	var chalk := paint("d4cdb7")
	var warning := paint("e3a354")
	var slab := paint("656d69")
	var dark_rock := paint("3c4040")
	var grass := paint("718363")
	var pine := paint("304b3a")
	var bark := paint("4d4032")
	var rocky := paint("66645e")

	var valley := PlaneMesh.new()
	valley.size = Vector2(4100,3500)
	valley.material = grass
	var valley_node := MeshInstance3D.new()
	valley_node.name = "LowlandBase"
	valley_node.mesh = valley
	valley_node.position = Vector3(850,0,1030)
	valley_node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(valley_node)

	var road := SurfaceTool.new()
	road.begin(Mesh.PRIMITIVE_TRIANGLES)
	var terrain := SurfaceTool.new()
	terrain.begin(Mesh.PRIMITIVE_TRIANGLES)
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
			_quad(road,a,b,c,d,Color.WHITE)
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
		# A sculpted route-hugging landscape, deliberately absent from the
		# open-air section. The lowland is a separate low-cost plane.
		if i>=37 and i<FLIGHT_START:
			for side3 in [-1.0,1.0]:
				var start: Vector3 = p+n*side3*(w+0.1)
				var end: Vector3 = q+n2*side3*(w2+0.1)
				for ring in range(3):
					var low: float = float(ring)*48.0
					var high: float = float(ring+1)*48.0
					var p0: Vector3 = start+n*side3*low
					var p1: Vector3 = start+n*side3*high
					var q0: Vector3 = end+n2*side3*low
					var q1: Vector3 = end+n2*side3*high
					p0.y -= 0.6+low*0.10
					q0.y -= 0.6+low*0.10
					p1.y -= 0.6+high*0.10+4.0*sin(float(i)*0.38+side3+float(ring))
					q1.y -= 0.6+high*0.10+4.0*sin(float(i+1)*0.38+side3+float(ring))
					var tone: Color = Color("6e8066") if ring==0 else (Color("737269") if ring==1 else Color("535952"))
					_quad(terrain,p0,p1,q1,q0,tone)
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
	cone.top_radius = 0.12
	cone.bottom_radius = 3.4
	cone.height = 11.0
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
	var trunk_transforms: Array[Transform3D] = []
	var rock_transforms: Array[Transform3D] = []
	var hazards: Array[Vector3] = []
	for i in range(39,FLIGHT_START,2):
		var p: Vector3 = path[i]
		var n: Vector3 = Vector3(tangent_at(path,i).z,0,-tangent_at(path,i).x)
		for side in [-1.0,1.0]:
			for line in range(3):
				if rng.randf()>0.67: continue
				var offset: float = half_width(i)+8.0+float(line)*22.0+rng.randf_range(-5,5)
				var place: Vector3 = p+n*side*offset
				place.y -= 0.5+(offset-half_width(i))*0.11
				var height_scale: float = rng.randf_range(0.72,1.45)
				cone_transforms.append(Transform3D(Basis().scaled(Vector3(height_scale, height_scale, height_scale)),place+Vector3.UP*5.8*height_scale))
				trunk_transforms.append(Transform3D(Basis().scaled(Vector3(height_scale,height_scale,height_scale)),place+Vector3.UP*2.1*height_scale))
		if i>=46 and i<117 and i%9==1:
			var lane: float = (-1.0 if i%2==0 else 1.0)*rng.randf_range(9.0,23.0)
			var rock_pos: Vector3 = p+n*lane
			hazards.append(rock_pos)
			rock_transforms.append(Transform3D(Basis(Vector3.UP,rng.randf_range(0,TAU)).scaled(Vector3(rng.randf_range(1.4,2.0),1.1,rng.randf_range(1.0,1.7))),rock_pos+Vector3.UP*1.8))
	_instance_mesh(root,cone,pine,cone_transforms,"InstancedPineCanopies")
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
