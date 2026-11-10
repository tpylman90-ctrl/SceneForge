extends SceneTree

const Skyfall = preload("res://tracks/skyfall_run.gd")

func _initialize() -> void:
	call_deferred("check")

func check() -> void:
	var points: PackedVector3Array=Skyfall.route_points()
	assert(points.size()==Skyfall.COUNT)
	assert(absf(points[0].y-42.0)<0.05)
	assert(absf(points[Skyfall.COUNT-1].y-52.0)<0.05)
	var summit: float=0.0
	var traveled: float=0.0
	for i in range(points.size()-1):
		summit=maxf(summit,points[i].y)
		var step: float=points[i].distance_to(points[i+1])
		assert(step>3.0 and step<36.0,"Skyfall spline sampling should be continuous")
		traveled+=step
	assert(summit>420.0 and summit<455.0,"Missing dramatic mountain summit")
	assert(traveled>2900.0 and traveled<3800.0,"One-way stage length outside target")
	assert(Skyfall.GAP_END-Skyfall.GAP_START>=3)
	assert(Skyfall.FLIGHT_END-Skyfall.FLIGHT_START>45)
	assert(Skyfall.half_width(75)>Skyfall.half_width(5))
	assert(Skyfall.half_width(160)>Skyfall.half_width(75))
	set_meta("sceneforge_track",Skyfall.ID)
	set_meta("sceneforge_race_mode",0)
	var scene: Node3D=load("res://city_loop.tscn").instantiate()
	root.add_child(scene)
	scene.set_physics_process(false)
	assert(scene.track_id==Skyfall.ID)
	assert(scene.route.size()==Skyfall.COUNT)
	assert(scene.challenge_laps()==1)
	assert(scene.get_node_or_null("SkyfallDriveSurface")!=null)
	assert(scene.get_node_or_null("SculptedMountainRibbons")!=null)
	assert(scene.get_node_or_null("InstancedPineCanopies")!=null)
	assert(scene.get_node_or_null("SlalomBoulders")!=null)
	assert(scene.get_node_or_null("LowlandBase")!=null)
	assert(scene.skyfall_hazards.size()>=4)
	# The reveal must not secretly have a road or replace its hovercraft.
	var surface: MeshInstance3D=scene.get_node("SkyfallDriveSurface")
	assert(surface.mesh.get_surface_count()==1)
	scene.route_index=Skyfall.GAP_START
	scene.car.position=points[Skyfall.GAP_START]
	scene.update_jump(1.0/60.0,scene.car.position.y)
	assert(scene.airborne and scene.jump_launches==1)
	scene.route_index=Skyfall.GAP_END+1
	scene.update_jump(1.0/60.0,points[Skyfall.GAP_END+1].y)
	assert(not scene.airborne and scene.jump_landings==1)
	scene.route_index=Skyfall.FLIGHT_START+2
	scene.car.position=points[Skyfall.FLIGHT_START+2]
	scene.update_jump(1.0/60.0,scene.car.position.y)
	assert(scene.airborne and scene.jump_launches==2)
	var lower: float=scene.skyfall_trim
	scene.boost_active=true
	scene.update_jump(0.4,points[Skyfall.FLIGHT_START+2].y)
	assert(scene.skyfall_trim>lower,"Boost should lift the free-air trim")
	scene.route_index=Skyfall.FLIGHT_END+1
	scene.update_jump(0.1,points[Skyfall.FLIGHT_END+1].y)
	assert(not scene.airborne and scene.jump_landings==2)
	scene.lap_time=115.0
	scene.track_progress(Skyfall.FINISH_INDEX)
	assert(scene.race_finished and scene.checkpoint==1)
	scene.feedback.stop_audio()
	scene.free()
	print("SKYFALL_ROUTE_FLIGHT_OK length=%.1f summit=%.1f obstacles=%d"%[traveled,summit,8])
	quit()
