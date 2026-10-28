extends Node3D

# A bounded first driving prototype: one closed city loop, no external assets.
const COUNT := 128
const WIDTH := 16.0
var route: PackedVector3Array = []
var car: Node3D
var camera: Camera3D
var speed := 0.0
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
var glass: Array[Dictionary] = []
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
	var source: Node3D = load("res://assets/neon_foundry.glb").instantiate()
	add_child(source)
	# Reuse the original craft, preserving its independently rigged door.
	for child in source.get_children():
		if str(child.name).begins_with("Kestrel_") or str(child.name).begins_with("TailVector") or child.name == "DriverDoor":
			child.reparent(car, true)
	remove_child(source)
	source.queue_free()
	assert(car.get_child_count() > 5, "Kestrel meshes missing from circuit")
	var factory := preload("res://foundry.gd").new()
	factory.build_cockpit_details()
	var details: Node3D = factory.get_node("KestrelCockpitInstruments")
	details.reparent(car)
	factory.free()
	for node in car.find_children("*", "MeshInstance3D", true, false):
		for surface in range(node.mesh.get_surface_count()):
			var mat: Material = node.get_active_material(surface)
			if mat is StandardMaterial3D:
				mat.vertex_color_use_as_albedo = true
				if "vehicle_glass" in node.name:
					var inside: StandardMaterial3D = mat.duplicate()
					inside.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
					inside.albedo_color = Color(0.1, 0.18, 0.22, 0.12)
					inside.metallic = 0.0
					glass.append({"mesh": node, "surface": surface, "outside": mat, "inside": inside})
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
			# Repeated arrow chevrons indicate the clockwise lap direction.
			for side in [-1.0,1.0]:
				block(mid+normal*side*0.32+Vector3.UP*0.025,Vector3(0.12,0.025,0.85),orange,angle+side*0.7)
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
	add_child(sign)

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
	top.position = Vector2(820,20)
	layer.add_child(top)
	ui_button(top,"VIEW",toggle_camera)
	ui_button(top,"RESET",reset_car)
	ui_button(top,"FOUNDRY",func(): get_tree().change_scene_to_file("res://main.tscn"))
	var row := HBoxContainer.new()
	row.position = Vector2(24,610)
	row.add_theme_constant_override("separation",16)
	layer.add_child(row)
	var l := ui_button(row,"◀ LEFT",func(): pass,160)
	l.button_down.connect(func(): left=true)
	l.button_up.connect(func(): left=false)
	var r := ui_button(row,"RIGHT ▶",func(): pass,160)
	r.button_down.connect(func(): right=true)
	r.button_up.connect(func(): right=false)
	var pedals := HBoxContainer.new()
	pedals.position = Vector2(870,610)
	pedals.add_theme_constant_override("separation",16)
	layer.add_child(pedals)
	var b := ui_button(pedals,"BRAKE",func(): pass,170)
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
	steer = 0.0
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
	for entry in glass:
		var mesh: MeshInstance3D = entry["mesh"]
		mesh.set_surface_override_material(entry["surface"], entry["inside"] if cockpit else entry["outside"])

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
	if event is InputEventScreenTouch:
		if event.pressed and event.position.y >= 600:
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
		if point.y < 600:
			continue
		left = left or (point.x >= 24 and point.x < 192)
		right = right or (point.x >= 192 and point.x < 370)
		brake = brake or (point.x >= 870 and point.x < 1048)
		throttle = throttle or (point.x >= 1048 and point.x < 1260)
	get_viewport().set_input_as_handled()

func _physics_process(delta: float) -> void:
	var gas := throttle or Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP)
	var stopping := brake or Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN)
	var turn := float(right or Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT))-float(left or Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT))
	steer = move_toward(steer,turn,delta*4)
	var acceleration := 10.0 if gas else -2.8
	if stopping:
		acceleration = -20
	speed = clampf(speed+acceleration*delta,0,32)
	heading -= steer*1.15*clampf(speed/8,0,1)*delta
	var forward := Vector3(sin(heading),0,cos(heading))
	car.position += forward*speed*delta
	var nearest := closest_segment(car.position)
	var center: Vector3 = nearest["point"]
	var offset := car.position-center
	if offset.length() > 6.0:
		car.position = center+offset.normalized()*6.0
		speed = maxf(0,speed-35*delta)
	car.rotation = Vector3(0,heading,steer*0.055*clampf(speed/20,0,1))
	if speed > 0.1:
		lap_time += delta
	track_progress(nearest["index"])
	update_camera(delta)
	hud.text = "NEON LOOP / LAP %d\n%03d KM/H  ·  %.1f s\nBEST %s  ·  %d FPS" % [lap,int(speed*3.6),lap_time,"—" if best==0 else "%.1f s"%best,Engine.get_frames_per_second()]

func update_camera(delta: float) -> void:
	if cockpit:
		camera.global_position = car.to_global(Vector3(0,1.829,0.418))
		camera.global_rotation = Vector3(-0.10472,PI+heading,0)
	else:
		var desired := car.to_global(Vector3(0,3.6,-8.5))
		camera.position = camera.position.lerp(desired,1-exp(-delta*8))
		camera.look_at(car.to_global(Vector3(0,1.15,4)))

func _process(_delta: float) -> void:
	if "--capture" in OS.get_cmdline_user_args():
		capture_frames+=1
		if capture_frames==35:
			var file := "NeonLoop-cockpit.png" if cockpit else "NeonLoop-track.png"
			get_viewport().get_texture().get_image().save_png(OS.get_environment("GITHUB_WORKSPACE")+"/build/"+file)
			get_tree().quit()

func test_loop() -> void:
	# Geometric continuity, road containment and ordered lap gates.
	for i in range(COUNT):
		assert(route[i].distance_to(route[(i+1)%COUNT]) < 3.3)
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
	assert(speed==0)
	toggle_camera()
	update_camera(1)
	assert(camera.position.distance_to(car.to_global(Vector3(0,1.829,0.418))) < 0.01)
	print("SCENEFORGE_CITY_LOOP_OK")
	get_tree().quit()
