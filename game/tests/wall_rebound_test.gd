extends SceneTree
func _initialize() -> void:
	call_deferred("check")
func check() -> void:
	var scene: Node3D=load("res://city_loop.tscn").instantiate()
	root.add_child(scene)
	scene.set_physics_process(false)
	# Glancing collision retains tangent velocity and gives an inward impulse.
	scene.reset_car()
	scene.speed=30
	scene.travel_velocity=Vector3(6,0,28)
	scene.car.position=Vector3(6.2,0,0)
	scene.resolve_wall(Vector3.ZERO,6)
	assert(absf(scene.travel_velocity.x)<0.001 and scene.travel_velocity.z==28)
	assert(scene.wall_recoil.x< -1.0 and scene.speed>27)
	assert(scene.car.position.x<6 and scene.wall_hits==1)
	# Cooldown prevents repeated impulses and repeated speed loss while scraping.
	var after: float=scene.speed
	scene.car.position.x=6.1
	scene.travel_velocity=Vector3(4,0,28)
	scene.resolve_wall(Vector3.ZERO,6)
	assert(scene.speed==after and scene.wall_hits==1)
	# Head-on hit sheds speed but never flips the selected drive direction.
	scene.reset_car()
	scene.speed=30
	scene.travel_velocity=Vector3(30,0,0)
	scene.car.position=Vector3(6.2,0,0)
	scene.resolve_wall(Vector3.ZERO,6)
	assert(scene.speed>0 and scene.speed<6 and scene.wall_recoil.x== -4.5)
	assert(scene.travel_velocity.length()<0.001)
	scene.reset_car()
	scene.speed=-8
	scene.travel_velocity=Vector3(-8,0,0)
	scene.car.position=Vector3(-6.2,0,0)
	scene.resolve_wall(Vector3.ZERO,6)
	assert(scene.speed<0 and scene.wall_recoil.x>0)
	# Resolving an overshoot while already moving away adds no spurious hit.
	scene.reset_car()
	scene.speed=10
	scene.travel_velocity=Vector3(-2,0,9)
	scene.car.position=Vector3(6.2,0,0)
	scene.resolve_wall(Vector3.ZERO,6)
	assert(scene.wall_hits==0 and scene.wall_recoil==Vector3.ZERO)
	# Recovery works through the actual controller, independent of tick rate.
	for hz in [30,60,120]:
		scene.reset_car()
		var near: Dictionary=scene.closest_segment(scene.route[0],0)
		var tangent: Vector3=scene.flat(scene.route[1]-scene.route[0]).normalized()
		var normal := Vector3(tangent.z,0,-tangent.x)
		scene.car.position=near["point"]+normal*6.15
		scene.heading=atan2(tangent.x,tangent.z)
		scene.speed=30
		scene.travel_velocity=tangent*28+normal*6
		scene.throttle=true
		for tick in range(hz/4):
			scene._physics_process(1.0/hz)
		assert(scene.wall_hits==1 and scene.speed>24,"Glancing impact should continue sliding")
		assert(scene.wall_recoil.dot(normal)<0)
		print("WALL_GLANCE_OK ",hz," Hz / speed=",scene.speed)
	scene.feedback.stop_audio()
	print("WALL_REBOUND_OK")
	quit()
