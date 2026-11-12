extends RefCounted
## Reusable, deterministic hover-response model for the SceneForge handling lab.
## Track geometry provides a desired craft-origin height, not a rigid Y lock.
## No Node3D, camera, art, or race-specific dependencies: portable to Neon Foundry.

const SPRING_STIFFNESS := 70.0
const SPRING_DAMPING := 16.0
const MAX_FALL_BELOW_DECK := 0.18
const MAX_RISE_ABOVE_DECK := 0.55
const IDLE_BOB_AMPLITUDE := 0.018
const LATERAL_GRIP_FRACTION := 0.88

var height := 0.0
var vertical_velocity := 0.0
var hover_phase := 0.0
var initialized := false

func reset(current_height: float) -> void:
	height = current_height
	vertical_velocity = 0.0
	hover_phase = 0.0
	initialized = true

func follow_surface(delta: float, desired_height: float, speed: float) -> float:
	# The racing spline/terrain samples the *surface*. Only the suspension
	# decides where the craft actually is. Step size is bounded for recovery
	# when Android frames stall; the game physics tick normally stays at 60 Hz.
	if not initialized:
		reset(desired_height)
	var dt: float = clampf(delta, 0.0, 0.05)
	hover_phase = fposmod(hover_phase + dt * (2.0 + absf(speed) * 0.055), TAU)
	var bob_factor: float = 1.0 - 0.65 * clampf(absf(speed) / 35.0, 0.0, 1.0)
	var target: float = desired_height + sin(hover_phase) * IDLE_BOB_AMPLITUDE * bob_factor
	var acceleration: float = (target - height) * SPRING_STIFFNESS - vertical_velocity * SPRING_DAMPING
	vertical_velocity = clampf(vertical_velocity + acceleration * dt, -8.0, 8.0)
	height += vertical_velocity * dt
	# This is an anti-clipping suspension stop, *not* a hard road follower.
	# Flight/jumps bypass the suspension entirely.
	if height < desired_height - MAX_FALL_BELOW_DECK:
		height = desired_height - MAX_FALL_BELOW_DECK
		vertical_velocity = maxf(vertical_velocity, 0.0)
	elif height > desired_height + MAX_RISE_ABOVE_DECK:
		height = desired_height + MAX_RISE_ABOVE_DECK
		vertical_velocity = minf(vertical_velocity, 0.0)
	return height

static func horizontal_velocity(current: Vector3, forward: Vector3, speed: float, grip: float, delta: float, airborne: bool) -> Vector3:
	# Momentum stays in world space; heading and travel direction are distinct.
	# Strong longitudinal response keeps throttle precise, while slightly
	# slower lateral bleed produces a readable hovercraft slip/countersteer.
	var dt: float = clampf(delta, 0.0, 0.05)
	var planar := Vector3(current.x, 0.0, current.z)
	var longitudinal: Vector3 = forward * planar.dot(forward)
	var lateral: Vector3 = planar - longitudinal
	var drive_alpha: float = 1.0 - exp(-maxf(0.0, grip) * dt)
	var side_grip: float = grip * (1.0 if airborne else LATERAL_GRIP_FRACTION)
	var lateral_alpha: float = 1.0 - exp(-maxf(0.0, side_grip) * dt)
	return longitudinal.lerp(forward * speed, drive_alpha) + lateral * (1.0 - lateral_alpha)
