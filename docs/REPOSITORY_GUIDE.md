# SceneForge repository guide — 2026-11-14

## What this repository is

SceneForge is the **Godot/Vulkan Android hover-racing proving ground** used for
driving controls, scenery, vehicle inspection and automated Android validation.
It is not the separate new racing production repository and it is not the
Model Forge Android editor. Preserve the current app identifier and signing
pipeline, regardless of where concepts are later moved.

The source-of-truth roster is `game/vehicles/fleet_catalog.gd` (10 craft).
`game/city_loop.gd` and `game/tracks/` define the eight current circuit IDs
0–7: Neon Cross, Skyway, Viper Rift, Iron Harbor, Crimson Serpent, Red Mesa,
Devil's Gate and Skyfall Run. Historical roadmaps may describe earlier plans.

## Stable source, generated assets and other apps

| Location | Purpose | Cleanup rule |
| --- | --- | --- |
| `game/` | Runtime GDScript/scenes, tests, source heightfield and small authored textures | Keep source files and tests |
| `showroom_sources/` | Uploaded Shrike and Kestrel original + prepared binary inputs | **Never remove as build trash**; preserve provenance |
| `tools/*.py` and `tools/*.sh` | Blender generation, game assets, installs, regression and previews | Keep used scripts; audit before retiring variants |
| `tools/glb-inspector-android/` | Independent native Android GLB inspector | Build in its own workflows; do not move blindly |
| `tools/serpent_terrain_editor/` | Standalone Terrain3D authoring experiment | Keep experiment source; downloaded plugins are local-only |
| `art/`, `docs/`, game Markdown | Design briefs, visual records, workflow notes | Some are historical; do not treat as current runtime authority |
| `build/`, `**/.godot/`, `**/.gradle/`, generated runtime GLBs | Derived local/CI outputs | Ignored; safe to regenerate, not commit |

All app signing material stays in GitHub Secrets or local private storage, not
the repository. The 8.5 MB Shrike input and compact Kestrel original/prepared
binaries are deliberately versioned inputs rather than duplicate APK outputs.

## Independent CI entry points

- **Android pipeline** — game, top-level source scripts, authored showroom
  inputs and its own workflow only. Manual `workflow_dispatch` always works.
  Runs Godot, fleet/track regressions, Vulkan checks, selective captures and
  release-signed game APK.
- **SceneForge GLB Inspector APK** and **GLB Inspector startup smoke** —
  `tools/glb-inspector-android/**` and their own workflows. Neither should
  trigger the game APK when changed alone.
- **Vehicle viewer preview** — only game/asset/vehicle script changes reach the
  push trigger; preview generation still requires `[viewer]` in the commit
  message or an explicit manual run, except for a Shrike uploaded-source change.
- **Original Solstice vehicle study** and **Crimson Serpent Terrain3D Brush
  Trial** — isolated experiment workflows with their own triggers. The terrain
  workflow can push a successful sculpt to main; review its output before
  dispatching it.

`tools/ci_capture_plan.py` controls which renders are generated, **not** which
gameplay regression tests run. To manually build a no-screenshot APK, choose
`capture_scope=none`.

## Unmerged development work (preserved)

As audited on November 14, 2026, these branches diverged from main:

- `experiment/nova-blender-mpfb-v02` — character/MPFB study
- `feature/hover-terrain-air-tracks-20261109` — surface/air track experiments
- `feature/neon-cross-aerial-rebuild-20261109` — skyline course rebuild
- `serpent-rock-density` — canyon geometry experiment

They are **not duplicates of main**. Do not delete them or force-merge without
a comparative review, regression run and Android capture.

## Fast maintenance checks

```bash
python3 -m unittest discover -s tools/tests -p 'test_*.py'
python3 tools/verify_vulkan_pipeline.py
git status --short
git ls-files | grep -E '(\.apk$|\.aab$|\.keystore$|\.jks$)' && echo "Unexpected package or key tracked"
```

After source changes, the authoritative runtime gate is the GitHub Android
workflow followed by installation/inspection on real Vulkan-capable Android
hardware. CPU/Lavapipe previews are not evidence of a device FPS target.

**Cleanup policy:** Do not rewrite Git history, delete active branches,
discard uploaded model originals or move the GLB inspector until its release
and testing workflow have a tested migration path. Prefer CI isolation,
explicit generated-file ignores, corrected documentation and targeted tests.
