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
