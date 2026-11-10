# Neon Cross — Aerial City Rebuild (track ID 0)

**Status:** first full scene replacement, pending Godot CI and Android driving review. The 192-sample figure-eight, jump from 44–52, checkpoint timing, save records, touch handling and existing other circuits are preserved.

## Racing-first city

Instead of a continuous asphalt road on an enormous slab, the city now sits 82 metres below the racing plane. Compact platforms only exist at the start, launch, landing, northern turns, lower crossing and finish. The remaining 125 of 192 segments (approximately 65%) are open-air racing corridors with luminous rails, arched guide gates and magnetic support from the existing controller. Hover footprints are hidden when there is no visible platform. The ballistic leap remains an actual jump.

## Efficient world design

The new scene lives in game/tracks/neon_cross_rebuild.gd, independent of the old giant city builder. Four sectors each contain MultiMeshes for near towers, roof light bands and distant skyline silhouettes. The buildings are static, visually grouped and placed with geometric clearance from the racing route. The world uses one dark low city floor, very sparse material batches, unlit navigation accents, no scenery collision and no additional realtime lights or active environmental effects. Geometry is built once at load.

Godot recommends MultiMesh for drawing repeated geometry at lower submission cost, but warns that one far-spanning MultiMesh may be culled as a whole. Grouping by sector lets the camera cull large offscreen groups while keeping scene objects predictable.

## Compatibility

No circuit renumbering. Both branches of the figure-eight still cross at the same XZ position and retain local route-index driving guidance. No change to tested steering, repulsor support, magnetic wall response, checkpoint events, jump recovery or reverse logic. Skyfall, Tidal Relics, Frostline, the canyon scenery and fleet content are untouched.

## Review gates

1. CI parser, full figure-eight regression and dedicated scene contract test.
2. Actual chase, cockpit, top-down and leap screenshots to verify orientation and readable high-speed route markers.
3. Android on-device frametime and FPS comparison against the original Neon Cross, recorded under matching settings.
4. Structural art pass after the racing route is approved: curved transit megastructures, distinctive city districts, improved near-field architecture and richer depth without dense independent props.
5. Once validated, port the same racing-first visual/world separation to later tracks.

Do not label prototype scene geometry as final art or report phone-performance gains until they are measured on the phone.

## Skyline corridor correction (Build Track Layouts)

The first scene pass over-emphasized a city 82m beneath the craft. That made the
track feel isolated in the sky instead of threading a high-rise environment.
This revision follows the previously agreed visual-depth strategy:

- **Near zone:** twelve true 3D high-rise compositions with stepped roofs,
  mechanical rooftop silhouettes, fins and raised neon facade strips. Primary
  towers sit at the center of each figure-eight lobe, within the open spaces
  between both race arms, and along their outer edges. Towers extend 40–84m
  above the nominal racing altitude, so drivers pass beside buildings and can
  look down on their roofs when jumping. Each footprint is tested against the
  entire 2D race spline (including both crossing branches).
- **Mid zone:** up to 176 additional instanced building volumes, capped per
  spatial quadrant and stepped to varying heights. Roof caps and route-facing
  facade strips are additional material/sector-batched 3D instances, never
  per-building scene objects or dynamic light sources.
- **Far zone:** two cut-edge cylindrical skyline silhouettes of differing
  radii and heights (procedural geometry, not yet image-textured panoramas).
  These establish distant city depth with two additional mesh submissions.
  Later we can replace the silhouettes with baked high-resolution panorama
  atlas materials if phone measurements justify it.
- **Racing first:** the route, speed, jump, magnetic support and open-air
  partial deck are unchanged; all building objects remain collision-free and
  are outside the controlled race clearance envelope.

Implementation: game/tracks/neon_cross_skyline.gd is invoked from
neon_cross_rebuild.gd. No further world changes are made to tracks 1–9.
**Still pending:** in-game camera verification of tower silhouettes and
measured Android GPU frame-time; do not assume geometric savings guarantee FPS.
