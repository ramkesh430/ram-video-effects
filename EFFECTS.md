# Effects reference

Every effect takes `start` and `end` (seconds). Other options are listed below with their defaults.

Use them in `plan.json`:

```json
[{"fx": "orbit", "start": 3, "end": 6, "images": "my_reels/"}]
```

## 1. `noise`

Reels/screenshots pile up behind your head

| option | default |
|---|---|
| `images` | `null` |
| `count` | `10` |

## 2. `lineup`

Numbered tiles fan out above your head

| option | default |
|---|---|
| `items` | `["1", "2", "3", "4", "5"]` |
| `color` | `"#111111"` |
| `accent` | `"#FFFFFF"` |

## 3. `locked-on`

Brackets lock onto your face and the camera follows you

| option | default |
|---|---|
| `color` | `"#FFFFFF"` |
| `zoom` | `1.15` |

## 4. `backdrop-word`

Giant word drops in BEHIND your head (style: display|serif|serif-italic)

| option | default |
|---|---|
| `text` | `"FOCUS"` |
| `color` | `"#FFFFFF"` |
| `style` | `"display"` |
| `y` | `null` |
| `glow` | `false` |

## 5. `spotlight`

Kill the lights, keep you lit (optional glowing word behind you)

| option | default |
|---|---|
| `dark` | `0.85` |
| `word` | `null` |
| `color` | `"#FF9EB5"` |

## 6. `the-bill`

Your instructions print out like a receipt

| option | default |
|---|---|
| `title` | `"RECEIPT"` |
| `lines` | `["01 FOLLOW MY FACE", "02 ORBIT", "03 WORD BEHIND ME", "04 KILL THE LIGHTS"]` |
| `total` | `"TOTAL  4 EFFECTS"` |

## 7. `moody`

Moody colour grade (optional serif word behind you)

| option | default |
|---|---|
| `word` | `null` |

## 8. `swipe`

Before/after slider wipes across (before: bw|dark|blur|raw)

| option | default |
|---|---|
| `before` | `"bw"` |
| `labels` | `["BEFORE", "AFTER"]` |

## 9. `todo`

Notes checklist beside your head that ticks off as you talk

| option | default |
|---|---|
| `title` | `"Notes"` |
| `items` | `["Drop your video", "Install my skill", "Type / + the effect"]` |

## 10. `comment-box` (also: `comment`)

A comment types itself, then posts

| option | default |
|---|---|
| `user` | `"you"` |
| `text` | `"This is so useful!"` |
| `accent` | `"#3B82F6"` |
| `dark` | `true` |

## 11. `tap`

A Follow button gets tapped and flips to Following

| option | default |
|---|---|
| `name` | `"Your Name"` |
| `handle` | `"@yourhandle"` |
| `accent` | `"#3B82F6"` |

## 12. `pause-point`

Freeze frame with PAUSED chip and hand-drawn arrows + labels

| option | default |
|---|---|
| `labels` | `["me", "Claude did this"]` |
| `targets` | `["face", [0.5, 0.62]]` |
| `color` | `"#FFC531"` |

## 13. `uninstall`

App tiles with minus badges, a glitchy uninstall bar breaks the frame

| option | default |
|---|---|
| `apps` | `["Editor", "Clips", "FX"]` |
| `label` | `"Uninstalling..."` |

## 14. `reel-frame`

Your video shrinks into a film-strip reel card

| option | default |
|---|---|
| `label` | `"KODAK 400 • 21"` |
| `scale` | `0.78` |

## 15. `shortcut-rain`

Keyboard keys rain down behind you

| option | default |
|---|---|
| `keys` | `["⌘", "Z", "K", "J", "⇧", "C", "V", "⌥"]` |
| `count` | `10` |

## 16. `reject-stamp` (also: `stamp`)

A big red stamp slams down (with camera shake)

| option | default |
|---|---|
| `text` | `"NOPE"` |
| `color` | `"#E11D2E"` |
| `angle` | `-14` |

## 17. `countdown`

3-2-1 flip tiles above your head

| option | default |
|---|---|
| `from` | `3` |

## 18. `countdown-flip`

Flip-clock counter rolls from one value to another (e.g. 43:00 -> 4:22)

| option | default |
|---|---|
| `from` | `"43:00"` |
| `to` | `"04:22"` |
| `label` | `"RAW → FINAL"` |

## 19. `rabbit-hole`

The room tunnels away behind you (nested frames)

| option | default |
|---|---|
| `depth` | `5` |
| `color` | `"#FFFFFF"` |

## 20. `cover-star`

You become a magazine cover (look: classic|editorial)

| option | default |
|---|---|
| `title` | `"VIBE"` |
| `lines` | `["THE AI ISSUE", "22 EFFECTS NO EDITOR"]` |
| `color` | `"#FF6B8A"` |
| `look` | `"classic"` |

## 21. `scribble`

Marker circle draws itself around you + arrow and a word (B&W frame)

| option | default |
|---|---|
| `word` | `"me"` |
| `color` | `"#E3262B"` |
| `bw` | `true` |

## 22. `glass-widgets`

Frosted glass widgets (stat, chart, progress) float around your head

| option | default |
|---|---|
| `stat` | `"38"` |
| `stat_label` | `"effects"` |
| `chart_label` | `"Top reels"` |
| `chart_value` | `"197K"` |
| `progress_label` | `"Rendering"` |
| `progress` | `0.92` |

## 23. `red-collage`

Black & white you, a giant red word behind, three lines slam in

| option | default |
|---|---|
| `word` | `"EDIT"` |
| `lines` | `["ONE CLIP.", "34 EFFECTS.", "ZERO APPS."]` |
| `color` | `"#FF2A2A"` |

## 24. `split-headline`

Headline card slides down and pushes you to the bottom half. [word] = highlight; | = new line

| option | default |
|---|---|
| `text` | `"Claude [edits] my|reels."` |
| `accent` | `"#22C55E"` |
| `bg` | `"#F7F5F0"` |
| `chip` | `"in seconds ↗"` |

## 25. `pastel-word`

Lavender room, a giant word behind you, a profile card gets followed

| option | default |
|---|---|
| `word` | `"REELS"` |
| `bg` | `["#C9B8F5", "#E9E0FF"]` |
| `name` | `"Your Name"` |
| `handle` | `"@yourhandle"` |

## 26. `check-pills`

Grid-paper room, your reels pinned behind you, blue pills get clicked

| option | default |
|---|---|
| `pills` | `["Hook", "Cuts", "Captions", "B-roll"]` |
| `images` | `null` |
| `accent` | `"#2563EB"` |

## 27. `timeline`

Dark red film look with an editing timeline and a glowing playhead

| option | default |
|---|---|
| `title` | `"AUTO-EDIT"` |
| `sub` | `"timeline by Claude"` |
| `color` | `"#E53935"` |

## 28. `headline`

White headline card slides down at the top (goes behind your head if needed). | = 2nd line

| option | default |
|---|---|
| `text` | `"BIG NEWS|Here is why"` |
| `accent` | `"#E8432E"` |

## 29. `headline-box`

A punch-in with a clean two-line headline (black text on white boxes)

| option | default |
|---|---|
| `text` | `"How I got Claude|to edit my reels."` |
| `zoom` | `1.18` |

## 30. `profile-wall`

Your reels grid fills the wall while a follower counter ticks up

| option | default |
|---|---|
| `images` | `null` |
| `count` | `197000` |
| `label` | `"followers"` |
| `handle` | `"@yourhandle"` |

## 31. `tier-list`

A tier list drops in and your pick flies into S tier

| option | default |
|---|---|
| `tiers` | `{"S": [], "A": ["templates"], "B": ["timelines"], "C": ["apps"], "D": ["doing it by hand"]}` |
| `winner` | `"Claude"` |
| `accent` | `"#F97316"` |

## 32. `broll-split`

B-roll (image or video) on top, you below, with a price-tag sticker

| option | default |
|---|---|
| `broll` | `null` |
| `tag` | `"4 hrs → 4 min"` |
| `word` | `"CLAUDIT"` |
| `color` | `"#FF8A80"` |

## 33. `phone-fan`

Your reels fan out like a hand of phones

| option | default |
|---|---|
| `images` | `null` |
| `count` | `4` |

## 34. `dot-reveal`

Your shot builds out of glowing dots, then snaps into focus

| option | default |
|---|---|
| `color` | `"#F5A623"` |
| `cell` | `18` |

## 35. `headline-wall`

Your headlines pile up behind your head, then a total pops in front

| option | default |
|---|---|
| `headlines` | `["Same prompt, two models", "The new AI model is cheaper", "Protect your personal data", "Easiest no-code automation", "Scrape anything in 5 min"]` |
| `total` | `"672K"` |
| `total_label` | `"views from 7 reels"` |
| `accent` | `"#F97316"` |

## 36. `checklist`

Task list card under your chin, each step ticks green (style: dark|light)

| option | default |
|---|---|
| `title` | `"Claude is editing your clip"` |
| `items` | `["Found your face", "Cut you out of the room", "Put the text behind you", "Graded the colour", "Rendered in 4K"]` |
| `notes` | `["every frame", "AI mask", "depth", "warm", "2160p"]` |
| `accent` | `"#22C55E"` |
| `style` | `"dark"` |

## 37. `name-tag`

Lower-third with your name and title

| option | default |
|---|---|
| `name` | `"Your Name"` |
| `title` | `"Creator"` |
| `accent` | `"#F59E0B"` |

## 38. `lean-in` (also: `punch-in`)

A quick punch-in zoom on one word

| option | default |
|---|---|
| `zoom` | `1.3` |

## 39. `slow-push`

Slow cinematic push-in while the room melts out of focus

| option | default |
|---|---|
| `zoom` | `1.15` |

## 40. `orbit`

Your reels (or text chips) circle your head - behind at the top, below the chin in front

| option | default |
|---|---|
| `items` | `null` |
| `images` | `null` |
| `count` | `5` |
| `speed` | `0.33` |

## 41. `carousel-spin`

Your reels spin around you in a 3D carousel

| option | default |
|---|---|
| `images` | `null` |
| `count` | `6` |
| `speed` | `0.22` |
| `tilt` | `0.35` |
| `flat3d` | `true` |

## 42. `liquid-glass-graph`

Liquid glass card with a climbing graph and a counting number (look=bento for a glass dashboard)

| option | default |
|---|---|
| `value` | `197000` |
| `prefix` | `""` |
| `suffix` | `""` |
| `label` | `"views this month"` |
| `values` | `[3, 4, 3.5, 6, 5.5, 8, 9.5, 13]` |
| `look` | `"card"` |

## 43. `match-cut`

News pages cut on one word, locked in place behind your head

| option | default |
|---|---|
| `pages` | `["AI EDITS VIDEO NOW", "CREATORS SKIP THE TIMELINE", "ONE PROMPT, ONE REEL", "THE EDITOR IS A CHAT"]` |
| `word` | `"AI"` |
| `color` | `"#D7263D"` |

## 44. `apple-toggles` (also: `toggles`)

Switches flip on under your chin, one line at a time

| option | default |
|---|---|
| `items` | `["Face tracking", "Text behind me", "Colour grade", "Auto-render"]` |
| `accent` | `"#34C759"` |

## 45. `led-sign`

The lights drop and a glowing LED sign types itself out behind you

| option | default |
|---|---|
| `text` | `"ON AIR"` |
| `color` | `"#FF5A1F"` |
| `dark` | `0.8` |

## 46. `over-the-shoulder-zoom`

Pushes into one corner, a glass graph pops beside your head, then the other corner with a 2nd graph

| option | default |
|---|---|
| `graphs` | `[{"value": 21, "label": "reels", "values": [1, 2, 2, 4, 6, 9]}, {"value": 672000, "label": "views", "values": [2, 3, 5, 4, 8, 12]}]` |
| `zoom` | `1.3` |

## 47. `messages`

Message notifications pop in one after another with a soft glow

| option | default |
|---|---|
| `messages` | `[{"from": "Mom", "text": "Saw your reel!!"}, {"from": "Alex", "text": "how did you edit this??"}, {"from": "Sam", "text": "teach me pls"}]` |
| `accent` | `"#34C759"` |

## 48. `place-in-grid`

You shrink into the centre of your 3x3 profile grid; reels pop in around you with view counts

| option | default |
|---|---|
| `images` | `null` |
| `views` | `["12K", "40K", "8K", "197K", "23K", "61K", "9K", "88K"]` |

## 49. `countup`

Big number counts up under your chin (e.g. followers, money)

| option | default |
|---|---|
| `value` | `10000` |
| `prefix` | `""` |
| `suffix` | `""` |
| `label` | `"followers"` |
| `accent` | `"#FACC15"` |

## 50. `glitter-spotlight`

Spotlight with golden rays and sparkles behind you

| option | default |
|---|---|
| `color` | `"#FFD36E"` |
| `dark` | `0.8` |

## 51. `confetti`

Confetti burst falls over the frame

| option | default |
|---|---|
| `count` | `140` |

## 52. `glitch`

Digital glitch hit (RGB split + slice shifts)

| option | default |
|---|---|
| `amount` | `1.0` |

## 53. `vhs`

VHS tape look: scanlines, noise, colour bleed, date stamp

| option | default |
|---|---|
| `date` | `"PLAY ▶  OCT 30 2026"` |

## 54. `captions`

Bold word-by-word captions (give 'words':[[word,start,end],...] from whisper, or 'text' to spread evenly)

| option | default |
|---|---|
| `text` | `"this is how I edit my reels"` |
| `words` | `null` |
| `color` | `"#FFFFFF"` |
| `highlight` | `"#FACC15"` |
| `per` | `3` |
| `y` | `0.72` |

## 55. `progress-bar`

Thin progress bar along the top that fills over the effect duration

| option | default |
|---|---|
| `color` | `"#FACC15"` |

## 56. `poll`

A two-option poll card; votes animate in

| option | default |
|---|---|
| `question` | `"Would you use this?"` |
| `options` | `["YES", "NO"]` |
| `result` | `[78, 22]` |
| `accent` | `"#8B5CF6"` |

## 57. `whip-zoom`

Fast zoom-blur transition (put it on a cut, ~0.4s)

| option | default |
|---|---|
| `strength` | `1.0` |

## 58. `neon-outline`

A glowing neon outline traces around you

| option | default |
|---|---|
| `color` | `"#22D3EE"` |
| `width` | `10` |

## 59. `heart-burst`

Hearts float up from the bottom corner (like a live stream)

| option | default |
|---|---|
| `count` | `18` |
| `color` | `"#FF3B5C"` |

## 60. `sticker`

A bold tilted text sticker pops on (e.g. 'NEW!', 'PART 2')

| option | default |
|---|---|
| `text` | `"NEW!"` |
| `color` | `"#FACC15"` |
| `x` | `0.75` |
| `y` | `0.18` |
| `angle` | `10` |

## 61. `freeze-bw`

Freeze frame turns black & white with a big label (record-scratch moment)

| option | default |
|---|---|
| `text` | `"yep, that's me."` |
| `color` | `"#FFFFFF"` |

## 62. `split-screen`

Two of you side by side (wide + close-up)

---

# Part 2 - the 22 Vox effects (vox.py)

All 22 Vox effects with their default options. Every effect also takes `start` and `end` (seconds).
`vox.py` also runs all 62 effects of fx.py (see `python vox/vox.py --list`).

## paper-room
Background becomes textured paper; you become a cut-out with a white sticker border (Vox collage look)

```json
{"fx": "paper-room", "start": 0, "end": 3, "color": "#EFE8D8", "border": 14, "shadow": true}
```

## paper-grain
Whole frame gets a warm printed-paper texture, grain and vignette

```json
{"fx": "paper-grain", "start": 0, "end": 3, "amount": 0.6, "color": "#EFE8D8"}
```

## archive-film
Old archive-footage look: sepia/BW, grain, flicker, scratches, dust, gate weave (look: sepia|bw)

```json
{"fx": "archive-film", "start": 0, "end": 3, "look": "sepia", "strength": 1.0}
```

## parallax
2.5D Ken Burns: you push in faster than the background (great on photos)

```json
{"fx": "parallax", "start": 0, "end": 3, "bg_zoom": 1.05, "you_zoom": 1.16}
```

## block-wipe
Yellow + black blocks sweep across - a Vox-style transition (~0.6s, centre it on your cut)

```json
{"fx": "block-wipe", "start": 0, "end": 3, "colors": ["#FFE03A", "#151515"], "direction": "right"}
```

## highlight-clip
Newspaper clipping slides in, a yellow marker highlights the [key phrase]

```json
{"fx": "highlight-clip", "start": 0, "end": 3, "source": "The Kathmandu Post", "headline": "Why prices keep rising", "body": "Economists say the [real reason prices keep rising] is not what most people think.", "date": "", "y": 0.72, "angle": -3}
```

## marker-text
Key line on paper strips; [words] get a yellow highlighter swipe. | = new line

```json
{"fx": "marker-text", "start": 0, "end": 3, "text": "This is the [real reason]|nobody talks about", "y": 0.78, "size": 0.075}
```

## torn-headline
A torn paper strip with a yellow kicker and a bold headline slides in at the top

```json
{"fx": "torn-headline", "start": 0, "end": 3, "kicker": "EXPLAINED", "text": "Why Nepal's rupee is pegged to India", "y": 0.13}
```

## context-label
Typewriter place/date label bottom-left (e.g. 'KATHMANDU, 1990'), Vox lower-third

```json
{"fx": "context-label", "start": 0, "end": 3, "text": "KATHMANDU, 1990", "sub": "", "y": 0.88}
```

## quote-card
Full-screen paper quote: words appear one by one, [words] get highlighted, then the attribution

```json
{"fx": "quote-card", "start": 0, "end": 3, "quote": "The [economy] is not the [stock market].", "by": "— Someone, 2024", "color": "#EFE8D8"}
```

## vox-bars
Horizontal bar chart on paper; bars grow, values count up, one bar highlighted yellow

```json
{"fx": "vox-bars", "start": 0, "end": 3, "title": "Remittance share of GDP", "labels": ["Nepal", "India", "Bangladesh"], "values": [26, 3, 5], "suffix": "%", "highlight": 0, "source": "World Bank", "y": 0.7}
```

## vox-line
Line chart draws itself on paper, a yellow dot rides the tip, end value pops

```json
{"fx": "vox-line", "start": 0, "end": 3, "title": "Price of rice (Rs/kg)", "values": [40, 42, 47, 55, 61, 78, 92], "labels": ["2015", "2025"], "prefix": "Rs ", "suffix": "", "source": "", "y": 0.7, "color": "#E2372B"}
```

## big-number
A huge number counts up on a paper card with a label and a yellow underline

```json
{"fx": "big-number", "start": 0, "end": 3, "value": 3000000, "prefix": "", "suffix": "", "label": "Nepalis work abroad", "y": 0.72, "fmt": "{:,}"}
```

## vox-timeline
Paper timeline: a yellow marker steps through years, each event label pops above it

```json
{"fx": "vox-timeline", "start": 0, "end": 3, "years": ["1990", "2006", "2008", "2015"], "events": ["Democracy restored", "Peace deal", "Republic", "New constitution"], "y": 0.8, "active": null}
```

## map-pin
Cut to a map: camera zooms to a pin that drops in with a place label (image = your own map screenshot)

```json
{"fx": "map-pin", "start": 0, "end": 3, "place": "KATHMANDU", "sub": "Nepal", "image": null, "x": 0.56, "y": 0.44, "zoom": 2.2}
```

## doc-reveal
Cut to a document; camera pushes in while a red marker circles the key part (image = your screenshot)

```json
{"fx": "doc-reveal", "start": 0, "end": 3, "image": null, "title": "OFFICIAL REPORT", "circle": [0.18, 0.46, 0.64, 0.1], "note": "this part!", "zoom": 1.5}
```

## photo-drop
Taped archive photos drop onto the wall behind you, one by one, with typed captions

```json
{"fx": "photo-drop", "start": 0, "end": 3, "images": null, "captions": ["1990", "2006", "2015"], "count": 3, "sepia": true}
```

## arrow-callout
Hand-drawn arrow draws itself to a point (x,y 0-1) with a marker label - point at anything

```json
{"fx": "arrow-callout", "start": 0, "end": 3, "text": "look here", "x": 0.5, "y": 0.45, "from_x": 0.2, "from_y": 0.7, "color": "#E2372B"}
```

## redact
Cut to a document; black redaction bars swipe over lines, then a stamp lands (image = your screenshot)

```json
{"fx": "redact", "start": 0, "end": 3, "image": null, "title": "CONFIDENTIAL MEMO", "lines": [2, 3, 6, 9, 10], "stamp": "CLASSIFIED"}
```

## compare-split
Full-screen A vs B on paper: two halves, numbers count up, the bigger side gets a yellow bar

```json
{"fx": "compare-split", "start": 0, "end": 3, "left": "NEPAL", "right": "INDIA", "left_value": 1400, "right_value": 2500, "prefix": "$", "suffix": "", "note": "GDP per person", "source": ""}
```

## icon-array
Grid of people icons; some turn yellow one by one ('1 in 4 households...')

```json
{"fx": "icon-array", "start": 0, "end": 3, "total": 100, "highlight": 25, "cols": 10, "label": "1 in 4 households has someone abroad", "y": null}
```

## source-tag
Small 'Source: ...' citation chip in the bottom corner (keep it on while a fact is shown)

```json
{"fx": "source-tag", "start": 0, "end": 3, "text": "Source: World Bank, 2024", "corner": "right", "y": 0.955}
```
