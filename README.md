# SceneForge
Android scenery laboratory. First planned environment: Neon Foundry.

## Download
Open [latest pipeline build](https://github.com/tpylman90-ctrl/SceneForge/releases/tag/pipeline-latest) and download **SceneForge.apk** directly. Successful main builds update this prerelease; failed builds leave the last working download intact. Run-specific APKs and logs are also available in Actions for 30 days.

## Pipeline
Godot 4.5.1 stable, Java 17, Android build tools 35.0.0. Push to main or run Android pipeline manually. Pull requests validate and export without publishing.

The initial app is a pipeline check screen, not the Neon Foundry environment. Android hardware testing remains necessary.

## Signing
Main builds produce SceneForge.apk with permanent release signing, package com.sceneforge.lab. The separate SceneForge-debug.apk uses com.sceneforge.lab.debug. Both apps can coexist. Release builds require ANDROID_KEYSTORE_BASE64, ANDROID_KEYSTORE_PASSWORD, ANDROID_KEY_ALIAS, and ANDROID_KEY_PASSWORD repository secrets. Store and key passwords must match for Godot. Every release verifies its APK signature against the configured keystore certificate before publication. Private keys are decoded only in runner temporary storage and removed after export; no keystore is uploaded. Keep the original key backup for future updates. Pull requests never receive release credentials.

## Layout
- game/: Godot runtime and GLB assets
- art/: Blender source workflow
- tools/: repeatable asset scripts
- .github/workflows/: builds and downloads

Keep source .blend files outside game/. Export GLB in meters, apply transforms, use named materials, and keep collision separate. Exported runtime assets are checked in; the APK build does not require Blender.
