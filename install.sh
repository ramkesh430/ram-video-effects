#!/usr/bin/env bash
# Ram's Video Effects - one-line installer (macOS / Linux)
#   bash install.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CACHE="$HOME/.cache/fxkit"
SKILL="$HOME/.claude/skills/ram-video-effects"
PY="${PYTHON:-python3}"
mkdir -p "$CACHE/fonts" "$SKILL"

echo "==> Python packages"
$PY -m pip install -q -r "$HERE/requirements.txt" 2>/dev/null || \
$PY -m pip install -q --break-system-packages -r "$HERE/requirements.txt"

echo "==> ffmpeg"
if ! command -v ffmpeg >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then brew install ffmpeg
  elif command -v apt-get >/dev/null 2>&1; then sudo apt-get install -y ffmpeg
  else echo "   Please install ffmpeg yourself: https://ffmpeg.org/download.html"; fi
fi

echo "==> AI models (person cut-out + face finder)"
get() { curl -fsSL --retry 2 -o "$2" "$1" 2>/dev/null; }
MP="https://storage.googleapis.com/mediapipe-models"
[ -s "$CACHE/selfie_segmenter.tflite" ] || get "$MP/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite" "$CACHE/selfie_segmenter.tflite"
[ -s "$CACHE/blaze_face_short_range.tflite" ] || get "$MP/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite" "$CACHE/blaze_face_short_range.tflite"
if ! ls "$CACHE"/*selfie*.tflite >/dev/null 2>&1 || ! ls "$CACHE"/*face*.tflite >/dev/null 2>&1; then
  echo "   direct download blocked - extracting models from the mediapipe wheel"
  TMP="$(mktemp -d)"
  $PY -m pip download -q mediapipe==0.10.14 --no-deps --only-binary=:all: --python-version 3.12 \
      --platform manylinux_2_17_x86_64 -d "$TMP" && \
  $PY - "$TMP" "$CACHE" <<'EOF'
import glob, sys, zipfile, os
tmp, cache = sys.argv[1], sys.argv[2]
z = zipfile.ZipFile(glob.glob(os.path.join(tmp, "*.whl"))[0])
for n in ["mediapipe/modules/selfie_segmentation/selfie_segmentation.tflite",
          "mediapipe/modules/face_detection/face_detection_short_range.tflite"]:
    open(os.path.join(cache, os.path.basename(n)), "wb").write(z.read(n))
EOF
  rm -rf "$TMP"
fi
find "$CACHE" -maxdepth 1 -name '*.tflite' -size -1k -delete 2>/dev/null

echo "==> Fonts (optional, Google Fonts / OFL)"
GF="https://github.com/google/fonts/raw/main"
for f in ofl/anton/Anton-Regular.ttf ofl/archivoblack/ArchivoBlack-Regular.ttf \
         ofl/instrumentserif/InstrumentSerif-Regular.ttf ofl/instrumentserif/InstrumentSerif-Italic.ttf \
         ofl/spacemono/SpaceMono-Bold.ttf apache/permanentmarker/PermanentMarker-Regular.ttf; do
  [ -s "$CACHE/fonts/$(basename $f)" ] || get "$GF/$f" "$CACHE/fonts/$(basename $f)" || true
done
find "$CACHE/fonts" -size -1k -delete 2>/dev/null

echo "==> Engine + Claude skill"
cp "$HERE/fx.py" "$CACHE/fx.py"
cp "$HERE/fx.py" "$HERE/SKILL.md" "$SKILL/"

echo "==> Self-test"
echo "   OK: $($PY "$CACHE/fx.py" --list | grep -vc params) effects ready"
ls "$CACHE"/*.tflite 2>/dev/null | sed 's/^/   model: /'
echo "Done. Restart Claude Code, drop in a video and ask for an effect (e.g. 'orbit from 3 to 6 seconds')."
