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
bash vox/install.sh                                          # Mac / Linux
powershell -ExecutionPolicy Bypass -File vox\install.ps1     # Windows
```

**Claude app:** upload `vox/ram-vox-effects.zip` in Settings → Capabilities → Skills.

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

## Honest notes

- Use real numbers, sources and quotes. The effects only draw what you give them.
- The built-in map is a stylised placeholder. For a real place, pass a map screenshot as `image` and set `x`/`y` to the pin.
- `paper-room` and `photo-drop` need the person cut-out model (the installer downloads it).
- Draft edits: watch before you post. No music or sound is added.

## Credits

Person cut-out and face detection: Google MediaPipe (Apache 2.0). Fonts: Google Fonts (OFL / Apache 2.0).
"Vox style" describes a popular explainer look; this pack is not affiliated with Vox Media. Code licence: MIT (see LICENSE).
