# Ram's Vox Effects

22 Vox-style explainer effects for Claude: paper cut-out look, newspaper clippings with a yellow highlighter,
maps with pins, paper charts, big numbers, icon arrays, A-vs-B splits, timelines, quote cards, document reveals, redactions, arrows, archive film and block-wipe transitions.
This folder sits inside ram-video-effects and uses the same engine (`../fx.py`), so all 62 effects work here too.

Made by Ramkesh Gupta (@ramkesh430).

## The 22 effects

| group | effect | what it does |
|---|---|---|
| Look | `paper-room` | background becomes paper, you become a cut-out with a white sticker border |
| | `paper-grain` | warm printed-paper texture, grain and vignette |
| | `archive-film` | old footage: sepia/BW, grain, flicker, scratches, dust |
| | `parallax` | 2.5D Ken Burns, you push in faster than the background |
| | `block-wipe` | yellow + black blocks sweep across (transition) |
| Text | `torn-headline` | torn paper strip with a yellow kicker and a bold headline |
| | `highlight-clip` | newspaper clipping, the `[key phrase]` gets highlighted |
| | `marker-text` | key line on paper strips with a highlighter swipe |
| | `context-label` | typewriter place/date label (`KATHMANDU, 1990`) |
| | `quote-card` | full-screen quote, word by word, with attribution |
| Data | `vox-bars` | bar chart that grows, one bar in yellow |
| | `vox-line` | line chart that draws itself |
| | `big-number` | huge number counts up |
| | `vox-timeline` | marker steps through years with events |
| Cutaways | `map-pin` | map zooms in, a pin drops with the place name |
| | `doc-reveal` | document, camera push, red circle around the key part |
| | `photo-drop` | taped archive photos drop behind you |
| | `redact` | document lines get blacked out, then a stamp |
| | `compare-split` | full-screen A vs B with counting numbers |
| Pointers | `arrow-callout` | hand-drawn arrow to any point with a label |
| | `icon-array` | grid of people, "1 in 4" turn yellow |
| | `source-tag` | small "Source: ..." chip in the corner |

Every option: [EFFECTS.md](EFFECTS.md).

![Vox effects preview](vox_preview.jpg)

## Use it

**In Claude:** drop in your video and type, for example:

```
Vox style intro: headline "Why everyone in Nepal is going abroad", label KATHMANDU, 2026
big-number 3,000,000 "Nepalis work abroad" from 4 to 7 seconds
map-pin on Pokhara when I say "Pokhara"
vox-bars: Nepal 26%, Bangladesh 5%, India 3% - source World Bank
```

**On GitHub (no install):** upload your video into the main `inputs/` folder together with a plan `NAME.json` that uses Vox effects
(copy `vox/example_plan.json`). The usual **Render effects** action renders it into `outputs/NAME_effects.mp4`.

**Install for Claude Code:**

```bash
bash install.sh                                              # Mac / Linux (main installer, includes Vox)
powershell -ExecutionPolicy Bypass -File install.ps1         # Windows
```

**Claude app:** upload the one `ram-video-effects.zip` (repo root) in Settings → Capabilities → Skills - it includes the Vox effects.

**Without Claude:**

```bash
python vox/vox.py --list                                          # every effect
python vox/vox.py in.mp4 check.png --plan plan.json --preview 2,6 # check frames
python vox/vox.py in.mp4 out.mp4 --plan plan.json                 # render
```

```json
[{"fx": "paper-room", "start": 0, "end": 4},
 {"fx": "torn-headline", "start": 0.2, "end": 3.8, "text": "Why rent is so high"},
 {"fx": "block-wipe", "start": 3.7, "end": 4.3},
 {"fx": "vox-line", "start": 4, "end": 8, "title": "Rent in Kathmandu", "values": [8, 10, 13, 18, 25], "prefix": "Rs ", "suffix": "k"}]
```

## Make a full voiced video from a script

`make_video.py` turns a script into a finished explainer: AI voice-over (edge-tts, e.g. Nepali `ne-NP-SagarNeural`),
a moving paper background, Vox effects timed to each line, and block-wipes between scenes.

- **On GitHub:** Actions → **Make Vox video** → Run workflow → script `vox/scripts/digital_marketing_ne.json` (format: as in the script, 9:16, 16:9 or both).
  The video lands in `outputs/digital_marketing_ne.mp4` (and as a download on the run page).
- **Locally:** `pip install edge-tts` then `python vox/make_video.py vox/scripts/digital_marketing_ne.json`
  (`--silent --preview` checks the layout without a voice).
- Copy a script in [scripts/](scripts/) to make your own: each scene has `say` (voice text) and `fx` (effects, `at`/`end` in seconds from the scene start).

## Type a prompt, get a video (fully automatic)

Actions → **Prompt to video** → Run workflow → type what you want, pick the format (9:16, 16:9 or both) and voice.
Claude writes the script, the AI voice is generated, the Vox effects are added, and the video lands in `outputs/`
(plus the script in `vox/scripts/auto/`, so you can edit it and re-render with **Make Vox video**).

One-time setup: **Settings → Secrets and variables → Actions → New repository secret**, name `ANTHROPIC_API_KEY`,
value = your key from console.anthropic.com (API usage is billed by Anthropic). Optional variable `CLAUDE_MODEL` to pick a model.

Example prompts:
- `60 sec Nepali promo for Ram Digital: Google Ads, TikTok Ads, UGC AI video, AI automation. End with "DM us".`
- `3 min Nepali explainer: why small shops in Nepal should use Google Business Profile`

## Honest notes

- Use real numbers, sources and quotes. The effects only draw what you give them.
- The built-in map is a stylised placeholder. For a real place, pass a map screenshot as `image` and set `x`/`y` to the pin.
- `paper-room` and `photo-drop` need the person cut-out model (the installer downloads it).
- Draft edits: watch before you post. No music or sound is added.

## Credits

Person cut-out and face detection: Google MediaPipe (Apache 2.0). Fonts: Google Fonts (OFL / Apache 2.0).
"Vox style" describes a popular explainer look; this pack is not affiliated with Vox Media. Code licence: MIT (see LICENSE).
