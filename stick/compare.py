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
DUR = 21.5
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

SC = [0.0, 3.0, 6.5, 10.0, 13.5, 17.0, DUR]        # scene starts


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


def sports_car(d, layer, cx, t, moving, flip=False):
    """white sports car; flip=True faces right"""
    f = -1 if flip else 1
    gy = FLOOR
    beam = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(beam)
    poly(bd, [(cx - f * 200, gy - 70), (cx - f * 560, gy - 150), (cx - f * 560, gy + 20)], (255, 246, 220, 60))
    layer.alpha_composite(beam.filter(ImageFilter.GaussianBlur(14)))
    body = [(-215, -30), (220, -30), (226, -62), (150, -84), (70, -132), (-60, -136), (-150, -92), (-222, -80)]
    poly(d, [(cx - f * x, gy + y) for x, y in body], (226, 228, 236, 255), outline=INK + (255,), w=3)
    poly(d, [(cx - f * x, gy + y) for x, y in [(130, -86), (62, -126), (-50, -128), (-118, -90)]], (40, 46, 62, 255))
    line(d, [(cx - 200, gy - 56), (cx + 200, gy - 56)], (255, 255, 255, 255), 3)
    ell(d, cx + f * 46, gy - 104, 17, 17, (190, 192, 200, 255))
    ell(d, cx - f * 214, gy - 60, 12, 8, (255, 244, 200, 255))
    ell(d, cx + f * 214, gy - 62, 8, 6, (220, 40, 40, 255))
    if moving > 0.05:
        for j in range(5):
            y = gy - 40 - j * 18
            line(d, [(cx + f * 230, y), (cx + f * (330 + 60 * (j % 2)), y)], (220, 228, 255, int(180 * moving)), 3)
    for wx in (-130, 140):
        ell(d, cx - f * wx, gy - 4, 40, 40, (18, 18, 22, 255))
        ell(d, cx - f * wx, gy - 4, 22, 22, (170, 174, 186, 255))
        for j in range(5):
            a = -f * t * 20 * moving + j * 1.256
            line(d, [(cx - f * wx, gy - 4), (cx - f * wx + 20 * math.cos(a), gy - 4 + 20 * math.sin(a))],
                 (90, 94, 104, 255), 4)


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
# every scene returns: captions, spotlights, camera (focus x, focus y, zoom), extra
def run_pose(ph, amp, lean=0.24):
    p = {}
    L = lean * (0.4 + 0.6 * amp)
    p["neck"] = (104 * math.sin(L), -104 * math.cos(L))
    p["head"] = (p["neck"][0] + 42 * math.sin(L * 0.8), p["neck"][1] - 42 * math.cos(L * 0.8))
    for side, off in (("l", 0.0), ("r", math.pi)):
        q = ph + off
        thigh = 0.15 + 0.1 * amp + (0.3 + 0.55 * amp) * math.sin(q)
        flex = 0.32 + (0.5 + 1.6 * amp) * max(0.0, math.cos(q + 0.9)) ** 2
        kx, ky = 56 * math.sin(thigh), 56 * math.cos(thigh)
        sh = thigh - flex
        p["k" + side] = (kx, ky)
        p["f" + side] = (kx + 57 * math.sin(sh), ky + 57 * math.cos(sh))
        a = -(0.3 + 0.85 * amp) * math.sin(q) + L * 0.5
        nx, ny = p["neck"]
        ex, ey = nx + 40 * math.sin(a), ny + 40 * math.cos(a)
        fa = a + 1.35 + 0.25 * amp
        p["e" + side] = (ex, ey)
        p["h" + side] = (ex + 36 * math.sin(fa), ey + 36 * math.cos(fa))
    return p


def grounded(pose, x, s, feet=FLOOR):
    low = max(pose["fl"][1], pose["fr"][1])
    return (x, feet - low * s)


LUSH = (58, 168, 74)
DRY = (168, 140, 76)
LEAN = dict(STAND, head=(18, -150), neck=(8, -108), el=(34, -86), hl=(66, -96), er=(30, -90), hr=(62, -100))


def turf(d, layer, x0, x1, health, sc=1.0, seed=0, glow=0.0, lush_extra=0.0, fl_gap=60):
    """a raised patch of lawn: a bumpy green mass with a lit top edge, tufts, flowers and a bush.
    health 1 = green and in bloom, 0 = dry and wilted. coordinates on screen, sc = size scale"""
    rng = np.random.default_rng(seed)
    col = tuple(int(lerp(b, a, health)) for a, b in zip(LUSH, DRY))
    if lush_extra > 0:
        col = tuple(int(min(255, c * (1 + 0.25 * lush_extra))) for c in col)
    top = FLOOR - 58 * sc
    if glow > 0:
        gl = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        ell(ImageDraw.Draw(gl), (x0 + x1) / 2, top, (x1 - x0) * 0.6, 70 * sc, (120, 255, 140, int(60 * glow)))
        layer.alpha_composite(gl.filter(ImageFilter.GaussianBlur(30 * sc * K)))
    xs = np.linspace(x0, x1, 40)
    edge = [(x, top - 6 * sc * math.sin(x * 0.05 + seed) - 4 * sc * math.sin(x * 0.13 + seed * 2)) for x in xs]
    body = edge + [(x1, FLOOR + 16 * sc), (x0, FLOOR + 16 * sc)]
    dark = tuple(int(c * 0.55) for c in col)
    poly(d, body, dark + (255,), outline=INK + (255,), w=2 * sc)
    inner = [(x, y + 6 * sc) for x, y in edge] + [(x1 - 6 * sc, FLOOR + 4 * sc), (x0 + 6 * sc, FLOOR + 4 * sc)]
    poly(d, inner, col + (255,))
    lite = tuple(min(255, int(c * 1.3 + 20)) for c in col)
    line(d, [(x, y + 4 * sc) for x, y in edge], lite + (255,), 5 * sc)
    # tufts along the top
    for j in range(int((x1 - x0) / (9 * sc))):
        x = x0 + 6 * sc + j * 9 * sc + rng.uniform(-2, 2) * sc
        y = top - 6 * sc * math.sin(x * 0.05 + seed) - 4 * sc * math.sin(x * 0.13 + seed * 2) + 2 * sc
        hgt = rng.uniform(12, 26) * sc * (0.55 + 0.45 * health) * (1 + 0.5 * lush_extra)
        lean = rng.uniform(-4, 4) * sc + (1 - health) * 6 * sc
        poly(d, [(x - 3 * sc, y), (x + 3 * sc, y), (x + lean, y - hgt)], lite + (255,))
    # flowers
    for j in range(int((x1 - x0) / (fl_gap * sc)) + 1):
        x = x0 + 30 * sc + j * fl_gap * sc + rng.uniform(-10, 10) * sc
        if x > x1 - 60 * sc:
            continue
        y = top - 4 * sc
        stem_h = 40 * sc * (0.4 + 0.6 * health) * (1 + 0.3 * lush_extra)
        bend = (1 - health) * 14 * sc
        tip = (x + bend, y - stem_h + (1 - health) * 10 * sc)
        line(d, [(x, y), tip], (40, 110, 50, 255), 3 * sc)
        fc = [(240, 90, 120), (255, 210, 70), (250, 250, 255), (180, 120, 240)][int(rng.integers(4))]
        fcol = tuple(int(lerp(b, a, health)) for a, b in zip(fc, (120, 100, 70)))
        r = 10 * sc * (0.5 + 0.5 * health)
        for k2 in range(5):
            a = k2 * 1.256
            ell(d, tip[0] + r * 0.9 * math.cos(a), tip[1] + r * 0.9 * math.sin(a), r * 0.6, r * 0.6, fcol + (255,))
        ell(d, tip[0], tip[1], r * 0.45, r * 0.45, (250, 200, 60, 255))
    # a bush at the far end
    bx = x1 - 50 * sc
    for dx, dy, r in ((-30, -14, 40), (24, -18, 46), (0, -48, 44)):
        ell(d, bx + dx * sc, top + dy * sc, r * sc * (0.75 + 0.25 * health), r * sc * (0.75 + 0.25 * health),
            tuple(int(c * 0.8) for c in col) + (255,), outline=INK + (255,), w=2 * sc)
    ell(d, bx - 8 * sc, top - 58 * sc, 16 * sc, 10 * sc, lite + (255,))


def fence_s(d, x, sc=1.0):
    """a picket fence between two gardens, seen at an angle"""
    for j in range(6):
        px = x + (j * 12 - 30) * sc
        py = FLOOR + (20 - j * 14) * sc
        poly(d, [(px - 7 * sc, py), (px + 7 * sc, py), (px + 7 * sc, py - 125 * sc), (px, py - 137 * sc),
                 (px - 7 * sc, py - 125 * sc)], (196, 188, 176, 255), outline=INK + (255,), w=2 * sc)
    line(d, [(x - 36 * sc, FLOOR - 40 * sc), (x + 36 * sc, FLOOR - 110 * sc)], (150, 142, 130, 255), 7 * sc)
    line(d, [(x - 36 * sc, FLOOR - 0 * sc), (x + 36 * sc, FLOOR - 70 * sc)], (150, 142, 130, 255), 7 * sc)


def sprinkler(d, x, T, sc=1.0):
    y = FLOOR - 30 * sc
    rrect(d, (x - 7 * sc, y - 16 * sc, x + 7 * sc, y + 2 * sc), 3, (60, 62, 70, 255))
    ang = -math.pi / 2 + 0.9 * math.sin(T * 2.2)
    for j in range(30):
        u = ((T * 1.6 + j / 30) % 1.0)
        a = ang + (j % 5 - 2) * 0.07
        px = x + math.cos(a) * 240 * u * sc
        py = y - 16 * sc + math.sin(a) * 240 * u * sc + 300 * u * u * sc
        ell(d, px, py, 3 * sc, 3.5 * sc, (190, 225, 255, int(235 * (1 - u))))


def watering_can(d, hand, T, tilt, pour):
    hx, hy = hand
    poly(d, [(hx - 10, hy - 10), (hx + 34, hy - 10), (hx + 30, hy + 26), (hx - 6, hy + 26)], (70, 140, 200, 255),
         outline=INK + (255,), w=2)
    line(d, [(hx + 32, hy + 6), (hx + 70, hy - 12 + 30 * tilt)], (70, 140, 200, 255), 6)
    if pour:
        for j in range(12):
            u = ((T * 2.5 + j / 12) % 1.0)
            ell(d, hx + 72 + 30 * u, hy - 8 + 30 * tilt + 200 * u * u + 40 * u, 3, 4, (170, 210, 255, int(220 * (1 - u))))


def s0(stage, d, st, T):
    """the grass is greener: both gardens in view from frame 0; his dries up while he stares over the fence"""
    s = 1.2
    look = smooth(prog(st, 0.7, 1.1))
    dry = smooth(prog(st, 1.3, 2.3))
    turf(d, stage, 580, 1080, 1.0, 1.0, seed=2, glow=1.0, lush_extra=1.0, fl_gap=34)
    sprinkler(d, 800, T)
    turf(d, stage, 20, 520, 0.85 * (1 - dry), 1.0, seed=1, fl_gap=90)
    fence_s(d, 550)
    fence_s(d, 0)
    # the hidden detail: someone peeking over the left fence at HIS garden (dark, only on a second look)
    pk = place(LEAN, stand_hip(-50, 1.0), 1, 1.0)
    figure(stage, pk, 1.0, light=(0.6, -0.8), body=(70, 72, 80), alpha=0.9, blur=2.5)
    hip = stand_hip(300, s)
    pose = dict(STAND, er=(30, -80), hr=(66, -64), head=(lerp(0, 18, look), -150))
    if dry > 0.5:
        pose = lerp_pose(pose, dict(SAD, er=(20, -60), hr=(36, -24)), smooth(prog(st, 2.1, 2.7)))
    pts = place(pose, hip, 1, s)
    figure(stage, pts, s, light=(0.5, -0.85), scarf=True)
    tilt = 0.5 * (1 - smooth(prog(st, 1.0, 1.4)))
    watering_can(d, pts["hr"], T, tilt, st < 1.0)
    fx = lerp(560, 330, smooth(prog(st, 1.5, 2.6)))
    z = lerp(1.06, 1.22, smooth(prog(st, 1.5, 2.6)))
    return [(-1.0, "WHEN YOU COMPARE YOURSELF")], ((300, 0.9), (820, 1.0)), (fx, 1060, z), None



BIKE_X = 430
STOP1 = 2.55                       # the bike stops (scene time in S1)


def bike_scroll(st):
    """distance the world has moved in S1 (px)"""
    v0 = 560.0
    if st < 1.8:
        return v0 * st
    u = min(st, STOP1) - 1.8
    dur = STOP1 - 1.8
    return v0 * 1.8 + v0 * (u - u * u / (2 * dur))


def street(d, c, seed=5):
    """lamps, dashes and puddles of the S1/S5 street, scrolled by c"""
    for k in range(int((c - 200) // 520), int((c + W + 200) // 520) + 1):
        x = k * 520 + 140 - c
        line(d, [(x, FLOOR - 40), (x, FLOOR - 560)], (40, 42, 50, 255), 8)
        line(d, [(x, FLOOR - 560), (x + 60, FLOOR - 580)], (40, 42, 50, 255), 6)
        ell(d, x + 62, FLOOR - 574, 16, 8, (255, 226, 160, 255))
    for k in range(int((c - 100) // 160), int((c + W + 100) // 160) + 1):
        x = k * 160 - c
        line(d, [(x, FLOOR + 36), (x + 70, FLOOR + 36)], (70, 72, 84, 255), 5)


def s1(stage, d, st, T):
    c = bike_scroll(st)
    v = (bike_scroll(st + 0.01) - bike_scroll(st - 0.01)) / 0.02
    street(d, c)
    drained = smooth(prog(st, 1.75, 2.4))
    col = tuple(int(lerp(a, b, drained)) for a, b in zip(ORANGE, DULL))
    ph = c / 60.0
    b = bike(d, BIKE_X, st, col, ph, -c / 95.0)
    droop = smooth(prog(st, 2.0, 2.6))
    pts = rider_pts(b, 1.2, droop)
    figure(stage, pts, 1.2, light=(-0.5, -0.85), scarf=True, back=-1)
    # the white car comes from behind and passes him, splashing through a puddle
    if 0.7 <= st < 2.2:
        u = prog(st, 0.7, 2.2)
        cx = lerp(-400, 1600, u)
        sports_car(d, stage, cx, T, 1.0, flip=True)
        if 1.25 <= st < 1.9:
            k = prog(st, 1.25, 1.9)
            rng = np.random.default_rng(3)
            for j in range(40):
                vx, vy = rng.uniform(-260, 120), rng.uniform(-520, -200)
                x = BIKE_X + 120 + vx * k
                y = FLOOR - 10 + vy * k + 900 * k * k
                ell(d, x, y, 4, 5, (170, 200, 240, int(230 * (1 - k))))
    return [(0.3, "YOU WERE HAPPY."), (1.85, "UNTIL YOU LOOKED.")], ((BIKE_X + 60, 1.0),), \
        (lerp(BIKE_X + 120, BIKE_X + 40, smooth(prog(st, 2.3, 3.5))), 1050, lerp(1.0, 1.12, smooth(prog(st, 2.3, 3.5)))), \
        ("shake", [1.3])


def s2(stage, d, st, T):
    s = 1.2
    hip = stand_hip(330, s)
    jit = 6 * math.exp(-(st - 2.05) * 9) * math.sin(st * 90) if st > 2.05 else 0.0
    if st < 1.95:
        c = 0.5 - 0.5 * math.cos(st * 2 * math.pi / 0.95)
        hand = (lerp(14, 40, c), lerp(-12, -100, c))
        pose = dict(PROUD, er=(12, -58), hr=hand, el=(-10, -58), hl=(-14, -12))
        pts = place(pose, hip, 1, s)
        figure(stage, pts, s, light=(-0.5, -0.85), scarf=True)
        dumbbell(d, pts["hr"], s * 1.2)
    else:
        k = smooth(prog(st, 2.3, 2.9))
        pose = lerp_pose(dict(PROUD, er=(12, -58), hr=(14, -12), head=(10, -150)),
                         dict(SAD, er=(-22, -54), hr=(-36, -8)), k)
        pts = place(pose, hip, 1, s)
        figure(stage, pts, s, light=(-0.5, -0.85), scarf=True)
        hx, hy = pts["hr"]
        dumbbell(d, (hx + jit, hy), s * 1.2, 0.4 * k + 0.05 * jit)
    s2_ = 1.5
    hip2 = stand_hip(760, s2_)
    lift = smooth(prog(st, 0.7, 1.3))
    drop = st >= 1.85
    if not drop:
        bar_y = lerp(-112, -196, lift)
        pose2 = dict(STAND, el=(-46, lerp(-80, -150, lift)), hl=(-60, bar_y), er=(46, lerp(-80, -150, lift)),
                     hr=(60, bar_y), kl=(-26, 52), fl=(-40, 113), kr=(26, 52), fr=(40, 113))
        pts2 = place(pose2, hip2, 1, s2_)
        bar_c = ((pts2["hl"][0] + pts2["hr"][0]) / 2, pts2["hl"][1])
    else:
        u = st - 1.85
        up = dict(STAND, el=(-46, -150), hl=(-60, -196), er=(46, -150), hr=(60, -196), kl=(-26, 52), fl=(-40, 113),
                  kr=(26, 52), fr=(40, 113))
        down = dict(STAND, head=(4, -150), el=(-34, -64), hl=(-40, -16), er=(34, -64), hr=(40, -16), kl=(-26, 52),
                    fl=(-40, 113), kr=(26, 52), fr=(40, 113))
        pose2 = lerp_pose(up, down, smooth(prog(st, 1.9, 2.3)))
        pts2 = place(pose2, hip2, 1, s2_)
        y0 = hip2[1] - 196 * s2_
        bar_c = (hip2[0], min(FLOOR - 78, y0 + 1600 * u * u))
        if bar_c[1] >= FLOOR - 78:
            bounce = max(0.0, 30 * math.sin((u - 0.2) * 22) * math.exp(-(u - 0.2) * 8))
            bar_c = (bar_c[0], FLOOR - 78 - bounce)
    figure(stage, pts2, s2_, light=(0.5, -0.85))
    barbell(d, bar_c, s2_)
    if st >= 2.05:
        u = st - 2.05
        rng = np.random.default_rng(6)
        for j in range(26):
            vx = rng.uniform(-300, 300)
            ell(d, 760 + vx * u, FLOOR - 4 - abs(vx) * 0.3 * u + 200 * u * u, 6 + 30 * u, 3 + 8 * u,
                (150, 150, 160, int(150 * max(0, 1 - u * 1.4))))
    orbit = smooth(prog(st, 0.0, 3.5))
    return [(0.3, "SAME EFFORT."), (2.4, "LESS PRIDE.")], ((330, 1.0), (760, 0.75)), \
        (lerp(700, 420, orbit), 1020, lerp(1.28, 1.12, orbit)), ("shake", [2.05])


def office_bg(layer):
    d = ImageDraw.Draw(layer)
    for x in (80, 300, 780, 1000):
        rrect(d, (x - 90, 640, x + 90, 1000), 8, (22, 24, 32, 255), outline=(60, 64, 80, 255), w=4)
        for y in range(660, 990, 26):
            line(d, [(x - 80, y), (x + 80, y)], (40, 44, 58, 255), 3)
    for x in (300, 780):
        rrect(d, (x - 150, FLOOR - 120, x + 150, FLOOR - 104), 4, (50, 52, 62, 255))
        line(d, [(x - 130, FLOOR - 104), (x - 130, FLOOR)], (50, 52, 62, 255), 8)
        line(d, [(x + 130, FLOOR - 104), (x + 130, FLOOR)], (50, 52, 62, 255), 8)


def envelope(d, x, y, glow=0.0, open_=0.0, scale=1.0):
    w, h = 46 * scale, 30 * scale
    if glow > 0:
        for r, a in ((90, 40), (60, 60), (40, 90)):
            ell(d, x, y - 10, r * scale, r * scale * 0.8, (255, 210, 90, int(a * glow)))
    rrect(d, (x - w, y - h, x + w, y + h), 3, (240, 238, 230, 255), outline=INK + (255,), w=2)
    poly(d, [(x - w, y - h), (x + w, y - h), (x, y - h + lerp(26, -30, open_) * scale)], (220, 216, 206, 255),
         outline=INK + (255,), w=2)


def bill(d, x, y, ang, a=255, scale=1.0):
    c, s_ = math.cos(ang), math.sin(ang)
    pts = [(-30, -14), (30, -14), (30, 14), (-30, 14)]
    poly(d, [(x + (px * c - py * s_) * scale, y + (px * s_ + py * c) * scale) for px, py in pts], (110, 190, 110, a),
         outline=(30, 80, 40, a), w=2)
    ell(d, x, y, 7 * scale, 7 * scale, (60, 140, 70, a))


def s3(stage, d, st, T):
    """payday: his envelope makes him smile - until the colleague's bursts with money"""
    s = 1.2
    # the boss walks in and hands the envelopes
    if st < 1.0:
        u = smooth(prog(st, 0.0, 0.8))
        bx = lerp(1250, 520, u)
        bpose = AJ.walk(st * 9, STAND) if u < 0.99 else dict(STAND, er=(40, -80), hr=(80, -86), el=(-40, -80),
                                                             hl=(-80, -86))
        bpts = place(bpose, stand_hip(bx, 1.25), -1, 1.25)
        figure(stage, bpts, 1.25, light=(0.2, -1), body=(150, 154, 168))
        line(d, [bpts["neck"], ((bpts["neck"][0] + bpts["hip"][0]) / 2, (bpts["neck"][1] + bpts["hip"][1]) / 2)],
             (40, 60, 120, 255), 8)
    elif st < 1.6:
        u = smooth(prog(st, 1.0, 1.6))
        bpts = place(AJ.walk(st * 9, STAND), stand_hip(lerp(520, 1300, u), 1.25), 1, 1.25)
        figure(stage, bpts, 1.25, light=(0.2, -1), body=(150, 154, 168))
    # hero
    opened = smooth(prog(st, 1.0, 1.3))
    happy = smooth(prog(st, 1.3, 1.6)) * (1 - smooth(prog(st, 2.1, 2.5)))
    hp = dict(STAND, er=(26, -84), hr=(50, -92), el=(-26, -84), hl=(-46, -92))
    hp = lerp_pose(hp, dict(CHEER, er=(30, -120), hr=(46, -150)), happy * 0.5)
    if st > 2.1:
        hp = lerp_pose(hp, dict(SAD, er=(20, -60), hr=(40, -40)), smooth(prog(st, 2.1, 2.6)))
    hpts = place(hp, stand_hip(330, s), 1, s)
    figure(stage, hpts, s, light=(-0.5, -0.85), scarf=True)
    if st >= 0.8:
        hx, hy = hpts["hr"]
        envelope(d, hx, hy - 4, 0.0, opened, 0.9)
        if st >= 1.2:
            k = smooth(prog(st, 1.2, 1.4))
            bill(d, hx, hy - 30 - 20 * k, 0.1, scale=0.8)
    # colleague
    cp = dict(STAND, er=(26, -84), hr=(50, -92), el=(-26, -84), hl=(-46, -92))
    burst = smooth(prog(st, 1.85, 2.1))
    cp = lerp_pose(cp, CHEER, smooth(prog(st, 2.0, 2.4)))
    cpts = place(cp, stand_hip(760, s), -1, s)
    figure(stage, cpts, s, light=(0.5, -0.85))
    if st >= 0.8:
        ex, ey = (cpts["hr"][0] + cpts["hl"][0]) / 2, min(cpts["hr"][1], cpts["hl"][1]) if st >= 2.0 else cpts["hr"][1]
        if st < 2.0:
            envelope(d, cpts["hr"][0], cpts["hr"][1] - 4, burst, burst, 1.0)
    if st >= 1.9:
        u = st - 1.9
        rng = np.random.default_rng(12)
        for j in range(60):
            vx, vy = rng.uniform(-420, 420), rng.uniform(-900, -350)
            g = 520
            x = 760 + vx * u
            y = 1000 + vy * u + g * u * u
            if y > FLOOR - 6:
                y = FLOOR - 6
            bill(d, x, y, rng.uniform(0, 6) + u * rng.uniform(-6, 6), scale=0.9)
        if u < 0.5:
            glow = Image.new("RGBA", stage.size, (0, 0, 0, 0))
            ell(ImageDraw.Draw(glow), 760, 1000, 320, 260, (255, 210, 100, int(120 * (1 - u * 2))))
            stage.alpha_composite(glow.filter(ImageFilter.GaussianBlur(50)))
    # camera: on him, a whip to the colleague, then both
    if st < 1.85:
        fx, z = 360, 1.3
    elif st < 2.15:
        k = smooth(prog(st, 1.85, 2.1))
        fx, z = lerp(360, 760, k), 1.3
    else:
        k = smooth(prog(st, 2.3, 3.2))
        fx, z = lerp(760, 540, k), lerp(1.3, 1.12, k)
    return [(0.4, "IT WAS ENOUGH."), (2.3, "UNTIL IT WASN'T.")], ((330, 1.0), (760, 0.6 + 0.4 * burst)), \
        (fx, 1040, z), ("whip", [1.85])


def s4(stage, d, st, T):
    """he runs, breaks the 5K tape, gets his medal; the giant screen shows a marathon winner; he drops it"""
    s = 1.25
    run_end = 1.35
    tape_x = 760
    if st < run_end:
        x = lerp(80, 560, st / run_end)
        ph = st * 15
        pose = run_pose(ph, 0.9)
        hip = grounded(pose, x, s)
    else:
        u = smooth(prog(st, run_end, run_end + 0.4))
        x = 560 + 50 * u
        pose = lerp_pose(run_pose(run_end * 15, 0.9), STAND, u)
        hip = stand_hip(x, s)
    cheer = smooth(prog(st, 1.6, 1.9)) * (1 - smooth(prog(st, 2.35, 2.6)))
    if st >= 1.6:
        pose = lerp_pose(pose, CHEER, cheer)
    if st >= 2.45:
        k = smooth(prog(st, 2.45, 2.75))
        pose = lerp_pose(pose, dict(SAD, el=(-10, -96), hl=(4, -134)), k)
    drop_t = 2.85
    if st >= drop_t:
        pose = SAD
    pts = place(pose, hip, 1, s)
    # the finish arch "5K" he runs through (world scroll: the arch comes towards him)
    arch_x = tape_x - 420 * smooth(prog(st, 0.0, run_end)) + 220
    line(d, [(arch_x - 120, FLOOR), (arch_x - 120, FLOOR - 430)], (70, 74, 90, 255), 10)
    line(d, [(arch_x + 120, FLOOR), (arch_x + 120, FLOOR - 430)], (70, 74, 90, 255), 10)
    rrect(d, (arch_x - 150, FLOOR - 480, arch_x + 150, FLOOR - 420), 8, (40, 60, 110, 255), outline=(150, 170, 230, 255),
          w=3)
    f = font(PW.FD + "InterDisplay-Bold.otf", 40 * K)
    d.text(((arch_x - f.getlength("5K FINISH") / K / 2) * K, (FLOOR - 474) * K), "5K FINISH", font=f,
           fill=(240, 244, 255, 255))
    if st < run_end - 0.15:
        line(d, [(arch_x - 120, FLOOR - 200), (arch_x + 120, FLOOR - 200)], (220, 50, 60, 255), 6)
    elif st < run_end + 0.5:
        k = prog(st, run_end - 0.15, run_end + 0.5)
        for sgn in (-1, 1):
            line(d, [(arch_x + sgn * 120, FLOOR - 200), (arch_x + sgn * 120 - sgn * 60 * (1 - k),
                                                         FLOOR - 200 + 140 * k)], (220, 50, 60, 255), 6)
    # the giant screen
    if st >= 2.0:
        a = smooth(prog(st, 2.0, 2.35)) * (1 - smooth(prog(st, 3.1, 3.5)))
        trophy_card(stage, 840, 760, a)
    figure(stage, pts, s, light=(-0.4, -0.9), scarf=True)
    nx, ny = pts["neck"]
    if 1.45 <= st < drop_t:
        if st < 2.55:
            mx, my = nx + 6, ny + 60 * s
            line(d, [(nx - 16, ny), (mx, my - 20)], (200, 40, 50, 255), 6)
            line(d, [(nx + 16, ny), (mx, my - 20)], (200, 40, 50, 255), 6)
            if st < 1.75:
                k = 1 - prog(st, 1.45, 1.75)
                ell(d, mx, my, 50 * k + 26, 50 * k + 26, (255, 240, 180, int(160 * k)))
        else:
            mx, my = pts["hl"][0], pts["hl"][1] + 40
            line(d, [pts["hl"], (mx, my - 20)], (200, 40, 50, 255), 5)
        medal(d, mx, my, 26)
    elif st >= drop_t:
        u = st - drop_t
        x0, y0 = pts["hl"][0] + 10, pts["hl"][1] + 40
        tb = math.sqrt(max(1.0, FLOOR - 26 - y0) / 900)
        if u < tb:
            y = y0 + 900 * u * u
        else:
            u2 = u - tb
            v = 900 * 2 * tb * 0.35
            y = FLOOR - 26 - max(0.0, v * u2 - 450 * u2 * u2)
        medal(d, x0 + 60 * u, y, 26)
    dim = smooth(prog(st, 3.05, 3.45))
    fx = lerp(lerp(260, 560, smooth(st / run_end)), 640, smooth(prog(st, 1.9, 2.6)))
    return [(drop_t - 0.15, "YOU FORGOT YOUR OWN WIN.")], ((560, 1.0 - 0.8 * dim),), \
        (fx, 1040, lerp(1.25, 1.12, smooth(prog(st, 1.9, 2.6)))), None


def s5(stage, d, st, T):
    """back at the fence; the camera pulls far back: a row of gardens, everyone staring over a fence at the next one"""
    pull = smooth(prog(st, 0.7, 2.6))
    ws = lerp(1.0, 0.52, pull)
    pc = lerp(540, 820, pull)
    green_back = smooth(prog(st, 1.6, 2.6))

    def X(wx):
        return W / 2 + (wx - pc) * ws

    def Y(wy):
        return FLOOR + (wy - FLOOR) * ws
    gw = 560
    owners = []
    for i in range(-1, 5):
        gx0 = 20 + (i - 0) * gw
        health = 1.0 if i != 0 else lerp(0.0, 1.0, green_back)
        turf(d, stage, X(gx0), X(gx0 + 500), health, ws, seed=i + 1)
        fence_s(d, X(gx0 + 530), ws)
        owners.append((i, gx0))
    for i, gx0 in owners:
        if i == 0:
            continue
        ox = gx0 + 440
        pts = place(LEAN, (X(ox), Y(FLOOR - 113 * 1.15)), 1, 1.15 * ws)
        shade = [(150, 152, 162), (190, 192, 200), (170, 172, 182), (205, 206, 212), (160, 162, 172)][i % 5]
        figure(stage, pts, 1.15 * ws, light=(0.4, -0.9), body=shade)
    # the hero: by his fence, staring right; at the end he turns back to his own garden
    hx = 20 + 440
    turn = smooth(prog(st, 3.4, 3.8))
    pose = lerp_pose(dict(SAD, head=(18, -146)), LEAN, smooth(prog(st, 0.0, 0.5)))
    f = 1
    if turn > 0.5:
        pose = dict(STAND, head=(6, -152))
        f = -1
    pts = place(pose, (X(hx), Y(FLOOR - 113 * 1.2)), f, 1.2 * ws)
    figure(stage, pts, 1.2 * ws, light=(-0.5, -0.85), scarf=True)
    spots = [(540.0, 1.0 - 0.5 * pull)]
    for i in range(-1, 4):
        k = round(smooth(prog(st, 2.0 + 0.15 * (i + 1), 2.3 + 0.15 * (i + 1))) * 4) / 4
        if k > 0:
            spots.append((float(round(X(20 + i * gw + 360))), 0.8 * k))
    return [(2.3, "EVERYONE IS LOOKING"), (3.0, "AT SOMEONE ELSE'S GRASS.")], tuple(spots), (540, 1040, 1.0), None


SCENES = [s0, s1, s2, s3, s4, s5]
_BACK = [None]


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
    _BACK[0] = back
    if sc == 2:
        gym_bg(back)
    if sc == 3:
        office_bg(back)
    lines, spots, camf, extra = SCENES[sc](stage, d, st, t)
    base = stage_bg(tuple((float(round(x)), round(float(s_), 2)) for x, s_ in spots)).copy()
    if extra and extra[0] == "flip":
        focus, light2 = extra[1]
        observer(stage if focus >= 0.5 else back, focus, light2, t)
    if sc in (2, 3):
        back = back.filter(ImageFilter.GaussianBlur(6 * K))
    base.alpha_composite(back)
    dd = ImageDraw.Draw(base)
    dust(dd, t, spots, seed=sc + 1)
    top = stage.crop((0, 0, W * K, FLOOR * K))
    refl = top.transpose(Image.FLIP_TOP_BOTTOM).crop((0, 0, W * K, (H - FLOOR) * K))
    refl = refl.resize((W * K // 4, (H - FLOOR) * K // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
    refl = refl.resize((W * K, (H - FLOOR) * K), Image.BILINEAR)
    fade = np.linspace(0.32, 0.0, (H - FLOOR) * K, dtype=np.float32)[:, None]
    ra = (np.asarray(refl.split()[3], np.float32) * fade).astype(np.uint8)
    refl.putalpha(Image.fromarray(ra))
    base.alpha_composite(refl, (0, FLOOR * K))
    g = stage.resize((W * K // 8, H * K // 8), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6))
    ga = g.split()[3].point(lambda v: int(v * 0.35))
    gl = Image.new("RGBA", g.size, (200, 210, 235, 0))
    gl.putalpha(ga)
    base.alpha_composite(gl.resize(stage.size, Image.BILINEAR))
    base.alpha_composite(stage)
    # camera
    fx, fy, z = camf
    z *= 1.08
    dx = z * (W / 2 - fx)
    dy = z * (H / 2 - fy)
    if extra and extra[0] == "shake":
        for t0 in extra[1]:
            if t0 <= st < t0 + 0.4:
                k = 1 - (st - t0) / 0.4
                dx += 14 * k * math.sin(st * 85)
                dy += 9 * k * math.cos(st * 71)
    im = hq.camera(base, z, dx * K, dy * K).resize((W, H), Image.LANCZOS)
    # whip-in at every cut, and the in-scene whip
    whips = [0.0] + ([extra[1][0]] if extra and extra[0] == "whip" else [])
    for w0 in whips:
        if w0 <= st < w0 + 0.16 and not (sc == 0 and w0 == 0.0):
            k = 1 - prog(st, w0, w0 + 0.16)
            bl = im.resize((max(8, int(W / (1 + 40 * k))), H), Image.BILINEAR).resize((W, H), Image.BILINEAR)
            im = Image.blend(im, bl, min(1.0, k * 1.2))
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


def burst_noise(dur, seed, lo, hi, a=0.002, d=0.05):
    return noise(dur, seed, lo=lo, hi=hi)[:int(dur * SR)] * env(int(dur * SR), a, d)


def audio():
    n = int(DUR * SR)
    fx = np.zeros((n, 2))
    mus = score()
    # S0: watering, the sprinkler, the lawn drying
    w = noise(2.1, 1, lo=1500, hi=7000)[:int(2.1 * SR)] * 0.5
    mix_in(fx, w * np.minimum(1, np.linspace(0, 8, len(w))), SC[0], 0.03, -0.2)
    for j in range(16):
        mix_in(fx, burst_noise(0.03, 20 + j, 3000, 9000, 0.0005, 0.01), SC[0] + 0.1 + j * 0.17, 0.03, 0.5)
    mix_in(fx, noise(0.8, 2, lo=1500, hi=6000)[:int(0.8 * SR)] * (np.random.default_rng(1).random(int(0.8 * SR)) > 0.985),
           SC[0] + 1.5, 0.25)
    mix_in(fx, tone(160, 0.6, (1, 0.5), a=0.01, d=0.3, sweep=70), SC[0] + 1.6, 0.06)
    # S1: chain, the car passing, the splash, the brakes
    for j in range(16):
        mix_in(fx, burst_noise(0.02, 40 + j, 2000, 7000, 0.0005, 0.006), SC[1] + j * 0.15, 0.035, -0.3)
    pas = noise(1.4, 3, lo=60, hi=900)[:int(1.4 * SR)]
    pas *= np.exp(-((np.linspace(0, 1.4, len(pas)) - 0.75) / 0.25) ** 2)
    mix_in(fx, pas, SC[1] + 0.7, 0.3)
    mix_in(fx, burst_noise(0.5, 4, 300, 5000, 0.005, 0.15), SC[1] + 1.25, 0.14, 0.2)
    sq = tone(2400, 0.35, (1, 0.5), a=0.01, d=0.2, sweep=1900)
    mix_in(fx, sq, SC[1] + 2.2, 0.025, -0.2)
    # S2: curls, the barbell slammed on the floor
    for j in range(2):
        mix_in(fx, tone(900, 0.1, (1, 2.7), a=0.001, d=0.05), SC[2] + 0.47 + j * 0.95, 0.03, -0.3)
    mix_in(fx, tone(55, 0.8, (1, 0.6), a=0.001, d=0.35) + 0.5 * burst_noise(0.8, 5, 100, 4000, 0.001, 0.12) +
           0.4 * tone(320, 0.8, (1, 2.4, 3.9), a=0.001, d=0.2), SC[2] + 2.05, 0.4, 0.3)
    # S3: footsteps, the envelope, the money burst
    for j in range(5):
        mix_in(fx, tone(140, 0.07, (1, 0.5), a=0.002, d=0.025), SC[3] + j * 0.17, 0.05, 0.4)
    mix_in(fx, burst_noise(0.25, 6, 1500, 7000, 0.01, 0.08), SC[3] + 1.0, 0.07, -0.3)
    mix_in(fx, tone(1400, 0.25, (1, 0.4), a=0.002, d=0.12), SC[3] + 1.3, 0.04, -0.3)
    for j, f_ in enumerate((1568, 2093, 2637)):
        mix_in(fx, tone(f_, 0.5, (1, 0.3), a=0.001, d=0.25), SC[3] + 1.9 + j * 0.06, 0.06, 0.3)
    mix_in(fx, noise(1.0, 7, lo=1500, hi=7000)[:SR] * np.linspace(1, 0, SR) ** 2, SC[3] + 1.9, 0.08, 0.3)
    # S4: running feet, the tape, applause, the medal, the giant screen's roar, the medal falls, the light dies
    for j in range(10):
        mix_in(fx, tone(180, 0.06, (1, 0.5), a=0.001, d=0.02), SC[4] + j * 0.135, 0.05)
    mix_in(fx, tone(1200, 0.08, (1, 0.5), a=0.001, d=0.03, sweep=600), SC[4] + 1.2, 0.08)
    ap = noise(1.0, 8, lo=800, hi=6000)[:SR] * (np.random.default_rng(2).random(SR) > 0.97) * np.linspace(1, 0, SR)
    mix_in(fx, ap, SC[4] + 1.35, 0.35)
    mix_in(fx, tone(2600, 0.6, (1, 2.76), a=0.002, d=0.3), SC[4] + 1.45, 0.04)
    roar = noise(1.2, 9, lo=300, hi=3000)[:int(1.2 * SR)] * np.sin(np.linspace(0, np.pi, int(1.2 * SR)))
    mix_in(fx, roar, SC[4] + 2.0, 0.12, 0.3)
    t_drop = SC[4] + 2.85
    for dt, g in ((0.33, 0.12), (0.52, 0.06), (0.62, 0.03)):
        mix_in(fx, tone(2600, 0.25, (1, 2.76, 5.4), a=0.0005, d=0.1), t_drop + dt, g)
    mix_in(fx, tone(90, 0.2, (1, 0.5), a=0.001, d=0.06) + 0.3 * burst_noise(0.2, 10, 200, 2000, 0.001, 0.03),
           SC[4] + 3.05, 0.14)
    # whooshes into every cut
    for cut in SC[1:6]:
        mix_in(fx, noise(0.35, int(cut * 10), lo=400, hi=6000)[:int(0.35 * SR)] *
               np.linspace(0, 1, int(0.35 * SR)) ** 2, cut - 0.35, 0.07)
    mix_in(fx, noise(0.25, 11, lo=500, hi=6000)[:int(0.25 * SR)] * np.linspace(0, 1, int(0.25 * SR)) ** 2,
           SC[3] + 1.62, 0.06)
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
