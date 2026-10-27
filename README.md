# SceneForge
Android scenery laboratory. First planned environment: Neon Foundry.

## Download
Open [latest pipeline build](https://github.com/tpylman90-ctrl/SceneForge/releases/tag/pipeline-latest) and download **SceneForge-debug.apk** directly. Successful main builds update this prerelease; failed builds leave the last working download intact. Run-specific APKs and logs are also available in Actions for 30 days.

## Pipeline
Godot 4.5.1 stable, Java 17, Android build tools 35.0.0. Push to main or run Android pipeline manually. Pull requests validate and export without publishing.

The initial app is a pipeline check screen, not the Neon Foundry environment. Android hardware testing remains necessary.

## Signing
These are temporary debug-signed builds, package com.sceneforge.lab.debug. The debug key is cached, not a permanent release identity: cache loss can require uninstalling an earlier debug build. Release signing and a separate production package will be configured next. Never commit private release keystores or passwords.

## Layout
- game/: Godot runtime and GLB assets
- art/: Blender source workflow
- tools/: repeatable asset scripts
- .github/workflows/: builds and downloads

Keep source .blend files outside game/. Export GLB in meters, apply transforms, use named materials, and keep collision separate. Exported runtime assets are checked in; the APK build does not require Blender.
