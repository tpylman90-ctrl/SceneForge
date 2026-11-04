extends RefCounted

# Crimson Divide's static, deterministic, collision-free landscape.
# A single vertex-coloured formation batch replaces the cylinder forest.
# Geometry is constructed once when a circuit loads, not every frame.
const ROCK_COLORS = [
	Color("b66a47"), Color("d18a58"), Color("a65b43"),
	Color("c47851"), Color("8a503f"), Color("dd9960"),
	Color("a96046"), Color("c17b50")
]
const TERRAIN_PALE = Color("ad7755")
const TERRAIN_DARK = Color("80523f")
# Shared immutable radial profiles avoid re-allocating four arrays for each
# vertex on an Android track load.
const ROCK_LEVELS = [0.0,0.08,0.19,0.31,0.44,0.57,0.69,0.83,1.0]
const ROCK_MESA = [1.16,1.10,1.04,0.93,1.03,0.97,0.92,0.84,0.76]
const ROCK_NEEDLE = [1.08,0.91,0.83,0.70,0.77,0.65,0.55,0.46,0.27]
const ROCK_BLUFF = [1.18,1.06,0.92,1.01,0.91,0.82,0.88,0.70,0.61]

static func _face(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, tint: Color) -> void:
	var normal: Vector3=(b-a).cross(c-a)
	if normal.length_squared()<0.000001:
		return
	normal=normal.normalized()
	st.set_normal(normal)
	st.set_color(tint)
	st.add_vertex(a)
	st.set_normal(normal)
	st.set_color(tint)
	st.add_vertex(b)
	st.set_normal(normal)
	st.set_color(tint)
	st.add_vertex(c)

static func _vertex_material() -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color=Color.WHITE
	mat.vertex_color_use_as_albedo=true
	mat.roughness=0.96
	mat.metallic=0.0
	return mat

static func _distance_to_route_squared(route: PackedVector3Array, x: float, z: float) -> float:
	var closest := INF
	for point in route:
		var dx: float=x-point.x
		var dz: float=z-point.z
		closest=minf(closest,dx*dx+dz*dz)
	return closest

static func _ground_height(route: PackedVector3Array, noise: FastNoiseLite, x: float, z: float) -> float:
	# Road decks and containment walls stay well above decorative terrain.
	var distance: float=sqrt(_distance_to_route_squared(route,x,z))
	var rise: float=smoothstep(19.0,68.0,distance)
	var bedrock: float=absf(noise.get_noise_2d(x*0.48,z*0.48))
	var broad: float=noise.get_noise_2d(x*0.12+77.0,z*0.12-29.0)
	return -0.65+rise*(1.2+bedrock*6.0+2.3*maxf(0.0,broad))

static func _terrain(owner: Node3D, route: PackedVector3Array, noise: FastNoiseLite) -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	const X_COUNT = 38
	const Z_COUNT = 28
	var positions: Array=[]
	# Precompute every height once; colors change per triangle, not per vertex.
	for x in range(X_COUNT+1):
		var strip: Array[Vector3]=[]
		var world_x: float=-342.0+684.0*float(x)/float(X_COUNT)
		for z in range(Z_COUNT+1):
			var world_z: float=-232.0+464.0*float(z)/float(Z_COUNT)
			strip.append(Vector3(world_x,_ground_height(route,noise,world_x,world_z),world_z))
		positions.append(strip)
	for x in range(X_COUNT):
		for z in range(Z_COUNT):
			var a: Vector3=positions[x][z]
			var b: Vector3=positions[x+1][z]
			var c: Vector3=positions[x+1][z+1]
			var d: Vector3=positions[x][z+1]
			var grain: float=clampf(0.5+noise.get_noise_2d(a.x*0.24,a.z*0.24)*0.43,0.0,1.0)
			var tint: Color=TERRAIN_DARK.lerp(TERRAIN_PALE,grain)
			# Counter-clockwise from above (world +Y).
			_face(st,a,c,b,tint)
			_face(st,a,d,c,tint.lightened(0.035))
	var mesh := MeshInstance3D.new()
	mesh.name="CrimsonTerrain"
	mesh.mesh=st.commit()
	mesh.material_override=_vertex_material()
	mesh.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	owner.add_child(mesh)

static func _stone_point(base: Vector3, radius: float, height: float, yaw: float, seed: int, style: int, ring: int, slice: int, sides: int) -> Vector3:
	# Broad mesas, broken towers and eroded wall-like buttes have different profiles.
	var profile: Array=ROCK_MESA if style==0 else (ROCK_NEEDLE if style==1 else ROCK_BLUFF)
	var angle: float=TAU*float(slice)/float(sides)+yaw
	var t: float=ROCK_LEVELS[ring]
	var grain: float=1.0+0.085*sin(angle*3.0+float(seed)*0.13)+0.052*cos(angle*5.0-float(seed)*0.21)
	var fracture: float=1.0+0.055*sin(angle*7.0+float(seed)*0.10+float(ring)*0.68)
	var r: float=radius*profile[ring]*grain*fracture
	var wobble: float=height*0.025*sin(angle*3.0+float(seed)*0.31)*(0.3+0.7*t)
	# Offset upper strata: natural leaning shelves rather than perfect cylinders.
	return base+Vector3(cos(angle)*r+height*0.04*t*sin(float(seed)*0.7),height*t+wobble,sin(angle)*r*0.87+height*0.035*t*cos(float(seed)*0.4))

static func _formation(st: SurfaceTool, base: Vector3, radius: float, height: float, style: int, seed: int, yaw: float) -> void:
	var sides: int=9 if radius<5.0 else 11
	for ring in range(8):
		for slice in range(sides):
			var a: Vector3=_stone_point(base,radius,height,yaw,seed,style,ring,slice,sides)
			var b: Vector3=_stone_point(base,radius,height,yaw,seed,style,ring,(slice+1)%sides,sides)
			var c: Vector3=_stone_point(base,radius,height,yaw,seed,style,ring+1,slice,sides)
			var d: Vector3=_stone_point(base,radius,height,yaw,seed,style,ring+1,(slice+1)%sides,sides)
			var color: Color=ROCK_COLORS[(ring+seed%4)%ROCK_COLORS.size()]
			if ring==2 or ring==5:
				color=color.darkened(0.17)
			color=color*clampf(0.91+0.075*sin(float(slice)*2.1+float(seed)),0.82,1.0)
			# Outer rock surface normal (from interior toward exterior).
			_face(st,a,c,d,color)
			_face(st,a,d,b,color.darkened(0.035))
	var top: Vector3=base+Vector3(height*0.04*sin(float(seed)*0.7),height,0)
	var cap_color: Color=Color("b7815c") if style==0 else Color("a86d4d")
	for slice in range(sides):
		var a: Vector3=_stone_point(base,radius,height,yaw,seed,style,8,slice,sides)
		var b: Vector3=_stone_point(base,radius,height,yaw,seed,style,8,(slice+1)%sides,sides)
		_face(st,top,b,a,cap_color)

static func _ridge_point(index: int, tier: int, id: int) -> Vector3:
	var angle: float=TAU*float(index)/72.0
	var height: float=28.0+14.0*absf(sin(angle*4.0+float(id)*0.6))+9.0*absf(sin(angle*9.0-0.7))
	var jag: float=10.0*sin(angle*7.0+float(id)*0.3)
	var x_radius: float=305.0+float(tier)*22.0
	var z_radius: float=176.0+float(tier)*20.0
	var y: float=-0.8 if tier==0 else (height*0.45 if tier==1 else height)
	return Vector3(cos(angle)*(x_radius+jag),y,sin(angle)*(z_radius+jag*0.64))

static func _ridge(owner: Node3D, id: int) -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for tier in range(2):
		for i in range(72):
			var a: Vector3=_ridge_point(i,tier,id)
			var b: Vector3=_ridge_point(i+1,tier,id)
			var c: Vector3=_ridge_point(i,tier+1,id)
			var d: Vector3=_ridge_point(i+1,tier+1,id)
			var tint: Color=Color("845140") if tier==0 else Color("ad6d50")
			tint=tint.lerp(Color("b77f60"),0.15+0.15*sin(float(i)*0.8))
			# Inward-facing ridgeline; no cylindrical horizon pillars.
			_face(st,a,b,d,tint)
			_face(st,a,d,c,tint.lightened(0.04))
	var mesh := MeshInstance3D.new()
	mesh.name="CrimsonDistantRidgeline"
	mesh.mesh=st.commit()
	mesh.material_override=_vertex_material()
	mesh.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	owner.add_child(mesh)

static func populate(owner: Node3D, route: PackedVector3Array, track_id: int) -> void:
	var noise := FastNoiseLite.new()
	noise.seed=73119+track_id*171
	noise.noise_type=FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	noise.frequency=0.018
	noise.fractal_octaves=3
	_terrain(owner,route,noise)
	_ridge(owner,track_id)
	var rng := RandomNumberGenerator.new()
	rng.seed=61271+track_id*653
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	# Chunked roadside rock faces follow the course but never cross guardrails.
	for index in range(0,route.size(),8):
		var p: Vector3=route[index]
		var forward: Vector3=Vector3(route[(index+2)%route.size()].x-p.x,0,route[(index+2)%route.size()].z-p.z).normalized()
		var normal: Vector3=Vector3(forward.z,0,-forward.x)
		for side in [-1.0,1.0]:
			var radius: float=rng.randf_range(7.0,14.5)
			var offset: float=radius+24.0+rng.randf_range(3.0,17.0)
			var x: float=p.x+side*normal.x*offset
			var z: float=p.z+side*normal.z*offset
			if _distance_to_route_squared(route,x,z)<pow(radius+16.5,2):
				continue
			var ground: float=_ground_height(route,noise,x,z)
			var base := Vector3(x,ground-0.45,z)
			var style: int=(index/8+track_id+int(side+1.0))%3
			_formation(st,base,radius,rng.randf_range(18.0,35.0),style,rng.randi_range(1,30000),rng.randf_range(-PI,PI))
	# Distinct skyline mesas and isolated pillars between course and distant ridge.
	for i in range(28):
		var angle: float=TAU*float(i)/28.0
		var x: float=cos(angle)*(258.0+13.0*sin(angle*5.0))
		var z: float=sin(angle)*(149.0+19.0*cos(angle*3.0))
		var radius: float=rng.randf_range(13.0,23.0)
		if _distance_to_route_squared(route,x,z)<pow(radius+17.0,2):
			continue
		var base := Vector3(x,_ground_height(route,noise,x,z)-0.7,z)
		_formation(st,base,radius,rng.randf_range(28.0,49.0),i%3,rng.randi_range(1,30000),angle)
	# Small weathered talus gives close-up parallax without expensive instances.
	for index in range(0,route.size(),2):
		var p: Vector3=route[index]
		var next: Vector3=route[(index+1)%route.size()]
		var forward: Vector3=Vector3(next.x-p.x,0,next.z-p.z).normalized()
		var normal := Vector3(forward.z,0,-forward.x)
		var side: float=-1.0 if rng.randf()<0.5 else 1.0
		var distance: float=rng.randf_range(19.0,42.0)
		var x: float=p.x+normal.x*side*distance
		var z: float=p.z+normal.z*side*distance
		var radius: float=rng.randf_range(0.9,2.9)
		if _distance_to_route_squared(route,x,z)<pow(radius+15.5,2):
			continue
		_formation(st,Vector3(x,_ground_height(route,noise,x,z)-0.13,z),radius,rng.randf_range(0.7,2.8),2,rng.randi_range(1,30000),rng.randf_range(-PI,PI))
	var mesh := MeshInstance3D.new()
	mesh.name="CrimsonStratifiedCliffs"
	mesh.mesh=st.commit()
	mesh.material_override=_vertex_material()
	owner.add_child(mesh)
