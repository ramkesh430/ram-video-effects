#!/usr/bin/env python3
"""
make_video.py - a complete Vox-style explainer from a script: AI voice-over + paper background + Vox effects.

  python vox/make_video.py vox/scripts/digital_marketing_ne.json            # -> outputs/<name>.mp4
  python vox/make_video.py SCRIPT.json --out my.mp4 --silent                  # no TTS (timing estimate, for previews)
  python vox/make_video.py SCRIPT.json --preview                              # PNG frames from the middle of each scene

Script JSON:
{
  "name": "digital_marketing_ne",
  "voice": "ne-NP-SagarNeural",          # any edge-tts voice (ne-NP-HemkalaNeural, en-US-GuyNeural, hi-IN-MadhurNeural ...)
  "rate": "+0%",
  "size": [1080, 1920],                    # 9:16 reel; [1920,1080] for YouTube
  "background": "paper" | "path/to/video_or_photo",
  "transitions": true,                     # block-wipe between scenes
  "global": [{"fx": "paper-grain", "amount": 0.35}],   # effects over the whole video
  "scenes": [
    {"say": "voice text", "fx": [{"fx": "big-number", "value": 100, "at": 0.2, "end": "end"}]}
  ]
}
Inside a scene, "at"/"end" are seconds from the scene start ("end": "end" = until the scene ends; a negative "at" or "end" counts back from the scene end).
Needs: edge-tts (pip install edge-tts) and internet for the voice; ffmpeg; everything vox.py needs.
"""
import argparse, asyncio, json, math, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAD = 0.45          # silence after each scene's line (s)
LEAD = 0.5          # silence before the first line (s)

def sh(*a):
    subprocess.run(a, check=True)

def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip()
    return float(out or 0)

async def _tts(text, voice, rate, path):
    import edge_tts
    await edge_tts.Communicate(text, voice, rate=rate).save(path)

def tts(text, voice, rate, path, silent):
    if not silent:
        for attempt in range(3):
            try:
                asyncio.run(_tts(text, voice, rate, path))
                if os.path.exists(path) and os.path.getsize(path) > 1000:
                    return duration(path)
            except Exception as e:
                print(f"   TTS attempt {attempt + 1} failed: {e}", file=sys.stderr)
        sys.exit("Voice generation failed (edge-tts needs internet). Use --silent for a timing preview.")
    d = max(1.5, len(text) / 13.0)                      # rough speaking time
    sh("ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", f"{d:.2f}", path)
    return d

def paper_background(size, seconds, out, fps=30):
    """slowly drifting paper texture video (no audio)."""
    sys.path[:0] = [HERE, ROOT]
    import numpy as np, cv2, vox
    W, H = size; big = vox.paper_tex(int(W * 1.12), int(H * 1.12), vox.PAPER, 77).astype(np.uint8)
    big = cv2.cvtColor(big, cv2.COLOR_RGB2BGR)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                          "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", out],
                         stdin=subprocess.PIPE)
    n = int(math.ceil(seconds * fps)); mx, my = big.shape[1] - W, big.shape[0] - H
    for i in range(n):
        t = i / fps
        x = int(mx / 2 + math.sin(t * 0.21) * mx * 0.45); y = int(my / 2 + math.cos(t * 0.17) * my * 0.45)
        p.stdin.write(np.ascontiguousarray(big[y:y + H, x:x + W]).tobytes())
    p.stdin.close(); p.wait()

def fit_background(src, size, seconds, out):
    W, H = size
    loop = ["-stream_loop", "-1"] if not src.lower().endswith((".jpg", ".jpeg", ".png", ".webp")) else ["-loop", "1"]
    sh("ffmpeg", "-y", "-loglevel", "error", *loop, "-i", src, "-t", f"{seconds:.2f}", "-an",
       "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=30",
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script"); ap.add_argument("--out"); ap.add_argument("--silent", action="store_true")
    ap.add_argument("--preview", action="store_true"); ap.add_argument("--max-short", default="1080")
    ap.add_argument("--crf", default="26", help="quality (lower = bigger file)")
    ap.add_argument("--max-mb", type=float, default=90, help="re-encode if the video is bigger (GitHub limit is 100 MB)")
    a = ap.parse_args()
    S = json.load(open(a.script, encoding="utf-8"))
    name = S.get("name") or os.path.splitext(os.path.basename(a.script))[0]
    size = S.get("size", [1080, 1920]); voice = S.get("voice", "ne-NP-SagarNeural"); rate = S.get("rate", "+0%")
    out = a.out or os.path.join(ROOT, "outputs", name + ".mp4")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="voxvid_")

    # 1. voice per scene -> timeline
    plan, wavs, starts, t = [], [], [], 0.0
    for i, sc in enumerate(S["scenes"]):
        mp3 = os.path.join(tmp, f"s{i:02d}.mp3")
        d = tts(sc["say"], sc.get("voice", voice), sc.get("rate", rate), mp3, a.silent)
        pre = LEAD if i == 0 else 0.0                       # small lead-in before the very first line
        length = max(float(sc.get("min", 0)), pre + d + PAD)
        wav = os.path.join(tmp, f"s{i:02d}.wav")
        sh("ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-af", f"adelay={int(pre * 1000)}:all=1,apad",
           "-t", f"{length:.3f}", "-ar", "48000", "-ac", "2", wav)
        wavs.append(wav)
        s0, s1 = t, t + length
        starts.append((s0, s1))
        for f in sc.get("fx", []):                         # at/end are relative to the scene start
            f = dict(f); at = float(f.pop("at", 0)); en = f.pop("end", "end")
            st = s0 + at if at >= 0 else s1 + at          # negative "at" = seconds before the scene ends
            e = s1 if en == "end" else (s1 + float(en) if float(en) < 0 else s0 + float(en))
            f["start"], f["end"] = round(st, 3), round(max(st + 0.2, e), 3)
            plan.append(f)
        print(f"scene {i + 1}: {s0:6.2f}s - {s1:6.2f}s  ({d:.1f}s voice)  {sc['say'][:40]}", flush=True)
        t = s1
    total = t + 0.6
    if S.get("transitions", True):
        for s0, s1 in starts[1:]:
            plan.append({"fx": "block-wipe", "start": round(s0 - 0.3, 3), "end": round(s0 + 0.3, 3)})
    for g in S.get("global", []):
        g = dict(g); g.setdefault("start", 0); g.setdefault("end", total); plan.insert(0, g)

    # 2. audio track
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{w}'\n" for w in wavs))
    audio = os.path.join(tmp, "voice.wav")
    sh("ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-af", "apad", "-t", f"{total:.3f}", audio)

    # 3. background + audio -> base clip
    bgv = os.path.join(tmp, "bg.mp4")
    bg = S.get("background", "paper")
    if bg == "paper": paper_background(size, total, bgv)
    else: fit_background(os.path.join(ROOT, bg) if not os.path.isabs(bg) else bg, size, total, bgv)
    base = os.path.join(tmp, "base.mp4")
    sh("ffmpeg", "-y", "-loglevel", "error", "-i", bgv, "-i", audio, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
       "-c:a", "aac", "-b:a", "192k", "-shortest", base)
    plan_path = os.path.splitext(out)[0] + "_plan.json"
    json.dump(plan, open(plan_path, "w", encoding="utf-8"), ensure_ascii=False, indent=0)

    # 4. Vox effects
    eng = [sys.executable, os.path.join(HERE, "vox.py"), base]
    if a.preview:
        mids = ",".join(f"{(s0 + s1) / 2:.2f}" for s0, s1 in starts)
        sh(*eng, os.path.splitext(out)[0] + ".png", "--plan", plan_path, "--preview", mids)
    else:
        sh(*eng, out, "--plan", plan_path, "--max-short", str(a.max_short), "--crf", str(a.crf))
        mb = os.path.getsize(out) / 1e6
        if mb > a.max_mb:                                   # keep it pushable to GitHub
            kbps = int(a.max_mb * 8000 * 0.92 / total) - 160
            small = out + ".small.mp4"
            sh("ffmpeg", "-y", "-loglevel", "error", "-i", out, "-c:v", "libx264", "-preset", "medium", "-b:v", f"{kbps}k",
               "-maxrate", f"{int(kbps * 1.3)}k", "-bufsize", f"{kbps * 2}k", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
               "-movflags", "+faststart", small)
            os.replace(small, out); print(f"   re-encoded {mb:.0f} MB -> {os.path.getsize(out) / 1e6:.0f} MB")
        print(f"Video: {out}  ({total:.1f}s, {os.path.getsize(out) / 1e6:.0f} MB)")

if __name__ == "__main__":
    main()
