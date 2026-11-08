# SceneForge GLB Inspector — Android (native)
Standalone offline Android GLB inspector for SceneForge and AssetWright.

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
