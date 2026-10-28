# Twilight sky and circuit pack

The original twilight panorama is game/assets/twilight_sky.jpg. It was created with the built-in image-generation tool and converted to an optimized JPEG (185 KB), with no external assets or paid API workflow. The same panorama is used in the Foundry inspection scene and all three circuits.

Prompt: "Seamless equirectangular 360-degree sky panorama texture for a semi-realistic sci-fi Android racing game. Wide 2:1 blue-hour twilight sky, layered soft atmospheric clouds, deep blue zenith, subdued warm amber horizon. Horizon halfway vertically; lower half dark blue atmospheric gradient, no land. Match left/right edges; smooth poles. Polished game environment matte painting; subtle stars. No buildings, terrain, cars, text, logo, sun disk, or watermark."

## Circuits

Use TRACKS in the driving view. Selecting a circuit starts a fresh attempt; RESUME keeps the current attempt. Best lap times are stored per circuit in user://records.cfg.

- Neon Cross (medium): original figure-eight with elevated crossing jump.
- Skyway (easy): broad oval, elevated 2 m above the city ground, launch ramp and wide landing. No crossing traffic branch.
- Viper Rift (hard): S-bends, mild banked road cross-sections, a 3 m crest, longer crossing leap with stronger magnetic launch assist.

All use the same Kestrel, controls, boost and reverse rules. This is a time-trial prototype with barrier containment; no traffic opponents or wall-driving physics. Road banking affects mesh height, vehicle support height, cockpit roll and repulsor footprint roll. Flight remains ballistic with reduced steering.

## Validation

game/tests/circuits_test.gd drives every layout at 30/60/120 simulation Hz, tests approach speeds 8/32/42 m/s, checks one successful launch/landing per lap without recovery, and exercises actual menu-triggered scene replacement. Existing figure-eight, controls, boost, cockpit and reverse checks remain.

CI publishes Skyway/ViperRift overview, cockpit and airborne renders plus Circuit-select.png. CI software-render FPS does not predict Android performance.

## City detail and wall response

The district pack adds a batched distant skyline, storefront awnings and entry frames, plus mechanical equipment, transit signs, freight crates and plaza lights outside the racing surface. No extra realtime lights or external assets are used.

Barrier impacts remove outward velocity while preserving tangent motion. A speed-dependent inward recoil (1.3–4.5 m/s) decays over time; a 0.28 s contact cooldown suppresses repeated impulses and blocks thrust into the contacted wall while permitting sliding and steering away. Speed loss scales with impact angle. Reverse retains its selected direction. Landing-zone containment uses its wider deck width. Failed-jump recovery clears recoil.

wall_rebound_test.gd checks glancing, head-on, reverse and already-separating contacts, repeated-contact suppression, and controller recovery at 30/60/120 Hz.
