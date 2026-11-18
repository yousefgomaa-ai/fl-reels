#!/usr/bin/env python3
"""A vertical 1080x1920 puzzle reel: shape-math with a 5-second countdown, then the answer.

Everything is drawn here with PIL and numpy, and the music and sound effects are synthesised from sine waves
(no samples, no noise), then ffmpeg joins them into an MP4.

    python3 puzzles/shape_math.py out/shape-math.mp4

The puzzle (checked by `check()` below before anything is drawn):
    circle + circle + circle     = 30  -> circle   = 10
    triangle + triangle + circle = 20  -> triangle = 5
    square + triangle + triangle = 13  -> square   = 3
    square + circle x triangle   = ?   -> 3 + 10 x 5 = 3 + 50 = 53   (multiplication first; the trap answer is 65)
"""
import math
import os
import random
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
DUR = 23.0
SR = 44100

# ---------------------------------------------------------------- the puzzle
VAL = {"circle": 10, "triangle": 5, "square": 3}
ROWS = [
    (["circle", "+", "circle", "+", "circle"], 30),
    (["triangle", "+", "triangle", "+", "circle"], 20),
    (["square", "+", "triangle", "+", "triangle"], 13),
]
QUESTION = ["square", "+", "circle", "×", "triangle"]
ANSWER, TRAP = 53, 65


def check():
    def ev(tokens, left_to_right=False):
        expr = " ".join(str(VAL[t]) if t in VAL else {"×": "*"}.get(t, t) for t in tokens)
        if left_to_right:  # the wrong way people read it: (3 + 10) x 5
            a, op, b, op2, c = expr.split()
            return eval(f"({a}{op}{b}){op2}{c}")
        return eval(expr)

    for toks, total in ROWS:
        assert ev(toks) == total, (toks, total)
    # each row must pin its new shape down uniquely given the earlier rows (they do: 3c=30, 2t+c=20, s+2t=13)
    assert ev(QUESTION) == ANSWER and ev(QUESTION, True) == TRAP


# ---------------------------------------------------------------- fonts & colours
def font_path(names):
    for d in ["/usr/share/fonts/opentype/inter", "/usr/share/fonts/truetype/inter", "/usr/share/fonts/truetype/dejavu"]:
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return p
    raise SystemExit("no font found: install fonts-inter")


BLACK = font_path(["Inter-Black.otf", "Inter-Black.ttf", "DejaVuSans-Bold.ttf"])
XBOLD = font_path(["Inter-ExtraBold.otf", "Inter-ExtraBold.ttf", "DejaVuSans-Bold.ttf"])
_fonts = {}


def F(path, size):
    k = (path, size)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(path, size)
    return _fonts[k]


WHITE = (255, 255, 255, 255)
GOLD = (255, 205, 60, 255)
RED = (255, 70, 90, 255)
INK = (20, 10, 45, 255)
SHAPE_COL = {"circle": (255, 140, 50), "triangle": (60, 215, 255), "square": (255, 80, 170)}


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, start, dur):
    return clamp((t - start) / dur)


def out_cubic(x):
    return 1 - (1 - x) ** 3


def out_back(x, s=1.9):
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


def in_cubic(x):
    return x ** 3


def elastic(x):
    if x <= 0 or x >= 1:
        return clamp(x)
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi) / 3) + 1


# ---------------------------------------------------------------- sprites
def text_sprite(s, size, fill=WHITE, font=BLACK, stroke=0, stroke_fill=INK, shadow=True):
    f = F(font, size)
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, r, b = d.textbbox((0, 0), s, font=f, stroke_width=stroke)
    pad = 24
    im = Image.new("RGBA", (r - l + pad * 2, b - t + pad * 2), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - l + 4, pad - t + 9), s, font=f, fill=(0, 0, 0, 150),
                                stroke_width=stroke, stroke_fill=(0, 0, 0, 150))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(im).text((pad - l, pad - t), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return im


def shape_sprite(kind, size):
    k = 4
    S = size * k
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = SHAPE_COL[kind]
    lite = tuple(min(255, c + 70) for c in col)
    m = 10 * k
    ow = 7 * k
    if kind == "circle":
        d.ellipse([m, m, S - m, S - m], fill=col + (255,), outline=WHITE, width=ow)
        d.ellipse([S * 0.28, S * 0.2, S * 0.5, S * 0.38], fill=lite + (160,))
    elif kind == "square":
        d.rounded_rectangle([m * 1.6, m * 1.6, S - m * 1.6, S - m * 1.6], radius=S // 9, fill=col + (255,),
                            outline=WHITE, width=ow)
        d.rounded_rectangle([S * 0.27, S * 0.25, S * 0.5, S * 0.36], radius=S // 30, fill=lite + (150,))
    else:
        h = (S - 2 * m) * math.sqrt(3) / 2
        top = (S - h) / 2 + 2 * k
        pts = [(S / 2, top), (S - m, top + h), (m, top + h)]
        d.polygon(pts, fill=col + (255,))
        d.line(pts + [pts[0], pts[1]], fill=WHITE, width=ow, joint="curve")
        d.ellipse([S * 0.44, S * 0.36, S * 0.54, S * 0.48], fill=lite + (160,))
    im = im.resize((size, size), Image.LANCZOS)
    # soft glow behind
    glow = Image.new("RGBA", (size + 60, size + 60), (0, 0, 0, 0))
    a = im.split()[3].point(lambda v: v * 0.55)
    g = Image.new("RGBA", im.size, col + (0,))
    g.putalpha(a)
    glow.alpha_composite(g, (30, 30))
    glow = glow.filter(ImageFilter.GaussianBlur(14))
    glow.alpha_composite(im, (30, 30))
    return glow


def panel(w, h, border=(255, 255, 255, 70), fill=(255, 255, 255, 26), bw=3, r=40):
    k = 2
    im = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([bw * k, bw * k, w * k - bw * k, h * k - bw * k], radius=r * k, fill=fill,
                                         outline=border, width=bw * k)
    return im.resize((w, h), Image.LANCZOS)


def row_sprite(tokens, rhs, shape=108, size=84, w=860, h=150, border=(255, 255, 255, 70), qfill=WHITE):
    parts = []
    for tok in tokens:
        parts.append(shape_sprite(tok, shape) if tok in SHAPE_COL else text_sprite(tok, size, shadow=False))
    parts.append(text_sprite("=", size, shadow=False))
    parts.append(text_sprite(str(rhs), size, fill=qfill if rhs == "?" else GOLD, shadow=False))
    gap = -14
    total = sum(p.width for p in parts) + gap * (len(parts) - 1)
    im = panel(w, h, border=border)
    x = (w - total) // 2
    for p in parts:
        im.alpha_composite(p, (x, (h - p.height) // 2))
        x += p.width + gap
    return im


def ring_sprite(frac, num_col, r=118, width=20):
    k = 2
    S = (r + width + 8) * 2 * k
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = S / 2
    box = [c - r * k, c - r * k, c + r * k, c + r * k]
    d.ellipse([c - (r - width) * k, c - (r - width) * k, c + (r - width) * k, c + (r - width) * k],
              fill=(15, 8, 40, 200))
    d.arc(box, 0, 360, fill=(255, 255, 255, 45), width=width * k)
    if frac > 0:
        d.arc(box, -90, -90 + 360 * frac, fill=num_col, width=width * k)
    return im.resize((S // k, S // k), Image.LANCZOS)


def rays_sprite(R=560, n=14):
    im = Image.new("RGBA", (R * 2, R * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i in range(n):
        a0 = 2 * math.pi * i / n
        a1 = a0 + math.pi / n * 0.8
        d.polygon([(R, R), (R + R * math.cos(a0), R + R * math.sin(a0)), (R + R * math.cos(a1), R + R * math.sin(a1))],
                  fill=(255, 210, 80, 60))
    mask = Image.radial_gradient("L").resize((R * 2, R * 2)).point(lambda v: 255 - v)
    a = Image.composite(im.split()[3], Image.new("L", im.size, 0), mask)
    im.putalpha(a)
    return im.filter(ImageFilter.GaussianBlur(3))


# ---------------------------------------------------------------- drawing helpers
def put(canvas, spr, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if alpha <= 0.003 or scale <= 0.01:
        return
    if abs(scale - 1) > 1e-3:
        spr = spr.resize((max(1, int(spr.width * scale)), max(1, int(spr.height * scale))), Image.BILINEAR)
    if abs(rot) > 0.05:
        spr = spr.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 0.999:
        spr = spr.copy()
        spr.putalpha(spr.split()[3].point(lambda v: int(v * alpha)))
    x, y = int(round(cx - spr.width / 2)), int(round(cy - spr.height / 2))
    sx, sy = max(0, -x), max(0, -y)
    ex, ey = min(spr.width, W - x), min(spr.height, H - y)
    if ex <= sx or ey <= sy:
        return
    canvas.alpha_composite(spr, (x + sx, y + sy), (sx, sy, ex, ey))


# animated background, computed small and scaled up (it is all soft gradients)
BW, BH = 270, 480
_yy, _xx = np.mgrid[0:BH, 0:BW].astype(np.float32)
_grad = np.zeros((BH, BW, 3), np.float32)
_top, _bot = np.array([42, 14, 92], np.float32), np.array([8, 18, 52], np.float32)
_grad[:] = (_top[None, None, :] * (1 - _yy[..., None] / BH) + _bot[None, None, :] * (_yy[..., None] / BH))
BLOBS = [((120, 60, 255), 0.25, 0.25, 0.23, 0.31), ((255, 60, 160), 0.8, 0.55, 0.19, 0.43),
         ((40, 190, 255), 0.35, 0.85, 0.17, 0.37)]


def background(t, red=0.0, gold=0.0):
    img = _grad.copy()
    for i, (col, bx, by, sp, ph) in enumerate(BLOBS):
        cx = (bx + 0.18 * math.sin(t * sp * 2 + ph * 10)) * BW
        cy = (by + 0.12 * math.cos(t * sp * 1.7 + i)) * BH
        rad = (0.42 + 0.06 * math.sin(t * 0.9 + i)) * BW
        g = np.exp(-((_xx - cx) ** 2 + (_yy - cy) ** 2) / (2 * rad * rad))
        img += g[..., None] * np.array(col, np.float32) * 0.33
    if red > 0:
        img = img * (1 - 0.35 * red) + np.array([200, 20, 40], np.float32) * 0.35 * red
    if gold > 0:
        img = img * (1 - 0.25 * gold) + np.array([255, 170, 40], np.float32) * 0.25 * gold
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.BILINEAR)
    return im.convert("RGBA")


rng = random.Random(7)
DOTS = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(2, 6), rng.uniform(15, 60), rng.uniform(0, 6.28))
        for _ in range(46)]
CONF = []
for _ in range(150):
    ang = rng.uniform(-math.pi * 0.95, -math.pi * 0.05)
    sp = rng.uniform(700, 1700)
    CONF.append((math.cos(ang) * sp, math.sin(ang) * sp, rng.uniform(0, 6.28), rng.uniform(-14, 14),
                 rng.choice([GOLD, (255, 255, 255, 255), RED, (60, 215, 255, 255), (255, 80, 170, 255)]),
                 rng.uniform(10, 22)))


def draw_dots(canvas, t):
    d = ImageDraw.Draw(canvas)
    for x, y, r, v, ph in DOTS:
        yy = (y - v * t) % H
        xx = x + 18 * math.sin(t * 0.8 + ph)
        a = int(60 + 50 * math.sin(t * 2 + ph))
        d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(255, 255, 255, a))


def draw_confetti(canvas, t, t0, cx, cy):
    dt = t - t0
    if dt < 0 or dt > 3.2:
        return
    d = ImageDraw.Draw(canvas)
    for vx, vy, rot0, vr, col, s in CONF:
        x = cx + vx * dt * 0.9
        y = cy + vy * dt + 1300 * dt * dt
        if y > H + 40:
            continue
        a = rot0 + vr * dt
        w2, h2 = s, s * 0.45
        ca, sa = math.cos(a), math.sin(a)
        pts = [(x + ca * px - sa * py, y + sa * px + ca * py) for px, py in [(-w2, -h2), (w2, -h2), (w2, h2), (-w2, h2)]]
        fade = clamp((3.2 - dt) / 0.6)
        d.polygon(pts, fill=col[:3] + (int(255 * fade),))


# ---------------------------------------------------------------- timeline (seconds)
T_ROW = [2.0, 3.25, 4.5]
T_Q = 5.8
T_CTA = 6.7
T_CD = 7.5           # countdown 5..1 runs T_CD .. T_CD+5
T_UP = T_CD + 5      # 12.5 time's up
T_CHIP = [13.3, 13.75, 14.2]
T_L1, T_L2, T_ANS, T_NOT = 15.0, 16.0, 17.1, 18.1
T_END = 19.4


def build_sprites():
    S = {}
    S["shapes_big"] = {k: shape_sprite(k, 210) for k in SHAPE_COL}
    S["most"] = text_sprite("MOST PEOPLE", 118, stroke=6)
    S["wrong"] = text_sprite("GET THIS WRONG", 112, fill=GOLD, stroke=6)
    S["can"] = text_sprite("Can you solve it?", 64, font=XBOLD)
    S["header"] = text_sprite("CAN YOU SOLVE IT?", 70, fill=GOLD, stroke=4)
    S["rows"] = [row_sprite(t, r) for t, r in ROWS]
    S["q"] = row_sprite(QUESTION, "?", shape=118, size=92, w=900, h=172, border=(255, 205, 60, 230))
    S["cta1"] = text_sprite("Comment your answer", 62, font=XBOLD)
    S["cta2"] = text_sprite("BEFORE THE TIMER ENDS!", 58, fill=GOLD, stroke=3)
    S["nums"] = {n: text_sprite(str(n), 150, stroke=0, shadow=False) for n in range(1, 6)}
    S["up"] = text_sprite("TIME'S UP!", 130, fill=RED, stroke=7, stroke_fill=WHITE)
    S["answer_hdr"] = text_sprite("THE ANSWER", 70, fill=GOLD, stroke=4)
    chips = []
    for k in ["circle", "triangle", "square"]:
        p = panel(300, 150, border=SHAPE_COL[k] + (220,), fill=(255, 255, 255, 30))
        sh = shape_sprite(k, 92)
        tx = text_sprite(f"= {VAL[k]}", 70, shadow=False)
        p.alpha_composite(sh, (6, (150 - sh.height) // 2))
        p.alpha_composite(tx, (sh.width - 28, (150 - tx.height) // 2))
        chips.append(p)
    S["chips"] = chips
    v = VAL
    S["l1"] = text_sprite(f"{v['square']} + {v['circle']} × {v['triangle']}", 104, stroke=3)
    S["l2"] = text_sprite(f"= {v['square']} + {v['circle'] * v['triangle']}", 104, stroke=3)
    S["rule"] = text_sprite("× comes before +", 54, fill=(140, 230, 255, 255), font=XBOLD)
    S["ans"] = text_sprite(f"= {ANSWER}", 230, fill=GOLD, stroke=9)
    S["not"] = text_sprite(f"NOT {TRAP}!", 96, fill=RED, stroke=5, stroke_fill=WHITE)
    S["rays"] = rays_sprite()
    S["e1"] = text_sprite(f"Got {ANSWER}? Say it below", 66, font=XBOLD)
    S["e2"] = text_sprite(f"Tag a friend who said {TRAP}", 60, fill=GOLD, font=XBOLD)
    S["e3"] = text_sprite("Follow for a new puzzle every day", 48, fill=(220, 220, 255, 255), font=XBOLD)
    S["arrow"] = arrow_sprite()
    return S


def arrow_sprite():
    k = 4
    im = Image.new("RGBA", (90 * k, 110 * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([30 * k, 0, 60 * k, 62 * k], radius=10 * k, fill=GOLD)
    d.polygon([(0, 52 * k), (90 * k, 52 * k), (45 * k, 108 * k)], fill=GOLD)
    return im.resize((90, 110), Image.LANCZOS)


ROW_Y = [420, 590, 760]
Q_Y = 975


def frame(t, S):
    red = 0.0
    if T_CD + 2 <= t < T_UP:  # last three seconds pulse red on each tick
        red = 0.55 * math.exp(-((t - T_CD) % 1.0) * 4)
    gold = 0.0
    if T_ANS <= t < T_ANS + 1.2:
        gold = math.exp(-(t - T_ANS) * 3)
    c = background(t, red, gold)
    draw_dots(c, t)

    # ---- hook (0 - 2.0)
    if t < 2.15:
        out = prog(t, 1.75, 0.35)
        fade = 1 - out_cubic(out)
        names = ["circle", "triangle", "square"]
        starts = [(-250, -200), (W + 250, 300), (-250, 900)]
        for i, k in enumerate(names):
            p = out_back(prog(t, 0.05 + i * 0.09, 0.5))
            sx, sy = starts[i]
            tx, ty = 230 + i * 310, 560
            x = sx + (tx - sx) * p
            y = sy + (ty - sy) * p + 12 * math.sin(t * 5 + i)
            rot = (1 - p) * 540 + 6 * math.sin(t * 4 + i)
            put(c, S["shapes_big"][k], x, y - out * 300, 1 + 0.4 * out, fade, rot)
        p1 = prog(t, 0.12, 0.28)
        if p1 > 0:
            put(c, S["most"], W / 2, 900 - out * 120, 2.4 - 1.4 * out_cubic(p1) + 0.3 * out, min(1, p1 * 3) * fade)
        p2 = prog(t, 0.38, 0.28)
        if p2 > 0:
            pulse = 1 + 0.04 * math.sin(t * 14)
            put(c, S["wrong"], W / 2, 1040 - out * 60, (2.4 - 1.4 * out_cubic(p2)) * pulse + 0.3 * out,
                min(1, p2 * 3) * fade, -3 * (1 - p2) + 2 * math.sin(t * 6))
        p3 = prog(t, 0.95, 0.4)
        if p3 > 0:
            put(c, S["can"], W / 2, 1210 + 40 * (1 - out_cubic(p3)), 1, p3 * fade)

    # ---- header (stays from 2.0 on)
    if t >= 1.9:
        p = out_back(prog(t, 1.9, 0.45))
        hdr = S["header"] if t < T_UP + 0.3 else S["answer_hdr"]
        sw = 1.0
        if T_UP + 0.1 <= t < T_UP + 0.5:  # flip to "THE ANSWER"
            sw = abs(math.cos(prog(t, T_UP + 0.1, 0.4) * math.pi))
        put(c, hdr, W / 2, 210 + 8 * math.sin(t * 3), p * (0.6 + 0.4 * sw), clamp(p) * 1, 0)

    # ---- puzzle rows (leave when the answer starts)
    leave = out_cubic(prog(t, T_UP + 0.35, 0.5))
    for i, (ty, t0) in enumerate(zip(ROW_Y, T_ROW)):
        if t < t0:
            continue
        p = out_back(prog(t, t0, 0.55), 1.4)
        x = W / 2 + (1 - p) * 900 - leave * (W + 200) * (1 if i % 2 == 0 else -1)
        bob = 5 * math.sin(t * 2.2 + i * 1.3)
        put(c, S["rows"][i], x, ty + bob, 1 + 0.02 * math.sin(t * 3 + i), 1 - leave * 0.3)

    # ---- question row: drops in, pulses, then rises to the top for the solution
    if t >= T_Q:
        p = elastic(prog(t, T_Q, 0.9))
        rise = out_cubic(prog(t, T_UP + 0.5, 0.6))
        y = Q_Y - 420 * (1 - p) * 0 + (-(1 - clamp(p)) * 200) + rise * (640 - Q_Y)
        sc = (0.4 + 0.6 * p) * (1 + 0.035 * math.sin(t * 7)) if t < T_UP else 1 + 0.015 * math.sin(t * 4)
        put(c, S["q"], W / 2, y, sc, clamp(prog(t, T_Q, 0.2)))

    # ---- comment CTA during the countdown
    if T_CTA <= t < T_UP + 0.3:
        p = out_back(prog(t, T_CTA, 0.5))
        a = 1 - prog(t, T_UP, 0.3)
        put(c, S["cta1"], W / 2 + (1 - p) * -700, 1135, 1, a)
        put(c, S["cta2"], W / 2 + (1 - p) * 700, 1210, 1 + 0.05 * max(0, math.sin(t * 8)), a)

    # ---- countdown ring
    if T_CD - 0.3 <= t < T_UP + 0.45:
        app = out_back(prog(t, T_CD - 0.3, 0.4))
        gone = prog(t, T_UP, 0.45)
        rem = clamp(1 - (t - T_CD) / 5)
        sec = int(math.ceil(T_UP - t)) if t >= T_CD else 5
        sec = max(1, min(5, sec))
        hue = clamp((t - T_CD) / 5)
        col = (int(80 + 175 * hue), int(230 - 170 * hue), int(140 - 60 * hue), 255)
        ring = ring_sprite(rem, col)
        cy = 1395
        sc = app * (1 + 0.5 * out_cubic(gone))
        put(c, ring, W / 2, cy, sc, 1 - gone)
        if t >= T_CD:
            within = (t - T_CD) % 1.0
            nsc = 1 + 0.45 * math.exp(-within * 7)
            num = S["nums"][sec]
            put(c, num, W / 2, cy - 4, nsc * app, 1 - gone)

    # ---- time's up
    if T_UP <= t < T_UP + 1.0:
        p = prog(t, T_UP, 0.25)
        a = 1 - prog(t, T_UP + 0.65, 0.35)
        put(c, S["up"], W / 2, 1395, 2.2 - 1.2 * out_cubic(p), min(1, p * 3) * a, 4 * math.sin(t * 30) * (1 - p))

    # ---- solution
    for i, t0 in enumerate(T_CHIP):
        if t >= t0:
            p = out_back(prog(t, t0, 0.45), 2.2)
            end = out_cubic(prog(t, T_END, 0.4))
            put(c, S["chips"][i], 200 + i * 340 - 20 * (i == 1) * 0, 410 + 6 * math.sin(t * 3 + i) - end * 30, p, 1 - end * 0.15)
    end = out_cubic(prog(t, T_END, 0.45))
    if t >= T_L1:
        p = out_cubic(prog(t, T_L1, 0.4))
        put(c, S["l1"], W / 2 + (1 - p) * 800, 840, 1, p * (1 - end))
    if t >= T_L2:
        p = out_cubic(prog(t, T_L2, 0.4))
        put(c, S["l2"], W / 2 - (1 - p) * 800, 990, 1, p * (1 - end))
        pr = prog(t, T_L2 + 0.35, 0.35)
        put(c, S["rule"], W / 2, 1090, out_back(pr), pr * (1 - end))
    if t >= T_ANS:
        p = prog(t, T_ANS, 0.5)
        y = 1270 - end * 360
        put(c, S["rays"], W / 2, y, 0.3 + 0.8 * out_cubic(p), clamp(p * 2), (t - T_ANS) * 25)
        put(c, S["ans"], W / 2, y, (0.2 + 0.8 * elastic(p)) * (1 + 0.03 * math.sin(t * 6)), clamp(p * 4))
    if T_NOT <= t:
        p = out_back(prog(t, T_NOT, 0.35), 2.5)
        a = 1 - end
        spr = S["not"]
        put(c, spr, W / 2, 1450, p, a, -4 + 2 * math.sin(t * 5))
        ps = prog(t, T_NOT + 0.3, 0.25)
        if ps > 0 and a > 0:
            d = ImageDraw.Draw(c)
            half = spr.width * 0.42
            x0 = W / 2 - half
            d.line([(x0, 1460), (x0 + 2 * half * ps, 1440)], fill=WHITE[:3] + (int(255 * a),), width=12)

    # ---- end card
    if t >= T_END + 0.2:
        for j, (k, y) in enumerate([("e1", 1150), ("e2", 1260), ("e3", 1370)]):
            p = out_back(prog(t, T_END + 0.2 + j * 0.35, 0.45))
            put(c, S[k], W / 2 + (1 - p) * (700 if j % 2 else -700), y + 4 * math.sin(t * 3 + j), 1, clamp(p))
        pa = prog(t, T_END + 1.3, 0.3)
        put(c, S["arrow"], W / 2, 1490 + 22 * abs(math.sin(t * 5)), 1, pa)

    draw_confetti(c, t, T_ANS, W / 2, 1270)

    # progress bar: something to wait for until the end
    d = ImageDraw.Draw(c)
    d.rectangle([0, 0, W, 12], fill=(255, 255, 255, 40))
    d.rectangle([0, 0, int(W * t / DUR), 12], fill=GOLD)

    c = c.convert("RGB")
    # camera shake on impacts
    shake = 0
    for ti, amp in [(0.14, 16), (0.4, 18), (T_UP, 20), (T_ANS, 16)]:
        if ti <= t < ti + 0.3:
            shake = amp * (1 - (t - ti) / 0.3)
    if shake:
        dx = int(shake * math.sin(t * 91))
        dy = int(shake * math.cos(t * 77))
        base = c.copy()
        c.paste(base, (dx, dy))
    # fade from black for the first 3 frames is skipped on purpose: frame 0 must already grab attention
    return c


# ---------------------------------------------------------------- audio
def env(n, a=0.004, d=0.2):
    t = np.arange(n) / SR
    e = np.minimum(1, t / a) * np.exp(-t / d)
    tail = min(n, int(0.006 * SR))
    e[-tail:] *= np.linspace(1, 0, tail)
    return e


def tone(freq, dur, harm=(1.0,), a=0.004, d=0.2, sweep=None):
    n = int(dur * SR)
    t = np.arange(n) / SR
    if sweep is not None:
        f = freq * (sweep / freq) ** (t / dur)
        ph = 2 * np.pi * np.cumsum(f) / SR
    else:
        ph = 2 * np.pi * freq * t
    y = sum(h * np.sin(ph * (i + 1)) for i, h in enumerate(harm))
    return y * env(n, a, d)


def add(buf, sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= len(buf):
        return
    sig = sig[: len(buf) - i]
    l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
    buf[i:i + len(sig), 0] += sig * gain * l * 1.41
    buf[i:i + len(sig), 1] += sig * gain * r * 1.41


def midi(n):
    return 440 * 2 ** ((n - 69) / 12)


def music_and_sfx():
    n = int(DUR * SR)
    mus = np.zeros((n, 2))
    sfx = np.zeros((n, 2))
    bpm = 120
    beat = 60 / bpm
    # Am - F - C - G, one chord per bar (2 s)
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
    roots = [45, 41, 48, 43]

    def section(t):
        if T_CD <= t < T_UP:
            return "count"
        return "full"

    b = 0
    while b * beat < DUR:
        t = b * beat
        bar = int(t // 2) % 4
        sec = section(t)
        if sec == "full":
            # kick
            add(mus, tone(110, 0.35, (1.0,), a=0.002, d=0.12, sweep=42), t, 0.75)
            # bass on 8ths
            for e in range(2):
                add(mus, tone(midi(roots[bar]), beat / 2 * 0.95, (1, 0.35, 0.12), a=0.006, d=0.18), t + e * beat / 2, 0.32)
            # pluck arp on 8ths
            for e in range(2):
                note = chords[bar][(b * 2 + e) % 3] + 12
                add(mus, tone(midi(note), 0.4, (1, 0.25, 0.1, 0.05), a=0.003, d=0.12), t + e * beat / 2, 0.13,
                    pan=-0.4 if e else 0.4)
            # clap-like snare from stacked sines on 2 and 4 (no noise)
            if b % 2 == 1:
                add(mus, tone(330, 0.18, (1, 0.6, 0.4, 0.3, 0.2), a=0.002, d=0.05, sweep=180), t, 0.16)
        else:
            # heartbeat during the countdown
            if (t - T_CD) % 1.0 < 1e-6 or abs(((t - T_CD) % 1.0) - 0.0) < 1e-6:
                pass
        b += 1
    # pads: whole bars, quieter in the countdown
    for bar_i in range(int(DUR // 2) + 1):
        t = bar_i * 2.0
        ch = chords[bar_i % 4]
        g = 0.05
        for k, note in enumerate(ch):
            p = tone(midi(note), 2.1, (1, 0.5, 0.25, 0.12), a=0.25, d=1.6)
            add(mus, p, t, g, pan=(k - 1) * 0.5)
    # countdown: heartbeat thumps + rising tension tone
    for s in range(5):
        t = T_CD + s
        add(mus, tone(70, 0.3, (1.0, 0.3), a=0.003, d=0.09, sweep=45), t, 0.9)
        add(mus, tone(70, 0.3, (1.0, 0.3), a=0.003, d=0.08, sweep=45), t + 0.24, 0.6)
    nrise = int(5 * SR)
    tt = np.arange(nrise) / SR
    f = 220 * 2 ** (tt / 5)
    rise = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    rise *= np.minimum(1, tt / 0.5) * (0.3 + 0.7 * tt / 5)
    rise[-int(0.02 * SR):] *= np.linspace(1, 0, int(0.02 * SR))
    add(mus, rise, T_CD, 0.06)

    # sfx
    def pop(at, g=0.35, f0=500):
        add(sfx, tone(f0, 0.12, (1, 0.3), a=0.002, d=0.05, sweep=f0 * 2.2), at, g)

    def whoosh(at, g=0.18, up=True):
        dur = 0.35
        nn = int(dur * SR)
        t2 = np.arange(nn) / SR
        f1, f2 = (250, 1400) if up else (1400, 250)
        fr = f1 * (f2 / f1) ** (t2 / dur)
        s = sum(np.sin(2 * np.pi * np.cumsum(fr * m) / SR) / (j + 1) for j, m in enumerate([1, 1.013, 1.51]))
        s *= np.sin(np.pi * t2 / dur) ** 2
        add(sfx, s, at, g)

    def boom(at, g=0.9):
        add(sfx, tone(95, 0.8, (1.0, 0.4), a=0.002, d=0.25, sweep=32), at, g)

    def tick(at, hi=False, g=0.4):
        add(sfx, tone(2000 if hi else 1500, 0.06, (1.0,), a=0.001, d=0.012), at, g)
        add(sfx, tone(900 if hi else 700, 0.08, (1.0,), a=0.001, d=0.02), at, g * 0.6)

    def ding(at, g=0.35, base=880):
        for m, dd, gg in [(1, 1.2, 1), (2.0, 0.7, 0.4), (3.01, 0.45, 0.25), (4.2, 0.3, 0.15)]:
            add(sfx, tone(base * m, 1.4, (1.0,), a=0.002, d=dd), at, g * gg)

    boom(0.12, 0.9)
    boom(0.38, 0.7)
    for i in range(3):
        whoosh(0.03 + i * 0.09, 0.08)
    pop(0.98, 0.25, 700)
    whoosh(1.78, 0.12)
    for t0 in T_ROW:
        whoosh(t0 - 0.05, 0.14)
        pop(t0 + 0.22, 0.3)
    whoosh(T_Q - 0.05, 0.16, up=False)
    boom(T_Q + 0.25, 0.4)
    pop(T_CTA + 0.1, 0.22, 600)
    for s in range(5):
        tick(T_CD + s, hi=(s >= 2), g=0.45)
    # time's up: a falling two-note horn from stacked sines
    for k, nte in enumerate([72, 67]):
        add(sfx, tone(midi(nte), 0.32, (1, 0.6, 0.4, 0.25, 0.15), a=0.01, d=0.25), T_UP + k * 0.18, 0.18)
    boom(T_UP, 0.7)
    for t0 in T_CHIP:
        pop(t0 + 0.05, 0.3, 650)
    whoosh(T_L1 - 0.05, 0.13)
    whoosh(T_L2 - 0.05, 0.13, up=False)
    pop(T_L2 + 0.4, 0.2, 800)
    # drum roll before the answer: quick ticks
    for k in range(10):
        tick(T_ANS - 0.6 + k * 0.06, g=0.08 + 0.02 * k)
    boom(T_ANS, 0.7)
    for k, nte in enumerate([72, 76, 79, 84]):
        ding(T_ANS + 0.05 + k * 0.09, 0.16, midi(nte))
    pop(T_NOT, 0.3, 400)
    whoosh(T_END, 0.12)
    for j in range(3):
        pop(T_END + 0.25 + j * 0.35, 0.18, 600 + 100 * j)

    # music ducks under the countdown & ends with a fade
    tt = np.arange(n) / SR
    duck = np.ones(n)
    duck[(tt >= T_CD) & (tt < T_UP)] = 0.85
    fade = np.clip((DUR - tt) / 0.8, 0, 1)
    fin = np.clip(tt / 0.01, 0, 1)
    mix = mus * (duck * fade * fin)[:, None] * 0.8 + sfx * (fade * fin)[:, None]
    mix -= mix.mean(axis=0)
    mix = np.tanh(mix * 1.1)
    mix /= max(1e-9, np.abs(mix).max()) / 0.9
    return mix


def write_wav(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ---------------------------------------------------------------- main
def main():
    check()
    out = sys.argv[1] if len(sys.argv) > 1 else "out/shape-math.mp4"
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    wav = out[:-4] + ".wav"
    write_wav(wav, music_and_sfx())
    S = build_sprites()
    only = os.environ.get("ONLY_FRAMES")  # e.g. "0,1.0,9" -> write PNG stills instead of the video
    if only:
        for s in only.split(","):
            frame(float(s), S).save(f"{out[:-4]}-{float(s):05.2f}.png")
        return
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    nf = int(DUR * FPS)
    for i in range(nf):
        ff.stdin.write(frame(i / FPS, S).tobytes())
        if i % 60 == 0:
            print(f"frame {i}/{nf}", flush=True)
    ff.stdin.close()
    if ff.wait() != 0:
        raise SystemExit("ffmpeg failed")
    os.remove(wav)
    print("wrote", out)


if __name__ == "__main__":
    main()
