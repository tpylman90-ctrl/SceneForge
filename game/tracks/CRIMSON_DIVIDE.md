# Crimson Divide — three-course first build

**Production stage:** procedural first-playable pass, code committed on main. **Android CI result and handset handling have not yet been verified.** Track IDs 0–3 and their existing records are unchanged.

## Environment contract

Crimson Divide is a sunlit sandstone basin with ochre mesas, rust-red stratified cliffs, freestanding stone needles, rough-cut rock arches, dry canyon terrain and a warm horizon. Each course uses original vertex-colored, stratified geological formations and rolling terrain; no paid generation, high-resolution imported textures or additional realtime scene lights are required. Road surfaces and continuous containment barriers remain distinct from visual cliffs.

Road geometry is sampled from hand-placed **Catmull–Rom control points**. Total route lengths below are approximate centerline chord lengths calculated from 192 spline samples, not measured race time. Each course carries its own segment width, elevation, banking, desert sector names, launch-to-landing stretch, signage and selectable track ID.

## Track 4 — Crimson Serpent

**Approximate length:** 1.15 km per complete route. **Event:** *single-stage sprint challenge* (one complete long route instead of three laps). **Width:** generally 24 m, narrowing to 21 m through the scenic ridge. **Difficulty:** medium.

| Course section | Sample index | Corner-by-corner intention |
|---|---:|---|
| Sunstone Approach | 0–43 | Launch straight, twin broad right-to-left hillside sweeps, rising ridge and downhill bends into a canyon leap |
| Arch Run | 44–85 | Four-segment raised leap, wide landing, layered rolling curves and a flowing run through open sandstone |
| Cliffside Sweep | 86–125 | A large clear-span stone arch at index 86, narrower cliff road, sustained direction changes and vista |
| Low Canyon | 126–191 | Long return valley with high vertical stone markers and broad S-curves into the start/finish gantry |

**Driving contract:** rhythm and line choice, not hairpin after hairpin; it is the longest of the three tracks. The first build uses the current closed-loop race engine for reliability, so stage start and finish share a physical line. A *true point-to-point sprint with distinct start/finish* remains a later engine feature; do not label this as implemented.

## Track 5 — Red Mesa Circuit

**Approximate length:** 0.81 km, **event:** three-lap circuit challenge. **Width:** 26 m throughout. **Difficulty:** easy.

| Course section | Sample index | Corner-by-corner intention |
|---|---:|---|
| Mesa Plateau | 0–43 | Fast broad opening left and sweeping uphill ridge |
| Horseshoe Ridge | 44–95 | Short protected leap with a generous landing, long rounded top-of-mesa arc |
| Basin Crossing | 96–138 | Wide valley turn, tall mesa near the edge, enough width for future AI overtakes |
| Red Rock Return | 139–191 | Natural-looking overhead rock gateway and a descending straight-to-curve finish |

**Driving contract:** easiest route in Crimson Divide, generous margins and clean sightlines. Intended as the race pack's later AI traffic training ground.

## Track 6 — Devil's Gate

**Approximate length:** 0.80 km, **event:** three-lap circuit challenge. **Width:** 20.6 m generally, narrowing to 17.8 m through the stone gate sequence. **Difficulty:** hard.

| Course section | Sample index | Corner-by-corner intention |
|---|---:|---|
| Gate Approach | 0–43 | Rising lateral bends and a crest into a short canyon leap |
| Stone Needles | 44–95 | Rapid elevation transitions and needle markers at index 77 |
| Broken Ridge | 96–143 | Technical left-right-right changes, narrow width and another needle marker at index 101 |
| Spiral Descent | 144–191 | Tight valley combination, needle at index 148 and a fast but demanding finish |

**Driving contract:** deliberate braking and steering control; do not expect full-throttle precision through every segment.

## Common features

- Canyon tracks use IDs 4, 5 and 6. Original IDs 0–3 are stable.
- The scenic canyon now uses a single batched vertex-colored rock mesh (mesas, buttes, stone needles and talus), a separate undulating ground mesh and a continuous distant ridgeline. Decorative rock has no collision; road containment is authoritative. Shared faceted normals and dark strata seams create carved geology without imported textures, extra lights or moving objects.
- Starting gantries and landing signs follow the actual route tangent.
- Canyon jumps use a 4-segment missing-deck span rather than the city's 8-segment span. Launch, recovery and road support use the same gameplay functions.
- Free Drive, Time Trial, one-stage Serpent event and three-lap Mesa/Devil events use existing vehicle/boost/upgrade physics and local records.
- The circuit chooser now scrolls on mobile to fit all seven courses.
- CI should parse the runtime, execute `tests/crimson_divide_test.gd`, capture three **overview, cockpit and jump** previews per course, then package the APK. CI software-render previews do not verify phone frame rate or steering feel.

## First phone review gates

1. **Serpent:** continuous smooth driving, arch clearance, visible cliff turns, finish registered exactly once, no gap recovery at normal race speed.
2. **Mesa:** easy full lap, ample road margin, no obscuring rock geometry.
3. **Devil:** technical corners remain driveable without sticky wall rebounds, camera keeps road ahead in view.
4. **Performance:** ensure scene load time, FPS and memory remain viable with all nine craft on Android.

**No visual craft modifications were added.** Earned performance-part upgrades remain mechanical.

## November 3 scenery-quality pass

- Replaced the flat 660×400 ground slab with a collision-free height-varying 38×28 grid, tapered to stay under the drivable road.
- Replaced the repeated cylinder-forest landmarks with radially deformed, multi-strata mesas, eroded buttes and needles. The base colors, ledge profiles and silhouettes vary deterministically per course.
- Added a single low-poly, continuous far canyon ridgeline and scattered talus for depth and speed parallax.
- Adjusted canyon-only skylight and sun intensity to reduce blown-out colors. City routes retain their previous lighting.
- Road, barriers, jump geometry, course controls and gameplay collision remain unchanged. Three scenery meshes replace many individual scenic props. The existing stone arches and track signs remain.
- CI test now checks scenery node presence, batching and a broad static rock vertex cap. **Android FPS and real-device screenshots require verification after CI.**

## Crimson Serpent canyon corridor — focused second-pass experiment

**Scope: track 4 only.** Red Mesa and Devil's Gate still run the prior
`canyon_scenery.gd` scene builder. The racing engine, wall collision,
track controls, jump gap, crafting systems, garage and fleet are unchanged.

- `serpent_canyon.gd` samples the route centerline and builds a connected
  136×92 heightfield using the nearest track-segment distance. This carves a
  real winding gorge into one landscape surface: 16.7 m clearance from the
  centerline, steep rocky slopes immediately beyond the shoulders, broad upper
  benches and a valley that merges naturally where the route doubles back.
  There are no individual pillar props pretending to be cliff walls.
- Cliff detail uses smooth surface normals, nuanced geology vertex colors
  with irregular shallow bedding, and one small procedurally generated
  triplanar grain map. The skyline is a simple 96-segment batched silhouette.
- A separate low-poly shoulder mesh and one MultiMesh of small talus add close
  parallax. All are decorative, static and collision-free.
- Serpent alone has increased climb/descent variation and a warmer aerial
  perspective fog treatment. No extra dynamic lights or volumetric fog.
- Expected: roughly 75,000 cliff vertices (one terrain mesh), inexpensive
  far silhouettes, plus one instanced debris draw. CI tests check the isolated
  scenery change and vertex budget. **Phone FPS and load time must be measured
  on-device after this build before extending the technique to other tracks.**

## Crimson Serpent — cliff realism, erosion terraces and mobile shadow fix

- Replaced abruptly stepped 4-sector wall heights with a continuous, loop-periodic height modulation. Steeper rock escarpments now have a talus foot, two eroded shelves, upper vertical faces and natural mesas, all in one heightfield.
- Darkened the rock base and added irregular weathered sediment coloring, plus a 256×256 procedurally generated world-triplanar albedo-grain texture. No new geometry density or imported paid assets.
- Disabled terrain casting oversized jagged shadows onto the racing surface, retaining natural cliff lighting and vehicle shadows. Added a second inexpensive far ridge in the same draw surface.
- Scoped completely to track 4; Red Mesa / Devil's Gate remain unchanged. CI tests guard the no-terrain-shadow performance policy. Android FPS needs verifying on-device for this revision.

## Crimson Serpent — Terrain3D authoring bridge

The continuous Serpent rock basin is now sourced from
`res://tracks/serpent_sculpt/height.r16`, a checked-in **1024×512**
single-meter editor heightmap. SceneForge's existing 136×92 static mesh
builder samples it bilinearly, so Android keeps the Compatibility renderer
without Terrain3D or any extra geometry.

The initial height source is seeded from the previous canyon with four broad
sculpt-brush incisions in the outer rock wall. A real, editable Terrain3D
studio now lives in `tools/serpent_terrain_editor/`. Install the pinned
MIT-licensed Terrain3D v1.1.0-stable plugin in this **separate Godot project**
and use its sculpting / paint tools against the matching 192-sample road
guide. After editing, export a 32-bit height EXR from the Terrain3D importer
and run `game/tools/import_serpent_heightmap.gd` headlessly. The converter
verifies height range and road clearance before replacing the Android-safe
`height.r16` source.

Only **track 4** reads this map. Tracks 5/6 and all fleet assets are intact.
No Terrain3D binaries are shipped in Android, and the runtime's 136×92
terrain mesh budget is retained. Sculpting cannot form overhangs, which will
require isolated, optimized Blender meshes later.

**Verification:** The Godot editor studio is prepared in the repository,
but interactive Terrain3D brush editing has not yet been performed here.
The initial heightmap is an authored seed, not a claimed finished sculpt.
Game load, preview and handset FPS must be verified after CI.
