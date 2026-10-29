extends Node3D

const Fleet = preload("res://vehicles/fleet_catalog.gd")
var selected := 0
var craft: Node3D
var visual
var camera: Camera3D
var title: Label
var info: Label
var busy := false
var orbit := -0.62
var elevation := 0.30
var drag := false
var frames := 0
var cockpit := false
var fleet_panel: Control
var fleet_list: Control

func _ready() -> void:
	selected=clampi(int(get_tree().get_meta("sceneforge_craft",0)),0,Fleet.IDS.size()-1)
	for i in range(Fleet.IDS.size()):
		if "--craft-%d"%i in OS.get_cmdline_user_args():selected=i
	var env := WorldEnvironment.new()
	var settings := Environment.new()
	settings.background_mode=Environment.BG_SKY
	var sky := Sky.new()
	var pano := PanoramaSkyMaterial.new()
	pano.panorama=load("res://assets/twilight_sky.jpg")
	sky.sky_material=pano
	settings.sky=sky
	settings.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
	settings.ambient_light_color=Color("9fb9cf")
	settings.ambient_light_energy=0.8
	settings.tonemap_mode=Environment.TONE_MAPPER_FILMIC
	env.environment=settings
	add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees=Vector3(-40,-35,0)
	sun.light_energy=1.3
	sun.shadow_enabled=true
	add_child(sun)
	var floor := MeshInstance3D.new()
	var mesh := CylinderMesh.new()
	mesh.top_radius=7
	mesh.bottom_radius=7.2
	mesh.height=.25
	mesh.radial_segments=64
	floor.name="DisplayPlinth"
	floor.mesh=mesh
	floor.position.y=-.2
	var m := StandardMaterial3D.new()
	m.albedo_color=Color("263b49")
	m.roughness=.6
	m.metallic=.45
	floor.material_override=m
	add_child(floor)
	camera=Camera3D.new()
	camera.current=true
	camera.fov=48
	camera.near=.03
	add_child(camera)
	get_viewport().msaa_3d=Viewport.MSAA_2X
	var ui := CanvasLayer.new()
	add_child(ui)
	var panel := ColorRect.new()
	fleet_panel=panel
	panel.color=Color(.025,.05,.075,.94)
	panel.position=Vector2(20,20)
	panel.size=Vector2(325,570)
	ui.add_child(panel)
	var list := VBoxContainer.new()
	fleet_list=list
	list.position=Vector2(36,38)
	list.add_theme_constant_override("separation",12)
	ui.add_child(list)
	var heading := Label.new()
	heading.text="SCENEFORGE / FLEET"
	heading.add_theme_font_size_override("font_size",25)
	list.add_child(heading)
	for i in range(Fleet.IDS.size()):
		var button := Button.new()
		button.text=Fleet.NAMES[i]
		button.custom_minimum_size=Vector2(285,62)
		button.add_theme_font_size_override("font_size",23)
		button.pressed.connect(select_craft.bind(i))
		list.add_child(button)
	title=Label.new()
	title.position=Vector2(380,24)
	title.add_theme_font_size_override("font_size",30)
	ui.add_child(title)
	info=Label.new()
	info.position=Vector2(380,66)
	info.add_theme_font_size_override("font_size",20)
	ui.add_child(info)
	var row := HBoxContainer.new()
	row.position=Vector2(380,630)
	row.add_theme_constant_override("separation",12)
	ui.add_child(row)
	for label in ["FRONT","TAIL","COCKPIT","DRIVE","FOUNDRY"]:
		var button := Button.new()
		button.text=label
		button.custom_minimum_size=Vector2(155,66)
		button.pressed.connect(action.bind(label))
		row.add_child(button)
	spawn_craft()
	update_camera()
	if "--fleet-nose" in OS.get_cmdline_user_args():
		orbit=0.0
		elevation=.15
		update_camera()
	if "--fleet-tail" in OS.get_cmdline_user_args():action("TAIL")
	if "--fleet-cockpit" in OS.get_cmdline_user_args():action("COCKPIT")
	if "--fleet-side" in OS.get_cmdline_user_args():
		orbit=-PI/2
		elevation=.04
		update_camera()
	if "--fleet-under" in OS.get_cmdline_user_args():
		floor.hide()
		camera.h_offset=-1.65
		camera.position=craft.position+Vector3(-6,-2,5)
		camera.look_at(craft.position+Vector3(0,.65,0))
	if "--fleet-top" in OS.get_cmdline_user_args():
		camera.h_offset=0
		camera.position=craft.position+Vector3(0,11.5,.01)
		camera.look_at(craft.position,Vector3(0,0,-1))

func spawn_craft() -> void:
	craft=Node3D.new()
	craft.position.x=1.8
	add_child(craft)
	visual=preload("res://vehicles/kestrel_feedback.gd").new()
	craft.add_child(visual)
	var definition: Resource=Fleet.definition(selected)
	visual.configure(definition)
	visual.set_cockpit(cockpit)
	visual.update_feedback(1.0,0,0,0,0,0,cockpit)
	title.text=definition.display_name
	info.text=Fleet.NOTES[selected]+"\nCRUISE %d KM/H / Drag to orbit"%int(definition.max_forward_speed*3.6)
	get_tree().set_meta("sceneforge_craft",selected)

func select_craft(index: int) -> void:
	if busy:return
	busy=true
	visual.stop_audio()
	await get_tree().create_timer(.15).timeout
	craft.free()
	selected=index
	cockpit=false
	spawn_craft()
	update_camera()
	busy=false

func action(label: String) -> void:
	if busy:return
	if label=="DRIVE" or label=="FOUNDRY":
		busy=true
		visual.stop_audio()
		await get_tree().create_timer(.15).timeout
		get_tree().change_scene_to_file("res://city_loop.tscn" if label=="DRIVE" else "res://main.tscn")
		return
	cockpit=label=="COCKPIT"
	fleet_panel.visible=not cockpit
	fleet_list.visible=not cockpit
	visual.set_cockpit(cockpit)
	orbit=2.5 if label=="TAIL" else -.62
	update_camera()

func update_camera() -> void:
	if cockpit:
		camera.h_offset=0
		var definition: Resource=Fleet.definition(selected)
		camera.global_transform=visual.global_transform*Transform3D(Basis.from_euler(Vector3(definition.cockpit_pitch,PI,0)),definition.cockpit_eye)
	else:
		camera.h_offset=-1.65
		camera.position=craft.position+Vector3(sin(orbit)*9.0,2.0+elevation*5,cos(orbit)*9.0)
		camera.look_at(craft.position+Vector3(0,1.1,.4))

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:drag=event.pressed
	if event is InputEventMouseMotion and drag and not cockpit:
		orbit-=event.relative.x*.006
		elevation=clampf(elevation+event.relative.y*.003,.03,.85)
		update_camera()
	if event is InputEventScreenDrag and not cockpit:
		orbit-=event.relative.x*.006
		elevation=clampf(elevation+event.relative.y*.003,.03,.85)
		update_camera()

func _process(_delta: float) -> void:
	if "--capture" in OS.get_cmdline_user_args():
		frames+=1
		if frames==35:
			var suffix := ""
			for view in ["tail","cockpit","side","top","under","nose"]:
				if "--fleet-"+view in OS.get_cmdline_user_args():suffix="-"+view
			get_viewport().get_texture().get_image().save_png(OS.get_environment("GITHUB_WORKSPACE")+"/build/Fleet-"+Fleet.IDS[selected]+suffix+".png")
			visual.stop_audio()
			await get_tree().create_timer(.15).timeout
			get_tree().quit()
