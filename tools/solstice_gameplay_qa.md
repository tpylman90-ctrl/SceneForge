# SOLSTICE playable fleet release checklist

This file intentionally accompanies the first Android release integrating SOLSTICE
as Fleet index 9. Its name selects SOLSTICE-only screenshot captures on the
existing change-aware Android CI pipeline. Gameplay/unit tests still cover all
ten vehicles.

## Source of truth
- Original Blender connected-body generator: `tools/build_original_solstice.py`.
- No AI-generated render or sketch is used as a game mesh.
- Real modeled large rear light recesses, smoked ruby lenses, red brake
  signatures and three swept LED guide ribs on each rear haunch.
- The same master generates the isolated review GLB and the asset-only
  release GLB; `SCENEFORGE_SOLSTICE_ASSET_ONLY=1` suppresses image
  rendering, not source geometry.
- The signed APK requires `game/assets/fleet/solstice.glb`, built from
  the original source in the Android workflow and cached by generator SHA.

## Mandatory acceptance checks
- The original GLB exports below the 75,000-triangle mobile-first budget,
  maintains the connected shell and original three PBR maps.
- Godot 4.5.1 Compatibility importer accepts the GLB.
- Fleet contains exactly ten selectable unique chassis IDs.
- SOLSTICE uses dedicated original-body runtime integration, not
  Kestrel dummy yoke or synthetic five-fin exhaust.
- Three racing circuits complete one lap with SOLSTICE in the headless
  drive simulation, preserving steering, reversing, boost, jumps and lap data.
- The fitted windshield becomes less opaque from inside cockpit and
  returns to the exterior shader afterwards.
- Brake lights and engine emitter materials have independent source
  overrides; the physical 3D lamp pieces are not flattened decals.
- Selecting SOLSTICE in Fleet and Foundry and returning from a track
  preserves its chassis identity.
- Selective capture includes SOLSTICE in garage, rear, seat and racing.
- Permanent signed release success is required before sending a final APK.

## Android visual QA
The published run validates logic and import, not device-specific 60 FPS.
Review on the user's phone for clipping, overdraw, glass visibility,
large high-mounted red LED proportions, rear haunch reflections, camera
height, collision feedback and control responsiveness. All ten craft
retain their previous playable state; SOLSTICE is added rather than
replacing an approved model.

## Fast-mode export bug resolved
The first packaging attempt created the model but failed reporting because
`views` was defined only in the preview-render branch. The report now emits
an empty list in asset-only mode; the actual Blender geometry, UVs,
materials and GLB are identical in both modes. The signed Android build
must re-run from this fix and pass Godot/Fleet/Foundry tests.
