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

func _ready() -> void:
	add_child(load("res://assets/neon_foundry.glb").instantiate())
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
	settings.ambient_light_color = Color("7598b2")
	settings.ambient_light_energy = 0.4
	settings.reflected_light_source = Environment.REFLECTED_SOURCE_SKY
	settings.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	environment.environment = settings
	add_child(environment)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-35, -25, 0)
	sun.light_color = Color("8cadcf")
	sun.light_energy = 0.45
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 24.0
	sun.shadow_bias = 0.07
	sun.shadow_normal_bias = 0.8
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
	title.text = "SCENEFORGE  /  NEON FOUNDRY\nRepair bay · surface & lighting study 02"
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
	stick_ring = Control.new()
	stick_ring.mouse_filter = Control.MOUSE_FILTER_IGNORE
	stick_ring.draw.connect(func():
		stick_ring.draw_circle(Vector2.ZERO, 65, Color(0.2, 0.7, 0.9, 0.12))
		stick_ring.draw_arc(Vector2.ZERO, 65, 0, TAU, 48, Color(0.4, 0.8, 1, 0.45), 2)
		stick_ring.draw_circle(stick * 48, 18, Color(0.5, 0.9, 1, 0.6)))
	stick_ring.visible = false
	layer.add_child(stick_ring)

func _unhandled_input(event: InputEvent) -> void:
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
		fps_label.text = "%d FPS  |  Surface study 02" % Engine.get_frames_per_second()
		elapsed = 0

var capture_frames := 0
func _process(_delta: float) -> void:
	if "--capture" in OS.get_cmdline_user_args():
		capture_frames += 1
		if capture_frames == 35:
			get_viewport().get_texture().get_image().save_png(OS.get_environment("GITHUB_WORKSPACE") + "/build/NeonFoundry-ingame.png")
			get_tree().quit()
