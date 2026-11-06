# Kestrel — user-supplied 3D body upgrade

The user corrected the intended target of `futuristic car 3d model.glb`:
**KESTREL**, not Shrike. The imported mesh has 39,464 triangles and
20,955 vertices, one fused mesh and no original materials, textures, UVs,
or independently operable glass. Its original GLB is preserved in
`Kestrel_User_Upgrade_Source_Meshopt.glb` (SHA-256
`2a436ee1e67b6e3df51d70033cb7546f531bf719fd940ef28020b8bd5a0d88aa`).
It uses required `EXT_meshopt_compression` and `KHR_mesh_quantization`,
so it is **not directly importable** into the Godot 4.5 runtime.

The source geometry is decoded without changing its 39,464 triangles.
The game-ready version is rotated from its original +X forward
to Godot +Z forward, scaled to 6.8 m long, and moved to a 0.34–2.22 m
height envelope. Resulting bounds are 3.576 × 1.889 × 6.797 m.
Original, restrained slate/carbon/rust vertex colors are applied to the
model's existing vertices, with a dark windscreen impression and brighter
rear feather areas. This is a presentation-material addition, not new
body geometry. The game-ready GLB uses standard uncompressed glTF without
required unsupported extensions and ships as `*.glb.xz`, unpacked by
`tools/install_kestrel_upgrade.py` before Godot import.

### Runtime behavior
Kestrel remains vehicle index 0 with its existing race physics, steering,
reverse, boost, cockpit HUD, sound, repulsor mounts and upgrade ownership.
For exterior views, the uploaded user model is the visible body. Kestrel's
original procedural rig remains loaded but is hidden from exterior review
to avoid duplicate fenders/fin stacks. Entering the cockpit hides the fused
uploaded shell and restores the established functioning procedural cockpit
and transparent windshield, since the upload has no separate glass or
interior. The original Kestrel remains the fallback if the optional upload
is missing outside CI. The user asset is not repurposed for Shrike.

The model has no independent wing/door pivot or physical transparent
windscreen. As a result, door-opening and separately articulated imported
fin visual upgrades are **not** claimed for this pass; new topology and
subparts are needed to add those without inventing hidden geometry.
Automatic and on-device quality checks will cover cockpit view, speed,
FPS, visual scale and actual race events.

**Licensing:** User-supplied geometry, rights not independently verified.
Do not relicense this source as CC0 or imply it was built from scratch.
Its provided filename and original content SHA are retained for audit.
