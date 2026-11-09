extends RefCounted

# Cohesive Canyon pass: fewer, broader eroded modules, carefully sunk into
# the original Terrain3D landform. The shared Blender UV atlas is 1024px;
# all rocks remain visual-only, collision-free and batched via MultiMesh.
const ATLAS_PATH = "res://tracks/serpent_textures/rock_atlas_1024.png"
const ASSET_DIR = "res://assets/scenery/serpent/"
const NAMES = ["wall_a","wall_b","wall_c","ledge_a","ledge_b","boulder_a",
	"sunstone_fang","strata_buttress","split_chimney"]
const MAP_WIDTH = 1024
const MAP_HEIGHT = 512
const MIN_H = -32.0
const MAX_H = 128.0

static func _terrain_y(raw: PackedByteArray, x: float, z: float) -> float:
	var u: float=clampf(x+512.0,0.0,1023.0)
	var v: float=clampf(z+256.0,0.0,511.0)
	var xi: int=floori(u)
	var zi: int=floori(v)
	var xj: int=mini(xi+1,1023)
	var zj: int=mini(zi+1,511)
	var f: float=u-float(xi)
	var g: float=v-float(zi)
	var a: float=float(raw.decode_u16(2*(zi*MAP_WIDTH+xi)))
	var b: float=float(raw.decode_u16(2*(zi*MAP_WIDTH+xj)))
	var c: float=float(raw.decode_u16(2*(zj*MAP_WIDTH+xi)))
	var d: float=float(raw.decode_u16(2*(zj*MAP_WIDTH+xj)))
	var h: float=lerpf(lerpf(a,b,f),lerpf(c,d,f),g)
	return MIN_H+(MAX_H-MIN_H)*h/65535.0

static func _near_road(route: PackedVector3Array, x: float, z: float) -> float:
	var best: float=INF
	for i in range(route.size()):
		var p: Vector3=route[i]
		var q: Vector3=route[(i+1)%route.size()]
		var dx: float=q.x-p.x
		var dz: float=q.z-p.z
		var f: float=clampf(((x-p.x)*dx+(z-p.z)*dz)/maxf(0.001,dx*dx+dz*dz),0.0,1.0)
		var ex: float=x-(p.x+dx*f)
		var ez: float=z-(p.z+dz*f)
		best=minf(best,ex*ex+ez*ez)
	return sqrt(best)

static func _mesh_of(node: Node) -> Mesh:
	if node is MeshInstance3D:
		return (node as MeshInstance3D).mesh
	for child in node.get_children():
		var found: Mesh=_mesh_of(child)
		if found!=null:
			return found
	return null

static func _load_mesh(name: String) -> Mesh:
	var source: PackedScene=load(ASSET_DIR+name+".glb") as PackedScene
	if source==null:
		push_error("Missing Blender cliff-kit mesh: "+name)
		return null
	var root: Node=source.instantiate()
	var mesh: Mesh=_mesh_of(root)
	root.free()
	return mesh

static func _stone_material() -> StandardMaterial3D:
	var mat:=StandardMaterial3D.new()
	mat.albedo_color=Color(0.99,0.97,0.94)
	mat.albedo_texture=load(ATLAS_PATH) as Texture2D
	# Blender already bakes deep cleft/underside shadows into COLOR_0.
	mat.vertex_color_use_as_albedo=true
	mat.roughness=0.88
	mat.metallic=0.0
	mat.cull_mode=BaseMaterial3D.CULL_DISABLED
	mat.uv1_triplanar=false
	mat.normal_enabled=false
	mat.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	return mat

static func populate(owner: Node3D, route: PackedVector3Array, heightmap: PackedByteArray) -> void:
	if heightmap.size()!=MAP_WIDTH*MAP_HEIGHT*2:
		push_error("Cannot place rock kit without valid sculpted canyon heightmap")
		return
	var group:=Node3D.new()
	group.name="CrimsonRockKit"
	owner.add_child(group)
	var spots: Array[Array]=[]
	for i in range(NAMES.size()):
		spots.append([])
	var rng:=RandomNumberGenerator.new()
	rng.seed=712239
	# Attach detailed cliff pieces to the steep part of both walls. Sampling
	# the real sculpt height and checking nearest road branch prevents random
	# rock pillars intruding into the playable course on tight turns.
	for index in range(6,route.size()-4,16):
		if index>=39 and index<=52:
			continue # Unobstructed leap silhouette and landing
		if index>=81 and index<=92:
			continue # Existing Arch Run landmark
		var p: Vector3=route[index]
		var q: Vector3=route[(index+3)%route.size()]
		var tangent:=Vector3(q.x-p.x,0.0,q.z-p.z).normalized()
		var outward:=Vector3(tangent.z,0.0,-tangent.x)
		var yaw: float=atan2(-tangent.z,tangent.x)
		for side_sign in [-1.0,1.0]:
			var lateral: float=28.0+rng.randf_range(-0.8,2.2)
			var center: Vector3=p+outward*side_sign*lateral
			if _near_road(route,center.x,center.z)<25.0:
				continue
			if absf(center.x)>330.0 or absf(center.z)>216.0:
				continue
			var model: int=(index/16+(0 if side_sign<0 else 1))%3
			var height: float=[25.0,27.0,23.0][model]
			# More than half of each authored rock is embedded in the real
			# terrain, so the contact is continuous rather than pasted on.
			center.y=_terrain_y(heightmap,center.x,center.z)-height*0.52
			var rotation: float=yaw+(PI if side_sign>0.0 else 0.0)
			var scale: float=rng.randf_range(0.94,1.06)
			spots[model].append(Transform3D(Basis(Vector3.UP,rotation).scaled(Vector3(scale,scale,scale)),center))
			# Shelf motifs appear between some wall modules, not everywhere.
			if index%32==6:
				var shelf_id: int=3+int(side_sign>0.0)
				var shelf_point: Vector3=center+outward*side_sign*1.8+Vector3.UP*(height*0.38)
				var shelf_basis:=Basis(Vector3.UP,rotation).scaled(Vector3(scale,scale,scale))
				spots[shelf_id].append(Transform3D(shelf_basis,shelf_point))
	# Small boulders are placed sparsely and never in the road envelope.
	for index in range(4,route.size(),6):
		if index>=40 and index<=52:
			continue
		var p: Vector3=route[index]
		var q: Vector3=route[(index+1)%route.size()]
		var tangent:=Vector3(q.x-p.x,0.0,q.z-p.z).normalized()
		var outward:=Vector3(tangent.z,0.0,-tangent.x)
		var sign: float=-1.0 if rng.randf()<0.5 else 1.0
		var candidate: Vector3=p+outward*sign*rng.randf_range(19.2,25.5)
		if _near_road(route,candidate.x,candidate.z)<18.0:
			continue
		if absf(candidate.x)>330.0 or absf(candidate.z)>216.0:
			continue
		candidate.y=_terrain_y(heightmap,candidate.x,candidate.z)+0.3
		var size: float=rng.randf_range(0.90,1.50)
		spots[5].append(Transform3D(Basis(Vector3.UP,rng.randf_range(-PI,PI)).scaled(Vector3(size,size,size)),candidate))
	# One sculpted escarpment per cinematic zone. They are wide, shallow
	# erosion folds, NOT grouped vertical pillars. The rest of the canyon
	# remains the continuous sculpted terrain and its native rock texture.
	var landmark_plan: Array[Dictionary]=[
		{"index":20, "side":-1.0, "kind":6, "distance":30.0, "scale":1.0},
		{"index":75, "side":1.0, "kind":7, "distance":30.0, "scale":1.0},
		{"index":155, "side":-1.0, "kind":8, "distance":30.0, "scale":1.0},
	]
	for feature in landmark_plan:
		var index: int=int(feature["index"])
		var sign: float=float(feature["side"])
		var kind: int=int(feature["kind"])
		var along: Vector3=route[index]
		var ahead: Vector3=route[(index+3)%route.size()]
		var tangent:=Vector3(ahead.x-along.x,0.0,ahead.z-along.z).normalized()
		var outward:=Vector3(tangent.z,0.0,-tangent.x)
		var position: Vector3=along+outward*sign*float(feature["distance"])
		if _near_road(route,position.x,position.z)<26.0:
			push_error("Cohesive cliff too close to neighboring branch")
			continue
		if absf(position.x)>325.0 or absf(position.z)>211.0:
			continue
		var form_height: float=[33.0,31.0,35.0][kind-6]
		position.y=_terrain_y(heightmap,position.x,position.z)-form_height*0.69
		var rotation: float=atan2(-tangent.z,tangent.x)+(PI if sign>0.0 else 0.0)
		var size: float=float(feature["scale"])
		spots[kind].append(Transform3D(
			Basis(Vector3.UP,rotation).scaled(Vector3(size,size,size)),position))
	var material: StandardMaterial3D=_stone_material()
	for i in range(NAMES.size()):
		var mesh: Mesh=_load_mesh(NAMES[i])
		if mesh==null:
			push_error("Cannot complete Crimson Serpent Blender kit: "+NAMES[i])
			continue
		var batch:=MultiMesh.new()
		batch.transform_format=MultiMesh.TRANSFORM_3D
		batch.mesh=mesh
		batch.instance_count=spots[i].size()
		for index in range(spots[i].size()):
			batch.set_instance_transform(index,spots[i][index])
		var instance:=MultiMeshInstance3D.new()
		instance.name=NAMES[i]
		instance.multimesh=batch
		instance.material_override=material
		instance.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		# Sparse landmarks stay visual-only; no hovercraft snag collisions.
		if i>=6:
			instance.set_meta("hero_landmark",true)
		group.add_child(instance)
