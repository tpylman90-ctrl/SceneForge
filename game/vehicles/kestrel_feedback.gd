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
var hover_glow_materials: Array[StandardMaterial3D] = []
var synapse_thrusters: Array[MeshInstance3D] = []
var sound: AudioStreamPlayer3D
var muted := true
var visual_roll := 0.0
var visual_pitch := 0.0
var motion_clock := 0.0
var last_drive := 0.0
var showroom_upload := false
var windshield_prepared := false
var windshield_faces := 0
var windshield_windows: Array[MeshInstance3D] = []
var solstice_brake_lamps: Array[StandardMaterial3D] = []
var solstice_engine_materials: Array[StandardMaterial3D] = []
# Fused user Kestrel exterior is separate from the original functioning cockpit
# and articulated drive rig, so one does not erase the other.
const KESTREL_USER_UPGRADE_PATH := "res://assets/showroom/kestrel_user_upgrade.glb"
var kestrel_upgrade: Node3D
var kestrel_legacy_shell_meshes: Array[MeshInstance3D] = []
var kestrel_real_glass: StandardMaterial3D

func configure(definition: Resource) -> void:
	chassis = definition
	if chassis.chassis_id=="synapse":
		configure_synapse(definition)
		return
	if chassis.chassis_id=="aerolith":
		configure_aerolith(definition)
		return
	if chassis.chassis_id=="solstice":
		configure_solstice(definition)
		return
	showroom_upload=chassis.chassis_id=="shrike" and chassis.visual_scene.ends_with("/showroom/shrike_uploaded.glb")
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
	if showroom_upload:
		# Keep the same eight garage component markers without installing
		# Kestrel's synthetic cockpit, repulsor rings, HUD or exhaust.
		build_component_mounts()
		build_audio()
		# Original baked surface remains intact in exterior view. On first
		# cockpit entry, isolate a conservative painted-windscreen patch so it
		# can be hidden without modifying the rest of the approved vehicle.
		# Do not install a synthetic interior in this windshield-only trial.
		print("SCENEFORGE_SHRIKE_UPLOADED_SHOWROOM_OK")
		return
	var details: Node3D
	if chassis.chassis_id=="kestrel":
		details=preload("res://vehicles/kestrel_cockpit.gd").new()
		add_child(details)
		details.build()
	elif chassis.chassis_id=="piledriver":
		details=preload("res://vehicles/pyldriver_cockpit.gd").new()
		add_child(details)
		details.build()
	elif chassis.chassis_id=="forge":
		details=preload("res://vehicles/forge_cockpit.gd").new()
		add_child(details)
		details.build()
	elif chassis.chassis_id=="shrike":
		details=preload("res://vehicles/shrike_cockpit.gd").new()
		add_child(details)
		details.build()
	elif chassis.chassis_id=="tremor":
		details=preload("res://vehicles/tremor_cockpit.gd").new()
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
	if chassis.chassis_id in ["kestrel","piledriver","forge"]:
		var hologram: MeshInstance3D=details.get_node("HolographicDisplay")
		var holo: StandardMaterial3D=screen.duplicate()
		holo.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
		holo.blend_mode=BaseMaterial3D.BLEND_MODE_ADD
		holo.albedo_color=Color(.72,.96,1,.82) if chassis.chassis_id=="forge" else Color(.35,.9,1,.55)
		holo.cull_mode=BaseMaterial3D.CULL_DISABLED
		hologram.material_override=holo
	for node in find_children("*","MeshInstance3D",true,false):
		for surface in range(node.mesh.get_surface_count()):
			var mat: Material = node.get_active_material(surface)
			if mat is StandardMaterial3D and node != display:
				mat.vertex_color_use_as_albedo = true
				if "vehicle_glass" in node.name:
					if chassis.chassis_id in ["kestrel","piledriver","forge","shrike","tremor"]:
						mat=mat.duplicate()
						mat.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
						mat.albedo_color=Color(.032,.055,.075,.54) if chassis.chassis_id=="tremor" else Color(.018,.026,.047,.70 if chassis.chassis_id=="shrike" else .36)
						mat.metallic=.09 if chassis.chassis_id=="shrike" else .15
						mat.cull_mode=BaseMaterial3D.CULL_DISABLED
						node.set_surface_override_material(surface,mat)
					var inside: StandardMaterial3D = mat.duplicate()
					inside.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
					inside.albedo_color = Color(0.1,0.18,0.22,0.08 if chassis.chassis_id=="piledriver" else 0.12)
					inside.metallic = 0.0
					glass.append({"mesh":node,"surface":surface,"outside":mat,"inside":inside})
	build_component_mounts()
	build_exhaust()
	build_audio()
	if chassis.chassis_id=="kestrel":
		configure_kestrel_uploaded_body()

# Upgrade Kestrel's EXTERIOR using the user's real high-detail imported GLB.
# The uploaded asset is one fused mesh with no independent glazing or door;
# retain the verified original cockpit/hologram and 5-channel flight rig.
func configure_kestrel_uploaded_body() -> void:
	if not ResourceLoader.exists(KESTREL_USER_UPGRADE_PATH):
		push_warning("User Kestrel upgrade not installed; procedural Kestrel remains operational")
		return
	var source: PackedScene=load(KESTREL_USER_UPGRADE_PATH)
	assert(source!=null,"Kestrel user upgrade GLB is not a PackedScene")
	kestrel_upgrade=source.instantiate()
	kestrel_upgrade.name="Kestrel_User_Upgrade"
	add_child(kestrel_upgrade)
	var exterior: MeshInstance3D=kestrel_upgrade.find_child("Kestrel_User_Upgrade_Exterior",true,false) as MeshInstance3D
	assert(exterior!=null and exterior.mesh!=null,"Original imported Kestrel exterior mesh missing")
	assert(exterior.mesh.get_surface_count()==2,"Kestrel repaired body + glass surfaces missing")
	assert(exterior.mesh.surface_get_array_index_len(0)/3>30000,
		"Kestrel body geometry did not survive processing")
	assert(exterior.mesh.surface_get_array_index_len(1)/3>4000,
		"Kestrel independent tinted glass missing")
	# The original model had no vertex normals and very dark vertex colors.
	# The installer now calculates actual normals, separates the windshield,
	# and raises the satin-slate palette; avoid a black metallic override.
	var finish:=StandardMaterial3D.new()
	finish.albedo_color=Color.WHITE
	finish.vertex_color_use_as_albedo=true
	finish.metallic=.27
	finish.roughness=.40
	finish.cull_mode=BaseMaterial3D.CULL_DISABLED
	exterior.set_surface_override_material(0,finish)
	kestrel_real_glass=StandardMaterial3D.new()
	kestrel_real_glass.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
	kestrel_real_glass.albedo_color=Color(.27,.48,.57,.30)
	kestrel_real_glass.metallic=.06
	kestrel_real_glass.roughness=.21
	kestrel_real_glass.cull_mode=BaseMaterial3D.CULL_DISABLED
	kestrel_real_glass.vertex_color_use_as_albedo=false
	exterior.set_surface_override_material(1,kestrel_real_glass)
	# Keep original Kestrel source rig intact but visually suppressed in chase
	# and garage views, avoiding double fenders and duplicate tail feathers.
	for child in get_children():
		if child is MeshInstance3D and str(child.name).begins_with("Kestrel_"):
			kestrel_legacy_shell_meshes.append(child as MeshInstance3D)
			child.visible=false
	if yoke!=null:
		yoke.visible=false
	for tail in tails:
		tail.visible=false
	assert(kestrel_legacy_shell_meshes.size()>0,"Kestrel cockpit fallback shell missing")
	assert(tails.size()==5 and yoke!=null,"Kestrel steering/yoke controls lost")
	print("SCENEFORGE_KESTREL_REPAIRED_SURFACES_OK",
		exterior.mesh.surface_get_array_index_len(0)/3,
		exterior.mesh.surface_get_array_index_len(1)/3)
	print("SCENEFORGE_KESTREL_USER_BODY_UPGRADE_OK",
		(exterior.mesh.surface_get_array_index_len(0)+
		exterior.mesh.surface_get_array_index_len(1))/3)

# SOLSTICE has its own genuine parametric Blender mesh and embedded engine.
# It intentionally does not depend on the legacy Kestrel tail/yoke rig.
func configure_solstice(definition: Resource) -> void:
	var body: Node3D=load(definition.visual_scene).instantiate()
	body.name="SOLSTICE_Original_Body"
	add_child(body)
	telemetry.craft_name=definition.display_name
	for candidate in body.find_children("*","MeshInstance3D",true,false):
		var mesh_node: MeshInstance3D=candidate as MeshInstance3D
		if mesh_node.mesh==null:
			continue
		var lower: String=str(mesh_node.name).to_lower()
		var is_glass: bool=lower.contains("windscreen") or lower.ends_with("_glazing")
		var is_lamp: bool=lower.contains("upper_red_rear_signature") or lower.contains("rear_led_rib") or lower.contains("rear_light_endcap")
		var is_drive: bool=lower.contains("thrust_amber_capsule") or lower.contains("_flux_ring")
		if not (is_glass or is_lamp or is_drive):
			continue
		for surface in range(mesh_node.mesh.get_surface_count()):
			var imported: Material=mesh_node.get_active_material(surface)
			if not imported is StandardMaterial3D:
				continue
			var active: StandardMaterial3D=(imported as StandardMaterial3D).duplicate()
			if is_glass:
				active.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
				active.albedo_color.a=.42
				active.cull_mode=BaseMaterial3D.CULL_DISABLED
				var inside: StandardMaterial3D=active.duplicate()
				inside.albedo_color.a=.085
				inside.metallic=0.0
				mesh_node.set_surface_override_material(surface,active)
				glass.append({"mesh":mesh_node,"surface":surface,
					"outside":active,"inside":inside})
			elif is_lamp:
				active.emission_enabled=true
				active.emission=Color(.96,.025,.013)
				active.emission_energy_multiplier=1.6
				mesh_node.set_surface_override_material(surface,active)
				solstice_brake_lamps.append(active)
			else:
				active.emission_enabled=true
				active.emission=Color(.94,.39,.10)
				active.emission_energy_multiplier=1.1
				mesh_node.set_surface_override_material(surface,active)
				solstice_engine_materials.append(active)
	assert(body.find_child("SOLSTICE_UNIFIED_OUTER_SKIN",true,false)!=null)
	assert(body.find_child("SOLSTICE_Port_Upper_Red_Rear_Signature",true,false)!=null)
	assert(body.find_child("SOLSTICE_Starboard_Upper_Red_Rear_Signature",true,false)!=null)
	assert(glass.size()>=4,"SOLSTICE must retain independent transparent cabin glazing")
	assert(solstice_brake_lamps.size()>=8,"SOLSTICE LED mesh layers missing")
	assert(solstice_engine_materials.size()>=5,"SOLSTICE hover and engine fields missing")
	build_component_mounts()
	build_repulsor_footprints()
	build_audio()
	print("SCENEFORGE_SOLSTICE_PLAYABLE_BODY_OK")

# AEROLITH is a completely original Blender craft from Assetwright.
# Unlike the legacy vehicle exporters, its mesh has no "Kestrel_*" rig.
# Preserve the complete node hierarchy and use its real thruster locations.
func configure_aerolith(definition: Resource) -> void:
	var body: Node3D=load(definition.visual_scene).instantiate()
	body.name="Aerolith_Original_Body"
	add_child(body)
	telemetry.craft_name=definition.display_name
	setup_aerolith_glass(body)
	build_component_mounts()
	build_repulsor_footprints()
	build_aerolith_thrusters()
	build_audio()
	print("SCENEFORGE_AEROLITH_DRIVE_MODEL_OK")

func setup_aerolith_glass(body: Node3D) -> void:
	for node in body.find_children("*","MeshInstance3D",true,false):
		var label: String=str(node.name).to_lower()
		if not (label.contains("visor") or label.contains("side glazing")):
			continue
		for surface in range(node.mesh.get_surface_count()):
			var source: Material=node.get_active_material(surface)
			if not source is StandardMaterial3D:
				continue
			var outside: StandardMaterial3D=source.duplicate()
			outside.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
			outside.albedo_color=Color(.035,.12,.18,.59)
			outside.cull_mode=BaseMaterial3D.CULL_DISABLED
			outside.metallic=.16
			var inside: StandardMaterial3D=outside.duplicate()
			inside.albedo_color=Color(.04,.10,.15,.10)
			inside.metallic=0.0
			node.set_surface_override_material(surface,outside)
			glass.append({"mesh":node,"surface":surface,
				"outside":outside,"inside":inside})

func build_aerolith_thrusters() -> void:
	var material: StandardMaterial3D=glow()
	material.albedo_color=Color(.19,.76,1.0,.55)
	material.emission_enabled=true
	material.emission=Color(.08,.50,.94)
	material.emission_energy_multiplier=1.5
	hover_glow_materials.append(material)
	for x in [-1.06,1.06]:
		var plume:=MeshInstance3D.new()
		plume.name="Aerolith_VectorPlume"
		var cone:=CylinderMesh.new()
		cone.top_radius=.035
		cone.bottom_radius=.25
		cone.height=1.0
		cone.radial_segments=20
		plume.mesh=cone
		plume.material_override=material
		plume.rotation.x=-PI/2
		plume.position=Vector3(x,.89,-4.05)
		plume.visible=false
		plume.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(plume)
		synapse_thrusters.append(plume)

func configure_synapse(definition: Resource) -> void:
	var body: Node3D=load(definition.visual_scene).instantiate()
	body.name="Synapse_Body"
	add_child(body)
	telemetry.craft_name=definition.display_name
	setup_synapse_glass(body)
	build_component_mounts()
	build_synapse_hover_units()
	build_repulsor_footprints()
	build_synapse_thrusters()
	build_audio()

func setup_synapse_glass(body: Node3D) -> void:
	for node in body.find_children("*","MeshInstance3D",true,false):
		if not node.name.to_lower().contains("glass"):continue
		for surface in range(node.mesh.get_surface_count()):
			var source:Material=node.get_active_material(surface)
			if source==null or not source is StandardMaterial3D:continue
			var outside:StandardMaterial3D=source.duplicate()
			outside.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
			outside.albedo_color=Color(.025,.045,.22,.34)
			outside.cull_mode=BaseMaterial3D.CULL_DISABLED
			outside.metallic=.16
			var inside:StandardMaterial3D=outside.duplicate()
			inside.albedo_color=Color(.025,.045,.22,.10)
			glass.append({"mesh":node,"surface":surface,"outside":outside,"inside":inside})

func build_component_mounts() -> void:
	var mounts := Node3D.new()
	mounts.name = "ComponentMounts"
	add_child(mounts)
	for slot in chassis.mount_points:
		var mount := Marker3D.new()
		mount.name = slot
		mount.position = chassis.mount_points[slot]
		mount.set_meta("component_category","repulsor" if str(slot).begins_with("repulsor") else ("aero" if str(slot).begins_with("aero") else str(slot)))
		mounts.add_child(mount)

func build_audio() -> void:
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

func build_synapse_hover_units() -> void:
	var casing_material := StandardMaterial3D.new()
	casing_material.albedo_color=Color("101629")
	casing_material.metallic=.78
	casing_material.roughness=.28
	var alloy_material := StandardMaterial3D.new()
	alloy_material.albedo_color=Color("485273")
	alloy_material.metallic=.86
	alloy_material.roughness=.22
	var glow_material := glow()
	glow_material.albedo_color=Color(.48,.19,1.0,.78)
	glow_material.emission_enabled=true
	glow_material.emission=Color(.25,.06,1.0)
	glow_material.emission_energy_multiplier=.8
	var seal_material := glow()
	seal_material.albedo_color=Color(.16,.62,1.0,.9)
	seal_material.emission_enabled=true
	seal_material.emission=Color(.05,.32,1.0)
	seal_material.emission_energy_multiplier=1.2
	hover_glow_materials.append(glow_material)
	hover_glow_materials.append(seal_material)
	for slot in ["repulsor_fl","repulsor_fr","repulsor_rl","repulsor_rr"]:
		var point:Vector3=chassis.mount_points[slot]
		var casing := MeshInstance3D.new()
		casing.name="Synapse_Repulsor_"+slot
		var shell := CylinderMesh.new()
		shell.top_radius=.33
		shell.bottom_radius=.30
		shell.height=.23
		shell.radial_segments=32
		casing.mesh=shell
		casing.material_override=casing_material
		casing.position=point+Vector3(0,-.12,0)
		add_child(casing)
		var lip := MeshInstance3D.new()
		lip.name="Synapse_Repulsor_Rim_"+slot
		var rim := TorusMesh.new()
		rim.inner_radius=.285
		rim.outer_radius=.325
		rim.rings=16
		rim.ring_segments=8
		lip.mesh=rim
		lip.material_override=alloy_material
		lip.position=point+Vector3(0,-.25,0)
		add_child(lip)
		var field := MeshInstance3D.new()
		field.name="Synapse_Repulsor_Field_"+slot
		var field_mesh := TorusMesh.new()
		field_mesh.inner_radius=.225
		field_mesh.outer_radius=.265
		field_mesh.rings=20
		field_mesh.ring_segments=8
		field.mesh=field_mesh
		field.material_override=glow_material
		field.position=point+Vector3(0,-.255,0)
		add_child(field)
		var emitter := MeshInstance3D.new()
		emitter.name="Synapse_Repulsor_Emitter_"+slot
		var lens := CylinderMesh.new()
		lens.top_radius=.20
		lens.bottom_radius=.16
		lens.height=.045
		lens.radial_segments=24
		emitter.mesh=lens
		emitter.material_override=seal_material
		emitter.position=point+Vector3(0,-.265,0)
		add_child(emitter)

func build_synapse_thrusters() -> void:
	var plume_material:=glow()
	plume_material.albedo_color=Color(.18,.48,1.0,.72)
	plume_material.emission_enabled=true
	plume_material.emission=Color(.06,.24,1.0)
	plume_material.emission_energy_multiplier=1.5
	hover_glow_materials.append(plume_material)
	for x in [-.73,0.0,.73]:
		var plume:=MeshInstance3D.new()
		plume.name="Synapse_IonPlume"
		var nozzle:=CylinderMesh.new()
		nozzle.top_radius=.025
		nozzle.bottom_radius=.16 if is_zero_approx(x) else .12
		nozzle.height=1.0
		nozzle.radial_segments=20
		plume.mesh=nozzle
		plume.material_override=plume_material
		plume.rotation.x=-PI/2
		plume.visible=false
		add_child(plume)
		synapse_thrusters.append(plume)

func build_repulsor_footprints() -> void:
	var rings:=MultiMeshInstance3D.new()
	rings.name="RepulsorFootprints"
	var ring_mesh:=TorusMesh.new()
	ring_mesh.inner_radius=.24
	ring_mesh.outer_radius=.29
	ring_mesh.rings=20
	ring_mesh.ring_segments=6
	ring_mesh.material=glow()
	var instances:=MultiMesh.new()
	instances.transform_format=MultiMesh.TRANSFORM_3D
	instances.mesh=ring_mesh
	instances.instance_count=4
	for i in range(4):
		var slot:String=["repulsor_fl","repulsor_fr","repulsor_rl","repulsor_rr"][i]
		var point:Vector3=chassis.mount_points[slot]
		var pos:=Vector3(point.x,.025,point.z)
		footprint_positions.append(pos)
		instances.set_instance_transform(i,Transform3D(Basis.from_scale(Vector3(1,1,chassis.footprint_stretch)),pos))
	rings.multimesh=instances
	rings.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	get_parent().add_child(rings)

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
	# Forge's magnetic hardware is fully buried in the monocoque; do not draw
	# the generic floating footprint halos beneath its body.
	if chassis.chassis_id != "forge":
		build_repulsor_footprints()

func set_cockpit(enabled: bool) -> void:
	if showroom_upload:
		if enabled and not windshield_prepared:
			windshield_prepared=true
			var cut: Dictionary=preload("res://vehicles/shrike_windshield.gd").isolate(self,chassis.cockpit_eye)
			windshield_faces=int(cut["faces"])
			windshield_windows.assign(cut["windows"])
		for window in windshield_windows:
			window.visible=not enabled
		display_clock=1.0
		return
	if kestrel_upgrade!=null:
		# A fused opaque shell cannot have only its glass hidden. In cockpit
		# view we temporarily reveal the original transparent cockpit rig.
		kestrel_upgrade.visible=not enabled
		for legacy in kestrel_legacy_shell_meshes:
			legacy.visible=enabled
		yoke.visible=enabled
		for tail in tails:
			tail.visible=enabled
	for entry in glass:
		var mesh: MeshInstance3D = entry["mesh"]
		mesh.set_surface_override_material(entry["surface"],entry["inside"] if enabled else entry["outside"])
	display_clock = 1.0

func update_feedback(delta: float, signed_speed: float, drive: float, steering: float, acceleration: float, slip: float, cockpit: bool, boosting: bool = false, charge: float = 100.0, flight_pitch: float = 0.0) -> void:
	if showroom_upload:
		# Original Shrike with a cockpit-only reversible windshield cutout.
		# This pass does not invent or replace the missing interior.
		last_drive=drive
		motion_clock+=delta
		var fraction:=clampf(absf(signed_speed)/chassis.max_forward_speed,0.0,1.0)
		visual_roll=lerpf(visual_roll,steering*.07*fraction,1-exp(-delta*6.0))
		visual_pitch=lerpf(visual_pitch,flight_pitch+clampf(acceleration*.001,-.022,.018),1-exp(-delta*5.0))
		rotation=Vector3(visual_pitch,0,visual_roll)
		position.y=sin(motion_clock*3.0)*.012*fraction
		if sound!=null:
			sound.pitch_scale=.86+fraction*.47+drive*.10
			sound.volume_db=-80 if muted else -28+fraction*6+drive*4
		display_clock+=delta
		if display_clock>=.35:
			display_clock=0.0
			telemetry.update(signed_speed,drive,steering,slip,boosting,charge)
		return
	if chassis.chassis_id=="solstice":
		last_drive=drive
		motion_clock+=delta
		var fraction: float=clampf(absf(signed_speed)/chassis.max_forward_speed,0.0,1.0)
		visual_roll=lerpf(visual_roll,steering*.095*fraction,1-exp(-delta*7.0))
		visual_pitch=lerpf(visual_pitch,flight_pitch+clampf(acceleration*.0014,-.025,.022),1-exp(-delta*5.0))
		rotation=Vector3(visual_pitch,0,visual_roll)
		position.y=sin(motion_clock*3.15)*.013*fraction
		var braking: bool=acceleration< -2.0 or drive< -.15
		for lamp in solstice_brake_lamps:
			lamp.emission_energy_multiplier=3.1 if braking else 1.4
		for emitter in solstice_engine_materials:
			emitter.emission_energy_multiplier=1.0+drive*.65+fraction*.45+(1.0 if boosting else 0.0)
		if sound!=null:
			sound.pitch_scale=.82+fraction*.55+drive*.13
			sound.volume_db=-80 if muted else -27+fraction*5+drive*5
		display_clock+=delta
		if display_clock>=(.1 if cockpit else .45):
			display_clock=0.0
			telemetry.update(signed_speed,drive,steering,slip,boosting,charge)
		return
	if chassis.chassis_id=="aerolith":
		last_drive=drive
		motion_clock+=delta
		var fraction:=clampf(absf(signed_speed)/chassis.max_forward_speed,0.0,1.0)
		visual_roll=lerpf(visual_roll,steering*.10*fraction,1-exp(-delta*7.0))
		visual_pitch=lerpf(visual_pitch,flight_pitch+clampf(acceleration*.0015,-.028,.023),1-exp(-delta*5.0))
		rotation=Vector3(visual_pitch,0,visual_roll)
		position.y=sin(motion_clock*3.25)*.017*fraction
		var plume_len:=.15+drive*.60+fraction*.22+(.25 if boosting else 0.0)
		for plume in synapse_thrusters:
			plume.visible=drive>.04 or boosting
			plume.scale=Vector3(1.0,plume_len,1.0)
			plume.position.z=-3.94-plume_len*.51
		for material in hover_glow_materials:
			material.emission_energy_multiplier=1.1+drive*.8+fraction*.6
		if sound!=null:
			sound.pitch_scale=.83+fraction*.55+drive*.10
			sound.volume_db=-80 if muted else -27+fraction*5+drive*5
		display_clock+=delta
		if display_clock>= (.1 if cockpit else .5):
			display_clock=0.0
			telemetry.update(signed_speed,drive,steering,slip,boosting,charge)
		return
	if chassis.chassis_id=="synapse":
		last_drive=drive
		motion_clock+=delta
		var amount:=clampf(absf(signed_speed)/chassis.max_forward_speed,0.0,1.0)
		visual_roll=lerpf(visual_roll,steering*.10*amount,1-exp(-delta*7.0))
		visual_pitch=lerpf(visual_pitch,clampf(acceleration*.0015,-.025,.02)+flight_pitch,1-exp(-delta*5.0))
		rotation=Vector3(visual_pitch,0,visual_roll)
		position.y=sin(motion_clock*3.4)*.022*amount
		for material in hover_glow_materials:
			material.emission_energy_multiplier=1.0+drive*1.6+amount*.8+(1.0 if boosting else 0.0)
		var plume_length:float=.18+drive*.72+amount*.24+(.32 if boosting else 0.0)
		for plume in synapse_thrusters:
			plume.visible=drive>.025 or boosting
			plume.scale=Vector3(1.0,plume_length,1.0)
			plume.position.z=-4.63-plume_length*.48
		if sound!=null:
			sound.pitch_scale=.82+amount*.60+drive*.12+(.18 if boosting else 0.0)
			sound.volume_db=-80 if muted else -27+drive*5+amount*2
		display_clock+=delta
		if display_clock>=(.1 if cockpit else .5):
			display_clock=0.0
			telemetry.update(signed_speed,drive,steering,slip,boosting,charge)
		return
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
		if chassis.chassis_id=="kestrel" and kestrel_upgrade!=null:
			# The uploaded raptor has its own longer rear body. Five exhaust
			# field tails exit just behind the imported rear feather cluster.
			base=Vector3((i-2)*.33,1.11,-3.15)
			exhaust.visible=drive>.045 or absf(signed_speed)>5.0 or boosting
		if chassis.chassis_id=="shrike":
			# Drive exhaust through the five recessed rear induction outlets.
			# Old Kestrel positions floated ABOVE the canopy as five white dots.
			base=Vector3((i-2)*.24,.73,-3.57)
			exhaust.visible=drive>.04 or absf(signed_speed)>4.0 or boosting
		if chassis.chassis_id=="tremor":
			# Rear vectors never pierce the cabin. Only show active plumes.
			base=Vector3((i-2)*.23,1.04,-3.49)
			exhaust.visible=drive>.06 or absf(signed_speed)>5.0 or boosting
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

