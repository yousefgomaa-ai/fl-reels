#!/usr/bin/env python3
"""LIFE IN ONE FRAME #1 - GROWTH YOU CAN'T SEE.  ~15 s, 4 situations, one lesson.

1 (0.0-3.4)  the stone: hit after hit, a counter racing 1..99 - nothing. 100: it splits.
2 (3.4-6.6)  the seed: watering every day, nothing above ground - the camera drops below: roots everywhere.
3 (6.6-9.8)  the mirror: months of curls, the reflection never changes... then it does.
4 (9.8-13.4) the bamboo: YEAR 1, 2, 3, 4 - a tiny shoot. YEAR 5: it shoots past the top of the screen.
13.4         GROWTH YOU CAN'T SEE.

    python3 stick/ep1.py --stills [t ...]
    python3 stick/ep1.py stick/frame/ep1.mp4            # with music
    python3 stick/ep1.py stick/frame/ep1-sfx.mp4 --sfx  # sound effects only (add a YouTube sound on upload)
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perfect_wave as PW  # noqa
import hq  # noqa
from compare import ell, line, rrect, poly, figure, place, ik, FLOOR, K, W, H  # noqa
from perfect_wave import clamp, env, font, lerp, lerp_pose, mix_in, noise, prog, smooth, tone, write_wav  # noqa
from money_chars import hero, S, GOLD, RED  # noqa
from money import text, compose, put, track  # noqa

FPS, SR = 30, 44100
DUR = 15.0
NF = int(round(DUR * FPS))
STAND = PW.STAND
ORIG = {"stone": 3.4, "seed": 3.2, "ice": 3.2, "mirror": 3.2, "views": 3.2, "bamboo": 3.6}
ORDER = [("stone", 2.3), ("seed", 2.1), ("ice", 2.1), ("mirror", 2.1), ("views", 2.1), ("bamboo", 2.7)]
SC = []
_t = 0.0
for _k, _d in ORDER:
    SC.append((_t, _t + _d, _k))
    _t += _d
SC.append((_t, DUR, "end"))
T_END = _t
SOIL = (58, 40, 28)
GREEN = (90, 190, 90)


def scene_at(t):
    """(kind, u on the scene's own clock, real length)"""
    for a, b, k in SC:
        if a <= t < b:
            return k, (t - a) * (ORIG.get(k, 1.0) / (b - a) if k in ORIG else 1.0), b - a
    return "end", t - SC[-1][0], 1.6


def start(kind):
    return [a for a, b, k in SC if k == kind][0]


def at(kind, u):
    """real time of a moment u on that scene's own clock"""
    a, b = [(a, b) for a, b, k in SC if k == kind][0]
    return a + u * (b - a) / ORIG[kind]


def counter(im, s, col=(246, 246, 250), y=170, size=150, k=1.0):
    f = font("InterDisplay-Bold.otf", int(size * max(0.4, k)))
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    PW.spaced(ImageDraw.Draw(g), W / 2, y, s, f, col + (150,), 2)
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(18)))
    PW.spaced(ImageDraw.Draw(im), W / 2, y, s, f, col + (255,), 2)


def set_arm(p, side, tgt, sgn=1):
    p = dict(p)
    p["h" + side] = tgt
    p["e" + side] = ik(p["neck"], tgt, 42 * S, 40 * S, sgn)
    return p


# ---------------------------------------------------------------- 1. the stone
HITS_AT = 2.55      # the 100th hit


def stone(st, d, u):
    n_swings = 9
    ph = (u / (HITS_AT / n_swings)) % 1.0 if u < HITS_AT + 0.05 else 1.0
    lift = math.cos(math.pi * ph) if u < HITS_AT else -1.0     # 1 = raised, -1 = down on the stone
    hx = 410
    p = place(dict(STAND, kl=(-20, 56), fl=(-30, 113), kr=(20, 56), fr=(30, 113)), (hx, FLOOR - 113 * S), 1, S)
    ang = lerp(-0.2, 2.2, (lift + 1) / 2)          # hammer angle from horizontal-forward to over the head
    grip = (p["neck"][0] + 30 * math.cos(ang) * 0.6 + 20, p["neck"][1] - 60 * math.sin(ang) * 0.6 + 40)
    p = set_arm(set_arm(p, "r", grip, 1), "l", (grip[0] - 8, grip[1] + 10), 1)
    head = (grip[0] + 150 * math.cos(ang), grip[1] - 150 * math.sin(ang))
    hero(st, p, "plain", 1, "determined" if u < HITS_AT + 0.3 else "happy", u)
    split = smooth(prog(u, HITS_AT, HITS_AT + 0.4))
    cx, cy = 660, FLOOR - 110
    for side in (-1, 1):
        off = side * 60 * split
        rot = side * 0.25 * split
        pts = []
        for j in range(13):
            a = math.pi / 2 + side * (math.pi * j / 12)
            x, y = 130 * math.cos(a), 110 * math.sin(a)
            pts.append((x, y))
        pts = [(cx + off + x * math.cos(rot) - y * math.sin(rot), cy + x * math.sin(rot) + y * math.cos(rot)) for x, y in pts]
        poly(d, pts, (120, 120, 128, 255), outline=(60, 60, 66, 255), w=3)
    rng_s = np.random.default_rng(8)
    for j in range(40):    # texture
        a = rng_s.uniform(0, 2 * math.pi)
        r = rng_s.uniform(0, 0.85)
        xx = cx + 110 * r * math.cos(a)
        side = -1 if xx < cx else 1
        ell(d, xx + side * 60 * split, cy + 90 * r * math.sin(a), rng_s.uniform(3, 10), rng_s.uniform(2, 7),
            (96, 96, 104, 255) if j % 2 else (146, 146, 154, 255))
    ell(d, cx - 40 - 60 * split, cy - 50, 40, 18, (160, 160, 168, 255))
    if split <= 0:   # hairline cracks that never seem to matter
        for j in range(min(6, int(u * 2.5))):
            x0 = cx - 30 + 14 * j
            line(d, [(x0, cy - 70 + 10 * j), (x0 + 12, cy - 40 + 8 * j), (x0 + 4, cy - 10 + 6 * j)], (60, 60, 66, 255), 2)
    if split > 0:   # the crack + dust
        rng = np.random.default_rng(3)
        for j in range(16):
            r = 60 + 220 * split * rng.uniform(0.4, 1.0)
            a = rng.uniform(0, 2 * math.pi)
            ell(d, cx + r * math.cos(a), cy + 0.6 * r * math.sin(a), 14, 10, (170, 160, 150, int(170 * (1 - split))))
    line(d, [(grip[0], grip[1]), head], (140, 100, 60, 255), 7)
    c_, s_ = math.cos(ang), math.sin(ang)
    hp = [(-22, -26), (22, -26), (22, 26), (-22, 26)]
    poly(d, [(head[0] + x * c_ + y * s_, head[1] - x * s_ + y * c_) for x, y in hp], (80, 82, 90, 255), outline=(30, 30, 34, 255), w=2)
    return (1.8, 540, FLOOR - 160)


def stone_count(u):
    if u >= HITS_AT:
        return 100
    return max(1, min(99, int(round(1 + 98 * (u / HITS_AT) ** 1.6))))


# ---------------------------------------------------------------- 2. the seed
def roots(d, x, y, g, depth=0, ang=math.pi / 2, length=120, seed=1):
    if depth > 5 or g <= 0:
        return
    rng = np.random.default_rng(seed)
    L = length * clamp(g * 1.6 - depth * 0.15)
    if L <= 1:
        return
    x2, y2 = x + L * math.cos(ang), y + L * math.sin(ang)
    line(d, [(x, y), (x2, y2)], (230, 210, 170, 255), max(1.5, 7 - depth))
    for k in range(2 + (depth < 2)):
        roots(d, x2, y2, g, depth + 1, ang + rng.uniform(-0.8, 0.8), length * 0.72, seed * 7 + k + 1)


def seed(st, d, u):
    poly(d, [(0, FLOOR), (W, FLOOR), (W, H), (0, H)], SOIL + (255,))
    line(d, [(0, FLOOR), (W, FLOOR)], (90, 120, 70, 255), 5)
    sx = 620
    p = place(dict(STAND, head=(20, -146), er=(40, -100), hr=(80, -110)), (430, FLOOR - 113 * S), 1, S)
    hero(st, p, "determined", 1, "determined", u)
    hx, hy = p["hr"]
    rrect(d, (hx - 4, hy - 22, hx + 44, hy + 16), 8, (70, 110, 170, 255))
    line(d, [(hx + 44, hy - 6), (hx + 90, hy - 30)], (70, 110, 170, 255), 6)
    for j in range(8):   # water
        v = (u * 3 + j / 8) % 1
        ell(d, lerp(hx + 92, sx, v), lerp(hy - 30, FLOOR - 6, v) - 60 * v * (1 - v), 3, 5, (150, 200, 255, 230))
    ell(d, sx, FLOOR + 14, 9, 6, (140, 100, 60, 255))
    g = smooth(prog(u, 0.6, 3.0))
    roots(d, sx, FLOOR + 18, g, length=150)
    if u > 2.7:   # finally, a tiny sprout
        k = smooth(prog(u, 2.7, 3.1))
        line(d, [(sx, FLOOR), (sx, FLOOR - 26 * k)], GREEN + (255,), 4)
        ell(d, sx + 8, FLOOR - 26 * k, 8 * k, 4 * k, GREEN + (255,))
    cam_y = lerp(FLOOR - 160, FLOOR + 220, smooth(prog(u, 0.6, 1.4)))
    return (1.7, 560, cam_y)


# ---------------------------------------------------------------- 3. the mirror
def mirror(st, d, u):
    mx = 720
    rrect(d, (mx - 120, FLOOR - 430, mx + 120, FLOOR - 10), 8, (30, 34, 46, 255), outline=(180, 160, 110, 255), w=8)
    rep = abs(math.sin(u * 7))
    p = place(STAND, (430, FLOOR - 113 * S), 1, S)
    p = set_arm(p, "r", (p["neck"][0] + 34, p["neck"][1] + 90 - 80 * rep), 1)
    big = smooth(prog(u, 2.3, 2.7))
    hero(st, p, "tired" if u < 2.3 else "happy", 1, "tired" if u < 2.3 else "happy", u)
    hx_, hy_ = p["hr"]
    line(d, [(hx_ - 14, hy_), (hx_ + 14, hy_)], (180, 184, 194, 255), 4)
    for x in (hx_ - 16, hx_ + 16):
        rrect(d, (x - 5, hy_ - 10, x + 5, hy_ + 10), 2, (40, 42, 50, 255))
    # the reflection: same thin guy... until it isn't
    rl = Image.new("RGBA", st.size, (0, 0, 0, 0))
    q = place(STAND, (mx, FLOOR - 113 * S - 40), -1, S * 0.85)
    q = dict(q)
    tgt = (q["neck"][0] - 30, q["neck"][1] + 80 - 70 * rep)
    q["hr"] = tgt
    q["er"] = ik(q["neck"], tgt, 36, 34, -1)
    figure(rl, q, S * 0.85 * (1 + 0.35 * big), light=(0.4, -0.9))
    rd = ImageDraw.Draw(rl)
    if big > 0:   # broad chest
        nx, ny = q["neck"]
        poly(rd, [(nx - 34 * big, ny + 6), (nx + 34 * big, ny + 6), (nx + 14, ny + 70), (nx - 14, ny + 70)], (238, 238, 242, 255))
    poly(rd, [(q["neck"][0] - 16, q["neck"][1]), (q["neck"][0] + 16, q["neck"][1]), (q["neck"][0], q["neck"][1] + 10)], RED + (255,))
    a = np.asarray(rl.split()[3], np.float32) * 0.8
    rl.putalpha(Image.fromarray(a.astype(np.uint8)))
    st.alpha_composite(rl)
    return (1.6, 580, FLOOR - 210)


# ---------------------------------------------------------------- the ice cube
MELT = 2.4


def ice_temp(u):
    if u >= MELT:
        return 0
    return -10 + int(10 * (u / MELT) ** 0.9)


def ice(st, d, u):
    rrect(d, (440, FLOOR - 92, 840, FLOOR - 80), 3, (90, 70, 52, 255))
    for x in (460, 820):
        line(d, [(x, FLOOR - 80), (x, FLOOR)], (60, 46, 34, 255), 7)
    m = smooth(prog(u, MELT, MELT + 0.7))
    w = 150 * (1 - 0.85 * m)
    h = 130 * (1 - 0.9 * m)
    cx = 640
    if h > 4:
        rrect(d, (cx - w / 2, FLOOR - 92 - h, cx + w / 2, FLOOR - 92), 14, (190, 225, 250, 255), outline=(120, 170, 210, 255), w=3)
        line(d, [(cx - w / 2 + 16, FLOOR - 92 - h + 16), (cx - w / 2 + 40, FLOOR - 92 - h + 16)], (240, 250, 255, 255), 5)
    if m > 0:
        ell(d, cx, FLOOR - 92, 60 + 160 * m, 8 + 6 * m, (150, 200, 240, 220))
        for j in range(4):
            v = (u * 2 + j / 4) % 1
            ell(d, cx + 160 * m - 20 + 10 * j, FLOOR - 80 + 80 * v, 3, 5, (150, 200, 240, int(220 * (1 - v))))
    p = place(dict(STAND, head=(16, -146)), (330, FLOOR - 113 * S), 1, S)
    hero(st, p, "plain", 1, "tired" if u < MELT else "shocked" if u < MELT + 0.3 else "happy", u)
    # thermometer
    rrect(d, (900, FLOOR - 420, 930, FLOOR - 150), 14, (230, 230, 236, 255))
    lvl = (ice_temp(u) + 10) / 10
    rrect(d, (906, FLOOR - 170 - 230 * lvl, 924, FLOOR - 150), 9, (220, 60, 60, 255))
    ell(d, 915, FLOOR - 140, 26, 26, (220, 60, 60, 255))
    return (1.55, 620, FLOOR - 190)


# ---------------------------------------------------------------- the views
VIRAL = 2.4


def views_now(u):
    if u >= VIRAL:
        return int(1200000 * smooth(prog(u, VIRAL, VIRAL + 0.4)))
    rng = np.random.default_rng(int(u * 6))
    return int(rng.integers(6, 40))


def views(st, d, u):
    rrect(d, (520, FLOOR - 96, 860, FLOOR - 84), 3, (90, 70, 52, 255))
    for x in (540, 840):
        line(d, [(x, FLOOR - 84), (x, FLOOR)], (60, 46, 34, 255), 7)
    # the laptop, screen toward us
    rrect(d, (590, FLOOR - 290, 800, FLOOR - 140), 8, (30, 32, 40, 255), outline=(150, 154, 164, 255), w=3)
    poly(d, [(570, FLOOR - 140), (820, FLOOR - 140), (840, FLOOR - 96), (550, FLOOR - 96)], (150, 154, 164, 255))
    v = views_now(u)
    col = GOLD if u >= VIRAL else (200, 204, 214)
    PW.spaced(d, 695 * K, (FLOOR - 236) * K, f"{v:,}", font("InterDisplay-Bold.otf", (40 if v < 1000 else 34) * K), col + (255,), 1)
    PW.spaced(d, 695 * K, (FLOOR - 186) * K, "VIEWS", font("Inter-SemiBold.otf", 18 * K), (150, 154, 170, 255), 4)
    pose = dict(PW.SIT, head=(20, -146))
    p = place(pose, (470, FLOOR - 90), 1, S)
    p = set_arm(set_arm(p, "r", (548, FLOOR - 104 - 6 * abs(math.sin(u * 14))), 1), "l", (532, FLOOR - 104), 1)
    rrect(d, (430, FLOOR - 92, 510, FLOOR - 80), 3, (40, 40, 46, 255))
    line(d, [(470, FLOOR - 80), (470, FLOOR)], (40, 40, 46, 255), 6)
    hero(st, p, "plain", 1, "tired" if u < VIRAL else ("shocked" if u < VIRAL + 0.5 else "happy"), u)
    return (1.6, 600, FLOOR - 190)


def video_no(u):
    if u >= VIRAL:
        return 100
    return max(1, min(99, int(1 + 98 * (u / VIRAL) ** 1.3)))


# ---------------------------------------------------------------- 4. the bamboo
def bamboo(st, d, u):
    poly(d, [(0, FLOOR), (W, FLOOR), (W, H), (0, H)], SOIL + (255,))
    line(d, [(0, FLOOR), (W, FLOOR)], (90, 120, 70, 255), 5)
    bx = 760
    shoot = smooth(prog(u, 2.4, 3.3))
    hgt = 30 + 1900 * shoot ** 1.4
    seg = 70
    y = FLOOR
    while y > FLOOR - hgt:
        top = max(FLOOR - hgt, y - seg)
        rrect(d, (bx - 14, top, bx + 14, y), 6, (110, 180, 90, 255), outline=(60, 110, 50, 255), w=2)
        y -= seg
        if FLOOR - y > 150 and int(y) % 3 == 0:
            poly(d, [(bx + 14, y + 10), (bx + 70, y - 14), (bx + 20, y + 2)], (120, 200, 100, 255))
    look = smooth(prog(u, 2.5, 3.0))
    p = place(dict(STAND, head=(10 - 16 * look, -150 - 6 * look), er=(30, -100), hr=(60, -110)), (430, FLOOR - 113 * S), 1, S)
    hero(st, p, "determined", 1, "shocked" if 2.5 < u < 3.0 else ("happy" if u >= 3.0 else "determined"), u)
    cam_y = lerp(FLOOR - 170, FLOOR - 1300, smooth(prog(u, 2.5, 3.4)))
    return (1.6, 620, max(cam_y, 620))


def bamboo_year(u):
    if u >= 2.4:
        return 5
    return 1 + min(3, int(u / 0.6))


# ---------------------------------------------------------------- look
GRADE = {"stone": (1.08, 0.98, 0.9), "seed": (0.95, 1.06, 0.92), "ice": (0.88, 0.98, 1.12), "mirror": (1.08, 1.0, 0.88),
         "views": (0.9, 0.98, 1.1), "bamboo": (0.96, 1.08, 0.92), "end": (1.0, 1.0, 1.0)}
_M = {}


def spot_mask(cy):
    key = int(cy)
    if key not in _M:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        g = np.exp(-(((xx - W / 2) / 520) ** 2 + ((yy - cy) / 720) ** 2))
        _M[key] = (0.22 + 0.95 * g)[..., None]
    return _M[key]


def look(im, kind, t):
    a = np.asarray(im.convert("RGB"), np.float32)
    a *= spot_mask(1150 if kind not in ("end",) else 760)
    a *= np.array(GRADE[kind], np.float32)[None, None, :]
    # a soft cone of light from above + dust in it
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.polygon([(W / 2 - 60, 0), (W / 2 + 60, 0), (W / 2 + 420, H * 0.72), (W / 2 - 420, H * 0.72)], (255, 240, 210, 22))
    rng = np.random.default_rng(5)
    for _ in range(40):
        x0, y0, sp = rng.uniform(250, 830), rng.uniform(0, 1400), rng.uniform(8, 24)
        y = (y0 + t * sp) % 1400
        x = x0 + 14 * math.sin(t * 0.7 + y0)
        d.ellipse((x - 2, y - 2, x + 2, y + 2), (255, 240, 210, 90))
    lay = lay.filter(ImageFilter.GaussianBlur(6))
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    out.alpha_composite(lay)
    return out


def whip(im, amt):
    """a fast horizontal whip-pan blur between scenes"""
    if amt <= 0.01:
        return im
    a = np.asarray(im.convert("RGB"), np.float32)
    acc = np.zeros_like(a)
    n = 8
    for k in range(n):
        acc += np.roll(a, int((k - n / 2) * 18 * amt), axis=1)
    return Image.fromarray((acc / n).astype(np.uint8)).convert("RGBA")


# ---------------------------------------------------------------- frame
FN = {"stone": stone, "seed": seed, "ice": ice, "mirror": mirror, "views": views, "bamboo": bamboo}


def frame(t):
    kind, u, dur = scene_at(t)
    st = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(st)
    if kind == "end":
        z, cx, cy = bamboo(st, d, 3.4 + u * 0.3)
        z, cx, cy = 1.6, 520, 620
    else:
        z, cx, cy = FN[kind](st, d, u)
    shake = 0
    if kind == "stone":
        if u >= HITS_AT:
            shake = 16 * max(0, 1 - (u - HITS_AT) / 0.4)
        else:
            ph = (u / (HITS_AT / 9)) % 1.0
            shake = 5 * max(0, 1 - abs(ph - 0.5) / 0.08)
    push = 0.93 + 0.12 * clamp(u / max(0.5, ORIG.get(kind, 1.6)))
    drift = 26 * math.sin(t * 0.9)
    im = compose(st, None, z * push, cx + drift + shake * math.sin(t * 80), cy, spots=((540, 1.0),), refl=True)
    im = look(im, kind, t)
    for a_, b_, k_ in SC[1:]:
        if abs(t - a_) < 0.12:
            im = whip(im, 1 - abs(t - a_) / 0.12)
    if kind == "stone":
        n = stone_count(u)
        counter(im, str(n), GOLD if n == 100 else (246, 246, 250), k=hq.pop(u, HITS_AT, 0.2) if n == 100 else 1.0)
    elif kind == "seed":
        counter(im, f"DAY {max(1, int(1 + 89 * clamp(u / 2.6)))}", size=110)
    elif kind == "mirror":
        counter(im, f"MONTH {max(1, min(6, 1 + int(u / 0.45)))}", size=110)
    elif kind == "ice":
        tmp = ice_temp(u)
        counter(im, f"{tmp}°C", GOLD if tmp == 0 else (170, 210, 250), size=130, k=hq.pop(u, MELT, 0.2) if tmp == 0 else 1.0)
    elif kind == "views":
        n = video_no(u)
        counter(im, f"VIDEO #{n}", GOLD if n == 100 else (246, 246, 250), size=110)
    elif kind == "bamboo":
        yr = bamboo_year(u)
        counter(im, f"YEAR {yr}", GOLD if yr == 5 else (246, 246, 250), size=120)
    else:
        a = smooth(prog(u, 0.0, 0.3))
        text(im, W / 2, 640, "GROWTH", 120, a=a)
        text(im, W / 2, 780, "YOU CAN'T SEE.", 96, col=GOLD, a=smooth(prog(u, 0.25, 0.55)))
    dd = ImageDraw.Draw(im)
    PW.spaced(dd, 70, 40, "#1", font("InterDisplay-Bold.otf", 34), (236, 70, 60, 255), 1)
    PW.spaced(dd, W / 2, 40, "LIFE IN ONE FRAME", font("Inter-SemiBold.otf", 22), (180, 186, 204, 255), 6)
    return np.asarray(im.convert("RGB"))


def render(i):
    return frame(i / FPS).tobytes()


MUSIC = "Undaunted.mp3"
HIT = 69.0     # lands on the bamboo shooting up


def audio(sfx_only=False):
    n = int(DUR * SR)
    out = np.zeros((n, 2))
    if not sfx_only:
        put(out, track(MUSIC, HIT - at("bamboo", 2.4), DUR), 0.0, 2.2, fin=0.05, fout=1.0)
    clank = lambda: tone(900, 0.25, (1, 2.76, 5.4), a=0.001, d=0.2)  # noqa
    for k in range(9):
        mix_in(out, clank(), at("stone", (k + 0.5) * HITS_AT / 9), 0.35, 0.2)
    boom = lambda: tone(50, 0.7, (1, 2), a=0.002, d=0.6)  # noqa
    crack = noise(0.9, 4, lo=60, hi=3000)[:int(0.9 * SR)] * env(int(0.9 * SR), 0.002, 0.6)
    mix_in(out, crack, at("stone", HITS_AT), 0.8, 0.0)
    mix_in(out, boom(), at("stone", HITS_AT), 0.7, 0.0)
    mix_in(out, noise(2.0, 6, lo=1500, hi=7000)[:int(2.0 * SR)] * env(int(2.0 * SR), 0.2, 0.4), start("seed"), 0.08, 0.3)
    for k in range(9):   # the thermometer ticking up
        mix_in(out, tone(1600, 0.05, (1, 2), a=0.001, d=0.03), at("ice", (k + 0.5) * MELT / 10), 0.12, 0.3)
    mix_in(out, noise(0.8, 8, lo=300, hi=4000)[:int(0.8 * SR)] * env(int(0.8 * SR), 0.05, 0.6), at("ice", MELT), 0.3, 0.0)
    for k in range(5):
        mix_in(out, tone(2400, 0.12, (1, 2.3), a=0.001, d=0.08), at("mirror", 0.2 + k * 0.45), 0.12, -0.2)
    mix_in(out, tone(1300, 0.9, (1, 2, 3), a=0.002, d=0.8), at("mirror", 2.35), 0.2, 0.0)
    for k in range(10):  # keyboard
        mix_in(out, tone(3000, 0.03, (1,), a=0.001, d=0.02), at("views", 0.1 + k * 0.22), 0.08, 0.2)
    mix_in(out, tone(880, 0.6, (1, 2, 3), a=0.002, d=0.5), at("views", VIRAL), 0.25, 0.0)
    for k in range(4):
        mix_in(out, tone(220, 0.12, (1, 2), a=0.001, d=0.08), at("bamboo", k * 0.6), 0.3, 0.0)
    whoosh = noise(1.0, 9, lo=200, hi=6000)[:int(1.0 * SR)] * env(int(1.0 * SR), 0.6, 0.3)
    mix_in(out, whoosh, at("bamboo", 2.35), 0.5, 0.0)
    mix_in(out, boom(), T_END, 0.5, 0.0)
    tt = np.arange(n) / SR
    out *= np.clip((DUR - tt) / 0.5, 0.0, 1)[:, None]
    out /= max(1.0, np.abs(out).max() / 0.9)
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    if "--stills" in sys.argv:
        ts = [float(a) for a in sys.argv[2:]] or [0.8, 2.0, 3.6, 5.6, 6.9, 8.4, 9.6, 10.6, 11.7, 13.6, 14.6]
        sheet = Image.new("RGB", (360 * len(ts), 640))
        for j, t in enumerate(ts):
            sheet.paste(Image.fromarray(frame(t)).resize((360, 640), Image.LANCZOS), (j * 360, 0))
        p = os.path.join(here, "frame", "ep1-stills.png")
        sheet.save(p)
        print(p)
        return
    out = sys.argv[1]
    wav = out + ".wav"
    write_wav(wav, audio("--sfx" in sys.argv))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                          "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-13:TP=-1.5:LRA=11", "-ar", "44100",
                          "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                         stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for b in pool.imap(render, range(NF), chunksize=2):
            p.stdin.write(b)
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print(out)


if __name__ == "__main__":
    main()
