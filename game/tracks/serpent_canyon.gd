extends RefCounted

# Crimson Serpent ONLY (track 4).
# One continuous canyon heightfield replaces the isolated butte field. Every
# surface is visual only; the original road, collision barriers and leap survive.
# The entire terrain is deterministic and built once per circuit load.
const GRID_X = 136
const GRID_Z = 92
const HALF_X = 340.0
const HALF_Z = 222.0
const ROAD_CLEARANCE = 16.7
const ROCK_PALETTE = [
	Color("85503e"), Color("9c6049"), Color("ae7053"),
	Color("ba8060"), Color("9e654e")
]

static func _noise() -> FastNoiseLite:
	var noise := FastNoiseLite.new()
	noise.seed=904211
	noise.noise_type=FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	noise.frequency=0.024
	noise.fractal_octaves=3
	return noise

static func _nearest(route: PackedVector3Array, x: float, z: float) -> Vector3:
	# x = distance, y = nearest segment, z = interpolated road elevation.
	# Segment projection (not point distance) gives a smooth carved floor
	# even on the tightest bends and when neighboring road branches converge.
	var closest: float=INF
	var nearest_index: int=0
	var road_y: float=0.0
	for index in range(route.size()):
		var p: Vector3=route[index]
		var q: Vector3=route[(index+1)%route.size()]
		var dx: float=q.x-p.x
		var dz: float=q.z-p.z
		var length_squared: float=maxf(0.001,dx*dx+dz*dz)
		var t: float=clampf(((x-p.x)*dx+(z-p.z)*dz)/length_squared,0.0,1.0)
		var side_x: float=x-p.x-dx*t
		var side_z: float=z-p.z-dz*t
		var d2: float=side_x*side_x+side_z*side_z
		if d2<closest:
			closest=d2
			nearest_index=index
			road_y=lerpf(p.y,q.y,t)
	return Vector3(sqrt(closest),float(nearest_index),road_y)

static func _ground(nearest: Vector3, noise: FastNoiseLite, x: float, z: float) -> float:
	var distance: float=nearest.x
	var index: int=int(nearest.y)
	var phase: float=TAU*float(index)/192.0
	# Periodic height variation removes the previous abrupt 4-sector jumps.
	var wall_begin: float=ROAD_CLEARANCE+0.8*sin(phase*3.0+0.3)
	var d: float=maxf(0.0,distance-wall_begin)
	var erosion: float=noise.get_noise_2d(x*0.15+33.0,z*0.15-11.0)
	var fine: float=noise.get_noise_2d(x*0.67,z*0.67)
	var broad: float=noise.get_noise_2d(x*0.062-81.0,z*0.062+46.0)
	# Carved sandstone: apron, steep scarp, two eroded benches and an upper rim.
	var toe: float=4.8*smoothstep(0.0,5.3,d)
	var lower_face: float=16.4*smoothstep(4.5,10.6,d)
	var lower_shelf: float=2.3*smoothstep(11.1,16.3,d)
	var upper_face: float=18.3*smoothstep(16.0,23.2,d)
	var upper_shelf: float=3.7*smoothstep(24.4,28.0,d)
	var rim: float=7.5*smoothstep(28.0,36.0,d)
	var mesa: float=5.5*smoothstep(40.0,84.0,d)
	var mass: float=toe+lower_face+lower_shelf+upper_face+upper_shelf+rim+mesa
	var variation: float=0.94+0.085*sin(phase*2.0+0.7)+0.06*sin(phase*5.0-0.4)
	var fracture: float=smoothstep(5.0,12.0,d)*(1.8*erosion+0.55*fine)
	var weathering: float=smoothstep(15.0,43.0,d)*2.4*broad
	var floor_y: float=nearest.z-2.3
	# Gradual carve underneath the leap, no abrupt step at index 43/48.
	var gap_mask: float=smoothstep(39.0,44.0,float(index))*(1.0-smoothstep(48.0,53.0,float(index)))
	floor_y=lerpf(floor_y,minf(floor_y,-3.0),gap_mask)
	return floor_y+mass*variation+fracture+weathering

static func _color(y: float, distance: float, x: float, z: float, noise: FastNoiseLite) -> Color:
	# Subtle layered rock bedding and darkened bases, avoiding stripe blocks.
	var grain: float=noise.get_noise_2d(x*0.18+63.0,z*0.18-11.0)
	var contour: float=noise.get_noise_2d(x*0.34+7.0,z*0.34+51.0)
	var strata_y: float=y+2.6*noise.get_noise_2d(x*0.11+53.0,z*0.11-47.0)
	var band: float=0.5+0.5*sin(strata_y*0.44+contour)
	var seam: float=pow(1.0-band,8.0)
	var hue: float=clampf(0.44+0.23*grain+0.12*band,0.07,0.9)
	var color: Color=ROCK_PALETTE[0].lerp(ROCK_PALETTE[3],hue)
	color*=1.0-0.11*seam
	var near_foot: float=1.0-smoothstep(17.0,29.0,distance)
	color=color.lerp(ROCK_PALETTE[0].darkened(0.08),near_foot*0.48)
	return color.lerp(Color("a27b6a"),clampf((distance-125.0)/210.0,0.0,0.24))

static func _material(use_grain: bool=false) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color=Color.WHITE
	mat.vertex_color_use_as_albedo=true
	mat.roughness=0.97
	mat.metallic=0.0
	if use_grain:
		# Tiny baked-on-load tiling grain, only one texture rather than a
		# costly stack of PBR maps. World triplanar prevents stretching over
		# cliffs without demanding dense geometry or external paid textures.
		var image := Image.create(256,256,false,Image.FORMAT_RGB8)
		var micro := FastNoiseLite.new()
		micro.seed=918733
		micro.frequency=0.072
		micro.noise_type=FastNoiseLite.TYPE_SIMPLEX_SMOOTH
		for x in range(256):
			for y in range(256):
				var n: float=micro.get_noise_2d(float(x),float(y))
				var chips: float=micro.get_noise_2d(float(x)*1.9+37.0,float(y)*1.9-13.0)
				var drift: float=micro.get_noise_2d(float(x)*0.23+87.0,float(y)*0.23)
				var bedding: float=0.5+0.5*sin(TAU*(float(y)/32.0+0.012*drift))
				var seam: float=pow(1.0-bedding,13.0)*0.17
				var crack: float=pow(maxf(0.0,0.5-absf(chips)),5.0)*0.37
				var v: float=clampf(0.91+0.14*n+0.04*chips-seam-crack,0.63,1.0)
				image.set_pixel(x,y,Color(v,v*0.987,v*0.978))
		image.generate_mipmaps()
		mat.albedo_texture=ImageTexture.create_from_image(image)
		mat.uv1_triplanar=true
		mat.uv1_world_triplanar=true
		mat.uv1_scale=Vector3(0.105,0.105,0.105)
	return mat

static func _vertex(st: SurfaceTool, point: Vector3, normal: Vector3, tint: Color) -> void:
	st.set_normal(normal)
	st.set_color(tint)
	st.set_uv(Vector2(point.x*0.05+point.z*0.018,point.y*0.09))
	st.add_vertex(point)

static func _tri(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, na: Vector3, nb: Vector3, nc: Vector3, ca: Color, cb: Color, cc: Color) -> void:
	_vertex(st,a,na,ca)
	_vertex(st,b,nb,cb)
	_vertex(st,c,nc,cc)

static func _cliff_mesh(owner: Node3D, route: PackedVector3Array, noise: FastNoiseLite) -> void:
	var points: Array=[]
	var shades: Array=[]
	for ix in range(GRID_X+1):
		var x: float=-HALF_X+2.0*HALF_X*float(ix)/float(GRID_X)
		var strip: Array[Vector3]=[]
		var colors: Array[Color]=[]
		for iz in range(GRID_Z+1):
			var z: float=-HALF_Z+2.0*HALF_Z*float(iz)/float(GRID_Z)
			var nearest: Vector3=_nearest(route,x,z)
			var height: float=_ground(nearest,noise,x,z)
			strip.append(Vector3(x,height,z))
			colors.append(_color(height,nearest.x,x,z,noise))
		points.append(strip)
		shades.append(colors)
	# Reuse the same averaged normal across adjacent triangles to remove
	# obvious low-poly blocks without increasing the triangle budget.
	var smooth_normals: Array=[]
	for ix in range(GRID_X+1):
		var normals: Array[Vector3]=[]
		for iz in range(GRID_Z+1):
			var lo_x: Vector3=points[maxi(0,ix-1)][iz]
			var hi_x: Vector3=points[mini(GRID_X,ix+1)][iz]
			var lo_z: Vector3=points[ix][maxi(0,iz-1)]
			var hi_z: Vector3=points[ix][mini(GRID_Z,iz+1)]
			var dx: float=(hi_x.y-lo_x.y)/maxf(0.01,hi_x.x-lo_x.x)
			var dz: float=(hi_z.y-lo_z.y)/maxf(0.01,hi_z.z-lo_z.z)
			normals.append(Vector3(-dx,1.0,-dz).normalized())
		smooth_normals.append(normals)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for ix in range(GRID_X):
		for iz in range(GRID_Z):
			var a: Vector3=points[ix][iz]
			var b: Vector3=points[ix+1][iz]
			var c: Vector3=points[ix+1][iz+1]
			var d: Vector3=points[ix][iz+1]
			var na: Vector3=smooth_normals[ix][iz]
			var nb: Vector3=smooth_normals[ix+1][iz]
			var nc: Vector3=smooth_normals[ix+1][iz+1]
			var nd: Vector3=smooth_normals[ix][iz+1]
			var ca: Color=shades[ix][iz]
			var cb: Color=shades[ix+1][iz]
			var cc: Color=shades[ix+1][iz+1]
			var cd: Color=shades[ix][iz+1]
			# The grid is one continuous surface, including joined canyon walls
			# and saddle passes between neighboring serpentine road sections.
			_tri(st,a,c,b,na,nc,nb,ca,cc,cb)
			_tri(st,a,d,c,na,nd,nc,ca,cd,cc)
	var mesh := MeshInstance3D.new()
	mesh.name="CrimsonStratifiedCliffs"
	mesh.mesh=st.commit()
	mesh.material_override=_material(true)
	# Avoid giant stairstep shadow triangles across the mobile racing surface.
	# Diffuse terrain normals and baked albedo still shade the canyon itself.
	mesh.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	owner.add_child(mesh)

static func _road_shoulder(owner: Node3D, route: PackedVector3Array, noise: FastNoiseLite) -> void:
	# Thin gravel transitions blend the raised road edges into the canyon
	# floor. Only decorative: cannot affect steering or collisions.
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var size: int=route.size()
	var soil: Color=Color("8a624f")
	for index in range(size):
		var p: Vector3=route[index]
		var q: Vector3=route[(index+1)%size]
		var tangent: Vector3=Vector3(q.x-p.x,0.0,q.z-p.z).normalized()
		var next: Vector3=route[(index+2)%size]
		var ahead: Vector3=Vector3(next.x-q.x,0.0,next.z-q.z).normalized()
		var side: Vector3=Vector3(tangent.z,0,-tangent.x)
		var side_next: Vector3=Vector3(ahead.z,0,-ahead.x)
		for sign in [-1.0,1.0]:
			var w: float=10.5 if index>=86 and index<=126 else 12.0
			var next_i: int=(index+1)%size
			var w_next: float=10.5 if next_i>=86 and next_i<=126 else 12.0
			var a: Vector3=p+side*sign*(w+1.5)-Vector3.UP*0.55
			var b: Vector3=q+side_next*sign*(w_next+1.5)-Vector3.UP*0.55
			var c: Vector3=q+side_next*sign*(w_next+5.6)
			var d: Vector3=p+side*sign*(w+5.6)
			c.y=_ground(_nearest(route,c.x,c.z),noise,c.x,c.z)
			d.y=_ground(_nearest(route,d.x,d.z),noise,d.x,d.z)
			# Skip the gap, keeping a visible leap instead of a soil bridge.
			if index>=44 and index<48:
				continue
			var n: Vector3=Vector3.UP
			_tri(st,a,b,c,n,n,n,soil,soil,soil.lightened(0.04))
			_tri(st,a,c,d,n,n,n,soil,soil.lightened(0.04),soil.lightened(0.05))
	var mesh := MeshInstance3D.new()
	mesh.name="CrimsonTerrain"
	mesh.mesh=st.commit()
	mesh.material_override=_material()
	mesh.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	owner.add_child(mesh)

static func _far_ridge(owner: Node3D) -> void:
	# Two atmospheric skyline silhouettes in a single low-poly material batch.
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for layer in range(2):
		var rx: float=367.0 if layer==0 else 414.0
		var rz: float=257.0 if layer==0 else 287.0
		var bottom: Color=Color("805d51") if layer==0 else Color("98796a")
		var top: Color=Color("a77b64") if layer==0 else Color("b9957d")
		for index in range(96):
			var p: float=TAU*float(index)/96.0
			var q: float=TAU*float(index+1)/96.0
			var h0: float=53.0+17.0*absf(sin(p*3.0+float(layer)*0.7))+10.0*absf(sin(p*9.0-0.3))
			var h1: float=53.0+17.0*absf(sin(q*3.0+float(layer)*0.7))+10.0*absf(sin(q*9.0-0.3))
			var a:=Vector3(rx*cos(p),-4.0,rz*sin(p))
			var b:=Vector3(rx*cos(q),-4.0,rz*sin(q))
			var c:=Vector3(rx*cos(q),h1,rz*sin(q))
			var d:=Vector3(rx*cos(p),h0,rz*sin(p))
			var n: Vector3=Vector3(-cos((p+q)*0.5),0.0,-sin((p+q)*0.5))
			_tri(st,a,b,c,n,n,n,bottom,bottom,top)
			_tri(st,a,c,d,n,n,n,bottom,top,top)
	var mesh := MeshInstance3D.new()
	mesh.name="CrimsonDistantRidgeline"
	mesh.mesh=st.commit()
	mesh.material_override=_material()
	mesh.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	owner.add_child(mesh)

static func _talus(owner: Node3D, route: PackedVector3Array, noise: FastNoiseLite) -> void:
	var pebble := SphereMesh.new()
	pebble.radial_segments=8
	pebble.rings=4
	var mat := _material()
	pebble.material=mat
	var placements: Array[Transform3D]=[]
	var colors: Array[Color]=[]
	var rng := RandomNumberGenerator.new()
	rng.seed=332147
	for index in range(0,route.size(),2):
		var p: Vector3=route[index]
		var q: Vector3=route[(index+1)%route.size()]
		var direction:=Vector3(q.x-p.x,0.0,q.z-p.z).normalized()
		var side:=Vector3(direction.z,0.0,-direction.x)
		var sign: float=-1.0 if rng.randf()<0.5 else 1.0
		var span: float=rng.randf_range(19.0,34.0)
		var x: float=p.x+side.x*span*sign
		var z: float=p.z+side.z*span*sign
		var nearest: Vector3=_nearest(route,x,z)
		if nearest.x<17.8:
			continue
		var r: float=rng.randf_range(0.55,1.65)
		var h: float=rng.randf_range(0.35,0.9)
		var ground: float=_ground(nearest,noise,x,z)
		var orientation: Basis=Basis(Vector3.UP,rng.randf_range(-PI,PI)).scaled(Vector3(r,h,r*0.78))
		placements.append(Transform3D(orientation,Vector3(x,ground+h*0.35,z)))
		colors.append(Color("a76e54").lerp(Color("ca8a62"),rng.randf_range(0.0,1.0)))
	var multi := MultiMesh.new()
	multi.transform_format=MultiMesh.TRANSFORM_3D
	multi.use_colors=true
	multi.mesh=pebble
	multi.instance_count=placements.size()
	for index in range(placements.size()):
		multi.set_instance_transform(index,placements[index])
		multi.set_instance_color(index,colors[index])
	var instance := MultiMeshInstance3D.new()
	instance.name="CrimsonTalus"
	instance.multimesh=multi
	instance.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	owner.add_child(instance)

static func populate(owner: Node3D, route: PackedVector3Array) -> void:
	var noise: FastNoiseLite=_noise()
	_cliff_mesh(owner,route,noise)
	_road_shoulder(owner,route,noise)
	_far_ridge(owner)
	_talus(owner,route,noise)
