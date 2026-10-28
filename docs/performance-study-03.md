# Performance study 03
Scope: game/foundry.gd and CI smoke verification. One candidate configuration; no automatic tuning.
Reference preserves study 02: full resolution, 2x MSAA, four shadow cascades at 24 m.
Balanced: 85% resolution per axis (27.75% fewer 3D pixels), 2x MSAA retained, two shadow cascades at 20 m. Text and touch UI stay at viewport resolution. Materials, normal maps, lighting and reflection probe remain unchanged.
This is a quality/performance tradeoff, not proof of an Android FPS improvement.
The COMPARE FPS button locks the same start viewpoint, discards 90 warmup frames per phase, and collects 240 presentation intervals with a monotonic clock for reference then balanced. It shows mean-derived FPS and p95 frame interval and saves user://performance-comparison.json. It returns to the user's view in Balanced mode.
Phone power and thermal state are uncontrolled; rerun under similar conditions and compare more than once. No GPU timer or energy claim is made. CI runs a shortened software-renderer check to validate the measurement path only, not to predict phone performance.
Target for device review: lower median frame interval while preserving acceptable visual quality. Prior screenshots from differing viewpoints cannot establish a baseline.
