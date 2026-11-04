# Shrike MK I — reversible windshield visibility trial

Baseline: user-approved single textured Shrike GLB at `showroom_sources/Shrike_MK_I_Android_LOD_ready.glb`. **Do not overwrite or remodel this source** in the windshield trial.

## What changed

- The original uploaded mesh contains one approximately 164K-triangle surface and a single baked material, not a separately addressable windshield material. Making that material transparent would also fade body panels.
- On first cockpit entry, `game/vehicles/shrike_windshield.gd` temporarily partitions candidate dark windscreen triangles by their forward-cabin location and base-color texture sample. The parent shell keeps its original opaque material and faces; a child mesh preserves the selected face geometry and original material for exterior modes.
- Entering cockpit hides only the candidate mesh; leaving cockpit displays it again. No polygon is deleted from the source GLB, and the original body and cockpit art remain unchanged.
- Fleet, Foundry and on-track driving now allow the Shrike driver-eye view rather than forcing third-person cameras.

## Verification gates

- Godot tests must detect at least twelve split faces and verify cockpit visibility toggles and restoration of the exterior.
- Build previews: `Fleet-shrike-cockpit.png`, `Foundry-shrike-seat.png`, plus unchanged `Fleet-shrike-hero-clean.png` and `Foundry-shrike.png`. Inspect both before and after, not just a single cropped view.
- Compare windshield screen visibility, center-line horizon, side pillar integrity, tint, interior occlusion and face-boundary artifacts. Keep the released signed APK unchanged if import, runtime, previews or tests fail.
- Confirm Android load time, frame rate and touch VIEW behavior on hardware. GLB and CI software rendering alone cannot certify the phone experience.

## Intentionally deferred

This trial does **not** create physically transparent glass in exterior views, rebuild the original cabin, separate actual glass material islands, install a procedural cockpit/HUD, or remodel the hood. After handset acceptance, a later non-destructive mesh/material reconstruction may implement genuine transmissive glass.
