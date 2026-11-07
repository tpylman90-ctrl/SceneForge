extends RefCounted

# Crimson Serpent ONLY (track 4).
# One continuous canyon heightfield replaces the isolated butte field. Every
# surface is visual only; the original road, collision barriers and leap survive.
# The entire terrain is deterministic and built once per circuit load.
const GRID_X = 136
const GRID_Z = 92
# Four static chunks with local origins and two prebuilt mesh resolutions.
const CHUNKS_X = 2
const CHUNKS_Z = 2
const FAR_STEP = 2
const LOD_DISTANCE = 215.0
const SANDSTONE_BREAKUP = preload("res://tracks/serpent_textures/serpent_breakup_256.png")
const HALF_X = 340.0
const HALF_Z = 222.0
const ROAD_CLEARANCE = 16.7
# Bottom plane and perimeter skirts make the heightfield a closed visual shell.
# Above-ground cliffs remain purely decorative, with no racing collisions.
const CLIFF_BASE_Y = -38.0
# Terrain3D-edited source, compiled into 16-bit static heights for Android.
# The Terrain3D GDExtension is NEVER shipped in the racing game.
const SCULPT_PATH = "res://tracks/serpent_sculpt/height.r16"
const SCULPT_W = 1024
const SCULPT_H = 512
const SCULPT_MIN = -32.0
const SCULPT_MAX = 128.0
const SCULPT_X0 = -512.0
const SCULPT_Z0 = -256.0
static var _sculpt_bytes: PackedByteArray = PackedByteArray()
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

static func _sample_sculpt_height(x: float, z: float) -> float:
	# PackedByteArray.decode_u16 reads little-endian ushort values directly.
	# Bilinear reconstruction keeps the editor's 1 m brush details smooth.
	var u: float=clampf(x-SCULPT_X0,0.0,float(SCULPT_W-1))
	var v: float=clampf(z-SCULPT_Z0,0.0,float(SCULPT_H-1))
	var ix: int=floori(u)
	var iz: int=floori(v)
	var jx: int=mini(ix+1,SCULPT_W-1)
	var jz: int=mini(iz+1,SCULPT_H-1)
	var f: float=u-float(ix)
	var g: float=v-float(iz)
	var h00: float=float(_sculpt_bytes.decode_u16((iz*SCULPT_W+ix)*2))
	var h10: float=float(_sculpt_bytes.decode_u16((iz*SCULPT_W+jx)*2))
	var h01: float=float(_sculpt_bytes.decode_u16((jz*SCULPT_W+ix)*2))
	var h11: float=float(_sculpt_bytes.decode_u16((jz*SCULPT_W+jx)*2))
	var encoded: float=lerpf(lerpf(h00,h10,f),lerpf(h01,h11,f),g)
	return SCULPT_MIN+encoded*(SCULPT_MAX-SCULPT_MIN)/65535.0

static func _height(nearest: Vector3, noise: FastNoiseLite, x: float, z: float) -> float:
	if _sculpt_bytes.size()==SCULPT_W*SCULPT_H*2:
		return _sample_sculpt_height(x,z)
	# Protect developer edit sessions with no authoring image, but production
	# CI asserts the file exists and the Android export explicitly includes it.
	return _ground(nearest,noise,x,z)

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
		# Retain the verified two-sided cliff visibility fix.
		mat.cull_mode=BaseMaterial3D.CULL_DISABLED
		# One imported 256px color map; no triplanar or normal texture reads.
		mat.albedo_texture=SANDSTONE_BREAKUP
		mat.uv1_triplanar=false
		mat.uv1_world_triplanar=false
		mat.normal_enabled=false
		mat.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	return mat

static func _surface_uv(point: Vector3, face: Vector3) -> Vector2:
	# Project each triangle from one plane to prevent within-face stretching.
	if absf(face.y)>0.70:
		return Vector2(point.x*0.075,point.z*0.075)
	if absf(face.x)>absf(face.z):
		return Vector2(point.z*0.073,point.y*0.095)
	return Vector2(point.x*0.073,point.y*0.095)

static func _vertex(st: SurfaceTool, point: Vector3, normal: Vector3, tint: Color, uv: Vector2, origin: Vector3) -> void:
	st.set_normal(normal)
	st.set_color(tint)
	st.set_uv(uv)
	st.add_vertex(point-origin)

static func _tri(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, na: Vector3, nb: Vector3, nc: Vector3, ca: Color, cb: Color, cc: Color, origin: Vector3=Vector3.ZERO) -> void:
	var face: Vector3=(b-a).cross(c-a).normalized()
	_vertex(st,a,na,ca,_surface_uv(a,face),origin)
	_vertex(st,b,nb,cb,_surface_uv(b,face),origin)
	_vertex(st,c,nc,cc,_surface_uv(c,face),origin)

static func _cliff_skirt_segment(st: SurfaceTool, a: Vector3, b: Vector3, tint_a: Color, tint_b: Color, outward: Vector3, origin: Vector3, exterior: bool) -> void:
	# External skirts retain the sealed cliff shell; internal skirts hide
	# gaps where nearby and distant geometry have different triangulation.
	var low_a:=Vector3(a.x,CLIFF_BASE_Y if exterior else a.y-11.0,a.z)
	var low_b:=Vector3(b.x,CLIFF_BASE_Y if exterior else b.y-11.0,b.z)
	var foot: Color=Color("634a42") if exterior else tint_a.darkened(0.26)
	_tri(st,a,b,low_b,outward,outward,outward,tint_a,tint_b,foot,origin)
	_tri(st,a,low_b,low_a,outward,outward,outward,tint_a,foot,foot,origin)

static func _close_chunk_boundary(st: SurfaceTool, points: Array, colors: Array, ix0: int, ix1: int, iz0: int, iz1: int, stride: int, origin: Vector3) -> void:
	for ix in range(ix0,ix1,stride):
		_cliff_skirt_segment(st,points[ix][iz0],points[ix+stride][iz0],colors[ix][iz0],colors[ix+stride][iz0],Vector3(0,0,-1),origin,iz0==0)
		_cliff_skirt_segment(st,points[ix+stride][iz1],points[ix][iz1],colors[ix+stride][iz1],colors[ix][iz1],Vector3(0,0,1),origin,iz1==GRID_Z)
	for iz in range(iz0,iz1,stride):
		_cliff_skirt_segment(st,points[ix0][iz+stride],points[ix0][iz],colors[ix0][iz+stride],colors[ix0][iz],Vector3(-1,0,0),origin,ix0==0)
		_cliff_skirt_segment(st,points[ix1][iz],points[ix1][iz+stride],colors[ix1][iz],colors[ix1][iz+stride],Vector3(1,0,0),origin,ix1==GRID_X)
	# Reproduce the original underside cap, now one low-cost quad per chunk.
	var a:=Vector3(points[ix0][iz0].x,CLIFF_BASE_Y,points[ix0][iz0].z)
	var b:=Vector3(points[ix1][iz0].x,CLIFF_BASE_Y,points[ix1][iz0].z)
	var c:=Vector3(points[ix1][iz1].x,CLIFF_BASE_Y,points[ix1][iz1].z)
	var d:=Vector3(points[ix0][iz1].x,CLIFF_BASE_Y,points[ix0][iz1].z)
	var down:=Vector3.DOWN
	var bedrock:=Color("634a42")
	_tri(st,a,b,c,down,down,down,bedrock,bedrock,bedrock,origin)
	_tri(st,a,c,d,down,down,down,bedrock,bedrock,bedrock,origin)

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
			var height: float=_height(nearest,noise,x,z)
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
	var group:=Node3D.new()
	group.name="CrimsonStratifiedCliffs"
	owner.add_child(group)
	var sandstone: StandardMaterial3D=_material(true)
	var x_step: int=int(GRID_X/CHUNKS_X)
	var z_step: int=int(GRID_Z/CHUNKS_Z)
	for chunk_x in range(CHUNKS_X):
		for chunk_z in range(CHUNKS_Z):
			var x0: int=chunk_x*x_step
			var x1: int=(chunk_x+1)*x_step
			var z0: int=chunk_z*z_step
			var z1: int=(chunk_z+1)*z_step
			# Visibility range distance uses the node's origin, not mesh bounds.
			var center:=Vector3((points[x0][z0].x+points[x1][z1].x)*0.5,0.0,(points[x0][z0].z+points[x1][z1].z)*0.5)
			for lod in range(2):
				var stride: int=1 if lod==0 else FAR_STEP
				var st:=SurfaceTool.new()
				st.begin(Mesh.PRIMITIVE_TRIANGLES)
				for ix in range(x0,x1,stride):
					for iz in range(z0,z1,stride):
						var a: Vector3=points[ix][iz]
						var b: Vector3=points[ix+stride][iz]
						var c: Vector3=points[ix+stride][iz+stride]
						var d: Vector3=points[ix][iz+stride]
						var na: Vector3=smooth_normals[ix][iz]
						var nb: Vector3=smooth_normals[ix+stride][iz]
						var nc: Vector3=smooth_normals[ix+stride][iz+stride]
						var nd: Vector3=smooth_normals[ix][iz+stride]
						var ca: Color=shades[ix][iz]
						var cb: Color=shades[ix+stride][iz]
						var cc: Color=shades[ix+stride][iz+stride]
						var cd: Color=shades[ix][iz+stride]
						_tri(st,a,c,b,na,nc,nb,ca,cc,cb,center)
						_tri(st,a,d,c,na,nd,nc,ca,cd,cc,center)
				_close_chunk_boundary(st,points,shades,x0,x1,z0,z1,stride,center)
				var patch:=MeshInstance3D.new()
				patch.name=("Near_" if lod==0 else "Far_")+str(chunk_x)+"_"+str(chunk_z)
				patch.mesh=st.commit()
				patch.position=center
				patch.material_override=sandstone
				patch.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				if lod==0:
					patch.visibility_range_end=LOD_DISTANCE
					patch.visibility_range_end_margin=8.0
				else:
					patch.visibility_range_begin=LOD_DISTANCE
					patch.visibility_range_begin_margin=8.0
				group.add_child(patch)

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
			c.y=_height(_nearest(route,c.x,c.z),noise,c.x,c.z)
			d.y=_height(_nearest(route,d.x,d.z),noise,d.x,d.z)
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
		var ground: float=_height(nearest,noise,x,z)
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
	_sculpt_bytes=FileAccess.get_file_as_bytes(SCULPT_PATH)
	if _sculpt_bytes.size()!=SCULPT_W*SCULPT_H*2:
		push_error("Crimson Serpent authored heightmap missing or wrong size; using procedural fallback")
	var noise: FastNoiseLite=_noise()
	_cliff_mesh(owner,route,noise)
	_road_shoulder(owner,route,noise)
	_far_ridge(owner)
	_talus(owner,route,noise)
