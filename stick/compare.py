#!/usr/bin/env python3
"""WHEN YOU COMPARE YOURSELF - a 19.3 s montage of five night scenes, one quiet line each, a flip at the end, loops.

Look: near-black stage, one spotlight per scene, light-grey figures with real shading (lit edge on the light side,
shadow on the far side, dark outline), a wet floor that reflects everything, depth of field (the background is
blurred), floating dust in the light, small spaced serif captions. Music: an epic cinematic cue on real GM
instruments (FluidSynth): piano ostinato, taiko, cellos, strings, brass and choir at the flip.

  S0 0.0-2.5   a giant phone, the hero in front of it shrinks with every scroll. WHEN YOU COMPARE YOURSELF
  S1 2.5-6.0   happy on his orange bike; a white sports car pulls up; the bike drains to grey, his head drops.
               (a barefoot man stands blurred in the dark behind - nobody notices him the first time)
               YOU WERE HAPPY. / UNTIL YOU LOOKED.
  S2 6.0-9.5   proud dumbbell curls; the guy next to him presses a huge barbell; he hides the dumbbell.
               SAME EFFORT. / LESS PRIDE.
  S3 9.5-13.0  the giant phone again: ring, house, promotion, stroller - he shrinks to a dot. EVERYONE SEEMS AHEAD.
  S4 13.0-16.0 a medal "5K" on his chest; his phone shows a marathon winner; he drops the medal, the light goes out.
               YOU FORGOT YOUR OWN WIN.
  S5 16.0-19.3 back at the grey bike; the camera pulls back, the man in the dark comes into focus: barefoot,
               torn shoes in his hand, staring at the bike. The hero turns; the bike's colour comes back.
               SOMEONE IS LOOKING AT YOU / THE SAME WAY.

    python3 stick/compare.py stick/compare.mp4
    ONLY_FRAMES=0,1.5,3.2,5.2,7.9,11,14.2,15.5,17,18.6 python3 stick/compare.py /tmp/cmp
"""
import math
import os
import subprocess
import sys
import tempfile
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perfect_wave as PW  # noqa
import ai_job as AJ  # noqa
import hq  # noqa
from perfect_wave import clamp, env, font, lerp, lerp_pose, midi, mix_in, noise, prog, smooth, tone, write_wav  # noqa

W, H, FPS = 1080, 1920, 30
K = 2
SR = 44100
DUR = 19.3
NF = int(round(DUR * FPS))
FLOOR = 1330
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"

BODY = (226, 227, 232)
INK = (14, 14, 18)
SCARF = (205, 40, 48)
ORANGE = (238, 140, 36)
DULL = (104, 98, 92)
GOLD = (244, 190, 60)

SC = [0.0, 2.5, 6.0, 9.5, 13.0, 16.0, DUR]        # scene starts


def scene_of(t):
    for i in range(6):
        if t < SC[i + 1]:
            return i, t - SC[i]
    return 5, t - SC[5]


# ---------------------------------------------------------------- 2x drawing helpers
def P(x, y):
    return (x * K, y * K)


def ell(d, cx, cy, rx, ry, fill, outline=None, w=0):
    d.ellipse([(cx - rx) * K, (cy - ry) * K, (cx + rx) * K, (cy + ry) * K], fill=fill, outline=outline,
              width=int(w * K))


def line(d, pts, fill, w):
    d.line([P(*p) for p in pts], fill=fill, width=int(w * K), joint="curve")
    for x, y in (pts[0], pts[-1]):
        ell(d, x, y, w / 2, w / 2, fill)


def rrect(d, box, r, fill, outline=None, w=0):
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0 * K, y0 * K, x1 * K, y1 * K], int(r * K), fill=fill, outline=outline, width=int(w * K))


def poly(d, pts, fill, outline=None, w=0):
    d.polygon([P(*p) for p in pts], fill=fill, outline=outline, width=int(w * K) if outline else 0)


# ---------------------------------------------------------------- stage: background with spotlights
_BG = {}


def stage_bg(spots):
    """spots: tuple of (x, strength). near-black, light cones from above, a floor with a sheen, vignette"""
    if spots in _BG:
        return _BG[spots]
    W2, H2 = W * K, H * K
    yy, xx = np.mgrid[0:H2:2, 0:W2:2].astype(np.float32) / K
    img = np.zeros(yy.shape + (3,), np.float32)
    img[:] = np.array([7, 8, 11], np.float32)
    floor = yy > FLOOR
    img[floor] = np.array([10, 11, 15], np.float32)
    for sx, st in spots:
        # cone: width grows downwards, soft edges
        half = 70 + (yy / FLOOR) * 330
        dx = np.abs(xx - sx)
        cone = np.clip(1 - (dx - half * 0.6) / (half * 0.6), 0, 1) * (yy < FLOOR + 5)
        cone *= np.clip(yy / 500, 0.15, 1.0) * 0.9
        img += cone[..., None] * np.array([26, 28, 34], np.float32) * st
        # pool of light on the floor
        pool = np.exp(-(((xx - sx) / 340) ** 2 + ((yy - FLOOR - 40) / 70) ** 2))
        img += pool[..., None] * np.array([60, 62, 70], np.float32) * st * floor[..., None]
    r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2)
    img *= np.clip(1.25 - r * 1.3, 0.25, 1.0)[..., None]
    rng = np.random.default_rng(3)
    img += rng.normal(0, 1.4, img.shape)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").resize((W2, H2), Image.BILINEAR)
    im = im.convert("RGBA")
    # floor ripples
    d = ImageDraw.Draw(im)
    for j in range(26):
        x, y = rng.uniform(0, W), rng.uniform(FLOOR + 30, H - 80)
        rx = rng.uniform(30, 90)
        ell(d, x, y, rx, rx * 0.12, None, outline=(30, 32, 40, 255), w=1.5)
    _BG[spots] = im
    return im


def dust(d, t, spots, seed=1, n=40):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        sx, st = spots[int(rng.integers(len(spots)))]
        x0, y0 = sx + rng.uniform(-260, 260), rng.uniform(200, FLOOR)
        sp, ph = rng.uniform(6, 18), rng.uniform(0, 6.28)
        x = x0 + 14 * math.sin(t * 0.4 + ph)
        y = (y0 - t * sp) % FLOOR
        a = int(st * (50 + 70 * (0.5 + 0.5 * math.sin(t * 1.7 + ph))))
        r = rng.uniform(1.0, 2.6)
        ell(d, x, y, r, r, (220, 224, 235, a))


# ---------------------------------------------------------------- shaded figures
BONES = [("neck", "hip"), ("neck", "el"), ("el", "hl"), ("neck", "er"), ("er", "hr"), ("hip", "kl"), ("kl", "fl"),
         ("hip", "kr"), ("kr", "fr")]


def _shift(a, dx, dy):
    out = np.zeros_like(a)
    h, w = a.shape
    sx, sy = int(round(dx)), int(round(dy))
    ys0, ys1 = max(0, -sy), min(h, h - sy)
    xs0, xs1 = max(0, -sx), min(w, w - sx)
    out[ys0 + sy:ys1 + sy, xs0 + sx:xs1 + sx] = a[ys0:ys1, xs0:xs1]
    return out


def figure(layer, pts, s, light=(-0.6, -0.8), body=BODY, alpha=1.0, blur=0.0, scarf=False, back=None):
    """draw a volumetric stick figure onto a 2x RGBA layer. pts in 1x screen coords."""
    lw = 21 * s
    hr = 31 * s
    xs = [p[0] for p in pts.values()]
    ys = [p[1] for p in pts.values()]
    pad = hr + lw + 20 + blur * 3
    x0, y0 = int(min(xs) - pad), int(min(ys) - pad)
    x1, y1 = int(max(xs) + pad), int(max(ys) + pad)
    w2, h2 = (x1 - x0) * K, (y1 - y0) * K
    if w2 <= 4 or h2 <= 4:
        return
    m = Image.new("L", (w2, h2), 0)
    md = ImageDraw.Draw(m)

    def Q(p):
        return ((p[0] - x0) * K, (p[1] - y0) * K)
    for b0, b1 in BONES:
        md.line([Q(pts[b0]), Q(pts[b1])], fill=255, width=int(lw * K))
        for p in (pts[b0], pts[b1]):
            cx, cy = Q(p)
            r = lw * K / 2
            md.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    hx, hy = Q(pts["head"])
    md.ellipse([hx - hr * K, hy - hr * K, hx + hr * K, hy + hr * K], fill=255)
    a = np.asarray(m, np.float32) / 255
    dd = 9 * s * K
    lx, ly = light
    toward = _shift(a, -lx * dd, -ly * dd)
    away = _shift(a, lx * dd, ly * dd)
    shadow = Image.fromarray((a * (1 - away) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5 * s * K))
    rim = Image.fromarray((a * (1 - toward) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.5 * s * K))
    sh = np.asarray(shadow, np.float32)[..., None] / 255
    rm = np.asarray(rim, np.float32)[..., None] / 255
    yy = np.linspace(0, 1, h2, dtype=np.float32)[:, None, None]
    col = np.array(body, np.float32)[None, None, :] * (1.04 - 0.16 * yy)
    col = col * (1 - 0.55 * sh) + 38 * rm
    rgb = np.clip(col * np.ones((h2, w2, 1), np.float32), 0, 255).astype(np.uint8)
    fig = Image.fromarray(rgb, "RGB").convert("RGBA")
    fig.putalpha(m)
    # dark outline under the figure
    out = m.filter(ImageFilter.MaxFilter(int(2 * s * K) * 2 + 1))
    o = Image.new("RGBA", m.size, INK + (255,))
    o.putalpha(out)
    o.alpha_composite(fig)
    if scarf:
        od = ImageDraw.Draw(o)
        nx, ny = Q(pts["neck"])
        bx = -1 if back is None else back
        od.ellipse([nx - 20 * s * K, ny - 9 * s * K, nx + 20 * s * K, ny + 13 * s * K], fill=SCARF + (255,))
        od.polygon([(nx, ny), (nx + bx * 44 * s * K, ny + 26 * s * K), (nx + bx * 30 * s * K, ny + 40 * s * K)],
                   fill=SCARF + (255,))
    if blur > 0:
        o = o.filter(ImageFilter.GaussianBlur(blur * K))
    if alpha < 0.999:
        o.putalpha(o.split()[3].point(lambda v: int(v * alpha)))
    layer.alpha_composite(o, (x0 * K, y0 * K))


def ik(a, b, l1, l2, sgn):
    dx, dy = b[0] - a[0], b[1] - a[1]
    dist = max(1e-3, min(math.hypot(dx, dy), l1 + l2 - 1e-3))
    ang = math.atan2(dy, dx)
    c = (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist)
    off = math.acos(clamp(c, -1, 1))
    return (a[0] + l1 * math.cos(ang + sgn * off), a[1] + l1 * math.sin(ang + sgn * off))


def place(pose, hip, f, s):
    return AJ.place(pose, hip, f, s)


STAND = PW.STAND
LOOK_UP = dict(STAND, head=(10, -152), neck=(5, -108))
SAD = dict(STAND, head=(16, -136), neck=(8, -104), el=(4, -60), hl=(6, -12), er=(14, -58), hr=(18, -10))
PROUD = dict(STAND, head=(-6, -152), neck=(-3, -108))
CHEER = dict(STAND, el=(-34, -140), hl=(-44, -190), er=(34, -140), hr=(44, -190))


def stand_hip(x, s, feet=FLOOR):
    return (x, feet - 113 * s)


# ---------------------------------------------------------------- props
def giant_phone(d, layer, t, posts, ticks, cx=650):
    x0, y0, x1, y1 = cx - 180, 520, cx + 180, FLOOR
    # light from the screen
    glow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    ell(gd, cx, (y0 + y1) / 2, 330, 470, (120, 150, 255, 46))
    ell(gd, cx, FLOOR + 30, 380, 60, (140, 170, 255, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    layer.alpha_composite(glow)
    rrect(d, (x0, y0, x1, y1), 46, (18, 18, 22, 255), outline=(70, 72, 82, 255), w=4)
    sx0, sy0, sx1, sy1 = x0 + 18, y0 + 50, x1 - 18, y1 - 40
    scr = Image.new("RGBA", ((sx1 - sx0) * K, (sy1 - sy0) * K), (226, 232, 248, 255))
    sd = ImageDraw.Draw(scr)
    # scroll offset
    n = sum(1 for tk in ticks if t >= tk)
    frac = 0.0
    for tk in ticks:
        if tk <= t < tk + 0.28:
            frac = smooth(prog(t, tk, tk + 0.28)) - 1
    off = (n + frac) * 330
    for i, kind in enumerate(posts):
        py = 30 + i * 330 - off
        if py > sy1 - sy0 or py < -330:
            continue
        sd.rounded_rectangle([14 * K, py * K, (sx1 - sx0 - 14) * K, (py + 300) * K], 18 * K, fill=(250, 251, 255, 255),
                             outline=(200, 206, 224, 255), width=2 * K)
        sd.ellipse([26 * K, (py + 12) * K, 52 * K, (py + 38) * K], fill=(150, 160, 190, 255))
        sd.rectangle([60 * K, (py + 20) * K, 160 * K, (py + 30) * K], fill=(190, 196, 214, 255))
        post_art(sd, kind, (sx1 - sx0) / 2, py + 165)
        for hx in (30, 60):
            sd.ellipse([hx * K, (py + 268) * K, (hx + 16) * K, (py + 284) * K], fill=(230, 70, 90, 255))
    layer.alpha_composite(scr, (sx0 * K, sy0 * K))
    rrect(d, (cx - 50, y0 + 18, cx + 50, y0 + 32), 7, (40, 42, 50, 255))


def post_art(sd, kind, cx, cy):
    def E(x, y, rx, ry, fill):
        sd.ellipse([(cx + x - rx) * K, (cy + y - ry) * K, (cx + x + rx) * K, (cy + y + ry) * K], fill=fill)

    def Pp(pts, fill):
        sd.polygon([((cx + x) * K, (cy + y) * K) for x, y in pts], fill=fill)
    if kind == "yacht":
        sd.rectangle([(cx - 140) * K, (cy + 30) * K, (cx + 140) * K, (cy + 110) * K], fill=(90, 160, 220, 255))
        E(70, -60, 34, 34, (255, 200, 90, 255))
        Pp([(-110, 30), (110, 30), (80, 60), (-90, 60)], (250, 250, 252, 255))
        Pp([(-60, 30), (40, 30), (20, 0), (-50, 0)], (230, 232, 240, 255))
        Pp([(-30, 0), (10, 0), (0, -20), (-24, -20)], (60, 80, 120, 255))
    elif kind == "car":
        sd.rectangle([(cx - 140) * K, (cy + 50) * K, (cx + 140) * K, (cy + 110) * K], fill=(70, 74, 86, 255))
        Pp([(-110, 40), (110, 40), (100, 10), (40, 0), (10, -26), (-60, -26), (-100, 6)], (220, 40, 50, 255))
        for x in (-60, 60):
            E(x, 44, 20, 20, (30, 30, 34, 255))
    elif kind == "beach":
        sd.rectangle([(cx - 140) * K, (cy - 110) * K, (cx + 140) * K, (cy + 10) * K], fill=(120, 190, 240, 255))
        sd.rectangle([(cx - 140) * K, (cy + 10) * K, (cx + 140) * K, (cy + 110) * K], fill=(240, 214, 150, 255))
        Pp([(30, 10), (40, -90), (50, 10)], (110, 80, 50, 255))
        for a in range(5):
            ang = -2.6 + a * 0.5
            Pp([(40, -90), (40 + 70 * math.cos(ang), -90 + 40 * math.sin(ang) + 20), (40 + 60 * math.cos(ang + 0.2),
                                                                                         -80 + 40 * math.sin(ang))],
               (60, 150, 80, 255))
    elif kind == "party":
        sd.rectangle([(cx - 140) * K, (cy - 110) * K, (cx + 140) * K, (cy + 110) * K], fill=(60, 40, 90, 255))
        rng = np.random.default_rng(4)
        for _ in range(40):
            E(rng.uniform(-130, 130), rng.uniform(-100, 100), 5, 5,
              [(255, 200, 60, 255), (255, 90, 160, 255), (90, 200, 255, 255)][int(rng.integers(3))])
    elif kind == "ring":
        sd.rectangle([(cx - 140) * K, (cy - 110) * K, (cx + 140) * K, (cy + 110) * K], fill=(250, 226, 230, 255))
        sd.ellipse([(cx - 50) * K, (cy - 20) * K, (cx + 50) * K, (cy + 80) * K], outline=(230, 180, 60, 255), width=14 * K)
        Pp([(-24, -20), (24, -20), (36, -44), (0, -70), (-36, -44)], (190, 230, 255, 255))
    elif kind == "house":
        sd.rectangle([(cx - 140) * K, (cy - 110) * K, (cx + 140) * K, (cy + 110) * K], fill=(170, 210, 250, 255))
        sd.rectangle([(cx - 140) * K, (cy + 70) * K, (cx + 140) * K, (cy + 110) * K], fill=(90, 170, 90, 255))
        sd.rectangle([(cx - 80) * K, (cy - 10) * K, (cx + 80) * K, (cy + 80) * K], fill=(250, 246, 236, 255))
        Pp([(-100, -10), (100, -10), (0, -90)], (170, 60, 50, 255))
        sd.rectangle([(cx - 15) * K, (cy + 30) * K, (cx + 15) * K, (cy + 80) * K], fill=(110, 70, 40, 255))
    elif kind == "promo":
        sd.rectangle([(cx - 140) * K, (cy - 110) * K, (cx + 140) * K, (cy + 110) * K], fill=(236, 240, 248, 255))
        for j, hgt in enumerate((30, 50, 80, 130)):
            sd.rectangle([(cx - 100 + j * 50) * K, (cy + 90 - hgt) * K, (cx - 70 + j * 50) * K, (cy + 90) * K],
                         fill=(60, 170, 100, 255))
        Pp([(-110, 60), (70, -70), (60, -50), (90, -80), (100, -40), (80, -60), (-100, 70)], (40, 140, 80, 255))
    elif kind == "stroller":
        sd.rectangle([(cx - 140) * K, (cy - 110) * K, (cx + 140) * K, (cy + 110) * K], fill=(250, 236, 214, 255))
        sd.pieslice([(cx - 70) * K, (cy - 70) * K, (cx + 70) * K, (cy + 70) * K], 180, 360, fill=(120, 170, 220, 255))
        sd.rectangle([(cx - 70) * K, (cy) * K, (cx + 70) * K, (cy + 30) * K], fill=(120, 170, 220, 255))
        for x in (-45, 45):
            E(x, 55, 20, 20, (60, 60, 70, 255))
        E(0, -10, 16, 16, (255, 220, 200, 255))


def bike(d, cx, t, col, pedal_ph, spin):
    wy = FLOOR - 95
    wl, wr = cx - 125, cx + 125
    for wx in (wl, wr):
        ell(d, wx, wy, 95, 95, None, outline=(24, 24, 28, 255), w=13)
        ell(d, wx, wy, 86, 86, None, outline=(70, 72, 80, 255), w=3)
        for j in range(8):
            a = spin + j * math.pi / 4
            line(d, [(wx, wy), (wx + 84 * math.cos(a), wy + 84 * math.sin(a))], (120, 124, 134, 255), 2)
        ell(d, wx, wy, 8, 8, (150, 154, 164, 255))
    crank = (cx - 10, wy)
    seat = (cx - 55, FLOOR - 250)
    head_t = (cx + 85, FLOOR - 255)
    c4 = col + (255,)
    line(d, [(wl, wy), crank, seat, (wl, wy)], c4, 13)
    line(d, [crank, head_t, (wr, wy)], c4, 13)
    line(d, [seat, (head_t[0] - 10, head_t[1] + 4)], c4, 13)
    line(d, [(seat[0] - 8, seat[1] - 6), (seat[0] + 40, seat[1] - 8)], (26, 26, 30, 255), 12)
    line(d, [head_t, (head_t[0] + 8, head_t[1] - 30), (head_t[0] + 50, head_t[1] - 36)], (40, 40, 46, 255), 9)
    # highlight stripe on the frame
    hl = tuple(min(255, c + 40) for c in col) + (255,)
    line(d, [(crank[0] + 6, crank[1] - 8), (head_t[0] - 4, head_t[1] + 8)], hl, 3)
    pa = (crank[0] + 34 * math.cos(pedal_ph), crank[1] + 34 * math.sin(pedal_ph))
    pb = (crank[0] - 34 * math.cos(pedal_ph), crank[1] - 34 * math.sin(pedal_ph))
    line(d, [pa, pb], (40, 40, 46, 255), 7)
    return {"seat": seat, "bar": (head_t[0] + 50, head_t[1] - 36), "pa": pa, "pb": pb, "crank": crank}


def rider_pts(b, s, droop=0.0):
    hip = (b["seat"][0] + 4, b["seat"][1] - 16)
    neck = (hip[0] + 62 * s + 10 * droop, hip[1] - 92 * s + 18 * droop)
    head = (neck[0] + 22 * s + 14 * droop, neck[1] - 36 * s + 30 * droop)
    l1, l2 = 60 * s, 62 * s
    kl = ik(hip, b["pa"], l1, l2, -1)
    kr = ik(hip, b["pb"], l1, l2, -1)
    hand = b["bar"]
    el = ik(neck, hand, 44 * s, 44 * s, 1)
    return {"head": head, "neck": neck, "hip": hip, "el": el, "hl": hand, "er": el, "hr": hand, "kl": kl,
            "fl": b["pa"], "kr": kr, "fr": b["pb"]}


def sports_car(d, layer, cx, t, moving):
    gy = FLOOR
    beam = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(beam)
    poly(bd, [(cx - 200, gy - 70), (cx - 560, gy - 150), (cx - 560, gy + 20)], (255, 246, 220, 60))
    layer.alpha_composite(beam.filter(ImageFilter.GaussianBlur(14)))
    body = [(-215, -30), (220, -30), (226, -62), (150, -84), (70, -132), (-60, -136), (-150, -92), (-222, -80)]
    poly(d, [(cx - x, gy + y) for x, y in body], (226, 228, 236, 255), outline=INK + (255,), w=3)
    poly(d, [(cx - x, gy + y) for x, y in [(130, -86), (62, -126), (-50, -128), (-118, -90)]], (40, 46, 62, 255))
    line(d, [(cx - 200, gy - 56), (cx + 200, gy - 56)], (255, 255, 255, 255), 3)
    ell(d, cx + 46, gy - 104, 17, 17, (190, 192, 200, 255))          # the friend at the wheel
    ell(d, cx - 214, gy - 60, 12, 8, (255, 244, 200, 255))
    ell(d, cx + 214, gy - 62, 8, 6, (220, 40, 40, 255))
    for wx in (-130, 140):
        ell(d, cx - wx, gy - 4, 40, 40, (18, 18, 22, 255))
        ell(d, cx - wx, gy - 4, 22, 22, (170, 174, 186, 255))
        for j in range(5):
            a = -t * 20 * moving + j * 1.256
            line(d, [(cx - wx, gy - 4), (cx - wx + 20 * math.cos(a), gy - 4 + 20 * math.sin(a))], (90, 94, 104, 255), 4)


def dumbbell(d, hand, s, ang=0.0):
    hx, hy = hand
    c, sn = math.cos(ang), math.sin(ang)
    a = (hx - 26 * s * c, hy - 26 * s * sn)
    b = (hx + 26 * s * c, hy + 26 * s * sn)
    line(d, [a, b], (90, 92, 100, 255), 7 * s)
    for p in (a, b):
        ell(d, p[0], p[1], 13 * s, 13 * s, (50, 52, 60, 255), outline=(120, 124, 134, 255), w=2)


def barbell(d, center, s):
    cx, cy = center
    line(d, [(cx - 230, cy), (cx + 230, cy)], (150, 154, 164, 255), 8)
    for sgn in (-1, 1):
        for j, (r, off) in enumerate(((78, 170), (66, 196), (54, 218))):
            rrect(d, (cx + sgn * off - 12, cy - r, cx + sgn * off + 12, cy + r), 6, (32, 32, 38, 255),
                  outline=(90, 94, 104, 255), w=2)


def medal(d, cx, cy, r=26, rot=0.0):
    ell(d, cx, cy, r, r, GOLD + (255,), outline=(150, 110, 30, 255), w=3)
    ell(d, cx - r * 0.3, cy - r * 0.3, r * 0.35, r * 0.25, (255, 236, 160, 255))
    f = font(PW.FD + "InterDisplay-Bold.otf", int(r * 0.8 * K))
    s = "5K"
    tw = f.getlength(s)
    d.text((cx * K - tw / 2, (cy - r * 0.45) * K), s, font=f, fill=(140, 96, 20, 255))


def trophy_card(layer, cx, cy, a):
    """the marathon winner his phone shows, floating big and soft behind him"""
    card = Image.new("RGBA", (380 * K, 480 * K), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([0, 0, 380 * K - 1, 480 * K - 1], 26 * K, fill=(40, 46, 70, 200),
                         outline=(150, 170, 230, 220), width=3 * K)
    rng = np.random.default_rng(9)
    for _ in range(50):
        x, y = rng.uniform(20, 360), rng.uniform(20, 300)
        c = [(255, 200, 60), (255, 90, 160), (90, 200, 255), (255, 255, 255)][int(rng.integers(4))]
        cd.rectangle([x * K, y * K, (x + 8) * K, (y + 5) * K], fill=c + (230,))
    tmp = Image.new("RGBA", card.size, (0, 0, 0, 0))
    pts = place(CHEER, (190, 330), 1, 0.95)
    figure(tmp, pts, 0.95, light=(0, -1))
    card.alpha_composite(tmp)
    td = ImageDraw.Draw(card)
    hx, hy = pts["hl"]
    td.polygon([((hx - 30) * K, (hy - 80) * K), ((hx + 30) * K, (hy - 80) * K), ((hx + 16) * K, (hy - 20) * K),
                ((hx - 16) * K, (hy - 20) * K)], fill=GOLD + (255,))
    td.rectangle([(hx - 8) * K, (hy - 20) * K, (hx + 8) * K, (hy + 4) * K], fill=GOLD + (255,))
    td.rectangle([40 * K, 420 * K, 340 * K, 450 * K], fill=(255, 255, 255, 60))
    f = font(PW.FD + "InterDisplay-Bold.otf", 30 * K)
    s = "MARATHON WINNER"
    td.text((190 * K - f.getlength(s) / 2, 418 * K), s, font=f, fill=(255, 255, 255, 230))
    card.putalpha(card.split()[3].point(lambda v: int(v * a)))
    layer.alpha_composite(card, (int((cx - 190) * K), int((cy - 240) * K)))


def shoes(d, hand):
    hx, hy = hand
    for j, dx in enumerate((-10, 12)):
        poly(d, [(hx + dx - 14, hy + 30), (hx + dx + 16, hy + 30), (hx + dx + 22, hy + 70), (hx + dx - 18, hy + 70)],
             (96, 70, 50, 255), outline=INK + (255,), w=2)
        line(d, [(hx + dx - 6, hy + 52), (hx + dx + 8, hy + 60)], (40, 30, 22, 255), 3)      # a tear
        line(d, [(hx, hy), (hx + dx, hy + 30)], (180, 180, 180, 255), 2)


def observer(layer, focus, light_on, t):
    """the barefoot man in the dark: blurred and dark until the flip"""
    s = 0.86
    hip = (130, FLOOR - 70 - 113 * s)
    pose = dict(STAND, head=(10, -148), el=(14, -66), hl=(26, -30), er=(-12, -60), hr=(-10, -14))
    pts = place(pose, hip, 1, s)
    col = tuple(int(lerp(c * 0.36, c, light_on)) for c in BODY)
    figure(layer, pts, s, light=(0.3, -0.95), body=col, blur=lerp(9, 0, focus), alpha=lerp(0.85, 1, focus))
    d = ImageDraw.Draw(layer)
    if focus > 0.4:
        shoes(d, pts["hr"])


# ---------------------------------------------------------------- captions
def caption(img, lines, t):
    """lines: [(t_in, text)], small spaced serif caps"""
    d = ImageDraw.Draw(img)
    f = font(SERIF, 40)
    for i, (t0, s) in enumerate(lines):
        if t < t0:
            continue
        a = smooth(prog(t, t0, t0 + 0.35))
        y = 300 + i * 62 + 10 * (1 - a)
        PW.spaced(d, W / 2, y, s, f, (236, 236, 240, int(255 * a)), 6)


# ---------------------------------------------------------------- scenes (st = seconds into the scene)
def s0(stage, d, st, T):
    ticks = [0.35, 0.95, 1.55, 2.15]
    giant_phone(d, stage, st, ["yacht", "car", "beach", "party", "yacht"], ticks)
    n = sum(1 for tk in ticks if st >= tk)
    k = 0.0
    for tk in ticks:
        if tk <= st < tk + 0.3:
            k = smooth(prog(st, tk, tk + 0.3))
    s = 1.3 * (0.8 ** (n - 1 + k)) if n else 1.3
    pts = place(LOOK_UP, stand_hip(250, s), 1, s)
    figure(stage, pts, s, light=(0.8, -0.6), scarf=True)
    return [(-1.0, "WHEN YOU COMPARE YOURSELF")], ((650, 0.6),), (0.0, 0.0)


BIKE_X = 400


def s1(stage, d, st, T, flip=False):
    drained = smooth(prog(st, 1.8, 2.4))
    col = tuple(int(lerp(a, b, drained)) for a, b in zip(ORANGE, DULL))
    pedal = st < 2.1
    ph = (st if pedal else 2.1) * 6.0
    b = bike(d, BIKE_X, st, col, ph, -ph * 1.6)
    droop = smooth(prog(st, 1.9, 2.4))
    pts = rider_pts(b, 1.2, droop)
    figure(stage, pts, 1.2, light=(-0.5, -0.85), scarf=True, back=-1)
    if st >= 0.9:
        u = smooth(prog(st, 0.9, 1.5))
        sports_car(d, stage, lerp(1400, 840, u), T, 1 - u)
    return [(0.3, "YOU WERE HAPPY."), (1.85, "UNTIL YOU LOOKED.")], ((BIKE_X, 1.0),), (0.0, 0.0)


def s2(stage, d, st, T):
    # background rack silhouettes are in the bg layer (drawn by the caller)
    s = 1.2
    hip = stand_hip(330, s)
    if st < 1.9:
        c = 0.5 - 0.5 * math.cos(st * 2 * math.pi / 0.95)
        hand = (lerp(14, 40, c), lerp(-12, -100, c))
        el = (12, -58)
        pose = dict(PROUD, er=el, hr=hand, el=(-10, -58), hl=(-14, -12))
        pts = place(pose, hip, 1, s)
        figure(stage, pts, s, light=(-0.5, -0.85), scarf=True)
        dumbbell(d, pts["hr"], s * 1.2)
    else:
        k = smooth(prog(st, 2.0, 2.6))
        pose = lerp_pose(dict(PROUD, er=(12, -58), hr=(14, -12)), dict(SAD, er=(-22, -54), hr=(-36, -8)), k)
        pts = place(pose, hip, 1, s)
        figure(stage, pts, s, light=(-0.5, -0.85), scarf=True)
        dumbbell(d, pts["hr"], s * 1.2, 0.4 * k)
    # the big lifter
    s2_ = 1.5
    hip2 = stand_hip(760, s2_)
    lift = smooth(prog(st, 1.2, 1.8))
    bar_y = lerp(-112, -196, lift)
    pose2 = dict(STAND, head=(0, -150), el=(-46, lerp(-80, -150, lift)), hl=(-60, bar_y), er=(46, lerp(-80, -150, lift)),
                 hr=(60, bar_y), kl=(-26, 52), fl=(-40, 113), kr=(26, 52), fr=(40, 113))
    pts2 = place(pose2, hip2, 1, s2_)
    figure(stage, pts2, s2_, light=(0.5, -0.85))
    barbell(d, ((pts2["hl"][0] + pts2["hr"][0]) / 2, pts2["hl"][1]), s2_)
    return [(0.3, "SAME EFFORT."), (2.2, "LESS PRIDE.")], ((330, 1.0), (760, 0.7)), (0.0, 0.0)


def s3(stage, d, st, T):
    ticks = [0.4, 1.1, 1.8, 2.5]
    giant_phone(d, stage, st, ["ring", "house", "promo", "stroller", "ring"], ticks)
    n = sum(1 for tk in ticks if st >= tk)
    k = 0.0
    for tk in ticks:
        if tk <= st < tk + 0.3:
            k = smooth(prog(st, tk, tk + 0.3))
    s = 1.1 * (0.68 ** (n + k))
    pts = place(LOOK_UP, stand_hip(250, s), 1, s)
    figure(stage, pts, s, light=(0.8, -0.6), scarf=True)
    return [(0.25, "EVERYONE SEEMS AHEAD.")], ((650, 0.6),), (0.0, 0.0)


def s4(stage, d, st, T):
    s = 1.3
    hip = stand_hip(470, s)
    raise_ = smooth(prog(st, 0.7, 1.0))
    drop_t = 2.15
    if st < 0.7:
        pose = lerp_pose(PROUD, dict(CHEER, el=(-34, -120), hl=(-30, -170)), math.sin(math.pi * st / 0.7) * 0.6)
    elif st < 1.8:
        pose = dict(PROUD, er=(24, -96), hr=(44, -132))
    elif st < drop_t:
        k = smooth(prog(st, 1.8, drop_t))
        pose = lerp_pose(dict(SAD, er=(24, -96), hr=(44, -132)), dict(SAD, el=(-10, -96), hl=(4, -134), er=(26, -70),
                                                                         hr=(40, -30)), k)
    else:
        pose = SAD
    pts = place(pose, hip, 1, s)
    # the winner card behind him
    if 0.8 <= st < 2.6:
        a = smooth(prog(st, 0.8, 1.2)) * (1 - smooth(prog(st, 2.2, 2.6)))
        trophy_card(stage, 800, 820, a)
    figure(stage, pts, s, light=(-0.4, -0.9), scarf=True)
    if 0.8 <= st < 1.9:
        hx, hy = pts["hr"]
        rrect(d, (hx - 12, hy - 20, hx + 12, hy + 20), 4, (18, 18, 24, 255))
        rrect(d, (hx - 9, hy - 16, hx + 9, hy + 16), 3, (170, 200, 255, 255))
    # the medal: on his chest, then pulled off over his head and dropped
    nx, ny = pts["neck"]
    if st < drop_t:
        if st < 1.8:
            mx, my = nx + 6, ny + 60 * s
            line(d, [(nx - 16, ny), (mx, my - 20)], (200, 40, 50, 255), 6)
            line(d, [(nx + 16, ny), (mx, my - 20)], (200, 40, 50, 255), 6)
        else:
            mx, my = pts["hl"][0], pts["hl"][1] + 40
            line(d, [pts["hl"], (mx, my - 20)], (200, 40, 50, 255), 5)
        medal(d, mx, my, 26)
    else:
        u = st - drop_t
        x0, y0 = pts["hl"][0] + 10, pts["hl"][1] + 40
        y = y0 + 900 * u * u
        x = x0 + 60 * u
        if y > FLOOR - 26:
            # bounce
            tb = math.sqrt((FLOOR - 26 - y0) / 900)
            v = 900 * 2 * tb * 0.35
            u2 = u - tb
            y = FLOOR - 26 - max(0.0, v * u2 - 450 * u2 * u2)
            x = x0 + 60 * u
        medal(d, x, y, 26)
    dim = smooth(prog(st, 2.5, 2.95))
    return [(drop_t - 0.1, "YOU FORGOT YOUR OWN WIN.")], ((470, 1.0 - 0.8 * dim),), (0.0, 0.0)


def s5(stage, d, st, T):
    color_back = smooth(prog(st, 1.9, 2.7))
    col = tuple(int(lerp(a, b, color_back)) for a, b in zip(DULL, ORANGE))
    bike(d, BIKE_X, st, col, 0.6, 0.0)
    s = 1.2
    turn = st >= 1.45
    pose = SAD if not turn else lerp_pose(SAD, dict(STAND, head=(8, -150)), smooth(prog(st, 1.45, 1.8)))
    pts = place(pose, stand_hip(640, s), -1 if turn else 1, s)
    figure(stage, pts, s, light=(-0.5, -0.85), scarf=True)
    light2 = smooth(prog(st, 0.8, 1.3))
    return [(1.4, "SOMEONE IS LOOKING AT YOU"), (2.0, "THE SAME WAY.")], ((BIKE_X + 120, 1.0), (130, 0.9 * light2)), \
        (smooth(prog(st, 0.6, 1.3)), light2)


SCENES = [s0, s1, s2, s3, s4, s5]


def gym_bg(layer):
    d = ImageDraw.Draw(layer)
    for x in (120, 560, 980):
        rrect(d, (x - 70, FLOOR - 420, x + 70, FLOOR - 60), 6, None, outline=(60, 62, 72, 255), w=10)
        for y in range(FLOOR - 360, FLOOR - 80, 70):
            line(d, [(x - 70, y), (x + 70, y)], (60, 62, 72, 255), 6)
            ell(d, x - 50, y - 18, 16, 16, (50, 52, 60, 255))
            ell(d, x + 50, y - 18, 16, 16, (50, 52, 60, 255))


def frame(t):
    sc, st = scene_of(t)
    stage = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(stage)
    back = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    if sc == 2:
        gym_bg(back)
    if sc in (1, 5):
        if sc == 1:
            observer(back, 0.0, 0.0, t)
    res = SCENES[sc](stage, d, st, t)
    lines, spots, extra = res
    base = stage_bg(tuple((float(x), round(float(s_), 2)) for x, s_ in spots)).copy()
    if sc == 5:
        focus, light2 = extra
        if focus < 0.5:
            observer(back, focus, light2, t)
            base.alpha_composite(back.filter(ImageFilter.GaussianBlur(4 * K * (1 - focus))) if False else back)
        else:
            observer(stage, focus, light2, t)
    else:
        if sc == 2:
            back = back.filter(ImageFilter.GaussianBlur(7 * K))
        base.alpha_composite(back)
    dd = ImageDraw.Draw(base)
    dust(dd, t, spots, seed=sc + 1)
    # wet-floor reflection of the stage
    top = stage.crop((0, 0, W * K, FLOOR * K))
    refl = top.transpose(Image.FLIP_TOP_BOTTOM).crop((0, 0, W * K, (H - FLOOR) * K))
    refl = refl.resize((W * K // 4, (H - FLOOR) * K // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
    refl = refl.resize((W * K, (H - FLOOR) * K), Image.BILINEAR)
    fade = np.linspace(0.32, 0.0, (H - FLOOR) * K, dtype=np.float32)[:, None]
    ra = (np.asarray(refl.split()[3], np.float32) * fade).astype(np.uint8)
    refl.putalpha(Image.fromarray(ra))
    base.alpha_composite(refl, (0, FLOOR * K))
    # soft glow of the lit things, then the stage itself
    g = stage.resize((W * K // 8, H * K // 8), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6))
    ga = g.split()[3].point(lambda v: int(v * 0.35))
    gl = Image.new("RGBA", g.size, (200, 210, 235, 0))
    gl.putalpha(ga)
    base.alpha_composite(gl.resize(stage.size, Image.BILINEAR))
    base.alpha_composite(stage)
    # camera: a slow push in every scene, a small punch on each cut; S5 pulls back
    dur = SC[sc + 1] - SC[sc]
    if sc == 5:
        z = lerp(1.35, 1.0, smooth(prog(st, 0.0, 1.3)))
        cx_f = lerp(640, W / 2, smooth(prog(st, 0.0, 1.3)))
        dx = z * (W / 2 - cx_f)
        dy = z * (H / 2 - 1050) * (1 - smooth(prog(st, 0.0, 1.3)))
    else:
        z = 1.0 + 0.05 * st / dur + 0.06 * (1 - smooth(prog(st, 0, 0.3)))
        dx = dy = 0.0
    zb = 1.16                                    # everything a bit bigger on a phone
    z *= zb
    dx *= zb
    dy = dy * zb + z * (H / 2 - 1010)
    im = hq.camera(base, z, dx * K, dy * K).resize((W, H), Image.LANCZOS)
    caption(im, lines, st)
    return np.asarray(im.convert("RGB"))


def init_worker():
    pass


def render(i):
    return frame(i / FPS).tobytes()


# ---------------------------------------------------------------- music: an epic cinematic cue on GM instruments
BPM = 120
BEAT = 0.5


def score():
    import mido
    notes = []                  # (start, dur, ch, note, vel)
    prg = {0: 0, 1: 42, 2: 48, 3: 116, 4: 47, 5: 61, 6: 52, 7: 43, 8: 60, 10: 89}
    chords = [(50, 57, 62, 65), (46, 53, 58, 62), (53, 60, 65, 69), (48, 55, 60, 64)]   # Dm Bb F C
    end = DUR
    nb = int(end / BEAT)
    for b in range(nb):
        t0 = b * BEAT
        bar = b // 4
        ch = chords[bar % 4]
        sc, st = scene_of(t0 + 1e-4)
        inten = [0.45, 0.6, 0.7, 0.75, 0.85, 1.0][sc]
        # piano ostinato, 8ths
        pat = [ch[0] + 12, ch[2] + 12, ch[3] + 12, ch[2] + 12]
        for e in range(2):
            notes.append((t0 + e * BEAT / 2, BEAT / 2 * 0.9, 0, pat[(b * 2 + e) % 4], int(62 + 30 * inten)))
        # cellos 8ths from S1
        if sc >= 1:
            for e in range(2):
                notes.append((t0 + e * BEAT / 2, BEAT / 2 * 0.8, 1, ch[0] - 12, int(70 + 35 * inten)))
        # contrabass whole notes
        if b % 4 == 0:
            notes.append((t0, 4 * BEAT * 0.98, 7, ch[0] - 24, int(80 + 30 * inten)))
        # strings: sustained from S2, spiccato 16ths from S4
        if sc >= 2 and b % 4 == 0:
            for n in ch[1:]:
                notes.append((t0, 4 * BEAT * 0.98, 2, n, int(50 + 40 * inten)))
        if sc >= 4:
            for e in range(4):
                notes.append((t0 + e * BEAT / 4, BEAT / 4 * 0.5, 2, ch[[1, 2, 3, 2][e]] + 12, 85))
        # taiko groove from S1, busier as it builds
        if sc >= 1:
            if b % 2 == 0:
                notes.append((t0, 0.3, 3, 60, int(80 + 40 * inten)))
            if sc >= 3 and b % 4 == 3:
                notes.append((t0 + BEAT / 2, 0.2, 3, 60, 90))
                notes.append((t0 + 3 * BEAT / 4, 0.2, 3, 60, 100))
            if sc >= 4 and b % 2 == 1:
                notes.append((t0 + BEAT / 2, 0.2, 3, 60, 95))
        # pad underneath
        if b % 4 == 0:
            for n in ch[1:]:
                notes.append((t0, 4 * BEAT * 0.98, 10, n, 55))
        # the flip: brass + horns melody, choir
        if sc == 5 and b % 4 == 0:
            for n in ch:
                notes.append((t0, 4 * BEAT * 0.98, 6, n + 12, 95))
                notes.append((t0, 4 * BEAT * 0.95, 5, n, 100))
    # horn theme in S5
    theme = [(0, 1.0, 74), (1.0, 0.5, 72), (1.5, 0.5, 69), (2.0, 1.0, 77), (3.0, 0.5, 76)]
    for t_, du, n in theme:
        notes.append((SC[5] + 0.2 + t_, du * 0.95, 8, n, 110))
    # hits on every cut: taiko + timpani + low brass + cymbal; a build into the flip
    for cut in SC[:6]:
        notes.append((cut, 0.6, 3, 60, 127))
        notes.append((cut, 0.8, 4, 38, 120))
        for n in (38, 50):
            notes.append((cut, 0.7, 5, n, 115))
        notes.append((cut, 1.2, 9, 49, 110))
    for j in range(8):
        tt = SC[5] - 1.0 + j * 0.125
        notes.append((tt, 0.1, 3, 60, 70 + 7 * j))
    notes.append((SC[5] - 1.5, 1.5, 9, 55, 90))
    # the last line: a big held chord
    for n in (38, 50, 57, 62, 65, 69):
        notes.append((SC[5] + 2.0, DUR - SC[5] - 2.0, 6 if n > 45 else 7, n, 110))
    mid = mido.MidiFile(ticks_per_beat=960)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))
    vol = {0: 96, 1: 100, 2: 92, 3: 120, 4: 110, 5: 96, 6: 92, 7: 105, 8: 108, 9: 100, 10: 70}
    for c_, p_ in prg.items():
        tr.append(mido.Message("program_change", channel=c_, program=p_, time=0))
    for c_, v in vol.items():
        tr.append(mido.Message("control_change", channel=c_, control=7, value=v, time=0))
        tr.append(mido.Message("control_change", channel=c_, control=91, value=80, time=0))
    ev = []
    for s_, du, c_, n, v in notes:
        ev.append((s_, 1, c_, n, v))
        ev.append((s_ + du, 0, c_, n, 0))
    ev.sort(key=lambda e: (e[0], e[1]))
    now = 0
    for s_, on, c_, n, v in ev:
        tk = int(round(max(0.0, s_) * 1920))
        tr.append(mido.Message("note_on" if on else "note_off", channel=c_, note=int(n), velocity=int(min(127, v)),
                               time=max(0, tk - now)))
        now = max(now, tk)
    tmp = tempfile.mkdtemp()
    mp, wp = os.path.join(tmp, "s.mid"), os.path.join(tmp, "s.wav")
    mid.save(mp)
    subprocess.run(["fluidsynth", "-ni", "-g", "0.6", "-r", str(SR), "-F", wp, SF2, mp], check=True, capture_output=True)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", wp, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True).stdout
    m = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    n = int(DUR * SR)
    out = np.zeros((n, 2))
    out[:min(n, len(m))] = m[:n]
    out = np.tanh(out * 1.5) / np.tanh(1.5)
    out /= np.abs(out).max() + 1e-9
    return out * 0.55


def audio():
    n = int(DUR * SR)
    fx = np.zeros((n, 2))
    mus = score()
    # S0 / S3: scroll ticks and a falling "shrink" on each
    for base_t, ticks in ((SC[0], [0.35, 0.95, 1.55, 2.15]), (SC[3], [0.4, 1.1, 1.8, 2.5])):
        for tk in ticks:
            mix_in(fx, tone(2200, 0.03, (1,), a=0.0005, d=0.012), base_t + tk, 0.06)
            mix_in(fx, tone(180, 0.35, (1, 0.5), a=0.005, d=0.2, sweep=70), base_t + tk + 0.05, 0.08)
    # S1: chain ticking, the car, the colour draining
    for j in range(14):
        mix_in(fx, noise(0.02, 10 + j, lo=2000, hi=7000) * env(int(0.02 * SR), 0.0005, 0.006), SC[1] + j * 0.15, 0.04, -0.3)
    car = noise(0.8, 11, lo=60, hi=600) * np.sin(np.linspace(0, np.pi, int(0.8 * SR)))
    mix_in(fx, car, SC[1] + 0.9, 0.12, 0.5)
    mix_in(fx, noise(0.6, 12, lo=300, hi=3000) * np.linspace(1, 0, int(0.6 * SR)) ** 2, SC[1] + 1.8, 0.06)
    # S2: dumbbell, barbell clank
    for j in range(2):
        mix_in(fx, tone(900, 0.1, (1, 2.7), a=0.001, d=0.05), SC[2] + 0.47 + j * 0.95, 0.03, -0.3)
    mix_in(fx, tone(320, 0.6, (1, 2.4, 3.9), a=0.001, d=0.25) + 0.4 * noise(0.6, 13, lo=500, hi=6000) *
           env(int(0.6 * SR), 0.001, 0.08), SC[2] + 1.8, 0.14, 0.4)
    # S4: medal clink and bounces, the light switching off
    t_drop = SC[4] + 2.15
    for j, (dt, g) in enumerate(((0.33, 0.12), (0.52, 0.06), (0.62, 0.03))):
        mix_in(fx, tone(2600, 0.25, (1, 2.76, 5.4), a=0.0005, d=0.1), t_drop + dt, g)
    mix_in(fx, tone(90, 0.2, (1, 0.5), a=0.001, d=0.06) + 0.3 * noise(0.2, 14, lo=200, hi=2000) *
           env(int(0.2 * SR), 0.001, 0.03), SC[4] + 2.5, 0.14)
    # cut whooshes
    for cut in SC[1:6]:
        mix_in(fx, noise(0.35, int(cut * 10), lo=400, hi=6000) * np.linspace(0, 1, int(0.35 * SR)) ** 2, cut - 0.35, 0.06)
    x = mus + fx
    m = int(0.2 * SR)
    k = np.linspace(0, 1, m)[:, None]
    x[-m:] = x[-m:] * (1 - k) + x[:m] * k
    x /= max(1.0, np.abs(x).max() / 0.9)
    return x


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "compare.mp4"
    only = os.environ.get("ONLY_FRAMES")
    if only:
        os.makedirs(out, exist_ok=True)
        for s in only.split(","):
            t = float(s)
            Image.fromarray(np.frombuffer(render(int(round(t * FPS))), np.uint8).reshape(H, W, 3)).save(
                os.path.join(out, f"f{t:05.2f}.png"))
        return
    wav = out + ".wav"
    write_wav(wav, audio())
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                          "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100",
                          "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                         stdin=subprocess.PIPE)
    with Pool(os.cpu_count(), initializer=init_worker) as pool:
        for i, b in enumerate(pool.imap(render, range(NF), chunksize=2)):
            p.stdin.write(b)
            if i % 120 == 0:
                print(f"{i}/{NF}", flush=True)
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print(out)


if __name__ == "__main__":
    main()
