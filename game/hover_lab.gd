extends Node3D
## Playable real-physics control test for Android. The gray box is a test rig,
## not a preview or an integration of the approval-locked NF-H01 craft.

const Rig = preload("res://vehicles/hover_rig.gd")
const Touch = preload("res://vehicles/hover_touch_input.gd")

var rig # Script-backed RigidBody3D; dynamic interface from hover_rig.gd
var camera: Camera3D
var hud: Label
var touches: Dictionary = {}
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
	platform("RIGHT BARRIER",Vector3(46,1.35,60),Vector3(1.0,2.7,220),Color("bc7154"))
	platform("LEFT BARRIER",Vector3(-46,1.35,60),Vector3(1.0,2.7,220),Color("bc7154"))
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

func platform(label: String, center: Vector3, size: Vector3, color: Color) -> void:
	var body := StaticBody3D.new()
	body.name=label
	body.position=center
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
	var steer_row := HBoxContainer.new()
	steer_row.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	steer_row.position=Vector2(24,-130)
	steer_row.add_theme_constant_override("separation",16)
	layer.add_child(steer_row)
	var l := button(steer_row,"◀ LEFT",208)
	var r := button(steer_row,"RIGHT ▶",208)
	l.button_down.connect(func():left=true)
	l.button_up.connect(func():left=false)
	r.button_down.connect(func():right=true)
	r.button_up.connect(func():right=false)
	var pedals := HBoxContainer.new()
	pedals.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT)
	pedals.position=Vector2(-410,-110)
	pedals.add_theme_constant_override("separation",16)
	layer.add_child(pedals)
	var b := button(pedals,"BRAKE / REV",170)
	var g := button(pedals,"THRUST",190)
	b.button_down.connect(func():brake=true)
	b.button_up.connect(func():brake=false)
	g.button_down.connect(func():thrust=true)
	g.button_up.connect(func():thrust=false)
	var boost_row := HBoxContainer.new()
	boost_row.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT)
	boost_row.position=Vector2(-410,-200)
	layer.add_child(boost_row)
	var boost_btn := button(boost_row,"BOOST",376)
	boost_btn.button_down.connect(func():boost=true)
	boost_btn.button_up.connect(func():boost=false)

func reset_lab() -> void:
	touches.clear()
	left=false
	right=false
	brake=false
	thrust=false
	boost=false
	rig.reset_to(initial_position)

func _notification(what: int) -> void:
	if what==NOTIFICATION_APPLICATION_FOCUS_OUT:
		touches.clear()
		left=false
		right=false
		brake=false
		thrust=false
		boost=false

func _input(event: InputEvent) -> void:
	var screen := get_viewport().get_visible_rect().size
	if event is InputEventScreenTouch:
		if event.pressed and Touch.is_drive_area(event.position,screen):
			touches[event.index]=event.position
		elif not event.pressed:
			touches.erase(event.index)
		else:
			return
	elif event is InputEventScreenDrag and touches.has(event.index):
		touches[event.index]=event.position
	else:
		return
	var state: Dictionary=Touch.decode(touches,screen)
	left=bool(state["left"])
	right=bool(state["right"])
	brake=bool(state["brake"])
	thrust=bool(state["throttle"])
	boost=bool(state["boost"])
	get_viewport().set_input_as_handled()

func _physics_process(delta: float) -> void:
	if rig.global_position.y < -15.0:
		reset_lab()
	var gas: bool=thrust or Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP)
	var stopping: bool=brake or Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN)
	var active_boost: bool=boost or Input.is_physical_key_pressed(KEY_SHIFT)
	var turn: float=float(right or Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT))-float(left or Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT))
	rig.set_controls(gas,stopping,turn,active_boost)
	update_camera(delta)
	display_timer+=delta
	if display_timer>=0.10:
		display_timer=0.0
		var state := "AIRBORNE" if rig.contact_count==0 else "HOVER / %d PROBES"%rig.contact_count
		hud.text="SCENEFORGE / TRUE HOVER LAB\n%s  |  %03d KM/H  |  SIDE SLIP %.1f M/S\nCLEARANCE %.2f M  |  Y %.2f M  |  %d FPS\nGRAY TEST RIG / NOT NF-H01" % [
			state,int(absf(rig.forward_speed())*3.6),absf(rig.lateral_speed()),
			rig.ground_distance,rig.global_position.y,Engine.get_frames_per_second()]

func update_camera(delta: float) -> void:
	if cockpit:
		camera.global_transform=rig.global_transform*Transform3D(Basis.from_euler(Vector3(-0.07,PI,0)),Vector3(0,0.55,0.65))
	else:
		var ideal: Vector3=rig.to_global(Vector3(0,3.6,-9.5))
		camera.global_position=camera.global_position.lerp(ideal,1.0-exp(-delta*5.0))
		camera.look_at(rig.to_global(Vector3(0,0.8,5.5)))
