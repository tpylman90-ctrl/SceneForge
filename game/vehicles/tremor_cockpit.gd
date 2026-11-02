extends Node3D

# Tremor's cockpit is deep in its armored cabin, never inherited from Kestrel.
# Godot local axes: X sides, Y up, +Z forward.
func mat(color: String, metal: float = 0.0, unshaded: bool = false) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color=Color(color)
	m.metallic=metal
	m.roughness=.46
	if unshaded:m.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
	return m

func part(root: Node3D, label: String, pos: Vector3, size: Vector3, material: Material) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	node.name=label
	var shape := BoxMesh.new()
	shape.size=size
	node.mesh=shape
	node.position=pos
	node.material_override=material
	node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(node)
	return node

func build() -> void:
	name="TremorCockpitInstruments"
	var dark := mat("151a21",.16)
	var steel := mat("58616e",.62)
	var red := mat("933f4a",.26)
	var cyan := mat("67d8ec",0.0,true)
	# Rugged floating-looking panels were the problem in Shrike; this dashboard
	# is seated below the windshield and physically bracketed by the sill.
	part(self,"IntegratedDashSupport",Vector3(0,1.35,.42),Vector3(1.29,.18,.38),dark)
	part(self,"RecessedInstrumentBox",Vector3(0,1.47,.39),Vector3(.79,.18,.075),steel)
	var screen := MeshInstance3D.new()
	screen.name="FlightDisplay"
	var quad := QuadMesh.new()
	quad.size=Vector2(.68,.15)
	screen.mesh=quad
	screen.position=Vector3(0,1.495,.345)
	screen.rotation=Vector3(-.19,PI,0)
	var instrument_mat: StandardMaterial3D=mat("ffffff",0.0,true)
	instrument_mat.albedo_texture=load("res://assets/cockpit-instruments.svg")
	instrument_mat.cull_mode=BaseMaterial3D.CULL_DISABLED
	screen.material_override=instrument_mat
	screen.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(screen)
	for side in [-1.0,1.0]:
		part(self,"ShieldedSideConsole",Vector3(side*.68,1.29,-.14),
			Vector3(.14,.15,1.0),dark)
		part(self,"SafetyAccentRail",Vector3(side*.61,1.38,.17),
			Vector3(.035,.02,.67),red)
		part(self,"PanelStatusLight",Vector3(side*.40,1.56,.38),
			Vector3(.06,.017,.036),cyan)
	var controls := Node3D.new()
	controls.name="YokeDetail"
	add_child(controls)
	for side in [-1.0,1.0]:
		part(controls,"TremorYokeSafetyTrim",Vector3(side*.23,1.45,.44),
			Vector3(.07,.05,.07),red)
	assert(screen.position.y<1.75 and screen.position.z<.8)
	print("SCENEFORGE_TREMOR_COCKPIT_MOUNT_OK")
