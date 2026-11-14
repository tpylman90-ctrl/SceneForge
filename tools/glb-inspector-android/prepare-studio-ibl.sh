#!/usr/bin/env bash
# Prepare a high dynamic range photographic Filament environment for offline Android use.
#
# CC0 HDR: Studio Small 09 (Sergej Majboroda), https://polyhaven.com/a/studio_small_09
# Filament cmgen: https://github.com/google/filament, Apache-2.0, matched to Android 1.77.3.
# Files are downloaded only by the BUILDER; the installed APK never uses the network.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
destination="$here/app/src/main/assets/studio"
mkdir -p "$destination"
if [ -s "$destination/studio_ibl.ktx" ] && \
   [ -s "$here/app/src/main/assets/materials/selection.filamat" ] && \
   [ -s "$here/app/src/main/assets/materials/zebra.filamat" ]; then
  echo "Preprocessed HDR studio and materials already present"
  exit 0
fi

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

echo "Obtaining reproducible Filament 1.77.3 host cmgen tool..."
curl --fail --location --retry 3 --retry-delay 3 --silent --show-error \
  "https://github.com/google/filament/releases/download/v1.77.3/filament-v1.77.3-linux.tgz" \
  --output "$work/filament.tgz"
echo "6d3391197dcbdec318dd8a7f4e8d6fd0766794231d53c756a1565fd92bba31b2  $work/filament.tgz" | sha256sum --check
mkdir -p "$work/filament"
tar -xzf "$work/filament.tgz" -C "$work/filament"
cmgen="$(find "$work/filament" -type f -name cmgen -print -quit)"
if [ -z "$cmgen" ]; then
  echo "Missing cmgen executable in Filament release" >&2
  exit 1
fi
chmod +x "$cmgen"

echo "Fetching the CC0 source photo studio HDRI..."
curl --fail --location --retry 3 --retry-delay 3 --silent --show-error \
  "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/studio_small_09_1k.hdr" \
  --output "$work/studio_small_09_1k.hdr"
test "$(wc -c < "$work/studio_small_09_1k.hdr")" -gt 100000
head -c 12 "$work/studio_small_09_1k.hdr" | grep -qa "RADIANCE\|RGBE" || {
  echo "Unexpected HDR image signature" >&2; exit 1;
}

echo "Prefiltering realistic HDR softbox reflections and diffuse irradiance..."
mkdir -p "$work/ibl"
"$cmgen" -f ktx -x "$work/ibl" "$work/studio_small_09_1k.hdr"

ibl="$(find "$work/ibl" -type f -name '*_ibl.ktx' -print -quit)"
if [ -z "$ibl" ]; then
  echo "cmgen did not produce a Filament IBL KTX" >&2
  find "$work/ibl" -maxdepth 3 -type f >&2
  exit 1
fi
cp "$ibl" "$destination/studio_ibl.ktx"
test "$(wc -c < "$destination/studio_ibl.ktx")" -gt 30000
echo "Bundled studio environment $(du -h "$destination/studio_ibl.ktx" | awk '{print $1}')"
matc="$(find "$work/filament" -type f -name matc -print -quit)"
if [ -z "$matc" ]; then echo "Missing Filament matc executable" >&2; exit 1; fi
chmod +x "$matc"
mkdir -p "$here/app/src/main/assets/materials"
for name in selection zebra; do
  "$matc" -p mobile -a opengl -a vulkan \
    -o "$here/app/src/main/assets/materials/${name}.filamat" \
    "$here/materials/${name}.mat"
  test -s "$here/app/src/main/assets/materials/${name}.filamat"
done
echo "Bundled genuine GPU selection and zebra-reflection diagnostic materials"
