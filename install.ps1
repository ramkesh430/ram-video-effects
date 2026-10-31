# Ram's Video Effects - installer for Windows (PowerShell)
#   powershell -ExecutionPolicy Bypass -File install.ps1                  # Ram's 62 effects
#   powershell -ExecutionPolicy Bypass -File install.ps1 -WithOriginal    # + Vibha Ramprakash's original skill
param([switch]$WithOriginal)
$ErrorActionPreference = "Continue"
$Here  = Split-Path -Parent $MyInvocation.MyCommand.Path
$Cache = Join-Path $HOME ".cache\fxkit"
$Skill = Join-Path $HOME ".claude\skills\ram-video-effects"
New-Item -ItemType Directory -Force -Path (Join-Path $Cache "fonts"), $Skill | Out-Null

Write-Host "==> Python packages"
python -m pip install -q -r (Join-Path $Here "requirements.txt")
python -m pip install -q edge-tts   # AI voice for make_video.py

Write-Host "==> ffmpeg"
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
  if (Get-Command winget -ErrorAction SilentlyContinue) { winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements }
  else { Write-Host "   Please install ffmpeg: https://ffmpeg.org/download.html" }
}

Write-Host "==> AI models"
$MP = "https://storage.googleapis.com/mediapipe-models"
$models = @{
  "selfie_segmenter.tflite"       = "$MP/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite";
  "blaze_face_short_range.tflite" = "$MP/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite"
}
foreach ($k in $models.Keys) {
  $dst = Join-Path $Cache $k
  if (-not (Test-Path $dst)) { try { Invoke-WebRequest -Uri $models[$k] -OutFile $dst -UseBasicParsing } catch { Write-Host "   could not download $k" } }
}

Write-Host "==> Fonts (optional)"
$GF = "https://github.com/google/fonts/raw/main"
foreach ($f in @("ofl/anton/Anton-Regular.ttf","ofl/archivoblack/ArchivoBlack-Regular.ttf","ofl/instrumentserif/InstrumentSerif-Regular.ttf",
                 "ofl/instrumentserif/InstrumentSerif-Italic.ttf","ofl/spacemono/SpaceMono-Bold.ttf","apache/permanentmarker/PermanentMarker-Regular.ttf")) {
  $dst = Join-Path $Cache ("fonts\" + (Split-Path $f -Leaf))
  if (-not (Test-Path $dst)) { try { Invoke-WebRequest -Uri "$GF/$f" -OutFile $dst -UseBasicParsing } catch {} }
}

Write-Host "==> Engine + Claude skill"
$V = Join-Path $Here "vox"
$Eng = @((Join-Path $Here "fx.py"), (Join-Path $V "vox.py"), (Join-Path $V "make_video.py"), (Join-Path $V "prompt_to_script.py"))
Copy-Item $Eng $Cache -Force
Copy-Item ($Eng + @((Join-Path $Here "SKILL.md"), (Join-Path $Here "EFFECTS.md"))) $Skill -Force
New-Item -ItemType Directory -Force -Path (Join-Path $Skill "scripts") | Out-Null
Copy-Item (Join-Path $V "scripts\*.json") (Join-Path $Skill "scripts") -Force

if ($WithOriginal) {
  Write-Host "==> Original skill (github.com/Vibha-Ramprakash/claude-video-effects)"
  $Orig = Join-Path $HOME ".claude\skills\effects"
  if (Test-Path (Join-Path $Orig ".git")) { git -C $Orig pull -q } else { git clone -q https://github.com/Vibha-Ramprakash/claude-video-effects $Orig }
}

python (Join-Path $Cache "vox.py") --list | Select-Object -First 1 | Out-Null
Write-Host "Done. Restart Claude Code, drop in a video and ask for an effect."
