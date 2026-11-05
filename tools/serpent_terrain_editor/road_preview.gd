@tool
extends MeshInstance3D

# Read-only reference ribbon: shows the actual Crimson Serpent deck while
# sculpting in Terrain3D. This is not a separate drivable track.
func _ready() -> void:
	call_deferred("_build_road_guide")

func _build_road_guide() -> void:
	var path: String="res://serpent_route.json"
	if not FileAccess.file_exists(path):
		return
	var parsed: Variant=JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(parsed)!=TYPE_DICTIONARY:
		return
	var data: Array=parsed.get("route",[])
	if data.size()!=192:
		return
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(data.size()):
		var a: Array=data[i]
		var b: Array=data[(i+1)%data.size()]
		var c: Array=data[(i+2)%data.size()]
		var p:=Vector3(float(a[0]),float(a[1])+0.1,float(a[2]))
		var q:=Vector3(float(b[0]),float(b[1])+0.1,float(b[2]))
		var r:=Vector3(float(c[0]),float(c[1])+0.1,float(c[2]))
		var f: Vector3=Vector3(q.x-p.x,0,q.z-p.z).normalized()
		var g: Vector3=Vector3(r.x-q.x,0,r.z-q.z).normalized()
		var side:=Vector3(f.z,0,-f.x)
		var side_next:=Vector3(g.z,0,-g.x)
		var width: float=10.5 if i>=86 and i<=126 else 12.0
		var next_id: int=(i+1)%data.size()
		var next_width: float=10.5 if next_id>=86 and next_id<=126 else 12.0
		var aa: Vector3=p-side*width
		var bb: Vector3=q-side_next*next_width
		var cc: Vector3=q+side_next*next_width
		var dd: Vector3=p+side*width
		for vertex in [aa,cc,bb,aa,dd,cc]:
			st.set_normal(Vector3.UP)
			st.set_uv(Vector2(vertex.x*0.1,vertex.z*0.1))
			st.add_vertex(vertex)
	mesh=st.commit()
	var guide:=StandardMaterial3D.new()
	guide.albedo_color=Color(0.09,0.38,0.45)
	guide.roughness=0.9
	guide.cull_mode=BaseMaterial3D.CULL_DISABLED
	material_override=guide
