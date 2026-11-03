extends SceneTree

const Crimson = preload("res://tracks/crimson_divide.gd")

func _initialize() -> void:
	call_deferred("check")

func check() -> void:
	var names := ["CRIMSON SERPENT","RED MESA CIRCUIT","DEVIL'S GATE"]
	var lengths: Array[float]=[]
	for offset in range(3):
		var circuit: int=4+offset
		set_meta("sceneforge_track",circuit)
		set_meta("sceneforge_race_mode",0)
		var scene: Node3D=load("res://city_loop.tscn").instantiate()
		root.add_child(scene)
		scene.set_physics_process(false)
		assert(scene.track_id==circuit)
		assert(scene.track_name()==names[offset])
		assert(scene.route.size()==scene.COUNT)
		assert(scene.get_node_or_null("CrimsonDriveSurface")!=null)
		assert(scene.get_node_or_null("CrimsonDeckSides")!=null)
		assert(scene.jump_start_index()==44 and scene.jump_end_index()==48)
		assert(scene.is_jump_gap(44) and scene.is_jump_gap(47))
		assert(not scene.is_jump_gap(48))
		var length: float=Crimson.route_length(circuit,scene.COUNT)
		lengths.append(length)
		var widest: float=0.0
		for i in range(scene.COUNT):
			var p: Vector3=scene.route[i]
			var q: Vector3=scene.route[(i+1)%scene.COUNT]
			var segment: float=scene.flat(q-p).length()
			widest=maxf(widest,segment)
			assert(segment>0.1 and segment<10.0,"Canyon path has an invalid or excessive gap")
			assert(p.y>-1.0 and p.y<18.0,"Unsafe road elevation")
			assert(scene.road_half_width(i)>=8.5)
			assert(scene.closest_segment(p)["point"].distance_to(p)<0.1)
		assert(scene.route[44].y>scene.route[28].y+2.0,"Canyon launch must rise above approach")
		assert(widest<10.0)
		assert(scene.challenge_laps()==(1 if circuit==4 else 3))
		scene.begin_event(scene.MODE_SOLO_RACE)
		scene.set_physics_process(false)
		assert(scene.race_countdown==3.0)
		for stage in range(scene.challenge_laps()):
			scene.lap_time=32.0+stage
			for gate in [scene.COUNT/4,scene.COUNT/2,scene.COUNT*3/4,0]:
				scene.track_progress(int(gate))
			if stage<scene.challenge_laps()-1:
				assert(not scene.race_finished)
		assert(scene.race_finished and scene.results_panel.visible,"Expected race finish after required stages")
		assert(scene.race_splits.size()==scene.challenge_laps())
		assert(scene.results_info.text.contains("SPRINT STAGE COMPLETE") if circuit==4 else scene.results_info.text.contains("3-LAP SOLO CHALLENGE COMPLETE"))
		scene.feedback.stop_audio()
		scene.free()
	assert(lengths[0]>1000.0,"Serpent must be a long curving stage")
	assert(lengths[1]>700.0 and lengths[1]<1000.0)
	assert(lengths[2]>750.0 and lengths[2]<1000.0)
	assert(lengths[0]>lengths[1] and lengths[0]>lengths[2])
	print("CRIMSON_DIVIDE_THREE_COURSES_OK ",lengths)
	quit()
