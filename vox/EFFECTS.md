# Vox effects - every option

All 17 Vox effects with their default options. Every effect also takes `start` and `end` (seconds).
`vox.py` also runs all 62 effects of fx.py (see `python vox.py --list`).

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
