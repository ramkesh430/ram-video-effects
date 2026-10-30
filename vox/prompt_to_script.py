#!/usr/bin/env python3
"""
prompt_to_script.py - turn a plain-language prompt into a make_video.py script JSON, using Claude.

  export ANTHROPIC_API_KEY=...            # GitHub: Settings -> Secrets -> Actions -> ANTHROPIC_API_KEY
  python vox/prompt_to_script.py "60 sec Nepali promo for Ram Digital: Google Ads, TikTok Ads, UGC AI video, AI automation" \
         --out vox/scripts/auto/ram_digital.json

Then: python vox/make_video.py vox/scripts/auto/ram_digital.json [--size 1920x1080]
"""
import argparse, json, os, re, sys, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = [m for m in [os.environ.get("CLAUDE_MODEL")] if m] + ["claude-sonnet-4-5", "claude-sonnet-4-0", "claude-opus-4-1"]

EFFECTS = """Vox effects (all positions are fractions of the frame; y = vertical centre):
LOOK   paper-grain{amount} (use once in "global" with amount 0.2) | archive-film{look: sepia|bw} | block-wipe (added automatically between scenes)
TEXT   torn-headline{kicker, text, y=0.13} - section title strip at the top. Keep text under 45 characters.
       marker-text{text, y, size=0.07-0.1} - 1-4 lines on paper strips, "|" = new line, [words] get a yellow highlighter. Short lines (< 30 chars).
       context-label{text, sub, y=0.86} - small typewriter label bottom-left (place/date/episode).
       quote-card{quote, by} - FULL SCREEN quote, [words] highlighted. Use alone in its scene.
       highlight-clip{source, headline, body, date, y} - newspaper clipping; [phrase] in body gets highlighted.
DATA   big-number{value, prefix, suffix, label, y=0.5} | vox-bars{title, labels[], values[], suffix, highlight, source, y=0.6}
       vox-line{title, values[], labels[first,last], prefix, suffix, y=0.6} | icon-array{total=100, highlight, cols=10, label, y=0.6}
       vox-timeline{years[], events[], y=0.62, active (optional fixed index)} | compare-split{left, right, left_value, right_value, prefix, suffix, note, source} (FULL SCREEN)
       source-tag{text, y=0.96} - put on every scene that shows a number.
CUTAWAY doc-reveal{title, note} | redact{title, lines[], stamp} (FULL SCREEN, use alone) | photo-drop{captions[3], sepia=false} (3 labelled cards near the top)
OTHER  sticker{text, x, y, angle} - small tilted badge (e.g. "DM US", "NEW") | arrow-callout{text, x, y, from_x, from_y}"""

SYSTEM = f"""You write scripts for a Vox-style explainer/ad video generator. Reply with ONE JSON object only, no prose, no code fences.

Schema:
{{"name": "snake_case_name", "voice": "<edge-tts voice>", "rate": "+0%", "size": [W, H], "background": "paper", "transitions": true,
  "global": [{{"fx": "paper-grain", "amount": 0.2}}],
  "scenes": [{{"say": "<what the voice says>", "fx": [{{"fx": "<effect>", "at": <s from scene start>, ...params}}]}}]}}

Rules:
- Voice: Nepali -> "ne-NP-SagarNeural" (male) or "ne-NP-HemkalaNeural" (female); Hindi -> "hi-IN-MadhurNeural"/"hi-IN-SwaraNeural";
  English -> "en-US-GuyNeural"/"en-US-JennyNeural". Default: Nepali male. Write "say" in that language and script
  (Devanagari for Nepali/Hindi). Write numbers in words in "say" so the voice reads them well.
- On-screen text (all effect params) in short, punchy ENGLISH (fonts do not render Devanagari).
- Length: about 13 characters of Nepali speech per second. 60 s ~ 7-8 scenes of 80-130 characters; 5 min ~ 16-20 scenes.
- Each scene: 1-3 effects. A full-screen effect (quote-card, compare-split, doc-reveal, redact) is alone in its scene.
  Usually: torn-headline at the top + one main element (marker-text / data / cutaway) + optional source-tag or context-label.
  "at" may be negative = seconds before the scene ends (e.g. a sticker at -3).
- NEVER invent statistics, prices, client names, results, testimonials or quotes. Use numbers only if the prompt gives them,
  and then add a source-tag naming the source the prompt gave. Without data, use text effects instead of data effects.
- No fake reviews or "real customer" claims. If the topic is AI-made UGC, say it is AI-made and labelled.
- For an ad/promo: hook -> problem -> services/benefits (one scene each) -> how it works -> call to action (brand name + sticker).
- size: [1080, 1920] for reels/shorts/TikTok (default), [1920, 1080] for YouTube/landscape.

{EFFECTS}"""

def call_claude(prompt, key):
    last = None
    for model in MODELS:
        body = json.dumps({"model": model, "max_tokens": 8000, "system": SYSTEM,
                           "messages": [{"role": "user", "content": prompt}]}).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
            "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                data = json.load(r)
            print(f"model: {model}", file=sys.stderr)
            return "".join(b.get("text", "") for b in data.get("content", []))
        except urllib.error.HTTPError as e:
            last = f"{e.code} {e.read().decode(errors='ignore')[:300]}"
            if e.code in (400, 404) and "model" in last.lower():
                continue                                   # try the next model name
            sys.exit(f"Claude API error: {last}")
    sys.exit(f"No model worked (set CLAUDE_MODEL). Last error: {last}")

def validate(S):
    sys.path[:0] = [HERE, os.path.dirname(HERE)]
    import vox, fx                                     # noqa: F401  (registers every effect)
    ok = set(fx.REG) | set(fx.ALIAS)
    for sc in S.get("scenes", []):
        sc["fx"] = [f for f in sc.get("fx", []) if f.get("fx") in ok or print(f"   dropped unknown effect {f.get('fx')}", file=sys.stderr)]
    S["scenes"] = [sc for sc in S.get("scenes", []) if str(sc.get("say", "")).strip()]
    if not S["scenes"]: sys.exit("The generated script has no scenes.")
    S.setdefault("background", "paper"); S.setdefault("transitions", True)
    return S

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt"); ap.add_argument("--out", required=True)
    ap.add_argument("--voice", help="force an edge-tts voice"); ap.add_argument("--size", help="force WxH")
    a = ap.parse_args()
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key: sys.exit("ANTHROPIC_API_KEY is not set. On GitHub: Settings -> Secrets and variables -> Actions -> New secret.")
    text = call_claude(a.prompt, key)
    m = re.search(r"\{.*\}", text, re.S)
    if not m: sys.exit("Claude did not return JSON:\n" + text[:500])
    S = validate(json.loads(m.group(0)))
    if a.voice: S["voice"] = a.voice
    if a.size: S["size"] = [int(v) for v in a.size.lower().split("x")]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(S, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"script: {a.out}  ({len(S['scenes'])} scenes, name={S.get('name')})")

if __name__ == "__main__":
    main()
