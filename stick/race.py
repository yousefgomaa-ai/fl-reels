#!/usr/bin/env python3
"""WHO WINS? - three lanes, one race, 26.8 s, a perfect loop (the race rewinds into frame 0).

Top: SPRINTER - straight road, bursts ahead, "EASY!", pants, sits, sleeps, wakes in a panic, sprints, overtakes,
cramps, limps. Middle: CONSISTENT - a winding road, the same steady walk the whole time, through the rain; passes the
sleeper, gets passed back, passes again and is one step from the tape. Bottom: RICH KID - never runs: a lounger at the
start line, keys spinning on his finger, a red sports car with a gift bow behind him. Juice, selfie, fanning himself
with cash, a drone brings pizza, checks his gold watch, stands, pulls the bow, gets in, revs - and while CONSISTENT's
hand reaches for the tape in slow motion, the car tears through its own tape first. Stamps: TIRED / 2ND / 1ST.
Then everything rewinds to the start line (frame 0).

    python3 stick/race.py stick/who-wins.mp4
    ONLY_FRAMES=0,3.5,8,10.5,15.5,16.3,21,23.4,23.7,24.6,26.3 python3 stick/race.py /tmp/race
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
import music  # noqa
import hq  # noqa
from perfect_wave import clamp, env, font, lerp, lerp_pose, midi, mix_in, noise, prog, smooth, tone, write_wav  # noqa

W, H, FPS = 1080, 1920, 30
SR = 44100
DUR = 26.8
NF = int(round(DUR * FPS))
K = hq.K
BOLD = hq.BOLD
MUSIC = "strings_am"

TITLE_H = 292
PX0 = 20
PWD, PHT = 1040, 500
PANEL_Y = [296, 802, 1308]
HORIZON = 228
FEET = 392                 # feet on the straight roads
START_X, FIN_X = 92, 800
S = 1.05

INK = (14, 16, 28)
WHITE = (226, 230, 240)
NIGHT = (7, 10, 24)
GOLD = (255, 196, 40)
RED = (226, 54, 54)
GREEN = (40, 176, 86)
GREY = (120, 124, 134)
YEL = (255, 210, 60)
CAR = (230, 40, 52)

# ---------------------------------------------------------------- timeline (scene time)
T_EASY0, T_EASY1 = 3.1, 4.7
T_PANT = 4.4
T_SIT = 6.0
T_LIE = 6.8
T_WAKE = 14.0
T_RUN2 = 14.4
T_CRAMP = 16.0
T_FALL = 16.5
T_UP = 16.95
T_LIMP = 17.35
T_RAIN0, T_RAIN1 = 9.0, 11.7
T_REACH = 22.9
T_TOUCH = 23.85            # CONSISTENT reaches his tape
T_KEYS1 = 3.0
T_JUICE1 = 5.5
T_SELFIE = 6.55            # the flash
T_FAN0, T_FAN1 = 7.6, 9.9
T_DRONE0, T_DRONE_HAND, T_DRONE1 = 9.9, 11.0, 12.2
T_EAT1 = 14.0
T_YAWN1 = 16.0
T_WATCH1 = 18.3
T_STAND1 = 19.0
T_WALK0, T_WALK1 = 19.55, 20.25
T_BOW = 20.45
T_WALK2 = 21.15
T_IN = 21.45
T_IGN = 22.0
T_LAUNCH = 23.2
T_CROSS = 23.55            # the car's nose breaks its tape
T_STOP = 23.78
T_STAMP = 24.1
T_RW = 25.8                # rewind into frame 0


def scene_t(t):
    if t < T_RW:
        return t
    u = prog(t, T_RW, DUR)
    return T_RW * (1 - smooth(u))


# ---------------------------------------------------------------- the roads
def zig_y(x):
    """the winding road of the middle lane (feet line)"""
    return FEET + 40 * math.sin(2 * math.pi * (x - START_X) / ((FIN_X - START_X) / 3))


def lane_x(frac):
    return START_X + frac * (FIN_X - START_X)


def depth(y):
    return S * (1 + (y - FEET) / 40 * 0.07)


# ---------------------------------------------------------------- poses (hip-relative, y up is negative)
STAND = PW.STAND
HANDS_HIP = dict(STAND, el=(-34, -74), hl=(-14, -34), er=(34, -74), hr=(14, -34))
LAUGH = dict(HANDS_HIP, head=(-8, -150), neck=(-4, -108))
BENT = {"head": (66, -112), "neck": (44, -82), "el": (50, -36), "hl": (34, 22), "er": (44, -40), "hr": (28, 18),
        "kl": (22, 54), "fl": (6, 113), "kr": (18, 56), "fr": (-4, 113)}
SIT_G = {"head": (-16, -138), "neck": (-10, -96), "el": (-32, -52), "hl": (-52, -4), "er": (-26, -48), "hr": (-46, 0),
         "kl": (52, -38), "fl": (104, -2), "kr": (46, -32), "fr": (100, 2)}
HOP = {"head": (18, -146), "neck": (12, -104), "el": (36, -62), "hl": (50, -16), "er": (30, -58), "hr": (46, -12),
       "kl": (8, 56), "fl": (2, 113), "kr": (48, -6), "fr": (24, 42)}
GRAB_HEAD = dict(STAND, el=(-40, -120), hl=(-12, -168), er=(40, -120), hr=(12, -168))
CHEER = dict(STAND, el=(-30, -130), hl=(-40, -180), er=(30, -130), hr=(40, -180))
RECLINE = {"head": (-64, -126), "neck": (-46, -90), "el": (-86, -112), "hl": (-58, -150), "er": (-8, -58),
           "hr": (26, -84), "kl": (58, -16), "fl": (116, -8), "kr": (56, -10), "fr": (114, -2)}
R_JUICE = dict(RECLINE, er=(-6, -76), hr=(-34, -118))
R_SELFIE = dict(RECLINE, er=(6, -116), hr=(34, -166))
R_FAN = dict(RECLINE, er=(-4, -84), hr=(-24, -126))
R_TAKE = dict(RECLINE, er=(10, -112), hr=(22, -160))
R_EAT = dict(RECLINE, er=(-6, -76), hr=(-36, -116))
R_YAWN = dict(RECLINE, el=(-76, -150), hl=(-70, -200), er=(-30, -150), hr=(-18, -202))
R_WATCH = dict(RECLINE, el=(-16, -70), hl=(-30, -120), er=(-10, -60), hr=(-26, -114))
STRETCH = CHEER


def run_pose(ph, amp):
    p = {}
    lean = 20 * amp
    p["neck"] = (lean, -104)
    p["head"] = (lean + 10 * amp, -146)
    for side, off in (("l", 0.0), ("r", math.pi)):
        s = math.sin(ph + off)
        a = 0.8 * amp * s
        kx, ky = 56 * math.sin(a), 56 * math.cos(a)
        bend = 0.15 + 1.4 * amp * max(0.0, -math.cos(ph + off))
        p["k" + side] = (kx, ky)
        p["f" + side] = (kx + 57 * math.sin(a - bend), ky + 57 * math.cos(a - bend))
        b = -0.95 * amp * s
        nx, ny = p["neck"]
        ex, ey = nx + 42 * math.sin(b), ny + 42 * math.cos(b)
        fb = b + 0.3 + 1.3 * amp
        p["e" + side] = (ex, ey)
        p["h" + side] = (ex + 40 * math.sin(fb), ey + 40 * math.cos(fb))
    return p


def walk_pose(ph, amp=0.3, base=STAND):
    p = dict(base)
    for side, off in (("l", 0.0), ("r", math.pi)):
        s = math.sin(ph + off)
        a = amp * s
        kx, ky = 56 * math.sin(a), 56 * math.cos(a)
        bend = 0.1 + 0.7 * max(0.0, -math.cos(ph + off))
        p["k" + side] = (kx, ky)
        p["f" + side] = (kx + 57 * math.sin(a - bend), ky + 57 * math.cos(a - bend))
    if base is STAND:
        for side, off in (("l", math.pi), ("r", 0.0)):
            b = -0.5 * amp / 0.3 * 0.6 * math.sin(ph + off)
            ex, ey = 42 * math.sin(b), -104 + 42 * math.cos(b)
            p["e" + side] = (ex, ey)
            p["h" + side] = (ex + 40 * math.sin(b + 0.35), ey + 40 * math.cos(b + 0.35))
    return p


# ---------------------------------------------------------------- the sprinter
def frac_s(t):
    if t < 4.2:
        u = t / 4.2
        return 0.50 * (1 - (1 - u) ** 2)
    if t < T_RUN2:
        return 0.50
    if t < T_CRAMP:
        u = prog(t, T_RUN2, T_CRAMP)
        return 0.50 + 0.24 * (u * u * (1.6 - 0.6 * u))
    if t < T_LIMP:
        return 0.74 + 0.01 * smooth(prog(t, T_CRAMP, T_FALL))
    return 0.75 + 0.115 * prog(t, T_LIMP, T_RW)


def sprinter(t):
    """pose, hip, facing, extra"""
    x = lane_x(frac_s(t))
    hip_y = FEET - 113 * S
    if t < 3.2 or T_RUN2 <= t < T_CRAMP:
        v = (frac_s(t + 0.02) - frac_s(t - 0.02)) / 0.04 * (FIN_X - START_X)
        amp = clamp(0.45 + v / 220, 0.45, 1.05)
        ph = 2 * math.pi * x / 72
        return run_pose(ph, amp), (x, hip_y - 7 * amp * abs(math.sin(ph))), 1, None
    if t < T_EASY0 + 0.35:
        k = smooth(prog(t, 3.2, T_EASY0 + 0.35))
        ph = 2 * math.pi * x / 72
        return lerp_pose(run_pose(ph, 0.45), STAND, k), (x, hip_y), 1, None
    if t < T_PANT:
        b = 4 * math.sin(t * 16)
        return dict(LAUGH, head=(-8 + b * 0.5, -150 + b)), (x, hip_y), -1, None
    if t < T_SIT:
        k = smooth(prog(t, T_PANT, T_PANT + 0.3))
        b = 5 * math.sin(t * 13)
        pose = lerp_pose(STAND, dict(BENT, head=(66, -112 + b), neck=(44, -82 + b * 0.6)), k)
        return pose, (x, hip_y + 4 * k), 1, "sweat"
    sit_hip = FEET - 12
    if t < T_LIE:
        k = smooth(prog(t, T_SIT, T_SIT + 0.5))
        return lerp_pose(BENT, SIT_G, k), (x, lerp(hip_y + 4, sit_hip, k)), 1, "sweat"
    if t < T_WAKE:
        k = smooth(prog(t, T_LIE, T_LIE + 0.45))
        br = 1.5 * math.sin(t * 2.4)
        lie = dict(STAND, head=(0, -150 + br), el=(-14, -62), hl=(-30, -20), er=(12, -62), hr=(22, -18))
        return lerp_pose(SIT_G, lie, k), (x, lerp(sit_hip, FEET - 16, k)), 1, ("lie", k * math.pi / 2)
    if t < T_RUN2:
        u = prog(t, T_WAKE, T_RUN2)
        jump = 60 * math.sin(math.pi * u)
        return lerp_pose(STAND, CHEER, math.sin(math.pi * u)), (x, hip_y - jump), 1, "panic"
    if t < T_FALL:
        hop = 18 * abs(math.sin((t - T_CRAMP) * 14))
        return HOP, (x, hip_y - hop), 1, "ow"
    if t < T_UP:
        k = smooth(prog(t, T_FALL, T_FALL + 0.15))
        return lerp_pose(HOP, SIT_G, k), (x, lerp(hip_y, sit_hip, k)), 1, "ow"
    if t < T_LIMP:
        k = smooth(prog(t, T_UP, T_LIMP))
        return lerp_pose(SIT_G, STAND, k), (x, lerp(sit_hip, hip_y, k)), 1, None
    ph = 2 * math.pi * x / 40
    p = walk_pose(ph, 0.3)
    dip = 12 * max(0.0, math.sin(ph))
    p["head"] = (6, -146 + dip * 0.3)
    p["neck"] = (4, -104)
    return p, (x, hip_y + dip), 1, "sweat"


# ---------------------------------------------------------------- the consistent one
_ZX = np.linspace(START_X, FIN_X + 120, 4000)
_ZY = np.array([zig_y(x) for x in _ZX])
_ZARC = np.concatenate([[0], np.cumsum(np.hypot(np.diff(_ZX), np.diff(_ZY)))])


def frac_c(t):
    if t < 0.15:
        return 0.0
    if t < T_REACH:
        return (t - 0.15) * 0.0416
    f0 = (T_REACH - 0.15) * 0.0416
    if t < T_TOUCH:
        return f0 + (1.0 - f0) * prog(t, T_REACH, T_TOUCH)
    return 1.0 + 0.07 * (1 - (1 - prog(t, T_TOUCH, T_TOUCH + 0.6)) ** 2)


def consistent(t):
    x = lane_x(frac_c(t))
    y = zig_y(x)
    s = depth(y)
    arc = float(np.interp(x, _ZX, _ZARC))
    ph = 2 * math.pi * arc / 62
    hip = (x, y - 113 * s)
    if t >= T_TOUCH + 0.6:
        k = smooth(prog(t, T_TOUCH + 0.6, T_TOUCH + 0.9))
        return lerp_pose(walk_pose(ph, 0.3), GRAB_HEAD, k), hip, 1, s
    p = walk_pose(ph, 0.3)
    if T_RAIN0 + 0.3 <= t < T_RAIN1:
        p["head"] = (12, -142)
        p["neck"] = (6, -104)
    if t >= T_REACH:
        k = smooth(prog(t, T_REACH, T_REACH + 0.4))
        p["er"] = lerp_pose({"a": p["er"]}, {"a": (44, -108)}, k)["a"]
        p["hr"] = lerp_pose({"a": p["hr"]}, {"a": (90, -112)}, k)["a"]
        p["head"] = (14, -146)
    return p, (hip[0], hip[1] - 3 * abs(math.sin(ph))), 1, s


# ---------------------------------------------------------------- the rich kid
CHAIR_X = 560
LOUNGE_Y = 478             # lounger feet (foreground grass)
KID_HIP = (CHAIR_X - 10, LOUNGE_Y - 68)
CAR_X0 = 220


def car_x(t):
    if t < T_LAUNCH:
        return CAR_X0
    if t < T_CROSS:
        u = prog(t, T_LAUNCH, T_CROSS)
        return CAR_X0 + 430 * u * u
    u = prog(t, T_CROSS, T_STOP)
    return CAR_X0 + 430 + 200 * (1 - (1 - u) ** 2)


def rich(t):
    """pose, hip, facing, prop (or None when he is in the car)"""
    hip = KID_HIP
    if t < T_KEYS1:
        return RECLINE, hip, 1, "keys"
    if t < T_JUICE1:
        k = math.sin(math.pi * prog(t, T_KEYS1, T_JUICE1))
        return lerp_pose(RECLINE, R_JUICE, min(1, k * 2)), hip, 1, "juice"
    if t < T_FAN0:
        k = math.sin(math.pi * prog(t, T_JUICE1, T_FAN0))
        return lerp_pose(RECLINE, R_SELFIE, min(1, k * 2)), hip, 1, "phone"
    if t < T_FAN1:
        k = math.sin(math.pi * prog(t, T_FAN0, T_FAN1))
        p = lerp_pose(RECLINE, R_FAN, min(1, k * 2.5))
        w = 16 * math.sin(t * 22) * min(1, k * 2.5)
        p["hr"] = (p["hr"][0] + w, p["hr"][1] + w * 0.3)
        return p, hip, 1, "cash"
    if t < T_DRONE_HAND:
        k = smooth(prog(t, T_DRONE_HAND - 0.5, T_DRONE_HAND))
        return lerp_pose(RECLINE, R_TAKE, k), hip, 1, "box" if t >= T_DRONE_HAND - 0.02 else None
    if t < T_EAT1:
        k = smooth(prog(t, T_DRONE_HAND, T_DRONE_HAND + 0.4))
        p = lerp_pose(R_TAKE, R_EAT, k)
        ch = 4 * math.sin(t * 18) if t > T_DRONE_HAND + 0.5 else 0
        p["head"] = (p["head"][0], p["head"][1] + ch)
        return p, hip, 1, "slice"
    if t < T_YAWN1:
        k = math.sin(math.pi * prog(t, T_EAT1, T_YAWN1))
        return lerp_pose(RECLINE, R_YAWN, min(1, k * 1.6)), hip, 1, None
    if t < T_WATCH1:
        k = math.sin(math.pi * prog(t, T_YAWN1, T_WATCH1))
        return lerp_pose(RECLINE, R_WATCH, min(1, k * 2.2)), hip, 1, "watch"
    st_hip = (CHAIR_X + 30, LOUNGE_Y - 113 * S)
    if t < T_STAND1:
        k = smooth(prog(t, T_WATCH1, T_STAND1))
        return lerp_pose(RECLINE, STAND, k), (lerp(hip[0], st_hip[0], k), lerp(hip[1], st_hip[1], k)), 1, None
    if t < T_WALK0:
        k = math.sin(math.pi * prog(t, T_STAND1, T_WALK0))
        return lerp_pose(STAND, STRETCH, k), st_hip, 1, None
    if t < T_WALK1:
        u = prog(t, T_WALK0, T_WALK1)
        x = lerp(st_hip[0], CAR_X0 + 70, smooth(u))
        y = lerp(st_hip[1], FEET - 113 * S + 30, smooth(u))
        return walk_pose(t * 9, 0.35), (x, y), -1, None
    bx, by = CAR_X0 + 70, FEET - 113 * S + 30
    if t < T_BOW + 0.35:
        k = math.sin(math.pi * prog(t, T_WALK1, T_BOW + 0.35))
        pull = dict(STAND, el=(30, -126), hl=(40, -176), er=(24, -120), hr=(34, -172))
        return lerp_pose(STAND, pull, k), (bx, by), -1, None
    if t < T_WALK2:
        u = prog(t, T_BOW + 0.35, T_WALK2)
        return walk_pose(t * 9, 0.35), (lerp(bx, CAR_X0 + 10, u), by), -1, None
    if t < T_IN:
        u = prog(t, T_WALK2, T_IN)
        return lerp_pose(STAND, CHEER, math.sin(math.pi * u)), (CAR_X0 + 10, by - 70 * math.sin(math.pi * u)), 1, "hop"
    return None


# ---------------------------------------------------------------- drawing helpers
def figure(d, pts, s, acc, facing=1, alpha=255):
    lw0, lw1 = 15 * s, 10 * s
    for w, col in ((lw0, INK), (lw1, WHITE)):
        for b0, b1 in [("neck", "hip"), ("neck", "el"), ("el", "hl"), ("neck", "er"), ("er", "hr"), ("hip", "kl"),
                       ("kl", "fl"), ("hip", "kr"), ("kr", "fr")]:
            (x0, y0), (x1, y1) = pts[b0], pts[b1]
            d.line([x0 * K, y0 * K, x1 * K, y1 * K], fill=col + (alpha,), width=int(w * K))
            for x, y in ((x0, y0), (x1, y1)):
                r = w * K / 2
                d.ellipse([x * K - r, y * K - r, x * K + r, y * K + r], fill=col + (alpha,))
    hx, hy = pts["head"]
    for r, col in ((30 * s, INK), (25.5 * s, WHITE)):
        d.ellipse([(hx - r) * K, (hy - r) * K, (hx + r) * K, (hy + r) * K], fill=col + (alpha,))
    f = facing
    if acc == "band":
        d.line([(hx - 25 * s) * K, (hy - 9 * s) * K, (hx + 25 * s) * K, (hy - 9 * s) * K], fill=RED + (255,),
               width=int(9 * s * K))
        for j in (0, 1):
            ex = hx - f * (24 + 26 + 6 * j) * s
            d.line([(hx - f * 22 * s) * K, (hy - 9 * s) * K, ex * K, (hy - 2 + 10 * j) * K], fill=RED + (255,),
                   width=int(6 * s * K))
    elif acc == "cap":
        d.chord([(hx - 27 * s) * K, (hy - 32 * s) * K, (hx + 27 * s) * K, (hy + 14 * s) * K], 180, 360,
                fill=(50, 110, 220, 255), outline=INK + (255,), width=int(3 * K))
        x0, x1 = (hx, hx + 42 * s) if f > 0 else (hx - 42 * s, hx)
        d.rectangle([x0 * K, (hy - 12 * s) * K, x1 * K, (hy - 4 * s) * K], fill=(50, 110, 220, 255),
                    outline=INK + (255,), width=int(2 * K))
    elif acc == "rich":
        x0, x1 = (hx - 4 * s, hx + 27 * s) if f > 0 else (hx - 27 * s, hx + 4 * s)
        d.rounded_rectangle([x0 * K, (hy - 10 * s) * K, x1 * K, (hy + 3 * s) * K], int(4 * K), fill=(15, 15, 20, 255))
        d.line([(hx - f * 24 * s) * K, (hy - 8 * s) * K, x0 * K if f > 0 else x1 * K, (hy - 7 * s) * K],
               fill=(15, 15, 20, 255), width=int(3 * K))
        nx, ny = pts["neck"]
        d.arc([(nx - 20 * s) * K, (ny - 16 * s) * K, (nx + 20 * s) * K, (ny + 20 * s) * K], 20, 160,
              fill=GOLD + (255,), width=int(5 * K))


def text_c(d, x, y, s, size, col, stroke=0, stroke_col=INK, a=255):
    f = font(BOLD, max(4, int(size * K)))
    tw = f.getlength(s)
    d.text((x * K - tw / 2, y * K), s, font=f, fill=col + (int(a),), stroke_width=int(stroke * K),
           stroke_fill=stroke_col + (int(a),))


def bubble(lay, t, t0, t1, s, x, y):
    if not (t0 <= t < t1):
        return
    k = hq.pop(t, t0, 0.22) * (1 - smooth(prog(t, t1 - 0.15, t1)))
    if k < 0.05:
        return
    f = font(BOLD, max(4, int(40 * K * k)))
    tw = f.getlength(s)
    bw, bh = tw + 44 * K * k, 70 * K * k
    d = ImageDraw.Draw(lay)
    x0, y0 = x * K - bw / 2, y * K - bh
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], int(16 * K * k), fill=(255, 255, 255, 250), outline=INK + (255,),
                        width=int(4 * K))
    d.polygon([(x * K - 14 * K * k, y0 + bh - 2), (x * K + 14 * K * k, y0 + bh - 2), (x * K - 4 * K * k, y0 + bh + 22 * K * k)],
              fill=(255, 255, 255, 250), outline=INK + (255,))
    d.text((x0 + 22 * K * k, y0 + 10 * K * k), s, font=f, fill=INK + (255,))


def stamp(base, t, t0, t1, s, col, x, y, size=78):
    if not (t0 <= t < t1):
        return
    k = hq.pop(t, t0, 0.28) * (1 - smooth(prog(t, t1 - 0.2, t1)))
    if k < 0.05:
        return
    f = font(BOLD, max(4, int(size * K * k)))
    tw = sum(f.getlength(c) for c in s) + 4 * K * k * (len(s) - 1)
    lay = Image.new("RGBA", (int(tw + 70 * K * k), int(size * 1.55 * K * k)), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle([0, 0, lay.width - 1, lay.height - 1], int(18 * K * k), fill=(255, 255, 255, 245),
                         outline=col + (255,), width=int(9 * K * k))
    xx = lay.width / 2 - tw / 2
    for c in s:
        ld.text((xx, lay.height / 2 - size * 0.62 * K * k), c, font=f, fill=col + (255,))
        xx += f.getlength(c) + 4 * K * k
    lay = lay.rotate(-6, resample=Image.BICUBIC, expand=True)
    base.alpha_composite(lay, (int(x * K - lay.width / 2), int(y * K - lay.height / 2)))


# ---------------------------------------------------------------- backgrounds
def make_bg(lane):
    a = np.zeros((PHT * K, PWD * K, 3), np.float32)
    yy = np.arange(PHT * K)[:, None] / K
    sky = np.clip(yy / HORIZON, 0, 1)
    c0, c1 = np.array([8, 12, 30]), np.array([30, 44, 86])
    g0, g1 = np.array([26, 38, 60]), np.array([12, 18, 32])
    gk = np.clip((yy - HORIZON) / (PHT - HORIZON), 0, 1)
    for c in range(3):
        a[..., c] = np.where(yy < HORIZON, c0[c] * (1 - sky) + c1[c] * sky, g0[c] * (1 - gk) + g1[c] * gk)
    im = Image.fromarray(a.astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    # stars, the moon and its halo, hills, trees
    rng = np.random.default_rng(lane + 3)
    for _ in range(90):
        x, y = rng.uniform(0, PWD), rng.uniform(0, HORIZON - 30)
        r = rng.uniform(0.7, 2.0)
        d.ellipse([(x - r) * K, (y - r) * K, (x + r) * K, (y + r) * K], fill=(220, 228, 255, int(rng.uniform(70, 220))))
    mx, my = 600, 92
    halo = Image.new("RGBA", im.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    for r, a_ in ((210, 14), (160, 18), (115, 26), (80, 34)):
        hd.ellipse([(mx - r) * K, (my - r) * K, (mx + r) * K, (my + r) * K], fill=(110, 140, 220, a_))
    im.alpha_composite(halo)
    d.ellipse([(mx - 46) * K, (my - 46) * K, (mx + 46) * K, (my + 46) * K], fill=(240, 236, 214, 255))
    for cx, cy, r in ((-14, -10, 10), (12, 8, 8), (-6, 18, 6), (16, -16, 5)):
        d.ellipse([(mx + cx - r) * K, (my + cy - r) * K, (mx + cx + r) * K, (my + cy + r) * K], fill=(214, 208, 186, 255))
    d.polygon([(0, (HORIZON - 40) * K), (200 * K, (HORIZON - 90) * K), (420 * K, (HORIZON - 30) * K),
               (650 * K, (HORIZON - 100) * K), (880 * K, (HORIZON - 40) * K), (PWD * K, (HORIZON - 80) * K),
               (PWD * K, HORIZON * K), (0, HORIZON * K)], fill=(14, 20, 38, 255))
    for j in range(9):
        tx = 40 + j * 125 + rng.uniform(-20, 20)
        ty = HORIZON + 6
        d.rectangle([(tx - 5) * K, (ty - 30) * K, (tx + 5) * K, ty * K], fill=(10, 14, 26, 255))
        d.ellipse([(tx - 24) * K, (ty - 74) * K, (tx + 24) * K, (ty - 22) * K], fill=(12, 18, 32, 255))
    # the road
    if lane == 1:
        xs = np.linspace(-40, PWD + 40, 600)
        pts = [(x * K, (zig_y(x) if START_X - 30 <= x else zig_y(START_X - 30)) * K) for x in xs]
        d.line(pts, fill=INK + (255,), width=int(66 * K), joint="curve")
        d.line(pts, fill=(84, 80, 98, 255), width=int(58 * K), joint="curve")
        for j, (px, py) in enumerate(pts[::12]):
            d.ellipse([px - 3 * K, py - 3 * K, px + 3 * K, py + 3 * K], fill=(54, 54, 68, 255))
    else:
        d.rectangle([0, (FEET - 38) * K, PWD * K, (FEET + 26) * K], fill=(34, 38, 54, 255), outline=INK + (255,),
                    width=int(3 * K))
        for x in range(0, PWD, 90):
            d.rectangle([x * K, (FEET - 8) * K, (x + 44) * K, (FEET - 3) * K], fill=(170, 180, 210, 170))
    # grass tufts in the foreground
    for j in range(40):
        gx, gy = rng.uniform(0, PWD), rng.uniform(FEET + 40, PHT - 6)
        if lane == 1 and abs(gy - zig_y(gx)) < 62:
            continue
        for dx in (-5, 0, 5):
            d.line([gx * K, gy * K, (gx + dx * 1.6) * K, (gy - 14) * K], fill=(36, 54, 70, 255), width=int(2 * K))
    # start line
    fy = zig_y(START_X) if lane == 1 else FEET
    d.polygon([((START_X - 6 + 18) * K, (fy - 34) * K), ((START_X + 6 + 18) * K, (fy - 34) * K),
               ((START_X + 6 - 14) * K, (fy + 24) * K), ((START_X - 6 - 14) * K, (fy + 24) * K)], fill=(255, 255, 255, 255))
    # finish: checkered strip on the road, a tall flag
    fy = zig_y(FIN_X) if lane == 1 else FEET
    for r in range(6):
        for c in range(2):
            y0 = fy - 34 + r * 10
            x0 = FIN_X + 18 - (r * 10) * 0.55 + c * 12 - 6
            col = (255, 255, 255, 255) if (r + c) % 2 == 0 else (20, 20, 24, 255)
            d.polygon([(x0 * K, y0 * K), ((x0 + 12) * K, y0 * K), ((x0 + 12 - 5.5) * K, (y0 + 10) * K),
                       ((x0 - 5.5) * K, (y0 + 10) * K)], fill=col)
    vy, vx = np.mgrid[0:PHT * K:4, 0:PWD * K:4].astype(np.float32)
    r = np.sqrt(((vx - PWD * K / 2) / (PWD * K)) ** 2 + ((vy - PHT * K / 2) / (PHT * K)) ** 2)
    vig = Image.fromarray((np.clip((r - 0.3) * 1.5, 0, 1) * 150).astype(np.uint8), "L").resize(im.size)
    v = Image.new("RGBA", im.size, (0, 0, 0, 255))
    v.putalpha(vig)
    im.alpha_composite(v)
    return im


def finish_poles(d, lane, broken_at, t):
    fy = zig_y(FIN_X) if lane == 1 else FEET
    back = (FIN_X + 22, fy - 34)
    front = (FIN_X - 14, fy + 26)
    # back pole + flag
    d.rectangle([(back[0] - 4) * K, (back[1] - 250) * K, (back[0] + 4) * K, back[1] * K], fill=(240, 240, 240, 255),
                outline=INK + (255,), width=int(2 * K))
    wav = 6 * math.sin(t * 5)
    for r in range(4):
        for c in range(6):
            x0 = back[0] + 4 + c * 16
            y0 = back[1] - 250 + r * 15 + wav * c / 6
            col = (255, 255, 255, 255) if (r + c) % 2 == 0 else (20, 20, 24, 255)
            d.rectangle([x0 * K, y0 * K, (x0 + 16) * K, (y0 + 15) * K], fill=col)
    d.rectangle([(back[0] + 4) * K, (back[1] - 250 + wav * 0) * K, (back[0] + 100) * K, (back[1] - 190 + wav) * K],
                outline=INK + (255,), width=int(2 * K))
    # tape between the posts at chest height
    hb = (back[0], back[1] - 130)
    hf = (front[0], front[1] - 130)
    if broken_at is None or t < broken_at:
        d.line([hb[0] * K, hb[1] * K, hf[0] * K, hf[1] * K], fill=RED + (255,), width=int(7 * K))
    else:
        u = clamp((t - broken_at) / 0.4)
        sw = 1 - u
        for p0, sgn in ((hb, 1), (hf, -1)):
            ang = math.pi / 2 * (0.3 + 0.7 * u)
            L = 70
            ex = p0[0] + sgn * L * math.cos(ang) * 0.8 + 30 * sw
            ey = p0[1] + L * math.sin(ang)
            d.line([p0[0] * K, p0[1] * K, ex * K, ey * K], fill=RED + (255,), width=int(7 * K))
    return front


def front_pole(d, front):
    d.rectangle([(front[0] - 5) * K, (front[1] - 150) * K, (front[0] + 5) * K, front[1] * K],
                fill=(240, 240, 240, 255), outline=INK + (255,), width=int(2 * K))


# ---------------------------------------------------------------- props
def draw_car(d, cx, gy, t, bow, driver, vib=0.0, moving=0.0):
    cy = gy - 4 * vib * math.sin(t * 60)
    P = lambda x, y: ((cx + x) * K, (cy + y) * K)  # noqa
    if moving > 0.05:
        for j in range(6):
            y = -30 - j * 14
            L = 120 + 60 * (j % 2)
            d.line([P(-170 - L * moving, y), P(-160, y)], fill=(255, 255, 255, int(200 * moving)), width=int(4 * K))
    body = [(-152, -36), (152, -36), (158, -58), (70, -78), (10, -118), (-66, -118), (-126, -86), (-156, -80)]
    d.polygon([P(*p) for p in body], fill=CAR + (255,), outline=INK + (255,), width=int(4 * K))
    d.line([P(-140, -60), P(140, -60)], fill=(255, 110, 110, 255), width=int(4 * K))
    if driver:
        hx, hy = cx - 22, cy - 96
        d.ellipse([(hx - 22) * K, (hy - 22) * K, (hx + 22) * K, (hy + 22) * K], fill=WHITE + (255,),
                  outline=INK + (255,), width=int(3 * K))
        d.rounded_rectangle([(hx - 2) * K, (hy - 8) * K, (hx + 21) * K, (hy + 2) * K], int(3 * K), fill=(15, 15, 20, 255))
    win = [(58, -80), (6, -112), (-60, -112), (-104, -82)]
    d.polygon([P(*p) for p in win], fill=(150, 210, 245, 95), outline=INK + (255,), width=int(3 * K))
    d.line([P(-24, -112), P(-24, -80)], fill=INK + (255,), width=int(3 * K))
    d.rectangle([P(-160, -100), P(-118, -92)], fill=(40, 40, 46, 255))
    d.line([P(-138, -92), P(-132, -84)], fill=(40, 40, 46, 255), width=int(4 * K))
    d.ellipse([P(140, -58), P(156, -46)], fill=(255, 240, 150, 255), outline=INK + (255,), width=int(2 * K))
    for wx in (-96, 100):
        r = 31
        d.ellipse([P(wx - r, -r - 2), P(wx + r, r - 2)], fill=(24, 24, 28, 255), outline=INK + (255,), width=int(2 * K))
        d.ellipse([P(wx - 15, -17), P(wx + 15, 13)], fill=(190, 194, 204, 255))
        rot = -t * 40 * moving - (cx / 31)
        for j in range(5):
            a = rot + j * 2 * math.pi / 5
            d.line([P(wx, -2), P(wx + 14 * math.cos(a), -2 + 14 * math.sin(a))], fill=(90, 94, 104, 255),
                   width=int(3 * K))
    if bow is not None:
        bx, by, ang, al = bow
        if al > 0.02:
            a = int(255 * al)
            band = [(-30, -118), (-16, -118), (-14, -36), (-32, -36)]
            if bx is None:
                d.polygon([P(*p) for p in band], fill=GOLD + (a,), outline=INK + (a,))
                bx, by = cx - 23, cy - 122
            c, s = math.cos(ang), math.sin(ang)

            def Q(x, y):
                return ((bx + x * c - y * s) * K, (by + x * s + y * c) * K)
            for sg in (-1, 1):
                d.polygon([Q(0, 0), Q(sg * 46, -36), Q(sg * 54, 6)], fill=(255, 90, 160, a), outline=INK + (a,),
                          width=int(3 * K))
                d.line([Q(0, 0), Q(sg * 26, 34)], fill=(255, 90, 160, a), width=int(8 * K))
            d.ellipse([Q(-12, -12)[0], Q(-12, -12)[1], Q(12, 12)[0], Q(12, 12)[1]] if abs(ang) < 1e-3 else
                      [(bx - 12) * K, (by - 12) * K, (bx + 12) * K, (by + 12) * K], fill=(230, 60, 140, a),
                      outline=INK + (a,), width=int(3 * K))


def lounger(d):
    x, y = CHAIR_X, LOUNGE_Y
    d.line([(x - 120) * K, y * K, (x - 100) * K, (y - 44) * K], fill=INK + (255,), width=int(5 * K))
    d.line([(x + 110) * K, y * K, (x + 94) * K, (y - 44) * K], fill=INK + (255,), width=int(5 * K))
    d.polygon([((x - 110) * K, (y - 58) * K), ((x + 120) * K, (y - 58) * K), ((x + 120) * K, (y - 42) * K),
               ((x - 110) * K, (y - 42) * K)], fill=(255, 140, 60, 255), outline=INK + (255,))
    d.polygon([((x - 60) * K, (y - 58) * K), ((x - 46) * K, (y - 46) * K), ((x - 112) * K, (y - 168) * K),
               ((x - 128) * K, (y - 158) * K)], fill=(255, 140, 60, 255), outline=INK + (255,))
    for j in range(1, 5):
        xx = x - 110 + j * 46
        d.line([xx * K, (y - 58) * K, xx * K, (y - 42) * K], fill=(255, 220, 120, 255), width=int(4 * K))


def keys(d, hx, hy, t):
    a = t * 14
    kx, ky = hx + 32 * math.cos(a), hy + 32 * math.sin(a)
    d.ellipse([(hx - 14) * K, (hy - 14) * K, (hx + 14) * K, (hy + 14) * K], outline=GOLD + (255,), width=int(5 * K))
    d.line([hx * K, hy * K, kx * K, ky * K], fill=GOLD + (255,), width=int(5 * K))
    d.rounded_rectangle([(kx - 18) * K, (ky - 11) * K, (kx + 18) * K, (ky + 11) * K], int(5 * K), fill=(20, 20, 24, 255),
                        outline=GOLD + (255,), width=int(3 * K))
    d.ellipse([(kx + 4) * K, (ky - 4) * K, (kx + 12) * K, (ky + 4) * K], fill=(255, 60, 60, 255))


def drone(d, x, y, t, box):
    for sx in (-38, 38):
        d.ellipse([(x + sx - 30) * K, (y - 20) * K, (x + sx + 30) * K, (y - 10) * K], fill=(200, 200, 210, 140))
        d.line([(x + sx) * K, (y - 15) * K, (x + sx) * K, y * K], fill=INK + (255,), width=int(3 * K))
    d.rounded_rectangle([(x - 40) * K, (y - 2) * K, (x + 40) * K, (y + 14) * K], int(6 * K), fill=(60, 64, 76, 255),
                        outline=INK + (255,), width=int(2 * K))
    d.ellipse([(x + 26) * K, (y + 2) * K, (x + 34) * K, (y + 10) * K], fill=(255, 60, 60, 255))
    if box:
        d.line([x * K, (y + 14) * K, x * K, (y + 40) * K], fill=INK + (255,), width=int(2 * K))
        pizza_box(d, x, y + 52)


def pizza_box(d, x, y, sc=1.0):
    d.rectangle([(x - 34 * sc) * K, (y - 12 * sc) * K, (x + 34 * sc) * K, (y + 12 * sc) * K], fill=(230, 200, 150, 255),
                outline=INK + (255,), width=int(3 * K))
    text_c(d, x, y - 10 * sc, "PIZZA", 14 * sc, (200, 40, 40))


def slice_(d, x, y):
    d.polygon([((x - 14) * K, (y - 10) * K), ((x + 18) * K, (y - 16) * K), ((x + 2) * K, (y + 22) * K)],
              fill=(255, 200, 70, 255), outline=INK + (255,), width=int(2 * K))
    d.line([(x - 14) * K, (y - 10) * K, (x + 18) * K, (y - 16) * K], fill=(200, 130, 60, 255), width=int(6 * K))
    for px, py in ((x, y - 4), (x + 6, y + 6)):
        d.ellipse([(px - 4) * K, (py - 4) * K, (px + 4) * K, (py + 4) * K], fill=(220, 50, 40, 255))


def cash_fan(d, x, y, t):
    for j in range(5):
        a = -0.9 + j * 0.42
        ex, ey = x + 46 * math.sin(a), y - 46 * math.cos(a)
        d.line([x * K, y * K, ex * K, ey * K], fill=(70, 160, 80, 255), width=int(18 * K))
        d.line([x * K, y * K, ex * K, ey * K], fill=(150, 220, 140, 255), width=int(10 * K))
    text_c(d, x, y - 40, "$", 22, (30, 100, 40))


def zzz(d, x, y, t):
    for j in range(3):
        u = ((t * 0.7 + j / 3) % 1.0)
        a = int(255 * math.sin(math.pi * u))
        text_c(d, x + 20 + 40 * u, y - 30 - 90 * u, "Z", 30 + 22 * u, (255, 255, 255), stroke=4, a=a)


def sweat(d, pts, t, f):
    hx, hy = pts["head"]
    for j in range(2):
        u = (t * 1.8 + j * 0.5) % 1.0
        x, y = hx - f * (30 + 14 * u) + j * 10, hy - 10 + 40 * u
        a = int(255 * (1 - u))
        d.polygon([(x * K, (y - 9) * K), ((x + 6) * K, (y + 3) * K), ((x - 6) * K, (y + 3) * K)],
                  fill=(120, 200, 255, a))
        d.ellipse([(x - 6) * K, (y - 2) * K, (x + 6) * K, (y + 9) * K], fill=(120, 200, 255, a))


def rain(d, cx, t, t0, t1):
    if not (t0 <= t < t1):
        return
    a = smooth(prog(t, t0, t0 + 0.4)) * (1 - smooth(prog(t, t1 - 0.4, t1)))
    cy = 70
    for dx, dy, r in ((-60, 10, 36), (-20, -6, 46), (30, 0, 44), (72, 12, 32)):
        d.ellipse([(cx + dx - r) * K, (cy + dy - r * 0.8) * K, (cx + dx + r) * K, (cy + dy + r * 0.8) * K],
                  fill=(120, 126, 140, int(250 * a)), outline=INK + (int(255 * a),), width=int(3 * K))
    rng = np.random.default_rng(7)
    for j in range(34):
        x0 = cx + rng.uniform(-110, 110)
        sp = rng.uniform(500, 700)
        ph = rng.uniform(0, 1)
        y = 100 + ((t * sp / 400 + ph) % 1.0) * 340
        d.line([x0 * K, y * K, (x0 - 6) * K, (y + 22) * K], fill=(90, 150, 230, int(230 * a)), width=int(3 * K))


# ---------------------------------------------------------------- panel
BGS = None


def tag(base, lab):
    tl = ImageDraw.Draw(base)
    f = font("Inter-SemiBold.otf", int(34 * K))
    x = 30 * K
    for c in lab:
        tl.text((x, 20 * K), c, font=f, fill=(196, 204, 226, 255))
        x += f.getlength(c) + 9 * K


def panel(t, st, lane):
    base = BGS[lane].copy()
    lay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    ev = []
    if lane == 0:
        broken = None
        front = finish_poles(d, 0, broken, st)
        pose, hip, f, extra = sprinter(st)
        if isinstance(extra, tuple):
            pts = AJ.place(pose, hip, f, S, extra[1])
        else:
            pts = AJ.place(pose, hip, f, S)
        # running dust
        if st < 3.2 or T_RUN2 <= st < T_CRAMP:
            for j in range(4):
                u = ((st * 3 + j / 4) % 1.0)
                px = hip[0] - 40 - 80 * u
                r = 8 + 16 * u
                d.ellipse([(px - r) * K, (FEET - r) * K, (px + r) * K, (FEET + r * 0.5) * K],
                          fill=(230, 220, 200, int(170 * (1 - u))))
        figure(d, pts, S, "band", f)
        front_pole(d, front)
        if extra == "sweat":
            sweat(d, pts, st, f)
        if isinstance(extra, tuple) and st > T_LIE + 0.6:
            zzz(d, pts["head"][0], pts["head"][1], st)
        if extra == "panic":
            k = hq.pop(st, T_WAKE, 0.2)
            text_c(d, pts["head"][0] + 10, pts["head"][1] - 120 * k, "!", 90 * k + 4, RED, stroke=5)
        bubble(lay, st, T_EASY0, T_EASY1, "EASY!", pts["head"][0] - 10, pts["head"][1] - 40)
        bubble(lay, st, T_CRAMP + 0.05, T_LIMP - 0.1, "OW!", pts["head"][0] + 20, pts["head"][1] - 40)
        ev = [T_CRAMP, T_FALL]
    elif lane == 1:
        front = finish_poles(d, 1, T_TOUCH, st)
        pose, hip, f, s = consistent(st)
        pts = AJ.place(pose, hip, f, s)
        figure(d, pts, s, "cap", f)
        if not (T_TOUCH - 0.1 < st):
            pass
        front_pole(d, front)
        rain(d, pts["head"][0], st, T_RAIN0, T_RAIN1)
        if T_RAIN0 + 0.3 <= st < T_RAIN1:
            for j in range(3):
                u = ((st * 2.2 + j / 3) % 1.0)
                fx = pts["fl"][0] if j % 2 else pts["fr"][0]
                fy = max(pts["fl"][1], pts["fr"][1])
                r = 8 + 26 * u
                d.ellipse([(fx - r) * K, (fy - r * 0.25) * K, (fx + r) * K, (fy + r * 0.25) * K],
                          outline=(220, 240, 255, int(220 * (1 - u))), width=int(2 * K))
        if st >= T_REACH - 0.6:
            sweat(d, pts, st, f)
        ev = [T_TOUCH]
    else:
        front = finish_poles(d, 2, T_CROSS, st)
        cx = car_x(st)
        moving = clamp((cx - CAR_X0) / 200) * (1 - smooth(prog(st, T_CROSS + 0.05, T_STOP + 0.25)))
        vib = 1.0 if T_IGN <= st < T_LAUNCH + 0.2 else 0.0
        # the bow: on the car, then thrown off
        if st < T_BOW:
            bow = (None, None, 0.0, 1.0)
        else:
            u = prog(st, T_BOW, T_BOW + 0.9)
            bow = (CAR_X0 - 23 - 160 * u, FEET - 122 - 220 * u + 260 * u * u, 6 * u, 1 - smooth(prog(st, T_BOW + 0.6, T_BOW + 0.9)))
        driver = st >= T_IN
        # exhaust puffs
        if st >= T_IGN:
            for j in range(5):
                u = ((st * (1.6 if st < T_LAUNCH else 0.8) + j / 5) % 1.0)
                if st > T_STOP + 0.6:
                    break
                px, py = cx - 160 - 60 * u, FEET - 40 - 20 * u
                r = 8 + 22 * u
                d.ellipse([(px - r) * K, (py - r) * K, (px + r) * K, (py + r) * K], fill=(220, 220, 226, int(170 * (1 - u))))
        if st >= T_STOP - 0.1 and st < T_STOP + 1.2:
            u = prog(st, T_STOP - 0.1, T_STOP + 1.2)
            for j in range(5):
                px = cx - 40 - j * 40 - 60 * u
                r = 20 + 30 * u
                d.ellipse([(px - r) * K, (FEET - 20 - r * 0.6) * K, (px + r) * K, (FEET - 20 + r * 0.4) * K],
                          fill=(230, 230, 236, int(200 * (1 - u))))
        draw_car(d, cx, FEET + 30, st, bow, driver, vib, moving)
        front_pole(d, front)
        lounger(d)
        rs = rich(st)
        if rs is not None:
            pose, hip, f, prop = rs
            pts = AJ.place(pose, hip, f, S)
            figure(d, pts, S, "rich", f)
            hx, hy = pts["hr"]
            if prop == "keys":
                keys(d, hx, hy - 10, st)
            elif prop == "juice":
                d.rounded_rectangle([(hx - 12) * K, (hy - 14) * K, (hx + 12) * K, (hy + 22) * K], int(4 * K),
                                    fill=(255, 160, 40, 255), outline=INK + (255,), width=int(2 * K))
                d.line([(hx + 4) * K, (hy - 14) * K, (hx - 8) * K, (hy - 36) * K], fill=(255, 80, 120, 255), width=int(4 * K))
            elif prop == "phone":
                d.rounded_rectangle([(hx - 12) * K, (hy - 20) * K, (hx + 12) * K, (hy + 18) * K], int(4 * K),
                                    fill=(20, 20, 26, 255))
                if T_SELFIE <= st < T_SELFIE + 0.25:
                    k = 1 - prog(st, T_SELFIE, T_SELFIE + 0.25)
                    for r in (90, 60, 34):
                        d.ellipse([(hx - r) * K, (hy - r) * K, (hx + r) * K, (hy + r) * K], fill=(255, 255, 255, int(110 * k)))
            elif prop == "cash":
                cash_fan(d, hx, hy, st)
            elif prop == "box":
                pizza_box(d, hx, hy - 12)
            elif prop == "slice":
                slice_(d, hx, hy)
            elif prop == "watch":
                lx, ly = pts["hl"]
                d.rounded_rectangle([(lx - 12) * K, (ly - 6) * K, (lx + 12) * K, (ly + 14) * K], int(4 * K),
                                    fill=GOLD + (255,), outline=INK + (255,), width=int(2 * K))
                if st > T_YAWN1 + 0.6:
                    text_c(d, lx + 10, ly - 110, "...", 40, INK)
            if prop not in ("keys",) and st < T_KEYS1 + 0.2:
                pass
        # the drone with the pizza
        if T_DRONE0 <= st < T_DRONE1:
            hx0, hy0 = AJ.place(R_TAKE, KID_HIP, 1, S)["hr"]
            if st < T_DRONE_HAND:
                u = smooth(prog(st, T_DRONE0, T_DRONE_HAND))
                x, y = lerp(1120, hx0, u), lerp(-60, hy0 - 64, u)
                drone(d, x, y, st, True)
            else:
                u = smooth(prog(st, T_DRONE_HAND, T_DRONE1))
                drone(d, lerp(hx0, 1140, u), lerp(hy0 - 64, -80, u), st, False)
        hq.confetti(_Pp(d), st, T_CROSS, T_CROSS + 0.6, FIN_X, 140, 5, 50)
        ev = [T_IGN, T_LAUNCH, T_STOP]
    g = lay.resize((lay.width // 4, lay.height // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(5))
    ga = g.split()[3].point(lambda v: int(v * 0.55))
    glow = Image.new("RGBA", g.size, (150, 180, 255, 0))
    glow.putalpha(ga)
    base.alpha_composite(glow.resize(lay.size, Image.BILINEAR))
    base.alpha_composite(lay)
    if lane == 2 and T_CROSS <= st < T_CROSS + 0.2:
        fl = Image.new("RGBA", base.size, (255, 255, 255, int(120 * (1 - prog(st, T_CROSS, T_CROSS + 0.2)))))
        base.alpha_composite(fl)
    tag(base, ["SPRINTER", "CONSISTENT", "RICH KID"][lane])
    # answer stamps (held to the end), gone before the rewind
    if t < T_RW:
        if lane == 0:
            stamp(base, t, T_STAMP + 0.3, T_RW, "TIRED", GREY, 470, 110)
        elif lane == 1:
            stamp(base, t, T_STAMP + 0.15, T_RW, "2ND", (200, 120, 30), 560, 110)
        else:
            stamp(base, t, T_STAMP, T_RW, "1ST", GREEN, 470, 110, 96)
    im = hq.downsample(base, PWD, PHT)
    dx, dy = hq.shake(st, ev, 9) if t < T_RW else (0.0, 0.0)
    z = 1.0 + 0.04 * math.sin(math.pi * st / T_RW)
    im = hq.camera(im, z, dx, dy)
    ImageDraw.Draw(im).rounded_rectangle([1, 1, PWD - 2, PHT - 2], 16, outline=(44, 54, 88, 255), width=3)
    return im


class _Pp:
    """adapter so hq.confetti can draw on our 2x layer"""

    def __init__(self, d):
        self.ds = d


def title(img):
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(11)
    for _ in range(140):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        r = rng.uniform(0.6, 1.6)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(210, 220, 255, int(rng.uniform(40, 170))))
    PW.spaced(d, W / 2, 18, "WHO WINS?", font("InterDisplay-Bold.otf", 78), (240, 242, 250, 255), 10)
    PW.spaced(d, W / 2, 116, "DISTANCE  ( M )", font("Inter-SemiBold.otf", 26), (150, 158, 184, 255), 9)


COLS = [(190, "SPRINTER"), (540, "CONSISTENT"), (890, "RICH KID")]


def meters(st):
    car = clamp((car_x(st) - CAR_X0) / 430)
    return [min(100, frac_s(st) * 100), min(100, frac_c(st) * 100), car * 100]


def counter(img, st, t):
    d = ImageDraw.Draw(img)
    m = meters(st)
    lead = max(range(3), key=lambda i: (m[i], -i))
    if m[2] >= 100:
        lead = 2
    fnum = font("InterDisplay-Bold.otf", 92)
    flab = font("Inter-SemiBold.otf", 24)
    for i, (cx, lab) in enumerate(COLS):
        v = int(m[i])
        win = i == 2 and v >= 100 and t < T_RW + 0.3
        col = GOLD if win else ((245, 246, 252) if i == lead else (128, 136, 160))
        PW.spaced(d, cx, 148, str(v), fnum, col + (255,), 2)
        PW.spaced(d, cx, 254, lab, flab, ((230, 232, 242) if i == lead else (128, 136, 160)) + (255,), 6)


TITLE = None


def frame(t):
    st = scene_t(t)
    img = TITLE.copy()
    counter(img, st, t)
    for lane in range(3):
        img.alpha_composite(panel(t, st, lane), (PX0, PANEL_Y[lane]))
    if t >= T_RW:
        # rewind look: a ◀◀ icon and tracking lines
        d = ImageDraw.Draw(img)
        a = int(230 * min(1, prog(t, T_RW, T_RW + 0.1)) * (1 - prog(t, DUR - 0.12, DUR)))
        cx, cy = W / 2, PANEL_Y[1] + PHT / 2
        d.rounded_rectangle([cx - 110, cy - 70, cx + 110, cy + 70], 20, fill=(0, 0, 0, int(a * 0.5)))
        for ox in (-46, 14):
            d.polygon([(cx + ox + 40, cy - 44), (cx + ox + 40, cy + 44), (cx + ox - 20, cy)], fill=(255, 255, 255, a))
        rng = np.random.default_rng(int(t * 30))
        for _ in range(3):
            y = rng.uniform(PANEL_Y[0], H - 200)
            d.rectangle([0, y, W, y + rng.uniform(3, 9)], fill=(255, 255, 255, int(a * 0.35)))
    return np.asarray(img.convert("RGB"))


def init_worker():
    global BGS, TITLE
    BGS = [make_bg(i) for i in range(3)]
    TITLE = Image.new("RGBA", (W, H), NIGHT + (255,))
    title(TITLE)


def render(i):
    return frame(i / FPS).tobytes()


# ---------------------------------------------------------------- sound
def engine(dur, f0, f1, curve=1.0, rough=0.25, seed=0):
    n = int(dur * SR)
    u = (np.arange(n) / n) ** curve
    f = f0 + (f1 - f0) * u
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = sum(np.sin(k * ph) / k for k in range(1, 9))
    x += rough * noise(dur, seed, lo=60, hi=2000)
    return x / (np.abs(x).max() + 1e-9)


def step(fx, at, g, pan, hi=False):
    mix_in(fx, tone(160 if not hi else 210, 0.07, (1, 0.5), a=0.001, d=0.025) +
           0.4 * noise(0.07, int(at * 1000) % 9999, lo=300, hi=3000) * env(int(0.07 * SR), 0.001, 0.015), at, g, pan)


def audio():
    n = int(DUR * SR)
    fx = np.zeros((n, 2))
    mus = music.score(MUSIC, DUR, t_end=T_CROSS - 0.35, t_warm=T_CROSS + 0.05, t_line=T_STAMP + 0.1, start=0.0, loud=1.0)
    # birds + breeze bed, continuous (the loop stays seamless)
    bed = noise(DUR, 3, lo=150, hi=1200)
    fx[:, 0] += 0.02 * bed
    fx[:, 1] += 0.02 * bed
    for t0 in (1.6, 8.3, 13.1, 19.4):
        for k2 in range(3):
            mix_in(fx, tone(2700 + 250 * k2, 0.07, (1,), a=0.003, d=0.035, sweep=3300), t0 + k2 * 0.11, 0.018, 0.5)
    # frame 0: the starting pistol
    mix_in(fx, noise(0.5, 1, lo=200, hi=8000) * env(int(0.5 * SR), 0.0005, 0.07), 0.0, 0.32)
    mix_in(fx, tone(90, 0.4, (1, 0.5), a=0.001, d=0.15), 0.0, 0.25)
    # sprinter's steps (fast, then the second sprint), CONSISTENT's steady steps under everything
    t0 = 0.05
    while t0 < 3.2:
        step(fx, t0, 0.07, -0.3, True)
        x = lane_x(frac_s(t0))
        t0 += max(0.11, 36 / max(30, (frac_s(t0 + 0.05) - frac_s(t0)) / 0.05 * 710))
    t0 = T_RUN2
    while t0 < T_CRAMP:
        step(fx, t0, 0.07, -0.3, True)
        t0 += 0.13
    t0 = 0.3
    while t0 < T_TOUCH:
        step(fx, t0, 0.03, 0.1)
        t0 += 0.5
    # "EASY!" pop, panting, snoring
    mix_in(fx, tone(880, 0.1, (1, 0.4), a=0.002, d=0.05, sweep=1200), T_EASY0, 0.05)
    for j in range(5):
        mix_in(fx, noise(0.22, 20 + j, lo=500, hi=3000) * np.sin(np.linspace(0, np.pi, int(0.22 * SR))),
               T_PANT + 0.1 + j * 0.32, 0.05, -0.3)
    t0 = T_LIE + 0.6
    while t0 < T_WAKE - 0.6:
        sn = noise(1.0, int(t0 * 10), lo=80, hi=500) * np.sin(np.linspace(0, np.pi, SR)) ** 2
        mix_in(fx, sn, t0, 0.07, -0.3)
        t0 += 1.8
    # the wake: alarm-ish sting
    for j, m in enumerate((84, 88, 84)):
        mix_in(fx, tone(midi(m), 0.09, (1, 0.5), a=0.001, d=0.05), T_WAKE + j * 0.08, 0.05)
    # cramp + fall
    mix_in(fx, tone(300, 0.35, (1, 0.6), a=0.002, d=0.2, sweep=110), T_CRAMP, 0.08, -0.3)
    mix_in(fx, tone(70, 0.4, (1, 0.5), a=0.002, d=0.18) + 0.3 * noise(0.4, 77, lo=100, hi=2000) *
           env(int(0.4 * SR), 0.002, 0.08), T_FALL, 0.2, -0.3)
    # rain
    rn = noise(T_RAIN1 - T_RAIN0, 9, lo=800, hi=9000)
    m = len(rn)
    rn *= np.minimum(1, np.minimum(np.arange(m), m - np.arange(m)) / (0.4 * SR))
    mix_in(fx, rn, T_RAIN0, 0.05, 0.1)
    # rich kid: keys jingle, slurp, shutter, cash flutter, drone, munching, watch ticks
    for j in range(8):
        mix_in(fx, tone(3200 + 400 * (j % 3), 0.05, (1, 0.6), a=0.001, d=0.03), 0.15 + j * 0.34, 0.02, 0.4)
    mix_in(fx, noise(0.6, 31, lo=1500, hi=6000) * env(int(0.6 * SR), 0.05, 0.2), T_KEYS1 + 0.9, 0.04, 0.4)
    mix_in(fx, noise(0.12, 32, lo=1000, hi=8000) * env(int(0.12 * SR), 0.001, 0.03), T_SELFIE, 0.12, 0.4)
    mix_in(fx, noise(0.12, 33, lo=1000, hi=8000) * env(int(0.12 * SR), 0.001, 0.03), T_SELFIE + 0.07, 0.08, 0.4)
    for j in range(10):
        mix_in(fx, noise(0.08, 40 + j, lo=1200, hi=7000) * env(int(0.08 * SR), 0.002, 0.03), T_FAN0 + 0.3 + j * 0.2,
               0.03, 0.4)
    dr = (np.sin(2 * np.pi * 180 * np.arange(int((T_DRONE1 - T_DRONE0) * SR)) / SR) * 0.4 +
          noise(T_DRONE1 - T_DRONE0, 50, lo=200, hi=900) * 0.6)
    m = len(dr)
    dr *= np.sin(np.linspace(0, np.pi, m))
    mix_in(fx, dr, T_DRONE0, 0.06, 0.5)
    for j in range(5):
        mix_in(fx, noise(0.07, 60 + j, lo=800, hi=4000) * env(int(0.07 * SR), 0.002, 0.03), T_DRONE_HAND + 0.6 + j * 0.35,
               0.04, 0.4)
    for j in range(6):
        mix_in(fx, tone(2400, 0.02, (1,), a=0.0005, d=0.01), T_YAWN1 + 0.6 + j * 0.25, 0.04, 0.4)
    # the bow rips, the door, the engine
    mix_in(fx, noise(0.35, 70, lo=1500, hi=8000) * np.sin(np.linspace(0, np.pi, int(0.35 * SR))), T_BOW, 0.08, 0.4)
    mix_in(fx, tone(100, 0.2, (1, 0.5), a=0.001, d=0.06) + 0.4 * noise(0.2, 71, lo=200, hi=3000) *
           env(int(0.2 * SR), 0.001, 0.04), T_IN, 0.18, 0.4)
    mix_in(fx, engine(0.5, 30, 70, 0.6, 0.6, 72) * env(int(0.5 * SR), 0.02, 0.3), T_IGN - 0.35, 0.10, 0.4)
    idle = engine(T_LAUNCH - T_IGN, 46, 58, 1.0, 0.3, 73)
    for j, tr in enumerate((0.35, 0.8)):
        lo, hi_ = int(tr * SR), int((tr + 0.25) * SR)
        idle[lo:hi_] *= 1.6
    mix_in(fx, idle * np.minimum(1, np.arange(len(idle)) / (0.05 * SR)), T_IGN, 0.16, 0.4)
    # heartbeat under the slow reach
    for j in range(3):
        for k2, dt in enumerate((0.0, 0.17)):
            mix_in(fx, tone(48, 0.2, (1, 0.5), a=0.003, d=0.08), T_REACH + j * 0.42 + dt, 0.16 - 0.06 * k2)
    # launch: roar + whoosh, the tape snaps, the skid
    mix_in(fx, engine(0.8, 70, 260, 0.7, 0.35, 74) * env(int(0.8 * SR), 0.01, 0.5), T_LAUNCH, 0.30, 0.2)
    mix_in(fx, noise(0.6, 75, lo=300, hi=5000) * np.sin(np.linspace(0, np.pi, int(0.6 * SR))), T_LAUNCH + 0.05, 0.12)
    mix_in(fx, tone(1200, 0.08, (1, 0.5), a=0.001, d=0.03, sweep=600), T_CROSS, 0.10)
    sk = noise(0.5, 76, lo=1500, hi=5000) * env(int(0.5 * SR), 0.01, 0.25)
    sk *= np.sin(2 * np.pi * 2200 * np.arange(len(sk)) / SR) * 0.5 + 0.5
    mix_in(fx, sk, T_CROSS + 0.03, 0.12, 0.3)
    mix_in(fx, tone(1000, 0.08, (1, 0.5), a=0.001, d=0.03, sweep=500), T_TOUCH, 0.06, -0.1)
    # stamps
    for t0, g in ((T_STAMP, 0.2), (T_STAMP + 0.15, 0.14), (T_STAMP + 0.3, 0.12)):
        mix_in(fx, tone(70, 0.3, (1, 0.5), a=0.001, d=0.12) + 0.3 * noise(0.3, int(t0 * 100), lo=300, hi=4000) *
               env(int(0.3 * SR), 0.001, 0.05), t0, g)
    for j, m in enumerate((72, 76, 79, 84)):
        mix_in(fx, music.marimba(midi(m), 0.9), T_CROSS + 0.05 + 0.07 * j, 0.07)
    # rewind whir into frame 0
    rw = DUR - T_RW
    nrw = int(rw * SR)
    fr = 300 + 2200 * np.linspace(0, 1, nrw) ** 1.5
    w = np.sin(2 * np.pi * np.cumsum(fr) / SR) * 0.5 + noise(rw, 80, lo=1000, hi=6000) * 0.5
    w *= np.minimum(1, np.arange(nrw) / (0.05 * SR))
    mix_in(fx, w, T_RW, 0.06)
    x = mus + fx
    # duck the music under the rewind
    i0 = int(T_RW * SR)
    x[i0:] = fx[i0:] + mus[i0:] * np.linspace(1, 0.2, n - i0)[:, None]
    m = int(0.3 * SR)
    k = np.linspace(0, 1, m)[:, None]
    x[-m:] = x[-m:] * (1 - k) + x[:m] * k
    x /= max(1.0, np.abs(x).max() / 0.9)
    return x


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "who-wins.mp4"
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
