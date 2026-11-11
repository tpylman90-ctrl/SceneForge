extends CanvasLayer
## Persistent Android track transition overlay.
## Resource loading runs in the ResourceLoader worker; procedural course
## assembly runs on the scene thread while this CanvasLayer remains visible.
## Do not claim a complete GPU/texture bake: the warm-up only draws the
## start view and gives the Mobile/Vulkan pipeline several frames to settle.

const TRACK_SCENE := "res://city_loop.tscn"
const TRACK_NAMES := [
	"NEON CROSS", "SKYWAY", "VIPER RIFT", "IRON HARBOR",
	"CRIMSON SERPENT", "RED MESA CIRCUIT", "DEVIL'S GATE", "SKYFALL RUN"
]
const TRACK_DETAIL := [
	"SKYLINE / CROSSING", "SKYLINE / ELEVATED", "SKYLINE / TECHNICAL",
	"HARBOR / INDUSTRIAL", "CANYON / SPRINT", "DESERT / MESA",
	"DESERT / RIDGELINE", "SKYLINE TO SUMMIT / FLIGHT"
]

var _busy := false
var _screen: Control
var _track_title: Label
var _course_detail: Label
var _phase_label: Label
var _percent_label: Label
var _renderer_label: Label
var _meter: ProgressBar
var _back_button: Button


func _ready() -> void:
	layer = 120
	process_mode = Node.PROCESS_MODE_ALWAYS
	# Script-based CI checks use the headless display server and never open
	# the transition screen. Avoid allocating persistent themed GUI resources
	# in these short-lived tests; the visual Android game still builds it.
	if DisplayServer.get_name() == "headless" and "--script" in OS.get_cmdline_args():
		return
	_build_screen()
	_screen.hide()


func _build_screen() -> void:
	_screen = Control.new()
	_screen.name = "TrackLoadingScreen"
	_screen.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_screen.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_screen)

	var backdrop := ColorRect.new()
	backdrop.color = Color("080e19")
	backdrop.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_screen.add_child(backdrop)

	# Simple native, resolution-independent HUD: no extra textures or shader
	# dependencies are introduced just to display the loading interface.
	var top_rule := ColorRect.new()
	top_rule.color = Color("ef5548")
	top_rule.anchor_right = 1.0
	top_rule.offset_top = 0.0
	top_rule.offset_bottom = 5.0
	_screen.add_child(top_rule)

	var panel := VBoxContainer.new()
	panel.anchor_left = 0.12
	panel.anchor_right = 0.88
	panel.anchor_top = 0.24
	panel.anchor_bottom = 0.79
	panel.add_theme_constant_override("separation", 16)
	_screen.add_child(panel)

	var overline := Label.new()
	overline.text = "NEON FOUNDRY  /  RACE CONTROL"
	overline.add_theme_font_size_override("font_size", 19)
	overline.add_theme_color_override("font_color", Color("70d9e7"))
	panel.add_child(overline)

	_track_title = Label.new()
	_track_title.text = "PREPARING COURSE"
	_track_title.add_theme_font_size_override("font_size", 52)
	_track_title.add_theme_color_override("font_color", Color("f4f7fc"))
	panel.add_child(_track_title)

	_course_detail = Label.new()
	_course_detail.add_theme_font_size_override("font_size", 22)
	_course_detail.add_theme_color_override("font_color", Color("a3b8c9"))
	panel.add_child(_course_detail)

	var separator := ColorRect.new()
	separator.color = Color("29465a")
	separator.custom_minimum_size = Vector2(0, 2)
	panel.add_child(separator)

	var progress_row := HBoxContainer.new()
	panel.add_child(progress_row)
	_phase_label = Label.new()
	_phase_label.text = "REQUESTING COURSE"
	_phase_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_phase_label.add_theme_font_size_override("font_size", 21)
	_phase_label.add_theme_color_override("font_color", Color("e6a07b"))
	progress_row.add_child(_phase_label)
	_percent_label = Label.new()
	_percent_label.text = "0%"
	_percent_label.add_theme_font_size_override("font_size", 21)
	_percent_label.add_theme_color_override("font_color", Color("f4f7fc"))
	progress_row.add_child(_percent_label)

	_meter = ProgressBar.new()
	_meter.min_value = 0
	_meter.max_value = 100
	_meter.show_percentage = false
	_meter.custom_minimum_size = Vector2(0, 18)
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color("1a2b39")
	bg.set_corner_radius_all(5)
	_meter.add_theme_stylebox_override("background", bg)
	var fill := StyleBoxFlat.new()
	fill.bg_color = Color("ef5548")
	fill.set_corner_radius_all(5)
	_meter.add_theme_stylebox_override("fill", fill)
	panel.add_child(_meter)

	_renderer_label = Label.new()
	_renderer_label.add_theme_font_size_override("font_size", 18)
	_renderer_label.add_theme_color_override("font_color", Color("8aa8bd"))
	panel.add_child(_renderer_label)

	_back_button = Button.new()
	_back_button.text = "RETURN TO FOUNDRY"
	_back_button.custom_minimum_size = Vector2(300, 58)
	_back_button.pressed.connect(_return_to_foundry)
	panel.add_child(_back_button)
	_back_button.hide()

	var foot := Label.new()
	foot.anchor_left = 0.12
	foot.anchor_right = 0.88
	foot.anchor_top = 0.88
	foot.anchor_bottom = 0.96
	foot.text = "ASSEMBLING ROAD  /  SCENERY  /  VEHICLE  /  GPU WARM-UP"
	foot.add_theme_font_size_override("font_size", 17)
	foot.add_theme_color_override("font_color", Color("637f96"))
	_screen.add_child(foot)


func begin(scene_path: String = TRACK_SCENE) -> void:
	if _busy:
		return
	_busy = true
	var track_id := clampi(int(get_tree().get_meta("sceneforge_track", 0)), 0, TRACK_NAMES.size() - 1)
	_track_title.text = TRACK_NAMES[track_id] if scene_path == TRACK_SCENE else "PREPARING SCENE"
	_course_detail.text = TRACK_DETAIL[track_id] if scene_path == TRACK_SCENE else "LOADING SCENE ASSETS"
	_renderer_label.text = "RENDERER  /  %s  /  %s" % [
		RenderingServer.get_current_rendering_method().to_upper(),
		RenderingServer.get_current_rendering_driver_name().to_upper()
	]
	_back_button.hide()
	_set_stage("REQUESTING COURSE ASSETS", 0.0)
	_screen.show()
	_load_scene(scene_path)


func _set_stage(message: String, percentage: float) -> void:
	_phase_label.text = message
	_meter.value = clampf(percentage, 0.0, 100.0)
	_percent_label.text = "%d%%" % roundi(_meter.value)


func _load_scene(scene_path: String) -> void:
	# Ensure the transition actually draws before any potentially expensive
	# procedural work starts on the main thread.
	await get_tree().process_frame
	var request_error := ResourceLoader.load_threaded_request(scene_path)
	if request_error != OK and request_error != ERR_BUSY:
		_fail("COULD NOT REQUEST COURSE (%d)" % request_error)
		return

	var progress: Array = []
	while true:
		var status := ResourceLoader.load_threaded_get_status(scene_path, progress)
		if status == ResourceLoader.THREAD_LOAD_FAILED or status == ResourceLoader.THREAD_LOAD_INVALID_RESOURCE:
			_fail("COURSE ASSET LOAD FAILED")
			return
		if status == ResourceLoader.THREAD_LOAD_LOADED:
			break
		var ratio := float(progress[0]) if not progress.is_empty() else 0.0
		_set_stage("STREAMING COURSE ASSETS", ratio * 70.0)
		await get_tree().process_frame

	var scene := ResourceLoader.load_threaded_get(scene_path) as PackedScene
	if scene == null:
		_fail("INVALID COURSE SCENE")
		return

	_set_stage("ASSEMBLING ROAD AND SCENERY", 75.0)
	await get_tree().process_frame
	var change_error := get_tree().change_scene_to_packed(scene)
	if change_error != OK:
		_fail("COULD NOT INITIALIZE COURSE (%d)" % change_error)
		return
	# CityLoop._ready() builds its procedural road, hazards, terrain and car.
	# The autoload overlay survives the scene replacement and covers this work.
	await get_tree().scene_changed
	var active_scene := get_tree().current_scene
	if active_scene == null:
		_fail("COURSE DID NOT START")
		return
	active_scene.set_physics_process(false)
	_set_stage("WARMING UP RENDER PIPELINE", 92.0)
	# Give the completed 3D scene several visible-to-the-GPU frames behind
	# the opaque overlay before opening controls and the race countdown.
	for frame in range(4):
		await get_tree().process_frame

	if not is_instance_valid(active_scene):
		_fail("COURSE WAS INTERRUPTED")
		return
	if active_scene.has_method("finish_track_load"):
		active_scene.finish_track_load()
	else:
		active_scene.set_physics_process(true)
	_set_stage("COURSE READY", 100.0)
	await get_tree().process_frame
	_screen.hide()
	_busy = false


func _fail(message: String) -> void:
	_set_stage(message, _meter.value)
	_back_button.show()
	_busy = false
	push_error("SceneForge track loading: " + message)


func _return_to_foundry() -> void:
	if _busy:
		return
	_screen.hide()
	get_tree().change_scene_to_file("res://main.tscn")
