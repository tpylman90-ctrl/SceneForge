extends SceneTree
func _initialize() -> void:
	call_deferred("check")
func drive(scene: Node3D, hz: int) -> void:
	var near: Dictionary=scene.closest_segment(scene.car.position,scene.route_index)
	var target: Vector3=scene.route[(int(near["index"])+4)%scene.COUNT]
	var offset: Vector3=target-scene.car.position
	var error := wrapf(atan2(offset.x,offset.z)-scene.heading,-PI,PI)
	scene.left=error>0.015
	scene.right=error< -0.015
	scene._physics_process(1.0/hz)
func check() -> void:
	var scene: Node3D=load("res://city_loop.tscn").instantiate()
	root.add_child(scene)
	scene.set_physics_process(false)
	assert(scene.flat(scene.route[48]-scene.route[144]).length()<0.001)
	assert(scene.route[48].y-scene.route[144].y>4)
	assert(abs(int(scene.closest_segment(Vector3(0,5,0),48)["index"])-48)<=1)
	assert(abs(int(scene.closest_segment(Vector3(0,0,0),144)["index"])-144)<=1)
	for hz in [30,60,120]:
		scene.reset_car()
		scene.throttle=true
		var checked_lower := false
		for frame in range(hz*40):
			drive(scene,hz)
			if scene.route_index>=142 and scene.route_index<=146:
				checked_lower=true
				assert(not scene.airborne and scene.jump_launches==1)
			if scene.lap>1:break
		assert(scene.lap==2 and scene.jump_launches==1 and scene.jump_landings==1 and scene.jump_recoveries==0)
		assert(scene.peak_height>5 and checked_lower)
		print("FIGURE8_LAP_OK ",hz," Hz / peak=",scene.peak_height)
	for initial_speed in [8.0,32.0,42.0]:
		scene.reset_car()
		scene.route_index=43
		scene.car.position=scene.route[43]
		var direction: Vector3=scene.flat(scene.route[44]-scene.route[43]).normalized()
		scene.heading=atan2(direction.x,direction.z)
		scene.speed=initial_speed
		scene.travel_velocity=direction*initial_speed
		for frame in range(240):
			drive(scene,60)
			if scene.jump_landings>0:break
		assert(scene.jump_landings==1 and scene.jump_recoveries==0)
		print("FIGURE8_JUMP_OK speed=",initial_speed," air=",scene.air_time)
	scene.prepare_jump_capture()
	assert(scene.airborne and not scene.hover_rings.visible)
	print("FIGURE8_CAPTURE_OK")
	scene.route_index=48
	scene.airborne=true
	scene.car.position=Vector3(0,-1,0)
	scene.vertical_speed=-5
	scene.update_jump(1.0/60,4.2)
	assert(scene.jump_recoveries==1 and scene.route_index==36 and not scene.airborne and scene.speed==0)
	print("FIGURE8_RECOVERY_OK")
	scene.feedback.stop_audio()
	quit()
