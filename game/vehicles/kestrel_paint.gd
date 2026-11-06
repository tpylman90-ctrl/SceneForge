extends RefCounted

# SceneForge Kestrel S03 showroom + racing paint. The 4 actual GLB
# surfaces are: clearcoat slate (0), graphite (1), copper (2), glass (3).
# Imported source and detached original interior remain untouched.
static func apply(exterior: MeshInstance3D) -> Array[StandardMaterial3D]:
	assert(exterior!=null and exterior.mesh!=null)
	assert(exterior.mesh.get_surface_count()==4, "Expected 4 real Kestrel paint surfaces")
	var results: Array[StandardMaterial3D] = []
	for i in range(4):
		var mat := StandardMaterial3D.new()
		mat.cull_mode=BaseMaterial3D.CULL_DISABLED
		if i==0:
			mat.resource_name="Kestrel Stormsteel Pearl"
			mat.vertex_color_use_as_albedo=true
			mat.albedo_color=Color.WHITE
			mat.metallic=.56
			mat.roughness=.265
		elif i==1:
			mat.resource_name="Kestrel Blue Graphite"
			mat.vertex_color_use_as_albedo=true
			mat.albedo_color=Color.WHITE
			mat.metallic=.20
			mat.roughness=.57
		elif i==2:
			mat.resource_name="Kestrel Forged Copper"
			mat.vertex_color_use_as_albedo=true
			mat.albedo_color=Color.WHITE
			mat.metallic=.64
			mat.roughness=.32
		else:
			mat.resource_name="Kestrel Smoked Cyan Canopy"
			mat.vertex_color_use_as_albedo=false
			mat.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
			mat.albedo_color=Color(.26,.55,.64,.27)
			mat.metallic=.04
			mat.roughness=.18
		exterior.set_surface_override_material(i,mat)
		results.append(mat)
	assert(results[3].transparency==BaseMaterial3D.TRANSPARENCY_ALPHA)
	assert(results[0].roughness<results[1].roughness)
	assert(results[2].metallic>results[1].metallic)
	return results
