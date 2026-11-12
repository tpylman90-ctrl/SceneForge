extends SceneTree
## Smoke-test real-world surface sensors and collision-based hover lift.
func _initialize() -> void:
	call_deferred("check")

func check() -> void:
	var lab: Node3D=load("res://hover_lab.tscn").instantiate()
	root.add_child(lab)
	for tick in range(180):
		await physics_frame
	assert(lab.rig.contact_count>=3,"Four probes should find the test floor")
	assert(lab.rig.global_position.y>1.0 and lab.rig.global_position.y<2.2,"Real spring lift must stabilize craft above actual floor")
	lab.thrust=true
	var begin_z: float=lab.rig.global_position.z
	for tick in range(130):
		await physics_frame
	assert(lab.rig.global_position.z>begin_z+6.0,"Thrust should move the physics body forward")
	lab.thrust=false
	lab.right=true
	for tick in range(90):
		await physics_frame
	assert(lab.rig.global_position.x>0.1,"Right steering should yaw in the direction of the right button")
	lab.reset_lab()
	assert(lab.rig.linear_velocity.length()<0.01)
	print("SCENEFORGE_RIGIDBODY_HOVER_OK")
	quit()
