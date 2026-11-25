#!/usr/bin/env python3
"""SAME WALL v2 - "Who's still building on Day 365?" One night scene, three builders, 23.5 s.

Every character has a turn:
  MOTIVATION builds, sits on his phone ("I'LL FINISH IT MONDAY."), jumps up every "MONDAY!", builds fast, kicks it
  down, sits again - his counter goes 8 -> 48 -> 0 -> 36 -> 0.
  OBSESSION looks like the winner: three times faster, the camera drifts to him, "+N AHEAD" - his crooked wall
  collapses around day 225.
  DISCIPLINE looks like the loser: smallest pile on screen, falls to his knees in the rain, gets up, lays ONE brick.
Day 365: he climbs it. It was never a wall - fog rolls in below, the moon behind him. IT WAS NEVER A WALL. / IT WAS A WAY UP.

    python3 stick/wall.py --stills          # 4 frames -> stick/versus/wall-stills.png
    python3 stick/wall.py stick/wall.mp4
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
import ai_job as AJ  # noqa
import hq  # noqa
import compare as C  # noqa
from compare import ell, line, rrect, poly, figure, place, ik, FLOOR, K, W, H  # noqa
from perfect_wave import clamp, env, font, lerp, lerp_pose, mix_in, noise, prog, smooth, tone, write_wav  # noqa

FPS, SR = 30, 44100
DUR = 23.5
NF = int(round(DUR * FPS))
SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
MDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "study", "music")
STAND = PW.STAND
T365 = 18.5
T_COLLAPSE = 16.6
T_RH = 10.0                        # mid re-hook: obsession's wall wobbles
T_KNEEL = 8.1
T_CLIMB = 18.8
STEP_DT = 0.34
T_LINES = 20.8
BW, BH = 34, 17
COLS = 4
LX = [215, 575, 905]               # label / counter x
FIG_X = [130, 382, 785]
MOT_X0 = 170                        # motivation's wall
OBS_X0 = 905 - COLS * BW / 2
ST_X0, ST_N, ST_W, ST_R = 420, 5, 68, 4      # discipline's stair: 5 steps, 2 bricks wide, 4 rows high
LABELS = ["MOTIVATION", "DISCIPLINE", "OBSESSION"]
ORANGE = (255, 140, 40)
GOLD = (246, 200, 90)
BRICK = (170, 82, 60)
BOUT = (60, 30, 22, 255)


def day(t):
    if t >= T365:
        return 365
    return max(1, int(round(1 + 364 * ((t / T365) ** 1.35))))


# ---------------------------------------------------------------- motivation's on/off story
SITS = [(2.6, 5.3), (7.5, 11.7), (13.5, 99)]
BUILDS = [(0.0, 2.6, 3.3), (5.6, 7.0, 5.0), (12.0, 13.0, 5.0)]
KNOCKS = [(7.0, 48), (13.0, 36)]


def mot_sit(t):
    return max(smooth(prog(t, a, a + 0.4)) * (1 - smooth(prog(t, b - 0.3, b))) for a, b in SITS)


def mot_bricks(t):
    if t < 2.6:
        return min(8, int(t / 0.3) + 1)
    if t < 5.6:
        return 8
    if t < 7.0:
        return 8 + int(40 * (t - 5.6) / 1.4)
    if t < 12.0:
        return 0
    if t < 13.0:
        return int(36 * (t - 12.0) / 1.0)
    return 0


def building(i, t):
    """brick-laying rate right now, 0 if not laying"""
    if i == 0:
        for a, b, r in BUILDS:
            if a <= t < b:
                return r
        return 0
    if i == 1:
        return 0 if T_KNEEL <= t < T_KNEEL + 1.5 or t >= T365 else 1.7
    return 4.2 if t < T_COLLAPSE else 0


def bricks(i, t):
    d = day(t)
    if i == 0:
        return mot_bricks(t)
    if i == 1:
        return d * 10
    return int(day(min(t, T_COLLAPSE - 0.01)) * 30)


def wobble(t):
    u = t - T_RH
    return 0.0 if not 0 <= u < 1.4 else 0.035 * math.sin(u * 22) * (1 - u / 1.4)


def lean(t):
    return wobble(t) +  0.0 if t < 3 else min(0.30, 0.02 + 0.28 * ((t - 3) / (T_COLLAPSE - 3)) ** 2)


# ---------------------------------------------------------------- bricks
def brick(d, x, y, col=BRICK, rot=0.0):
    if abs(rot) < 1e-3:
        rrect(d, (x + 1, y + 1, x + BW - 1, y + BH - 1), 2, col + (255,), outline=BOUT, w=1.5)
        return
    c_, s_ = math.cos(rot), math.sin(rot)
    pts = [(-BW / 2, -BH / 2), (BW / 2, -BH / 2), (BW / 2, BH / 2), (-BW / 2, BH / 2)]
    poly(d, [(x + BW / 2 + px * c_ - py * s_, y + BH / 2 + px * s_ + py * c_) for px, py in pts], col + (255,),
         outline=BOUT, w=1.5)


def shade(rng):
    return tuple(int(v * (0.85 + 0.25 * rng.uniform())) for v in BRICK)


def stack(d, x0, n, seed, ang=0.0, jitter=0.0):
    """n bricks laid in rows of COLS from x0; returns top y"""
    rng = np.random.default_rng(seed)
    rows = math.ceil(n / COLS)
    for r in range(rows):
        nb = min(COLS, n - r * COLS)
        for c in range(nb):
            bx = x0 + c * BW + (BW / 2 if r % 2 else 0) - (BW / 2 if r % 2 and c == COLS - 1 else 0)
            by = FLOOR - (r + 1) * BH
            jx, jy = rng.uniform(-jitter, jitter), rng.uniform(-jitter / 2, jitter / 2)
            brick(d, bx + (FLOOR - by) * math.sin(ang) + jx, by + jy, shade(rng))
    return FLOOR - rows * BH


def scatter(d, x0, n, u, seed, ang=0.0, side=1, fast=1.0):
    """a stack of n bricks falling apart; u = seconds since it went. bricks settle on the floor."""
    rng = np.random.default_rng(seed)
    rows = math.ceil(n / COLS)
    for r in range(rows):
        for c in range(min(COLS, n - r * COLS)):
            h = (r + 1) * BH
            bx = x0 + c * BW + h * math.sin(ang)
            by = FLOOR - h
            v = max(0.0, u - (rows - r) * 0.012)
            vx = rng.uniform(40, 220) * fast * side
            ground = FLOOR - BH - rng.uniform(0, 26)
            tl = math.sqrt(max(0.0, ground - by) / 900) if ground > by else 0.0
            vv = min(v, tl + 0.25)
            nx = bx + vx * min(vv, tl + 0.25)
            ny = min(ground, by + 900 * vv * vv)
            rot = rng.uniform(-3, 3) * min(vv, tl)
            brick(d, nx, ny, shade(rng), rot)


def stair_fill(t):
    return min(1.0, (day(t) / 365) ** 0.8) * ST_N * ST_R


def stair(d, t):
    """discipline's build: looks like a wall, steps only show late. returns top y of the growing part"""
    F = stair_fill(t)
    rng = np.random.default_rng(5)
    top = FLOOR
    for c in range(ST_N):
        hc = min((c + 1) * ST_R, F)
        full = int(hc)
        part = hc - full
        for r in range(full + 1):
            nb = 4 if r < full else int(round(part * 4))
            for k in range(nb):
                off = BW / 2 if r % 2 else 0
                bx = ST_X0 + c * ST_W + (k % 2) * BW + (off if k % 2 == 0 else -off) * 0
                brick(d, bx, FLOOR - (r + 1) * BH, shade(rng)) if k < 2 else None
        top = min(top, FLOOR - hc * BH)
    return top


def step_top(c):
    return (ST_X0 + c * ST_W + ST_W / 2, FLOOR - (c + 1) * ST_R * BH)


# ---------------------------------------------------------------- figures
SIT_PHONE = {"head": (4, -134), "neck": (0, -96), "el": (26, -56), "hl": (46, -78), "er": (22, -52), "hr": (42, -74),
             "kl": (52, -38), "fl": (104, -2), "kr": (46, -32), "fr": (100, 2)}
KNEEL = {"head": (30, -120), "neck": (20, -84), "el": (30, -40), "hl": (40, 4), "er": (24, -36), "hr": (34, 8),
         "kl": (40, 6), "fl": (-10, 60), "kr": (-20, 54), "fr": (-70, 60)}
S = 0.95


def lay(stage, d, i, t, x, rate, tx, ty, scarf=False, glow=False):
    ph = (t * rate) % 1.0
    lift = math.sin(math.pi * ph)
    hand = (lerp(x + 40, tx, ph), lerp(FLOOR - 70, ty - 8, lift))
    pose = dict(STAND, head=(10 + 8 * lift, -150 - 6 * lift))
    pts = dict(place(pose, (x, FLOOR - 113 * S), 1, S))
    for side, dy in (("r", 0), ("l", 12)):
        tgt = (hand[0] - (6 if side == "l" else 0), hand[1] + dy)
        pts["h" + side] = tgt
        pts["e" + side] = ik(pts["neck"], tgt, 42 * S, 40 * S, 1)
    figure(stage, pts, S, light=(0.4, -0.9), scarf=scarf, back=-1)
    brick(d, hand[0] - BW / 2, hand[1] - BH)
    if glow:
        for side in ("hl", "hr"):
            ell(d, *pts[side], 14, 14, ORANGE + (90,))
    return pts


def pile(d, x):
    for j in range(3):
        brick(d, x - 70 + j * 18, FLOOR - BH * (j + 1))


def motivation(stage, d, t, top):
    x = FIG_X[0]
    k = mot_sit(t)
    r = building(0, t)
    pile(d, x)
    if k > 0.001:
        pose = lerp_pose(STAND, SIT_PHONE, k)
        pts = place(pose, (x - 20 * k, lerp(FLOOR - 113 * S, FLOOR - 12 * S, k)), 1, S)
        figure(stage, pts, S, light=(0.4, -0.9))
        if k > 0.6:
            hx, hy = pts["hr"]
            rrect(d, (hx - 7, hy - 22, hx + 9, hy + 4), 3, (18, 18, 24, 255))
            rrect(d, (hx - 5, hy - 19, hx + 7, hy + 1), 2, (150, 190, 255, 255))
        return
    if r:
        lay(stage, d, 0, t, x, r, MOT_X0 + 30, max(top, FLOOR - 250))
        return
    # standing: the kick that knocks it down
    kick = 0.0
    for t0, _ in KNOCKS:
        kick = max(kick, math.sin(math.pi * clamp((t - t0 + 0.05) / 0.35)))
    pose = dict(STAND, fr=(13 + 60 * kick, 113 - 50 * kick), kr=(9 + 40 * kick, 56 - 30 * kick))
    figure(stage, place(pose, (x, FLOOR - 113 * S), 1, S), S, light=(0.4, -0.9))


def discipline(stage, d, t, top):
    x = FIG_X[1]
    if t >= T_CLIMB:
        u = (t - T_CLIMB) / STEP_DT
        pts_path = [(x, FLOOR)] + [step_top(c) for c in range(ST_N)]
        j = min(int(u), ST_N - 1)
        f = clamp(u - j) if u < ST_N else 1.0
        if u >= ST_N:
            j, f = ST_N - 1, 1.0
        (x0, y0), (x1, y1) = pts_path[j], pts_path[j + 1]
        fx = lerp(x0, x1 - 10, smooth(f))
        fy = lerp(y0, y1, smooth(min(1, f * 1.6))) - 14 * math.sin(math.pi * f)
        sw = math.sin(math.pi * f) if u < ST_N else 0.0
        pose = dict(STAND, fr=(13 + 26 * sw, 113 - 46 * sw), kr=(16 + 20 * sw, 50 - 24 * sw),
                    hl=(-24, -10), hr=(24, -10))
        if u >= ST_N + 0.6:   # looks up at the moon
            pose = dict(pose, head=(10, -152))
        figure(stage, place(pose, (fx, fy - 113 * S), 1, S), S, light=(0.4, -0.9), scarf=True)
        return
    if T_KNEEL <= t < T_KNEEL + 1.5:
        k = smooth(prog(t, T_KNEEL, T_KNEEL + 0.35)) * (1 - smooth(prog(t, T_KNEEL + 1.0, T_KNEEL + 1.5)))
        pose = lerp_pose(STAND, KNEEL, k)
        figure(stage, place(pose, (x, lerp(FLOOR - 113 * S, FLOOR - 62 * S, k)), 1, S), S, light=(0.4, -0.9),
               scarf=True)
        pile(d, x)
        return
    if t >= T365:
        figure(stage, place(STAND, (x, FLOOR - 113 * S), 1, S), S, light=(0.4, -0.9), scarf=True)
        return
    lay(stage, d, 1, t, x, 1.7, ST_X0 + 34, max(top, FLOOR - 250), scarf=True)
    pile(d, x)


def obsession(stage, d, t):
    x = FIG_X[2]
    if t >= T_COLLAPSE:
        k = smooth(prog(t, T_COLLAPSE + 0.4, T_COLLAPSE + 1.0))
        pose = lerp_pose(STAND, KNEEL, k)
        figure(stage, place(pose, (x, lerp(FLOOR - 113 * S, FLOOR - 62 * S, k)), 1, S), S, light=(0.4, -0.9))
        return
    rows = min(40, 2 + 44 * (day(t) / 365) ** 0.6)
    lay(stage, d, 2, t, x, 4.2, OBS_X0 + 30, max(FLOOR - rows * BH, FLOOR - 260), glow=True)
    pile(d, x)


def weather(d, t):
    dd = day(t)
    rain = smooth(clamp((dd - 80) / 15)) * (1 - smooth(clamp((dd - 150) / 15)))
    snow = smooth(clamp((dd - 245) / 15)) * (1 - smooth(clamp((dd - 330) / 15)))
    rng = np.random.default_rng(4)
    if rain > 0.01:
        for _ in range(170):
            x0, sp = rng.uniform(-60, W + 60), rng.uniform(1.0, 1.4)
            y = ((t * sp * 1.6 + rng.uniform(0, 1)) % 1.0) * (FLOOR + 60) - 40
            line(d, [(x0 - 0.15 * y, y), (x0 - 0.15 * y - 6, y + 34)], (150, 170, 210, int(150 * rain)), 1.6)
    if snow > 0.01:
        for _ in range(140):
            x0, sp, ph = rng.uniform(-40, W + 40), rng.uniform(0.08, 0.16), rng.uniform(0, 1)
            y = ((t * sp + ph) % 1.0) * (FLOOR + 40) - 20
            r = rng.uniform(2, 4.2)
            ell(d, x0 + 18 * math.sin(t * 0.8 + ph * 6), y, r, r, (236, 240, 250, int(220 * snow)))


_FOG = {}


def moon(rv):
    if "m" not in _FOG:
        im = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        mx, my, r = 800 * K, 700 * K, 58 * K
        d.ellipse((mx - 3 * r, my - 3 * r, mx + 3 * r, my + 3 * r), (150, 170, 230, 40))
        d.ellipse((mx - 1.6 * r, my - 1.6 * r, mx + 1.6 * r, my + 1.6 * r), (200, 210, 240, 70))
        im = im.filter(ImageFilter.GaussianBlur(40 * K))
        d = ImageDraw.Draw(im)
        d.ellipse((mx - r, my - r, mx + r, my + r), (240, 238, 226, 255))
        _FOG["m"] = im
    m = _FOG["m"].copy()
    m.putalpha(Image.fromarray((np.asarray(m.split()[3], np.float32) * rv).astype(np.uint8)))
    return m


def fog_band():
    if "f" not in _FOG:
        h = 1100
        im = Image.new("RGBA", (W, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        rng = np.random.default_rng(12)
        for _ in range(45):
            x, y = rng.uniform(-100, W + 100), rng.uniform(260, 400)
            r = rng.uniform(80, 220)
            d.ellipse((x - r, y - r * 0.55, x + r, y + r * 0.55), (84, 94, 132, 235))
        for yy in range(400, h):
            k = (yy - 400) / (h - 400)
            d.line((0, yy, W, yy), (int(lerp(70, 10, k)), int(lerp(80, 12, k)), int(lerp(115, 24, k)), 240))
        _FOG["f"] = im.filter(ImageFilter.GaussianBlur(22)).resize((W * K, h * K), Image.BILINEAR)
    return _FOG["f"]


def reveal(t):
    return smooth(prog(t, T_CLIMB + 0.2, T_CLIMB + ST_N * STEP_DT + 0.4))


def frame(t):
    stage = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(stage)
    # motivation's wall + the debris of every time he kicked it down
    for t0, n in KNOCKS:
        if t >= t0:
            scatter(d, MOT_X0, n, t - t0, seed=int(t0 * 10), side=1, fast=0.5)
    mtop = stack(d, MOT_X0, mot_bricks(t), 2) if mot_bricks(t) else FLOOR
    stop = stair(d, t)
    if t < T_COLLAPSE:
        rows = min(40, 2 + 44 * (day(t) / 365) ** 0.6)
        stack(d, OBS_X0, int(rows * COLS), 3, ang=lean(t), jitter=6)
    else:
        scatter(d, OBS_X0, int(min(40, 2 + 44 * (day(T_COLLAPSE) / 365) ** 0.6) * COLS), t - T_COLLAPSE, 9,
                ang=lean(T_COLLAPSE))
        u = t - T_COLLAPSE
        if u < 1.2:
            rng = np.random.default_rng(9)
            for _ in range(20):
                a = rng.uniform(0, 6.28)
                rr = 40 + 260 * u
                ell(d, 965 + rr * math.cos(a), FLOOR - 40 + rr * 0.3 * math.sin(a), 18 + 30 * u, 12 + 20 * u,
                    (150, 140, 130, int(150 * (1 - u / 1.2))))
    if T_RH + 0.15 <= t < T_RH + 2.5:
        rows = min(40, 2 + 44 * (day(T_RH) / 365) ** 0.6)
        h = rows * BH
        rng = np.random.default_rng(21)
        for j in range(6):
            v = max(0.0, t - T_RH - 0.15 - j * 0.06)
            y0 = FLOOR - h - BH
            ground = FLOOR - BH
            tl = math.sqrt((ground - y0) / 900)
            vv = min(v, tl)
            brick(d, OBS_X0 + 20 + j * 18 + h * math.sin(lean(T_RH)) + 60 * vv, y0 + 900 * vv * vv, shade(rng),
                  rng.uniform(-4, 4) * vv)
    motivation(stage, d, t, mtop)
    obsession(stage, d, t)
    discipline(stage, d, t, stop)
    import race
    race.bubble(stage, t, 3.2, 5.2, "I'LL FINISH IT MONDAY.", FIG_X[0] + 150, FLOOR - 230, size=26)
    race.bubble(stage, t, 5.3, 6.4, "MONDAY!", FIG_X[0] + 40, FLOOR - 290, size=30)
    race.bubble(stage, t, 11.7, 12.8, "THIS TIME FOR REAL.", FIG_X[0] + 130, FLOOR - 290, size=26)
    weather(d, t)
    spots = ((LX[0], 0.7), (LX[1], 1.0), (LX[2], 0.8))
    base = C.stage_bg(spots).copy()
    rv = reveal(t)
    if rv > 0:   # the moon behind him
        base.alpha_composite(moon(rv))
    C.dust(ImageDraw.Draw(base), t, spots, seed=1, n=30)
    tp = stage.crop((0, 0, W * K, FLOOR * K))
    refl = tp.transpose(Image.FLIP_TOP_BOTTOM).crop((0, 0, W * K, (H - FLOOR) * K))
    refl = refl.resize((W * K // 4, (H - FLOOR) * K // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
    refl = refl.resize((W * K, (H - FLOOR) * K), Image.BILINEAR)
    fade = np.linspace(0.3, 0.0, (H - FLOOR) * K, dtype=np.float32)[:, None]
    refl.putalpha(Image.fromarray((np.asarray(refl.split()[3], np.float32) * fade).astype(np.uint8)))
    base.alpha_composite(refl, (0, FLOOR * K))
    base.alpha_composite(stage)
    if rv > 0:   # fog rolls in below him
        fb = fog_band()
        y = int((FLOOR - 140 - 360 * rv) * K)
        f = fb.copy()
        f.putalpha(Image.fromarray((np.asarray(f.split()[3], np.float32) * rv).astype(np.uint8)))
        base.alpha_composite(f.crop((0, 0, W * K, min(fb.size[1], H * K - y))), (0, y))
        # re-draw him on top of the fog
        top = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
        discipline(top, ImageDraw.Draw(top), t, stop)
        base.alpha_composite(top)
    # camera: default; drifts to obsession while he's "winning"; rises with discipline at the end
    z, cx, cy = 1.08, W / 2, 1080.0
    fo = smooth(prog(t, 3.0, 9.0)) * (1 - smooth(prog(t, T_COLLAPSE + 0.6, T_COLLAPSE + 2.0)))
    z, cx, cy = z + 0.03 * fo, cx, cy - 40 * fo
    z, cx, cy = lerp(z, 1.5, rv), lerp(cx, 660, rv), lerp(cy, 880, rv)
    sh = 14 * (1 - (t - T_COLLAPSE) / 0.5) if T_COLLAPSE <= t < T_COLLAPSE + 0.5 else 0.0
    im = hq.camera(base, z, (z * (W / 2 - cx) + sh * math.sin(t * 90)) * K,
                   (z * (H / 2 - cy) + sh * 0.6 * math.cos(t * 77)) * K)
    im = im.resize((W, H), Image.LANCZOS)
    header(im, t, stop, z, cx, cy)
    return np.asarray(im.convert("RGB"))


def header(im, t, stop, z, cx, cy):
    d = ImageDraw.Draw(im)
    hide = 1 - smooth(prog(t, T_CLIMB, T_CLIMB + 0.6))
    if hide > 0:
        a = int(255 * hide)
        PW.spaced(d, W / 2, 34, "WHO'S STILL BUILDING ON DAY 365?", font("InterDisplay-Bold.otf", 44),
                  (236, 238, 246, a), 3)
        PW.spaced(d, W / 2, 150, f"DAY {day(t)}", font("InterDisplay-Bold.otf", 110), (246, 246, 250, a), 6)
        lead = bricks(2, t) - bricks(1, t)
        for i in range(3):
            n = bricks(i, t)
            dead = i == 2 and t >= T_COLLAPSE
            col = (128, 136, 160) if i == 0 else (GOLD if i == 1 and t >= T365 else
                                                  ((236, 120, 90) if dead else (236, 238, 246)))
            PW.spaced(d, LX[i], 300, LABELS[i], font("Inter-SemiBold.otf", 24),
                      (ORANGE if i == 2 else (214, 220, 238)) + (a,), 6)
            PW.spaced(d, LX[i], 334, "0" if dead else f"{n:,}", font("InterDisplay-Bold.otf", 52), col + (a,), 2)
            PW.spaced(d, LX[i], 396, "FELL" if dead else "BRICKS", font("Inter-SemiBold.otf", 18),
                      (128, 136, 160, a), 5)
            if i == 2 and 2.0 < t < T_COLLAPSE and lead > 0:
                PW.spaced(d, LX[i], 426, f"+{lead:,} AHEAD", font("InterDisplay-Bold.otf", 26), ORANGE + (a,), 3)
    if T_KNEEL + 1.1 <= t < T_KNEEL + 2.2:   # the one brick he lays after falling
        u = t - T_KNEEL - 1.1
        a = 1 - smooth(prog(u, 0.7, 1.1))
        sx = (ST_X0 + 40 - cx) * z + W / 2
        sy = (stop - 30 - 60 * u - cy) * z + H / 2
        PW.spaced(d, sx, sy, "+1", font("InterDisplay-Bold.otf", 54), GOLD + (int(255 * a),), 0)
    a = hq.pop(t, T_RH + 0.2, 0.3) * (1 - smooth(prog(t, T_RH + 2.3, T_RH + 2.7))) if t >= T_RH + 0.2 else 0
    if a > 0:
        fr = font(SERIF_B, 54)
        for j, s_ in enumerate(("ONE OF THESE WALLS", "WON'T MAKE IT TO DAY 365.")):
            PW.spaced(d, W / 2, 560 + j * 68, s_, fr, ((246, 240, 226) if j == 0 else ORANGE) + (int(255 * min(1, a)),), 4)
    f = font(SERIF_B, 62)
    for j, s in enumerate(("IT WAS NEVER A WALL.", "IT WAS A WAY UP.")):
        a = smooth(prog(t, T_LINES + 0.8 * j, T_LINES + 0.8 * j + 0.4))
        if a > 0:
            PW.spaced(d, W / 2, 120 + j * 80, s, f, (246, 240, 226, int(255 * a)), 5)


def render(i):
    return frame(i / FPS).tobytes()


def audio():
    n = int(DUR * SR)
    out = np.zeros((n, 2))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(max(0.0, MUSIC_HIT - T365)), "-t", str(DUR), "-i",
                          os.path.join(MDIR, MUSIC_FILE), "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True).stdout
    m = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    out[:min(n, len(m))] += m[:n] * np.minimum(1, np.arange(min(n, len(m))) / (0.15 * SR))[:, None]
    tt = np.arange(n) / SR
    out *= np.clip((DUR - tt) / 0.8, 0.0, 1)[:, None]
    for i in range(3):
        for f in range(int(DUR * 100)):
            t0, t1 = f / 100, (f + 1) / 100
            r = building(i, t0)
            if r and math.floor(t0 * r - 0.98) != math.floor(t1 * r - 0.98):
                mix_in(out, tone(320 - 40 * i, 0.08, (1, 2.1), a=0.001, d=0.03) * 0.8, t1, 0.04, (i - 1) * 0.5)
    mix_in(out, tone(520, 0.5, (1, 2, 3), a=0.002, d=0.35), T_KNEEL + 1.15, 0.12, 0.0)
    mix_in(out, noise(1.4, 5, lo=60, hi=2500)[:int(1.4 * SR)] * env(int(1.4 * SR), 0.005, 0.5), T_COLLAPSE, 0.35, 0.5)
    for t0, _ in KNOCKS:
        mix_in(out, noise(0.6, 6, lo=80, hi=2500)[:int(0.6 * SR)] * env(int(0.6 * SR), 0.005, 0.3), t0, 0.15, -0.6)
    for j in range(10):
        mix_in(out, tone(260 + 30 * j, 0.06, (1, 2.1), a=0.001, d=0.02), T_COLLAPSE + 0.2 + j * 0.07, 0.05, 0.5)
    for j in range(ST_N):
        mix_in(out, tone(180, 0.1, (1, 2), a=0.002, d=0.06), T_CLIMB + (j + 0.9) * STEP_DT, 0.08, 0.0)
    for j in range(5):
        mix_in(out, tone(90 - 6 * j, 0.25, (1, 2.3, 3.1), a=0.01, d=0.2), T_RH + j * 0.14, 0.18, 0.5)
    for j in range(6):
        mix_in(out, tone(300 + 25 * j, 0.06, (1, 2.1), a=0.001, d=0.02), T_RH + 0.75 + j * 0.06, 0.06, 0.5)
    out /= max(1.0, np.abs(out).max() / 0.9)
    return out


MUSIC_FILE = "The Escalation.mp3"
MUSIC_HIT = 308.0


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    if "--stills" in sys.argv:
        ts = [float(a) for a in sys.argv[2:]] or [6.3, 8.6, 12.0, 22.3]
        sheet = Image.new("RGB", (360 * len(ts), 640))
        for j, t in enumerate(ts):
            sheet.paste(Image.fromarray(frame(t)).resize((360, 640), Image.LANCZOS), (j * 360, 0))
        p = os.path.join(here, "versus", "wall-stills.png")
        sheet.save(p)
        print(p)
        return
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "wall.mp4")
    wav = out + ".wav"
    write_wav(wav, audio())
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                          "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100",
                          "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                         stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for b in pool.imap(render, range(NF), chunksize=2):
            p.stdin.write(b)
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print(out)
    print(f'Credit: Music: "{MUSIC_FILE[:-4]}" by Kevin MacLeod (incompetech.com), CC BY 4.0')


if __name__ == "__main__":
    main()
