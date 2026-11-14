extends SceneTree
const Sticks = preload("res://vehicles/dual_stick_controls.gd")
func _initialize() -> void:
	call_deferred("check")

func touch(index: int, down: bool, point: Vector2) -> InputEventScreenTouch:
	var e := InputEventScreenTouch.new()
	e.index=index
	e.pressed=down
	e.position=point
	return e

func drag(index: int, point: Vector2) -> InputEventScreenDrag:
	var e := InputEventScreenDrag.new()
	e.index=index
	e.position=point
	return e

func check() -> void:
	var sticks: Control=Sticks.new()
	root.add_child(sticks)
	sticks.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var l: Vector2=sticks.left_center()
	var r: Vector2=sticks.right_center()
	assert(sticks.handle_event(touch(1,true,l+Vector2(0,-80))))
	assert(sticks.handle_event(touch(2,true,r+Vector2(60,-60))))
	assert(sticks.throttle_axis>0.85 and sticks.steer_axis>0.45 and sticks.height_axis>0.45)
	assert(sticks.handle_event(drag(1,l+Vector2(0,80))))
	assert(sticks.throttle_axis< -0.85,"Down throttle must brake/reverse")
	assert(sticks.handle_event(drag(2,r+Vector2(-60,60))))
	assert(sticks.steer_axis < -0.45 and sticks.height_axis < -0.45)
	assert(sticks.handle_event(touch(2,false,r)))
	assert(sticks.steer_axis==0.0 and sticks.height_axis==0.0)
	assert(sticks.throttle_axis< -0.85,"Releasing right stick must not release left")
	assert(sticks.handle_event(touch(1,false,l)))
	assert(sticks.throttle_axis==0.0)
	assert(sticks.handle_event(touch(8,true,l)))
	assert(sticks.throttle_axis==0.0,"Centered left stick must be neutral")
	assert(sticks.handle_event(drag(8,l+Vector2(0,-800))))
	assert(sticks.throttle_axis<=1.0 and sticks.throttle_axis>0.99)
	assert(sticks.handle_event(touch(8,false,l)))
	assert(sticks.handle_event(touch(3,true,sticks.boost_center())))
	assert(sticks.boost_remaining>2.0)
	sticks.tick(2.5)
	assert(sticks.boost_remaining==0.0)
	assert(sticks.handle_event(touch(4,true,sticks.boost_center())))
	assert(sticks.handle_event(touch(5,true,sticks.boost_center())))
	assert(sticks.boost_remaining==0.0,"Second tap must cancel boost")
	assert(not sticks.handle_event(touch(6,true,Vector2(640,100))),"Menu touch must pass through")
	sticks.set_enabled(false)
	assert(not sticks.handle_event(touch(7,true,l)))
	print("SCENEFORGE_DUAL_STICK_OK")
	quit()
