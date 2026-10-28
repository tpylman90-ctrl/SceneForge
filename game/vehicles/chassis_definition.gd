extends Resource

# Chassis identity, handling and compatible mount locations travel together.
@export var chassis_id := "kestrel"
@export var display_name := "KESTREL / MK I"
@export var visual_scene := "res://assets/neon_foundry.glb"
@export var accent_color := Color("66dcf0")
@export var max_forward_speed := 32.0
@export var max_reverse_speed := 8.0
@export var reverse_acceleration := 5.0
@export var acceleration := 11.5
@export var braking := 20.0
@export var coast_drag := 2.8
@export var yaw_rate := 1.28
@export var lateral_grip := 9.0
@export var steering_response := 5.0
@export var reverse_delay := 0.3
@export var boost_speed_bonus := 10.0
@export var boost_acceleration_multiplier := 1.6
@export var boost_drain := 28.0
@export var boost_recharge := 18.0
@export var cockpit_eye := Vector3(0, 1.829, 0.418)
@export var cockpit_pitch := -0.10472
@export var mount_points: Dictionary = {
	"repulsor_fl": Vector3(1.0, 0.37, 2.23),
	"repulsor_fr": Vector3(-1.0, 0.37, 2.23),
	"repulsor_rl": Vector3(1.12, 0.65, -0.40),
	"repulsor_rr": Vector3(-1.12, 0.65, -0.40),
	"propulsion": Vector3(0, 1.49, -1.67),
	"power_core": Vector3(0, 1.0, -0.7),
	"aero_left": Vector3(0.95, 1.25, -0.6),
	"aero_right": Vector3(-0.95, 1.25, -0.6)
}

