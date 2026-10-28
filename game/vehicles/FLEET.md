# SceneForge fleet

Five selectable, driveable craft. Open FLEET from the Foundry or driving view. Choose a craft, orbit it by dragging, use FRONT / TAIL / COCKPIT, then DRIVE. Track choice is retained. Only the selected craft is instantiated during play.

| Craft | Silhouette | Cruise | Handling |
|---|---|---|---|
| Kestrel | Slate/orange raptor; refreshed vents, pod hydraulics, heat shields and rear bracing | 115 km/h | Balanced |
| Pyldriver | Purple/brass cage, broad shoulders, forward skis, twin turbine housings | 108 km/h | Heavy and stable |
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

## Pyldriver hero pass

Display spelling is PYLDRIVER (Pylman + driver). The stable internal ID and filenames remain piledriver to preserve existing selections and lap records.

tools/piledriver_detail.py authors the dedicated sculpted hull, lower swept frame and wind deflector, integrated hover fairings, suspended runners, hollow turbine bells with stators, plum lacquer/carbon/brass finish textures, body-following seams, shoulder vents, fasteners, livery and seat details. Existing handling and cockpit camera placement remain. The five tail rigs retain their names; exhaust attachment points match the revised nozzle layout.

CI captures front, tail, side, top and cockpit views. All geometry remains subject to the 40,000-triangle budget and named-rig/vertex-color checks.

## Pyldriver cockpit and underside mount correction

Pyldriver now builds its instruments in native craft coordinates through pyldriver_cockpit.gd. The display sits on a supported binnacle inside the cockpit (center approximately y=1.45, z=0.98 m), and the driver's eye sits back at z=-0.22 m. It no longer inherits the Kestrel-specific instrument transform.

All four hover units are recessed beneath the belly at x=±0.48 m, with front z=1.95 m and rear z=-1.25 m. Chassis markers and ground footprints use those same positions, including the existing hull rake. Tail exhaust origins also follow the raked nozzle geometry. CI includes an underside inspection capture and assertions for instrument and mount placement.
