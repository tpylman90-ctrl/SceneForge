extends Node3D

var chassis: Resource
var telemetry := preload("res://vehicles/cockpit_telemetry.gd").new()
var display_clock := 0.0
var yoke: Node3D
var yoke_rest := Transform3D.IDENTITY
var tails: Array[Node3D] = []
var tail_rest: Array[Transform3D] = []
var glass: Array[Dictionary] = []
var exhaust: MultiMeshInstance3D
var footprint_positions: PackedVector3Array = []
var sound: AudioStreamPlayer3D
var muted := true
var visual_roll := 0.0
var visual_pitch := 0.0
var motion_clock := 0.0
var last_drive := 0.0

func configure(definition: Resource) -> void:
	chassis = definition
	var source: Node3D = load(chassis.visual_scene).instantiate()
	telemetry.craft_name=chassis.display_name
	add_child(source)
	for child in source.get_children():
		if str(child.name).begins_with("Kestrel_") or str(child.name).begins_with("TailVector") or child.name == "DriverDoor":
			child.reparent(self,true)
	remove_child(source)
	source.queue_free()
	yoke = find_child("Kestrel_Yoke",true,false)
	assert(yoke != null,"Missing articulated Kestrel yoke")
	yoke_rest = yoke.transform
	for i in range(5):
		var tail: Node3D = find_child("Kestrel_Tail_%d"%i,true,false)
		assert(tail != null,"Missing vectoring tail vane")
		tails.append(tail)
		tail_rest.append(tail.transform)
	var details: Node3D
	if chassis.chassis_id=="piledriver":
		details=preload("res://vehicles/pyldriver_cockpit.gd").new()
		add_child(details)
		details.build()
	elif chassis.chassis_id=="forge":
		details=preload("res://vehicles/forge_cockpit.gd").new()
		add_child(details)
		details.build()
	else:
		var factory := preload("res://foundry.gd").new()
		factory.build_cockpit_details()
		details=factory.get_node("KestrelCockpitInstruments")
		details.reparent(self,false)
		factory.free()
	var yoke_details: Node3D = details.get_node("YokeDetail")
	yoke_details.reparent(yoke,true)
	var display: MeshInstance3D = details.get_node_or_null("FlightDisplay")
	var screen := StandardMaterial3D.new()
	screen.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
	if display != null:
		screen=display.material_override.duplicate()
	screen.albedo_texture = telemetry.texture
	screen.vertex_color_use_as_albedo = false
	if display != null:
		display.material_override = screen
	if chassis.chassis_id in ["piledriver","forge"]:
		var hologram: MeshInstance3D=details.get_node("HolographicDisplay")
		var holo: StandardMaterial3D=screen.duplicate()
		holo.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
		holo.blend_mode=BaseMaterial3D.BLEND_MODE_ADD
		holo.albedo_color=Color(1,.55,.16,.55) if chassis.chassis_id=="forge" else Color(.35,.9,1,.55)
		holo.cull_mode=BaseMaterial3D.CULL_DISABLED
		hologram.material_override=holo
	for node in find_children("*","MeshInstance3D",true,false):
		for surface in range(node.mesh.get_surface_count()):
			var mat: Material = node.get_active_material(surface)
			if mat is StandardMaterial3D and node != display:
				mat.vertex_color_use_as_albedo = true
				if "vehicle_glass" in node.name:
					if chassis.chassis_id in ["piledriver","forge"]:
						mat=mat.duplicate()
						mat.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
						mat.albedo_color=Color(.08,.16,.22,.36)
						mat.metallic=.15
						mat.cull_mode=BaseMaterial3D.CULL_DISABLED
						node.set_surface_override_material(surface,mat)
					var inside: StandardMaterial3D = mat.duplicate()
					inside.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
					inside.albedo_color = Color(0.1,0.18,0.22,0.08 if chassis.chassis_id=="piledriver" else 0.12)
					inside.metallic = 0.0
					glass.append({"mesh":node,"surface":surface,"outside":mat,"inside":inside})
	var mounts := Node3D.new()
	mounts.name = "ComponentMounts"
	add_child(mounts)
	for slot in chassis.mount_points:
		var mount := Marker3D.new()
		mount.name = slot
		mount.position = chassis.mount_points[slot]
		mount.set_meta("component_category","repulsor" if str(slot).begins_with("repulsor") else ("aero" if str(slot).begins_with("aero") else str(slot)))
		mounts.add_child(mount)
	build_exhaust()
	var hum: AudioStreamWAV = load("res://assets/kestrel_hum.wav")
	hum.loop_mode = AudioStreamWAV.LOOP_FORWARD
	hum.loop_end = int(hum.get_length()*hum.mix_rate)
	sound = AudioStreamPlayer3D.new()
	sound.stream = hum
	sound.unit_size = 8
	sound.max_distance = 30
	sound.volume_db = -80
	add_child(sound)
	if DisplayServer.get_name() != "headless":
		sound.play()

func glow() -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.albedo_color = Color(chassis.accent_color,0.45)
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	return m

func build_exhaust() -> void:
	exhaust = MultiMeshInstance3D.new()
	exhaust.name = "VectorExhaust"
	var mesh := CylinderMesh.new()
	mesh.top_radius = 0.10
	mesh.bottom_radius = 0.015
	mesh.height = 1.0
	mesh.radial_segments = 12
	mesh.rings = 1
	mesh.material = glow()
	var instances := MultiMesh.new()
	instances.transform_format = MultiMesh.TRANSFORM_3D
	instances.mesh = mesh
	instances.instance_count = 5
	exhaust.multimesh = instances
	exhaust.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(exhaust)
	var rings := MultiMeshInstance3D.new()
	rings.name = "RepulsorFootprints"
	var ring := TorusMesh.new()
	ring.inner_radius = 0.24
	ring.outer_radius = 0.29
	ring.rings = 20
	ring.ring_segments = 6
	ring.material = glow()
	var pods := MultiMesh.new()
	pods.transform_format = MultiMesh.TRANSFORM_3D
	pods.mesh = ring
	pods.instance_count = 4
	for i in range(4):
		var slot: String = ["repulsor_fl","repulsor_fr","repulsor_rl","repulsor_rr"][i]
		var point: Vector3 = chassis.mount_points[slot]
		footprint_positions.append(Vector3(point.x,0.025,point.z))
		pods.set_instance_transform(i,Transform3D(Basis.from_scale(Vector3(1,1,chassis.footprint_stretch)),footprint_positions[i]))
	rings.multimesh = pods
	rings.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	get_parent().add_child(rings)

func set_cockpit(enabled: bool) -> void:
	for entry in glass:
		var mesh: MeshInstance3D = entry["mesh"]
		mesh.set_surface_override_material(entry["surface"],entry["inside"] if enabled else entry["outside"])
	display_clock = 1.0

func update_feedback(delta: float, signed_speed: float, drive: float, steering: float, acceleration: float, slip: float, cockpit: bool, boosting: bool = false, charge: float = 100.0, flight_pitch: float = 0.0) -> void:
	last_drive = drive
	motion_clock += delta
	var amount := clampf(absf(signed_speed)/20,0,1)
	visual_roll = lerpf(visual_roll,steering*0.13*amount,1-exp(-delta*8))
	visual_pitch = lerpf(visual_pitch,clampf(acceleration*0.002,-0.035,0.025)+flight_pitch,1-exp(-delta*5))
	rotation = Vector3(visual_pitch,0,visual_roll)
	position.y = sin(motion_clock*3.0)*0.018*amount
	yoke.transform = yoke_rest*Transform3D(Basis(Vector3.BACK,steering*0.22),Vector3.ZERO)
	for i in range(5):
		var fan := float(i-2)/2
		var vector := Basis.from_euler(Vector3(visual_pitch*1.5,steering*(0.09+absf(fan)*0.035)*amount,fan*drive*0.025))
		tails[i].transform = tail_rest[i]*Transform3D(vector,Vector3.ZERO)
		var yy := 3.24-absf(i-2)*0.06
		var base := Vector3((i-2)*0.42,0.2+yy*sin(deg_to_rad(6))+1.125*cos(deg_to_rad(6)),0.8-yy*cos(deg_to_rad(6))+1.125*sin(deg_to_rad(6)))
		if chassis.chassis_id=="piledriver":
			base=Vector3((i-2)*.36,1.9201,-2.34)
		var length := 0.10+drive*0.58+absf(signed_speed)/32*0.20+(0.35 if boosting else 0.0)
		var nozzle_motion := tails[i].transform*tail_rest[i].affine_inverse()
		var axis := nozzle_motion.basis*Basis(Vector3.RIGHT,PI/2)*Basis.from_scale(Vector3(1,length,1))
		exhaust.multimesh.set_instance_transform(i,Transform3D(axis,nozzle_motion*(base+Vector3(0,0,-length*0.5))))
	if sound != null:
		sound.pitch_scale = 0.78+absf(signed_speed)/32*0.65+drive*0.12+(0.18 if boosting else 0.0)
		sound.volume_db = -80 if muted else -25+drive*5+amount*2
	display_clock += delta
	if display_clock >= (0.1 if cockpit else 0.5):
		display_clock = 0.0
		telemetry.update(signed_speed,drive,steering,slip,boosting,charge)

func stop_audio() -> void:
	if sound != null:
		sound.stop()
		sound.stream = null

func _exit_tree() -> void:
	stop_audio()

