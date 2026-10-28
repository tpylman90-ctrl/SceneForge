# SceneForge fleet

Five selectable, driveable craft. Open FLEET from the Foundry or driving view. Choose a craft, orbit it by dragging, use FRONT / TAIL / COCKPIT, then DRIVE. Track choice is retained. Only the selected craft is instantiated during play.

| Craft | Silhouette | Cruise | Handling |
|---|---|---|---|
| Kestrel | Slate/orange raptor; refreshed vents, pod hydraulics, heat shields and rear bracing | 115 km/h | Balanced |
| Piledriver | Purple/brass cage, broad shoulders, forward skis, twin turbine housings | 108 km/h | Heavy and stable |
| Shrike | Silver/orange split beak and overlapping swept feather fins | 122 km/h | Quick turn-in |
| Mantis | Olive utility shoulders, twin fork runners, upright stabilizers | 111 km/h | High grip |
| Aurora | Midnight-blue low delta wings, copper seams and blue running lights | 126 km/h | Fast, more lateral slip |

## Production and provenance

tools/build_fleet.py builds four original Blender GLBs in game/assets/fleet. User-supplied reference images guide silhouette and palette; no image or third-party mesh bytes are bundled. Original generated geometry/source is CC0-1.0. This uses the existing free Blender 4.5.3 / Godot 4.5.1 GitHub pipeline, no paid provider. Kestrel remains in the original Foundry GLB.

Each new craft has a recessed open cockpit, seat, frame, windshield, instrument/yoke compatibility, four pod housings and five animated tail assemblies. Geometry policy: below 40,000 triangles per new craft, COLOR_0 shading attributes, required named control/nozzle rig nodes. Material batches group static parts. No pilot character mesh is included.

The production script authors +Z-forward, +Y-up Godot metres and converts into Blender coordinates for export. The four new hulls are separately authored profiles and silhouette parts, not transformed Kestrel meshes.

## Runtime and validation

fleet_catalog.gd stores identity, appearance and modest handling differences. The existing boost, reverse, wall rebound and jump-assist systems are shared. Lap records are stored by circuit and chassis; existing Kestrel track records migrate through a fallback.

fleet_test.gd drives all 15 chassis/circuit combinations through a full lap and landing, checks rigs, component mounts, live display identity and cockpit camera placement, and exercises actual hangar selection. CI renders Fleet-kestrel.png, Fleet-piledriver.png, Fleet-shrike.png, Fleet-mantis.png and Fleet-aurora.png, and publishes fleet-report.json alongside the signed APK.

Local controller checks may use geometry fixtures; Blender output inspection and production GLB/Godot captures occur in CI. Screenshot FPS from software rendering is not Android performance telemetry.
