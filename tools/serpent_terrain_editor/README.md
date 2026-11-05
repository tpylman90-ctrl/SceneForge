# Crimson Serpent — Terrain3D sculpting studio

This is a **separate Godot project for authoring**, not the racing APK.
The release APK and SceneForge's game project remain completely free of
the Terrain3D GDExtension. We use Terrain3D's genuine viewport sculpting
brushes, then bake the edited heightmap into a small signed 16-bit source
file that SceneForge's regular static canyon mesh reads.

## Install (free, Godot 4.5)

1. From the SceneForge repository root run:
   `python tools/serpent_terrain_editor/setup.py --install-terrain3d`
   It downloads **Terrain3D v1.1.0-stable** (MIT license) into this
   authoring project's `addons/terrain_3d/`. It never modifies `game/`.
   The distribution isn't checked into the repository.
2. Open `tools/serpent_terrain_editor/project.godot` using the
   **desktop Godot editor**, not the SceneForge Android APK.
3. Enable Terrain3D in *Project Settings → Plugins* if necessary.
   Open `SerpentAuthoring.tscn`. It contains a Terrain3D node,
   sun, camera and a translucent-color **RoadGuide** reference mesh.
4. Open `addons/terrain_3d/tools/importer.tscn`, select its Importer
   root, and set **Height = res://heightmaps/serpent_seed.r16**:
   width **1024**, height **512**, height range **-32 m to 128 m**,
   Import Position **(-512, 0, -256)** (X,Y,Z).
   Use the importer’s *Run Import*, then specify **Data Directory =
   res://terrain_data** and save. Return to SerpentAuthoring.tscn,
   select Terrain3D and load the saved directory.
5. Sculpt **Raise/Lower, Smooth, Flatten, Erosion** and paint textures in
   the Terrain3D editor viewport. The teal RoadGuide is a reference,
   **not** a substitute racing track. Keep terrain at least ~1 m
   below the road across the width and the canyon leap clear.
6. Save your Terrain3D data directory. Open the importer's **Export**
   section, select **Height (32-bit floats)** and write **EXR**:
   `res://heightmaps/serpent_sculpt.exr`.
   Export must remain exactly **1024×512**, covering the same rectangle.
   Keep heights within **-32 m to 128 m**.
7. From the repository root run:
   `godot --headless --path game --script res://tools/import_serpent_heightmap.gd -- --source <ABSOLUTE_PATH_TO_EXR>`
   The importer verifies the map, samples the real Serpent road and
   rejects sculpt changes that would intersect the driving surface.
   It writes `game/tracks/serpent_sculpt/height.r16`.
8. Commit the edited `height.r16` to SceneForge. CI builds the existing
   static terrain mesh from that heightmap; no terrain plugin is shipped.

## Engine boundary / acceptance

- **Only track 4, Crimson Serpent** reads the sculpt map. Red Mesa and
  Devil's Gate still use their unchanged procedural canyon builder.
- The painted, full-resolution height source is **1024×512 at 1 m per
  pixel**. The Android runtime uses bilinear samples on its existing
  **136×92** render grid (~75k generated vertices), preserving the
  previously demonstrated 60 FPS target. Since that is a coarser grid,
  meter-scale brush details should primarily live in textures; sculpt
  broader shelves/valleys using 5–20 m brushes.
- Use Blender for any true overhangs or cavern ceilings: Terrain3D is a
  heightfield and cannot sculpt an undercut. Extra overhang meshes must
  be collision-checked and LOD-budgeted separately.
- Verify Arch Run and the long rising/descending sections in the actual
  Godot driving camera, not just an editor overhead view.
- CI verifies route clearance, stable terrain data dimensions, the
  canyon's mesh budget and the signed APK export. Phone FPS still needs
  a real-device check after each visually meaningful sculpt pass.
- Terrain3D full-runtime Android operation has experimental mobile
  compatibility considerations; this split pipeline avoids the risk.

Source: https://terrain3d.readthedocs.io/en/stable/docs/import_export.html
Plugin: https://github.com/TokisanGames/Terrain3D/releases/tag/v1.1.0-stable
