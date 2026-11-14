# SceneForge
Godot 4.5.1 / Vulkan Mobile hover-racing and scenery testbed for Neon Foundry. The repository contains the playable SceneForge prototype, reproducible vehicle/terrain tools and a **separate native Android GLB Inspector**. It is not the fresh Neon Foundry Racing production repository or Model Forge editor.

## Download
Open [latest pipeline build](https://github.com/tpylman90-ctrl/SceneForge/releases/tag/pipeline-latest) and download **SceneForge.apk** directly. Successful main builds update this prerelease; failed builds leave the last working download intact. Run-specific APKs and logs are also available in Actions for 30 days.

## Pipeline
Godot 4.5.1 stable, Java 17, Android build tools 35.0.0. Push to main or run Android pipeline manually. Pull requests validate and export without publishing.

### Standard graphics backend: Vulkan
All SceneForge **game** tracks (Neon Cross, Skyway, Viper Rift, Iron Harbor, Crimson Serpent, Red Mesa, Devil's Gate and Skyfall), racing craft, Foundry and Fleet use Godot **Mobile/Vulkan** on Android. The Godot game project explicitly selects Mobile and Vulkan for Android and Linux. It does not silently fall back to OpenGL. Vulkan-capable Android hardware is required for this distribution. Godot's Mobile renderer is deliberately preferred to Forward+ to preserve phone performance.

Screenshot CI and vehicle-viewer previews now explicitly use Mobile/Vulkan too. CI runs on Mesa Lavapipe software Vulkan under Xvfb, so its *performance numbers are not representative of phone GPU frame rates*; only native phone tests establish FPS. The separate Terrain3D **desktop authoring editor** uses Forward+/Vulkan. Native Android GLB Inspector and Blender are not Godot runtime renderers and are unchanged.

The Vulkan configuration and preview invocation rules are verified by `tools/verify_vulkan_pipeline.py` during Android CI. If a device doesn't support Vulkan, restore a separate legacy build from Git history instead of silently changing this build's backend.

SceneForge is an evolving gameplay/visual testbed; the committed Godot project, not older planning notes, defines current playable behavior. Android hardware validation remains necessary.

## Signing
Main builds produce SceneForge.apk with permanent release signing, package com.sceneforge.lab. The separate SceneForge-debug.apk uses com.sceneforge.lab.debug. Both apps can coexist. Release builds require ANDROID_KEYSTORE_BASE64, ANDROID_KEYSTORE_PASSWORD, ANDROID_KEY_ALIAS, and ANDROID_KEY_PASSWORD repository secrets. Store and key passwords must match for Godot. Every release verifies its APK signature against the configured keystore certificate before publication. Private keys are decoded only in runner temporary storage and removed after export; no keystore is uploaded. Keep the original key backup for future updates. Pull requests never receive release credentials.

## Repository layout and workflow ownership
- `game/`: Godot runtime, 8 registered circuits, 10 registered craft, tests and authored terrain source
- `showroom_sources/`: original supplied Shrike/Kestrel GLBs; **preserve these**
- `tools/`: Blender vehicle and environment generators, validators and selective captures
- `tools/glb-inspector-android/`: independent native Android inspector; not part of the Godot APK
- `tools/serpent_terrain_editor/`: optional standalone desktop Terrain3D authoring project
- `art/` and `docs/`: asset guidance, reports and historical design briefs
- `.github/workflows/`: independently scoped game APK, inspector APK/smoke, preview and experiments

See [repository maintenance guide](docs/REPOSITORY_GUIDE.md) for what is active, generated, safe to clean and deliberately retained.

Keep source .blend files outside game/. Export GLB in meters, apply transforms, use named materials, and keep collision separate. Runtime GLBs generated for CI are **not** checked in; CI rebuilds/restores those assets before Godot import. The uploaded original GLBs under `showroom_sources/` are intentionally tracked and never treated as disposable outputs.
