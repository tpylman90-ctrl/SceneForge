#!/usr/bin/env bash
# Fleet correctness is always checked by Godot tests. This runs only the
# expensive screenshots requested by change impact analysis or manual scope.
set -euo pipefail
export VK_ICD_FILENAMES="${VK_ICD_FILENAMES:-/usr/share/vulkan/icd.d/lvp_icd.x86_64.json}"
mkdir -p build

capture_fleet() {
  local log="$1"; shift
  timeout 120 xvfb-run -a godot --audio-driver Dummy --path game --rendering-method mobile --rendering-driver vulkan --resolution 1280x720 "$@" 2>&1 | tee "build/$log.log"
  if grep -E 'SCRIPT ERROR:|ERROR:' "build/$log.log"; then exit 1; fi
}

names=(kestrel piledriver shrike mantis aurora forge synapse tremor aerolith solstice)
for craft in ${CAPTURE_FLEET:-}; do
  name="${names[$craft]}"
  capture_fleet "fleet-$craft-render" res://fleet_hangar.tscn -- --capture --craft-"$craft"
  test -s "build/Fleet-$name.png"
  case "$craft" in
    1)
      capture_fleet "foundry-pyldriver-render" -- --capture --craft-1
      capture_fleet "foundry-pyldriver-seat-render" -- --capture --craft-1 --seat-view
      test -s build/Foundry-piledriver.png
      test -s build/Foundry-piledriver-seat.png
      for view in tail side top cockpit under; do
        capture_fleet "fleet-pyldriver-$view-render" res://fleet_hangar.tscn -- --capture --craft-1 --fleet-"$view"
        test -s "build/Fleet-piledriver-$view.png"
      done
      ;;
    2)
      capture_fleet "foundry-shrike-render" -- --capture --craft-2
      test -s build/Foundry-shrike.png
      grep -q SCENEFORGE_SHRIKE_UPLOADED_SHOWROOM_OK build/foundry-shrike-render.log
      capture_fleet "fleet-shrike-uploaded-render" res://fleet_hangar.tscn -- --capture --craft-2 --fleet-hero --fleet-clean
      test -s build/Fleet-shrike-hero-clean.png
      grep -q SCENEFORGE_SHRIKE_UPLOADED_SHOWROOM_OK build/fleet-shrike-uploaded-render.log
      capture_fleet "fleet-shrike-cockpit-render" res://fleet_hangar.tscn -- --capture --craft-2 --fleet-cockpit
      capture_fleet "foundry-shrike-seat-render" -- --capture --craft-2 --seat-view
      test -s build/Fleet-shrike-cockpit.png
      test -s build/Foundry-shrike-seat.png
      grep -q SCENEFORGE_SHRIKE_WINDSCREEN_SEPARATED build/fleet-shrike-cockpit-render.log
      capture_fleet "drive-2-render" res://city_loop.tscn -- --capture --craft-2 --track-action
      test -s build/NeonLoop-shrike-driving.png
      grep -q SCENEFORGE_SHRIKE_UPLOADED_SHOWROOM_OK build/drive-2-render.log
      ;;
    5)
      for view in nose side top cockpit; do
        capture_fleet "fleet-forge-$view-render" res://fleet_hangar.tscn -- --capture --craft-5 --fleet-"$view"
        test -s "build/Fleet-forge-$view.png"
      done
      ;;
    6)
      for view in front rear side top under zoomed-rear; do
        capture_fleet "fleet-synapse-$view-render" res://fleet_hangar.tscn -- --capture --craft-6 --fleet-"$view"
        test -s "build/Fleet-synapse-$view.png"
      done
      ;;
    7)
      capture_fleet "foundry-tremor-render" -- --capture --craft-7
      test -s build/Foundry-tremor.png
      capture_fleet "fleet-tremor-hero-render" res://fleet_hangar.tscn -- --capture --craft-7 --fleet-hero --fleet-clean
      capture_fleet "fleet-tremor-rear-render" res://fleet_hangar.tscn -- --capture --craft-7 --fleet-rear-quarter --fleet-clean
      test -s build/Fleet-tremor-hero-clean.png
      test -s build/Fleet-tremor-rear-quarter-clean.png
      ;;
    8)
      capture_fleet "foundry-aerolith-render" -- --capture --craft-8
      test -s build/Foundry-aerolith.png
      grep -q SCENEFORGE_AEROLITH_DRIVE_MODEL_OK build/foundry-aerolith-render.log
      capture_fleet "fleet-aerolith-render" res://fleet_hangar.tscn -- --capture --craft-8 --fleet-hero --fleet-clean
      test -s build/Fleet-aerolith-hero-clean.png
      grep -q SCENEFORGE_AEROLITH_DRIVE_MODEL_OK build/fleet-aerolith-render.log
      capture_fleet "drive-8-render" res://city_loop.tscn -- --capture --craft-8 --track-action
      test -s build/NeonLoop-aerolith-driving.png
      grep -q SCENEFORGE_AEROLITH_DRIVE_MODEL_OK build/drive-8-render.log
      ;;
    9)
      capture_fleet "fleet-solstice-hero-render" res://fleet_hangar.tscn -- --capture --craft-9 --fleet-hero --fleet-clean
      capture_fleet "fleet-solstice-rear-render" res://fleet_hangar.tscn -- --capture --craft-9 --fleet-zoomed-rear --fleet-clean
      capture_fleet "fleet-solstice-seat-render" res://fleet_hangar.tscn -- --capture --craft-9 --fleet-cockpit
      test -s build/Fleet-solstice-hero-clean.png
      test -s build/Fleet-solstice-zoomed-rear-clean.png
      test -s build/Fleet-solstice-cockpit.png
      grep -q SCENEFORGE_SOLSTICE_PLAYABLE_BODY_OK build/fleet-solstice-rear-render.log
      capture_fleet "solstice-driving-render" res://city_loop.tscn -- --capture --craft-9 --track-action
      # city_loop currently uses NeonLoop-action.png for non-Shrike/AEROLITH
      # race screenshots. Retain that source behavior and give this selected
      # craft's review artifact its own permanent name.
      test -s build/NeonLoop-action.png
      cp build/NeonLoop-action.png build/NeonLoop-solstice-driving.png
      test -s build/NeonLoop-solstice-driving.png
      grep -q SCENEFORGE_SOLSTICE_PLAYABLE_BODY_OK build/solstice-driving-render.log
      ;;
  esac
done
