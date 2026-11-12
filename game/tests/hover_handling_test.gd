extends SceneTree
## Pure handling/phone-input regression; requires no car GLB or track graphics.
const Motion = preload("res://vehicles/hover_motion.gd")
const Touch = preload("res://vehicles/hover_touch_input.gd")

func _initialize() -> void:
	call_deferred("check")

func check() -> void:
	for hz in [30, 60, 120]:
		var model = Motion.new()
		model.reset(0.0)
		for tick in range(hz * 2):
			model.follow_surface(1.0 / float(hz), 0.0, 0.0)
		assert(absf(model.height) < 0.04, "Hover idle should settle without bouncing")
		for tick in range(hz):
			model.follow_surface(1.0 / float(hz), 0.45, 25.0)
		assert(absf(model.height - 0.45) < 0.06, "Hover spring should climb a shallow change")
		assert(absf(model.vertical_velocity) < 0.7, "Hover spring should not oscillate indefinitely")
		var forward := Vector3.BACK # SceneForge racers travel along Godot +Z
		var current := Vector3(8.0, 0.0, 10.0)
		for tick in range(hz):
			current = Motion.horizontal_velocity(current, forward, 25.0, 6.0, 1.0 / float(hz), false)
		assert(absf(current.x) < 0.10 and current.z > 24.0, "Hover must retain then bleed lateral speed")
		print("HOVER_HANDLING_RATE_OK ", hz)
	var screen := Vector2(1280.0, 720.0)
	var touches := {1: Vector2(100.0, 640.0), 2: Vector2(1150.0, 640.0)}
	var input_state: Dictionary = Touch.decode(touches, screen)
	assert(input_state["left"] and input_state["throttle"] and not input_state["right"])
	touches.erase(1)
	input_state = Touch.decode(touches, screen)
	assert(not input_state["left"] and input_state["throttle"])
	touches[2] = Vector2(1150.0, 550.0)
	input_state = Touch.decode(touches, screen)
	assert(input_state["boost"] and not input_state["throttle"])
	touches[1] = Vector2(475.0, 710.0)
	input_state = Touch.decode(touches, screen)
	assert(input_state["right"] and input_state["boost"] and not input_state["left"])
	touches.clear()
	input_state = Touch.decode(touches, screen)
	assert(not input_state["right"] and not input_state["boost"])
	print("SCENEFORGE_HOVER_HANDLING_OK")
	quit()
