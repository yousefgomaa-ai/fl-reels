#!/usr/bin/env python3
"""SHAKE IT. OR TAP IT. - ketchup, two people at one diner counter, a moving camera. 18 s, loops.

Frame 0 is the peak: a ketchup explosion in slow motion all over the orange guy (no words). Rewind. Both bottles are
stuck. He smacks the bottom; the cyan guy taps the neck twice - the orange guy laughs at him. He shakes with both hands,
then pokes a knife in. Twist: the cyan guy's ketchup flows slowly onto his fries - TAPPED. One last mega-shake: BOOM,
the explosion from frame 0, now explained. Wide: "SHAKE IT. / OR TAP IT." He wipes his face, takes a new bottle,
starts shaking... and it loops into frame 0.

    python3 stick/ketchup.py stick/ketchup.mp4
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
import game_spend as GS  # noqa
import music  # noqa
import hq  # noqa
import airport as AP  # noqa
from perfect_wave import clamp, env, font, lerp, lerp_pose, midi, mix_in, noise, prog, smooth, spaced, tone, write_wav  # noqa

W, H, FPS = 1080, 1920, 30
SR = 44100
DUR = 18.0
NF = int(round(DUR * FPS))
XFADE = 0.5
K = hq.K
FLOOR = AP.FLOOR
S = AP.S
HIP_Y = AP.HIP_Y
ORG = (255, 150, 40)
CYN = (60, 220, 255)
GOLD, GREEN, REDC = AP.GOLD, AP.GREEN, AP.REDC
KET = (205, 22, 28)
KET_HI = (255, 110, 100)
TITLE_H = 300
MUSIC = "piano_c"

ORANGE_X = 700
BLUE_X = 1400
COUNTER_TOP = FLOOR - 250

# timeline
T_HOOK1 = 1.5            # slow-mo explosion until here
T_REW1 = 2.4             # rewind until here
T_SMACK = [3.2, 3.7]
T_WHIP_B = 4.1           # -> cyan guy
T_TAPS = [5.0, 5.45]
T_WHIP_O = 6.2           # -> orange, laughing
T_SHAKE2 = 7.4
T_KNIFE = 8.7
T_WHIP_B2 = 10.0         # -> cyan: it flows
T_FLOW = 10.2
T_TAPPED = 10.7
T_WHIP_O2 = 11.6         # -> orange, shocked
T_MEGA = 12.4
T_BOOM = 13.1
T_WIDE = 14.6
T_L1, T_L2 = 14.9, 15.6
CPS = 16.0
LINE1, LINE2 = "SHAKE IT.", "OR TAP IT."
T_WIPE = 16.4
T_NEW = 17.0
WHIPS = (T_WHIP_B, T_WHIP_O, T_WHIP_B2, T_WHIP_O2)


# ---------------------------------------------------------------- the explosion
def splash_u(t):
    """explosion clock (s since the burst) - slow motion in the hook, rewind, then the real one"""
    if t < T_HOOK1:
        return lerp(0.26, 0.5, t / T_HOOK1)
    if t < T_REW1:
        return lerp(0.5, 0.0, smooth(prog(t, T_HOOK1, T_REW1)))
    if t < T_BOOM:
        return 0.0
    d = t - T_BOOM
    return 0.16 * d / 0.6 if d < 0.6 else 0.16 + (d - 0.6) * 0.8


def splash_on(t):
    return t < T_REW1 or t >= T_BOOM


def stain_k(t):
    """how much ketchup is on him and the wall"""
    if t < T_HOOK1:
        return smooth(prog(splash_u(t), 0.18, 0.5))
    if t < T_REW1:
        return smooth(prog(splash_u(t), 0.18, 0.5))
    if t < T_BOOM:
        return 0.0
    k = smooth(prog(splash_u(t), 0.18, 0.55))
    if t >= T_WIPE:
        k *= 1 - 0.45 * smooth(prog(t, T_WIPE, T_WIPE + 0.5))
    return k


# ---------------------------------------------------------------- camera
def cam(t):
    hook = (ORANGE_X + 70, 1260, 2.15)

    def boom_shot(u):
        return ORANGE_X + 70, 1260, 2.15 + 0.08 * prog(u, T_BOOM, T_WIDE)

    def hook_shot(u):
        return hook[0], hook[1], hook[2] + 0.08 * prog(u, 0, T_HOOK1)

    def rewind(u):
        k = smooth(prog(u, T_HOOK1, T_REW1))
        return lerp(hook[0], ORANGE_X + 170, k), lerp(hook[1], 1180, k), lerp(2.23, 1.5, k)

    def orange(z0, z1, t0, t1):
        return lambda u: (ORANGE_X + 170, 1180, lerp(z0, z1, prog(u, t0, t1)))

    def blue(u):
        return BLUE_X + 170, 1180, lerp(1.5, 1.6, prog(u, T_WHIP_B, 4.8))

    def blue_close(u):
        k = smooth(prog(u, 4.8, 5.2))
        return BLUE_X + lerp(170, 220, k), lerp(1180, 1270, k), lerp(1.6, 2.1, k)

    def mega(u):
        k = smooth(prog(u, T_MEGA, T_BOOM))
        return ORANGE_X + lerp(170, 70, k), lerp(1180, 1260, k), lerp(1.6, 2.15, k)

    def wide(u):
        k = smooth(prog(u, T_WIDE, T_WIDE + 1.1))
        return lerp(ORANGE_X + 70, (ORANGE_X + BLUE_X) / 2 + 100, k), lerp(1260, 1150, k), lerp(2.23, 0.85, k)

    def back_to_hook(u):
        k = smooth(prog(u, T_WIPE, DUR - 0.3))
        x0, y0, z0 = wide(T_WIPE)
        return lerp(x0, hook[0], k), lerp(y0, hook[1], k), lerp(z0, hook[2], k)

    segs = [(0, hook_shot), (T_HOOK1, rewind), (T_REW1, orange(1.5, 1.6, T_REW1, T_WHIP_B)), (T_WHIP_B, blue),
            (4.8, blue_close), (T_WHIP_O, orange(1.55, 1.65, T_WHIP_O, T_WHIP_B2)), (T_WHIP_B2, blue_close),
            (T_WHIP_O2, orange(1.6, 1.6, 0, 1)), (T_MEGA, mega), (T_BOOM, boom_shot), (T_WIDE, wide),
            (T_WIPE, back_to_hook)]
    whips = {T_WHIP_B: 0.32, T_WHIP_O: 0.32, T_WHIP_B2: 0.32, T_WHIP_O2: 0.32}
    cur_i = 0
    for i, (ts, fn) in enumerate(segs):
        if t >= ts:
            cur_i = i
    ts, fn = segs[cur_i]
    a = fn(t)
    d = whips.get(ts, 0)
    if d and t < ts + d and cur_i > 0:
        prev = segs[cur_i - 1][1](ts)
        k = smooth(smooth(prog(t, ts, ts + d)))
        a = tuple(lerp(p_, q_, k) for p_, q_ in zip(prev, a))
    cx, cy, z = a
    cx += 4 * math.sin(t * 1.7) + 3 * math.sin(t * 4.3 + 1)
    cy += 3 * math.sin(t * 2.1 + 2) + 2 * math.sin(t * 5.1)
    # the camera shakes with him
    sh = 0
    if T_SHAKE2 <= t < T_KNIFE or T_MEGA <= t < T_BOOM or t >= T_NEW + 0.2:
        sh = 9
    for t0 in T_SMACK + [T_BOOM]:
        if t0 <= t < t0 + 0.3:
            sh = max(sh, 22 * (1 - (t - t0) / 0.3))
    cx += sh * math.sin(t * 61) / z
    cy += sh * 0.7 * math.cos(t * 53) / z
    return cx, cy, z


class View(AP.View):
    def __init__(self, t):
        self.cx, self.cy, self.z = cam(t)


# ---------------------------------------------------------------- poses
STAND = PW.STAND
HOLDINV = dict(STAND, el=(48, -84), hl=(110, -62), er=(14, -60), hr=(20, -14))
SMACK_UP = dict(HOLDINV, er=(60, -110), hr=(100, -134))
SMACK_HIT = dict(HOLDINV, er=(66, -96), hr=(110, -100))
TWO_HANDS = dict(HOLDINV, er=(54, -80), hr=(104, -70))
TAPPOSE = dict(STAND, el=(46, -86), hl=(100, -74), er=(52, -66), hr=(132, -44))
LAUGH = dict(STAND, head=(-14, -146), neck=(-8, -106), el=(-10, -60), hl=(20, -54), er=(14, -64), hr=(30, -50))
SHOCKED = dict(HOLDINV, head=(12, -148))
DRENCH = dict(STAND, head=(4, -144), el=(-44, -84), hl=(-70, -60), er=(46, -84), hr=(74, -60))
WIPE = dict(STAND, el=(30, -110), hl=(16, -150), er=(14, -60), hr=(20, -14))
EAT = dict(STAND, el=(40, -96), hl=(18, -136), er=(14, -60), hr=(20, -14))


def orange_state(t):
    """pose, bottle angle (deg, 180 = upside down), bottle in hand?, knife"""
    if t < T_REW1:
        k = 0.5 + 0.5 * math.sin(t * 30) if t >= T_HOOK1 else 0.0
        return (DRENCH if stain_k(t) > 0.5 else TWO_HANDS), -60, stain_k(t) < 0.5, False
    if t < T_WHIP_B:
        pose = HOLDINV
        for t0 in T_SMACK:
            if t0 - 0.25 <= t < t0:
                pose = lerp_pose(HOLDINV, SMACK_UP, smooth(prog(t, t0 - 0.25, t0 - 0.12)))
            elif t0 <= t < t0 + 0.2:
                pose = SMACK_HIT
        return pose, 180, True, False
    if t < T_SHAKE2:
        if t >= T_WHIP_O:
            b = abs(math.sin(t * 14)) * 6
            return dict(LAUGH, head=(-14, -146 - b), neck=(-8, -106 - b * 0.5)), 180, False, False
        return HOLDINV, 180, True, False
    if t < T_KNIFE:
        y = 34 * math.sin(t * 34)
        return dict(TWO_HANDS, hl=(110, -62 + y), hr=(104, -70 + y), el=(48, -84 + y * 0.5),
                    er=(54, -80 + y * 0.5)), 180 + 14 * math.sin(t * 34), True, False
    if t < T_WHIP_B2:
        y = 10 * math.sin(t * 22)
        return dict(HOLDINV, er=(66, -40 + y), hr=(116, -24 + y)), 180, True, True
    if t < T_MEGA:
        return SHOCKED, 180, True, False
    if t < T_BOOM:
        y = 44 * math.sin(t * 40)
        a = lerp(180, -60, smooth(prog(t, T_BOOM - 0.2, T_BOOM)))
        return dict(TWO_HANDS, hl=(110, -62 + y), hr=(104, -70 + y), el=(48, -84 + y * 0.5),
                    er=(54, -80 + y * 0.5)), a, True, False
    if t < T_WIPE:
        return DRENCH if splash_u(t) > 0.12 else TWO_HANDS, -60, splash_u(t) < 0.12, False
    if t < T_NEW:
        w = 8 * math.sin(t * 16)
        return dict(WIPE, hl=(16 + w, -150)), 180, False, False
    y = 34 * math.sin(t * 34) * smooth(prog(t, T_NEW + 0.2, T_NEW + 0.5))
    return dict(TWO_HANDS, hl=(110, -62 + y), hr=(104, -70 + y), el=(48, -84 + y * 0.5),
                er=(54, -80 + y * 0.5)), lerp(180, 120, smooth(prog(t, DUR - 0.8, DUR))), True, False


def blue_state(t):
    """pose, bottle angle, bottle in hand, eating"""
    if t < T_TAPS[0] - 0.4:
        return HOLDINV, 180, True, False
    if t < T_FLOW:
        p = dict(TAPPOSE)
        for t0 in T_TAPS:
            if t0 - 0.15 <= t < t0 + 0.05:
                p = dict(TAPPOSE, er=(56, -70), hr=(124, -54))
        return p, 145, True, False
    if t < T_WIDE:
        return dict(TAPPOSE, er=(14, -60), hr=(20, -14)), 150, True, False
    k = int(t * 2.2) % 2
    return (EAT if k else STAND), 0, False, True


# ---------------------------------------------------------------- drawing
def rot(x, y, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return x * c - y * s, x * s + y * c


BOTTLE = [(-22, 50), (-22, -40), (-10, -62), (-9, -100), (9, -100), (10, -62), (22, -40), (22, 50)]


def bottle_pts(hand, ang, sc=1.0):
    return [(hand[0] + rot(x * sc, y * sc, ang)[0], hand[1] + rot(x * sc, y * sc, ang)[1]) for x, y in BOTTLE]


def mouth(hand, ang):
    dx, dy = rot(0, -108, ang)
    return hand[0] + dx, hand[1] + dy


def draw_bottle(p, v, hand, ang, fill=0.85):
    pts = bottle_pts(hand, ang)
    p.fill_poly(v.pts(pts), (40, 10, 14), 255)
    body = [(x, max(y, 50 - 90 * fill)) for x, y in BOTTLE[:2] + BOTTLE[-2:]]
    body = [(-20, 48), (-20, 48 - 88 * fill), (20, 48 - 88 * fill), (20, 48)]
    p.fill_poly(v.pts([(hand[0] + rot(x, y, ang)[0], hand[1] + rot(x, y, ang)[1]) for x, y in body]), KET, 255)
    lab = [(-20, 30), (-20, -6), (20, -6), (20, 30)]
    p.fill_poly(v.pts([(hand[0] + rot(x, y, ang)[0], hand[1] + rot(x, y, ang)[1]) for x, y in lab]), (240, 240, 230),
                255)
    p.line(v.pts(pts + [pts[0]]), (230, 236, 245), 3.5 * v.z, 230)
    cap = [(-11, -100), (-11, -114), (11, -114), (11, -100)]
    p.fill_poly(v.pts([(hand[0] + rot(x, y, ang)[0], hand[1] + rot(x, y, ang)[1]) for x, y in cap]), (240, 240, 240),
                255)


def counter(p, v, x0, col, t, fries_k=0.0):
    z = v.z
    p.fill_rect(v.box([x0 + 40, COUNTER_TOP, x0 + 380, FLOOR]), (30, 22, 40), 255, r=6 * z)
    p.rect(v.box([x0 + 40, COUNTER_TOP, x0 + 380, FLOOR]), col, 4 * z, 220, r=6 * z)
    p.fill_rect(v.box([x0 + 26, COUNTER_TOP - 16, x0 + 394, COUNTER_TOP + 4]), (190, 196, 220), 255, r=4 * z)
    # plate + fries
    px = x0 + 220
    p.ds.ellipse([(v.x(px - 90)) * K, (v.y(COUNTER_TOP - 30)) * K, (v.x(px + 90)) * K, (v.y(COUNTER_TOP - 4)) * K],
                 fill=(235, 235, 240, 255))
    rng = np.random.default_rng(int(x0))
    for j in range(14):
        fx = px - 60 + j * 9 + rng.uniform(-4, 4)
        a = rng.uniform(-25, 25)
        dx, dy = rot(0, -50, a)
        p.line(v.pts([(fx, COUNTER_TOP - 20), (fx + dx, COUNTER_TOP - 20 + dy)]), (255, 200, 70), 7 * z, 255)


def wall(p, v, t):
    z = v.z
    fy = v.y(FLOOR)
    p.fill_rect([0, 0, W, fy], (16, 12, 26), 255)
    p.fill_rect([0, fy, W, H], (22, 18, 30), 255)
    # checker floor
    for i in range(-20, 40):
        x = i * 120
        p.ds.line([v.x(x) * K, fy * K, (v.x(x) + (v.x(x) - W / 2) * 0.9) * K, H * K], fill=(60, 50, 80, 120),
                  width=int(2 * K))
    # diner wall: tiles band, neon DINER sign, menu boards, a window
    p.fill_rect(v.box([-400, 1150, 2600, COUNTER_TOP - 20]), (34, 26, 48), 255)
    for x in range(-400, 2600, 60):
        p.line(v.pts([(x, 1150), (x, COUNTER_TOP - 20)]), (50, 40, 70), 2 * z, 255)
    p.text((v.x(1050), v.y(700)), "DINER", 110 * z, (255, 70, 200), 255, neon=True, spacing=10)
    for mx, c in ((350, (255, 205, 60)), (1750, (120, 220, 255))):
        p.fill_rect(v.box([mx - 170, 820, mx + 170, 1080]), (10, 10, 18), 255, r=10 * z)
        p.rect(v.box([mx - 170, 820, mx + 170, 1080]), c, 4 * z, 230, r=10 * z)
        for j in range(4):
            p.fill_rect(v.box([mx - 140, 850 + j * 56, mx + 40, 868 + j * 56]), c, 120, r=4 * z)
            p.fill_rect(v.box([mx + 80, 850 + j * 56, mx + 140, 868 + j * 56]), c, 160, r=4 * z)
    for lx in range(-200, 2600, 300):
        p.line([(v.x(lx), v.y(420)), (v.x(lx), v.y(560))], (120, 110, 160), 3 * z, 255)
        p.circle(v.x(lx), v.y(580), 26 * z, (255, 220, 160), a=230, fill=True)


def blob(d, x, y, r, col, a=255):
    d.ellipse([(x - r) * K, (y - r) * K, (x + r) * K, (y + r) * K], fill=col + (int(a),))


RNG = np.random.default_rng(5)
DROPS = []
for _ in range(80):
    ang = math.radians(-150 + RNG.normal(0, 28))
    sp = RNG.uniform(500, 1600)
    DROPS.append((math.cos(ang) * sp, math.sin(ang) * sp, RNG.uniform(7, 24)))
WALL_STAINS = [(RNG.uniform(ORANGE_X - 260, ORANGE_X + 260), RNG.uniform(880, 1260), RNG.uniform(16, 46))
               for _ in range(18)]
BODY_STAINS = [("head", (-10, 6), 14), ("head", (12, -8), 10), ("head", (2, 14), 9), ("neck", (6, 30), 16),
               ("neck", (-4, 60), 12), ("el", (0, 0), 10), ("hip", (8, -40), 13)]


def ketchup_layer(v, t, opts, mouth_o, mouth_b, b_flow):
    lay = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    z = v.z
    sk = stain_k(t)
    # stains on the wall (behind him) - drawn on this layer but they sit far back
    for x, y, r in WALL_STAINS:
        if sk > 0.02:
            sx, sy = v.p((x, y))
            blob(d, sx, sy, r * z * sk, KET, 235)
            blob(d, sx, sy + r * z * sk * 0.9, r * z * sk * 0.35, KET, 235)
    # stains on him
    if sk > 0.02:
        for joint, (dx, dy), r in BODY_STAINS:
            jx, jy = opts[joint]
            blob(d, jx + dx * z, jy + dy * z, r * z * sk * 1.3, KET, 245)
    # the flying drops
    if splash_on(t):
        u = splash_u(t)
        if u > 0:
            mx, my = mouth_o
            for vx, vy, r in DROPS:
                x, y = mx + vx * u, my + vy * u + 900 * u * u
                if y > FLOOR:
                    continue
                sx, sy = v.p((x, y))
                for j in range(3):
                    blob(d, sx - vx * 0.012 * j * z, sy - (vy + 1800 * u) * 0.012 * j * z, r * z * (1 - 0.22 * j), KET,
                         255)
                blob(d, sx - r * 0.3 * z, sy - r * 0.3 * z, r * 0.3 * z, KET_HI, 200)
            # the burst at the mouth
            if u < 0.3:
                sx, sy = v.p(mouth_o)
                blob(d, sx, sy, (40 + 60 * u) * z, KET, 255 * (1 - u / 0.3))
    # the cyan guy's slow, clean pour and the pool on his fries
    if b_flow > 0:
        bx, by = mouth_b
        tx, ty = BLUE_X + 225, COUNTER_TOP - 40
        sx0, sy0 = v.p((bx, by))
        sx1, sy1 = v.p((tx, ty))
        if b_flow < 1:
            d.line([sx0 * K, sy0 * K, lerp(sx0, sx1, min(1, b_flow * 3)) * K, lerp(sy0, sy1, min(1, b_flow * 3)) * K],
                   fill=KET + (255,), width=int(12 * z * K))
        r = 46 * z * smooth(clamp(b_flow * 1.4))
        d.ellipse([(sx1 - r * 1.4) * K, (sy1 - r * 0.45) * K, (sx1 + r * 1.4) * K, (sy1 + r * 0.45) * K],
                  fill=KET + (255,))
        d.ellipse([(sx1 - r * 0.6) * K, (sy1 - r * 0.25) * K, (sx1 - r * 0.1) * K, (sy1 - r * 0.05) * K],
                  fill=KET_HI + (180,))
    return lay


BG = None
VIG = None
FRAME0 = None


def scene(t):
    v = View(t)
    p = AP.SafePanel(BG)
    p.tops = []
    wall(p, v, t)
    counter(p, v, ORANGE_X, ORG, t)
    counter(p, v, BLUE_X, CYN, t)
    # orange
    pose, ang, has_b, knife = orange_state(t)
    opts = AJ.place(pose, (ORANGE_X, HIP_Y), 1, S)
    sp_o = {k_: v.p(q) for k_, q in opts.items()}
    hand_o = opts["hl"]
    if has_b:
        draw_bottle(p, v, hand_o, ang)
    mouth_o = mouth((ORANGE_X + 220, HIP_Y - 124), -60)
    if knife:
        mx, my = mouth(hand_o, ang)
        hr = opts["hr"]
        p.line(v.pts([hr, (lerp(hr[0], mx, 1.4), lerp(hr[1], my, 1.4))]), (210, 220, 235), 5 * v.z, 255)
    p.stick(sp_o, ORG, 10 * v.z)
    # cyan
    pose, ang, has_b, eating = blue_state(t)
    bpts = AJ.place(pose, (BLUE_X, HIP_Y), 1, S)
    sp_b = {k_: v.p(q) for k_, q in bpts.items()}
    if has_b:
        draw_bottle(p, v, bpts["hl"], ang)
    if eating:
        hx, hy = sp_b["hl"]
        p.line([(hx, hy), (hx + 8 * v.z, hy - 40 * v.z)], (255, 200, 70), 7 * v.z, 255)
    p.stick(sp_b, CYN, 10 * v.z)
    mouth_b = mouth(bpts["hl"], 150)
    b_flow = prog(t, T_FLOW, T_FLOW + 1.4) if t >= T_FLOW else 0.0
    if t >= T_WIDE:
        b_flow = max(b_flow, 1.0)
    # taps: little rings on the neck
    for t0 in T_TAPS:
        if t0 <= t < t0 + 0.3:
            nx, ny = v.p(mouth(bpts["hl"], 145))
            r = (20 + 80 * (t - t0)) * v.z
            p.circle(nx, ny, r, CYN, 3 * v.z, 255 * (1 - (t - t0) / 0.3))
    # smack impact rings
    for t0 in T_SMACK:
        if t0 <= t < t0 + 0.25:
            hx, hy = v.p((hand_o[0], hand_o[1] - 60))
            r = (30 + 140 * (t - t0)) * v.z
            p.circle(hx, hy, r, ORG, 4 * v.z, 255 * (1 - (t - t0) / 0.25))
    if t >= T_TAPPED:
        AP.stamp(p, t, T_TAPPED, v.x(BLUE_X + 200), max(420, v.y(1020)), "TAPPED", GREEN)
    out = p.compose()
    out.alpha_composite(ketchup_layer(v, t, sp_o, mouth_o, mouth_b, b_flow))
    for lay, pos in p.tops:
        out.alpha_composite(lay.filter(ImageFilter.GaussianBlur(10 * K)), pos)
        out.alpha_composite(lay, pos)
    return hq.downsample(out, W, H)


def frame(t):
    img = scene(t).convert("RGBA")
    c0, c1 = cam(t - 1 / FPS), cam(t)
    vx = (c1[0] - c0[0]) * c1[2]
    if any(tw <= t < tw + 0.36 for tw in WHIPS) and abs(vx) > 18:
        span = min(abs(vx) * 0.7, 220)
        a_ = np.asarray(img, np.float32)
        acc = np.zeros_like(a_)
        n = 16
        for j in range(n):
            acc += np.roll(a_, int(span * (j / (n - 1) - 0.5)), axis=1)
        img = Image.fromarray((acc / n).astype(np.uint8), "RGBA")
    if t >= T_WIDE:
        img.alpha_composite(VIG)
    else:
        img.alpha_composite(VIG_SIDES)
    tp = hq.Panel(Image.new("RGBA", (W * K, TITLE_H * K), (0, 0, 0, 0)))
    for t0, s2, y, c in ((T_L1, LINE1, 40, ORG), (T_L2, LINE2, 140, CYN)):
        if t < t0:
            continue
        k = int(clamp((t - t0) * CPS, 0, len(s2)))
        tp.text((W / 2, y), s2[:k] + " " * (len(s2) - k), 78, c, 255, neon=True, spacing=6)
    # rewind marker
    if T_HOOK1 <= t < T_REW1:
        for j in range(2):
            x0 = W - 190 + j * 54
            tp.fill_poly([(x0 + 40, 60), (x0 + 40, 140), (x0, 100)], (255, 255, 255), 230)
    tl = tp.compose(glow=0.8)
    img.alpha_composite(tl.resize((W, TITLE_H), Image.LANCZOS), (0, 0))
    rgb = hq.bloom(np.asarray(img.convert("RGB")), 0.45, 150, 26)
    if T_HOOK1 <= t < T_REW1:
        g = rgb.astype(np.float32)
        g = g * 0.8 + g.mean(axis=2, keepdims=True) * 0.2
        g[::4] *= 0.86
        rgb = np.clip(g, 0, 255).astype(np.uint8)
    for t0, amt in ((0.0, 22), (T_BOOM, 45), (T_TAPPED, 25)):
        if t0 <= t < t0 + 0.14:
            rgb = np.clip(rgb.astype(np.float32) + amt * (1 - (t - t0) / 0.14), 0, 255).astype(np.uint8)
    return rgb


def init_worker():
    global BG, VIG, VIG_SIDES
    AP.init_worker()
    BG, VIG = AP.BG, AP.VIG
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2)
    vig = (np.clip((r - 0.3) * 1.4, 0, 1) * 150).astype(np.uint8)
    VIG_SIDES = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    VIG_SIDES.putalpha(Image.fromarray(vig, "L"))


VIG_SIDES = None


def render(i):
    global FRAME0
    t = i / FPS
    fr = frame(t)
    if t > DUR - XFADE:
        if FRAME0 is None:
            FRAME0 = frame(0.0).astype(np.float32)
        k = smooth(prog(t, DUR - XFADE, DUR))
        fr = (fr.astype(np.float32) * (1 - k) + FRAME0 * k).astype(np.uint8)
    return fr.tobytes()


# ---------------------------------------------------------------- sound
def splat(fx, at, g=0.3, slow=1.0):
    n = int(0.9 * slow * SR)
    s = noise(0.9 * slow, int(at * 100), lo=60, hi=int(2500 / slow)) * env(n, 0.002, 0.25 * slow)
    mix_in(fx, s, at, g)
    mix_in(fx, tone(90 / slow, 0.6 * slow, (1, 0.5), a=0.002, d=0.25 * slow, sweep=40 / slow), at, g * 0.9)
    for j in range(6):
        mix_in(fx, noise(0.08, int(at * 10) + j, lo=300, hi=3000) * env(int(0.08 * SR), 0.002, 0.03),
               at + 0.12 * slow + j * 0.09 * slow, g * 0.25, (j % 3 - 1) * 0.4)


def thump(fx, at, g=0.22):
    mix_in(fx, tone(80, 0.25, (1, 0.6), a=0.001, d=0.08, sweep=50), at, g)
    mix_in(fx, noise(0.05, int(at * 77), lo=500, hi=4000) * env(int(0.05 * SR), 0.001, 0.015), at, g * 0.5)


def tik(fx, at, g=0.1):
    mix_in(fx, tone(2600, 0.12, (1, 0.6, 0.3), a=0.0005, d=0.04), at, g, 0.3)
    mix_in(fx, tone(3900, 0.08, (1,), a=0.0005, d=0.025), at, g, 0.3)


def audio():
    n = int(DUR * SR)
    fx = np.zeros((n, 2))
    mus = music.score(MUSIC, DUR, t_end=T_BOOM, t_warm=T_L1, t_line=T_L1 + 0.4, start=T_REW1, loud=1.0)
    mix_in(fx, noise(DUR, 41, lo=200, hi=1500) * 0.4, 0, 0.018)            # diner chatter bed
    # hook: a slow-motion splat from frame 0
    splat(fx, 0.0, 0.34, slow=1.7)
    # rewind: reversed splat + tape chirps
    m = int((T_REW1 - T_HOOK1) * SR)
    rv = noise(T_REW1 - T_HOOK1, 3, lo=200, hi=5000) * np.linspace(0.2, 1, m)
    mix_in(fx, rv, T_HOOK1, 0.06)
    for j in range(6):
        mix_in(fx, tone(500 + 300 * j, 0.06, (1,), a=0.002, d=0.03, sweep=900 + 300 * j), T_HOOK1 + j * 0.14, 0.04)
    for t0 in T_SMACK:
        thump(fx, t0)
    for tw in WHIPS:
        AP.whoosh(fx, tw, 0.1, int(tw * 10))
    for t0 in T_TAPS:
        tik(fx, t0)
    # laugh -> bouncy honks
    for j in range(5):
        mix_in(fx, tone(330 - 12 * j, 0.11, (1, 0.6, 0.4), a=0.004, d=0.05), T_WHIP_O + 0.35 + j * 0.15, 0.05, -0.3)
    # shaking: rattle
    for t0, t1 in ((T_SHAKE2, T_KNIFE), (T_MEGA, T_BOOM), (T_NEW + 0.2, DUR)):
        tt = t0
        while tt < t1:
            mix_in(fx, noise(0.05, int(tt * 90), lo=150, hi=1500) * env(int(0.05 * SR), 0.002, 0.02), tt, 0.09, -0.2)
            tt += 0.092
    # knife scrape
    mix_in(fx, noise(1.2, 8, lo=2500, hi=8000) * (0.5 + 0.5 * np.sin(np.linspace(0, 40, int(1.2 * SR)))) *
           env(int(1.2 * SR), 0.05, 0.6), T_KNIFE, 0.035)
    # the pour: a soft glug, then a success chime + stamp
    for j in range(3):
        mix_in(fx, tone(140 - 15 * j, 0.25, (1, 0.5), a=0.02, d=0.12, sweep=110 - 15 * j), T_FLOW + j * 0.3, 0.07)
    mix_in(fx, tone(70, 0.5, (1, 0.5), a=0.002, d=0.25) + 0.35 * noise(0.5, 21, lo=400, hi=5000) *
           env(int(0.5 * SR), 0.002, 0.12), T_TAPPED, 0.2)
    for j, mm in enumerate((76, 79, 84)):
        mix_in(fx, music.music_box(midi(mm), 1.0), T_TAPPED + 0.15 + 0.08 * j, 0.06)
    # the boom
    splat(fx, T_BOOM, 0.42, slow=1.3)
    mix_in(fx, tone(40, 1.2, (1, 0.6, 0.3), a=0.002, d=0.6), T_BOOM, 0.3)
    # eating crunches
    for j in range(5):
        mix_in(fx, noise(0.07, 60 + j, lo=1500, hi=7000) * env(int(0.07 * SR), 0.002, 0.03), T_WIDE + 0.3 + j * 0.45,
               0.05, 0.3)
    for t0, s in ((T_L1, LINE1), (T_L2, LINE2)):
        for i2, c in enumerate(s):
            if c != " ":
                mix_in(fx, noise(0.03, 500 + i2 + int(t0 * 10), lo=1200, hi=4000) * env(int(0.03 * SR), 0.001, 0.008),
                       t0 + i2 / CPS, 0.05)
    x = mus + fx
    m = int(XFADE * SR)
    k = np.linspace(0, 1, m)[:, None]
    x[-m:] = x[-m:] * (1 - k) + x[:m] * k
    x /= max(1.0, np.abs(x).max() / 0.9)
    return x


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "ketchup.mp4"
    only = os.environ.get("ONLY_FRAMES")
    if only:
        init_worker()
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
