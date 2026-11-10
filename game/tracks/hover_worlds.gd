extends RefCounted

# SceneForge's first terrain-free racing pack. Tracks 7-9 deliberately keep the
# hover handling independent of surface friction and use the existing route
# cursor, checkpoint system, invisible lateral containment and jump recovery.
# All scenery is deterministic, decorative and collision-free.
const FIRST_ID := 7
const LAST_ID := 9
const ROUTE_NAMES := ["TIDAL RELICS", "FROSTLINE WILDS", "SKYFALL RUN"]
const ROUTE_INFO := [
	"MEDIUM / Flooded ruins, lagoon racing and cobblestone causeways",
	"MEDIUM / Frozen lake, muddy thaw basin and grassy alpine slopes",
	"HARD / Floating platforms, repulsor lift corridors and aerial gates"
]
const CAPTURE_NAMES := ["TidalRelics", "FrostlineWilds", "SkyfallRun"]
const SECTORS := [
	["OPEN LAGOON","DROWNED CAUSEWAY","RUINED CITADEL","FLOODED GARDENS"],
	["FROZEN MIRROR","THAW BASIN","ALPINE MEADOW","GLACIER RETURN"],
	["ASCENT PLATFORM","CLOUD GATES","SKY ISLAND","FINAL AIRWAY"]
]
const TIDAL := [
	Vector2(154,0),Vector2(152,38),Vector2(125,76),Vector2(85,88),
	Vector2(55,58),Vector2(24,70),Vector2(-12,112),Vector2(-68,103),
	Vector2(-109,74),Vector2(-145,42),Vector2(-158,-3),Vector2(-148,-49),
	Vector2(-108,-76),Vector2(-63,-66),Vector2(-14,-104),Vector2(41,-106),
	Vector2(97,-79),Vector2(133,-42)
]
const FROST := [
	Vector2(155,0),Vector2(146,43),Vector2(116,86),Vector2(72,103),
	Vector2(31,83),Vector2(-8,67),Vector2(-48,100),Vector2(-92,80),
	Vector2(-142,38),Vector2(-155,-10),Vector2(-132,-58),Vector2(-84,-77),
	Vector2(-38,-51),Vector2(8,-91),Vector2(56,-106),Vector2(103,-77),
	Vector2(143,-41)
]
const SKY := [
	Vector2(155,0),Vector2(149,45),Vector2(112,87),Vector2(65,108),
	Vector2(19,91),Vector2(-19,64),Vector2(-64,102),Vector2(-112,73),
	Vector2(-149,31),Vector2(-159,-14),Vector2(-132,-63),Vector2(-89,-81),
	Vector2(-39,-54),Vector2(9,-88),Vector2(62,-99),Vector2(112,-67),
	Vector2(144,-35)
]

static func _controls(track_id: int) -> Array:
	match track_id:
		7: return TIDAL
		8: return FROST
		9: return SKY
	return []

static func point(track_id: int, index: int, count: int) -> Vector2:
	var controls: Array=_controls(track_id)
	var size: int=controls.size()
	assert(size>=4 and count>=size)
	var position: float=float(posmod(index,count))*float(size)/float(count)
	var k: int=floori(position)
	var t: float=position-float(k)
	var a: Vector2=controls[posmod(k-1,size)]
	var b: Vector2=controls[k%size]
	var c: Vector2=controls[(k+1)%size]
	var d: Vector2=controls[(k+2)%size]
	return 0.5*(2.0*b+(-a+c)*t+(2.0*a-5.0*b+4.0*c-d)*t*t+(-a+3.0*b-3.0*c+d)*t*t*t)

static func height(track_id: int, index: int, count: int) -> float:
	var a: float=TAU*float(posmod(index,count))/float(count)
	match track_id:
		7: return 2.8+0.7*sin(a*2.0+0.15)+0.45*sin(a*4.0)
		8: return 4.7+2.4*sin(a+0.45)+1.0*sin(a*3.0-0.3)
		9: return 75.0+13.0*sin(a+0.3)+6.0*sin(a*3.0-0.7)
	return 0.0

static func width(track_id: int, index: int) -> float:
	match track_id:
		7: return 16.0 if not has_deck(track_id,index) else 12.0
		8: return 11.5 if index>=80 and index<136 else 13.5
		9: return 14.5 if not has_deck(track_id,index) else 11.5
	return 10.0

static func bank(track_id: int, index: int, count: int) -> float:
	if track_id==9:
		return 0.055*sin(TAU*float(index)*3.0/float(count))
	if track_id==8:
		return 0.025*sin(TAU*float(index)*2.0/float(count))
	return 0.0

static func sector(track_id: int, index: int, count: int) -> String:
	var quarter: int=clampi(int(float(posmod(index,count))*4.0/float(count)),0,3)
	return SECTORS[track_id-FIRST_ID][quarter]

static func has_deck(track_id: int, index: int) -> bool:
	# No fake asphalt over the lagoon. The water mesh below is visual; the
	# existing hover support plane remains the authoritative driving surface.
	if track_id==7:
		return index>=49 and index<133
	# Skyfall's lift fields are open air, NOT invisible physical bridges.
	# Players retain normal left/right steering; altitude follows the
	# authored anti-gravity flight ribbon until a full 6-DOF mode exists.
	if track_id==9:
		return index<70 or (index>=111 and index<126) or index>=149
	return true

static func is_air_channel(track_id: int, index: int) -> bool:
	return track_id==9 and not has_deck(track_id,index)

static func _surface_style(track_id: int, index: int) -> int:
	if track_id==7:
		return 3 if index<87 else 2 # cobble then mossy stone
	if track_id==8:
		if index<52 or index>=158: return 0 # frozen lake
		if index<102: return 1 # wet mud
		if index<146: return 2 # grass
		return 3 # stone crossing
	return 4 # elevated carbon-alloy platform

static func _mat(color: Color, roughness: float=0.86, glow: bool=false) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color=color
	mat.roughness=roughness
	mat.cull_mode=BaseMaterial3D.CULL_DISABLED
	if glow:
		mat.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
	return mat

static func _vertex_mat(roughness: float=0.91) -> StandardMaterial3D:
	var mat := _mat(Color.WHITE,roughness)
	mat.vertex_color_use_as_albedo=true
	return mat

static func _triangle(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, tint: Color) -> void:
	var n: Vector3=(b-a).cross(c-a)
	if n.length_squared()<0.00001:
		return
	n=n.normalized()
	for p in [a,b,c]:
		st.set_normal(n)
		st.set_color(tint)
		st.set_uv(Vector2(p.x,p.z)*0.045)
		st.add_vertex(p)

static func _finish(owner: Node3D, name: String, st: SurfaceTool, mat: Material) -> void:
	var node := MeshInstance3D.new()
	node.name=name
	node.mesh=st.commit()
	node.material_override=mat
	node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	owner.add_child(node)

static func _road(owner: Node3D, route: PackedVector3Array, track_id: int) -> void:
	var styles: Array=[]
	var uses: Array[int]=[0,0,0,0,0]
	for style in range(5):
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		styles.append(st)
	var edge_mat: StandardMaterial3D=owner.material("69dce0",true) if track_id==7 else (owner.material("d9f2ff",true) if track_id==8 else owner.material("b39eff",true))
	var wall_mat: StandardMaterial3D=owner.material("4a4c53")
	for i in range(route.size()):
		if owner.is_jump_gap(i) or not has_deck(track_id,i):
			continue
		var p: Vector3=route[i]
		var q: Vector3=route[(i+1)%route.size()]
		var dir: Vector3=Vector3(q.x-p.x,0,q.z-p.z).normalized()
		var right: Vector3=Vector3(dir.z,bank(track_id,i,route.size()),-dir.x)
		var next: Vector3=route[(i+2)%route.size()]-q
		var next_dir: Vector3=Vector3(next.x,0,next.z).normalized()
		var next_right: Vector3=Vector3(next_dir.z,bank(track_id,(i+1)%route.size(),route.size()),-next_dir.x)
		var w: float=width(track_id,i)
		var w2: float=width(track_id,(i+1)%route.size())
		var a: Vector3=p-right*w
		var b: Vector3=q-next_right*w2
		var c: Vector3=q+next_right*w2
		var d: Vector3=p+right*w
		var style: int=_surface_style(track_id,i)
		var tint: Color=Color("c0e6ee") if style==0 else (Color("594439") if style==1 else (Color("486d46") if style==2 else (Color("928f82") if style==3 else Color("343b58"))))
		tint=tint*(0.93+0.065*sin(float(i)*0.41))
		_triangle(styles[style],a,b,c,tint)
		_triangle(styles[style],a,c,d,tint.lightened(0.025))
		uses[style]+=1
		# No visible wall across an open lagoon or aerial lift corridor;
		# discrete edge markers show direction while the existing magnetic
		# containment calculation guards against leaving the spline.
		if i%6==0:
			var angle: float=atan2(dir.x,dir.z)
			for sign in [-1.0,1.0]:
				var edge: Vector3=p+right*sign*(w+0.35)
				owner.block(edge+Vector3.UP*0.22,Vector3(0.34,0.42,1.5),edge_mat,angle)
		if (track_id==8 or track_id==9) and i%3==0:
			var midpoint: Vector3=(p+q)*0.5
			var angle2: float=atan2(dir.x,dir.z)
			for sign in [-1.0,1.0]:
				owner.block(midpoint+right*sign*(w+1.0)+Vector3.UP*0.46,
					Vector3(0.6,0.9,Vector3(q.x-p.x,0,q.z-p.z).length()*2.5),wall_mat,angle2)
	for style in range(5):
		if uses[style]>0:
			var name: String=["IceDeck","MudDeck","GrassDeck","StoneDeck","SkyPlatformDeck"][style]
			_finish(owner,"Hover"+name,styles[style],_vertex_mat(0.3 if style==0 else 0.9))
	# Beacon arches mark the invisible field when a track has no floor.
	if track_id==7:
		_beacons(owner,route,[8,28,145,165,184],"68e4e2")
	if track_id==9:
		_air_gates(owner,route)
	var start: Vector3=route[0]
	var f: Vector3=Vector3(route[1].x-start.x,0,route[1].z-start.z).normalized()
	var side: Vector3=Vector3(f.z,0,-f.x)
	var yaw: float=atan2(f.x,f.z)
	var gantry: StandardMaterial3D=owner.material("f0d6aa" if track_id==7 else ("d4f6ff" if track_id==8 else "dbb8ff"),true)
	for sign in [-1.0,1.0]:
		owner.block(start+side*sign*(width(track_id,0)+2.0)+Vector3.UP*4.2,
			Vector3(0.65,8.4,0.65),gantry,yaw)
	owner.block(start+Vector3.UP*8.1,Vector3(width(track_id,0)*2.0+4.2,0.45,0.6),gantry,yaw)
	var label:=Label3D.new()
	label.name="HoverWorldStart"
	label.text=ROUTE_NAMES[track_id-FIRST_ID]+" / START"
	label.font_size=60
	label.pixel_size=0.008
	label.position=start+Vector3.UP*7.25
	label.rotation.y=yaw
	owner.add_child(label)
	owner.flush_batches()

static func _beacons(owner: Node3D, route: PackedVector3Array, slots: Array, color: String) -> void:
	var mat: StandardMaterial3D=owner.material(color,true)
	for idx in slots:
		var i: int=int(idx)
		var p: Vector3=route[i]
		var heading: Vector3=route[(i+1)%route.size()]-p
		var f: Vector3=Vector3(heading.x,0,heading.z).normalized()
		var r: Vector3=Vector3(f.z,0,-f.x)
		var yaw: float=atan2(f.x,f.z)
		for sign in [-1.0,1.0]:
			owner.block(p+r*sign*(width(7,i)+1.0)+Vector3.UP*1.8,
				Vector3(0.55,3.6,0.55),mat,yaw)

static func _water_and_ground(owner: Node3D, track_id: int) -> void:
	var st:=SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var rng: float=1.0 if track_id==7 else 0.62
	for x in range(34):
		for z in range(24):
			var x0: float=-225.0+450.0*float(x)/34.0
			var x1: float=-225.0+450.0*float(x+1)/34.0
			var z0: float=-165.0+330.0*float(z)/24.0
			var z1: float=-165.0+330.0*float(z+1)/24.0
			var y: float=0.9 if track_id==7 else -0.9
			var a:=Vector3(x0,y+0.08*rng*sin(x0*0.11+z0*0.17),z0)
			var b:=Vector3(x1,y+0.08*rng*sin(x1*0.11+z0*0.17),z0)
			var c:=Vector3(x1,y+0.08*rng*sin(x1*0.11+z1*0.17),z1)
			var d:=Vector3(x0,y+0.08*rng*sin(x0*0.11+z1*0.17),z1)
			var tint: Color=Color("285f6a").lerp(Color("348b8f"),0.5+0.35*sin(float(x)*0.42+float(z)*0.30)) if track_id==7 else Color("c3d8da").lerp(Color("658d9c"),0.5+0.35*sin(float(x)*0.32+float(z)*0.43))
			_triangle(st,a,b,c,tint)
			_triangle(st,a,c,d,tint)
	_finish(owner,"HoverWorldLagoon" if track_id==7 else "HoverWorldFrozenValley",st,_vertex_mat(0.36 if track_id==7 else 0.94))

static func _ruins(owner: Node3D, route: PackedVector3Array) -> void:
	# Four connected temple complexes, with overlapping stone tiers rather
	# than hundreds of separate draw calls. Never intersect racing clearance.
	var stone: StandardMaterial3D=owner.material("7c8076")
	var pale: StandardMaterial3D=owner.material("a2a99a")
	var moss: StandardMaterial3D=owner.material("4d6d59")
	for i in [63,79,102,117]:
		var p: Vector3=route[i]
		var q: Vector3=route[(i+1)%route.size()]
		var forward: Vector3=Vector3(q.x-p.x,0,q.z-p.z).normalized()
		var side: Vector3=Vector3(forward.z,0,-forward.x)
		var yaw: float=atan2(forward.x,forward.z)
		var base: Vector3=p+side*34.0
		base.y=1.5
		owner.block(base,Vector3(27.0,2.0,19.0),stone,yaw)
		owner.block(base+Vector3.UP*1.1,Vector3(25.8,0.45,17.7),moss,yaw)
		for offset in [-9.0,0.0,9.0]:
			var column: Vector3=base+forward*offset+side*6.0
			owner.block(column+Vector3.UP*6.0,Vector3(2.7,10.0,2.7),pale,yaw)
			owner.block(column+Vector3.UP*11.1,Vector3(4.1,0.85,4.1),stone,yaw)
		owner.block(base+forward*0.0+side*6.0+Vector3.UP*12.0,
			Vector3(25.0,1.1,2.5),pale,yaw)

static func _frost_shards(owner: Node3D, route: PackedVector3Array) -> void:
	var st:=SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(0,route.size(),7):
		var p: Vector3=route[i]
		var q: Vector3=route[(i+1)%route.size()]
		var f: Vector3=Vector3(q.x-p.x,0,q.z-p.z).normalized()
		var side: Vector3=Vector3(f.z,0,-f.x)
		for sign in [-1.0,1.0]:
			var base: Vector3=p+side*sign*(width(8,i)+23.0+6.0*sin(float(i)))
			base.y=-0.6
			var h: float=10.0+9.0*absf(sin(float(i)*1.14+sign))
			var a: Vector3=base+side*4.3
			var b: Vector3=base-side*4.3
			var c: Vector3=base+f*4.6
			var peak: Vector3=base+Vector3.UP*h+f*2.0
			var cold: Color=Color("6fa6b7") if i%3==0 else Color("b2d9db")
			_triangle(st,a,b,peak,cold)
			_triangle(st,b,c,peak,cold.darkened(0.13))
			_triangle(st,c,a,peak,cold.lightened(0.08))
	_finish(owner,"HoverGlacialShards",st,_vertex_mat())

static func _islands(owner: Node3D, route: PackedVector3Array) -> void:
	var st:=SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for n in range(11):
		var idx: int=(n*17+8)%route.size()
		var p: Vector3=route[idx]
		var dir: Vector3=route[(idx+1)%route.size()]-p
		var f: Vector3=Vector3(dir.x,0,dir.z).normalized()
		var side: Vector3=Vector3(f.z,0,-f.x)
		var sign: float=-1.0 if n%2==0 else 1.0
		var center: Vector3=p+side*sign*(48.0+float(n%3)*8.0)
		center.y=p.y-15.0
		var rad: float=18.0+float(n%4)*4.0
		var levels: Array[float]=[1.0,1.12,0.86,0.51,0.08]
		for tier in range(4):
			for edge in range(12):
				var alpha: float=TAU*float(edge)/12.0
				var beta: float=TAU*float(edge+1)/12.0
				var t1: float=float(tier)
				var t2: float=float(tier+1)
				var a: Vector3=center+Vector3(cos(alpha)*rad*levels[tier],-t1*10.0,sin(alpha)*rad*levels[tier])
				var b: Vector3=center+Vector3(cos(beta)*rad*levels[tier],-t1*10.0,sin(beta)*rad*levels[tier])
				var c: Vector3=center+Vector3(cos(beta)*rad*levels[tier+1],-t2*10.0,sin(beta)*rad*levels[tier+1])
				var d: Vector3=center+Vector3(cos(alpha)*rad*levels[tier+1],-t2*10.0,sin(alpha)*rad*levels[tier+1])
				var tint: Color=Color("665b7f").lerp(Color("9283a7"),float(tier)/4.0)
				_triangle(st,a,b,c,tint)
				_triangle(st,a,c,d,tint)
	_finish(owner,"HoverFloatingIslands",st,_vertex_mat())
	# The decked stop on the third island has a visible landing assembly.
	var p: Vector3=route[117]
	var color: StandardMaterial3D=owner.material("636483")
	owner.block(p+Vector3.DOWN*4.0,Vector3(35,7,39),color)

static func _air_gates(owner: Node3D, route: PackedVector3Array) -> void:
	var st:=SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in [76,87,98,108,131,140,147]:
		var p: Vector3=route[i]
		var delta: Vector3=route[(i+2)%route.size()]-p
		var f: Vector3=Vector3(delta.x,0,delta.z).normalized()
		var r: Vector3=Vector3(f.z,0,-f.x)
		for k in range(32):
			var a: float=TAU*float(k)/32.0
			var b: float=TAU*float(k+1)/32.0
			var c0: Vector3=p+r*cos(a)*13.0+Vector3.UP*sin(a)*7.5
			var c1: Vector3=p+r*cos(b)*13.0+Vector3.UP*sin(b)*7.5
			var v0: Vector3=p+r*cos(a)*13.7+Vector3.UP*sin(a)*8.2
			var v1: Vector3=p+r*cos(b)*13.7+Vector3.UP*sin(b)*8.2
			var tint: Color=Color("9ce6f9") if k%8<4 else Color("bea8ff")
			_triangle(st,c0,c1,v1,tint)
			_triangle(st,c0,v1,v0,tint)
	_finish(owner,"HoverAirGateRings",st,_vertex_mat(0.25))

static func populate(owner: Node3D, route: PackedVector3Array, track_id: int) -> void:
	assert(track_id>=FIRST_ID and track_id<=LAST_ID)
	if track_id!=9:
		_water_and_ground(owner,track_id)
	_road(owner,route,track_id)
	match track_id:
		7: _ruins(owner,route)
		8: _frost_shards(owner,route)
		9: _islands(owner,route)
	owner.flush_batches()
