# SceneForge twin-stick hover control experiment

Status: code integrated; Android CI and phone acceptance pending. This is a deliberately non-production controls experiment that Neon Foundry can eventually reuse without touching its approval-gated hero craft.

## Phone layout

- **Left analog:** hold up for forward thrust; pull down to brake and then reverse; spring-return neutral coasts. Forward and reverse acceleration scale with stick displacement.
- **Right analog:** move left/right to yaw in the same direction; move up/down to increase/decrease repulsor clearance. Both right-axis inputs work diagonally. Releasing the right stick maintains the selected height.
- **BOOST:** tap the large orange button for a 2.25-second burst. Tap again to cancel; the existing race capacitor and recharge rules still apply.
- **Course ceiling:** standard circuits permit 0.8–5.5 metres above the deck reference. Skyfall unsupported/flight segments permit 3–20 metres. Height is a commanded hover target and never represents permission to clip through real objects.
- **Keyboard fallback:** W/S throttle, A/D steer, E/Q height, Shift boost.

## True clearance test

Enter **TRACKS → HOVER PHYSICS LAB**. The neutral gray vehicle is intentionally a temporary test rigid body. Four real ground probes provide lift. Drive under the blue overhead beam at low altitude, then climb over the amber floor fence; both are collision objects on the obstacle layer, excluded from downward floor sensor hits. The test keeps its actual unsupported gap and tall side walls.

The standard tracks use a spring-suspension prototype and route-relative altitude. They do **not** yet provide universal 3D obstacle collisions; only the physical proving ground demonstrates real over/under clearance. Transfer to Neon Foundry Racing only after device review and explicit acceptance. The original NF-H01 twelve-gate approval sequence remains unchanged.

## Test expectations

Unit test: independent touch pointers; diagonal steering + climb; signed throttle; deadzone; drag bounds; tap-to-boost timer; paused control. Rigidbody test: probe support, forward drive, yaw, altitude target min/max and neutral hold. Circuit smoke: altitude band at 30/60/120 Hz, jump/rebound and classic route regression. Mobile acceptance: observe real altitude change, pad-to-pad lateral feel, under-beam and over-fence traversal, collision and phone FPS.
