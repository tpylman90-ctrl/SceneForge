extends SceneTree

const Crimson = preload("res://tracks/crimson_divide.gd")
const SerpentCanyon = preload("res://tracks/serpent_canyon.gd")

func _initialize() -> void:
	call_deferred("check")

func _nearest_reference(route: PackedVector3Array, x: float, z: float) -> Vector3:
	var closest: float=INF
	var nearest_index: int=0
	var elevation: float=0.0
	for index in range(route.size()):
		var p: Vector3=route[index]
		var q: Vector3=route[(index+1)%route.size()]
		var dx: float=q.x-p.x
		var dz: float=q.z-p.z
		var length_squared: float=maxf(0.001,dx*dx+dz*dz)
		var fraction: float=clampf(((x-p.x)*dx+(z-p.z)*dz)/length_squared,0.0,1.0)
		var px: float=x-p.x-dx*fraction
		var pz: float=z-p.z-dz*fraction
		var distance_squared: float=px*px+pz*pz
		if distance_squared<closest:
			closest=distance_squared
			nearest_index=index
			elevation=lerpf(p.y,q.y,fraction)
	return Vector3(sqrt(closest),float(nearest_index),elevation)

func check() -> void:
	var names := ["CRIMSON SERPENT","RED MESA CIRCUIT","DEVIL'S GATE"]
	var lengths: Array[float]=[]
	for offset in range(3):
		var circuit: int=4+offset
		set_meta("sceneforge_track",circuit)
		set_meta("sceneforge_race_mode",0)
		var scene: Node3D=load("res://city_loop.tscn").instantiate()
		root.add_child(scene)
		scene.set_physics_process(false)
		assert(scene.track_id==circuit)
		assert(scene.track_name()==names[offset])
		assert(scene.route.size()==scene.COUNT)
		assert(scene.get_node_or_null("CrimsonDriveSurface")!=null)
		assert(scene.get_node_or_null("CrimsonDeckSides")!=null)
		for name in ["CrimsonTerrain","CrimsonDistantRidgeline"]:
			var scenic: MeshInstance3D=scene.get_node_or_null(name)
			assert(scenic!=null and scenic.mesh!=null,"Missing canyon scenery: "+name)
			assert(scenic.mesh.get_surface_count()==1,"Scenery must stay batched")
		if circuit==4:
			# Cached segment sampling must reproduce the original brute-force
			# projection across the sculpted basin, including road-adjacent points.
			for xi in range(-3,4):
				for zi in range(-2,3):
					var sample_x: float=float(xi)*97.0+11.0
					var sample_z: float=float(zi)*84.0-7.0
					var reference: Vector3=_nearest_reference(scene.route,sample_x,sample_z)
					var cached: Vector3=SerpentCanyon._nearest(sample_x,sample_z)
					assert(absf(reference.x-cached.x)<0.002,"Serpent cached distance changed")
					assert(absf(reference.z-cached.z)<0.02,"Serpent cached road height changed")
			var rock_group: Node3D=scene.get_node_or_null("CrimsonStratifiedCliffs")
			assert(rock_group!=null)
			assert(rock_group.get_child_count()==8,"Expected four near/far chunk pairs")
			var near_count: int=0
			var far_count: int=0
			var near_vertices: int=0
			var far_vertices: int=0
			var has_bedrock_cap: bool=false
			for child in rock_group.get_children():
				var rock: MeshInstance3D=child as MeshInstance3D
				assert(rock!=null and rock.mesh!=null)
				assert(rock.mesh.get_surface_count()==1)
				assert(rock.cast_shadow==GeometryInstance3D.SHADOW_CASTING_SETTING_OFF)
				var mat: StandardMaterial3D=rock.material_override as StandardMaterial3D
				assert(mat!=null and mat.cull_mode==BaseMaterial3D.CULL_DISABLED)
				assert(mat.albedo_texture!=null and mat.albedo_texture.get_width()==256)
				assert(mat.albedo_texture.get_height()==256)
				assert(not mat.uv1_triplanar and not mat.normal_enabled,"Single-pass UV albedo only")
				has_bedrock_cap=has_bedrock_cap or (rock.mesh.get_aabb().position.y+rock.position.y<=-37.9)
				var vertices: int=rock.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX].size()
				if rock.name.begins_with("Near_"):
					near_count+=1
					near_vertices+=vertices
					assert(rock.visibility_range_end>0.0)
				else:
					assert(rock.name.begins_with("Far_"))
					far_count+=1
					far_vertices+=vertices
					assert(rock.visibility_range_begin>0.0)
			assert(near_count==4 and far_count==4)
			assert(near_vertices>79000 and near_vertices<85000,"Near mesh vertex budget")
			assert(far_vertices<near_vertices*0.30,"Distant LOD is not sufficiently simplified")
			assert(has_bedrock_cap,"Near-wall shell must stay closed")
			var map_path: String="res://tracks/serpent_sculpt/height.r16"
			assert(FileAccess.file_exists(map_path))
			assert(FileAccess.get_file_as_bytes(map_path).size()==1024*512*2)
			var apron: MeshInstance3D=scene.get_node("CrimsonTerrain")
			assert(apron.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX].size()>1000)
			var rubble: MultiMeshInstance3D=scene.get_node_or_null("CrimsonTalus")
			assert(rubble!=null and rubble.multimesh!=null)
			assert(rubble.multimesh.instance_count>=40)
		else:
			var rock: MeshInstance3D=scene.get_node_or_null("CrimsonStratifiedCliffs")
			assert(rock!=null and rock.mesh!=null)
			assert(rock.mesh.get_surface_count()==1)
			var rock_vertices: int=rock.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX].size()
			assert(rock_vertices>2000 and rock_vertices<100000)
			assert(scene.get_node_or_null("CrimsonTalus")==null,"Other canyons must be unchanged")
		assert(scene.jump_start_index()==44 and scene.jump_end_index()==48)
		assert(scene.is_jump_gap(44) and scene.is_jump_gap(47))
		assert(not scene.is_jump_gap(48))
		var length: float=Crimson.route_length(circuit,scene.COUNT)
		lengths.append(length)
		var widest: float=0.0
		for i in range(scene.COUNT):
			var p: Vector3=scene.route[i]
			var q: Vector3=scene.route[(i+1)%scene.COUNT]
			var segment: float=scene.flat(q-p).length()
			widest=maxf(widest,segment)
			assert(segment>0.1 and segment<10.0,"Canyon path has an invalid or excessive gap")
			assert(p.y>-1.0 and p.y<18.0,"Unsafe road elevation")
			assert(scene.road_half_width(i)>=8.5)
			assert(scene.closest_segment(p)["point"].distance_to(p)<0.1)
		assert(scene.route[44].y>scene.route[28].y+2.0,"Canyon launch must rise above approach")
		assert(widest<10.0)
		assert(scene.challenge_laps()==(1 if circuit==4 else 3))
		scene.begin_event(scene.MODE_SOLO_RACE)
		scene.set_physics_process(false)
		assert(scene.race_countdown==3.0)
		for stage in range(scene.challenge_laps()):
			scene.lap_time=32.0+stage
			for gate in [scene.COUNT/4,scene.COUNT/2,scene.COUNT*3/4,0]:
				scene.track_progress(int(gate))
			if stage<scene.challenge_laps()-1:
				assert(not scene.race_finished)
		assert(scene.race_finished and scene.results_panel.visible,"Expected race finish after required stages")
		assert(scene.race_splits.size()==scene.challenge_laps())
		if circuit==4:
			assert(scene.results_info.text.contains("SPRINT STAGE COMPLETE"))
		else:
			assert(scene.results_info.text.contains("3-LAP SOLO CHALLENGE COMPLETE"))
		scene.feedback.stop_audio()
		scene.free()
	assert(lengths[0]>1000.0,"Serpent must be a long curving stage")
	assert(lengths[1]>700.0 and lengths[1]<1000.0)
	assert(lengths[2]>750.0 and lengths[2]<1000.0)
	assert(lengths[0]>lengths[1] and lengths[0]>lengths[2])
	print("CRIMSON_DIVIDE_THREE_COURSES_OK ",lengths)
	quit()
