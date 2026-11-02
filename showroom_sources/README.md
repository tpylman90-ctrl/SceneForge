# Uploaded Shrike — Fleet / Foundry showroom only

Place the user-approved **Shrike_MK_I_Android_LOD_ready.glb** in this folder,
and rename it **shrike_uploaded.glb**. The file is a pre-oriented glTF 2.0
binary, including the original textured model and the seven SceneForge
node names `Kestrel_Hull`, `Kestrel_Yoke` and `Kestrel_Tail_0`–`4`.

The workflow runs `python tools/install_showroom_shrike.py` after restoring
any Blender-generated assets and copies the exact GLB, unchanged, into
`game/assets/showroom/shrike_uploaded.glb` before Godot imports assets.

**Only Fleet and Foundry use this uploaded asset.** The driver/racing scenes
continue using `game/assets/fleet/shrike.glb` from the procedural generator.

Without the uploaded binary, the original procedurally generated Shrike
continues loading as a safe fallback. When present, the workflow checks that
the actual uploaded showroom model rendered and includes it as SelectedCraft.glb
in the viewer release.

Notes:
- The uploaded Tripo asset is a single textured mesh: canopy transparency
  and a full cockpit driving view require later mesh separation.
- Do not apply the old Shrike procedural HUD or synthetic exhaust details
  to this showroom version.
- Confirm the model's Tripo export/license terms before publicly redistributing
  it. This directory lives in a public repository.
