extends RefCounted

# Non-destructive cockpit-only cutout for the uploaded, single-texture Shrike.
# Its painted windshield is NOT a separate material. Retain every original
# triangle for exterior views; place only front-glazing faces in a detachable
# overlay, hidden when the driver camera is active.
# This is a visibility experiment, not genuine transparent glazing or an
# interior reconstruction.
const MIN_FACES := 12

static func is_front_windscreen(a: Vector3, b: Vector3, c: Vector3, eye: Vector3) -> bool:
	var center: Vector3=(a+b+c)/3.0
	var forward: float=center.z-eye.z
	if forward<0.24 or forward>2.20:
		return false
	if absf(center.x)>1.17 or center.y<eye.y-0.30 or center.y>eye.y+1.30:
		return false
	# Sloped forward-facing sheet, rather than the horizontal roof/bonnet or
	# the side shoulder. Use absolute Z to cover backfaces of the baked mesh.
	var face_normal: Vector3=(b-a).cross(c-a)
	if face_normal.length_squared()<0.0000001:
		return false
	face_normal=face_normal.normalized()
	return absf(face_normal.z)>0.20 and absf(face_normal.x)<0.80

static func isolate(craft: Node3D, eye: Vector3) -> Dictionary:
	var hull: Node=craft.find_child("Kestrel_Hull",true,false)
	var windows: Array[MeshInstance3D]=[]
	if hull==null:
		push_warning("Shrike windshield: original Kestrel_Hull node was not found")
		return {"windows":windows,"faces":0}
	var meshes: Array[MeshInstance3D]=[]
	if hull is MeshInstance3D:
		meshes.append(hull as MeshInstance3D)
	for candidate in hull.find_children("*","MeshInstance3D",true,false):
		meshes.append(candidate as MeshInstance3D)
	var total_faces: int=0
	for node in meshes:
		var source: Mesh=node.mesh
		if source==null:
			continue
		var solid := ArrayMesh.new()
		var canopy := ArrayMesh.new()
		var split_faces: int=0
		var vertex_to_craft: Transform3D=craft.global_transform.affine_inverse()*node.global_transform
		for surface in range(source.get_surface_count()):
			if source.surface_get_primitive_type(surface)!=Mesh.PRIMITIVE_TRIANGLES:
				continue
			var original_arrays: Array=source.surface_get_arrays(surface)
			var vertices: PackedVector3Array=original_arrays[Mesh.ARRAY_VERTEX]
			var indices: PackedInt32Array=original_arrays[Mesh.ARRAY_INDEX]
			if indices.is_empty():
				indices=PackedInt32Array()
				for i in range(vertices.size()):
					indices.append(i)
			if indices.size()%3!=0:
				push_warning("Shrike windshield: invalid triangle index count")
				return {"windows":windows,"faces":0}
			var keep: PackedInt32Array=PackedInt32Array()
			var window: PackedInt32Array=PackedInt32Array()
			for face in range(0,indices.size(),3):
				var ia: int=indices[face]
				var ib: int=indices[face+1]
				var ic: int=indices[face+2]
				var a: Vector3=vertex_to_craft*vertices[ia]
				var b: Vector3=vertex_to_craft*vertices[ib]
				var c: Vector3=vertex_to_craft*vertices[ic]
				var target: PackedInt32Array=window if is_front_windscreen(a,b,c,eye) else keep
				target.append(ia)
				target.append(ib)
				target.append(ic)
			var active: Material=node.get_active_material(surface)
			if not keep.is_empty():
				var opaque_arrays: Array=original_arrays.duplicate(true)
				opaque_arrays[Mesh.ARRAY_INDEX]=keep
				solid.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,opaque_arrays)
				solid.surface_set_material(solid.get_surface_count()-1,active)
			if not window.is_empty():
				var window_arrays: Array=original_arrays.duplicate(true)
				window_arrays[Mesh.ARRAY_INDEX]=window
				canopy.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,window_arrays)
				canopy.surface_set_material(canopy.get_surface_count()-1,active)
				split_faces+=window.size()/3
		if split_faces>0:
			var cover := MeshInstance3D.new()
			cover.name="ShrikePaintedWindscreen"
			cover.mesh=canopy
			cover.material_override=node.material_override
			cover.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			node.mesh=solid
			node.add_child(cover)
			windows.append(cover)
			total_faces+=split_faces
	if total_faces<MIN_FACES:
		push_warning("Shrike windshield: only %d candidate faces; check canopy geometry" % total_faces)
	print("SCENEFORGE_SHRIKE_WINDSCREEN_SEPARATED ",total_faces)
	return {"windows":windows,"faces":total_faces}
