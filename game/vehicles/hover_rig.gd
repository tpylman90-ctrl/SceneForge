extends RigidBody3D
## Independent real-collision hover test rig (not an NF-H01 production model).
## Four downward surface probes push on the body at separate mount points.
## This is intentionally a reusable craft controller, not route-following code.

const SENSOR_MOUNTS := [
	Vector3(-0.95, 0.0, 1.55), Vector3(0.95, 0.0, 1.55),
	Vector3(-0.95, 0.0, -1.55), Vector3(0.95, 0.0, -1.55)
]
const HOVER_HEIGHT := 1.48
const MIN_HEIGHT := 1.10
const MAX_HEIGHT := 5.50
const HEIGHT_RATE := 3.25
const SPRING_ACCEL := 32.0
const SPRING_DAMP := 10.0
const YAW_RATE := 1.28
const SIDE_GRIP := 2.9
const AIR_GRIP := 0.35
const REVERSE_DELAY := 0.28

var probes: Array[RayCast3D] = []
var contact_count := 0
var ground_distance := 0.0
var thrust_requested := false
var brake_requested := false
var boost_requested := false
var steering := 0.0
var reverse_hold := 0.0
var throttle_axis := 0.0
var climb_axis := 0.0
var hover_clearance := HOVER_HEIGHT
var deck_y := 0.0

func _ready() -> void:
	mass = 350.0
	gravity_scale = 1.0
	linear_damp = 0.06
	angular_damp = 0.08
	continuous_cd = true
	collision_mask = 3 # Actual floor and separate obstacle collision layers
	can_sleep = false
	var surface := PhysicsMaterial.new()
	surface.friction = 0.1
	surface.bounce = 0.24
	physics_material_override = surface
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(2.18, 0.74, 4.2)
	shape.shape = box
	add_child(shape)
	var chassis_mesh := MeshInstance3D.new()
	var hull := BoxMesh.new()
	hull.size = Vector3(2.14, 0.69, 4.13)
	chassis_mesh.mesh = hull
	chassis_mesh.material_override = material(Color("30434f"),0.5)
	add_child(chassis_mesh)
	var nose := MeshInstance3D.new()
	var nose_mesh := BoxMesh.new()
	nose_mesh.size = Vector3(1.1,0.12,0.70)
	nose.mesh = nose_mesh
	nose.position = Vector3(0,0.39,1.48)
	nose.material_override = material(Color("ff793f"),0.35)
	add_child(nose)
	for mount in SENSOR_MOUNTS:
		var ray := RayCast3D.new()
		ray.position = mount
		ray.target_position = Vector3(0,-8.0,0)
		ray.collision_mask = 1
		ray.exclude_parent = true
		ray.enabled = true
		add_child(ray)
		probes.append(ray)
		var visual := MeshInstance3D.new()
		var cell := CylinderMesh.new()
		cell.top_radius = 0.30
		cell.bottom_radius = 0.38
		cell.height = 0.18
		visual.mesh = cell
		visual.position = mount + Vector3(0,-0.42,0)
		visual.material_override = material(Color("39c6e5"),0.55)
		add_child(visual)

func material(color: Color, metal: float) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color=color
	mat.metallic=metal
	mat.roughness=0.42
	return mat

func set_controls(thrust_on: bool, brake_on: bool, turn: float, boost_on: bool) -> void:
	# Preserve legacy tests and keyboard controls.
	set_analog_controls(1.0 if thrust_on else (-1.0 if brake_on else 0.0),turn,0.0,boost_on)

func set_analog_controls(throttle: float, turn: float, climb: float, boost_on: bool) -> void:
	throttle_axis=clampf(throttle,-1.0,1.0)
	thrust_requested=throttle_axis>0.10
	brake_requested=throttle_axis< -0.10
	steering=clampf(turn,-1.0,1.0)
	climb_axis=clampf(climb,-1.0,1.0)
	boost_requested=boost_on

func advance_height_target(delta: float) -> void:
	hover_clearance=clampf(hover_clearance+climb_axis*HEIGHT_RATE*maxf(delta,0.0),MIN_HEIGHT,MAX_HEIGHT)

func forward_vector() -> Vector3:
	var v := global_transform.basis.z
	v.y=0.0
	return v.normalized() if v.length_squared()>0.0001 else Vector3.BACK

func forward_speed() -> float:
	return linear_velocity.dot(forward_vector())

func lateral_speed() -> float:
	var forward := forward_vector()
	var side := Vector3(forward.z,0,-forward.x)
	return linear_velocity.dot(side)

func _physics_process(delta: float) -> void:
	advance_height_target(delta)
	contact_count=0
	ground_distance=0.0
	var normal_sum := Vector3.ZERO
	var floor_total := 0.0
	for ray in probes:
		ray.force_raycast_update()
		if not ray.is_colliding():
			continue
		var normal: Vector3=ray.get_collision_normal()
		if normal.dot(Vector3.UP)<0.50:
			continue
		var distance: float=ray.global_position.distance_to(ray.get_collision_point())
		floor_total+=ray.get_collision_point().y
		var offset: Vector3=ray.global_position-global_position
		var point_velocity: Vector3=linear_velocity+angular_velocity.cross(offset)
		var acceleration: float=9.81+SPRING_ACCEL*(hover_clearance-distance)-SPRING_DAMP*point_velocity.dot(Vector3.UP)
		var force: float=clampf(acceleration,0.0,65.0)*mass/4.0
		apply_force(Vector3.UP*force,offset)
		contact_count+=1
		ground_distance+=distance
		normal_sum+=normal
	if contact_count>0:
		ground_distance/=float(contact_count)
		deck_y=floor_total/float(contact_count)
	# Align to a real averaged surface normal, not to the race spline.
	var target_up: Vector3=normal_sum.normalized() if contact_count>=2 else Vector3.UP
	var tilt_error: Vector3=global_transform.basis.y.normalized().cross(target_up)
	var tilt_damping := Vector3(angular_velocity.x,0,angular_velocity.z)
	apply_torque((tilt_error*15.0-tilt_damping*3.0)*mass)
	var forward := forward_vector()
	var speed_along: float=linear_velocity.dot(forward)
	var turn_authority: float=clampf(speed_along/8.0,-1.0,1.0)
	var target_yaw: float=steering*YAW_RATE*turn_authority*(0.48 if contact_count==0 else 1.0)
	apply_torque(Vector3.UP*(target_yaw-angular_velocity.y)*mass*4.0)
	var speed_limit: float=44.0 if boost_requested else 34.0
	if brake_requested:
		if speed_along>0.5:
			apply_central_force(-forward*mass*22.0*absf(throttle_axis))
			reverse_hold=0.0
		else:
			reverse_hold+=delta
			if reverse_hold>=REVERSE_DELAY and speed_along>-9.0:
				apply_central_force(-forward*mass*5.5*absf(throttle_axis))
	elif thrust_requested or boost_requested:
		reverse_hold=0.0
		if speed_along < -0.5:
			apply_central_force(forward*mass*22.0)
		elif speed_along<speed_limit:
			apply_central_force(forward*mass*(17.0 if boost_requested else 11.5)*maxf(throttle_axis,0.25 if boost_requested else 0.0))
	else:
		reverse_hold=0.0
	var side := Vector3(forward.z,0,-forward.x)
	var side_velocity: Vector3=side*linear_velocity.dot(side)
	apply_central_force(-side_velocity*mass*(SIDE_GRIP if contact_count>=2 else AIR_GRIP))
	if not thrust_requested and not brake_requested and not boost_requested:
		apply_central_force(-forward*speed_along*mass*0.42)

func _integrate_forces(state: PhysicsDirectBodyState3D) -> void:
	# Contact must come from real sensor rays. No invisible floor over gaps.
	var pose: Transform3D=state.transform
	var original_y: float=pose.origin.y
	pose.origin.y=minf(original_y,deck_y+MAX_HEIGHT)
	if contact_count>0:
		pose.origin.y=maxf(pose.origin.y,deck_y+MIN_HEIGHT)
	if pose.origin.y!=original_y:
		state.transform=pose
		var velocity: Vector3=state.linear_velocity
		if (pose.origin.y<original_y and velocity.y>0.0) or (pose.origin.y>original_y and velocity.y<0.0):
			velocity.y=0.0
		state.linear_velocity=velocity

func reset_to(where: Vector3) -> void:
	freeze=true
	global_transform=Transform3D(Basis.IDENTITY,where)
	linear_velocity=Vector3.ZERO
	angular_velocity=Vector3.ZERO
	reverse_hold=0.0
	hover_clearance=HOVER_HEIGHT
	deck_y=0.0
	set_analog_controls(0.0,0.0,0.0,false)
	freeze=false
	sleeping=false
