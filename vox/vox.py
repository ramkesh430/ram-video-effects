#!/usr/bin/env python3
"""
Ram's Vox Effects - Vox-style explainer edits (paper, highlights, maps, charts, archive film).

  python vox.py IN.mp4 OUT.mp4 --plan plan.json                       # render (audio kept)
  python vox.py IN.mp4 prev.png --plan plan.json --preview 1.5,4      # check frames
  python vox.py --list                                                 # every effect (Vox + the 62 fx effects)

vox.py adds 22 Vox-style effects on top of fx.py (same engine, same plan.json format),
so a plan can mix both: [{"fx":"paper-room","start":0,"end":4}, {"fx":"captions",...}]
"""
import math, os, random, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter

_here = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_here, os.path.dirname(_here)]          # fx.py next to vox.py, or one folder up (repo layout)
import fx
from fx import (FX, register, clamp, lerp, ease_out_cubic, ease_in_out, ease_out_back, hex2rgb, rgba,
                as_list, font, T, fit_size, wrap, paste, card, shadowed, scale_img, rot, load_images,
                affine, zoom_on, to_gray, count_fmt)

# ================================================================= Vox palette
PAPER, INK, YELLOW, RED, BLUE, GREY = "#EFE8D8", "#151515", "#FFE03A", "#E2372B", "#2F5D8A", "#9A958A"

def U(c):
    """size unit: frame width for vertical video, the height for landscape"""
    return min(c.W, c.H)

# ================================================================= textures
_tex = {}
def paper_tex(W, H, color=PAPER, seed=7, grain=6.0):
    """procedural paper: soft blotches + fibres + fine grain. float32 HxWx3, cached."""
    key = (W, H, str(color), seed)
    if key in _tex: return _tex[key]
    r = np.random.default_rng(seed)
    base = np.array(hex2rgb(color), np.float32)
    blot = cv2.resize(r.normal(0, 1, (max(2, H // 90), max(2, W // 90))).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    mid = cv2.resize(r.normal(0, 1, (max(2, H // 12), max(2, W // 12))).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    fine = r.normal(0, 1, (H, W)).astype(np.float32)
    fib = np.zeros((H, W), np.uint8)
    for _ in range(int(W * H / 6000)):
        x, y = int(r.uniform(0, W)), int(r.uniform(0, H)); a = r.uniform(0, math.pi); L = r.uniform(4, 22)
        cv2.line(fib, (x, y), (int(x + L * math.cos(a)), int(y + L * math.sin(a))), 255, 1)
    n = blot * 7 + mid * 3 + fine * grain - fib.astype(np.float32) / 255 * 10
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    vig = 1 - 0.18 * (((xx / W - 0.5) * 2) ** 2 + ((yy / H - 0.5) * 2) ** 2) / 2
    out = np.clip((base + n[..., None]) * vig[..., None], 0, 255).astype(np.float32)
    _tex[key] = out
    return out

def paper_img(w, h, color=PAPER, seed=3):
    return Image.fromarray(paper_tex(int(w), int(h), color, seed, 4).astype(np.uint8), "RGB").convert("RGBA")

def torn(im, jag=None, seed=1, sides="tb"):
    """cut ragged torn-paper edges into an RGBA image (sides: any of t,b,l,r)."""
    w, h = im.size; jag = jag or max(4, int(min(w, h) * 0.025)); r = random.Random(seed)
    pts = []
    step = max(6, jag * 1.4)
    def edge(p0, p1, rough):
        n = max(2, int(math.hypot(p1[0] - p0[0], p1[1] - p0[1]) / step))
        nx, ny = (p1[1] - p0[1]), -(p1[0] - p0[0]); L = math.hypot(nx, ny) or 1; nx, ny = nx / L, ny / L
        for i in range(n):
            t = i / n; o = r.uniform(0, jag) if rough else 0
            pts.append((lerp(p0[0], p1[0], t) + nx * o, lerp(p0[1], p1[1], t) + ny * o))
    edge((0, 0), (w, 0), "t" in sides); edge((w, 0), (w, h), "r" in sides)
    edge((w, h), (0, h), "b" in sides); edge((0, h), (0, 0), "l" in sides)
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).polygon(pts, fill=255)
    out = im.copy(); out.putalpha(Image.fromarray(np.minimum(np.array(m), np.array(im.getchannel("A")))))
    return out

def paper_card(w, h, color=PAPER, seed=3, sides="tb"):
    return torn(paper_img(w, h, color, seed), seed=seed, sides=sides)

def tape(w, angle=0):
    t = Image.new("RGBA", (int(w), int(w * 0.32)), (236, 228, 200, 170))
    return rot(torn(t, max(2, int(w * 0.03)), 9, "lr"), angle)

# ================================================================= marker / highlighter text
def marker_block(lines, kind, size, color, hl, q, max_w=None, gap=0.18, rough=True):
    """render lines; words in [brackets] get a yellow marker swept in by q (0..1, across all highlights in order)."""
    if isinstance(color, str): color = rgba(color)
    if isinstance(hl, str): hl = rgba(hl, 235)
    if max_w:
        ll = []
        for ln in lines: ll += wrap(ln, kind, size, max_w)
        lines = ll
    f = font(kind, size); sp = size * 0.27
    rows, hl_total, inhl = [], 0.0, False
    for ln in lines:
        toks = []
        for tok in str(ln).split():
            if "[" in tok: inhl = True
            word = tok.replace("[", "").replace("]", ""); im = T(word, kind, size, color)
            toks.append([word, im, inhl])
            if "]" in tok: inhl = False
        rows.append(toks)
        for i, (w, im, h) in enumerate(toks):
            if h: hl_total += im.width + (sp if i + 1 < len(toks) and toks[i + 1][2] else 0)
    asc, desc = f.getmetrics(); lh = asc + desc
    W = int(max([sum(t[1].width for t in r) + sp * (len(r) - 1) for r in rows] + [1]) + size * 0.3)
    H = int(len(rows) * lh * (1 + gap) + size * 0.2)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(out)
    budget = hl_total * clamp(q); rr = random.Random(4)
    y = size * 0.1
    for r in rows:      # marker first (under the ink)
        x = size * 0.15
        for i, (w, im, h) in enumerate(r):
            seg = im.width + (sp if i + 1 < len(r) and r[i + 1][2] else 0)
            if h and budget > 0:
                L = min(seg, budget); budget -= L
                y0, y1 = y + lh * 0.18, y + lh * 0.98
                if rough:
                    d.polygon([(x - size * 0.08, y0 + rr.uniform(-2, 2)), (x + L + size * 0.05, y0 + rr.uniform(-3, 1)),
                               (x + L + size * 0.08, y1 + rr.uniform(-1, 3)), (x - size * 0.05, y1 + rr.uniform(-2, 2))], fill=hl)
                else:
                    d.rectangle((x, y0, x + L, y1), fill=hl)
            x += im.width + sp
        y += lh * (1 + gap)
    y = size * 0.1
    for r in rows:
        x = size * 0.15
        for w, im, h in r:
            paste(out, im, x, y + f.getbbox(w)[1])
            x += im.width + sp
        y += lh * (1 + gap)
    return out

def strip_hl(s): return str(s).replace("[", "").replace("]", "")

def full_alpha(lt, dur, fin=0.25, fout=0.25):
    return clamp(lt / fin if fin else 1) * clamp((dur - lt) / fout if fout else 1)

# ================================================================= LOOK effects
@register
class PaperRoom(FX):
    name = "paper-room"; help = "Background becomes textured paper; you become a cut-out with a white sticker border (Vox collage look)"
    params = {"color": PAPER, "border": 14, "shadow": True}
    def bgfx(self, c, img, lt):
        a = self.env(lt, 0.25, 0.25); bg = paper_tex(c.W, c.H, self.p["color"]).copy()
        bw = int(U(c) / 1080 * float(self.p["border"]))
        m = (c.mask > 0.5).astype(np.uint8)
        if bw > 0 and m.any():
            k = np.ones((bw * 2 + 1, bw * 2 + 1), np.uint8); ring = cv2.dilate(m, k).astype(np.float32)
            if self.p["shadow"]:
                sh = cv2.GaussianBlur(np.roll(np.roll(ring, int(bw * 0.8), 0), int(bw * 0.5), 1), (0, 0), bw)
                bg *= (1 - 0.35 * sh)[..., None]
            ring = cv2.GaussianBlur(ring, (0, 0), 1.2)[..., None]
            bg = bg * (1 - ring) + np.array([250, 249, 244], np.float32) * ring
        return img * (1 - a) + bg * a

@register
class PaperGrain(FX):
    name = "paper-grain"; help = "Whole frame gets a warm printed-paper texture, grain and vignette"
    params = {"amount": 0.6, "color": PAPER}
    def grade(self, c, img, lt):
        a = float(self.p["amount"]) * self.env(lt, 0.3, 0.3)
        tex = paper_tex(c.W, c.H, self.p["color"]); mul = tex / tex.mean(axis=(0, 1))
        warm = img * np.array([1.04, 1.0, 0.9], np.float32)
        g = to_gray(warm); warm = warm * 0.8 + g * 0.2
        grain = np.random.default_rng(int(c.t * 100)).normal(0, 7, (c.H, c.W, 1)).astype(np.float32)
        out = warm * mul + grain
        return img * (1 - a) + out * a

_vig = {}
@register
class ArchiveFilm(FX):
    name = "archive-film"; help = "Old archive-footage look: sepia/BW, grain, flicker, scratches, dust, gate weave (look: sepia|bw)"
    params = {"look": "sepia", "strength": 1.0}
    def grade(self, c, img, lt):
        a = self.env(lt, 0.15, 0.15) * float(self.p["strength"])
        fr = int(c.t * c.fps); r = np.random.default_rng(fr)
        g = to_gray(img); g = (g - 128) * 1.25 + 128
        g *= 1 + r.uniform(-0.06, 0.06)                                   # flicker
        if self.p["look"] == "sepia": g = g * np.array([1.07, 0.93, 0.74], np.float32) + np.array([10, 4, -6], np.float32)
        key = (c.W, c.H)
        if key not in _vig:
            yy, xx = np.mgrid[0:c.H, 0:c.W].astype(np.float32)
            _vig[key] = (1 - 0.55 * ((((xx / c.W - .5) * 2) ** 2 + ((yy / c.H - .5) * 2) ** 2) / 2) ** 1.2)[..., None]
        g = g * _vig[key]
        small = r.normal(0, 1, (c.H // 2, c.W // 2)).astype(np.float32)
        g += cv2.resize(small, (c.W, c.H))[..., None] * 14
        o = np.zeros((c.H, c.W), np.uint8)
        for _ in range(r.integers(0, 3)):                                 # scratches
            x = int(r.uniform(0, c.W)); cv2.line(o, (x, 0), (x + int(r.uniform(-8, 8)), c.H), 255, 1)
        for _ in range(r.integers(2, 9)):                                 # dust
            cv2.circle(o, (int(r.uniform(0, c.W)), int(r.uniform(0, c.H))), int(r.uniform(1, 4)), 255, -1)
        sc = o.astype(np.float32)[..., None] / 255
        g = g * (1 - sc * 0.8) + (r.uniform() > 0.5) * 230 * sc * 0.8
        return img * (1 - a) + np.clip(g, 0, 255) * a
    def post(self, c, img, lt):
        r = np.random.default_rng(int(c.t * c.fps) + 99); s = U(c) / 1080
        return affine(img, 1.02, c.W / 2, c.H / 2, c.W, c.H, r.normal(0, 1.2) * s, r.normal(0, 2.0) * s)

@register
class Parallax(FX):
    name = "parallax"; help = "2.5D Ken Burns: you push in faster than the background (great on photos)"
    params = {"bg_zoom": 1.05, "you_zoom": 1.16}
    def post(self, c, img, lt):
        q = ease_in_out(lt / self.dur)
        zb, zp = lerp(1, float(self.p["bg_zoom"]), q), lerp(1, float(self.p["you_zoom"]), q)
        cx, cy = c.face[0], c.face[1] + c.face[3] * 0.8
        bg = affine(img, zb, c.W / 2, c.H / 2, c.W, c.H)
        tx = (cx - c.W / 2) * zp - (cx - c.W / 2); ty = (cy - c.H / 2) * zp - (cy - c.H / 2)
        p = affine(img, zp, c.W / 2, c.H / 2, c.W, c.H, tx, ty)
        m = affine(np.repeat(c.mask[..., None], 3, 2), zp, c.W / 2, c.H / 2, c.W, c.H, tx, ty, border=cv2.BORDER_CONSTANT)
        return bg * (1 - m) + p * m

@register
class BlockWipe(FX):
    name = "block-wipe"; help = "Yellow + black blocks sweep across - a Vox-style transition (~0.6s, centre it on your cut)"
    params = {"colors": [YELLOW, INK], "direction": "right"}
    def top(self, c, canvas, lt):
        W, H = c.W, c.H; d = ImageDraw.Draw(canvas); cols = as_list(self.p["colors"]); n = len(cols)
        lag = self.dur * 0.18
        for k, col in enumerate(cols):
            p = ease_in_out((lt - k * lag) / max(0.05, self.dur - (n - 1) * lag))
            if p <= 0 or p >= 1: continue
            x0 = lerp(-W * 1.05, W * 1.05, p)
            if self.p["direction"] == "left": x0 = W - x0 - W
            d.rectangle((x0, 0, x0 + W, H), fill=rgba(col))

# ================================================================= TEXT effects
@register
class HighlightClip(FX):
    name = "highlight-clip"; help = "Newspaper clipping slides in, a yellow marker highlights the [key phrase]"
    params = {"source": "The Kathmandu Post", "headline": "Why prices keep rising",
              "body": "Economists say the [real reason prices keep rising] is not what most people think.",
              "date": "", "y": 0.72, "angle": -3}
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; u = U(c); cw = u * 0.84; pad = u * 0.05
        st = self.__dict__.setdefault("_st", {})
        if "base" not in st:
            src = T(self.p["source"].upper(), "serif", u * 0.032, INK)
            hd = marker_block([self.p["headline"]], "serif", u * 0.058, INK, YELLOW, 0, cw - pad * 2)
            ch = pad * 2.4 + src.height + hd.height + u * 0.04
            body_h = len(wrap(strip_hl(self.p["body"]), "serif", u * 0.04, cw - pad * 2)) * u * 0.058 + u * 0.03
            st["h"] = ch + body_h; st["hd"] = hd; st["src"] = src
        q = ease_out_cubic(lt / 0.45); ch = st["h"]
        cardi = paper_card(cw, ch, "#F4EFE3", 5, "tblr"); d = ImageDraw.Draw(cardi)
        paste(cardi, st["src"], pad, pad)
        if self.p.get("date"):
            dt = T(self.p["date"], "serif-italic", u * 0.028, GREY); paste(cardi, dt, cw - pad - dt.width, pad)
        y = pad + st["src"].height + u * 0.015
        d.line((pad, y, cw - pad, y), fill=rgba(INK), width=max(2, int(u * 0.003))); y += u * 0.02
        paste(cardi, st["hd"], pad - u * 0.01, y); y += st["hd"].height + u * 0.01
        hq = clamp((lt - 0.6) / max(0.4, min(1.2, self.dur * 0.35)))
        body = marker_block([self.p["body"]], "serif", u * 0.04, "#333333", YELLOW, ease_in_out(hq), cw - pad * 2)
        paste(cardi, body, pad - u * 0.01, y)
        im = rot(shadowed(cardi, int(u * 0.02), (0, int(u * 0.01)), 90), float(self.p["angle"]))
        yc = lerp(H + im.height / 2, H * float(self.p["y"]), q)
        paste(canvas, im, W / 2, yc, self.outa(lt, 0.3), center=True)
    def post(self, c, img, lt):                     # gentle push while reading
        return affine(img, 1 + 0.03 * ease_in_out(lt / self.dur), c.W / 2, c.H / 2, c.W, c.H)

@register
class MarkerText(FX):
    name = "marker-text"; help = "Key line on paper strips; [words] get a yellow highlighter swipe. | = new line"
    params = {"text": "This is the [real reason]|nobody talks about", "y": 0.78, "size": 0.075}
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; u = U(c); lines = as_list(self.p["text"]); sz = u * float(self.p["size"])
        hq = ease_in_out((lt - 0.35) / 0.6)
        def build(sz):
            out = []
            for i, ln in enumerate(lines):
                blk = marker_block([ln], "heavy", sz, INK, YELLOW, hq, u * 0.86 if H >= W else W * 0.8)
                strip = paper_card(blk.width + sz * 0.5, blk.height + sz * 0.35, "#FAF7EF", 11 + i, "lr")
                paste(strip, blk, sz * 0.25, sz * 0.17)
                out.append(rot(shadowed(strip, int(u * 0.012), (0, 4), 90), (-1.5 if i % 2 else 1.2)))
            return out
        strips = build(sz)
        room = H * (0.5 if W > H else 0.62)                     # keep the block clear of headlines and labels
        total = sum(st.height * 0.92 for st in strips)
        if total > room: strips = build(sz * room / total * 0.97)
        y = H * float(self.p["y"]) - sum(st.height * 0.92 for st in strips) / 2      # the block is centred on y
        for i, strip in enumerate(strips):
            q = ease_out_cubic((lt - i * 0.12) / 0.35)
            if q > 0:
                paste(canvas, strip, lerp(-strip.width, W / 2, q) if i % 2 == 0 else lerp(W + strip.width, W / 2, q), y + strip.height / 2,
                      self.outa(lt), center=True)
            y += strip.height * 0.92

@register
class TornHeadline(FX):
    name = "torn-headline"; help = "A torn paper strip with a yellow kicker and a bold headline slides in at the top"
    params = {"kicker": "EXPLAINED", "text": "Why Nepal's rupee is pegged to India", "y": 0.13}
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; u = U(c); q = ease_out_cubic(lt / 0.45)
        bw = u * 0.86 if H >= W else W * 0.7                     # landscape: wider, so the headline stays on one line
        lines = wrap(self.p["text"], "heavy", u * 0.068, bw - u * 0.04)
        hd = Image.new("RGBA", (int(bw), int(len(lines) * u * 0.085)), (0, 0, 0, 0))
        for i, ln in enumerate(lines): paste(hd, T(ln, "heavy", u * 0.068, INK), 0, i * u * 0.085)
        sw = W * 1.1; sh = hd.height + u * 0.16
        strip = paper_card(sw, sh, "#F6F1E6", 21, "tb")
        k = T(self.p["kicker"], "mono", u * 0.03, INK); kb = card(k.width + u * 0.03, k.height + u * 0.02, 0, rgba(YELLOW))
        paste(kb, k, u * 0.015, u * 0.01)
        x0 = (W - bw) / 2 + (sw - W) / 2
        paste(strip, kb, x0, u * 0.035); paste(strip, hd, x0, u * 0.035 + kb.height + u * 0.015)
        strip = rot(shadowed(strip, int(u * 0.015), (0, 6), 100), -1.5)
        paste(canvas, strip, lerp(-W, W / 2, q), H * float(self.p["y"]) + sh / 2 - u * 0.05, self.outa(lt), center=True)

@register
class ContextLabel(FX):
    name = "context-label"; help = "Typewriter place/date label bottom-left (e.g. 'KATHMANDU, 1990'), Vox lower-third"
    params = {"text": "KATHMANDU, 1990", "sub": "", "y": 0.88}
    def top(self, c, canvas, lt):
        W, H = c.W, c.H; u = U(c); txt = str(self.p["text"])
        n = int(len(txt) * clamp((lt - 0.15) / max(0.3, len(txt) * 0.045))); a = self.outa(lt)
        t = T(txt, "mono", u * 0.04, "#FFFFFF"); full = t.width
        x0 = W * 0.06 if W < H else W * 0.05; y0 = H * float(self.p["y"])
        bar = ease_out_cubic(lt / 0.2)
        paste(canvas, card(u * 0.014, t.height + u * 0.03, 0, rgba(YELLOW)), x0, y0 - u * 0.015, a * bar)
        if n > 0:
            tt = T(txt[:n], "mono", u * 0.04, "#FFFFFF")
            bx = card(tt.width + u * 0.04, t.height + u * 0.03, 0, rgba(INK, 235)); paste(bx, tt, u * 0.02, u * 0.015)
            paste(canvas, bx, x0 + u * 0.022, y0 - u * 0.015, a)
        if self.p.get("sub") and lt > 0.3 + len(txt) * 0.045:
            s = T(self.p["sub"], "mono", u * 0.028, INK); sb = card(s.width + u * 0.03, s.height + u * 0.02, 0, rgba(YELLOW))
            paste(sb, s, u * 0.015, u * 0.01); paste(canvas, sb, x0 + u * 0.022, y0 + t.height + u * 0.025, a)

@register
class QuoteCard(FX):
    name = "quote-card"; help = "Full-screen paper quote: words appear one by one, [words] get highlighted, then the attribution"
    params = {"quote": "The [economy] is not the [stock market].", "by": "— Someone, 2024", "color": PAPER}
    def grade(self, c, img, lt):
        W, H = c.W, c.H; u = U(c); a = full_alpha(lt, self.dur, 0.25, 0.25)
        base = Image.fromarray(paper_tex(W, H, self.p["color"]).astype(np.uint8)).convert("RGBA")
        paste(base, T("“", "serif", u * 0.4, YELLOW), W * 0.08, H * 0.22 - u * 0.15)
        words = str(self.p["quote"]).split(); k = int(len(words) * clamp((lt - 0.2) / max(0.4, self.dur * 0.45))) + 1
        shown = " ".join(words[:min(len(words), k)])
        if shown.count("[") > shown.count("]"): shown += "]"
        hq = clamp((lt - self.dur * 0.55) / 0.6)
        blk = marker_block([shown], "serif", u * 0.075, INK, YELLOW, ease_in_out(hq), W * 0.82)
        paste(base, blk, W * 0.09, H * 0.32)
        if lt > self.dur * 0.6:
            paste(base, T(self.p["by"], "mono", u * 0.032, "#444444"), W * 0.1, H * 0.32 + blk.height + u * 0.06, clamp((lt - self.dur * 0.6) / 0.3))
        q = np.asarray(base.convert("RGB"), np.float32)
        return img * (1 - a) + q * a

# ================================================================= DATA effects
def chart_card(c, w, h, title, source):
    u = U(c); cardi = paper_card(w, h, "#F7F3EA", 13, "tb")
    paste(cardi, T(title, "heavy", fit_size(title, "heavy", w - u * 0.1, u * 0.05), INK), u * 0.05, u * 0.05)
    if source: paste(cardi, T("Source: " + source, "mono", u * 0.022, GREY), u * 0.05, h - u * 0.06)
    return cardi

@register
class VoxBars(FX):
    name = "vox-bars"; help = "Horizontal bar chart on paper; bars grow, values count up, one bar highlighted yellow"
    params = {"title": "Remittance share of GDP", "labels": ["Nepal", "India", "Bangladesh"], "values": [26, 3, 5],
              "suffix": "%", "highlight": 0, "source": "World Bank", "y": 0.7}
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; u = U(c); labs = as_list(self.p["labels"]); vals = [float(v) for v in self.p["values"]]
        n = len(vals); w = u * 0.86; rowh = u * 0.085; h = u * 0.2 + n * rowh
        cardi = chart_card(c, w, h, self.p["title"], self.p.get("source")); d = ImageDraw.Draw(cardi)
        vmax = max(vals) or 1; lx = u * 0.05; bx = u * 0.27; bw = w - bx - u * 0.15
        for i, (lab, v) in enumerate(zip(labs, vals)):
            q = ease_out_cubic((lt - 0.3 - i * 0.12) / 0.7); y = u * 0.13 + i * rowh
            paste(cardi, T(lab, "bold", u * 0.032, INK), lx, y + rowh * 0.18)
            col = YELLOW if i == int(self.p["highlight"]) else "#2B2B2B"
            if q > 0:
                d.rectangle((bx, y + rowh * 0.12, bx + max(2, bw * v / vmax * q), y + rowh * 0.78), fill=rgba(col))
                val = v * q; s = (f"{val:.1f}" if v != int(v) else f"{int(round(val))}") + str(self.p["suffix"])
                paste(cardi, T(s, "bold", u * 0.03, INK), bx + bw * v / vmax * q + u * 0.015, y + rowh * 0.2)
        im = shadowed(cardi, int(u * 0.02), (0, 8), 90)
        paste(canvas, im, W / 2, lerp(H + h, H * float(self.p["y"]), ease_out_cubic(lt / 0.4)), self.outa(lt), center=True)

@register
class VoxLine(FX):
    name = "vox-line"; help = "Line chart draws itself on paper, a yellow dot rides the tip, end value pops"
    params = {"title": "Price of rice (Rs/kg)", "values": [40, 42, 47, 55, 61, 78, 92], "labels": ["2015", "2025"],
              "prefix": "Rs ", "suffix": "", "source": "", "y": 0.7, "color": RED}
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; u = U(c); vals = [float(v) for v in self.p["values"]]; w = u * 0.86; h = u * 0.62
        cardi = chart_card(c, w, h, self.p["title"], self.p.get("source")); d = ImageDraw.Draw(cardi)
        x0, x1, y0, y1 = u * 0.07, w - u * 0.2, u * 0.15, h - u * 0.12
        for k in range(4):
            yy = lerp(y0, y1, k / 3); d.line((x0, yy, x1, yy), fill=(0, 0, 0, 35), width=1)
        d.line((x0, y1, x1, y1), fill=rgba(INK), width=max(2, int(u * 0.003)))
        labs = as_list(self.p["labels"])
        if labs:
            paste(cardi, T(labs[0], "mono", u * 0.024, GREY), x0, y1 + u * 0.012)
            lb = T(labs[-1], "mono", u * 0.024, GREY); paste(cardi, lb, x1 - lb.width, y1 + u * 0.012)
        lo, hi = min(vals), max(vals); rng = (hi - lo) or 1
        pts = [(lerp(x0, x1, i / max(1, len(vals) - 1)), lerp(y1 - u * 0.02, y0 + u * 0.03, (v - lo) / rng)) for i, v in enumerate(vals)]
        q = ease_in_out((lt - 0.35) / max(0.5, self.dur * 0.55)); seg = q * (len(pts) - 1)
        k = int(seg); fr = seg - k; path = pts[:k + 1]
        if k + 1 < len(pts): path = path + [(lerp(pts[k][0], pts[k + 1][0], fr), lerp(pts[k][1], pts[k + 1][1], fr))]
        if len(path) > 1: d.line(path, fill=rgba(self.p["color"]), width=max(3, int(u * 0.008)), joint="curve")
        if q > 0:
            tx, ty = path[-1]; r = u * 0.016 * (1 + 0.15 * math.sin(lt * 8))
            d.ellipse((tx - r, ty - r, tx + r, ty + r), fill=rgba(YELLOW), outline=rgba(INK), width=max(2, int(u * 0.003)))
            cur = vals[min(len(vals) - 1, int(round(seg)))] if q < 1 else vals[-1]
            s = f"{self.p['prefix']}{count_fmt(cur)}{self.p['suffix']}"
            lab = T(s, "bold", u * 0.034, INK); lb = card(lab.width + u * 0.02, lab.height + u * 0.016, u * 0.006, rgba(YELLOW))
            paste(lb, lab, u * 0.01, u * 0.008); paste(cardi, lb, min(tx + u * 0.025, w - lb.width - u * 0.01), ty - lb.height / 2)
        im = shadowed(cardi, int(u * 0.02), (0, 8), 90)
        paste(canvas, im, W / 2, lerp(H + h, H * float(self.p["y"]), ease_out_cubic(lt / 0.4)), self.outa(lt), center=True)

@register
class BigNumber(FX):
    name = "big-number"; help = "A huge number counts up on a paper card with a label and a yellow underline"
    params = {"value": 3000000, "prefix": "", "suffix": "", "label": "Nepalis work abroad", "y": 0.72, "fmt": "{:,}"}
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; u = U(c); q = ease_out_cubic((lt - 0.2) / max(0.6, self.dur * 0.5))
        v = float(self.p["value"]) * q; s = f"{self.p['prefix']}{count_fmt(int(round(v)) if float(self.p['value']).is_integer() else round(v, 1), self.p['fmt'])}{self.p['suffix']}"
        full = f"{self.p['prefix']}{count_fmt(self.p['value'], self.p['fmt'])}{self.p['suffix']}"
        sz = fit_size(full, "display", u * 0.74, u * 0.16)
        num = T(s, "display", sz, INK); lab = T(self.p["label"], "bold", fit_size(self.p["label"], "bold", u * 0.74, u * 0.045), "#333333")
        w = u * 0.86; h = sz * 1.25 + lab.height + u * 0.12
        cardi = paper_card(w, h, "#F7F3EA", 17, "tb"); d = ImageDraw.Draw(cardi)
        paste(cardi, num, w / 2, u * 0.05 + sz * 0.6, center=True)
        uq = ease_in_out((lt - 0.4) / 0.5); uy = u * 0.06 + sz * 1.15
        if uq > 0: d.rectangle((w / 2 - u * 0.3, uy, w / 2 - u * 0.3 + u * 0.6 * uq, uy + u * 0.018), fill=rgba(YELLOW))
        paste(cardi, lab, w / 2, uy + u * 0.03 + lab.height / 2, center=True)
        im = scale_img(shadowed(cardi, int(u * 0.02), (0, 8), 90), lerp(0.85, 1, ease_out_back(lt / 0.4)))
        paste(canvas, im, W / 2, H * float(self.p["y"]), self.env(lt, 0.2, 0.25), center=True)

@register
class VoxTimeline(FX):
    name = "vox-timeline"; help = "Paper timeline: a yellow marker steps through years, each event label pops above it"
    params = {"years": ["1990", "2006", "2008", "2015"], "events": ["Democracy restored", "Peace deal", "Republic", "New constitution"],
              "y": 0.8, "active": None}
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; u = U(c); ys = as_list(self.p["years"]); ev = as_list(self.p["events"]); n = len(ys)
        bw = W * 1.04; bh = u * 0.2; band = paper_card(bw, bh, "#F7F3EA", 23, "tb"); d = ImageDraw.Draw(band)
        x0, x1, ly = W * 0.1 + W * 0.02, W * 0.9 + W * 0.02, bh * 0.42
        q = ease_out_cubic(lt / 0.5); d.line((x0, ly, lerp(x0, x1, q), ly), fill=rgba(INK), width=max(3, int(u * 0.005)))
        xs = [lerp(x0, x1, i / max(1, n - 1)) for i in range(n)]
        act = self.p["active"]
        pos = float(act) if act is not None else clamp((lt - 0.5) / max(0.3, self.dur - 0.9)) * (n - 1)
        for i, (x, yr) in enumerate(zip(xs, ys)):
            if q * (n - 1) + 0.01 < i: continue
            r = u * 0.012; d.ellipse((x - r, ly - r, x + r, ly + r), fill=rgba(INK))
            t = T(yr, "mono", u * 0.03, INK if abs(pos - i) < 0.5 else GREY); paste(band, t, x, ly + u * 0.05, center=True)
        mx = lerp(xs[0], xs[-1], pos / max(1, n - 1)); r = u * 0.024
        d.ellipse((mx - r, ly - r, mx + r, ly + r), fill=rgba(YELLOW), outline=rgba(INK), width=max(2, int(u * 0.004)))
        by = H * float(self.p["y"])
        paste(canvas, shadowed(band, int(u * 0.015), (0, 6), 90), W / 2, by, self.outa(lt), center=True)
        k = int(round(pos))
        if 0 <= k < len(ev) and lt > 0.45:
            t = T(ev[k], "bold", fit_size(ev[k], "bold", u * 0.7, u * 0.042), "#FFFFFF")
            bx = card(t.width + u * 0.05, t.height + u * 0.035, u * 0.01, rgba(INK, 240)); paste(bx, t, u * 0.025, u * 0.0175)
            mxc = clamp(mx - W * 0.02 + (W - bw) / 2 + (bw - W) / 2, bx.width / 2 + 8, W - bx.width / 2 - 8)
            pop = ease_out_back(clamp((pos - k + 0.5) * 3)) if act is None else 1
            paste(canvas, scale_img(bx, max(0.3, pop)), mxc, by - bh / 2 - bx.height * 0.7, self.outa(lt), center=True)

# ================================================================= FULL-SCREEN cutaways
_maps = {}
def make_map(W, H, seed=11):
    key = (W, H, seed)
    if key in _maps: return _maps[key]
    r = np.random.default_rng(seed); n = np.zeros((H, W), np.float32)
    for s, amp in ((6, 1.0), (14, 0.5), (34, 0.25), (80, 0.12)):
        n += cv2.resize(r.normal(0, 1, (s, max(2, int(s * W / H)))).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC) * amp
    land = (n > -0.15).astype(np.uint8)
    water = np.array([168, 196, 214], np.float32); ground = np.array([233, 226, 205], np.float32)
    img = np.where(land[..., None] == 1, ground, water)
    img += cv2.GaussianBlur(n, (0, 0), 3)[..., None] * 6 * land[..., None]
    coast = cv2.morphologyEx(land, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)).astype(np.float32)
    img = img * (1 - coast[..., None] * 0.6) + np.array([90, 110, 125], np.float32) * coast[..., None] * 0.6
    pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA"); d = ImageDraw.Draw(pil)
    step = int(min(W, H) / 8)
    for x in range(0, W, step): d.line((x, 0, x, H), fill=(255, 255, 255, 60), width=1)
    for y in range(0, H, step): d.line((0, y, W, y), fill=(255, 255, 255, 60), width=1)
    rr = random.Random(seed)
    for _ in range(14):                          # borders / roads
        x, y = rr.uniform(0, W), rr.uniform(0, H); pts = [(x, y)]
        for _ in range(8):
            x += rr.uniform(-W * 0.08, W * 0.08); y += rr.uniform(-H * 0.06, H * 0.06); pts.append((x, y))
        d.line(pts, fill=(150, 140, 120, 120), width=max(1, W // 600))
    out = np.asarray(pil.convert("RGB"), np.float32); _maps[key] = out
    return out

@register
class MapPin(FX):
    name = "map-pin"; help = "Cut to a map: camera zooms to a pin that drops in with a place label (image = your own map screenshot)"
    params = {"place": "KATHMANDU", "sub": "Nepal", "image": None, "x": 0.56, "y": 0.44, "zoom": 2.2}
    def _base(self, c):
        st = self.__dict__.setdefault("_st", {})
        if "m" not in st:
            if self.p["image"] and os.path.exists(str(self.p["image"])):
                st["m"] = np.asarray(load_images([self.p["image"]], 1, c.W, c.H)[0].convert("RGB"), np.float32)
            else:
                st["m"] = make_map(c.W, c.H)
        return st["m"]
    def _z(self, lt): return lerp(1, float(self.p["zoom"]), ease_in_out(lt / max(0.6, self.dur * 0.7)))
    def grade(self, c, img, lt):
        m = self._base(c); px, py = c.W * float(self.p["x"]), c.H * float(self.p["y"]); z = self._z(lt)
        v = affine(m, z, lerp(c.W / 2, px, clamp(z - 1)), lerp(c.H / 2, py, clamp(z - 1)), c.W, c.H)
        q = ease_out_cubic(lt / 0.35) * self.outa(lt, 0.3); edge = int(c.H * (1 - q))
        out = img.copy(); out[edge:] = v[edge:]
        return out
    def top(self, c, canvas, lt):
        u = U(c); px, py = c.W * float(self.p["x"]), c.H * float(self.p["y"]); z = self._z(lt); k = clamp(z - 1)
        cx, cy = lerp(c.W / 2, px, k), lerp(c.H / 2, py, k)
        sx, sy = c.W / 2 + (px - cx) * z, c.H / 2 + (py - cy) * z
        dq = ease_out_back((lt - self.dur * 0.45) / 0.35)
        if dq <= 0: return
        a = self.outa(lt, 0.3); d = ImageDraw.Draw(canvas)
        pr = ((lt * 1.2) % 1); R = u * (0.03 + 0.09 * pr)
        d.ellipse((sx - R, sy - R * 0.45, sx + R, sy + R * 0.45), outline=rgba(RED, 200 * (1 - pr) * a), width=max(2, int(u * 0.004)))
        r = u * 0.035; hy = sy - r * 2.6 - (1 - min(1, dq)) * u * 0.15
        pin = Image.new("RGBA", (int(r * 2.4), int(r * 3.4)), (0, 0, 0, 0)); pd = ImageDraw.Draw(pin); cx0 = pin.width / 2
        pd.polygon([(cx0 - r * 0.8, r * 1.5), (cx0 + r * 0.8, r * 1.5), (cx0, r * 3.3)], fill=rgba(RED))
        pd.ellipse((cx0 - r, r * 0.2, cx0 + r, r * 2.2), fill=rgba(RED)); pd.ellipse((cx0 - r * 0.4, r * 0.8, cx0 + r * 0.4, r * 1.6), fill=(255, 255, 255, 255))
        paste(canvas, shadowed(pin, 6, (0, 4), 120), sx, hy + pin.height / 2 - r * 0.2, a, center=True)
        lq = ease_out_cubic((lt - self.dur * 0.55) / 0.3)
        if lq > 0:
            t = T(self.p["place"], "heavy", u * 0.05, "#FFFFFF"); bx = card(t.width + u * 0.05, t.height + u * 0.035, 0, rgba(INK)); paste(bx, t, u * 0.025, u * 0.0175)
            lx = clamp(sx + r * 1.5, 8, c.W - bx.width - 8); ly = sy - r * 4.2
            paste(canvas, bx, lx, ly, a * lq)
            if self.p.get("sub"):
                s = T(self.p["sub"], "mono", u * 0.03, INK); sb = card(s.width + u * 0.03, s.height + u * 0.02, 0, rgba(YELLOW)); paste(sb, s, u * 0.015, u * 0.01)
                paste(canvas, sb, lx, ly + bx.height, a * lq)

@register
class DocReveal(FX):
    name = "doc-reveal"; help = "Cut to a document; camera pushes in while a red marker circles the key part (image = your screenshot)"
    params = {"image": None, "title": "OFFICIAL REPORT", "circle": [0.18, 0.46, 0.64, 0.1], "note": "this part!", "zoom": 1.5}
    def grade(self, c, img, lt):
        W, H = c.W, c.H; u = U(c); st = self.__dict__.setdefault("_st", {})
        if "page" not in st:
            bg = Image.fromarray(paper_tex(W, H, "#D9D2C2", 31).astype(np.uint8)).convert("RGBA")
            pw, ph = W * 0.84, H * 0.84
            if self.p["image"] and os.path.exists(str(self.p["image"])):
                pg = load_images([self.p["image"]], 1, pw, ph)[0]
            else:
                pg = paper_img(pw, ph, "#FBFAF6", 41); d = ImageDraw.Draw(pg); rr = random.Random(2)
                paste(pg, T(self.p["title"], "serif", fit_size(self.p["title"], "serif", pw * 0.8, u * 0.06), INK), pw * 0.08, ph * 0.06)
                d.line((pw * 0.08, ph * 0.13, pw * 0.92, ph * 0.13), fill=rgba(INK), width=2); y = ph * 0.17
                while y < ph * 0.92:
                    L = pw * rr.uniform(0.55, 0.84) if rr.random() > 0.15 else pw * 0.3
                    d.rounded_rectangle((pw * 0.08, y, pw * 0.08 + L, y + u * 0.014), radius=4, fill=(60, 60, 60, 150))
                    y += u * 0.036 + (u * 0.03 if rr.random() < 0.12 else 0)
            st["page"] = (bg, pg, (W - pw) / 2, (H - ph) / 2, pw, ph)
        bg, pg, ox, oy, pw, ph = st["page"]; base = bg.copy(); paste(base, shadowed(pg, int(u * 0.02), (0, 10), 110), ox - u * 0.04, oy - u * 0.04 + 10 * 0)
        cx_, cy_, cw_, ch_ = [float(v) for v in self.p["circle"]]
        ex0, ey0 = ox + cx_ * pw, oy + cy_ * ph; ex1, ey1 = ex0 + cw_ * pw, ey0 + ch_ * ph
        cq = ease_in_out((lt - self.dur * 0.35) / 0.6)
        if cq > 0:
            d = ImageDraw.Draw(base); m = u * 0.03
            d.arc((ex0 - m, ey0 - m, ex1 + m, ey1 + m), -100, -100 + 380 * cq, fill=rgba(RED), width=max(4, int(u * 0.009)))
        if cq >= 1 and self.p.get("note"):
            t = T(self.p["note"], "marker", u * 0.06, RED); paste(base, rot(t, -6), (ex0 + ex1) / 2, ey1 + u * 0.1, clamp((lt - self.dur * 0.35 - 0.6) / 0.25), center=True)
        arr = np.asarray(base.convert("RGB"), np.float32)
        z = lerp(1, float(self.p["zoom"]), ease_in_out(lt / self.dur))
        k = clamp((z - 1) / max(0.01, float(self.p["zoom"]) - 1))
        arr = affine(arr, z, lerp(W / 2, (ex0 + ex1) / 2, k), lerp(H / 2, (ey0 + ey1) / 2 + u * 0.04, k), W, H, border=cv2.BORDER_REPLICATE)
        a = full_alpha(lt, self.dur, 0.2, 0.2)
        return img * (1 - a) + arr * a

@register
class PhotoDrop(FX):
    name = "photo-drop"; help = "Taped archive photos drop onto the wall behind you, one by one, with typed captions"
    params = {"images": None, "captions": ["1990", "2006", "2015"], "count": 3, "sepia": True}
    def behind(self, c, canvas, lt):
        W, H = c.W, c.H; u = U(c); n = int(self.p["count"]); caps = as_list(self.p["captions"])
        st = self.__dict__.setdefault("_st", {})
        if "ims" not in st:
            pw = u * 0.36; ims = load_images(self.p["images"], n, pw, pw * 0.78, labels=caps)
            out = []
            for i, im in enumerate(ims):
                if self.p["sepia"]:
                    a = np.asarray(im.convert("RGB"), np.float32); g = to_gray(a) * np.array([1.07, 0.93, 0.76], np.float32)
                    im = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).convert("RGBA")
                fr = Image.new("RGBA", (int(pw + u * 0.04), int(pw * 0.78 + u * 0.1)), (250, 248, 240, 255)); paste(fr, im, u * 0.02, u * 0.02)
                if i < len(caps): paste(fr, T(caps[i], "mono", u * 0.026, INK), fr.width / 2, pw * 0.78 + u * 0.06, center=True)
                paste(fr, tape(u * 0.14, random.Random(i).uniform(-8, 8)), fr.width / 2, u * 0.005, center=True)
                out.append(fr)
            st["ims"] = out
        spots = [(0.24, 0.2, -7), (0.76, 0.18, 6), (0.5, 0.08, -2), (0.2, 0.42, 4), (0.8, 0.42, -5), (0.5, 0.3, 3)]
        for i, im in enumerate(st["ims"]):
            q = (lt - 0.15 - i * min(0.45, self.dur * 0.6 / max(1, n))) / 0.3
            if q <= 0: continue
            sx, sy, ang = spots[i % len(spots)]
            s = lerp(1.35, 1, ease_out_cubic(q))
            paste(canvas, rot(shadowed(scale_img(im, s), int(u * 0.015), (0, 6), 110), ang), W * sx, H * sy + im.height * 0.25,
                  clamp(q * 2) * self.outa(lt), center=True)

# ================================================================= more Vox staples
def doc_page(c, pw, ph, title, seed=2):
    """generated document page: title, rule, grey text lines. returns (page, list of line boxes)."""
    u = U(c); pg = paper_img(pw, ph, "#FBFAF6", 41); d = ImageDraw.Draw(pg); rr = random.Random(seed)
    paste(pg, T(title, "serif", fit_size(title, "serif", pw * 0.8, u * 0.06), INK), pw * 0.08, ph * 0.06)
    d.line((pw * 0.08, ph * 0.13, pw * 0.92, ph * 0.13), fill=rgba(INK), width=2); y = ph * 0.17; boxes = []
    while y < ph * 0.92:
        L = pw * rr.uniform(0.55, 0.84) if rr.random() > 0.15 else pw * 0.3
        d.rounded_rectangle((pw * 0.08, y, pw * 0.08 + L, y + u * 0.014), radius=4, fill=(60, 60, 60, 150))
        boxes.append((pw * 0.08, y, pw * 0.08 + L, y + u * 0.014))
        y += u * 0.036 + (u * 0.03 if rr.random() < 0.12 else 0)
    return pg, boxes

@register
class ArrowCallout(FX):
    name = "arrow-callout"; help = "Hand-drawn arrow draws itself to a point (x,y 0-1) with a marker label - point at anything"
    params = {"text": "look here", "x": 0.5, "y": 0.45, "from_x": 0.2, "from_y": 0.7, "color": RED}
    def top(self, c, canvas, lt):
        W, H = c.W, c.H; u = U(c); col = rgba(self.p["color"]); a = self.outa(lt)
        if a < 1: col = col[:3] + (int(255 * a),)
        p0 = (W * float(self.p["from_x"]), H * float(self.p["from_y"])); p1 = (W * float(self.p["x"]), H * float(self.p["y"]))
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2; nx, ny = -(p1[1] - p0[1]), p1[0] - p0[0]
        ctrl = (mx + nx * 0.25, my + ny * 0.25); q = ease_in_out((lt - 0.15) / 0.5)
        pts = []
        for i in range(31):
            t = i / 30 * q
            pts.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * ctrl[0] + t * t * p1[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * ctrl[1] + t * t * p1[1]))
        d = ImageDraw.Draw(canvas); lw = max(4, int(u * 0.01))
        if q > 0.02: d.line(pts, fill=col, width=lw, joint="curve")
        if q > 0.98:
            ang = math.atan2(pts[-1][1] - pts[-4][1], pts[-1][0] - pts[-4][0]); hl = u * 0.05
            for s in (-1, 1):
                d.line([p1, (p1[0] - hl * math.cos(ang + s * 0.5), p1[1] - hl * math.sin(ang + s * 0.5))], fill=col, width=lw)
        t = T(self.p["text"], "marker", u * 0.06, self.p["color"])
        lab = card(t.width + u * 0.05, t.height + u * 0.04, u * 0.01, (250, 247, 238, 240)); paste(lab, t, u * 0.025, u * 0.02)
        paste(canvas, rot(shadowed(lab, int(u * 0.01), (0, 4), 90), -4), p0[0], p0[1] + (u * 0.06 if p0[1] > p1[1] else -u * 0.06), clamp(lt / 0.2) * a, center=True)

@register
class Redact(FX):
    name = "redact"; help = "Cut to a document; black redaction bars swipe over lines, then a stamp lands (image = your screenshot)"
    params = {"image": None, "title": "CONFIDENTIAL MEMO", "lines": [2, 3, 6, 9, 10], "stamp": "CLASSIFIED"}
    def grade(self, c, img, lt):
        W, H = c.W, c.H; u = U(c); st = self.__dict__.setdefault("_st", {})
        pw, ph = W * 0.84, H * 0.84; ox, oy = (W - pw) / 2, (H - ph) / 2
        if "pg" not in st:
            st["bg"] = Image.fromarray(paper_tex(W, H, "#D9D2C2", 33).astype(np.uint8)).convert("RGBA")
            if self.p["image"] and os.path.exists(str(self.p["image"])):
                st["pg"] = load_images([self.p["image"]], 1, pw, ph)[0]
                st["boxes"] = [(pw * 0.08, ph * (0.2 + i * 0.06), pw * 0.9, ph * (0.2 + i * 0.06) + u * 0.03) for i in range(12)]
            else:
                st["pg"], st["boxes"] = doc_page(c, pw, ph, self.p["title"], 5)
        pg = st["pg"].copy(); d = ImageDraw.Draw(pg); idx = [int(i) for i in as_list(self.p["lines"]) if int(i) < len(st["boxes"])]
        for k, i in enumerate(idx):
            q = ease_in_out((lt - 0.4 - k * 0.22) / 0.3)
            if q <= 0: continue
            x0, y0, x1, y1 = st["boxes"][i]; pad = u * 0.008
            d.rectangle((x0 - pad, y0 - pad, x0 + (x1 - x0 + pad * 2) * q - pad, y1 + pad), fill=(12, 12, 12, 255))
        base = st["bg"].copy(); paste(base, shadowed(pg, int(u * 0.02), (0, 10), 110), ox - u * 0.04, oy - u * 0.04)
        sq = (lt - 0.6 - len(idx) * 0.22) / 0.3
        if self.p.get("stamp") and sq > 0:
            t = T(self.p["stamp"], "display", u * 0.11, RED); bx = card(t.width + u * 0.06, t.height + u * 0.05, u * 0.015, (0, 0, 0, 0), rgba(RED), max(5, int(u * 0.01)))
            paste(bx, t, u * 0.03, u * 0.025)
            paste(base, rot(scale_img(bx, lerp(1.8, 1, ease_out_cubic(sq))), 12), W / 2, H * 0.62, clamp(sq * 2) * 0.88, center=True)
        a = full_alpha(lt, self.dur, 0.2, 0.2)
        return img * (1 - a) + np.asarray(base.convert("RGB"), np.float32) * a

@register
class CompareSplit(FX):
    name = "compare-split"; help = "Full-screen A vs B on paper: two halves, numbers count up, the bigger side gets a yellow bar"
    params = {"left": "NEPAL", "right": "INDIA", "left_value": 1400, "right_value": 2500, "prefix": "$", "suffix": "",
              "note": "GDP per person", "source": ""}
    def grade(self, c, img, lt):
        W, H = c.W, c.H; u = U(c); a = full_alpha(lt, self.dur, 0.2, 0.2)
        base = Image.fromarray(paper_tex(W, H, PAPER, 51).astype(np.uint8)).convert("RGBA"); d = ImageDraw.Draw(base)
        vert = H > W; q = ease_out_cubic((lt - 0.3) / max(0.6, self.dur * 0.45))
        lv, rv = float(self.p["left_value"]), float(self.p["right_value"]); mx = max(lv, rv) or 1
        halves = [((0, 0, W, H / 2) if vert else (0, 0, W / 2, H)), ((0, H / 2, W, H) if vert else (W / 2, 0, W, H))]
        d.rectangle(halves[1], fill=(226, 219, 202, 255))
        for (x0, y0, x1, y1), name, v in zip(halves, (self.p["left"], self.p["right"]), (lv, rv)):
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            paste(base, T(name, "heavy", fit_size(name, "heavy", (x1 - x0) * 0.8, u * 0.07), INK), cx, cy - u * 0.14, center=True)
            s = f"{self.p['prefix']}{count_fmt(int(round(v * q)))}{self.p['suffix']}"
            full = f"{self.p['prefix']}{count_fmt(int(v))}{self.p['suffix']}"
            paste(base, T(s, "display", fit_size(full, "display", (x1 - x0) * 0.8, u * 0.15), INK), cx, cy + u * 0.01, center=True)
            bw = (x1 - x0) * 0.7 * v / mx * q
            d.rectangle((cx - (x1 - x0) * 0.35, cy + u * 0.11, cx - (x1 - x0) * 0.35 + bw, cy + u * 0.135), fill=rgba(YELLOW if v == mx else INK))
        vs = card(u * 0.14, u * 0.14, u * 0.07, rgba(INK)); paste(vs, T("VS", "display", u * 0.06, "#FFFFFF"), u * 0.07, u * 0.07, center=True)
        paste(base, scale_img(vs, max(0.05, ease_out_back(lt / 0.4))), W / 2, H / 2, center=True)
        if self.p.get("note"):
            n = T(self.p["note"], "mono", u * 0.032, INK); nb = card(n.width + u * 0.03, n.height + u * 0.02, 0, rgba(YELLOW)); paste(nb, n, u * 0.015, u * 0.01)
            paste(base, nb, W / 2, H * 0.06 if vert else H * 0.08, center=True)
        if self.p.get("source"): paste(base, T("Source: " + self.p["source"], "mono", u * 0.022, GREY), u * 0.04, H - u * 0.06)
        return img * (1 - a) + np.asarray(base.convert("RGB"), np.float32) * a

@register
class IconArray(FX):
    name = "icon-array" ; help = "Grid of people icons; some turn yellow one by one ('1 in 4 households...')"
    params = {"total": 100, "highlight": 25, "cols": 10, "label": "1 in 4 households has someone abroad", "y": None}
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; u = U(c); n = int(self.p["total"]); k = int(self.p["highlight"]); cols = int(self.p["cols"])
        rows = math.ceil(n / cols); w = u * 0.86; lab_h = u * 0.09
        cell = min((w - u * 0.1) / cols, (H * (0.4 if H > W else 0.62) - u * 0.1 - lab_h) / rows)            # keep the card under ~40% of the frame
        lab = T(self.p["label"], "bold", fit_size(self.p["label"], "bold", w - u * 0.1, u * 0.04), INK)
        w = max(cols * cell, lab.width) + u * 0.1
        h = rows * cell + u * 0.1 + lab_h; cardi = paper_card(w, h, "#F7F3EA", 29, "tb"); d = ImageDraw.Draw(cardi)
        q = clamp((lt - 0.5) / max(0.6, self.dur * 0.5)); lit = int(k * q)
        for i in range(n):
            r_, c_ = divmod(i, cols); x = (w - cols * cell) / 2 + c_ * cell + cell / 2; y = u * 0.05 + r_ * cell + cell / 2
            if ease_out_cubic((lt - i * 0.004) / 0.25) <= 0: continue
            col = rgba(YELLOW) if i < lit else (60, 60, 60, 200); s = cell * 0.37
            d.ellipse((x - s * 0.32, y - s * 0.95, x + s * 0.32, y - s * 0.3), fill=col)
            d.rounded_rectangle((x - s * 0.5, y - s * 0.22, x + s * 0.5, y + s * 0.95), radius=s * 0.3, fill=col)
            if i < lit: d.rounded_rectangle((x - s * 0.5, y - s * 0.22, x + s * 0.5, y + s * 0.95), radius=s * 0.3, outline=rgba(INK), width=2)
        paste(cardi, lab, w / 2, h - lab_h / 2 - u * 0.02, center=True)
        yc = H * float(self.p["y"]) if self.p["y"] is not None else H - h / 2 - H * 0.04
        paste(canvas, shadowed(cardi, int(u * 0.02), (0, 8), 90), W / 2, lerp(H + h, yc, ease_out_cubic(lt / 0.4)), self.outa(lt), center=True)

@register
class SourceTag(FX):
    name = "source-tag"; help = "Small 'Source: ...' citation chip in the bottom corner (keep it on while a fact is shown)"
    params = {"text": "Source: World Bank, 2024", "corner": "right", "y": 0.955}
    def top(self, c, canvas, lt):
        u = U(c); t = T(self.p["text"], "mono", u * 0.024, INK); bx = card(t.width + u * 0.03, t.height + u * 0.02, 0, (247, 243, 234, 230))
        paste(bx, t, u * 0.015, u * 0.01)
        x = c.W - bx.width - u * 0.04 if self.p["corner"] == "right" else u * 0.04
        paste(canvas, bx, x, c.H * float(self.p["y"]) - bx.height, self.env(lt, 0.2, 0.2))

if __name__ == "__main__":
    fx.main()
