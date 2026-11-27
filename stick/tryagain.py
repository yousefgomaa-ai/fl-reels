#!/usr/bin/env python3
"""TRY AGAIN - ten situations, the first attempt always fails. ~25 s.

baby walking (hook) - bike - jump rope - hoop - backflip - skate - pull-up - penalty kick - weightlifting - high jump.
Each: TRY 1..N while it fails (failed attempts stay as ghosts), then it works (counter turns gold).
YOU NEVER QUIT AS A KID. / WHY QUIT NOW?

    python3 stick/tryagain.py --stills [t ...]
    python3 stick/tryagain.py stick/tryagain.mp4
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
import race as R  # noqa
from compare import ell, line, rrect, poly, figure, place, ik, FLOOR, K, W, H  # noqa
from perfect_wave import clamp, env, font, lerp, lerp_pose, mix_in, noise, prog, smooth, tone, write_wav  # noqa
from money_chars import hero, face, outfit, S, GOLD, RED  # noqa
from money import put, track, compose  # noqa
import compare as C  # noqa
from failfast import bg, finish, spot, label, glow_text, glow_ell, whip, ease_back, alive, skater, draw_board, set_arm  # noqa

FPS, SR = 30, 44100
L = 2.3                      # seconds per situation
T_S = 1.45                   # success moment inside a situation
P = 0.42                     # one failed attempt
SC = [("baby", 12), ("bike", 7), ("rope", 15), ("hoop", 30), ("flip", 40), ("skate", 60), ("pullup", 30),
      ("penalty", 70), ("lift", 90), ("jump", 100)]
T_END = L * len(SC)
DUR = T_END + 2.0
NF = int(round(DUR * FPS))
STAND = PW.STAND
LYING = {"head": (-150, -10), "neck": (-108, -6), "el": (-80, 30), "hl": (-46, 40), "er": (-80, -44), "hr": (-40, -70),
         "kl": (56, -24), "fl": (113, -2), "kr": (56, -6), "fr": (113, 6)}
SITF = {"head": (6, -120), "neck": (4, -80), "el": (30, -40), "hl": (50, -10), "er": (-20, -40), "hr": (-40, -10),
        "kl": (40, -20), "fl": (90, 0), "kr": (36, -16), "fr": (86, 4)}       # sitting on the floor
KNEEL = {"head": (30, -120), "neck": (20, -84), "el": (30, -40), "hl": (40, 4), "er": (24, -36), "hr": (34, 8),
         "kl": (40, 6), "fl": (-10, 60), "kr": (-20, 54), "fr": (-70, 60)}


def tries(u, n):
    if u >= T_S:
        return n
    return max(1, min(n - 1, int(1 + (n - 1) * (u / T_S) ** 1.6)))


def phase(u):
    return (u % P) / P


def rotp(p, c, a):
    ca, sa = math.cos(a), math.sin(a)
    return {k: (c[0] + (x - c[0]) * ca - (y - c[1]) * sa, c[1] + (x - c[0]) * sa + (y - c[1]) * ca) for k, (x, y) in p.items()}


def ghosts(st, poses, alpha=0.14, body=(220, 230, 255)):
    if not poses:
        return
    gl = Image.new("RGBA", st.size, (0, 0, 0, 0))
    for p, s_ in poses:
        figure(gl, p, s_, light=(0.4, -0.9), body=body)
    a = np.asarray(gl.split()[3], np.float32) * alpha
    gl.putalpha(Image.fromarray(a.astype(np.uint8)))
    st.alpha_composite(gl)


def floor_line(d):
    line(d, [(-20, FLOOR), (W + 20, FLOOR)], (70, 72, 84, 255), 4)


# ---------------------------------------------------------------- 1 baby
def baby_fig(st, d, pose, hip, expr, t, f=1):
    s_ = 0.58
    p = place(pose, hip, f, s_)
    figure(st, p, s_, light=(0.4, -0.9))
    hx, hy = p["head"]
    ell(d, hx, hy - 6, 30, 30, (238, 238, 242, 255))
    d.ellipse(((hx - 30) * K, (hy - 36) * K, (hx + 30) * K, (hy + 24) * K), outline=(28, 28, 34, 255), width=int(2.5 * K))
    line(d, [(hx - 4, hy - 36), (hx + 2, hy - 46), (hx + 8, hy - 38)], (28, 28, 34, 255), 3)   # a curl of hair
    q = dict(p, head=(hx, hy - 6))
    face(d, q, expr, f, t)
    return p


def baby(st, d, u):
    floor_line(d)
    done = u >= T_S
    hug = smooth(prog(u, T_S + 0.55, T_S + 0.75)) if done else 0.0
    mp = place(dict(KNEEL, el=(lerp(-50, -10, hug), -100), hl=(lerp(-100, -30, hug), -110), er=(lerp(-40, 0, hug), -96),
                    hr=(lerp(-90, -20, hug), -104)), (740, FLOOR - 62 * S), -1, S)
    figure(st, mp, S, light=(0.4, -0.9))
    dd = ImageDraw.Draw(st)
    hx, hy = mp["head"]
    ell(dd, hx + 6, hy - 24, 18, 14, (60, 40, 30, 255))
    outfit(dd, mp, (190, 110, 130), -1, legs=False)
    face(dd, mp, "happy", -1, u)
    if not done:
        ph = phase(u)
        up = smooth(clamp(ph / 0.35))
        fall = smooth(clamp((ph - 0.55) / 0.2))
        wob = math.sin(ph * 30) * 10 * up * (1 - fall)
        pose = lerp_pose(SITF, dict(STAND, el=(-40, -100), hl=(-70, -140), er=(40, -100), hr=(70, -140)), up * (1 - fall))
        hip = (430 + wob, lerp(FLOOR - 30, FLOOR - 113 * 0.58, up * (1 - fall)))
        baby_fig(st, d, pose, hip, "laugh" if fall > 0.5 else "determined", u)
    else:
        w = clamp((u - T_S) / 0.6)
        pose = R.walk_pose(w * 9, 0.4)
        pose = dict(pose, el=(-40, -100), hl=(-60, -140), er=(40, -100), hr=(60, -140))
        baby_fig(st, d, pose, (lerp(430, 650, w), FLOOR - 113 * 0.58), "laugh", u)
    return 1.9, 590, FLOOR - 130


# ---------------------------------------------------------------- 2 bike
def bike_parts(x, tilt):
    pivot = (x, FLOOR)
    parts = {"w1": (x - 70, FLOOR - 36), "w2": (x + 70, FLOOR - 36), "a": (x - 10, FLOOR - 36), "b": (x + 30, FLOOR - 90),
             "c": (x - 30, FLOOR - 96), "h": (x + 40, FLOOR - 120)}
    return rotp(parts, pivot, tilt)


def bike(st, d, u):
    floor_line(d)
    done = u >= T_S
    if not done:
        ph = phase(u)
        x = 330 + 110 * ph
        tilt = 1.25 * smooth(clamp((ph - 0.35) / 0.4))
    else:
        w = clamp((u - T_S) / 0.85)
        x, tilt = lerp(330, 820, w), 0.0
    bp = bike_parts(x, tilt)
    for k in ("w1", "w2"):
        d.ellipse(((bp[k][0] - 36) * K, (bp[k][1] - 36) * K, (bp[k][0] + 36) * K, (bp[k][1] + 36) * K),
                  outline=(170, 174, 184, 255), width=int(5 * K))
    line(d, [bp["w1"], bp["a"], bp["b"], bp["w2"]], (60, 140, 220, 255), 6)
    line(d, [bp["a"], bp["c"]], (60, 140, 220, 255), 6)
    line(d, [bp["b"], bp["h"]], (90, 90, 100, 255), 5)
    pedal = u * 14
    pose = {"head": (30, -146), "neck": (22, -104), "kl": (40, 30 + 14 * math.sin(pedal)), "fl": (30, 76 + 20 * math.sin(pedal)),
            "kr": (40, 30 - 14 * math.sin(pedal)), "fr": (30, 76 - 20 * math.sin(pedal)), "el": (50, -70), "hl": (74, -36),
            "er": (54, -66), "hr": (78, -32)}
    if done and u > T_S + 0.4:
        pose = dict(pose, er=(30, -150), hr=(50, -196))
    p = place(pose, (x - 30, FLOOR - 104), 1, S)
    p = rotp(p, (x, FLOOR), tilt)
    hero(st, p, "plain", 1, "happy" if done else ("shocked" if tilt > 0.5 else "determined"), u)
    return 1.7, 560, FLOOR - 170


# ---------------------------------------------------------------- 3 rope
def rope(st, d, u):
    floor_line(d)
    done = u >= T_S
    per = 0.38 if done else P
    ph = (u % per) / per
    a = 2 * math.pi * ph
    jump = max(0.0, math.sin(a - math.pi / 2 + math.pi)) if True else 0
    caught = (not done) and ph > 0.55
    hop = 0.0 if caught else 60 * max(0.0, -math.cos(a)) ** 3
    pose = dict(STAND, el=(-40, -70), hl=(-60, -40), er=(40, -70), hr=(60, -40), kl=(-6, 50), kr=(8, 50))
    if caught:
        k = smooth(clamp((ph - 0.55) / 0.3))
        pose = lerp_pose(pose, dict(pose, head=(30, -136), neck=(18, -98), kl=(20, 40), fl=(40, 100)), k)
    p = place(pose, (540, FLOOR - 113 * S - hop), 1, S)
    hl, hr = p["hl"], p["hr"]
    if caught:
        mid = (540, FLOOR - 10)
    else:
        mid = (540 + 40 * math.sin(a), lerp(p["head"][1] - 80, FLOOR + 6, (1 - math.cos(a)) / 2))
    pts = []
    for k in range(17):
        tt = k / 16
        x = (1 - tt) ** 2 * hl[0] + 2 * (1 - tt) * tt * (2 * mid[0] - (hl[0] + hr[0]) / 2) + tt ** 2 * hr[0]
        y = (1 - tt) ** 2 * hl[1] + 2 * (1 - tt) * tt * (2 * mid[1] - (hl[1] + hr[1]) / 2) + tt ** 2 * hr[1]
        pts.append((x, y))
    line(d, pts, (240, 200, 60, 255), 4)
    hero(st, p, "plain", 1, "happy" if done else ("tired" if caught else "determined"), u)
    return 1.8, 540, FLOOR - 170


# ---------------------------------------------------------------- 4 hoop
RIM = (790, FLOOR - 430)


def ball(d, x, y, rot=0.0, col=(230, 120, 40)):
    ell(d, x, y, 24, 24, col + (255,))
    d.arc(((x - 24) * K, (y - 24) * K, (x + 24) * K, (y + 24) * K), 0, 360, fill=(80, 40, 16, 255), width=int(3 * K))
    line(d, [(x - 24 * math.cos(rot), y - 24 * math.sin(rot)), (x + 24 * math.cos(rot), y + 24 * math.sin(rot))], (80, 40, 16, 255), 3)


def hoop(st, d, u):
    floor_line(d)
    line(d, [(930, FLOOR), (930, FLOOR - 520)], (90, 94, 104, 255), 12)
    rrect(d, (890, FLOOR - 560, 906, FLOOR - 380), 3, (230, 232, 240, 255))
    done = u >= T_S
    sw = smooth(prog(u, T_S + 0.3, T_S + 0.45)) * (1 - smooth(prog(u, T_S + 0.6, T_S + 0.9))) if done else 0
    for j in range(5):
        x0 = RIM[0] + j * (890 - RIM[0]) / 4
        line(d, [(x0, RIM[1]), (830 - 20 + j * 10 + 6 * sw * math.sin(u * 40 + j), RIM[1] + 70 + 10 * sw)], (236, 236, 240, 220), 2)
    line(d, [(RIM[0] - 6, RIM[1]), (892, RIM[1])], (236, 96, 40, 255), 8)
    ph = phase(u) if not done else clamp((u - T_S) / 0.6)
    up = math.sin(math.pi * clamp(ph / 0.3)) if ph < 0.3 else 0
    pose = dict(STAND, el=(lerp(24, 10, up), lerp(-64, -160, up)), hl=(lerp(46, 20, up), lerp(-96, -210, up)),
                er=(lerp(34, 24, up), lerp(-60, -160, up)), hr=(lerp(54, 36, up), lerp(-92, -214, up)))
    if done and u > T_S + 0.6:
        pose = dict(PW.ARMS_UP)
    p = place(pose, (480, FLOOR - 113 * S - 20 * up), 1, S)
    hero(st, p, "plain", 1, "happy" if done and u > T_S + 0.5 else "determined", u)
    hand = ((p["hl"][0] + p["hr"][0]) / 2 + 6, (p["hl"][1] + p["hr"][1]) / 2 - 18)
    if ph < 0.15:
        bx, by = hand
    else:
        v = (ph - 0.15) / 0.85
        tgt = (830, RIM[1]) if done else RIM
        f_ = min(1.0, v / 0.6)
        bx = lerp(hand[0], tgt[0], f_)
        by = lerp(hand[1], tgt[1] - 26, f_) - 150 * 4 * f_ * (1 - f_)
        if v > 0.6:
            w = (v - 0.6) / 0.4
            if done:
                bx, by = tgt[0], lerp(tgt[1] - 26, FLOOR - 24, min(1, w * 1.4))
            else:
                bx, by = lerp(tgt[0], tgt[0] - 240, w), lerp(tgt[1] - 26, FLOOR - 24, w ** 0.7)
    ball(d, bx, by, u * 9)
    return 1.5, 680, FLOOR - 280


# ---------------------------------------------------------------- 5 backflip
def flip_pts(v, ok, x0=540):
    crouch = smooth(clamp(v / 0.2))
    air = clamp((v - 0.2) / 0.55)
    tuck = math.sin(math.pi * air)
    pose = lerp_pose(dict(STAND, el=(-30, -60), hl=(-50, -30), er=(30, -60), hr=(50, -30)),
                     dict(STAND, kl=(30, 10), fl=(10, 50), kr=(40, 16), fr=(20, 56), el=(20, -90), hl=(40, -60), er=(30, -90),
                          hr=(50, -60), head=(10, -120), neck=(6, -90)), max(crouch * (1 - air), tuck))
    hy = FLOOR - 113 * S - 230 * math.sin(math.pi * air) + 30 * crouch * (1 - air)
    rot = -2 * math.pi * smooth(air) * (1.0 if ok else 0.72)
    p = place(pose, (x0 - 40 * air, hy), 1, S)
    p = rotp(p, (x0 - 40 * air, hy - 40), rot)
    if not ok and v > 0.75:   # lands on his back
        w = smooth(clamp((v - 0.75) / 0.2))
        lp = place(dict(LYING, head=(-150, -10)), (x0 - 60, FLOOR - 30), -1, S)
        p = {k: (lerp(p[k][0], lp[k][0], w), lerp(p[k][1], lp[k][1], w)) for k in p}
    return p


def flip(st, d, u):
    floor_line(d)
    done = u >= T_S
    n = tries(u, 40)
    if not done:
        ghosts(st, [(flip_pts(0.95, False, 540 + ((k * 37) % 50) - 25), S) for k in range(min(n, 14))])
        p = flip_pts(phase(u), False)
        expr = "shocked"
    else:
        v = clamp((u - T_S) / 0.7)
        p = flip_pts(v, True)
        expr = "happy"
        if v >= 1:
            p = place(dict(PW.ARMS_UP), (500, FLOOR - 113 * S), 1, S)
    hero(st, p, "plain", 1, expr, u)
    return 1.6, 520, FLOOR - 250


# ---------------------------------------------------------------- 6 skate
def skate(st, d, u):
    floor_line(d)
    poly(d, [(500, FLOOR), (530, FLOOR - 70), (610, FLOOR - 70), (640, FLOOR)], (120, 120, 132, 255), outline=(70, 70, 80, 255), w=2)
    done = u >= T_S
    n = tries(u, 60)
    if not done:
        gp = []
        for k in range(1, min(n, 14)):
            pose, hip, board, rot = skater(0.6 + 0.25 * ((k * 0.37) % 1), False, seed=k)
            q = place(pose, (hip[0] + ((k * 53) % 140) - 70, hip[1]), 1, S)
            gp.append((q, S))
        ghosts(st, gp)
        v = phase(u)
    else:
        v = clamp((u - T_S) / 0.85)
    pose, hip, board, rot = skater(v, done, seed=n)
    p = place(pose, hip, 1, S)
    if rot:
        p = rotp(p, hip, rot)
    draw_board(d, *board)
    hero(st, p, "plain", 1, "happy" if done else ("shocked" if rot else "determined"), u)
    return 1.6, 560, FLOOR - 220


# ---------------------------------------------------------------- 7 pull-up
def pullup(st, d, u):
    floor_line(d)
    for x in (380, 700):
        line(d, [(x, FLOOR), (x, FLOOR - 470)], (90, 90, 96, 255), 9)
    line(d, [(370, FLOOR - 460), (710, FLOOR - 460)], (150, 150, 156, 255), 7)
    done = u >= T_S
    if not done:
        strain = math.sin(u * 30) * 4
        up = 0.12 + 0.08 * max(0, math.sin(phase(u) * math.pi))
    else:
        up = 0.5 - 0.5 * math.cos((u - T_S) * 7)
        strain = 0
    hip_y = FLOOR - 272 - 60 * up
    pose = {"head": (strain, -150 + 20 * (1 - up)), "neck": (0, -108), "kl": (-6, 56), "fl": (-14 + strain, 112), "kr": (6, 56),
            "fr": (-4 - strain, 112), "el": (0, 0), "hl": (0, 0), "er": (0, 0), "hr": (0, 0)}
    p = dict(place(pose, (540, hip_y), 1, S))
    for side, hx in (("l", 500), ("r", 580)):
        p = set_arm(p, side, (hx, FLOOR - 466), 1 if side == "r" else -1)
    hero(st, p, "plain", 1, "happy" if done and up > 0.6 else ("tired" if not done else "determined"), u)
    return 1.7, 540, FLOOR - 280


# ---------------------------------------------------------------- 8 penalty
GOAL_X = 880


def penalty(st, d, u):
    floor_line(d)
    # goal (side-ish view): post, crossbar, net
    line(d, [(GOAL_X, FLOOR), (GOAL_X, FLOOR - 260)], (240, 240, 245, 255), 8)
    line(d, [(GOAL_X, FLOOR - 260), (GOAL_X + 160, FLOOR - 230)], (240, 240, 245, 255), 8)
    done = u >= T_S
    bulge = smooth(prog(u, T_S + 0.3, T_S + 0.45)) * (1 - smooth(prog(u, T_S + 0.7, T_S + 1.0))) if done else 0
    for j in range(8):
        y = FLOOR - 250 + j * 32
        line(d, [(GOAL_X + 4, y), (GOAL_X + 150 + 30 * bulge * math.sin(j), y + 8)], (220, 220, 226, 140), 2)
    ph = phase(u) if not done else clamp((u - T_S) / 0.6)
    kind = ["post", "wide", "save"][int(u / P) % 3] if not done else "goal"
    kick = math.sin(math.pi * clamp(ph / 0.3))
    pose = dict(STAND, kr=(30 + 40 * kick, 50 - 20 * kick), fr=(40 + 90 * kick, 100 - 60 * kick), el=(-40, -90), hl=(-70, -60))
    if done and u > T_S + 0.6:
        pose = dict(PW.ARMS_UP)
    p = place(pose, (360, FLOOR - 113 * S), 1, S)
    hero(st, p, "plain", 1, "happy" if done and u > T_S + 0.5 else "determined", u)
    # keeper
    dive = 0.0
    if kind == "save":
        dive = smooth(clamp((ph - 0.3) / 0.3))
    elif kind == "goal":
        dive = smooth(clamp((ph - 0.45) / 0.3))
    kp = place(dict(STAND, el=(-30, -110 - 60 * dive), hl=(-40, -160 - 60 * dive), er=(30, -110), hr=(40, -160)),
               (GOAL_X - 50, FLOOR - 113 * S - 80 * dive), -1, S)
    if dive:
        kp = rotp(kp, (GOAL_X - 50, FLOOR - 120), -0.9 * dive)
    figure(st, kp, S, light=(0.4, -0.9), body=(200, 200, 210))
    outfit(ImageDraw.Draw(st), kp, (60, 160, 80), -1, legs=False)
    face(ImageDraw.Draw(st), kp, "determined", -1, u)
    # ball
    b0 = (440, FLOOR - 24)
    v = clamp((ph - 0.25) / 0.5)
    tgt = {"post": (GOAL_X, FLOOR - 250), "wide": (GOAL_X + 40, FLOOR - 360), "save": (GOAL_X - 60, FLOOR - 200),
           "goal": (GOAL_X + 30, FLOOR - 232)}[kind]
    if ph < 0.25:
        bx, by = b0
    elif v < 1 or kind == "goal":
        vv = min(1, v)
        bx, by = lerp(b0[0], tgt[0], vv), lerp(b0[1], tgt[1], vv) - 120 * 4 * vv * (1 - vv)
    else:
        w = clamp((ph - 0.75) / 0.25)
        bx, by = (lerp(tgt[0], tgt[0] - 200, w), lerp(tgt[1], FLOOR - 24, w)) if kind != "save" else (kp["hl"][0], kp["hl"][1])
    ball(d, bx, by, u * 12, col=(240, 240, 240))
    return 1.45, 640, FLOOR - 220


# ---------------------------------------------------------------- 9 lift
def lift(st, d, u):
    floor_line(d)
    done = u >= T_S
    if not done:
        ph = phase(u)
        h = math.sin(math.pi * clamp(ph / 0.7)) * 0.45       # gets it to the hips, drops it
    else:
        h = smooth(clamp((u - T_S) / 0.5))
    bar_y = lerp(FLOOR - 50, FLOOR - 470, h)
    if h < 0.5:
        k = h / 0.5
        pose = lerp_pose(dict(STAND, head=(30, -120), neck=(26, -86), kl=(40, 20), fl=(10, 100), kr=(46, 26), fr=(20, 104)),
                         STAND, k)
        hip_y = FLOOR - 113 * S + 40 * (1 - k)
    else:
        pose = dict(STAND)
        hip_y = FLOOR - 113 * S
    p = place(pose, (540, hip_y), 1, S)
    shake = (math.sin(u * 50) * 4) if not done else (math.sin(u * 30) * 2 * (1 - smooth(prog(u, T_S + 0.5, T_S + 0.8))))
    p = set_arm(set_arm(p, "l", (500, bar_y + shake), -1), "r", (580, bar_y - shake), 1)
    line(d, [(360, bar_y + shake), (720, bar_y - shake)], (190, 194, 204, 255), 7)
    for x in (380, 400, 680, 700):
        rrect(d, (x - 8, bar_y - 46, x + 8, bar_y + 46), 3, (40, 42, 50, 255), outline=(100, 104, 116, 255), w=1.5)
    hero(st, p, "plain", 1, "happy" if done and h > 0.9 else "determined", u)
    return 1.5, 540, FLOOR - 260


# ---------------------------------------------------------------- 10 high jump
BAR_X, BAR_H = 600, 240


def hj_pts(v, ok):
    x = lerp(180, 760, v)
    air = clamp((v - 0.45) / 0.35)
    if v < 0.45:
        pose = R.run_pose(v * 30, 0.7)
        return place(pose, R.grounded(pose, x, FLOOR, S), 1, S), 0
    arch = math.sin(math.pi * air)
    hy = FLOOR - 113 * S - (BAR_H + (30 if ok else -10)) * arch
    pose = dict(STAND, head=(-20, -140), neck=(-10, -100), el=(-40, -80), hl=(-70, -60), er=(-30, -84), hr=(-60, -64),
                kl=(30, 40), fl=(40, 100), kr=(36, 44), fr=(50, 104))
    p = place(pose, (x, hy), 1, S)
    p = rotp(p, (x, hy), -1.5 * arch)
    return p, air


def jump(st, d, u):
    floor_line(d)
    rrect(d, (BAR_X + 20, FLOOR - 70, BAR_X + 260, FLOOR), 8, (40, 70, 160, 255))
    for x in (BAR_X - 10, BAR_X + 70):
        line(d, [(x, FLOOR), (x, FLOOR - BAR_H - 40)], (210, 210, 220, 255), 6)
    done = u >= T_S
    n = tries(u, 100)
    if not done:
        ghosts(st, [(place(dict(LYING), (BAR_X + 100 + ((k * 41) % 80), FLOOR - 70 - 30), -1, S), S) for k in range(min(n, 12))])
        v = phase(u)
        p, air = hj_pts(v, False)
        knocked = air > 0.5
        bar_drop = smooth(clamp((air - 0.5) / 0.3))
        hero(st, p, "plain", 1, "shocked" if knocked else "determined", u)
    else:
        v = clamp((u - T_S) / 0.85) ** 0.85
        p, air = hj_pts(v, True)
        bar_drop = 0.0
        hero(st, p, "plain", 1, "happy", u)
    by = FLOOR - BAR_H - 20 + 200 * bar_drop
    line(d, [(BAR_X - 10, by), (BAR_X + 70, by + 30 * bar_drop)], (240, 220, 60, 255), 6)
    return 1.45, 520, FLOOR - 240


FN = {"baby": baby, "bike": bike, "rope": rope, "hoop": hoop, "flip": flip, "skate": skate, "pullup": pullup,
      "penalty": penalty, "lift": lift, "jump": jump}


# ---------------------------------------------------------------- frame
SPOTS = ((360, 0.8), (720, 1.0))


def sunrise(k):
    g = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    if k <= 0:
        return g
    glow_ell(g, 820, 760, 300, 300, (255, 170, 90, int(140 * k)))
    ImageDraw.Draw(g).ellipse(((820 - 90) * K, (760 - 90) * K, (820 + 90) * K, (760 + 90) * K), (255, 214, 140, int(255 * k)))
    return g


def header(im, t, n, done, pop=1.0, a=1.0):
    d = Image.new("RGBA", im.size, (0, 0, 0, 0))
    dd = ImageDraw.Draw(d)
    PW.spaced(dd, W / 2, 34, "HOW MANY TIMES WOULD YOU TRY?", font("InterDisplay-Bold.otf", 42), (236, 238, 246, int(255 * a)), 3)
    col = GOLD if done else (246, 246, 250)
    PW.spaced(dd, W / 2, 150, f"TRY {n}", font("InterDisplay-Bold.otf", int(110 * max(0.6, pop))), col + (int(255 * a),), 6)
    im.alpha_composite(d)


def frame(t):
    if t >= T_END:
        u = t - T_END
        st = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
        d = ImageDraw.Draw(st)
        z, cx, cy = baby(st, d, T_S + 1.2)
        im = compose(st, None, z, cx, cy, spots=SPOTS, refl=True)
        f = font("/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf", 66)
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        for j, (s_, col, t0) in enumerate((("YOU NEVER QUIT", (246, 240, 226), 0.0), ("AS A KID.", (246, 240, 226), 0.15),
                                            ("WHY QUIT NOW?", GOLD, 0.8))):
            a = smooth(prog(u, t0, t0 + 0.35))
            if a > 0:
                PW.spaced(ld, W / 2, 200 + j * 90 + (40 if j == 2 else 0), s_, f, col + (int(255 * a),), 5)
        im.alpha_composite(lay)
        return np.asarray(im.convert("RGB"))
    i = min(len(SC) - 1, int(t / L))
    kind, n = SC[i]
    u = t - i * L
    st = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(st)
    z, cx, cy = FN[kind](st, d, u)
    done = u >= T_S
    shake = 10 * max(0, 1 - (u - T_S) / 0.25) if done and u < T_S + 0.25 else 0
    push = 0.95 + 0.1 * clamp(u / L)
    back = sunrise(smooth(prog(u, T_S - 0.2, T_S + 0.6))) if kind == "jump" else None
    im = compose(st, None, z * push, cx + shake * math.sin(t * 80), cy, spots=SPOTS, back=back, refl=True)
    if done and u < T_S + 0.4:
        k = 1 - (u - T_S) / 0.4
        im.alpha_composite(Image.new("RGBA", im.size, (255, 220, 140, int(60 * k))))
    if abs(u) < 0.12 and i > 0:
        im = whip(im, 1 - abs(u) / 0.12)
    elif abs(u - L) < 0.12:
        im = whip(im, 1 - abs(u - L) / 0.12)
    header(im, t, tries(u, n), done, hq.pop(u, T_S, 0.2) if done else 1.0)
    return np.asarray(im.convert("RGB"))


def render(i):
    acc = None
    for k in range(3):
        f = frame((i + k / 6) / FPS).astype(np.float32)
        acc = f if acc is None else acc + f
    return (acc / 3).astype(np.uint8).tobytes()


MUSIC = "Undaunted.mp3"


def audio():
    n = int(DUR * SR)
    out = np.zeros((n, 2))
    put(out, track(MUSIC, 40.0, DUR), 0.0, 1.6, fin=0.05, fout=1.0)
    thud = noise(0.2, 3, lo=60, hi=1200)[:int(0.2 * SR)] * env(int(0.2 * SR), 0.002, 0.15)
    ding = tone(880, 0.7, (1, 2, 3), a=0.002, d=0.6)
    for i, (kind, nn) in enumerate(SC):
        s0 = i * L
        k = 0
        while k * P + 0.7 * P < T_S:      # every failed attempt
            mix_in(out, thud, s0 + k * P + 0.7 * P, 0.3, 0.0)
            k += 1
        mix_in(out, ding, s0 + T_S, 0.3, 0.0)
        mix_in(out, noise(0.3, 9, lo=500, hi=7000)[:int(0.3 * SR)] * env(int(0.3 * SR), 0.15, 0.1), s0 - 0.15, 0.15, 0.0)
    mix_in(out, tone(55, 1.0, (1, 2), a=0.002, d=0.9), T_END + 0.8, 0.5, 0.0)
    tt = np.arange(n) / SR
    out *= np.clip((DUR - tt) / 0.6, 0.0, 1)[:, None]
    out /= max(1.0, np.abs(out).max() / 0.9)
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    if "--stills" in sys.argv:
        ts = [float(a) for a in sys.argv[2:]] or [i * L + o for i in range(10) for o in (0.5, 1.9)] + [T_END + 1.5]
        cols = 7
        rows = math.ceil(len(ts) / cols)
        sheet = Image.new("RGB", (240 * cols, 427 * rows))
        for j, t in enumerate(ts):
            sheet.paste(Image.fromarray(frame(t)).resize((240, 427), Image.LANCZOS), ((j % cols) * 240, (j // cols) * 427))
        p = os.path.join(here, "tryagain", "stills.png")
        sheet.save(p)
        print(p)
        return
    out = sys.argv[1]
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
