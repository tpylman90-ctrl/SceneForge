# SceneForge GLB Inspector — Android (native)
Standalone offline Android GLB inspector for SceneForge and AssetWright.

## Photo reference and AI feedback (v0.6)
- Compare screen: **REF PHOTO** opens a floating native reference window. Tap the photo
  area to select a local image. Drag the header to move, PIN to lock, bottom-right grip
  to resize, expand to enlarge, percentage button to alter opacity, × to hide.
- The reference window remembers its last image, size, position and pin state locally.
- **MARK PANEL** then tap either real GLB model to create a numbered correction marker.
  Select issue type, severity, and describe the intended geometry correction.
- **ISSUES** shows saved annotations for the current GLB hashes and offers restore-view,
  edit and delete. Notes survive app restarts.
- **EXPORT JSON** invokes Android's Save document picker and exports portable
  `sceneforge.model-feedback/v1` JSON, including model SHA-256 and recorded camera pose.
- Screen-space anchors (0..1 within each viewport) are **not** 3D raycast positions;
  the JSON labels them honestly so an AI system can use the saved camera view and PNG.
- The A/B PNG export includes the numbered defect pins currently visible at the
  recorded camera angle.
- Original GLB files and source artwork are never modified by the inspector.

## Studio and two-model comparison
- Studio preview adds a **temporary PBR floor** to a model's in-memory GLB to receive
  real directional shadows. It never changes the saved GLB; toggle STUDIO ON/OFF.
- Native A/B comparison opens **two independent GLB files** in actual 3D using separate
  Filament viewports; synchronized orbit and zoom can be turned off for independent inspection.
- Portrait shows two models stacked; rotate to landscape for two live side-by-side views.
- Orthographic SIDE and other presets for profile/silhouette review.
- A/B PNG capture exports both viewports horizontally as one gallery image.
- Comparison renders at up to ~30 fps to reduce GPU pressure on entry-level Android phones.

## Inspection view modes
- **TEXTURED:** reloads the original GLB, including its authored materials.
- **CLAY:** temporary neutral opaque materials, exposing uninterrupted geometry and silhouette.
- **WIREFRAME:** emits unique indexed triangle edges as true GL_LINES; shared triangle edges are deduplicated.
- Modes are reversible, original GLB bytes are never rewritten on disk. Unsupported compressed/sparse
  topology returns a clear error rather than falsely displaying estimated edges.
- Native device smoke test exercises all three modes using a two-triangle diagnostic GLB.

## Features
- Native Android app, not HTML, WebView, or an image generator
- Opens **actual .glb** files with Android's local document picker, or via Open With
- PBR glTF material decoding through Google Filament, orbit drag, pinch zoom, camera presets
- Counts source triangles, meshes and material definitions from the GLB manifest
- Exports real rendered model-view PNG captures into **Pictures/SceneForge Inspector**
- No network permission and no cloud account
- Debug APK installable on Android 8+; produced by GitHub Actions

## Build
From this directory with JDK 17 and Android SDK platform 35:
```
gradle :app:assembleDebug
```
APK: `app/build/outputs/apk/debug/app-debug.apk`.

Alternatively use the GitHub Actions workflow **SceneForge GLB Inspector APK**.
After run success, download artifact **SceneForge-GLB-Inspector-APK** and unzip APK for installation.

Note: Debug signing is intended for testing and may change between CI runners.
If Android refuses an update due to signature mismatch, uninstall the previous inspector,
then install the new APK. This does not affect SceneForge game installations.

## Known v0.1 boundaries
- .glb only (not .gltf with external textures)
- 80 MB max per file
- Camera presets follow glTF axis convention; source craft orientation may vary
- First pass renders textured/PBR; clay and wireframe are next-pass features
- Polygon count is source geometry count, not per-instance rendered count
