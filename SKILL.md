---
name: ram-video-effects
description: All-in-one video kit - 62 talking-head effects (word behind head, orbit, spotlight, glass widgets, tier list, captions, confetti...), 22 Vox-style explainer effects (paper cut-out, newspaper highlights, maps, charts, timelines, quote cards, archive film...) and finished voiced videos from a prompt (AI voice-over in Nepali/English/Hindi, 9:16 or 16:9). Use when the user says /effects, asks to add an effect to a video or photo, asks for Vox style / explainer / documentary editing, or asks to make a video from a topic or prompt.
---

# Ram's Video Effects (fxkit + Vox + voiced videos)

The user gives a video (vertical talking-head works best) and asks for effects in plain words, e.g.
"orbit from 3 to 6 seconds", "spotlight when I say 'lights off'", "backdrop-word RAM for the first 2s".
Reply in the user's language (often Nepali in Roman script).

Everything is in this one skill folder:
- `fx.py` - the engine with the 62 effects. Accepts a video OR a photo (a photo becomes a slow-zoom vertical clip).
- `vox.py` - loads `fx.py` and adds 22 Vox effects; same plan format, so a plan can mix all 84 effects. Use `vox.py` whenever a plan has a Vox effect.
- `make_video.py` - script JSON -> AI voice-over + paper background + effects -> finished video (no footage needed).
- `prompt_to_script.py` - plain prompt -> script JSON, written by Claude through the API (only for the automatic GitHub action).
- `scripts/` - example scripts (promo, explainer, documentary). `EFFECTS.md` - every effect and its options.
Run `python vox.py --list` to see every effect with its params.

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


## Vox effects
LOOK
- paper-room: background becomes textured paper, the person becomes a cut-out with a white sticker border
- paper-grain: warm printed-paper texture + grain + vignette over the whole frame
- archive-film: old footage look - sepia/bw, grain, flicker, scratches, dust, gate weave (`look`: sepia|bw)
- parallax: 2.5D Ken Burns - the person pushes in faster than the background (great on photos)
- block-wipe: yellow + black blocks sweep across - transition, ~0.6 s centred on a cut
TEXT
- torn-headline: torn paper strip with a yellow kicker label and bold headline (`kicker`, `text`, `y`)
- highlight-clip: newspaper clipping slides in, the [phrase] gets a yellow marker (`source`, `headline`, `body`, `date`)
- marker-text: key line on paper strips, [words] get a highlighter swipe, `|` = new line
- context-label: typewriter place/date lower-third (`text`, `sub`)
- quote-card: full-screen paper quote, word by word, [words] highlighted, then `by`
DATA
- vox-bars: horizontal bar chart (`title`, `labels`, `values`, `suffix`, `highlight`, `source`)
- vox-line: line chart that draws itself (`title`, `values`, `labels` first|last, `prefix`, `suffix`)
- big-number: huge number counts up (`value`, `prefix`, `suffix`, `label`)
- vox-timeline: marker steps through years with event labels (`years`, `events`, `active` to pin one)
CUTAWAYS (full screen)
- map-pin: map zooms to a pin + place label (`place`, `sub`, `x`, `y` 0-1 pin position, `image` = real map screenshot)
- doc-reveal: document with camera push and red circle (`image` = screenshot, `circle` [x,y,w,h] 0-1 of the page, `note`)
- photo-drop: taped sepia archive photos drop behind the person (`images` folder, `captions`)
- redact: document with black redaction bars + stamp (`lines` = which text lines, `stamp`, `image`)
- compare-split: full-screen A vs B, numbers count up (`left`, `right`, `left_value`, `right_value`, `prefix`, `note`)
POINTERS
- arrow-callout: hand-drawn arrow draws to a point (`x`,`y` target 0-1, `from_x`,`from_y` label position, `text`)
- icon-array: grid of people icons, `highlight` of `total` turn yellow (`label`) - "1 in 4 ..."
- source-tag: small "Source: ..." chip in the corner - put one on every fact/chart

`[brackets]` = highlighted words in highlight-clip, marker-text and quote-card.
Use the user's REAL facts, numbers, sources and quotes - ask if missing; never invent statistics or quotes.
The built-in map is a stylised placeholder, not a real map: for a real place ask for a map screenshot (`image`) and set `x`,`y` to the pin.

## A good Vox sequence (adapt to the video)
1. Intro 0-4 s: `paper-room` + `torn-headline` + `context-label`
2. `block-wipe` on each section change
3. Facts: `big-number` / `vox-bars` / `vox-line` / `icon-array` / `compare-split` + `source-tag`
4. Places: `map-pin`; history: `archive-film` + `photo-drop` or `vox-timeline`
5. Evidence: `highlight-clip`, `doc-reveal` or `redact`; voices: `quote-card`; point at things with `arrow-callout`
6. Ending: `marker-text` with the main point; add `captions` from fx if wanted
Keep each card 2.5-4 s; leave gaps where the face is clean.

## Vox steps
1. **Setup:** same as above (packages, models, fonts), plus `vox.py`, `make_video.py` next to `fx.py` in `~/.cache/fxkit/`.
   Without the cut-out model, paper-room covers the whole frame and photo-drop sits in front - get the model.
2. **Timing by words.** For "when I say X": `faster-whisper` with `word_timestamps=True`, use that word's start.
3. **Plan** `plan.json`: `[{"fx":"paper-room","start":0,"end":4}, {"fx":"map-pin","start":8,"end":11,"place":"POKHARA"}]`. Effects stack.
4. **Preview:** `python ~/.cache/fxkit/vox.py VIDEO.mp4 /tmp/prev.png --plan plan.json --preview t1,t2 --debug` and look at the PNGs.
   Fix anything covering the face (cards have a `y` param, 0-1 of the height).
5. **Render:** `python ~/.cache/fxkit/vox.py VIDEO.mp4 VIDEO_vox.mp4 --plan plan.json` (`--max-short 2160` for 4K). Audio kept.
6. Tell the user what was added and when; offer tweaks.

## Prompt -> finished video (voice + effects)
When the user just describes a video ("60 sec Nepali promo for my agency", "5 min documentary on X"), build it end to end:
1. Write a script JSON like `scripts/ram_digital_promo.json` in this skill folder: `voice` (ne-NP-SagarNeural / ne-NP-HemkalaNeural / en-US-GuyNeural ...),
   `size` ([1080,1920] reel or [1920,1080] YouTube), `scenes` with `say` (voice text in the user's language, numbers in words)
   and `fx` (Vox effects with `at`/`end` in seconds from the scene start; negative = before the scene ends). On-screen text in short English.
   Use only real facts; add a `source-tag` to every number. No invented stats, clients, testimonials or quotes.
2. Preview: `python ~/.cache/fxkit/make_video.py SCRIPT.json --out /tmp/vid/NAME.mp4 --silent --preview` (add `--size 1920x1080` for landscape) and look at the PNGs.
3. Render: `python ~/.cache/fxkit/make_video.py SCRIPT.json --out NAME.mp4` (always pass `--out`) (needs `pip install edge-tts` + internet for the voice). `--size` and `--name` make other formats.
   Without internet for the voice, push the script to github.com/ramkesh430/ram-video-effects (vox/scripts/) and run the GitHub action "Make Vox video" (format: both = 9:16 + 16:9).
4. Fully automatic on GitHub: action "Prompt to video" takes a plain prompt, Claude writes the script (secret ANTHROPIC_API_KEY), then renders.


Notes: draft quality, the user approves before posting. No music or sound effects are added.
