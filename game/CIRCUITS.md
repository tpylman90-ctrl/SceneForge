# Twilight sky and circuit pack

The original twilight panorama is game/assets/twilight_sky.jpg. It was created with the built-in image-generation tool and converted to an optimized JPEG (185 KB), with no external assets or paid API workflow. The same panorama is used in the Foundry and the four city/harbor circuits. Crimson Divide uses a lightweight procedural sandstone-tinted sky instead.

Prompt: "Seamless equirectangular 360-degree sky panorama texture for a semi-realistic sci-fi Android racing game. Wide 2:1 blue-hour twilight sky, layered soft atmospheric clouds, deep blue zenith, subdued warm amber horizon. Horizon halfway vertically; lower half dark blue atmospheric gradient, no land. Match left/right edges; smooth poles. Polished game environment matte painting; subtle stars. No buildings, terrain, cars, text, logo, sun disk, or watermark."

## Circuits

Use TRACKS in the driving view. Selecting a circuit starts a fresh attempt; RESUME keeps the current attempt. Best lap times are stored per circuit in user://records.cfg.

- Neon Cross (medium): original figure-eight with elevated crossing jump.
- Skyway (easy): broad oval, elevated 2 m above the city ground, launch ramp and wide landing. No crossing traffic branch.
- Viper Rift (hard): S-bends, mild banked road cross-sections, a 3 m crest, longer crossing leap with stronger magnetic launch assist.
- Iron Harbor (medium; first environment pass): inset-oval harbor route, shipping-container stacks, dock cranes, industrial towers and established launch/landing mechanic.
- Crimson Serpent (medium; **1-stage sprint**): ~1.15 km of flowing S-curves, stone arch, cliff road and a short canyon leap. A long closed route is used in this first engine pass; true point-to-point mode is not yet shipped.
- Red Mesa Circuit (easy): ~0.81 km wide mesa loop, broad horseshoe, rock gateway and protected jump.
- Devil's Gate (hard): ~0.80 km of technical ridge turns, stone needles, narrow gates and technical descending bends.

See [Crimson Divide route layouts](tracks/CRIMSON_DIVIDE.md) for exact course design and review gates.

All use the same fleet selection, controls, boost and reverse rules. This is a solo-race and time-trial prototype with barrier containment; no traffic opponents or wall-driving physics. Road banking affects mesh height, vehicle support height, cockpit roll and repulsor footprint roll. Flight remains ballistic with reduced steering.

## Race weekend (first implementation)

The EVENT menu offers FREE DRIVE, TIME TRIAL (3-2-1 countdown and personal-best lap timing), and solo CHALLENGE (standing start, event record, results and replay). Crimson Serpent is a one-stage sprint; the other six are three laps. Three-lap challenges and Serpent's sprint award race credits redeemable for mechanical-only performance parts in the Foundry; visual modifications are not yet available. CPU rivals and career are still planned. The new game/tests/race_event_test.gd exercises the race lifecycle and is required by CI.

## Validation

game/tests/circuits_test.gd drives all four layouts at 30/60/120 simulation Hz, tests approach speeds 8/32/42 m/s, checks one successful launch/landing per lap without recovery, and exercises actual menu-triggered scene replacement. Existing figure-eight, controls, boost, cockpit and reverse checks remain.

CI is configured to publish Skyway, Viper Rift, Iron Harbor and the three Crimson Divide overview/cockpit/jump renders plus Circuit-select.png. The new canyon tracks must pass their dedicated geometry and event-mode tests before export. CI software-render FPS does not predict Android performance.

## City detail and wall response

The district pack adds a batched distant skyline, storefront awnings and entry frames, plus mechanical equipment, transit signs, freight crates and plaza lights outside the racing surface. No extra realtime lights or external assets are used.

Barrier impacts remove outward velocity while preserving tangent motion. A speed-dependent inward recoil (1.3–4.5 m/s) decays over time; a 0.28 s contact cooldown suppresses repeated impulses and blocks thrust into the contacted wall while permitting sliding and steering away. Speed loss scales with impact angle. Reverse retains its selected direction. Landing-zone containment uses its wider deck width. Failed-jump recovery clears recoil.

wall_rebound_test.gd checks glancing, head-on, reverse and already-separating contacts, repeated-contact suppression, and controller recovery at 30/60/120 Hz.
