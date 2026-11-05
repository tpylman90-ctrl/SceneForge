extends SceneTree

# Actual Terrain3D editor brush operation, run only in the isolated authoring
# project on GitHub Actions. The Android game never loads Terrain3D.
# Uses Terrain3DEditor.SCULPT/SUBTRACT and a feathered brush, then exports EXR.
const MAP_PATH = "res://heightmaps/serpent_seed.r16"
const ROUTE_PATH = "res://serpent_route.json"
const OUTPUT_PATH = "res://heightmaps/serpent_sculpt.exr"
const WIDTH = 1024
const HEIGHT = 512

func _initialize() -> void:
	call_deferred("_sculpt")

func _fail(message: String) -> void:
	printerr("TERRAIN3D_BRUSH_ERROR: ",message)
	quit(1)

func _make_seed() -> Image:
	var raw: PackedByteArray=FileAccess.get_file_as_bytes(MAP_PATH)
	if raw.size()!=WIDTH*HEIGHT*2:
		return null
	var image := Image.create(WIDTH,HEIGHT,false,Image.FORMAT_RF)
	for z in range(HEIGHT):
		for x in range(WIDTH):
			var encoded: int=raw.decode_u16(2*(z*WIDTH+x))
			image.set_pixel(x,z,Color(-32.0+160.0*float(encoded)/65535.0,0,0,1))
	return image

func _make_brush() -> Image:
	var mask := Image.create(128,128,false,Image.FORMAT_RF)
	for z in range(128):
		for x in range(128):
			var dx: float=(float(x)-63.5)/63.5
			var dz: float=(float(z)-63.5)/63.5
			var r: float=sqrt(dx*dx+dz*dz)
			var t: float=clampf(1.0-r,0.0,1.0)
			# Artist-style feathered brush, broad shelf at center and tapered edge.
			var weight: float=t*t*(3.0-2.0*t)
			mask.set_pixel(x,z,Color(weight,0,0,1))
	return mask

func _distance_to_route(x: float, z: float, route: Array) -> float:
	var best: float=INF
	for i in range(route.size()):
		var a: Array=route[i]
		var b: Array=route[(i+1)%route.size()]
		var dx: float=float(b[0])-float(a[0])
		var dz: float=float(b[2])-float(a[2])
		var denominator: float=maxf(0.0001,dx*dx+dz*dz)
		var t: float=clampf(((x-float(a[0]))*dx+(z-float(a[2]))*dz)/denominator,0.0,1.0)
		var px: float=float(a[0])+dx*t
		var pz: float=float(a[2])+dz*t
		best=minf(best,(x-px)*(x-px)+(z-pz)*(z-pz))
	return sqrt(best)

func _sculpt() -> void:
	if not ClassDB.class_exists("Terrain3D") or not ClassDB.class_exists("Terrain3DEditor"):
		_fail("Terrain3D v1.1 GDExtension not installed in authoring project")
		return
	var initial: Image=_make_seed()
	if initial==null:
		_fail("Invalid checked-in R16 heightmap")
		return
	var document: Variant=JSON.parse_string(FileAccess.get_file_as_string(ROUTE_PATH))
	if typeof(document)!=TYPE_DICTIONARY:
		_fail("Missing course spline preview route")
		return
	var route: Array=document.get("route",[])
	if route.size()!=192:
		_fail("Expected the actual 192-point Crimson Serpent road guide")
		return
	var terrain: Node3D=ClassDB.instantiate("Terrain3D") as Node3D
	if terrain==null:
		_fail("Terrain3D native class could not instantiate")
		return
	terrain.set("collision_mode",0)
	terrain.set("region_size",256)
	terrain.set("free_editor_textures",false)
	var editor_camera := Camera3D.new()
	editor_camera.position=Vector3(0,180,170)
	root.add_child(editor_camera)
	editor_camera.current=true
	terrain.set("clipmap_target",editor_camera)
	root.add_child(terrain)
	terrain.call("set_camera",editor_camera)
	await process_frame
	await process_frame
	var data: Object=terrain.get("data")
	if data==null:
		_fail("Terrain3DData unavailable")
		return
	var images: Array[Image]=[initial,null,null]
	data.call("import_images",images,Vector3(-512,0,-256),0.0,1.0)
	if int(data.call("get_region_count"))<8:
		_fail("Terrain3D failed to import 1024x512 source")
		return
	var editor: Object=ClassDB.instantiate("Terrain3DEditor")
	if editor==null:
		_fail("Terrain3DEditor native brush tool unavailable")
		return
	# Leave the editor plugin unset in command-line authoring mode. The
	# native Terrain3DEditor still applies brushes; an unrelated fake plugin
	# causes a C++ crash inside operate() rather than providing undo history.
	terrain.call("set_editor",editor)
	editor.call("set_terrain",terrain)
	var brush: Image=_make_brush()
	editor.call("set_brush_data",{
		"brush":[brush,ImageTexture.create_from_image(brush)],
		"size":28.0,
		"strength":68.0,
		"mouse_pressure":1.0,
		"gamma":1.0,
		"auto_regions":false,
		"align_to_view":false,
		"brush_spin_speed":0.0,
		"modifier_ctrl":false,
		"modifier_alt":false
	})
	editor.call("set_tool",1) # Terrain3DEditor.Tool.SCULPT
	editor.call("set_operation",1) # Terrain3DEditor.Operation.SUBTRACT
	var strokes: int=0
	var moved: float=0.0
	# Sculpt natural cut-back shelves along both sides of the long canyon,
	# skipping any area near a neighboring branch of road.
	for sector in [17,37,59,77,98,118,139,160,181]:
		var a: Array=route[sector]
		var b: Array=route[(sector+1)%route.size()]
		var direction:=Vector2(float(b[0])-float(a[0]),float(b[2])-float(a[2])).normalized()
		var side:=Vector2(direction.y,-direction.x)
		for sign in [-1.0,1.0]:
			var center: Vector2=Vector2(float(a[0]),float(a[2]))+side*float(sign)*44.0
			if _distance_to_route(center.x,center.y,route)<36.0:
				continue
			var center_pos:=Vector3(center.x,0,center.y)
			var before: float=data.call("get_height",center_pos)
			if is_nan(before):
				continue
			editor.call("start_operation",center_pos)
			# Connected brush stamps emulate a short drag through the cliff.
			for step in range(7):
				var offset: float=(float(step)-3.0)*3.8
				var at:=Vector3(center.x+direction.x*offset,0.0,center.y+direction.y*offset)
				editor.call("operate",at,0.0)
			editor.call("stop_operation")
			var after: float=data.call("get_height",center_pos)
			moved+=absf(before-after)
			strokes+=1
	if strokes<5 or moved<0.3:
		_fail("Terrain3D brushes did not deform enough rock; %d strokes delta=%0.3f" % [strokes,moved])
		return
	var export_error: int=data.call("export_image",OUTPUT_PATH,0,0)
	if export_error!=OK or not FileAccess.file_exists(OUTPUT_PATH):
		_fail("Terrain3D export_image failed: %d" % export_error)
		return
	print("TERRAIN3D_BRUSH_SCULPT_OK stamps=",strokes," sum_center_delta=",moved," regions=",data.call("get_region_count"))
	quit()
