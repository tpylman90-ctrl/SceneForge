extends SceneTree
const Fleet=preload("res://vehicles/fleet_catalog.gd")
func _initialize() -> void:call_deferred("check")
func check() -> void:
	var ids: Array[String]=[]
	for index in range(Fleet.IDS.size()):
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
			if index==0:
				var instruments: Node3D=scene.feedback.get_node("KestrelCockpitInstruments")
				assert(not instruments.has_node("FlightDisplay"),"Kestrel uses a clean holographic fascia")
				var hologram: MeshInstance3D=instruments.get_node("HolographicDisplay")
				assert(hologram.material_override.albedo_texture==scene.feedback.telemetry.texture,"Kestrel HUD must receive live telemetry")
				var point: Vector3=scene.feedback.to_local(hologram.global_position)
				assert(point.z>scene.chassis.cockpit_eye.z and point.z<1.6 and point.y<1.85,"Kestrel HUD must remain inside canopy")
			if index==1:
				var instruments: Node3D=scene.feedback.get_node("PyldriverCockpitInstruments")
				assert(not instruments.has_node("FlightDisplay") and not instruments.has_node("InstrumentBinnacle"),"Pyldriver uses holographic instruments only")
				var hologram: MeshInstance3D=instruments.get_node("HolographicDisplay")
				assert(hologram.material_override.albedo_texture==scene.feedback.telemetry.texture,"Hologram must show live flight telemetry")
				assert(hologram.position.z>.0 and hologram.position.z<1.0 and hologram.position.y<1.8,"Hologram must remain inside cockpit")
				assert(scene.chassis.footprint_stretch>2.0,"Pyldriver fields must match elongated pods")
				assert(scene.chassis.cockpit_eye.z<0,"Driver eye must sit behind the dashboard")
				for slot in ["repulsor_fl","repulsor_fr","repulsor_rl","repulsor_rr"]:
					var point: Vector3=scene.chassis.mount_points[slot]
					assert(absf(point.x)<.6 and point.y>0 and point.y<.65,"Pods must sit below the hull")
				assert(is_equal_approx(scene.feedback.footprint_positions[0].x,.48))
				assert(is_equal_approx(scene.feedback.footprint_positions[2].z,-1.25))
			if definition.chassis_id=="forge":
				var instruments: Node3D=scene.feedback.get_node("ForgeCockpitInstruments")
				for display_name in ["FlightDisplay","HolographicDisplay"]:
					var instrument: MeshInstance3D=instruments.get_node(display_name)
					var rectangle := instrument.mesh as QuadMesh
					for x in [-.5,.5]:
						for y in [-.5,.5]:
							var point: Vector3=scene.feedback.to_local(instrument.to_global(Vector3(x*rectangle.size.x,y*rectangle.size.y,0)))
							var windshield_z := 1.5-(point.y-1.10)*1.2/.88
							assert(point.z<windshield_z-.10 and absf(point.x)<.40,"FORGE display must sit entirely inside canopy")
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
	for index in range(Fleet.IDS.size()):
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
