extends RefCounted
## One touch-decoder shared by mobile UI tests and the live SceneForge race.
## Positive steering corresponds to the on-screen RIGHT arrow. BRAKE doubles
## as reverse only after the drivetrain's safe stopping delay.

static func decode(touches: Dictionary, screen: Vector2) -> Dictionary:
	var state := {"left": false, "right": false, "throttle": false, "brake": false, "boost": false}
	var control_top: float = screen.y - 160.0
	var pedal_left: float = screen.x - 410.0
	var boost_area := Rect2(screen.x - 410.0, screen.y - 210.0, 390.0, 80.0)
	for point in touches.values():
		var position: Vector2 = point
		if boost_area.has_point(position):
			state["boost"] = true
			continue
		if position.y < control_top:
			continue
		state["left"] = bool(state["left"]) or (position.x >= 0.0 and position.x < 240.0)
		state["right"] = bool(state["right"]) or (position.x >= 240.0 and position.x < 480.0)
		state["brake"] = bool(state["brake"]) or (position.x >= pedal_left and position.x < pedal_left + 178.0)
		state["throttle"] = bool(state["throttle"]) or (position.x >= pedal_left + 178.0 and position.x < screen.x - 20.0)
	return state

static func is_drive_area(position: Vector2, screen: Vector2) -> bool:
	return position.y >= screen.y - 160.0 or Rect2(screen.x - 410.0, screen.y - 210.0, 390.0, 80.0).has_point(position)
