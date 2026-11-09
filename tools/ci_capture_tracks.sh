#!/usr/bin/env bash
# Only preview tracks selected by tools/ci_capture_plan.py.
set -euo pipefail
mkdir -p build

capture_track() {
  local log="$1"; shift
  timeout 120 xvfb-run -a godot --audio-driver Dummy --path game --rendering-method gl_compatibility --resolution 1280x720 res://city_loop.tscn -- --capture "$@" 2>&1 | tee "build/$log.log"
  if grep -E 'SCRIPT ERROR:|ERROR:' "build/$log.log"; then exit 1; fi
}

for circuit in ${CAPTURE_TRACKS:-}; do
  case "$circuit" in
    0) name=NeonLoop; jump=NeonCross ;;
    1) name=Skyway; jump=Skyway ;;
    2) name=ViperRift; jump=ViperRift ;;
    3) name=IronHarbor; jump=IronHarbor ;;
    4) name=CrimsonSerpent; jump=CrimsonSerpent ;;
    5) name=RedMesa; jump=RedMesa ;;
    6) name=DevilsGate; jump=DevilsGate ;;
    *) echo "Unknown circuit $circuit"; exit 1 ;;
  esac
  capture_track "track-$circuit-overview" --track-overview --circuit-"$circuit"
  test -s "build/$name-overview.png"
  capture_track "track-$circuit-cockpit" --track-cockpit --track-action --circuit-"$circuit"
  test -s "build/$name-cockpit.png"
  capture_track "track-$circuit-jump" --track-jump --circuit-"$circuit"
  test -s "build/$jump-jump.png"
  if [[ "$circuit" == 4 ]]; then
    for index in 14 75 155; do
      capture_track "track-$circuit-landmark-$index" --track-landmark-"$index" --circuit-"$circuit"
      test -s "build/CrimsonSerpent-landmark-$index.png"
    done
  fi
done

# Extra legacy views only when the main city course is under inspection.
if [[ " ${CAPTURE_TRACKS:-} " == *" 0 "* ]]; then
  capture_track "loop-track-render" --circuit-0
  test -s build/NeonLoop-track.png
  capture_track "loop-action-render" --track-action --sound-on --circuit-0
  test -s build/NeonLoop-action.png
  capture_track "loop-jump-cockpit-render" --track-jump --track-cockpit --circuit-0
  test -s build/NeonCross-jump-cockpit.png
  capture_track "loop-menu-render" --track-menu
  test -s build/Circuit-select.png
fi
