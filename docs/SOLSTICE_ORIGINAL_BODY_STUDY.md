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

## Subsequent shape/audit pass
Actual recessed rear intakes were cut into the shared shell and backed with
inward cavity walls. Stronger integrated fender ridges and partly embedded
hover machinery replaced the initial generic smooth boat-like outline.
Additional source-geometry validation checks for nonmanifold edges before
Solidify. The latest review also produces two CPU Cycles PBR renders and runs
a real Godot Compatibility GLB import test. The asset remains experimental.

## S-01.3 greenhouse and mechanical refinement

The approved basic 8.26 m proportions, original station profiles and the
flowing hood/fender surfaces remain unchanged. The glass was rebuilt from
shared boundary functions: front windscreen to roof, side glass to front
screen and roof, and rear screen to roof are checked numerically at regular
samples with 0.01 mm tolerance. A/B/C pillars are formed dark frame strips
following the same edges; narrow bronze edge accents are secondary.

The former detached rear sail surfaces have been replaced by smooth formed
roof-to-haunch transitions. Their outer hem is located directly on evaluated
rear shoulder surface coordinates (separate intentional manufactured panel).

Eight tapered manufactured cradle webs connect the four hover emitter units
to underbody anchoring coordinates. Three small louvres sit in each actual
rear intake cavity. These details are supplementary to the main connected
body, not fake disconnected fender panels.

New review views: `Solstice-greenhouse.png` and
`Solstice-rear-mechanics.png`. Automated gates enforce the glazing seam
contract, structural part presence, triangle budget, clean main shell,
GLB export and Godot Compatibility import. Artistic reflection matching
and physical phone FPS remain review-required.

## Approved Shrike GLB inspection — original materials study
The approved 8.53MB Shrike GLB has 164,235 triangles, 105,667 vertices,
a 6.80 × 3.56 × 1.85 m bound, one mesh/material and UVs. It uses
three 2048 × 2048 images: albedo, metallic/roughness and normalGL.
Original SOLSTICE pass had 55,160 triangles in 77 GLB meshes and seven
materials, but no texture images at all. These proportions and shader-layer
differences explain its uniform soft appearance; triangles are not the only
difference. Source assets stay unchanged.

The SOLSTICE prototype now creates ORIGINAL deterministic 1024² color,
metallic/roughness, and OpenGL tangent normal atlases. The shell and
panel patches have UV coordinates. Three glTF material textures and the
main body UV attribute are asserted at export time. Microtexture is very
subtle: panel shapes must still come from geometry. No Shrike texture
pixels are ever reused.
Reference: https://github.com/KhronosGroup/glTF-Blender-IO/blob/main/docs/blender_docs/scene_gltf2.rst

## SOLSTICE fine-form refinement, informed by Shrike's real GLB
The primary body silhouette and stations remain unchanged. We added two
shallow, built-in hood extractor ducts to the shared-index hull. Unlike surface
stickers, their outer edges are the original body vertices, with intermediate
formed chamfer-lip rings, genuine dark return walls and inner floors. The two
original rear shoulder scoops now also have rolled edges, improving real
specular highlight breaks without splitting the master fender surfaces.
Three small stators occupy each new hood opening. This geometry is intentionally
more important than decoration and is checked independently in Blender CI.
Original 1024px base-color, packed ORM and OpenGL tangent-space normal maps
provide subtle microdetail without copying Shrike's UV art. For Android, these
three maps are initially used on the hero prototype only; they are not proof
that an opponent LOD can afford the same materials. The prototype must remain
outside the fleet until actual phone reviews and collision/seat controls.

## Visual QA correction: controlled, not noisy complexity
The first true hood cut-outs passed geometry validation but were too wide and
scalloped in the Blender studio images, while the original procedural normal
map produced excessive high-frequency specular mottling. For production
quality, the two hood openings have been made narrower and shallower and the
stators sit deeper inside. The coating now uses much slower, lower-amplitude
roughness/color variation and sub-degree paint micro-normals. This improves
the geometry's highlight readability while preserving separate textured
material channels. The source remains non-final until studio renders are
reviewed; automated topology and material tests alone are insufficient.

## S-01.6 — countersunk fastback cockpit, body-to-cabin proportion correction

The earlier roof crown was approximately 2.09 m high above the model
origin while the central deck/shoulder intersection was around 1.15 m.
Despite refined textures, this produced a disproportionately tall truck-cab
greenhouse standing on a thin body. The reference Shrike uses the opposite
design language: body shoulders climb toward the glazing and the roof is
a relatively shallow, visually integrated top.

Engineering corrections:
- Roof baseline lowers from 1.96 to 1.69 m; crown apex becomes roughly
  1.79 m, with the source body dimensions/long hood retained.
- The primary **connected** monocoque shoulder around the cabin now rises
  continuously (+0.31 m max, Gaussian falloff in width and length).
  Windows visually recess into the fender/shoulder rather than being set
  on a flat elevated base. No extra fender object or fake side cover.
- The front windshield rakes rearward more and its bottom follows a
  hood/cowl-like variable-height section instead of a horizontal frame.
- The roof panel is painted, with separate correctly fitted glazing and
  carefully bounded dark frame strips.
- The **main rear body** receives a smooth fastback crown that grows
  toward the rear window and fades into the long trunk. The shortened
  rear glazing lands against it; no vertical truck-like bulkhead.
- Curved quarter-panel buttress strips sample the same modeled haunch
  as their landing, replacing arbitrary suspended fin geometry.
- The seatback is lowered slightly for roof clearance.

Measured per-build gates check shoulder height, peak roof height, roof
exposure above the shoulder, rear screen slope and exact glazing edges.
Added front-half close side profile and physically lit side render, along
with the existing hero/clay/rear comparison angles. These constraints are
design targets, **not** certification of exact body/roof G2 continuity.
The playable fleet remains unaffected, and the actual Android FPS is not
established by the isolated preview.


## S-01.7 — Actual 3D tail and rear vectored thrust module

**Source-of-truth modeling pass:** This is a Blender generator change, NOT
an AI-produced concept image. Generated from `tools/build_original_solstice.py`
and confirmed only after CI's Blender exports + Godot 4.5 Compatibility test.

- Shortened rear overhang by 360 mm: stern moves from model Z -4.18 m to
  -3.82 m; rear deck center height drops by 120 mm from 0.95 to 0.83 m.
  Retains the forward nose, 4 magnetic hover pods and integrated low cabin.
- Removed both bolted-on cylindrical rear propulsion nozzles.
- Constructed **one recessed oval drive in the actual shared-index main
  body tail**: replaces the old rear end-cap ngon with 4 sampled 72-segment
  elliptical annular bands (288 structural quads) and one sealed bulkhead.
- Multi-stage mouth: molded painted rim, 17 mm offset bronze bezel,
  34 mm inset dark throat, recessed to 285 mm for convincing depth.
- Fourteen physically modeled low-profile radial guide fins, an internal
  bronze machine ring and a small amber central vector capsule. Amber is
  the only luminous propulsion element; no exposed rocket flame.
- The rear port is not a black decal or an external shell. The main
  automotive surface really terminates around the port opening, and
  the recess/duct uses connected geometry with dark inner material.
- Replaced the former floating rear lightbar with two slender outboard
  tail position markers that leave the central thrust chamber clear.
- New real Blender review views `Solstice-thrust-inspection.png`,
  `Solstice-rear-dead-on.png`, and physically-lit
  `Solstice-studio-thrust.png`. The build checks GlTF node names,
  body topology, 288 connected duct quads, 14 guide fins, rear geometry
  parameters, total triangle cap, and Godot import.

This prototype remains separate from the racing fleet; do not treat any
earlier edited concept artwork as verification of the real 3D model.

## S-01.8 — Approved upright rear design implemented in real body mesh

The user rejected the previous swept aft surface because it still resembled
another front nose. The approved image reference is a visual design brief;
it is NOT substituted for the real geometry or an approved game render.

**Source modifications**
- The connected primary body now preserves rear half-width: 1.43 m at the
  rear cut against 1.53 m one station forward. This removes the original
  spear-like taper (0.90 vs 1.28 m), with a broader true stern and a firm
  rear shoulder termination. The tail's central upper deck now measures
  1.10 m high instead of 0.83 m, creating a taller near-upright aft face.
- Reworked the integral rear mesh from four oval bands to **seven 72-quad
  annular bands** (504 shared-index quads) transitioning from a rounded
  rectangle into the same existing recessed oval duct. Bands provide
  painted rear cut-off, slender bronze perimeter, dark graphite rear fascia,
  machined engine bezel and the original deep duct throat.
- Added left and right thin red rear LED signatures in real modeled graphite
  pockets, small position optics, and a 3D-traced rear deck shutline.
- Preserved central 14-vane thrust unit, low integrated greenhouse, existing
  hover cells, paint and performance-focused modeling tools.
- Added direct physical rear-elevation Cycles render and closer rear fascia
  workbench inspection, checking front/rear silhouette consistency in the
  actual model rather than generated concept imagery.

**Validation gates** assert the broad rear width ratio, rear deck height,
504 integrated annulus quads, the named red rear light meshes, the duct and
seam GLB nodes, 75K prototype triangle cap, original body topology and Godot
4.5 Compatibility glTF import. Independent Android drive frame-rate testing
is still required before integrating SOLSTICE into the selectable roster.
