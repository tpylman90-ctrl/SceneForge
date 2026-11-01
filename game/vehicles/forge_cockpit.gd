extends Node3D

# FORGE owns its cockpit geometry so other craft updates cannot move its instruments.
func finish(color: String, metal: float=0.0, roughness: float=.45) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color=Color(color)
	m.metallic=metal
	m.roughness=roughness
	return m

func part(parent: Node3D, point: Vector3, size: Vector3, material: Material) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size=size
	node.mesh=box
	node.position=point
	node.material_override=material
	parent.add_child(node)
	return node

func canopy_surface_height(x: float, z: float) -> float:
	# Follow the same lofted canopy section used by the Blender body asset.
	var t := clampf((z-.45)/.60,0.0,1.0)
	var width := lerpf(.82,.76,t)
	var sill := lerpf(1.16,1.05,t)
	var crown := lerpf(1.80,1.48,t)
	var u := clampf(absf(x)/(.62*width),0.0,1.0)
	return sill+.012+(crown-sill)*pow(maxf(0.0,cos(u*PI*.5)),.48)

func cockpit_local(point: Vector3) -> Vector3:
	var fit := Transform3D(Basis.from_scale(Vector3(.66,1.0,.75)),Vector3(0,-.03,-.08))
	return fit.affine_inverse()*point

func hud_point(x: float, z: float, inset: float) -> Vector3:
	return cockpit_local(Vector3(x,canopy_surface_height(x,z)-inset,z))

func hud_mesh() -> ArrayMesh:
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	var columns := 25
	var rows := 7
	for row in range(rows):
		var v := float(row)/float(rows-1)
		for column in range(columns):
			var u := float(column)/float(columns-1)
			var x := lerpf(-.285,.285,u)
			var z := lerpf(.57,.82,v)
			surface.set_uv(Vector2(u,1.0-v))
			surface.add_vertex(hud_point(x,z,.060))
	for row in range(rows-1):
		for column in range(columns-1):
			var a := row*columns+column
			var b := a+1
			var c := a+columns
			var d := c+1
			for index in [a,c,b,b,c,d]:surface.add_index(index)
	surface.generate_normals()
	return surface.commit()

func hud_line(surface: SurfaceTool, a: Vector2, b: Vector2, inset: float) -> void:
	surface.add_vertex(hud_point(a.x,a.y,inset))
	surface.add_vertex(hud_point(b.x,b.y,inset))

func hud_traces(color: Color, amber: bool=false) -> MeshInstance3D:
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_LINES)
	# Curved visor boundary with stepped corner brackets.
	for i in range(24):
		var x0 := lerpf(-.285,.285,float(i)/24.0)
		var x1 := lerpf(-.285,.285,float(i+1)/24.0)
		hud_line(surface,Vector2(x0,.585),Vector2(x1,.585),.048)
		hud_line(surface,Vector2(x0,.805),Vector2(x1,.805),.048)
	for side in [-1.0,1.0]:
		hud_line(surface,Vector2(side*.285,.585),Vector2(side*.285,.805),.048)
		for z in [.60,.79]:
			hud_line(surface,Vector2(side*.285,z),Vector2(side*.235,z),.045)
	# Compact targeting reticle and two range ticks centered on the pilot's sightline.
	if not amber:
		for i in range(32):
			var a0 := TAU*float(i)/32.0
			var a1 := TAU*float(i+1)/32.0
			hud_line(surface,Vector2(.040*cos(a0),.69+.018*sin(a0)),Vector2(.040*cos(a1),.69+.018*sin(a1)),.043)
		hud_line(surface,Vector2(-.070,.69),Vector2(-.050,.69),.043)
		hud_line(surface,Vector2(.050,.69),Vector2(.070,.69),.043)
		hud_line(surface,Vector2(0,.655),Vector2(0,.675),.043)
		hud_line(surface,Vector2(0,.705),Vector2(0,.725),.043)
		for i in range(7):
			var z := .615+float(i)*.027
			hud_line(surface,Vector2(-.247,z),Vector2(-.229,z),.043)
			hud_line(surface,Vector2(.229,z),Vector2(.247,z),.043)
	else:
		# Amber brackets echo the craft's exterior accent without tinting the data.
		for side in [-1.0,1.0]:
			hud_line(surface,Vector2(side*.205,.625),Vector2(side*.178,.646),.041)
			hud_line(surface,Vector2(side*.178,.646),Vector2(side*.158,.646),.041)
	var node := MeshInstance3D.new()
	node.mesh=surface.commit()
	var material := finish(color,.05,.28)
	material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
	material.emission_enabled=true
	material.emission=Color(color)
	material.emission_energy_multiplier=1.25 if not amber else .85
	node.material_override=material
	node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return node

# Continuous rounded fascia, sweeping into both cockpit side consoles.
func dashboard(material: Material) -> void:
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	var points: Array[Vector3]=[]
	for i in range(25):
		var x := -.63+1.26*float(i)/24.0
		var sweep := absf(x)/.63
		for j in range(16):
			var angle := TAU*float(j)/16.0
			points.append(Vector3(x,1.35+.025*sweep+.095*sin(angle),1.08-.27*pow(sweep,2)+.14*cos(angle)))
	for i in range(24):
		for j in range(16):
			var a := i*16+j
			var b := i*16+(j+1)%16
			var c := (i+1)*16+j
			var d := (i+1)*16+(j+1)%16
			for index in [a,c,b,b,c,d]:surface.add_vertex(points[index])
	surface.generate_normals()
	var fascia := MeshInstance3D.new()
	fascia.name="SculptedDashboard"
	fascia.mesh=surface.commit()
	fascia.material_override=material
	add_child(fascia)

func build() -> void:
	name="PyldriverCockpitInstruments"
	var dark := finish("15222a",.4)
	var brass := finish("a77a30",.65)
	dashboard(dark)
	var frame := Transform3D(Basis.from_euler(Vector3(-.60,PI,0)),Vector3(0,1.41,.94))
	var bezel := part(self,Vector3.ZERO,Vector3(.54,.205,.04),dark)
	bezel.name="InstrumentBinnacle"
	bezel.transform=frame
	var display := MeshInstance3D.new()
	display.name="FlightDisplay"
	var quad := QuadMesh.new()
	quad.size=Vector2(.46,.15)
	display.mesh=quad
	display.transform=frame*Transform3D(Basis.IDENTITY,Vector3(0,0,.027))
	var screen := StandardMaterial3D.new()
	screen.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
	display.material_override=screen
	display.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(display)
	for side in [-1.0,1.0]:
		part(self,Vector3(side*.28,1.28,1.04),Vector3(.055,.10,.08),dark)
		var edge := part(self,Vector3.ZERO,Vector3(.018,.19,.045),brass)
		edge.transform=frame*Transform3D(Basis.IDENTITY,Vector3(side*.26,0,0))
	part(self,Vector3(0,1.15,1.04),Vector3(1.0,.08,.15),dark)
	var yoke_detail := Node3D.new()
	yoke_detail.name="YokeDetail"
	add_child(yoke_detail)
	for side in [-1.0,1.0]:
		part(yoke_detail,Vector3(side*.24,1.32,1.07),Vector3(.065,.025,.055),brass)
	var hologram := MeshInstance3D.new()
	hologram.name="HolographicDisplay"
	hologram.mesh=hud_mesh()
	hologram.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(hologram)
	add_child(hud_traces("62e5ed"))
	add_child(hud_traces("f3a14c",true))
	# Projector hardware is buried in the sculpted fascia; only the glass HUD is exposed.
	part(self,Vector3(0,1.365,.69),Vector3(.30,.055,.16),dark)
	var projector := finish("243742",.72,.30)
	part(self,Vector3(0,1.395,.68),Vector3(.22,.018,.095),projector)
	for side in [-1.0,1.0]:
		part(self,Vector3(side*.40,1.31,.70),Vector3(.11,.075,.26),projector)
		for index in range(3):
			var led := finish("55dce8" if index!=2 else "e69a45",.0,.25)
			led.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
			led.emission_enabled=true
			led.emission=Color("49d9e6" if index!=2 else "e69a45")
			led.emission_energy_multiplier=.8
			part(self,Vector3(side*(.37+index*.028),1.36,.78-index*.045),Vector3(.012,.009,.11),led)
	for side in [-1.0,1.0]:
		part(self,Vector3(.23+side*.10,1.37,.58),Vector3(.09,.05,.12),dark)
		var lens := finish("50d9e8")
		lens.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
		part(self,Vector3(.23+side*.10,1.40,.58),Vector3(.045,.008,.055),lens)
	name="ForgeCockpitInstruments"
	# Fit this fascia to FORGE's narrower canopy and put the display behind the glass.
	transform=Transform3D(Basis.from_scale(Vector3(.66,1,.75)),Vector3(0,-.03,-.08))
	var controls: Node3D=get_node("YokeDetail")
	# The common feedback code reparents these buttons onto the existing yoke.
	controls.transform=transform.affine_inverse()
	for node in find_children("*","MeshInstance3D",true,false):
		if node.name in ["FlightDisplay","HolographicDisplay"]:continue
		var material := node.material_override as StandardMaterial3D
		if material and material.shading_mode==BaseMaterial3D.SHADING_MODE_UNSHADED:
			material.albedo_color=Color("ff9c35")
