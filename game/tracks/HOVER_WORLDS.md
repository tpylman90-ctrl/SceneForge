# Beyond the Road — SceneForge hover terrain worlds (IDs 7–9)

**Status:** original procedural first-playable layouts implemented on a feature
branch, pending Godot CI and Android driving review. Existing IDs 0–6, save
records, vehicle physics, boost and the ongoing Crimson Serpent visual pass
remain untouched.

## Why these environments are possible

These craft hover above a route-relative support field. A water surface, ice,
mud, grass, cobblestone or an elevated deck need not impose wheel friction.
The important challenges are route shape, sight lines, altitude, course
markings, walls, gates and recovery. **No special per-surface speed penalty**
has been added. All procedural scenery is visual only; a single deterministic
192-sample centerline is the racing contract.

The new circuits are approximately 0.88–0.90 km around. Their four sectors are
mapped to the existing quarter-checkpoint logic. All use the proven 44–48
magnetic-leap span and a three-lap solo challenge. Records remain keyed by ID
and craft, so prior record files are not remapped.

## Track 7 — Tidal Relics

**Identity:** turquoise lagoon, submerged ancient city, preserved stone
causeways and broken temple courtyards. Mostly OPEN WATER; do **not** lay a
continuous road mesh across the lagoon merely for consistency with city
courses. The water is a broad, simple batched decorative surface beneath the
craft. Thin illuminated buoys identify the invisible lateral repulsor
boundary; a magnetic confinement correction still prevents lost vehicles.

- 0–47 **Open Lagoon** — water-running start, sweeping tidal curves and
  approach to the broken bridge leap
- 48–95 **Drowned Causeway** — first stone deck, columned masonry, broken
  colonnade landmarks and dry turns
- 96–143 **Ruined Citadel** — mossy crossing, narrow temple approaches,
  broad exit into water
- 144–191 **Flooded Gardens** — lagoon slalom around beacon markers and a
  waterborne finish

**Hero moment:** a low flight from open water to a ruined causeway. Need a
submerged-arch detail pass, curved waterline masonry, sculpted ruins,
deterministic water motion and optional spray sprites once the first playable
line is approved. Avoid expensive planar reflections.

## Track 8 — Frostline Wilds

**Identity:** a mountain glacier feeding a muddy spring basin and lush
wind-beaten alpine meadows. All sections can be skated across by the same
repulsor physics; changing surface is a visual and navigational event.

- 0–47 **Frozen Mirror** — high-speed ice-surface opening
- 48–95 **Thaw Basin** — icy leap and mud approach through frozen spires
- 96–143 **Alpine Meadow** — flowing grassland S-curves and open visibility
- 144–191 **Glacier Return** — stone transition and frozen home straight

**Hero moment:** breaking out of an ice corridor into a broad, lush valley
with meltwater channels. First pass has batched ice shards and four ground
material palettes. Later design passes should add coherent rocky snowbanks,
ice fissure detail and a dramatic glacial wall. Ice does **not** reduce grip.

## Track 9 — Skyfall Run

**Identity:** steeply elevated start platforms, suspended rock islands,
fast sky corridors and luminous navigational gates. This course is not a
conventional road in the air. It uses actual deck meshes only at start,
staging island and finish; large route portions have *no visible floor*.

- 0–69 **Ascent Platform** — climb and magnetic jump
- 70–110 **Cloud Gates** — open-air anti-gravity lift corridor
- 111–125 **Sky Island** — short visible landing/checkpoint platform
- 126–148 **Final Airway** — another airborne lift corridor
- 149–191 **Return Deck** — suspended finish platform

**First-pass flight contract:** existing touch controls remain left/right,
throttle, brake and boost; the authored magnetic lift ribbon controls altitude
during open-air segments. Hover ground rings are hidden in those sections.
A true six-degree-of-freedom flight mode (pitch/roll/yaw + lift control) is
a separate later milestone; do not describe it as already implemented.
The 44–48 standard jump still uses ballistic launch and normal recovery.

**Hero moment:** 100+ metres above floating islands, flying through an open
sequence of illuminated gates before a dramatic platform landing. Future
work needs atmospheric cloud geometry, multi-layer sky depth, more
sophisticated island meshes, lane gates with entry/exit direction tests
and more expansive safe flight corridors.

## Technical first-pass contract

- New routes: `game/tracks/hover_worlds.gd` only. Existing Crimson
  sculpt/textures/rocks are not modified.
- One material per surface class and batched procedural scenery. No paid
  assets, imported meshes, real-time water simulation, reflection probes,
  dynamic weather or extra shadow-casting lights in the first pass.
- New IDs are appended; existing IDs 0–6 are stable. Do not renumber.
- Checkpoint, race event, per-craft records, controls, boost, reverse, wall
  recovery and camera continue through the shared `city_loop.gd`.
- Route-following magnetic containment remains invisible on open water and
  aerial corridors. Stage testing must confirm that feels intentional rather
  than an unexpected collision with an invisible wall.
- Air corridor Y is scripted for now. Current gameplay does not yet let
  players climb or descend at will.

## Verification gates

1. Godot 4.5.1 parsing; `res://tests/hover_worlds_test.gd` plus all original
   driving, wall-rebound, canyon and race tests.
2. Race chooser: ten selectable IDs, correct labels, records and three-lap
   classification on 7–9.
3. CI preview: overhead, cockpit, jump screenshots for each new course,
   using the established build pipeline.
4. Phone: native Android hardware test at 60 FPS target, no geometry pop,
   phone-safe color contrast, readable course markers, no undesired lift
   tunnel snaps, and no sticky invisible barriers.
5. Only after approved driving lines: final scenic asset composition,
   textured geology, convincing water/ice/mud/grass and improved airborne
   presentation. Track 7 and 8 should visually feel natural, not like box
   collections. Android FPS claims require actual phone measurement.
