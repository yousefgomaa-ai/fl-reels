#!/usr/bin/env python3
"""GET UP - a boxing short. ~18.5 s.

HOOK: he's down on the canvas, the referee is counting, the crowd boos.  "GET UP."
Every number of the count cuts to a memory (sepia): laughed at in the gym (4), running at dawn (5), an old taped bag
in a garage (6), someone telling him QUIT (7), his mother (8). At 9 his eyes open. He stands. DOUBT comes in smug -
one uppercut - DOUBT is down. Bell. The referee raises his arm, confetti.
THEY COUNTED HIM OUT. / HE COUNTED ON HIMSELF.

    python3 stick/boxing.py --stills [t ...]   # -> stick/boxing/stills.png
    python3 stick/boxing.py stick/boxing.mp4
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perfect_wave as PW  # noqa
import hq  # noqa
import race as R  # noqa
from compare import ell, line, rrect, poly, figure, place, ik, FLOOR, K, W, H  # noqa
from perfect_wave import clamp, env, font, lerp, lerp_pose, mix_in, noise, prog, smooth, tone, write_wav  # noqa
from money_chars import face, outfit, scarf, S, GOLD, RED  # noqa
from money import text, compose, put, track  # noqa

FPS, SR = 30, 44100
DUR = 25.0
NF = int(round(DUR * FPS))
STAND = PW.STAND
HX, DX = 470, 650         # him / DOUBT in the ring
T_HIT, T_FLOOR = 2.2, 2.9                      # he gets caught, he's down
COUNT_T = [3.2, 5.6, 6.1, 8.2, 8.7, 10.8, 11.3, 13.4, 13.9]   # 1..9
MEMS = [(4.0, 5.6, "gym"), (6.6, 8.2, "pullup"), (9.2, 10.8, "pushup"), (11.8, 13.4, "dawn")]
T_RISE = 14.3
GYM_RATE = 2.6      # punches per second on the bag
COMBO = [16.6, 17.0, 17.5, 18.2]               # jab, jab, hook, uppercut
T_DOWN, T_WIN, T_LINES = 18.35, 19.8, 22.6
GLOVE_R = (214, 40, 40)
GLOVE_K = (30, 30, 34)
MAT = (214, 214, 222)


def count_at(t):
    n = 0
    for i, c in enumerate(COUNT_T):
        if t >= c:
            n = i + 1
    return n if t < T_RISE + 0.6 else 0


def flash_at(t):
    for t0, t1, kind in MEMS:
        if t0 <= t < t1:
            return kind, t - t0
    return None


# ---------------------------------------------------------------- characters
LYING = {"head": (-150, -10), "neck": (-108, -6), "el": (-80, 30), "hl": (-46, 40), "er": (-80, -44), "hr": (-40, -70),
         "kl": (56, -24), "fl": (113, -2), "kr": (56, -6), "fr": (113, 6)}
GUARD = dict(STAND, el=(26, -70), hl=(40, -130), er=(36, -66), hr=(52, -124))


def boxer_hero(st, p, expr, t, f=1, gloves=True):
    figure(st, p, S, light=(0.4, -0.9))
    d = ImageDraw.Draw(st)
    for side in ("l", "r"):
        line(d, [p["hip"], p["k" + side]], (200, 40, 40, 255), 26 * S)     # red shorts
    face(d, p, expr, f, t)
    scarf(d, p, f)
    if gloves:
        for side in ("hl", "hr"):
            ell(d, *p[side], 19, 17, GLOVE_R + (255,))
            ell(d, p[side][0] - 5, p[side][1] - 6, 6, 4, (250, 120, 120, 255))


def boxer_doubt(st, p, expr, t, f=-1):
    figure(st, p, S * 1.12, light=(0.4, -0.9), body=(205, 208, 216))
    d = ImageDraw.Draw(st)
    outfit(d, p, (34, 34, 40), f, legs=False)
    for side in ("l", "r"):
        line(d, [p["hip"], p["k" + side]], (24, 24, 28, 255), 28 * S)
    face(d, p, expr, f, t)
    for side in ("hl", "hr"):
        ell(d, *p[side], 21, 19, GLOVE_K + (255,))
    hx, hy = p["head"]
    PW.spaced(d, hx * K, (hy - 70) * K, "DOUBT", font("InterDisplay-Bold.otf", 30 * K), (240, 70, 60, 255), 6)


def referee(st, p, t, f=1):
    figure(st, p, S, light=(0.4, -0.9))
    d = ImageDraw.Draw(st)
    outfit(d, p, (236, 236, 240), f, legs=True)
    nx, ny = p["neck"]
    hx_, hy_ = p["hip"]
    for j in range(4):   # stripes
        x = nx - 12 + j * 8
        line(d, [(x, ny + 4), (x + (hx_ - nx) * 0.0, hy_)], (20, 20, 24, 255), 3)
    poly(d, [(nx - 8, ny - 2), (nx, ny + 4), (nx - 8, ny + 10)], (20, 20, 24, 255))
    poly(d, [(nx + 8, ny - 2), (nx, ny + 4), (nx + 8, ny + 10)], (20, 20, 24, 255))
    face(d, p, "determined", f, t)


def plain(st, p, expr, t, f=1, body=(150, 154, 166)):
    figure(st, p, S, light=(0.4, -0.9), body=body)
    face(ImageDraw.Draw(st), p, expr, f, t)


# ---------------------------------------------------------------- the ring
_C = {}


def ring_back(cheer=0.0, t=0.0):
    key = "rb"
    if key not in _C:
        img = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        rng = np.random.default_rng(5)
        for row in range(4):     # crowd silhouettes behind the ropes
            y = FLOOR - 330 + row * 48
            for x in np.arange(-20 + row * 17, W + 40, 44):
                sh = int(28 + row * 8 + rng.uniform(-6, 6))
                ell(d, x, y, 18, 20, (sh, sh, sh + 6, 255))
                rrect(d, (x - 24, y + 14, x + 24, y + 70), 12, (sh, sh, sh + 6, 255))
        _C[key] = img
    img = _C[key].copy()
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(int(t * 9))
    for _ in range(4 + int(10 * cheer)):    # camera flashes
        ell(d, rng.uniform(0, W), rng.uniform(FLOOR - 340, FLOOR - 160), 6, 6, (255, 255, 240, 220))
    return img


def ring(d):
    poly(d, [(0, FLOOR - 4), (W, FLOOR - 4), (W, FLOOR + 30), (0, FLOOR + 30)], MAT + (255,))
    poly(d, [(0, FLOOR + 30), (W, FLOOR + 30), (W, FLOOR + 140), (0, FLOOR + 140)], (120, 24, 30, 255))
    for x in (40, W - 40):
        rrect(d, (x - 12, FLOOR - 250, x + 12, FLOOR), 4, (200, 200, 210, 255))
    for j, col in enumerate(((200, 40, 40), (240, 240, 245), (40, 70, 170))):
        y = FLOOR - 230 + j * 60
        line(d, [(40, y), (W - 40, y + 4)], col + (255,), 7)


def front_ropes(d):
    for j, col in enumerate(((200, 40, 40), (240, 240, 245), (40, 70, 170))):
        y = FLOOR - 170 + j * 70
        line(d, [(-10, y + 40), (W + 10, y + 46)], col + (200,), 5)


# ---------------------------------------------------------------- scenes
def hit_k(t, t0, d=0.35):
    return math.sin(math.pi * clamp((t - t0) / d))


def ring_scene(t):
    st = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(st)
    ring(d)
    bob = 5 * math.sin(t * 7)
    # ---------------- him
    if t < T_HIT:                       # the opening exchange
        jab = hit_k(t, 1.1)
        blk = hit_k(t, 0.5, 0.4)
        pose = dict(GUARD, er=(36 + 30 * jab, -80), hr=(52 + 110 * jab, -124 - 10 * jab),
                    el=(26 - 10 * blk, -80), hl=(40 - 10 * blk, -150))
        hp = place(pose, (HX + 10 * jab, FLOOR - 113 * S + bob), 1, S)
        hexpr = "determined"
    elif t < T_RISE:                    # caught, spinning down, on the canvas
        k = smooth(prog(t, T_HIT, T_FLOOR))
        if k < 1:
            pose = lerp_pose(dict(GUARD, head=(-30, -140), neck=(-16, -104)), LYING, k)
            hp = place(pose, (HX - 30 * k, lerp(FLOOR - 113 * S, FLOOR - 30, k)), 1, S)
        else:
            hp = place(LYING, (HX - 30, FLOOR - 30), 1, S)
        hexpr = "determined" if t >= COUNT_T[8] + 0.2 else ("shocked" if t < T_FLOOR else "tired")
    else:
        rise = smooth(prog(t, T_RISE, T_RISE + 0.9))
        punch = max(hit_k(t, c, 0.3) for c in COMBO)
        upper = hit_k(t, COMBO[3], 0.4)
        if t < T_WIN:
            pose = lerp_pose(dict(STAND, head=(30, -100), neck=(20, -70), kl=(40, 20), fl=(0, 60), kr=(-20, 54),
                                  fr=(-60, 60), el=(40, -20), hl=(60, 30), er=(30, -20), hr=(50, 40)), GUARD, rise)
            side = "r" if any(c <= t < c + 0.3 for c in (COMBO[0], COMBO[2])) else "l"
            if punch > 0:
                if upper > 0:
                    pose = dict(pose, er=(60, -150), hr=(110, -200))
                elif side == "r":
                    pose = dict(pose, er=(36 + 30 * punch, -80), hr=(52 + 120 * punch, -124))
                else:
                    pose = dict(pose, el=(26 + 30 * punch, -84), hl=(40 + 120 * punch, -128))
            x = lerp(HX - 30, HX, rise) + 40 * smooth(prog(t, 16.3, 18.3))
            hp = place(pose, (x, lerp(FLOOR - 60 * S, FLOOR - 113 * S, rise) + bob * rise), 1, S)
            hexpr = "determined"
        else:
            up = smooth(prog(t, T_WIN, T_WIN + 0.4))
            pose = dict(STAND, er=(lerp(10, 26, up), lerp(-58, -148, up)), hr=(lerp(14, 40, up), lerp(-10, -196, up)))
            hp = place(pose, (HX + 40, FLOOR - 113 * S), 1, S)
            hexpr = "happy"
    boxer_hero(st, hp, hexpr, t, 1)
    # ---------------- DOUBT
    if t < T_DOWN:
        jab = hit_k(t, 0.5, 0.4)
        hook = hit_k(t, 1.9, 0.45)
        rocked = max([hit_k(t, c + 0.12, 0.35) for c in COMBO] + [0])
        pose = dict(GUARD, er=(36 + 30 * jab, -80), hr=(52 + 120 * jab, -120),
                    el=(26 + 40 * hook, -110), hl=(40 + 130 * hook, -150 + 20 * hook),
                    head=(-30 * rocked, -150 - 6 * rocked))
        if T_FLOOR <= t < T_RISE:       # walks off, arms up, sure he won
            pose = dict(PW.ARMS_UP)
        x = DX if t < T_RISE else lerp(DX + 60, DX, smooth(prog(t, T_RISE + 0.4, 16.3)))
        x += 30 * rocked
        dexpr = "smug" if t < 16.6 else "shocked"
        dp = place(pose, (x + (80 if T_FLOOR <= t < T_RISE else 0), FLOOR - 113 * S * 1.12 + bob), -1, S * 1.12)
        boxer_doubt(st, dp, dexpr, t)
    else:
        fall = smooth(prog(t, T_DOWN, T_DOWN + 0.6))
        dpose = lerp_pose(dict(GUARD, head=(-20, -150)), dict(LYING, head=(150, -10), neck=(108, -6), kl=(-56, -24),
                                                             fl=(-113, -2), kr=(-56, -6), fr=(-113, 6)), fall)
        dp = place(dpose, (DX + 60 + 40 * fall, lerp(FLOOR - 113 * S * 1.12, FLOOR - 30, fall)), -1, S * 1.12)
        boxer_doubt(st, dp, "shocked" if fall < 1 else "tired", t)
    # ---------------- referee
    if t < T_FLOOR:
        rp = place(STAND, (170, FLOOR - 113 * S), 1, S)
    elif t < T_RISE + 0.6:
        call = max([hit_k(t, c, 0.4) for c in COUNT_T] + [0])
        rp = place(dict(STAND, head=(20, -128), neck=(12, -94), kl=(30, 14), fl=(-6, 60), kr=(-24, 52), fr=(-60, 60),
                        er=(40, -130 - 30 * call), hr=(50, -180 - 40 * call)), (HX - 250, FLOOR - 70 * S), 1, S)
    elif t < T_WIN:
        rp = place(STAND, (170, FLOOR - 113 * S), 1, S)
    else:
        rp = place(dict(STAND, er=(30, -150), hr=(50, -196)), (HX - 30, FLOOR - 113 * S), 1, S)
    referee(st, rp, t, 1)
    front_ropes(d)
    if t >= T_WIN:
        rng = np.random.default_rng(1)
        for _ in range(120):
            x0, sp, ph = rng.uniform(0, W), rng.uniform(0.25, 0.5), rng.uniform(0, 1)
            y = ((t - T_WIN) * sp + ph) % 1.0 * (FLOOR + 100) - 60
            c = [(240, 200, 60), (230, 60, 60), (240, 240, 245), (80, 160, 240)][int(ph * 40) % 4]
            xx = x0 + 20 * math.sin(t * 3 + ph * 9)
            rrect(d, (xx, y, xx + 10, y + 6), 1, c + (255,))
    # ---------------- camera
    if t < T_HIT:
        z, cx, cy = lerp(2.3, 2.1, t / T_HIT), 560, FLOOR - 160
    elif t < T_FLOOR + 0.2:
        z, cx, cy = 2.1, lerp(560, HX - 60, smooth(prog(t, T_HIT, T_FLOOR))), lerp(FLOOR - 160, FLOOR - 90, smooth(prog(t, T_HIT, T_FLOOR)))
    elif t < T_RISE:
        z, cx, cy = 2.5 + 0.15 * math.sin(t * 2), HX - 90, FLOOR - 80
    elif t < T_WIN:
        k = smooth(prog(t, T_RISE, T_RISE + 1.0))
        k2 = smooth(prog(t, COMBO[3] - 0.1, COMBO[3] + 0.15))
        z, cx, cy = lerp(2.5, 2.1, k) + 0.3 * k2, lerp(HX - 90, 580, k), lerp(FLOOR - 80, FLOOR - 160, k)
    else:
        k = smooth(prog(t, T_WIN, T_WIN + 1.0))
        z, cx, cy = lerp(2.1, 1.75, k), 520, lerp(FLOOR - 170, FLOOR - 200, k)
    cheer = smooth(prog(t, T_DOWN, T_WIN + 0.5))
    sh = 0
    for c, a_ in ((T_HIT - 0.15, 12), (COMBO[3], 16)):
        if c <= t < c + 0.35:
            sh = a_ * (1 - (t - c) / 0.35)
    im = compose(st, None, z, cx + sh * math.sin(t * 90), cy, spots=((HX, 1.0), (DX, 0.6)),
                 back=ring_back(cheer, t), refl=False)
    return im


def memory(kind, u, t):
    st = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(st)
    cam = (2.0, 540, FLOOR - 130)
    if kind == "gym":
        ph = (u * GYM_RATE) % 1.0
        ext = math.sin(math.pi * ph) ** 2
        left = int(u * GYM_RATE) % 2 == 0
        since = (u - (math.floor(u * GYM_RATE - 0.5) + 0.5) / GYM_RATE) if u * GYM_RATE >= 0.5 else 9
        sw = 0.12 * math.exp(-since * 5) * math.sin(since * 14)          # the bag swings after each hit
        bx, by = 640 + 300 * math.sin(sw), FLOOR - 330 + 300 * (1 - math.cos(sw))
        line(d, [(640, FLOOR - 630), (bx, by)], (120, 120, 120, 255), 4)
        c_, s_ = math.cos(sw), math.sin(sw)
        poly(d, [(bx - 28 * c_, by + 28 * s_), (bx + 28 * c_, by - 28 * s_), (bx + 28 * c_ - 180 * s_, by - 28 * s_ + 180 * c_),
                 (bx - 28 * c_ - 180 * s_, by + 28 * s_ + 180 * c_)], (110, 60, 50, 255))
        pose = dict(GUARD)
        if left:
            pose = dict(pose, el=(26 + 50 * ext, -90), hl=(40 + 95 * ext, -118 + 10 * ext))
        else:
            pose = dict(pose, er=(36 + 50 * ext, -86), hr=(52 + 95 * ext, -114 + 10 * ext))
        p = place(pose, (520 + 10 * ext, FLOOR - 113 * S + 4 * ext), 1, S)
        boxer_hero(st, p, "determined", t)
        for j, x in enumerate((300, 380)):
            bounce = abs(math.sin(t * 9 + j))
            pp = place(dict(STAND, head=(4, -150 - 6 * bounce), er=(40, -110 + 8 * math.sin(t * 14 + j)),
                            hr=(90, -120 + 12 * math.sin(t * 14 + j)), el=(-20, -70), hl=(-10, -30 - 10 * bounce)),
                       (x, FLOOR - 113 * S - 5 * bounce), 1, S)
            plain(st, pp, "laugh", t)
        cam = (1.7, 470, FLOOR - 150)
    elif kind == "dawn":
        for r, a in ((200, 60), (110, 255)):
            ell(d, 760, FLOOR - 260, r, r, (255, 190, 110, a))
        line(d, [(260, FLOOR), (260, FLOOR - 420)], (60, 60, 70, 255), 7)
        pose = R.run_pose(t * 13, 0.7)
        p = place(pose, R.grounded(pose, 520 + 60 * u, FLOOR, S), 1, S)
        boxer_hero(st, p, "tired", t, gloves=False)
        cam = (1.8, 540, FLOOR - 150)
    elif kind == "garage":
        poly(d, [(200, FLOOR - 520), (880, FLOOR - 520), (880, FLOOR), (200, FLOOR)], (60, 56, 52, 255))
        line(d, [(640, FLOOR - 520), (640, FLOOR - 340)], (160, 150, 120, 255), 3)
        sw = 0.08 * math.sin(t * 7)
        rrect(d, (612, FLOOR - 340, 668, FLOOR - 160), 18, (90, 80, 70, 255))
        for j in range(3):
            line(d, [(612, FLOOR - 300 + j * 50), (668, FLOOR - 290 + j * 50)], (200, 200, 190, 255), 6)
        hit = abs(math.sin(t * 9))
        p = place(dict(GUARD, er=(40 + 50 * hit, -100), hr=(60 + 70 * hit, -120)), (520, FLOOR - 113 * S), 1, S)
        boxer_hero(st, p, "determined", t)
        cam = (1.9, 560, FLOOR - 160)
    elif kind == "pullup":
        for x in (380, 700):
            line(d, [(x, FLOOR), (x, FLOOR - 470)], (90, 90, 96, 255), 9)
        line(d, [(370, FLOOR - 460), (710, FLOOR - 460)], (150, 150, 156, 255), 7)
        up = 0.5 - 0.5 * math.cos(t * 5)
        hip_y = FLOOR - 272 - 60 * up
        pose = {"head": (0, -150 + 20 * (1 - up)), "neck": (0, -108), "kl": (-6, 56), "fl": (-14, 112), "kr": (6, 56),
                "fr": (-4, 112)}
        p = dict(place(dict(pose, el=(0, 0), hl=(0, 0), er=(0, 0), hr=(0, 0)), (540, hip_y), 1, S))
        for side, hx in (("l", 500), ("r", 580)):
            tgt = (hx, FLOOR - 466)
            p["h" + side] = tgt
            p["e" + side] = ik(p["neck"], tgt, 42 * S, 40 * S, 1 if side == "r" else -1)
        boxer_hero(st, p, "determined" if up > 0.5 else "tired", t, gloves=False)
        cam = (1.8, 540, FLOOR - 250)
    elif kind == "pushup":
        up = 0.5 - 0.5 * math.cos(t * 6)
        x = 470
        hip = (x, FLOOR - 52 - 26 * up)
        neck = (x + 100, FLOOR - 70 - 44 * up)
        p = {"hip": hip, "neck": neck, "head": (neck[0] + 40, neck[1] - 4),
             "kl": (x - 56, FLOOR - 34 - 14 * up), "fl": (x - 112, FLOOR - 12), "kr": (x - 56, FLOOR - 30 - 14 * up),
             "fr": (x - 112, FLOOR - 8)}
        for side, dx in (("l", -6), ("r", 6)):
            tgt = (neck[0] + 6 + dx, FLOOR - 4)
            p["h" + side] = tgt
            p["e" + side] = ik(neck, tgt, 42 * S, 40 * S, -1)
        boxer_hero(st, p, "determined", t, gloves=False)
        rng = np.random.default_rng(int(t * 6))
        for j in range(3):   # sweat
            ell(d, p["head"][0] + rng.uniform(-10, 20), p["head"][1] + 30 + 40 * ((t * 2 + j / 3) % 1), 3, 5, (150, 200, 255, 220))
        cam = (2.1, 520, FLOOR - 100)
    elif kind == "quit":
        p = place(dict(STAND, head=(16, -136)), (560, FLOOR - 113 * S), -1, S)
        boxer_hero(st, p, "sad", t, f=-1, gloves=False)
        pp = place(dict(STAND, er=(40, -100), hr=(80, -110)), (400, FLOOR - 113 * S), 1, S)
        plain(st, pp, "smug", t)
        R.bubble(st, u, 0.0, 1.0, "QUIT.", 440, FLOOR - 300, size=40)
        cam = (2.0, 480, FLOOR - 160)
    else:   # mom
        p = place(dict(STAND, head=(10, -140)), (560, FLOOR - 113 * S), -1, S)
        boxer_hero(st, p, "sad" if u < 0.4 else "happy", t, f=-1, gloves=False)
        mp = place(dict(STAND, er=(50, -110), hr=(110, -120), el=(46, -90), hl=(100, -80)), (440, FLOOR - 113 * S * 0.95), 1,
                   S * 0.95)
        figure(st, mp, S * 0.95, light=(0.4, -0.9))
        dd = ImageDraw.Draw(st)
        hx, hy = mp["head"]
        ell(dd, hx - 6, hy - 24, 18, 14, (150, 150, 156, 255))     # grey bun
        outfit(dd, mp, (120, 90, 140), 1, legs=False)
        face(dd, mp, "happy", 1, t)
        cam = (2.0, 500, FLOOR - 170)
    im = compose(st, None, *cam, spots=((540, 1.0),), refl=False)
    # memory look: warm sepia + vignette + grain
    g = ImageOps.grayscale(im.convert("RGB"))
    sep = ImageOps.colorize(g, (30, 18, 8), (250, 220, 170))
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse((-200, -100, W + 200, H + 100), fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(160))
    out = Image.composite(sep, Image.new("RGB", (W, H), (10, 6, 2)), vig)
    return out.convert("RGBA")


def frame(t):
    fl = flash_at(t)
    if fl:
        im = memory(fl[0], fl[1], t)
    else:
        im = ring_scene(t)
    d = ImageDraw.Draw(im)
    n = count_at(t)
    if n and not fl:
        c = COUNT_T[n - 1]
        k = hq.pop(t, c, 0.18)
        f = font("InterDisplay-Bold.otf", int(260 * max(0.3, k)))
        PW.spaced(d, W / 2, 180, str(n), f, (255, 255, 255, 255), 0)
    if COUNT_T[8] + 0.15 <= t < T_RISE + 0.9:
        a = hq.pop(t, COUNT_T[8] + 0.15, 0.2)
        text(im, W / 2, 1420, "GET UP.", 150, col=GOLD, a=min(1, a))
    for j, s_ in enumerate(("THEY COUNTED HIM OUT.", "HE COUNTED ON HIMSELF.")):
        a = smooth(prog(t, T_LINES + 0.8 * j, T_LINES + 0.8 * j + 0.35))
        if a > 0:
            text(im, W / 2, 150 + j * 84, s_, 64, col=(GOLD if j else (246, 240, 226)), a=a)
    cuts = [m[0] for m in MEMS] + [m[1] for m in MEMS]
    if any(c <= t < c + 0.06 for c in cuts):
        im = Image.blend(im.convert("RGB"), Image.new("RGB", (W, H), (255, 255, 255)), 0.45).convert("RGBA")
    return np.asarray(im.convert("RGB"))


def render(i):
    return frame(i / FPS).tobytes()


MUSIC = "The Escalation.mp3"
HIT = 308.0


def _punch(strength=1.0, seed=0):
    """a layered hit: sub thump with a pitch drop + leather smack + snap + short room tail"""
    n = int(0.6 * SR)
    tt = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    f = 70 * np.exp(-tt * 14) + 38
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9)
    sm = rng.normal(0, 1, n)
    sm = np.convolve(sm, np.ones(6) / 6, "same") - np.convolve(sm, np.ones(60) / 60, "same")   # ~300-3k band
    smack = sm * np.exp(-tt * 55) * 2.2
    snap = rng.normal(0, 1, n) * np.exp(-tt * 260) * 0.6
    tail = np.convolve(rng.normal(0, 1, n), np.ones(30) / 30, "same") * np.exp(-tt * 7) * 0.25
    x = sub * (0.9 + 0.6 * strength) + smack * (0.6 + 0.4 * strength) + snap + tail * strength
    return x / np.abs(x).max() * strength


def _bell(seed=0):
    """a boxing-ring bell: inharmonic partials, hard strike, long ring"""
    n = int(1.6 * SR)
    tt = np.arange(n) / SR
    x = np.zeros(n)
    for fr, a, dk in ((830, 1.0, 2.2), (2140, 0.6, 3.0), (2990, 0.35, 4.0), (4370, 0.2, 6.0), (1660, 0.3, 2.6)):
        x += a * np.sin(2 * np.pi * fr * tt) * np.exp(-tt * dk)
    x += np.random.default_rng(seed).normal(0, 1, n) * np.exp(-tt * 300) * 0.5
    return x / np.abs(x).max()


def audio():
    n = int(DUR * SR)
    out = np.zeros((n, 2))
    mus = np.zeros((n, 2))
    put(mus, track(MUSIC, HIT - T_LINES, DUR), 0.0, 1.0, fin=0.05, fout=1.0)
    tt = np.arange(n) / SR
    crowd = noise(DUR, 2, lo=200, hi=2500)[:n]
    crowd = np.pad(crowd, (0, n - len(crowd)))
    lvl = 0.03 + 0.08 * np.clip((tt - T_DOWN) / 0.5, 0, 1) * np.clip((DUR - tt) / 2, 0, 1)
    out += (crowd * lvl)[:, None]
    for c in COUNT_T:     # the count: a hard clap + boom
        mix_in(out, noise(0.12, 5, lo=800, hi=6000)[:int(0.12 * SR)] * env(int(0.12 * SR), 0.001, 0.08), c, 0.3, 0.0)
        mix_in(out, tone(70, 0.4, (1, 2), a=0.002, d=0.3), c, 0.35, 0.0)
    for t0, t1, kind in MEMS:
        for c in (t0, t1):
            mix_in(out, noise(0.3, 7, lo=400, hi=6000)[:int(0.3 * SR)] * env(int(0.3 * SR), 0.15, 0.1), c - 0.15, 0.12, 0.0)
    hits = [(0.6, 0.45), (1.25, 0.5), (T_HIT - 0.1, 1.0), (T_FLOOR - 0.1, 0.7), (COMBO[0] + 0.1, 0.7),
            (COMBO[1] + 0.1, 0.75), (COMBO[2] + 0.1, 0.85), (COMBO[3] + 0.12, 1.0), (T_DOWN + 0.55, 0.7)]
    duck = np.ones(n)
    for j, (c, g) in enumerate(hits):
        mix_in(out, _punch(g, j), c, 0.95 * g, 0.15 * (1 if j % 2 else -1))
        if g >= 0.85:   # the music breathes out under the big ones
            i0 = int(c * SR)
            m = int(0.35 * SR)
            if i0 + m < n:
                duck[i0:i0 + m] = np.minimum(duck[i0:i0 + m], 0.35 + 0.65 * np.linspace(0, 1, m) ** 2)
    g0 = [m[0] for m in MEMS if m[2] == "gym"][0]
    g1 = [m[1] for m in MEMS if m[2] == "gym"][0]
    k = 0
    while True:
        at = g0 + (k + 0.5) / GYM_RATE
        if at >= g1:
            break
        mix_in(out, _punch(0.55, 20 + k), at, 0.55, 0.3)
        k += 1
    bell = _bell()
    for k in range(3):
        mix_in(out, bell, T_WIN + 0.28 * k, 0.32, 0.0)
    mus *= duck[:, None]
    out = out + mus * 2.4
    out *= np.clip((DUR - tt) / 0.6, 0.0, 1)[:, None]
    out /= max(1.0, np.abs(out).max() / 0.9)
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(here, "boxing"), exist_ok=True)
    if "--stills" in sys.argv:
        ts = [float(a) for a in sys.argv[2:]] or [0.6, 2.3, 3.4, 4.8, 7.4, 10.0, 12.6, 14.2, 17.6, 18.3, 21.0, 24.0]
        sheet = Image.new("RGB", (360 * len(ts), 640))
        for j, t in enumerate(ts):
            sheet.paste(Image.fromarray(frame(t)).resize((360, 640), Image.LANCZOS), (j * 360, 0))
        p = os.path.join(here, "boxing", "stills.png")
        sheet.save(p)
        print(p)
        return
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "boxing.mp4")
    wav = out + ".wav"
    write_wav(wav, audio())
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
    print(f'Credit: Music: "{MUSIC[:-4]}" by Kevin MacLeod (incompetech.com), CC BY 4.0')


if __name__ == "__main__":
    main()
