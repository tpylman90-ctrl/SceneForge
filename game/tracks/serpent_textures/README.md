# Crimson Serpent — 2K sandstone material

`sandstone_cliff_2k.tres` is an editor-editable Godot StandardMaterial3D.
Its **original** tileable 2048×2048 albedo and OpenGL normal maps are baked
by `tools/bake_serpent_textures.py` (Python standard library, deterministic).
No purchased assets or runtime synthesis on Android.

To open in Godot, generate the image sources from repository root first:

```bash
python3 tools/bake_serpent_textures.py --output game/tracks/serpent_textures
```

The Android GitHub Actions pipeline executes that command **before** Godot's
image import. The PNGs are deliberately not checked in; the generator is
the source of truth. Godot's resource inspector can edit normal intensity,
triplanar scale, tint, filtering and roughness in `.tres` directly.

Material is opaque and keeps **Cull Disabled** from the previously verified
close-wall fix. It uses a single 2K albedo, single 2K normal, subtle
normal_scale=0.30, triplanar world-space projection and mipmapped filtering.
The terrain's vertex colors retain its broad red-orange geology variation.
The terrain has the **same vertex count** and no new collision or lights.

**Baseline on user's Android: 59–61 FPS** with previous 256² procedural
albedo and no normal. 2K is sufficient source detail, not proof that extra
triplanar normal reads are free: measure FPS on-device before approving.
If performance drops, reduce or disable normals, or use cheaper single-axis
projection rather than adding more polygons.
