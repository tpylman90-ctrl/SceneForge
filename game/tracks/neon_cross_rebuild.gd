extends RefCounted
const SkylineFeatures=preload("res://tracks/neon_cross_skyline.gd")

# Neon Cross / Aerial City Rebuild (track 0 only).
#
# The race route, crossing separation, jump physics and checkpoints belong to
# city_loop.gd and are intentionally unchanged. Everything visible is rebuilt
# with sparse deck anchors, luminous spline boundaries, 3D gate landmarks and
# spatially grouped static skyline instances. Nothing has physical collision.
#
# All static generation happens once at load. Draw budgets are based on node
# groups/materials rather than thousands of independent window meshes.
const DECK_RANGES := [
	Vector2i(0, 14), Vector2i(33, 44), Vector2i(52, 61),
	Vector2i(90, 100), Vector2i(138, 151), Vector2i(181, 192)
]
const AIR_GATE_INDICES := [18, 26, 65, 78, 108, 121, 161, 174]
const BUILDING_LEVEL := -82.0
const CLOSE_ROUTE_CLEARANCE := 28.0
const GRID_STEP_X := 19.0
const GRID_STEP_Z := 19.0
const MAX_BUILDINGS := 200

static func has_deck(index: int) -> bool:
	var wrapped: int=posmod(index,192)
	for interval in DECK_RANGES:
		if wrapped>=interval.x and wrapped<interval.y:
			return true
	return false

static func _mat(hex: String, unlit: bool=false, roughness: float=0.88) -> StandardMaterial3D:
	var m:=StandardMaterial3D.new()
	m.albedo_color=Color(hex)
	m.roughness=roughness
	m.cull_mode=BaseMaterial3D.CULL_DISABLED
	if unlit:
		m.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
	return m

static func _vertex_mat(unlit: bool=false) -> StandardMaterial3D:
	var m:=_mat("ffffff",unlit)
	m.vertex_color_use_as_albedo=true
	return m

static func _st() -> SurfaceTool:
	var tool:=SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	return tool

static func _tri(tool: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, tint: Color) -> void:
	var normal: Vector3=(b-a).cross(c-a)
	if normal.length_squared()<0.0000001:
		return
	normal=normal.normalized()
	for p in [a,b,c]:
		tool.set_normal(normal)
		tool.set_color(tint)
		tool.set_uv(Vector2(p.x,p.z)*0.10)
		tool.add_vertex(p)

static func _quad(tool: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3, tint: Color) -> void:
	_tri(tool,a,b,c,tint)
	_tri(tool,a,c,d,tint)

static func _mesh(parent: Node3D, name: String, tool: SurfaceTool, mat: Material) -> MeshInstance3D:
	var instance:=MeshInstance3D.new()
	instance.name=name
	instance.mesh=tool.commit()
	instance.material_override=mat
	instance.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(instance)
	return instance

static func _box(batches: Dictionary, pos: Vector3, size: Vector3, mat: Material, yaw: float=0.0) -> void:
	if not batches.has(mat):
		batches[mat]=_st()
	var builder: SurfaceTool=batches[mat]
	var cube:=BoxMesh.new()
	cube.size=size
	builder.append_from(cube,0,Transform3D(Basis(Vector3.UP,yaw),pos))

static func _flush_boxes(parent: Node3D, batches: Dictionary) -> void:
	var i: int=0
	for mat in batches:
		_mesh(parent,"NeonStructuralBatch_%d"%i,batches[mat],mat)
		i+=1

static func _distance_to_route_xz(route: PackedVector3Array, x: float, z: float) -> float:
	var closest: float=INF
	for i in range(route.size()):
		var a: Vector3=route[i]
		var b: Vector3=route[(i+1)%route.size()]
		var dx: float=b.x-a.x
		var dz: float=b.z-a.z
		var scale: float=maxf(dx*dx+dz*dz,0.00001)
		var t: float=clampf(((x-a.x)*dx+(z-a.z)*dz)/scale,0.0,1.0)
		var rx: float=x-a.x-dx*t
		var rz: float=z-a.z-dz*t
		closest=minf(closest,rx*rx+rz*rz)
	return sqrt(closest)

static func _district(position: Vector3) -> int:
	return (2 if position.z>=0.0 else 0)+(1 if position.x>=0.0 else 0)

static func _instances(parent: Node3D, name: String, descriptors: Array, unlit: bool=false) -> void:
	if descriptors.is_empty():
		return
	var cube:=BoxMesh.new()
	cube.size=Vector3.ONE
	var multi:=MultiMesh.new()
	multi.transform_format=MultiMesh.TRANSFORM_3D
	multi.use_colors=true
	multi.mesh=cube
	multi.instance_count=descriptors.size()
	for i in range(descriptors.size()):
		var item: Dictionary=descriptors[i]
		var transform:=Transform3D(Basis().scaled(item["size"]),item["position"])
		multi.set_instance_transform(i,transform)
		multi.set_instance_color(i,item["color"])
	var instance:=MultiMeshInstance3D.new()
	instance.name=name
	instance.multimesh=multi
	instance.material_override=_vertex_mat(unlit)
	instance.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(instance)

static func _skyline(parent: Node3D, route: PackedVector3Array) -> void:
	# Buildings are now route-adjacent (including the open inner lobes),
	# rather than remaining below the entire racing plane.
	SkylineFeatures.populate(parent,route)
	var base:=MeshInstance3D.new()
	base.name="NeonCityDepthFloor"
	var slab:=BoxMesh.new()
	slab.size=Vector3(480,1.0,360)
	base.mesh=slab
	base.position=Vector3(0,SkylineFeatures.BASE_Y-1.0,0)
	base.material_override=_mat("162735")
	base.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(base)
	parent.set_meta("instanced_buildings",
		int(parent.get_meta("midrise_towers",0))+
		int(parent.get_meta("hero_3d_towers",0)))

static func _surfaces(parent: Node3D, route: PackedVector3Array) -> void:
	# The deck is a series of isolated, camera-readable platforms. The
	# anti-gravity lane has no physical floor elsewhere; route-relative hover
	# support still comes from the existing tested racer, NOT collision meshes.
	var deck:=_st()
	var rail:=_st()
	var under:=_st()
	var deck_segments: int=0
	for i in range(route.size()):
		var p: Vector3=route[i]
		var q: Vector3=route[(i+1)%route.size()]
		var delta: Vector3=q-p
		var forward:=Vector3(delta.x,0.0,delta.z).normalized()
		var next_delta: Vector3=route[(i+2)%route.size()]-q
		var next_forward:=Vector3(next_delta.x,0.0,next_delta.z).normalized()
		var right:=Vector3(forward.z,0.0,-forward.x)
		var right_next:=Vector3(next_forward.z,0.0,-next_forward.x)
		var w: float=7.8
		if has_deck(i) and not (i>=44 and i<52):
			var a: Vector3=p-right*w
			var b: Vector3=q-right_next*w
			var c: Vector3=q+right_next*w
			var d: Vector3=p+right*w
			var tint: Color=Color("253542") if i%5 else Color("344754")
			# Four broad vertex colors, no texture fetches.
			_quad(deck,a,b,c,d,tint)
			var depth: float=0.65 if i<33 or i>=181 else 1.0
			var low_a: Vector3=a+Vector3.DOWN*depth
			var low_b: Vector3=b+Vector3.DOWN*depth
			var low_c: Vector3=c+Vector3.DOWN*depth
			var low_d: Vector3=d+Vector3.DOWN*depth
			_quad(under,a,low_a,low_b,b,Color("101f2d"))
			_quad(under,d,c,low_c,low_d,Color("101f2d"))
			deck_segments+=1
		# Paired slim light trails give the racer a readable route in open
		# air without representing a road or costing a transparent layer.
		if i>=44 and i<52:
			continue
		for sign in [-1.0,1.0]:
			var edge: Vector3=p+right*sign*8.55+Vector3.UP*0.07
			var end: Vector3=q+right_next*sign*8.55+Vector3.UP*0.07
			var inset: Vector3=p+right*sign*8.34+Vector3.UP*0.07
			var inset_end: Vector3=q+right_next*sign*8.34+Vector3.UP*0.07
			var color: Color=Color("5ce2df") if i<96 else Color("fdaf78")
			_quad(rail,edge,end,inset_end,inset,color)
	_mesh(parent,"NeonAnchorDeck",deck,_vertex_mat())
	_mesh(parent,"NeonAnchorUndersides",under,_vertex_mat())
	_mesh(parent,"NeonSplineLightTrails",rail,_vertex_mat(true))
	parent.set_meta("physical_visual_deck_segments",deck_segments)

static func _archway(parent: Node3D, tool: SurfaceTool, route: PackedVector3Array, index: int) -> void:
	var p: Vector3=route[index]
	var to: Vector3=route[(index+2)%route.size()]-p
	var f:=Vector3(to.x,0,to.z).normalized()
	var right:=Vector3(f.z,0,-f.x)
	# Open upper-half navigation hoop: two-sided unlit strips, not collision.
	for k in range(20):
		var a: float=PI*float(k)/20.0
		var b: float=PI*float(k+1)/20.0
		var o0: Vector3=p+right*cos(a)*11.5+Vector3.UP*(1.0+8.8*sin(a))
		var o1: Vector3=p+right*cos(b)*11.5+Vector3.UP*(1.0+8.8*sin(b))
		var i0: Vector3=p+right*cos(a)*11.1+Vector3.UP*(1.0+8.45*sin(a))
		var i1: Vector3=p+right*cos(b)*11.1+Vector3.UP*(1.0+8.45*sin(b))
		var color: Color=Color("61e7f1") if index<96 else Color("ffa66c")
		_quad(tool,o0,o1,i1,i0,color)

static func _landmarks(parent: Node3D, route: PackedVector3Array) -> void:
	var gates:=_st()
	for index in AIR_GATE_INDICES:
		_archway(parent,gates,route,index)
	_mesh(parent,"NeonDirectionArches",gates,_vertex_mat(true))
	var dark: StandardMaterial3D=_mat("1b2835")
	var alloy: StandardMaterial3D=_mat("536879")
	var cyan: StandardMaterial3D=_mat("52c9d6",true)
	var amber: StandardMaterial3D=_mat("efa86a",true)
	var batches: Dictionary={}
	# Four monumental visual anchors. Buildings and gantries are positioned
	# relative to the race centerline, but their central openings stay clear.
	for i in [12,74,110,169]:
		var p: Vector3=route[i]
		var direction: Vector3=route[(i+1)%route.size()]-p
		var f:=Vector3(direction.x,0,direction.z).normalized()
		var side:=Vector3(f.z,0,-f.x)
		var yaw: float=atan2(f.x,f.z)
		var dist: float=16.5
		for sign in [-1.0,1.0]:
			var foot: Vector3=p+side*sign*dist
			_box(batches,foot+Vector3.DOWN*11.5,Vector3(1.6,22.0,1.6),alloy,yaw)
			_box(batches,foot+Vector3.UP*2.5,Vector3(2.3,0.5,2.3),cyan if i<96 else amber,yaw)
		_box(batches,p+Vector3.UP*12.0,Vector3(34.0,0.85,1.8),dark,yaw)
		_box(batches,p+Vector3.UP*11.65,Vector3(32.0,0.15,1.92),cyan if i<96 else amber,yaw)
	# Launch and landing markers; the gap remains a REAL ballistic leap.
	for i in [34,57]:
		var p: Vector3=route[i]
		var dir: Vector3=route[(i+1)%route.size()]-p
		var f:=Vector3(dir.x,0,dir.z).normalized()
		var angle: float=atan2(f.x,f.z)
		var side:=Vector3(f.z,0,-f.x)
		for sign in [-1.0,1.0]:
			_box(batches,p+side*sign*9.8+Vector3.UP*3.0,
				Vector3(0.45,6.0,0.6),alloy,angle)
		_box(batches,p+Vector3.UP*5.9,Vector3(20.1,0.45,0.8),
			amber if i==34 else cyan,angle)
	# Start line is an actual platform and visible at high speed.
	var start: Vector3=route[0]
	var first: Vector3=route[1]-start
	var f0:=Vector3(first.x,0,first.z).normalized()
	var side0:=Vector3(f0.z,0,-f0.x)
	var ang: float=atan2(f0.x,f0.z)
	for sign in [-1.0,1.0]:
		_box(batches,start+side0*sign*9.4+Vector3.UP*3.25,
			Vector3(0.75,6.5,0.85),alloy,ang)
	_box(batches,start+Vector3.UP*6.3,Vector3(20.1,0.7,1.1),amber,ang)
	for stripe in range(10):
		var along: float=(float(stripe)-4.5)*1.6
		_box(batches,start+side0*along+Vector3.UP*0.12,
			Vector3(1.2,0.07,1.5),cyan if stripe%2 else amber,ang)
	_flush_boxes(parent,batches)
	var sign:=Label3D.new()
	sign.name="NeonCrossRebuildStart"
	sign.text="NEON CROSS / SKYLINE RACE"
	sign.font_size=62
	sign.pixel_size=0.0075
	sign.position=start+Vector3.UP*5.2
	sign.rotation.y=ang
	parent.add_child(sign)

static func populate(owner: Node3D, route: PackedVector3Array) -> void:
	assert(route.size()==192)
	var parent:=Node3D.new()
	parent.name="NeonCrossRebuild"
	owner.add_child(parent)
	_surfaces(parent,route)
	_skyline(parent,route)
	_landmarks(parent,route)
	parent.set_meta("open_air_segments",192-int(parent.get_meta("physical_visual_deck_segments")))
	parent.set_meta("geometry_contract","route-facing 3d skyline in lobes and gaps; spatial midrise instances; skyline cylinders; decorative no collision")
