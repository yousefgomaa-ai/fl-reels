#!/usr/bin/env python3
"""WAIT FOR HIS LAST STEPS - one night road, one father and son, 40 years in 21.5 s; loops.

Same night stage as compare.py (spotlights, shaded figures, wet-floor reflection, dust). The camera walks with them
along a road of street lamps. One counter on top: AGE (the son's). The father ages from scene to scene (hunch, slower,
greyer, a cane). The son wears the red scarf.

  AGE 1   0.0-3.0   close-up: a tiny hand around a big finger; pull back - dad, bent over, walks him; he falls;
                    dad lifts him up high.   (HE TAUGHT YOU TO WALK.)
  AGE 6   3.0-6.5   a little bike, dad running behind holding the seat - lets go - he rides off; dad cheers.
  AGE 16  6.5-10.0  headphones and phone, walking ahead; dad reaches for his shoulder; he speeds up; dad's hand
                    stays in the air. (the music stops)
  AGE 25  10.0-13.5 suitcase into the car, a wave, the car leaves; dad alone under the lamp.
  AGE 40  13.5-17.0 dad old on a bench with a cane; the son rushes past on the phone; dad half rises, sits back.
  AGE 45  17.0-21.5 the son comes back, offers his hand; dad stands; they walk slowly at dad's pace; close-up on the
                    hands (mirrors frame 0).  HE WAITED FOR YOUR FIRST STEPS. / WAIT FOR HIS LAST ONES.

    python3 stick/steps.py stick/steps.mp4
    ONLY_FRAMES=0,1.5,2.7,4.4,5.8,8.6,11.8,15,18.9,21.2 python3 stick/steps.py /tmp/steps
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
import compare as C  # noqa
from compare import ell, line, rrect, poly, figure, place, ik, FLOOR, K, W, H, INK, BODY  # noqa
from perfect_wave import clamp, env, font, lerp, lerp_pose, midi, mix_in, noise, prog, smooth, tone, write_wav  # noqa

FPS = 30
SR = 44100
DUR = 24.5
NF = int(round(DUR * FPS))
SC = [0.0, 3.2, 6.8, 11.0, 14.8, 18.8, DUR]
AGES = [1, 6, 16, 25, 40, 45]
DAD_AGE = [0.0, 0.08, 0.3, 0.5, 0.85, 0.9]
SON_S = [0.45, 0.62, 1.02, 1.12, 1.12, 1.12]
DAD_S = 1.2
SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
STAND = PW.STAND


def scene_of(t):
    for i in range(6):
        if t < SC[i + 1]:
            return i, t - SC[i]
    return 5, t - SC[5]


# ---------------------------------------------------------------- people
def dad_col(a):
    return tuple(int(lerp(c0, c1, a)) for c0, c1 in zip(BODY, (168, 170, 178)))


def aged(pose, a):
    """the father's hunch: head and shoulders forward and down"""
    p = dict(pose)
    hx, hy = p["head"]
    nx, ny = p["neck"]
    p["head"] = (hx + 26 * a, hy + 16 * a)
    p["neck"] = (nx + 18 * a, ny + 8 * a)
    for k in ("el", "hl", "er", "hr"):
        x, y = p[k]
        p[k] = (x + 14 * a, y + 6 * a)
    return p


def walk(ph, amp=1.0, arms=0.3):
    p = AJ.walk(ph, STAND)
    if amp < 1.0:
        for k in ("kl", "fl", "kr", "fr"):
            x, y = p[k]
            p[k] = (x * amp, STAND[k][1] + (y - STAND[k][1]) * amp)
    for side, off in (("l", math.pi), ("r", 0.0)):
        b = -arms * math.sin(ph + off)
        ex, ey = 40 * math.sin(b), -104 + 40 * math.cos(b)
        p["e" + side] = (ex, ey)
        p["h" + side] = (ex + 38 * math.sin(b + 0.25), ey + 38 * math.cos(b + 0.25))
    return p


def grounded(pose, x, s, feet=FLOOR):
    low = max(pose["fl"][1], pose["fr"][1])
    return (x, feet - low * s)


def reach(pts, s, hand, target, sgn=1):
    """bend the arm so the hand lands on target"""
    side = hand[-1]
    pts = dict(pts)
    pts["h" + side] = target
    pts["e" + side] = ik(pts["neck"], target, 42 * s, 40 * s, sgn)
    return pts


BEND = dict(STAND, head=(34, -136), neck=(24, -100), er=(46, -64), hr=(58, -26))
SIT_FLOOR = {"head": (-6, -140), "neck": (-4, -98), "el": (-24, -52), "hl": (-34, -10), "er": (24, -52), "hr": (40, -16),
             "kl": (44, -30), "fl": (90, -2), "kr": (40, -26), "fr": (86, 2)}
LIFT = dict(STAND, head=(0, -154), el=(-26, -146), hl=(-14, -196), er=(26, -146), hr=(14, -196))
WAVE = dict(STAND, er=(32, -130), hr=(44, -184))
SIT_B = {"head": (12, -146), "neck": (8, -104), "el": (24, -58), "hl": (44, -34), "er": (30, -60), "hr": (52, -40),
         "kl": (56, -2), "fl": (58, 62), "kr": (52, 2), "fr": (52, 64)}
REACH_OUT = dict(STAND, er=(40, -100), hr=(84, -106))
OFFER = dict(STAND, head=(20, -140), neck=(12, -102), er=(40, -70), hr=(76, -64))
PHONE_EAR = dict(STAND, er=(20, -84), hr=(10, -132))


# ---------------------------------------------------------------- props
def hands_hold(d, p, s_big, s_small, old_holds=False):
    """a small hand wrapped around a big finger (frame 0) or an old hand holding a strong one (the end)"""
    x, y = p
    if not old_holds:
        line(d, [(x - 4 * s_big, y - 6 * s_big), (x + 6 * s_big, y + 16 * s_big)], (232, 232, 236, 255), 9 * s_big)
        ell(d, x + 4 * s_small, y + 6 * s_big, 9 * s_small * 1.6, 9 * s_small * 1.6, (240, 240, 244, 255),
            outline=INK + (255,), w=2)
        for j in range(3):
            line(d, [(x - 4 * s_small * 1.6 + j * 5 * s_small, y + 2 * s_big),
                     (x - 4 * s_small * 1.6 + j * 5 * s_small, y + 10 * s_big)], (180, 182, 190, 255), 1.5)
    else:
        ell(d, x, y, 12 * s_big, 10 * s_big, (226, 227, 232, 255), outline=INK + (255,), w=2)
        ell(d, x + 6 * s_big, y + 4 * s_big, 10 * s_small, 8 * s_small, (176, 178, 186, 255), outline=INK + (255,), w=2)
        for j in range(3):
            line(d, [(x + j * 4 * s_small, y), (x + 3 + j * 4 * s_small, y + 9 * s_small)], (120, 122, 130, 255), 1.5)


def cane(d, hand, s):
    hx, hy = hand
    line(d, [(hx, hy), (hx + 6 * s, FLOOR)], (120, 84, 50, 255), 6 * s)
    line(d, [(hx - 12 * s, hy - 4), (hx + 2, hy)], (120, 84, 50, 255), 6 * s)


def mini_bike(d, cx, col, ph, spin, sc):
    r = 95 * sc
    wy = FLOOR - r
    wl, wr = cx - 125 * sc, cx + 125 * sc
    for wx in (wl, wr):
        ell(d, wx, wy, r, r, None, outline=(24, 24, 28, 255), w=12 * sc)
        for j in range(6):
            a = spin + j * math.pi / 3
            line(d, [(wx, wy), (wx + (r - 8) * math.cos(a), wy + (r - 8) * math.sin(a))], (120, 124, 134, 255), 2)
    crank = (cx - 10 * sc, wy)
    seat = (cx - 55 * sc, FLOOR - 250 * sc)
    head_t = (cx + 85 * sc, FLOOR - 255 * sc)
    c4 = col + (255,)
    line(d, [(wl, wy), crank, seat, (wl, wy)], c4, 12 * sc)
    line(d, [crank, head_t, (wr, wy)], c4, 12 * sc)
    line(d, [seat, (head_t[0] - 10 * sc, head_t[1] + 4 * sc)], c4, 12 * sc)
    line(d, [(seat[0] - 10 * sc, seat[1] - 6 * sc), (seat[0] + 36 * sc, seat[1] - 8 * sc)], (26, 26, 30, 255), 12 * sc)
    line(d, [head_t, (head_t[0] + 8 * sc, head_t[1] - 30 * sc), (head_t[0] + 50 * sc, head_t[1] - 36 * sc)],
         (40, 40, 46, 255), 9 * sc)
    pa = (crank[0] + 34 * sc * math.cos(ph), crank[1] + 34 * sc * math.sin(ph))
    pb = (crank[0] - 34 * sc * math.cos(ph), crank[1] - 34 * sc * math.sin(ph))
    line(d, [pa, pb], (40, 40, 46, 255), 6 * sc)
    return {"seat": seat, "bar": (head_t[0] + 50 * sc, head_t[1] - 36 * sc), "pa": pa, "pb": pb, "crank": crank}


def headphones(d, head, s):
    hx, hy = head
    d.arc([(hx - 30 * s) * K, (hy - 36 * s) * K, (hx + 30 * s) * K, (hy + 20 * s) * K], 190, 350, fill=(30, 30, 36, 255),
          width=int(7 * s * K))
    ell(d, hx - 26 * s, hy + 2 * s, 9 * s, 13 * s, (30, 30, 36, 255))
    ell(d, hx + 26 * s, hy + 2 * s, 9 * s, 13 * s, (30, 30, 36, 255))


def phone(d, hand, s, lit=True):
    hx, hy = hand
    rrect(d, (hx - 8 * s, hy - 14 * s, hx + 8 * s, hy + 14 * s), 3, (18, 18, 24, 255))
    if lit:
        rrect(d, (hx - 6 * s, hy - 11 * s, hx + 6 * s, hy + 11 * s), 2, (150, 190, 255, 255))


def suitcase(d, hand, s):
    hx, hy = hand
    line(d, [(hx, hy), (hx - 22 * s, hy + 40 * s)], (60, 62, 70, 255), 4 * s)
    rrect(d, (hx - 70 * s, hy + 40 * s, hx - 4 * s, hy + 120 * s), 8, (70, 90, 140, 255), outline=INK + (255,), w=2)
    ell(d, hx - 60 * s, hy + 124 * s, 5 * s, 5 * s, (20, 20, 24, 255))
    ell(d, hx - 14 * s, hy + 124 * s, 5 * s, 5 * s, (20, 20, 24, 255))


def briefcase(d, hand, s):
    hx, hy = hand
    rrect(d, (hx - 24 * s, hy + 6 * s, hx + 24 * s, hy + 40 * s), 4, (60, 40, 30, 255), outline=INK + (255,), w=2)
    line(d, [(hx - 8 * s, hy + 6 * s), (hx - 8 * s, hy), (hx + 8 * s, hy), (hx + 8 * s, hy + 6 * s)], (40, 30, 24, 255), 3)


def bench(d, x):
    rrect(d, (x - 130, FLOOR - 74, x + 130, FLOOR - 62), 3, (110, 80, 56, 255), outline=INK + (255,), w=2)
    rrect(d, (x - 130, FLOOR - 150, x + 130, FLOOR - 136), 3, (110, 80, 56, 255), outline=INK + (255,), w=2)
    for xx in (x - 110, x + 110):
        line(d, [(xx, FLOOR - 62), (xx, FLOOR)], (40, 40, 46, 255), 7)
        line(d, [(xx - 10, FLOOR - 74), (xx - 18, FLOOR - 150)], (40, 40, 46, 255), 6)


def lamps(d, c):
    C.street(d, c)


# ---------------------------------------------------------------- scenes: return lines, spots, (fx, fy, z), extra
def scroll(st, pieces):
    """piecewise-constant speeds [(t0, v)], integrated"""
    x = 0.0
    for i, (t0, v) in enumerate(pieces):
        t1 = pieces[i + 1][0] if i + 1 < len(pieces) else 1e9
        if st <= t0:
            break
        x += v * (min(st, t1) - t0)
    return x


def s0(stage, d, st, T):
    a = DAD_AGE[0]
    ks = SON_S[0]
    walking = st < 1.8
    c = scroll(st, [(0.0, 45.0), (1.8, 0.0)])
    lamps(d, c + 200)
    dx, kx = 440, 548
    if st < 2.1:
        ph = c / 22.0
        dpose = aged(BEND, a) if walking else aged(dict(BEND, head=(30, -132)), a)
        dpts = place(dict(dpose, **{k: v for k, v in walk(c / 40.0, 0.5).items() if k[0] in "kf"}) if walking else dpose,
                     grounded(BEND, dx, DAD_S), 1, DAD_S)
        if walking:
            kp = walk(ph, 0.6)
            kpts = place(kp, grounded(kp, kx, ks), 1, ks)
        else:
            fall = smooth(prog(st, 1.8, 2.0))
            kp = lerp_pose(walk(ph, 0.6), SIT_FLOOR, fall)
            kpts = place(kp, (kx, lerp(grounded(STAND, kx, ks)[1], FLOOR - 10 * ks, fall)), 1, ks)
        if st < 1.85:
            hand = dpts["hr"]
            kpts = reach(kpts, ks, "hl", hand, -1)
            figure(stage, kpts, ks, light=(-0.4, -0.9), scarf=True)
            figure(stage, dpts, DAD_S, light=(-0.4, -0.9), body=dad_col(a))
            hands_hold(d, hand, DAD_S, ks)
        else:
            figure(stage, kpts, ks, light=(-0.4, -0.9), scarf=True)
            figure(stage, dpts, DAD_S, light=(-0.4, -0.9), body=dad_col(a))
    else:
        up = smooth(prog(st, 2.1, 2.5))
        dp = lerp_pose(aged(BEND, a), LIFT, up)
        dpts = place(dp, grounded(STAND, dx + 40, DAD_S), 1, DAD_S)
        hx = (dpts["hl"][0] + dpts["hr"][0]) / 2
        hy = (dpts["hl"][1] + dpts["hr"][1]) / 2
        kp = dict(C.CHEER, kl=(20, 40), fl=(10, 90), kr=(-10, 44), fr=(-20, 96))
        kpts = place(kp, (lerp(kx, hx, up), lerp(FLOOR - 10 * ks, hy + 10, up)), 1, ks)
        figure(stage, dpts, DAD_S, light=(-0.4, -0.9), body=dad_col(a))
        figure(stage, kpts, ks, light=(-0.4, -0.9), scarf=True)
    pull = smooth(prog(st, 0.0, 1.4))
    hp = (dx + 58 * DAD_S + 22 * a, grounded(BEND, dx, DAD_S)[1] - 26 * DAD_S)
    fx = lerp(hp[0], 500, pull)
    fy = lerp(hp[1], 1120, pull)
    z = lerp(2.7, 1.15, pull)
    return [], ((460, 1.0),), (fx, fy, z), ("hook", None)


def s1(stage, d, st, T):
    a = DAD_AGE[1]
    ks = SON_S[1]
    c = scroll(st, [(0.0, 260.0), (1.4, 200.0), (1.8, 110.0), (2.2, 0.0)])
    lamps(d, c)
    kid_world = 260.0 * st
    kx = 520 + kid_world - c
    b = mini_bike(d, kx, C.ORANGE, kid_world / 30.0, -kid_world / 52.0, ks * 1.15)
    kpts = C.rider_pts(b, ks)
    figure(stage, kpts, ks, light=(-0.4, -0.9), scarf=True, back=-1)
    dad_world = scroll(st, [(0.0, 260.0), (1.4, 160.0), (1.7, 70.0), (1.95, 0.0)])
    dxs = 360 + dad_world - c
    if st < 1.95:
        rp = C.run_pose(dad_world / 34.0, 0.55 if st < 1.4 else 0.35, lean=0.3)
        dpts = place(aged(rp, a), grounded(rp, dxs, DAD_S), 1, DAD_S)
        if st < 1.4:
            dpts = reach(dpts, DAD_S, "hr", (b["seat"][0] - 20, b["seat"][1] + 6), 1)
    else:
        k = smooth(prog(st, 2.0, 2.35)) * (1 - smooth(prog(st, 2.8, 3.2)))
        dp = lerp_pose(STAND, C.CHEER, k)
        chest = smooth(prog(st, 2.9, 3.3))
        dp = lerp_pose(dp, dict(STAND, er=(26, -96), hr=(4, -96), head=(4, -150)), chest)     # hand on his heart
        dpts = place(aged(dp, a), grounded(dp, dxs, DAD_S), 1, DAD_S)
    figure(stage, dpts, DAD_S, light=(-0.4, -0.9), body=dad_col(a))
    fx = lerp(520, 600, smooth(prog(st, 1.6, 3.4)))
    return [], ((480, 1.0),), (fx, 1100, lerp(1.15, 1.25, smooth(prog(st, 2.6, 3.6)))), None


def s2(stage, d, st, T):
    """the hand left in the air - slow, long, the camera closes in on it"""
    a = DAD_AGE[2]
    ks = SON_S[2]
    c = scroll(st, [(0.0, 140.0), (1.6, 70.0), (2.0, 0.0)])
    lamps(d, c + 900)
    teen_world = 140.0 * st if st < 1.7 else 140.0 * 1.7 + 330.0 * (st - 1.7)
    tx = 600 + teen_world - c
    if tx < 1300:
        tp = walk(teen_world / 26.0, 1.0, 0.15)
        tp = dict(tp, er=(26, -70), hr=(40, -96), head=(10, -146))
        tpts = place(tp, grounded(tp, tx, ks), 1, ks)
        figure(stage, tpts, ks, light=(-0.4, -0.9), scarf=True)
        headphones(d, tpts["head"], ks)
        phone(d, tpts["hr"], ks)
    dad_world = scroll(st, [(0.0, 140.0), (1.6, 70.0), (1.95, 0.0)])
    dxs = 400 + dad_world - c
    dp = walk(dad_world / 28.0, 0.8, 0.2) if st < 1.95 else dict(STAND)
    k = smooth(prog(st, 1.2, 2.0)) * (1 - smooth(prog(st, 3.5, 4.1)))
    dp = lerp_pose(dp, dict(dp, er=REACH_OUT["er"], hr=REACH_OUT["hr"]), k)
    if st >= 3.6:
        dp = lerp_pose(dp, dict(C.SAD, head=(18, -134)), smooth(prog(st, 3.6, 4.1)))
    dpts = place(aged(dp, a), grounded(STAND, dxs, DAD_S), 1, DAD_S)
    figure(stage, dpts, DAD_S, light=(-0.4, -0.9), body=dad_col(a))
    push = smooth(prog(st, 2.0, 3.6))
    hx, hy = dpts["hr"]
    fx = lerp(520, hx - 40, push)
    fy = lerp(1110, hy + 30, push)
    z = lerp(1.15, 1.9, push) - 0.5 * smooth(prog(st, 3.6, 4.2))
    return [], ((440, 1.0),), (fx, fy, z), ("slowmo", (2.0, 3.6))


def rain(d, T, a, x0=-40, x1=W + 40):
    rng = np.random.default_rng(7)
    for j in range(140):
        x = rng.uniform(x0, x1)
        sp = rng.uniform(0.9, 1.3)
        ph = rng.uniform(0, 1)
        y = ((T * sp * 1.4 + ph) % 1.0) * (FLOOR + 60) - 40
        line(d, [(x, y), (x - 8, y + 34)], (150, 170, 210, int(150 * a)), 2)
        if y > FLOOR - 30:
            ell(d, x, FLOOR + 4, 10, 2, None, outline=(160, 180, 220, int(120 * a)), w=1.5)


def snow(d, T, a):
    rng = np.random.default_rng(11)
    for j in range(90):
        x0 = rng.uniform(-40, W + 40)
        sp = rng.uniform(0.08, 0.16)
        ph = rng.uniform(0, 1)
        y = ((T * sp + ph) % 1.0) * (FLOOR + 40) - 20
        x = x0 + 18 * math.sin(T * 0.8 + ph * 6)
        r = rng.uniform(2, 4.5)
        ell(d, x, y, r, r, (235, 238, 248, int(220 * a)))


def s3(stage, d, st, T):
    a = DAD_AGE[3]
    ks = SON_S[3]
    lamps(d, 1900)
    car_x = 1010 if st < 2.5 else 1010 + 900 * (st - 2.5) ** 2 * 1.6
    C.sports_car(d, stage, car_x, T, 1.0 if st >= 2.5 else 0.0, flip=True)
    if st < 2.3:
        if st < 1.25:
            u = st / 1.25
            sx = lerp(330, 700, u)
            sp = walk(st * 7.5, 1.0, 0.15)
            sp = dict(sp, er=(20, -60), hr=(30, -20))
            spts = place(sp, grounded(sp, sx, ks), 1, ks)
            figure(stage, spts, ks, light=(-0.4, -0.9), scarf=True)
            suitcase(d, spts["hr"], ks)
        else:
            k = smooth(prog(st, 1.5, 1.9))
            sp = lerp_pose(STAND, dict(STAND, el=(-32, -130), hl=(-44, -180)), k * (1 - smooth(prog(st, 1.9, 2.2))))
            spts = place(sp, grounded(STAND, 700, ks), -1, ks)
            figure(stage, spts, ks, light=(-0.4, -0.9), scarf=True, alpha=1 - smooth(prog(st, 2.1, 2.3)))
    dp = STAND
    if st >= 1.6:
        k = smooth(prog(st, 1.6, 1.9)) * (1 - smooth(prog(st, 2.9, 3.4)))
        dp = lerp_pose(STAND, WAVE, k)
        if 1.9 <= st < 2.9:
            dp = dict(dp, hr=(44 + 10 * math.sin(st * 12), -184))
    if st >= 3.0:
        dp = lerp_pose(dp, dict(C.SAD, head=(20, -132)), smooth(prog(st, 3.0, 3.6)))
    dpts = place(aged(dp, a), grounded(STAND, 250, DAD_S), 1, DAD_S)
    figure(stage, dpts, DAD_S, light=(0.4, -0.9), body=dad_col(a))
    if st >= 2.4:
        rain(d, T, smooth(prog(st, 2.4, 3.0)))
    narrow = smooth(prog(st, 2.6, 3.6))
    spots = ((250, 1.0), (700, round(1.0 - narrow, 1))) if narrow < 0.95 else ((250, 1.0),)
    fx = lerp(480, 290, narrow)
    return [], spots, (fx, 1110, lerp(1.12, 1.35, narrow)), None


def s4(stage, d, st, T):
    a = DAD_AGE[4]
    ks = SON_S[4]
    lamps(d, 3100)
    bench(d, 520)
    # his old little bike, leaning by the bench - rusty now
    b = mini_bike(d, 760, (150, 96, 50), 0.6, 0.0, SON_S[1] * 1.15)
    touch = smooth(prog(st, 0.2, 0.8)) * (1 - smooth(prog(st, 1.4, 1.8)))
    rise = smooth(prog(st, 1.8, 2.3)) * (1 - smooth(prog(st, 2.8, 3.4)))
    bp = SIT_B
    if touch > 0:
        bp = lerp_pose(SIT_B, dict(SIT_B, el=(60, -70), hl=(100, -80), head=(22, -144)), touch)
    bp = lerp_pose(bp, dict(STAND, head=(28, -134), neck=(20, -98), er=(30, -50), hr=(40, -6), el=(40, -96),
                            hl=(84, -110)), rise * 0.55)
    if st >= 3.0:
        bp = lerp_pose(bp, dict(SIT_B, head=(26, -128), neck=(16, -96)), smooth(prog(st, 3.0, 3.6)))
    hip = (500, lerp(FLOOR - 66 * DAD_S * 0.98, grounded(STAND, 500, DAD_S)[1], rise * 0.55))
    dpts = place(aged(bp, a), hip, 1, DAD_S)
    figure(stage, dpts, DAD_S, light=(0.3, -0.95), body=dad_col(a))
    cane(d, dpts["hr"], DAD_S)
    if 1.0 <= st < 3.2:
        u = prog(st, 1.0, 3.2)
        sx = lerp(-120, 1260, u)
        sp = walk(st * 11, 1.0, 0.1)
        sp = dict(sp, er=PHONE_EAR["er"], hr=PHONE_EAR["hr"], el=(-10, -60), hl=(-6, -14))
        spts = place(sp, grounded(sp, sx, ks), 1, ks)
        figure(stage, spts, ks, light=(-0.4, -0.9), scarf=True)
        phone(d, spts["hr"], ks, lit=False)
        briefcase(d, spts["hl"], ks)
    snow(d, T, 1.0)
    fx = lerp(600, 520, smooth(prog(st, 2.6, 4.0)))
    return [], ((520, 0.9),), (fx, 1120, lerp(1.12, 1.32, smooth(prog(st, 2.8, 4.0)))), None


def s5(stage, d, st, T):
    """he stops, turns, drops the briefcase, runs back, kneels; the old hand on his head; they walk at dad's pace"""
    a = DAD_AGE[5]
    ks = SON_S[5]
    walk_t = 3.6
    c = scroll(st, [(0.0, 0.0), (walk_t, 50.0)])
    lamps(d, 3100 + c)
    bench(d, 520 - c)
    mini_bike(d, 760 - c, (150, 96, 50), 0.6, 0.0, SON_S[1] * 1.15)
    warm = smooth(prog(st, 2.3, 3.4))
    if st < walk_t:
        # the father, sitting
        stand = smooth(prog(st, 3.0, 3.6))
        dp = SIT_B
        if 2.3 <= st:
            dp = lerp_pose(SIT_B, dict(SIT_B, el=(40, -110), hl=(70, -100)), smooth(prog(st, 2.3, 2.7)))
        dp = lerp_pose(dp, dict(STAND, er=(30, -50), hr=(40, -6)), stand)
        hip = (500 + 20 * stand, lerp(FLOOR - 66 * DAD_S * 0.98, grounded(STAND, 520, DAD_S)[1], stand))
        dpts = place(aged(dp, a), hip, 1, DAD_S)
        # the son
        bag = None
        if st < 0.9:
            k = smooth(prog(st, 0.4, 0.9))
            sp = lerp_pose(dict(STAND, el=(-10, -60), hl=(-6, -14)), dict(STAND, head=(-8, -152)), k)
            spts = place(sp, grounded(STAND, 980, ks), 1 if st < 0.6 else -1, ks)
            bag = spts["hl"]
        elif st < 1.2:
            sp = dict(STAND, head=(-6, -152), el=(-10, -60), hl=(-6, -14))
            spts = place(sp, grounded(STAND, 980, ks), -1, ks)
        elif st < 2.0:
            u = smooth(prog(st, 1.2, 2.0))
            rp = C.run_pose((st - 1.2) * 14, 0.8)
            spts = place(rp, grounded(rp, lerp(980, 640, u), ks), -1, ks)
        elif st < 3.0:
            k = smooth(prog(st, 2.0, 2.4))
            kneel = {"head": (-20, -128), "neck": (-14, -88), "el": (-30, -50), "hl": (-36, -10), "er": (8, -50),
                     "hr": (10, -8), "kl": (-40, 10), "fl": (-46, 66), "kr": (30, 52), "fr": (70, 60)}
            sp = lerp_pose(STAND, kneel, k)
            spts = place(sp, (620, lerp(grounded(STAND, 620, ks)[1], FLOOR - 64 * ks, k)), -1, ks)
        else:
            k = smooth(prog(st, 3.0, 3.6))
            sp = lerp_pose(STAND, OFFER, 0.6)
            spts = place(sp, (lerp(620, 640, k), lerp(FLOOR - 64 * ks, grounded(STAND, 640, ks)[1], k)), -1, ks)
            meet = (lerp(spts["hr"][0], dpts["neck"][0] + 60, 0.5), lerp(spts["hr"][1], dpts["neck"][1] + 70, 0.5))
            spts = reach(spts, ks, "hr", meet, -1)
            dpts = reach(dpts, DAD_S, "hl", meet, 1)
        if 2.4 <= st < 3.0:
            dpts = reach(dpts, DAD_S, "hl", (spts["head"][0] + 6, spts["head"][1] - 22), 1)   # hand on his head
        figure(stage, dpts, DAD_S, light=(0.3, -0.95), body=dad_col(a))
        cane(d, dpts["hr"], DAD_S)
        figure(stage, spts, ks, light=(-0.4, -0.9), scarf=True)
        # the briefcase: in his hand, dropped at 1.1
        if bag is not None:
            briefcase(d, bag, ks)
        else:
            u = st - 1.0
            y = min(FLOOR - 40 * ks, 1080 + 900 * u * u)
            briefcase(d, (1000, y), ks)
        if st >= 3.0:
            hands_hold(d, spts["hr"], ks, DAD_S, old_holds=True)
    else:
        briefcase(d, (1000 - c, FLOOR - 40 * ks), ks)
        w = st - walk_t
        dp = walk(w * 4.0, 0.45, 0.0)
        dp = dict(dp, er=(30, -50), hr=(40, -6))
        dpts = place(aged(dp, a), grounded(dp, 520, DAD_S), 1, DAD_S)
        sp = walk(w * 4.0 + 1.6, 0.45, 0.0)
        spts = place(sp, grounded(sp, 640, ks), 1, ks)
        meet = ((dpts["neck"][0] + spts["neck"][0]) / 2, dpts["hip"][1] - 10)
        spts = reach(spts, ks, "hl", meet, 1)
        dpts = reach(dpts, DAD_S, "hl", meet, -1)
        figure(stage, dpts, DAD_S, light=(0.3, -0.95), body=dad_col(a))
        cane(d, dpts["hr"], DAD_S)
        figure(stage, spts, ks, light=(-0.4, -0.9), scarf=True)
        hands_hold(d, meet, ks, DAD_S, old_holds=True)
    snow(d, T, 1 - warm)
    if st < 1.2:
        fx, fy, z = lerp(760, 820, st / 1.2), 1110, 1.2
    elif st < 2.4:
        fx, fy, z = lerp(820, 580, smooth(prog(st, 1.2, 2.2))), 1120, lerp(1.2, 1.35, smooth(prog(st, 1.6, 2.4)))
    elif st < 4.8:
        fx, fy, z = 580, 1110, lerp(1.35, 1.15, smooth(prog(st, 2.4, 3.6)))
    else:
        k = smooth(prog(st, 4.8, 5.6))
        fx, fy, z = lerp(580, 580, k), lerp(1110, 1160, k), lerp(1.15, 2.7, k)
    lines = [(3.7, "HE WAITED FOR YOUR FIRST STEPS."), (4.4, "WAIT FOR HIS LAST ONES.")]
    return lines, ((560, 0.6 + 0.4 * round(warm, 1)),), (fx, fy, z), ("warm", warm)


SCENES = [s0, s1, s2, s3, s4, s5]
GRADE = [0.9, 0.8, 0.0, -0.55, -1.0, -1.0]     # warm (+) to cold (-)


def grade(im, g):
    if abs(g) < 0.02:
        return im
    warm = np.array([1.12, 1.01, 0.82], np.float32)
    cold = np.array([0.84, 0.95, 1.16], np.float32)
    gain = 1 + (warm - 1) * g if g > 0 else 1 + (cold - 1) * (-g)
    a = np.asarray(im.convert("RGB"), np.float32)
    if g < 0:
        m = a.mean(axis=2, keepdims=True)
        a = a * (1 + 0.25 * g) + m * (-0.25 * g)
    a = np.clip(a * gain, 0, 255).astype(np.uint8)
    return Image.fromarray(a, "RGB").convert("RGBA")


# ---------------------------------------------------------------- frame
def age_now(sc, st):
    """the counter rolls through the years at the start of every scene"""
    if sc == 0:
        return 1
    a0, a1 = AGES[sc - 1], AGES[sc]
    return int(round(lerp(a0, a1, smooth(prog(st, 0.0, 0.55)))))


def age_counter(img, sc, st, t):
    if sc == 0 and st < 1.6:
        return
    d = ImageDraw.Draw(img)
    age = age_now(sc, st)
    k = hq.pop(st, 0.5, 0.3) if sc > 0 else hq.pop(st, 1.6, 0.3)
    fa = font(C.SERIF, 30)
    PW.spaced(d, W / 2, 150, "AGE", fa, (170, 174, 186, 255), 10)
    fb = font(SERIF_B, max(8, int(96 * (0.85 + 0.15 * k))))
    PW.spaced(d, W / 2, 186, str(age), fb, (244, 240, 230, 255), 4)


def frame(t):
    sc, st = scene_of(t)
    stage = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(stage)
    lines, spots, camf, extra = SCENES[sc](stage, d, st, t)
    base = C.stage_bg(tuple((float(round(x / 20) * 20), round(float(s_), 1)) for x, s_ in spots)).copy()
    C.dust(ImageDraw.Draw(base), t, spots, seed=sc + 1)
    top = stage.crop((0, 0, W * K, FLOOR * K))
    refl = top.transpose(Image.FLIP_TOP_BOTTOM).crop((0, 0, W * K, (H - FLOOR) * K))
    refl = refl.resize((W * K // 4, (H - FLOOR) * K // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
    refl = refl.resize((W * K, (H - FLOOR) * K), Image.BILINEAR)
    fade = np.linspace(0.32, 0.0, (H - FLOOR) * K, dtype=np.float32)[:, None]
    refl.putalpha(Image.fromarray((np.asarray(refl.split()[3], np.float32) * fade).astype(np.uint8)))
    base.alpha_composite(refl, (0, FLOOR * K))
    g = stage.resize((W * K // 8, H * K // 8), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6))
    gl = Image.new("RGBA", g.size, (200, 210, 235, 0))
    gl.putalpha(g.split()[3].point(lambda v: int(v * 0.35)))
    base.alpha_composite(gl.resize(stage.size, Image.BILINEAR))
    base.alpha_composite(stage)
    fx, fy, z = camf
    z *= 1.06
    dx = z * (W / 2 - fx)
    dy = z * (H / 2 - fy)
    im = hq.camera(base, z, dx * K, dy * K).resize((W, H), Image.LANCZOS)
    gr = GRADE[sc]
    if extra and extra[0] == "warm":
        gr = lerp(-1.0, 1.0, extra[1])
    im = grade(im, gr)
    if sc > 0 and st < 0.3:
        k = 1 - st / 0.3
        im = Image.blend(im, Image.new("RGBA", im.size, (0, 0, 0, 255)), 0.75 * k)
    if sc < 5 and st > SC[sc + 1] - SC[sc] - 0.25:
        k = (st - (SC[sc + 1] - SC[sc] - 0.25)) / 0.25
        im = Image.blend(im, Image.new("RGBA", im.size, (0, 0, 0, 255)), 0.75 * k)
    age_counter(im, sc, st, t)
    C.caption(im, lines, st)
    if sc == 0 and st < 1.6:
        k = 1 - smooth(prog(st, 1.35, 1.6))
        dq = ImageDraw.Draw(im)
        fb = font(SERIF_B, 84)
        for i, ln in enumerate(("HE TAUGHT YOU", "TO WALK.")):
            y = 300 + i * 104
            PW.spaced(dq, W / 2 + 3, y + 4, ln, fb, (0, 0, 0, int(160 * k)), 6)
            PW.spaced(dq, W / 2, y, ln, fb, (244, 240, 230, int(255 * k)), 6)
    return np.asarray(im.convert("RGB"))


def render(i):
    return frame(i / FPS).tobytes()


# ---------------------------------------------------------------- music: a dramatic cinematic cue (FluidSynth GM)
def score():
    """piano alone -> strings; heartbeat tension at 16; total silence and one high violin on the hand in the air;
    a timpani/low-brass blow as he walks away; a cello lament in the rain; sparse piano in the snow; a timpani roll
    when the briefcase drops; the full orchestra + choir as he comes back; the last chord rings into the loop"""
    import mido
    ev = []        # (time, kind, ch, a, b)  kind: 1 on, 0 off, 2 cc

    def note(t, du, ch, n, v):
        if t >= DUR or du <= 0:
            return
        ev.append((t, 1, ch, int(n), int(min(127, max(1, v)))))
        ev.append((min(DUR, t + du), 0, ch, int(n), 0))

    def swell(ch, t0, t1, v0, v1, steps=24):
        for j in range(steps + 1):
            u = j / steps
            ev.append((t0 + (t1 - t0) * u, 2, ch, 11, int(lerp(v0, v1, u))))
    prg = {0: 0, 1: 48, 2: 42, 3: 52, 4: 60, 5: 47, 6: 43, 7: 40, 8: 61, 10: 49, 11: 46}
    Am, F, Cc, G, Dm, E = (45, 57, 60, 64), (41, 57, 60, 65), (48, 55, 60, 64), (43, 55, 59, 62), (50, 57, 62, 65), \
        (40, 56, 59, 64)
    prog_ = [Am, F, Cc, G]
    bar = 2.0
    hand0, hand1 = SC[2] + 1.6, SC[2] + 3.7
    # piano throughout (except the silence): arpeggios, sparser in the cold
    t = 0.0
    i = 0
    while t < DUR - 0.05:
        ch = prog_[i % 4] if t < SC[5] + 1.2 else [Am, F, Cc, E][i % 4]
        sc, st = scene_of(t + 1e-4)
        dens = {0: 6, 1: 8, 2: 8, 3: 6, 4: 3, 5: 8}[sc]
        for j in range(dens):
            tt = t + j * bar / dens
            if hand0 <= tt < hand1:
                continue
            nn = [ch[1], ch[2], ch[3], ch[2] + 12, ch[3], ch[2]][j % 6] + (12 if sc in (0, 4) else 0)
            note(tt, bar / dens * 2.2, 0, nn, 52 + 8 * sc)
        if not (hand0 <= t < hand1):
            note(t, bar * 1.2, 0, ch[0], 66)
        t += bar
        i += 1
    # the theme (piano first, then strings) - a falling line that resolves
    theme = [(0.0, 1.0, 76), (1.0, 0.5, 74), (1.5, 0.5, 72), (2.0, 1.5, 71), (3.5, 0.5, 69), (4.0, 2.0, 72),
             (6.0, 1.0, 71), (7.0, 1.0, 69)]
    for t0, ch_ in ((0.2, 0), (SC[1] + 0.2, 0), (SC[3] + 0.3, 2), (SC[5] + 2.2, 10)):
        for b0, du, nn in theme:
            tt = t0 + b0 * 0.5
            if not (hand0 <= tt < hand1):
                note(tt, du * 0.5 * 1.05, ch_, nn - (12 if ch_ == 2 else 0), 96)
    # strings pad from AGE 6, swelling
    for k_, (t0, t1) in enumerate(((SC[1], SC[2] + 1.6), (SC[3], SC[5]))):
        t = t0
        i = 0
        while t < t1:
            ch = prog_[i % 4]
            for nn in ch[1:]:
                note(t, bar, 1, nn, 70)
            t += bar
            i += 1
    swell(1, SC[1], SC[2], 50, 90)
    swell(1, SC[3], SC[4], 60, 110)
    swell(1, SC[4], SC[5], 70, 50)
    # AGE 16: low string ostinato + heartbeat build, then the silence with one high violin, then the blow
    t = SC[2]
    while t < hand0:
        note(t, 0.2, 6, 33, 90)
        note(t + 0.25, 0.2, 6, 33, 70)
        t += 0.5
    note(hand0, hand1 - hand0, 7, 88, 70)
    swell(7, hand0, hand1, 30, 90)
    note(hand1, 1.6, 5, 33, 127)
    note(hand1, 1.6, 8, 33, 110)
    note(hand1, 1.6, 8, 45, 110)
    # AGE 25: cello lament in the rain
    swell(2, SC[3], SC[4], 70, 115)
    # AGE 40: sparse; high tremolo strings + a clock
    t = SC[4]
    while t < SC[5]:
        note(t, 2.0, 1, 88, 40)
        t += 2.0
    # AGE 45: timpani roll when the briefcase drops, then everything
    roll0 = SC[5] + 1.05
    for j in range(24):
        note(roll0 + j * 0.05, 0.05, 5, 45, int(50 + 3 * j))
    climax = SC[5] + 2.2
    for nn in (33, 45):
        note(climax, 0.9, 5, nn, 127)
    t = climax
    i = 0
    while t < DUR - 0.05:
        ch = [Am, F, Cc, G][i % 4]
        for nn in ch:
            note(t, bar, 1, nn + 12, 110)
            note(t, bar, 3, nn + 12, 100)
            note(t, bar, 8, nn - 12, 90)
            note(t, bar, 6, nn - 24, 100)
        note(t, bar, 4, ch[3] + 12, 105)
        t += bar
        i += 1
    swell(1, climax, DUR, 90, 127)
    swell(3, climax, DUR, 60, 120)
    for j, nn in enumerate((57, 60, 64, 67, 69, 72, 76, 79, 81, 84, 88)):
        note(SC[5] + 2.1 + j * 0.035, 1.5, 11, nn, 80)
    ev.sort(key=lambda e: (e[0], {2: 0, 0: 1, 1: 2}[e[1]]))
    mid = mido.MidiFile(ticks_per_beat=960)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))
    vol = {0: 106, 1: 100, 2: 108, 3: 88, 4: 96, 5: 118, 6: 104, 7: 96, 8: 100, 10: 104, 11: 80}
    for c_, p_ in prg.items():
        tr.append(mido.Message("program_change", channel=c_, program=p_, time=0))
    for c_, v in vol.items():
        tr.append(mido.Message("control_change", channel=c_, control=7, value=v, time=0))
        tr.append(mido.Message("control_change", channel=c_, control=91, value=110, time=0))
        tr.append(mido.Message("control_change", channel=c_, control=11, value=100, time=0))
    now = 0
    for s_, kind, c_, a_, b_ in ev:
        tk = int(round(max(0.0, s_) * 1920))
        dt = max(0, tk - now)
        if kind == 2:
            tr.append(mido.Message("control_change", channel=c_, control=a_, value=b_, time=dt))
        else:
            tr.append(mido.Message("note_on" if kind == 1 else "note_off", channel=c_, note=a_, velocity=b_, time=dt))
        now = max(now, tk)
    tmp = tempfile.mkdtemp()
    mp, wp = os.path.join(tmp, "s.mid"), os.path.join(tmp, "s.wav")
    mid.save(mp)
    subprocess.run(["fluidsynth", "-ni", "-g", "0.7", "-r", str(SR), "-F", wp, C.SF2, mp], check=True, capture_output=True)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", wp, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True).stdout
    m = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    n = int(DUR * SR)
    out = np.zeros((n, 2))
    out[:min(n, len(m))] = m[:n]
    # hard silence on the hand (only the violin), then the blow
    i0, i1 = int((hand0 + 0.05) * SR), int(hand1 * SR)
    out /= np.abs(out).max() + 1e-9
    return out * 0.65


def step(fx, at, g, pan=0.0, low=140):
    mix_in(fx, tone(low, 0.07, (1, 0.5), a=0.002, d=0.025) + 0.3 * noise(0.07, int(at * 1000) % 9999, lo=300, hi=2500)[
        :int(0.07 * SR)] * env(int(0.07 * SR), 0.001, 0.015), at, g, pan)


def audio():
    n = int(DUR * SR)
    fx = np.zeros((n, 2))
    mus = score()
    for j in range(6):
        step(fx, SC[0] + 0.2 + j * 0.3, 0.02, 0.1, 220)
    mix_in(fx, tone(90, 0.25, (1, 0.5), a=0.002, d=0.08), SC[0] + 1.95, 0.06)
    for j in range(8):
        step(fx, SC[1] + j * 0.18, 0.03, -0.2)
    for j in range(20):
        mix_in(fx, noise(0.02, 40 + j, lo=2000, hi=7000)[:int(0.02 * SR)] * env(int(0.02 * SR), 0.0005, 0.006),
               SC[1] + j * 0.16, 0.03, 0.3)
    for j in range(6):
        step(fx, SC[2] + j * 0.3, 0.03, -0.2)
    # heartbeat under AGE 16
    for j in range(6):
        for k2, dt in enumerate((0.0, 0.18)):
            mix_in(fx, tone(50, 0.2, (1, 0.5), a=0.003, d=0.08), SC[2] + 0.4 + j * 0.5 + dt, 0.12 - 0.05 * k2)
    # AGE 25: wheels, door, car, rain
    mix_in(fx, noise(1.2, 3, lo=200, hi=1500)[:int(1.2 * SR)] * 0.6, SC[3], 0.04, 0.2)
    mix_in(fx, tone(100, 0.2, (1, 0.5), a=0.001, d=0.06), SC[3] + 2.25, 0.12, 0.3)
    eng = noise(1.2, 4, lo=60, hi=500)[:int(1.2 * SR)] * np.linspace(1, 0, int(1.2 * SR))
    mix_in(fx, eng, SC[3] + 2.4, 0.12, 0.5)
    rn = noise(SC[4] - SC[3] - 2.4, 5, lo=900, hi=9000)
    rn = rn[:int((SC[4] - SC[3] - 2.4) * SR)] * np.minimum(1, np.linspace(0, 4, int((SC[4] - SC[3] - 2.4) * SR)))
    mix_in(fx, rn, SC[3] + 2.4, 0.06)
    # AGE 40: a clock ticking, steps rushing past
    t0 = SC[4]
    while t0 < SC[5]:
        mix_in(fx, tone(2400, 0.02, (1,), a=0.0005, d=0.008), t0, 0.03)
        t0 += 0.5
    for j in range(10):
        step(fx, SC[4] + 1.0 + j * 0.22, 0.03, lerp(-0.6, 0.6, j / 9))
    # AGE 45: the briefcase hits the ground, running steps, cane taps
    mix_in(fx, tone(80, 0.3, (1, 0.5), a=0.001, d=0.1) + 0.4 * noise(0.3, 6, lo=200, hi=3000)[:int(0.3 * SR)] *
           env(int(0.3 * SR), 0.001, 0.05), SC[5] + 1.12, 0.2, 0.4)
    for j in range(5):
        step(fx, SC[5] + 1.25 + j * 0.15, 0.04, 0.2)
    for j in range(5):
        mix_in(fx, tone(700, 0.05, (1, 2.4), a=0.001, d=0.02), SC[5] + 3.7 + j * 0.42, 0.035, -0.1)
    x = mus + fx
    m = int(0.25 * SR)
    k = np.linspace(0, 1, m)[:, None]
    x[-m:] = x[-m:] * (1 - k) + x[:m] * k
    x /= max(1.0, np.abs(x).max() / 0.9)
    return x


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "steps.mp4"
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
    with Pool(os.cpu_count()) as pool:
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
