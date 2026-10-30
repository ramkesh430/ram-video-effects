# Ram's Video Effects

62 effects for talking-head and photo videos. Give Claude a video, type `/effects` and the effect name, and it renders the edit for you.

![All effects](all_effects_sheet.jpg)

## Example

Original photo → [ram_couple_effects.mp4](ram_couple_effects.mp4) (12 s: word behind us, golden spotlight, neon outline, magazine cover, FOREVER collage).

<img src="original_photo.jpg" width="300">

## Install as a Claude skill

1. Put `SKILL.md` and `fx.py` in a folder called `ram-video-effects`.
2. Claude Code: copy the folder to `~/.claude/skills/ram-video-effects`.
   Claude app: zip the folder and upload it in **Settings → Capabilities → Skills**.
3. Drop in a video and ask, e.g. *"orbit from 3 to 6 seconds"* or *"backdrop-word RAM for the first 2 seconds"*.

## Run it yourself

```bash
pip install numpy opencv-python pillow mediapipe   # plus ffmpeg
python fx.py --list                                 # every effect and its options
python fx.py in.mp4 out.mp4 --plan plan.json        # render (audio kept)
python fx.py in.mp4 check.png --plan plan.json --preview 1.5,4 --debug   # preview frames
```

`plan.json` example:

```json
[{"fx": "backdrop-word", "start": 0, "end": 3, "text": "RAM"},
 {"fx": "glitter-spotlight", "start": 3, "end": 5.5},
 {"fx": "red-collage", "start": 10, "end": 12, "word": "FOREVER"}]
```

Models go in `~/.cache/fxkit/` (MediaPipe selfie segmenter + face detector). See `SKILL.md` for links.

## Effects

noise, lineup, locked-on, orbit, lean-in, backdrop-word, spotlight, the-bill, moody, swipe, todo, comment-box, tap, pause-point, uninstall, reel-frame, shortcut-rain, reject-stamp, countdown, countdown-flip, rabbit-hole, cover-star, scribble, glass-widgets, red-collage, split-headline, pastel-word, check-pills, timeline, headline, headline-box, profile-wall, tier-list, broll-split, phone-fan, dot-reveal, headline-wall, checklist, name-tag, slow-push, carousel-spin, liquid-glass-graph, match-cut, apple-toggles, led-sign, over-the-shoulder-zoom, messages, place-in-grid, countup, glitter-spotlight, confetti, glitch, vhs, captions, progress-bar, poll, whip-zoom, neon-outline, heart-burst, sticker, freeze-bw, split-screen.

Effect ideas inspired by [claude-video-effects](https://github.com/Vibha-Ramprakash/claude-video-effects); this code is written from scratch.
