#!/usr/bin/env python3
"""SHE CHOSE THE MONEY v2 - 31 s. Faces, the grind, a logical fall, two twists.

0.0  HOOK  a ring drops on the wet ground, he's crying behind it: "SHE SAID HE'D NEVER BE ENOUGH."
1.6  the bench: she laughs with the rich guy, looks down on him, drops the ring, leaves. He picks it up.
6.0  THE GRIND (DAY counter): delivery bike in the rain, half a cup of noodles, 4:00 AM alarm, [the rich guy: leased car,
     credit card], sells his phone, REJECTED x10, sick but typing.
13.7 RE-HOOK  3:00 AM, the laptop dies, head in his hands: "HE ALMOST QUIT."  the phone lights up: OFFER ACCEPTED.
16.3 the rise: a team, a tower, the money flies.  [the rich guy at APEX: PAST DUE]
19.0 APEX boardroom: "APEX HAS A NEW OWNER." the door opens - it's him. The rich guy's face.
24.0 outside, she's waiting, crying: "CAN WE START OVER?" He puts the ring she threw away in her hand and walks on.
     HE KEPT THE RING. / NOT THE PAIN.

    python3 stick/money2.py --stills [t ...]
    python3 stick/money2.py stick/money.mp4
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perfect_wave as PW  # noqa
import ai_job as AJ  # noqa
import hq  # noqa
import race as R  # noqa
from compare import ell, line, rrect, poly, figure, place, ik, FLOOR, K, W, H  # noqa
from perfect_wave import clamp, env, font, lerp, lerp_pose, mix_in, noise, prog, smooth, tone, write_wav  # noqa
from money_chars import hero, girl, rich, face, S, GOLD, RED  # noqa
import money as M  # noqa
from money import (pts_of, stand_hip, sit_hip, walk, text, stamp, money_fmt, lamp, lamp_glow, cached, bench, car,
                   rain, desk, laptop, chair, chair_back, city, compose, put, track, SEAT, CAR_GY)  # noqa

FPS, SR = 30, 44100
DUR = 31.0
NF = int(round(DUR * FPS))
STAND, SIT = PW.STAND, PW.SIT
T_BENCH, T_GRIND, T_RH, T_OFFER, T_RISE, T_ROOM, T_OUT = 1.6, 6.0, 13.7, 15.3, 16.3, 19.0, 24.0
GREEN = (60, 200, 110)
SHOTS = [("bike", 6.0), ("noodles", 7.1), ("alarm", 8.2), ("richcard", 9.3), ("phone", 10.4), ("reject", 11.5),
         ("sick", 12.6), ("quit", 13.7), ("rise", 16.3), ("pastdue", 17.9), ("room", 19.0)]


def shot_at(t):
    cur = None
    for name, t0 in SHOTS:
        if t >= t0:
            cur = (name, t - t0)
    return cur


def day_at(t):
    u = clamp((t - T_GRIND) / (T_RISE + 1.6 - T_GRIND))
    return max(1, int(round(1 + 1459 * u ** 1.6)))


def new_stage():
    st = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    return st, ImageDraw.Draw(st)


def ring(d, x, y, glint=0.0, r=9):
    d.ellipse(((x - r) * K, (y - r * 0.55) * K, (x + r) * K, (y + r * 0.55) * K), outline=GOLD + (255,), width=int(3.5 * K))
    ell(d, x + r * 0.4, y - r * 0.5, 3.5, 3.5, (230, 240, 255, 255))
    if glint > 0:
        for a in range(4):
            aa = a * math.pi / 2 + 0.4
            line(d, [(x + 6 * math.cos(aa), y - 4 + 6 * math.sin(aa)), (x + 18 * glint * math.cos(aa), y - 4 + 18 * glint * math.sin(aa))],
                 (255, 244, 200, 230), 2)


def set_arm(p, side, tgt, sgn=1):
    p = dict(p)
    p["h" + side] = tgt
    p["e" + side] = ik(p["neck"], tgt, 42 * S, 40 * S, sgn)
    return p


def clock(d, x, y, s_, col=(240, 80, 80), shake=0.0):
    x += shake * math.sin(y * 3 + shake * 40)
    rrect(d, (x - 46, y - 24, x + 46, y + 24), 6, (24, 24, 30, 255), outline=(90, 90, 100, 255), w=2)
    PW.spaced(d, x * K, y * K, s_, font("InterDisplay-Bold.otf", 30 * K), col + (255,), 2)


# ---------------------------------------------------------------- the bench (hook + act 1)
RING_DROP = 4.3     # bench-time when she drops the ring


def ring_y(u):
    """ring falling from her hand to the wet ground with a little bounce"""
    v = u - RING_DROP
    if v < 0:
        return None
    y0, g = FLOOR - 150, 1800
    tf = math.sqrt(150 / (g / 2))
    if v < tf:
        return y0 + g / 2 * v * v
    v2 = v - tf
    b = 0.22
    return FLOOR - 4 - max(0.0, 30 * (v2 / b) * (1 - v2 / b)) if v2 < b else FLOOR - 4


def bench_scene(u, tv, hook=False):
    st, d = new_stage()
    lamp(d, 900, u)
    bench(d, 560, 860, SEAT)
    HX = 770
    # -------- her
    gp, gexpr, gf = None, "laugh", 1
    if u < 1.6:
        gp = pts_of(dict(SIT, head=(14, -148)), 640, sit_hip(SEAT), 1)
        gexpr = "happy"
    elif u < 2.6:
        gp = pts_of(SIT, 640, sit_hip(SEAT), -1)
        gf, gexpr = -1, "happy"                 # looks at the car
    elif u < 3.0:
        k = smooth(prog(u, 2.6, 3.0))
        gp = pts_of(lerp_pose(SIT, STAND, k), 640, lerp(sit_hip(SEAT), stand_hip(), k), 1)
        gexpr = "smug"
    elif u < 4.8:                                # facing him: smug, the ring off, dropped
        gp = pts_of(STAND, 660, stand_hip(), 1)
        gexpr = "smug"
        if 3.6 <= u < 4.3:
            gp = set_arm(gp, "r", (gp["neck"][0] + 40, gp["neck"][1] + 30), 1)
    elif u < 5.6:
        pose, x = walk(660, 470, smooth(prog(u, 4.8, 5.6)), -1)
        gp, gf, gexpr = pts_of(pose, x, stand_hip(), -1), -1, "laugh"
    # -------- rich guy
    rp = None
    if 1.6 <= u < 5.7:
        rp = pts_of(STAND, 430, stand_hip(), 1)
        if u >= 4.8:
            rp = set_arm(rp, "r", (480, FLOOR - 150), 1)
    # -------- him
    if u < 3.0:
        hexpr = "happy" if u < 1.6 else ("sad" if u < 2.6 else "nervous")
        hp = pts_of(dict(SIT, head=(4, -150)), HX, sit_hip(SEAT), -1)
    else:
        hexpr = "sad" if u < 4.3 else "cry"
        hp = pts_of(dict(SIT, head=(10, -146)), HX, sit_hip(SEAT), -1)
        if 3.0 <= u < 3.8:
            k = smooth(prog(u, 3.0, 3.3)) * (1 - smooth(prog(u, 3.5, 3.8)))
            hp = set_arm(hp, "r", (lerp(hp["hr"][0], 700, k), lerp(hp["hr"][1], hp["neck"][1] + 10, k)), -1)
        if u >= 5.6:   # picks the ring up
            k = smooth(prog(u, 5.6, 6.0))
            hp = pts_of(lerp_pose(dict(SIT, head=(10, -146)), dict(SIT, head=(-30, -110), neck=(-20, -84), el=(-36, -30),
                                                                     hl=(-60, 30), er=(-30, -30), hr=(-56, 34)), k),
                        HX, sit_hip(SEAT), -1)
    hero(st, hp, "broke", -1, hexpr, tv)
    if gp is not None:
        girl(st, gp, f=gf, wind=0.2, expr=gexpr, t=tv)
        if u < 4.3 and u >= 3.0:
            hx_, hy_ = gp["hr"]
            ring(d, hx_ + 4, hy_ - 4, r=7)
    if rp is not None:
        rich(st, rp, "rich", 1, "laugh" if u >= 4.6 else "smug", tv)
    # car
    cx = lerp(1500, 300, 1 - (1 - smooth(prog(u, 0.6, 1.6))) ** 2) if u < 1.6 else (300 if u < 5.8 else 300 - 1500 * (u - 5.8) ** 2)
    if u >= 0.6 and cx > -400:
        car(d, cx, CAR_GY, -1)
    # the ring on the ground
    ry = ring_y(u)
    if ry is not None and not (u >= 5.9):
        ring(d, 690, ry, glint=0.6 if ry >= FLOOR - 5 else 0.0)
        if ry >= FLOOR - 5:
            v = u - RING_DROP - 0.3
            for j in range(2):
                rr = 20 + 90 * ((v + j * 0.3) % 0.9)
                d.ellipse(((690 - rr) * K, (FLOOR - 4 - rr * 0.18) * K, (690 + rr) * K, (FLOOR - 4 + rr * 0.18) * K),
                          outline=(180, 190, 220, int(160 * (1 - ((v + j * 0.3) % 0.9) / 0.9))), width=int(2 * K))
    rain(d, tv, smooth(prog(u, 3.4, 4.2)))
    glow = cached("lamp", lambda: lamp_glow(900))
    if hook:   # tight on the ring, him crying behind it
        return compose(st, glow, 2.6, 720, FLOOR - 130, spots=((700, 0.7),))
    return compose(st, glow, 1.6, 640, 1170, spots=((700, 0.7),))


# ---------------------------------------------------------------- the grind
def shot_bike(st, d, u, tv):
    for k in range(8):
        x = (k * 260 - tv * 500) % (W + 260) - 130
        line(d, [(x, FLOOR - 300), (x, FLOOR)], (60, 66, 80, 255), 5)
    bx = 540
    for wx in (bx - 70, bx + 70):
        d.ellipse(((wx - 36) * K, (FLOOR - 72) * K, (wx + 36) * K, FLOOR * K), outline=(150, 154, 164, 255), width=int(5 * K))
    line(d, [(bx - 70, FLOOR - 36), (bx - 10, FLOOR - 36), (bx + 30, FLOOR - 90), (bx + 70, FLOOR - 36)], (200, 60, 50, 255), 6)
    line(d, [(bx - 10, FLOOR - 36), (bx - 30, FLOOR - 96)], (200, 60, 50, 255), 6)
    line(d, [(bx + 30, FLOOR - 90), (bx + 40, FLOOR - 120)], (90, 90, 100, 255), 5)
    rrect(d, (bx - 110, FLOOR - 190, bx - 30, FLOOR - 110), 6, (230, 160, 40, 255), outline=(120, 80, 20, 255), w=2)
    ph = tv * 9
    pose = {"head": (30, -146), "neck": (22, -104), "kl": (40, 30 + 14 * math.sin(ph)), "fl": (30, 76 + 20 * math.sin(ph)),
            "kr": (40, 30 - 14 * math.sin(ph)), "fr": (30, 76 - 20 * math.sin(ph)), "el": (50, -70), "hl": (74, -36),
            "er": (54, -66), "hr": (78, -32)}
    p = pts_of(pose, bx - 30, FLOOR - 100, 1)
    hero(st, p, "broke", 1, "tired", tv)
    rain(d, tv, 1.0)
    return dict(z=1.7, cx=540, cy=1170)


def shot_noodles(st, d, u, tv):
    desk(d, 400, 720, FLOOR - 92)
    laptop(d, 600, FLOOR - 102, f=-1)
    cx = 440
    poly(d, [(cx - 30, FLOOR - 160), (cx + 30, FLOOR - 160), (cx + 22, FLOOR - 104), (cx - 22, FLOOR - 104)], (240, 236, 226, 255),
         outline=(150, 140, 120, 255), w=2)
    rrect(d, (cx - 30, FLOOR - 140, cx + 30, FLOOR - 126), 2, (220, 60, 50, 255))
    line(d, [(cx - 30, FLOOR - 132), (cx + 30, FLOOR - 132)], (40, 40, 40, 255), 2) if u > 0.5 else None
    PW.spaced(d, (cx + 70) * K, (FLOOR - 180) * K, "½", font("InterDisplay-Bold.otf", 44 * K), (240, 220, 120, 255), 0)
    chair(d, 330, SEAT + 6)
    p = pts_of(SIT, 330, sit_hip(SEAT + 6), 1)
    p = set_arm(p, "r", (cx - 6, FLOOR - 170 + 20 * math.sin(tv * 6)), 1)
    p = set_arm(p, "l", (cx - 20, FLOOR - 120), 1)
    line(d, [(p["hr"][0], p["hr"][1]), (cx + 6, FLOOR - 150)], (200, 170, 110, 255), 3)
    hero(st, p, "broke", 1, "tired", tv)
    clock(d, 680, FLOOR - 330, "11:58")
    return dict(z=1.7, cx=470, cy=1150)


def shot_alarm(st, d, u, tv):
    rrect(d, (300, FLOOR - 60, 760, FLOOR), 6, (70, 74, 96, 255))
    rrect(d, (300, FLOOR - 76, 760, FLOOR - 54), 8, (220, 224, 232, 255))
    rrect(d, (690, FLOOR - 96, 760, FLOOR - 70), 10, (240, 240, 246, 255))
    k = smooth(prog(u, 0.35, 0.8))
    lying = {"head": (-150, 0), "neck": (-108, 0), "el": (-60, 10), "hl": (-16, 10), "er": (-60, -6), "hr": (-16, -6),
             "kl": (56, 0), "fl": (113, 0), "kr": (56, -4), "fr": (113, -4)}
    sitting = dict(SIT)
    pose = lerp_pose(lying, sitting, k)
    p = pts_of(pose, 520 + 40 * k, FLOOR - 90 - 10 * k, -1 if k < 0.5 else 1)
    hero(st, p, "broke", 1, "tired" if u < 0.6 else "determined", tv)
    if k < 0.5:
        poly(d, [(330, FLOOR - 120), (680, FLOOR - 120), (690, FLOOR - 70), (320, FLOOR - 70)], (90, 110, 160, 255))
    clock(d, 760, FLOOR - 180, "4:00", shake=4 if u < 0.6 else 0)
    if u < 0.6:
        for j in range(3):
            line(d, [(810 + 8 * j, FLOOR - 210 - 6 * j), (830 + 10 * j, FLOOR - 230 - 8 * j)], (240, 80, 80, 255), 3)
    return dict(z=1.6, cx=560, cy=1170)


def shot_richcard(st, d, u, tv):
    car(d, 640, FLOOR, -1)
    rrect(d, (690, FLOOR - 170, 800, FLOOR - 140), 4, (240, 236, 220, 255), outline=(200, 40, 40, 255), w=2)
    PW.spaced(d, 745 * K, (FLOOR - 155) * K, "LEASED", font("InterDisplay-Bold.otf", 20 * K), (200, 40, 40, 255), 2)
    rp = pts_of(dict(STAND, er=(34, -80), hr=(66, -96)), 380, stand_hip(), 1)
    rich(st, rp, "rich", 1, "laugh", tv)
    hx, hy = rp["hr"]
    rrect(d, (hx - 4, hy - 20, hx + 38, hy + 4), 4, (30, 30, 34, 255), outline=GOLD + (255,), w=2)
    gp = pts_of(dict(STAND, el=(-26, -120), hl=(-30, -170)), 540, stand_hip(), -1)
    girl(st, gp, f=-1, wind=0.3, expr="laugh", t=tv)
    return dict(z=1.45, cx=580, cy=1150)


def shot_phone(st, d, u, tv):
    hp = pts_of(STAND, 470, stand_hip(), 1)
    bp = pts_of(STAND, 620, stand_hip(), -1)
    k = smooth(prog(u, 0.2, 0.6))
    mid = (540, FLOOR - 170)
    hp = set_arm(hp, "r", (lerp(hp["neck"][0] + 30, mid[0] - 10, k), lerp(FLOOR - 120, mid[1], k)), 1)
    bp = set_arm(bp, "r", (lerp(bp["neck"][0] - 30, mid[0] + 10, k), lerp(FLOOR - 120, mid[1], k)), -1)
    figure(st, bp, S, light=(0.4, -0.9), body=(150, 154, 166))
    hero(st, hp, "broke", 1, "sad", tv)
    px = hp["hr"][0] if u < 0.7 else bp["hr"][0]
    rrect(d, (px - 9, mid[1] - 26, px + 9, mid[1] + 4), 3, (18, 18, 24, 255))
    if u >= 0.7:
        rrect(d, (hp["hr"][0] - 18, hp["hr"][1] - 8, hp["hr"][0] + 18, hp["hr"][1] + 8), 2, (110, 180, 110, 255))
    PW.spaced(d, 540 * K, (FLOOR - 420) * K, "SOLD HIS PHONE", font("InterDisplay-Bold.otf", 34 * K), (236, 238, 246, 220), 3)
    return dict(z=1.6, cx=540, cy=1150)


def shot_reject(st, d, u, tv):
    desk(d, 400, 720, FLOOR - 92)
    laptop(d, 480, FLOOR - 102, f=-1)
    chair(d, 330, SEAT + 6)
    p = pts_of(SIT, 330, sit_hip(SEAT + 6), 1)
    for side, dx in (("l", 0), ("r", 18)):
        p = set_arm(p, side, (440 + dx, FLOOR - 104 - 5 * max(0, math.sin(tv * 14 + dx))), 1)
    hero(st, p, "broke", 1, "determined", tv)
    n = min(10, int(u / 0.09) + 1)
    rng = np.random.default_rng(5)
    for j in range(n):
        stamp(d, 600 + rng.uniform(-150, 150), FLOOR - 260 - rng.uniform(0, 260), "REJECTED", (220, 50, 50), 1.0,
              rot=rng.uniform(-0.4, 0.4), size=26)
    PW.spaced(d, 540 * K, (FLOOR - 600) * K, f"x{n}", font("InterDisplay-Bold.otf", 60 * K), (220, 50, 50, 255), 2)
    return dict(z=1.4, cx=540, cy=1110)


def shot_sick(st, d, u, tv):
    desk(d, 400, 720, FLOOR - 92)
    laptop(d, 480, FLOOR - 102, f=-1)
    chair(d, 330, SEAT + 6)
    p = pts_of(dict(SIT, head=(16, -140)), 330, sit_hip(SEAT + 6), 1)
    for side, dx in (("l", 0), ("r", 18)):
        p = set_arm(p, side, (440 + dx, FLOOR - 104 - 5 * max(0, math.sin(tv * 10 + dx))), 1)
    hero(st, p, "broke", 1, "tired", tv)
    nx, ny = p["neck"]
    poly(d, [(nx - 30, ny - 36), (nx + 16, ny - 24), (nx + 22, ny + 90), (nx - 52, ny + 90)], (110, 140, 120, 235))
    hx, hy = p["head"]
    line(d, [(hx + 20, hy + 18), (hx + 46, hy + 24)], (230, 230, 236, 255), 3)
    ell(d, hx + 46, hy + 24, 3, 3, (230, 60, 60, 255))
    PW.spaced(d, (hx + 80) * K, (hy - 40) * K, "39°", font("InterDisplay-Bold.otf", 30 * K), (240, 90, 90, 255), 1)
    return dict(z=1.7, cx=520, cy=1150)


def shot_quit(st, d, u, tv):
    desk(d, 400, 720, FLOOR - 92)
    off = u < 0.15 or u >= 1.6
    laptop(d, 480, FLOOR - 102, glow=not (0.15 <= u < 1.6) and u < 0.15, f=-1)
    chair(d, 330, SEAT + 6)
    clock(d, 760, FLOOR - 400, "3:00")
    if u < 1.6:   # head in his hands
        pose = dict(SIT, head=(30, -124), neck=(16, -100), el=(40, -60), hl=(34, -112), er=(46, -56), hr=(40, -108))
        p = pts_of(pose, 330, sit_hip(SEAT + 6), 1)
        hero(st, p, "broke", 1, "cry", tv)
    else:         # the phone lights up
        k = smooth(prog(u, 1.6, 2.0))
        pose = lerp_pose(dict(SIT, head=(30, -124), neck=(16, -100)), dict(SIT, head=(16, -150), neck=(6, -108)), k)
        p = pts_of(pose, 330, sit_hip(SEAT + 6), 1)
        p = set_arm(p, "r", (lerp(p["hr"][0], p["neck"][0] + 60, k), lerp(p["hr"][1], p["neck"][1] - 10, k)), 1)
        hero(st, p, "broke", 1, "shocked" if u < 2.2 else "happy", tv)
    # the phone on the desk
    px, py = (450, FLOOR - 110) if u < 1.6 else p["hr"]
    rrect(d, (px - 10, py - 30, px + 10, py + 2), 3, (18, 18, 24, 255))
    if u >= 1.5:
        rrect(d, (px - 8, py - 27, px + 8, py - 1), 2, GREEN + (255,))
    return dict(z=1.7, cx=500, cy=1150)


def shot_rise(st, d, u, tv):
    hgt = 260 + 380 * smooth(clamp(u / 1.5))
    TX = 700
    poly(d, [(TX - 100, FLOOR - hgt), (TX + 100, FLOOR - hgt), (TX + 100, FLOOR), (TX - 100, FLOOR)], (30, 38, 62, 255),
         outline=(80, 90, 120, 255), w=2)
    rng = np.random.default_rng(5)
    for yy in np.arange(FLOOR - hgt + 56, FLOOR - 14, 22):
        for xx in np.arange(TX - 86, TX + 86, 18):
            if rng.uniform() < 0.7:
                rrect(d, (xx, yy, xx + 10, yy + 12), 1, (250, 214, 130, 230))
    rrect(d, (TX - 50, FLOOR - hgt + 10, TX + 50, FLOOR - hgt + 44), 4, RED + (255,))
    PW.spaced(d, TX * K, (FLOOR - hgt + 27) * K, "HIM.CO", font("InterDisplay-Bold.otf", 22 * K), (255, 255, 255, 255), 2)
    for j in range(3):
        figure(st, pts_of(STAND, 200 + 80 * j, stand_hip(), 1), S * 0.95, light=(0.4, -0.9))
    p = pts_of(dict(STAND, er=(30, -150), hr=(60, -190)), 500, stand_hip(), 1)
    hero(st, p, "ceo", 1, "happy", tv)
    rng = np.random.default_rng(int(tv * 8))
    for _ in range(16):
        v = rng.uniform()
        rrect(d, (rng.uniform(200, 900), FLOOR - 700 + 600 * v, 0, 0) if False else
              (x0 := rng.uniform(200, 900), FLOOR - 700 + 600 * v, x0 + 32, FLOOR - 684 + 600 * v), 2, (110, 180, 110, 220))
    return dict(z=1.25, cx=560, cy=1080)


def shot_pastdue(st, d, u, tv):
    desk(d, 400, 720, FLOOR - 92)
    laptop(d, 480, FLOOR - 102, f=-1)
    chair(d, 330, SEAT + 6)
    p = pts_of(dict(SIT, head=(14, -146)), 330, sit_hip(SEAT + 6), 1)
    p = set_arm(p, "r", (430, FLOOR - 160), 1)
    rich(st, p, "broke", 1, "nervous", tv)
    for j, t0 in enumerate((0.15, 0.55, 0.95)):
        stamp(d, 560 + 60 * j, FLOOR - 250 - 70 * j, "PAST DUE", (220, 50, 50), hq.pop(u, t0, 0.18) if u >= t0 else 0,
              rot=-0.2 + 0.2 * j, size=26)
    return dict(z=1.6, cx=520, cy=1150)


SHOT_FN = {"bike": shot_bike, "noodles": shot_noodles, "alarm": shot_alarm, "richcard": shot_richcard, "phone": shot_phone,
           "reject": shot_reject, "sick": shot_sick, "quit": shot_quit, "rise": shot_rise, "pastdue": shot_pastdue}


# ---------------------------------------------------------------- the boardroom
def room_back():
    g, d = new_stage()
    poly(d, [(0, 0), (W, 0), (W, FLOOR), (0, FLOOR)], (18, 20, 28, 255))
    city(d, 80, 700, FLOOR - 640, FLOOR - 170, seed=4)
    rrect(d, (710, FLOOR - 600, 930, FLOOR - 510), 6, (24, 28, 44, 255))
    PW.spaced(d, 820 * K, (FLOOR - 555) * K, "APEX", font("InterDisplay-Bold.otf", 52 * K), (120, 170, 255, 255), 10)
    return g


def room_scene(u, tv):
    st, d = new_stage()
    # the door (right)
    open_k = smooth(prog(u, 1.5, 1.9))
    rrect(d, (880, FLOOR - 300, 1010, FLOOR), 4, (16, 16, 20, 255))
    poly(d, [(880, FLOOR - 300), (880 + 130 * (1 - open_k), FLOOR - 300 - 10 * open_k), (880 + 130 * (1 - open_k), FLOOR + 10 * open_k),
             (880, FLOOR)], (70, 52, 40, 255), outline=(40, 30, 22, 255), w=2)
    # seated team, the rich guy closest
    for j, x in enumerate((360, 500)):
        chair(d, x, SEAT + 6)
        figure(st, pts_of(SIT, x, sit_hip(SEAT + 6), 1), S, light=(0.4, -0.9))
    chair(d, 220, SEAT + 6)
    rexpr = "smug" if u < 1.9 else ("shocked" if u < 3.6 else "nervous")
    rk = smooth(prog(u, 2.0, 2.3))
    rp = pts_of(lerp_pose(SIT, dict(SIT, head=(-6, -154), neck=(-2, -110)), rk), 220, sit_hip(SEAT + 6), 1)
    rich(st, rp, "broke", 1, rexpr, tv)
    rrect(d, (150, FLOOR - 98, 700, FLOOR - 86), 3, (90, 70, 52, 255), outline=(40, 30, 22, 255), w=1.5)
    for x in (180, 670):
        line(d, [(x, FLOOR - 86), (x, FLOOR)], (50, 40, 32, 255), 7)
    # him: walks in from the door
    if u >= 1.8:
        pose, x = walk(950, 780, smooth(prog(u, 1.8, 2.8)), -1)
        if u >= 2.8:
            pose, x = STAND, 780
        hp = pts_of(pose, x, stand_hip(), -1)
        hero(st, hp, "ceo", -1, "neutral" if u < 3.4 else "happy", tv)
    hit = 0.05 * hq.pop(u, 2.0, 0.25) if u >= 2.0 else 0
    return compose(st, None, 1.35 + hit + 0.03 * u / 5, 520, 1130, spots=((520, 1.0), (840, 0.7)),
                   back=cached("room", room_back))


# ---------------------------------------------------------------- outside: the ring
def out_scene(u, tv):
    st, d = new_stage()
    lamp(d, 860, u)
    # building entrance
    poly(d, [(560, FLOOR - 600), (1080, FLOOR - 600), (1080, FLOOR), (560, FLOOR)], (26, 32, 52, 255))
    rrect(d, (640, FLOOR - 300, 780, FLOOR), 4, (200, 210, 230, 70))
    rrect(d, (600, FLOOR - 580, 840, FLOOR - 510), 6, RED + (255,))
    PW.spaced(d, 720 * K, (FLOOR - 545) * K, "HIM.CO", font("InterDisplay-Bold.otf", 40 * K), (255, 255, 255, 255), 8)
    gx = 430
    # him: out the door, stops, gives the ring, walks on
    if u < 1.2:
        pose, x = walk(710, 560, smooth(prog(u, 0.0, 1.2)), -1)
    elif u < 3.6:
        pose, x = STAND, 560
    else:
        pose, x = walk(560, 120, smooth(prog(u, 3.6, 6.0)), -1)
    hp = pts_of(pose, x, stand_hip(), -1)
    gp = pts_of(STAND, gx, stand_hip(), 1)
    if 2.0 <= u < 3.6:     # the ring into her hand
        k = smooth(prog(u, 2.0, 2.5))
        hp = set_arm(hp, "r", (lerp(hp["hr"][0], 500, k), lerp(hp["hr"][1], FLOOR - 160, k)), 1)
        gp = set_arm(gp, "r", (lerp(gp["hr"][0], 486, k), lerp(gp["hr"][1], FLOOR - 152, k)), 1)
    gexpr = "cry" if u < 3.0 else "sad"
    if u >= 3.6:
        gp = set_arm(gp, "r", (486, FLOOR - 152), 1)
    girl(st, gp, f=1, wind=0.2, expr=gexpr, t=tv)
    hero(st, hp, "ceo", -1 if u >= 3.6 or u < 1.2 else -1, "neutral" if u < 3.6 else "happy", tv)
    if u >= 1.6:
        rx_, ry_ = (gp["hr"] if u >= 2.5 else hp["hr"])
        ring(d, rx_, ry_ - 6, glint=0.8 if 1.6 <= u < 2.6 else 0.3)
    M_bubble(st, tv, u, 0.4, 2.0, "CAN WE START OVER?", gx + 10, FLOOR - 290)
    rain(d, tv, 0.5, seed=12, n=80)
    glow = cached("lamp_out", lambda: lamp_glow(860))
    return compose(st, glow, 1.5, 500, 1150, spots=((480, 0.9),))


def M_bubble(st, tv, u, a, b, s, x, y):
    if a <= u < b:
        R.bubble(st, u, a, b, s, x, y, size=28)


# ---------------------------------------------------------------- frame
def header_day(im, t):
    d = ImageDraw.Draw(im)
    PW.spaced(d, W / 2, 40, f"DAY {day_at(t):,}", font("InterDisplay-Bold.otf", 96), (246, 246, 250, 255), 6)


def frame(t):
    if t < T_BENCH:
        u = RING_DROP + 0.5 + 0.9 * min(t, 1.0)
        im = bench_scene(u, t, hook=True)
        a = hq.pop(t, 0.35, 0.25) if t >= 0.35 else 0
        if a > 0:
            text(im, W / 2, 330, "SHE SAID HE'D", int(100 * max(0.3, a)))
            text(im, W / 2, 330 + int(112 * max(0.3, a)), "NEVER BE ENOUGH.", int(100 * max(0.3, a)), col=GOLD)
    elif t < T_GRIND:
        u = t - T_BENCH + 0.3
        im = bench_scene(u, t)
        d = ImageDraw.Draw(im)
        PW.spaced(d, 270, 170, "HIM", font("Inter-SemiBold.otf", 24), (214, 220, 238, 255), 6)
        PW.spaced(d, 270, 206, "$12", font("InterDisplay-Bold.otf", 58), (236, 238, 246, 255), 2)
        a = smooth(prog(u, 1.7, 2.0))
        PW.spaced(d, 810, 170, "THE RICH GUY", font("Inter-SemiBold.otf", 24), (214, 220, 238, int(255 * a)), 6)
        PW.spaced(d, 810, 206, "$2,000,000", font("InterDisplay-Bold.otf", 58), GOLD + (int(255 * a),), 2)
    elif t < T_ROOM:
        name, u = shot_at(t)
        st, d = new_stage()
        cam = SHOT_FN[name](st, d, u, t)
        back = cached("room", room_back) if name == "pastdue" else None
        im = compose(st, None, cam["z"], cam["cx"], cam["cy"], spots=((cam["cx"], 1.0),), back=back)
        header_day(im, t)
        if name in ("richcard", "pastdue"):
            d = ImageDraw.Draw(im)
            debt = 38000 if name == "richcard" else 412000
            PW.spaced(d, W / 2, 160, "MEANWHILE, THE RICH GUY", font("Inter-SemiBold.otf", 26), (214, 220, 238, 255), 5)
            PW.spaced(d, W / 2, 200, f"DEBT: ${debt:,}", font("InterDisplay-Bold.otf", 54), (236, 80, 70, 255), 2)
        if name == "rise":
            d = ImageDraw.Draw(im)
            v = math.exp(lerp(math.log(12), math.log(40000000), smooth(clamp(u / 1.5))))
            PW.spaced(d, W / 2, 170, "HIM", font("Inter-SemiBold.otf", 26), (214, 220, 238, 255), 6)
            PW.spaced(d, W / 2, 206, money_fmt(v), font("InterDisplay-Bold.otf", 64), GREEN + (255,), 2)
        if name == "quit":
            a = hq.pop(u, 0.25, 0.25) * (1 - smooth(prog(u, 1.4, 1.6))) if u >= 0.25 else 0
            if a > 0:
                text(im, W / 2, 330, "HE ALMOST QUIT.", 84, a=min(1, a))
            a2 = hq.pop(u, 1.65, 0.25) if u >= 1.65 else 0
            if a2 > 0:
                text(im, W / 2, 310, "THEN ONE EMAIL", 66, a=min(1, a2))
                text(im, W / 2, 386, "CHANGED EVERYTHING.", 66, col=GREEN, a=min(1, a2))
                text(im, W / 2, 470, "OFFER ACCEPTED", 40, col=GREEN, a=min(1, a2), serif=False)
    elif t < T_OUT:
        u = t - T_ROOM
        im = room_scene(u, t)
        a = smooth(prog(u, 0.1, 0.4)) * (1 - smooth(prog(u, 1.6, 1.9)))
        if a > 0:
            text(im, W / 2, 300, "APEX HAS A NEW OWNER.", 64, a=a)
    else:
        u = t - T_OUT
        im = out_scene(u, t)
        for j, s in enumerate(("HE KEPT THE RING.", "NOT THE PAIN.")):
            a = smooth(prog(u, 4.0 + 0.8 * j, 4.4 + 0.8 * j))
            if a > 0:
                text(im, W / 2, 220 + j * 90, s, 76, col=(GOLD if j else (246, 240, 226)), a=a)
    cuts = [T_BENCH, T_ROOM, T_OUT] + [s[1] for s in SHOTS]
    for c in cuts:
        if c <= t < c + 0.08:
            im = Image.blend(im.convert("RGB"), Image.new("RGB", (W, H), (255, 255, 255)), 0.5 * (1 - (t - c) / 0.08))
    return np.asarray(im.convert("RGB"))


def render(i):
    return frame(i / FPS).tobytes()


HIT = 30.0   # Rynos Theme: big entrance -> the door opens


def audio():
    n = int(DUR * SR)
    out = np.zeros((n, 2))
    put(out, track("Bittersweet.mp3", 2.0, T_GRIND + 0.6), 0.0, 0.9, fin=0.05, fout=0.6)
    st = HIT - (T_ROOM + 2.0 - T_GRIND)
    put(out, track("Rynos Theme.mp3", st, DUR - T_GRIND), T_GRIND - 0.1, 1.0, fin=0.4, fout=1.2)
    # the ring
    for at, g in ((0.12, 0.5), (0.34, 0.25), (T_BENCH - 0.3 + RING_DROP + 0.3, 0.45)):
        mix_in(out, tone(2600, 0.5, (1, 2.7, 4.1), a=0.001, d=0.4), at, g * 0.5, 0.2)
    mix_in(out, tone(1800, 1.2, (1, 2, 3), a=0.01, d=1.0), T_OUT + 1.6, 0.12, 0.0)
    # alarm
    for j in range(5):
        mix_in(out, tone(1400, 0.08, (1, 2), a=0.002, d=0.04), 8.2 + j * 0.12, 0.2, 0.3)
    # stamps
    for j in range(10):
        mix_in(out, tone(90, 0.1, (1, 2.5), a=0.001, d=0.07), 11.5 + j * 0.09, 0.25, 0.0)
    for j, t0 in enumerate((0.15, 0.55, 0.95)):
        mix_in(out, tone(90, 0.1, (1, 2.5), a=0.001, d=0.07), 17.9 + t0, 0.3, -0.3)
    # phone buzz + ding
    mix_in(out, tone(180, 0.4, (1, 2), a=0.01, d=0.3), T_RH + 1.5, 0.25, 0.0)
    mix_in(out, tone(880, 0.6, (1, 2, 3), a=0.002, d=0.5), T_RH + 1.62, 0.2, 0.0)
    # the door
    mix_in(out, noise(0.5, 4, lo=80, hi=1200)[:int(0.5 * SR)] * env(int(0.5 * SR), 0.01, 0.35), T_ROOM + 1.5, 0.3, 0.4)
    tt = np.arange(n) / SR
    out *= np.clip((DUR - tt) / 0.8, 0.0, 1)[:, None]
    out /= max(1.0, np.abs(out).max() / 0.9)
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    if "--stills" in sys.argv:
        ts = [float(a) for a in sys.argv[2:]]
        sheet = Image.new("RGB", (360 * len(ts), 640))
        for j, t in enumerate(ts):
            sheet.paste(Image.fromarray(frame(t)).resize((360, 640), Image.LANCZOS), (j * 360, 0))
        p = os.path.join(here, "money", "stills.png")
        sheet.save(p)
        print(p)
        return
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "money.mp4")
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
    print('Credit: Music: "Bittersweet" and "Rynos Theme" by Kevin MacLeod (incompetech.com), CC BY 4.0')


if __name__ == "__main__":
    main()
