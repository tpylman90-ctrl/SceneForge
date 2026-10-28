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
	for circuit in range(3):
		set_meta("sceneforge_track",circuit)
		var scene: Node3D=load("res://city_loop.tscn").instantiate()
		root.add_child(scene)
		scene.set_physics_process(false)
		assert(scene.track_id==circuit)
		for hz in [30,60,120]:
			scene.reset_car()
			scene.throttle=true
			for frame in range(hz*55):
				drive(scene,hz)
				if scene.lap>1:break
			assert(scene.lap==2 and scene.jump_launches==1 and scene.jump_landings==1 and scene.jump_recoveries==0,"Circuit lap or jump failed")
			print("CIRCUIT_LAP_OK ",circuit," / ",hz)
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
			assert(scene.jump_landings==1 and scene.jump_recoveries==0,"Circuit low-speed jump failed")
			print("CIRCUIT_JUMP_OK ",circuit," / ",initial_speed)
		scene.prepare_jump_capture()
		assert(scene.airborne and not scene.hover_rings.visible)
		scene.open_tracks()
		assert(scene.track_menu.visible and not scene.is_physics_processing() and not scene.throttle)
		if circuit==1:
			assert(scene.route[0].y==2.0 and scene.route[48].z>37)
		if circuit==2:
			assert(absf(scene.bank_slope(16))>0.08 and scene.route[112].y>2.9)
		scene.feedback.stop_audio()
		scene.free()
	# Actual menu selection must tear down and create the requested circuit.
	set_meta("sceneforge_track",0)
	var previous: Node3D=load("res://city_loop.tscn").instantiate()
	root.add_child(previous)
	current_scene=previous
	previous.choose_track(2)
	await create_timer(0.3).timeout
	assert(current_scene.track_id==2 and current_scene.track_menu.visible==false)
	current_scene.set_physics_process(false)
	current_scene.feedback.stop_audio()
	print("CIRCUIT_SWITCH_OK")
	print("CIRCUITS_OK")
	quit()
