extends SceneTree

# Convert Terrain3D's edited 32-bit EXR to the 16-bit height source used by
# the mobile game. This script deliberately has no terrain plugin dependency.
const Crimson = preload("res://tracks/crimson_divide.gd")
const OUT_PATH = "res://tracks/serpent_sculpt/height.r16"
const WIDTH = 1024
const HEIGHT = 512
const MIN_M = -32.0
const MAX_M = 128.0
const ORIGIN_X = -512.0
const ORIGIN_Z = -256.0

func _initialize() -> void:
	call_deferred("_run")

func _die(reason: String) -> void:
	printerr("SERPENT_SCULPT_IMPORT_ERROR: ",reason)
	quit(1)

func _sample(image: Image, x: float, z: float) -> float:
	var u: float=clampf(x-ORIGIN_X,0.0,float(WIDTH-1))
	var v: float=clampf(z-ORIGIN_Z,0.0,float(HEIGHT-1))
	var ix: int=floori(u)
	var iz: int=floori(v)
	var jx: int=mini(ix+1,WIDTH-1)
	var jz: int=mini(iz+1,HEIGHT-1)
	var a: float=lerpf(image.get_pixel(ix,iz).r,image.get_pixel(jx,iz).r,u-float(ix))
	var b: float=lerpf(image.get_pixel(ix,jz).r,image.get_pixel(jx,jz).r,u-float(ix))
	return lerpf(a,b,v-float(iz))

func _run() -> void:
	var args: PackedStringArray=OS.get_cmdline_user_args()
	var source: String=""
	for index in range(args.size()-1):
		if args[index]=="--source":
			source=args[index+1]
	if source.is_empty():
		_die("Required: -- --source <full_path_to_Terrain3D_height_export.exr>")
		return
	var image := Image.new()
	var err: int=image.load(source)
	if err!=OK:
		_die("Cannot open heightmap EXR: %s (error %d)" % [source,err])
		return
	if image.get_width()!=WIDTH or image.get_height()!=HEIGHT:
		_die("Expected 1024x512 image at 1m resolution, got %dx%d" % [image.get_width(),image.get_height()])
		return
	var bytes := PackedByteArray()
	bytes.resize(WIDTH*HEIGHT*2)
	for z in range(HEIGHT):
		for x in range(WIDTH):
			var h: float=image.get_pixel(x,z).r
			if h!=h or h<MIN_M or h>MAX_M:
				_die("Invalid height at (%d,%d): %f m" % [x,z,h])
				return
			var normalized: float=(h-MIN_M)/(MAX_M-MIN_M)
			bytes.encode_u16(2*(z*WIDTH+x),clampi(roundi(normalized*65535.0),0,65535))
	# Never allow a painting mistake to block the real driveable deck.
	for index in range(192):
		var xy: Vector2=Crimson.point(4,index,192)
		var next_xy: Vector2=Crimson.point(4,index+1,192)
		var forward: Vector2=(next_xy-xy).normalized()
		var lateral:=Vector2(forward.y,-forward.x)
		var road_y: float=Crimson.ground_height(4,index,192)
		var half_width: float=Crimson.half_width(4,index)
		for offset in [-half_width,-half_width*0.5,0.0,half_width*0.5,half_width]:
			var point: Vector2=xy+lateral*offset
			var wall_height: float=_sample(image,point.x,point.y)
			if wall_height>road_y-0.6:
				_die("Sculpt intersects road near sample %d (road %.2f, terrain %.2f)" % [index,road_y,wall_height])
				return
	var f: FileAccess=FileAccess.open(OUT_PATH,FileAccess.WRITE)
	if f==null:
		_die("Could not write " + OUT_PATH)
		return
	f.store_buffer(bytes)
	f.close()
	print("SERPENT_SCULPT_BAKE_OK %s (%dx%d)" % [OUT_PATH,WIDTH,HEIGHT])
	quit()
