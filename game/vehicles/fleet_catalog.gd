extends RefCounted

const IDS := ["kestrel","piledriver","shrike","mantis","aurora","forge","synapse","tremor"]
const NAMES := ["KESTREL","PYLDRIVER","SHRIKE","MANTIS","AURORA","FORGE","SYNAPSE","TREMOR"]
const NOTES := ["Balanced raptor / slate and burnt orange", "Armored racer / purple and brass", "Wide-body interceptor / silver, lime and deep purple", "Stable utility racer / olive green", "Fast swept speedster / blue and copper", "Precision racer / graphite and amber", "AI racer / active four-point hover array and ion propulsion", "Armored heavy interceptor / reinforced drives and exposed reactor"]

# Garage/showroom override deliberately leaves the racing asset untouched.
# If the user-supplied GLB has not been installed, the original Shrike remains
# available; no broken missing-asset reference is ever introduced.
const SHRIKE_SHOWROOM_SCENE := "res://assets/showroom/shrike_uploaded.glb"

static func definition(index: int, presentation_only: bool = false) -> Resource:
	index=clampi(index,0,IDS.size()-1)
	var craft: Resource=preload("res://vehicles/kestrel.tres").duplicate(true)
	craft.chassis_id=IDS[index]
	craft.display_name=NAMES[index]+" / MK I"
	if index==0:craft.footprint_stretch=1.7
	if index>0:
		craft.visual_scene="res://assets/fleet/"+IDS[index]+".glb"
		if index==2 and presentation_only and ResourceLoader.exists(SHRIKE_SHOWROOM_SCENE):
			craft.visual_scene=SHRIKE_SHOWROOM_SCENE
		craft.mount_points=craft.mount_points.duplicate(true)
		craft.mount_points["repulsor_fl"]=Vector3(1,.58,2.1)
		craft.mount_points["repulsor_fr"]=Vector3(-1,.58,2.1)
		craft.mount_points["repulsor_rl"]=Vector3(1.12,.76,-.65)
		craft.mount_points["repulsor_rr"]=Vector3(-1.12,.76,-.65)
		craft.accent_color=[Color("66dcf0"),Color("b44dff"),Color("a6f018"),Color("91ed77"),Color("5d9fff"),Color("ff981c"),Color("9360ff"),Color("7dcaff")][index]
	if index==2:
		# Shrike MK I cockpit is lower than Kestrel and inside its sculpted
		# panoramic canopy. The eye looks forward through the windshield.
		craft.cockpit_eye=Vector3(0,1.48,-.38)
		craft.cockpit_pitch=-.08
		craft.mount_points["repulsor_fl"]=Vector3(1.14,.33,2.07)
		craft.mount_points["repulsor_fr"]=Vector3(-1.14,.33,2.07)
		craft.mount_points["repulsor_rl"]=Vector3(1.21,.33,-2.42)
		craft.mount_points["repulsor_rr"]=Vector3(-1.21,.33,-2.42)
	if index==1:
		craft.footprint_stretch=2.6
		craft.cockpit_eye=Vector3(0,1.942,-.22)
		craft.mount_points["repulsor_fl"]=Vector3(.48,.26675,1.95)
		craft.mount_points["repulsor_fr"]=Vector3(-.48,.26675,1.95)
		craft.mount_points["repulsor_rl"]=Vector3(.48,.56475,-1.25)
		craft.mount_points["repulsor_rr"]=Vector3(-.48,.56475,-1.25)
	if index==5:
		craft.cockpit_eye=Vector3(0,1.78,-.35)
	if index==7:
		craft.footprint_stretch=1.14
		craft.cockpit_eye=Vector3(0,1.85,-.30)
		craft.cockpit_pitch=-.08
		craft.mount_points["repulsor_fl"]=Vector3(1.51,.26,1.77)
		craft.mount_points["repulsor_fr"]=Vector3(-1.51,.26,1.77)
		craft.mount_points["repulsor_rl"]=Vector3(1.51,.26,-2.10)
		craft.mount_points["repulsor_rr"]=Vector3(-1.51,.26,-2.10)
		craft.mount_points["propulsion"]=Vector3(0,1.08,-3.40)
		craft.mount_points["power_core"]=Vector3(0,1.47,-2.31)
	if index==6:
		craft.footprint_stretch=1.15
		craft.cockpit_eye=Vector3(0,.91,-.62)
		craft.cockpit_pitch=-.06
		craft.mount_points["repulsor_fl"]=Vector3(1.02,-.17,1.55)
		craft.mount_points["repulsor_fr"]=Vector3(-1.02,-.17,1.55)
		craft.mount_points["repulsor_rl"]=Vector3(1.18,-.20,-2.60)
		craft.mount_points["repulsor_rr"]=Vector3(-1.18,-.20,-2.60)
		craft.mount_points["propulsion"]=Vector3(0,.38,-3.98)
		craft.mount_points["power_core"]=Vector3(0,-.02,-.40)
		craft.mount_points["aero_left"]=Vector3(-1.28,.28,-1.75)
		craft.mount_points["aero_right"]=Vector3(1.28,.28,-1.75)
	craft.max_forward_speed=[32.0,30.0,34.0,31.0,35.0,32.0,37.0,29.0][index]
	craft.acceleration=[11.5,10.0,12.5,11.0,12.0,11.5,13.0,9.2][index]
	craft.yaw_rate=[1.28,1.23,1.40,1.32,1.26,1.28,1.31,1.16][index]
	craft.lateral_grip=[9.0,10.0,9.5,10.5,8.5,9.0,9.2,11.0][index]
	return craft
