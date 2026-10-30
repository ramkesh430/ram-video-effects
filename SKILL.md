---
name: ram-video-effects
description: Add talking-head video effects (62 effects - word behind head, orbit, spotlight, receipts, glass widgets, tier list, captions, confetti and more) to a video. Use when the user says /effects or asks to add an effect to their video.
---

# Ram's Video Effects (fxkit)

The user gives a video (vertical talking-head works best) and asks for effects in plain words, e.g.
"orbit from 3 to 6 seconds", "spotlight when I say 'lights off'", "backdrop-word RAM for the first 2s".
Reply in the user's language (often Nepali in Roman script).

The engine is `fx.py` in this skill's folder. It accepts a video OR a photo (a photo becomes a slow-zoom vertical clip automatically). Run `python fx.py --list` to see every effect with its params.

## Effects
- noise: Reels/screenshots pile up behind your head
- lineup: Numbered tiles fan out above your head
- locked-on: Brackets lock onto your face and the camera follows you
- backdrop-word: Giant word drops in BEHIND your head (style: display|serif|serif-italic)
- spotlight: Kill the lights, keep you lit (optional glowing word behind you)
- the-bill: Your instructions print out like a receipt
- moody: Moody colour grade (optional serif word behind you)
- swipe: Before/after slider wipes across (before: bw|dark|blur|raw)
- todo: Notes checklist beside your head that ticks off as you talk
- comment-box (alias: comment): A comment types itself, then posts
- tap: A Follow button gets tapped and flips to Following
- pause-point: Freeze frame with PAUSED chip and hand-drawn arrows + labels
- uninstall: App tiles with minus badges, a glitchy uninstall bar breaks the frame
- reel-frame: Your video shrinks into a film-strip reel card
- shortcut-rain: Keyboard keys rain down behind you
- reject-stamp (alias: stamp): A big red stamp slams down (with camera shake)
- countdown: 3-2-1 flip tiles above your head
- countdown-flip: Flip-clock counter rolls from one value to another (e.g. 43:00 -> 4:22)
- rabbit-hole: The room tunnels away behind you (nested frames)
- cover-star: You become a magazine cover (look: classic|editorial)
- scribble: Marker circle draws itself around you + arrow and a word (B&W frame)
- glass-widgets: Frosted glass widgets (stat, chart, progress) float around your head
- red-collage: Black & white you, a giant red word behind, three lines slam in
- split-headline: Headline card slides down and pushes you to the bottom half. [word] = highlight; | = new line
- pastel-word: Lavender room, a giant word behind you, a profile card gets followed
- check-pills: Grid-paper room, your reels pinned behind you, blue pills get clicked
- timeline: Dark red film look with an editing timeline and a glowing playhead
- headline: White headline card slides down at the top (goes behind your head if needed). | = 2nd line
- headline-box: A punch-in with a clean two-line headline (black text on white boxes)
- profile-wall: Your reels grid fills the wall while a follower counter ticks up
- tier-list: A tier list drops in and your pick flies into S tier
- broll-split: B-roll (image or video) on top, you below, with a price-tag sticker
- phone-fan: Your reels fan out like a hand of phones
- dot-reveal: Your shot builds out of glowing dots, then snaps into focus
- headline-wall: Your headlines pile up behind your head, then a total pops in front
- checklist: Task list card under your chin, each step ticks green (style: dark|light)
- name-tag: Lower-third with your name and title
- lean-in (alias: punch-in): A quick punch-in zoom on one word
- slow-push: Slow cinematic push-in while the room melts out of focus
- orbit: Your reels (or text chips) circle your head - behind at the top, below the chin in front
- carousel-spin: Your reels spin around you in a 3D carousel
- liquid-glass-graph: Liquid glass card with a climbing graph and a counting number (look=bento for a glass dashboard)
- match-cut: News pages cut on one word, locked in place behind your head
- apple-toggles (alias: toggles): Switches flip on under your chin, one line at a time
- led-sign: The lights drop and a glowing LED sign types itself out behind you
- over-the-shoulder-zoom: Pushes into one corner, a glass graph pops beside your head, then the other corner with a 2nd graph
- messages: Message notifications pop in one after another with a soft glow
- place-in-grid: You shrink into the centre of your 3x3 profile grid; reels pop in around you with view counts
- countup: Big number counts up under your chin (e.g. followers, money)
- glitter-spotlight: Spotlight with golden rays and sparkles behind you
- confetti: Confetti burst falls over the frame
- glitch: Digital glitch hit (RGB split + slice shifts)
- vhs: VHS tape look: scanlines, noise, colour bleed, date stamp
- captions: Bold word-by-word captions (give 'words':[[word,start,end],...] from whisper, or 'text' to spread evenly)
- progress-bar: Thin progress bar along the top that fills over the effect duration
- poll: A two-option poll card; votes animate in
- whip-zoom: Fast zoom-blur transition (put it on a cut, ~0.4s)
- neon-outline: A glowing neon outline traces around you
- heart-burst: Hearts float up from the bottom corner (like a live stream)
- sticker: A bold tilted text sticker pops on (e.g. 'NEW!', 'PART 2')
- freeze-bw: Freeze frame turns black & white with a big label (record-scratch moment)
- split-screen: Two of you side by side (wide + close-up)

Anything that would cover the face goes behind the head automatically (person cut-out).
Effects without the user's own screenshots use colourful placeholder cards - ask for a folder of screenshots
(`"images": "path/to/folder"`) for noise, orbit, carousel-spin, phone-fan, profile-wall, place-in-grid, check-pills.
Charts, counters and headlines should use the user's real numbers and words - ask if missing.

## Steps
1. **Setup (once).** Copy `fx.py` from this skill folder to `~/.cache/fxkit/fx.py`.
   - `pip install numpy opencv-python pillow mediapipe` (add `--break-system-packages` if pip refuses). Make sure `ffmpeg`/`ffprobe` exist.
   - Models into `~/.cache/fxkit/`:
     - https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite
     - https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite
     - If blocked: `pip download mediapipe==0.10.14 --no-deps --only-binary=:all: --python-version 3.12 --platform manylinux_2_17_x86_64` and unzip `mediapipe/modules/selfie_segmentation/selfie_segmentation.tflite` + `mediapipe/modules/face_detection/face_detection_short_range.tflite` into `~/.cache/fxkit/`.
   - Optional fonts in `~/.cache/fxkit/fonts/` (Google Fonts, OFL): Anton, Archivo Black, Inter, Instrument Serif, Space Mono, Permanent Marker. Falls back to system fonts.
2. **Timing by words.** For "when I say X": `pip install faster-whisper`, `WhisperModel("small").transcribe(path, word_timestamps=True)`, use that word's start. Word-triggered effects usually last 1.5-3 s. The same word list feeds the `captions` effect (`"words": [[w,start,end],...]`).
3. **Plan** `plan.json` next to the video: `[{"fx":"orbit","start":3,"end":6}, {"fx":"reject-stamp","start":7,"end":8.5,"text":"NO"}]`. Effects can stack/overlap.
4. **Preview first:** `python ~/.cache/fxkit/fx.py VIDEO.mp4 /tmp/fxprev.png --plan plan.json --preview t1,t2 --debug` (one time inside each effect). Look at the PNGs (green = face, magenta = person). Fix anything covering the face, then preview again.
5. **Render:** `python ~/.cache/fxkit/fx.py VIDEO.mp4 VIDEO_effects.mp4 --plan plan.json` (`--max-short 2160` for 4K). Original audio is kept.
6. Tell the user what was added and when; offer tweaks ("too fast", "covers my face" -> adjust and re-render).

## More: Vox-style explainers and voiced videos
For "Vox style", explainer/documentary looks, or a finished video with an AI voice-over from a prompt, use the pack in
`vox/` of github.com/ramkesh430/ram-video-effects (skill `ram-vox-effects`): 22 Vox effects + `make_video.py`
(script -> voice + paper background + effects, 9:16 or 16:9). All 62 effects here also work inside Vox plans.

Notes: draft quality, the user approves before posting. No music or sound effects are added.
