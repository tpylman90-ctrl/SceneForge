# SOLSTICE S-01 — original connected-body vehicle study

**Status:** independent experimental model, *not* in the selectable SceneForge fleet.

## Intent
This vehicle is a long-tail hover GT, not another Shrike or Tremor variation.
Visual proportions: 8.26 m long; low needle-like nose; broad shoulder crests;
recessed panoramic cabin; narrowed midbody undercut; muscular rear quarters.
Deep petrol-teal clearcoat, graphite framework and champagne-bronze accents.

## What this pass demonstrates
- One welded-by-construction *quad surface* gives the main hood, side body,
  front fenders, rocker and rear haunches their shared topology. No disconnected
  fender boxes or 'join all body parts' illusion.
- Monotone cubic Hermite longitudinal station interpolation; analytic Gaussian
  shoulder bulges and waist recess (smooth derivatives, no boxy intersections).
- A genuine cockpit aperture through the body skin, then a 28 mm Solidify rim.
- Independent, fitted windshield, side glazing, rear screen and roof surfaces.
- Manufacturable A/C-pillar tubes, cantrails and a genuine interior tub.
- Four separate lift/magnetic machinery groups and twin aft nozzles.
- An editable .blend master plus evaluated GLB game-asset candidate.
- Consistent real Blender renders: front, rear, side, top, front 3/4, rear 3/4,
  and a neutral clay surfacing audit. These are not synthetic concept images.

## Technical cautions
The parametric quad mesh is mathematically continuous within its own surface;
that does NOT prove OEM Class-A G2 surface matching at *separate* patch seams.
The independent roof/glass and the painted shell need artistic assessment of
fit, tangency, reflections, seal clearance and visibility on actual phone.
The prototype material and geometry are explicitly unapproved pending review.
Workbench review images assess shape, not final PBR reflection or Android FPS.

## Rebuild
From repository root, on Blender 4.5:
\`\`\`sh
blender --background --python tools/build_original_solstice.py
\`\`\`
Outputs under \`build/original-solstice/\`:
- \`Solstice_S01_Master.blend\` (editable)
- \`Solstice_S01.glb\` (game asset candidate)
- \`Solstice-hero.png\`, \`-rear-quarter.png\`, \`-front.png\`,
  \`-rear.png\`, \`-side.png\`, \`-top.png\`, \`-clay.png\`
- \`geometry-report.json\`

A dedicated GitHub Actions workflow generates/reports every study build. It
does not modify the playable fleet or add this experimental asset to Android.

## Acceptance gates before full vehicle details
1. Confirm side/top proportions, fore-aft balance and rear visual identity.
2. Audit hood-to-front-shoulder and flank-to-rear-haunch highlights in clay.
3. Inspect true gap/overlap between canopy glass and body aperture.
4. Examine GLB in Godot Compatibility and check transparency + driver camera.
5. Establish racing LOD, rig mounts and Android performance before fleet entry.

## Underlying methods
- Blender evaluated modifiers and glTF exporter: https://docs.blender.org/api/4.5/bpy.ops.export_scene.html
- Blender Subdivision Surface: https://docs.blender.org/manual/en/4.5/modeling/modifiers/generate/subdivision_surface.html
- Automotive surface continuity: Autodesk Alias Class-A surfacing.
- Earlier project research: docs/TREMOR_MKIV_AUTOMOTIVE_SURFACING_RESEARCH.md
