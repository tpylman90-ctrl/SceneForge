extends SceneTree

# Race event state regression. Physics/circuit geometry are covered separately
# by circuits_test.gd; these checks focus on race lifecycle and persistence.
func _initialize() -> void:
	call_deferred("check")

func check() -> void:
	set_meta("sceneforge_track",0)
	set_meta("sceneforge_race_mode",0)
	var scene: Node3D=load("res://city_loop.tscn").instantiate()
	root.add_child(scene)
	scene.set_physics_process(false)
	assert(scene.race_mode==scene.MODE_FREE)
	assert(not scene.event_menu.visible)
	assert(not scene.results_panel.visible)
	assert(scene.race_countdown==0.0)
	scene.open_events()
	assert(scene.event_menu.visible and not scene.is_physics_processing())
	scene.begin_event(scene.MODE_SOLO_RACE)
	scene.set_physics_process(false)
	assert(scene.race_mode==scene.MODE_SOLO_RACE)
	assert(scene.race_countdown==3.0 and scene.lap==1)
	assert(not scene.event_menu.visible)
	scene.throttle=true
	scene._physics_process(1.0/60.0)
	assert(scene.speed==0.0 and scene.race_elapsed==0.0,"Countdown must lock thrust and race clock")
	scene.throttle=false
	for tick in range(190):
		scene._physics_process(1.0/60.0)
	assert(scene.race_countdown==0.0)
	scene._physics_process(1.0/60.0)
	assert(scene.race_elapsed>0.0 and scene.lap_running)
	for lap_index in range(scene.RACE_LAPS):
		scene.lap_time=12.0+lap_index
		for gate in [scene.COUNT/4,scene.COUNT/2,scene.COUNT*3/4,0]:
			scene.track_progress(int(gate))
	assert(scene.race_finished,"Third complete lap should end challenge")
	assert(scene.race_splits.size()==3)
	assert(is_equal_approx(scene.race_splits[0],12.0))
	assert(is_equal_approx(scene.race_splits[2],14.0))
	assert(is_equal_approx(scene.race_best_total,39.0) or scene.race_best_total<39.0)
	assert(scene.results_panel.visible and not scene.is_physics_processing())
	assert(scene.results_info.text.contains("3-LAP SOLO CHALLENGE COMPLETE"))
	scene.throttle=true
	var finish_speed: float=scene.speed
	scene._physics_process(1.0/60.0)
	assert(scene.speed==finish_speed,"Race must not keep driving after finish")
	scene.begin_event(scene.MODE_TIME_TRIAL)
	scene.set_physics_process(false)
	assert(scene.race_mode==scene.MODE_TIME_TRIAL and not scene.race_finished)
	assert(scene.race_splits.is_empty() and scene.race_countdown>0.0)
	assert(not scene.results_panel.visible)
	scene.begin_event(scene.MODE_FREE)
	scene.set_physics_process(false)
	assert(scene.race_countdown==0.0 and scene.lap==1)
	assert(scene.race_mode==scene.MODE_FREE)
	scene.feedback.stop_audio()
	scene.free()
	print("RACE_EVENT_LIFECYCLE_OK")
	quit()
