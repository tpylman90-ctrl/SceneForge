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
	Color("9d5b47"), Color("aa674d"), Color("b87755"),
	Color("c98c65"), Color("a46b50")
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
	var sector: int=clampi(index/48,0,3)
	# Hugs the roadway on both sides but leaves a broad physical clearance
	# for barriers and the racing line. No solid cliffs can cross the deck.
	var wall_begin: float=ROAD_CLEARANCE+1.0*sin(float(index)*0.085)
	var rise: float=smoothstep(wall_begin,wall_begin+26.0,distance)
	var detail: float=noise.get_noise_2d(x*0.42,z*0.42)
	var weathering: float=noise.get_noise_2d(x*0.095+83.0,z*0.095-17.0)
	var wall_top: float=[47.0,37.0,52.0,57.0][sector]
	wall_top+=7.0*weathering+4.0*sin(float(index)*0.11)
	# A shallow shoulder follows each climb/descent, so the road is a
	# canyon floor instead of a floating bridge over an unrelated slab.
	var floor_y: float=nearest.z-2.1
	# Keep the actual four-segment jump deck gap clearly below the racer.
	if index>=43 and index<=48:
		floor_y=minf(floor_y,-3.0)
	var face_breakup: float=rise*(2.7*detail+1.3*noise.get_noise_2d(x*0.75,z*0.75))
	var plateau: float=smoothstep(46.0,94.0,distance)*(7.0+6.0*weathering)
	return floor_y+rise*wall_top+face_breakup+plateau

static func _color(y: float, distance: float, x: float, z: float, noise: FastNoiseLite) -> Color:
	# Macro layers come from height and weathering, NOT regular alternating
	# color blocks. The distant wall reads as coherent sedimentary rock.
	var grain: float=noise.get_noise_2d(x*0.18+63.0,z*0.18-11.0)
	var contour: float=noise.get_noise_2d(x*0.34+7.0,z*0.34+51.0)
	var step: float=0.5+0.5*sin(y*0.91+0.95*contour)
	var hue: float=clampf(0.37+0.22*grain+0.13*step,0.08,0.88)
	var color: Color=ROCK_PALETTE[0].lerp(ROCK_PALETTE[3],hue)
	var seam: float=1.0-0.075*pow(1.0-step,3.0)
	color*=seam
	color=color.lerp(Color("97715d"),clampf((distance-160.0)/180.0,0.0,0.26))
	if distance<20.0:
		color=color.lerp(Color("865d4d"),1.0-smoothstep(15.0,21.0,distance))
	return color

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
		var image := Image.create(128,128,false,Image.FORMAT_RGB8)
		var micro := FastNoiseLite.new()
		micro.seed=918733
		micro.frequency=0.057
		micro.noise_type=FastNoiseLite.TYPE_SIMPLEX_SMOOTH
		for x in range(128):
			for y in range(128):
				var n: float=micro.get_noise_2d(float(x),float(y))
				var v: float=clampf(0.90+0.095*n,0.79,1.0)
				image.set_pixel(x,y,Color(v,v*0.992,v*0.98))
		image.generate_mipmaps()
		mat.albedo_texture=ImageTexture.create_from_image(image)
		mat.uv1_triplanar=true
		mat.uv1_world_triplanar=true
		mat.uv1_scale=Vector3(0.13,0.13,0.13)
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
	# A continuous, low-geometry horizon. Atmospheric fog handles detail at
	# this range; extra geometry would be invisible at Android resolution.
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var near_color: Color=Color("8a665d")
	var top_color: Color=Color("b48a70")
	for index in range(96):
		var p: float=TAU*float(index)/96.0
		var q: float=TAU*float(index+1)/96.0
		var h0: float=54.0+17.0*absf(sin(p*3.0))+9.0*absf(sin(p*8.0-0.3))
		var h1: float=54.0+17.0*absf(sin(q*3.0))+9.0*absf(sin(q*8.0-0.3))
		var a:=Vector3(365.0*cos(p),5.0,265.0*sin(p))
		var b:=Vector3(365.0*cos(q),5.0,265.0*sin(q))
		var c:=Vector3(365.0*cos(q),h1,265.0*sin(q))
		var d:=Vector3(365.0*cos(p),h0,265.0*sin(p))
		var n: Vector3=Vector3(-cos((p+q)*0.5),0.0,-sin((p+q)*0.5))
		_tri(st,a,b,c,n,n,n,near_color,near_color,top_color)
		_tri(st,a,c,d,n,n,n,near_color,top_color,top_color)
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
