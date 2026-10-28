# Neon Cross circuit

The original city loop is now a 192-segment figure-eight: x=80*cos(t), z=32*sin(2*t).
The start remains at the right-hand end. The two center crossings are route
indices 48 and 144; the first is the airborne branch and the second stays at
street level. District checkpoints use quarters of COUNT.

The controller uses a local route-index cursor to resolve the crossing. Do not
replace it with a global nearest-point query in driving code: both branches
occupy the same XZ position. Global queries remain useful for geometry tests.

The approach climbs from index 28 to 44, reaching 4.2 metres. There is no road
mesh from segment 44 through 51. Route points in this gap are guidance only.
The landing starts at 52, is initially wider, and descends to street level by 68.
Buildings and landmarks have been moved clear of the crossing and lobe roads.

At the lip, forward approaches receive a magnetic launch assist of at least
30 m/s and a 6.5 m/s upward kick. Gravity is 14 m/s^2. Steering and thrust have
reduced influence in flight. Landing compresses the visual suspension briefly;
repulsor ground rings hide in the air. Failed attempts return to the approach,
without erasing the running lap clock. This is arcade guidance and containment,
not triangle-mesh vehicle collision physics.

Godot test: --headless --path game --script res://tests/figure8_test.gd
It exercises crossing identity, full laps at three simulation rates, slow/normal/
fast launch approaches, landing, lower-branch traversal, capture and recovery.
These tests do not predict phone FPS.

--capture --track-jump captures an actual simulated jump near its apex.
Add --track-cockpit for the driver view. The existing overview and action
capture switches and release filenames remain available.
