extends Node3D

# Native craft coordinates: fitted inside the tub, independent of Kestrel's stance.
func finish(color: String, metal: float=0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color=Color(color)
	m.metallic=metal
	m.roughness=.45
	return m

func part(parent: Node3D, point: Vector3, size: Vector3, material: Material) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size=size
	node.mesh=box
	node.position=point
	node.material_override=material
	parent.add_child(node)
	return node

# Continuous rounded fascia, sweeping into both cockpit side consoles.
func dashboard(material: Material) -> void:
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	var points: Array[Vector3]=[]
	for i in range(25):
		var x := -.63+1.26*float(i)/24.0
		var sweep := absf(x)/.63
		for j in range(16):
			var angle := TAU*float(j)/16.0
			points.append(Vector3(x,1.35+.025*sweep+.095*sin(angle),1.08-.27*pow(sweep,2)+.14*cos(angle)))
	for i in range(24):
		for j in range(16):
			var a := i*16+j
			var b := i*16+(j+1)%16
			var c := (i+1)*16+j
			var d := (i+1)*16+(j+1)%16
			for index in [a,c,b,b,c,d]:surface.add_vertex(points[index])
	surface.generate_normals()
	var fascia := MeshInstance3D.new()
	fascia.name="SculptedDashboard"
	fascia.mesh=surface.commit()
	fascia.material_override=material
	add_child(fascia)

func build() -> void:
	name="PyldriverCockpitInstruments"
	var dark := finish("15222a",.4)
	var brass := finish("a77a30",.65)
	dashboard(dark)
	var yoke_detail := Node3D.new()
	yoke_detail.name="YokeDetail"
	add_child(yoke_detail)
	for side in [-1.0,1.0]:
		part(yoke_detail,Vector3(side*.24,1.32,1.07),Vector3(.065,.025,.055),brass)
	var hologram := MeshInstance3D.new()
	hologram.name="HolographicDisplay"
	var holo_quad := QuadMesh.new()
	holo_quad.size=Vector2(.28,.09)
	hologram.mesh=holo_quad
	hologram.position=Vector3(.23,1.62,.44)
	hologram.rotation.y=PI
	hologram.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(hologram)
	for side in [-1.0,1.0]:
		part(self,Vector3(.23+side*.10,1.37,.58),Vector3(.09,.05,.12),dark)
		var lens := finish("50d9e8")
		lens.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
		part(self,Vector3(.23+side*.10,1.40,.58),Vector3(.045,.008,.055),lens)
	# Match the additional rear-up body rake without moving the display out of the tub.
	transform=Transform3D(Basis(Vector3.RIGHT,Vector3.UP,Vector3(0,-.05,1)),Vector3(0,.171,0))
