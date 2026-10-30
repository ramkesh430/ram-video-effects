#!/usr/bin/env python3
"""
fxkit - talking-head video effects (Ram's version)

  python fx.py IN.mp4 OUT.mp4 --plan plan.json        # full render (audio kept)
  python fx.py IN.mp4 prev.png --plan plan.json --preview 1.5,3 [--debug]   # check frames
  python fx.py --list                                 # all effects + params

plan.json = list of effects: [{"fx":"orbit","start":3,"end":6,"items":["A","B"]}, ...]
Needs: numpy, opencv-python, pillow, mediapipe, ffmpeg. Models in ~/.cache/fxkit (*selfie*.tflite, *face*.tflite)
"""
import argparse, glob, json, math, os, random, subprocess, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CACHE = os.path.expanduser("~/.cache/fxkit")

# ================================================================= math / easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))
def lerp(a, b, t):
    return a + (b - a) * t
def ease_out_cubic(x):
    x = clamp(x); return 1 - (1 - x) ** 3
def ease_in_cubic(x):
    x = clamp(x); return x ** 3
def ease_in_out(x):
    x = clamp(x); return 3 * x * x - 2 * x * x * x
def ease_out_back(x, s=1.70158):
    x = clamp(x); c3 = s + 1
    return 1 + c3 * (x - 1) ** 3 + s * (x - 1) ** 2
def ease_out_elastic(x):
    x = clamp(x)
    if x in (0, 1): return x
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi) / 3) + 1
def hex2rgb(h):
    if isinstance(h, (list, tuple)): return tuple(h[:3])
    h = h.lstrip("#")
    if len(h) == 3: h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def rgba(h, a=255):
    return hex2rgb(h) + (int(a),)
def as_list(v, sep="|"):
    if v is None: return []
    if isinstance(v, (list, tuple)): return list(v)
    return [s.strip() for s in str(v).split(sep)]

# ================================================================= fonts
FONT_FILES = {
    "display": ["Anton-Regular.ttf", "ArchivoBlack-Regular.ttf", "Impact.ttf", "impact.ttf",
                "Arial Black.ttf", "ariblk.ttf", "Montserrat-Black.ttf", "DejaVuSans-Bold.ttf"],
    "heavy": ["ArchivoBlack-Regular.ttf", "Montserrat-Black.ttf", "Inter-Black.otf", "Inter-ExtraBold.otf",
              "Arial Black.ttf", "ariblk.ttf", "DejaVuSans-Bold.ttf"],
    "bold": ["Inter-Bold.otf", "Inter-Bold.ttf", "Montserrat-Bold.ttf", "Arial Bold.ttf",
             "arialbd.ttf", "DejaVuSans-Bold.ttf"],
    "semibold": ["Inter-SemiBold.otf", "Inter-SemiBold.ttf", "Montserrat-SemiBold.ttf",
                 "Arial Bold.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"],
    "regular": ["Inter-Regular.otf", "Inter-Regular.ttf", "Montserrat-Regular.ttf", "Arial.ttf",
                "arial.ttf", "DejaVuSans.ttf"],
    "mono": ["SpaceMono-Bold.ttf", "SpaceMono-Regular.ttf", "DejaVuSansMono-Bold.ttf",
             "Menlo.ttc", "Courier New Bold.ttf", "courbd.ttf"],
    "serif": ["InstrumentSerif-Regular.ttf", "PlayfairDisplay-Regular.ttf", "DejaVuSerif.ttf",
              "Georgia.ttf", "georgia.ttf", "Times New Roman.ttf", "times.ttf"],
    "serif-italic": ["InstrumentSerif-Italic.ttf", "PlayfairDisplay-Italic.ttf", "DejaVuSerif-Italic.ttf",
                     "Georgia Italic.ttf", "georgiai.ttf", "Times New Roman Italic.ttf", "timesi.ttf"],
    "marker": ["PermanentMarker-Regular.ttf", "Marker Felt.ttc", "Chalkboard.ttc", "comicbd.ttf",
               "DejaVuSans-BoldOblique.ttf"],
    "sym": ["DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "Apple Symbols.ttf", "seguisym.ttf",
            "Arial Unicode.ttf", "Arial Unicode MS.ttf"],
}
FONT_DIRS = [os.path.join(CACHE, "fonts"), "/usr/share/fonts", "/usr/local/share/fonts",
             os.path.expanduser("~/.fonts"), os.path.expanduser("~/.local/share/fonts"),
             os.path.expanduser("~/Library/Fonts"), "/Library/Fonts", "/System/Library/Fonts",
             "C:/Windows/Fonts"]
_font_index, _font_cache = None, {}

def font_path(kind):
    global _font_index
    if _font_index is None:
        _font_index = {}
        for d in FONT_DIRS:
            for root, _, files in os.walk(d):
                for f in files:
                    _font_index.setdefault(f, os.path.join(root, f))
    for name in FONT_FILES.get(kind, FONT_FILES["bold"]):
        if name in _font_index:
            return _font_index[name]
    return None

def font(kind, size):
    size = max(8, int(size)); key = (kind, size)
    if key not in _font_cache:
        p = font_path(kind)
        try:
            _font_cache[key] = ImageFont.truetype(p, size) if p else ImageFont.load_default(size)
        except Exception:
            _font_cache[key] = ImageFont.load_default(size)
    return _font_cache[key]

def text_img(text, fnt, fill=(255, 255, 255, 255), stroke=0, stroke_fill=(0, 0, 0, 255)):
    text = str(text) if str(text) else " "
    l, t, r, b = fnt.getbbox(text, stroke_width=stroke)
    im = Image.new("RGBA", (max(1, r - l), max(1, b - t)), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((-l, -t), text, font=fnt, fill=fill, stroke_width=stroke,
                            stroke_fill=stroke_fill)
    return im

def T(text, kind, size, fill=(255, 255, 255, 255), **kw):
    if isinstance(fill, str): fill = rgba(fill)
    return text_img(text, font(kind, size), fill, **kw)

def fit_size(text, kind, max_w, max_size):
    s = int(max_size)
    while s > 10:
        l, _, r, _ = font(kind, s).getbbox(str(text) or " ")
        if r - l <= max_w: return s
        s = int(s * 0.93)
    return s

def wrap(text, kind, size, max_w):
    f = font(kind, size); lines, cur = [], ""
    for w in str(text).split(" "):
        test = (cur + " " + w).strip()
        if f.getbbox(test)[2] > max_w and cur:
            lines.append(cur); cur = w
        else:
            cur = test
    lines.append(cur)
    return lines

# ================================================================= drawing
def paste(canvas, elem, x, y, alpha=1.0, center=False):
    """alpha-composite elem onto canvas at (x,y) (top-left, or centre) with clipping."""
    if elem is None or alpha <= 0.003: return
    if center: x, y = x - elem.width / 2, y - elem.height / 2
    x, y = int(round(x)), int(round(y))
    if alpha < 0.999:
        elem = elem.copy(); elem.putalpha(elem.getchannel("A").point(lambda v: int(v * alpha)))
    cx0, cy0 = max(0, -x), max(0, -y)
    cx1, cy1 = min(elem.width, canvas.width - x), min(elem.height, canvas.height - y)
    if cx1 <= cx0 or cy1 <= cy0: return
    if (cx0, cy0, cx1, cy1) != (0, 0, elem.width, elem.height):
        elem = elem.crop((cx0, cy0, cx1, cy1))
    canvas.alpha_composite(elem, dest=(x + cx0, y + cy0))

def card(w, h, r, fill, outline=None, width=0):
    im = Image.new("RGBA", (max(1, int(w)), max(1, int(h))), (0, 0, 0, 0))
    if isinstance(fill, str): fill = rgba(fill)
    if isinstance(outline, str): outline = rgba(outline)
    ImageDraw.Draw(im).rounded_rectangle((0, 0, int(w) - 1, int(h) - 1), radius=int(r), fill=fill,
                                         outline=outline, width=int(width))
    return im

def shadowed(im, blur=18, off=(0, 8), alpha=110):
    pad = blur * 2
    out = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, alpha)); sh.putalpha(im.getchannel("A").point(lambda v: v * alpha // 255))
    out.alpha_composite(sh, (pad + off[0], pad + off[1]))
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(im, (pad, pad))
    return out

def scale_img(im, s, sy=None):
    sy = s if sy is None else sy
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * sy))), Image.BILINEAR)

def rot(im, deg):
    return im.rotate(deg, expand=True, resample=Image.BICUBIC) if abs(deg) > 0.05 else im

def draw_check(d, cx, cy, s, color, width):
    d.line([(cx - s * 0.45, cy), (cx - s * 0.12, cy + s * 0.33), (cx + s * 0.5, cy - s * 0.38)],
           fill=color, width=int(width), joint="curve")

def draw_arrow(d, p0, p1, color, width, head=None):
    d.line([p0, p1], fill=color, width=int(width))
    head = head or width * 4
    a = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    for s in (-1, 1):
        d.line([p1, (p1[0] - head * math.cos(a + s * 0.5), p1[1] - head * math.sin(a + s * 0.5))],
               fill=color, width=int(width))

def cursor_img(size):
    im = Image.new("RGBA", (int(size), int(size * 1.4)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    s = size
    pts = [(2, 2), (2, s * 1.15), (s * 0.32, s * 0.88), (s * 0.55, s * 1.35), (s * 0.72, s * 1.27),
           (s * 0.5, s * 0.82), (s * 0.88, s * 0.82)]
    d.polygon(pts, fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=max(2, int(s * 0.07)))
    return im

def toggle_img(w, on, accent="#34C759"):
    h = w * 0.6; im = card(w, h, h / 2, rgba(accent) if on > 0.5 else (120, 120, 128, 160))
    d = ImageDraw.Draw(im); r = h / 2 - w * 0.04
    x = lerp(h / 2, w - h / 2, ease_in_out(on))
    d.ellipse((x - r, h / 2 - r, x + r, h / 2 + r), fill=(255, 255, 255, 255))
    return im

PALETTE = ["#F97316", "#8B5CF6", "#06B6D4", "#EC4899", "#22C55E", "#EAB308", "#3B82F6", "#EF4444"]

def placeholder(i, w, h, label=None):
    """gradient card used when the user gave no screenshots."""
    c1 = np.array(hex2rgb(PALETTE[i % len(PALETTE)]), np.float32)
    c2 = np.array(hex2rgb(PALETTE[(i + 3) % len(PALETTE)]), np.float32)
    t = np.linspace(0, 1, int(h))[:, None, None]
    arr = (c1 * (1 - t) + c2 * t).repeat(int(w), axis=1).astype(np.uint8)
    im = Image.fromarray(arr, "RGB").convert("RGBA")
    lab = T(label or f"REEL {i + 1}", "display", w * 0.2)
    paste(im, lab, w / 2, h / 2, center=True)
    return im

def load_images(spec, n, w, h, labels=None):
    """spec: list of paths, folder path, or None -> placeholders. returns n RGBA images w x h."""
    paths = []
    if isinstance(spec, str) and os.path.isdir(spec):
        for ext in ("png", "jpg", "jpeg", "webp", "PNG", "JPG", "JPEG"):
            paths += glob.glob(os.path.join(spec, "*." + ext))
        paths.sort()
    elif spec:
        paths = [p for p in as_list(spec) if os.path.exists(p)]
    out = []
    for i in range(n):
        if paths:
            im = Image.open(paths[i % len(paths)]).convert("RGBA")
            s = max(w / im.width, h / im.height)
            im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1))
            l, t = (im.width - w) // 2, (im.height - h) // 2
            out.append(im.crop((l, t, l + int(w), t + int(h))))
        else:
            out.append(placeholder(i, w, h, labels[i] if labels and i < len(labels) else None))
    return out

def rounded(im, r):
    m = card(im.width, im.height, r, (255, 255, 255, 255)).getchannel("A")
    im = im.copy(); im.putalpha(Image.fromarray(np.minimum(np.array(m), np.array(im.getchannel("A")))))
    return im

def framed(im, r, border, color=(255, 255, 255, 255)):
    fr = card(im.width + border * 2, im.height + border * 2, r + border, color)
    paste(fr, rounded(im, r), border, border)
    return fr

# ================================================================= image (numpy) ops
def rr_mask(h, w, r):
    return np.array(card(w, h, r, (255, 255, 255, 255)).getchannel("A"), np.float32)[..., None] / 255

def frost(img, x, y, w, h, r=30, tint=(255, 255, 255), amount=0.22, blur=None, alpha=1.0):
    """frosted-glass panel baked into a float image (in place, returns img)."""
    H, W = img.shape[:2]
    x, y, w, h = int(round(x)), int(round(y)), int(round(w)), int(round(h))
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 - x0 < 4 or y1 - y0 < 4 or alpha <= 0: return img
    blur = blur or max(9, int(W / 45)) | 1
    reg = img[y0:y1, x0:x1]
    b = cv2.GaussianBlur(reg, (0, 0), blur / 2)
    b = b * (1 - amount) + np.array(tint, np.float32) * amount
    m = rr_mask(int(h), int(w), r)[int(y0 - y):int(y0 - y) + (y1 - y0), int(x0 - x):int(x0 - x) + (x1 - x0)] * alpha
    img[y0:y1, x0:x1] = reg * (1 - m) + b * m
    return img

def to_gray(img):
    g = img @ np.array([0.299, 0.587, 0.114], np.float32)
    return np.repeat(g[..., None], 3, axis=2)

def affine(img, z, cx, cy, W, H, tx=0, ty=0, border=cv2.BORDER_REFLECT, fill=0):
    """scale z about (cx,cy) and put that point at the frame centre (+tx,ty)."""
    M = np.float32([[z, 0, W / 2 + tx - z * cx], [0, z, H / 2 + ty - z * cy]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=border, borderValue=(fill, fill, fill))

def zoom_on(img, c, z, cx=None, cy=None):
    cx = c.face[0] if cx is None else cx; cy = c.face[1] if cy is None else cy
    cx = clamp(cx, c.W / (2 * z), c.W - c.W / (2 * z)); cy = clamp(cy, c.H / (2 * z), c.H - c.H / (2 * z))
    return affine(img, z, cx, cy, c.W, c.H)

def place_frame(img, c, s, x, y, bg):
    """shrink whole frame by s and put its top-left at (x,y) on a bg (float image)."""
    small = cv2.resize(img, (max(1, int(c.W * s)), max(1, int(c.H * s))), interpolation=cv2.INTER_AREA)
    out = bg.copy(); x, y = int(x), int(y)
    h, w = small.shape[:2]
    xs0, ys0 = max(0, -x), max(0, -y); xs1, ys1 = min(w, c.W - x), min(h, c.H - y)
    if xs1 > xs0 and ys1 > ys0:
        out[y + ys0:y + ys1, x + xs0:x + xs1] = small[ys0:ys1, xs0:xs1]
    return out

def solid(c, color):
    return np.ones((c.H, c.W, 3), np.float32) * np.array(hex2rgb(color), np.float32)

def vgrad(c, top, bottom):
    t = np.linspace(0, 1, c.H, dtype=np.float32)[:, None, None]
    return np.array(hex2rgb(top), np.float32) * (1 - t) + np.array(hex2rgb(bottom), np.float32) * t + np.zeros((c.H, c.W, 3), np.float32)

# ================================================================= tracking
class Tracker:
    def __init__(self, model_path, face_path, W, H):
        self.W, self.H = W, H
        self.seg = self.fd = self.haar = None
        import mediapipe as mp
        from mediapipe.tasks.python import vision, BaseOptions
        self.mp = mp
        if model_path and os.path.exists(model_path):
            self.seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
                base_options=BaseOptions(model_asset_path=model_path),
                output_confidence_masks=True, running_mode=vision.RunningMode.IMAGE))
        else:
            print("WARNING: no person-segmentation model; 'behind head' layering disabled", file=sys.stderr)
        if face_path and os.path.exists(face_path):
            self.fd = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
                base_options=BaseOptions(model_asset_path=face_path), min_detection_confidence=0.5))
        else:
            hp = os.path.join(getattr(cv2, "data", None) and cv2.data.haarcascades or "",
                              "haarcascade_frontalface_default.xml")
            if os.path.exists(hp): self.haar = cv2.CascadeClassifier(hp)
        self.mask = None; self.face = None

    def segment(self, rgb):
        if self.seg is None: return np.zeros((self.H, self.W), np.float32)
        h, w = rgb.shape[:2]; s = 384 / min(h, w)
        small = cv2.resize(rgb, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
        masks = self.seg.segment(self.mp.Image(image_format=self.mp.ImageFormat.SRGB,
                                               data=np.ascontiguousarray(small))).confidence_masks
        m = masks[0].numpy_view() if len(masks) == 1 else 1 - masks[0].numpy_view()
        m = cv2.resize(np.squeeze(m).astype(np.float32), (self.W, self.H), interpolation=cv2.INTER_LINEAR)
        m = np.clip((m - 0.25) / 0.5, 0, 1)
        return cv2.GaussianBlur(m, (0, 0), max(1.5, self.W / 600))

    def detect_face(self, rgb, mask):
        W, H = self.W, self.H; s = 480 / W
        small = cv2.resize(rgb, (480, int(H * s))); faces = []
        if self.fd is not None:
            r = self.fd.detect(self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=np.ascontiguousarray(small)))
            faces = [(b.origin_x, b.origin_y, b.width, b.height) for b in (d.bounding_box for d in r.detections)]
        elif self.haar is not None:
            faces = self.haar.detectMultiScale(cv2.cvtColor(small, cv2.COLOR_RGB2GRAY), 1.1, 5, minSize=(40, 40))
        if len(faces):
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            return np.array([(x + w / 2) / s, (y + h / 2) / s, w / s, h / s], np.float32)
        if mask is not None and mask.max() > 0.5:       # fallback: head = top of the person blob
            rows = np.where(mask.max(axis=1) > 0.5)[0]; y0 = rows[0]
            xs = np.where((mask[y0:y0 + int(0.12 * H)] > 0.5).any(axis=0))[0]
            cx = xs.mean() if len(xs) else W / 2; fw = 0.26 * W
            return np.array([cx, y0 + 0.02 * H + fw * 0.65, fw, fw * 1.25], np.float32)
        return None

    def update(self, rgb, smooth=True):
        m = self.segment(rgb)
        self.mask = m if (self.mask is None or not smooth) else self.mask * 0.35 + m * 0.65
        f = self.detect_face(rgb, self.mask)
        if f is None:
            f = self.face if self.face is not None else np.array([self.W / 2, self.H * 0.35, self.W * 0.28, self.W * 0.35], np.float32)
        if self.face is None or not smooth:
            self.face = f
        else:
            k = 0.08 if np.abs(f[:2] - self.face[:2]).max() / self.W > 0.15 else 0.3
            self.face = self.face * (1 - k) + f * k
        return self.mask, self.face

    def close(self):
        for m in (self.seg, self.fd):
            if m is not None:
                try: m.close()
                except Exception: pass
        self.seg = self.fd = None

class Ctx:
    """per-frame context: W,H, face=(cx,cy,w,h), mask (H,W 0..1), raw frame, X/Y grids, t, fps"""
    pass

# ================================================================= effect base
class FX:
    name = ""; help = ""; params = {}
    def __init__(self, start, end, **kw):
        self.start, self.end = float(start), float(end)
        self.p = dict(self.params); self.p.update(kw)
        self.rng = random.Random(hash(self.name) & 0xffff)
    @property
    def dur(self): return max(0.01, self.end - self.start)
    def active(self, t): return self.start <= t <= self.end
    def env(self, lt, fin=0.25, fout=0.25):
        return clamp(lt / fin if fin else 1) * clamp((self.dur - lt) / fout if fout else 1)
    def outa(self, lt, fout=0.25):
        return clamp((self.dur - lt) / fout) if fout else 1.0
    # face helpers
    def head_top(self, c): return c.face[1] - c.face[3] * 0.85
    def chin(self, c): return c.face[1] + c.face[3] * 0.62
    def side(self, c):
        """+1 if there is more room on the right of the face, else -1"""
        return 1 if c.face[0] < c.W / 2 else -1
    # hooks (override what you need):
    #   grade(c,img,lt)->img   whole frame      bgfx(c,img,lt)->img  background only (person kept)
    #   behind(c,canvas,lt)    under the person front(c,canvas,lt)    over everything
    #   post(c,img,lt)->img    camera moves     top(c,canvas,lt)      after camera moves (UI)
    grade = bgfx = behind = front = post = top = None

REG, ALIAS = {}, {}
def register(cls):
    REG[cls.name] = cls
    for a in getattr(cls, "aliases", []): ALIAS[a] = cls.name
    return cls

# ================================================================= effects 1-12
@register
class Noise(FX):
    name = "noise"; help = "Reels/screenshots pile up behind your head"
    params = {"images": None, "count": 10}
    def behind(self, c, canvas, lt):
        st = self.__dict__.setdefault("_s", {})
        n = int(self.p["count"]); W, H = c.W, c.H
        if "cards" not in st:
            w = int(W * 0.2); h = int(w * 16 / 9)
            ims = load_images(self.p["images"], n, w, h)
            r = random.Random(3)
            st["cards"] = [(framed(im, w * 0.06, max(3, w // 40)), r.uniform(0.05, 0.95), r.uniform(-0.05, 1.0), r.uniform(-18, 18)) for im in ims]
        cx, cy, fw, fh = c.face; top = max(0, self.head_top(c) - H * 0.12); bot = self.chin(c)
        appear = self.dur * 0.6 / n
        for i, (im, rx, ry, ang) in enumerate(st["cards"]):
            q = (lt - i * appear) / 0.25
            if q <= 0: continue
            s = ease_out_back(q) * 1.0
            x = rx * W; y = top + ry * (bot - top)
            paste(canvas, rot(scale_img(im, max(0.05, s)), ang), x, y, self.outa(lt, 0.3), center=True)

@register
class Lineup(FX):
    name = "lineup"; help = "Numbered tiles fan out above your head"
    params = {"items": ["1", "2", "3", "4", "5"], "color": "#111111", "accent": "#FFFFFF"}
    def behind(self, c, canvas, lt):
        items = as_list(self.p["items"]); n = len(items); W, H = c.W, c.H
        cx = c.face[0]; ts = W * 0.15; R = W * 0.42
        pivot_y = self.head_top(c) + R * 0.75
        for i, it in enumerate(items):
            q = ease_out_back((lt - 0.08 * i) / 0.45)
            if q <= 0: continue
            ang = math.radians(lerp(-55, 55, i / max(1, n - 1)) * q)
            x = cx + R * math.sin(ang); y = pivot_y - R * math.cos(ang)
            tile = card(ts, ts * 1.2, ts * 0.16, rgba(self.p["color"], 235))
            lab = T(it, "display", fit_size(it, "display", ts * 0.8, ts * 0.7), self.p["accent"])
            paste(tile, lab, tile.width / 2, tile.height / 2, center=True)
            paste(canvas, rot(tile, -math.degrees(ang) * 0.6), x, max(ts * 0.7, y), self.outa(lt), center=True)

@register
class LockedOn(FX):
    name = "locked-on"; help = "Brackets lock onto your face and the camera follows you"
    params = {"color": "#FFFFFF", "zoom": 1.15}
    def post(self, c, img, lt):
        z = 1 + (float(self.p["zoom"]) - 1) * ease_in_out(lt / 0.6) * self.outa(lt, 0.4)
        return zoom_on(img, c, z)
    def top(self, c, canvas, lt):
        W, H = c.W, c.H; q = ease_out_cubic(lt / 0.5)
        bw, bh = c.face[3] * 1.5, c.face[3] * 1.7
        w, h = lerp(W * 0.95, bw, q), lerp(H * 0.9, bh, q); cx, cy = W / 2, H / 2 - lerp(0, c.face[3] * 0.1, q)
        d = ImageDraw.Draw(canvas); L = min(w, h) * 0.18; lw = max(3, int(W * 0.006))
        col = rgba(self.p["color"], 255 * self.env(lt, 0.15, 0.3))
        for sx in (-1, 1):
            for sy in (-1, 1):
                x0, y0 = cx + sx * w / 2, cy + sy * h / 2
                d.line([(x0, y0), (x0 - sx * L, y0)], fill=col, width=lw)
                d.line([(x0, y0), (x0, y0 - sy * L)], fill=col, width=lw)

@register
class BackdropWord(FX):
    name = "backdrop-word"; help = "Giant word drops in BEHIND your head (style: display|serif|serif-italic)"
    params = {"text": "FOCUS", "color": "#FFFFFF", "style": "display", "y": None, "glow": False}
    def behind(self, c, canvas, lt):
        W, H = c.W, c.H; kind = self.p["style"]
        txt = str(self.p["text"]); txt = txt.upper() if kind == "display" else txt
        size = fit_size(txt, kind, W * 0.96, int(H * 0.3))
        im = T(txt, kind, size, self.p["color"])
        if self.p.get("glow"):
            g = im.filter(ImageFilter.GaussianBlur(size * 0.08)); g.alpha_composite(im); im = g
        yc = self.p["y"] * H if self.p["y"] is not None else c.face[1] - c.face[3] * 0.55
        y = yc - (1 - ease_out_back(lt / 0.5, 1.2)) * H * 0.35
        paste(canvas, im, W / 2, y, self.env(lt, 0.12, 0.3), center=True)

@register
class Spotlight(FX):
    name = "spotlight"; help = "Kill the lights, keep you lit (optional glowing word behind you)"
    params = {"dark": 0.85, "word": None, "color": "#FF9EB5"}
    def _on(self, lt):
        on = ease_out_cubic(lt / 0.35)
        if lt < 0.3: on *= 0.55 + 0.45 * (int(lt * 24) % 2)
        return on * self.outa(lt, 0.3)
    def bgfx(self, c, img, lt):
        on = self._on(lt)
        if on <= 0: return img
        cx, cy = c.face[0], c.face[1]; sig = c.W * 0.4
        L = np.exp(-(((c.X - cx) ** 2 + ((c.Y - cy) * 0.7) ** 2) / (2 * sig ** 2)))[..., None]
        dark = 1 - float(self.p["dark"]) * on
        return img * (dark + (1 - dark) * 0.4 * L)
    def behind(self, c, canvas, lt):
        if not self.p.get("word"): return
        BackdropWord.behind(type("o", (), {"p": {"text": self.p["word"], "color": self.p["color"], "style": "serif",
                            "y": None, "glow": True}, "env": self.env, "dur": self.dur})(), c, canvas, lt)

@register
class TheBill(FX):
    name = "the-bill"; help = "Your instructions print out like a receipt"
    params = {"title": "RECEIPT", "lines": ["01 FOLLOW MY FACE", "02 ORBIT", "03 WORD BEHIND ME", "04 KILL THE LIGHTS"], "total": "TOTAL  4 EFFECTS"}
    def _paper(self, c):
        st = self.__dict__.setdefault("_s", {})
        if "p" in st: return st["p"]
        W = c.W; pw = int(W * 0.44); fs = W * 0.026; lh = fs * 1.6; pad = W * 0.03
        lines = [self.p["title"], "-" * 22] + as_list(self.p["lines"]) + ["-" * 22, self.p["total"], "", "THANK YOU"]
        ph = int(pad * 2 + lh * len(lines))
        im = Image.new("RGBA", (pw, ph), (250, 248, 240, 255)); d = ImageDraw.Draw(im)
        for i, ln in enumerate(lines):
            f = font("mono", fs * (1.25 if i == 0 else 1))
            d.text((pad, pad + i * lh), ln, font=f, fill=(30, 30, 30, 255))
        for x in range(0, pw, int(W * 0.02)):          # zig-zag torn bottom
            d.polygon([(x, ph), (x + W * 0.01, ph - W * 0.012), (x + W * 0.02, ph)], fill=(0, 0, 0, 0))
        st["p"] = im; return im
    def behind(self, c, canvas, lt):
        W, H = c.W, c.H; p = self._paper(c)
        x = clamp(c.face[0] + self.side(c) * W * 0.3, p.width / 2 + W * 0.03, W - p.width / 2 - W * 0.03)
        slot_y = H * 0.03; shown = int(p.height * ease_out_cubic(lt / max(0.6, self.dur * 0.6)))
        a = self.outa(lt, 0.3)
        if shown > 2: paste(canvas, p.crop((0, p.height - shown, p.width, p.height)), x - p.width / 2, slot_y + W * 0.03, a)
        printer = card(p.width * 1.12, W * 0.06, W * 0.015, (40, 40, 44, 255))
        d = ImageDraw.Draw(printer)
        for i in range(3): d.ellipse((W * 0.02 + i * W * 0.025, W * 0.02, W * 0.035 + i * W * 0.025, W * 0.035), fill=(110, 110, 115, 255))
        paste(canvas, printer, x, slot_y + W * 0.03, a, center=True)

@register
class Moody(FX):
    name = "moody"; help = "Moody colour grade (optional serif word behind you)"
    params = {"word": None}
    def grade(self, c, img, lt):
        a = self.env(lt, 0.4, 0.4)
        g = (img - 128) * 1.15 + 118; lum = g.mean(axis=2, keepdims=True)
        g = lum + (g - lum) * 0.6; w = np.clip(lum / 255, 0, 1)
        g = g + (1 - w) * np.array([-10, 4, 14]) + w * np.array([14, 4, -10])
        r = np.sqrt(((c.X - c.W / 2) / c.W) ** 2 + ((c.Y - c.H / 2) / c.H) ** 2)[..., None]
        g = g * (1 - 0.55 * np.clip((r - 0.3) / 0.45, 0, 1))
        return img * (1 - a) + np.clip(g, 0, 255) * a
    def behind(self, c, canvas, lt):
        if not self.p.get("word"): return
        BackdropWord.behind(type("o", (), {"p": {"text": self.p["word"], "color": "#F2EEE8", "style": "serif-italic",
                            "y": None, "glow": False}, "env": self.env, "dur": self.dur})(), c, canvas, lt)

@register
class Swipe(FX):
    name = "swipe"; help = "Before/after slider wipes across (before: bw|dark|blur|raw)"
    params = {"before": "bw", "labels": ["BEFORE", "AFTER"]}
    def _x(self, c, lt):
        return c.W * (1 - ease_in_out((lt - 0.2) / max(0.5, self.dur - 0.6)))
    def grade(self, c, img, lt):
        x = int(self._x(c, lt)); b = self.p["before"]
        if x <= 0: return img
        L = img[:, :x]
        if b == "bw": L = to_gray(L)
        elif b == "dark": L = L * 0.45
        elif b == "blur": L = cv2.GaussianBlur(L, (0, 0), c.W / 80)
        elif b == "raw": L = c.raw[:, :x].astype(np.float32)
        img = img.copy(); img[:, :x] = L; return img
    def top(self, c, canvas, lt):
        x = self._x(c, lt); d = ImageDraw.Draw(canvas); W, H = c.W, c.H
        d.line([(x, 0), (x, H)], fill=(255, 255, 255, 255), width=max(3, int(W * 0.006)))
        r = W * 0.04; d.ellipse((x - r, H / 2 - r, x + r, H / 2 + r), fill=(255, 255, 255, 255))
        d.text((x - r * 0.55, H / 2 - r * 0.5), "‹›", font=font("sym", r), fill=(20, 20, 20, 255))
        labs = as_list(self.p["labels"])
        for i, lab in enumerate(labs[:2]):
            pill = card(W * 0.22, W * 0.06, W * 0.03, (0, 0, 0, 150))
            paste(pill, T(lab, "bold", W * 0.03), pill.width / 2, pill.height / 2, center=True)
            paste(canvas, pill, W * 0.05 if i == 0 else W * 0.73, H * 0.06, self.outa(lt))

@register
class Todo(FX):
    name = "todo"; help = "Notes checklist beside your head that ticks off as you talk"
    params = {"title": "Notes", "items": ["Drop your video", "Install my skill", "Type / + the effect"]}
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; items = as_list(self.p["items"]); n = len(items)
        cw = W * 0.42; pad = W * 0.03; rh = W * 0.06
        ch = pad * 2 + W * 0.09 + rh * n
        box = card(cw, ch, W * 0.03, (255, 253, 245, 245)); d = ImageDraw.Draw(box)
        paste(box, T(self.p["title"], "bold", W * 0.042, "#E5A50A"), pad, pad)
        paste(box, T("Today", "regular", W * 0.022, "#999999"), pad, pad + W * 0.05)
        step = (self.dur - 0.5) / max(1, n)
        for i, it in enumerate(items):
            y = pad + W * 0.09 + i * rh; r = rh * 0.22; ccy = y + rh / 2
            done = lt > 0.4 + step * (i + 0.6)
            d.rounded_rectangle((pad, ccy - r, pad + 2 * r, ccy + r), radius=r * 0.3,
                                fill=(229, 165, 10, 255) if done else None, outline=(200, 160, 60, 255), width=2)
            if done: draw_check(d, pad + r, ccy, r * 1.2, (255, 255, 255, 255), r * 0.35)
            for ln_i, ln in enumerate(wrap(it, "regular", W * 0.027, cw - pad * 3 - 2 * r)[:1]):
                paste(box, T(ln, "regular", W * 0.027, (150, 150, 150, 255) if done else (40, 40, 40, 255)), pad + 2 * r + pad * 0.5, ccy - W * 0.016)
        s = self.side(c)
        x = clamp(c.face[0] + s * (c.face[2] * 0.6 + cw * 0.55), cw / 2 + W * 0.02, W - cw / 2 - W * 0.02)
        y = max(H * 0.04, c.face[1] - c.face[3] * 1.0) + (1 - ease_out_back(lt / 0.4)) * -H * 0.15
        paste(canvas, rot(box, -4 * s), x, y + ch / 2, self.env(lt, 0.2, 0.25), center=True)

@register
class Comment(FX):
    name = "comment-box"; aliases = ["comment"]; help = "A comment types itself, then posts"
    params = {"user": "you", "text": "This is so useful!", "accent": "#3B82F6", "dark": True}
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; dark = self.p.get("dark", True)
        bgc = (35, 35, 38, 235) if dark else (255, 255, 255, 245); fg = (240, 240, 240, 255) if dark else (30, 30, 30, 255)
        cw = W * 0.8; pad = W * 0.035; av = W * 0.075
        txt = str(self.p["text"]); te = 0.35 + max(0.5, self.dur * 0.45)
        k = int(len(txt) * clamp((lt - 0.35) / (te - 0.35)))
        shown = txt[:k] + ("|" if lt < te and int(lt * 3) % 2 == 0 else "")
        lines = wrap(shown, "regular", W * 0.036, cw - av - pad * 4 - W * 0.12)
        lh = W * 0.048; ch = pad * 2 + W * 0.04 + lh * max(1, len(lines))
        box = card(cw, ch, W * 0.04, bgc); d = ImageDraw.Draw(box)
        d.ellipse((pad, pad, pad + av, pad + av), fill=rgba(self.p["accent"]))
        paste(box, T(str(self.p["user"])[:1].upper(), "bold", av * 0.5), pad + av / 2, pad + av / 2, center=True)
        x0 = pad * 2 + av
        paste(box, T(self.p["user"], "bold", W * 0.032, fg), x0, pad)
        for i, ln in enumerate(lines):
            if ln: paste(box, T(ln, "regular", W * 0.036, fg), x0, pad + W * 0.045 + i * lh)
        posted = lt > te + 0.25
        heart = T("♥" if posted else "♡", "sym", W * 0.05, "#FF3B5C" if posted else fg)
        paste(box, scale_img(heart, ease_out_back((lt - te - 0.25) / 0.3) * 0.4 + 0.8 if posted else 1), cw - pad - W * 0.04, ch / 2, center=True)
        y = c.face[1] - c.face[3] * 1.1 - ch / 2
        if y < H * 0.03: y = self.chin(c) + H * 0.04
        y += (1 - ease_out_back(lt / 0.4)) * -H * 0.1
        paste(canvas, box, (W - cw) / 2, y, self.env(lt, 0.2, 0.25))

# ================================================================= effects 13-24
@register
class Tap(FX):
    name = "tap"; help = "A Follow button gets tapped and flips to Following"
    params = {"name": "Your Name", "handle": "@yourhandle", "accent": "#3B82F6"}
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; cw, ch = W * 0.78, W * 0.15; tap_t = self.dur * 0.5
        done = lt > tap_t
        box = card(cw, ch, ch * 0.3, (255, 255, 255, 245)); d = ImageDraw.Draw(box)
        av = ch * 0.62; pad = (ch - av) / 2
        d.ellipse((pad, pad, pad + av, pad + av), fill=rgba(PALETTE[1]))
        paste(box, T(str(self.p["name"])[:1].upper(), "bold", av * 0.5), pad + av / 2, ch / 2, center=True)
        paste(box, T(self.p["name"], "bold", W * 0.034, "#111111"), pad * 2 + av, ch * 0.24)
        paste(box, T(self.p["handle"], "regular", W * 0.026, "#888888"), pad * 2 + av, ch * 0.56)
        bw, bh = W * 0.21, ch * 0.5
        press = 1 - 0.12 * clamp(1 - abs(lt - tap_t) / 0.12)
        btn = card(bw, bh, bh / 2, (235, 235, 240, 255) if done else rgba(self.p["accent"]))
        paste(btn, T("Following" if done else "Follow", "bold", W * 0.028, "#111111" if done else "#FFFFFF"), bw / 2, bh / 2, center=True)
        bx, by = cw - pad - bw / 2, ch / 2
        paste(box, scale_img(btn, press), bx, by, center=True)
        y = self.chin(c) + H * 0.08
        y = min(y, H * 0.85); x0 = (W - cw) / 2
        paste(canvas, shadowed(box), W / 2, y + (1 - ease_out_back(lt / 0.4)) * H * 0.15, self.env(lt, 0.2, 0.3), center=True)
        # cursor
        q = ease_in_out((lt - 0.3) / max(0.2, tap_t - 0.3))
        tx, ty = x0 + bx + bw * 0.1, y + bh * 0.1
        cx_, cy_ = lerp(W * 0.95, tx, q), lerp(H * 0.95, ty, q)
        paste(canvas, cursor_img(W * 0.05), cx_, cy_, self.env(lt, 0.3, 0.3))

@register
class PausePoint(FX):
    name = "pause-point"; help = "Freeze frame with PAUSED chip and hand-drawn arrows + labels"
    params = {"labels": ["me", "Claude did this"], "targets": ["face", [0.5, 0.62]], "color": "#FFC531"}
    def grade(self, c, img, lt):
        st = self.__dict__.setdefault("_state", {})
        if "frozen" not in st: st["frozen"] = (img.copy(), c.mask.copy(), c.face.copy())
        img, c.mask, c.face = st["frozen"][0].copy(), st["frozen"][1], st["frozen"][2]
        return img
    def top(self, c, canvas, lt):
        W, H = c.W, c.H; d = ImageDraw.Draw(canvas)
        chip = card(W * 0.22, W * 0.06, W * 0.012, (20, 20, 20, 230))
        paste(chip, T("❚❚ PAUSED", "sym", W * 0.026), chip.width / 2, chip.height / 2, center=True)
        paste(canvas, chip, W * 0.74, H * 0.04)
        labels = as_list(self.p["labels"]); tg = self.p["targets"]
        for i, lab in enumerate(labels):
            q = ease_out_back((lt - 0.25 - i * 0.45) / 0.35)
            if q <= 0: continue
            t = tg[i] if i < len(tg) else "face"
            tx, ty = (c.face[0], c.face[1]) if t == "face" else (t[0] * W, t[1] * H)
            left = i % 2 == 0
            lx = W * (0.08 if left else 0.55); ly = ty + (-c.face[3] * 0.9 if i == 0 else H * 0.08)
            tag = card(W * 0.06 + font("bold", W * 0.03).getbbox(lab)[2] + W * 0.07, W * 0.065, W * 0.012, (255, 255, 255, 245))
            paste(tag, T(f"{i + 1:02d}", "bold", W * 0.03, self.p["color"]), W * 0.02, W * 0.017)
            paste(tag, T(lab, "bold", W * 0.03, "#111111"), W * 0.075, W * 0.017)
            paste(canvas, scale_img(tag, q), lx, ly)
            sx, sy = lx + (tag.width if left else 0), ly + tag.height / 2
            if q > 0.6:
                d.line([(sx, sy), (lerp(sx, tx, 0.85), lerp(sy, ty, 0.85))], fill=(255, 255, 255, 255), width=max(2, int(W * 0.004)))
                r = W * 0.012; ex, ey = lerp(sx, tx, 0.85), lerp(sy, ty, 0.85)
                d.ellipse((ex - r, ey - r, ex + r, ey + r), fill=(255, 255, 255, 255))

def glitch_img(img, amt, seed):
    r = random.Random(seed); H, W = img.shape[:2]; out = img.copy()
    for _ in range(int(6 + 10 * amt)):
        y = r.randint(0, H - 2); h = r.randint(2, max(3, int(H * 0.04 * amt) + 3)); dx = int(r.uniform(-1, 1) * W * 0.08 * amt)
        out[y:y + h] = np.roll(out[y:y + h], dx, axis=1)
    s = int(W * 0.012 * amt) + 1
    out[..., 0] = np.roll(out[..., 0], s, axis=1); out[..., 2] = np.roll(out[..., 2], -s, axis=1)
    return out

@register
class Uninstall(FX):
    name = "uninstall"; help = "App tiles with minus badges, a glitchy uninstall bar breaks the frame"
    params = {"apps": ["Editor", "Clips", "FX"], "label": "Uninstalling..."}
    def behind(self, c, canvas, lt):
        W, H = c.W, c.H; apps = as_list(self.p["apps"]); n = len(apps); ts = W * 0.16
        gone = clamp((lt - self.dur * 0.65) / 0.3)
        for i, a in enumerate(apps):
            q = ease_out_back((lt - 0.1 * i) / 0.35)
            if q <= 0: continue
            tile = card(ts, ts, ts * 0.24, rgba(PALETTE[(i * 2) % 8]))
            paste(tile, T(a, "bold", fit_size(a, "bold", ts * 0.8, ts * 0.26)), ts / 2, ts / 2, center=True)
            out = Image.new("RGBA", (int(ts * 1.25), int(ts * 1.25)), (0, 0, 0, 0)); paste(out, tile, ts * 0.12, ts * 0.12)
            dd = ImageDraw.Draw(out); r = ts * 0.13
            dd.ellipse((0, 0, 2 * r, 2 * r), fill=(235, 60, 60, 255)); dd.line([(r * 0.5, r), (r * 1.5, r)], fill=(255, 255, 255, 255), width=max(2, int(r * 0.3)))
            wob = math.sin(lt * 30 + i) * 3
            x = c.face[0] + (i - (n - 1) / 2) * ts * 1.35; y = self.head_top(c) - ts * 0.4 - H * 0.02
            paste(canvas, rot(scale_img(out, q * (1 - gone)), wob), x, max(ts * 0.7, y), 1 - gone, center=True)
    def post(self, c, img, lt):
        g = clamp((lt - self.dur * 0.55) / 0.2) * clamp((self.dur - lt) / 0.25)
        return glitch_img(img, g, int(lt * 20)) if g > 0.02 else img
    def top(self, c, canvas, lt):
        W, H = c.W, c.H; q = clamp((lt - 0.3) / (self.dur * 0.6))
        bar = card(W * 0.7, W * 0.13, W * 0.025, (20, 20, 22, 230)); d = ImageDraw.Draw(bar)
        paste(bar, T(self.p["label"], "mono", W * 0.03), W * 0.03, W * 0.02)
        d.rounded_rectangle((W * 0.03, W * 0.08, W * 0.03 + (W * 0.64) * q, W * 0.1), radius=W * 0.01, fill=(235, 60, 60, 255))
        paste(canvas, bar, W / 2, H * 0.8, self.env(lt, 0.2, 0.2), center=True)

@register
class ReelFrame(FX):
    name = "reel-frame"; help = "Your video shrinks into a film-strip reel card"
    params = {"label": "KODAK 400 • 21", "scale": 0.78}
    def post(self, c, img, lt):
        q = ease_out_cubic(lt / 0.45) * self.outa(lt, 0.35); s = lerp(1, float(self.p["scale"]), q)
        if q <= 0: return img
        bg = solid(c, "#0B0B0B"); w, h = c.W * s, c.H * s
        return place_frame(img, c, s, (c.W - w) / 2, (c.H - h) / 2, bg)
    def top(self, c, canvas, lt):
        q = ease_out_cubic(lt / 0.45) * self.outa(lt, 0.35)
        if q < 0.3: return
        W, H = c.W, c.H; s = lerp(1, float(self.p["scale"]), q); w = W * s; d = ImageDraw.Draw(canvas)
        strip = (W - w) / 2; hw, hh = strip * 0.42, strip * 0.32; a = int(255 * clamp((q - 0.3) / 0.4))
        off = (c.t * 300) % (hh * 2.4)
        for x in (strip / 2, W - strip / 2):
            y = -hh * 2.4 + off
            while y < H:
                d.rounded_rectangle((x - hw / 2, y, x + hw / 2, y + hh), radius=hh * 0.2, fill=(235, 235, 235, a)); y += hh * 2.4
        paste(canvas, T(self.p["label"], "mono", W * 0.026, "#E8A33A"), strip + W * 0.03, H - (H - H * s) / 2 - W * 0.06, a / 255)

@register
class ShortcutRain(FX):
    name = "shortcut-rain"; help = "Keyboard keys rain down behind you"
    params = {"keys": ["⌘", "Z", "K", "J", "⇧", "C", "V", "⌥"], "count": 10}
    def behind(self, c, canvas, lt):
        W, H = c.W, c.H; keys = as_list(self.p["keys"]); r = random.Random(11); ks = W * 0.13
        for i in range(int(self.p["count"])):
            k = keys[i % len(keys)]; x = r.uniform(0.08, 0.92) * W; delay = r.uniform(0, self.dur * 0.5)
            spd = r.uniform(0.5, 0.8) * H; spin = r.uniform(-60, 60); land = r.uniform(0.08, 0.5) * H
            q = lt - delay
            if q <= 0: continue
            y = min(land, -ks + spd * q * 1.6)
            cap = card(ks, ks, ks * 0.2, (245, 245, 247, 255), (200, 200, 205, 255), max(2, int(ks * 0.03)))
            paste(cap, T(k, "sym", ks * 0.45, "#222222"), ks / 2, ks / 2, center=True)
            paste(canvas, rot(shadowed(cap, 10, (0, 6), 90), spin * min(1, q)), x, y, self.outa(lt, 0.3), center=True)

@register
class Stamp(FX):
    name = "reject-stamp"; aliases = ["stamp"]; help = "A big red stamp slams down (with camera shake)"
    params = {"text": "NOPE", "color": "#E11D2E", "angle": -14}
    def _img(self, c):
        st = self.__dict__.setdefault("_s", {})
        if "im" in st: return st["im"]
        W = c.W; col = hex2rgb(self.p["color"]); txt = str(self.p["text"]).upper()
        t = T(txt, "display", fit_size(txt, "display", W * 0.6, int(W * 0.18)), col + (255,))
        pad = W * 0.04; bw = int(W * 0.014)
        im = card(t.width + pad * 2, t.height + pad * 2, W * 0.02, (0, 0, 0, 0), col + (255,), bw); paste(im, t, pad, pad)
        a = np.array(im.getchannel("A"), np.float32) * ((np.random.default_rng(7).random((im.height, im.width)) > 0.15) * 0.85 + 0.15)
        im.putalpha(Image.fromarray(a.clip(0, 255).astype(np.uint8)))
        st["im"] = rot(im, float(self.p["angle"])); return st["im"]
    def front(self, c, canvas, lt):
        s = lt / 0.2; sc = 2.4 - 1.4 * ease_in_cubic(s) if s < 1 else 1
        y = min(self.chin(c) + c.H * 0.1, c.H * 0.8)
        paste(canvas, scale_img(self._img(c), sc), c.W / 2, y, clamp(s * 1.5) * self.outa(lt), center=True)
    def post(self, c, img, lt):
        if 0.2 < lt < 0.5:
            k = (0.5 - lt) / 0.3 * c.W * 0.015
            return affine(img, 1.0, c.W / 2, c.H / 2, c.W, c.H, random.uniform(-k, k), random.uniform(-k, k))
        return img

def flip_digit(ch, w, h, q, bg=(22, 22, 24, 255)):
    tile = card(w, h, w * 0.14, bg); paste(tile, T(ch, "display", h * 0.72), w / 2, h / 2, center=True)
    ImageDraw.Draw(tile).line([(0, h / 2), (w, h / 2)], fill=(0, 0, 0, 200), width=max(2, int(h * 0.02)))
    return scale_img(tile, 1, max(0.03, abs(math.cos(math.pi * clamp(1 - q)))) if q < 1 else 1)

@register
class Countdown(FX):
    name = "countdown"; help = "3-2-1 flip tiles above your head"
    params = {"from": 3}
    def behind(self, c, canvas, lt):
        W, H = c.W, c.H; n = int(self.p["from"]); seg = self.dur / n
        idx = min(n - 1, int(lt / seg)); q = (lt - idx * seg) / seg
        ts = W * 0.22; tile = flip_digit(str(n - idx), ts, ts * 1.2, q / 0.15)
        y = self.head_top(c) - ts * 0.7; x = c.face[0]
        if y - ts * 0.6 < H * 0.03:
            y = c.face[1] - c.face[3] * 0.3; x = clamp(c.face[0] + self.side(c) * (c.face[2] * 0.8 + ts * 0.75), ts * 0.6, W - ts * 0.6)
        paste(canvas, tile, x, y, self.env(lt, 0.1, 0.2), center=True)

@register
class CountdownFlip(FX):
    name = "countdown-flip"; help = "Flip-clock counter rolls from one value to another (e.g. 43:00 -> 4:22)"
    params = {"from": "43:00", "to": "04:22", "label": "RAW → FINAL"}
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; a, b = str(self.p["from"]), str(self.p["to"]); n = max(len(a), len(b)); a, b = a.rjust(n), b.rjust(n)
        dw = W * 0.14; dh = dw * 1.35; gap = W * 0.015; tot = n * dw + (n - 1) * gap
        x0 = W / 2 - tot / 2; y = min(self.chin(c) + H * 0.12, H * 0.82)
        for i in range(n):
            sw = 0.3 + i * 0.12 + self.dur * 0.25; ch = b[i] if lt > sw else a[i]
            if ch == ":":
                paste(canvas, T(":", "display", dh * 0.6), x0 + i * (dw + gap) + dw / 2, y, self.env(lt), center=True); continue
            paste(canvas, flip_digit(ch, dw, dh, (lt - sw) / 0.18 if lt > sw else 1), x0 + i * (dw + gap) + dw / 2, y, self.env(lt), center=True)
        paste(canvas, T(self.p["label"], "mono", W * 0.03), x0, y - dh / 2 - W * 0.06, self.env(lt))

@register
class RabbitHole(FX):
    name = "rabbit-hole"; help = "The room tunnels away behind you (nested frames)"
    params = {"depth": 5, "color": "#FFFFFF"}
    def bgfx(self, c, img, lt):
        q = ease_out_cubic(lt / 0.6) * self.outa(lt, 0.4)
        if q <= 0: return img
        W, H = c.W, c.H; out = img.copy(); ph = (lt * 0.6) % 1
        bw = max(3, int(W * 0.008)); col = np.array(hex2rgb(self.p["color"]), np.float32)
        for k in range(1, int(self.p["depth"]) + 1):
            s = 0.78 ** (k - ph)
            if s >= 1: continue
            w, h = int(W * s), int(H * s); x, y = (W - w) // 2, int((H - h) * 0.45)
            small = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
            out[y:y + h, x:x + w] = out[y:y + h, x:x + w] * (1 - q) + small * q
            out[y:y + bw, x:x + w] = col; out[y + h - bw:y + h, x:x + w] = col
            out[y:y + h, x:x + bw] = col; out[y:y + h, x + w - bw:x + w] = col
        return out

@register
class CoverStar(FX):
    name = "cover-star"; help = "You become a magazine cover (look: classic|editorial)"
    params = {"title": "VIBE", "lines": ["THE AI ISSUE", "22 EFFECTS NO EDITOR"], "color": "#FF6B8A", "look": "classic"}
    def grade(self, c, img, lt):
        return img * 0.92 + 12 if self.p["look"] == "editorial" else img
    def behind(self, c, canvas, lt):
        W, H = c.W, c.H; kind = "serif" if self.p["look"] == "classic" else "display"
        t = str(self.p["title"]).upper(); im = T(t, kind, fit_size(t, kind, W * 0.92, H * 0.2), self.p["color"])
        paste(canvas, im, W / 2, H * 0.03 + im.height / 2 - (1 - ease_out_cubic(lt / 0.4)) * H * 0.2, self.env(lt, 0.2, 0.3), center=True)
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; ls = as_list(self.p["lines"]); a = self.env(lt, 0.4, 0.3)
        for i, ln in enumerate(ls[:4]):
            left = i % 2 == 0; y = H * 0.24 + (i // 2) * H * 0.1
            for j, part in enumerate(wrap(ln, "heavy", W * 0.05, W * 0.34)[:3]):
                im = T(part, "heavy", W * 0.05, "#FFFFFF", stroke=2, stroke_fill=(0, 0, 0, 120))
                paste(canvas, im, W * 0.05 if left else W * 0.95 - im.width, y + j * W * 0.06, a * clamp((lt - 0.3 - i * 0.15) / 0.2))
        bc = Image.new("RGBA", (int(W * 0.16), int(W * 0.09)), (255, 255, 255, 255)); d = ImageDraw.Draw(bc); r = random.Random(4); x = 4
        while x < bc.width - 4:
            w = r.choice([1, 2, 3]); d.rectangle((x, 4, x + w, bc.height - 4), fill=(0, 0, 0, 255)); x += w + r.choice([1, 2, 3])
        paste(canvas, bc, W * 0.05, H * 0.9, a)

@register
class Scribble(FX):
    name = "scribble"; help = "Marker circle draws itself around you + arrow and a word (B&W frame)"
    params = {"word": "me", "color": "#E3262B", "bw": True}
    def grade(self, c, img, lt):
        return to_gray(img) if self.p.get("bw") else img
    def top(self, c, canvas, lt):
        W, H = c.W, c.H; d = ImageDraw.Draw(canvas); col = rgba(self.p["color"]); lw = max(4, int(W * 0.009))
        cx, cy, fw, fh = c.face; rx, ry = fw * 1.0, fh * 1.05; q = ease_in_out(lt / 0.7)
        pts = []
        for k in range(int(100 * q * 1.1) + 1):
            a = -2.2 + k / 100 * 2 * math.pi * 1.1
            pts.append((cx + rx * math.cos(a) * (1 + 0.04 * math.sin(k * 0.3)), cy - fh * 0.15 + ry * math.sin(a)))
        if len(pts) > 1: d.line(pts, fill=col, width=lw, joint="curve")
        q2 = clamp((lt - 0.7) / 0.35)
        if q2 > 0:
            ax0 = (cx - rx * 1.9, cy + ry * 0.9); ax1 = (lerp(ax0[0], cx - rx * 1.05, q2), lerp(ax0[1], cy + ry * 0.5, q2))
            draw_arrow(d, ax0, ax1, col, lw, W * 0.03)
            paste(canvas, T(self.p["word"], "marker", W * 0.07, col), ax0[0] - W * 0.13, ax0[1] - W * 0.04, q2)

@register
class GlassWidgets(FX):
    name = "glass-widgets"; help = "Frosted glass widgets (stat, chart, progress) float around your head"
    params = {"stat": "38", "stat_label": "effects", "chart_label": "Top reels", "chart_value": "197K", "progress_label": "Rendering", "progress": 0.92}
    def _boxes(self, c):
        W = c.W; cx, cy, fw, fh = c.face; top = max(c.H * 0.03, self.head_top(c) - W * 0.05)
        L = [(W * 0.04, top, W * 0.25, W * 0.25), (W * 0.04, top + W * 0.29, W * 0.25, W * 0.3)]
        R = [(W * 0.71, top, W * 0.25, W * 0.17), (W * 0.71, top + W * 0.21, W * 0.25, W * 0.25)]
        return L + R
    def _q(self, i, lt): return ease_out_back((lt - 0.12 * i) / 0.4) * self.outa(lt)
    def bgfx(self, c, img, lt):
        for i, (x, y, w, h) in enumerate(self._boxes(c)):
            q = self._q(i, lt); fl = math.sin(lt * 2 + i) * c.W * 0.006
            if q > 0.05: frost(img, x, y + fl, w, h, c.W * 0.04, tint=(40, 40, 46), amount=0.38, alpha=clamp(q))
        return img
    def behind(self, c, canvas, lt):
        W = c.W; bx = self._boxes(c); d = ImageDraw.Draw(canvas); p = self.p; wh = (255, 255, 255, 255)
        for i, (x, y, w, h) in enumerate(bx):
            q = clamp(self._q(i, lt))
            if q < 0.3: continue
            y += math.sin(lt * 2 + i) * W * 0.006; a = int(255 * q); pad = W * 0.02
            if i == 0:
                paste(canvas, T(p["stat"], "display", W * 0.11, wh), x + pad, y + pad, q)
                paste(canvas, T(p["stat_label"], "semibold", W * 0.024, wh), x + pad, y + h - pad - W * 0.03, q)
            elif i == 1:
                paste(canvas, T(p["chart_label"], "semibold", W * 0.022, wh), x + pad, y + pad, q)
                paste(canvas, T(p["chart_value"], "bold", W * 0.04, "#FF4D4D"), x + pad, y + pad + W * 0.035, q)
                for k in range(6):
                    bh = (h * 0.35) * (0.3 + 0.7 * ((k * 37) % 10) / 10) * ease_out_cubic((lt - 0.3 - k * 0.05) / 0.4)
                    d.rectangle((x + pad + k * w * 0.13, y + h - pad - bh, x + pad + k * w * 0.13 + w * 0.09, y + h - pad), fill=(255, 77, 77, a))
            elif i == 2:
                paste(canvas, T(p["progress_label"], "semibold", W * 0.024, wh), x + pad, y + pad, q)
                pr = float(p["progress"]) * ease_out_cubic((lt - 0.3) / max(0.5, self.dur * 0.6))
                d.rounded_rectangle((x + pad, y + h * 0.6, x + w - pad, y + h * 0.6 + W * 0.018), radius=W * 0.009, fill=(255, 255, 255, a // 3))
                d.rounded_rectangle((x + pad, y + h * 0.6, x + pad + (w - 2 * pad) * pr, y + h * 0.6 + W * 0.018), radius=W * 0.009, fill=(255, 255, 255, a))
            else:
                r = min(w, h) * 0.32; ccx, ccy = x + w / 2, y + h / 2; pr = float(p["progress"]) * ease_out_cubic((lt - 0.3) / max(0.5, self.dur * 0.6))
                d.arc((ccx - r, ccy - r, ccx + r, ccy + r), 0, 360, fill=(255, 255, 255, a // 3), width=int(W * 0.018))
                d.arc((ccx - r, ccy - r, ccx + r, ccy + r), -90, -90 + 360 * pr, fill=(52, 199, 89, a), width=int(W * 0.018))
                paste(canvas, T(f"{int(pr * 100)}%", "bold", W * 0.035, wh), ccx, ccy, q, center=True)

@register
class RedCollage(FX):
    name = "red-collage"; help = "Black & white you, a giant red word behind, three lines slam in"
    params = {"word": "EDIT", "lines": ["ONE CLIP.", "34 EFFECTS.", "ZERO APPS."], "color": "#FF2A2A"}
    def grade(self, c, img, lt):
        a = self.env(lt, 0.15, 0.3); return img * (1 - a) + (to_gray(img) * 1.1 - 10) * a
    def bgfx(self, c, img, lt):
        return img * (1 - 0.35 * self.env(lt, 0.15, 0.3))
    def behind(self, c, canvas, lt):
        W, H = c.W, c.H; t = str(self.p["word"]).upper()
        im = T(t, "display", fit_size(t, "display", W * 0.98, H * 0.22), self.p["color"])
        g = im.filter(ImageFilter.GaussianBlur(W * 0.02)); g.alpha_composite(im)
        paste(canvas, g, W / 2, H * 0.03 + im.height / 2 + (1 - ease_out_back(lt / 0.35)) * -H * 0.2, self.env(lt, 0.1, 0.3), center=True)
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; ls = as_list(self.p["lines"]); y0 = H * 0.6
        for i, ln in enumerate(ls):
            q = (lt - 0.3 - i * 0.3) / 0.15
            if q <= 0: continue
            col = self.p["color"] if i == 1 else "#FFFFFF"
            im = shadowed(T(ln, "display", fit_size(ln, "display", W * 0.85, W * 0.11), col), int(W * 0.012), (0, 4), 200)
            paste(canvas, scale_img(im, lerp(1.8, 1, ease_out_cubic(q))), W * 0.07 + im.width / 2, y0 + i * W * 0.12, self.outa(lt) * clamp(q * 2), center=True)

# ================================================================= effects 25-36
def rich_line(text, kind, size, color, hi_bg, hi_fg):
    """'Claude [edits] my reels.' -> words in [] get a highlight box"""
    parts, out, x, h = [], [], 0, 0
    for tok in str(text).replace("[", " [").replace("]", "] ").split():
        hi = tok.startswith("[")
        tok = tok.strip("[]")
        im = T(tok, kind, size, hi_fg if hi else color)
        if hi:
            bx = card(im.width + size * 0.3, im.height + size * 0.3, size * 0.12, hi_bg)
            paste(bx, im, size * 0.15, size * 0.15); im = bx
        out.append(im); h = max(h, im.height)
    sp = size * 0.25; w = int(sum(i.width for i in out) + sp * (len(out) - 1))
    line = Image.new("RGBA", (max(1, w), max(1, h)), (0, 0, 0, 0))
    for im in out:
        paste(line, im, x, (h - im.height) / 2); x += im.width + sp
    return line

@register
class SplitHeadline(FX):
    name = "split-headline"; help = "Headline card slides down and pushes you to the bottom half. [word] = highlight; | = new line"
    params = {"text": "Claude [edits] my|reels.", "accent": "#22C55E", "bg": "#F7F5F0", "chip": "in seconds ↗"}
    def _h(self, c): return c.H * 0.36
    def post(self, c, img, lt):
        q = ease_out_cubic(lt / 0.45) * self.outa(lt, 0.35)
        if q <= 0: return img
        off = self._h(c) * q
        return affine(img, 1.0, c.W / 2, c.H / 2, c.W, c.H, 0, off, border=cv2.BORDER_REPLICATE)
    def top(self, c, canvas, lt):
        q = ease_out_cubic(lt / 0.45) * self.outa(lt, 0.35)
        if q <= 0: return
        W = c.W; h = self._h(c); panel = Image.new("RGBA", (W, int(h)), rgba(self.p["bg"]))
        y = W * 0.07
        for ln in as_list(self.p["text"]):
            im = rich_line(ln, "heavy", W * 0.1, (17, 17, 17, 255), rgba(self.p["accent"]), (255, 255, 255, 255))
            paste(panel, im, W * 0.07, y); y += im.height + W * 0.015
        if self.p.get("chip"):
            ch = card(W * 0.22, W * 0.05, W * 0.025, rgba(self.p["accent"]))
            paste(ch, T(self.p["chip"], "sym", W * 0.024), ch.width / 2, ch.height / 2, center=True)
            paste(panel, ch, W * 0.71, h - W * 0.08)
        paste(canvas, panel, 0, h * q - h)

@register
class PastelWord(FX):
    name = "pastel-word"; help = "Lavender room, a giant word behind you, a profile card gets followed"
    params = {"word": "REELS", "bg": ["#C9B8F5", "#E9E0FF"], "name": "Your Name", "handle": "@yourhandle"}
    def bgfx(self, c, img, lt):
        a = self.env(lt, 0.3, 0.3); bg = vgrad(c, *as_list(self.p["bg"])[:2])
        return img * (1 - a) + bg * a
    def behind(self, c, canvas, lt):
        BackdropWord.behind(type("o", (), {"p": {"text": self.p["word"], "color": "#FFFFFF", "style": "heavy",
                            "y": None, "glow": False}, "env": self.env, "dur": self.dur})(), c, canvas, lt)
    def front(self, c, canvas, lt):
        if lt < 0.4: return
        Tap.front(type("o", (), {"p": {"name": self.p["name"], "handle": self.p["handle"], "accent": "#111111"},
                  "dur": self.dur - 0.4, "env": lambda s, l, a=0.2, b=0.3: self.env(l + 0.4, 0.6, 0.3), "chin": self.chin})(),
                  c, canvas, lt - 0.4)

@register
class CheckPills(FX):
    name = "check-pills"; help = "Grid-paper room, your reels pinned behind you, blue pills get clicked"
    params = {"pills": ["Hook", "Cuts", "Captions", "B-roll"], "images": None, "accent": "#2563EB"}
    def bgfx(self, c, img, lt):
        a = self.env(lt, 0.3, 0.3); bg = solid(c, "#F4F6FA"); step = int(c.W / 18)
        bg[::step, :] = (205, 215, 235); bg[:, ::step] = (205, 215, 235)
        return img * (1 - a) + bg * a
    def behind(self, c, canvas, lt):
        W, H = c.W, c.H; ims = load_images(self.p["images"], 2, int(W * 0.34), int(W * 0.34 * 1.1))
        for i, im in enumerate(ims):
            q = ease_out_back((lt - 0.15 * i) / 0.4)
            if q <= 0: continue
            x = W * (0.2 if i == 0 else 0.8); y = H * 0.12 + i * W * 0.04
            paste(canvas, rot(shadowed(framed(im, W * 0.02, W * 0.012)), 6 if i == 0 else -5), x, y, q * self.outa(lt), center=True)
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; pills = as_list(self.p["pills"]); cx, cy, fw, fh = c.face
        spots = [(cx - fw * 1.3, cy + fh * 1.2), (cx - fw * 0.5, cy + fh * 1.6), (cx + fw * 1.25, cy + fh * 1.0), (cx + fw * 1.4, cy + fh * 1.55)]
        for i, p in enumerate(pills):
            t0 = 0.3 + i * (self.dur - 0.6) / max(1, len(pills)); q = ease_out_back((lt - t0) / 0.3)
            if q <= 0: continue
            on = lt > t0 + 0.35
            pill = card(font("bold", W * 0.03).getbbox(p)[2] + W * 0.1, W * 0.065, W * 0.0325, rgba(self.p["accent"]))
            paste(pill, T(p + (" ✓" if on else ""), "sym", W * 0.03), pill.width / 2, pill.height / 2, center=True)
            x, y = spots[i % 4]; x = clamp(x, pill.width / 2, W - pill.width / 2)
            paste(canvas, scale_img(pill, q), x, y, self.outa(lt), center=True)
            if lt - t0 < 0.6: paste(canvas, cursor_img(W * 0.04), x + pill.width * 0.3, y + W * 0.01, clamp((0.6 - (lt - t0)) / 0.2))

@register
class Timeline(FX):
    name = "timeline"; help = "Dark red film look with an editing timeline and a glowing playhead"
    params = {"title": "AUTO-EDIT", "sub": "timeline by Claude", "color": "#E53935"}
    def grade(self, c, img, lt):
        a = self.env(lt, 0.3, 0.3); g = img * np.array([1.05, 0.62, 0.58]) * 0.85
        return img * (1 - a) + g * a
    def top(self, c, canvas, lt):
        W, H = c.W, c.H; a = self.env(lt, 0.3, 0.3); d = ImageDraw.Draw(canvas); col = rgba(self.p["color"], 255 * a)
        rec = "● REC " + f"00:{int(c.t) % 60:02d}"
        paste(canvas, T(rec, "sym", W * 0.026, (255, 255, 255, 255)), W * 0.06, H * 0.04, a)
        paste(canvas, T(self.p["title"], "display", W * 0.1), W * 0.06, H * 0.065, a)
        paste(canvas, T(self.p["sub"], "regular", W * 0.028, self.p["color"]), W * 0.06, H * 0.065 + W * 0.13, a)
        y0 = H * 0.8; th = W * 0.05; r = random.Random(2)
        d.rectangle((0, y0 - W * 0.06, W, H), fill=(15, 8, 8, int(200 * a)))
        for k in range(5):
            paste(canvas, T(f"00:0{k}", "mono", W * 0.02, (200, 200, 200, 255)), W * 0.04 + k * W * 0.2, y0 - W * 0.045, a)
        for row in range(3):
            x = W * 0.03 + r.uniform(0, W * 0.05); y = y0 + row * th * 1.3
            while x < W:
                w = r.uniform(W * 0.08, W * 0.25); reveal = clamp((lt - 0.2) / 0.6)
                if x < W * reveal: d.rounded_rectangle((x, y, min(W, x + w), y + th), radius=th * 0.25, fill=col)
                x += w + W * 0.015
        px = W * ((lt / self.dur) * 0.9 + 0.05)
        for g in range(4, 0, -1): d.line([(px, y0 - W * 0.06), (px, H)], fill=(255, 255, 255, int(40 * a)), width=g * 3)
        d.line([(px, y0 - W * 0.06), (px, H)], fill=(255, 255, 255, int(255 * a)), width=max(2, int(W * 0.004)))

@register
class Headline(FX):
    name = "headline"; help = "White headline card slides down at the top (goes behind your head if needed). | = 2nd line"
    params = {"text": "BIG NEWS|Here is why", "accent": "#E8432E"}
    def _covers(self, c): return self.head_top(c) < c.H * 0.07 + c.W * 0.3
    def behind(self, c, canvas, lt):
        if self._covers(c): self._draw(c, canvas, lt)
    def front(self, c, canvas, lt):
        if not self._covers(c): self._draw(c, canvas, lt)
    def _draw(self, c, canvas, lt):
        W, H = c.W, c.H; lines = as_list(self.p["text"]); bw = W * 0.86; pad = W * 0.05
        t1 = T(lines[0].upper(), "display", fit_size(lines[0].upper(), "display", bw - 2 * pad, W * 0.13), (15, 15, 15, 255))
        t2 = T(lines[1], "bold", fit_size(lines[1], "bold", bw - 2 * pad, W * 0.055), self.p["accent"]) if len(lines) > 1 else None
        bh = pad * 2 + t1.height + (t2.height + pad * 0.5 if t2 else 0)
        box = card(bw, bh, W * 0.035, (255, 255, 255, 245)); paste(box, t1, (bw - t1.width) / 2, pad)
        if t2: paste(box, t2, (bw - t2.width) / 2, pad * 1.5 + t1.height)
        paste(canvas, box, (W - bw) / 2, H * 0.07 - (1 - ease_out_back(lt / 0.45)) * (bh + H * 0.08), self.outa(lt))

@register
class HeadlineBox(FX):
    name = "headline-box"; help = "A punch-in with a clean two-line headline (black text on white boxes)"
    params = {"text": "How I got Claude|to edit my reels.", "zoom": 1.18}
    def post(self, c, img, lt):
        return zoom_on(img, c, 1 + (float(self.p["zoom"]) - 1) * ease_out_cubic(lt / 0.25) * self.outa(lt, 0.25))
    def top(self, c, canvas, lt):
        W, H = c.W, c.H; y = H * 0.09
        for i, ln in enumerate(as_list(self.p["text"])):
            q = ease_out_back((lt - 0.1 - i * 0.12) / 0.35)
            if q <= 0: continue
            t = T(ln, "heavy", fit_size(ln, "heavy", W * 0.78, W * 0.075), "#111111")
            bx = card(t.width + W * 0.05, t.height + W * 0.035, W * 0.012, (255, 255, 255, 250)); paste(bx, t, W * 0.025, W * 0.0175)
            paste(canvas, scale_img(bx, q), W / 2, y + bx.height / 2, self.outa(lt), center=True); y += bx.height + W * 0.005

def count_fmt(v, fmt="{:,}"):
    try: return fmt.format(int(v))
    except Exception: return str(v)

@register
class ProfileWall(FX):
    name = "profile-wall"; help = "Your reels grid fills the wall while a follower counter ticks up"
    params = {"images": None, "count": 197000, "label": "followers", "handle": "@yourhandle"}
    def behind(self, c, canvas, lt):
        W, H = c.W, c.H; cols, rows = 3, 2; gw = W * 0.86; cw = (gw - W * 0.02 * 2) / 3; chh = cw * 1.25
        ims = load_images(self.p["images"], 6, int(cw), int(chh))
        panel = card(gw + W * 0.04, chh * rows + W * 0.12, W * 0.03, (18, 18, 20, 240)); d = ImageDraw.Draw(panel)
        for i, tab in enumerate(["Posts", "Reels", "Tagged"]):
            paste(panel, T(tab, "semibold", W * 0.026, (255, 255, 255, 255) if i == 1 else (140, 140, 140, 255)), W * 0.1 + i * W * 0.28, W * 0.025)
        for i, im in enumerate(ims):
            q = ease_out_back((lt - 0.1 - i * 0.08) / 0.3)
            if q <= 0: continue
            x = W * 0.02 + (i % 3) * (cw + W * 0.02); y = W * 0.09 + (i // 3) * (chh + W * 0.01)
            paste(panel, scale_img(rounded(im, W * 0.012), q), x + cw / 2, y + chh / 2, center=True)
        paste(canvas, panel, W / 2, H * 0.03 + panel.height / 2 - (1 - ease_out_cubic(lt / 0.4)) * H * 0.3, self.outa(lt), center=True)
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; v = int(float(self.p["count"]) * ease_out_cubic((lt - 0.3) / max(0.6, self.dur * 0.6)))
        bx = card(W * 0.64, W * 0.26, W * 0.04, (20, 20, 22, 235))
        paste(bx, T(count_fmt(v), "display", W * 0.1), bx.width / 2, W * 0.09, center=True)
        paste(bx, T(self.p["handle"], "semibold", W * 0.028), W * 0.05, W * 0.19)
        f = card(W * 0.17, W * 0.055, W * 0.0275, (255, 255, 255, 255)); paste(f, T("Follow", "bold", W * 0.026, "#111111"), f.width / 2, f.height / 2, center=True)
        paste(bx, f, bx.width - W * 0.22, W * 0.18)
        paste(canvas, bx, W / 2, min(self.chin(c) + H * 0.14, H * 0.85), self.env(lt, 0.3, 0.25), center=True)

@register
class TierList(FX):
    name = "tier-list"; help = "A tier list drops in and your pick flies into S tier"
    params = {"tiers": {"S": [], "A": ["templates"], "B": ["timelines"], "C": ["apps"], "D": ["doing it by hand"]}, "winner": "Claude", "accent": "#F97316"}
    COLS = {"S": "#FF7F7F", "A": "#FFBF7F", "B": "#FFDF7F", "C": "#BFFF7F", "D": "#7FBFFF", "F": "#BF7FFF"}
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; tiers = self.p["tiers"]; keys = list(tiers.keys()); rh = W * 0.095; tw = W * 0.86
        panel = card(tw, rh * len(keys) + W * 0.03, W * 0.025, (24, 24, 26, 235)); d = ImageDraw.Draw(panel)
        for i, k in enumerate(keys):
            y = W * 0.015 + i * rh
            d.rounded_rectangle((W * 0.015, y + 3, W * 0.015 + rh - 6, y + rh - 3), radius=W * 0.01, fill=rgba(self.COLS.get(k, "#999999")))
            paste(panel, T(k, "bold", rh * 0.45, "#111111"), W * 0.015 + (rh - 6) / 2, y + rh / 2, center=True)
            x = W * 0.03 + rh
            for it in as_list(tiers[k]):
                ch = card(font("semibold", W * 0.032).getbbox(it)[2] + W * 0.04, rh * 0.62, W * 0.012, (60, 60, 65, 255))
                paste(ch, T(it, "semibold", W * 0.032), ch.width / 2, ch.height / 2, center=True); paste(panel, ch, x, y + rh * 0.19); x += ch.width + W * 0.012
        py = min(self.chin(c) + H * 0.03, H * 0.97 - panel.height) + (1 - ease_out_back(lt / 0.4)) * H * 0.4
        px = (W - tw) / 2; paste(canvas, panel, px, py, self.outa(lt))
        q = ease_in_out((lt - self.dur * 0.4) / 0.6)
        win = card(font("bold", W * 0.036).getbbox(self.p["winner"])[2] + W * 0.05, rh * 0.62, W * 0.012, rgba(self.p["accent"]))
        paste(win, T(self.p["winner"], "bold", W * 0.036), win.width / 2, win.height / 2, center=True)
        sx, sy = W * 0.9, c.face[1] - c.face[3]; ex, ey = px + W * 0.03 + rh + win.width / 2, py + W * 0.015 + rh / 2
        if lt > self.dur * 0.25:
            x = lerp(sx, ex, q); y = lerp(sy, ey, q) - math.sin(q * math.pi) * H * 0.08
            paste(canvas, rot(win, (1 - q) * 25), x, y, self.outa(lt), center=True)

@register
class BrollSplit(FX):
    name = "broll-split"; help = "B-roll (image or video) on top, you below, with a price-tag sticker"
    params = {"broll": None, "tag": "4 hrs → 4 min", "word": "CLAUDIT", "color": "#FF8A80"}
    def _broll(self, c, lt):
        st = self.__dict__.setdefault("_s", {}); src = self.p.get("broll"); h = c.H // 2
        if src and str(src).lower().endswith((".mp4", ".mov", ".m4v", ".webm")):
            cap = st.setdefault("cap", cv2.VideoCapture(src)); ok, fr = cap.read()
            if not ok: cap.set(cv2.CAP_PROP_POS_FRAMES, 0); ok, fr = cap.read()
            if ok:
                fr = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB); s = max(c.W / fr.shape[1], h / fr.shape[0])
                fr = cv2.resize(fr, (int(fr.shape[1] * s) + 1, int(fr.shape[0] * s) + 1)); y0 = (fr.shape[0] - h) // 2; x0 = (fr.shape[1] - c.W) // 2
                return fr[y0:y0 + h, x0:x0 + c.W].astype(np.float32)
        if "img" not in st:
            if src and os.path.exists(str(src)):
                st["img"] = np.asarray(load_images([src], 1, c.W, h)[0].convert("RGB"), np.float32)
            else:   # default: darkened, spotlit copy of the first frame with the word
                g = (c.raw.astype(np.float32) * 0.25)[:h]; st["img"] = g
        return st["img"]
    def post(self, c, img, lt):
        q = ease_out_cubic(lt / 0.35) * self.outa(lt, 0.3)
        if q <= 0: return img
        h = c.H // 2; you = zoom_on(img, c, 1.0, cy=c.face[1] + c.H * 0.2)
        out = img.copy(); top = self._broll(c, lt)
        out[:h] = top * q + img[:h] * (1 - q); out[h:] = you[c.H // 4:c.H // 4 + (c.H - h)]
        return out
    def top(self, c, canvas, lt):
        W, H = c.W, c.H; q = ease_out_back((lt - 0.4) / 0.35)
        if not self.p.get("broll") and self.p.get("word"):
            w = str(self.p["word"]).upper(); paste(canvas, T(w, "serif", fit_size(w, "serif", W * 0.9, H * 0.12), self.p["color"]), W / 2, H * 0.18, self.outa(lt), center=True)
        if q <= 0: return
        tag = card(font("heavy", W * 0.045).getbbox(self.p["tag"])[2] + W * 0.08, W * 0.09, W * 0.015, (255, 255, 255, 255))
        d = ImageDraw.Draw(tag); d.ellipse((W * 0.015, tag.height / 2 - W * 0.01, W * 0.035, tag.height / 2 + W * 0.01), fill=(30, 30, 30, 255))
        paste(tag, T(self.p["tag"], "sym", W * 0.045, "#111111"), W * 0.05, tag.height / 2 - W * 0.028)
        paste(canvas, rot(shadowed(scale_img(tag, q)), 8), W * 0.55, H / 2, self.outa(lt), center=True)

@register
class PhoneFan(FX):
    name = "phone-fan"; help = "Your reels fan out like a hand of phones"
    params = {"images": None, "count": 4}
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; n = int(self.p["count"]); pw = W * 0.24; ph = pw * 2.05
        ims = load_images(self.p["images"], n, int(pw * 0.92), int(ph * 0.94))
        q = ease_out_back(lt / 0.55); base_y = min(self.chin(c) + H * 0.2, H * 0.78)
        for i, im in enumerate(ims):
            phone = card(pw, ph, pw * 0.16, (15, 15, 15, 255)); paste(phone, rounded(im, pw * 0.12), pw * 0.04, ph * 0.03)
            ang = lerp(-24, 24, i / max(1, n - 1)) * q; x = W / 2 + lerp(-1, 1, i / max(1, n - 1)) * W * 0.26 * q
            paste(canvas, rot(shadowed(phone), -ang), x, base_y + abs(ang) * W * 0.002, self.outa(lt), center=True)

@register
class DotReveal(FX):
    name = "dot-reveal"; help = "Your shot builds out of glowing dots, then snaps into focus"
    params = {"color": "#F5A623", "cell": 18}
    def post(self, c, img, lt):
        snap = self.dur * 0.65; q = clamp((lt - snap) / 0.2)
        if q >= 1: return img
        cell = max(6, int(c.W / 1080 * float(self.p["cell"]))); gw, gh = c.W // cell, c.H // cell
        small = cv2.resize(img, (gw, gh), interpolation=cv2.INTER_AREA); lum = small.mean(axis=2) / 255
        grow = ease_out_cubic(lt / max(0.3, snap * 0.8))
        rng = np.random.default_rng(5).random((gh, gw)); vis = rng < grow
        dots = np.zeros_like(img); col = np.array(hex2rgb(self.p["color"]), np.float32)
        for y, x in zip(*np.nonzero(vis)):
            r = int(cell * 0.5 * (0.2 + 0.8 * lum[y, x]))
            if r > 0: cv2.circle(dots, (x * cell + cell // 2, y * cell + cell // 2), r, (col * (0.4 + 0.6 * lum[y, x])).tolist(), -1, cv2.LINE_AA)
        glow = cv2.GaussianBlur(dots, (0, 0), cell * 0.6)
        dots = np.clip(dots + glow * 0.6, 0, 255)
        return dots * (1 - q) + img * q

@register
class HeadlineWall(FX):
    name = "headline-wall"; help = "Your headlines pile up behind your head, then a total pops in front"
    params = {"headlines": ["Same prompt, two models", "The new AI model is cheaper", "Protect your personal data", "Easiest no-code automation", "Scrape anything in 5 min"], "total": "672K", "total_label": "views from 7 reels", "accent": "#F97316"}
    def behind(self, c, canvas, lt):
        W, H = c.W, c.H; hs = as_list(self.p["headlines"]); r = random.Random(9)
        for i, h in enumerate(hs):
            q = ease_out_back((lt - i * self.dur * 0.5 / len(hs)) / 0.25)
            yellow = i % 3 == 1
            bx = card(W * 0.42, W * 0.22, W * 0.02, (255, 214, 10, 250) if yellow else (255, 255, 255, 250))
            for j, ln in enumerate(wrap(h, "bold", W * 0.03, W * 0.36)[:3]):
                paste(bx, T(ln, "bold", W * 0.03, "#111111"), W * 0.03, W * 0.03 + j * W * 0.04)
            paste(bx, T("@you • 40K views", "regular", W * 0.018, "#777777"), W * 0.03, W * 0.18)
            x = r.uniform(0.25, 0.75) * W; y = r.uniform(0.09, 0.33) * H
            if q > 0: paste(canvas, rot(shadowed(scale_img(bx, q), 12, (0, 6), 80), r.uniform(-12, 12)), x, y, self.outa(lt), center=True)
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; q = ease_out_elastic((lt - self.dur * 0.6) / 0.6)
        if lt < self.dur * 0.6: return
        t = T(self.p["total"], "display", W * 0.09); l = T(self.p["total_label"], "semibold", W * 0.028)
        bx = card(t.width + l.width + W * 0.1, W * 0.13, W * 0.025, rgba(self.p["accent"]))
        paste(bx, t, W * 0.035, (bx.height - t.height) / 2); paste(bx, l, W * 0.065 + t.width, (bx.height - l.height) / 2)
        paste(canvas, rot(scale_img(bx, max(0.05, q)), -3), W / 2, min(self.chin(c) + H * 0.12, H * 0.82), self.outa(lt), center=True)

@register
class Checklist(FX):
    name = "checklist"; help = "Task list card under your chin, each step ticks green (style: dark|light)"
    params = {"title": "Claude is editing your clip", "items": ["Found your face", "Cut you out of the room", "Put the text behind you", "Graded the colour", "Rendered in 4K"],
              "notes": ["every frame", "AI mask", "depth", "warm", "2160p"], "accent": "#22C55E", "style": "dark"}
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; items = as_list(self.p["items"]); notes = as_list(self.p.get("notes")); n = len(items); dark = self.p.get("style") == "dark"
        fg = (240, 240, 240, 255) if dark else (25, 25, 25, 255); mute = (130, 130, 130, 255)
        cw = W * 0.8; pad = W * 0.04; rh = W * 0.075; th = W * 0.065 if self.p.get("title") else 0
        ch = pad * 2 + th + rh * n
        box = card(cw, ch, W * 0.04, (22, 22, 24, 235) if dark else (255, 255, 255, 238)); d = ImageDraw.Draw(box)
        step = (self.dur - 0.6) / max(1, n); acc = rgba(self.p["accent"])
        if th:
            done_n = sum(1 for i in range(n) if lt > 0.35 + step * (i + 0.55))
            paste(box, T("✳ " + self.p["title"], "sym", W * 0.03, "#F97316" if dark else "#111111"), pad, pad)
            paste(box, T(f"{done_n} of {n}", "regular", W * 0.022, mute), cw - pad - W * 0.08, pad + W * 0.005)
        for i, it in enumerate(items):
            t0 = 0.35 + i * step
            if lt < t0: continue
            ya = ease_out_cubic((lt - t0) / 0.2); y = pad + th + i * rh + (1 - ya) * rh * 0.3
            r = rh * 0.26; ccx = pad + r; ccy = y + rh / 2; done = lt > t0 + step * 0.55
            if done:
                d.ellipse((ccx - r, ccy - r, ccx + r, ccy + r), fill=acc); draw_check(d, ccx, ccy, r * 1.1, (255, 255, 255, 255), r * 0.3)
            else:
                d.ellipse((ccx - r, ccy - r, ccx + r, ccy + r), outline=mute, width=max(2, int(r * 0.18)))
            ti = T(it, "semibold", W * 0.032, fg); ti.putalpha(ti.getchannel("A").point(lambda v: int(v * ya)))
            box.alpha_composite(ti, dest=(int(pad + r * 2 + pad * 0.5), int(ccy - ti.height / 2)))
            if i < len(notes) and notes[i]:
                nt = T(notes[i], "mono", W * 0.02, mute); paste(box, nt, cw - pad - nt.width, ccy - nt.height / 2, ya)
        y = min(self.chin(c) + H * 0.03, H * 0.96 - ch) + (1 - ease_out_cubic(lt / 0.35)) * H * 0.1
        paste(canvas, box, (W - cw) / 2, y, self.env(lt, 0.25, 0.25))

@register
class NameTag(FX):
    name = "name-tag"; help = "Lower-third with your name and title"
    params = {"name": "Your Name", "title": "Creator", "accent": "#F59E0B"}
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; t1 = T(self.p["name"], "display", W * 0.075); t2 = T(self.p["title"], "bold", W * 0.038, (20, 20, 20, 255))
        pad = W * 0.03
        b1 = card(t1.width + pad * 2, t1.height + pad * 1.4, W * 0.015, (15, 15, 15, 235)); paste(b1, t1, pad, pad * 0.7)
        b2 = card(t2.width + pad * 2, t2.height + pad * 1.2, W * 0.015, rgba(self.p["accent"])); paste(b2, t2, pad, pad * 0.6)
        x1 = W * 0.06 - (1 - ease_out_cubic(lt / 0.35)) * (b1.width + W * 0.1); x2 = W * 0.06 - (1 - ease_out_cubic((lt - 0.12) / 0.35)) * (b2.width + W * 0.1)
        a = self.outa(lt); paste(canvas, b1, x1, H * 0.76, a); paste(canvas, b2, x2, H * 0.76 + b1.height + W * 0.01, a)

# ================================================================= effects 37-45 + motion basics
@register
class PunchIn(FX):
    name = "lean-in"; aliases = ["punch-in"]; help = "A quick punch-in zoom on one word"
    params = {"zoom": 1.3}
    def post(self, c, img, lt):
        z = 1 + (float(self.p["zoom"]) - 1) * ease_out_cubic(lt / 0.18) * self.outa(lt, 0.18)
        return zoom_on(img, c, z) if z > 1.001 else img

@register
class SlowPush(FX):
    name = "slow-push"; help = "Slow cinematic push-in while the room melts out of focus"
    params = {"zoom": 1.15}
    def bgfx(self, c, img, lt):
        a = ease_out_cubic(lt / 0.8)
        return img * (1 - a) + cv2.GaussianBlur(img, (0, 0), c.W / 200) * a if a > 0.01 else img
    def post(self, c, img, lt):
        return zoom_on(img, c, 1 + (float(self.p["zoom"]) - 1) * ease_in_out(lt / self.dur))

class _OrbitBase(FX):
    def _cards(self, c): return []
    def _layout(self, c, lt):
        cx, cy, fw, fh = c.face; rx = max(c.W * 0.36, fw * 1.25); ry = fh * float(self.p.get("tilt", 1.05))
        cards = self._cards(c); n = len(cards); res = []
        for i, ch in enumerate(cards):
            th = 2 * math.pi * (i / n + lt * float(self.p["speed"]))
            front = -math.cos(th); res.append((front, cx + rx * math.sin(th), cy - fh * 0.1 - ry * math.cos(th), th, ch))
        return sorted(res, key=lambda r: r[0])
    def _draw(self, c, canvas, lt, want_front):
        a = self.env(lt, 0.3, 0.3)
        for front, x, y, th, ch in self._layout(c, lt):
            if (front > 0) != want_front: continue
            sc = 0.8 + 0.2 * (front + 1) / 2
            sx = sc * (max(0.15, abs(math.cos(th))) if self.p.get("flat3d") else 1)
            paste(canvas, scale_img(ch, sx, sc), x, y, a, center=True)
    def behind(self, c, canvas, lt): self._draw(c, canvas, lt, False)
    def front(self, c, canvas, lt): self._draw(c, canvas, lt, True)

@register
class Orbit(_OrbitBase):
    name = "orbit"; help = "Your reels (or text chips) circle your head - behind at the top, below the chin in front"
    params = {"items": None, "images": None, "count": 5, "speed": 0.33}
    def _cards(self, c):
        st = self.__dict__.setdefault("_s", {})
        if "c" in st: return st["c"]
        W = c.W
        if self.p.get("items") and not self.p.get("images"):
            out = []
            for s in as_list(self.p["items"]):
                t = T(s, "bold", W * 0.045, (20, 20, 20, 255)); ch = card(t.width + W * 0.07, t.height + W * 0.045, W * 0.04, (255, 255, 255, 240))
                paste(ch, t, ch.width / 2, ch.height / 2, center=True); out.append(ch)
        else:
            tw = int(W * 0.16); out = [framed(im, tw * 0.1, 4) for im in load_images(self.p.get("images"), int(self.p["count"]), tw, int(tw * 16 / 9))]
        st["c"] = out; return out

@register
class CarouselSpin(_OrbitBase):
    name = "carousel-spin"; help = "Your reels spin around you in a 3D carousel"
    params = {"images": None, "count": 6, "speed": 0.22, "tilt": 0.35, "flat3d": True}
    def _cards(self, c):
        st = self.__dict__.setdefault("_s", {})
        if "c" not in st:
            tw = int(c.W * 0.22); st["c"] = [framed(im, tw * 0.08, 5) for im in load_images(self.p.get("images"), int(self.p["count"]), tw, int(tw * 16 / 9))]
        return st["c"]

def line_graph(w, h, vals, q, color=(255, 255, 255, 255), fill=True):
    im = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    vals = [float(v) for v in vals]; mn, mx = min(vals), max(vals); n = len(vals)
    pts = [(w * i / (n - 1), h - (v - mn) / ((mx - mn) or 1) * h * 0.85 - h * 0.05) for i, v in enumerate(vals)]
    k = q * (n - 1); m = int(k); seg = pts[:m + 1]
    if m < n - 1: seg.append((lerp(pts[m][0], pts[m + 1][0], k - m), lerp(pts[m][1], pts[m + 1][1], k - m)))
    if len(seg) > 1:
        if fill: d.polygon(seg + [(seg[-1][0], h), (0, h)], fill=color[:3] + (60,))
        d.line(seg, fill=color, width=max(3, int(w * 0.012)), joint="curve")
        x, y = seg[-1]; r = w * 0.02; d.ellipse((x - r, y - r, x + r, y + r), fill=color)
    return im

@register
class LiquidGlassGraph(FX):
    name = "liquid-glass-graph"; help = "Liquid glass card with a climbing graph and a counting number (look=bento for a glass dashboard)"
    params = {"value": 197000, "prefix": "", "suffix": "", "label": "views this month", "values": [3, 4, 3.5, 6, 5.5, 8, 9.5, 13], "look": "card"}
    def _box(self, c):
        W = c.W; w, h = W * 0.78, W * 0.5; return ((W - w) / 2, min(self.chin(c) + c.H * 0.02, c.H * 0.95 - h), w, h)
    def _q(self, lt): return ease_out_cubic((lt - 0.2) / max(0.6, self.dur * 0.6))
    def grade(self, c, img, lt):
        a = self.env(lt, 0.3, 0.3); x, y, w, h = self._box(c)
        frost(img, x, y, w, h, c.W * 0.05, amount=0.18, alpha=a)
        if self.p["look"] == "bento":
            W = c.W
            for bx in [(W * 0.04, c.H * 0.05, W * 0.28, W * 0.28), (W * 0.68, c.H * 0.05, W * 0.28, W * 0.28)]:
                frost(img, *bx, W * 0.04, amount=0.2, alpha=a)
        return img
    def front(self, c, canvas, lt):
        W = c.W; a = self.env(lt, 0.3, 0.3); x, y, w, h = self._box(c); q = self._q(lt); pad = W * 0.04
        ImageDraw.Draw(canvas).rounded_rectangle((x, y, x + w, y + h), radius=W * 0.05, outline=(255, 255, 255, int(150 * a)), width=2)
        v = float(self.p["value"]) * q
        paste(canvas, T(f"{self.p['prefix']}{count_fmt(v)}{self.p['suffix']}", "display", W * 0.09), x + pad, y + pad, a)
        paste(canvas, T(self.p["label"], "semibold", W * 0.028), x + pad, y + pad + W * 0.12, a)
        paste(canvas, line_graph(w - 2 * pad, h * 0.4, self.p["values"], q), x + pad, y + h - pad - h * 0.4, a)
        if self.p["look"] == "bento":
            paste(canvas, T("↑ 38%", "sym", W * 0.06, "#4ADE80"), W * 0.18, c.H * 0.05 + W * 0.14, a, center=True)
            paste(canvas, T(f"{int(q * 21)}", "display", W * 0.1), W * 0.82, c.H * 0.05 + W * 0.12, a, center=True)
            paste(canvas, T("reels", "semibold", W * 0.026), W * 0.82, c.H * 0.05 + W * 0.22, a, center=True)

@register
class MatchCut(FX):
    name = "match-cut"; help = "News pages cut on one word, locked in place behind your head"
    params = {"pages": ["AI EDITS VIDEO NOW", "CREATORS SKIP THE TIMELINE", "ONE PROMPT, ONE REEL", "THE EDITOR IS A CHAT"], "word": "AI", "color": "#D7263D"}
    def behind(self, c, canvas, lt):
        W, H = c.W, c.H; pages = as_list(self.p["pages"]); seg = self.dur / len(pages); i = min(len(pages) - 1, int(lt / seg))
        pw, ph = W * 0.9, H * 0.42; pg = Image.new("RGBA", (int(pw), int(ph)), (246, 242, 232, 255)); d = ImageDraw.Draw(pg)
        mast = ["THE DAILY", "MORNING POST", "THE TIMES OF CODE", "EVENING STAR"][i % 4]
        paste(pg, T(mast, "serif", W * 0.06, "#111111"), pw / 2, W * 0.06, center=True)
        d.line([(W * 0.04, W * 0.11), (pw - W * 0.04, W * 0.11)], fill=(20, 20, 20, 255), width=3)
        y = W * 0.14
        for ln in wrap(pages[i], "heavy", W * 0.075, pw - W * 0.08)[:3]:
            im = T(ln, "heavy", W * 0.075, "#111111"); paste(pg, im, W * 0.04, y); y += im.height + W * 0.015
        r = random.Random(i)
        while y < ph - W * 0.03:
            d.line([(W * 0.04, y), (W * 0.04 + r.uniform(0.5, 0.95) * (pw - W * 0.08), y)], fill=(160, 160, 160, 255), width=max(2, int(W * 0.008))); y += W * 0.03
        flash = clamp(1 - (lt - i * seg) / 0.08)
        paste(canvas, rot(pg, [-2, 1.5, -1, 2][i % 4]), W / 2, max(ph / 2 + H * 0.02, c.face[1] - c.face[3] * 0.4), self.env(lt, 0.05, 0.2), center=True)
        if flash > 0: canvas.alpha_composite(Image.new("RGBA", canvas.size, (255, 255, 255, int(120 * flash))))

@register
class Toggles(FX):
    name = "apple-toggles"; aliases = ["toggles"]; help = "Switches flip on under your chin, one line at a time"
    params = {"items": ["Face tracking", "Text behind me", "Colour grade", "Auto-render"], "accent": "#34C759"}
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; items = as_list(self.p["items"]); n = len(items); rh = W * 0.1; cw = W * 0.8
        box = card(cw, rh * n + W * 0.02, W * 0.045, (245, 245, 247, 238)); d = ImageDraw.Draw(box); step = (self.dur - 0.6) / max(1, n)
        for i, it in enumerate(items):
            y = W * 0.01 + i * rh
            if i: d.line([(W * 0.05, y), (cw - W * 0.04, y)], fill=(210, 210, 215, 255), width=2)
            paste(box, T(it, "semibold", W * 0.036, "#111111"), W * 0.05, y + rh / 2 - W * 0.022)
            on = clamp((lt - 0.4 - i * step) / 0.2)
            paste(box, toggle_img(W * 0.13, on, self.p["accent"]), cw - W * 0.05 - W * 0.065, y + rh / 2, center=True)
        y = min(self.chin(c) + H * 0.03, H * 0.96 - box.height) + (1 - ease_out_back(lt / 0.4)) * H * 0.1
        paste(canvas, box, (W - cw) / 2, y, self.env(lt, 0.2, 0.25))

@register
class LedSign(FX):
    name = "led-sign"; help = "The lights drop and a glowing LED sign types itself out behind you"
    params = {"text": "ON AIR", "color": "#FF5A1F", "dark": 0.8}
    def bgfx(self, c, img, lt):
        return img * (1 - float(self.p["dark"]) * ease_out_cubic(lt / 0.3) * self.outa(lt, 0.3))
    def behind(self, c, canvas, lt):
        W, H = c.W, c.H; txt = str(self.p["text"]).upper()
        k = int(len(txt) * clamp((lt - 0.3) / max(0.4, self.dur * 0.45))); shown = txt[:k]
        if not shown: return
        g = T(txt, "display", 40); cols = max(1, int(g.width / 40 * 9)); grid = T(shown, "display", 40)
        small = np.array(grid.resize((max(1, int(grid.width / 40 * 9)), 9)).getchannel("A")) > 90
        cell = min(W * 0.92 / cols, H * 0.18 / 9); pw, ph = cols * cell, 9 * cell
        led = Image.new("RGBA", (int(pw + cell * 2), int(ph + cell * 2)), (0, 0, 0, 0)); d = ImageDraw.Draw(led); col = rgba(self.p["color"])
        for y in range(9):
            for x in range(cols):
                on = x < small.shape[1] and small[y, x]; r = cell * 0.38; px, py = cell + x * cell + cell / 2, cell + y * cell + cell / 2
                d.ellipse((px - r, py - r, px + r, py + r), fill=col if on else (60, 30, 20, 120))
        glow = led.filter(ImageFilter.GaussianBlur(cell * 0.8)); glow.alpha_composite(led)
        paste(canvas, glow, W / 2, max(ph / 2 + H * 0.04, c.face[1] - c.face[3] * 0.5), self.outa(lt), center=True)

@register
class OverShoulder(FX):
    name = "over-the-shoulder-zoom"; help = "Pushes into one corner, a glass graph pops beside your head, then the other corner with a 2nd graph"
    params = {"graphs": [{"value": 21, "label": "reels", "values": [1, 2, 2, 4, 6, 9]}, {"value": 672000, "label": "views", "values": [2, 3, 5, 4, 8, 12]}], "zoom": 1.3}
    def _phase(self, lt):
        return 0 if lt < self.dur / 2 else 1
    def post(self, c, img, lt):
        ph = self._phase(lt); l2 = lt - ph * self.dur / 2; z = 1 + (float(self.p["zoom"]) - 1) * ease_in_out(l2 / 0.5) * (self.outa(lt, 0.3) if ph else 1)
        cx = c.face[0] + (-1 if ph == 0 else 1) * c.W * 0.15
        return zoom_on(img, c, z, cx=cx, cy=c.face[1] + c.H * 0.05)
    def grade(self, c, img, lt):
        ph = self._phase(lt); l2 = lt - ph * self.dur / 2; q = ease_out_back((l2 - 0.4) / 0.35)
        if q > 0.05:
            x, y, w, h = self._box(c, ph); frost(img, x, y, w, h, c.W * 0.04, alpha=clamp(q))
        return img
    def _box(self, c, ph):
        W = c.W; w, h = W * 0.36, W * 0.3; s = 1 if ph == 0 else -1
        return (clamp(c.face[0] + s * (c.face[2] * 0.7) - (0 if s > 0 else w), W * 0.02, W - w - W * 0.02), c.face[1] - h / 2, w, h)
    def front(self, c, canvas, lt):
        ph = self._phase(lt); l2 = lt - ph * self.dur / 2; q = clamp(ease_out_back((l2 - 0.4) / 0.35))
        if q < 0.2: return
        g = self.p["graphs"][ph % len(self.p["graphs"])]; x, y, w, h = self._box(c, ph); W = c.W; pad = W * 0.025
        paste(canvas, T(count_fmt(float(g["value"]) * ease_out_cubic((l2 - 0.4) / 0.8)), "display", W * 0.06), x + pad, y + pad, q)
        paste(canvas, T(g["label"], "semibold", W * 0.024), x + pad, y + pad + W * 0.08, q)
        paste(canvas, line_graph(w - 2 * pad, h * 0.38, g["values"], ease_out_cubic((l2 - 0.5) / 0.8)), x + pad, y + h - pad - h * 0.38, q)

@register
class Messages(FX):
    name = "messages"; help = "Message notifications pop in one after another with a soft glow"
    params = {"messages": [{"from": "Mom", "text": "Saw your reel!!"}, {"from": "Alex", "text": "how did you edit this??"}, {"from": "Sam", "text": "teach me pls"}], "accent": "#34C759"}
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; msgs = self.p["messages"]; n = len(msgs); bw = W * 0.86; bh = W * 0.15
        for i, m in enumerate(msgs):
            q = ease_out_back((lt - 0.2 - i * (self.dur * 0.55 / n)) / 0.35)
            if q <= 0: continue
            b = card(bw, bh, W * 0.04, (245, 245, 247, 235)); d = ImageDraw.Draw(b); r = bh * 0.3
            d.rounded_rectangle((W * 0.03, bh / 2 - r, W * 0.03 + 2 * r, bh / 2 + r), radius=r * 0.45, fill=rgba(self.p["accent"]))
            paste(b, T("✉", "sym", r, "#FFFFFF"), W * 0.03 + r, bh / 2, center=True)
            paste(b, T(m.get("from", ""), "bold", W * 0.032, "#111111"), W * 0.06 + 2 * r, bh * 0.2)
            paste(b, T(m.get("text", ""), "regular", W * 0.03, "#333333"), W * 0.06 + 2 * r, bh * 0.52)
            paste(b, T("now", "regular", W * 0.022, "#888888"), bw - W * 0.08, bh * 0.2)
            glow = Image.new("RGBA", (int(bw + 80), int(bh + 80)), (0, 0, 0, 0)); paste(glow, card(bw, bh, W * 0.04, (255, 255, 255, 150)), 40, 40)
            glow = glow.filter(ImageFilter.GaussianBlur(22)); glow.alpha_composite(b, (40, 40))
            slot = n - 1 - i   # newest at top
            y = H * 0.05 + bh / 2 + slot * (bh + W * 0.025) * 0 + i * (bh + W * 0.025)
            paste(canvas, scale_img(glow, q), W / 2, y, self.outa(lt), center=True)

@register
class PlaceInGrid(FX):
    name = "place-in-grid"; help = "You shrink into the centre of your 3x3 profile grid; reels pop in around you with view counts"
    params = {"images": None, "views": ["12K", "40K", "8K", "197K", "23K", "61K", "9K", "88K"]}
    def _geo(self, c):
        W, H = c.W, c.H; gap = W * 0.012; cw = (W - gap * 4) / 3; ch = cw * 16 / 9 * 0.75
        tot = ch * 3 + gap * 2; y0 = (H - tot) / 2; return gap, cw, ch, y0
    def post(self, c, img, lt):
        q = ease_in_out(lt / 0.6) * self.outa(lt, 0.4)
        if q <= 0: return img
        gap, cw, ch, y0 = self._geo(c); s = lerp(1, cw / c.W, q)
        # crop around the face to the cell aspect, then shrink
        tx = lerp(0, gap * 2 + cw - (c.W * s - cw) / 2, q); ty = lerp(0, y0 + ch + gap - (c.H * s - ch) / 2, q)
        out = place_frame(img, c, s, tx, ty, solid(c, "#0E0E10"))
        if q > 0.98:   # hard crop to the cell
            x0, y1 = int(gap * 2 + cw), int(y0 + ch + gap); bg = solid(c, "#0E0E10"); bg[y1:y1 + int(ch), x0:x0 + int(cw)] = out[y1:y1 + int(ch), x0:x0 + int(cw)]; out = bg
        return out
    def top(self, c, canvas, lt):
        if lt < 0.5: return
        gap, cw, ch, y0 = self._geo(c); W = c.W; ims = load_images(self.p["images"], 8, int(cw), int(ch)); views = as_list(self.p["views"]); k = 0
        for r in range(3):
            for col in range(3):
                if r == 1 and col == 1: continue
                q = ease_out_back((lt - 0.55 - k * 0.07) / 0.3)
                if q > 0:
                    im = ims[k].copy(); paste(im, T("▶ " + views[k % len(views)], "sym", W * 0.026), W * 0.02, im.height - W * 0.05)
                    paste(canvas, scale_img(im, q), gap + col * (cw + gap) + cw / 2, y0 + r * (ch + gap) + ch / 2, self.outa(lt), center=True)
                k += 1

# ================================================================= extra effects (Ram's pack)
@register
class Countup(FX):
    name = "countup"; help = "Big number counts up under your chin (e.g. followers, money)"
    params = {"value": 10000, "prefix": "", "suffix": "", "label": "followers", "accent": "#FACC15"}
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; v = float(self.p["value"]) * ease_out_cubic((lt - 0.1) / max(0.5, self.dur * 0.7))
        t = T(f"{self.p['prefix']}{count_fmt(v)}{self.p['suffix']}", "display", W * 0.16, self.p["accent"], stroke=4, stroke_fill=(0, 0, 0, 160))
        l = T(self.p["label"], "bold", W * 0.04, "#FFFFFF", stroke=2, stroke_fill=(0, 0, 0, 160))
        y = min(self.chin(c) + H * 0.1, H * 0.8); a = self.env(lt, 0.2, 0.25)
        paste(canvas, scale_img(t, ease_out_back(lt / 0.35)), W / 2, y, a, center=True); paste(canvas, l, W / 2, y + t.height * 0.75, a, center=True)

@register
class GlitterSpotlight(FX):
    name = "glitter-spotlight"; help = "Spotlight with golden rays and sparkles behind you"
    params = {"color": "#FFD36E", "dark": 0.8}
    def bgfx(self, c, img, lt):
        on = ease_out_cubic(lt / 0.4) * self.outa(lt, 0.3); img = img * (1 - float(self.p["dark"]) * on)
        cx, cy = c.face[0], c.face[1] - c.face[3]; ang = np.arctan2(c.Y - cy, c.X - cx)
        rays = (np.cos(ang * 9 + lt * 1.5) * 0.5 + 0.5) ** 6 * np.exp(-np.hypot(c.X - cx, c.Y - cy) / (c.W * 0.7))
        return img + rays[..., None] * np.array(hex2rgb(self.p["color"]), np.float32) * 0.9 * on
    def behind(self, c, canvas, lt):
        d = ImageDraw.Draw(canvas); r = random.Random(1); W, H = c.W, c.H; col = hex2rgb(self.p["color"])
        for i in range(70):
            x, y = r.uniform(0, W), r.uniform(0, H * 0.7); ph = r.uniform(0, 6.28); s = W * 0.012 * (0.5 + 0.5 * math.sin(lt * 6 + ph)) * self.env(lt)
            if s > 1: d.polygon([(x, y - s * 2), (x + s * 0.5, y), (x, y + s * 2), (x - s * 0.5, y)], fill=col + (230,)); d.polygon([(x - s * 2, y), (x, y + s * 0.5), (x + s * 2, y), (x, y - s * 0.5)], fill=col + (230,))

@register
class Confetti(FX):
    name = "confetti"; help = "Confetti burst falls over the frame"
    params = {"count": 140}
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; r = random.Random(7); d = ImageDraw.Draw(canvas); a = int(255 * self.outa(lt, 0.4))
        for i in range(int(self.p["count"])):
            vx, vy = r.uniform(-0.7, 0.7) * W, r.uniform(-1.3, -0.7) * H; x0 = W / 2 + r.uniform(-0.1, 0.1) * W; y0 = H * 0.8
            t = lt * 0.9; drag = 1 - math.exp(-t * 2.5); x = x0 + vx * drag * 0.5 + math.sin(t * 5 + i) * W * 0.02; y = y0 + vy * drag * 0.6 + 0.08 * H * t * t
            s = W * r.uniform(0.008, 0.016); sp = math.cos(t * 9 + i) * s
            col = rgba(PALETTE[i % 8], a); d.polygon([(x - s, y - sp), (x + s, y - sp * 0.3), (x + s, y + sp), (x - s, y + sp * 0.3)], fill=col)

@register
class Glitch(FX):
    name = "glitch"; help = "Digital glitch hit (RGB split + slice shifts)"
    params = {"amount": 1.0}
    def post(self, c, img, lt):
        a = float(self.p["amount"]) * (0.4 + 0.6 * (int(lt * 15) % 2)) * self.env(lt, 0.05, 0.1)
        return glitch_img(img, a, int(lt * 30))

@register
class VHS(FX):
    name = "vhs"; help = "VHS tape look: scanlines, noise, colour bleed, date stamp"
    params = {"date": "PLAY ▶  OCT 30 2026"}
    def post(self, c, img, lt):
        a = self.env(lt, 0.2, 0.2); g = img.copy(); s = max(2, int(c.W * 0.004))
        g[..., 0] = np.roll(g[..., 0], s, axis=1); g[..., 2] = np.roll(g[..., 2], -s, axis=1)
        g[::3] *= 0.82; g = g * np.array([1.04, 0.98, 0.95]) + np.random.default_rng(int(lt * 100)).normal(0, 9, g.shape[:2])[..., None]
        y = int((lt * 0.4 % 1) * c.H); g[y:y + int(c.H * 0.01)] += 40
        return img * (1 - a) + g * a
    def top(self, c, canvas, lt):
        paste(canvas, T(self.p["date"], "sym", c.W * 0.04, "#FFFFFF", stroke=2, stroke_fill=(0, 0, 0, 200)), c.W * 0.06, c.H * 0.9, self.env(lt))

@register
class Captions(FX):
    name = "captions"; help = "Bold word-by-word captions (give 'words':[[word,start,end],...] from whisper, or 'text' to spread evenly)"
    params = {"text": "this is how I edit my reels", "words": None, "color": "#FFFFFF", "highlight": "#FACC15", "per": 3, "y": 0.72}
    def _words(self):
        if self.p.get("words"): return [(w, float(s) - self.start, float(e) - self.start) for w, s, e in self.p["words"]]
        ws = str(self.p["text"]).split(); n = len(ws); d = self.dur / max(1, n)
        return [(w, i * d, (i + 1) * d) for i, w in enumerate(ws)]
    def top(self, c, canvas, lt):
        W, H = c.W, c.H; ws = self._words(); per = int(self.p["per"])
        cur = next((i for i, (w, s, e) in enumerate(ws) if s <= lt < e), None)
        if cur is None: return
        g0 = cur // per * per; grp = ws[g0:g0 + per]; ims = []
        for i, (w, s, e) in enumerate(grp):
            hi = g0 + i == cur; im = T(w.upper(), "heavy", W * 0.075, self.p["highlight"] if hi else self.p["color"], stroke=int(W * 0.008), stroke_fill=(0, 0, 0, 255))
            if hi: im = scale_img(im, 1 + 0.12 * (1 - ease_out_cubic((lt - s) / 0.12)))
            ims.append(im)
        tot = sum(i.width for i in ims) + W * 0.02 * (len(ims) - 1); x = (W - tot) / 2; y = H * float(self.p["y"])
        for im in ims: paste(canvas, im, x, y - im.height / 2); x += im.width + W * 0.02

@register
class ProgressBar(FX):
    name = "progress-bar"; help = "Thin progress bar along the top that fills over the effect duration"
    params = {"color": "#FACC15"}
    def top(self, c, canvas, lt):
        ImageDraw.Draw(canvas).rectangle((0, 0, c.W * lt / self.dur, max(6, c.H * 0.006)), fill=rgba(self.p["color"]))

@register
class Poll(FX):
    name = "poll"; help = "A two-option poll card; votes animate in"
    params = {"question": "Would you use this?", "options": ["YES", "NO"], "result": [78, 22], "accent": "#8B5CF6"}
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; cw = W * 0.78; box = card(cw, W * 0.42, W * 0.04, (255, 255, 255, 245)); d = ImageDraw.Draw(box)
        paste(box, T(self.p["question"], "bold", fit_size(self.p["question"], "bold", cw - W * 0.1, W * 0.045), "#111111"), cw / 2, W * 0.07, center=True)
        q = ease_out_cubic((lt - self.dur * 0.35) / 0.6)
        for i, (op, r) in enumerate(zip(as_list(self.p["options"]), self.p["result"])):
            y = W * 0.14 + i * W * 0.13; d.rounded_rectangle((W * 0.05, y, cw - W * 0.05, y + W * 0.1), radius=W * 0.05, fill=(238, 238, 242, 255))
            if q > 0: d.rounded_rectangle((W * 0.05, y, W * 0.05 + (cw - W * 0.1) * r / 100 * q, y + W * 0.1), radius=W * 0.05, fill=rgba(self.p["accent"] if i == 0 else "#C4B5FD"))
            paste(box, T(op, "bold", W * 0.036, "#111111"), W * 0.09, y + W * 0.05 - W * 0.022)
            if q > 0: paste(box, T(f"{int(r * q)}%", "bold", W * 0.036, "#111111"), cw - W * 0.2, y + W * 0.05 - W * 0.022)
        paste(canvas, shadowed(box), W / 2, min(self.chin(c) + H * 0.14, H * 0.8), self.env(lt, 0.2, 0.25), center=True)

@register
class WhipZoom(FX):
    name = "whip-zoom"; help = "Fast zoom-blur transition (put it on a cut, ~0.4s)"
    params = {"strength": 1.0}
    def post(self, c, img, lt):
        k = math.sin(math.pi * clamp(lt / self.dur)) * float(self.p["strength"])
        if k < 0.02: return img
        acc = img.copy(); n = 6
        for i in range(1, n + 1): acc += zoom_on(img, c, 1 + 0.06 * k * i)
        return acc / (n + 1)

@register
class NeonOutline(FX):
    name = "neon-outline"; help = "A glowing neon outline traces around you"
    params = {"color": "#22D3EE", "width": 10}
    def bgfx(self, c, img, lt):
        a = self.env(lt, 0.3, 0.3); w = int(c.W / 1080 * float(self.p["width"]))
        m = (c.mask > 0.5).astype(np.uint8); ring = cv2.dilate(m, np.ones((w * 2 + 1, w * 2 + 1), np.uint8)).astype(np.float32) - m
        glow = cv2.GaussianBlur(ring, (0, 0), w * 2) * 1.5 + ring
        flick = 0.85 + 0.15 * math.sin(lt * 25)
        return img + np.clip(glow, 0, 1)[..., None] * np.array(hex2rgb(self.p["color"]), np.float32) * a * flick

@register
class HeartBurst(FX):
    name = "heart-burst"; help = "Hearts float up from the bottom corner (like a live stream)"
    params = {"count": 18, "color": "#FF3B5C"}
    def front(self, c, canvas, lt):
        W, H = c.W, c.H; r = random.Random(5)
        for i in range(int(self.p["count"])):
            t0 = r.uniform(0, self.dur * 0.7); q = (lt - t0) / 1.6
            if not 0 < q < 1: continue
            x = W * 0.85 + math.sin(q * 6 + i) * W * 0.05; y = H * 0.9 - q * H * 0.5
            col = PALETTE[i % 8] if i % 3 == 0 else self.p["color"]
            paste(canvas, T("♥", "sym", W * r.uniform(0.05, 0.09), col), x, y, (1 - q) * self.outa(lt), center=True)

@register
class Sticker(FX):
    name = "sticker"; help = "A bold tilted text sticker pops on (e.g. 'NEW!', 'PART 2')"
    params = {"text": "NEW!", "color": "#FACC15", "x": 0.75, "y": 0.18, "angle": 10}
    def top(self, c, canvas, lt):
        W = c.W; t = T(self.p["text"], "display", W * 0.08, "#111111")
        st = card(t.width + W * 0.06, t.height + W * 0.04, W * 0.02, rgba(self.p["color"]), (255, 255, 255, 255), W * 0.008); paste(st, t, W * 0.03, W * 0.02)
        paste(canvas, rot(shadowed(scale_img(st, max(0.05, ease_out_elastic(lt / 0.6)))), float(self.p["angle"])), W * float(self.p["x"]), c.H * float(self.p["y"]), self.outa(lt), center=True)

@register
class Freeze(FX):
    name = "freeze-bw"; help = "Freeze frame turns black & white with a big label (record-scratch moment)"
    params = {"text": "yep, that's me.", "color": "#FFFFFF"}
    def grade(self, c, img, lt):
        st = self.__dict__.setdefault("_state", {})
        if "f" not in st: st["f"] = img.copy()
        return to_gray(st["f"]) * 0.9
    def top(self, c, canvas, lt):
        paste(canvas, T(self.p["text"], "marker", c.W * 0.08, self.p["color"]), c.W / 2, c.H * 0.82, self.env(lt, 0.15, 0.2), center=True)

@register
class Zoomed(FX):
    name = "split-screen"; help = "Two of you side by side (wide + close-up)"
    params = {}
    def post(self, c, img, lt):
        q = ease_out_cubic(lt / 0.35) * self.outa(lt, 0.3)
        if q <= 0: return img
        W, H = c.W, c.H; h = H // 2; a = zoom_on(img, c, 1.0)[H // 4:H // 4 + h]; b = zoom_on(img, c, 2.0)[H // 4:H // 4 + (H - h)]
        out = np.concatenate([a, b], axis=0); return img * (1 - q) + out * q

# ================================================================= render
def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,avg_frame_rate",
                          "-of", "json", path], capture_output=True, text=True).stdout
    fps = 30.0
    for s in json.loads(out or "{}").get("streams", []):
        if s.get("codec_type") == "video":
            n, d = (s.get("avg_frame_rate") or "30/1").split("/")
            if float(d or 0) > 0 and float(n) > 0: fps = float(n) / float(d)
    return fps

def find_model(arg, key):
    if arg: return arg
    for p in sorted(glob.glob(os.path.join(CACHE, "*.tflite"))):
        if key in os.path.basename(p): return p
    return None

def build(plan):
    fxs = []
    for d in plan:
        d = dict(d); name = d.pop("fx"); name = ALIAS.get(name, name)
        if name not in REG: sys.exit(f"Unknown effect '{name}'. Run --list.")
        fxs.append(REG[name](d.pop("start", 0), d.pop("end", 3), **d))
    return fxs

def load_plan(args):
    plan = []
    if args.plan:
        with open(args.plan) as f: plan = json.load(f)
    for spec in args.fx or []:      # name;start=1;end=3;text=HI
        parts = spec.split(";"); d = {"fx": parts[0]}
        for kv in parts[1:]:
            k, v = kv.split("=", 1)
            try: v = json.loads(v)
            except Exception: pass
            d[k] = v
        plan.append(d)
    return build(plan)

def _composite(img, cv, mask=None):
    o = np.asarray(cv, np.float32); a = o[..., 3:4] / 255
    if mask is not None: a = a * (1 - mask[..., None])
    return img * (1 - a) + o[..., :3] * a

def process(ctx, frame, t, fxs, debug=False):
    ctx.t = t; ctx.raw = frame
    img = frame.astype(np.float32)
    act = [f for f in fxs if f.active(t)]
    lt = {id(f): t - f.start for f in act}
    for f in act:
        if f.grade: img = f.grade(ctx, img, lt[id(f)])
    if any(f.bgfx for f in act):
        bg = img.copy()
        for f in act:
            if f.bgfx: bg = f.bgfx(ctx, bg, lt[id(f)])
        M = ctx.mask[..., None]; img = bg * (1 - M) + img * M
    for hook, masked in (("behind", True), ("front", False)):
        if any(getattr(f, hook) for f in act):
            cv = Image.new("RGBA", (ctx.W, ctx.H), (0, 0, 0, 0))
            for f in act:
                if getattr(f, hook): getattr(f, hook)(ctx, cv, lt[id(f)])
            img = _composite(img, cv, ctx.mask if masked else None)
    for f in act:
        if f.post: img = f.post(ctx, img, lt[id(f)])
    if any(f.top for f in act):
        cv = Image.new("RGBA", (ctx.W, ctx.H), (0, 0, 0, 0))
        for f in act:
            if f.top: f.top(ctx, cv, lt[id(f)])
        img = _composite(img, cv)
    out = np.clip(img, 0, 255).astype(np.uint8)
    if debug:
        cx, cy, fw, fh = ctx.face.astype(int)
        cv2.rectangle(out, (cx - fw // 2, cy - fh // 2), (cx + fw // 2, cy + fh // 2), (0, 255, 0), 3)
        cnt, _ = cv2.findContours((ctx.mask > 0.5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(out, cnt, -1, (255, 0, 255), 2)
    return out

def main():
    ap = argparse.ArgumentParser(description="fxkit talking-head effects")
    ap.add_argument("input", nargs="?"); ap.add_argument("output", nargs="?")
    ap.add_argument("--plan"); ap.add_argument("--fx", action="append")
    ap.add_argument("--model"); ap.add_argument("--face-model"); ap.add_argument("--preview")
    ap.add_argument("--debug", action="store_true"); ap.add_argument("--list", action="store_true")
    ap.add_argument("--max-short", type=int, default=1080, help="short side px (2160 for 4K)")
    ap.add_argument("--crf", type=int, default=18)
    args = ap.parse_args()
    if args.list:
        for k, c in REG.items():
            al = f" (alias: {', '.join(c.aliases)})" if getattr(c, "aliases", None) else ""
            print(f"{k}{al}: {c.help}\n    params: {json.dumps(c.params)}")
        return
    fxs = load_plan(args)
    cap = cv2.VideoCapture(args.input)
    ok, fr = cap.read()
    if not ok: sys.exit("Cannot read video")
    h0, w0 = fr.shape[:2]; s = min(1.0, args.max_short / min(h0, w0))
    W, H = int(w0 * s) // 2 * 2, int(h0 * s) // 2 * 2
    fps = probe(args.input)
    ctx = Ctx(); ctx.W, ctx.H, ctx.fps = W, H, fps
    ctx.Y, ctx.X = np.mgrid[0:H, 0:W].astype(np.float32)
    tr = Tracker(find_model(args.model, "selfie"), find_model(args.face_model, "face"), W, H)
    prep = lambda f: cv2.cvtColor(cv2.resize(f, (W, H), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
    if args.preview:
        base = os.path.splitext(args.output or "preview")[0]
        for ts in [float(x) for x in args.preview.split(",")]:
            # warm up the frames just before ts so stateful effects (freeze etc.) behave
            for f in fxs: f.__dict__.pop("_state", None)
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(ts * fps)); ok, fr = cap.read()
            if not ok: continue
            rgb = prep(fr); ctx.mask, ctx.face = tr.update(rgb, smooth=False)
            out = process(ctx, rgb, ts, fxs, args.debug)
            p = f"{base}_{ts:.2f}s.png"
            Image.fromarray(out).resize((W // 2, H // 2)).save(p); print(p)
        tr.close(); return
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", f"{fps:.5f}", "-i", "-", "-i", args.input, "-map", "0:v", "-map", "1:a?",
           "-c:v", "libx264", "-preset", "medium", "-crf", str(args.crf), "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", args.output]
    pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0; i = 0
    while ok:
        rgb = prep(fr); ctx.mask, ctx.face = tr.update(rgb)
        pipe.stdin.write(process(ctx, rgb, i / fps, fxs).tobytes())
        i += 1
        if i % 30 == 0: print(f"\r{i}/{total} frames", end="", file=sys.stderr, flush=True)
        ok, fr = cap.read()
    pipe.stdin.close(); pipe.wait(); tr.close()
    print(f"\nDone: {args.output}", file=sys.stderr)

if __name__ == "__main__":
    main()
