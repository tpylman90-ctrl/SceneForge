extends SceneTree
const Fleet=preload("res://vehicles/fleet_catalog.gd")
func _initialize() -> void:call_deferred("check")
func check() -> void:
	var ids: Array[String]=[]
	for index in range(5):
		var definition: Resource=Fleet.definition(index)
		assert(not ids.has(definition.chassis_id))
		ids.append(definition.chassis_id)
		assert(ResourceLoader.exists(definition.visual_scene))
		set_meta("sceneforge_craft",index)
		for circuit in range(3):
			set_meta("sceneforge_track",circuit)
			var scene: Node3D=load("res://city_loop.tscn").instantiate()
			root.add_child(scene)
			scene.set_physics_process(false)
			assert(scene.chassis.chassis_id==definition.chassis_id)
			if index==1:
				var display: Node3D=scene.feedback.get_node("PyldriverCockpitInstruments/FlightDisplay")
				assert(display.position.z>.8 and display.position.z<1.15 and display.position.y<1.6,"Dashboard must remain inside cockpit")
				assert(scene.chassis.footprint_stretch>2.0,"Pyldriver fields must match elongated pods")
				assert(scene.chassis.cockpit_eye.z<0,"Driver eye must sit behind the dashboard")
				for slot in ["repulsor_fl","repulsor_fr","repulsor_rl","repulsor_rr"]:
					var point: Vector3=scene.chassis.mount_points[slot]
					assert(absf(point.x)<.6 and point.y>0 and point.y<.4,"Pods must sit below the hull")
				assert(is_equal_approx(scene.feedback.footprint_positions[0].x,.48))
				assert(is_equal_approx(scene.feedback.footprint_positions[2].z,-1.25))
			assert(scene.feedback.tails.size()==5 and scene.feedback.yoke!=null)
			assert(scene.feedback.get_node("ComponentMounts").get_child_count()==8)
			scene.toggle_camera()
			scene.reset_car()
			scene.throttle=true
			for frame in range(3600):
				var near: Dictionary=scene.closest_segment(scene.car.position,scene.route_index)
				var target: Vector3=scene.route[(int(near["index"])+4)%scene.COUNT]
				var offset: Vector3=target-scene.car.position
				var error := wrapf(atan2(offset.x,offset.z)-scene.heading,-PI,PI)
				scene.left=error>.015
				scene.right=error< -.015
				scene._physics_process(1.0/60)
				if scene.lap>1:break
			assert(scene.lap==2 and scene.jump_landings==1 and scene.jump_recoveries==0,"Fleet circuit failed")
			assert(scene.feedback.telemetry.craft_name==definition.display_name)
			assert(scene.camera.position.distance_to(scene.feedback.to_global(definition.cockpit_eye))<.01)
			print("FLEET_LAP_OK ",definition.chassis_id," / ",circuit)
			scene.feedback.stop_audio()
			scene.free()
	set_meta("sceneforge_craft",0)
	var hangar: Node3D=load("res://fleet_hangar.tscn").instantiate()
	root.add_child(hangar)
	for index in range(5):
		hangar.select_craft(index)
		await create_timer(.2).timeout
		assert(hangar.selected==index and not hangar.busy)
		assert(hangar.visual.chassis.chassis_id==Fleet.IDS[index])
		hangar.action("COCKPIT")
		assert(hangar.cockpit)
		hangar.action("FRONT")
		assert(not hangar.cockpit)
	print("FLEET_SELECTION_OK")
	hangar.visual.stop_audio()
	await create_timer(.15).timeout
	print("FLEET_OK")
	quit()
