# Forge body construction

Reference: user-supplied `forge_mk_iii_reference.png` (29 October 2026).
This pass establishes proportions and surfacing; decorative detailing is deferred.

Research sources (Blender primary documentation):
- https://docs.blender.org/manual/en/5.4/modeling/modifiers/generate/subdivision_surface.html
- https://docs.blender.org/manual/en/5.0/modeling/modifiers/generate/mirror.html
- https://docs.blender.org/manual/en/5.0/modeling/modifiers/deform/shrinkwrap.html

Application:
- A sparse quad cage controls the silhouette, rather than dense interpolated rings.
- Mirror with clipping/merge precedes level-two Catmull-Clark subdivision.
- Closely spaced stations support the nose and tail; broad panels use wider spacing.
- Hull aperture and curved glazing derive from the same section table. This provides
  a common starting boundary; subdivision of separate patches still requires visual
  inspection at the seam. No claim of exact G2 continuity is made.
- Solidify adds inward thickness after smoothing. End caps close the main body/blades.
- Secondary panels can later use Shrinkwrap to the resolved master. It is not needed
  for this initial pass and has not been added speculatively.
- Existing control and tail rig roots remain compatible with the fleet exporter.

Validation: run `SCENEFORGE_ONLY_CRAFT=forge blender --background --python tools/build_fleet.py`.
The exporter checks GLB vertex colors, named rigs and the existing 40k triangle cap.
Run `blender --background --python tools/preview_forge_body.py` for neutral studio
hero, front, side and top renders plus a saved review scene.
