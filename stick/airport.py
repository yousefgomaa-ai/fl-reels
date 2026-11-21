#!/usr/bin/env python3
"""WHO MAKES THE FLIGHT? - two people, one airport, a moving camera. 25.5 s, loops. Thanksgiving week.

Hook: the camera is pushed into the departures board - FLIGHT 227, BOARDING CLOSES 9:40 - and the clock reads 9:12.
Whip-pan to THE EARLY GUY, already at gate B12 with a coffee: "3 HOURS EARLY. AS ALWAYS."
Whip-pan to THE LAST-MINUTE GUY bursting through the doors; the camera runs with him. Security line, the arch
BEEPs, shoes off - 9:30. Whip to the gate: the early guy yawns, "JUST A QUICK NAP..." Back to the sprint: he jumps a
suitcase, FINAL CALL, he slides through the door at 9:39:58 - MADE IT.
Twist: the camera drifts left... the early guy is asleep in the chair right by the door. The plane pushes back.
He wakes: "WAIT... WAS THAT MY FLIGHT?" - MISSED IT.   "3 HOURS EARLY. STILL MISSED IT. / WHICH ONE ARE YOU?"

    python3 stick/airport.py stick/airport.mp4
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
from perfect_wave import clamp, env, font, lerp, lerp_pose, midi, mix_in, noise, prog, smooth, spaced, tone, write_wav  # noqa

W, H, FPS = 1080, 1920, 30
SR = 44100
DUR = 25.5
NF = int(round(DUR * FPS))
XFADE = 0.5
K = hq.K
BOLD = hq.BOLD
FLOOR = 1650
S = 2.0
HIP_Y = FLOOR - 113 * S
EARLY = (60, 220, 255)
LATE = (255, 150, 40)
GRAY = (120, 126, 156)
GOLD = (255, 205, 60)
GREEN = (110, 240, 140)
REDC = (255, 80, 80)
WARM = (255, 200, 120)
TITLE_H = 300

# world layout (x)
DOORS_X = 350
BOARD_X = -700
QUEUE_X = [1440, 1560, 1680]
ARCH_X = 1880
BELT = (1980, 2340)
SUITCASE_X = 4100
GATE_SIGNS = [(3300, "B10"), (4300, "B11")]
CHAIRS = [5260, 5380, 5500, 5620]
EARLY_X = 5500
WIN = (5120, 6320, 980, 1420)
DESK_X = 5950
DOOR_X = 6170

# timeline
T_WHIP1 = 1.35        # board -> early guy
T_WHIP2 = 3.6         # early guy -> doors
T_DOORS = 4.0
T_QUEUE = 5.5
T_BEEP = 7.0
T_SHOES = 7.6
T_RUN2 = 8.9
T_WHIP3 = 9.0         # -> gate (nap)
T_NAP = 9.5
T_WHIP4 = 11.2        # -> runner
T_JUMP = 12.95
T_FINAL = 14.6
T_DOOR_IN = 16.6
T_CLOSE = 17.05
T_PAN = 18.0          # the twist: pan to the sleeper
T_PUSH = 18.6         # the plane leaves
T_WAKE = 19.6
T_MISS = 20.5
T_WIDE = 21.2
T_L1, T_L2 = 21.6, 22.7
CPS = 18.0
LINE1, LINE2 = "3 HOURS EARLY. STILL MISSED IT.", "WHICH ONE ARE YOU?"
T_FOLLOW = 23.9
RUN_V = 520.0


def runner_x(t):
    if t < T_DOORS:
        return DOORS_X - 260
    if t < T_QUEUE:
        return lerp(DOORS_X - 200, 1300, prog(t, T_DOORS, T_QUEUE))
    if t < T_BEEP - 0.5:
        return lerp(1300, 1420, smooth(prog(t, T_QUEUE + 0.6, T_BEEP - 0.5)))
    if t < T_BEEP:
        return lerp(1420, ARCH_X, smooth(prog(t, T_BEEP - 0.5, T_BEEP)))
    if t < T_RUN2:
        return ARCH_X + 60 * smooth(prog(t, T_SHOES + 0.6, T_RUN2))
    return min(ARCH_X + 60 + RUN_V * (t - T_RUN2), DESK_X + 120 + 160 * prog(t, T_DOOR_IN, T_DOOR_IN + 0.4))


def clock_s(t):
    """seconds after 9:00"""
    keys = [(0, 12 * 60), (T_DOORS, 14 * 60), (T_QUEUE, 17 * 60), (T_BEEP, 23 * 60), (T_RUN2, 30 * 60),
            (T_WHIP4, 33 * 60), (T_FINAL, 37 * 60), (16.0, 39 * 60 + 40), (T_CLOSE, 40 * 60),
            (DUR, 47 * 60)]
    for (a, va), (b, vb) in zip(keys, keys[1:]):
        if t <= b:
            return lerp(va, vb, prog(t, a, b))
    return keys[-1][1]


# ---------------------------------------------------------------- camera
def cam(t):
    """cx, cy, z in world units; whip-pans are fast eases between holds."""
    rx = runner_x(t)

    def hold_board(u):
        return BOARD_X, 930, 1.85 + 0.12 * prog(u, 0, T_WHIP1)

    def early_shot(u, z0=1.25, z1=1.34):
        return EARLY_X + 120, 1210, lerp(z0, z1, prog(u, T_WHIP1, T_WHIP2))

    def doors_shot(u):
        x = max(620, rx + 160)
        return x, 1210, 1.22

    def security(u):
        return lerp(1500, ARCH_X + 40, smooth(prog(u, T_QUEUE, T_BEEP))), 1210, lerp(1.22, 1.36, prog(u, T_QUEUE, T_SHOES))

    def nap(u):
        return EARLY_X + 40, 1230, lerp(1.32, 1.55, prog(u, T_WHIP3, T_WHIP4))

    def chase(u):
        return runner_x(u) + 170, 1210, 1.28

    def door(u):
        return DESK_X + 140, 1210, lerp(1.28, 1.38, prog(u, T_DOOR_IN, T_PAN))

    def reveal(u):
        k = smooth(prog(u, T_PAN, T_PAN + 1.3))
        return lerp(DESK_X + 140, EARLY_X + 60, k), lerp(1210, 1260, k), lerp(1.38, 1.7, k)

    def wide(u):
        k = smooth(prog(u, T_WIDE, T_WIDE + 1.4))
        x0, y0, z0 = reveal(T_WIDE)
        return lerp(x0, 5760, k), lerp(y0, 1180, k), lerp(z0, 1.22, k)

    segs = [(0, hold_board), (T_WHIP1, early_shot), (T_WHIP2, doors_shot), (T_QUEUE, security),
            (T_WHIP3, nap), (T_WHIP4, chase), (T_DOOR_IN - 0.4, door), (T_PAN, reveal), (T_WIDE, wide)]
    whips = {T_WHIP1: 0.38, T_WHIP2: 0.38, T_WHIP3: 0.36, T_WHIP4: 0.36, T_DOOR_IN - 0.4: 0.5, T_QUEUE: 0.5}
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
    # handheld sway
    cx += 5 * math.sin(t * 1.7) + 3 * math.sin(t * 4.3 + 1)
    cy += 4 * math.sin(t * 2.1 + 2) + 2 * math.sin(t * 5.1)
    return cx, cy, z


class View:
    def __init__(self, t):
        self.cx, self.cy, self.z = cam(t)

    def x(self, x):
        return (x - self.cx) * self.z + W / 2

    def y(self, y):
        return (y - self.cy) * self.z + H / 2

    def p(self, pt):
        return self.x(pt[0]), self.y(pt[1])

    def pts(self, pts):
        return [self.p(q) for q in pts]

    def box(self, b):
        return [self.x(b[0]), self.y(b[1]), self.x(b[2]), self.y(b[3])]


# ---------------------------------------------------------------- poses
STAND = PW.STAND
SIT = dict(PW.SIT, kl=(62, -2), fl=(66, 108), kr=(54, 2), fr=(56, 110))
COFFEE_SIT = dict(SIT, el=(26, -64), hl=(40, -98))
YAWN = dict(SIT, head=(0, -154), el=(-26, -120), hl=(-44, -170), er=(26, -120), hr=(44, -170))
SLEEP = dict(SIT, head=(28, -128), neck=(10, -100), el=(22, -58), hl=(40, -26), er=(4, -56), hr=(14, -22))
SHOCK = dict(STAND, head=(-4, -152), el=(-26, -112), hl=(-20, -152), er=(24, -112), hr=(20, -152))
HANDS_HEAD = dict(STAND, el=(-40, -130), hl=(-8, -160), er=(40, -130), hr=(8, -160))
TAP = dict(STAND, el=(26, -70), hl=(4, -58), er=(-22, -60), hr=(-26, -14))
BEND = {"head": (40, -96), "neck": (28, -64), "el": (40, -20), "hl": (48, 30), "er": (30, -16), "hr": (36, 34),
        "kl": (-9, 56), "fl": (-13, 113), "kr": (12, 56), "fr": (16, 113)}
SHOES_UP = dict(STAND, el=(30, -84), hl=(56, -112), er=(26, -80), hr=(52, -108))
CHEER = dict(STAND, el=(-30, -130), hl=(-40, -180), er=(30, -130), hr=(40, -180))


def run(ph, lean=1.0):
    p = {"head": (18 * lean, -146), "neck": (12 * lean, -106)}
    for side, off in (("l", 0.0), ("r", math.pi)):
        s = math.sin(ph + off)
        a = 0.75 * s
        kx, ky = 56 * math.sin(a), 56 * math.cos(a)
        bend = 0.2 + 1.1 * max(0.0, -math.cos(ph + off))
        p["k" + side] = (kx, ky)
        p["f" + side] = (kx + 57 * math.sin(a - bend), ky + 57 * math.cos(a - bend))
        # arms opposite to legs, bent at the elbow
        aa = -0.9 * s
        ex, ey = 12 * lean + 48 * math.sin(aa), -106 + 48 * math.cos(aa)
        p["e" + side] = (ex, ey)
        p["h" + side] = (ex + 44 * math.sin(aa + 1.4), ey + 44 * math.cos(aa + 1.4) - 10)
    return p


def runner_state(t):
    """pose, hip (world), facing, alpha, bob"""
    x = runner_x(t)
    if t < T_DOORS:
        return None
    if t < T_QUEUE:
        ph = (t - T_DOORS) * 15
        return run(ph), (x, HIP_Y - 10 * abs(math.sin(ph))), 1, 1
    if t < T_BEEP - 0.5:
        k = smooth(prog(t, T_QUEUE, T_QUEUE + 0.3))
        pose = lerp_pose(run(0.8), TAP, k)
        if t > T_QUEUE + 0.6:
            pose = dict(pose, fr=(13 + 8 * max(0, math.sin(t * 18)), 113 - 14 * max(0, math.sin(t * 18))))
        return pose, (x, HIP_Y), 1, 1
    if t < T_BEEP:
        return AJ.walk((t - T_BEEP) * 9, STAND), (x, HIP_Y), 1, 1
    if t < T_SHOES:
        return lerp_pose(STAND, SHOCK, smooth(prog(t, T_BEEP, T_BEEP + 0.15))), (x, HIP_Y), 1, 1
    if t < T_RUN2 - 0.5:
        k = math.sin(math.pi * prog(t, T_SHOES, T_SHOES + 0.6))
        return lerp_pose(STAND, BEND, k) if t < T_SHOES + 0.6 else SHOES_UP, (x, HIP_Y), 1, 1
    if t < T_DOOR_IN:
        ph = (t - T_RUN2) * 16
        y = HIP_Y - 10 * abs(math.sin(ph))
        if T_JUMP <= t < T_JUMP + 0.55:
            u = prog(t, T_JUMP, T_JUMP + 0.55)
            y -= 170 * math.sin(math.pi * u)
            return run(1.2, 1.4), (x, y), 1, 1
        return run(ph, 1.2), (x, y), 1, 1
    if t < T_DOOR_IN + 0.45:
        a = 1 - smooth(prog(t, T_DOOR_IN + 0.15, T_DOOR_IN + 0.45))
        return run((t - T_RUN2) * 16, 1.3), (x, HIP_Y), 1, a
    return None


def early_state(t):
    """pose, hip, facing, alpha"""
    hip = (EARLY_X, FLOOR - 110 * S - 6)
    if t < T_NAP:
        sip = max(0, math.sin((t - 1.0) * 2.4)) if t > 2.0 else 0
        pose = dict(COFFEE_SIT, hl=(40, -98 - 14 * sip), head=(6, -150 - 3 * sip))
        return pose, hip, 1, 1, "coffee"
    if t < T_NAP + 1.0:
        k = math.sin(math.pi * prog(t, T_NAP, T_NAP + 1.0))
        return lerp_pose(SIT, YAWN, k), hip, 1, 1, None
    if t < T_WAKE:
        nod = 6 * math.sin(t * 2.2)
        return dict(SLEEP, head=(28, -128 + nod)), hip, 1, 1, "zzz"
    if t < T_WAKE + 0.6:
        k = smooth(prog(t, T_WAKE, T_WAKE + 0.25))
        return lerp_pose(SLEEP, dict(SIT, head=(-6, -156)), k), hip, 1, 1, None
    if t < T_MISS - 0.2:
        k = smooth(prog(t, T_WAKE + 0.6, T_MISS - 0.2))
        return lerp_pose(SIT, SHOCK, k), (lerp(hip[0], EARLY_X + 40, k), lerp(hip[1], HIP_Y, k)), 1, 1, None
    k = smooth(prog(t, T_MISS - 0.2, T_MISS + 0.3))
    return lerp_pose(SHOCK, HANDS_HEAD, k), (EARLY_X + 40, HIP_Y), 1, 1, None


# ---------------------------------------------------------------- drawing
def gline(p, pts, col, w, a=255):
    p.ds.line(hq.sc(pts), fill=col + (int(a),), width=max(1, int(w * K)), joint="curve")
    for x, y in pts:
        r = w * K / 2
        p.ds.ellipse([x * K - r, y * K - r, x * K + r, y * K + r], fill=col + (int(a),))


def gray_person(p, v, x, pose=None, facing=1, a=200, bag=False):
    pts = AJ.place(pose or STAND, (x, HIP_Y), facing, S)
    sp = {k_: v.p(q) for k_, q in pts.items()}
    w = 9 * v.z
    for b0, b1 in [("neck", "hip"), ("neck", "el"), ("el", "hl"), ("neck", "er"), ("er", "hr"), ("hip", "kl"),
                   ("kl", "fl"), ("hip", "kr"), ("kr", "fr")]:
        gline(p, [sp[b0], sp[b1]], GRAY, w, a)
    hx, hy = sp["head"]
    r = 22 * v.z
    p.ds.ellipse([(hx - r) * K, (hy - r) * K, (hx + r) * K, (hy + r) * K], fill=GRAY + (int(a),))
    if bag:
        bx, by = v.p((x + 60 * facing, FLOOR - 120))
        p.fill_rect([bx - 30 * v.z, by, bx + 30 * v.z, by + 110 * v.z], (40, 40, 60), a, r=8 * v.z)


def stick(p, v, pts, col, a=255):
    sp = {k_: v.p(q) for k_, q in pts.items()}
    p.stick(sp, col, 10 * v.z, a)
    return sp


def label(p, v, x, y, s, col, a=255):
    if not (-80 < v.x(x) < W + 80):
        return
    sz = 26 * v.z
    xx = clamp(v.x(x), 40 + len(s) * sz * 0.34, W - 40 - len(s) * sz * 0.34)
    p.fill_rect([xx - len(s) * sz * 0.36, v.y(y) - 8, xx + len(s) * sz * 0.36, v.y(y) + sz * 1.25], (6, 6, 14), a * 0.8,
                r=10)
    p.text((xx, v.y(y)), s, sz, col, a, neon=True)


def say(p, v, t, t0, t1, x, y, s, col, size=40):
    if not (t0 <= t < t1):
        return
    k = hq.pop(t, t0, 0.28)
    a = 255 * (1 - smooth(prog(t, t1 - 0.25, t1)))
    sz = size * v.z * max(0.3, k)
    xx = clamp(v.x(x), 60 + len(s) * sz * 0.33, W - 60 - len(s) * sz * 0.33)
    p.text((xx, v.y(y)), s, sz, col, a, neon=True)


def world(p, v, t):
    z = v.z
    # wall and floor
    fy = v.y(FLOOR)
    p.fill_rect([0, 0, W, fy], (12, 11, 26), 255)
    p.fill_rect([0, fy - 260 * z, W, fy], (22, 16, 42), 120)
    p.fill_rect([0, fy, W, H], (16, 14, 28), 255)
    p.ds.line([0, fy * K, W * K, fy * K], fill=(90, 80, 140, 255), width=int(3 * K))
    # ceiling lights and their floor reflections every 260 units - the parallax that sells the motion
    x0 = int((v.cx - W / z) // 260) * 260
    for x in range(x0, int(v.cx + W / z) + 260, 260):
        sx = v.x(x)
        p.line([(sx - 70 * z, v.y(330)), (sx + 70 * z, v.y(330))], (200, 210, 255), 5 * z, 150)
        p.fill_rect([sx - 50 * z, fy + 20 * z, sx + 50 * z, fy + 32 * z], (120, 130, 200), 40)
        for k_ in range(4):
            p.fill_rect([sx - 20 * z, fy + (50 + 50 * k_) * z, sx + 20 * z, fy + (60 + 50 * k_) * z], (120, 130, 200),
                        26 - 5 * k_)
    # entrance: glass doors that slide open
    dx = 110 * smooth(prog(t, T_DOORS - 0.2, T_DOORS + 0.15)) * (1 - smooth(prog(t, T_DOORS + 0.9, T_DOORS + 1.4)))
    p.fill_rect(v.box([DOORS_X - 230, 1000, DOORS_X + 230, FLOOR]), (8, 14, 34), 255)
    for side in (-1, 1):
        x0_ = DOORS_X + side * (dx + 2)
        b = [x0_, 1010, x0_ + side * 220, FLOOR]
        b = [min(b[0], b[2]), b[1], max(b[0], b[2]), b[3]]
        p.fill_rect(v.box(b), (60, 90, 140), 60)
        p.rect(v.box(b), (150, 190, 255), 3 * z, 200)
    p.text((v.x(DOORS_X), v.y(930)), "ENTRANCE", 26 * z, (150, 190, 255), 220)
    # departures board
    bx0, bx1, by0, by1 = BOARD_X - 270, BOARD_X + 270, 700, 1130
    p.fill_rect(v.box([bx0, by0, bx1, by1]), (6, 6, 12), 255, r=10 * z)
    p.rect(v.box([bx0, by0, bx1, by1]), GOLD, 5 * z, 255, r=10 * z)
    p.text((v.x(BOARD_X), v.y(by0 + 22)), "DEPARTURES", 34 * z, GOLD, 255, neon=True, spacing=4)
    rows = [("214", "CHICAGO", "ON TIME", (200, 200, 210)), ("227", "NEW YORK", "BOARDING", REDC),
            ("231", "DENVER", "DELAYED", (200, 200, 210))]
    for j, (fl, city, st, c) in enumerate(rows):
        yy = by0 + 100 + j * 70
        hi = j == 1
        if hi:
            p.fill_rect(v.box([bx0 + 14, yy - 8, bx1 - 14, yy + 50]), (60, 10, 14), 255, r=6 * z)
        p.text((v.x(bx0 + 30), v.y(yy)), fl, 28 * z, c if hi else (170, 170, 190), 255, center=False)
        p.text((v.x(bx0 + 110), v.y(yy)), city, 28 * z, c if hi else (170, 170, 190), 255, center=False)
        if not hi or int(t * 3) % 2 == 0:
            p.text((v.x(bx1 - 140), v.y(yy)), st, 24 * z, c, 255, neon=hi)
    p.text((v.x(BOARD_X), v.y(by1 - 110)), "GATE B12", 30 * z, (230, 230, 240), 255)
    p.text((v.x(BOARD_X), v.y(by1 - 66)), "DOORS CLOSE 9:40", 30 * z, REDC, 255, neon=True)
    # security
    p.text((v.x(1700), v.y(760)), "SECURITY", 38 * z, (150, 190, 255), 255, neon=True, spacing=6)
    p.rect(v.box([1560, 740, 1840, 820]), (150, 190, 255), 3 * z, 200, r=8 * z)
    beep = T_BEEP <= t < T_BEEP + 0.8 and int((t - T_BEEP) * 8) % 2 == 0
    arch = (255, 70, 70) if beep else (190, 200, 230)
    p.line(v.pts([(ARCH_X - 90, FLOOR), (ARCH_X - 90, 1080), (ARCH_X + 90, 1080), (ARCH_X + 90, FLOOR)]), arch,
           12 * z, 255)
    p.circle(v.x(ARCH_X), v.y(1050), 16 * z, (255, 60, 60) if beep else (90, 40, 40), a=255, fill=True)
    p.fill_rect(v.box([BELT[0], 1420, BELT[1], 1470]), (40, 40, 62), 255)
    p.rect(v.box([BELT[0], 1420, BELT[1], 1470]), (150, 160, 200), 3 * z, 200)
    for j in range(3):
        bxx = BELT[0] + 40 + ((t * 60 + j * 120) % 320)
        p.fill_rect(v.box([bxx, 1380, bxx + 90, 1420]), (70, 80, 110), 255, r=6 * z)
    # gate signs
    for gx, s in GATE_SIGNS:
        p.fill_rect(v.box([gx - 90, 860, gx + 90, 940]), (10, 10, 20), 255, r=8 * z)
        p.rect(v.box([gx - 90, 860, gx + 90, 940]), GOLD, 4 * z, 255, r=8 * z)
        p.text((v.x(gx), v.y(872)), s, 42 * z, GOLD, 255, neon=True)
    # the suitcase in the corridor
    sx0 = SUITCASE_X
    p.fill_rect(v.box([sx0 - 60, FLOOR - 130, sx0 + 60, FLOOR - 10]), (70, 40, 90), 255, r=10 * z)
    p.rect(v.box([sx0 - 60, FLOOR - 130, sx0 + 60, FLOOR - 10]), (255, 70, 200), 4 * z, 220, r=10 * z)
    p.line(v.pts([(sx0 - 20, FLOOR - 130), (sx0 - 20, FLOOR - 180), (sx0 + 20, FLOOR - 180), (sx0 + 20, FLOOR - 130)]),
           (255, 70, 200), 4 * z, 220)
    # the gate window, with the plane behind it
    wx0, wx1, wy0, wy1 = WIN
    p.fill_rect(v.box([wx0, wy0, wx1, wy1]), (6, 10, 26), 255)
    rng = np.random.default_rng(7)
    for _ in range(40):
        sx, sy = rng.uniform(wx0, wx1), rng.uniform(wy0, wy0 + 300)
        p.ds.ellipse([(v.x(sx) - 1.5) * K, (v.y(sy) - 1.5) * K, (v.x(sx) + 1.5) * K, (v.y(sy) + 1.5) * K],
                     fill=(220, 220, 255, 160))
    for j in range(12):
        lx = wx0 + 40 + j * 100
        on = int(t * 4 + j) % 3 == 0
        p.circle(v.x(lx), v.y(wy1 - 40), 5 * z, (80, 160, 255) if on else (40, 60, 110), a=255, fill=True)
    plane(p, v, t)
    for mx in np.linspace(wx0, wx1, 5):
        p.line(v.pts([(mx, wy0), (mx, wy1)]), (110, 110, 150), 8 * z, 255)
    p.line(v.pts([(wx0, wy0), (wx1, wy0)]), (110, 110, 150), 8 * z, 255)
    p.line(v.pts([(wx0, wy1), (wx1, wy1)]), (110, 110, 150), 8 * z, 255)
    # chairs
    for cxx in CHAIRS:
        p.fill_rect(v.box([cxx - 52, FLOOR - 232, cxx + 52, FLOOR - 196]), (40, 46, 80), 255, r=8 * z)
        p.fill_rect(v.box([cxx - 56, FLOOR - 330, cxx - 30, FLOOR - 170]), (40, 46, 80), 255, r=8 * z)
        p.line(v.pts([(cxx, FLOOR - 160), (cxx, FLOOR)]), (90, 100, 150), 6 * z, 255)
    # desk, gate door
    p.fill_rect(v.box([DESK_X - 110, FLOOR - 230, DESK_X + 110, FLOOR]), (24, 22, 44), 255, r=8 * z)
    p.rect(v.box([DESK_X - 110, FLOOR - 230, DESK_X + 110, FLOOR]), (150, 190, 255), 4 * z, 220, r=8 * z)
    closed = t >= T_CLOSE
    p.fill_rect(v.box([DESK_X - 120, 900, DESK_X + 120, 990]), (10, 10, 20), 255, r=8 * z)
    p.rect(v.box([DESK_X - 120, 900, DESK_X + 120, 990]), REDC if closed else GREEN, 4 * z, 255, r=8 * z)
    blink = t < T_FINAL or int(t * 4) % 2 == 0
    sgn = "CLOSED" if closed else ("FINAL CALL" if t >= T_FINAL else "227 NYC")
    if closed or blink:
        p.text((v.x(DESK_X), v.y(922)), sgn, 32 * z, REDC if (closed or t >= T_FINAL) else GREEN, 255, neon=True)
    p.fill_rect(v.box([DOOR_X - 10, 1000, DOOR_X + 200, FLOOR]), (4, 4, 10), 255)
    p.text((v.x(DOOR_X + 95), v.y(940)), "B12", 34 * z, GOLD, 255, neon=True)
    shut = smooth(prog(t, T_DOOR_IN + 0.35, T_CLOSE))
    p.fill_rect(v.box([DOOR_X - 10, 1000, DOOR_X - 10 + 210 * shut, FLOOR]), (60, 64, 96), 255)
    p.rect(v.box([DOOR_X - 10, 1000, DOOR_X + 200, FLOOR]), (150, 190, 255), 5 * z, 255)


def plane(p, v, t):
    # parked behind the window, then pushes back and taxis away to the right
    u = prog(t, T_PUSH, T_PUSH + 4.5)
    px = 5900 + 1400 * u ** 1.6
    py = 1150 - 30 * u
    sc_ = 0.62 - 0.15 * u
    body = [(-330, 0), (-300, -40), (260, -46), (330, -20), (330, 10), (-300, 14)]
    pts = [(px + x * sc_, py + y * sc_) for x, y in body]
    p.fill_poly(v.pts(pts), (190, 196, 220), 255)
    tail = [(-300, -40), (-340, -150), (-280, -150), (-220, -44)]
    p.fill_poly(v.pts([(px + x * sc_, py + y * sc_) for x, y in tail]), (60, 220, 255), 255)
    wing = [(-40, 0), (80, 0), (-60, 70), (-120, 70)]
    p.fill_poly(v.pts([(px + x * sc_, py + y * sc_) for x, y in wing]), (150, 156, 184), 255)
    for j in range(10):
        wx = px + (-220 + j * 46) * sc_
        p.fill_rect(v.box([wx, py - 30 * sc_, wx + 18 * sc_, py - 16 * sc_]), (255, 230, 160), 255)
    if u > 0 and int(t * 3) % 2 == 0:
        p.circle(v.x(px - 330 * sc_), v.y(py - 150 * sc_), 8 * v.z, (255, 60, 60), a=255, fill=True)


def stamp(p, t, t0, x, y, s, col):
    if t < t0:
        return
    k = hq.pop(t, t0, 0.3)
    f = font(BOLD, int(62 * K))
    tw = (f.getlength(s) + 3 * K * len(s)) / K + 70
    w, h = tw * k, 116 * k
    if w < 10:
        return
    lay = Image.new("RGBA", (int(w * K), int(h * K)), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle([0, 0, lay.width - 1, lay.height - 1], int(16 * K * k), fill=(8, 8, 12, 238),
                         outline=col + (255,), width=int(7 * K * k))
    fs = font(BOLD, max(4, int(62 * K * k)))
    tws = sum(fs.getlength(c) for c in s) + 3 * K * k * (len(s) - 1)
    xx = lay.width / 2 - tws / 2
    for c in s:
        ld.text((xx, lay.height / 2 - 38 * K * k), c, font=fs, fill=col + (255,))
        xx += fs.getlength(c) + 3 * K * k
    lay = lay.rotate(-5, resample=Image.BICUBIC, expand=True)
    p.tops.append((lay, (int(x * K - lay.width / 2), int(y * K - lay.height / 2))))


class SafePanel(hq.Panel):
    """Panel whose boxes may be off-screen or flipped (the camera moves everything around)."""

    @staticmethod
    def _fix(box):
        x0, y0, x1, y1 = box
        x0, x1 = sorted((x0, x1))
        y0, y1 = sorted((y0, y1))
        x0, x1 = max(x0, -50), min(x1, W + 50)
        y0, y1 = max(y0, -50), min(y1, H + 50)
        return None if x1 - x0 < 0.5 or y1 - y0 < 0.5 else [x0, y0, x1, y1]

    def fill_rect(self, box, col, a=255, r=0):
        b = self._fix(box)
        if b:
            super().fill_rect(b, col, a, min(r, (b[2] - b[0]) / 2, (b[3] - b[1]) / 2))

    def rect(self, box, col, w=4, a=255, r=0):
        b = self._fix(box)
        if b and b[2] - b[0] > 2 * w and b[3] - b[1] > 2 * w:
            super().rect(b, col, w, a, min(r, (b[2] - b[0]) / 2, (b[3] - b[1]) / 2))


BG = None
VIG = None
FRAME0 = None


def scene(t):
    v = View(t)
    p = SafePanel(BG)
    p.tops = []
    world(p, v, t)
    # queue people, then the security staff and the gate agent
    for j, qx in enumerate(QUEUE_X):
        k = smooth(prog(t, T_QUEUE + 0.4 + j * 0.3, T_QUEUE + 1.0 + j * 0.3))
        x = lerp(qx, ARCH_X + 400 + j * 60, k)
        if k < 1:
            gray_person(p, v, x, AJ.walk(t * 8 + j, STAND) if 0 < k < 1 else STAND, a=200 * (1 - k), bag=True)
    gray_person(p, v, ARCH_X + 210, dict(STAND, el=(30, -96), hl=(64, -120)) if T_SHOES - 0.3 < t < T_RUN2 else STAND,
                facing=-1)
    agent_pose = dict(STAND, el=(30, -100), hl=(66, -116)) if T_FINAL < t < T_CLOSE else STAND
    gray_person(p, v, DESK_X + 50, agent_pose, facing=-1)
    # the early guy
    pose, hip, facing, a, prop = early_state(t)
    sp = stick(p, v, AJ.place(pose, hip, facing, S), EARLY, 255 * a)
    hx, hy = sp["hl"]
    if prop == "coffee":
        z = v.z
        p.fill_rect([hx - 14 * z, hy - 40 * z, hx + 14 * z, hy + 4 * z], (240, 240, 236), 255, r=5 * z)
        for j in range(3):
            ph = (t * 0.8 + j / 3) % 1
            p.ds.ellipse([(hx + (-6 + 10 * math.sin(ph * 6 + j)) * z - 4 * z) * K, (hy - (50 + 60 * ph) * z - 4 * z) * K,
                          (hx + (-6 + 10 * math.sin(ph * 6 + j)) * z + 4 * z) * K, (hy - (50 + 60 * ph) * z + 4 * z) * K],
                         fill=(220, 220, 230, int(120 * (1 - ph))))
    if prop == "zzz":
        for j in range(3):
            ph = (t * 0.7 + j / 3) % 1
            zx, zy = sp["head"][0] + (40 + 50 * ph) * v.z, sp["head"][1] - (40 + 120 * ph) * v.z
            p.text((zx, zy), "Z", (26 + 22 * ph) * v.z, EARLY, 255 * (1 - ph), neon=True)
    ex, ey = EARLY_X, FLOOR - 640
    if t < T_WHIP4:
        label(p, v, ex, FLOOR - 590, "THE EARLY GUY", EARLY)
    # the last-minute guy
    rs = runner_state(t)
    if rs:
        pose, hip, facing, a = rs
        sp2 = stick(p, v, AJ.place(pose, hip, facing, S), LATE, 255 * a)
        if T_SHOES + 0.6 <= t < T_DOOR_IN + 0.45:
            hx, hy = sp2["hl"]
            z = v.z
            p.fill_rect([hx - 26 * z, hy - 12 * z, hx + 18 * z, hy + 8 * z], (240, 240, 240), 255 * a, r=6 * z)
        if t < T_WHIP4 + 1.2:
            label(p, v, hip[0], hip[1] - 400, "THE LAST-MINUTE GUY", LATE, 255 * a)
        # speed lines while sprinting
        if T_RUN2 < t < T_DOOR_IN or T_DOORS < t < T_QUEUE:
            rng = np.random.default_rng(int(t * 10))
            for j in range(6):
                yy = hip[1] - 260 + rng.uniform(0, 380)
                xx = hip[0] - 200 - rng.uniform(0, 300)
                p.line(v.pts([(xx, yy), (xx + 150, yy)]), LATE, 3 * v.z, 120)
    # words
    say(p, v, t, T_WHIP1 + 0.35, T_WHIP2, EARLY_X + 60, FLOOR - 710, "3 HOURS EARLY.", EARLY, 44)
    say(p, v, t, T_DOORS + 0.2, T_QUEUE, runner_x(t) + 60, FLOOR - 760, "I'VE GOT TIME.", LATE, 40)
    say(p, v, t, T_QUEUE + 0.6, T_BEEP - 0.1, 1420, FLOOR - 760, "COME ON, COME ON...", LATE, 38)
    say(p, v, t, T_BEEP, T_SHOES, ARCH_X, 1000, "BEEP! BEEP!", REDC, 60)
    say(p, v, t, T_SHOES, T_RUN2 + 0.1, ARCH_X + 120, FLOOR - 760, "SHOES OFF, SIR.", (200, 200, 220), 40)
    say(p, v, t, T_WHIP3 + 0.3, T_NAP + 1.1, EARLY_X + 60, FLOOR - 710, "NOW BOARDING. GROUP 1", GREEN, 32)
    say(p, v, t, T_NAP + 1.1, T_WHIP4, EARLY_X + 60, FLOOR - 710, "JUST A QUICK NAP...", EARLY, 36)
    say(p, v, t, T_WHIP4 + 0.3, T_JUMP, runner_x(t) + 40, FLOOR - 760, "GATE B12... GATE B12...", LATE, 38)
    say(p, v, t, T_FINAL, T_DOOR_IN - 0.2, runner_x(t) + 100, 1010, "FINAL CALL - FLIGHT 227", REDC, 36)
    say(p, v, t, T_WAKE + 0.3, T_MISS + 0.1, EARLY_X + 60, FLOOR - 710, "WAIT... WAS THAT MY FLIGHT?", EARLY, 34)
    if t >= T_CLOSE:
        stamp(p, t, T_CLOSE, v.x(DOOR_X + 95), v.y(1240), "MADE IT", GREEN)
    if t >= T_MISS:
        stamp(p, t, T_MISS, v.x(EARLY_X + 40), max(470, v.y(FLOOR - 640)), "MISSED IT", REDC)
    out = p.compose()
    for lay, pos in p.tops:
        out.alpha_composite(lay.filter(ImageFilter.GaussianBlur(10 * K)), pos)
        out.alpha_composite(lay, pos)
    return hq.downsample(out, W, H)


def clock_text(t):
    s = clock_s(t)
    m, sec = int(s // 60), int(s % 60)
    if t >= T_CLOSE:
        return "9:40", "GATE CLOSED"
    if t >= 15.9:
        return f"9:{m:02d}:{sec:02d}", "DOORS CLOSE 9:40"
    return f"9:{m:02d} AM", "DOORS CLOSE 9:40"


def frame(t):
    img = scene(t).convert("RGBA")
    # whip-pan motion blur on the scene only (the title and clock stay sharp)
    c0, c1 = cam(t - 1 / FPS), cam(t)
    vx = (c1[0] - c0[0]) * c1[2]
    in_whip = any(tw <= t < tw + 0.45 for tw in (T_WHIP1, T_WHIP2, T_WHIP3, T_WHIP4, T_DOOR_IN - 0.4))
    if in_whip and abs(vx) > 18:
        span = min(abs(vx) * 0.7, 220)
        a_ = np.asarray(img, np.float32)
        acc = np.zeros_like(a_)
        n = 16
        for j in range(n):
            acc += np.roll(a_, int(span * (j / (n - 1) - 0.5)), axis=1)
        img = Image.fromarray((acc / n).astype(np.uint8), "RGBA")
    img.alpha_composite(VIG)
    tp = hq.Panel(Image.new("RGBA", (W * K, TITLE_H * K), (0, 0, 0, 0)))
    if t < T_L1:
        tp.text((W / 2, 22), "WHO MAKES THE FLIGHT?", 58, (250, 250, 252), 255)
        c, sub = clock_text(t)
        late = clock_s(t) >= 35 * 60
        kk = 1 + (0.08 * (1 - (t * 2) % 1) if late and t < T_CLOSE else 0)
        tp.text((W / 2, 102), c, 76 * kk, REDC if late else GOLD, 255, neon=True, spacing=4)
        tp.text((W / 2, 200), sub, 30, REDC if t >= T_CLOSE else (200, 200, 215), 255, spacing=4)
    else:
        for t0, s2, y in ((T_L1, LINE1, 60), (T_L2, LINE2, 150)):
            if t < t0:
                continue
            k = int(clamp((t - t0) * CPS, 0, len(s2)))
            tp.text((W / 2, y), s2[:k] + " " * (len(s2) - k), 44 if len(s2) > 24 else 58,
                    (250, 250, 252) if t0 == T_L1 else GOLD, 255, neon=t0 == T_L2)
    tl = tp.compose(glow=0.8)
    img.alpha_composite(tl.resize((W, TITLE_H), Image.LANCZOS), (0, 0))
    rgb = hq.bloom(np.asarray(img.convert("RGB")), 0.45, 150, 26)
    if t < 0.22:
        rgb = np.clip(rgb.astype(np.float32) + 80 * (1 - t / 0.22), 0, 255).astype(np.uint8)
    for t0 in (T_BEEP, T_CLOSE, T_MISS):
        if t0 <= t < t0 + 0.12:
            rgb = np.clip(rgb.astype(np.float32) + 40 * (1 - (t - t0) / 0.12), 0, 255).astype(np.uint8)
    arr = rgb.astype(np.float32)
    if t >= T_FOLLOW:
        k = smooth(prog(t, T_FOLLOW, T_FOLLOW + 0.3))
        arr *= 1 - 0.75 * k
        card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        ff = font(BOLD, 76)
        spaced(cd, W / 2, H / 2 - 90, "FOLLOW", ff, (250, 250, 252, int(255 * k)), 6)
        spaced(cd, W / 2, H / 2 + 6, "FOR MORE", ff, (250, 250, 252, int(255 * k)), 6)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
        base.alpha_composite(card)
        return np.asarray(base.convert("RGB"))
    return np.clip(arr, 0, 255).astype(np.uint8)


def init_worker():
    global BG, VIG
    BG = Image.new("RGBA", (W * K, H * K), (8, 8, 18, 255))
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2)
    vig = (np.clip((r - 0.28) * 1.5, 0, 1) * 160).astype(np.uint8)
    top = (np.clip(1 - yy / 340, 0, 1) * 200).astype(np.uint8)
    VIG = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    VIG.putalpha(Image.fromarray(np.maximum(vig, top), "L"))


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
def synth(f, dur, bright=0.5, dec=7.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = sum((1 / k) * np.sin(2 * np.pi * f * k * tt) * (bright ** (k - 1)) for k in (1, 3, 5, 7))
    return x * np.minimum(1, tt / 0.004) * np.exp(-tt * dec)


def whoosh(fx, at, g=0.12, seed=1):
    n = int(0.45 * SR)
    sig = noise(0.45, seed, lo=300, hi=5000) * np.sin(np.linspace(0, np.pi, n)) ** 2
    mix_in(fx, sig, at - 0.15, g)


def chime(fx, at, g=0.06):
    mix_in(fx, music.marimba(midi(76), 1.4), at, g)
    mix_in(fx, music.marimba(midi(72), 1.6), at + 0.35, g)


def audio():
    n = int(DUR * SR)
    mus, fx = np.zeros((n, 2)), np.zeros((n, 2))
    # hook: a hit, the PA chime, and the clock ticking from the first frame
    mix_in(fx, tone(45, 1.2, (1, 0.6, 0.3), a=0.002, d=0.6), 0.0, 0.35)
    mix_in(fx, noise(0.4, 3, lo=800, hi=8000) * env(int(0.4 * SR), 0.001, 0.15), 0.0, 0.12)
    chime(fx, 0.15, 0.07)
    tt = 0.0
    while tt < T_CLOSE:
        hi = int(tt * 2) % 2 == 0
        g = 0.09 if tt < 1.4 else 0.04
        mix_in(fx, tone(2400 if hi else 1900, 0.04, (1, 0.5), a=0.0005, d=0.012) +
               0.5 * noise(0.04, 9, lo=2000, hi=8000) * env(int(0.04 * SR), 0.0005, 0.01), tt, g, 0.2)
        tt += 0.5 if tt < 14.6 else 0.25
    for tw in (T_WHIP1, T_WHIP2, T_WHIP3, T_WHIP4):
        whoosh(fx, tw, 0.14, int(tw * 10))
    # chase music: four-on-the-floor + a minor synth bass, building, from the doors to the gate
    bpm = 128
    beat = 60 / bpm
    chords = [57, 53, 55, 52]      # A F G E
    tt, i = T_DOORS - 0.1, 0
    while tt < T_CLOSE:
        bi = int((tt - T_DOORS) / (4 * beat)) % 4
        root = chords[bi]
        g = 0.05 + 0.06 * prog(tt, T_DOORS, T_CLOSE)
        if i % 4 == 0:
            mix_in(mus, tone(60, 0.25, (1,), a=0.002, d=0.1, sweep=42), tt, g * 2.6)
        if i % 2 == 1:
            mix_in(mus, noise(0.05, i, lo=6000, hi=12000) * env(int(0.05 * SR), 0.001, 0.02), tt, g * 0.5, 0.3)
        if i % 8 == 4:
            mix_in(mus, noise(0.15, 50 + i, lo=800, hi=5000) * env(int(0.15 * SR), 0.001, 0.06), tt, g * 0.9)
        mix_in(mus, synth(midi(root - 12), 0.2, 0.55, 9), tt, g * 1.1, -0.2)
        arp = [0, 7, 12, 15][i % 4] if bi != 3 else [0, 4, 7, 11][i % 4]
        mix_in(mus, synth(midi(root + 12 + arp), 0.16, 0.4, 12), tt, g * 0.45, 0.35 if i % 2 else -0.35)
        tt += beat / 2
        i += 1
    # footsteps while running
    for t0, t1, rate in ((T_DOORS, T_QUEUE, 0.17), (T_RUN2, T_WHIP3, 0.15), (T_WHIP4, T_DOOR_IN + 0.3, 0.15)):
        tt = t0
        while tt < t1:
            if not (T_JUMP < tt < T_JUMP + 0.5):
                mix_in(fx, noise(0.05, int(tt * 100), lo=100, hi=1500) * env(int(0.05 * SR), 0.001, 0.02), tt, 0.09,
                       0.1)
            tt += rate
    mix_in(fx, noise(0.7, 5, lo=200, hi=3000) * env(int(0.7 * SR), 0.05, 0.4), T_DOORS - 0.2, 0.06)
    # security beep
    for j in range(3):
        sq = np.sign(np.sin(2 * np.pi * 1250 * np.arange(int(0.14 * SR)) / SR)) * env(int(0.14 * SR), 0.002, 0.08)
        mix_in(fx, sq, T_BEEP + j * 0.2, 0.05)
    # gate PA, yawn, jump, final call
    chime(fx, T_WHIP3 + 0.25, 0.06)
    mix_in(fx, tone(330, 0.9, (1, 0.4), a=0.2, d=0.4, sweep=180), T_NAP, 0.05)
    mix_in(fx, noise(0.5, 12, lo=500, hi=6000) * np.sin(np.linspace(0, np.pi, int(0.5 * SR))), T_JUMP, 0.08)
    chime(fx, T_FINAL, 0.07)
    # the door: slam + a win sting, then the music drops out
    mix_in(fx, tone(55, 0.6, (1, 0.6), a=0.002, d=0.3) + 0.4 * np.pad(noise(0.3, 33, lo=100, hi=3000) *
                                                     env(int(0.3 * SR), 0.001, 0.1), (0, int(0.6 * SR) - int(0.3 * SR))), T_CLOSE, 0.3)
    for j, m in enumerate((72, 76, 79, 84)):
        mix_in(fx, synth(midi(m), 0.8, 0.4, 4), T_CLOSE + 0.05 + 0.07 * j, 0.05)
    # the twist: quiet room, snores, the jet leaving, a sting when he wakes
    for j in range(3):
        st = T_PAN + 0.1 + j * 0.55
        sn = noise(0.4, 70 + j, lo=60, hi=400) * np.sin(np.linspace(0, np.pi, int(0.4 * SR))) ** 2
        mix_in(fx, sn, st, 0.18)
    jet = noise(4.5, 90, lo=80, hi=2500) * np.sin(np.linspace(0, np.pi, int(4.5 * SR))) ** 1.5
    mix_in(fx, jet, T_PUSH, 0.07, 0.3)
    mix_in(fx, tone(180, 0.5, (1, 0.6, 0.4), a=0.002, d=0.3, sweep=90), T_WAKE, 0.12)
    mix_in(fx, tone(50, 0.9, (1, 0.6), a=0.002, d=0.5) + 0.35 * noise(0.9, 41, lo=400, hi=5000) *
           np.pad(env(int(0.45 * SR), 0.002, 0.12), (0, int(0.45 * SR))), T_MISS, 0.26)
    for j, m in enumerate((67, 63, 60, 55)):
        mix_in(mus, music.music_box(midi(m + 12), 1.8), T_MISS + 0.4 + j * 0.45, 0.055, 0.2)
    for k, m in enumerate((48, 55, 60, 63)):
        mix_in(mus, GS.pad(midi(m), 3.6, 0.5, 1.6), T_MISS + 0.4, 0.03, (k - 1.5) * 0.3)
    for t0, s in ((T_L1, LINE1), (T_L2, LINE2)):
        for i2, c in enumerate(s):
            if c != " ":
                mix_in(fx, noise(0.03, 500 + i2 + int(t0), lo=1200, hi=4000) * env(int(0.03 * SR), 0.001, 0.008),
                       t0 + i2 / CPS, 0.05)
    x = mus + fx
    m = int(XFADE * SR)
    k = np.linspace(0, 1, m)[:, None]
    x[-m:] = x[-m:] * (1 - k) + x[:m] * k
    x /= max(1.0, np.abs(x).max() / 0.9)
    return x


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "airport.mp4"
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
