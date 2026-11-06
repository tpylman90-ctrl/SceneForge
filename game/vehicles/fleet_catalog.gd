extends RefCounted

const IDS := ["kestrel","piledriver","shrike","mantis","aurora","forge","synapse","tremor","aerolith","solstice"]
const NAMES := ["KESTREL","PYLDRIVER","SHRIKE","MANTIS","AURORA","FORGE","SYNAPSE","TREMOR","AEROLITH","SOLSTICE"]
const NOTES := ["Balanced raptor / slate and burnt orange", "Armored racer / purple and brass", "Wide-body interceptor / silver, lime and deep purple", "Stable utility racer / olive green", "Fast swept speedster / blue and copper", "Precision racer / graphite and amber", "AI racer / active four-point hover array and ion propulsion", "Tremor MK III / armored box SUV, tall roof and square hover pods", "Satin-titanium manta interceptor / twin vectored plasma turbines", "Low-canopy teal grand tourer / sculpted haunch, large ruby tails and vectored drive"]

# The user-approved Shrike GLB is now the main drive model as well as the showroom model.
# AEROLITH uses the optimized original LOD1 during races, and LOD0 in the garage.
# Both are installed after procedural Blender asset generation with strict checksums.
const SHRIKE_SHOWROOM_SCENE := "res://assets/showroom/shrike_uploaded.glb"
const AEROLITH_SHOWROOM_SCENE := "res://assets/showroom/aerolith.glb"
const KESTREL_USER_UPGRADE_SCENE := "res://assets/showroom/kestrel_user_upgrade.glb"

static func definition(index: int, presentation_only: bool = false) -> Resource:
	index=clampi(index,0,IDS.size()-1)
	var craft: Resource=preload("res://vehicles/kestrel.tres").duplicate(true)
	craft.chassis_id=IDS[index]
	craft.display_name=NAMES[index]+(" / MK III" if index==7 else " / MK I")
	if index==0:
		craft.footprint_stretch=1.7
		if ResourceLoader.exists(KESTREL_USER_UPGRADE_SCENE):
			# Original Kestrel cockpit and race handling remain intact.
			# The new user model is a +Z-forward 6.80 m exterior with larger
			# side haunches and rear feathers; fit the real underbody mounts.
			craft.mount_points=craft.mount_points.duplicate(true)
			craft.cockpit_eye=Vector3(0,1.83,.40)
			craft.cockpit_pitch=-.09
			craft.mount_points["repulsor_fl"]=Vector3(1.22,.39,1.86)
			craft.mount_points["repulsor_fr"]=Vector3(-1.22,.39,1.86)
			craft.mount_points["repulsor_rl"]=Vector3(1.33,.45,-1.75)
			craft.mount_points["repulsor_rr"]=Vector3(-1.33,.45,-1.75)
			craft.mount_points["propulsion"]=Vector3(0,1.10,-3.18)
			craft.mount_points["power_core"]=Vector3(0,1.16,-.24)
			craft.mount_points["aero_left"]=Vector3(-1.46,1.26,-1.72)
			craft.mount_points["aero_right"]=Vector3(1.46,1.26,-1.72)
			craft.accent_color=Color("ca6b2b")
	if index>0:
		craft.visual_scene="res://assets/fleet/"+IDS[index]+".glb"
		if index==2 and ResourceLoader.exists(SHRIKE_SHOWROOM_SCENE):
			# Also used by track driving; the original procedural GLB remains
			# available as a fallback asset, not as the default vehicle.
			craft.visual_scene=SHRIKE_SHOWROOM_SCENE
		if index==8 and presentation_only and ResourceLoader.exists(AEROLITH_SHOWROOM_SCENE):
			craft.visual_scene=AEROLITH_SHOWROOM_SCENE
		craft.mount_points=craft.mount_points.duplicate(true)
		craft.mount_points["repulsor_fl"]=Vector3(1,.58,2.1)
		craft.mount_points["repulsor_fr"]=Vector3(-1,.58,2.1)
		craft.mount_points["repulsor_rl"]=Vector3(1.12,.76,-.65)
		craft.mount_points["repulsor_rr"]=Vector3(-1.12,.76,-.65)
		craft.accent_color=[Color("66dcf0"),Color("b44dff"),Color("a6f018"),Color("91ed77"),Color("5d9fff"),Color("ff981c"),Color("9360ff"),Color("7dcaff"),Color("53cfe4"),Color("58d1c8")][index]
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
	if index==8:
		craft.footprint_stretch=1.32
		craft.cockpit_eye=Vector3(0,1.43,-.46)
		craft.cockpit_pitch=-.075
		# LOD1 ships with original hull/visor geometry and 6 embedded cells.
		# Mounts used for physics feedback are hidden beneath the monocoque.
		craft.mount_points["repulsor_fl"]=Vector3(1.25,.34,2.37)
		craft.mount_points["repulsor_fr"]=Vector3(-1.25,.34,2.37)
		craft.mount_points["repulsor_rl"]=Vector3(1.25,.34,-2.38)
		craft.mount_points["repulsor_rr"]=Vector3(-1.25,.34,-2.38)
		craft.mount_points["propulsion"]=Vector3(0,.90,-3.75)
		craft.mount_points["power_core"]=Vector3(0,1.02,-.12)
		craft.mount_points["aero_left"]=Vector3(-1.48,.73,-1.35)
		craft.mount_points["aero_right"]=Vector3(1.48,.73,-1.35)
	if index==9:
		# SOLSTICE uses its original connected-body 7.32 m Blender model.
		craft.display_name="SOLSTICE / S-01"
		craft.footprint_stretch=1.05
		craft.cockpit_eye=Vector3(0,1.48,-.44)
		craft.cockpit_pitch=-.055
		craft.mount_points["repulsor_fl"]=Vector3(1.08,.28,2.32)
		craft.mount_points["repulsor_fr"]=Vector3(-1.08,.28,2.32)
		craft.mount_points["repulsor_rl"]=Vector3(1.17,.28,-2.46)
		craft.mount_points["repulsor_rr"]=Vector3(-1.17,.28,-2.46)
		craft.mount_points["propulsion"]=Vector3(0,.595,-3.24)
		craft.mount_points["power_core"]=Vector3(0,.76,-.10)
		craft.mount_points["aero_left"]=Vector3(-1.42,.63,-2.10)
		craft.mount_points["aero_right"]=Vector3(1.42,.63,-2.10)
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
	craft.max_forward_speed=[32.0,30.0,34.0,31.0,35.0,32.0,37.0,29.0,35.0,34.5][index]
	craft.acceleration=[11.5,10.0,12.5,11.0,12.0,11.5,13.0,9.2,12.0,11.9][index]
	craft.yaw_rate=[1.28,1.23,1.40,1.32,1.26,1.28,1.31,1.16,1.22,1.23][index]
	craft.lateral_grip=[9.0,10.0,9.5,10.5,8.5,9.0,9.2,11.0,9.5,9.7][index]
	return craft
