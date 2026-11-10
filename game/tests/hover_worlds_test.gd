extends SceneTree

# These checks protect the new 7-9 circuit IDs, surface continuity, actual
# in-engine race registration, decorative batching and sky air-corridor rules.
const Worlds = preload("res://tracks/hover_worlds.gd")

func _initialize() -> void:
	call_deferred("check")

func check() -> void:
	assert(Worlds.FIRST_ID==7 and Worlds.LAST_ID==9)
	var names: Array[String]=["TIDAL RELICS","FROSTLINE WILDS","SKYFALL RUN"]
	for offset in range(3):
		var id: int=7+offset
		set_meta("sceneforge_track",id)
		set_meta("sceneforge_race_mode",0)
		var scene: Node3D=load("res://city_loop.tscn").instantiate()
		root.add_child(scene)
		scene.set_physics_process(false)
		assert(scene.track_id==id)
		assert(scene.track_name()==names[offset])
		assert(scene.route.size()==192)
		assert(scene.challenge_laps()==3)
		var length: float=0.0
		for i in range(scene.COUNT):
			var p: Vector3=scene.route[i]
			var q: Vector3=scene.route[(i+1)%scene.COUNT]
			var distance: float=scene.flat(q-p).length()
			assert(distance>0.1 and distance<9.0,"Bad hover spline chord")
			assert(p.y>0.0,"Course elevation must stay above its decorative terrain")
			assert(scene.road_half_width(i)>=10.5)
			assert(scene.closest_segment(p)["point"].distance_to(p)<0.15)
			length+=distance
		assert(length>800.0 and length<1020.0,"Unexpected race length")
		assert(scene.jump_start_index()==44 and scene.jump_end_index()==48)
		assert(scene.is_jump_gap(44) and not scene.is_jump_gap(48))
		assert(scene.get_node_or_null("HoverWorldStart")!=null)
		if id==7:
			assert(scene.get_node_or_null("HoverWorldLagoon")!=null)
			assert(scene.get_node_or_null("HoverStoneDeck")!=null)
			assert(Worlds.has_deck(7,60) and not Worlds.has_deck(7,18))
			assert(not Worlds.is_air_channel(7,18))
		elif id==8:
			assert(scene.get_node_or_null("HoverWorldFrozenValley")!=null)
			assert(scene.get_node_or_null("HoverIceDeck")!=null)
			assert(scene.get_node_or_null("HoverMudDeck")!=null)
			assert(scene.get_node_or_null("HoverGrassDeck")!=null)
			assert(scene.get_node_or_null("HoverGlacialShards")!=null)
			assert(Worlds.has_deck(8,110))
		else:
			assert(scene.get_node_or_null("HoverFloatingIslands")!=null)
			assert(scene.get_node_or_null("HoverAirGateRings")!=null)
			assert(scene.get_node_or_null("HoverSkyPlatformDeck")!=null)
			assert(Worlds.is_air_channel(9,84) and Worlds.is_air_channel(9,134))
			assert(not Worlds.is_air_channel(9,117) and not Worlds.is_air_channel(9,155))
			assert(scene.route[100].y>55 and scene.route[100].y<105)
			scene.route_index=84
			scene.car.position=scene.route[84]
			scene.update_jump(1.0/60.0,scene.route[84].y)
			assert(not scene.hover_rings.visible,"Repulsor footprints must hide in the sky")
			scene.reset_car()
		scene.begin_event(scene.MODE_SOLO_RACE)
		scene.set_physics_process(false)
		assert(scene.race_countdown==3.0)
		for lap in range(3):
			scene.lap_time=24.0+float(lap)
			for gate in [48,96,144,0]:
				scene.track_progress(gate)
			if lap<2:
				assert(not scene.race_finished)
		assert(scene.race_finished)
		assert(scene.race_splits.size()==3)
		scene.feedback.stop_audio()
		scene.free()
		print("HOVER_WORLD_OK ",id," / ",length)
	print("HOVER_WORLDS_THREE_COURSES_OK")
	quit()
