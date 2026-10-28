# Kestrel reference chassis

`kestrel.tres` owns the chassis identity and handling values. The controller reads
these values rather than embedding chassis-specific performance constants.

Named `ComponentMounts` children identify four repulsor sockets, propulsion,
power core and two aero sockets. Positions are metres in the craft's Godot-local
frame: +Z forward, +Y up, +X to the seated pilot's left. They are attachment contracts for later components;
this build has no upgrade economy or purchasable parts.

`Kestrel_Yoke` and `Kestrel_Tail_0..4` are original Blender rig roots. Runtime
animation changes these roots; geometry stays shared with the foundry preview.
`ChassisVisual` is separate from the heading/position root so visual banking and
hover motion do not rotate the driving input frame.

The cockpit texture displays actual controller speed, gear, throttle demand,
steering command and measured lateral slip. Repulsor bars visualize commanded
load, not a simulated magnetic field. It refreshes at 10 Hz in cockpit view and
2 Hz in chase view using one 512x192 texture and an original bitmap font.

Future Swift and Bulwark chassis should preserve the mount categories while
supplying their own silhouettes, cockpit eye positions and handling data.
