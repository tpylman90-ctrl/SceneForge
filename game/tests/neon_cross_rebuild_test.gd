extends SceneTree

# Neon Cross city-replacement contract. Existing Figure8 tests still own
# driving/crossing/jump physics; these gates verify the scene is rebuilt with
# spatial instancing, large open-air exposure and safe route continuity.
const Skyline=preload("res://tracks/neon_cross_rebuild.gd")
const Skyline3D=preload("res://tracks/neon_cross_skyline.gd")

func _initialize() -> void:
	call_deferred("check")

func check() -> void:
	set_meta("sceneforge_track",0)
	set_meta("sceneforge_race_mode",0)
	var scene: Node3D=load("res://city_loop.tscn").instantiate()
	root.add_child(scene)
	scene.set_physics_process(false)
	assert(scene.track_id==0)
	var world: Node3D=scene.get_node_or_null("NeonCrossRebuild")
	assert(world!=null,"Neon Cross must use the dedicated new environment")
	assert(world.get_meta("geometry_contract")!=null)
	assert(scene.route.size()==192)
	assert(scene.flat(scene.route[48]-scene.route[144]).length()<0.001)
	assert(scene.route[48].y-scene.route[144].y>4.0)
	var deck_segments: int=int(world.get_meta("physical_visual_deck_segments",0))
	var air_segments: int=int(world.get_meta("open_air_segments",0))
	assert(deck_segments>=55 and deck_segments<81,"Deck should be scenic anchor, not a continuous road")
	assert(air_segments>112 and air_segments+deck_segments==192)
	assert(Skyline.has_deck(0) and Skyline.has_deck(34) and Skyline.has_deck(58))
	assert(Skyline.has_deck(144) and not Skyline.has_deck(72))
	assert(not Skyline.has_deck(44) and not Skyline.has_deck(48))
	assert(world.get_node_or_null("NeonAnchorDeck")!=null)
	assert(world.get_node_or_null("NeonAnchorUndersides")!=null)
	assert(world.get_node_or_null("NeonSplineLightTrails")!=null)
	assert(world.get_node_or_null("NeonDirectionArches")!=null)
	assert(world.get_node_or_null("NeonCrossRebuildStart")!=null)
	var floor: MeshInstance3D=world.get_node_or_null("NeonCityDepthFloor")
	assert(floor!=null and floor.position.y < -55.0)
	assert(floor.cast_shadow==GeometryInstance3D.SHADOW_CASTING_SETTING_OFF)
	var towers: int=int(world.get_meta("instanced_buildings",0))
	assert(towers>=60 and towers<=Skyline.MAX_BUILDINGS)
	var multi_count: int=0
	var node_count: int=world.get_child_count()
	var instanced_vertices: int=0
	for child in world.get_children():
		var mm: MultiMeshInstance3D=child as MultiMeshInstance3D
		if mm==null:
			continue
		assert(mm.multimesh!=null)
		assert(mm.multimesh.instance_count>0)
		assert(mm.cast_shadow==GeometryInstance3D.SHADOW_CASTING_SETTING_OFF)
		multi_count+=1
		instanced_vertices+=mm.multimesh.instance_count
	assert(multi_count>=24 and multi_count<=28,"3D near/mid skyline must batch by spatial district")
	assert(instanced_vertices>=towers+200)
	assert(int(world.get_meta("hero_3d_towers",0))==Skyline3D.HERO_SITES.size())
	assert(int(world.get_meta("midrise_towers",0))>=45)
	assert(int(world.get_meta("batched_facade_details",0))>80)
	assert(world.get_node_or_null("NeonPanoramaLayerNear")!=null)
	assert(world.get_node_or_null("NeonPanoramaLayerFar")!=null)
	for site in Skyline3D.HERO_SITES:
		assert(Skyline3D.safe_footprint(scene.route,site,16.4,14.0))
	assert(Skyline3D.HERO_HEIGHTS[0]+Skyline3D.BASE_Y>60.0,"High rises must surround the racing flight plane")
	assert(node_count<48,"Too many scene nodes for an intentionally batched skyline")
	for i in range(192):
		var p: Vector3=scene.route[i]
		var closest: Dictionary=scene.closest_segment(p)
		assert(closest["point"].distance_to(p)<0.11)
		if i>=44 and i<52:
			assert(not Skyline.has_deck(i),"Leap must not acquire visual collision floor")
	scene.route_index=72
	scene.car.position=scene.route[72]
	scene.update_jump(1.0/60.0,scene.route[72].y)
	assert(not scene.hover_rings.visible,"Floating ground rings must hide without a deck")
	scene.route_index=0
	scene.update_jump(1.0/60.0,scene.route[0].y)
	assert(scene.hover_rings.visible,"Repulsor rings reappear on anchored start deck")
	scene.feedback.stop_audio()
	scene.free()
	# Other established city courses must still use their original environment.
	set_meta("sceneforge_track",1)
	var existing: Node3D=load("res://city_loop.tscn").instantiate()
	root.add_child(existing)
	existing.set_physics_process(false)
	assert(existing.track_id==1)
	assert(existing.get_node_or_null("NeonCrossRebuild")==null)
	assert(existing.route.size()==192)
	existing.feedback.stop_audio()
	existing.free()
	print("NEON_CROSS_AERIAL_REBUILD_OK decks=",deck_segments," air=",air_segments,
		" towers=",towers," hero=",world.get_meta("hero_3d_towers"),
		" facade=",world.get_meta("batched_facade_details"),
		" multi=",multi_count," scene_nodes=",node_count)
	quit()
