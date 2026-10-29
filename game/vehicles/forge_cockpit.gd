extends "res://vehicles/pyldriver_cockpit.gd"

func build() -> void:
	super.build()
	name="ForgeCockpitInstruments"
	# Fit this fascia to FORGE's narrower canopy and put the display behind the glass.
	transform=Transform3D(Basis.from_scale(Vector3(.66,1,.75)),Vector3(0,-.03,-.08))
	var yoke_detail: Node3D=get_node("YokeDetail")
	# The common feedback code reparents these buttons onto the existing yoke.
	yoke_detail.transform=transform.affine_inverse()
	for node in find_children("*","MeshInstance3D",true,false):
		if node.name in ["FlightDisplay","HolographicDisplay"]:continue
		var material := node.material_override as StandardMaterial3D
		if material and material.shading_mode==BaseMaterial3D.SHADING_MODE_UNSHADED:
			material.albedo_color=Color("ff9c35")
