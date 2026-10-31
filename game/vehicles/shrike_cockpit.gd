extends Node3D

# Shrike-specific integrated dashboard. Every dimension uses Godot craft space
# (Y up, +Z towards the nose), never Kestrel's old Blender-rotated cockpit frame.
# All instruments are below the Shrike glazing and behind its windshield.
func finish(hex_color: String, metal: float = 0.0) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = Color(hex_color)
	material.metallic = metal
	material.roughness = .57
	return material

func part(parent: Node3D, name_text: String, point: Vector3, size: Vector3, material: Material) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	node.name = name_text
	var shape := BoxMesh.new()
	shape.size = size
	node.mesh = shape
	node.position = point
	node.material_override = material
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(node)
	return node

func build() -> void:
	name = "ShrikeCockpitInstruments"
	var dark := finish("18232c", .18)
	var panel_dark := finish("263640", .12)
	var trim := finish("bc5b20", .5)
	var teal := finish("4cd1e3")
	teal.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED

	# The old inherited display was around (0, 1.43, 1.62), forward
	# of the windshield. This recessed assembly is within the real cockpit:
	# the bonnet starts forward of it, and the canopy surrounds it.
	part(self, "MoldedDashBridge", Vector3(0, 1.01, 1.02), Vector3(1.22, .16, .37), dark)
	part(self, "InstrumentRecess", Vector3(0, 1.095, .97), Vector3(.72, .20, .095), panel_dark)
	var display := MeshInstance3D.new()
	display.name = "FlightDisplay"
	var glass_panel := QuadMesh.new()
	glass_panel.size = Vector2(.62, .16)
	display.mesh = glass_panel
	display.position = Vector3(0, 1.105, .905)
	display.rotation = Vector3(-.24, PI, 0)
	display.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var screen := StandardMaterial3D.new()
	screen.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	screen.albedo_texture = load("res://assets/cockpit-instruments.svg")
	screen.cull_mode = BaseMaterial3D.CULL_DISABLED
	display.material_override = screen
	add_child(display)

	# Subtle flush console illumination. No tall external HUD panels.
	for side in [-1.0, 1.0]:
		part(self, "ShrikeConsoleRail", Vector3(side * .61, .97, .32),
			Vector3(.11, .105, 1.04), dark)
		part(self, "ConsoleLight", Vector3(side * .57, 1.024, .44),
			Vector3(.014, .007, .56), teal)
		part(self, "DisplayBezelAccent", Vector3(side * .38, 1.10, .905),
			Vector3(.017, .16, .018), trim)

	# The animated yoke still receives a YokeDetail node. The details stay
	# physically at the mounted yoke in craft space when reparented by feedback.
	var yoke_detail := Node3D.new()
	yoke_detail.name = "YokeDetail"
	add_child(yoke_detail)
	for side in [-1.0, 1.0]:
		part(yoke_detail, "YokeGripTrim", Vector3(side * .19, 1.24, .88),
			Vector3(.057, .035, .045), trim)

	# Guardrails ensure future refactors do not accidentally put a screen
	# outside the canopy or in front of its windscreen again.
	assert(display.position.z < 1.2 and display.position.z > .50)
	assert(display.position.y < 1.24 and display.position.y > .80)
	print("SCENEFORGE_SHRIKE_HUD_IN_COCKPIT_OK")
