# Preserved user-supplied vehicle source models

This folder holds **input/source assets**, not disposable CI artifacts. Do not
delete, rename, recompress or relicense files here during repository cleanup.

## Shrike

`Shrike_MK_I_Android_LOD_ready.glb` is the existing, user-supplied textured
Shrike GLB. `tools/install_showroom_shrike.py` accepts that name directly
(or the optional alias `shrike_uploaded.glb`); **no manual rename is needed**.
The installer validates the glTF 2.0 binary and required rig nodes, then
copies it to `game/assets/showroom/shrike_uploaded.glb` during CI.

The approved uploaded Shrike is used by both the Fleet/Foundry and racing when
available (see `game/vehicles/fleet_catalog.gd`). The procedural Shrike is a
fallback. The original source remains untouched in this folder.

Its node names include `Kestrel_Hull`, `Kestrel_Yoke` and
`Kestrel_Tail_0`–`4`; these are compatibility names, not an instruction to
substitute a Kestrel model. A fused canopy still limits independent cockpit
glass adjustments.

## Kestrel

`Kestrel_User_Upgrade_Source_Meshopt.glb` preserves the original uploaded
Meshopt-compressed source, while
`Kestrel_User_Upgrade_GameReady.glb.xz` preserves the SHA-pinned prepared
standard-GLB baseline. Both are needed for
`tools/install_kestrel_upgrade.py`, which generates a refined game-ready
runtime copy. See `KESTREL_USER_UPGRADE.md` for provenance and checksums.

## Licensing

These GLBs were supplied by the user. Their independent redistribution rights
have not been verified; do not automatically mark them CC0 or assume their
licenses match the original procedural Blender generator scripts.
