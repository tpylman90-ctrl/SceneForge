# Crimson Serpent — Racing-Optimized Blender + Godot Environment Kit
**Implementation brief and first build contract · 2026-11-08**

## Goal and acceptance criteria
Make the Crimson Serpent canyon and asphalt look materially richer than the
current smooth terrain **without repeating the 41 FPS triplanar/2K failure**.
Ship only if the Android handset remains approximately **59–61 FPS** at
Sunstone Approach, Arch Run, the canyon leap and a full lap. Performance is
not inferred from a passing GitHub Actions run.

**Frozen systems:** route, race controls, barriers, jumps, vehicle physics,
sculpted `height.r16`, sealed cliff shell, 2×2 static near/far terrain
chunks, fog, existing vertex AO and vehicle assets. Red Mesa and Devil's
Gate are deliberately excluded. The original 256px canyon base texture
continues to cover broad terrain; the kit adds limited, richly shaped
objects only where driving-camera composition benefits.

## Blender asset manifest — meters, local Y-up in Godot
All original assets are generated with Blender 4.5.3 and exported as
individual UV-mapped `.glb` meshes. In Blender, local X is lateral,
local Y is cliff thickness, and local Z is height. glTF export uses Y-up.

| Module | Width × vertical height × thickness (m) | Purpose | Triangle ceiling |
|---|---:|---|---:|
| `wall_a` | 19 × 17 × 3.0 | fractured stratified near wall | 750 |
| `wall_b` | 25 × 21 × 4.2 | tall vertical scarp | 750 |
| `wall_c` | 16 × 15 × 3.1 | narrow weathered wall insert | 750 |
| `ledge_a` | 11.5 × 4.2 × 4.5 | protruding bench | 750 |
| `ledge_b` | 14 × 3.6 × 5.1 | overhanging shelf | 750 |
| `boulder_a` | approximately 2.6 × 1.5 × 1.9 | reusable low-poly talus | 150 |

Total source kit is capped at **3,500 unique triangles** across six GLBs.
Individual objects are intentionally closed, not 1-sided rock cards. Low
poly silhouette and deep fracture relief are in actual Blender geometry,
not encoded through expensive tangent-space normal maps.

### Source of truth and build reproducibility
- Blender generation: `tools/build_serpent_rock_kit.py`
- 512px texture generation: `tools/bake_serpent_racing_textures.py`
- Expected intermediate GLBs: `game/assets/scenery/serpent/*.glb`
- Atlas: `game/tracks/serpent_textures/rock_atlas_512.png`
- Road texture: `game/tracks/serpent_textures/asphalt_512.png`
- Manifest: `build/serpent-kit-report.json`

All artwork is original procedural work, no paid tools or external models.
Textures and GLBs are built **before Godot's editor import** in Actions;
the scripts and CI cache key are versioned, generated binaries are not
treated as the source of truth. The Android game does no texture
synthesis, procedural cliff modeling, Blender execution, or atlas baking.

## Shared 512px rock atlas
The atlas contains four independently tileable 256px regions (2×2):
top-left red/orange sediment; top-right shadowed brown fracture;
bottom-left pale sunlit bedding; bottom-right gravel/ledge brown.
UVs on the Blender models are allocated with 3–4px tile-edge guards to
avoid filtering into adjacent atlas patches. Each model assigns a chosen
UV quadrant and uses the same Godot `StandardMaterial3D`.

The shader uses **one albedo lookup per pixel**. No 2K maps, normals,
triplanar projection, screen-space AO, per-pixel splatmap mixing or
dynamic reflection probes. Existing geometry and baked vertex shading
handle most of the large-scale rock contrast.

## Lightweight road surface
One original 512px grayscale/tinted `asphalt_512.png` multiplies the
existing asphalt base and previously baked wheel-track/shoulder vertex
colors. Uses existing world-space XZ UVs; no additional road draw calls,
normal textures or shadow passes. The road geometry itself is unchanged.

## Godot integration and placement
`game/tracks/serpent_rock_kit.gd` loads the six imported Blender GLBs,
extracts the UV-carrying Mesh resources, and places many copies using
**one MultiMeshInstance3D per archetype**. A single shared rock atlas
material is assigned to all six. Placement is deterministic from the
192-point race spline: broad cliff segments are attached to the true
sculpted heightfield, not an independently modeled canyon. A nearest
road-segment distance check and jump/arch exclusions protect drive space.
Boulders are placed outside the road barriers at sparse intervals. All
props are **visual only, no collisions** and cannot snag hovercraft.
Real-time shadow casting is disabled for these decorative batches, as it
previously generated jagged large-area shadows on mobile.

No new per-frame CPU loops or draw-call-heavy individual rock nodes.
The existing terrain supports scenery continuity in all sectors; a small
amount of authored detail appears near useful driving-camera viewpoints.

## Android staging and review gates
1. CI generates both PNGs and six GLBs, checks PNG dimensions and GLB
   headers and asserts the unique triangle budget.
2. Godot import and smoke tests pass, followed by all racing/circuit tests.
3. Crimson Serpent regression validates atlas size, UV channels, six
   instanced module batches, instance count and zero dynamic rock shadows.
4. Confirm zero rock kit nodes on Red Mesa / Devil's Gate.
5. Capture track screenshots; signed APK must be committed and released
   at the **same commit** as the test result. Do not send a stale APK.
6. Phone test: monitor FPS during a lap, view cliff face at low camera
   angles, inspect floating props, repeating UV seams and road texture.
7. **Accept** only if it materially improves close cliff/road appearance
   and stays in the 59–61 FPS band. If performance falls or quality is
   unchanged, disable or revert the kit before adding any more shaders.

### Future work only after passing handset gate
Optional two-channel packed atlas variant, fewer instances and more
deliberately modeled overhangs where proven beneficial. No wholesale 4-way
splatmapping or renderer switch without separate controlled benchmarks.

## Second art-direction gate — Canyon landmarks (November 9, 2026)

The first six-module kit preserved phone FPS but barely changed the silhouette.
This revision deliberately changes the **authored geometry** rather than
stacking more expensive shaders:

- `wall_a/b/c`: increased from ~15–21 m to **28–34 m** in height and
  8–10 m in thickness, more visible above the sculpted heightfield.
  Fractures are cut 2–3 m deep into actual polygon surfaces; stepped
  ledges now extend outward.
- `sunstone_fang`: ~47 m primary tilted fang and ~27 m satellite blade,
  three copies along **Sunstone Approach**.
- `strata_buttress`: three linked, overlapping, tiered masses up to
  ~43 m; four instances frame **Arch Run**.
- `split_chimney`: asymmetrical 52 m and 42 m twin columns separated by
  a genuine open slot; four instances mark **Low Canyon**.

The landmarks use a second original Blender source:
`tools/build_serpent_landmarks.py`. Source assets are assembled as
closed solid meshes with real horizon-breaking geometry, then packed
with baked vertex colors for local cavity/underside darkening.
Every GLB asserts UV0 plus COLOR0; vertices are tinted in the shader by
an ordinary StandardMaterial3D with **one 1024px albedo atlas only**.
Each of its four tiles occupies 512px. The 256px original heightfield
and 512px asphalt remain unchanged.

The 11 landmark placements are art-directed along real spline indices
14,20,28 / 60,67,75,101 / 146,155,166,175. The closest road branch must
be at least 26 m from each placement; they are decorative and have no
vehicle collisions or dynamic shadows. The old 59–61 FPS user baseline
is **not proof of this revision's performance**.

CI also takes real in-game driving-camera screenshots from 7 spline
segments before indices **14,75,155**, so the landmark impact can be
reviewed directly from the intended vehicle approach. Reject the pass
if landmarks do not visibly read at driving speed or FPS drops from
the verified 60 target.
