extends SceneTree
const Fleet=preload("res://vehicles/fleet_catalog.gd")
func _initialize() -> void:call_deferred("check")
func check() -> void:
	var hangar: Node3D=load("res://fleet_hangar.tscn").instantiate()
	root.add_child(hangar)
	current_scene=hangar
	for index in range(Fleet.IDS.size()):
		hangar.select_craft(index)
		await create_timer(.2).timeout
		hangar.action("FOUNDRY")
		await create_timer(.3).timeout
		var lot: Node3D=current_scene
		assert(lot.scene_file_path=="res://main.tscn")
		assert(lot.chassis.chassis_id==Fleet.IDS[index])
		assert(lot.craft_title.text==Fleet.NAMES[index])
		if Fleet.IDS[index]=="synapse":
			assert(lot.lot_feedback.chassis.chassis_id==Fleet.IDS[index],"Synapse body study must appear in the Foundry lot")
			lot.open_fleet()
			await create_timer(.3).timeout
			hangar=current_scene
			assert(hangar.selected==index,"Returning from the Foundry must preserve Synapse selection")
			print("FOUNDRY_SELECTION_OK ",Fleet.IDS[index])
			continue
		if index>0:
			assert(lot.lot_feedback.chassis.chassis_id==Fleet.IDS[index])
			assert(lot.lot_feedback.get_node("ComponentMounts").get_child_count()==8)
			assert(lot.driver_door==null and lot.door_button.disabled)
			assert(not lot.has_node("KestrelCockpitInstruments"))
			var baked: Node3D=lot.get_child(0)
			for child in baked.get_children():
				assert(not str(child.name).begins_with("Kestrel_") and child.name!="DriverDoor","Original Kestrel must be removed")
		else:
			assert(lot.driver_door!=null and not lot.door_button.disabled)
		lot.inspection_preset("seat")
		lot.update_orbit()
		var eye: Vector3=lot.lot_feedback.to_global(lot.chassis.cockpit_eye) if index>0 else lot.chassis.cockpit_eye
		assert(lot.camera.global_position.distance_to(eye)<.001)
		lot.inspection_preset("tail")
		lot.set_inspection(false)
		assert(not lot.seat_mode and not lot.orbit_mode)
		lot.open_track()
		await create_timer(.3).timeout
		var track: Node3D=current_scene
		assert(track.chassis.chassis_id==Fleet.IDS[index])
		track.shutdown("res://main.tscn")
		await create_timer(.3).timeout
		lot=current_scene
		assert(lot.chassis.chassis_id==Fleet.IDS[index],"Track return must preserve selected craft")
		lot.open_fleet()
		await create_timer(.3).timeout
		hangar=current_scene
		assert(hangar.selected==index)
		print("FOUNDRY_SELECTION_OK ",Fleet.IDS[index])
	hangar.visual.stop_audio()
	await create_timer(.15).timeout
	print("FOUNDRY_FLEET_OK")
	quit()
