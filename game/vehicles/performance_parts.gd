extends RefCounted

# Race-earned mechanical tuning. No meshes, materials or visual rigs change.
# Credits are shared; installed part levels belong to each chassis.
const SAVE_PATH := "user://performance_parts.cfg"
const PARTS := ["drive", "stability", "capacitor"]
const NAMES := ["THRUST DRIVE", "STABILITY GYROS", "BOOST CAPACITOR"]
const BENEFITS := [
	"Acceleration and maximum speed",
	"Cornering grip and yaw response",
	"Boost speed and recharge"
]
const MAX_LEVEL := 3
const COSTS := [125, 300, 575]
const RACE_REWARD := 150
const RECORD_BONUS := 25

static func part_cost(next_level: int) -> int:
	if next_level<1 or next_level>MAX_LEVEL:
		return 0
	return COSTS[next_level-1]

static func balance(path: String = SAVE_PATH) -> int:
	var cfg := ConfigFile.new()
	if cfg.load(path)!=OK:
		return 0
	return maxi(0,int(cfg.get_value("economy","credits",0)))

static func level(craft_id: String, part_id: String, path: String = SAVE_PATH) -> int:
	if craft_id.is_empty() or not PARTS.has(part_id):
		return 0
	var cfg := ConfigFile.new()
	if cfg.load(path)!=OK:
		return 0
	return clampi(int(cfg.get_value("parts/"+craft_id,part_id,0)),0,MAX_LEVEL)

static func buy(craft_id: String, part_id: String, path: String = SAVE_PATH) -> bool:
	if craft_id.is_empty() or not PARTS.has(part_id):
		return false
	var cfg := ConfigFile.new()
	cfg.load(path)
	var installed: int=clampi(int(cfg.get_value("parts/"+craft_id,part_id,0)),0,MAX_LEVEL)
	if installed>=MAX_LEVEL:
		return false
	var price: int=part_cost(installed+1)
	var credits: int=maxi(0,int(cfg.get_value("economy","credits",0)))
	if credits<price:
		return false
	cfg.set_value("economy","credits",credits-price)
	cfg.set_value("parts/"+craft_id,part_id,installed+1)
	return cfg.save(path)==OK

static func award_race(total_seconds: float, personal_best: bool, path: String = SAVE_PATH) -> int:
	# Called once when a completed three-lap solo challenge is classified.
	if is_nan(total_seconds) or is_inf(total_seconds) or total_seconds<=0.0:
		return 0
	var cfg := ConfigFile.new()
	cfg.load(path)
	var credits: int=maxi(0,int(cfg.get_value("economy","credits",0)))
	var amount: int=RACE_REWARD+(RECORD_BONUS if personal_best else 0)
	cfg.set_value("economy","credits",credits+amount)
	cfg.set_value("economy","races_completed",maxi(0,int(cfg.get_value("economy","races_completed",0)))+1)
	if cfg.save(path)!=OK:
		return 0
	return amount

static func apply_to_chassis(craft: Resource, path: String = SAVE_PATH) -> void:
	# Only mutate a fresh duplicated race definition. Do not call on a
	# displayed garage mesh or modify the canonical .tres values.
	var cfg := ConfigFile.new()
	if cfg.load(path)!=OK:
		return
	var section := "parts/"+str(craft.chassis_id)
	var drive_level: int=clampi(int(cfg.get_value(section,"drive",0)),0,MAX_LEVEL)
	var stability_level: int=clampi(int(cfg.get_value(section,"stability",0)),0,MAX_LEVEL)
	var capacitor_level: int=clampi(int(cfg.get_value(section,"capacitor",0)),0,MAX_LEVEL)
	craft.acceleration+=0.75*drive_level
	craft.max_forward_speed+=0.6*drive_level
	craft.lateral_grip+=0.5*stability_level
	craft.yaw_rate+=0.025*stability_level
	craft.boost_speed_bonus+=0.75*capacitor_level
	craft.boost_recharge+=1.5*capacitor_level
