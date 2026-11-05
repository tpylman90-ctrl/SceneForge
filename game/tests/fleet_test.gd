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
					var vertices: Array[Vector3]=[]
					if instrument.mesh is QuadMesh:
						var rectangle := instrument.mesh as QuadMesh
						for x in [-.5,.5]:
							for y in [-.5,.5]:
								vertices.append(Vector3(x*rectangle.size.x,y*rectangle.size.y,0))
					elif instrument.mesh is ArrayMesh:
						# FORGE holographic windscreen is a curved ArrayMesh,
						# not a flat QuadMesh. Validate actual mesh vertices.
						var surface_vertices: PackedVector3Array=instrument.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
						for v in surface_vertices:
							vertices.append(v)
					else:
						assert(false,"Unrecognized FORGE cockpit display mesh")
					assert(vertices.size()>0)
					for vertex in vertices:
						var point: Vector3=scene.feedback.to_local(instrument.to_global(vertex))
						assert(absf(point.x)<.55 and point.y<1.92 and point.z<1.52,
							"FORGE cockpit display must remain inside body bounds")
			if definition.chassis_id=="synapse":
				assert(scene.feedback.synapse_thrusters.size()==3 and scene.feedback.hover_glow_materials.size()==3)
				assert(scene.feedback.footprint_positions.size()==4)
				for slot in ["repulsor_fl","repulsor_fr","repulsor_rl","repulsor_rr"]:
					assert(scene.chassis.mount_points[slot].y<0,"Synapse repulsors must sit beneath the low hull")
				assert(scene.chassis.cockpit_eye.y<1.0 and scene.chassis.cockpit_eye.z<0.0,"Synapse cockpit camera must sit inside the fitted canopy")
			elif definition.chassis_id=="solstice":
				assert(scene.feedback.has_node("SOLSTICE_Original_Body"),"Original SOLSTICE GLB missing")
				assert(scene.feedback.glass.size()>=4,"SOLSTICE needs actual glass")
				assert(scene.feedback.footprint_positions.size()==4)
				assert(scene.feedback.solstice_brake_lamps.size()>=8,"Modeled LED layers missing")
				assert(scene.feedback.solstice_engine_materials.size()>=5,"Original lift and thrust fields missing")
				assert(scene.feedback.tails.is_empty(),"SOLSTICE must not depend on Kestrel tail rigs")
				assert(scene.chassis.cockpit_eye.y<1.65)
				assert(scene.chassis.mount_points["propulsion"].z< -3.0)
				print("FLEET_SOLSTICE_ORIGINAL_DRIVE_MODEL_OK")
			elif definition.chassis_id=="aerolith":
				assert(scene.feedback.has_node("Aerolith_Original_Body"),"Original Assetwright model did not instantiate in racing scene")
				assert(scene.feedback.synapse_thrusters.size()==2,"AEROLITH must use two real vectored thruster positions")
				assert(scene.feedback.footprint_positions.size()==4)
				assert(scene.feedback.glass.size()>0,"AEROLITH visor must have cockpit transparency overrides")
				assert(not scene.feedback.showroom_upload)
				print("FLEET_AEROLITH_ORIGINAL_DRIVE_MODEL_OK")
			else:
				assert(scene.feedback.tails.size()==5 and scene.feedback.yoke!=null)
			if definition.chassis_id=="shrike":
				assert(scene.feedback.showroom_upload,"Racing Shrike must use uploaded master, not procedural fallback")
			assert(scene.feedback.get_node("ComponentMounts").get_child_count()==8)
			scene.toggle_camera()
			assert(scene.cockpit,"Cockpit should be accessible to every craft")
			if definition.chassis_id=="solstice":
				for pane in scene.feedback.glass:
					assert(pane["mesh"].get_surface_override_material(pane["surface"])==pane["inside"],
						"SOLSTICE glass must use cockpit interior material")
			if definition.chassis_id=="shrike":
				assert(scene.feedback.windshield_faces>=12,"Shrike glass cutout must isolate actual faces")
				assert(scene.feedback.windshield_windows.size()>0)
				for canopy in scene.feedback.windshield_windows:
					assert(not canopy.visible,"Painted Shrike glazing must hide only in cockpit view")
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
			if definition.chassis_id=="shrike":
				scene.toggle_camera()
				assert(not scene.cockpit)
				for canopy in scene.feedback.windshield_windows:
					assert(canopy.visible,"Shrike's original exterior glass must return in chase mode")
				print("FLEET_SHRIKE_UPLOADED_DRIVE_OK ",circuit)
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
		if index==2 and hangar.visual.showroom_upload:
			assert(hangar.visual.windshield_faces>=12)
			assert(hangar.visual.get_node_or_null("ComponentMounts")!=null)
			print("FLEET_SHRIKE_WINDSCREEN_VIEW_OK")
		hangar.action("FRONT")
		assert(not hangar.cockpit)
	print("FLEET_SELECTION_OK")
	hangar.visual.stop_audio()
	await create_timer(.15).timeout
	print("FLEET_OK")
	quit()
