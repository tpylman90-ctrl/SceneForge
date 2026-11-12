extends Node3D

const Fleet = preload("res://vehicles/fleet_catalog.gd")
const Parts = preload("res://vehicles/performance_parts.gd")
const HoverMotion = preload("res://vehicles/hover_motion.gd")
const HoverTouchInput = preload("res://vehicles/hover_touch_input.gd")
const Crimson = preload("res://tracks/crimson_divide.gd")
const CanyonScenery = preload("res://tracks/canyon_scenery.gd")
const SerpentCanyon = preload("res://tracks/serpent_canyon.gd")
const Skyfall = preload("res://tracks/skyfall_run.gd")

# A bounded first driving prototype: one closed city loop, no external assets.
const COUNT := 192
const JUMP_START := 44
const JUMP_END := 52
const RAMP_HEIGHT := 4.2
const GRAVITY := 14.0
const BASE_3D_SCALE := 0.85
const RUSH_3D_SCALE := 0.80
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
var yaw_velocity := 0.0
var throttle := false
var brake := false
var boost := false
var boost_active := false
var boost_energy := 100.0
var boost_cooldown := 0.0
var boost_locked := false
var boost_button: Button
# Mobile speed VFX: full-screen sampling is skipped when hidden, while 3D
# resolution drops by one discrete step at race velocity (not every frame).
var speed_blur_rect: ColorRect
var speed_blur_material: ShaderMaterial
var speed_blur_level := 0.0
var speed_reduced_resolution := false
var speed_vfx_enabled := true
var left := false
var right := false
var cockpit := false
var near_chase := false # Shrike baked-in glass needs a second exterior camera
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
# Independent physics module; switchable A/B against the proven classic model.
var hover_response = HoverMotion.new()
var hover_handling_enabled := true
var track_id := 0
var skyfall_hazards: Array[Vector3] = []
var skyfall_trim := 0.0
var skyfall_vertical_speed := 0.0
var skyfall_gate_next := 0
var skyfall_renderer_label := ""
var track_menu: Control
var event_menu: ColorRect
var results_panel: ColorRect
var results_info: Label
var countdown_label: Label
const MODE_FREE := 0
const MODE_TIME_TRIAL := 1
const MODE_SOLO_RACE := 2
var race_mode := MODE_FREE
var race_countdown := 0.0
var race_go_flash := 0.0
var race_finished := false
var race_elapsed := 0.0
var race_best_total := 0.0
var race_splits: Array[float] = []
const RACE_LAPS := 3
var wall_cooldown := 0.0
var wall_normal := Vector3.ZERO
var wall_recoil := Vector3.ZERO
var wall_hits := 0
const TRACK_NAMES := ["NEON CROSS","SKYWAY","VIPER RIFT","IRON HARBOR","CRIMSON SERPENT","RED MESA CIRCUIT","DEVIL'S GATE","SKYFALL RUN"]
const TRACK_INFO := ["MEDIUM / Figure-eight crossing jump", "EASY / Elevated oval and forgiving jump", "HARD / S-bends, banked turns and extended leap", "MEDIUM / Dockside straights, technical chicanes and harbor leap", "MEDIUM / Long flowing single-stage canyon sprint", "EASY / Wide mesa loop and sweeping horseshoe turns", "HARD / Tight red-rock gates, crests and ridge chicanes", "OPENING SPRINT / Bridge glide, mountain ascent, airborne finish"]

func route_position(index: int) -> Vector3:
	if track_id==Skyfall.ID:
		return Skyfall.route_points(COUNT)[posmod(index,COUNT)]
	if (track_id>=Crimson.FIRST_ID and track_id<=Crimson.LAST_ID):
		var point: Vector2=Crimson.point(track_id,index,COUNT)
		return Vector3(point.x,deck_height(index),point.y)
	var a := TAU*index/COUNT
	var z := 32*sin(2*a)
	if track_id==1:
		z=38*sin(a)
	elif track_id==2:
		z+=5*sin(4*a)
	elif track_id==3:
		# A closed harbor oval with two chicane-like inset bends per side,
		# distinct from the three existing city circuits.
		z=38.0*sin(a)+8.0*sin(3*a)
	return Vector3(80*cos(a),deck_height(index),z)

func bank_slope(index: int) -> float:
	if track_id==Skyfall.ID:
		return 0.02*sin(float(index)*TAU/float(COUNT)*3.0)
	if (track_id>=Crimson.FIRST_ID and track_id<=Crimson.LAST_ID):
		return Crimson.bank(track_id,index,COUNT)
	if track_id!=2 or index>=26 and index<=70 or index>=132 and index<=156:
		return 0.0
	return -0.10*sin(TAU*index/COUNT*2)

func track_name() -> String:
	return TRACK_NAMES[track_id]

func challenge_laps() -> int:
	return 1 if track_id==4 or track_id==Skyfall.ID else RACE_LAPS

func region_name(index: int) -> String:
	if track_id==Skyfall.ID:
		return Skyfall.sector(index)
	if (track_id>=Crimson.FIRST_ID and track_id<=Crimson.LAST_ID):
		return Crimson.sector(track_id,index,COUNT)
	return DISTRICTS[int(index)/(COUNT/4)]

func jump_start_index() -> int:
	return Skyfall.GAP_START if track_id==Skyfall.ID else JUMP_START

func jump_end_index() -> int:
	return Skyfall.GAP_END if track_id==Skyfall.ID else (48 if (track_id>=Crimson.FIRST_ID and track_id<=Crimson.LAST_ID) else JUMP_END)

func load_best() -> void:
	var records := ConfigFile.new()
	if records.load("user://records.cfg")==OK:
		var legacy: float=float(records.get_value("best",str(track_id),0.0)) if chassis.chassis_id=="kestrel" else 0.0
		best=float(records.get_value("best",str(track_id)+"/"+chassis.chassis_id,legacy))
	else:
		best=0.0

func save_best() -> void:
	var records := ConfigFile.new()
	records.load("user://records.cfg")
	records.set_value("best",str(track_id)+"/"+chassis.chassis_id,best)
	records.save("user://records.cfg")

func load_race_best() -> void:
	var records := ConfigFile.new()
	if records.load("user://records.cfg")==OK:
		race_best_total=float(records.get_value("race_totals",str(track_id)+"/"+chassis.chassis_id,0.0))
	else:
		race_best_total=0.0

func save_race_best() -> void:
	var records := ConfigFile.new()
	records.load("user://records.cfg")
	records.set_value("race_totals",str(track_id)+"/"+chassis.chassis_id,race_best_total)
	records.save("user://records.cfg")

func clear_drive_input() -> void:
	left=false
	right=false
	throttle=false
	brake=false
	boost=false
	driving_touches.clear()

func open_events() -> void:
	clear_drive_input()
	set_physics_process(false)
	if speed_blur_rect!=null:
		speed_blur_rect.hide()
	track_menu.hide()
	results_panel.hide()
	event_menu.show()

func begin_event(mode: int) -> void:
	race_mode=clampi(mode,MODE_FREE,MODE_SOLO_RACE)
	get_tree().set_meta("sceneforge_race_mode",race_mode)
	event_menu.hide()
	track_menu.hide()
	results_panel.hide()
	reset_car()
	set_physics_process(true)

func resume_track() -> void:
	if race_finished:
		reset_car()
	track_menu.hide()
	set_physics_process(true)

func finish_solo_race() -> void:
	if race_finished or race_mode!=MODE_SOLO_RACE:
		return
	race_finished=true
	clear_drive_input()
	set_physics_process(false)
	var total := 0.0
	for split in race_splits:
		total+=split
	var personal_best := race_best_total<=0.0 or total<race_best_total
	if personal_best and total>0:
		race_best_total=total
		save_race_best()
	var credits_earned: int=Parts.award_race(total,personal_best)
	var race_title: String="SPRINT STAGE COMPLETE" if track_id==4 or track_id==Skyfall.ID else "3-LAP SOLO CHALLENGE COMPLETE"
	var report := "%s  /  %s\n%s\nTOTAL  %.2f s\n" % [track_name(),chassis.display_name,race_title,total]
	for i in range(race_splits.size()):
		report+="LAP %d   %.2f s\n" % [i+1,race_splits[i]]
	report+=("NEW EVENT RECORD" if personal_best else "EVENT BEST  %.2f s" % race_best_total)
	report+="\n+%d RACE CREDITS  /  BANK %d" % [credits_earned,Parts.balance()]
	report+="\nSPEND CREDITS ON PERFORMANCE PARTS IN THE FOUNDRY"
	report+="\nSOLO CHALLENGE — CPU RIVALS COMING LATER"
	results_info.text=report
	countdown_label.hide()
	results_panel.show()
	if speed_blur_rect!=null:
		speed_blur_rect.hide()
	hud.text=track_name()+" / FINISHED\nTOTAL %.2f s  /  %d STAGE(S)" % [total,challenge_laps()]

func advance_countdown(delta: float) -> bool:
	if race_countdown>0.0:
		race_countdown=maxf(0.0,race_countdown-delta)
		countdown_label.text=str(ceili(race_countdown)) if race_countdown>0.0 else "GO!"
		countdown_label.show()
		if race_countdown<=0.0:
			race_go_flash=0.8
		return true
	if race_go_flash>0.0:
		race_go_flash=maxf(0.0,race_go_flash-delta)
		countdown_label.visible=race_go_flash>0.0
	return false

func open_tracks() -> void:
	clear_drive_input()
	set_physics_process(false)
	if speed_blur_rect!=null:
		speed_blur_rect.hide()
	event_menu.hide()
	results_panel.hide()
	track_menu.show()

func choose_track(index: int) -> void:
	get_tree().set_meta("sceneforge_track",index)
	get_tree().set_meta("sceneforge_race_mode",race_mode)
	shutdown("res://city_loop.tscn")

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
	var craft_index := clampi(int(get_tree().get_meta("sceneforge_craft",0)),0,Fleet.IDS.size()-1)
	for index in range(Fleet.IDS.size()):
		if "--craft-%d"%index in OS.get_cmdline_user_args():craft_index=index
	chassis=preload("res://vehicles/fleet_catalog.gd").definition(craft_index)
	Parts.apply_to_chassis(chassis)
	track_id=clampi(int(get_tree().get_meta("sceneforge_track",0)),0,TRACK_NAMES.size()-1)
	race_mode=clampi(int(get_tree().get_meta("sceneforge_race_mode",0)),MODE_FREE,MODE_SOLO_RACE)
	for index in range(TRACK_NAMES.size()):
		if "--circuit-%d"%index in OS.get_cmdline_user_args():
			track_id=index
	load_best()
	load_race_best()
	var environment := WorldEnvironment.new()
	var settings := Environment.new()
	settings.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	if track_id==Skyfall.ID:
		var mountain_sky := ProceduralSkyMaterial.new()
		mountain_sky.sky_top_color=Color("3d6e9d")
		mountain_sky.sky_horizon_color=Color("d9c6ab")
		mountain_sky.ground_horizon_color=Color("788c87")
		mountain_sky.ground_bottom_color=Color("46514c")
		sky.sky_material=mountain_sky
	elif (track_id>=Crimson.FIRST_ID and track_id<=Crimson.LAST_ID):
		var desert_sky := ProceduralSkyMaterial.new()
		desert_sky.sky_top_color=Color("41657f") if track_id==4 else Color("496b83")
		desert_sky.sky_horizon_color=Color("d8b296") if track_id==4 else Color("e9ac83")
		desert_sky.ground_horizon_color=Color("c88965")
		desert_sky.ground_bottom_color=Color("473b3d")
		sky.sky_material=desert_sky
	else:
		var panorama := PanoramaSkyMaterial.new()
		panorama.panorama=load("res://assets/twilight_sky.jpg")
		sky.sky_material=panorama
	settings.sky=sky
	settings.background_color = Color("172c42")
	settings.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	settings.ambient_light_color = Color("c4c9bc") if track_id==Skyfall.ID else (Color("a4b0ba") if track_id==4 else (Color("a9aeaa") if (track_id>=Crimson.FIRST_ID and track_id<=Crimson.LAST_ID) else Color("91afc4")))
	settings.ambient_light_energy = 0.76 if track_id==Skyfall.ID else (0.53 if track_id==4 else (0.62 if (track_id>=Crimson.FIRST_ID and track_id<=Crimson.LAST_ID) else 0.8))
	settings.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	settings.fog_enabled = true
	settings.fog_light_color = Color("b2c1c9") if track_id==Skyfall.ID else (Color("c59b86") if track_id==4 else (Color("be8368") if (track_id>=Crimson.FIRST_ID and track_id<=Crimson.LAST_ID) else Color("273c50")))
	settings.fog_density = 0.00082 if track_id==Skyfall.ID else (0.0032 if track_id==4 else (0.0014 if (track_id>=Crimson.FIRST_ID and track_id<=Crimson.LAST_ID) else 0.002))
	settings.fog_sky_affect = 0.0
	if track_id==4:
		# Lightweight distance haze, not expensive realtime volumetrics.
		settings.fog_aerial_perspective=0.3
		settings.fog_sun_scatter=0.12
		settings.fog_height=1.0
		settings.fog_height_density=0.008
	environment.environment = settings
	add_child(environment)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-38, -28, 0)
	sun.light_color = Color("fff0d5") if track_id==Skyfall.ID else (Color("ffe0b8") if track_id==4 else (Color("ffd3a5") if (track_id>=Crimson.FIRST_ID and track_id<=Crimson.LAST_ID) else Color("b8d6ef")))
	sun.light_energy = 1.24 if track_id==Skyfall.ID else (1.01 if track_id==4 else (0.98 if (track_id>=Crimson.FIRST_ID and track_id<=Crimson.LAST_ID) else 1.0))
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 70
	sun.shadow_bias = 0.15
	sun.shadow_normal_bias = 1.5
	add_child(sun)
	build_city()
	car = Node3D.new()
	car.name = chassis.chassis_id.capitalize()
	add_child(car)
	feedback = preload("res://vehicles/kestrel_feedback.gd").new()
	feedback.name = "ChassisVisual"
	car.add_child(feedback)
	feedback.configure(chassis)
	hover_rings=car.get_node_or_null("RepulsorFootprints")
	camera = Camera3D.new()
	camera.current = true
	camera.fov = 74
	camera.far = 2400 if track_id==Skyfall.ID else (500 if (track_id>=Crimson.FIRST_ID and track_id<=Crimson.LAST_ID) else 300)
	camera.near = 0.03
	add_child(camera)
	get_viewport().scaling_3d_scale = BASE_3D_SCALE
	get_viewport().msaa_3d = Viewport.MSAA_2X
	build_speed_effect()
	build_ui()
	skyfall_renderer_label="RENDERER %s / %s" % [RenderingServer.get_current_rendering_method().to_upper(),RenderingServer.get_current_rendering_driver_name().to_upper()]
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
		hud.text = chassis.display_name+" / "+track_name()+"\nD 129 KM/H  /  BOOST ACTIVE"
	if "--track-jump" in OS.get_cmdline_user_args():
		prepare_jump_capture()
	# Landmark proof: capture 7 spline segments before each hero assembly.
	# The captures are in the real playable scene, not Blender mockups.
	if track_id==4:
		for landmark in [14,75,155]:
			if "--track-landmark-%d" % landmark in OS.get_cmdline_user_args():
				set_physics_process(false)
				var start_idx: int=posmod(landmark-7,COUNT)
				route_index=start_idx
				car.position=route[start_idx]
				var forward: Vector3=flat(route[(start_idx+3)%COUNT]-route[start_idx]).normalized()
				heading=atan2(forward.x,forward.z)
				car.rotation.y=heading
				speed=30
				update_camera(1.0)
				hud.text="CRIMSON SERPENT / CANYON LANDMARK %d" % landmark
				break
	# Capture the actual live 3D descent at two positions for mobile review.
	# These views use the race camera, not offline concept artwork.
	if track_id==Skyfall.ID:
		for flight_index in [140,167]:
			if "--track-flight-%d" % flight_index in OS.get_cmdline_user_args():
				set_physics_process(false)
				route_index=flight_index
				car.position=route[flight_index]+Vector3.UP*8.0
				var tangent: Vector3=flat(route[flight_index+1]-route[flight_index]).normalized()
				heading=atan2(tangent.x,tangent.z)
				car.rotation.y=heading
				speed=43.0
				airborne=true
				feedback.update_feedback(1.0,speed,0.8,0,0,0,cockpit,true,75,-0.17)
				update_camera(1.0)
				hud.text="SKYFALL RUN / FLIGHT %d\nVULKAN  /  3D DESCENT" % flight_index
				break
	if "--track-overview" in OS.get_cmdline_user_args():
		set_physics_process(false)
		camera.position=Vector3(850,950,-300) if track_id==Skyfall.ID else (Vector3(25,390,-25) if (track_id>=Crimson.FIRST_ID and track_id<=Crimson.LAST_ID) else Vector3(120,185,-120))
		camera.far=3400 if track_id==Skyfall.ID else (850 if (track_id>=Crimson.FIRST_ID and track_id<=Crimson.LAST_ID) else 450)
		camera.fov=65 if track_id==Skyfall.ID else (54 if (track_id>=Crimson.FIRST_ID and track_id<=Crimson.LAST_ID) else 48)
		camera.look_at(Vector3(850,140,970) if track_id==Skyfall.ID else Vector3.ZERO)
		for child in get_node("DrivingUI").get_children():
			if child != hud:
				child.hide()
		hud.text=track_name()+" / CIRCUIT OVERVIEW\n"+TRACK_INFO[track_id]
	if "--track-smoke" in OS.get_cmdline_user_args():
		call_deferred("test_loop")
	if "--track-menu" in OS.get_cmdline_user_args():
		open_tracks()


func flat(value: Vector3) -> Vector3:
	return Vector3(value.x,0,value.z)

func deck_height(index: int) -> float:
	if track_id==Skyfall.ID:
		return route[posmod(index,COUNT)].y if route.size()==COUNT else Skyfall.route_points(COUNT)[posmod(index,COUNT)].y
	var base: float=Crimson.ground_height(track_id,index,COUNT) if (track_id>=Crimson.FIRST_ID and track_id<=Crimson.LAST_ID) else (2.0 if track_id==1 else 0.0)
	if track_id==2 and index>=96 and index<=128:
		base=3.0*pow(sin(PI*float(index-96)/32.0),2)
	var first: int=jump_start_index()
	var last: int=jump_end_index()
	var ramp_begin: int=first-16
	var ramp_finish: int=last+16
	if index>=ramp_begin and index<=first:
		var t: float=float(index-ramp_begin)/float(first-ramp_begin)
		return base+smoothstep(0.0,1.0,t)*RAMP_HEIGHT
	if index>first and index<last:
		return base+RAMP_HEIGHT
	if index>=last and index<=ramp_finish:
		var t: float=float(index-last)/float(ramp_finish-last)
		return base+(1.0-smoothstep(0.0,1.0,t))*RAMP_HEIGHT
	return base

func is_jump_gap(index: int) -> bool:
	return index>=jump_start_index() and index<jump_end_index()

func road_half_width(index: int) -> float:
	if track_id==Skyfall.ID:
		return Skyfall.half_width(index)
	if (track_id>=Crimson.FIRST_ID and track_id<=Crimson.LAST_ID):
		var natural: float=Crimson.half_width(track_id,index)
		var finish: int=jump_end_index()
		return natural+2.5*(1.0-clampf(float(index-finish)/10.0,0.0,1.0)) if index>=finish and index<finish+10 else natural
	return 8.0+3.0*(1-clampf(float(index-JUMP_END)/12,0,1)) if index>=JUMP_END and index<64 else 8.0

func outward_at(index: int) -> Vector3:
	var p := route[index]
	var forward := flat(route[(index+1)%COUNT]-p).normalized()
	var normal := Vector3(forward.z,0,-forward.x)
	if (track_id>=Crimson.FIRST_ID and track_id<=Crimson.LAST_ID):
		return normal if normal.dot(flat(p))>=0.0 else -normal
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
			block(p+normal*side*11.5+Vector3.UP*3.75,Vector3(0.35,7.5,0.35),trim,angle)
		block(p+Vector3.UP*7.5,Vector3(23.5,0.65,0.4),trim,angle)
		block(p+Vector3.UP*7.1,Vector3(22.5,0.08,0.5),orange if index==34 else cyan,angle)
		district_sign("CROSSING JUMP / AUTO LAUNCH" if index==34 else "LANDING ZONE",p+Vector3.UP*7.5,forward,Color("ffca85") if index==34 else Color("85eeee"))

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

func outer_building_position(index: int) -> Vector3:
	var angle := TAU*index/28
	return Vector3(104*cos(angle),0,66*sin(angle))

func build_city() -> void:
	if track_id==Skyfall.ID:
		route=Skyfall.route_points(COUNT)
		skyfall_hazards=Skyfall.populate(self,route)
		flush_batches()
		return
	if (track_id>=Crimson.FIRST_ID and track_id<=Crimson.LAST_ID):
		build_crimson_circuit()
		return
	var asphalt := road_material()
	var concrete := material("475b66")
	var dark := material("192932")
	var wall := material(["344b5b","3b5264","493f50","505d66"][track_id])
	var trim := material("657681")
	var orange := material("ce793a")
	var cyan := material("55cbd6", true)
	var window := material("91b8bd", true)
	var warm := material("c4a779", true)
	block(Vector3(0,-0.4,0), Vector3(400,0.5,320), dark)
	for i in range(COUNT):
		route.append(route_position(i))
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
		normal.y=bank_slope(i)
		n2.y=bank_slope((i+1)%COUNT)
		var width := road_half_width(i)
		var next_width := road_half_width((i+1)%COUNT)
		var verts := PackedVector3Array([p-normal*width,q-n2*next_width,q+n2*next_width,p+normal*width])
		var mid := (p+q)*0.5
		var angle := atan2(forward.x,forward.z)
		var pitch := -atan2(q.y-p.y,flat(q-p).length())
		var surface_normal := (q-p).cross(verts[2]-verts[1]).normalized()
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
		var pos := outer_building_position(i)
		var height := rng.randf_range(11,27)
		# Leave an open parcel for the freight yard at the new lobe.
		if i in [11,12]:
			continue
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
		block(Vector3(x,3.5+route[0].y,0),Vector3(0.6,7,0.6),trim)
	block(Vector3(80,7+route[0].y,0),Vector3(20.6,1.0,0.7),dark)
	for i in range(16):
		block(Vector3(72.5+i,route[0].y+0.025,0),Vector3(1,0.04,0.8),trim if i%2==0 else dark)
	build_jump_landmarks(trim,orange,cyan)
	build_districts(wall,trim,dark,cyan,orange,warm,concrete)
	build_street_detail(concrete,dark,trim,orange,cyan,warm)
	build_map_polish(wall,trim,dark,orange,cyan,warm)
	if track_id==3:
		build_harbor_details(concrete,dark,trim,orange,cyan)
	if track_id==1:
		for index in range(0,COUNT,12):
			var p := route[index]
			var forward := flat(route[(index+1)%COUNT]-p).normalized()
			var normal := Vector3(forward.z,0,-forward.x)
			for side in [-1.0,1.0]:
				block(p+normal*side*9.2-Vector3.UP*0.6,Vector3(0.8,2.5,0.8),trim)
				block(p+normal*side*9.2+Vector3.UP*0.8,Vector3(0.85,0.12,0.85),cyan)
	flush_batches()
	var sign := Label3D.new()
	sign.text = track_name()+"  /  START"
	sign.font_size = 80
	sign.pixel_size = 0.006
	sign.position = Vector3(80,7+route[0].y,-0.4)
	sign.rotation.y = PI
	add_child(sign)


func rock_column(base: Vector3, radius: float, height: float, mat: Material, yaw: float = 0.0) -> void:
	# Low-poly seven-sided sandstone with tapered tops. Batch by material so
	# dozens of formations do not require dozens of Android draw calls.
	var rock := CylinderMesh.new()
	rock.top_radius=radius*0.66
	rock.bottom_radius=radius
	rock.height=height
	rock.radial_segments=7
	if not batches.has(mat):
		var surface := SurfaceTool.new()
		surface.begin(Mesh.PRIMITIVE_TRIANGLES)
		batches[mat]=surface
	var builder: SurfaceTool=batches[mat]
	builder.append_from(rock,0,Transform3D(Basis(Vector3.UP,yaw).scaled(Vector3(1.0,1.0,0.82)),base+Vector3.UP*height*0.5))

func canyon_clear(point: Vector3, clearance: float) -> bool:
	# Keep large decoration clear of every branch of the route, including
	# its far side. The player never collides with hidden scenic geometry.
	var radius_squared: float=clearance*clearance
	for line_point in route:
		if flat(point-line_point).length_squared()<radius_squared:
			return false
	return true

func canyon_arch(index: int, rock: Material, lip: Material) -> void:
	var p: Vector3=route[index]
	var tangent: Vector3=flat(route[(index+1)%COUNT]-p).normalized()
	var normal: Vector3=Vector3(tangent.z,0.0,-tangent.x)
	var angle: float=atan2(tangent.x,tangent.z)
	var width: float=road_half_width(index)
	# Genuine clear opening, not an arch-shaped collision obstacle.
	for side in [-1.0,1.0]:
		rock_column(Vector3(p.x+normal.x*side*(width+7.5),-0.45,p.z+normal.z*side*(width+7.5)),5.5,16.5,rock,angle)
		block(p+normal*side*(width+7.0)+Vector3.UP*16.7,Vector3(6.0,2.3,5.8),lip,angle)
	block(p+Vector3.UP*18.7,Vector3(width*2.0+20.0,2.7,6.1),rock,angle)
	district_sign("CRIMSON DIVIDE / STONE ARCH",p+Vector3.UP*17.8,tangent,Color("ffe1b8"))

func build_crimson_landmarks(sand: Material, sandstone: Material, rust: Material, dark_rock: Material, warm: Material) -> void:
	# Unique route arches are retained. Geological terrain, rock walls and
	# skyline formations are now built by CanyonScenery in one static batch.
	if track_id==4:
		canyon_arch(86,sandstone,warm)
	elif track_id==5:
		canyon_arch(139,rust,sandstone)
	# Track markers remain outside the driving envelope.
	for index in range(0,COUNT,12):
		var p: Vector3=route[index]
		var outward: Vector3=outward_at(index)
		var marker: Vector3=p+outward*(road_half_width(index)+3.8)
		block(marker+Vector3.UP*1.7,Vector3(0.55,3.4,0.55),sand)
		block(marker+Vector3.UP*3.5,Vector3(0.75,0.3,0.75),warm)

func build_crimson_circuit() -> void:
	# All three tracks use one proven driving/boost/jump engine. This separate
	# biome bypasses the city buildings, street props and district decals.
	var sand: StandardMaterial3D=material("684238")
	var sandstone: StandardMaterial3D=material("b86c4b")
	var rust: StandardMaterial3D=material("884b38")
	var dark_rock: StandardMaterial3D=material("62443e")
	var warm: StandardMaterial3D=material("d99a65")
	var guard: StandardMaterial3D=material("614d49")
	var edge: StandardMaterial3D=material("ffd096",true)
	var road_mat: StandardMaterial3D=material("464348")
	road_mat.roughness=0.87
	# A single road draw call, with inexpensive baked roadside darkening and
	# tire-wear color variation on Crimson Serpent. No asphalt normal maps.
	if track_id==4:
		road_mat.vertex_color_use_as_albedo=true
		# Single-sample racing asphalt map, blended with the baked wear colors.
		road_mat.albedo_texture=load("res://tracks/serpent_textures/asphalt_512.png") as Texture2D
		road_mat.normal_enabled=false
		road_mat.uv1_triplanar=false
		road_mat.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	for index in range(COUNT):
		route.append(route_position(index))
	if track_id==4:
		SerpentCanyon.populate(self,route)
	else:
		CanyonScenery.populate(self,route,track_id)
	var road := SurfaceTool.new()
	road.begin(Mesh.PRIMITIVE_TRIANGLES)
	var walls := SurfaceTool.new()
	walls.begin(Mesh.PRIMITIVE_TRIANGLES)
	for index in range(COUNT):
		if is_jump_gap(index):
			continue
		var p: Vector3=route[index]
		var q: Vector3=route[(index+1)%COUNT]
		var forward: Vector3=flat(q-p).normalized()
		var side: Vector3=Vector3(forward.z,0,-forward.x)
		var tangent_next: Vector3=flat(route[(index+2)%COUNT]-q).normalized()
		var side_next: Vector3=Vector3(tangent_next.z,0,-tangent_next.x)
		side.y=bank_slope(index)
		side_next.y=bank_slope((index+1)%COUNT)
		var half_width: float=road_half_width(index)
		var next_width: float=road_half_width((index+1)%COUNT)
		var corners := PackedVector3Array([p-side*half_width,q-side_next*next_width,q+side_next*next_width,p+side*half_width])
		var face_normal: Vector3=(q-p).cross(corners[2]-corners[1]).normalized()
		if track_id==4:
			# More believable asphalt: darker road shoulders and gently worn
			# wheel paths encoded directly as vertex colors. Four lengthwise
			# strips still produce ONE road surface and ONE material.
			for strip in range(4):
				var u0: float=float(strip)*0.25
				var u1: float=float(strip+1)*0.25
				var a: Vector3=corners[0].lerp(corners[3],u0)
				var b: Vector3=corners[1].lerp(corners[2],u0)
				var c: Vector3=corners[1].lerp(corners[2],u1)
				var d: Vector3=corners[0].lerp(corners[3],u1)
				var quad: PackedVector3Array=PackedVector3Array([a,c,b,a,d,c])
				var us: PackedFloat32Array=PackedFloat32Array([u0,u1,u0,u0,u1,u1])
				for corner in range(quad.size()):
					var lateral: float=us[corner]
					var road_edge_distance: float=absf(lateral-0.5)*2.0
					var shoulder: float=smoothstep(0.35,1.0,road_edge_distance)
					var wear: float=0.024*(1.0-smoothstep(0.03,0.17,absf(lateral-0.25)))
					wear+=0.024*(1.0-smoothstep(0.03,0.17,absf(lateral-0.75)))
					var variation: float=0.009*sin(float(index)*0.17+lateral*5.0)
					var tint: float=clampf(0.97-0.095*shoulder+wear+variation,0.84,1.02)
					road.set_normal(face_normal)
					road.set_color(Color(tint,tint*0.995,tint*0.993))
					road.set_uv(Vector2(quad[corner].x,quad[corner].z)*0.07)
					road.add_vertex(quad[corner])
		else:
			for corner in [0,2,1,0,3,2]:
				road.set_normal(face_normal)
				road.set_uv(Vector2(corners[corner].x,corners[corner].z)*0.07)
				road.add_vertex(corners[corner])
		if p.y>-0.01 or q.y>-0.01:
			add_wall(walls,PackedVector3Array([corners[0],corners[1],Vector3(corners[1].x,-0.5,corners[1].z),Vector3(corners[0].x,-0.5,corners[0].z)]))
			add_wall(walls,PackedVector3Array([corners[2],corners[3],Vector3(corners[3].x,-0.5,corners[3].z),Vector3(corners[2].x,-0.5,corners[2].z)]))
		var center: Vector3=(p+q)*0.5
		var angle: float=atan2(forward.x,forward.z)
		var pitch: float=-atan2(q.y-p.y,flat(q-p).length())
		var length: float=flat(q-p).length()
		for side_sign in [-1.0,1.0]:
			block(center+side*side_sign*(half_width+0.75)+Vector3.UP*0.65,Vector3(1.2,1.3,length+0.1),guard,angle,pitch)
			if index%2==0:
				block(center+side*side_sign*(half_width+0.12)+Vector3.UP*0.07,Vector3(0.11,0.10,length*0.75),edge,angle,pitch)
		if index%4==0:
			block(center+Vector3.UP*0.06,Vector3(0.21,0.06,1.7),warm,angle,pitch)
		if index>=jump_start_index()-9 and index<jump_start_index() and index%2==0:
			block(center+Vector3.UP*0.09,Vector3(half_width*1.5,0.06,0.25),edge,angle,pitch)
	var road_mesh := MeshInstance3D.new()
	road_mesh.name="CrimsonDriveSurface"
	road_mesh.mesh=road.commit()
	road_mesh.material_override=road_mat
	road_mesh.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(road_mesh)
	walls.generate_normals()
	var wall_mesh := MeshInstance3D.new()
	wall_mesh.name="CrimsonDeckSides"
	wall_mesh.mesh=walls.commit()
	wall_mesh.material_override=dark_rock
	add_child(wall_mesh)
	# The finish gantry and clear checkpoint markers are aligned to the
	# actual first road segment rather than hard-coded city coordinates.
	var start: Vector3=route[0]
	var forward: Vector3=flat(route[1]-start).normalized()
	var normal: Vector3=Vector3(forward.z,0,-forward.x)
	var angle: float=atan2(forward.x,forward.z)
	for sign in [-1.0,1.0]:
		block(start+normal*sign*(road_half_width(0)+2.6)+Vector3.UP*4.3,Vector3(0.9,8.6,0.9),guard,angle)
	block(start+Vector3.UP*8.4,Vector3(road_half_width(0)*2.0+6.0,0.8,0.9),warm,angle)
	for stripe in range(16):
		block(start+normal*(float(stripe)-7.5)*1.45+Vector3.UP*0.07,Vector3(1.0,0.06,0.95),warm if stripe%2==0 else dark_rock,angle)
	var jump_p: Vector3=route[jump_start_index()-9]
	var jump_forward: Vector3=flat(route[jump_start_index()-8]-jump_p).normalized()
	district_sign("CANYON LEAP / AUTO LAUNCH",jump_p+Vector3.UP*8.3,jump_forward,Color("fff2c6"))
	var landing: Vector3=route[jump_end_index()+8]
	var landing_forward: Vector3=flat(route[jump_end_index()+9]-landing).normalized()
	district_sign("STABLE LANDING",landing+Vector3.UP*8.3,landing_forward,Color("eec39f"))
	build_crimson_landmarks(sand,sandstone,rust,dark_rock,warm)
	flush_batches()
	var start_label := Label3D.new()
	start_label.text=track_name()+" / START"
	start_label.font_size=64
	start_label.pixel_size=0.009
	start_label.position=start+Vector3.UP*7.7
	start_label.rotation.y=angle
	add_child(start_label)


func build_harbor_details(concrete: Material, dark: Material, trim: Material, orange: Material, cyan: Material) -> void:
	# The first Harbor production pass uses existing material batches, no
	# additional dynamic lights, and scenery placed clear of the road envelope.
	var water := material("1b4352")
	water.roughness=0.35
	block(Vector3(-147,-0.12,0),Vector3(106,0.11,300),water)
	# Solid dock apron supports the containers and gantries; all are outside
	# the road barrier so they do not pretend to be navigable shortcuts.
	block(Vector3(-109,0.16,0),Vector3(20,0.33,160),concrete)
	for z in [-64.0,-43.0,43.0,64.0]:
		for level in range(2):
			var paint: Material=orange if (int(z)+level)%3==0 else trim
			block(Vector3(-109,1.25+2.15*level,z),Vector3(7.8,2.1,12.0),paint)
			for rib in range(4):
				block(Vector3(-104.98,1.25+2.15*level,z-4.5+rib*3.0),Vector3(0.08,1.8,0.17),dark)
	for z in [-57.0,57.0]:
		# Two recognizable dock cranes visible from the racing lane.
		block(Vector3(-131,13,z),Vector3(2.0,26.0,2.0),trim)
		block(Vector3(-121,26,z),Vector3(24.0,1.6,1.5),trim)
		block(Vector3(-115,16,z),Vector3(0.22,18.0,0.22),dark)
		block(Vector3(-115,6.5,z),Vector3(3.0,0.7,1.1),orange)
		block(Vector3(-131,26.6,z),Vector3(3.2,0.2,3.2),cyan)
	for z in [-53.0,-30.0,30.0,53.0]:
		# Refinery silhouettes on the opposite skyline.
		block(Vector3(120,9.0,z),Vector3(7.0,18.0,7.0),concrete)
		block(Vector3(120,18.3,z),Vector3(7.8,0.45,7.8),dark)
		block(Vector3(120,20.2,z),Vector3(1.0,4.0,1.0),trim)
	for i in [12,84,112,166]:
		var p := route[i]
		var forward := flat(route[(i+1)%COUNT]-p).normalized()
		var outward := outward_at(i)
		var base := p+outward*12.0
		block(base+Vector3.UP*5.0,Vector3(1.0,10.0,1.0),trim)
		block(base+Vector3.UP*10.1,Vector3(2.5,0.25,2.5),orange)
		district_sign("SHIPYARD / DANGER",base+Vector3.UP*7.2,forward,Color("ffb376"))

func build_street_detail(concrete: Material, dark: Material, trim: Material, orange: Material, cyan: Material, warm: Material) -> void:
	# Shared material batches: depth and readable silhouettes without extra lights.
	for index in range(0,COUNT,4):
		if index>=26 and index<=70 or index>=136 and index<=152:
			continue
		var p := route[index]
		var forward := flat(route[(index+1)%COUNT]-p).normalized()
		var normal := outward_at(index)
		var angle := atan2(forward.x,forward.z)
		var edge := p+normal*10.7
		block(edge-Vector3.UP*0.05,Vector3(3.0,0.25,3.0),concrete,angle)
		# Recessed drain and protective service bollards.
		block(edge-normal*0.8+Vector3.UP*0.09,Vector3(0.45,0.06,1.8),dark,angle)
		for rib in range(5):
			block(edge-normal*0.8+forward*(rib-2)*0.3+Vector3.UP*0.13,Vector3(0.4,0.025,0.06),trim,angle)
		if index%12==0:
			block(edge+Vector3.UP*1.7,Vector3(0.3,3.4,0.3),dark,angle)
			block(edge+Vector3.UP*3.2,Vector3(0.4,0.55,0.4),cyan if index<96 else warm,angle)
			block(edge+Vector3.UP*3.6,Vector3(0.65,0.12,0.65),trim,angle)
		else:
			block(edge+Vector3.UP*0.85,Vector3(0.8,1.7,0.5),dark,angle)
			block(edge-forward*0.28+Vector3.UP*1.15,Vector3(0.58,0.35,0.04),orange,angle)
	# Inner facades: inset window bands, mechanical panels and rooftop housings.
	for x in [-43.0,43.0]:
		for z in [-10.0,10.0]:
			var height := 12.0+(2.0 if z>0 else 0.0)
			for side in [-1.0,1.0]:
				for level in [3.0,6.0,9.0]:
					block(Vector3(x,level,z+side*4.05),Vector3(12,0.22,0.35),dark)
					for col in [-4.5,-1.5,1.5,4.5]:
						block(Vector3(x+col,level+1,z+side*4.03),Vector3(1.2,1.3,0.06),warm if int(col+level)%3==0 else trim)
			block(Vector3(x,height+0.7,z),Vector3(4,1.4,3),dark)
			for rib in range(6):
				block(Vector3(x-1.5+rib*0.6,height+1.43,z),Vector3(0.16,0.08,2.7),trim)

func build_map_polish(wall: Material, trim: Material, dark: Material, orange: Material, cyan: Material, warm: Material) -> void:
	# Skyline silhouettes and repeated facade shapes remain in material batches.
	for index in range(36):
		var a := TAU*index/36
		var p := Vector3(145*cos(a),0,108*sin(a))
		var height := 18.0+float((index*17)%31)
		block(p+Vector3.UP*height*0.5,Vector3(12,height,10),wall)
		block(p+Vector3.UP*(height+0.4),Vector3(13,0.8,11),dark)
		for level in range(5,int(height)-2,5):
			for side in [-1.0,1.0]:
				block(p+Vector3(0,level,side*5.03),Vector3(9,0.25,0.05),warm if index%3==0 else cyan)
		if index%3==0:
			block(p+Vector3.UP*(height+3),Vector3(0.16,6,0.16),trim)
			block(p+Vector3.UP*(height+6),Vector3(0.3,0.25,0.3),orange)
	# Give each district a different roadside silhouette; keep jumps clear.
	for index in range(4,COUNT,8):
		if index>=26 and index<=70 or index>=132 and index<=156:
			continue
		var p := route[index]
		var forward := flat(route[(index+1)%COUNT]-p).normalized()
		var outward := outward_at(index)
		var angle := atan2(forward.x,forward.z)
		var point := p+outward*13.0
		var sector := index/(COUNT/4)
		if sector==0:
			block(point+Vector3.UP*1.2,Vector3(2.2,2.4,1.4),dark,angle)
			for rib in range(5):
				block(point+forward*(rib-2)*0.24+Vector3.UP*2.45,Vector3(1.9,0.08,0.1),trim,angle)
		elif sector==1:
			block(point+Vector3.UP*2.4,Vector3(0.25,4.8,0.25),trim,angle)
			block(point+Vector3.UP*4.8,Vector3(2.5,1.2,0.2),dark,angle)
			block(point+Vector3.UP*4.8-forward*0.13,Vector3(2.2,0.7,0.05),cyan,angle)
		elif sector==2:
			for box in range(3):
				block(point+forward*(box-1)*1.1+Vector3.UP*0.55,Vector3(0.9,1.1,0.9),orange if box%2==0 else dark,angle)
		else:
			block(point+Vector3.UP*1.5,Vector3(0.5,3,0.5),dark,angle)
			block(point+Vector3.UP*3,Vector3(2.2,0.15,2.2),trim,angle)
			block(point+Vector3.UP*2.88,Vector3(1.6,0.04,1.6),warm,angle)
	# Lower facade storefront depth and awnings make the city feel inhabited.
	for index in range(28):
		if index in [11,12]:
			continue
		var p := outer_building_position(index)
		var toward := Vector3(-p.x,0,-p.z).normalized()
		var along := Vector3(toward.z,0,-toward.x)
		# Use axis-aligned building faces, so signs stay attached to the facade.
		var face := Vector3(signf(toward.x),0,0) if absf(toward.x)>absf(toward.z) else Vector3(0,0,signf(toward.z))
		var angle := atan2(face.x,face.z)
		var entry := p+face*6.1
		block(entry+Vector3.UP*1.4,Vector3(3,2.8,0.12),dark,angle)
		block(entry+face*0.65+Vector3.UP*3.1,Vector3(5.0,0.18,1.8),trim,angle)
		block(entry+face*0.12+Vector3.UP*3.65,Vector3(3.7,0.5,0.12),orange if index%3==0 else cyan,angle)
		for side in [-1.0,1.0]:
			block(entry+Vector3(face.z,0,-face.x)*side*2.5+Vector3.UP*1.1,Vector3(0.3,2.2,0.3),trim)

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
		var pos := outer_building_position(i)
		var height := rng.randf_range(11,27)
		# Leave an open parcel for the freight yard at the new lobe.
		if i in [11,12]:
			continue
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

func build_speed_effect() -> void:
	var args := OS.get_cmdline_user_args()
	# Keep existing fleet/build captures sharp unless explicitly testing blur.
	speed_vfx_enabled = not ("--no-speed-vfx" in args or ("--capture" in args and not "--capture-speed-vfx" in args))
	if not speed_vfx_enabled:
		return
	var layer := CanvasLayer.new()
	layer.name="SpeedRush"
	layer.layer=0
	add_child(layer)
	speed_blur_material=ShaderMaterial.new()
	speed_blur_material.shader=preload("res://effects/speed_rush.gdshader")
	speed_blur_rect=ColorRect.new()
	speed_blur_rect.name="PeripheralRush"
	speed_blur_rect.color=Color.WHITE
	speed_blur_rect.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	speed_blur_rect.mouse_filter=Control.MOUSE_FILTER_IGNORE
	speed_blur_rect.material=speed_blur_material
	speed_blur_rect.visible=false
	layer.add_child(speed_blur_rect)

func set_speed_effect_enabled(enabled: bool) -> void:
	if speed_blur_rect==null:
		return
	speed_vfx_enabled=enabled
	if not enabled:
		speed_blur_level=0.0
		speed_blur_rect.hide()
		if speed_reduced_resolution:
			speed_reduced_resolution=false
			get_viewport().scaling_3d_scale=BASE_3D_SCALE

func update_speed_effect(delta: float) -> void:
	if not speed_vfx_enabled:
		return
	var ratio := clampf(maxf(0.0,speed)/maxf(1.0,chassis.max_forward_speed),0.0,1.5)
	var target := smoothstep(0.35,0.97,ratio)
	if boost_active and ratio>0.45:
		target=maxf(target,0.50)
	if airborne and ratio>0.35:
		target=minf(1.0,target+0.13)
	speed_blur_level=lerpf(speed_blur_level,target,1.0-exp(-7.0*delta))
	var driving_visible := not (track_menu.visible or event_menu.visible or results_panel.visible or race_countdown>0.0)
	speed_blur_rect.visible=driving_visible and speed_blur_level>0.018
	if speed_blur_rect.visible:
		speed_blur_material.set_shader_parameter("intensity",speed_blur_level)
	# Lower pixel shading cost only once per threshold crossing. Hysteresis
	# prevents expensive resolution-buffer reallocations every physics frame.
	if ratio>=0.80 and not speed_reduced_resolution:
		speed_reduced_resolution=true
		get_viewport().scaling_3d_scale=RUSH_3D_SCALE
	elif ratio<=0.65 and speed_reduced_resolution:
		speed_reduced_resolution=false
		get_viewport().scaling_3d_scale=BASE_3D_SCALE

func build_ui() -> void:
	var layer := CanvasLayer.new()
	layer.name="DrivingUI"
	layer.layer=1  # Controls and telemetry remain sharp above the blur overlay.
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
	top.position = Vector2(-790,20)
	layer.add_child(top)
	ui_button(top,"VIEW",toggle_camera,100)
	sound_button = ui_button(top,"SOUND OFF",func():
		feedback.muted = not feedback.muted
		sound_button.text = "SOUND OFF" if feedback.muted else "SOUND ON",110)
	ui_button(top,"RESET",reset_car,100)
	ui_button(top,"TRACKS",open_tracks,105)
	ui_button(top,"EVENT",open_events,105)
	ui_button(top,"FLEET",func(): shutdown("res://fleet_hangar.tscn"),95)
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
	track_menu=ColorRect.new()
	track_menu.color=Color(0.025,0.055,0.085,0.98)
	track_menu.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	layer.add_child(track_menu)
	var menu_scroll := ScrollContainer.new()
	menu_scroll.position=Vector2(85,65)
	menu_scroll.size=Vector2(1120,605)
	track_menu.add_child(menu_scroll)
	var choices := VBoxContainer.new()
	choices.custom_minimum_size=Vector2(1065,0)
	choices.add_theme_constant_override("separation",9)
	menu_scroll.add_child(choices)
	var title := Label.new()
	title.text=chassis.display_name+" / CHOOSE YOUR CIRCUIT"
	title.add_theme_font_size_override("font_size",30)
	choices.add_child(title)
	# A separate physics scene, not a racer GLB or an unfinished Neon Foundry map.
	var proving_ground := Button.new()
	proving_ground.text="HOVER PHYSICS LAB / TRUE SURFACE PROBES + DRIFT + AIR CONTROL"
	proving_ground.custom_minimum_size=Vector2(1040,67)
	proving_ground.add_theme_font_size_override("font_size",23)
	proving_ground.pressed.connect(func(): shutdown("res://hover_lab.tscn"))
	choices.add_child(proving_ground)
	for index in [Skyfall.ID,0,1,2,3,4,5,6]:
		var choice := Button.new()
		choice.text=TRACK_NAMES[index]+"  /  "+TRACK_INFO[index]
		choice.custom_minimum_size=Vector2(1040,67)
		choice.add_theme_font_size_override("font_size",24)
		choice.pressed.connect(choose_track.bind(index))
		choices.add_child(choice)
	var resume := Button.new()
	resume.text="RESUME / "+track_name()
	resume.custom_minimum_size=Vector2(1040,63)
	resume.pressed.connect(resume_track)
	choices.add_child(resume)
	track_menu.hide()

	# Race setup is separate from track selection so existing free-drive and
	# circuit-record behavior remains backward compatible.
	event_menu=ColorRect.new()
	event_menu.color=Color(0.018,0.043,0.070,0.985)
	event_menu.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	layer.add_child(event_menu)
	var event_choices := VBoxContainer.new()
	event_choices.position=Vector2(110,95)
	event_choices.add_theme_constant_override("separation",14)
	event_menu.add_child(event_choices)
	var event_title := Label.new()
	event_title.text="NEON FOUNDRY / RACE WEEKEND"
	event_title.add_theme_font_size_override("font_size",34)
	event_choices.add_child(event_title)
	var event_note := Label.new()
	event_note.text="CHOOSE AN EVENT  ·  SOLO COMPETITION / AI RIVALS IN DEVELOPMENT"
	event_note.add_theme_font_size_override("font_size",18)
	event_choices.add_child(event_note)
	for option in [
		{"name":"FREE DRIVE", "detail":"Explore the selected circuit without a countdown", "mode":MODE_FREE},
		{"name":"TIME TRIAL", "detail":"Standing start / timed laps / personal bests", "mode":MODE_TIME_TRIAL},
		{"name":"SPRINT STAGE" if track_id==4 or track_id==Skyfall.ID else "3-LAP CHALLENGE", "detail":"Standing start / mountain ascent and full-air descent" if track_id==Skyfall.ID else ("Standing start / one long canyon stage" if track_id==4 else "Standing start / three laps / event classification"), "mode":MODE_SOLO_RACE}
	]:
		var button := Button.new()
		button.text=option["name"]+"   /   "+option["detail"]
		button.custom_minimum_size=Vector2(1020,88)
		button.add_theme_font_size_override("font_size",24)
		button.pressed.connect(begin_event.bind(int(option["mode"])))
		event_choices.add_child(button)
	# Phone-side A/B comparison: disable the effect without a rebuild.
	var speed_fx_button := Button.new()
	speed_fx_button.text="SPEED EFFECTS: ON  /  TAP TO COMPARE"
	speed_fx_button.custom_minimum_size=Vector2(1020,54)
	speed_fx_button.disabled=speed_blur_rect==null
	speed_fx_button.pressed.connect(func():
		set_speed_effect_enabled(not speed_vfx_enabled)
		speed_fx_button.text="SPEED EFFECTS: ON  /  TAP TO COMPARE" if speed_vfx_enabled else "SPEED EFFECTS: OFF  /  TAP TO COMPARE"
	)
	event_choices.add_child(speed_fx_button)
	# Compare real spring suspension and retained lateral momentum on the phone.
	var hover_mode_button := Button.new()
	hover_mode_button.text="HANDLING: HOVER PHYSICS / TAP FOR CLASSIC"
	hover_mode_button.custom_minimum_size=Vector2(1020,54)
	hover_mode_button.pressed.connect(func():
		hover_handling_enabled=not hover_handling_enabled
		hover_response.reset(car.position.y)
		hover_mode_button.text="HANDLING: HOVER PHYSICS / TAP FOR CLASSIC" if hover_handling_enabled else "HANDLING: CLASSIC / TAP FOR HOVER"
	)
	event_choices.add_child(hover_mode_button)
	var back := Button.new()
	back.text="RETURN TO CIRCUIT"
	back.custom_minimum_size=Vector2(1020,62)
	back.pressed.connect(func(): event_menu.hide(); set_physics_process(true))
	event_choices.add_child(back)
	event_menu.hide()

	results_panel=ColorRect.new()
	results_panel.color=Color(0.018,0.043,0.070,0.985)
	results_panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	layer.add_child(results_panel)
	var results_column := VBoxContainer.new()
	results_column.position=Vector2(110,55)
	results_column.add_theme_constant_override("separation",14)
	results_panel.add_child(results_column)
	results_info=Label.new()
	results_info.add_theme_font_size_override("font_size",25)
	results_column.add_child(results_info)
	for option in ["RACE AGAIN","TIME TRIAL","TRACKS","FOUNDRY GARAGE"]:
		var button := Button.new()
		button.text=option
		button.custom_minimum_size=Vector2(870,66)
		button.add_theme_font_size_override("font_size",22)
		if option=="RACE AGAIN":
			button.pressed.connect(begin_event.bind(MODE_SOLO_RACE))
		elif option=="TIME TRIAL":
			button.pressed.connect(begin_event.bind(MODE_TIME_TRIAL))
		elif option=="TRACKS":
			button.pressed.connect(open_tracks)
		else:
			button.pressed.connect(func(): shutdown("res://main.tscn"))
		results_column.add_child(button)
	results_panel.hide()

	countdown_label=Label.new()
	countdown_label.position=Vector2(475,170)
	countdown_label.size=Vector2(330,150)
	countdown_label.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER
	countdown_label.add_theme_font_size_override("font_size",100)
	countdown_label.add_theme_color_override("font_color",Color("ffca85"))
	layer.add_child(countdown_label)
	countdown_label.hide()

func reset_car() -> void:
	skyfall_trim=0.0
	skyfall_vertical_speed=0.0
	skyfall_gate_next=0
	car.position = route[0]
	hover_response.reset(car.position.y)
	route_index=0
	airborne=false
	vertical_speed=0
	air_time=0
	landing_kick=0
	jump_launches=0
	jump_landings=0
	jump_recoveries=0
	peak_height=0
	if hover_rings!=null:
		hover_rings.visible=true
		hover_rings.rotation=Vector3.ZERO
	var tangent := flat(route[1]-route[0]).normalized()
	heading = atan2(tangent.x,tangent.z)
	car.rotation = Vector3(0,heading,0)
	speed = 0.0
	speed_blur_level=0.0
	if speed_blur_rect!=null:
		speed_blur_rect.hide()
	if speed_reduced_resolution:
		speed_reduced_resolution=false
		get_viewport().scaling_3d_scale=BASE_3D_SCALE
	reverse_hold = 0.0
	travel_velocity = Vector3.ZERO
	steer = 0.0
	yaw_velocity = 0.0
	wall_cooldown=0.0
	wall_normal=Vector3.ZERO
	wall_recoil=Vector3.ZERO
	wall_hits=0
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
	race_elapsed=0.0
	race_splits.clear()
	race_finished=false
	race_go_flash=0.0
	race_countdown=3.0 if race_mode!=MODE_FREE else 0.0
	if countdown_label!=null:
		countdown_label.visible=race_countdown>0.0
		countdown_label.text="3" if race_countdown>0.0 else ""
	if results_panel!=null:
		results_panel.hide()

func toggle_camera() -> void:
	# The approved Shrike's painted glass is kept outside but detached for
	# cockpit view. Match the other craft's true eye-level camera position.
	cockpit = not cockpit
	near_chase=false
	feedback.set_cockpit(cockpit)

func closest_segment(pos: Vector3, cursor: int = -1) -> Dictionary:
	var distance := INF
	var result := {"point":route[0],"index":0}
	# Local continuity keeps crossing branches independent, including in mid-air.
	var search := COUNT if cursor<0 else 29
	for slot in range(search):
		var i := slot if cursor<0 else posmod(cursor+slot-14,COUNT)
		# This is a one-way stage: there is no invisible finish-to-start seam.
		if track_id==Skyfall.ID and i==COUNT-1:
			continue
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
	if track_id==Skyfall.ID:
		if checkpoint==0 and index>=Skyfall.FINISH_INDEX:
			checkpoint=1
			var record: bool=best==0.0 or lap_time<best
			if record and lap_time>0.0:
				best=lap_time
				save_best()
			lap_banner.text="SKYFALL RUN COMPLETE / %.1f s"%lap_time
			banner_time=4.0
			if race_mode==MODE_SOLO_RACE:
				race_splits.append(lap_time)
				finish_solo_race()
			else:
				hud.text="SKYFALL RUN / FINISH\n%.1f s  /  REPLAY: RESET"%lap_time
				race_finished=true
				clear_drive_input()
		return
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
			if lap_time>0.0:
				save_best()
		if race_mode==MODE_SOLO_RACE and not race_finished:
			race_splits.append(lap_time)
		lap+=1
		lap_time=0
		checkpoint=0
		if race_mode==MODE_SOLO_RACE and race_splits.size()>=challenge_laps():
			finish_solo_race()

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		throttle=false
		brake=false
		boost=false
		left=false
		right=false
		driving_touches.clear()

func _input(event: InputEvent) -> void:
	if track_menu.visible or event_menu.visible or results_panel.visible or race_countdown>0.0:
		return
	var screen := get_viewport().get_visible_rect().size
	if event is InputEventScreenTouch:
		if event.pressed and HoverTouchInput.is_drive_area(event.position,screen):
			driving_touches[event.index] = event.position
		elif not event.pressed:
			driving_touches.erase(event.index)
		else:
			return
	elif event is InputEventScreenDrag and driving_touches.has(event.index):
		driving_touches[event.index] = event.position
	else:
		return
	var decoded: Dictionary=HoverTouchInput.decode(driving_touches,screen)
	left=bool(decoded["left"])
	right=bool(decoded["right"])
	throttle=bool(decoded["throttle"])
	brake=bool(decoded["brake"])
	boost=bool(decoded["boost"])
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

func update_skyfall_flight(delta: float, surface_height: float) -> float:
	var crossing: bool = route_index>=Skyfall.GAP_START and route_index<Skyfall.GAP_END
	var dive: bool = route_index>=Skyfall.FLIGHT_START and route_index<Skyfall.FLIGHT_END
	if crossing or dive:
		if not airborne:
			airborne=true
			air_time=0.0
			skyfall_vertical_speed=0.0
			jump_launches+=1
			if dive and speed>6.0:
				# The summit transitions to a fast powered dive, not a slow coast.
				speed=maxf(speed,chassis.max_forward_speed*1.06)
		air_time+=delta
		if crossing:
			# A gentle first reveal: glide across genuine open space.
			car.position.y=lerpf(car.position.y,surface_height+3.0,clampf(delta*2.8,0.0,1.0))
			skyfall_trim=move_toward(skyfall_trim,0.0,delta*10.0)
		else:
			# Assisted descent with meaningful lateral and limited vertical control.
			# Boost trims upward; brake trims downward, preserving phone controls.
			var input_trim: float=24.0 if boost_active else (-20.0 if brake else 0.0)
			skyfall_trim=move_toward(skyfall_trim,input_trim,delta*13.0)
			var target_height: float=surface_height+8.0+skyfall_trim
			# Smooth vertical response trails the contour instead of snapping
			# the vehicle to a camera-invisible altitude spline each frame.
			var descent_target: float=clampf((target_height-car.position.y)*1.15,-58.0,28.0)
			skyfall_vertical_speed=move_toward(skyfall_vertical_speed,descent_target,delta*48.0)
			car.position.y+=skyfall_vertical_speed*delta
			car.position.y=clampf(car.position.y,target_height-17.0,target_height+26.0)
		peak_height=maxf(peak_height,car.position.y)
	else:
		if airborne:
			jump_landings+=1
			landing_kick=0.04
			lap_banner.text="FLIGHT CORRIDOR CLEARED / %.1f s"%air_time
			banner_time=2.8
			airborne=false
			air_time=0.0
		car.position.y=surface_height
		skyfall_vertical_speed=0.0
		skyfall_trim=move_toward(skyfall_trim,0.0,delta*20.0)
	if hover_rings!=null:
		hover_rings.visible=not airborne
		hover_rings.rotation.x=0.0
	if dive:
		var p: Vector3=route[route_index]
		var q: Vector3=route[mini(route_index+1,COUNT-1)]
		var downhill: float=maxf(0.0,p.y-q.y)/maxf(1.0,flat(q-p).length())
		return -clampf(0.10+downhill*0.20,0.10,0.24)
	return 0.0

func update_skyfall_gates() -> void:
	if skyfall_gate_next>=Skyfall.FlightWorld.GATES.size():
		return
	var gate_index: int=Skyfall.FlightWorld.GATES[skyfall_gate_next]
	if route_index<gate_index:
		return
	var target: Vector3=Skyfall.FlightWorld.flight_gate_center(route,skyfall_gate_next)
	var offset: Vector3=car.position-target
	var sideways: Vector3=Skyfall.FlightWorld.right(route,gate_index)
	var radius: float=Vector2(offset.dot(sideways),offset.y).length()
	var passed: bool=radius<40.5
	if passed:
		boost_energy=minf(100.0,boost_energy+7.0)
		lap_banner.text="AERIAL GATE %d / %d  ·  CLEAN LINE" % [skyfall_gate_next+1,Skyfall.FlightWorld.GATES.size()]
	else:
		lap_banner.text="AERIAL GATE %d / %d  ·  OFF LINE" % [skyfall_gate_next+1,Skyfall.FlightWorld.GATES.size()]
	banner_time=1.9
	skyfall_gate_next+=1

func update_jump(delta: float, surface_height: float) -> float:
	if track_id==Skyfall.ID:
		return update_skyfall_flight(delta,surface_height)
	var p := route[route_index]
	var q := route[(route_index+1)%COUNT]
	var ramp_pitch := -atan2(q.y-p.y,flat(q-p).length())
	if not airborne and is_jump_gap(route_index):
		airborne=true
		air_time=0
		vertical_speed=8.0 if track_id==2 else 6.5
		car.position.y=maxf(car.position.y,deck_height(jump_start_index()))
		var route_forward := flat(q-p).normalized()
		if travel_velocity.dot(route_forward)>0.2 and speed>0:
			speed=maxf(speed,34.0 if track_id==2 else 30.0)
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
			lap_banner.text="JUMP CLEARED / %.1f s AIR"%air_time
			banner_time=2
		elif car.position.y < -0.7 or air_time>3:
			recover_jump()
	else:
		car.position.y=surface_height
	if hover_rings!=null:
		hover_rings.visible=not airborne
		hover_rings.rotation.x=ramp_pitch if not airborne else 0.0
	return -clampf(vertical_speed*0.012,-0.085,0.085) if airborne else ramp_pitch

func recover_jump() -> void:
	jump_recoveries+=1
	wall_cooldown=0.0
	wall_normal=Vector3.ZERO
	wall_recoil=Vector3.ZERO
	route_index=36
	car.position=route[36]
	var tangent := flat(route[37]-route[36]).normalized()
	heading=atan2(tangent.x,tangent.z)
	speed=0
	yaw_velocity=0.0
	travel_velocity=Vector3.ZERO
	vertical_speed=0
	airborne=false
	landing_kick=0
	lap_banner.text="JUMP RESET / FOLLOW THE LAUNCH MARKERS"
	banner_time=3

func prepare_jump_capture() -> void:
	if track_id==Skyfall.ID:
		set_physics_process(false)
		route_index=Skyfall.GAP_START
		car.position=route[route_index]
		var approach: Vector3=flat(route[route_index+1]-route[route_index]).normalized()
		heading=atan2(approach.x,approach.z)
		car.rotation.y=heading
		speed=32.0
		airborne=true
		air_time=0.6
		car.position.y+=2.5
		update_camera(1.0)
		hud.text="SKYFALL RUN / BRIDGE REVEAL\nHOVER GLIDE / OPEN AIR"
		return
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
	hud.text=track_name()+" / JUMP\nD %03d KM/H\nAIRBORNE / %.1f s"%[int(speed*3.6),air_time]

func _physics_process(delta: float) -> void:
	if race_finished or track_menu.visible or event_menu.visible or results_panel.visible:
		return
	if race_mode!=MODE_FREE and advance_countdown(delta):
		return
	if race_mode!=MODE_FREE:
		race_elapsed+=delta
	var boost_requested := boost or Input.is_physical_key_pressed(KEY_SHIFT)
	var gas := throttle or boost_requested or Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP)
	var stopping := brake or Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN)
	var turn := float(right or Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT))-float(left or Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT))
	var skyfall_dive: bool=track_id==Skyfall.ID and route_index>=Skyfall.FLIGHT_START and route_index<Skyfall.FLIGHT_END
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
			var limit: float = chassis.max_forward_speed + (chassis.boost_speed_bonus if boost_active else 0.0) + (12.0 if skyfall_dive else 0.0)
			var push: float = chassis.acceleration * (chassis.boost_acceleration_multiplier if boost_active else 1.0) * ((0.72 if skyfall_dive else 0.25) if airborne else 1.0)
			speed = move_toward(speed,limit,(push if speed < limit else 5.0)*delta)
	else:
		reverse_hold = 0.0
		speed = move_toward(speed,0,chassis.coast_drag*(0.30 if skyfall_dive and airborne else 1.0)*delta)
	update_steering(delta)
	var forward := Vector3(sin(heading),0,cos(heading))
	var speed_ratio := clampf(absf(speed)/chassis.max_forward_speed,0,1)
	var grip: float = chassis.lateral_grip*lerpf(1.0,0.65,speed_ratio)*((0.70 if track_id==Skyfall.ID else 0.45) if airborne else 1.0)
	wall_cooldown=maxf(0,wall_cooldown-delta)
	var desired_velocity := forward*speed
	if wall_cooldown>0:
		desired_velocity-=wall_normal*maxf(0,desired_velocity.dot(wall_normal))
	if hover_handling_enabled:
		travel_velocity=HoverMotion.horizontal_velocity(travel_velocity,forward,speed,grip,delta,airborne)
	else:
		travel_velocity = travel_velocity.lerp(desired_velocity,1-exp(-grip*delta))
	car.position += (travel_velocity+wall_recoil)*delta
	wall_recoil=wall_recoil.lerp(Vector3.ZERO,1-exp(-8.0*delta))
	var nearest := closest_segment(car.position,route_index)
	route_index=int(nearest["index"])
	var center: Vector3 = nearest["point"]
	var offset := flat(car.position-center)
	resolve_wall(center,road_half_width(route_index)-2.0)
	if track_id==Skyfall.ID and route_index>45 and route_index<121 and not airborne:
		for obstacle in skyfall_hazards:
			var separation: Vector3=flat(car.position-obstacle)
			if absf(car.position.y-obstacle.y)<8.0 and separation.length_squared()<42.25:
				var bounce: Vector3=separation.normalized() if separation.length_squared()>0.001 else Vector3.RIGHT
				car.position+=bounce*1.0
				speed*=0.74
				travel_velocity=travel_velocity.slide(bounce)*0.8
				break
	offset=flat(car.position-center)
	var road_forward := flat(route[(route_index+1)%COUNT]-route[route_index]).normalized()
	var road_right := Vector3(road_forward.z,0,-road_forward.x)
	var bank := bank_slope(route_index)
	var surface_height: float=center.y+offset.dot(road_right)*bank
	var was_airborne := airborne
	var surface_pitch := update_jump(delta,surface_height)
	if hover_handling_enabled:
		if airborne:
			hover_response.reset(car.position.y)
		else:
			if was_airborne:
				hover_response.reset(car.position.y)
			car.position.y=hover_response.follow_surface(delta,surface_height,speed)
	if track_id==Skyfall.ID and route_index>=Skyfall.FLIGHT_START and route_index<Skyfall.FLIGHT_END:
		update_skyfall_gates()
	if hover_rings!=null:
		hover_rings.rotation.z=atan(bank) if not airborne else 0.0
	car.rotation = Vector3(0,heading,0)
	var side := Vector3(forward.z,0,-forward.x)
	var slip := clampf(absf(travel_velocity.dot(side))/maxf(absf(speed),1),0,1)
	feedback.update_feedback(delta,speed,1.0 if gas and not stopping else (0.35 if speed < -0.1 and stopping else 0.0),steer,(speed-previous_speed)/maxf(delta,0.001),slip,cockpit,boost_active,boost_energy,surface_pitch)
	landing_kick=move_toward(landing_kick,0,delta*0.3)
	feedback.position.y-=landing_kick
	if not airborne:
		feedback.rotation.z+=atan(bank)
	if race_mode!=MODE_FREE or absf(speed)>0.1:
		lap_running=true
	if lap_running:
		lap_time += delta
	banner_time=maxf(0,banner_time-delta)
	lap_banner.visible=banner_time > 0
	lap_banner.modulate.a=minf(1,banner_time*2)
	if speed > 0.1:
		track_progress(nearest["index"])
	update_camera(delta)
	update_speed_effect(delta)
	boost_button.text = "%s / %03d%%" % ["BOOST" if not boost_locked else "RECHARGING",int(boost_energy)]
	if not race_finished:
		var event_name := "FREE DRIVE" if race_mode==MODE_FREE else ("TIME TRIAL" if race_mode==MODE_TIME_TRIAL else ("SPRINT STAGE" if track_id==4 or track_id==Skyfall.ID else "3-LAP CHALLENGE"))
		hud.text = track_name()+" / "+event_name+" / LAP %d\n%s %03d KM/H  ·  %.1f s\nBEST %s  ·  %d FPS\n%s" % [lap,"R" if speed < -0.05 else "D",int(absf(speed)*3.6),lap_time,"—" if best==0 else "%.1f s"%best,Engine.get_frames_per_second(),("AIRBORNE / %.1f s"%air_time) if airborne else region_name(int(nearest["index"]))]
		if track_id==Skyfall.ID:
			hud.text+="\n"+skyfall_renderer_label

func resolve_wall(center: Vector3, limit: float) -> void:
	var offset := flat(car.position-center)
	if offset.length()<=limit:
		return
	var outward := offset.normalized()
	var incoming := maxf(0,travel_velocity.dot(outward))
	var bounded := center+outward*(limit-0.12)
	car.position.x=bounded.x
	car.position.z=bounded.z
	# Remove only motion into the barrier: tangent motion survives the impact.
	travel_velocity-=outward*incoming
	if wall_cooldown<=0 and incoming>0.25:
		wall_hits+=1
		wall_normal=outward
		wall_cooldown=0.28
		wall_recoil=-outward*clampf(incoming*0.30,1.3,4.5)
		var severity := clampf(incoming/maxf(absf(speed),1.0),0,1)
		speed*=lerpf(0.98,0.15,severity*severity)

func update_steering(delta: float) -> void:
	# Short yaw spool gives weight; countersteer and release settle promptly.
	var ratio := clampf(absf(speed)/chassis.max_forward_speed,0,1)
	var authority := lerpf(1.0,0.90,ratio)
	var target: float = -steer*chassis.yaw_rate*clampf(speed/8,-1,1)*authority*((0.68 if track_id==Skyfall.ID else 0.3) if airborne else 1.0)
	var response := 8.0 if airborne else (11.0 if absf(steer)<0.1 or target*yaw_velocity<0 else 7.0)
	yaw_velocity=lerpf(yaw_velocity,target,1-exp(-response*delta))
	if absf(speed)<0.05:
		yaw_velocity=0.0
	heading+=yaw_velocity*delta

func update_camera(delta: float) -> void:
	camera.fov = lerpf(camera.fov,74.0+clampf(absf(speed)/chassis.max_forward_speed,0,1)*7.0+(3.0 if boost_active else 0.0),1-exp(-delta*3))
	if cockpit:
		camera.global_transform = feedback.global_transform*Transform3D(Basis.from_euler(Vector3(chassis.cockpit_pitch,PI,0)),chassis.cockpit_eye)
	else:
		var diving: bool=track_id==Skyfall.ID and route_index>=Skyfall.FLIGHT_START and route_index<Skyfall.FLIGHT_END
		var desired := car.to_global(Vector3(0,5.6,-9.6) if diving else (Vector3(0,2.8,-5.65) if near_chase else Vector3(0,3.6,-8.5)))
		camera.position = camera.position.lerp(desired,1-exp(-delta*6))
		camera.look_at(car.to_global(Vector3(0,-5.5,23.0) if diving else (Vector3(0,1.05,3.3) if near_chase else Vector3(0,1.15,4))))

func _process(_delta: float) -> void:
	if "--capture" in OS.get_cmdline_user_args():
		capture_frames+=1
		if capture_frames==35:
			var file := "NeonLoop-cockpit.png" if cockpit else ("NeonLoop-action.png" if "--track-action" in OS.get_cmdline_user_args() else "NeonLoop-track.png")
			if "--track-jump" in OS.get_cmdline_user_args():
				file="NeonCross-jump-cockpit.png" if cockpit else "NeonCross-jump.png"
			if "--track-overview" in OS.get_cmdline_user_args():
				file="NeonLoop-overview.png"
			if track_id>0:
				var circuit_prefix: String = ["NeonLoop","Skyway","ViperRift","IronHarbor","CrimsonSerpent","RedMesa","DevilsGate","SkyfallRun"][track_id]
				file=circuit_prefix+("-overview.png" if "--track-overview" in OS.get_cmdline_user_args() else ("-jump.png" if "--track-jump" in OS.get_cmdline_user_args() else "-cockpit.png"))
			if track_id==Skyfall.ID:
				for flight_index in [140,167]:
					if "--track-flight-%d" % flight_index in OS.get_cmdline_user_args():
						file="SkyfallRun-flight-%d.png"%flight_index
						break
			if track_id==4:
				for landmark in [14,75,155]:
					if "--track-landmark-%d" % landmark in OS.get_cmdline_user_args():
						file="CrimsonSerpent-landmark-%d.png" % landmark
						break
			if "--track-menu" in OS.get_cmdline_user_args():
				file="Circuit-select.png"
			if chassis.chassis_id in ["shrike","aerolith"] and "--track-action" in OS.get_cmdline_user_args():
				file="NeonLoop-"+chassis.chassis_id+"-driving.png"
			get_viewport().get_texture().get_image().save_png(OS.get_environment("GITHUB_WORKSPACE")+"/build/"+file)
			shutdown()

func test_loop() -> void:
	# The blur is dormant while stationary. A high-speed sample must activate
	# both peripheral rush and a lower-cost 3D buffer, then recover at rest.
	if speed_vfx_enabled:
		speed=chassis.max_forward_speed
		update_speed_effect(1.0)
		assert(speed_blur_rect.visible and speed_reduced_resolution)
		speed=0.0
		update_speed_effect(1.0)
		assert(not speed_blur_rect.visible and not speed_reduced_resolution)
		reset_car()
		print("SCENEFORGE_SPEED_VFX_OK")
	# Steering settles consistently at different simulation rates.
	var headings: Array[float] = []
	for hz in [30,60,120]:
		heading=0.0
		yaw_velocity=0.0
		steer=1.0
		speed=32.0
		for tick in range(hz):
			update_steering(1.0/hz)
		assert(yaw_velocity < -0.9 and yaw_velocity > -1.2)
		headings.append(heading)
		steer=0.0
		for tick in range(hz):
			update_steering(1.0/hz)
		assert(absf(yaw_velocity)<0.001, "Release must settle yaw")
	assert(absf(headings[0]-headings[2])<0.03, "Yaw must remain stable across tick rates")
	reset_car()
	print("SCENEFORGE_STEERING_OK")
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

# Called only after the persistent loading screen has covered scene creation
# and initial Mobile/Vulkan pipeline warm-up. Race clocks remain frozen until now.
func finish_track_load() -> void:
	clear_drive_input()
	set_physics_process(not (track_menu.visible or event_menu.visible or results_panel.visible))

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
		if next_scene == "res://city_loop.tscn":
			TrackLoader.begin(next_scene)
		else:
			get_tree().change_scene_to_file(next_scene)


