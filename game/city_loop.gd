extends Node3D

# A bounded first driving prototype: one closed city loop, no external assets.
const COUNT := 128
const WIDTH := 16.0
var route: PackedVector3Array = []
var car: Node3D
var camera: Camera3D
var speed := 0.0
var reverse_hold := 0.0
var heading := 0.0
var steer := 0.0
var throttle := false
var brake := false
var left := false
var right := false
var cockpit := false
var hud: Label
var lap := 1
var checkpoint := 0
var lap_time := 0.0
var best := 0.0
var capture_frames := 0
var batches: Dictionary = {}
var chassis: Resource = preload("res://vehicles/kestrel.tres")
var feedback
var travel_velocity := Vector3.ZERO
var sound_button: Button
var shutting_down := false
var driving_touches: Dictionary = {}

func material(color: String, glow: bool = false) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(color)
	m.roughness = 0.72
	if glow:
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	return m

func block(pos: Vector3, size: Vector3, mat: Material, angle: float = 0.0) -> void:
	var box := BoxMesh.new()
	box.size = size
	if not batches.has(mat):
		var surface := SurfaceTool.new()
		surface.begin(Mesh.PRIMITIVE_TRIANGLES)
		batches[mat] = surface
	var builder: SurfaceTool = batches[mat]
	builder.append_from(box, 0, Transform3D(Basis(Vector3.UP, angle), pos))

func flush_batches() -> void:
	for mat in batches:
		var mesh := MeshInstance3D.new()
		var builder: SurfaceTool = batches[mat]
		mesh.mesh = builder.commit()
		mesh.material_override = mat
		add_child(mesh)
	batches.clear()

func _ready() -> void:
	var environment := WorldEnvironment.new()
	var settings := Environment.new()
	settings.background_mode = Environment.BG_COLOR
	settings.background_color = Color("172c42")
	settings.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	settings.ambient_light_color = Color("91afc4")
	settings.ambient_light_energy = 0.8
	settings.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	settings.fog_enabled = true
	settings.fog_light_color = Color("273c50")
	settings.fog_density = 0.002
	environment.environment = settings
	add_child(environment)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-38, -28, 0)
	sun.light_color = Color("b8d6ef")
	sun.light_energy = 1.0
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 70
	sun.shadow_bias = 0.15
	sun.shadow_normal_bias = 1.5
	add_child(sun)
	build_city()
	car = Node3D.new()
	car.name = "Kestrel"
	add_child(car)
	feedback = preload("res://vehicles/kestrel_feedback.gd").new()
	feedback.name = "ChassisVisual"
	car.add_child(feedback)
	feedback.configure(chassis)
	camera = Camera3D.new()
	camera.current = true
	camera.fov = 74
	camera.far = 300
	camera.near = 0.03
	add_child(camera)
	get_viewport().scaling_3d_scale = 0.85
	get_viewport().msaa_3d = Viewport.MSAA_2X
	build_ui()
	reset_car()
	update_camera(1.0)
	if "--track-cockpit" in OS.get_cmdline_user_args():
		toggle_camera()
	if "--sound-on" in OS.get_cmdline_user_args():
		feedback.muted=false
		sound_button.text="SOUND ON"
	if "--track-action" in OS.get_cmdline_user_args():
		set_physics_process(false)
		car.position = route[20]
		var tangent := (route[21]-route[20]).normalized()
		heading = atan2(tangent.x,tangent.z)
		car.rotation.y = heading
		speed = 24
		steer = 0.7
		feedback.update_feedback(1.0,speed,0.85,steer,5,0.12,cockpit)
		update_camera(1.0)
		hud.text = "KESTREL MK I / NEON LOOP\nD 086 KM/H  /  VECTOR ACTIVE"
	if "--track-smoke" in OS.get_cmdline_user_args():
		call_deferred("test_loop")

func build_city() -> void:
	var asphalt := material("263440")
	var concrete := material("475b66")
	var dark := material("192932")
	var wall := material("344b5b")
	var trim := material("657681")
	var orange := material("ce793a")
	var cyan := material("55cbd6", true)
	var window := material("91b8bd", true)
	var warm := material("c4a779", true)
	block(Vector3(0,-0.4,0), Vector3(240,0.5,200), dark)
	for i in range(COUNT):
		var a := TAU * i / COUNT
		route.append(Vector3(64 * cos(a), 0, 42 * sin(a)))
	var road := SurfaceTool.new()
	road.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(COUNT):
		var p := route[i]
		var q := route[(i+1) % COUNT]
		var forward := (q-p).normalized()
		var normal := Vector3(forward.z,0,-forward.x)
		var next := (route[(i+2) % COUNT]-q).normalized()
		var n2 := Vector3(next.z,0,-next.x)
		var verts := [p-normal*8,q-normalize_safe(n2)*8,q+normalize_safe(n2)*8,p+normal*8]
		for index in [0,2,1,0,3,2]:
			road.set_normal(Vector3.UP)
			road.add_vertex(verts[index])
		var mid := (p+q)*0.5
		var angle := atan2(forward.x,forward.z)
		for side in [-1.0,1.0]:
			block(mid+normal*side*8.7+Vector3.UP*0.35,Vector3(1.1,0.7,p.distance_to(q)+0.08),concrete,angle)
			if i % 2 == 0:
				block(mid+normal*side*8.12+Vector3.UP*0.5,Vector3(0.035,0.08,p.distance_to(q)*0.8),cyan,angle)
			if i % 4 == 0:
				block(mid+normal*side*7.4+Vector3.UP*0.012,Vector3(0.35,0.025,p.distance_to(q)),orange,angle)
		if i % 3 == 0:
			block(mid+Vector3.UP*0.015,Vector3(0.16,0.025,1.4),trim,angle)
		if i % 8 == 0:
			# Both strokes meet at a tip ahead along the actual route tangent.
			var arrow := arrow_points(mid, forward)
			for tail in [arrow[1], arrow[2]]:
				var stroke: Vector3 = arrow[0]-tail
				block((arrow[0]+tail)*0.5+Vector3.UP*0.025,Vector3(0.12,0.025,stroke.length()),orange,atan2(stroke.x,stroke.z))
	var road_mesh := MeshInstance3D.new()
	road_mesh.mesh = road.commit()
	road_mesh.material_override = asphalt
	road_mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(road_mesh)
	var rng := RandomNumberGenerator.new()
	rng.seed = 8431
	for i in range(28):
		var a := TAU*i/28
		var pos := Vector3(88*cos(a),0,66*sin(a))
		var height := rng.randf_range(11,27)
		block(pos+Vector3.UP*height/2,Vector3(12,height,12),wall)
		block(pos+Vector3.UP*(height+0.15),Vector3(12.5,0.3,12.5),trim)
		# Windows on all four facades keep the full lap visually finished.
		for floor_index in range(2,int(height/3)):
			for col in [-3.4,0.0,3.4]:
				for side in [-1.0,1.0]:
					var glass_mat := warm if (i+floor_index)%4==0 else window
					block(pos+Vector3(col,floor_index*3,side*6.02),Vector3(1.35,1.5,0.05),glass_mat)
					block(pos+Vector3(side*6.02,floor_index*3,col),Vector3(0.05,1.5,1.35),glass_mat)
	# An inner district provides parallax on both sides without blocking the road.
	for x in [-28.0,0.0,28.0]:
		for z in [-12.0,12.0]:
			var height := 8.0+absf(x)*0.2
			block(Vector3(x,height/2,z),Vector3(16,height,12),wall)
			block(Vector3(x,height+0.2,z),Vector3(16.5,0.4,12.5),trim)
			for col in range(5):
				for side in [-1.0,1.0]:
					block(Vector3(x-6+col*3,height-2, z+side*6.03),Vector3(1.1,1.4,0.06),warm)
	# Gantry straddles the start lane, with supports outside the driving envelope.
	for x in [54.0,74.0]:
		block(Vector3(x,3.5,0),Vector3(0.6,7,0.6),trim)
	block(Vector3(64,7,0),Vector3(20.6,1.0,0.7),dark)
	for i in range(16):
		block(Vector3(56.5+i,0.025,0),Vector3(1,0.04,0.8),trim if i%2==0 else dark)
	flush_batches()
	var sign := Label3D.new()
	sign.text = "NEON LOOP  /  START"
	sign.font_size = 80
	sign.pixel_size = 0.006
	sign.position = Vector3(64,7,-0.4)
	sign.rotation.y = PI
	add_child(sign)

func arrow_points(center: Vector3, forward: Vector3) -> PackedVector3Array:
	var side := Vector3(forward.z,0,-forward.x)
	return PackedVector3Array([center+forward*0.55,center-forward*0.35+side*0.55,center-forward*0.35-side*0.55])

func normalize_safe(v: Vector3) -> Vector3:
	return v.normalized()

func ui_button(row: Control, text: String, action: Callable, width: float = 125) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(width,64)
	button.pressed.connect(action)
	row.add_child(button)
	return button

func build_ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	hud = Label.new()
	hud.position = Vector2(24,20)
	hud.add_theme_font_size_override("font_size",24)
	layer.add_child(hud)
	var top := HBoxContainer.new()
	top.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	top.position = Vector2(-460,20)
	layer.add_child(top)
	ui_button(top,"VIEW",toggle_camera,100)
	sound_button = ui_button(top,"SOUND OFF",func():
		feedback.muted = not feedback.muted
		sound_button.text = "SOUND OFF" if feedback.muted else "SOUND ON",110)
	ui_button(top,"RESET",reset_car,100)
	ui_button(top,"FOUNDRY",func(): shutdown("res://main.tscn"),125)
	var row := HBoxContainer.new()
	row.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	row.position = Vector2(24,-110)
	row.add_theme_constant_override("separation",16)
	layer.add_child(row)
	var l := ui_button(row,"◀ LEFT",func(): pass,160)
	l.button_down.connect(func(): left=true)
	l.button_up.connect(func(): left=false)
	var r := ui_button(row,"RIGHT ▶",func(): pass,160)
	r.button_down.connect(func(): right=true)
	r.button_up.connect(func(): right=false)
	var pedals := HBoxContainer.new()
	pedals.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT)
	pedals.position = Vector2(-410,-110)
	pedals.add_theme_constant_override("separation",16)
	layer.add_child(pedals)
	var b := ui_button(pedals,"BRAKE / REV",func(): pass,170)
	b.button_down.connect(func(): brake=true)
	b.button_up.connect(func(): brake=false)
	var gas := ui_button(pedals,"THRUST",func(): pass,190)
	gas.button_down.connect(func(): throttle=true)
	gas.button_up.connect(func(): throttle=false)

func reset_car() -> void:
	car.position = route[0]
	heading = 0.0
	car.rotation = Vector3.ZERO
	speed = 0.0
	reverse_hold = 0.0
	travel_velocity = Vector3.ZERO
	steer = 0.0
	if feedback != null:
		feedback.rotation = Vector3.ZERO
		feedback.position = Vector3.ZERO
		feedback.visual_roll = 0
		feedback.visual_pitch = 0
		feedback.update_feedback(1.0,0,0,0,0,0,cockpit)
	checkpoint = 0
	lap = 1
	lap_time = 0
	throttle=false
	brake=false
	left=false
	right=false
	driving_touches.clear()

func toggle_camera() -> void:
	cockpit = not cockpit
	feedback.set_cockpit(cockpit)

func closest_segment(pos: Vector3) -> Dictionary:
	var distance := INF
	var result := {"point":route[0],"index":0}
	for i in range(COUNT):
		var a := route[i]
		var d := route[(i+1)%COUNT]-a
		var p := a+d*clampf((pos-a).dot(d)/d.length_squared(),0,1)
		var ds := pos.distance_squared_to(p)
		if ds < distance:
			distance = ds
			result={"point":p,"index":i}
	return result

func track_progress(index: int) -> void:
	if checkpoint == 0 and index >= 30 and index <= 38:
		checkpoint=1
	elif checkpoint == 1 and index >= 62 and index <= 70:
		checkpoint=2
	elif checkpoint == 2 and index >= 94 and index <= 102:
		checkpoint=3
	elif checkpoint == 3 and index <= 4:
		if best == 0 or lap_time < best:
			best=lap_time
		lap+=1
		lap_time=0
		checkpoint=0

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		throttle=false
		brake=false
		left=false
		right=false
		driving_touches.clear()

func _input(event: InputEvent) -> void:
	var screen := get_viewport().get_visible_rect().size
	var control_top := screen.y-120
	var pedal_left := screen.x-410
	if event is InputEventScreenTouch:
		if event.pressed and event.position.y >= control_top:
			driving_touches[event.index] = event.position
		elif not event.pressed:
			driving_touches.erase(event.index)
		else:
			return
	elif event is InputEventScreenDrag and driving_touches.has(event.index):
		driving_touches[event.index] = event.position
	else:
		return
	left=false
	right=false
	throttle=false
	brake=false
	for point in driving_touches.values():
		if point.y < control_top:
			continue
		left = left or (point.x >= 24 and point.x < 192)
		right = right or (point.x >= 192 and point.x < 370)
		brake = brake or (point.x >= pedal_left and point.x < pedal_left+178)
		throttle = throttle or (point.x >= pedal_left+178 and point.x < screen.x-20)
	get_viewport().set_input_as_handled()

func _physics_process(delta: float) -> void:
	var gas := throttle or Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP)
	var stopping := brake or Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN)
	var turn := float(right or Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT))-float(left or Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT))
	var previous_speed := speed
	steer = move_toward(steer,turn,delta*chassis.steering_response)
	if stopping:
		if speed > 0.0:
			speed = move_toward(speed,0,chassis.braking*delta)
			reverse_hold = 0.0
		else:
			# A short stop separates braking from deliberate reversing.
			reverse_hold += delta
			if reverse_hold >= chassis.reverse_delay:
				speed = move_toward(speed,-chassis.max_reverse_speed,5*delta)
	elif gas:
		reverse_hold = 0.0
		# Thrust first stops backward travel, then accelerates forward.
		speed = move_toward(speed,0,chassis.braking*delta) if speed < 0 else minf(chassis.max_forward_speed,speed+chassis.acceleration*delta)
	else:
		reverse_hold = 0.0
		speed = move_toward(speed,0,chassis.coast_drag*delta)
	heading -= steer*chassis.yaw_rate*clampf(speed/8,-1,1)*delta
	var forward := Vector3(sin(heading),0,cos(heading))
	travel_velocity = travel_velocity.lerp(forward*speed,1-exp(-chassis.lateral_grip*delta))
	car.position += travel_velocity*delta
	var nearest := closest_segment(car.position)
	var center: Vector3 = nearest["point"]
	var offset := car.position-center
	if offset.length() > 6.0:
		car.position = center+offset.normalized()*6.0
		speed = move_toward(speed,0,35*delta)
		var outward := offset.normalized()
		travel_velocity -= outward*maxf(0,travel_velocity.dot(outward))
	car.rotation = Vector3(0,heading,0)
	var side := Vector3(forward.z,0,-forward.x)
	var slip := clampf(absf(travel_velocity.dot(side))/maxf(absf(speed),1),0,1)
	feedback.update_feedback(delta,speed,1.0 if gas and not stopping else (0.35 if speed < -0.1 and stopping else 0.0),steer,(speed-previous_speed)/maxf(delta,0.001),slip,cockpit)
	if absf(speed) > 0.1:
		lap_time += delta
	if speed > 0.1:
		track_progress(nearest["index"])
	update_camera(delta)
	hud.text = "NEON LOOP / LAP %d\n%s %03d KM/H  ·  %.1f s\nBEST %s  ·  %d FPS" % [lap,"R" if speed < -0.05 else "D",int(absf(speed)*3.6),lap_time,"—" if best==0 else "%.1f s"%best,Engine.get_frames_per_second()]

func update_camera(delta: float) -> void:
	camera.fov = lerpf(camera.fov,74.0+clampf(absf(speed)/chassis.max_forward_speed,0,1)*7.0,1-exp(-delta*3))
	if cockpit:
		camera.global_transform = feedback.global_transform*Transform3D(Basis.from_euler(Vector3(-0.10472,PI,0)),Vector3(0,1.829,0.418))
	else:
		var desired := car.to_global(Vector3(0,3.6,-8.5))
		camera.position = camera.position.lerp(desired,1-exp(-delta*8))
		camera.look_at(car.to_global(Vector3(0,1.15,4)))

func _process(_delta: float) -> void:
	if "--capture" in OS.get_cmdline_user_args():
		capture_frames+=1
		if capture_frames==35:
			var file := "NeonLoop-cockpit.png" if cockpit else ("NeonLoop-action.png" if "--track-action" in OS.get_cmdline_user_args() else "NeonLoop-track.png")
			get_viewport().get_texture().get_image().save_png(OS.get_environment("GITHUB_WORKSPACE")+"/build/"+file)
			shutdown()

func test_loop() -> void:
	# Android must allow a steering finger and a thrust finger together.
	var touch := InputEventScreenTouch.new()
	touch.index=1
	touch.pressed=true
	var screen := get_viewport().get_visible_rect().size
	touch.position=Vector2(100,screen.y-80)
	_input(touch)
	touch.index=2
	touch.position=Vector2(screen.x-130,screen.y-80)
	_input(touch)
	assert(left and throttle)
	touch.index=1
	touch.pressed=false
	_input(touch)
	assert(not left and throttle)
	touch.index=2
	_input(touch)
	assert(not throttle)
	# Geometric continuity, road containment and ordered lap gates.
	for i in range(COUNT):
		assert(route[i].distance_to(route[(i+1)%COUNT]) < 3.3)
		var forward := (route[(i+1)%COUNT]-route[i]).normalized()
		var arrow := arrow_points(route[i],forward)
		assert((arrow[0]-arrow[1]).dot(forward)>0.8 and (arrow[0]-arrow[2]).dot(forward)>0.8)
		assert(closest_segment(route[i])["point"].distance_to(route[i]) < 0.01)
		track_progress(i)
	assert(lap==1 and checkpoint==3)
	track_progress(0)
	assert(lap==2 and checkpoint==0)
	reset_car()
	throttle=true
	for i in range(60):
		await get_tree().physics_frame
	assert(speed > 5 and car.position.distance_to(route[0]) > 2)
	throttle=false
	brake=true
	for i in range(60):
		await get_tree().physics_frame
	assert(speed < 0, "Holding brake must engage reverse after stopping")
	# Release coasts to a stop without accidentally accelerating forward.
	set_physics_process(false)
	brake=false
	for frame in range(240):
		_physics_process(1.0/60)
	assert(speed==0)
	reset_car()
	brake=true
	for frame in range(120):
		_physics_process(1.0/60)
	assert(speed < -5 and car.position.z < 0, "Reverse must move backward from standstill")
	var before := heading
	right=true
	_physics_process(1.0/60)
	assert(heading > before, "Steering must reverse its yaw effect while backing up")
	right=false
	brake=false
	throttle=true
	for frame in range(60):
		_physics_process(1.0/60)
	assert(speed > 0, "Thrust must stop reverse and regain forward travel")
	car.position = route[0]+Vector3(15,0,0)
	speed=-8
	throttle=false
	brake=true
	_physics_process(1.0/60)
	assert(speed < 0 and car.position.distance_to(closest_segment(car.position)["point"]) <= 6.01)
	toggle_camera()
	update_camera(1)
	assert(camera.position.distance_to(feedback.to_global(Vector3(0,1.829,0.418))) < 0.01)
	# Drive one complete lap through the same acceleration and steering code.
	set_physics_process(false)
	reset_car()
	throttle=true
	for frame in range(2400):
		var near := closest_segment(car.position)
		var target: Vector3 = route[(int(near["index"])+4)%COUNT]
		var offset := target-car.position
		var error := wrapf(atan2(offset.x,offset.z)-heading,-PI,PI)
		left=error>0.015
		right=error< -0.015
		_physics_process(1.0/60)
		if lap>1:
			break
	assert(lap==2, "Driving model could not complete a city lap")
	# Verify physical feedback, live instruments and chassis attachment contracts.
	assert(feedback.get_node("ComponentMounts").get_child_count()==8)
	assert(chassis.chassis_id=="kestrel" and chassis.lateral_grip>0)
	feedback.update_feedback(1.0,24,0.85,0.7,5,0.12,true)
	assert(feedback.telemetry.last_speed==86 and feedback.telemetry.last_mode=="DRIVE")
	assert(absf(feedback.visual_roll)>0.05)
	assert(not feedback.yoke.transform.is_equal_approx(feedback.yoke_rest))
	assert(not feedback.tails[0].transform.is_equal_approx(feedback.tail_rest[0]))
	feedback.update_feedback(1.0,-4,0.3,0,0,0,true)
	assert(feedback.telemetry.last_mode=="REVERSE")
	assert(feedback.sound.pitch_scale>0.78)
	feedback.muted=false
	feedback.update_feedback(0.1,20,1,0,0,0,true)
	assert(feedback.sound.volume_db > -30)
	feedback.muted=true
	feedback.update_feedback(0.1,20,1,0,0,0,true)
	assert(feedback.sound.volume_db == -80)
	print("SCENEFORGE_KESTREL_FEEDBACK_OK")
	print("SCENEFORGE_CITY_LOOP_OK")
	shutdown()

func shutdown(next_scene: String = "") -> void:
	if shutting_down:
		return
	shutting_down=true
	set_physics_process(false)
	feedback.stop_audio()
	await get_tree().create_timer(0.15).timeout
	if next_scene.is_empty():
		get_tree().quit()
	else:
		get_tree().change_scene_to_file(next_scene)

