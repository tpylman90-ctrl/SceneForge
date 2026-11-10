extends RefCounted

# Skyfall's actual three-dimensional destination. This scenery is NOT a
# roadway or invisible physics rail: it lies below and beside the aerial line.
# Chunked opaque geometry + low-cost MultiMeshes for Godot Mobile/Vulkan.
const START := 127
const END := 185
const GATES := [137,150,163,177]
const LATERALS := [-420.0,-315.0,-240.0,-184.0,-148.0,-114.0,-87.0,-68.0,-48.0,-24.0,0.0,24.0,48.0,68.0,87.0,114.0,148.0,184.0,240.0,315.0,420.0]

static func tangent(path: PackedVector3Array, i: int) -> Vector3:
	var p: Vector3=path[maxi(0,i-1)]
	var q: Vector3=path[mini(path.size()-1,i+1)]
	return Vector3(q.x-p.x,0.0,q.z-p.z).normalized()

static func right(path: PackedVector3Array, i: int) -> Vector3:
	var direction: Vector3=tangent(path,i)
	return Vector3(direction.z,0,-direction.x)

static func flight_gate_center(path: PackedVector3Array, ordinal: int) -> Vector3:
	var index: int=GATES[ordinal]
	var shift: float=18.0 if ordinal%2==0 else -18.0
	return path[index]+right(path,index)*shift+Vector3.UP*(2.0 if ordinal%2==0 else -3.0)

static func _noise() -> FastNoiseLite:
	var noise := FastNoiseLite.new()
	noise.seed=23821
	noise.noise_type=FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	noise.frequency=0.012
	noise.fractal_type=FastNoiseLite.FRACTAL_FBM
	noise.fractal_octaves=3
	return noise

static func _valley_vertex(path: PackedVector3Array, index: int, lateral: float, noise: FastNoiseLite) -> Vector3:
	var p: Vector3=path[index]
	var pos: Vector3=p+right(path,index)*lateral
	var progress: float=clampf(float(index-START)/float(END-START),0.0,1.0)
	var depth: float=lerpf(108.0,33.0,progress)
	# First the ridge falls away dramatically. Near the finish the terrain
	# climbs back up to meet the low road.
	var reveal: float=smoothstep(0.0,0.15,progress)
	var landing: float=1.0-smoothstep(0.86,1.0,progress)
	depth=lerpf(7.0,depth,reveal*landing)
	var distance: float=absf(lateral)
	var rise: float=smoothstep(38.0,150.0,distance)*(depth+19.0)
	var outer_drop: float=smoothstep(172.0,420.0,distance)*102.0
	var breakup: float=noise.get_noise_2d(pos.x,pos.z)*lerpf(2.0,19.0,clampf(distance/250.0,0.0,1.0))
	var erosion: float=sin(pos.x*0.028+pos.z*0.022)*4.0*clampf(distance/100.0,0.0,1.0)
	pos.y=p.y-depth+rise-outer_drop+breakup+erosion
	return pos

static func _valley_color(p: Vector3, lateral: float, noise: FastNoiseLite) -> Color:
	var n: float=noise.get_noise_2d(p.x+240.0,p.z-500.0)
	var ridge: float=smoothstep(44.0,180.0,absf(lateral))
	var rock: Color=Color("7b796c").lerp(Color("4b5350"),clampf(ridge*0.55+n*0.25,0,1))
	var grass: Color=Color("395b48").lerp(Color("688166"),clampf(0.45+n,0,1))
	return grass.lerp(rock,clampf(ridge*0.78+absf(n)*0.20,0,1))

static func _triangle(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, ca: Color, cb: Color, cc: Color) -> void:
	var normal: Vector3=(b-a).cross(c-a).normalized()
	if normal.y<0.0:
		normal=-normal
	st.set_color(ca)
	st.set_normal(normal)
	st.add_vertex(a)
	st.set_color(cb)
	st.set_normal(normal)
	st.add_vertex(b)
	st.set_color(cc)
	st.set_normal(normal)
	st.add_vertex(c)

static func _quad(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3, ca: Color, cb: Color, cc: Color, cd: Color) -> void:
	_triangle(st,a,b,c,ca,cb,cc)
	_triangle(st,a,c,d,ca,cc,cd)

static func _material(color: Color, vertex_colors: bool = false, unshaded: bool = false) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color=color
	m.roughness=0.93
	m.vertex_color_use_as_albedo=vertex_colors
	m.cull_mode=BaseMaterial3D.CULL_DISABLED
	if unshaded:
		m.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
	return m

static func _multimesh(root: Node3D, mesh: Mesh, mat: Material, transforms: Array[Transform3D], label: String) -> void:
	var multi := MultiMesh.new()
	multi.transform_format=MultiMesh.TRANSFORM_3D
	multi.mesh=mesh
	multi.instance_count=transforms.size()
	for index in range(transforms.size()):
		multi.set_instance_transform(index,transforms[index])
	var node := MultiMeshInstance3D.new()
	node.name=label
	node.multimesh=multi
	node.material_override=mat
	node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(node)

static func populate(root: Node3D, path: PackedVector3Array) -> void:
	var noise: FastNoiseLite=_noise()
	var terrain_material := _material(Color.WHITE,true)
	# Three chunks, instead of one immense strip, permit viewport frustum
	# culling. No extra transparent layers or expensive real-time lights.
	for chunk in range(3):
		var first: int=START+int(float(END-START)*float(chunk)/3.0)
		var last: int=START+int(float(END-START)*float(chunk+1)/3.0)
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		for i in range(first,last):
			for band in range(LATERALS.size()-1):
				var left: float=LATERALS[band]
				var other: float=LATERALS[band+1]
				var a: Vector3=_valley_vertex(path,i,left,noise)
				var b: Vector3=_valley_vertex(path,i,other,noise)
				var c: Vector3=_valley_vertex(path,i+1,other,noise)
				var d: Vector3=_valley_vertex(path,i+1,left,noise)
				_quad(st,a,b,c,d,_valley_color(a,left,noise),_valley_color(b,other,noise),
					_valley_color(c,other,noise),_valley_color(d,left,noise))
		var node := MeshInstance3D.new()
		node.name="SkyfallFlightValley_%d"%chunk
		node.mesh=st.commit()
		node.material_override=terrain_material
		node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		root.add_child(node)

	# Distinctive cliff needles bracket the route rather than being scattered
	# randomly in empty space. The player visibly passes close to real forms.
	var needle_mesh := CylinderMesh.new()
	needle_mesh.top_radius=3.2
	needle_mesh.bottom_radius=15.0
	needle_mesh.height=88.0
	needle_mesh.radial_segments=9
	var needle_caps := CylinderMesh.new()
	needle_caps.top_radius=0.4
	needle_caps.bottom_radius=7.8
	needle_caps.height=36.0
	needle_caps.radial_segments=9
	var needles: Array[Transform3D]=[]
	var caps: Array[Transform3D]=[]
	for j in range(9):
		var index: int=130+j*6
		if index>=END:
			break
		for side in [-1.0,1.0]:
			var lateral: float=side*(125.0+float((j*17)%45))
			var base: Vector3=_valley_vertex(path,index,lateral,noise)
			var scale: float=0.70+0.13*float((j+int(side+1.0))%4)
			var angle: float=float(j)*1.17+side*0.31
			var basis: Basis=Basis(Vector3.UP,angle).scaled(Vector3(scale,scale,scale))
			needles.append(Transform3D(basis,base+Vector3.UP*44.0*scale))
			caps.append(Transform3D(basis,base+Vector3.UP*102.0*scale))
	_multimesh(root,needle_mesh,_material(Color("66665e")),needles,"SkyfallFlightRockNeedles")
	_multimesh(root,needle_caps,_material(Color("939083")),caps,"SkyfallFlightNeedleCrowns")

	# Forest-covered lower shoulders are visible from high above. Shared
	# meshes make hundreds of trees only two additional draw groups.
	var canopy := CylinderMesh.new()
	canopy.top_radius=0.45
	canopy.bottom_radius=3.7
	canopy.height=10.0
	canopy.radial_segments=7
	var trunks := CylinderMesh.new()
	trunks.top_radius=0.42
	trunks.bottom_radius=0.68
	trunks.height=5.0
	trunks.radial_segments=7
	var leaves: Array[Transform3D]=[]
	var stems: Array[Transform3D]=[]
	for index in range(START+4,END-2,3):
		for lateral in [-304.0,-225.0,-178.0,178.0,225.0,304.0]:
			var p: Vector3=_valley_vertex(path,index,lateral+noise.get_noise_2d(float(index)*42.0,lateral)*23.0,noise)
			var scale: float=0.7+0.55*absf(noise.get_noise_2d(p.x+100.0,p.z+50.0))
			var turn: float=float(index)*0.73+lateral*0.019
			var basis: Basis=Basis(Vector3.UP,turn).scaled(Vector3.ONE*scale)
			leaves.append(Transform3D(basis,p+Vector3.UP*8.0*scale))
			stems.append(Transform3D(basis,p+Vector3.UP*2.6*scale))
	_multimesh(root,canopy,_material(Color("345748")),leaves,"SkyfallFlightForestCrowns")
	_multimesh(root,trunks,_material(Color("50483c")),stems,"SkyfallFlightForestTrunks")

	# Wide aerial rings show a 3D flight line without adding a fake road.
	# Offset centers encourage piloting around the scenery; route center
	# remains within every beginner-friendly gate.
	var markers := SurfaceTool.new()
	markers.begin(Mesh.PRIMITIVE_TRIANGLES)
	for gate in range(GATES.size()):
		var center: Vector3=flight_gate_center(path,gate)
		var sideways: Vector3=right(path,GATES[gate])
		for segment in range(28):
			var angle0: float=TAU*float(segment)/28.0
			var angle1: float=TAU*float(segment+1)/28.0
			var outer0: Vector3=center+sideways*cos(angle0)*43.0+Vector3.UP*sin(angle0)*43.0
			var inner0: Vector3=center+sideways*cos(angle0)*41.1+Vector3.UP*sin(angle0)*41.1
			var inner1: Vector3=center+sideways*cos(angle1)*41.1+Vector3.UP*sin(angle1)*41.1
			var outer1: Vector3=center+sideways*cos(angle1)*43.0+Vector3.UP*sin(angle1)*43.0
			var tint: Color=Color("48e3ef") if gate%2==0 else Color("f6ae62")
			_quad(markers,outer0,inner0,inner1,outer1,tint,tint,tint,tint)
	var gates := MeshInstance3D.new()
	gates.name="SkyfallFlightAerialGates"
	gates.mesh=markers.commit()
	gates.material_override=_material(Color.WHITE,true,true)
	gates.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(gates)
