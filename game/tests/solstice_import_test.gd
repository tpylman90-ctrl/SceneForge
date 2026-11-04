extends SceneTree

# Prototype-only GLB import check; the race roster is unchanged.
func _initialize() -> void:
    call_deferred("check")

func check() -> void:
    var source_path := "res://assets/prototypes/Solstice_S01.glb"
    assert(ResourceLoader.exists(source_path),"Solstice study asset missing")
    var packed: PackedScene = load(source_path)
    assert(packed != null,"Godot cannot import Solstice GLB")
    var craft: Node3D = packed.instantiate()
    root.add_child(craft)
    var meshes := craft.find_children("*","MeshInstance3D",true,false)
    assert(meshes.size() >= 25,"Lost Solstice geometry on import")
    var shell: MeshInstance3D = craft.find_child("SOLSTICE_UNIFIED_OUTER_SKIN",true,false)
    var windshield: MeshInstance3D = craft.find_child("SOLSTICE_FRONT_WINDSCREEN",true,false)
    var roof: MeshInstance3D = craft.find_child("SOLSTICE_STRUCTURAL_ROOF",true,false)
    assert(shell!=null and shell.mesh!=null)
    assert(windshield!=null and windshield.mesh!=null)
    assert(roof!=null and roof.mesh!=null)
    var mat: Material = windshield.get_active_material(0)
    assert(mat is StandardMaterial3D,"Godot windshield material was lost")
    assert(mat.transparency!=BaseMaterial3D.TRANSPARENCY_DISABLED,
        "Windshield becomes opaque in Godot")
    print("SCENEFORGE_SOLSTICE_GODOT_IMPORT_OK ",meshes.size())
    quit()
