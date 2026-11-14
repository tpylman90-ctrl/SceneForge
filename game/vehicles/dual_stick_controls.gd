extends Control
## Multitouch Android control surface. Left Y = signed throttle; right X = yaw,
## right Y = commanded hover clearance. Boost is a two-thumb-friendly pulse.
## No dependency on a particular circuit, race mode, chassis mesh or camera.
const RADIUS := 84.0
const TOUCH_RADIUS := 132.0
const DEAD_ZONE := 0.13
const BOOST_SECONDS := 2.25

var left_finger := -1
var right_finger := -1
var throttle_axis := 0.0
var steer_axis := 0.0
var height_axis := 0.0
var boost_remaining := 0.0
var enabled := true
var altitude_fraction := 0.0
var ceiling_label := "5.8 M"

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	resized.connect(queue_redraw)
	queue_redraw()

func left_center() -> Vector2:
	return Vector2(155.0, size.y-143.0)

func right_center() -> Vector2:
	return Vector2(size.x-155.0, size.y-143.0)

func boost_center() -> Vector2:
	return Vector2(size.x-352.0,size.y-296.0)

static func axis_at(point: Vector2, center: Vector2) -> Vector2:
	var raw: Vector2=(point-center)/RADIUS
	if raw.length()>1.0:
		raw=raw.normalized()
	if raw.length()<DEAD_ZONE:
		return Vector2.ZERO
	return raw.normalized() * ((raw.length()-DEAD_ZONE)/(1.0-DEAD_ZONE))

func set_enabled(value: bool) -> void:
	enabled=value
	if not enabled:
		clear()

func clear() -> void:
	left_finger=-1
	right_finger=-1
	throttle_axis=0.0
	steer_axis=0.0
	height_axis=0.0
	boost_remaining=0.0
	queue_redraw()

func tick(delta: float) -> void:
	if boost_remaining>0.0:
		boost_remaining=maxf(0.0,boost_remaining-maxf(0.0,delta))
		if boost_remaining==0.0:
			queue_redraw()

func handle_event(event: InputEvent) -> bool:
	if not enabled or not visible:
		return false
	var point: Vector2
	if event is InputEventScreenTouch:
		var touch: InputEventScreenTouch=event
		point=touch.position
		if touch.pressed:
			if point.distance_to(boost_center())<=77.0:
				# Tap once for a timed boost, tap again to cancel.
				boost_remaining=0.0 if boost_remaining>0.0 else BOOST_SECONDS
				queue_redraw()
				return true
			if point.distance_to(left_center())<=TOUCH_RADIUS and left_finger==-1:
				left_finger=touch.index
				apply_point(left_finger,point)
				return true
			if point.distance_to(right_center())<=TOUCH_RADIUS and right_finger==-1:
				right_finger=touch.index
				apply_point(right_finger,point)
				return true
		else:
			if touch.index==left_finger:
				left_finger=-1
				throttle_axis=0.0
				queue_redraw()
				return true
			if touch.index==right_finger:
				right_finger=-1
				steer_axis=0.0
				height_axis=0.0
				queue_redraw()
				return true
	elif event is InputEventScreenDrag:
		var drag: InputEventScreenDrag=event
		if drag.index==left_finger or drag.index==right_finger:
			apply_point(drag.index,drag.position)
			return true
	return false

func apply_point(finger: int, point: Vector2) -> void:
	if finger==left_finger:
		var sampled: Vector2=axis_at(point,left_center())
		throttle_axis=-sampled.y
	elif finger==right_finger:
		var sampled: Vector2=axis_at(point,right_center())
		steer_axis=sampled.x
		height_axis=-sampled.y
	queue_redraw()

func _draw() -> void:
	if not enabled:
		return
	var left: Vector2=left_center()
	var right: Vector2=right_center()
	var boost_pos: Vector2=boost_center()
	var blue:=Color(0.12,0.53,0.69,0.48)
	var orange:=Color(1.0,0.43,0.16,0.65)
	for center in [left,right]:
		draw_circle(center,RADIUS+11.0,Color(0.015,0.035,0.055,0.76))
		draw_arc(center,RADIUS,0.0,TAU,64,blue,3.0,true)
		draw_line(center+Vector2(-RADIUS,0),center+Vector2(RADIUS,0),Color(0.35,0.65,0.77,0.30),2.0)
		draw_line(center+Vector2(0,-RADIUS),center+Vector2(0,RADIUS),Color(0.35,0.65,0.77,0.30),2.0)
	var left_knob:=left+Vector2(0.0,-throttle_axis*RADIUS)
	var right_knob:=right+Vector2(steer_axis,-height_axis)*RADIUS
	draw_circle(left_knob,34.0,Color(0.18,0.62,0.76,0.92))
	draw_circle(right_knob,34.0,Color(0.18,0.62,0.76,0.92))
	draw_arc(left_knob,34.0,0.0,TAU,32,Color("d6f8ff"),2.0)
	draw_arc(right_knob,34.0,0.0,TAU,32,Color("d6f8ff"),2.0)
	draw_circle(boost_pos,69.0,Color(0.13,0.07,0.05,0.90))
	draw_arc(boost_pos,66.0,0.0,TAU,48,orange,4.0)
	if boost_remaining>0.0:
		draw_circle(boost_pos,58.0,Color(0.60,0.22,0.06,0.76))
		draw_arc(boost_pos,62.0,-PI/2.0,-PI/2.0+TAU*boost_remaining/BOOST_SECONDS,48,Color("ffe1a0"),5.0)
	var font: Font=ThemeDB.fallback_font
	draw_string(font,left+Vector2(-70,-110),"THROTTLE",HORIZONTAL_ALIGNMENT_LEFT,-1,18,Color("d8f4ff"))
	draw_string(font,left+Vector2(-49,122),"REVERSE",HORIZONTAL_ALIGNMENT_LEFT,-1,17,Color("d8f4ff"))
	draw_string(font,right+Vector2(-72,-110),"CLIMB   ↑",HORIZONTAL_ALIGNMENT_LEFT,-1,17,Color("d8f4ff"))
	draw_string(font,right+Vector2(-70,123),"↓ DESCEND",HORIZONTAL_ALIGNMENT_LEFT,-1,17,Color("d8f4ff"))
	draw_string(font,right+Vector2(-61,16),"←  YAW  →",HORIZONTAL_ALIGNMENT_LEFT,-1,16,Color("081a29"))
	draw_string(font,boost_pos+Vector2(-37,7),"BOOST",HORIZONTAL_ALIGNMENT_LEFT,-1,20,Color("fff4e0"))
	# Vertical envelope indicator: controlled altitude is bounded by the course.
	var meter_x: float=size.x-18.0
	var meter_top: float=size.y-355.0
	var meter_h: float=176.0
	draw_rect(Rect2(meter_x-10.0,meter_top,6.0,meter_h),Color(0.05,0.15,0.20,0.9))
	draw_rect(Rect2(meter_x-10.0,meter_top+meter_h*(1.0-altitude_fraction),6.0,meter_h*altitude_fraction),Color("6be9f7"))
	draw_string(font,Vector2(size.x-118.0,meter_top-12.0),"MAX "+ceiling_label,HORIZONTAL_ALIGNMENT_LEFT,-1,13,Color("e9fdff"))
