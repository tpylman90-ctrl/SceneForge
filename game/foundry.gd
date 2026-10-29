extends Node3D

const Fleet = preload("res://vehicles/fleet_catalog.gd")
var selected_craft := 0
var chassis: Resource
var lot_craft: Node3D
var lot_feedback: Node3D
var craft_title: Label

var body: CharacterBody3D
var camera: Camera3D
var yaw := 0.58
var pitch := -0.1
var move_touch := -1
var look_touch := -1
var stick_origin := Vector2.ZERO
var stick := Vector2.ZERO
var stick_ring: Control
var fps_label: Label
var elapsed := 0.0
var orbit_mode := true
var seat_mode := false
var seat_look_yaw := 0.0
var seat_look_pitch := -0.10472
var glass_surfaces: Array[Dictionary] = []
var cockpit_locked := false
var orbit_angle := 0.58
var orbit_elevation := 0.20
var orbit_radius := 5.7
var touch_points: Dictionary = {}
var driver_door: Node3D
var door_open := false
var door_busy := false
var door_button: Button
var mode_button: Button
var help_label: Label
var stats_panel: Control
var last_door_tween: Tween
var saved_orbit := false
var sun: DirectionalLight3D
var quality_button: Button
var compare_button: Button
var result_label: Label
var balanced := true
var comparing := false
var phase := 0
var phase_frames := 0
var last_tick := 0
var samples: Array[float] = []
var results: Array[Dictionary] = []
var saved_position := Vector3.ZERO
var saved_yaw := 0.0
var saved_pitch := 0.0

func _ready() -> void:
	selected_craft=clampi(int(get_tree().get_meta("sceneforge_craft",0)),0,Fleet.IDS.size()-1)
	for index in range(Fleet.IDS.size()):
		if "--craft-%d"%index in OS.get_cmdline_user_args():selected_craft=index
	get_tree().set_meta("sceneforge_craft",selected_craft)
	chassis=Fleet.definition(selected_craft)
	var scenery: Node3D = load("res://assets/neon_foundry.glb").instantiate()
	add_child(scenery)
	# The scenery GLB also contains the original Kestrel. Remove its complete
	# rig before loading another craft, keeping the workshop/environment intact.
	if selected_craft>0:
		for child in scenery.get_children():
			if str(child.name).begins_with("Kestrel_") or str(child.name).begins_with("TailVector") or child.name=="DriverDoor":
				scenery.remove_child(child)
				child.free()
	for node in scenery.find_children("*", "MeshInstance3D", true, false):
		for surface in range(node.mesh.get_surface_count()):
			var material: Material = node.get_active_material(surface)
			if material is StandardMaterial3D:
				material.vertex_color_use_as_albedo = true

		if "vehicle_glass" in node.name:
			for surface in range(node.mesh.get_surface_count()):
				var original: StandardMaterial3D = node.get_active_material(surface)
				var inside: StandardMaterial3D = original.duplicate()
				inside.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
				inside.albedo_color = Color(0.1, 0.18, 0.22, 0.18)
				inside.metallic = 0.0
				inside.roughness = 0.18
				glass_surfaces.append({"mesh": node, "surface": surface, "outside": original, "inside": inside})
		if "asphalt" in node.name or "grime" in node.name or "skyline" in node.name:
			node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

	if selected_craft==0:
		var door_visual: Node3D = scenery.find_child("DriverDoor", true, false)
		assert(door_visual != null, "Missing rigged DriverDoor")
		var door_body := AnimatableBody3D.new()
		door_body.name = "DriverDoorMechanism"
		add_child(door_body)
		door_visual.reparent(door_body, true)
		var door_shape := CollisionShape3D.new()
		var door_box := BoxShape3D.new()
		door_box.size = Vector3(0.16, 0.65, 2.2)
		door_shape.shape = door_box
		door_shape.position = Vector3(1.16, 1.3, 0.65)
		door_body.add_child(door_shape)
		driver_door = door_body

		build_cockpit_details()

	else:
		glass_surfaces.clear()
		lot_craft=Node3D.new()
		lot_craft.name="FoundryCraft"
		lot_craft.position=Vector3(0,0,.8)
		add_child(lot_craft)
		# Runtime load avoids a preload cycle with the legacy cockpit factory.
		lot_feedback=load("res://vehicles/kestrel_feedback.gd").new()
		lot_craft.add_child(lot_feedback)
		lot_feedback.configure(chassis)
		lot_feedback.update_feedback(1.0,0,0,0,0,0,false)

	var environment := WorldEnvironment.new()
	var settings := Environment.new()
	var sky := Sky.new()
	var atmosphere := PanoramaSkyMaterial.new()
	atmosphere.panorama=load("res://assets/twilight_sky.jpg")
	sky.sky_material = atmosphere
	settings.sky = sky
	settings.background_mode = Environment.BG_SKY
	settings.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	settings.ambient_light_color = Color("8b9ba8")
	settings.ambient_light_energy = 0.72
	settings.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	settings.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	environment.environment = settings
	add_child(environment)
	sun = DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-35, -25, 0)
	sun.light_color = Color("8cadcf")
	sun.light_energy = 0.52
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 24.0
	sun.shadow_blur = 1.3
	sun.shadow_bias = 0.15
	sun.shadow_normal_bias = 1.5
	add_child(sun)
	var reflections := ReflectionProbe.new()
	reflections.position = Vector3(0, 2.5, 0)
	reflections.size = Vector3(27, 11, 27)
	reflections.origin_offset = Vector3(0, 0, 0)
	reflections.box_projection = true
	reflections.update_mode = ReflectionProbe.UPDATE_ONCE
	add_child(reflections)
	light(Vector3(2.5, 3.2, 1.0), Color("d5e8ff"), 2.2, 6.0)
	light(Vector3(0, 3.3, -5.8), Color("ff9b4d"), 3.5, 6.0)
	light(Vector3(0, 3.5, -2.0), Color("ffc175"), 2.0, 5.5)
	light(Vector3(-5.4, 4.0, 6), Color("56dfff"), 2.3, 7.0)
	light(Vector3(-5.4, 4.0, 0), Color("56dfff"), 1.5, 5.0)
	# Collision deliberately follows the open bay rather than enclosing the doorway.
	for side in [-1.0, 1.0]:
		collider(Vector3(side * 7.8, 4.0, 0), Vector3(0.3, 8, 24))
	collider(Vector3(0, 1.1, 11.35), Vector3(15, 2.2, 0.15))
	collider(Vector3(0, 1.0, 0.8), Vector3(3.3, 2.0, 6.5))
	collider(Vector3(0, -0.15, 0), Vector3(28, 0.3, 24))
	collider(Vector3(-4.5, 2.5, -4), Vector3(5, 5, 1))
	collider(Vector3(4.5, 2.5, -4), Vector3(5, 5, 1))
	collider(Vector3(0, 2, -8.5), Vector3(6, 4, 0.3))
	for x in [-2.7, 2.7]:
		collider(Vector3(x, 2, -6), Vector3(0.3, 4, 5))
	collider(Vector3(-4.05, 0.3, -1.75), Vector3(1.05, 0.6, 0.65))
	collider(Vector3(1.85, 0.36, -6.35), Vector3(0.52, 0.72, 0.52))
	collider(Vector3(0, 0.9, -5.5), Vector3(2.0, 1.8, 1.1))
	collider(Vector3(0, 0.6, -7.5), Vector3(3.4, 1.2, 0.9))
	for p in [Vector3(-3, 0.42, -1.5), Vector3(3.8, 0.42, -0.7), Vector3(5.2, 0.42, -1.2)]:
		collider(p, Vector3(0.8, 0.84, 0.8))
	body = CharacterBody3D.new()
	body.position = Vector3(3.2, 0.1, 5.7)
	var shape := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.28
	capsule.height = 1.7
	shape.shape = capsule
	shape.position.y = 0.85
	body.add_child(shape)
	camera = Camera3D.new()
	camera.position.y = 1.65
	camera.fov = 70
	camera.current = true
	camera.far = 75
	body.add_child(camera)
	add_child(body)

	var hum: AudioStreamWAV = load("res://assets/kestrel_hum.wav")
	hum.loop_mode = AudioStreamWAV.LOOP_FORWARD
	hum.loop_end = int(hum.get_length() * hum.mix_rate)
	var sound := AudioStreamPlayer3D.new()
	sound.name = "KestrelHum"
	sound.stream = hum
	sound.position = Vector3(0, 0.8, 0.8)
	sound.volume_db = -25
	sound.unit_size = 4
	sound.max_distance = 18
	add_child(sound)
	if DisplayServer.get_name() != "headless":
		sound.play()
	ui()
	apply_quality(true)

	set_inspection(true)
	var args := OS.get_cmdline_user_args()
	if "--vehicle-tail" in args:
		inspection_preset("tail")
	if "--cockpit-view" in args or "--door-open" in args:
		inspection_preset("cockpit")
	if "--rear-view" in args or "--road-closeup" in args:
		set_inspection(false)
		if "--rear-view" in args:
			body.position = Vector3(0, 0.1, 5)
			yaw = PI
			pitch = 0.03
		else:
			body.position = Vector3(0, 0.1, 4.5)
			yaw = 0
			pitch = -0.8
	if "--door-open" in args:
		toggle_door()
	if "--seat-view" in args:
		inspection_preset("seat")
	if "--door-motion-smoke" in args:
		call_deferred("test_door_motion")
	if "--benchmark-smoke" in args:
		start_comparison()


# Original physical cockpit detailing; a single static instrument texture avoids
# a per-frame SubViewport or extra lights on mobile.
func cockpit_part(root: Node3D, pos: Vector3, size: Vector3, material: Material) -> MeshInstance3D:
	var part := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = size
	part.mesh = mesh
	part.material_override = material
	part.position = pos
	part.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(part)
	return part

func cockpit_material(color: Color, metallic: float = 0.0, glow: bool = false) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.metallic = metallic
	material.roughness = 0.48
	if glow:
		material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	return material

func build_cockpit_details() -> void:
	var root := Node3D.new()
	root.name = "KestrelCockpitInstruments"
	# Blender's Z-up frame, including the craft's six-degree stance.
	root.rotation.x = deg_to_rad(-84)
	# Match rotation about Blender (0, -0.8, 0), then the 0.2 m lift.
	root.position = Vector3(0, 0.28362277, 0.00438248)
	add_child(root)
	var graphite := cockpit_material(Color("15222a"), 0.5)
	var silver := cockpit_material(Color("567078"), 0.7)
	var rubber := cockpit_material(Color("10181c"))
	var amber := cockpit_material(Color("ed934d"), 0.0, true)
	var cyan := cockpit_material(Color("65ccd5"), 0.0, true)
	# Raised, recessed binnacle masks the former placeholder display.
	var bezel := cockpit_part(root, Vector3(0, -1.49, 1.31), Vector3(0.96, 0.38, 0.035), graphite)
	bezel.rotation.x = -0.45
	var display := MeshInstance3D.new()
	display.name = "FlightDisplay"
	var panel := QuadMesh.new()
	panel.size = Vector2(0.89, 0.334)
	display.mesh = panel
	var screen := StandardMaterial3D.new()
	screen.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	screen.albedo_texture = load("res://assets/cockpit-instruments.svg")
	screen.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	display.material_override = screen
	display.position = Vector3(0, -1.481, 1.332)
	display.rotation.x = -0.45
	# Pilot faces Blender -Y: turn the artwork toward the seated reader.
	display.rotate_object_local(Vector3.BACK, PI)
	display.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(display)
	var yoke_detail := Node3D.new()
	yoke_detail.name = "YokeDetail"
	root.add_child(yoke_detail)
	for side in [-1.0, 1.0]:
		# End caps and tiny instrument-retention screws.
		cockpit_part(root, Vector3(side * 0.48, -1.49, 1.30), Vector3(0.035, 0.35, 0.065), silver).rotation.x = -0.45
		# Padded side-console inserts, luminous channels and guarded switches.
		cockpit_part(root, Vector3(side * 0.57, -0.78, 1.082), Vector3(0.155, 0.72, 0.025), rubber)
		cockpit_part(root, Vector3(side * 0.475, -0.78, 1.083), Vector3(0.009, 0.64, 0.008), cyan)
		for i in range(5):
			var yy := -1.02 + i * 0.11
			cockpit_part(root, Vector3(side * 0.57, yy, 1.097), Vector3(0.07, 0.065, 0.012), graphite)
			cockpit_part(root, Vector3(side * 0.60, yy, 1.108), Vector3(0.018, 0.028, 0.008), amber if i == 0 else cyan)
		# Sculpted yoke grip collars and illuminated thumb buttons.
		cockpit_part(yoke_detail, Vector3(side * 0.21, -1.135, 1.14), Vector3(0.075, 0.07, 0.045), graphite)
		cockpit_part(yoke_detail, Vector3(side * 0.21, -1.132, 1.224), Vector3(0.023, 0.025, 0.009), cyan)
		for i in range(3):
			cockpit_part(yoke_detail, Vector3(side * 0.21, -1.133, 1.055 + i * 0.032), Vector3(0.072, 0.013, 0.009), rubber)
	# Yoke hub, inset emblem and paired thumb selectors.
	cockpit_part(yoke_detail, Vector3(0, -1.16, 1.045), Vector3(0.19, 0.075, 0.085), graphite)
	cockpit_part(yoke_detail, Vector3(0, -1.16, 1.092), Vector3(0.08, 0.042, 0.008), silver)
	cockpit_part(yoke_detail, Vector3(0, -1.16, 1.098), Vector3(0.012, 0.03, 0.005), amber)
	batch_cockpit_parts(yoke_detail)
	batch_cockpit_parts(root)


func batch_cockpit_parts(root: Node3D) -> void:
	var groups: Dictionary = {}
	for child in root.get_children():
		if child is MeshInstance3D and child.mesh is BoxMesh:
			var material: Material = child.material_override
			if not groups.has(material):
				var surface := SurfaceTool.new()
				surface.begin(Mesh.PRIMITIVE_TRIANGLES)
				groups[material] = surface
			var builder: SurfaceTool = groups[material]
			builder.append_from(child.mesh, 0, child.transform)
			root.remove_child(child)
			child.queue_free()
	for material in groups:
		var batch := MeshInstance3D.new()
		var builder: SurfaceTool = groups[material]
		batch.mesh = builder.commit()
		batch.material_override = material
		batch.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		root.add_child(batch)

func light(pos: Vector3, color: Color, energy: float, radius: float) -> void:
	var lamp := OmniLight3D.new()
	lamp.position = pos
	lamp.light_color = color
	lamp.light_energy = energy
	lamp.omni_range = radius
	lamp.omni_attenuation = 1.5
	add_child(lamp)

func collider(pos: Vector3, size: Vector3) -> void:
	var wall := StaticBody3D.new()
	wall.position = pos
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = size
	shape.shape = box
	wall.add_child(shape)
	add_child(wall)


func make_button(label: String, action: Callable, width: float = 112) -> Button:
	var button := Button.new()
	button.text = label
	button.custom_minimum_size = Vector2(width, 54)
	button.pressed.connect(action)
	return button

func ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	var title := Label.new()
	title.text = Fleet.NAMES[selected_craft]
	craft_title=title
	title.position = Vector2(26, 20)
	title.add_theme_font_size_override("font_size", 32)
	layer.add_child(title)
	var subtitle := Label.new()
	subtitle.text = "NEON FOUNDRY  /  VEHICLE INSPECTION"
	subtitle.position = Vector2(28, 64)
	subtitle.add_theme_font_size_override("font_size", 15)
	layer.add_child(subtitle)
	fps_label = Label.new()
	fps_label.position = Vector2(28, 89)
	fps_label.visible = false
	layer.add_child(fps_label)
	result_label = Label.new()
	result_label.position = Vector2(28, 112)
	result_label.add_theme_font_size_override("font_size", 17)
	layer.add_child(result_label)
	help_label = Label.new()
	help_label.position = Vector2(28, 151)
	help_label.add_theme_font_size_override("font_size", 16)
	layer.add_child(help_label)
	var row := HBoxContainer.new()
	row.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	row.position = Vector2(-565, -78)
	row.size = Vector2(1130, 54)
	row.add_theme_constant_override("separation", 10)
	layer.add_child(row)
	mode_button = make_button("WALK", func(): set_inspection(not orbit_mode))
	row.add_child(mode_button)
	row.add_child(make_button("FRONT", func(): inspection_preset("front"), 100))
	row.add_child(make_button("TAIL", func(): inspection_preset("tail"), 100))
	row.add_child(make_button("COCKPIT", func(): inspection_preset("cockpit")))
	row.add_child(make_button("SEAT", func(): inspection_preset("seat"), 100))
	door_button = make_button("OPEN DOOR" if driver_door!=null else "NO DOOR", toggle_door, 140)
	door_button.disabled=driver_door==null
	row.add_child(door_button)
	row.add_child(make_button("SOUND", func():
		var sound: AudioStreamPlayer3D = get_node("KestrelHum")
		sound.volume_db = -80 if sound.volume_db > -50 else -25, 100))
	row.add_child(make_button("TRACK", open_track, 100))
	var fleet_button := make_button("FLEET", open_fleet, 130)
	fleet_button.position=Vector2(1100,100)
	layer.add_child(fleet_button)
	row.add_child(make_button("STATS", func():
		stats_panel.visible = not stats_panel.visible
		fps_label.visible = stats_panel.visible
		result_label.visible = stats_panel.visible, 100))
	var stats := VBoxContainer.new()
	stats.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	stats.position = Vector2(-205, 24)
	stats.size = Vector2(180, 120)
	stats.visible = false
	layer.add_child(stats)
	stats_panel = stats
	quality_button = make_button("BALANCED", func(): apply_quality(not balanced), 180)
	stats.add_child(quality_button)
	compare_button = make_button("COMPARE FPS", start_comparison, 180)
	stats.add_child(compare_button)
	stick_ring = Control.new()
	stick_ring.mouse_filter = Control.MOUSE_FILTER_IGNORE
	stick_ring.draw.connect(func():
		stick_ring.draw_circle(Vector2.ZERO, 65, Color(0.2, 0.7, 0.9, 0.12))
		stick_ring.draw_arc(Vector2.ZERO, 65, 0, TAU, 48, Color(0.4, 0.8, 1, 0.45), 2)
		stick_ring.draw_circle(stick * 48, 18, Color(0.5, 0.9, 1, 0.6)))
	stick_ring.visible = false
	layer.add_child(stick_ring)

func set_inspection(enabled: bool) -> void:
	set_seat_view(false)
	orbit_mode = enabled
	inspection_mode = false
	touch_points.clear()
	stick = Vector2.ZERO
	move_touch = -1
	look_touch = -1
	stick_ring.visible = false
	body.velocity = Vector3.ZERO
	mode_button.text = "WALK" if enabled else "INSPECT"
	help_label.text = "Drag to orbit · Pinch / scroll to zoom" if enabled else "Left: move · Right: look"
	if not enabled:
		body.position = Vector3(3.2, 0.1, 5.7)
		yaw = 0.58
		pitch = -0.1
		body.rotation = Vector3(0, yaw, 0)
		camera.position = Vector3(0, 1.65, 0)
		camera.rotation = Vector3(pitch, 0, 0)

func inspection_preset(which: String) -> void:
	cancel_comparison()
	set_inspection(true)
	cockpit_locked = which == "cockpit"
	if which == "seat":
		set_seat_view(true)
	if which == "front":
		orbit_angle = 0.58
		orbit_elevation = 0.20
		orbit_radius = 5.7
	elif which == "tail":
		orbit_angle = 2.55
		orbit_elevation = 0.22
		orbit_radius = 4.5

func set_seat_view(enabled: bool) -> void:
	seat_mode = enabled
	if lot_feedback!=null:lot_feedback.set_cockpit(enabled)
	camera.fov = 78.0 if enabled else 70.0
	camera.near = 0.03 if enabled else 0.05
	for entry in glass_surfaces:
		var mesh: MeshInstance3D = entry["mesh"]
		mesh.set_surface_override_material(entry["surface"], entry["inside"] if enabled else entry["outside"])
	if enabled:
		seat_look_yaw = 0.0
		seat_look_pitch = chassis.cockpit_pitch
		help_label.text = "Driver's seat · Drag to look around · SEAT to re-center"

func update_orbit() -> void:
	if seat_mode:
		# Pilot eye position follows the rigid 6-degree nose-down vehicle stance.
		camera.global_position = lot_feedback.to_global(chassis.cockpit_eye) if lot_feedback!=null else chassis.cockpit_eye
		camera.global_rotation = Vector3(seat_look_pitch, PI + seat_look_yaw, 0)
		return
	if cockpit_locked:
		camera.global_position = Vector3(2.45, 2.65, 0.25)
		camera.look_at(Vector3(0, 1.18, 0.8))
		return
	var center := Vector3(0, 1.05, 0.8)
	var pos := center + Vector3(sin(orbit_angle) * cos(orbit_elevation), sin(orbit_elevation), cos(orbit_angle) * cos(orbit_elevation)) * orbit_radius
	pos.x = clampf(pos.x, -6.7, 6.7)
	pos.y = maxf(pos.y, 0.4)
	pos.z = clampf(pos.z, -2.6, 9.0)
	camera.global_position = pos
	camera.look_at(center)

func toggle_door() -> void:
	if driver_door==null or door_busy:
		return
	door_busy = true
	door_button.disabled = true
	door_open = not door_open
	var kick := Vector3(0.52, 0.04, 0)
	var slide := Vector3(0.52, 0.21, -1.65)
	last_door_tween = create_tween()
	last_door_tween.set_process_mode(Tween.TWEEN_PROCESS_PHYSICS)
	last_door_tween.set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	if door_open:
		last_door_tween.tween_property(driver_door, "position", kick, 0.45)
		last_door_tween.tween_property(driver_door, "position", slide, 0.9)
	else:
		last_door_tween.tween_property(driver_door, "position", kick, 0.9)
		last_door_tween.tween_property(driver_door, "position", Vector3.ZERO, 0.45)
	last_door_tween.finished.connect(func():
		door_busy = false
		door_button.disabled = false
		door_button.text = "CLOSE DOOR" if door_open else "OPEN DOOR")

func test_door_motion() -> void:
	toggle_door()
	await last_door_tween.finished
	assert(driver_door.position.distance_to(Vector3(0.52, 0.21, -1.65)) < 0.01)
	toggle_door()
	await last_door_tween.finished
	assert(driver_door.position.length() < 0.01)
	print("SCENEFORGE_DOOR_MOTION_OK")
	shutdown_for_test()

func _input(event: InputEvent) -> void:
	if event is InputEventScreenTouch and not event.pressed:
		touch_points.erase(event.index)

func _unhandled_input(event: InputEvent) -> void:

	if seat_mode and orbit_mode and not comparing:
		if event is InputEventScreenTouch:
			if event.pressed:
				touch_points[event.index] = event.position
			else:
				touch_points.erase(event.index)
		elif event is InputEventScreenDrag:
			if touch_points.size() < 2:
				seat_look_yaw = clampf(seat_look_yaw - event.relative.x * 0.004, -1.35, 1.35)
				seat_look_pitch = clampf(seat_look_pitch - event.relative.y * 0.004, -0.9, 0.65)
			touch_points[event.index] = event.position
		elif event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
			seat_look_yaw = clampf(seat_look_yaw - event.relative.x * 0.004, -1.35, 1.35)
			seat_look_pitch = clampf(seat_look_pitch - event.relative.y * 0.004, -0.9, 0.65)
		elif event is InputEventMouseButton and event.pressed:
			if event.button_index == MOUSE_BUTTON_WHEEL_UP:
				camera.fov = maxf(60, camera.fov - 2)
			elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
				camera.fov = minf(90, camera.fov + 2)
		return

	if orbit_mode and not comparing:
		if event is InputEventScreenTouch:
			if event.pressed:
				touch_points[event.index] = event.position
			else:
				touch_points.erase(event.index)
		elif event is InputEventScreenDrag:
			cockpit_locked = false
			if touch_points.size() >= 2:
				var points: Array = touch_points.values()
				var first: Vector2 = points[0]
				var second: Vector2 = points[1]
				var old_span: float = first.distance_to(second)
				touch_points[event.index] = event.position
				points = touch_points.values()
				first = points[0]
				second = points[1]
				var new_span: float = first.distance_to(second)
				if new_span > 5:
					orbit_radius = clampf(orbit_radius * old_span / new_span, 3.0, 8.5)
			else:
				touch_points[event.index] = event.position
				orbit_angle -= event.relative.x * 0.005
				orbit_elevation = clampf(orbit_elevation + event.relative.y * 0.004, -0.05, 1.05)
		elif event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
			cockpit_locked = false
			orbit_angle -= event.relative.x * 0.005
			orbit_elevation = clampf(orbit_elevation + event.relative.y * 0.004, -0.05, 1.05)
		elif event is InputEventMouseButton and event.pressed:
			if event.button_index == MOUSE_BUTTON_WHEEL_UP:
				orbit_radius = maxf(3.0, orbit_radius - 0.4)
			elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
				orbit_radius = minf(8.5, orbit_radius + 0.4)
		elif event is InputEventMagnifyGesture:
			cockpit_locked = false
			orbit_radius = clampf(orbit_radius / event.factor, 3.0, 8.5)
		return
	if comparing:
		return
	var screen := get_viewport().get_visible_rect().size
	if event is InputEventScreenTouch:
		if event.pressed:
			if event.position.x < screen.x * 0.45 and move_touch == -1:
				move_touch = event.index
				stick_origin = event.position
				stick_ring.position = stick_origin
				stick_ring.visible = true
			elif look_touch == -1:
				look_touch = event.index
		else:
			if event.index == move_touch:
				move_touch = -1
				stick = Vector2.ZERO
				stick_ring.visible = false
			if event.index == look_touch:
				look_touch = -1
	elif event is InputEventScreenDrag:
		if event.index == move_touch:
			stick = ((event.position - stick_origin) / 65.0).limit_length()
			stick_ring.queue_redraw()
		elif event.index == look_touch:
			yaw -= event.relative.x * 0.003
			pitch = clampf(pitch - event.relative.y * 0.003, -1.1, 1.1)
	elif event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		yaw -= event.relative.x * 0.003
		pitch = clampf(pitch - event.relative.y * 0.003, -1.1, 1.1)

func _physics_process(delta: float) -> void:
	if orbit_mode and not comparing:
		body.velocity = Vector3.ZERO
		return

	if "--cockpit-view" in OS.get_cmdline_user_args():
		body.rotation.y = yaw
		camera.rotation.x = pitch
		return
	if inspection_mode:
		if stick.length() > 0.05 or Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_D):
			inspection_mode = false
		else:
			body.velocity = Vector3.ZERO
			body.rotation.y = yaw
			camera.rotation.x = pitch
			return
	if comparing:
		body.position = Vector3(3.2, 0.1, 5.7)
		body.velocity = Vector3.ZERO
		body.rotation.y = 0.58
		camera.rotation.x = -0.1
		return
	var keys := Vector2(float(Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT)) - float(Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT)), float(Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN)) - float(Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP)))
	var input := (stick + keys).limit_length()
	body.rotation.y = yaw
	camera.rotation.x = pitch
	var direction := body.basis * Vector3(input.x, 0, input.y)
	body.velocity.x = direction.x * 3.6
	body.velocity.z = direction.z * 3.6
	body.velocity.y -= 18 * delta
	body.move_and_slide()
	body.position.x = clampf(body.position.x, -7.0, 7.0)
	body.position.z = clampf(body.position.z, -8.0, 9.5)
	elapsed += delta
	if elapsed > 0.5:
		fps_label.text = "Godot renderer preview" if "--capture" in OS.get_cmdline_user_args() else "%d FPS  |  %s" % [Engine.get_frames_per_second(), "BALANCED" if balanced else "REFERENCE"]
		elapsed = 0

var capture_frames := 0
func _process(_delta: float) -> void:
	if orbit_mode and not comparing:
		update_orbit()
		elapsed += _delta
		if elapsed > 0.5:
			fps_label.text = "%d FPS · %s" % [Engine.get_frames_per_second(), "BALANCED" if balanced else "REFERENCE"]
			elapsed = 0
	if comparing:
		comparison_frame()
	if "--capture" in OS.get_cmdline_user_args():
		capture_frames += 1
		if capture_frames == 35:
			var filename := "NeonFoundry-ingame.png"
			if "--seat-view" in OS.get_cmdline_user_args():
				filename = "Kestrel-driver-seat.png"
			elif "--door-open" in OS.get_cmdline_user_args():
				filename = "Kestrel-door-open.png"
			elif "--cockpit-view" in OS.get_cmdline_user_args():
				filename = "Kestrel-cockpit.png"
			elif "--vehicle-view" in OS.get_cmdline_user_args():
				filename = "Kestrel-hovercar.png"
			elif "--vehicle-tail" in OS.get_cmdline_user_args():
				filename = "Kestrel-tail.png"
			elif "--rear-view" in OS.get_cmdline_user_args():
				filename = "NeonFoundry-rear.png"
			elif "--road-closeup" in OS.get_cmdline_user_args():
				filename = "NeonFoundry-road.png"
			if selected_craft>0:
				filename="Foundry-"+chassis.chassis_id+("-seat" if seat_mode else "")+".png"
			get_viewport().get_texture().get_image().save_png(OS.get_environment("GITHUB_WORKSPACE") + "/build/" + filename)
			shutdown_for_test()

# Bounded A/B: same camera, workload and renderer; two phases, no auto tuning.
# Monotonic presentation intervals are not GPU timer measurements.
func apply_quality(use_balanced: bool) -> void:
	balanced = use_balanced
	var viewport := get_viewport()
	viewport.scaling_3d_scale = 0.85 if balanced else 1.0
	viewport.msaa_3d = Viewport.MSAA_2X
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS if balanced else DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.directional_shadow_max_distance = 20.0 if balanced else 24.0
	quality_button.text = "BALANCED" if balanced else "REFERENCE"

func start_comparison() -> void:
	saved_orbit = orbit_mode
	set_inspection(false)
	fps_label.visible = true
	inspection_mode = false
	if comparing:
		return
	saved_position = body.position
	saved_yaw = yaw
	saved_pitch = pitch
	stick = Vector2.ZERO
	move_touch = -1
	look_touch = -1
	stick_ring.visible = false
	fps_label.text = "Same-view comparison running"
	comparing = true
	phase = 0
	phase_frames = 0
	samples.clear()
	results.clear()
	quality_button.disabled = true
	compare_button.disabled = true
	apply_quality(false)
	last_tick = Time.get_ticks_usec()

func cancel_comparison() -> void:
	if not comparing:
		return
	comparing = false
	quality_button.disabled = false
	compare_button.disabled = false
	result_label.text = "Comparison cancelled"
	apply_quality(true)

func comparison_frame() -> void:
	var now := Time.get_ticks_usec()
	var interval := float(now - last_tick) / 1000.0
	last_tick = now
	phase_frames += 1
	var smoke := "--benchmark-smoke" in OS.get_cmdline_user_args()
	var warmup := 3 if smoke else 90
	var count := 8 if smoke else 240
	result_label.text = "Comparing %s: %d / %d frames" % ["REFERENCE" if phase == 0 else "BALANCED", maxi(0, phase_frames - warmup), count]
	if phase_frames <= warmup:
		return
	samples.append(interval)
	if samples.size() < count:
		return
	var ordered := samples.duplicate()
	ordered.sort()
	var mean_ms := 0.0
	for value in samples:
		mean_ms += value
	mean_ms /= samples.size()
	results.append({
		"profile": "reference" if phase == 0 else "balanced",
		"mean_ms": mean_ms,
		"median_ms": ordered[ordered.size() / 2],
		"p95_ms": ordered[mini(ordered.size()-1, int(ceil(ordered.size() * 0.95))-1)],
		"approx_fps": 1000.0 / maxf(mean_ms, 0.001),
		"frames": samples.size(),
		"draw_calls": Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
	})
	if phase == 0:
		phase = 1
		phase_frames = 0
		samples.clear()
		apply_quality(true)
		last_tick = Time.get_ticks_usec()
		return
	comparing = false
	fps_label.text = "BALANCED · comparison complete"
	quality_button.disabled = false
	compare_button.disabled = false
	body.position = saved_position
	yaw = saved_yaw
	pitch = saved_pitch
	result_label.text = "Same-view comparison · REFERENCE %.1f FPS / BALANCED %.1f FPS\nFrame p95: %.1f ms / %.1f ms" % [results[0]["approx_fps"], results[1]["approx_fps"], results[0]["p95_ms"], results[1]["p95_ms"]]
	var report := {
		"measurement": "monotonic rendered-frame callback interval; not GPU time",
		"os": OS.get_name(),
		"adapter": RenderingServer.get_video_adapter_name(),
		"viewport": [get_viewport().size.x, get_viewport().size.y],
		"warmup_frames_per_phase": warmup,
		"order": "reference then balanced; thermal and power state uncontrolled",
		"results": results
	}
	var file := FileAccess.open("user://performance-comparison.json", FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(report, "  "))
	print("SCENEFORGE_COMPARISON ", JSON.stringify(report))
	if saved_orbit:
		set_inspection(true)
	if smoke:
		shutdown_for_test()

var show_tail := false
var inspection_mode := false

func _exit_tree() -> void:
	if lot_feedback!=null:lot_feedback.stop_audio()
	if has_node("KestrelHum"):
		var sound: AudioStreamPlayer3D = get_node("KestrelHum")
		sound.stop()
		sound.stream = null

func shutdown_for_test() -> void:
	if lot_feedback!=null:lot_feedback.stop_audio()
	var sound: AudioStreamPlayer3D = get_node("KestrelHum")
	sound.stop()
	sound.stream = null
	# Playback is released by the audio mixer after a mix cycle.
	await get_tree().create_timer(0.15).timeout
	get_tree().quit()

func open_track() -> void:
	await leave_foundry("res://city_loop.tscn")

func open_fleet() -> void:
	await leave_foundry("res://fleet_hangar.tscn")

func leave_foundry(destination: String) -> void:
	if lot_feedback!=null:lot_feedback.stop_audio()
	var sound: AudioStreamPlayer3D=get_node("KestrelHum")
	sound.stop()
	sound.stream=null
	await get_tree().create_timer(.15).timeout
	get_tree().change_scene_to_file(destination)
