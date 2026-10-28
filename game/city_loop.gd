extends Node3D

# A bounded first driving prototype: one closed city loop, no external assets.
const COUNT := 192
const JUMP_START := 44
const JUMP_END := 52
const RAMP_HEIGHT := 4.2
const GRAVITY := 14.0
const WIDTH := 16.0
const DISTRICTS := ["FOUNDRY ROW","TRANSIT","FREIGHT DOCKS","EXCHANGE"]
var route: PackedVector3Array = []
var car: Node3D
var camera: Camera3D
var route_index := 0
var airborne := false
var vertical_speed := 0.0
var air_time := 0.0
var landing_kick := 0.0
var jump_launches := 0
var jump_landings := 0
var jump_recoveries := 0
var peak_height := 0.0
var hover_rings: Node3D
var speed := 0.0
var reverse_hold := 0.0
var heading := 0.0
var steer := 0.0
var throttle := false
var brake := false
var boost := false
var boost_active := false
var boost_energy := 100.0
var boost_cooldown := 0.0
var boost_locked := false
var boost_button: Button
var left := false
var right := false
var cockpit := false
var hud: Label
var left_button: Button
var right_button: Button
var lap_banner: Label
var banner_time := 0.0
var lap_running := false
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

func block(pos: Vector3, size: Vector3, mat: Material, angle: float = 0.0, pitch: float = 0.0) -> void:
	var box := BoxMesh.new()
	box.size = size
	if not batches.has(mat):
		var surface := SurfaceTool.new()
		surface.begin(Mesh.PRIMITIVE_TRIANGLES)
		batches[mat] = surface
	var builder: SurfaceTool = batches[mat]
	builder.append_from(box, 0, Transform3D(Basis(Vector3.UP, angle)*Basis(Vector3.RIGHT,pitch), pos))

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
	hover_rings=car.get_node("RepulsorFootprints")
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
		speed = 36
		boost_active=true
		boost_energy=62
		steer = 0.7
		feedback.update_feedback(1.0,speed,1.0,steer,5,0.12,cockpit,true,62)
		update_camera(1.0)
		steering_feedback(right_button,true)
		boost_button.text="BOOST / 062%"
		hud.text = "KESTREL MK I / NEON CROSS\nD 129 KM/H  /  BOOST ACTIVE"
	if "--track-jump" in OS.get_cmdline_user_args():
		prepare_jump_capture()
	if "--track-overview" in OS.get_cmdline_user_args():
		set_physics_process(false)
		camera.position=Vector3(120,185,-120)
		camera.far=450
		camera.fov=48
		camera.look_at(Vector3.ZERO)
		for child in get_node("DrivingUI").get_children():
			if child != hud:
				child.hide()
		hud.text="NEON CROSS / DISTRICT STUDY\nFOUNDRY ROW  /  TRANSIT  /  FREIGHT DOCKS  /  EXCHANGE"
	if "--track-smoke" in OS.get_cmdline_user_args():
		call_deferred("test_loop")


func flat(value: Vector3) -> Vector3:
	return Vector3(value.x,0,value.z)

func deck_height(index: int) -> float:
	if index>=28 and index<=JUMP_START:
		var t := float(index-28)/(JUMP_START-28)
		return smoothstep(0.0,1.0,t)*RAMP_HEIGHT
	if index>JUMP_START and index<JUMP_END:
		return RAMP_HEIGHT
	if index>=JUMP_END and index<=68:
		var t := float(index-JUMP_END)/(68-JUMP_END)
		return (1-smoothstep(0.0,1.0,t))*RAMP_HEIGHT
	return 0.0

func is_jump_gap(index: int) -> bool:
	return index>=JUMP_START and index<JUMP_END

func road_half_width(index: int) -> float:
	return 8.0+3.0*(1-clampf(float(index-JUMP_END)/12,0,1)) if index>=JUMP_END and index<64 else 8.0

func outward_at(index: int) -> Vector3:
	var p := route[index]
	var forward := flat(route[(index+1)%COUNT]-p).normalized()
	var normal := Vector3(forward.z,0,-forward.x)
	var center := Vector3(43 if p.x>0 else -43,0,0)
	return normal if (p+normal*14).distance_squared_to(center)>(p-normal*14).distance_squared_to(center) else -normal

func add_wall(surface: SurfaceTool, points: PackedVector3Array) -> void:
	for index in [0,1,2,0,2,3]:
		surface.add_vertex(points[index])

func build_jump_landmarks(trim: Material, orange: Material, cyan: Material) -> void:
	for index in [34,56]:
		var p := route[index]
		var forward := flat(route[index+1]-p).normalized()
		var normal := Vector3(forward.z,0,-forward.x)
		var angle := atan2(forward.x,forward.z)
		for side in [-1.0,1.0]:
			block(p+normal*side*11.5+Vector3.UP*2.5,Vector3(0.35,5,0.35),trim,angle)
		block(p+Vector3.UP*5,Vector3(23.5,0.65,0.4),trim,angle)
		block(p+Vector3.UP*4.6,Vector3(22.5,0.08,0.5),orange if index==34 else cyan,angle)
		district_sign("CROSSING JUMP / AUTO LAUNCH" if index==34 else "LANDING ZONE",p+Vector3.UP*5,forward,Color("ffca85") if index==34 else Color("85eeee"))

func road_material() -> StandardMaterial3D:
	# Fine albedo grain only: no displacement, normal-map shimmer or extra light.
	var road := material("ffffff")
	road.roughness=0.86
	var noise := FastNoiseLite.new()
	noise.seed=4421
	noise.noise_type=FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	noise.frequency=0.7
	noise.fractal_octaves=2
	var ramp := Gradient.new()
	ramp.set_color(0,Color("24343f"))
	ramp.set_color(1,Color("2b3b46"))
	var texture := NoiseTexture2D.new()
	texture.width=256
	texture.height=256
	texture.noise=noise
	texture.color_ramp=ramp
	texture.seamless=true
	texture.generate_mipmaps=true
	road.albedo_texture=texture
	return road

func build_city() -> void:
	var asphalt := road_material()
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
		var a := TAU*i/COUNT
		route.append(Vector3(80*cos(a),deck_height(i),32*sin(2*a)))
	var road := SurfaceTool.new()
	road.begin(Mesh.PRIMITIVE_TRIANGLES)
	var walls := SurfaceTool.new()
	walls.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(COUNT):
		if is_jump_gap(i):
			continue
		var p := route[i]
		var q := route[(i+1)%COUNT]
		var forward := flat(q-p).normalized()
		var normal := Vector3(forward.z,0,-forward.x)
		var next := flat(route[(i+2)%COUNT]-q).normalized()
		var n2 := Vector3(next.z,0,-next.x)
		var width := road_half_width(i)
		var next_width := road_half_width((i+1)%COUNT)
		var verts := PackedVector3Array([p-normal*width,q-n2*next_width,q+n2*next_width,p+normal*width])
		var mid := (p+q)*0.5
		var angle := atan2(forward.x,forward.z)
		var pitch := -atan2(q.y-p.y,flat(q-p).length())
		var surface_normal := Basis(Vector3.UP,angle)*Basis(Vector3.RIGHT,pitch)*Vector3.UP
		for index in [0,2,1,0,3,2]:
			road.set_normal(surface_normal)
			road.set_uv(Vector2(verts[index].x,verts[index].z)*0.2)
			road.add_vertex(verts[index])
		if p.y>0.01 or q.y>0.01:
			add_wall(walls,PackedVector3Array([verts[0],verts[1],Vector3(verts[1].x,-0.1,verts[1].z),Vector3(verts[0].x,-0.1,verts[0].z)]))
			add_wall(walls,PackedVector3Array([verts[2],verts[3],Vector3(verts[3].x,-0.1,verts[3].z),Vector3(verts[2].x,-0.1,verts[2].z)]))
			if i==JUMP_START-1:
				add_wall(walls,PackedVector3Array([verts[1],verts[2],Vector3(verts[2].x,-0.1,verts[2].z),Vector3(verts[1].x,-0.1,verts[1].z)]))
			if i==JUMP_END:
				add_wall(walls,PackedVector3Array([verts[3],verts[0],Vector3(verts[0].x,-0.1,verts[0].z),Vector3(verts[3].x,-0.1,verts[3].z)]))
		for side in [-1.0,1.0]:
			block(mid+normal*side*(width+0.7)+Vector3.UP*0.35,Vector3(1.1,0.7,flat(q-p).length()+0.08),concrete,angle,pitch)
			if i%2==0:
				block(mid+normal*side*(width+0.12)+Vector3.UP*0.5,Vector3(0.035,0.08,p.distance_to(q)*0.8),cyan,angle,pitch)
			var inner := -1.0 if p.x>0 else 1.0
			if side==inner and absf(p.z)>20:
				block(mid+normal*side*(width-0.6)+Vector3.UP*0.015,Vector3(0.48,0.03,p.distance_to(q)+0.02),orange if i%2==0 else concrete,angle,pitch)
			elif i%4==0:
				block(mid+normal*side*(width-0.6)+Vector3.UP*0.012,Vector3(0.35,0.025,p.distance_to(q)),orange,angle,pitch)
		if i%3==0:
			block(mid+Vector3.UP*0.015,Vector3(0.16,0.025,1.4),trim,angle,pitch)
		if i%8==0:
			var arrow := arrow_points(mid,forward)
			for tail in [arrow[1],arrow[2]]:
				var stroke: Vector3=arrow[0]-tail
				block((arrow[0]+tail)*0.5+Vector3.UP*0.025,Vector3(0.12,0.025,stroke.length()),orange,atan2(stroke.x,stroke.z),pitch)
		if i>=36 and i<JUMP_START:
			block(mid+Vector3.UP*0.02,Vector3(width*1.6,0.035,0.22),orange,angle,pitch)
	var road_mesh := MeshInstance3D.new()
	road_mesh.mesh=road.commit()
	road_mesh.material_override=asphalt
	road_mesh.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(road_mesh)
	walls.generate_normals()
	var ramp_walls := MeshInstance3D.new()
	ramp_walls.mesh=walls.commit()
	ramp_walls.material_override=dark
	add_child(ramp_walls)
	var rng := RandomNumberGenerator.new()
	rng.seed = 8431
	for i in range(28):
		var a := TAU*i/28
		var pos := Vector3(104*cos(a),0,66*sin(a))
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
	# Buildings occupy the two lobes, with the crossing kept completely clear.
	for x in [-43.0,43.0]:
		for z in [-10.0,10.0]:
			var height := 12.0+(2.0 if z>0 else 0.0)
			block(Vector3(x,height/2,z),Vector3(14,height,8),wall)
			block(Vector3(x,height+0.2,z),Vector3(14.5,0.4,8.5),trim)
			for col in range(5):
				for side in [-1.0,1.0]:
					block(Vector3(x-5+col*2.5,height-2,z+side*4.03),Vector3(1.1,1.4,0.06),warm)
	for x in [70.0,90.0]:
		block(Vector3(x,3.5,0),Vector3(0.6,7,0.6),trim)
	block(Vector3(80,7,0),Vector3(20.6,1.0,0.7),dark)
	for i in range(16):
		block(Vector3(72.5+i,0.025,0),Vector3(1,0.04,0.8),trim if i%2==0 else dark)
	build_jump_landmarks(trim,orange,cyan)
	build_districts(wall,trim,dark,cyan,orange,warm,concrete)
	flush_batches()
	var sign := Label3D.new()
	sign.text = "NEON CROSS  /  START"
	sign.font_size = 80
	sign.pixel_size = 0.006
	sign.position = Vector3(80,7,-0.4)
	sign.rotation.y = PI
	add_child(sign)


func district_sign(label: String, point: Vector3, forward: Vector3, color: Color) -> void:
	var sign := Label3D.new()
	sign.text=label
	sign.font_size=64
	sign.pixel_size=0.008
	sign.modulate=color
	sign.position=point-forward*0.23
	sign.rotation.y=atan2(forward.x,forward.z)+PI
	add_child(sign)

func build_districts(wall: Material, trim: Material, dark: Material, cyan: Material, orange: Material, warm: Material, concrete: Material) -> void:
	# Facade depth, cornices, rooftop machinery and vertical service ribs.
	var rng := RandomNumberGenerator.new()
	rng.seed=8431
	for i in range(28):
		var a := TAU*i/28
		var pos := Vector3(88*cos(a),0,66*sin(a))
		var height := rng.randf_range(11,27)
		block(pos+Vector3.UP*0.3,Vector3(12.6,0.6,12.6),concrete)
		for side in [-1.0,1.0]:
			for rib in [-5.5,5.5]:
				block(pos+Vector3(rib,height/2,side*6.15),Vector3(0.3,height,0.3),trim)
				block(pos+Vector3(side*6.15,height/2,rib),Vector3(0.3,height,0.3),trim)
			for floor_index in range(2,int(height/3)):
				block(pos+Vector3(0,floor_index*3-0.9,side*6.2),Vector3(11.3,0.16,0.5),dark)
				block(pos+Vector3(side*6.2,floor_index*3-0.9,0),Vector3(0.5,0.16,11.3),dark)
		block(pos+Vector3(2,height+0.8,0),Vector3(3,1.2,2.4),dark)
		for vent in range(5):
			block(pos+Vector3(1.0+vent*0.45,height+1.44,0),Vector3(0.16,0.08,2),trim)
		if i%4==0:
			block(pos+Vector3(-4,height+2.0,1),Vector3(0.12,4,0.12),trim)
	for district in range(4):
		var index: int = [12,76,108,172][district]
		var p := route[index]
		var forward := (route[(index+1)%COUNT]-p).normalized()
		var normal := Vector3(forward.z,0,-forward.x)
		var angle := atan2(forward.x,forward.z)
		var center := p+outward_at(index)*14
		block(center+Vector3.UP*2.4,Vector3(0.5,4.8,0.5),trim,angle)
		block(center+Vector3.UP*4.8,Vector3(8,1.6,0.4),dark,angle)
		block(center+Vector3.UP*3.9,Vector3(8,0.12,0.45),orange if district%2==0 else cyan,angle)
		district_sign("%02d / %s"%[district+1,DISTRICTS[district]],center+Vector3.UP*4.8,forward,Color("e0eced"))
	# Corner boards sit outside the barriers, facing approaching drivers.
	for index in [8,16,80,88,104,112,176,184]:
		var p := route[index]
		var forward := (route[(index+1)%COUNT]-p).normalized()
		var normal := Vector3(forward.z,0,-forward.x)
		var angle := atan2(forward.x,forward.z)
		var point := p+outward_at(index)*9.8
		block(point+Vector3.UP*0.55,Vector3(0.12,1.1,0.12),trim,angle)
		block(point+Vector3.UP*1.4,Vector3(1.7,1.0,0.3),dark,angle)
		district_sign("››" if p.x>0 else "‹‹",point+Vector3.UP*1.4,forward,Color("ffc078"))
	# Transit skybridge: a generous clear span above the racing surface.
	var p := route[76]
	var forward := flat(route[77]-p).normalized()
	var normal := Vector3(forward.z,0,-forward.x)
	var angle := atan2(forward.x,forward.z)
	block(p+Vector3.UP*8,Vector3(27,2.4,4),wall,angle)
	for side in [-1.0,1.0]:
		block(p+normal*side*11.8+Vector3.UP*3.4,Vector3(0.9,6.8,3.5),trim,angle)
		block(p+forward*side*2.03+Vector3.UP*8,Vector3(24,0.7,0.04),dark,angle)
		block(p+forward*side*2.08+Vector3.UP*7.45,Vector3(25,0.08,0.04),cyan,angle)
	for level in [6.85,9.2]:
		block(p+Vector3.UP*level,Vector3(27.5,0.18,4.4),trim,angle)
	district_sign("TRANSIT / MAGLEV",p-forward*2+Vector3.UP*8,forward,Color("8fe8e9"))
	# Freight Docks: stacked ribbed containers and an orange yard crane.
	p=route[108]
	forward=flat(route[109]-p).normalized()
	normal=outward_at(108)
	angle=atan2(normal.x,normal.z)-PI/2
	for column in range(3):
		var center := p+normal*(16+column*5)
		for level in range(1+(column%2)):
			block(center+Vector3.UP*(1.3+level*2.6),Vector3(4,2.5,8),orange if column%2==0 else wall,angle)
			for rib in range(7):
				block(center+forward*(-3+rib)+Vector3.UP*(1.3+level*2.6)-normal*2.05,Vector3(0.1,2.3,0.12),trim,angle)
	block(p+normal*30+Vector3.UP*7,Vector3(1.2,14,1.2),orange,angle)
	block(p+normal*24+Vector3.UP*14,Vector3(14,0.8,1.2),orange,angle)
	block(p+normal*18+Vector3.UP*11.5,Vector3(0.08,4.4,0.08),dark,angle)
	# Exchange tower and blue architectural strips create a fourth silhouette.
	p=route[156]
	forward=flat(route[157]-p).normalized()
	normal=Vector3(forward.z,0,-forward.x)
	var tower := Vector3(44,0,0)
	block(tower+Vector3.UP*14,Vector3(8,28,8),wall)
	block(tower+Vector3.UP*28.3,Vector3(9,0.6,9),trim)
	for side in [-1.0,1.0]:
		block(tower+Vector3(side*4.04,15,0),Vector3(0.06,24,0.18),cyan)
		block(tower+Vector3(0,15,side*4.04),Vector3(0.18,24,0.06),cyan)
	for level in range(4,27,4):
		block(tower+Vector3.UP*level,Vector3(8.1,0.18,8.1),dark)
	# Warm service arches on Foundry Row contrast with the cool transit section.
	for index in [4,12,20]:
		p=route[index]
		forward=(route[index+1]-p).normalized()
		normal=Vector3(forward.z,0,-forward.x)
		angle=atan2(forward.x,forward.z)
		block(p+normal*12+Vector3.UP*3,Vector3(0.3,6,0.3),trim,angle)
		block(p+normal*10+Vector3.UP*6,Vector3(4,0.22,0.3),trim,angle)
		block(p+normal*10+Vector3.UP*5.84,Vector3(3,0.06,0.16),warm,angle)

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

func style_steering(button: Button) -> void:
	button.custom_minimum_size=Vector2(208,90)
	button.add_theme_font_size_override("font_size",23)
	button.focus_mode=Control.FOCUS_NONE
	var normal := StyleBoxFlat.new()
	normal.bg_color=Color(0.025,0.07,0.095,0.78)
	normal.border_color=Color(0.35,0.65,0.72,0.65)
	normal.set_border_width_all(2)
	normal.set_corner_radius_all(8)
	var pressed: StyleBoxFlat=normal.duplicate()
	pressed.bg_color=Color(0.08,0.32,0.39,0.92)
	pressed.border_color=Color("91f1f0")
	button.add_theme_stylebox_override("normal",normal)
	button.add_theme_stylebox_override("hover",normal)
	button.add_theme_stylebox_override("pressed",pressed)
	button.add_theme_color_override("font_pressed_color",Color("dfffff"))
	button.set_meta("idle_style",normal)
	button.set_meta("active_style",pressed)
	button.set_meta("lit",false)

func steering_feedback(button: Button, active: bool) -> void:
	if bool(button.get_meta("lit",false))==active:
		return
	button.set_meta("lit",active)
	var style: StyleBox=button.get_meta("active_style" if active else "idle_style")
	button.add_theme_stylebox_override("normal",style)
	button.add_theme_stylebox_override("hover",style)
	button.add_theme_color_override("font_color",Color("dfffff") if active else Color.WHITE)

func build_ui() -> void:
	var layer := CanvasLayer.new()
	layer.name="DrivingUI"
	add_child(layer)
	hud = Label.new()
	hud.position = Vector2(24,20)
	hud.add_theme_font_size_override("font_size",24)
	layer.add_child(hud)
	lap_banner=Label.new()
	lap_banner.set_anchors_and_offsets_preset(Control.PRESET_CENTER_TOP)
	lap_banner.position=Vector2(-250,110)
	lap_banner.size=Vector2(500,64)
	lap_banner.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER
	lap_banner.add_theme_font_size_override("font_size",22)
	lap_banner.add_theme_color_override("font_color",Color("ffc685"))
	lap_banner.visible=false
	layer.add_child(lap_banner)
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
	row.position = Vector2(24,-130)
	row.add_theme_constant_override("separation",16)
	layer.add_child(row)
	var l := ui_button(row,"◀ LEFT",func(): pass,208)
	left_button=l
	style_steering(l)
	l.button_down.connect(func(): left=true)
	l.button_up.connect(func(): left=false)
	var r := ui_button(row,"RIGHT ▶",func(): pass,208)
	right_button=r
	style_steering(r)
	r.button_down.connect(func(): right=true)
	r.button_up.connect(func(): right=false)
	var pedals := HBoxContainer.new()
	pedals.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT)
	pedals.position = Vector2(-410,-110)
	pedals.add_theme_constant_override("separation",16)
	layer.add_child(pedals)
	var booster := HBoxContainer.new()
	booster.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT)
	booster.position = Vector2(-410,-200)
	layer.add_child(booster)
	boost_button = ui_button(booster,"BOOST / 100%",func(): pass,376)
	boost_button.button_down.connect(func(): boost=true)
	boost_button.button_up.connect(func(): boost=false)
	var b := ui_button(pedals,"BRAKE / REV",func(): pass,170)
	b.button_down.connect(func(): brake=true)
	b.button_up.connect(func(): brake=false)
	var gas := ui_button(pedals,"THRUST",func(): pass,190)
	gas.button_down.connect(func(): throttle=true)
	gas.button_up.connect(func(): throttle=false)

func reset_car() -> void:
	car.position = route[0]
	route_index=0
	airborne=false
	vertical_speed=0
	air_time=0
	landing_kick=0
	jump_launches=0
	jump_landings=0
	jump_recoveries=0
	peak_height=0
	hover_rings.visible=true
	hover_rings.rotation=Vector3.ZERO
	var tangent := flat(route[1]-route[0]).normalized()
	heading = atan2(tangent.x,tangent.z)
	car.rotation = Vector3(0,heading,0)
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
	lap_running=false
	banner_time=0
	lap_banner.visible=false
	throttle=false
	brake=false
	boost=false
	boost_active=false
	boost_energy=100
	boost_cooldown=0
	boost_locked=false
	left=false
	right=false
	driving_touches.clear()

func toggle_camera() -> void:
	cockpit = not cockpit
	feedback.set_cockpit(cockpit)

func closest_segment(pos: Vector3, cursor: int = -1) -> Dictionary:
	var distance := INF
	var result := {"point":route[0],"index":0}
	# Local continuity keeps crossing branches independent, including in mid-air.
	var search := COUNT if cursor<0 else 29
	for slot in range(search):
		var i := slot if cursor<0 else posmod(cursor+slot-14,COUNT)
		var a := route[i]
		var d := route[(i+1)%COUNT]-a
		var test_d := d if cursor<0 else flat(d)
		var offset := pos-a if cursor<0 else flat(pos-a)
		var t := clampf(offset.dot(test_d)/test_d.length_squared(),0,1)
		var p := a+d*t
		var ds := pos.distance_squared_to(p) if cursor<0 else flat(pos-p).length_squared()
		if ds<distance:
			distance=ds
			result={"point":p,"index":i}
	return result

func track_progress(index: int) -> void:
	if checkpoint == 0 and index >= COUNT/4-2 and index <= COUNT/4+8:
		checkpoint=1
	elif checkpoint == 1 and index >= COUNT/2-2 and index <= COUNT/2+8:
		checkpoint=2
	elif checkpoint == 2 and index >= COUNT*3/4-2 and index <= COUNT*3/4+8:
		checkpoint=3
	elif checkpoint == 3 and index <= 4:
		var record := best == 0 or lap_time < best
		lap_banner.text="LAP %d  /  %.1f s\n%s"%[lap,lap_time,"NEW PERSONAL BEST" if record else "LAP COMPLETE"]
		banner_time=3.0
		if record:
			best=lap_time
		lap+=1
		lap_time=0
		checkpoint=0

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		throttle=false
		brake=false
		boost=false
		left=false
		right=false
		driving_touches.clear()

func _input(event: InputEvent) -> void:
	var screen := get_viewport().get_visible_rect().size
	var control_top := screen.y-160
	var pedal_left := screen.x-410
	if event is InputEventScreenTouch:
		if event.pressed and (event.position.y >= control_top or Rect2(screen.x-410,screen.y-210,390,80).has_point(event.position)):
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
	boost=false
	for point in driving_touches.values():
		if Rect2(screen.x-410,screen.y-210,390,80).has_point(point):
			boost=true
			continue
		if point.y < control_top:
			continue
		left = left or (point.x >= 0 and point.x < 240)
		right = right or (point.x >= 240 and point.x < 480)
		brake = brake or (point.x >= pedal_left and point.x < pedal_left+178)
		throttle = throttle or (point.x >= pedal_left+178 and point.x < screen.x-20)
	get_viewport().set_input_as_handled()

func update_boost(delta: float, requested: bool, stopping: bool) -> void:
	boost_active = requested and not stopping and speed >= 0 and not boost_locked and boost_energy > 0
	if boost_active:
		boost_energy = maxf(0,boost_energy-chassis.boost_drain*delta)
		boost_cooldown = 0.8
		if boost_energy == 0:
			boost_locked=true
			boost_active=false
	else:
		boost_cooldown = maxf(0,boost_cooldown-delta)
		if boost_cooldown == 0:
			boost_energy = minf(100,boost_energy+chassis.boost_recharge*delta)
		if boost_energy >= 25:
			boost_locked=false

func update_jump(delta: float, surface_height: float) -> float:
	var p := route[route_index]
	var q := route[(route_index+1)%COUNT]
	var ramp_pitch := -atan2(q.y-p.y,flat(q-p).length())
	if not airborne and is_jump_gap(route_index):
		airborne=true
		air_time=0
		vertical_speed=6.5
		car.position.y=maxf(car.position.y,RAMP_HEIGHT)
		var route_forward := flat(q-p).normalized()
		if travel_velocity.dot(route_forward)>0.2 and speed>0:
			speed=maxf(speed,30.0)
			travel_velocity=Vector3(sin(heading),0,cos(heading))*speed
		jump_launches+=1
	if airborne:
		air_time+=delta
		vertical_speed-=GRAVITY*delta
		car.position.y+=vertical_speed*delta
		peak_height=maxf(peak_height,car.position.y)
		if not is_jump_gap(route_index) and vertical_speed<0 and car.position.y<=surface_height:
			landing_kick=minf(0.10,absf(vertical_speed)*0.012)
			car.position.y=surface_height
			vertical_speed=0
			airborne=false
			jump_landings+=1
			lap_banner.text="CROSSING CLEARED / %.1f s AIR"%air_time
			banner_time=2
		elif car.position.y < -0.7 or air_time>3:
			recover_jump()
	else:
		car.position.y=surface_height
	hover_rings.visible=not airborne
	hover_rings.rotation.x=ramp_pitch if not airborne else 0.0
	return -clampf(vertical_speed*0.012,-0.085,0.085) if airborne else ramp_pitch

func recover_jump() -> void:
	jump_recoveries+=1
	route_index=36
	car.position=route[36]
	var tangent := flat(route[37]-route[36]).normalized()
	heading=atan2(tangent.x,tangent.z)
	speed=0
	travel_velocity=Vector3.ZERO
	vertical_speed=0
	airborne=false
	landing_kick=0
	lap_banner.text="JUMP RESET / FOLLOW THE LAUNCH MARKERS"
	banner_time=3

func prepare_jump_capture() -> void:
	set_physics_process(false)
	reset_car()
	route_index=43
	car.position=route[43]
	var forward := flat(route[44]-route[43]).normalized()
	heading=atan2(forward.x,forward.z)
	speed=32
	travel_velocity=forward*speed
	throttle=true
	for frame in range(36):
		var near := closest_segment(car.position,route_index)
		var target: Vector3=route[(int(near["index"])+4)%COUNT]
		var offset := flat(target-car.position)
		var error := wrapf(atan2(offset.x,offset.z)-heading,-PI,PI)
		left=error>0.015
		right=error< -0.015
		_physics_process(1.0/60)
	assert(airborne and car.position.y>RAMP_HEIGHT)
	update_camera(1.0)

func _physics_process(delta: float) -> void:
	var boost_requested := boost or Input.is_physical_key_pressed(KEY_SHIFT)
	var gas := throttle or boost_requested or Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP)
	var stopping := brake or Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN)
	var turn := float(right or Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT))-float(left or Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT))
	update_boost(delta,boost_requested,stopping)
	var previous_speed := speed
	steering_feedback(left_button,turn < -0.1)
	steering_feedback(right_button,turn > 0.1)
	steer = move_toward(steer,turn,delta*chassis.steering_response)
	if stopping:
		if airborne:
			speed=move_toward(speed,0,3*delta)
			reverse_hold=0
		elif speed > 0.0:
			speed = move_toward(speed,0,chassis.braking*delta)
			reverse_hold = 0.0
		else:
			# A short stop separates braking from deliberate reversing.
			reverse_hold += delta
			if reverse_hold >= chassis.reverse_delay:
				speed = move_toward(speed,-chassis.max_reverse_speed,chassis.reverse_acceleration*delta)
	elif gas:
		reverse_hold = 0.0
		# Thrust first stops backward travel, then accelerates forward.
		if speed < 0:
			speed = move_toward(speed,0,chassis.braking*delta)
		else:
			var limit: float = chassis.max_forward_speed + (chassis.boost_speed_bonus if boost_active else 0.0)
			var push: float = chassis.acceleration * (chassis.boost_acceleration_multiplier if boost_active else 1.0) * (0.25 if airborne else 1.0)
			speed = move_toward(speed,limit,(push if speed < limit else 5.0)*delta)
	else:
		reverse_hold = 0.0
		speed = move_toward(speed,0,chassis.coast_drag*delta)
	heading -= steer*chassis.yaw_rate*clampf(speed/8,-1,1)*delta*(0.3 if airborne else 1.0)
	var forward := Vector3(sin(heading),0,cos(heading))
	travel_velocity = travel_velocity.lerp(forward*speed,1-exp(-chassis.lateral_grip*delta*(0.45 if airborne else 1.0)))
	car.position += travel_velocity*delta
	var nearest := closest_segment(car.position,route_index)
	route_index=int(nearest["index"])
	var center: Vector3 = nearest["point"]
	var offset := flat(car.position-center)
	if offset.length() > 6.0:
		var bounded := center+offset.normalized()*6.0
		car.position.x=bounded.x
		car.position.z=bounded.z
		speed = move_toward(speed,0,35*delta)
		var outward := offset.normalized()
		travel_velocity -= outward*maxf(0,travel_velocity.dot(outward))
	var surface_pitch := update_jump(delta,center.y)
	car.rotation = Vector3(0,heading,0)
	var side := Vector3(forward.z,0,-forward.x)
	var slip := clampf(absf(travel_velocity.dot(side))/maxf(absf(speed),1),0,1)
	feedback.update_feedback(delta,speed,1.0 if gas and not stopping else (0.35 if speed < -0.1 and stopping else 0.0),steer,(speed-previous_speed)/maxf(delta,0.001),slip,cockpit,boost_active,boost_energy,surface_pitch)
	landing_kick=move_toward(landing_kick,0,delta*0.3)
	feedback.position.y-=landing_kick
	if absf(speed) > 0.1:
		lap_running=true
	if lap_running:
		lap_time += delta
	banner_time=maxf(0,banner_time-delta)
	lap_banner.visible=banner_time > 0
	lap_banner.modulate.a=minf(1,banner_time*2)
	if speed > 0.1:
		track_progress(nearest["index"])
	update_camera(delta)
	boost_button.text = "%s / %03d%%" % ["BOOST" if not boost_locked else "RECHARGING",int(boost_energy)]
	hud.text = "NEON CROSS / LAP %d\n%s %03d KM/H  ·  %.1f s\nBEST %s  ·  %d FPS\n%s" % [lap,"R" if speed < -0.05 else "D",int(absf(speed)*3.6),lap_time,"—" if best==0 else "%.1f s"%best,Engine.get_frames_per_second(),("AIRBORNE / %.1f s"%air_time) if airborne else DISTRICTS[int(nearest["index"])/(COUNT/4)]]

func update_camera(delta: float) -> void:
	camera.fov = lerpf(camera.fov,74.0+clampf(absf(speed)/chassis.max_forward_speed,0,1)*7.0+(3.0 if boost_active else 0.0),1-exp(-delta*3))
	if cockpit:
		camera.global_transform = feedback.global_transform*Transform3D(Basis.from_euler(Vector3(chassis.cockpit_pitch,PI,0)),chassis.cockpit_eye)
	else:
		var desired := car.to_global(Vector3(0,3.6,-8.5))
		camera.position = camera.position.lerp(desired,1-exp(-delta*8))
		camera.look_at(car.to_global(Vector3(0,1.15,4)))

func _process(_delta: float) -> void:
	if "--capture" in OS.get_cmdline_user_args():
		capture_frames+=1
		if capture_frames==35:
			var file := "NeonLoop-cockpit.png" if cockpit else ("NeonLoop-action.png" if "--track-action" in OS.get_cmdline_user_args() else "NeonLoop-track.png")
			if "--track-jump" in OS.get_cmdline_user_args():
				file="NeonCross-jump-cockpit.png" if cockpit else "NeonCross-jump.png"
			if "--track-overview" in OS.get_cmdline_user_args():
				file="NeonLoop-overview.png"
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
	touch.index=1
	touch.pressed=true
	touch.position=Vector2(100,screen.y-80)
	_input(touch)
	touch.index=2
	touch.position=Vector2(screen.x-130,screen.y-170)
	_input(touch)
	assert(left and boost and not throttle, "Boost and steering must work with two fingers")
	touch.pressed=false
	_input(touch)
	touch.index=1
	_input(touch)
	assert(not boost and not left)
	# Generous edge hit areas and dragging between directions.
	touch.index=3
	touch.pressed=true
	touch.position=Vector2(5,screen.y-10)
	_input(touch)
	assert(left and not right)
	_physics_process(1.0/60)
	assert(left_button.get_theme_stylebox("normal").bg_color.is_equal_approx(Color(0.08,0.32,0.39,0.92)))
	var drag := InputEventScreenDrag.new()
	drag.index=3
	drag.position=Vector2(475,screen.y-10)
	_input(drag)
	assert(right and not left)
	_physics_process(1.0/60)
	assert(right_button.get_meta("lit") and not left_button.get_meta("lit"))
	touch.pressed=false
	_input(touch)
	assert(not left and not right)
	_physics_process(1.0/60)
	assert(not right_button.get_meta("lit") and not left_button.get_meta("lit"))
	assert(left_button.custom_minimum_size.x==208 and left_button.custom_minimum_size.y==90)
	# Geometric continuity, road containment and ordered lap gates.
	for i in range(COUNT):
		assert(route[i].distance_to(route[(i+1)%COUNT]) < 4.0)
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
	var stopped_time := lap_time
	for frame in range(60):
		_physics_process(1.0/60)
	assert(lap_time > stopped_time+0.9, "Lap clock must include time spent stopped after launch")
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
	assert(camera.position.distance_to(feedback.to_global(chassis.cockpit_eye)) < 0.01)
	# Drive one complete lap through the same acceleration and steering code.
	set_physics_process(false)
	reset_car()
	throttle=true
	for frame in range(2400):
		var near := closest_segment(car.position,route_index)
		var target: Vector3 = route[(int(near["index"])+4)%COUNT]
		var offset := target-car.position
		var error := wrapf(atan2(offset.x,offset.z)-heading,-PI,PI)
		left=error>0.015
		right=error< -0.015
		_physics_process(1.0/60)
		if lap>1:
			break
	assert(lap==2, "Driving model could not complete a city lap")
	# Capacitor drains, locks out at empty, recharges and respects braking.
	reset_car()
	for tick in range(240):
		update_boost(1.0/60,true,false)
	assert(boost_energy < 5 and boost_locked and not boost_active)
	for tick in range(180):
		update_boost(1.0/60,false,false)
	assert(boost_energy > 25 and not boost_locked)
	update_boost(0.1,true,true)
	assert(not boost_active)
	reset_car()
	throttle=true
	boost=true
	# Follow the route while accelerating beyond normal cruise speed.
	var peak := 0.0
	for tick in range(210):
		var nearest := closest_segment(car.position)
		var target: Vector3 = route[(int(nearest["index"])+5)%COUNT]
		var to_target := target-car.position
		var error := wrapf(atan2(to_target.x,to_target.z)-heading,-PI,PI)
		left=error>0.015
		right=error< -0.015
		_physics_process(1.0/60)
		peak=maxf(peak,speed)
	assert(peak > chassis.max_forward_speed+2, "Boost must exceed normal cruise speed")
	boost=false
	print("SCENEFORGE_BOOST_OK")
	# Verify physical feedback, live instruments and chassis attachment contracts.
	assert(feedback.get_node("ComponentMounts").get_child_count()==8)
	assert(chassis.chassis_id=="kestrel" and chassis.lateral_grip>0)
	feedback.update_feedback(1.0,24,0.85,0.7,5,0.12,true)
	assert(feedback.telemetry.last_speed==86 and feedback.telemetry.last_mode=="DRIVE")
	assert(absf(feedback.visual_roll)>0.05)
	assert(not feedback.yoke.transform.is_equal_approx(feedback.yoke_rest))
	var yoke_motion: Transform3D = feedback.yoke_rest.affine_inverse()*feedback.yoke.transform
	assert(yoke_motion.basis.x.y > 0, "Right steering must raise the pilot's left grip")
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
	feedback.update_feedback(1.0,36,1.0,0.7,5,0.12,true,true,62)
	assert(feedback.telemetry.last_mode=="BOOST" and feedback.telemetry.last_speed==129)
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

