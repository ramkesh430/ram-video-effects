#!/usr/bin/env python3
"""
make_video.py - a complete Vox-style explainer from a script: AI voice-over + paper background + Vox effects.

  python vox/make_video.py vox/scripts/digital_marketing_ne.json            # -> outputs/<name>.mp4
  python vox/make_video.py SCRIPT.json --out my.mp4 --silent                  # no TTS (timing estimate, for previews)
  python vox/make_video.py SCRIPT.json --preview                              # PNG frames from the middle of each scene

Script JSON (captions, music, sfx and motion are on by default):
{
  "name": "digital_marketing_ne",
  "voice": "ne-NP-SagarNeural",          # any edge-tts voice (ne-NP-HemkalaNeural, en-US-GuyNeural, hi-IN-MadhurNeural ...)
  "rate": "+0%",
  "size": [1080, 1920],                    # 9:16 reel; [1920,1080] for YouTube
  "background": "paper" | "path/to/video_or_photo",
  "transitions": true,                     # block-wipe between scenes
  "global": [{"fx": "paper-grain", "amount": 0.35}],   # effects over the whole video
  "captions": true, "music": "auto" | "none" | "path/to/music.mp3", "music_volume": 0.28, "sfx": true, "motion": true,
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
    """voice-over mp3 + word timings [(word, start_s, end_s)] from edge-tts word boundaries."""
    import edge_tts
    words = []
    with open(path, "wb") as f:
        async for ch in edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary").stream():
            if ch["type"] == "audio": f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                s0 = ch["offset"] / 1e7; words.append([ch["text"], s0, s0 + ch["duration"] / 1e7])
    return words

def spread_words(text, d):
    """estimated word timings when the TTS gives none (silent preview or no boundaries)."""
    ws = str(text).split(); tot = sum(len(w) + 1 for w in ws) or 1; t, out = 0.05, []
    for w in ws:
        dd = (len(w) + 1) / tot * (d - 0.1); out.append([w, t, t + dd * 0.95]); t += dd
    return out

def tts(text, voice, rate, path, silent):
    """returns (duration, words)"""
    if not silent:
        for attempt in range(3):
            try:
                words = asyncio.run(_tts(text, voice, rate, path))
                if os.path.exists(path) and os.path.getsize(path) > 1000:
                    d = duration(path); return d, (words or spread_words(text, d))
            except Exception as e:
                print(f"   TTS attempt {attempt + 1} failed: {e}", file=sys.stderr)
        sys.exit("Voice generation failed (edge-tts needs internet). Use --silent for a timing preview.")
    d = max(1.5, len(text) / 13.0)                      # rough speaking time
    sh("ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", f"{d:.2f}", path)
    return d, spread_words(text, d)

# ---------------------------------------------------------------- original music + sound effects (synthesised, no licence issues)
SR = 44100
def _midi(n): return 440.0 * 2 ** ((n - 69) / 12)

def make_music(total, path, seed=7, bpm=92):
    """a soft, original lo-fi bed: pads, bass, kick, clap, hats and a light pluck arp (I-V-vi-IV)."""
    import numpy as np
    rng = np.random.default_rng(seed); n = int(total * SR); out = np.zeros((n, 2), np.float32)
    beat = 60 / bpm; bar = beat * 4
    chords = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]          # C G Am F
    def add(sig, t0, pan=0.0, gain=1.0):
        i0 = int(t0 * SR); i1 = min(n, i0 + len(sig))
        if i1 <= i0: return
        s = sig[:i1 - i0] * gain; out[i0:i1, 0] += s * (1 - max(0, pan)); out[i0:i1, 1] += s * (1 + min(0, pan))
    tb = np.arange(int(bar * SR)) / SR
    env_pad = np.minimum(1, tb / 0.5) * np.minimum(1, (bar - tb) / 0.4)
    k = 0; t = 0.0
    while t < total:
        ch = chords[k % 4]
        pad = sum(np.sin(2 * np.pi * _midi(m) * tb) + 0.25 * np.sin(4 * np.pi * _midi(m) * tb + 0.3) for m in ch) / 3
        add((pad * env_pad * (0.8 + 0.2 * np.sin(2 * np.pi * 0.5 * tb))).astype(np.float32), t, gain=0.16)
        for b in range(4):                                                       # bass, kick, clap
            tt = t + b * beat; tk = np.arange(int(0.35 * SR)) / SR
            if b in (0, 2):
                add((np.sin(2 * np.pi * _midi(ch[0] - 24) * tk) * np.exp(-tk * 5)).astype(np.float32), tt, gain=0.22)
                f = 45 + 80 * np.exp(-tk * 30); add((np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tk * 12)).astype(np.float32), tt, gain=0.35)
            else:
                tc = np.arange(int(0.15 * SR)) / SR; nz = rng.normal(0, 1, len(tc)); nz = np.diff(nz, prepend=0)
                add((nz * np.exp(-tc * 28)).astype(np.float32), tt, gain=0.05)
        for e in range(8):                                                       # hats + arp on 8ths
            tt = t + e * beat / 2; th = np.arange(int(0.05 * SR)) / SR
            add((np.diff(rng.normal(0, 1, len(th)), prepend=0) * np.exp(-th * 90)).astype(np.float32), tt, pan=0.3, gain=0.025)
            if rng.random() < 0.55:
                m = rng.choice(ch) + 12 + (12 if rng.random() < 0.25 else 0); ta = np.arange(int(0.4 * SR)) / SR
                tri = 2 / np.pi * np.arcsin(np.sin(2 * np.pi * _midi(m) * ta))
                add((tri * np.exp(-ta * 7)).astype(np.float32), tt, pan=float(rng.uniform(-0.5, 0.5)), gain=0.06)
        t += bar; k += 1
    out = _lowpass(out, 0.35)                                                    # gentle low-pass
    fade = np.ones(n, np.float32); fi, fo = int(1.0 * SR), int(2.5 * SR)
    fade[:fi] = np.linspace(0, 1, fi); fade[-fo:] = np.linspace(1, 0, fo); out *= fade[:, None]
    out /= max(1e-6, np.abs(out).max()) / 0.6
    _write_wav(path, out)

def make_sfx(total, whooshes, pops, path, seed=11):
    import numpy as np
    rng = np.random.default_rng(seed); n = int(total * SR); out = np.zeros(n, np.float32)
    def put(sig, t0, g):
        i0 = int(max(0, t0) * SR); i1 = min(n, i0 + len(sig))
        if i1 > i0: out[i0:i1] += sig[:i1 - i0] * g
    L = int(0.55 * SR); tw = np.arange(L) / L
    for t in whooshes:                                                           # filtered-noise sweep
        nz = rng.normal(0, 1, L).astype(np.float32); y = np.empty_like(nz); acc = 0.0
        coef = 0.02 + 0.35 * np.sin(np.pi * tw) ** 2
        for i in range(L): acc += coef[i] * (nz[i] - acc); y[i] = acc
        put(y * np.sin(np.pi * tw) ** 2, t - 0.3, 0.9)
    tp = np.arange(int(0.09 * SR)) / SR
    for t in pops:                                                               # soft pop / blip
        f = 520 + 600 * np.exp(-tp * 40)
        put((np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tp * 45)).astype(np.float32), t, 0.25)
    out /= max(1e-6, np.abs(out).max()) / 0.7
    _write_wav(path, np.stack([out, out], 1))

def _lowpass(x, a):
    """one-pole low-pass y += a*(x-y) along axis 0 (scipy if present, else a cumulative trick per block)."""
    import numpy as np
    try:
        from scipy.signal import lfilter
        return lfilter([a], [1, a - 1], x, axis=0).astype(np.float32)
    except Exception:
        k = max(1, int(round(1 / a)))                                            # fallback: moving average of ~1/a samples
        c = np.cumsum(np.pad(x, ((k, 0),) + ((0, 0),) * (x.ndim - 1)), axis=0)
        return ((c[k:] - c[:-k]) / k).astype(np.float32)

def _write_wav(path, data):
    import numpy as np, wave
    d = (np.clip(data, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(d.shape[1]); w.setsampwidth(2); w.setframerate(SR); w.writeframes(d.tobytes())

POP_FX = {"torn-headline", "marker-text", "big-number", "vox-bars", "vox-line", "icon-array", "vox-timeline", "highlight-clip",
          "search-bar", "phone-feed", "chat-flow", "sticker", "photo-drop", "context-label", "quote-card", "compare-split", "redact", "doc-reveal"}

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
    ap.add_argument("--size", help="override the frame size, e.g. 1080x1920 (reel) or 1920x1080 (YouTube)")
    ap.add_argument("--name", help="override the output name")
    a = ap.parse_args()
    S = json.load(open(a.script, encoding="utf-8"))
    name = a.name or S.get("name") or os.path.splitext(os.path.basename(a.script))[0]
    size = [int(v) for v in a.size.lower().split("x")] if a.size else S.get("size", [1080, 1920]); voice = S.get("voice", "ne-NP-SagarNeural"); rate = S.get("rate", "+0%")
    out = a.out or os.path.join(ROOT, "outputs", name + ".mp4")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="voxvid_")

    # 1. voice per scene -> timeline
    plan, wavs, starts, t, all_words = [], [], [], 0.0, []
    for i, sc in enumerate(S["scenes"]):
        mp3 = os.path.join(tmp, f"s{i:02d}.mp3")
        d, words = tts(sc["say"], sc.get("voice", voice), sc.get("rate", rate), mp3, a.silent)
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
        all_words += [[w, round(s0 + pre + a_, 3), round(s0 + pre + b_, 3)] for w, a_, b_ in words]
        print(f"scene {i + 1}: {s0:6.2f}s - {s1:6.2f}s  ({d:.1f}s voice)  {sc['say'][:40]}", flush=True)
        t = s1
    total = t + 0.6
    if S.get("transitions", True):
        for s0, s1 in starts[1:]:
            plan.append({"fx": "block-wipe", "start": round(s0 - 0.3, 3), "end": round(s0 + 0.3, 3)})
    for g in S.get("global", []):
        g = dict(g); g.setdefault("start", 0); g.setdefault("end", total); plan.insert(0, g)
    land = size[0] > size[1]
    if S.get("motion", True):                                                    # never a static frame
        plan.insert(0, {"fx": "bg-shapes", "start": 0, "end": round(total, 3), "seed": len(S["scenes"])})
        for i, (s0, s1) in enumerate(starts):
            plan.append({"fx": "camera-drift", "start": round(s0, 3), "end": round(s1, 3), "direction": "in" if i % 2 == 0 else "out"})
    if S.get("captions", True) and all_words:                                   # subtitles of the voice, word by word
        cy = 0.88 if land else 0.86
        for f in plan:                                                           # keep the bottom band free for them
            if f["fx"] == "source-tag": f["y"] = 0.06; f["corner"] = "right"
            elif f["fx"] in ("context-label", "sticker") and float(f.get("y", 0.88 if f["fx"] == "context-label" else 0.18)) > 0.78:
                f["y"] = 0.74 if not land else 0.72
        plan.append({"fx": "voice-captions", "start": 0, "end": round(total, 3), "words": all_words, "y": cy})

    # 2. audio track
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{w}'\n" for w in wavs))
    audio = os.path.join(tmp, "voice.wav")
    voice_wav = os.path.join(tmp, "voice_raw.wav")
    sh("ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-af", "apad", "-t", f"{total:.3f}", voice_wav)
    music = S.get("music", "auto")
    mus = None
    if music == "auto" and not a.preview:
        mus = os.path.join(tmp, "music.wav"); make_music(total, mus, seed=len(S["scenes"]) * 7 + 3)
    elif music not in ("auto", "none", None, False):
        mus = os.path.join(tmp, "music.wav")
        sh("ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", music if os.path.isabs(music) else os.path.join(ROOT, music),
           "-t", f"{total:.3f}", "-af", f"afade=t=in:d=1,afade=t=out:st={max(0, total - 2.5):.2f}:d=2.5", "-ar", str(SR), "-ac", "2", mus)
    sfx = None
    if S.get("sfx", True) and not a.preview:
        sfx = os.path.join(tmp, "sfx.wav")
        make_sfx(total, [s0 for s0, _ in starts[1:]] if S.get("transitions", True) else [],
                 sorted({round(f["start"], 2) for f in plan if f["fx"] in POP_FX}), sfx)
    ins = ["-i", voice_wav] + (["-i", mus] if mus else []) + (["-i", sfx] if sfx else [])
    fc = "[0:a]aresample=44100,loudnorm=I=-16:TP=-1.5:LRA=11,asplit=2[v1][v2];"; mix = "[v1]"; k = 1
    if mus:
        fc += f"[{k}:a]volume={float(S.get('music_volume', 0.28)):.2f}[m];[m][v2]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=400[md];"; mix += "[md]"; k += 1
    else:
        fc += "[v2]anullsink;"
    if sfx:
        fc += f"[{k}:a]volume=0.35[s];"; mix += "[s]"; k += 1
    n_in = mix.count("[")
    fc += (f"{mix}amix=inputs={n_in}:normalize=0:duration=first," if n_in > 1 else f"{mix}") + "alimiter=limit=0.95[a]"
    sh("ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", fc, "-map", "[a]", "-ar", "48000", "-ac", "2", "-t", f"{total:.3f}", audio)

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
