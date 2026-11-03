# Tremor MK IV — automotive surfacing research and build contract

Research date: 2026-11-03. Scope: SceneForge / Blender 4.5 / Godot 4.5 / Android compatibility. Retain the currently playable MK III until independently reviewed and tested.

## Primary finding: quality is lost in our export pipeline

At tools/tremor_mk3.py, shaped_fender() creates a BEVEL modifier and does not apply it. tools/build_fleet.py then joins all static meshes by material via bpy.ops.object.join(), which does NOT preserve/apply modifiers on selected source objects. Therefore the shaped fender's bevel may be silently discarded before glTF export. Confirm this with a Blender isolated regression before modifying any vehicle.

Recommended immediate safe patch (after testing):
1. Keep editable source meshes in an untouched Blend master.
2. Copy objects to an export collection; ensure each mesh has consistent applied scale.
3. On each export copy, evaluate/apply desired Geometry/Bevel/Subsurf/Solidify modifiers in their intended order, BEFORE joining or baking.
4. Measure realized triangle count and inspect per-object evaluated topology. Compare before/after silhouette, edge geometry, surfaces and object bounds.
5. Only THEN join groups for draw-call optimization, while retaining separate transparency, animation and dissimilar material pieces.
6. Recheck that Godot shows the same curved edges as the Blender approved master.

The current script also uses Cube Projection globally after joins and only 256px procedural base color maps; it does not produce an actual high-to-low normal bake for Tremor. Joining by material merges object data but does NOT weld separate islands or make physically continuous fender transitions. The current body is an end-to-end cross-section loft with relatively sparse station control, and its pasted fender surfaces remain separate from the chassis.

## What Class-A style continuity means for a game vehicle

Autodesk Alias defines G0 position, G1 tangent, G2 curvature, and G3 curvature rate continuity. Our goal is NOT to claim actual OEM-certified Class-A surfacing. It is to achieve controlled visual continuity in a low-cost Blender mesh and inspect it with reflection tests.

- Seamless monocoque to fender/roof shoulder: aim for visually G1 and where reflective sweep is important visually G2-like transitions; share border vertices and control derivative directions across connected patch boundaries.
- Actual door seam, split engine cover, separate panel edge: G0 meeting along a deliberate small panel gap is desirable, not an error. Separate sheetmetal doors are legitimate; copying a raised rectangle on a vehicle side is not.
- A-pillars, windshield, roof side header, cargo edge: deliberate chamfered, manufactured hard highlights rather than smoothed sports-car bulb volumes.
- Do not apply subdivision blindly to the whole SUV; it will soften shoulders and destroy intentionally planar features.

## Recommended hybrid master model geometry

Stage 1 — Designer's surface skeleton:
- Preserve approved Tremor SUV ortho profiles and dimensions: tall near-upright windshield, long mostly flat roof, blunt nose, side door slab, body-width fenders, broad hover rear.
- Write centerline, beltline, shoulder line, bonnet break, sill, greenhouse footprint and wheel/hover housings as 3D curves with shared control stations.
- Separate dominant primary A-surfaces from small B-side supports: hood+shoulder, continuous exterior flank, roof/greenhouse cage, rear quarter, nose face.
- Model one half, mirror to the other; ensure seam normal and mirrored topology are checked.
- Begin with few regularly spaced sections, and increase density gradually only where local silhouette curvature demands it. Avoid spline overshoot: clamp cubic interpolation or use Bezier control handles instead of uncontrolled station overshoot.
- Use radial/longitudinal surface parameters to produce connected quad grids (or matched bicubic patches). A flush fender should not intersect the hull as a disconnected shell.

Stage 2 — Panel engineering:
- Design each hard surface with controlled real radius; use small multi-segment bevels on armor edges and wider rolled transitions on the main shoulders.
- Different bevel styles by feature function: tight manufactured steps on vents/plates, broad continuous rounds on large body shoulder, and deliberately sharp shadow breaks around separate panels.
- Primary continuity BEFORE trim operations: lock the reflection flow of side, hood and quarter; perform Boolean or inset operations after those surfaces have enough resolution.
- Actual openings: create solid backed manifold cutter geometry, apply Boolean Exact on the high-poly copy, inspect for pinching, retopologize bad junctions. Do NOT run booleans on unsealed or coplanar shell surfaces and assume perfect topology.
- Separate cabin window, doors and hood by explicit perimeter curves and opposing panel lips, with consistent physical gaps and inward return surfaces; keep glass its own material and render layer.

Stage 3 — Detail and materials:
- Fix mechanical modules to designed structural mounting coordinates; do not scatter cylinders or bars where openings ought to be.
- Front hover rings should sit in actual recessed sockets, not protrude as detached wheels.
- The underside magnetic cells can remain mostly covered; the rear twin nozzles need visible interior depth and assembly connections.
- Use proper edge-seam UV unwrap for body, not universal cube projection; allocate UV texture space by visual importance. Reuse mirrored details only where asymmetry is not expected.
- Build high-poly detail source then an optimized explicit game mesh; tangent-space normal, base-color, packed metallic/roughness/AO (as pipeline permits), emissive where needed. Bake with selected-to-active and a suitable cage/ray envelope. Check normals in Godot (OpenGL +Y normal maps).
- Do not mistake 256px material noise or ambient-light exaggeration for surface detail. Use controlled studio lights and actual PBR texture maps.

## Minimal Blender modifier policy

Smooth exterior body mesh: Mirror if modeled half -> carefully controlled Subdivision Surface (level 1–2 only as justified) -> controlled trimming/retopo -> calculated/specified normals.

Hard structural component: actual geometry -> Boolean where necessary -> Bevel (angle/weight restricted, multi-segment) -> Weighted Normal if this improves planar face shading. A Weighted Normal is not an alternative to a curved surface.

Panels/retainer plates: formed surface -> Solidify with valid normals -> tight Bevel -> optional Weighted Normal.

Never join away nonapplied modifiers. Never pretend a bevel counts as successful just because a modifier exists in source. The exported evaluated mesh is the truth.

## Reflection and curvature inspection

Use the same camera, scale, focal length, light rig and environment for old and new versions.
1. Pure clay: long softbox highlights across hood, front shoulder and long side. No decorations.
2. Black gloss and light tunnel/zebra stripes: stripes must bend intentionally; no unexpected kinks, singularities or breaks where surfaces should be seamless.
3. Matcap + wireframe: spot poles on broad reflective surfaces, uneven quad spacing, pinching at intake/door corners, and uncontrolled triangle fans.
4. Normal-angle/curvature continuity diagnostic: sample adjacent patch normals and second differences across intended smooth boundaries. Report discontinuity; DO NOT treat this metric as proving G2 continuity on its own.
5. Fixed front, side, top, rear, front 3/4, rear 3/4. Front-side rear results are mandatory.
6. Compare with the exact existing MK III shape and the visually approved Shrike reference. Compare geometry, not a cherry-picked studio light.
7. Mark aesthetics as review-required until approved; a successful CI export or triangle count never certifies good automotive surfacing.

## Technical and Android gates

- Preserve existing Tremor rig nodes (Kestrel_Yoke and Kestrel_Tail_0 through _4) and Godot cockpit/glass nodes, and all vehicle mounting semantics.
- Audit water-tightness only where relevant to physically closed shell parts; separate glass and doors can be intentionally open surfaces.
- No coincident coplanar overlay panels, major hidden intersections, visible geometry clipping or inverted winding.
- Explicit main visual GLB, LOD/optional showroom detail, UV set, normal/tangent data and stable material slots.
- Avoid enormous textures for unseen opponent cars. Use LODs for distance, inspect imported Godot LOD transitions, measure phone FPS/memory rather than assuming a number-of-triangles budget guarantees 60 fps.
- Regression: before/after exported fender bevel edge count, projected orthographic dimensions, rig node names, missing textures, and Godot automatic import/render.
- Publish immutable A/B test views separately. No APK replacement until both the comparative geometry QA and playable Godot smoke test pass.

## First mandatory experiment

A small fender-to-door transition coupon, NOT the full Tremor:
- Control A: our current independent fender loft crossing chassis at 6 sections.
- Prototype B: connected shared-vertex quad patch, Bezier/Hermite-controlled longitudinal shape, clamped shoulder radii, and fit an actual seam into the door.
- Generate matching clay, zebra, wireframe, curvature/normal overlay and top/front profile screenshots.
- Test whether export applies the non-destructive edge rounding correctly and whether intended highlights survive import into Godot.
- Choose the better form and only then scale this pattern to the full Tremor body.
- Keep the previously playable Tremor build intact until a demonstrated win.

## References checked

Autodesk Alias geometric continuity, levels G0–G3:
https://help.autodesk.com/cloudhelp/2026/ENU/Alias-Video-Tutorials/files/essential-concepts/continuity-g0-g1-g2-g3.html

Ali Ismail's advanced automotive polygon model/surface reflection guide:
https://www.carbodydesign.com/article/59531-modeling-cars-in-polygons/

Blender 4.5 Join explicitly drops modifiers of selected objects:
https://docs.blender.org/manual/en/4.5/scene_layout/object/editing/join.html

Blender 4.5 Bevel Modifier and Harden Normals/Face Strength:
https://docs.blender.org/manual/en/4.5/modeling/modifiers/generate/bevel.html

Blender 4.5 Boolean: only manifold results guaranteed and Exact for complex overlaps:
https://docs.blender.org/manual/en/4.5/modeling/modifiers/generate/booleans.html

Blender Cycles Baking — selected-to-active, ray distance and cage:
https://docs.blender.org/manual/en/4.5/render/cycles/baking.html

Godot 4.5 glTF importer, tangent generation and mesh LOD options:
https://docs.godotengine.org/en/4.5/classes/class_resourceimporterscene.html

Godot 4.5 normal map OpenGL convention:
https://docs.godotengine.org/en/4.5/tutorials/assets_pipeline/importing_images.html
