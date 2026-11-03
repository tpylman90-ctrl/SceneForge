# NEON FOUNDRY — Hover Racing conversion plan

Status: **early implementation underway**. The race-weekend UI, timed starts, solo three-lap challenge and Iron Harbor circuit prototype have been committed to main; GitHub Actions/Android device validation is not yet confirmed here. CPU rivals, career, credits, new garages and the other new worlds remain planned. This roadmap covers the wider conversion.

## Baseline to preserve

- Godot 4.5.1 / Android; free tools and original or appropriately licensed assets.
- Nine selectable craft, including the user-uploaded Shrike racing shell and AEROLITH.
- Existing, playable circuit IDs **0 Neon Cross**, **1 Skyway**, **2 Viper Rift**.
- Mobile touch steering, throttle, brake/reverse, boost, multiple cameras, repulsor behavior, leap/recovery, checkpoint-based lap timing and per-craft/per-circuit records.
- Existing Foundry and Fleet inspection scenes; do not regress model selection, camera framing, quality settings or APK publishing.
- Circuit IDs 0–2 and their historical records remain stable when new circuits are introduced.

## Creative pillars

1. **Every track has a driving identity.** Silhouette, rhythm, visibility and one signature set-piece matter more than decoration density.
2. **Every craft feels owned.** A hero vehicle is visible at useful scale in a functional garage, paddock and results screen.
3. **A satisfying race loop precedes visual sprawl.** Select craft → race setup → countdown → race → finish classification → credits/unlocks → garage.
4. **Mobile-first performance.** Instancing, batching, occlusion, conservative dynamic lights, tiered assets and QA on the actual phone.
5. **No paid services or required connectivity.** Offline races and local saves; no simulated gambling, premium currency or paywalls.

## Circuit catalog

The first three layouts currently use a common city environment. Keep them as the initial **Neon District** pack and make their signage/landmarks more distinct, instead of calling them unrelated worlds.

| Stable ID | Circuit | Environment and race geometry | Signature mechanic | Priority |
|---|---|---|---|---|
| 0 | Neon Cross | Twilight city figure eight | Elevated crossing jump | Existing / polish |
| 1 | Skyway | Forgiving elevated city oval | Wide high-speed bank and landing | Existing / polish |
| 2 | Viper Rift | City technical S-bends | Banked turns, long leap | Existing / polish |
| 3 | Iron Harbor | Industrial port, container lanes, gantries | Inset-oval chicanes and harbor leap | First playable scene prototype committed; needs phone review |
| 4 | Crimson Divide | Red-rock canyon, cuttings, bridge spans | Ravine jump; dramatic sightlines | First fully distinct outdoor biome |
| 5 | Emerald Run | Forested mountain valley | Flowing bends, waterfall and tunnel landmarks | Expansion |
| 6 | Orbital Velocity | Orbital structure above a planet | Dramatic inclined transitions; *not* fully free-flight physics | Expansion |
| 7 | Stormbreak | Ocean platforms and stormfront | Long open-air leap, difficult late apexes | Final-tier circuit |

**Course specification for each circuit:** route centerline, left/right edge widths, surface elevation and bank, forward-facing checkpoints, visible start/finish, safe respawn anchors, gap launch and landing regions, AI/ghost racing line, production cameras, mobile geometry budget and one screenshot-worthy landmark. Every road feature must agree with vehicle-support physics and barriers.

**Design rule:** separate route/collision data from procedural scenery. Avoid copying the 1,338-line city_loop.gd into one script per new track. Move existing tracks into a data-driven circuit registry with environment-scene references; migrate without changing IDs 0–2.

## Garage locations

Use **one shared fleet/inspection controller and save data**, with several environmental scenes. No separate garage should silently duplicate vehicles or modify handling.

### A. Foundry Workshop — player's home

- Purpose: select craft, inspect body/underside/cockpit, apply unlocked upgrades and paint, view repair/status.
- Architectural mood: industrial fabrication shop; worn concrete, structural gantries, visible lifts, warm task lighting and cyan tools.
- Camera: front-three-quarter hero shot plus front, tail, side, underside and cockpit presets.
- Plan: central vehicle service pad with clear orbit envelope; workbench/parts wall to left, diagnostics wall to right, visible workshop exit at rear. No fake doorways.
- First release: retain current Foundry workflow; add a workshop visual theme and garage-mode navigation later.

### B. Circuit Paddock — race-day prep

- Purpose: pre-race selection, circuit/weather briefing, practice/qualifying/race mode, and post-race results.
- Mood: temporary high-tech pit tents, telemetry boards, tool racks, mechanics' platforms and lighting matched to the selected track.
- Function: player craft occupies main service bay, competitors in distant low-detail background bays only if performance permits.
- Transition: garage → race loading → countdown → race → classification → paddock.

### C. Skyline Gallery — collector's garage

- Purpose: showroom, trophy display, favorite-vehicle inspection, photo mode.
- Mood: premium glass-and-metal mezzanine high above the neon city; low visual clutter around the vehicle.
- Function: turntable presentation and trophy wall. This is a cosmetic unlock, not an alternate storage system.
- Camera/framing: wide establishing view then centered close-up; protect the craft silhouette against window mullions.

### D. Outlaw Depot — stretch concept

- An abandoned transit terminal repurposed by underground racers; unlockable social identity/visual theme.
- Only add when the primary three locations have proven functional and performant.

For each room: define vehicle circulation/clearance, arrival opening with actual passage depth, lighting budget, collision, player camera and tactile touch targets **before** dressing. Room floor plans, prop references, final Blender compositions and exports require the normal room review gates. No paid mesh generation.

## Racing gameplay: ordered milestones

### Milestone 1 — true race shell (must ship before adding many tracks)
- Reuse the current track and controls; introduce a start grid and 3-2-1-GO countdown.
- **Practice / Time Trial** as two clear selections: practice free-run and timed clean laps. Keep existing best times.
- **3-Lap Race** initially against a recorded ghost or deterministic pacing target; clearly label it non-AI until opponent craft physically race.
- Race-complete state: finishing position/time where valid, lap breakdown, new best, replay and return-to-paddock/garage.
- Pause/abort/retry without leaving stuck throttle, boost or audio.

### Milestone 2 — first fully themed track and garages
- Iron Harbor: geometry and props from reusable modular pieces, with distinct sky/fog, lane silhouettes and dock cranes; course-specific screenshots and physics smoke tests.
- Foundry Workshop theme and Circuit Paddock scene, using one shared craft inspection controller.
- First local credits and cosmetic unlocks, earned only through races; save migration and rollback test.

### Milestone 3 — real opponents
- 3–5 CPU-controlled craft after the race shell is stable. AI follows a racing spline with obstacle anticipation, safe overtakes, recovery and no teleporting near the player.
- Race rank, collision rules, rubber-band limits (if any), difficulty and sanity checks across 30/60/120Hz.
- Standing starts and finish/retirement classification; avoid selling a ghost as wheel-to-wheel AI.

### Milestone 4 — career
- Starter district cup → industrial cup → outdoor cup → advanced orbital/storm events.
- Unlock new racing venues and cosmetic items through results. Preserve craft choice and player best records. Do not make basic steering performance dependent on grind.
- Distinct vehicle classes may be introduced only after handling and AI balancing.

## Implementation and regression constraints

- Move circuit metadata to a registry only with automated tests confirming track ID, geometry, lap/jump behavior, records and selection for all original three circuits.
- Do not place interactive hazards within blind launch or landing sightlines.
- CPU/gpu budgets should be measured on the actual Android review device; CI software-render FPS is not phone FPS.
- Target a smooth 60 FPS on the current phone where feasible, offering a performance setting if new rooms or crowds exceed headroom.
- Render first-pass **top-down track map, on-track chase and cockpit**, plus **garage front-three-quarter and rear** before detail passes. Distinguish preview imagery from tested mobile runtime.
- Quality gates: Godot headless parse; full circuit/race regression; UI transition; scene capture; signed APK from existing CI; phone review.

## Immediate build order

1. Freeze a baseline branch/commit and add **race shell** using current Neon Cross track; do not risk modifying Shrike/AEROLITH content simultaneously.
2. Prove countdown, 3-lap completion, replay and return to garage on phone.
3. Prototype Iron Harbor road layout in clay/wire and chase view; confirm racing line, collision and jump recovery before adding port dressing.
4. Design Foundry Workshop and Circuit Paddock as shared-controller scenes; review their function and floor plans before final geometry.
5. Add ghosts/CPU challengers and then the wider circuit catalog.

**Implementation note:** race-event code, a fourth course layout, and industrial scenery are committed but require passing CI and phone review before being called shipped. The proposed distinct garages, more environments, racing AI and career features have not been implemented.
