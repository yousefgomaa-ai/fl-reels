#!/usr/bin/env python3
"""LAZY vs EGO vs WORKER - one screen, three people, one chance each. Then the flashback: why.
Situation 1: the penalty kick.  (hoop + pull-up come next; each is its own video first.)
Real motion capture (CMU) for every movement. Stadium-at-night look (as in the track race).

    python3 stick/drill.py penalty --stills [t ...]
    python3 stick/drill.py penalty stick/drill/penalty.mp4
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
from perfect_wave import clamp, env, font, lerp, mix_in, noise, prog, smooth, tone, write_wav  # noqa
from money_chars import face, outfit, S, GOLD  # noqa
from money import put, track, text  # noqa
from tryagain2 import Seq, seg, clip, blend  # noqa
from tryagain import ball  # noqa

FPS, SR = 30, 44100
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
STAND = PW.STAND
WALK, KICK, HAPPY, UPSET, LAUGH, RUN = "007/07_01", "010/10_01", "079/79_69", "079/79_74", "079/79_70", "009/09_01"
KICK_T, KICK_FOOT = 4.99, "fr"
FREE, FREE_T = "124/124_04", 4.45
SIT = next((a for a in sys.argv[1:] if a in ("penalty", "hoop", "pullup")), "penalty")
SPEED = 1.25        # the final video plays this much faster
COMBO = os.environ.get("DRILL_COMBO")            # "WHO:k" when rendering a piece of the combined video
CHALLENGE = {"penalty": 1, "hoop": 2, "pullup": 3}
WHO = ["LAZY", "EGO", "WORKER"]
COL = {"LAZY": (120, 128, 140), "EGO": (140, 80, 200), "WORKER": None}
SCARF = (214, 44, 44)
GREEN = (90, 200, 110)
RED = (226, 70, 60)
SC = S

# ---------------------------------------------------------------- timeline
T_INTRO = 1.4
FB_LEN = 1.4
TURN, FB_AT = {}, {}
_t = T_INTRO
for _w, _d in ((("LAZY", 3.4), ("EGO", 3.4), ("WORKER", 4.2)) if SIT == "pullup" else (("LAZY", 3.5), ("EGO", 3.3), ("WORKER", 3.2))):
    TURN[_w] = (_t, _d)
    FB_AT[_w] = _t + _d            # the flashback right after his kick
    _t += _d + FB_LEN
T_LINE = _t
DUR = T_LINE + 2.2
NF = int(round(DUR * FPS))

# ---------------------------------------------------------------- the pitch
GX, GH = 680, 270                  # goal post x, crossbar height
SPOT = 430                         # the ball
WAIT = {0: (290, 0.8), 1: (350, 0.8)}
CAM = (1.55, 595, FLOOR - 316)


def to_scr(x, y):
    z, cx, cy = CAM
    return W / 2 + (x - cx) * z, H / 2 + (y - cy) * z


_B = {}
_tb = np.zeros((H, W, 4), np.uint8)
_tb[..., 3] = (np.clip(1 - np.arange(H) / 300.0, 0, 1) ** 1.2 * 235).astype(np.uint8)[:, None]
_tb[..., :3] = (6, 7, 12)
TOPBAND = Image.fromarray(_tb, "RGBA")


def stadium():
    if "bg" in _B:
        return _B["bg"]
    im = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    for j in range(60):
        k = j / 59
        y0, y1 = j * (FLOOR - 120) / 60, (j + 1) * (FLOOR - 120) / 60
        d.rectangle((0, y0 * K, W * K, y1 * K + 1), (int(lerp(6, 20, k)), int(lerp(8, 24, k)), int(lerp(16, 40, k)), 255))
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for x in (60, 400, 740, 1080):
        gd.ellipse(((x - 220) * K, 440 * K, (x + 220) * K, 800 * K), (200, 220, 255, 70))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(50 * K)))
    rng = np.random.default_rng(3)
    for row in range(8):     # crowd
        y = FLOOR - 470 + row * 40
        d.rectangle((0, (y + 12) * K, W * K, (y + 40) * K), (22 + row * 2, 24 + row * 2, 32 + row * 2, 255))
        for x in np.arange(-10, W + 20, 22):
            sh = int(30 + row * 5 + rng.uniform(-8, 10))
            xx = x + rng.uniform(-5, 5) + (11 if row % 2 else 0)
            ell(d, xx, y, 9, 10, (sh, sh, sh + 8, 255))
            if rng.uniform() < 0.04:
                ell(d, xx, y - 4, 3, 3, (255, 250, 230, 255))
    d.rectangle((0, (FLOOR - 150) * K, W * K, (FLOOR - 120) * K), (34, 54, 110, 255))   # advertising board
    for j in range(12):     # grass stripes / court planks
        y0, y1 = FLOOR - 120 + j * 60, FLOOR - 60 + j * 60
        if SIT == "hoop":
            col = (168, 112, 66) if j % 2 else (178, 120, 72)
        elif SIT == "pullup":
            col = (54, 56, 64) if j % 2 else (60, 62, 70)
        else:
            col = (36, 92, 48) if j % 2 else (42, 104, 54)
        d.rectangle((0, y0 * K, W * K, y1 * K), col + (255,))
    line(d, [(-10, FLOOR + 30), (W + 10, FLOOR + 30)], (230, 236, 230, 200), 4)
    _B["bg"] = im
    return im


# 3/4 view: the mouth faces the shooter. near post is closer to us (lower on screen), far post further (higher).
def _goal_pts(bulge=0.0):
    nb, fb = (GX, FLOOR + 22), (GX + 95, FLOOR - 32)                 # post bottoms (near, far)
    nt, ft = (nb[0], nb[1] - GH), (fb[0], fb[1] - GH * 0.86)         # post tops
    D = (150, 6)                                                    # depth vector (into the net)
    bulge_dx = 40 * bulge
    nbb, fbb = (nb[0] + D[0] + bulge_dx, nb[1] + D[1]), (fb[0] + D[0] + bulge_dx, fb[1] + D[1])
    ntb, ftb = (nt[0] + D[0] * 0.8 + bulge_dx, nt[1] + 40), (ft[0] + D[0] * 0.8 + bulge_dx, ft[1] + 36)
    return nb, fb, nt, ft, nbb, fbb, ntb, ftb


def _mesh(d, a, b, c, e, n1, n2, col):
    """grid on quad a-b-c-e (a->b one edge, e->c the opposite)"""
    for i in range(n1 + 1):
        u = i / n1
        p0 = (lerp(a[0], b[0], u), lerp(a[1], b[1], u))
        p1 = (lerp(e[0], c[0], u), lerp(e[1], c[1], u))
        line(d, [p0, p1], col, 1.6)
    for j in range(n2 + 1):
        v = j / n2
        p0 = (lerp(a[0], e[0], v), lerp(a[1], e[1], v))
        p1 = (lerp(b[0], c[0], v), lerp(b[1], c[1], v))
        line(d, [p0, p1], col, 1.6)


def _post(d, a, b, w=10):
    line(d, [a, b], (160, 162, 170, 255), w + 3)
    line(d, [a, b], (250, 250, 252, 255), w)
    line(d, [(a[0] - 2, a[1]), (b[0] - 2, b[1])], (255, 255, 255, 255), 3)


def goal_back(d, bulge=0.0):
    nb, fb, nt, ft, nbb, fbb, ntb, ftb = _goal_pts(bulge)
    poly(d, [nb, fb, fbb, nbb], (20, 60, 30, 120))                          # shadow on the grass
    net = (232, 236, 240, 150)
    _mesh(d, fb, ft, ftb, fbb, 8, 6, net)            # far side net
    _mesh(d, fbb, ftb, ntb, nbb, 8, 9, net)          # back net
    _mesh(d, ft, nt, ntb, ftb, 9, 6, net)            # roof net
    line(d, [fbb, ftb], (200, 202, 210, 255), 4)     # back stanchions
    line(d, [ftb, ntb], (200, 202, 210, 255), 4)
    line(d, [nbb, fbb], (200, 202, 210, 255), 3)
    _post(d, fb, ft, 9)                               # far post


def goal_front(d, bulge=0.0):
    nb, fb, nt, ft, nbb, fbb, ntb, ftb = _goal_pts(bulge)
    _mesh(d, nb, nt, ntb, nbb, 8, 6, (232, 236, 240, 110))   # near side net
    line(d, [nbb, ntb], (200, 202, 210, 255), 4)
    _post(d, nt, ft, 10)                              # crossbar
    _post(d, nb, nt, 11)                              # near post


def mouth(a, h):
    """a point in the goal mouth: a 0 near..1 far post, h 0 ground..1 crossbar"""
    nb, fb, nt, ft, *_ = _goal_pts()
    bx, by = lerp(nb[0], fb[0], a), lerp(nb[1], fb[1], a)
    tx, ty = lerp(nt[0], ft[0], a), lerp(nt[1], ft[1], a)
    return lerp(bx, tx, h), lerp(by, ty, h)


def goal(d, bulge=0.0):
    goal_back(d, bulge)
    goal_front(d, bulge)


# ---------------------------------------------------------------- the three
def dress(st, p, who, expr, t, sc):
    figure(st, p, sc, light=(0.4, -0.9))
    d = ImageDraw.Draw(st)
    f = 1 if p["head"][0] >= p["neck"][0] else -1
    if COL[who]:
        outfit(d, p, COL[who], f, legs=False)
    face(d, p, expr, f, t)
    hx, hy = p["head"]
    if who == "EGO":
        rrect(d, (hx - (34 if f < 0 else 4), hy - 10, hx + (4 if f < 0 else 34), hy + 2), 4, (12, 12, 16, 255))
    if who == "LAZY":
        line(d, [(hx - 20, hy - 30), (hx + 22, hy - 34)], (90, 96, 108, 255), 10)    # beanie
    if who == "WORKER":
        nx, ny = p["neck"]
        ell(d, nx, ny + 2, 21 * sc / S, 11 * sc / S, SCARF + (255,))
        poly(d, [(nx, ny), (nx - f * 44 * sc / S, ny + 26 * sc / S), (nx - f * 30 * sc / S, ny + 40 * sc / S)], SCARF + (255,))


def kick_seq(who):
    if who == "LAZY":
        segs = [seg(WALK, 0.3, 1.0, 1.0), seg(KICK, 4.1, 5.4, 1.9)]
    elif who == "EGO":
        segs = [seg(HAPPY, 0.3, 1.6, 1.1, lock=0), seg(KICK, 4.1, 5.4, 0.9)]
    else:
        segs = [seg(KICK, 4.1, 5.4, 0.9)]
    probe = Seq(segs, 0)
    tk = probe.starts[-1] + segs[-1]["dur"] * (KICK_T - 4.1) / 1.3
    fx = probe.pts(tk)[KICK_FOOT][0]
    return Seq(segs, SPOT - 28 - fx), tk


HOOP_X, RIM_Y = 700, FLOOR - 430
BALL_COL = (230, 120, 40) if SIT == "hoop" else (245, 245, 245)
SHOOT_X = 420


def hoop(d, sway=0.0):
    line(d, [(820, FLOOR), (820, FLOOR - 470)], (90, 94, 104, 255), 14)
    line(d, [(820, FLOOR - 470), (790, FLOOR - 470)], (90, 94, 104, 255), 10)
    rrect(d, (774, FLOOR - 560, 792, FLOOR - 370), 3, (236, 238, 244, 255), outline=(140, 144, 156, 255), w=2)
    rrect(d, (777, RIM_Y - 70, 789, RIM_Y), 2, (220, 60, 50, 255))
    for j in range(7):
        x0 = HOOP_X - 50 + j * 100 / 6
        x1 = HOOP_X - 28 + j * 56 / 6 + 8 * sway * math.sin(j * 2.1)
        line(d, [(x0, RIM_Y), (x1, RIM_Y + 82 + 10 * sway)], (240, 240, 244, 210), 2)
    for k in range(1, 4):
        y = RIM_Y + 20 * k
        line(d, [(HOOP_X - 50 + 6 * k, y), (HOOP_X + 50 - 6 * k, y)], (240, 240, 244, 170), 2)
    d.ellipse(((HOOP_X - 52) * K, (RIM_Y - 7) * K, (HOOP_X + 52) * K, (RIM_Y + 7) * K), outline=(236, 96, 40, 255), width=int(5 * K))
    line(d, [(HOOP_X + 52, RIM_Y), (776, RIM_Y)], (236, 96, 40, 255), 5)


def hand_mid(p):
    return ((p["hl"][0] + p["hr"][0]) / 2, (p["hl"][1] + p["hr"][1]) / 2)


def shot_seq(who):
    if who == "LAZY":
        segs = [seg(WALK, 0.3, 1.0, 0.9), seg(FREE, 3.6, 5.6, 2.3, lock=0)]
    elif who == "EGO":
        segs = [seg(HAPPY, 0.3, 1.6, 1.1, lock=0), seg(FREE, 3.6, 5.6, 1.3, lock=0)]
    else:
        segs = [seg(FREE, 3.6, 5.6, 1.3, lock=0)]
    probe = Seq(segs, 0)
    tk = probe.starts[-1] + segs[-1]["dur"] * (FREE_T - 3.6) / 2.0
    end = probe.pts(probe.dur - 1e-3)["hip"][0]
    return Seq(segs, SHOOT_X - end), tk


# ---------------------------------------------------------------- pull-ups
BAR_X, BAR_Y = 560, FLOOR - 470
GRAB0 = 0.85           # walked in, jumps up to the bar
REPS = {"LAZY": 0, "EGO": 2, "WORKER": 10}


def hang_pts(x, bar_y, up, sc, sway=0.0, kick=0.0, shake=0.0):
    """hands locked on the bar, body rising with `up` (0 dead hang .. 1 chin over the bar)"""
    neck = (x + shake, bar_y + lerp(78, 6, up) * sc / S)
    hip = (neck[0] + 4 * sc / S, neck[1] + 104 * sc / S)
    head = (neck[0] + 4 * sc / S, neck[1] - 44 * sc / S)
    p = {"neck": neck, "hip": hip, "head": head}
    for side, dx in (("l", -40), ("r", 40)):
        hand = (x + dx * sc / S, bar_y)
        p["h" + side] = hand
        p["e" + side] = ik(neck, hand, 42 * sc / S, 40 * sc / S, 1 if side == "r" else -1)
    k1 = 0.25 + 0.6 * kick
    for side, ph in (("l", 0.0), ("r", math.pi)):
        a = 0.08 * math.sin(ph) + kick * 0.9 * math.sin(kick * 6 + ph)
        kn = (hip[0] + 56 * sc / S * math.sin(a + 0.15), hip[1] + 56 * sc / S * math.cos(a + 0.15))
        ft = (kn[0] + 57 * sc / S * math.sin(a - k1), kn[1] + 57 * sc / S * math.cos(a - k1))
        p["k" + side], p["f" + side] = kn, ft
    if sway:
        c_, s_ = math.cos(sway), math.sin(sway)
        p = {j: (x + (px - x) * c_ - (py - bar_y) * s_, bar_y + (px - x) * s_ + (py - bar_y) * c_) for j, (px, py) in p.items()}
    return p


def reps_up(who, v):
    """(up 0..1, reps done, still hanging?)"""
    t = v - GRAB0 - 0.25
    if t < 0:
        return 0.0, 0, True
    if who == "LAZY":
        if t < 1.7:
            return 0.12 * abs(math.sin(t * 2.4)), 0, True
        return 0.0, 0, t < 1.9
    if who == "EGO":
        if t < 1.0:
            return 0.5 - 0.5 * math.cos(t / 0.5 * 2 * math.pi), int(t / 0.5 + 0.5), True
        if t < 1.8:
            return 0.35 * math.sin(math.pi * clamp((t - 1.0) / 0.8)), 2, True
        return 0.0, 2, t < 2.0
    per = 0.27
    n = min(10, int(t / per + 0.5))
    if t < 10 * per:
        return 0.5 - 0.5 * math.cos(t / per * 2 * math.pi), n, True
    return (1.0 if t < 10 * per + 0.5 else 0.0), 10, t < 10 * per + 0.6


def pull_pose(who, v):
    """walk in, grab, reps, drop"""
    walk = Seq([seg(WALK, 0.3, 1.1, GRAB0)], 0)
    end = walk.pts(GRAB0 - 1e-3)["hip"][0]
    walk = Seq([seg(WALK, 0.3, 1.1, GRAB0)], BAR_X - end)
    if v < GRAB0:
        return walk.pts(v)
    up, n, hanging = reps_up(who, v)
    t = v - GRAB0 - 0.25
    sway = 0.06 * math.sin(v * 3.1) + (0.12 * math.sin(t * 12) if who == "EGO" and 0 < t < 1.0 else 0)
    kick = 0.45 * clamp(1 - abs(t - 0.5) / 0.5) if who == "EGO" else 0.0
    shake = 2.5 * math.sin(v * 70) if (who == "LAZY" and hanging) or (who == "EGO" and 1.0 < t < 1.8) else 0.0
    hp = hang_pts(BAR_X, BAR_Y, up, SC, sway, kick, shake)
    stand = place(STAND, (BAR_X, FLOOR - 113 * SC), 1, SC)
    if v < GRAB0 + 0.25:
        return blend(walk.pts(GRAB0 - 1e-3), hp, smooth((v - GRAB0) / 0.25))
    if not hanging:
        # drops back to the floor
        t_drop = {"LAZY": 1.7, "EGO": 1.8, "WORKER": 10 * 0.27 + 0.5}[who]
        k = smooth(clamp((t - t_drop) / 0.25))
        hp0 = hang_pts(BAR_X, BAR_Y, 0.0, SC)
        p = blend(hp0, stand, k)
        if who == "WORKER" and t > t_drop + 0.3:
            p = blend(stand, place(PW.ARMS_UP, (BAR_X, FLOOR - 113 * SC), 1, SC), smooth(clamp((t - t_drop - 0.3) / 0.3)))
        if who == "LAZY" and t > t_drop + 0.3:
            p = blend(stand, place(dict(STAND, head=(18, -136), neck=(10, -100)), (BAR_X, FLOOR - 113 * SC), 1, SC), 0.8)
        return p
    return hp


def gym(d):
    for x in (BAR_X - 180, BAR_X + 180):
        line(d, [(x, FLOOR), (x, BAR_Y - 10)], (70, 72, 84, 255), 12)
        line(d, [(x - 30, FLOOR), (x + 30, FLOOR)], (70, 72, 84, 255), 8)
    line(d, [(BAR_X - 186, BAR_Y), (BAR_X + 186, BAR_Y)], (200, 204, 214, 255), 9)
    line(d, [(BAR_X - 186, BAR_Y - 2), (BAR_X + 186, BAR_Y - 2)], (250, 250, 252, 255), 3)


if SIT == "pullup":
    _K = {w: (None, {"LAZY": GRAB0 + 0.25 + 1.95, "EGO": GRAB0 + 0.25 + 2.05, "WORKER": GRAB0 + 0.25 + 10 * 0.27}[w]) for w in WHO}
    OUTCOME = {"LAZY": "MISS", "EGO": "MISS", "WORKER": "GOAL"}
    FLIGHT = {w: 0.0 for w in WHO}
elif SIT == "hoop":
    _K = {w: shot_seq(w) for w in WHO}
    OUTCOME = {"LAZY": "MISS", "EGO": "MISS", "WORKER": "GOAL"}
    FLIGHT = {"LAZY": 0.8, "EGO": 0.6, "WORKER": 0.62}
else:
    _K = {w: kick_seq(w) for w in WHO}
    OUTCOME = {"LAZY": "SAVED", "EGO": "OVER", "WORKER": "GOAL"}
    FLIGHT = {"LAZY": 1.1, "EGO": 0.55, "WORKER": 0.32}


def hoop_ball(who, v):
    sq, tk = _K[who]
    if v < tk:
        hx, hy = hand_mid(sq.pts(min(v, sq.dur - 1e-3)))
        return hx + 4, hy - 26, 0.0
    hx, hy = hand_mid(sq.pts(tk))
    a = (hx + 4, hy - 26)
    w = clamp((v - tk) / FLIGHT[who])
    u = v - tk - FLIGHT[who]
    if who == "LAZY":           # airball: falls well short
        tgt, h = (HOOP_X - 170, FLOOR - 24), 150
        if u > 0:
            return tgt[0] + 60 * min(u, 0.6), FLOOR - 24 - 50 * abs(math.sin(u * 7)) * math.exp(-u * 3), u * 5
    elif who == "EGO":          # front of the rim, bounces out
        tgt, h = (HOOP_X - 50, RIM_Y - 18), 210
        if u > 0:
            w2 = clamp(u / 0.6)
            return lerp(tgt[0], HOOP_X - 300, w2), lerp(tgt[1], FLOOR - 24, w2) - 140 * math.sin(math.pi * w2 * 0.8), u * 8
    else:                       # swish
        tgt, h = (HOOP_X, RIM_Y - 22), 240
        if u > 0:
            return HOOP_X, min(FLOOR - 24, RIM_Y - 22 + 700 * u * u + 120 * u), 0.0
    x = lerp(a[0], tgt[0], w)
    y = lerp(a[1], tgt[1], w) - h * 4 * w * (1 - w)
    return x, y, (v - tk) * 9


def ball_pos(who, v):
    if SIT == "hoop":
        return hoop_ball(who, v)
    sq, tk = _K[who]
    if v < tk:
        return SPOT, FLOOR - 22, 0.0
    w = clamp((v - tk) / FLIGHT[who])
    if who == "LAZY":         # a weak roller, straight to the keeper
        x = lerp(SPOT, GX - 40, 1 - (1 - w) ** 2)
        return x, FLOOR - 22, (v - tk) * 6
    if who == "EGO":          # way over the bar
        x, y = lerp(SPOT, GX + 130, w), lerp(FLOOR - 22, FLOOR - 600, w) - 80 * math.sin(math.pi * w)
        return x, y, (v - tk) * 14
    tx, ty = mouth(0.78, 0.84)
    if w < 1:                 # top corner
        return lerp(SPOT, tx, w), lerp(FLOOR - 22, ty, w) - 60 * math.sin(math.pi * w), (v - tk) * 16
    u = v - tk - FLIGHT[who]
    return tx + 420 * min(u, 0.25), min(FLOOR - 40, ty + 20 + 900 * u * u), 0.0


def keeper(st, who, v):
    sq, tk = _K[who]
    x, y, rot = GX - 10, FLOOR - 113 * SC, 0.0
    pose = dict(STAND, el=(-36, -96), hl=(-60, -80), er=(36, -96), hr=(60, -80), kl=(-26, 52), fl=(-40, 113), kr=(26, 52), fr=(40, 113))
    if who == "LAZY" and v > tk + FLIGHT["LAZY"] * 0.7:
        k = smooth(clamp((v - tk - FLIGHT["LAZY"] * 0.7) / 0.3))
        pose = dict(pose, head=(20, -120), neck=(14, -86), el=(30, -40), hl=(30, 10), er=(40, -40), hr=(40, 10))
        y += 30 * k
    if who == "EGO" and v > tk:
        y -= 60 * math.sin(math.pi * clamp((v - tk) / 0.5))
        pose = dict(pose, el=(-20, -150), hl=(-30, -200), er=(20, -150), hr=(30, -200))
    if who == "WORKER" and v > tk + 0.05:
        k = smooth(clamp((v - tk - 0.05) / 0.35))
        rot = 1.2 * k              # dives the wrong way (low, toward us)
        x -= 40 * k
        y += 50 * k
        pose = dict(pose, el=(-30, -150), hl=(-40, -200), er=(30, -150), hr=(40, -200))
    p = place(pose, (x, y), -1, SC)
    if rot:
        c_, s_ = math.cos(rot), math.sin(rot)
        p = {j: (x + (px - x) * c_ - (py - y) * s_, y + (px - x) * s_ + (py - y) * c_) for j, (px, py) in p.items()}
    figure(st, p, SC, light=(0.4, -0.9), body=(230, 230, 236))
    d = ImageDraw.Draw(st)
    outfit(d, p, (240, 200, 50), -1, legs=False)
    for side in ("hl", "hr"):
        ell(d, *p[side], 14, 14, (60, 160, 80, 255))
    face(d, p, "determined", -1, v)


def shooter_pose(who, v):
    sq, tk = _K[who]
    p = sq.pts(min(v, sq.dur - 1e-3))
    if who == "WORKER" and v > sq.dur:
        k = smooth(clamp((v - sq.dur) / 0.35))
        cel = place(PW.ARMS_UP, (p["hip"][0], FLOOR - 113 * SC), 1, SC)
        p = blend(p, cel, k)
    if who == "EGO" and v > sq.dur:
        k = smooth(clamp((v - sq.dur) / 0.3))
        p = blend(p, place(dict(STAND, el=(-20, -130), hl=(-6, -150), er=(20, -130), hr=(6, -150)), (p["hip"][0], FLOOR - 113 * SC), 1, SC), k)
    if who == "LAZY" and v > sq.dur:
        k = smooth(clamp((v - sq.dur) / 0.4))
        p = blend(p, place(dict(STAND, head=(18, -136), neck=(10, -100)), (p["hip"][0], FLOOR - 113 * SC), 1, SC), k)
    return p


def expr_of(who, v, tk, done):
    if who == "LAZY":
        return "tired" if not done else "sad"
    if who == "EGO":
        return "smug" if v < tk else ("shocked" if done else "smug")
    return "determined" if not done else "happy"


def turn_at(t):
    for who in WHO:
        a, d_ = TURN[who]
        if a <= t < a + d_:
            return who, t - a
    return None, 0.0


def results_so_far(t):
    return {w: (t >= TURN[w][0] + _K[w][1] + FLIGHT[w]) for w in WHO}


# ---------------------------------------------------------------- flashbacks
FB_TXT = {"LAZY": "SKIPPED PRACTICE.", "EGO": "TOO GOOD TO PRACTICE.", "WORKER": "1,000 KICKS. EVERY DAY."}
if SIT == "pullup":
    FB_TXT = {"LAZY": "SKIPPED THE GYM.", "EGO": "\"I DON'T NEED TO TRAIN.\"", "WORKER": "ONE MORE REP. EVERY DAY."}
if SIT == "hoop":
    FB_TXT = {"LAZY": "\"I'LL PRACTICE TOMORROW.\"", "EGO": "\"I WAS BORN FOR THIS.\"", "WORKER": "1,000 SHOTS. EVERY NIGHT."}
_FY, _FX = np.mgrid[0:H, 0:W].astype(np.float32)
FB_VIG = np.clip(0.25 + 0.9 * np.exp(-(((_FX - 540) / 620) ** 2 + ((_FY - 1060) / 900) ** 2)), 0, 1)[..., None]


def flashback(who, u):
    st = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(st)
    F = FLOOR
    sc = S * 1.5
    poly(d, [(0, 0), (W, 0), (W, F), (0, F)], (40, 34, 30, 255))
    poly(d, [(0, F), (W, F), (W, H), (0, H)], (24, 20, 18, 255))
    if who == "LAZY":
        rrect(d, (240, F - 150, 840, F - 60), 20, (120, 70, 60, 255))
        rrect(d, (230, F - 230, 280, F - 60), 14, (110, 64, 56, 255))
        lying = {"head": (-150, -10), "neck": (-108, -6), "el": (-80, 20), "hl": (-50, 40), "er": (-70, -30), "hr": (-120, -40),
                 "kl": (56, -10), "fl": (113, -2), "kr": (56, 4), "fr": (110, 10)}
        p = place(lying, (560, F - 172), -1, sc)
        dress(st, p, "LAZY", "tired", u, sc)
        for j in range(3):
            v = (u * 1.2 + j / 3) % 1
            PW.spaced(d, (300 + 30 * v + 14 * j) * K, (F - 300 - 120 * v) * K, "Z", font("InterDisplay-Bold.otf", (30 + 12 * j) * K),
                      (230, 230, 240, int(255 * (1 - v))), 0)
        ball(d, 900, F - 24, 0.0, col=(240, 240, 240))
        rrect(d, (870, F - 120, 950, F - 70), 6, (60, 52, 46, 255))
        PW.spaced(d, 910 * K, (F - 95) * K, "PRACTICE", font("InterDisplay-Bold.otf", 13 * K), (200, 190, 170, 255), 1)
    elif who == "EGO":
        rrect(d, (640, F - 560, 900, F - 20), 10, (60, 70, 90, 255), outline=(190, 160, 100, 255), w=8)
        flex = dict(STAND, el=(-50, -140), hl=(-30, -190), er=(50, -140), hr=(30, -190))
        p = place(flex, (520, F - 113 * sc), 1, sc)
        dress(st, p, "EGO", "smug", u, sc)
        q = place(flex, (770, F - 113 * sc * 0.85 - 20), -1, sc * 0.85)
        figure(st, q, sc * 0.85, light=(0.4, -0.9))
        outfit(ImageDraw.Draw(st), q, COL["EGO"], -1, legs=False)
        if SIT == "penalty":
            PW.spaced(d, 520 * K, (F - 520) * K, "I'M A NATURAL.", font(SERIF, 40 * K), (240, 230, 210, 255), 2)
    elif SIT == "pullup":
        poly(d, [(0, 0), (W, 0), (W, F), (0, F)], (20, 26, 40, 255))
        by = F - 560
        for x in (300, 760):
            line(d, [(x, F), (x, by - 10)], (70, 72, 84, 255), 14)
        line(d, [(294, by), (766, by)], (200, 204, 214, 255), 10)
        per = 0.42
        up = 0.5 - 0.5 * math.cos(u / per * 2 * math.pi)
        p = hang_pts(530, by, up, sc, 0.04 * math.sin(u * 3))
        dress(st, p, "WORKER", "determined", u, sc)
        rng = np.random.default_rng(int(u * 20))
        for _ in range(10):   # chalk dust
            ell(d, 490 + rng.uniform(-60, 140), by + rng.uniform(-20, 40), 4, 4, (240, 240, 240, 160))
        rrect(d, (90, 620, 330, 720), 10, (10, 10, 14, 255))
        PW.spaced(d, 210 * K, 670 * K, f"REP {87 + int(u / per)}", font("InterDisplay-Bold.otf", 44 * K), (240, 80, 80, 255), 2)
    elif SIT == "hoop":
        poly(d, [(0, 0), (W, 0), (W, F), (0, F)], (20, 26, 40, 255))
        hoop(d)
        for j in range(9):
            ball(d, 560 + (j * 41) % 220, F - 24, 0.0, col=(230, 120, 40))
        c = clip(FREE)
        ph = (u * 1.3) % 1.0
        ct = 3.6 + ph * 2.0
        p = c.pts(ct, x0=0, floor=F, scale=sc, x_lock=380)
        dress(st, p, "WORKER", "determined", u, sc)
        rel = (FREE_T - 3.6) / 2.0
        if ph < rel:
            hx, hy = hand_mid(p)
            ball(d, hx + 4, hy - 30, 0.0, col=(230, 120, 40))
        else:
            w = clamp((ph - rel) / 0.35)
            ball(d, lerp(430, HOOP_X, w), lerp(F - 330, RIM_Y - 22, w) - 260 * 4 * w * (1 - w), w * 9, col=(230, 120, 40))
        rrect(d, (90, 620, 330, 720), 10, (10, 10, 14, 255))
        PW.spaced(d, 210 * K, 670 * K, "11:00 PM", font("InterDisplay-Bold.otf", 44 * K), (240, 80, 80, 255), 2)
    else:
        poly(d, [(0, 0), (W, 0), (W, F), (0, F)], (20, 26, 40, 255))
        goal(d)
        for j in range(14):
            ball(d, GX + 30 + (j * 19) % 110, FLOOR - 24 - (j % 3) * 30, 0.0, col=(230, 230, 230))
        c = clip(KICK)
        ct = 4.1 + ((u * 1.4) % 1.0) * 1.3
        p = c.pts(ct, x0=0, floor=F, scale=sc, x_lock=430)
        dress(st, p, "WORKER", "determined", u, sc)
        ph = (u * 1.4) % 1.0
        if ph > 0.68:
            w = (ph - 0.68) / 0.32
            ball(d, lerp(520, GX + 60, w), lerp(F - 22, F - 200, w), w * 10, col=(240, 240, 240))
        else:
            ball(d, 520, F - 22, 0.0, col=(240, 240, 240))
        rrect(d, (90, 620, 330, 720), 10, (10, 10, 14, 255))
        PW.spaced(d, 210 * K, 670 * K, "5:00 AM", font("InterDisplay-Bold.otf", 44 * K), (240, 80, 80, 255), 2)
    im = st.resize((W, H), Image.LANCZOS)
    a = np.asarray(im.convert("RGB"), np.float32)
    g = a.mean(-1, keepdims=True)
    sep = g * np.array([1.12, 0.96, 0.78], np.float32)[None, None, :] + np.array([18, 10, 0], np.float32)
    a = (a * 0.3 + sep * 0.7) * FB_VIG
    a += np.random.default_rng(int(u * 60)).normal(0, 6, (H // 4, W // 4, 1)).repeat(4, 0).repeat(4, 1)
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    dd = ImageDraw.Draw(im)
    al = smooth(clamp(u / 0.15))
    PW.spaced(dd, W / 2, 260, who, font("InterDisplay-Bold.otf", 90), (GOLD if who == "WORKER" else (246, 240, 226)) + (int(255 * al),), 8)
    PW.spaced(dd, W / 2, 380, FB_TXT[who], font(SERIF, 52), (236, 228, 210, int(255 * smooth(clamp((u - 0.1) / 0.2)))), 3)
    for e in (0.0, FB_LEN):
        if abs(u - e) < 0.1:
            im.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, int(150 * (1 - abs(u - e) / 0.1)))))
    return im


# ---------------------------------------------------------------- frame
def frame(t):
    for w in WHO:
        if FB_AT[w] <= t < FB_AT[w] + FB_LEN:
            return np.asarray(flashback(w, t - FB_AT[w]).convert("RGB"))
    st = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(st)
    cur, v = turn_at(t)
    last = None
    if cur is None and t >= T_INTRO:
        last = "WORKER" if t >= TURN["WORKER"][0] else None
    shooter = cur or last
    sv = v if cur else (t - TURN["WORKER"][0] if last else 0.0)
    bulge = 0.0
    if shooter == "WORKER":
        sq, tk = _K["WORKER"]
        bulge = math.sin(math.pi * clamp((sv - tk - FLIGHT["WORKER"]) / 0.4))
    if SIT == "hoop":
        hoop(d, max(0.0, bulge))
    elif SIT == "pullup":
        gym(d)
    else:
        goal_back(d, max(0.0, bulge))
        keeper(st, shooter or "LAZY", sv if shooter else 0.0)
    # waiting players, a little further back
    waiting = [w for w in WHO if w != shooter] if shooter else WHO[:2]
    for slot, w in enumerate(waiting[:2]):
        x, s_ = WAIT[slot]
        p = place(dict(STAND, head=(4, -150 + 3 * math.sin(t * 2 + slot))), (x, FLOOR - 46 - 113 * SC * s_), 1, SC * s_)
        dress(st, p, w, "neutral" if w != "EGO" else "smug", t, SC * s_)
    pts = {}
    if shooter:
        sq, tk = _K[shooter]
        done = sv > tk + FLIGHT[shooter]
        if SIT == "pullup":
            p = pull_pose(shooter, sv)
            up, n_, hanging = reps_up(shooter, sv)
            ex = {"LAZY": "tired" if not done else "sad", "EGO": ("smug" if sv < GRAB0 + 1.25 else "nervous") if not done else "shocked",
                  "WORKER": "determined" if not done else "happy"}[shooter]
        else:
            p = shooter_pose(shooter, sv)
            ex = expr_of(shooter, sv, tk, done)
        ell(d, p["hip"][0], FLOOR + 3, 60, 10, (0, 0, 0, 90))
        dress(st, p, shooter, ex, t, SC)
        pts[shooter] = p
        if SIT != "pullup":
            bx, by, br = ball_pos(shooter, sv)
            ball(d, bx, by, br, col=BALL_COL)
    else:   # intro: all three lined up
        p = place(STAND, {"hoop": SHOOT_X, "pullup": 420}.get(SIT, 370), FLOOR - 113 * SC) if False else place(STAND, ({"hoop": SHOOT_X, "pullup": 420}.get(SIT, 370), FLOOR - 113 * SC), 1, SC)
        dress(st, p, "WORKER", "determined", t, SC)
        pts["WORKER"] = p
        if SIT != "pullup":
            ball(d, SPOT if SIT != "hoop" else SHOOT_X + 60, FLOOR - 22, 0.0, col=BALL_COL)
    if SIT == "penalty":
        goal_front(d, max(0.0, bulge))
    base = stadium().copy()
    base.alpha_composite(st)
    z, cx, cy = CAM
    shake = 0.0
    if shooter == "WORKER":
        sq, tk = _K["WORKER"]
        if tk + FLIGHT["WORKER"] <= sv < tk + FLIGHT["WORKER"] + 0.3:
            shake = 10 * (1 - (sv - tk - FLIGHT["WORKER"]) / 0.3)
    im = hq.camera(base, z, (z * (W / 2 - cx) + shake * math.sin(t * 80)) * K, z * (H / 2 - cy) * K).resize((W, H), Image.LANCZOS)
    im.alpha_composite(TOPBAND)
    dd = ImageDraw.Draw(im)
    # header + scoreboard
    PW.spaced(dd, W / 2, 40, {"penalty": "PENALTY KICK", "hoop": "FREE THROW", "pullup": "PULL-UPS"}[SIT], font("InterDisplay-Bold.otf", 70), (246, 246, 250, 255), 6)
    res = results_so_far(t)
    if COMBO:
        cw, k_ = COMBO.split(":")
        prev = (int(k_) - 1) if cw == "WORKER" else 0
        won = prev + (1 if (cw == "WORKER" and res[cw]) else 0)
        PW.spaced(dd, W / 2, 128, f"CHALLENGE {CHALLENGE[SIT]}/3", font("Inter-SemiBold.otf", 26), (180, 186, 204, 255), 6)
        col = (246, 200, 90) if cw == "WORKER" else (220, 224, 236)
        PW.spaced(dd, W / 2 - 70, 176, cw, font("InterDisplay-Bold.otf", 44), col + (255,), 5)
        PW.spaced(dd, W / 2 + 120, 168, f"{won}/3", font("InterDisplay-Bold.otf", 56), (GREEN if won else RED) + (255,), 2)
    for j, w in enumerate(WHO if not COMBO else []):
        x = 220 + j * 320
        col = (246, 200, 90) if w == "WORKER" else (220, 224, 236)
        PW.spaced(dd, x, 150, w, font("Inter-SemiBold.otf", 30), col + (255,), 5)
        mark = ("✓" if OUTCOME[w] == "GOAL" else "✗") if res[w] else "–"
        mc = (GREEN if mark == "✓" else RED) if res[w] else (120, 124, 140)
        PW.spaced(dd, x, 190, mark, font("InterDisplay-Bold.otf", 64), mc + (255,), 0)
    # names over the heads
    for w, p in pts.items():
        hx, hy = to_scr(*p["head"])
        PW.spaced(dd, hx, hy - 90, w, font("Inter-SemiBold.otf", 26), ((246, 200, 90) if w == "WORKER" else (220, 224, 236)) + (255,), 4)
    if SIT == "pullup" and cur and GRAB0 < v:
        up, n_, hanging = reps_up(cur, v)
        bx_, by_ = to_scr(BAR_X + 250, BAR_Y - 40)
        PW.spaced(dd, bx_, by_, "REPS", font("Inter-SemiBold.otf", 28), (200, 206, 224, 255), 6)
        PW.spaced(dd, bx_, by_ + 36, str(n_), font("InterDisplay-Bold.otf", 96), (GOLD if n_ >= 10 else (246, 246, 250)) + (255,), 2)
    # the outcome word
    if cur:
        sq, tk = _K[cur]
        a = hq.pop(v, tk + FLIGHT[cur], 0.25) if v >= tk + FLIGHT[cur] else 0
        if a > 0:
            col = GOLD if cur == "WORKER" else RED
            word = {"hoop": {"LAZY": "AIRBALL.", "EGO": "OFF THE RIM.", "WORKER": "SWISH!"},
                    "pullup": {"LAZY": "0 REPS.", "EGO": "2 REPS.", "WORKER": "10 REPS!"},
                    "penalty": {"LAZY": "SAVED.", "EGO": "OVER THE BAR.", "WORKER": "GOAL!"}}[SIT][cur]
            text(im, W / 2, 470, word, int(110 * max(0.3, min(1, a))), col=col)
    if t < T_INTRO:
        a = smooth(prog(t, 0.1, 0.4)) * (1 - smooth(prog(t, T_INTRO - 0.3, T_INTRO)))
        text(im, W / 2, 470, "3 CHALLENGES." if COMBO else ("ONE TRY EACH." if SIT == "pullup" else "ONE SHOT EACH."), 84, a=a)
    if t >= T_LINE:
        u = t - T_LINE
        im = Image.blend(im.convert("RGB"), Image.new("RGB", (W, H), (0, 0, 0)), 0.75 * smooth(clamp(u / 0.4))).convert("RGBA")
        text(im, W / 2, 820, "SAME CHANCE.", 92, a=smooth(prog(u, 0.2, 0.5)))
        text(im, W / 2, 940, "DIFFERENT PREPARATION.", 74, col=GOLD, a=smooth(prog(u, 0.7, 1.0)))
    return np.asarray(im.convert("RGB"))


class render_fb_factory:
    def __init__(self, who, u0):
        self.who, self.u0 = who, u0

    def __call__(self, i):
        return np.asarray(flashback(self.who, self.u0 + i / FPS).convert("RGB")).tobytes()


def render(i):
    acc = None
    for k_ in range(2):
        f = frame((i + k_ / 4) / FPS).astype(np.float32)
        acc = f if acc is None else acc + f
    return (acc / 2).astype(np.uint8).tobytes()


MUSIC = "Undaunted.mp3"


def audio(sfx_only=False):
    n = int(DUR * SR)
    out = np.zeros((n, 2))
    if not sfx_only:
        put(out, track(MUSIC, 40.0, DUR), 0.0, 1.5, fin=0.05, fout=1.0)
    tt = np.arange(n) / SR
    crowd = np.pad(noise(DUR, 2, lo=250, hi=3000)[:n], (0, max(0, n - int(DUR * SR))))[:n]
    out += (crowd * 0.05)[:, None]
    thud = noise(0.18, 3, lo=60, hi=1500)[:int(0.18 * SR)] * env(int(0.18 * SR), 0.002, 0.12)
    for w in WHO:
        a = TURN[w][0]
        sq, tk = _K[w]
        if SIT == "penalty":
            mix_in(out, thud, a + tk, 0.7, 0.0)
        hit = a + tk + FLIGHT[w]
        if SIT == "pullup":
            mix_in(out, tone(700, 0.2, (1, 2.7), a=0.001, d=0.15), a + GRAB0 + 0.2, 0.3, 0.0)          # hands on the bar
            for r in range(REPS[w]):
                at = a + GRAB0 + 0.25 + (r + 0.5) * (0.5 if w == "EGO" else 0.27)
                mix_in(out, tone(880 + 40 * r, 0.12, (1, 2), a=0.002, d=0.08), at, 0.18, 0.0)
            mix_in(out, noise(0.2, 3, lo=60, hi=900)[:int(0.2 * SR)] * env(int(0.2 * SR), 0.002, 0.15), hit + 0.2, 0.5, 0.0)
            if w == "WORKER":
                mix_in(out, noise(1.8, 6, lo=300, hi=3500)[:int(1.8 * SR)] * env(int(1.8 * SR), 0.05, 1.4), hit, 0.6, 0.0)
            else:
                mix_in(out, noise(1.0, 4, lo=200, hi=1500)[:int(1.0 * SR)] * env(int(1.0 * SR), 0.1, 0.8), hit, 0.35, 0.0)
            continue
        if SIT == "hoop":
            if w == "EGO":
                mix_in(out, tone(520, 0.4, (1, 2.4, 3.9), a=0.001, d=0.3), hit, 0.45, 0.4)     # clang
            for b in (0.35, 0.65):
                mix_in(out, tone(90, 0.12, (1, 2), a=0.001, d=0.1), hit + b, 0.35, 0.0)    # bounces
            if w == "WORKER":
                mix_in(out, noise(0.45, 10, lo=2000, hi=9000)[:int(0.45 * SR)] * env(int(0.45 * SR), 0.05, 0.35), hit, 0.5, 0.4)
        if w == "WORKER":
            mix_in(out, noise(1.8, 6, lo=300, hi=3500)[:int(1.8 * SR)] * env(int(1.8 * SR), 0.05, 1.4), hit, 0.6, 0.0)   # roar
            mix_in(out, tone(1320, 0.6, (1, 2, 3), a=0.002, d=0.5), hit, 0.25, 0.0)
        else:
            mix_in(out, noise(1.0, 4, lo=200, hi=1500)[:int(1.0 * SR)] * env(int(1.0 * SR), 0.1, 0.8), hit, 0.35, 0.0)  # "ohh"
    for e in [FB_AT[w] for w in WHO] + [FB_AT[w] + FB_LEN for w in WHO]:
        mix_in(out, noise(0.3, 11, lo=400, hi=6000)[:int(0.3 * SR)] * env(int(0.3 * SR), 0.15, 0.1), e - 0.15, 0.22, 0.0)
    mix_in(out, tone(55, 1.0, (1, 2), a=0.002, d=0.9), T_LINE + 0.7, 0.5, 0.0)
    out *= np.clip((DUR - tt) / 0.6, 0.0, 1)[:, None]
    out /= max(1.0, np.abs(out).max() / 0.9)
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(here, "drill"), exist_ok=True)
    args = [a for a in sys.argv[1:] if a not in ("penalty", "hoop", "pullup")]
    if "--stills" in args:
        ts = [float(a) for a in args[1:]] or [0.7, 2.2, 3.6, 4.4, 5.4, 6.4, 7.2, 8.6, 9.2, 10.0, 11.9, 13.3, 14.7, 17.0]
        cols = 7
        rows = math.ceil(len(ts) / cols)
        sheet = Image.new("RGB", (220 * cols, 391 * rows))
        for j, t in enumerate(ts):
            sheet.paste(Image.fromarray(frame(t)).resize((220, 391), Image.LANCZOS), ((j % cols) * 220, (j // cols) * 391))
        p = os.path.join(here, "drill", f"{SIT}-stills.png")
        sheet.save(p)
        print(p, round(DUR, 1), {w: round(_K[w][1], 2) for w in WHO})
        return
    if "--range" in args or "--fb" in args:     # a raw piece for the combined video (normal speed, effects only)
        i = args.index("--range") if "--range" in args else args.index("--fb")
        a, b, out = float(args[i + 1]), float(args[i + 2]), args[i + 3]
        who = args[i + 4] if "--fb" in args else None
        n0, n1 = int(round(a * FPS)), int(round(b * FPS))
        wav = out + ".wav"
        if who is None:
            full = audio(sfx_only=True)
            piece = full[int(a * SR):int(b * SR)]
        else:
            piece = np.zeros((int((b - a) * SR), 2))
        write_wav(wav, piece)
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
                              "-c:a", "pcm_s16le", "-ar", str(SR), "-shortest", out], stdin=subprocess.PIPE)
        with Pool(os.cpu_count()) as pool:
            fn = render if who is None else render_fb_factory(who, a)
            for buf in pool.imap(fn, range(n0, n1) if who is None else range(n1 - n0), chunksize=2):
                p.stdin.write(buf)
        p.stdin.close()
        p.wait()
        os.remove(wav)
        print(out)
        return
    out = args[0]
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
    fast = out + ".fast.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out, "-filter_complex",
                    f"[0:v]setpts=PTS/{SPEED},fps={FPS}[v];[0:a]atempo={SPEED}[a]", "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", fast], check=True)
    os.replace(fast, out)
    print(out)
    print(f'Credit: Music: "{MUSIC[:-4]}" by Kevin MacLeod (incompetech.com), CC BY 4.0')


if __name__ == "__main__":
    main()
