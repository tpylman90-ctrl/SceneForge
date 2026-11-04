extends RefCounted

# Authored Crimson Divide course centerlines. Stable IDs 4-6.
# Catmull-Rom interpolation gives the player smooth, flowing turns while
# retaining distinct track silhouettes. No external meshes or AI content.
const FIRST_ID := 4
const LAST_ID := 6
const ROUTE_NAMES := ["CRIMSON SERPENT", "RED MESA CIRCUIT", "DEVIL'S GATE"]
const ROUTE_INFO := [
	"MEDIUM / Long flowing single-stage canyon sprint",
	"EASY / Wide mesa loop and sweeping horseshoe turns",
	"HARD / Tight red-rock gates, crests and ridge chicanes"
]
const CAPTURE_NAMES := ["CrimsonSerpent", "RedMesa", "DevilsGate"]
const REGION_SECTORS := [
	["SUNSTONE APPROACH","ARCH RUN","CLIFFSIDE SWEEPS","LOW CANYON"],
	["MESA PLATEAU","HORSESHOE RIDGE","BASIN CROSSING","RED ROCK RETURN"],
	["GATE APPROACH","STONE NEEDLES","BROKEN RIDGE","SPIRAL DESCENT"]
]
# Hand-authored controls ordered forward around each closed circuit.
# The sprint uses one long closed stage so existing steering, reset and
# checkpoint navigation stay compatible; a true point-to-point mode is later.
const SERPENT := [
	Vector2(220,0),Vector2(218,30),Vector2(180,61),Vector2(145,66),
	Vector2(110,42),Vector2(75,40),Vector2(37,70),Vector2(3,75),
	Vector2(-35,57),Vector2(-74,22),Vector2(-120,51),
	Vector2(-171,70),Vector2(-216,40),Vector2(-231,7),
	Vector2(-220,-28),Vector2(-195,-69),Vector2(-151,-79),
	Vector2(-109,-56),Vector2(-65,-89),Vector2(-15,-78),
	Vector2(36,-54),Vector2(86,-72),Vector2(138,-54),
	Vector2(188,-50),Vector2(220,-29)
]
const MESA := [
	Vector2(145,0),Vector2(138,55),Vector2(108,86),
	Vector2(65,96),Vector2(20,104),Vector2(-30,100),
	Vector2(-85,82),Vector2(-135,50),Vector2(-152,5),
	Vector2(-145,-42),Vector2(-110,-87),Vector2(-60,-98),
	Vector2(10,-94),Vector2(75,-77),Vector2(130,-45)
]
const GATE := [
	Vector2(125,0),Vector2(128,38),Vector2(93,59),
	Vector2(65,42),Vector2(40,22),Vector2(15,48),
	Vector2(-20,78),Vector2(-60,60),Vector2(-75,20),
	Vector2(-110,32),Vector2(-145,15),Vector2(-135,-30),
	Vector2(-98,-60),Vector2(-65,-40),Vector2(-37,-75),
	Vector2(0,-90),Vector2(35,-65),Vector2(60,-80),
	Vector2(85,-48),Vector2(112,-30)
]

static func controls(track_id: int) -> Array:
	match track_id:
		4: return SERPENT
		5: return MESA
		6: return GATE
		_: return []

static func point(track_id: int, index: int, count: int) -> Vector2:
	var controls_array: Array=controls(track_id)
	var size: int=controls_array.size()
	assert(size>=4 and count>=size)
	var position: float=float(posmod(index,count))*float(size)/float(count)
	var section: int=floori(position)
	var u: float=position-float(section)
	var p0: Vector2=controls_array[posmod(section-1,size)]
	var p1: Vector2=controls_array[section%size]
	var p2: Vector2=controls_array[(section+1)%size]
	var p3: Vector2=controls_array[(section+2)%size]
	return 0.5*(p1*2.0+(p2-p0)*u+(p0*2.0-p1*5.0+p2*4.0-p3)*u*u+(-p0+p1*3.0-p2*3.0+p3)*u*u*u)

static func ground_height(track_id: int, index: int, count: int) -> float:
	var a: float=TAU*float(posmod(index,count))/float(count)
	if track_id==4:
		# Longer climbs and descents for the carved Serpent canyon only;
		# measured grades remain gentle enough for the hovercraft physics.
		return 6.0+2.5*sin(a+0.3)+1.7*sin(a*2.0-0.75)+1.0*sin(a*4.0+0.4)
	if track_id==5:
		return 4.0+1.8*sin(a+0.2)
	return 5.2+2.1*sin(a*2.0-0.35)+0.7*sin(a*4.0)

static func half_width(track_id: int, index: int) -> float:
	match track_id:
		4: return 10.5 if index>=86 and index<=126 else 12.0
		5: return 13.0
		6: return 8.9 if index>=60 and index<=122 else 10.3
		_: return 8.0

static func bank(track_id: int, index: int, count: int) -> float:
	if track_id==6:
		return 0.07*sin(TAU*float(index)/float(count)*3.0)
	if track_id==4:
		return 0.035*sin(TAU*float(index)/float(count)*2.0)
	return 0.0

static func sector(track_id: int, index: int, count: int) -> String:
	var key: int=clampi(track_id-FIRST_ID,0,REGION_SECTORS.size()-1)
	var sector_index: int=clampi(int(float(index)*4.0/float(count)),0,3)
	return REGION_SECTORS[key][sector_index]

static func route_length(track_id: int, count: int) -> float:
	var length := 0.0
	for index in range(count):
		length+=point(track_id,index,count).distance_to(point(track_id,index+1,count))
	return length
