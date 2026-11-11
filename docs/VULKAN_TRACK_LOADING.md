# SceneForge — Vulkan Mobile track loading

The standard Android race renderer is Godot 4.5 **Mobile over Vulkan**. Keep
`game/project.godot` set to `mobile` with the Android `vulkan` driver.
Godot's Compatibility fallback remains enabled for devices that cannot run
Vulkan. At runtime, check `RenderingServer.get_current_rendering_method()`
and `get_current_rendering_driver_name()`; project settings alone do not
prove the driver actually in use.

## Transition contract

The `TrackLoader` CanvasLayer is an autoload that survives scene replacement.
It covers every interactive entry to `res://city_loop.tscn`:

- Foundry workshop → DRIVE
- Fleet hangar → DRIVE
- Race track selector → chosen race scene

The loading sequence is:

1. Show a fullscreen, native Control overlay that consumes touch input.
2. Asynchronously request `res://city_loop.tscn` via ResourceLoader. The bar
   reflects actual threaded resource progress in the 0–70% section.
3. Switch to the loaded PackedScene while the overlay remains visible. Its
   `_ready()` builds the chosen track's procedural road, terrain, objects,
   environment and selected vehicle. This phase currently runs on the main
   thread; the bar *may pause* while it executes.
4. Freeze the scene's physics progression, then let the created scene render
   through several frames behind the opaque overlay. This is a **start-view
   GPU warm-up**, not a bake of the entire environment.
5. Release controls / countdown only after warm-up; hide the overlay.
6. If a request or scene switch fails, show an error and a Foundry return
   action rather than a blank or endlessly spinning screen.

**What it does NOT do:** This implementation does not cache every viewpoint,
turn all procedural tracks into offline GLBs, or guarantee that every material
and texture encountered later in a race has been rendered. Godot's Mobile
renderer can precompile many pipelines as surfaces enter the scene, but
shader/draw compilation later in a level is still possible. Full static track
baking or visible-sector warming would be separate optimizations requiring
Android FPS and memory validation.

## Performance and correctness gates

- Confirm no black frame at Foundry → DRIVE, Fleet → DRIVE, and TRACKS switch.
- Confirm speed, lap timer and 3-2-1 countdown stay frozen behind the screen.
- Confirm the overlay displays the selected track name and the actual renderer.
- Confirm road geometry and texture are visible on Neon Cross; the prior
  invisible-road rendering bug is **not considered fixed by the loader**.
- Test on the Android device at 60 Hz and after a cold launch; note load time,
  average FPS, p95 frame time and peak memory.
- Keep existing CLI direct-scene captures and physics regression tests working
  independently of this UI. The desktop CI headless renderer does not prove
  Vulkan performance on an Android device.

Related Godot 4.5 documentation:
- https://docs.godotengine.org/en/4.5/tutorials/io/background_loading.html
- https://docs.godotengine.org/en/4.5/tutorials/rendering/jitter_stutter.html
