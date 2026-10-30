---
name: ram-vox-effects
description: Vox-style explainer video editing (22 effects) - paper cut-out look, newspaper clippings with yellow highlighter, maps with pins, paper bar/line charts, big numbers, icon arrays, A-vs-B splits, timelines, quote cards, document reveals and redactions, arrows, source tags, archive film and block-wipe transitions (plus the 62 ram-video-effects). Use when the user asks for "Vox editing", "Vox style", an explainer/documentary look, or any of these effects on a video or photo.
---

# Ram's Vox Effects

The user gives a video (or photo) and asks for a Vox-style edit in plain words, e.g.
"Vox style intro with the headline 'Why rent is so high'", "map of Kathmandu at 8 seconds",
"bar chart of these numbers when I say 'compare'". Reply in the user's language (often Nepali in Roman script).

The engine is `vox.py` in this skill folder. It loads `fx.py` (same folder) and adds 22 Vox effects, so a plan
can mix Vox effects with all 62 fx effects (captions, whip-zoom, glitch ...). Run `python vox.py --list` for every effect and its params.

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

## Steps
1. **Setup (once).** Copy `fx.py` and `vox.py` to `~/.cache/fxkit/`. `pip install numpy opencv-python pillow mediapipe`
   (`--break-system-packages` if needed), ffmpeg/ffprobe on PATH. Models (person cut-out + face) in `~/.cache/fxkit/`:
   - https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite
   - https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite
   Without the cut-out model, paper-room covers the whole frame and photo-drop sits in front - get the model.
   Optional fonts in `~/.cache/fxkit/fonts/`: Archivo Black, Instrument Serif, Space Mono, Permanent Marker (Google Fonts).
2. **Timing by words.** For "when I say X": `faster-whisper` with `word_timestamps=True`, use that word's start.
3. **Plan** `plan.json`: `[{"fx":"paper-room","start":0,"end":4}, {"fx":"map-pin","start":8,"end":11,"place":"POKHARA"}]`. Effects stack.
4. **Preview:** `python ~/.cache/fxkit/vox.py VIDEO.mp4 /tmp/prev.png --plan plan.json --preview t1,t2 --debug` and look at the PNGs.
   Fix anything covering the face (cards have a `y` param, 0-1 of the height).
5. **Render:** `python ~/.cache/fxkit/vox.py VIDEO.mp4 VIDEO_vox.mp4 --plan plan.json` (`--max-short 2160` for 4K). Audio kept.
6. Tell the user what was added and when; offer tweaks.

## Prompt -> finished video (voice + effects)
When the user just describes a video ("60 sec Nepali promo for my agency", "5 min documentary on X"), build it end to end:
1. Write a script JSON like `vox/scripts/ram_digital_promo.json`: `voice` (ne-NP-SagarNeural / ne-NP-HemkalaNeural / en-US-GuyNeural ...),
   `size` ([1080,1920] reel or [1920,1080] YouTube), `scenes` with `say` (voice text in the user's language, numbers in words)
   and `fx` (Vox effects with `at`/`end` in seconds from the scene start; negative = before the scene ends). On-screen text in short English.
   Use only real facts; add a `source-tag` to every number. No invented stats, clients, testimonials or quotes.
2. Preview: `python make_video.py SCRIPT.json --silent --preview` (add `--size 1920x1080` for landscape) and look at the PNGs.
3. Render: `python make_video.py SCRIPT.json` (needs `pip install edge-tts` + internet for the voice). `--size` and `--name` make other formats.
   Without internet for the voice, push the script and run the GitHub action "Make Vox video" (format: both = 9:16 + 16:9).
4. Fully automatic on GitHub: action "Prompt to video" takes a plain prompt, Claude writes the script (secret ANTHROPIC_API_KEY), then renders.

Notes: draft quality - the user approves before posting. No music or sound effects are added.
