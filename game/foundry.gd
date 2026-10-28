extends Node3D

var body: CharacterBody3D
var camera: Camera3D
var yaw := 0.0
var pitch := -0.06
var move_touch := -1
var look_touch := -1
var stick_origin := Vector2.ZERO
var stick := Vector2.ZERO
var stick_ring: Control
var fps_label: Label
var elapsed := 0.0
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
	var scenery: Node3D = load("res://assets/neon_foundry.glb").instantiate()
	add_child(scenery)
	for node in scenery.find_children("*", "MeshInstance3D", true, false):
		for surface in range(node.mesh.get_surface_count()):
			var material: Material = node.get_active_material(surface)
			if material is StandardMaterial3D:
				material.vertex_color_use_as_albedo = true
		if "asphalt" in node.name or "grime" in node.name:
			node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var environment := WorldEnvironment.new()
	var settings := Environment.new()
	var sky := Sky.new()
	var atmosphere := ProceduralSkyMaterial.new()
	atmosphere.sky_top_color = Color("142b48")
	atmosphere.sky_horizon_color = Color("627a89")
	atmosphere.ground_bottom_color = Color("101a21")
	atmosphere.ground_horizon_color = Color("485b68")
	atmosphere.sky_energy_multiplier = 0.6
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
	light(Vector3(0, 3.3, -5.8), Color("ff9b4d"), 3.5, 6.0)
	light(Vector3(0, 3.5, -2.0), Color("ffc175"), 2.0, 5.5)
	light(Vector3(-5.4, 4.0, 6), Color("56dfff"), 2.3, 7.0)
	light(Vector3(-5.4, 4.0, 0), Color("56dfff"), 1.5, 5.0)
	# Collision deliberately follows the open bay rather than enclosing the doorway.
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
	body.position = Vector3(0, 0.1, 7.5)
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
	ui()
	apply_quality(true)
	if "--road-closeup" in OS.get_cmdline_user_args():
		body.position = Vector3(0, 0.1, 4.5)
		pitch = -0.8
	if "--benchmark-smoke" in OS.get_cmdline_user_args():
		start_comparison()

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

func ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	var title := Label.new()
	title.text = "SCENEFORGE  /  NEON FOUNDRY\nRepair bay · lighting & contact study 06"
	title.position = Vector2(28, 20)
	title.add_theme_font_size_override("font_size", 23)
	layer.add_child(title)
	var help := Label.new()
	help.text = "LEFT: MOVE      RIGHT: LOOK      •      Walk into the workshop\nDesktop: WASD / arrows · drag to look"
	help.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	help.position = Vector2(28, -88)
	help.add_theme_font_size_override("font_size", 18)
	layer.add_child(help)
	fps_label = Label.new()
	fps_label.position = Vector2(28, 90)
	layer.add_child(fps_label)
	var reset := Button.new()
	reset.text = "RESET VIEW"
	reset.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	reset.position = Vector2(-200, 25)
	reset.size = Vector2(170, 55)
	reset.pressed.connect(func(): body.position = Vector3(0, 0.1, 7.5); yaw = 0; pitch = -0.06; stick = Vector2.ZERO)
	layer.add_child(reset)
	quality_button = Button.new()
	quality_button.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	quality_button.position = Vector2(-200, 92)
	quality_button.size = Vector2(170, 55)
	quality_button.pressed.connect(func(): apply_quality(not balanced))
	layer.add_child(quality_button)
	compare_button = Button.new()
	compare_button.text = "COMPARE FPS"
	compare_button.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	compare_button.position = Vector2(-200, 159)
	compare_button.size = Vector2(170, 55)
	compare_button.pressed.connect(start_comparison)
	layer.add_child(compare_button)
	result_label = Label.new()
	result_label.position = Vector2(28, 120)
	result_label.add_theme_font_size_override("font_size", 18)
	layer.add_child(result_label)
	reset.pressed.connect(func(): cancel_comparison())
	stick_ring = Control.new()
	stick_ring.mouse_filter = Control.MOUSE_FILTER_IGNORE
	stick_ring.draw.connect(func():
		stick_ring.draw_circle(Vector2.ZERO, 65, Color(0.2, 0.7, 0.9, 0.12))
		stick_ring.draw_arc(Vector2.ZERO, 65, 0, TAU, 48, Color(0.4, 0.8, 1, 0.45), 2)
		stick_ring.draw_circle(stick * 48, 18, Color(0.5, 0.9, 1, 0.6)))
	stick_ring.visible = false
	layer.add_child(stick_ring)

func _unhandled_input(event: InputEvent) -> void:
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
	if comparing:
		body.position = Vector3(0, 0.1, 7.5)
		body.velocity = Vector3.ZERO
		body.rotation.y = 0
		camera.rotation.x = -0.06
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
	if comparing:
		comparison_frame()
	if "--capture" in OS.get_cmdline_user_args():
		capture_frames += 1
		if capture_frames == 35:
			get_viewport().get_texture().get_image().save_png(OS.get_environment("GITHUB_WORKSPACE") + ("/build/NeonFoundry-road.png" if "--road-closeup" in OS.get_cmdline_user_args() else "/build/NeonFoundry-ingame.png"))
			get_tree().quit()

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
	if smoke:
		get_tree().quit()
