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
	for section in range(3):
		var cliff: MeshInstance3D=scene.get_node_or_null("SkyfallFlightValley_%d"%section)
		assert(cliff!=null and cliff.mesh!=null)
		var vertices: PackedVector3Array=cliff.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
		assert(vertices.size()>1000,"Aerial descent must render nearby land, not emptiness")
	for name in ["SkyfallFlightRockNeedles","SkyfallFlightNeedleCrowns",
		"SkyfallFlightForestCrowns","SkyfallFlightForestTrunks"]:
		var markers: MultiMeshInstance3D=scene.get_node_or_null(name)
		assert(markers!=null and markers.multimesh.instance_count>15)
	var sky_gates: MeshInstance3D=scene.get_node_or_null("SkyfallFlightAerialGates")
	assert(sky_gates!=null and sky_gates.mesh.get_surface_count()==1)
	assert(sky_gates.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX].size()>450)
	assert(Skyfall.FlightWorld.GATES.size()==4)
	for gate_index in range(Skyfall.FlightWorld.GATES.size()):
		var ring_center: Vector3=Skyfall.FlightWorld.flight_gate_center(points,gate_index)
		var course_point: Vector3=points[Skyfall.FlightWorld.GATES[gate_index]]
		assert(ring_center.distance_to(course_point)<25.0,"Sky rings must be reachable by the player")
	var valley_noise: FastNoiseLite=Skyfall.FlightWorld._noise()
	var sky_start: Vector3=Skyfall.FlightWorld._valley_vertex(points,146,0.0,valley_noise)
	assert(points[146].y-sky_start.y>35.0 and points[146].y-sky_start.y<150.0,
		"Real ground must be visible below the airborne craft")
	# The reveal must not secretly have a road or replace its hovercraft.
	var surface: MeshInstance3D=scene.get_node("SkyfallDriveSurface")
	assert(surface.mesh.get_surface_count()==1)
	# A road can exist in memory yet be invisible in Mobile/Vulkan if its
	# triangles are back-facing. Check the exact face orientation, not just
	# mesh existence. Godot treats clockwise winding as front-facing.
	var road_material: StandardMaterial3D=surface.material_override as StandardMaterial3D
	assert(road_material!=null)
	assert(road_material.cull_mode==BaseMaterial3D.CULL_BACK)
	assert(road_material.transparency==BaseMaterial3D.TRANSPARENCY_DISABLED)
	var road_arrays: Array=surface.mesh.surface_get_arrays(0)
	var verts: PackedVector3Array=road_arrays[Mesh.ARRAY_VERTEX]
	var normals: PackedVector3Array=road_arrays[Mesh.ARRAY_NORMAL]
	var segment_count: int=0
	for segment in range(Skyfall.COUNT-1):
		if (segment<Skyfall.GAP_START or segment>=Skyfall.GAP_END) and (segment<Skyfall.FLIGHT_START or segment>=Skyfall.FLIGHT_END):
			segment_count+=1
	assert(verts.size()==segment_count*6,"Only intentional flight and bridge gaps should have no road")
	assert(normals.size()==verts.size())
	for triangle in range(0,verts.size(),3):
		var v0: Vector3=verts[triangle]
		var v1: Vector3=verts[triangle+1]
		var v2: Vector3=verts[triangle+2]
		var clockwise_normal: Vector3=(v2-v0).cross(v1-v0).normalized()
		assert(clockwise_normal.y>0.12,"Road top faces must point up, not under the Vulkan camera")
		assert(normals[triangle].dot(clockwise_normal)>0.98,"Road lighting normals must agree with front-facing winding")
	print("SKYFALL_ROAD_WINDING_OK triangles=%d" % (verts.size()/3))
	scene.route_index=Skyfall.GAP_START
	scene.car.position=points[Skyfall.GAP_START]
	scene.update_jump(1.0/60.0,scene.car.position.y)
	assert(scene.airborne and scene.jump_launches==1)
	scene.route_index=Skyfall.GAP_END+1
	scene.update_jump(1.0/60.0,points[Skyfall.GAP_END+1].y)
	assert(not scene.airborne and scene.jump_landings==1)
	scene.route_index=Skyfall.FLIGHT_START+2
	scene.car.position=points[Skyfall.FLIGHT_START+2]
	scene.speed=scene.chassis.max_forward_speed*0.88
	scene.update_jump(1.0/60.0,scene.car.position.y)
	assert(scene.airborne and scene.jump_launches==2)
	assert(scene.speed>=scene.chassis.max_forward_speed*1.05,"Summit must launch at racing speed")
	var lower: float=scene.skyfall_trim
	scene.boost_active=true
	scene.update_jump(0.4,points[Skyfall.FLIGHT_START+2].y)
	assert(scene.skyfall_trim>lower,"Boost should lift the free-air trim")
	scene.skyfall_gate_next=0
	scene.route_index=Skyfall.FlightWorld.GATES[0]
	scene.car.position=Skyfall.FlightWorld.flight_gate_center(points,0)
	scene.boost_energy=75.0
	scene.update_skyfall_gates()
	assert(scene.skyfall_gate_next==1 and scene.boost_energy>75.0,
		"A clean aerial gate must reward the chosen 3D racing line")
	scene.route_index=Skyfall.FLIGHT_END+1
	scene.update_jump(0.1,points[Skyfall.FLIGHT_END+1].y)
	assert(not scene.airborne and scene.jump_landings==2)
	scene.lap_time=115.0
	scene.track_progress(Skyfall.FINISH_INDEX)
	assert(scene.race_finished and scene.checkpoint==1)
	scene.feedback.stop_audio()
	scene.free()
	print("SKYFALL_AERIAL_WORLD_OK 3 chunks, 4 gates, forest and needles")
	print("SKYFALL_ROUTE_FLIGHT_OK length=%.1f summit=%.1f obstacles=%d"%[traveled,summit,8])
	quit()
