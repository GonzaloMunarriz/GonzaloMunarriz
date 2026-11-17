"""Motor de vídeo: guion JSON -> voz (Piper TTS local) -> motion graphics -> MP4 1080p.

Uso:  python3 render.py ../guiones/video1.json ../salida/
Opciones de entorno:
  PREVIEW=1      renderiza solo las 3 primeras escenas a 540p (para revisar)
  VOICE=ruta.onnx  modelo de voz Piper
"""
import json
import math
import os
import random
import re
import subprocess
import sys
import wave
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
from music import write_music  # noqa: E402

W, H = 1920, 1080
FPS = 30
PREVIEW = os.environ.get("PREVIEW") == "1"
VOICE = os.environ.get(
    "VOICE",
    "/tmp/claude-0/-home-user-GonzaloMunarriz/7ab6e17c-920f-5d69-866a-90513239f0b0/scratchpad/tts/es-mls_10246-low.onnx",
)
CHANNEL = os.environ.get("CHANNEL", "MODO LEONIDA")

# Paleta original (inspiración "atardecer de Florida", sin assets de Rockstar)
BG = (12, 10, 30)
PINK = (255, 46, 136)
CYAN = (41, 224, 255)
ORANGE = (255, 170, 64)
YELLOW = (255, 221, 87)
WHITE = (245, 243, 255)
GREY = (170, 165, 200)
PURPLE = (120, 60, 200)
COLORS = {"pink": PINK, "cyan": CYAN, "orange": ORANGE, "yellow": YELLOW, "white": WHITE, "purple": PURPLE}

FONT_DIR = "/usr/share/fonts/opentype/inter/"
F_BLACK = FONT_DIR + "InterDisplay-Black.otf"
F_BOLD = FONT_DIR + "InterDisplay-Bold.otf"
F_SEMI = FONT_DIR + "Inter-SemiBold.otf"
F_REG = FONT_DIR + "Inter-Medium.otf"
F_ITAL = FONT_DIR + "InterDisplay-BlackItalic.otf"

# ---------------------------------------------------------------- pronunciación
PRON = [
    (r"\bGTA VI\b", "ge te a seis"),
    (r"\bGTA 6\b", "ge te a seis"),
    (r"\bGTA V\b", "ge te a cinco"),
    (r"\bGTA IV\b", "ge te a cuatro"),
    (r"\bGTA\b", "ge te a"),
    (r"Grand Theft Auto", "Grand Zeft Óto"),
    (r"Vice City", "Vais Síti"),
    (r"Liberty City", "Líberti Síti"),
    (r"\bVice\b", "Vais"),
    (r"\bJason\b", "Yéison"),
    (r"\bLucia\b", "Lucía"),
    (r"Take-Two", "Teik Tu"),
    (r"\bUltimate\b", "Áltimeit"),
    (r"Port Gellhorn", "Port Guéljorn"),
    (r"Grassrivers", "Gras Ríbers"),
    (r"Mount Kalaga", "Maunt Kalága"),
    (r"Leonida Keys", "Leónida Kis"),
    (r"Florida Keys", "Flórida Kis"),
    (r"\bKeys\b", "Kis"),
    (r"Everglades", "Évergleids"),
    (r"Panhandle", "Pánjandel"),
    (r"Boobie Ike", "Búbi Áik"),
    (r"Real Dimez", "Ríal Daims"),
    (r"Dre'Quan Priest", "Drecuán Prist"),
    (r"Dre'Quan", "Drecuán"),
    (r"Brian Heder", "Bráian Jéder"),
    (r"\bBrian\b", "Bráian"),
    (r"Cal Hampton", "Cal Jámpton"),
    (r"Raul Bautista", "Raúl Bautista"),
    (r"Only Raw", "Ónli Ro"),
    (r"Bonnie y Clyde", "Bóni y Cláid"),
    (r"Red Dead Redemption 2", "Red Ded Ridémpshon dos"),
    (r"Red Dead Redemption", "Red Ded Ridémpshon"),
    (r"Tommy Vercetti", "Tómi Verchéti"),
    (r"PlayStation 5 Pro", "Pleisteishon cinco Pro"),
    (r"PlayStation 5", "Pleisteishon cinco"),
    (r"PlayStation 4", "Pleisteishon cuatro"),
    (r"PlayStation 3", "Pleisteishon tres"),
    (r"PlayStation 2", "Pleisteishon dos"),
    (r"PlayStation", "Pleisteishon"),
    (r"\bPS5 Pro\b", "Pleisteishon cinco Pro"),
    (r"\bPS5\b", "Pleisteishon cinco"),
    (r"Xbox Series X\|S", "Ecsbox Síries Ecs y Ese"),
    (r"Xbox Series S", "Ecsbox Síries Ese"),
    (r"Xbox Series X", "Ecsbox Síries Ecs"),
    (r"Xbox Series", "Ecsbox Síries"),
    (r"Xbox 360", "Ecsbox trescientos sesenta"),
    (r"Xbox One", "Ecsbox Uan"),
    (r"Xbox", "Ecsbox"),
    (r"\bOnline\b", "Onláin"),
    (r"\bonline\b", "onláin"),
    (r"gameplay", "guéimplei"),
    (r"\bstreamers?\b", "estrímers"),
    (r"\bstreaming\b", "estríming"),
    (r"\bSteam\b", "Estím"),
    (r"\bRockstar\b", "Rócstar"),
    (r"\bspoilers?\b", "espóilers"),
    (r"\bleaks?\b", "filtraciones"),
    (r"\bshooter\b", "chúter"),
    (r"\bfps\b", "fotogramas por segundo"),
    (r"\bGB\b", "gigas"),
    (r"\bTB\b", "teras"),
    (r"\bSSD\b", "ese ese de"),
    (r"\bPC\b", "pe ce"),
    (r"\bYouTube\b", "Yutub"),
    (r"\bTwitch\b", "Tuích"),
    (r"\bLos Santos\b", "Los Santos"),
    (r"\bLeonida\b", "Leónida"),
    (r"\bClassic\b", "Clásic"),
    (r"\bwebs?\b", "güeb"),
    (r"\bCheetah\b", "Chíta"),
    (r"\bstores?\b", "estor"),
    (r"\bfeedback\b", "fídbac"),
    (r"\bmods?\b", "mods"),
    (r"\bremaster\b", "remáster"),
    (r"\bgamers?\b", "guéimers"),
    (r"\bLive\b", "Láiv"),
    (r"\bPlus\b", "Plas"),
    (r"\bGame Pass\b", "Guéim Pas"),
    (r"\bdownload\b", "descarga"),
    (r"\bReddit\b", "Rédit"),
    (r"\bTikTok\b", "Tic Toc"),
    (r"\bshorts?\b", "chorts"),
    (r"\bHD\b", "ache de"),
    (r"\b4K\b", "cuatro ka"),
    (r"\$", " dólares"),
    (r"%", " por ciento"),
    (r"€", " euros"),
    (r"\bvs\.?\b", "contra"),
]


def to_speech(text):
    s = text
    for pat, rep in PRON:
        s = re.sub(pat, rep, s)
    s = s.replace("…", ",").replace("—", ",").replace("–", ",")
    return s


# ---------------------------------------------------------------- TTS
_voice = None


def tts(text, path, length_scale=0.86):
    global _voice
    if _voice is None:
        from piper import PiperVoice
        _voice = PiperVoice.load(VOICE)
    from piper.config import SynthesisConfig
    cfg = SynthesisConfig(length_scale=length_scale, noise_scale=0.6, noise_w_scale=0.75)
    chunks = []
    sr = _voice.config.sample_rate
    # frase a frase, con pausas naturales
    sentences = [x for x in re.split(r"(?<=[\.\?\!:;])\s+", text) if x.strip()]
    for sent in sentences:
        for ch in _voice.synthesize(to_speech(sent), syn_config=cfg):
            chunks.append(ch.audio_int16_array)
        pause = 0.42 if sent.rstrip().endswith((".", "!", "?")) else 0.3
        chunks.append(np.zeros(int(sr * pause), dtype=np.int16))
    audio = np.concatenate(chunks) if chunks else np.zeros(sr, dtype=np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(audio.tobytes())
    return len(audio) / sr


# ---------------------------------------------------------------- utilidades de dibujo
@lru_cache(maxsize=64)
def font(path, size):
    return ImageFont.truetype(path, size)


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return 3 * t * t - 2 * t * t * t


@lru_cache(maxsize=2048)
def text_img(text, fpath, size, color, glow=None, stroke=0, max_w=None, spacing=1.12, align="left"):
    """Renderiza texto (con salto de línea automático) a una imagen RGBA cacheada."""
    f = font(fpath, size)
    lines = []
    for para in text.split("\n"):
        if max_w is None:
            lines.append(para)
            continue
        words = para.split(" ")
        cur = ""
        for wd in words:
            test = (cur + " " + wd).strip()
            if f.getlength(test) <= max_w or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = wd
        lines.append(cur)
    asc, desc = f.getmetrics()
    lh = int((asc + desc) * spacing)
    tw = int(max(f.getlength(l) for l in lines)) + 2 * stroke + 4
    th = lh * len(lines) + 2 * stroke
    pad = 40 if glow else 4
    img = Image.new("RGBA", (tw + 2 * pad, th + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, l in enumerate(lines):
        lw = f.getlength(l)
        x = pad + stroke + (0 if align == "left" else ((tw - lw) / 2 if align == "center" else tw - lw - 2 * stroke))
        d.text((x, pad + stroke + i * lh), l, font=f, fill=color + (255,), stroke_width=stroke,
               stroke_fill=(10, 8, 25, 255))
    if glow:
        g = Image.new("RGBA", img.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        for i, l in enumerate(lines):
            lw = f.getlength(l)
            x = pad + stroke + (0 if align == "left" else ((tw - lw) / 2 if align == "center" else tw - lw - 2 * stroke))
            gd.text((x, pad + stroke + i * lh), l, font=f, fill=glow + (200,), stroke_width=stroke + 3,
                    stroke_fill=glow + (200,))
        g = g.filter(ImageFilter.GaussianBlur(18))
        g.alpha_composite(img)
        img = g
    img.info["pad"] = pad
    return img


def paste(frame, img, x, y, alpha=1.0, anchor="lt"):
    """Pega una imagen RGBA en el frame. anchor: lt (top-left) | mt (centro arriba) | mm (centro)."""
    pad = img.info.get("pad", 0)
    if anchor == "mt":
        x = x - img.width // 2
        y = y - pad
    elif anchor == "mm":
        x = x - img.width // 2
        y = y - img.height // 2
    else:
        x = x - pad
        y = y - pad
    x, y = int(x), int(y)
    if alpha <= 0.01:
        return
    if alpha < 0.99:
        a = img.getchannel("A").point(lambda v: int(v * alpha))
        img = img.copy()
        img.putalpha(a)
    frame.alpha_composite(img, (max(0, x), max(0, y)),
                          (max(0, -x), max(0, -y)))


def rrect(size, radius, fill, outline=None, width=0):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=fill, outline=outline, width=width)
    return img


@lru_cache(maxsize=256)
def panel(w, h, color=(28, 22, 60), border=PINK, alpha=215):
    return rrect((w, h), 22, color + (alpha,), outline=border + (255,), width=3)


# ---------------------------------------------------------------- fondos
def _gradient(h, top, bottom):
    t = np.linspace(0, 1, h)[:, None]
    col = np.array(top)[None, :] * (1 - t) + np.array(bottom)[None, :] * t
    return np.repeat(col[:, None, :], W, axis=1)


def _palm(d, x, base_y, height, lean, color):
    # palmera genérica procedural
    pts = []
    segs = 18
    for i in range(segs + 1):
        t = i / segs
        px = x + lean * (t ** 1.8) * height
        py = base_y - t * height
        pts.append((px, py))
    for i in range(segs):
        w = 14 * (1 - i / segs) + 6
        (x1, y1), (x2, y2) = pts[i], pts[i + 1]
        d.polygon([(x1 - w, y1), (x1 + w, y1), (x2 + w * 0.9, y2), (x2 - w * 0.9, y2)], fill=color)
    tx, ty = pts[-1]
    for ang in [-170, -140, -110, -70, -40, -10, 15, 200, 160]:
        a = math.radians(ang)
        L = height * 0.42
        pts2 = []
        for k in range(12):
            t = k / 11
            px = tx + math.cos(a) * L * t
            py = ty + math.sin(a) * L * t + (t ** 2) * L * 0.45
            pts2.append((px, py))
        for k in range(11):
            w = 16 * math.sin(math.pi * (k + 0.5) / 11) + 2
            d.line([pts2[k], pts2[k + 1]], fill=color, width=int(w))


@lru_cache(maxsize=4)
def sunset_sky(variant=0):
    sky = _gradient(H, (18, 8, 48), (255, 92, 120))
    horizon = int(H * 0.62)
    sky[horizon:] = _gradient(H - horizon, (40, 10, 60), (8, 6, 22))
    img = Image.fromarray(sky.astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(img)
    # sol con franjas
    cx, cy, r = W // 2 + (variant * 380 - 380), horizon - 60, 250
    sun = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sun)
    for yy in range(2 * r):
        t = yy / (2 * r)
        col = (int(255), int(220 - 150 * t), int(90 + 40 * t), 255)
        half = math.sqrt(max(0, r * r - (yy - r) ** 2))
        sd.line([(r - half, yy), (r + half, yy)], fill=col)
    for k in range(7):
        yy = int(r * 1.05 + k * k * 4.2 + k * 10)
        sd.rectangle([0, yy, 2 * r, yy + 4 + k * 2], fill=(0, 0, 0, 0))
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([cx - r - 80, cy - r - 80, cx + r + 80, cy + r + 80], fill=(255, 80, 140, 120))
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    img.alpha_composite(glow)
    img.alpha_composite(sun, (cx - r, cy - r))
    # recorte bajo el horizonte
    d.rectangle([0, horizon, W, H], fill=(14, 8, 34, 255))
    # skyline genérico
    rnd = random.Random(7 + variant)
    x = 0
    while x < W:
        bw = rnd.randint(30, 90)
        bh = rnd.randint(30, 190) if abs(x - cx) > 260 else rnd.randint(20, 70)
        d.rectangle([x, horizon - bh, x + bw, horizon], fill=(22, 10, 46, 255))
        for wy in range(horizon - bh + 10, horizon - 6, 16):
            for wx in range(x + 6, x + bw - 6, 14):
                if rnd.random() < 0.25:
                    d.rectangle([wx, wy, wx + 4, wy + 6], fill=(255, 190, 120, 160))
        x += bw + rnd.randint(0, 8)
    # palmeras
    _palm(d, 140, horizon + 30, 420, 0.25, (10, 4, 22, 255))
    _palm(d, 300, horizon + 40, 300, -0.2, (10, 4, 22, 255))
    _palm(d, W - 180, horizon + 30, 460, -0.28, (10, 4, 22, 255))
    # estrellas
    for _ in range(140):
        sx, sy = rnd.randint(0, W), rnd.randint(0, int(horizon * 0.55))
        b = rnd.randint(120, 255)
        d.point((sx, sy), fill=(b, b, 255, 255))
    return img, horizon


@lru_cache(maxsize=4)
def dark_bg(tint=0):
    tints = [((14, 10, 34), (34, 12, 54)), ((8, 16, 34), (12, 36, 60)), ((24, 10, 24), (60, 18, 40))]
    a, b = tints[tint % 3]
    g = _gradient(H, a, b)
    img = Image.fromarray(g.astype(np.uint8), "RGB").convert("RGBA")
    # viñeta + manchas de luz
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-300, -300, 700, 600], fill=PINK + (60,))
    gd.ellipse([W - 600, H - 500, W + 300, H + 300], fill=CYAN + (50,))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    img.alpha_composite(glow)
    # retícula sutil
    d = ImageDraw.Draw(img)
    for x in range(0, W, 80):
        d.line([(x, 0), (x, H)], fill=(255, 255, 255, 8))
    for y in range(0, H, 80):
        d.line([(0, y), (W, y)], fill=(255, 255, 255, 8))
    return img


def draw_grid(frame, horizon, t, alpha=255):
    d = ImageDraw.Draw(frame)
    vx = W // 2
    # líneas de fuga
    for k in range(-14, 15):
        x0 = vx + k * 40
        x1 = vx + k * 260
        d.line([(x0, horizon), (x1, H)], fill=(255, 46, 136, 110), width=2)
    # líneas horizontales en movimiento
    phase = (t * 0.6) % 1.0
    for i in range(14):
        z = (i + phase) / 14
        y = horizon + (H - horizon) * (z ** 2.2)
        d.line([(0, y), (W, y)], fill=(255, 46, 136, int(40 + 140 * z)), width=2)


def particles(frame, t, seed=3, n=36, color=CYAN):
    d = ImageDraw.Draw(frame)
    rnd = random.Random(seed)
    for _ in range(n):
        x0 = rnd.uniform(0, W)
        y0 = rnd.uniform(0, H)
        sp = rnd.uniform(8, 30)
        r = rnd.uniform(1.5, 4)
        y = (y0 - t * sp) % H
        x = x0 + math.sin(t * 0.5 + x0) * 20
        a = int(60 + 80 * (0.5 + 0.5 * math.sin(t * 1.3 + y0)))
        d.ellipse([x - r, y - r, x + r, y + r], fill=color + (a,))


# ---------------------------------------------------------------- mapa estilizado (Leonida ~ península genérica)
PENINSULA = [(0.12, 0.10), (0.62, 0.10), (0.66, 0.16), (0.70, 0.26), (0.73, 0.36), (0.76, 0.46),
             (0.78, 0.56), (0.77, 0.66), (0.74, 0.74), (0.69, 0.80), (0.64, 0.82), (0.60, 0.77),
             (0.57, 0.68), (0.53, 0.60), (0.48, 0.52), (0.45, 0.44), (0.42, 0.36), (0.38, 0.28),
             (0.30, 0.22), (0.20, 0.20), (0.12, 0.18)]
REGIONS = {
    "port": ("Port Gellhorn", (0.25, 0.15), ORANGE),
    "kalaga": ("Mount Kalaga", (0.50, 0.20), (120, 230, 140)),
    "ambrosia": ("Ambrosia", (0.58, 0.40), YELLOW),
    "grass": ("Grassrivers", (0.62, 0.62), (90, 220, 170)),
    "vice": ("Vice City", (0.72, 0.70), PINK),
    "keys": ("Leonida Keys", (0.56, 0.90), CYAN),
}


@lru_cache(maxsize=2)
def map_base():
    img = dark_bg(1).copy()
    d = ImageDraw.Draw(img)
    ox, oy, sw, sh = 420, 30, 1080, 870
    pts = [(ox + x * sw, oy + y * sh) for x, y in PENINSULA]
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).polygon(pts, fill=CYAN + (90,))
    glow = glow.filter(ImageFilter.GaussianBlur(30))
    img.alpha_composite(glow)
    d.polygon(pts, fill=(30, 40, 80, 255), outline=CYAN + (255,))
    d.line(pts + [pts[0]], fill=CYAN + (255,), width=4)
    # cayos
    for i in range(9):
        t = i / 8
        x = ox + (0.62 - 0.16 * t) * sw
        y = oy + (0.85 + 0.07 * t) * sh
        d.ellipse([x - 14 + i, y - 6, x + 14, y + 6], fill=(30, 40, 80, 255), outline=CYAN + (255,), width=2)
    return img, (ox, oy, sw, sh)


# ---------------------------------------------------------------- escenas
def header(frame, title, lt, color=PINK):
    a = ease_out(lt / 0.5)
    img = text_img(title.upper(), F_BLACK, 64, WHITE, glow=color)
    paste(frame, img, 120 - (1 - a) * 60, 90, a)
    bar_w = int(160 * a)
    ImageDraw.Draw(frame).rectangle([120, 180, 120 + bar_w, 188], fill=color + (255,))


def scene_title(frame, s, lt, dur, t):
    sky, hz = sunset_sky(s.get("variant", 1))
    frame.alpha_composite(sky)
    draw_grid(frame, hz, t)
    a = ease_out(lt / 0.8)
    kicker = s.get("kicker")
    if kicker:
        paste(frame, text_img(kicker.upper(), F_SEMI, 40, YELLOW), W // 2, 210 - (1 - a) * 30, a, "mt")
    title = text_img(s["title"], F_ITAL, s.get("size", 120), WHITE, glow=PINK, max_w=1600, align="center", stroke=2)
    sc = 0.9 + 0.1 * a + 0.015 * math.sin(t * 1.5)
    tw = title.resize((int(title.width * sc), int(title.height * sc)))
    tw.info["pad"] = 0
    paste(frame, tw, W // 2, 420, a, "mm")
    if s.get("sub"):
        a2 = ease_out((lt - 0.5) / 0.6)
        paste(frame, text_img(s["sub"], F_BOLD, 50, CYAN, max_w=1400, align="center", stroke=3), W // 2, 640 + (1 - a2) * 30, a2, "mt")


def scene_chapter(frame, s, lt, dur, t):
    frame.alpha_composite(dark_bg(s.get("tint", 0)))
    particles(frame, t)
    a = ease_out(lt / 0.6)
    num = text_img(s["n"], F_ITAL, 300, PINK, glow=PINK)
    paste(frame, num, 200 - (1 - a) * 120, 300, a)
    ttl = text_img(s["title"].upper(), F_BLACK, 96, WHITE, max_w=1100)
    a2 = ease_out((lt - 0.25) / 0.6)
    paste(frame, ttl, 720 + (1 - a2) * 120, 360, a2)
    if s.get("sub"):
        a3 = ease_out((lt - 0.6) / 0.6)
        paste(frame, text_img(s["sub"], F_REG, 44, GREY, max_w=1050), 724, 600, a3)
    # barrido
    sw = ease_in_out(lt / 0.7)
    if sw < 1:
        ImageDraw.Draw(frame).rectangle([0, 0, int(W * (1 - sw)), H], fill=PINK + (255,))


def _reveal_times(n, dur, start=0.6, end_pad=1.2):
    span = max(0.5, dur - start - end_pad)
    return [start + span * i / max(1, n) for i in range(n)]


def scene_bullets(frame, s, lt, dur, t):
    frame.alpha_composite(dark_bg(s.get("tint", 0)))
    particles(frame, t, n=20)
    color = COLORS.get(s.get("color", "pink"), PINK)
    header(frame, s["title"], lt, color)
    items = s["items"]
    times = s.get("times") or _reveal_times(len(items), dur)
    y = 270
    size = 60 if len(items) <= 4 else (52 if len(items) <= 5 else 44)
    gap = 58 if len(items) <= 4 else (38 if len(items) <= 5 else 26)
    check = s.get("check", False)
    for i, it in enumerate(items):
        a = ease_out((lt - times[i]) / 0.45)
        img = text_img(it, F_SEMI, size, WHITE, max_w=1450)
        if a > 0:
            x = 220 + (1 - a) * 80
            d = ImageDraw.Draw(frame)
            cy = y + size * 0.62
            if check:
                d.line([(x - 80, cy), (x - 64, cy + 16), (x - 36, cy - 18)], fill=color + (int(255 * a),), width=8)
            else:
                d.rounded_rectangle([x - 76, cy - 14, x - 48, cy + 14], radius=6, fill=color + (int(255 * a),))
            paste(frame, img, x, y, a)
        y += img.height - 8 + gap


def scene_stat(frame, s, lt, dur, t):
    if s.get("bg") == "sunset":
        sky, hz = sunset_sky(s.get("variant", 0))
        frame.alpha_composite(sky)
        draw_grid(frame, hz, t)
        ov = Image.new("RGBA", (W, H), (8, 4, 20, 150))
        frame.alpha_composite(ov)
    else:
        frame.alpha_composite(dark_bg(s.get("tint", 2)))
        particles(frame, t, color=YELLOW)
    color = COLORS.get(s.get("color", "yellow"), YELLOW)
    a = ease_out(lt / 0.5)
    val = s["value"]
    if "count" in s:
        target = s["count"]
        k = ease_out(lt / 1.6)
        cur = target * k
        fmt = s.get("fmt", "{:,.0f}")
        val = fmt.format(cur).replace(",", ".") if s.get("es_thousands", True) else fmt.format(cur)
        if s.get("comma"):
            val = val.replace(".", ",")
        val = s.get("prefix", "") + val + s.get("suffix", "")
    if s.get("kicker"):
        paste(frame, text_img(s["kicker"].upper(), F_BOLD, 46, GREY), W // 2, 230, a, "mt")
    big = text_img(val, F_ITAL, s.get("size", 230), color, glow=color)
    paste(frame, big, W // 2, 470 + (1 - a) * 40, a, "mm")
    a2 = ease_out((lt - 0.5) / 0.6)
    paste(frame, text_img(s["label"], F_BOLD, 50, WHITE, max_w=1500, align="center"), W // 2, 680, a2, "mt")
    if s.get("note"):
        a3 = ease_out((lt - 1.0) / 0.6)
        paste(frame, text_img(s["note"], F_REG, 34, GREY, max_w=1400, align="center"), W // 2, 800, a3, "mt")


def scene_timeline(frame, s, lt, dur, t):
    frame.alpha_composite(dark_bg(s.get("tint", 1)))
    particles(frame, t, n=16)
    header(frame, s["title"], lt, CYAN)
    ev = s["events"]
    n = len(ev)
    x0, x1, y = 180, W - 180, 600
    d = ImageDraw.Draw(frame)
    prog = ease_in_out(lt / max(1.0, dur * 0.75))
    d.line([(x0, y), (x0 + (x1 - x0) * prog, y)], fill=CYAN + (255,), width=6)
    times = _reveal_times(n, dur * 0.85, start=0.4, end_pad=0.2)
    hl = s.get("hl", n - 1)
    for i, (date, label) in enumerate(ev):
        x = x0 + (x1 - x0) * (i / max(1, n - 1))
        a = ease_out((lt - times[i]) / 0.45)
        if a <= 0:
            continue
        col = PINK if i == hl else CYAN
        r = 18 if i == hl else 13
        pulse = 1 + (0.25 * math.sin(t * 5) if i == hl else 0)
        d.ellipse([x - r * pulse, y - r * pulse, x + r * pulse, y + r * pulse], fill=col + (int(255 * a),))
        up = i % 2 == 0
        di = text_img(date, F_BLACK, 40, col)
        li = text_img(label, F_SEMI, 32, WHITE, max_w=300, align="center")
        if up:
            paste(frame, di, x, y - 170 - (1 - a) * 30, a, "mt")
            paste(frame, li, x, y - 110 - (1 - a) * 30, a, "mt")
        else:
            paste(frame, di, x, y + 50 + (1 - a) * 30, a, "mt")
            paste(frame, li, x, y + 110 + (1 - a) * 30, a, "mt")


def scene_map(frame, s, lt, dur, t):
    base, (ox, oy, sw, sh) = map_base()
    frame.alpha_composite(base)
    hl = s.get("hl")
    keys = s.get("show", list(REGIONS.keys()))
    times = _reveal_times(len(keys), min(dur, 6), start=0.3, end_pad=0.2) if not hl else [0] * len(keys)
    d = ImageDraw.Draw(frame)
    for i, k in enumerate(keys):
        name, (rx, ry), col = REGIONS[k]
        x, y = ox + rx * sw, oy + ry * sh
        a = ease_out((lt - times[i]) / 0.5)
        if a <= 0:
            continue
        on = (hl == k)
        dim = 1.0 if (not hl or on) else 0.35
        r = 22 if on else 14
        if on:
            for ring in range(3):
                rr = r + ((t * 40 + ring * 30) % 90)
                al = int(200 * (1 - ((t * 40 + ring * 30) % 90) / 90))
                d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=col + (al,), width=4)
        d.ellipse([x - r, y - r, x + r, y + r], fill=col + (int(255 * a * dim),))
        lbl = text_img(name, F_BLACK, 46 if on else 34, col if on else WHITE, glow=col if on else None, stroke=2)
        lx = x + 34 if rx < 0.7 else x - lbl.width + 20
        paste(frame, lbl, lx, y - 30, a * dim)
    if s.get("title"):
        header(frame, s["title"], lt, PINK)
    if s.get("info"):
        a = ease_out((lt - 0.6) / 0.5)
        items = s["info"]
        pw, ph = 560, 90 + 64 * len(items)
        px, py = (W - pw - 60, 300) if (not hl or REGIONS[hl][1][0] < 0.6) else (60, 300)
        paste(frame, panel(pw, ph, border=REGIONS[hl][2] if hl else PINK), px + (1 - a) * 60, py, a)
        for j, it in enumerate(items):
            aj = ease_out((lt - 0.9 - j * 0.5) / 0.4)
            paste(frame, text_img("• " + it, F_SEMI, 34, WHITE, max_w=pw - 70), px + 36, py + 40 + j * 64, aj * a)


def scene_compare(frame, s, lt, dur, t):
    frame.alpha_composite(dark_bg(s.get("tint", 0)))
    particles(frame, t, n=14)
    header(frame, s["title"], lt, PINK)
    cols = [s["left"], s["right"]]
    ccol = [CYAN, PINK]
    n = max(len(c["items"]) for c in cols)
    times = _reveal_times(n * 2, dur)
    for ci, c in enumerate(cols):
        x = 140 + ci * 860
        a = ease_out((lt - 0.2 - ci * 0.3) / 0.5)
        pw, ph = 780, 760
        paste(frame, panel(pw, ph, border=ccol[ci]), x, 240 + (1 - a) * 40, a)
        paste(frame, text_img(c["h"].upper(), F_BLACK, 56, ccol[ci]), x + 50, 280, a)
        for j, it in enumerate(c["items"]):
            ti = times[j * 2 + ci]
            aj = ease_out((lt - ti) / 0.4)
            paste(frame, text_img(it, F_SEMI, 44, WHITE, max_w=pw - 110), x + 60 + (1 - aj) * 40, 400 + j * 125, aj)


def scene_card(frame, s, lt, dur, t):
    frame.alpha_composite(dark_bg(s.get("tint", 2)))
    particles(frame, t, n=20, color=COLORS.get(s.get("color", "pink"), PINK))
    col = COLORS.get(s.get("color", "pink"), PINK)
    a = ease_out(lt / 0.6)
    # "retrato" abstracto: monograma en marco neón (no representa arte oficial)
    cx, cy, r = 470, 540, 260
    d = ImageDraw.Draw(frame)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([cx - r - 30, cy - r - 30, cx + r + 30, cy + r + 30], fill=col + (int(120 * a),))
    glow = glow.filter(ImageFilter.GaussianBlur(40))
    frame.alpha_composite(glow)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(20, 14, 44, 255), outline=col + (255,), width=8)
    ini = "".join(w[0] for w in s["name"].split()[:2]).upper()
    paste(frame, text_img(ini, F_ITAL, 200, col), cx, cy, a, "mm")
    rot = t * 0.6
    for k in range(3):
        ang = rot + k * 2.09
        d.arc([cx - r - 50, cy - r - 50, cx + r + 50, cy + r + 50], math.degrees(ang), math.degrees(ang) + 40,
              fill=col + (200,), width=6)
    paste(frame, text_img(s["name"].upper(), F_BLACK, 84, WHITE, glow=col), 860 + (1 - a) * 60, 200, a)
    y = 330
    if s.get("role"):
        ri = text_img(s["role"], F_BOLD, 42, col, max_w=950)
        paste(frame, ri, 864, y, a)
        y += ri.height + 30
    times = _reveal_times(len(s["items"]), dur, start=0.9)
    for j, it in enumerate(s["items"]):
        aj = ease_out((lt - times[j]) / 0.4)
        ii = text_img("— " + it, F_SEMI, 42, WHITE, max_w=950)
        paste(frame, ii, 864 + (1 - aj) * 40, y, aj)
        y += ii.height + 18


def scene_quote(frame, s, lt, dur, t):
    sky, hz = sunset_sky(s.get("variant", 2))
    frame.alpha_composite(sky)
    draw_grid(frame, hz, t)
    frame.alpha_composite(Image.new("RGBA", (W, H), (8, 4, 20, 170)))
    a = ease_out(lt / 0.7)
    paste(frame, text_img("“", F_ITAL, 260, PINK), 200, 120, a)
    paste(frame, text_img(s["text"], F_ITAL, s.get("size", 76), WHITE, max_w=1450, align="center", glow=PURPLE),
          W // 2, 470, a, "mm")
    if s.get("by"):
        a2 = ease_out((lt - 0.7) / 0.5)
        paste(frame, text_img(s["by"], F_BOLD, 40, CYAN), W // 2, 760, a2, "mt")


def scene_bars(frame, s, lt, dur, t):
    frame.alpha_composite(dark_bg(s.get("tint", 1)))
    header(frame, s["title"], lt, YELLOW)
    bars = s["bars"]
    mx = max(b[1] for b in bars)
    unit = s.get("unit", "")
    times = _reveal_times(len(bars), dur * 0.8, start=0.6, end_pad=0.2)
    d = ImageDraw.Draw(frame)
    for i, (lab, v, *rest) in enumerate(bars):
        y = 290 + i * (620 / len(bars))
        a = ease_out((lt - times[i]) / 0.9)
        col = PINK if rest and rest[0] == "hl" else CYAN
        paste(frame, text_img(lab, F_BOLD, 40, WHITE), 120, y, min(1, a * 2))
        bw = int(1100 * (v / mx) * a)
        d.rounded_rectangle([600, y + 4, 600 + max(bw, 4), y + 54], radius=10, fill=col + (255,))
        if a > 0.05:
            vv = v * a
            txt = (f"{vv:.0f} {unit}" if not (rest and rest[0] == "hl" and len(rest) > 1) else rest[1])
            if rest and rest[0] == "hl" and len(rest) > 1:
                txt = rest[1]
            paste(frame, text_img(txt, F_BLACK, 40, col), 600 + bw + 24, y, a)
    if s.get("note"):
        a3 = ease_out((lt - dur * 0.6) / 0.6)
        paste(frame, text_img(s["note"], F_REG, 34, GREY, max_w=1600, align="center"), W // 2, 860, a3, "mt")


def scene_clock(frame, s, lt, dur, t):
    frame.alpha_composite(dark_bg(s.get("tint", 1)))
    particles(frame, t, n=14)
    header(frame, s["title"], lt, CYAN)
    rows = s["rows"]
    times = _reveal_times(len(rows), dur)
    for i, (place, when) in enumerate(rows):
        a = ease_out((lt - times[i]) / 0.4)
        y = 260 + i * 105
        paste(frame, panel(1600, 86, border=CYAN if i % 2 else PINK, alpha=180), 160 + (1 - a) * 60, y, a)
        paste(frame, text_img(place, F_BOLD, 40, WHITE), 210 + (1 - a) * 60, y + 18, a)
        paste(frame, text_img(when, F_BLACK, 40, YELLOW), 1000 + (1 - a) * 60, y + 18, a)
    if s.get("note"):
        a3 = ease_out((lt - 1.0) / 0.6)
        paste(frame, text_img(s["note"], F_REG, 32, GREY, max_w=1600, align="center"), W // 2, 845, a3, "mt")


def scene_outro(frame, s, lt, dur, t):
    sky, hz = sunset_sky(0)
    frame.alpha_composite(sky)
    draw_grid(frame, hz, t)
    a = ease_out(lt / 0.6)
    paste(frame, text_img(s.get("title", "SUSCRÍBETE"), F_ITAL, 130, WHITE, glow=PINK), W // 2, 300, a, "mm")
    paste(frame, text_img(s.get("sub", ""), F_BOLD, 46, CYAN, max_w=1500, align="center"), W // 2, 430, a, "mt")
    # tarjetas de "siguiente vídeo" (zona para pantallas finales de YouTube)
    for k in range(2):
        ak = ease_out((lt - 0.5 - k * 0.3) / 0.5)
        x = 300 + k * 760
        paste(frame, panel(560, 315, color=(10, 8, 25), border=PINK if k == 0 else CYAN, alpha=200), x, 600 + (1 - ak) * 60, ak)
        paste(frame, text_img("SIGUIENTE VÍDEO" if k == 0 else "TE PUEDE GUSTAR", F_BOLD, 34, GREY), x + 280, 740, ak, "mt")


SCENES = {
    "title": scene_title, "chapter": scene_chapter, "bullets": scene_bullets, "stat": scene_stat,
    "timeline": scene_timeline, "map": scene_map, "compare": scene_compare, "card": scene_card,
    "quote": scene_quote, "bars": scene_bars, "clock": scene_clock, "outro": scene_outro,
}


# ---------------------------------------------------------------- subtítulos
def caption_chunks(text, dur, max_words=7):
    words = text.split()
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= max_words or re.search(r"[\.\?\!,:;]$", w) and len(cur) >= 3:
            chunks.append(" ".join(cur))
            cur = []
    if cur:
        if chunks and len(cur) < 3:
            chunks[-1] = chunks[-1] + " " + " ".join(cur)
        else:
            chunks.append(" ".join(cur))
    total = sum(len(c) + 6 for c in chunks)
    out, acc = [], 0.0
    usable = dur - 0.5
    for c in chunks:
        d = usable * (len(c) + 6) / total
        out.append((acc, acc + d, c))
        acc += d
    return out


def draw_caption(frame, txt):
    img = text_img(txt, F_BOLD, 44, WHITE, stroke=3, max_w=1500, align="center")
    bw, bh = img.width + 40, img.height + 10
    box = rrect((bw, bh), 16, (8, 6, 20, 170))
    frame.alpha_composite(box, (W // 2 - bw // 2, H - 70 - bh))
    paste(frame, img, W // 2, H - 70 - bh + 5, 1.0, "mt")


def draw_brand(frame, t):
    tag = text_img(CHANNEL, F_ITAL, 30, WHITE, glow=PINK)
    paste(frame, tag, W - 60 - tag.width + tag.info["pad"] * 2, 40, 0.85)


# ---------------------------------------------------------------- principal
def build(script_path, outdir):
    if script_path.endswith(".py"):
        ns = {}
        exec(open(script_path).read(), ns)
        sc = ns["SCRIPT"]
    else:
        with open(script_path) as f:
            sc = json.load(f)
    slug = sc["slug"]
    work = os.path.join(outdir, f"_work_{slug}")
    os.makedirs(work, exist_ok=True)
    scenes = sc["scenes"][:3] if PREVIEW else sc["scenes"]

    # 1) voz
    timeline = []
    t0 = 0.0
    wavs = []
    for i, s in enumerate(scenes):
        p = os.path.join(work, f"s{i:03d}.wav")
        d = tts(s["say"], p) if s.get("say") else 0.0
        if not s.get("say"):
            sr = 16000
            with wave.open(p, "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
                w.writeframes(np.zeros(int(sr * s.get("dur", 2.0)), dtype=np.int16).tobytes())
            d = s.get("dur", 2.0)
        dur = d + s.get("hold", 0.25)
        timeline.append((t0, dur, s))
        wavs.append((p, dur))
        t0 += dur
    total = t0
    print(f"[{slug}] duración total: {total/60:.2f} min, escenas: {len(scenes)}", flush=True)

    # 2) pista de voz unida (respetando duraciones)
    sr = 16000
    voice = np.zeros(int(total * sr) + sr, dtype=np.int16)
    pos = 0.0
    for p, dur in wavs:
        with wave.open(p) as w:
            a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
            sr = w.getframerate()
        st = int(pos * sr)
        voice[st:st + len(a)] = a[: len(voice) - st]
        pos += dur
    vpath = os.path.join(work, "voice.wav")
    with wave.open(vpath, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(voice.tobytes())
    mpath = os.path.join(work, "music.wav")
    write_music(mpath, total + 1, key=sc.get("music_key", "a"), bpm=sc.get("bpm", 96), seed=sc.get("seed", 1))
    apath = os.path.join(work, "mix.m4a")
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", vpath, "-i", mpath, "-filter_complex",
        "[0:a]aresample=48000,highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,"
        "equalizer=f=3000:t=q:w=1:g=3,volume=1.6,asplit=2[v][sc];"
        "[1:a]aresample=48000,volume=0.22[m];"
        "[m][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[md];"
        "[v][md]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[out]",
        "-map", "[out]", "-c:a", "aac", "-b:a", "192k", apath], check=True)

    # 3) capítulos (para la descripción de YouTube)
    chapters = []
    for st, dur, s in timeline:
        if s["v"]["t"] in ("chapter",) or (s["v"]["t"] == "title" and st == 0):
            name = s["v"].get("title") if s["v"]["t"] == "chapter" else "Intro"
            chapters.append(f"{int(st//60)}:{int(st%60):02d} {name}")
    with open(os.path.join(outdir, f"{slug}_capitulos.txt"), "w") as f:
        f.write("\n".join(chapters) + "\n")
    # SRT
    srt = []
    k = 1
    for st, dur, s in timeline:
        if not s.get("say"):
            continue
        for a, b, c in caption_chunks(s["say"], dur):
            def ts(x):
                x = st + x
                return f"{int(x//3600):02d}:{int(x%3600//60):02d}:{int(x%60):02d},{int((x%1)*1000):03d}"
            srt.append(f"{k}\n{ts(a)} --> {ts(b)}\n{c}\n")
            k += 1
    with open(os.path.join(outdir, f"{slug}.srt"), "w") as f:
        f.write("\n".join(srt))

    # 4) vídeo
    scale = "960:540" if PREVIEW else f"{W}:{H}"
    out = os.path.join(outdir, f"{slug}{'_preview' if PREVIEW else ''}.mp4")
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-", "-i", apath, "-vf", f"scale={scale}", "-c:v", "libx264", "-preset",
        os.environ.get("X264_PRESET", "medium"), "-crf", os.environ.get("CRF", "21"), "-pix_fmt", "yuv420p",
        "-tune", "animation", "-c:a", "copy", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    nframes = int(total * FPS)
    si = 0
    caps_cache = {}
    for fi in range(nframes):
        t = fi / FPS
        while si < len(timeline) - 1 and t >= timeline[si][0] + timeline[si][1]:
            si += 1
        st, dur, s = timeline[si]
        lt = t - st
        frame = Image.new("RGBA", (W, H), BG + (255,))
        SCENES[s["v"]["t"]](frame, s["v"], lt, dur, t)
        # fundido corto entre escenas
        if lt < 0.12 and si > 0:
            frame.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * (1 - lt / 0.12)))))
        if s.get("say") and not s.get("nocap"):
            if si not in caps_cache:
                caps_cache = {si: caption_chunks(s["say"], dur)}
            for a, b, c in caps_cache[si]:
                if a <= lt < b:
                    draw_caption(frame, c)
                    break
        if s["v"]["t"] not in ("title", "outro"):
            draw_brand(frame, t)
        ff.stdin.write(frame.tobytes())
        if fi % (FPS * 30) == 0:
            print(f"[{slug}] {t/60:.1f}/{total/60:.1f} min", flush=True)
    ff.stdin.close()
    ff.wait()
    print(f"[{slug}] OK -> {out}", flush=True)


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
