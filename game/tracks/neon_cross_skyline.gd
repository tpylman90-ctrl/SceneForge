extends RefCounted

# Neon Cross skyline pass: tall *near-field* 3D high rises around the flyway
# and within the free space between figure-eight arms, mid-field instanced
# 3D blocks, and two very cheap polygon-cut cylindrical horizon silhouettes.
#
# Every tower is checked in XZ against the actual sampled race centerline.
# No scenery collision and no separate real-time light sources.
const BASE_Y := -64.0
const MEDIUM_LIMIT := 176
const SAFETY_GAP := 10.5
const HERO_SITES := [
	Vector2(-50.0,0.0), Vector2(50.0,0.0),
	Vector2(-45.0,-57.0), Vector2(-45.0,57.0),
	Vector2(45.0,-57.0), Vector2(45.0,57.0),
	Vector2(0.0,-50.0), Vector2(0.0,50.0),
	Vector2(-107.0,0.0), Vector2(107.0,0.0),
	Vector2(-103.0,43.0), Vector2(103.0,-43.0)
]
const HERO_WIDTHS := [12.0,12.0,13.0,12.0,13.0,13.0,15.0,15.0,12.0,12.0,14.0,14.0]
const HERO_HEIGHTS := [130.0,143.0,108.0,119.0,123.0,108.0,115.0,111.0,148.0,136.0,104.0,108.0]

static func _material(hex: String, unlit: bool=false) -> StandardMaterial3D:
	var m:=StandardMaterial3D.new()
	m.albedo_color=Color(hex)
	m.roughness=0.86
	m.cull_mode=BaseMaterial3D.CULL_DISABLED
	m.vertex_color_use_as_albedo=true
	if unlit:
		m.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
	return m

static func _sector(p: Vector3) -> int:
	return (2 if p.z>=0.0 else 0)+(1 if p.x>=0.0 else 0)

static func route_clearance(route: PackedVector3Array, at: Vector2) -> float:
	var best: float=INF
	for i in range(route.size()):
		var p: Vector3=route[i]
		var q: Vector3=route[(i+1)%route.size()]
		var start:=Vector2(p.x,p.z)
		var segment:=Vector2(q.x,q.z)-start
		var t: float=clampf((at-start).dot(segment)/maxf(segment.length_squared(),0.0001),0.0,1.0)
		best=minf(best,(at-(start+segment*t)).length())
	return best

static func safe_footprint(route: PackedVector3Array, at: Vector2, sx: float, sz: float) -> bool:
	var extent: float=0.5*Vector2(sx,sz).length()
	return route_clearance(route,at) > extent+SAFETY_GAP

static func _batch(parent: Node3D, name: String, descriptors: Array, material: Material) -> void:
	if descriptors.is_empty():
		return
	var box:=BoxMesh.new()
	box.size=Vector3.ONE
	var multi:=MultiMesh.new()
	multi.transform_format=MultiMesh.TRANSFORM_3D
	multi.use_colors=true
	multi.mesh=box
	multi.instance_count=descriptors.size()
	for index in range(descriptors.size()):
		var d: Dictionary=descriptors[index]
		multi.set_instance_transform(index,Transform3D(Basis().scaled(d["size"]),d["position"]))
		multi.set_instance_color(index,d["color"])
	var mi:=MultiMeshInstance3D.new()
	mi.name=name
	mi.multimesh=multi
	mi.material_override=material
	mi.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)

static func _element(pos: Vector3, size: Vector3, tint: Color) -> Dictionary:
	return {"position":pos,"size":size,"color":tint}

static func _fill_medium(parent: Node3D, route: PackedVector3Array) -> void:
	var mass: Array=[]
	var crown: Array=[]
	var facade: Array=[]
	for _i in range(4):
		mass.append([])
		crown.append([])
		facade.append([])
	var rng:=RandomNumberGenerator.new()
	rng.seed=140982
	var tower_count: int=0
	var facade_count: int=0
	for gx in range(-10,11):
		for gz in range(-8,9):
			# Deterministic scattered footprints, not a visible regular grid.
			if posmod(gx*19+gz*29,4)==0:
				continue
			var x: float=gx*19.0+4.2*sin(float(gx*7+gz*11))
			var z: float=gz*19.0+3.7*cos(float(gx*13-gz*5))
			var site:=Vector2(x,z)
			var sx: float=rng.randf_range(8.0,13.0)
			var sz: float=rng.randf_range(8.0,13.0)
			if not safe_footprint(route,site,sx,sz):
				continue
			var hero_overlap: bool=false
			for hero in HERO_SITES:
				if site.distance_to(hero)<21.0:
					hero_overlap=true
					break
			if hero_overlap:
				continue
			var separation: float=route_clearance(route,site)
			var h: float=rng.randf_range(65.0,114.0) if separation<57.0 else rng.randf_range(34.0,82.0)
			var sector: int=_sector(Vector3(x,0,z))
			if mass[sector].size()>=int(MEDIUM_LIMIT/4):
				continue
			var base_color: Color=Color("34445b").lerp(Color("53647b"),rng.randf_range(0.05,0.7))
			mass[sector].append(_element(Vector3(x,BASE_Y+h*0.5,z),Vector3(sx,h,sz),base_color))
			var top_y: float=BASE_Y+h
			crown[sector].append(_element(Vector3(x,top_y+0.4,z),
				Vector3(sx+0.7,0.8,sz+0.7),
				Color("617e8c") if (gx+gz)%2 else Color("385b70")))
			# 3D exterior light bands on the actual route-facing faces. These
			# are shallow solid geometry, not thousands of window nodes.
			if separation<55.0 and (gx+gz)%3!=0:
				var color: Color=Color("62b7bf") if (gx+gz)%4 else Color("d9a483")
				var n: int=clampi(int(h/13.0),3,8)
				for level in range(1,n):
					var y: float=BASE_Y+h*float(level)/float(n)
					facade[sector].append(_element(Vector3(x,y,z+sz*0.5+0.07),
						Vector3(sx*0.8,0.16,0.18),color))
					facade[sector].append(_element(Vector3(x+sx*0.5+0.07,y,z),
						Vector3(0.18,0.16,sz*0.8),color))
					facade_count+=2
			tower_count+=1
	for sector in range(4):
		_batch(parent,"NeonMidTowers_%d"%sector,mass[sector],_material("ffffff"))
		_batch(parent,"NeonRoofCaps_%d"%sector,crown[sector],_material("ffffff"))
		_batch(parent,"NeonFacadeBands_%d"%sector,facade[sector],_material("ffffff",true))
	parent.set_meta("midrise_towers",tower_count)
	parent.set_meta("batched_facade_details",facade_count)

static func _hero_towers(parent: Node3D, route: PackedVector3Array) -> void:
	# The skyline's strong near-field shapes: real 3D setback profiles,
	# face strips, offset service spines and roofs visible when the course
	# wraps around them. All parts still batch by material in four quadrants.
	var bodies: Array=[]
	var trims: Array=[]
	var glass: Array=[]
	var roofs: Array=[]
	for _i in range(4):
		bodies.append([])
		trims.append([])
		glass.append([])
		roofs.append([])
	var count: int=0
	for i in range(HERO_SITES.size()):
		var site: Vector2=HERO_SITES[i]
		var width: float=HERO_WIDTHS[i]
		var depth: float=width*0.83
		assert(safe_footprint(route,site,width+1.4,depth+1.4),
			"Hero tower must clear Neon Cross drive corridor")
		var height: float=HERO_HEIGHTS[i]
		var x: float=site.x
		var z: float=site.y
		var top_y: float=BASE_Y+height
		var sec: int=_sector(Vector3(x,0,z))
		var metal: Color=Color("52617a") if i%3==0 else Color("3d5064")
		var accent: Color=Color("69deea") if i%2==0 else Color("ecaa82")
		# Distinct bottom, middle and tapered roof sections make the hero
		# towers recognizable from both chase and cockpit cameras.
		bodies[sec].append(_element(Vector3(x,BASE_Y+height*0.38,z),
			Vector3(width,height*0.76,depth),metal))
		bodies[sec].append(_element(Vector3(x+width*0.08,BASE_Y+height*0.85,z-depth*0.04),
			Vector3(width*0.76,height*0.20,depth*0.72),metal.darkened(0.10)))
		bodies[sec].append(_element(Vector3(x,BASE_Y+height*0.975,z),
			Vector3(width*0.50,height*0.05,depth*0.52),metal.lightened(0.15)))
		# Roof caps and rooftop mechanical volumes are actual 3D pieces.
		roofs[sec].append(_element(Vector3(x,top_y+0.22,z),
			Vector3(width*0.61,0.44,depth*0.62),Color("74899a")))
		roofs[sec].append(_element(Vector3(x-width*0.17,top_y+1.0,z-depth*0.12),
			Vector3(width*0.19,1.65,depth*0.23),Color("273d56")))
		# Layered perimeter spines give the silhouette real architectural
		# depth without per-window box objects.
		for side in [-1.0,1.0]:
			trims[sec].append(_element(Vector3(x+side*(width*0.5+0.22),
				BASE_Y+height*0.39,z),Vector3(0.36,height*0.75,0.37),
				Color("8294a4")))
			trims[sec].append(_element(Vector3(x,BASE_Y+height*0.39,
				z+side*(depth*0.5+0.22)),Vector3(0.37,height*0.75,0.36),
				Color("8294a4")))
		for tier in range(3,11):
			var y: float=BASE_Y+height*float(tier)/12.0
			# Lit solid facade strips on two planes: the visible near faces
			# change naturally through lateral parallax while racing.
			for sign in [-1.0,1.0]:
				glass[sec].append(_element(Vector3(x,y,z+sign*(depth*0.5+0.09)),
					Vector3(width*0.69,0.23,0.19),accent))
				glass[sec].append(_element(Vector3(x+sign*(width*0.5+0.09),y,z),
					Vector3(0.19,0.23,depth*0.68),accent))
		count+=1
	for sector in range(4):
		_batch(parent,"NeonHeroBuildings_%d"%sector,bodies[sector],_material("ffffff"))
		_batch(parent,"NeonHeroStructuralRibs_%d"%sector,trims[sector],_material("ffffff"))
		_batch(parent,"NeonHeroFacadeLights_%d"%sector,glass[sector],_material("ffffff",true))
		_batch(parent,"NeonHeroRoofTops_%d"%sector,roofs[sector],_material("ffffff"))
	parent.set_meta("hero_3d_towers",count)

static func _silhouette_ring(parent: Node3D, name: String, radius_x: float, radius_z: float,
		base: float, height: float, tint: Color, phase: float) -> void:
	var segments: int=80
	var st:=SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for index in range(segments):
		var a: float=TAU*float(index)/float(segments)
		var b: float=TAU*float(index+1)/float(segments)
		var top_a: float=base+height*(0.37+0.63*absf(sin(a*11.0+phase)))
		var top_b: float=base+height*(0.37+0.63*absf(sin(b*11.0+phase)))
		var pa:=Vector3(radius_x*cos(a),base,radius_z*sin(a))
		var pb:=Vector3(radius_x*cos(b),base,radius_z*sin(b))
		var qa:=Vector3(pa.x,top_a,pa.z)
		var qb:=Vector3(pb.x,top_b,pb.z)
		# Vertex-color silhouette with a cut upper skyline edge, waiting
		# for a later optional baked panorama material. No transparency,
		# no image sampling and only two draw surfaces.
		for v in [pa,qa,qb,pa,qb,pb]:
			st.set_normal(Vector3(-cos(a),0.0,-sin(a)))
			st.set_color(tint)
			st.add_vertex(v)
	var mesh:=MeshInstance3D.new()
	mesh.name=name
	mesh.mesh=st.commit()
	mesh.material_override=_material("ffffff",true)
	mesh.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mesh)

static func populate(parent: Node3D, route: PackedVector3Array) -> void:
	assert(route.size()==192)
	_fill_medium(parent,route)
	_hero_towers(parent,route)
	_silhouette_ring(parent,"NeonPanoramaLayerNear",234.0,180.0,BASE_Y-11.0,108.0,
		Color("253b50"),0.3)
	_silhouette_ring(parent,"NeonPanoramaLayerFar",282.0,218.0,BASE_Y-20.0,94.0,
		Color("1d2a40"),1.4)
	parent.set_meta("scene_depth_strategy",
		"12 geometric hero highrises + route-spaced instanced midrise buildings + two cut skyline cylinders")
