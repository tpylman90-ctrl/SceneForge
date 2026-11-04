# SceneForge selective Android captures

The Android workflow always builds both Android APKs, verifies signing,
runs the Godot runtime import/smoke checks, exercises all circuits, and runs
the fleet/foundry/racing/regression suites.

Screenshot generation is separately selected by tools/ci_capture_plan.py:

- **auto** (default): no screenshots for documentation or CI-only changes;
  changes to game/tracks/ render Crimson Divide tracks 4-6, without rendering
  any approved fleet craft. A city_loop.gd change renders all seven tracks.
  Vehicle-specific changes render that craft only (e.g., Shrike #2 or
  Tremor #7). Shared fleet renderer/catalog/Blender changes render all craft.
  The Foundry itself is captured only for foundry-wide changes.
- **active**: manual review of current active craft (Shrike #2, Tremor #7)
  and Crimson Divide circuits 4-6.
- **full**: manual complete fleet / Foundry / seven-track screenshot regression.
- **none**: manual test and APK build with screenshots explicitly disabled.

Use **Actions > Android pipeline > Run workflow > capture_scope** to select.
The default "auto" scope uses git diff (entire push or PR) against the prior
revision, so an unrelated scenery change cannot force screenshots of all nine
craft. Each job writes the chosen capture scope to the GitHub step summary and
build/capture-plan.txt.

After the screenshot pass, CI publishes only the files generated on that run
to pipeline-latest, plus the permanently signed APK and checksum. Older approved
screenshots already on pipeline-latest may remain available, but the artifact
ZIP for a specific run contains only screenshots produced in that run.

Adjust ACTIVE_CRAFT in tools/ci_capture_plan.py when our active model work changes.
The lightweight per-craft unit and integration suites are intentionally
unconditional: suppressing captures does *not* suppress fleet correctness tests.

Notes: speedup is expected, not benchmarked until a successful selective
pipeline run. Significant source/layout changes may legitimately request a full
fleet capture. For exact reproducibility, use a GitHub Actions run artifact
rather than old persistent gallery images.
