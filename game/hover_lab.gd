extends Node3D
## Playable real-physics control test for Android. The gray box is a test rig,
## not a preview or an integration of the approval-locked NF-H01 craft.

const Rig = preload("res://vehicles/hover_rig.gd")
const Sticks = preload("res://vehicles/dual_stick_controls.gd")

var rig # Script-backed RigidBody3D; dynamic interface from hover_rig.gd
var camera: Camera3D
var hud: Label
var sticks: Control
var thrust := false
var brake := false
var boost := false
var left := false
var right := false
var cockpit := false
var display_timer := 0.0
var initial_position := Vector3(0, 1.6, 0)

func _ready() -> void:
	var env := WorldEnvironment.new()
	var settings := Environment.new()
	var sky := Sky.new()
	var sky_mat := ProceduralSkyMaterial.new()
	sky_mat.sky_top_color=Color("31506e")
	sky_mat.sky_horizon_color=Color("91abc1")
	sky.sky_material=sky_mat
	settings.sky=sky
	settings.background_mode=Environment.BG_SKY
	settings.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
	settings.ambient_light_color=Color("adbccb")
	settings.ambient_light_energy=0.8
	env.environment=settings
	add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees=Vector3(-49,-25,0)
	sun.light_energy=1.3
	sun.shadow_enabled=true
	add_child(sun)
	# One 8 m discontinuity is genuinely unsupported air: no invisible road.
	platform("START / HARD SURFACE",Vector3(0,-0.5,8),Vector3(90,1,94),Color("293c48"))
	platform("SECOND DECK",Vector3(0,-0.5,119),Vector3(90,1,110),Color("365465"))
	platform("RAISED TEST PAD",Vector3(20,0.37,34),Vector3(13,0.74,20),Color("a17a4f"))
	platform("GRASS MATERIAL TEST",Vector3(-20,0.06,42),Vector3(15,0.12,24),Color("4b6950"))
	platform("WATER-LOOK TEST",Vector3(0,0.06,98),Vector3(28,0.12,42),Color("276c88"))
	platform("RIGHT BARRIER",Vector3(46,4,60),Vector3(1,8,220),Color("bc7154"),true)
	platform("LEFT BARRIER",Vector3(-46,4,60),Vector3(1,8,220),Color("bc7154"),true)
	# Real physical height-gates. Floor sensors ignore obstacle layer 2.
	platform("BLUE BEAM / GO UNDER",Vector3(0,4.10,17),Vector3(72,1.0,2.4),Color("238daf"),true)
	platform("AMBER FENCE / GO OVER",Vector3(0,1.08,45),Vector3(72,2.16,2.4),Color("d37c3d"),true)
	rig=Rig.new()
	rig.name="SurfaceProbeCraft"
	rig.position=initial_position
	add_child(rig)
	camera=Camera3D.new()
	camera.current=true
	camera.fov=76
	camera.far=520
	add_child(camera)
	build_ui()
	update_camera(1.0)

func platform(label: String, center: Vector3, size: Vector3, color: Color, obstacle: bool = false) -> void:
	var body := StaticBody3D.new()
	body.name=label
	body.position=center
	body.collision_layer=2 if obstacle else 1
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size=size
	shape.shape=box
	body.add_child(shape)
	var mesh := MeshInstance3D.new()
	var cube := BoxMesh.new()
	cube.size=size
	mesh.mesh=cube
	var paint := StandardMaterial3D.new()
	paint.albedo_color=color
	paint.roughness=0.84
	mesh.material_override=paint
	body.add_child(mesh)
	var friction := PhysicsMaterial.new()
	friction.friction=0.12
	friction.bounce=0.1
	body.physics_material_override=friction
	add_child(body)

func button(row: HBoxContainer, caption: String, width: float) -> Button:
	var b := Button.new()
	b.text=caption
	b.custom_minimum_size=Vector2(width,88)
	b.add_theme_font_size_override("font_size",23)
	b.focus_mode=Control.FOCUS_NONE
	row.add_child(b)
	return b

func build_ui() -> void:
	var layer := CanvasLayer.new()
	layer.name="LabControls"
	add_child(layer)
	hud=Label.new()
	hud.position=Vector2(22,18)
	hud.add_theme_font_size_override("font_size",22)
	hud.add_theme_color_override("font_color",Color("dcefff"))
	layer.add_child(hud)
	var top := HBoxContainer.new()
	top.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	top.position=Vector2(-410,20)
	layer.add_child(top)
	var reset_btn := button(top,"RESET",110)
	reset_btn.pressed.connect(reset_lab)
	var view_btn := button(top,"VIEW",105)
	view_btn.pressed.connect(func():cockpit=not cockpit)
	var leave := button(top,"TRACK",145)
	leave.pressed.connect(func():get_tree().change_scene_to_file("res://city_loop.tscn"))
	sticks=Sticks.new()
	sticks.name="DualAnalog"
	layer.add_child(sticks)
	sticks.ceiling_label="5.5 M"

func reset_lab() -> void:
	sticks.clear()
	left=false
	right=false
	brake=false
	thrust=false
	boost=false
	rig.reset_to(initial_position)

func _notification(what: int) -> void:
	if what==NOTIFICATION_APPLICATION_FOCUS_OUT:
		sticks.clear()
		left=false
		right=false
		brake=false
		thrust=false
		boost=false

func _input(event: InputEvent) -> void:
	if sticks!=null and sticks.handle_event(event):
		get_viewport().set_input_as_handled()

func _physics_process(delta: float) -> void:
	if rig.global_position.y < -15.0:
		reset_lab()
	sticks.tick(delta)
	var analog_throttle: float=sticks.throttle_axis
	if thrust or Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP):
		analog_throttle=1.0
	if brake or Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN):
		analog_throttle=-1.0
	var active_boost: bool=boost or sticks.boost_remaining>0.0 or Input.is_physical_key_pressed(KEY_SHIFT)
	var turn: float=clampf(sticks.steer_axis+float(right or Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT))-float(left or Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT)),-1.0,1.0)
	var altitude: float=clampf(sticks.height_axis+float(Input.is_physical_key_pressed(KEY_E))-float(Input.is_physical_key_pressed(KEY_Q)),-1.0,1.0)
	rig.set_analog_controls(analog_throttle,turn,altitude,active_boost)
	sticks.altitude_fraction=(rig.hover_clearance-rig.MIN_HEIGHT)/(rig.MAX_HEIGHT-rig.MIN_HEIGHT)
	sticks.queue_redraw()
	update_camera(delta)
	display_timer+=delta
	if display_timer>=0.10:
		display_timer=0.0
		var state := "UNSUPPORTED AIR" if rig.contact_count==0 else "REAL HOVER / %d PROBES"%rig.contact_count
		hud.text="SCENEFORGE / TWIN-STICK HOVER LAB\n%s  |  %03d KM/H  |  SLIP %.1f M/S\nHEIGHT %.2f M / TARGET %.2f M [1.1–5.5]\nBLUE: UNDER  /  AMBER: OVER  /  %d FPS" % [
			state,int(absf(rig.forward_speed())*3.6),absf(rig.lateral_speed()),
			rig.global_position.y-rig.deck_y,rig.hover_clearance,Engine.get_frames_per_second()]

func update_camera(delta: float) -> void:
	if cockpit:
		camera.global_transform=rig.global_transform*Transform3D(Basis.from_euler(Vector3(-0.07,PI,0)),Vector3(0,0.55,0.65))
	else:
		var ideal: Vector3=rig.to_global(Vector3(0,3.6,-9.5))
		camera.global_position=camera.global_position.lerp(ideal,1.0-exp(-delta*5.0))
		camera.look_at(rig.to_global(Vector3(0,0.8,5.5)))
