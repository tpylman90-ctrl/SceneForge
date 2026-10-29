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

func build() -> void:
	name="PyldriverCockpitInstruments"
	var dark := finish("15222a",.4)
	var brass := finish("a77a30",.65)
	var frame := Transform3D(Basis.from_euler(Vector3(-.60,PI,0)),Vector3(0,1.43,1.00))
	var bezel := part(self,Vector3.ZERO,Vector3(.79,.31,.05),dark)
	bezel.name="InstrumentBinnacle"
	bezel.transform=frame
	var display := MeshInstance3D.new()
	display.name="FlightDisplay"
	var quad := QuadMesh.new()
	quad.size=Vector2(.70,.24)
	display.mesh=quad
	display.transform=frame*Transform3D(Basis.IDENTITY,Vector3(0,0,.027))
	var screen := StandardMaterial3D.new()
	screen.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
	display.material_override=screen
	display.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(display)
	for side in [-1.0,1.0]:
		part(self,Vector3(side*.28,1.29,1.04),Vector3(.055,.27,.08),dark)
		var edge := part(self,Vector3.ZERO,Vector3(.025,.29,.065),brass)
		edge.transform=frame*Transform3D(Basis.IDENTITY,Vector3(side*.385,0,0))
	part(self,Vector3(0,1.15,1.04),Vector3(1.0,.08,.15),dark)
	var yoke_detail := Node3D.new()
	yoke_detail.name="YokeDetail"
	add_child(yoke_detail)
	for side in [-1.0,1.0]:
		part(yoke_detail,Vector3(side*.24,1.32,1.07),Vector3(.065,.025,.055),brass)
	var hologram := MeshInstance3D.new()
	hologram.name="HolographicDisplay"
	var holo_quad := QuadMesh.new()
	holo_quad.size=Vector2(.48,.16)
	hologram.mesh=holo_quad
	hologram.position=Vector3(0,1.65,.48)
	hologram.rotation.y=PI
	hologram.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(hologram)
	for side in [-1.0,1.0]:
		part(self,Vector3(side*.20,1.37,.58),Vector3(.09,.05,.12),dark)
		var lens := finish("50d9e8")
		lens.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
		part(self,Vector3(side*.20,1.40,.58),Vector3(.045,.008,.055),lens)
	# Match the additional rear-up body rake without moving the display out of the tub.
	transform=Transform3D(Basis(Vector3.RIGHT,Vector3.UP,Vector3(0,-.05,1)),Vector3(0,.171,0))
