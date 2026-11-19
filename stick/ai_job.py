#!/usr/bin/env python3
"""AI IS HERE - Doer vs Overthinker, the split-room style (same job, same desk, same day), 26.4 s, loops on itself.

Day 1, both screens say AI IS HERE and the same little robot rolls into both offices. The doer: "TEACH ME." - the
robot hands him a book and works next to him; AI books pile up, his chart climbs, SALARY $4,000 -> $16,000. The
overthinker: "IT'S JUST A FAD." - he pushes the robot into the corner, where it gathers cobwebs; his paper pile grows,
SALARY stays $4,000 ("IT CAN'T DO MY JOB." "I'LL LEARN IT LATER.").
Day 365: his screen goes red, REPLACED. The doer leaves the top room and walks into his, tablet in hand ("I'LL TAKE IT
FROM HERE."), wakes the dusty robot, it takes the chair and clears the pile in seconds. He walks out with a box.
SALARY $0 below, $20,000 above (+$4,000).
"AI DIDN'T TAKE HIS JOB. / SOMEONE USING AI DID."

    python3 stick/ai_job.py stick/ai-job.mp4
    ONLY_FRAMES=0,1.6,3.0,7,13,15.2,16.8,18.3,22 python3 stick/ai_job.py /tmp/ai   (PNG stills)
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perfect_wave as PW  # noqa  (fonts, easing, the 2x canvas, sound helpers)
from perfect_wave import (MONO, clamp, env, font, in_quad, lerp, lerp_pose, midi, mix_in, noise, out_back,  # noqa
                          out_cubic, prog, rot, smooth, spaced, tone, write_wav)

W, H, FPS = 1080, 1920, 30
SR = 44100
BPM = 100
BEAT = 60 / BPM
BAR = 4 * BEAT
DUR = 11 * BAR                          # 26.4 s
NF = int(round(DUR * FPS))
XFADE = 0.5

# ---------------------------------------------------------------- layout (as in the split-room reels)
PH = 600                                # panel height
FY = 565                                # floor, panel coordinates
TOP_Y0, BOT_Y0 = 330, 1075               # panel tops in the frame
SC = 1.25                               # people and robots are drawn a quarter bigger than in perfect_wave

CHAIR_X = 235
HIP_SIT = (CHAIR_X, FY - 115 * SC)
DESK_X0, DESK_X1 = 330, 668
DESK_TOP = FY - 196
MON_X, MON_W, MON_H = 468, 206, 138
STACK_X = 620
TABLE_X0, TABLE_X1, TABLE_TOP = 700, 800, FY - 150
ROBOT_DESK_X = 862                      # where the top robot works, next to its laptop
CORNER_X = 1000
INK = (12, 14, 22)
DOER, DOER_FAR = (246, 246, 242), (204, 205, 206)
OT, OT_FAR = (150, 152, 158), (116, 118, 124)
GOLD = (246, 196, 72)
CYAN = (110, 200, 255)
RED = (236, 76, 70)
GREEN = (110, 220, 140)

# ---------------------------------------------------------------- timeline
T_AI = 1.0                              # AI IS HERE on both screens
T_ROLL0, T_ROLL1 = 1.4, 2.4             # the robots roll in
T_BOOK = 3.4
T_PUSH0, T_PUSH1 = 3.55, 4.3
T_D0, T_D1, T_365 = 4.2, 14.2, 14.4
T_UP = 14.6                             # the doer stands up and leaves the top room
T_EXIT0, T_EXIT1 = 14.9, 15.9
T_IN0, T_IN1 = 15.6, 16.5               # ... and walks into the bottom one
T_WAKE = 16.6
T_OUT_UP = 16.9
T_OUT0, T_OUT1 = 17.25, 18.9
T_RB0, T_RB1 = 17.35, 18.05             # the dusty robot takes the chair
T_ZERO = 17.4
T_RAISE = 17.8
T_L1, T_L2 = 19.6, 20.75
CPS = 24.0
LINE1, LINE2 = "AI DIDN'T TAKE HIS JOB.", "SOMEONE USING AI DID."

TOP_SAL = [(0, 4000), (5.5, 5500), (7.5, 7000), (9.5, 9500), (11.5, 12000), (13.2, 16000), (T_RAISE, 20000)]
BOOK_T = [T_BOOK + 0.4, 5.0, 6.4, 7.8, 9.2, 10.6, 12.0, 13.4]

BUBBLES_TOP = [(2.5, 3.45, "TEACH ME.", "doer"), (5.6, 6.6, "AUTOMATE IT.", "doer"), (9.9, 10.9, "WHAT ELSE?", "doer"),
               (1.95, 2.55, "HI!", "robot")]
BUBBLES_BOT = [(2.5, 3.6, "IT'S JUST A FAD.", "ot"), (5.4, 6.6, "IT CAN'T DO MY JOB.", "ot"),
               (8.5, 9.7, "I'LL LEARN IT LATER.", "ot"), (11.5, 12.7, "SO MUCH WORK...", "ot"),
               (14.65, 15.55, "WHAT?!", "ot"), (16.6, 17.95, "I'LL TAKE IT FROM HERE.", "doer"),
               (1.95, 2.55, "HI!", "robot")]


def day_at(t):
    if t < T_D0:
        return 1
    if t < T_365:
        return min(364, 1 + int(round(363 * prog(t, T_D0, T_D1) ** 1.25)))
    return 365


def top_salary(t):
    v = TOP_SAL[0][1]
    for t0, s in TOP_SAL:
        if t >= t0:
            v = s
    return v


def bot_salary(t):
    return 4000 if t < T_ZERO else 0


# ---------------------------------------------------------------- poses (facing right, y down, from the hip)
STAND = PW.STAND
SIT_TYPE = {"head": (12, -148), "neck": (8, -106), "el": (40, -62), "hl": (84, -50), "er": (34, -58), "hr": (78, -46),
            "kl": (58, -4), "fl": (60, 110), "kr": (52, 0), "fr": (52, 112)}
SIT_SHOO = dict(SIT_TYPE, el=(56, -88), hl=(108, -96))
SIT_SLUMP = dict(SIT_TYPE, head=(18, -136), neck=(12, -98), el=(40, -50), hl=(70, -34), er=(34, -48), hr=(64, -30))
SIT_LOOK = dict(SIT_TYPE, head=(6, -150), neck=(4, -107), el=(30, -64), hl=(62, -70))
CARRY_BOX = dict(STAND, el=(30, -72), hl=(62, -66), er=(26, -68), hr=(58, -62))
HOLD_TAB = dict(STAND, el=(26, -64), hl=(50, -92))


def walk(ph, base):
    p = dict(base)
    for side, off in (("l", 0.0), ("r", math.pi)):
        s = math.sin(ph + off)
        a = 0.42 * s
        kx, ky = 56 * math.sin(a), 56 * math.cos(a)
        bend = 0.1 + 0.6 * max(0.0, -math.cos(ph + off))
        p["k" + side] = (kx, ky)
        p["f" + side] = (kx + 57 * math.sin(a - bend), ky + 57 * math.cos(a - bend))
    return p


def place(pose, hip, facing=1, scale=SC, ang=0.0):
    out = {"hip": hip}
    for j, (x, y) in pose.items():
        dx, dy = rot((x * facing * scale, y * scale), ang)
        out[j] = (hip[0] + dx, hip[1] + dy)
    return out


def typing(pose, t, speed=11.0, amp=5.0):
    p = dict(pose)
    p["hl"] = (p["hl"][0], p["hl"][1] - amp * max(0.0, math.sin(t * speed)))
    p["hr"] = (p["hr"][0], p["hr"][1] - amp * max(0.0, math.sin(t * speed + 1.7)))
    return p


# ---------------------------------------------------------------- 2x drawing
Canvas = PW.Canvas
SS = PW.SS


def seg(cv, a, b, w, col):
    PW.seg(cv, a, b, w, col)


def disc(cv, p, r, col):
    PW.disc(cv, p, r, col)


def draw_stick(cv, pts, body, far, facing=1, s=SC):
    ink = INK + (255,)
    limb, out = 24 * s, 6 * s
    order = [((("neck", "er"), ("er", "hr")), far, "hr"), ((("hip", "kr"), ("kr", "fr")), far, "fr"),
             ((("neck", "hip"),), body, None), ((("hip", "kl"), ("kl", "fl")), body, "fl"),
             ((("neck", "el"), ("el", "hl")), body, "hl")]
    for segs, col, end in order:
        w = limb + (4 * s if segs[0] == ("neck", "hip") else 0)
        for a, b in segs:
            seg(cv, pts[a], pts[b], w + 2 * out, ink)
        if end and end[0] == "f":
            fx, fy = pts[end]
            disc(cv, (fx + facing * 6 * s, fy + 2), 13 * s + out, ink)
        if end and end[0] == "h":
            disc(cv, pts[end], 11 * s + out, ink)
        for a, b in segs:
            seg(cv, pts[a], pts[b], w, col + (255,))
        if end and end[0] == "f":
            fx, fy = pts[end]
            q = cv.P((fx + facing * 6 * s, fy + 2))
            cv.d.ellipse([q[0] - 16 * s * SS, q[1] - 10 * s * SS, q[0] + 16 * s * SS, q[1] + 10 * s * SS],
                         fill=col + (255,))
        if end and end[0] == "h":
            disc(cv, pts[end], 11 * s, col + (255,))
    hx, hy = pts["head"]
    disc(cv, (hx, hy), 31 * s + out, ink)
    disc(cv, (hx, hy), 31 * s, body + (255,))
    q = cv.P((hx - 10 * s, hy - 11 * s))
    cv.d.ellipse([q[0] - 9 * s * SS, q[1] - 6 * s * SS, q[0] + 9 * s * SS, q[1] + 6 * s * SS], fill=(255, 255, 255, 110))


def person_sprite(pts, body, far, facing, prop=None):
    allp = list(pts.values())
    cv = Canvas(*PW.bbox_of(allp, 110))
    draw_stick(cv, pts, body, far, facing)
    ink = INK + (255,)
    if prop == "box":
        hx = (pts["hl"][0] + pts["hr"][0]) / 2
        hy = (pts["hl"][1] + pts["hr"][1]) / 2
        bw, bh = 92, 66
        x0, y0 = hx - bw / 2 + facing * 8, hy - 18
        # a plant and a mug stick out of the top
        cv.d.line([cv.P((x0 + 26, y0 + 4)), cv.P((x0 + 26, y0 - 34))], fill=(70, 150, 80, 255), width=5 * SS)
        for dx, dy in ((-12, -30), (12, -40), (-8, -48), (10, -22)):
            q = cv.P((x0 + 26 + dx, y0 + dy))
            cv.d.ellipse([q[0] - 9 * SS, q[1] - 5 * SS, q[0] + 9 * SS, q[1] + 5 * SS], fill=(92, 176, 96, 255),
                         outline=ink, width=2 * SS)
        m0, m1 = cv.P((x0 + 54, y0 - 18)), cv.P((x0 + 74, y0 + 4))
        cv.d.rounded_rectangle([m0[0], m0[1], m1[0], m1[1]], 3 * SS, fill=(220, 90, 80, 255), outline=ink,
                               width=2 * SS)
        b0, b1 = cv.P((x0, y0)), cv.P((x0 + bw, y0 + bh))
        cv.d.rectangle([b0[0], b0[1], b1[0], b1[1]], fill=(176, 136, 92, 255), outline=ink, width=4 * SS)
        f0, f1 = cv.P((x0 + 4, y0 + 4)), cv.P((x0 + bw - 4, y0 + 14))
        cv.d.rectangle([f0[0], f0[1], f1[0], f1[1]], fill=(150, 112, 74, 255))
        for hand in ("hl", "hr"):
            disc(cv, pts[hand], 11 * SC + 6 * SC, ink)
            disc(cv, pts[hand], 11 * SC, body + (255,))
    if prop == "tablet":
        hx, hy = pts["hl"]
        q0, q1 = cv.P((hx - 6 * facing - 30, hy - 52)), cv.P((hx - 6 * facing + 30, hy + 2))
        cv.d.rounded_rectangle([min(q0[0], q1[0]), q0[1], max(q0[0], q1[0]), q1[1]], 6 * SS, fill=(30, 36, 52, 255),
                               outline=ink, width=4 * SS)
        s0, s1 = cv.P((hx - 6 * facing - 24, hy - 46)), cv.P((hx - 6 * facing + 24, hy - 4))
        cv.d.rectangle([min(s0[0], s1[0]), s0[1], max(s0[0], s1[0]), s1[1]], fill=(70, 150, 220, 255))
        disc(cv, pts["hl"], 11 * SC + 6 * SC, ink)
        disc(cv, pts["hl"], 11 * SC, body + (255,))
    return cv.done()


def robot_sprite(x, t, facing=-1, eyes="open", arm=0.0, dust=0.0, wave=0.0, typing_=0.0):
    """A small rolling office robot: wheel, body, a screen face, an antenna. (x, FY) is where its wheel meets the floor."""
    k = SS
    cv = Canvas(x - 130, FY - 280, x + 130, FY + 10)
    ink = INK + (255,)
    shell = PW.lerp_c((222, 226, 234), (150, 150, 150), dust)
    dark = PW.lerp_c((60, 66, 80), (70, 70, 70), dust)
    P = cv.P
    # wheel and stem
    w0, w1 = P((x - 30, FY - 44)), P((x + 30, FY))
    cv.d.ellipse([w0[0], w0[1], w1[0], w1[1]], fill=dark + (255,), outline=ink, width=5 * k)
    h0, h1 = P((x - 9, FY - 31)), P((x + 9, FY - 13))
    cv.d.ellipse([h0[0], h0[1], h1[0], h1[1]], fill=shell + (255,))
    cv.d.rectangle([P((x - 10, FY - 70))[0], P((x - 10, FY - 70))[1], P((x + 10, FY - 38))[0], P((x + 10, FY - 38))[1]],
                   fill=dark + (255,), outline=ink, width=3 * k)
    # body
    b0, b1 = P((x - 46, FY - 160)), P((x + 46, FY - 66))
    cv.d.rounded_rectangle([b0[0], b0[1], b1[0], b1[1]], 22 * k, fill=shell + (255,), outline=ink, width=6 * k)
    c0, c1 = P((x - 16, FY - 130)), P((x + 16, FY - 98))
    cv.d.ellipse([c0[0], c0[1], c1[0], c1[1]], fill=PW.lerp_c(CYAN, (90, 90, 90), dust) + (255,), outline=ink,
                 width=3 * k)
    # arms: the far one behind, the near one can wave or type
    sh = (x + facing * 30, FY - 140)
    if typing_ > 0:
        a1 = (x + facing * 78, FY - 120 + 8 * math.sin(t * 34))
        a2 = (x + facing * 70, FY - 112 + 8 * math.sin(t * 34 + 2))
    else:
        ang = -1.9 + 0.5 * math.sin(t * 14) if wave > 0 else 0.5 + arm
        a1 = (sh[0] + facing * 62 * math.cos(ang), sh[1] + 62 * math.sin(ang))
        a2 = (x + facing * -34, FY - 92)
    for a, b in (((x - facing * 30, FY - 140), a2), (sh, a1)):
        cv.d.line([P(a), P(b)], fill=ink, width=16 * k)
        cv.d.line([P(a), P(b)], fill=shell + (255,), width=8 * k)
        q = P(b)
        cv.d.ellipse([q[0] - 11 * k, q[1] - 11 * k, q[0] + 11 * k, q[1] + 11 * k], fill=shell + (255,), outline=ink,
                     width=4 * k)
    # head with a screen face
    g0, g1 = P((x - 56, FY - 236)), P((x + 56, FY - 158))
    cv.d.rounded_rectangle([g0[0], g0[1], g1[0], g1[1]], 24 * k, fill=shell + (255,), outline=ink, width=6 * k)
    s0, s1 = P((x - 44, FY - 226)), P((x + 44, FY - 168))
    cv.d.rounded_rectangle([s0[0], s0[1], s1[0], s1[1]], 16 * k, fill=(18, 22, 34, 255))
    ex = x + facing * 8
    ec = PW.lerp_c(CYAN, (60, 60, 60), dust)
    for dx in (-18, 18):
        cx_, cy_ = ex + dx, FY - 197
        if eyes == "open":
            blink = 1.0 if (t * 1.7) % 3.1 > 0.12 else 0.15
            q0, q1 = P((cx_ - 8, cy_ - 11 * blink)), P((cx_ + 8, cy_ + 11 * blink))
            cv.d.ellipse([q0[0], q0[1], q1[0], q1[1]], fill=ec + (255,))
        elif eyes == "happy":
            q0, q1 = P((cx_ - 10, cy_ - 8)), P((cx_ + 10, cy_ + 10))
            cv.d.arc([q0[0], q0[1], q1[0], q1[1]], 200, 340, fill=ec + (255,), width=5 * k)
        elif eyes == "sad":
            q0, q1 = P((cx_ - 10, cy_ - 2)), P((cx_ + 10, cy_ + 16))
            cv.d.arc([q0[0], q0[1], q1[0], q1[1]], 200, 340, fill=ec + (255,), width=5 * k)
            cv.d.line([P((cx_ - 9, cy_ - 10 - dx / 6)), P((cx_ + 9, cy_ - 10 + dx / 6))], fill=ec + (255,), width=3 * k)
        elif eyes == "sleep":
            cv.d.line([P((cx_ - 9, cy_ + 2)), P((cx_ + 9, cy_ + 2))], fill=(70, 80, 96, 255), width=4 * k)
    # antenna
    cv.d.line([P((x, FY - 236)), P((x, FY - 262))], fill=ink, width=6 * k)
    lit = eyes != "sleep"
    q = P((x, FY - 266))
    cv.d.ellipse([q[0] - 9 * k, q[1] - 9 * k, q[0] + 9 * k, q[1] + 9 * k],
                 fill=((255, 90, 80) if lit else (90, 80, 80)) + (255,), outline=ink, width=3 * k)
    spr, off = cv.done()
    if lit:
        g = PW.glow_of(spr, 0.25, 12, (150, 210, 255))
        base = Image.new("RGBA", spr.size, (0, 0, 0, 0))
        base.alpha_composite(g)
        base.alpha_composite(spr)
        spr = base
    return spr, off


# ---------------------------------------------------------------- the room (static)
def build_room():
    yy, xx = np.mgrid[0:PH, 0:W].astype(np.float32)
    img = np.zeros((PH, W, 3), np.float32) + np.array([9, 9, 11], np.float32)
    light = np.zeros((PH, W), np.float32)
    for lx, wid in ((300, 250), (720, 230)):
        ly = 52
        inside = (yy >= ly) & (yy <= FY)
        depth = np.clip((yy - ly) / (FY - ly), 0, 1)
        half = 34 + depth * wid
        light += np.where(inside, np.clip(1 - np.abs(xx - lx) / half, 0, 1) ** 1.5 * (0.35 + 0.35 * (1 - depth)), 0) * 0.5
        light += np.exp(-(((xx - lx) / (wid * 0.95)) ** 2 + ((yy - FY) / 22) ** 2)) * 0.75
        light += np.exp(-(((xx - lx) ** 2 + (yy - ly) ** 2) / (2 * 36 ** 2))) * 1.0
    img += light[..., None] * np.array([255, 212, 158], np.float32) / 255 * 92
    floor = yy > FY
    img = np.where(floor[..., None], img * 0.75 + np.array([16, 14, 13], np.float32), img)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    d.line([(0, FY), (W, FY)], fill=(70, 62, 54, 255), width=3)
    rng = np.random.default_rng(3)
    for i in range(40):
        x = rng.uniform(0, W)
        d.line([(x, FY + 6), (x + rng.uniform(8, 30), FY + 6)], fill=(40, 36, 32, 255), width=2)
    # lamps
    for lx in (300, 720):
        d.line([(lx, 0), (lx, 34)], fill=(70, 70, 74, 255), width=3)
        d.polygon([(lx - 28, 56), (lx + 28, 56), (lx + 14, 32), (lx - 14, 32)], fill=(120, 116, 110, 255),
                  outline=INK + (255,))
        d.ellipse([lx - 12, 50, lx + 12, 62], fill=(255, 236, 196, 255))
    return im


def draw_furniture(d):
    ink = INK + (255,)
    # office chair (back on the left, the person faces right)
    sx, sy = CHAIR_X, FY - 112
    d.rounded_rectangle([sx - 54, sy - 12, sx + 46, sy + 6], 6, fill=(74, 72, 70, 255), outline=ink, width=3)
    d.rounded_rectangle([sx - 70, sy - 148, sx - 50, sy - 6], 8, fill=(74, 72, 70, 255), outline=ink, width=3)
    d.line([(sx - 4, sy + 6), (sx - 4, FY - 22)], fill=(60, 60, 62, 255), width=8)
    d.line([(sx - 50, FY - 14), (sx + 42, FY - 14)], fill=(60, 60, 62, 255), width=6)
    for wx in (sx - 50, sx + 42):
        d.ellipse([wx - 9, FY - 18, wx + 9, FY], fill=(40, 40, 42, 255), outline=ink, width=2)
    # desk
    d.rectangle([DESK_X0, DESK_TOP, DESK_X1, DESK_TOP + 16], fill=(96, 88, 80, 255), outline=ink, width=3)
    for lx in (DESK_X0 + 14, DESK_X1 - 22):
        d.rectangle([lx, DESK_TOP + 16, lx + 10, FY], fill=(70, 66, 62, 255), outline=ink, width=2)
    # keyboard
    d.rounded_rectangle([DESK_X0 + 6, DESK_TOP - 8, DESK_X0 + 96, DESK_TOP + 1], 3, fill=(50, 52, 58, 255),
                        outline=ink, width=2)
    # side table
    d.rectangle([TABLE_X0, TABLE_TOP, TABLE_X1, TABLE_TOP + 12], fill=(96, 88, 80, 255), outline=ink, width=3)
    for lx in (TABLE_X0 + 10, TABLE_X1 - 18):
        d.rectangle([lx, TABLE_TOP + 12, lx + 8, FY], fill=(70, 66, 62, 255), outline=ink, width=2)


def draw_laptop(d, x, open_, lit, t, fast=False):
    ink = INK + (255,)
    d.rounded_rectangle([x - 46, TABLE_TOP - 8, x + 46, TABLE_TOP], 3, fill=(120, 124, 134, 255), outline=ink, width=2)
    if open_:
        d.polygon([(x - 40, TABLE_TOP - 8), (x - 52, TABLE_TOP - 74), (x + 30, TABLE_TOP - 74), (x + 42, TABLE_TOP - 8)],
                  fill=(120, 124, 134, 255), outline=ink)
        if lit:
            d.polygon([(x - 34, TABLE_TOP - 13), (x - 44, TABLE_TOP - 68), (x + 24, TABLE_TOP - 68),
                       (x + 34, TABLE_TOP - 13)], fill=(40, 90, 140, 255))
            for i in range(5):
                y = TABLE_TOP - 60 + i * 10
                L = 20 + 30 * abs(math.sin(i * 1.7 + t * (9 if fast else 3)))
                d.line([(x - 36 + i * 1.8, y), (x - 36 + i * 1.8 + L, y)], fill=(150, 220, 255, 255), width=3)


def draw_monitor(d, im, kind, t, value=0.0, flash=0.0):
    ink = INK + (255,)
    x0, y1 = MON_X - MON_W / 2, DESK_TOP - 22
    y0 = y1 - MON_H
    d.rectangle([MON_X - 10, y1, MON_X + 10, DESK_TOP], fill=(54, 54, 58, 255))
    d.rectangle([MON_X - 40, DESK_TOP - 6, MON_X + 40, DESK_TOP], fill=(54, 54, 58, 255))
    d.rounded_rectangle([x0 - 8, y0 - 8, x0 + MON_W + 8, y1 + 8], 8, fill=(40, 42, 48, 255), outline=ink, width=3)
    sc = (18, 26, 44)
    if kind == "red":
        sc = PW.lerp_c((90, 14, 16), (150, 24, 24), flash)
    if kind == "done":
        sc = (14, 46, 30)
    d.rectangle([x0, y0, x0 + MON_W, y1], fill=sc + (255,))
    fb = font("InterDisplay-Bold.otf", 34)
    fs = font(MONO, 15)
    if kind == "code":
        for i in range(7):
            y = y0 + 14 + i * 16
            L = 40 + 110 * abs(math.sin(i * 2.3 + int(t * 6) * 0.7))
            d.line([(x0 + 14 + (i % 3) * 10, y), (x0 + 14 + (i % 3) * 10 + L, y)], fill=(110, 170, 230, 255), width=4)
    elif kind == "ai":
        on = 0.55 + 0.45 * math.sin(t * 16)
        c = PW.lerp_c((60, 120, 200), (170, 225, 255), on)
        spaced(d, MON_X, y0 + 26, "AI IS", fb, c + (255,), 3)
        spaced(d, MON_X, y0 + 70, "HERE", fb, c + (255,), 3)
    elif kind == "chart":
        spaced(d, x0 + 46, y0 + 10, "AI SKILLS", fs, (150, 200, 240, 255), 1)
        n = 7
        for i in range(n):
            h = (14 + 80 * value * (i + 1) / n) * (0.85 + 0.15 * math.sin(t * 3 + i))
            bx = x0 + 18 + i * 26
            d.rectangle([bx, y1 - 10 - h, bx + 16, y1 - 10], fill=(90, 210, 140, 255))
        d.line([(x0 + 14, y1 - 10), (x0 + MON_W - 14, y1 - 10)], fill=(120, 140, 170, 255), width=2)
    elif kind == "tasks":
        spaced(d, MON_X, y0 + 12, "TASKS LEFT", fs, (240, 170, 150, 255), 2)
        spaced(d, MON_X, y0 + 44, str(int(value)), font("InterDisplay-Bold.otf", 54), (255, 150, 130, 255), 0)
    elif kind == "red":
        spaced(d, MON_X, y0 + 18, "YOUR ROLE WAS", font(MONO, 18), (255, 220, 220, 255), 2)
        spaced(d, MON_X, y0 + 54, "REPLACED", font("InterDisplay-Bold.otf", 32), (255, 255, 255, 255), 2)
    elif kind == "done":
        spaced(d, MON_X, y0 + 12, "TASKS LEFT", fs, (170, 240, 190, 255), 2)
        spaced(d, MON_X, y0 + 44, str(int(value)), font("InterDisplay-Bold.otf", 54), (140, 255, 170, 255), 0)


def draw_books(d, n, t):
    cols = [(220, 90, 70), (70, 140, 220), (240, 190, 70), (90, 190, 120), (170, 110, 210), (240, 140, 60),
            (80, 200, 220), (230, 230, 230)]
    y = DESK_TOP
    for i in range(n):
        h = 20
        w = 74 - (i % 3) * 6
        x = STACK_X - w / 2 + ((i * 7) % 9 - 4)
        d.rounded_rectangle([x, y - h, x + w, y], 3, fill=cols[i % len(cols)] + (255,), outline=INK + (255,), width=3)
        d.line([(x + 6, y - h / 2), (x + w - 6, y - h / 2)], fill=(255, 255, 255, 120), width=2)
        d.text((x + w / 2 - 9, y - h + 2), "AI", font=font("Inter-Bold.otf", 13), fill=(255, 255, 255, 230))
        y -= h


def draw_papers(d, h, t, fly=0.0):
    y = DESK_TOP
    rng = np.random.default_rng(11)
    n = int(h / 7)
    for i in range(n):
        ox = rng.uniform(-6, 6)
        w = 72
        x = STACK_X - w / 2 + ox
        d.rectangle([x, y - 7, x + w, y], fill=(232, 228, 216, 255), outline=(120, 116, 108, 255), width=1)
        y -= 7
    if n:
        d.line([(STACK_X - 30, y + 2), (STACK_X + 30, y + 2)], fill=(80, 80, 80, 255), width=2)


def draw_web(d, k, t):
    if k <= 0.01:
        return
    a = int(170 * k)
    cx, cy = W, FY - 300
    col = (210, 210, 220, a)
    ends = [(CORNER_X - 50, FY - 250), (CORNER_X - 70, FY - 170), (CORNER_X - 10, FY - 120), (CORNER_X + 30, FY - 60),
            (W - 140, FY - 300)]
    for ex, ey in ends:
        d.line([(cx, cy), (cx + (ex - cx) * k, cy + (ey - cy) * k)], fill=col, width=2)
    for r in (0.3, 0.55, 0.8):
        if k > r:
            pts = [(cx + (ex - cx) * r, cy + (ey - cy) * r) for ex, ey in ends]
            d.line(pts, fill=col, width=1)


# ---------------------------------------------------------------- who is where
def sit_pose_top(t):
    p = typing(SIT_TYPE, t)
    if 2.5 <= t < 3.45:
        p = SIT_LOOK
    return p


def top_people(t):
    """[(pts, body, far, facing, prop)] in the top room."""
    if t < T_UP:
        return [(place(sit_pose_top(t), HIP_SIT), DOER, DOER_FAR, 1, None)]
    if t < T_EXIT0:
        k = smooth(prog(t, T_UP, T_EXIT0))
        hip = (CHAIR_X + 20 * k, lerp(HIP_SIT[1], FY - 113 * SC, k))
        return [(place(lerp_pose(SIT_TYPE, HOLD_TAB, k), hip), DOER, DOER_FAR, 1, "tablet" if k > 0.5 else None)]
    if t < T_EXIT1:
        u = prog(t, T_EXIT0, T_EXIT1)
        x = lerp(CHAIR_X + 20, 1200, u)
        hip = (x, FY - 113 * SC - 5 * abs(math.sin(t * 9)))
        return [(place(walk(t * 9, HOLD_TAB), hip), DOER, DOER_FAR, 1, "tablet")]
    return []


def bot_people(t):
    out = []
    if t < T_OUT_UP:
        if 2.5 <= t < 3.6:
            p = SIT_LOOK
        elif T_PUSH0 <= t < T_PUSH1:
            p = SIT_SHOO
        elif t < 4.3:
            p = typing(SIT_TYPE, t)
        elif t < 14.45:
            k = smooth(prog(t, 4.3, 14.2))
            p = lerp_pose(typing(SIT_TYPE, t, 6, 4), SIT_SLUMP, 0.75 * k)
        else:
            p = SIT_LOOK
        out.append((place(p, HIP_SIT), OT, OT_FAR, 1, None))
    elif t < T_OUT0:
        k = smooth(prog(t, T_OUT_UP, T_OUT0))
        hip = (CHAIR_X - 10 * k, lerp(HIP_SIT[1], FY - 113 * SC, k))
        out.append((place(lerp_pose(SIT_LOOK, CARRY_BOX, k), hip, -1 if k > 0.5 else 1), OT, OT_FAR,
                    -1 if k > 0.5 else 1, "box" if k > 0.4 else None))
    elif t < T_OUT1:
        u = prog(t, T_OUT0, T_OUT1)
        x = lerp(CHAIR_X - 10, -170, u)
        hip = (x, FY - 113 * SC - 3 * abs(math.sin(t * 6.5)))
        p = walk(t * 6.5, CARRY_BOX)
        p["head"] = (p["head"][0] + 6, p["head"][1] + 8)        # head down
        out.append((place(p, hip, -1), OT, OT_FAR, -1, "box"))
    # the doer walks in
    if t >= T_IN0:
        u = prog(t, T_IN0, T_IN1)
        x = lerp(1200, 905, u)
        if t < T_IN1:
            hip = (x, FY - 113 * SC - 5 * abs(math.sin(t * 9)))
            out.append((place(walk(t * 9, HOLD_TAB), hip, -1), DOER, DOER_FAR, -1, "tablet"))
        else:
            hip = (x, FY - 113 * SC)
            p = dict(HOLD_TAB)
            if T_WAKE - 0.15 <= t < T_WAKE + 0.2:
                p["er"], p["hr"] = (24, -70), (46, -86)        # taps the tablet
            out.append((place(p, hip, -1), DOER, DOER_FAR, -1, "tablet"))
    return out


def top_robot(t):
    if t < T_ROLL0:
        return None
    if t < T_ROLL1:
        x = lerp(1200, ROBOT_DESK_X, out_cubic(prog(t, T_ROLL0, T_ROLL1)))
        return dict(x=x, facing=-1, eyes="open")
    if t < T_BOOK + 0.4:
        return dict(x=ROBOT_DESK_X, facing=-1, eyes="happy", wave=1.0 if t < 2.6 else 0.0,
                    arm=-1.2 * math.sin(math.pi * prog(t, T_BOOK - 0.2, T_BOOK + 0.3)))
    return dict(x=ROBOT_DESK_X, facing=-1, eyes="happy", typing_=1.0)


def bot_robot(t):
    if t < T_ROLL0:
        return None
    if t < T_ROLL1:
        x = lerp(1200, ROBOT_DESK_X, out_cubic(prog(t, T_ROLL0, T_ROLL1)))
        return dict(x=x, facing=-1, eyes="open")
    if t < T_PUSH0 + 0.1:
        return dict(x=ROBOT_DESK_X, facing=-1, eyes="happy", wave=1.0 if t < 2.6 else 0.0)
    if t < T_PUSH1:
        x = lerp(ROBOT_DESK_X, CORNER_X, out_cubic(prog(t, T_PUSH0 + 0.1, T_PUSH1)))
        return dict(x=x, facing=-1, eyes="sad")
    if t < T_WAKE:
        dust = 0.85 * smooth(prog(t, 4.5, 14.0))
        return dict(x=CORNER_X, facing=-1, eyes="sad" if t < 5.2 else "sleep", dust=dust)
    if t < T_RB0:
        k = 1 - smooth(prog(t, T_WAKE, T_WAKE + 0.4))
        return dict(x=CORNER_X + 3 * math.sin(t * 60) * (t < T_WAKE + 0.3), facing=-1, eyes="open", dust=0.85 * k)
    if t < T_RB1:
        x = lerp(CORNER_X, CHAIR_X + 40, smooth(prog(t, T_RB0, T_RB1)))
        return dict(x=x, facing=-1, eyes="open")
    return dict(x=CHAIR_X + 40, facing=1, eyes="happy", typing_=1.0)


def bot_papers(t):
    if t < T_D0:
        return 14.0
    if t < T_RB1 + 0.1:
        return 14 + 236 * smooth(prog(t, T_D0, T_D1))
    return 250 * (1 - smooth(prog(t, T_RB1 + 0.1, T_RB1 + 1.4)))


def bot_tasks(t):
    if t < T_RB1 + 0.1:
        return 12 + int(176 * smooth(prog(t, T_D0, T_D1)))
    return int(188 * (1 - smooth(prog(t, T_RB1 + 0.1, T_RB1 + 1.4))))


def head_of(people, who_body):
    for pts, body, far, f, prop in people:
        if body == who_body:
            return pts["head"]
    return None


# ---------------------------------------------------------------- bubbles (light, like the split-room reels)
_bub = {}


def bubble(s):
    if s in _bub:
        return _bub[s]
    f = font(MONO, 30)
    lw = f.getlength(s) + 2 * (len(s) - 1)
    pw, ph = int(lw + 40), 58
    k = 2
    im = Image.new("RGBA", (pw * k, (ph + 22) * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([3 * k, 3 * k, (pw - 3) * k, (ph - 3) * k], 12 * k, fill=(242, 240, 234, 255),
                        outline=INK + (255,), width=4 * k)
    tx = pw * 0.5
    d.polygon([((tx - 12) * k, (ph - 6) * k), ((tx + 12) * k, (ph - 6) * k), (tx * k, (ph + 18) * k)], fill=INK + (255,))
    d.polygon([((tx - 7) * k, (ph - 8) * k), ((tx + 7) * k, (ph - 8) * k), (tx * k, (ph + 9) * k)],
              fill=(242, 240, 234, 255))
    im = im.reduce(k)
    spaced(ImageDraw.Draw(im), pw / 2, 12, s, f, INK + (255,), 2)
    _bub[s] = im
    return im


def put_bubbles(panel, t, lst, people, robot):
    for b0, b1, s, who in lst:
        if not (b0 <= t < b1):
            continue
        if who == "robot":
            if not robot:
                continue
            anchor = (robot["x"], FY - 290)
        else:
            head = head_of(people, DOER if who == "doer" else OT)
            if head is None:
                continue
            anchor = (head[0], head[1] - 52)
        bs = bubble(s)
        if who != "robot":
            anchor = (anchor[0] + bs.width / 2 - 70 if anchor[0] < W / 2 else anchor[0] - bs.width / 2 + 70, anchor[1])
        sc = out_back(prog(t, b0, b0 + 0.16))
        al = 1 - smooth(prog(t, b1 - 0.1, b1))
        if sc < 0.05:
            continue
        spr = bs.resize((max(1, int(bs.width * sc)), max(1, int(bs.height * sc))), Image.LANCZOS)
        if al < 0.999:
            spr.putalpha(spr.split()[3].point(lambda v: int(v * al)))
        x = clamp(anchor[0] - spr.width / 2, 16, W - 16 - spr.width)
        y = max(4, anchor[1] - spr.height)
        panel.alpha_composite(spr, (int(x), int(y)))


def salary_box(d, panel, value, t, last_change, red=False, plus=None):
    x0, y0, bw, bh = 40, 18, 300, 92
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], 8, fill=(22, 24, 30, 235), outline=(90, 94, 104, 255), width=2)
    spaced(d, x0 + bw / 2, y0 + 10, "SALARY", font("Inter-SemiBold.otf", 22), (190, 194, 204, 255), 6)
    pop = math.exp(-(t - last_change) * 9) if last_change > 0 and t >= last_change else 0.0
    col = RED if red else PW.lerp_c(GOLD, (255, 250, 210), pop)
    fv = font(MONO, int(40 * (1 + 0.18 * pop)))
    spaced(d, x0 + bw / 2, y0 + 40 - 6 * pop, f"${value:,}", fv, col + (255,), 1)
    if plus and plus[0] <= t < plus[0] + 1.4:
        u = prog(t, plus[0], plus[0] + 1.4)
        a = int(255 * (1 - smooth(prog(u, 0.6, 1.0))))
        spaced(d, x0 + bw + 100, y0 + 34 - 30 * out_cubic(u), plus[1], font(MONO, 34), GREEN + (a,), 1)


def change_time(fn, t, back=0.5):
    v = fn(t)
    s = t
    while s > t - back:
        s -= 1 / FPS
        if fn(s) != v:
            return s + 1 / FPS
    return -9


# ---------------------------------------------------------------- one frame
ROOM = None
FRAME0 = None


def panel_frame(t, top):
    im = ROOM.copy()
    d = ImageDraw.Draw(im)
    draw_furniture(d)
    if top:
        # the doer's side
        if t < T_AI:
            kind = "code"
        elif t < T_ROLL1 + 0.3:
            kind = "ai"
        else:
            kind = "chart"
        draw_monitor(d, im, kind, t, value=smooth(prog(t, T_D0, T_D1)) if kind == "chart" else 0)
        nb = sum(1 for bt in BOOK_T if t >= bt)
        draw_books(d, nb, t)
        # the book the robot hands over
        if T_BOOK <= t < T_BOOK + 0.4:
            u = prog(t, T_BOOK, T_BOOK + 0.4)
            bx = lerp(ROBOT_DESK_X - 70, STACK_X, u)
            by = lerp(FY - 150, DESK_TOP - 10, u) - 120 * math.sin(math.pi * u)
            d.rounded_rectangle([bx - 36, by - 10, bx + 36, by + 10], 3, fill=(220, 90, 70, 255), outline=INK + (255,),
                                width=3)
        robot = top_robot(t)
        draw_laptop(d, (TABLE_X0 + TABLE_X1) / 2, robot is not None and t > T_BOOK + 0.3, t > T_BOOK + 0.3, t)
        people = top_people(t)
        salary_box(d, im, top_salary(t), t, change_time(top_salary, t), plus=(T_RAISE, "+$4,000"))
        bl = BUBBLES_TOP
    else:
        if t < T_AI:
            kind, val = "code", 0
        elif t < T_ROLL1 + 0.3:
            kind, val = "ai", 0
        elif t < 14.45:
            kind, val = "tasks", bot_tasks(t)
        elif t < T_RB1 + 0.1:
            kind, val = "red", 0
        else:
            kind, val = "done", bot_tasks(t)
        draw_monitor(d, im, kind, t, value=val, flash=0.5 + 0.5 * math.sin(t * 18))
        draw_papers(d, bot_papers(t), t)
        robot = bot_robot(t)
        draw_laptop(d, (TABLE_X0 + TABLE_X1) / 2, False, False, t)
        web = smooth(prog(t, 4.6, 13.5)) * (1 - smooth(prog(t, T_WAKE, T_WAKE + 0.2)))
        draw_web(d, web, t)
        people = bot_people(t)
        salary_box(d, im, bot_salary(t), t, change_time(bot_salary, t), red=bot_salary(t) == 0)
        bl = BUBBLES_BOT
    if robot:
        spr, off = robot_sprite(robot["x"], t, robot["facing"], robot["eyes"], robot.get("arm", 0.0),
                                robot.get("dust", 0.0), robot.get("wave", 0.0), robot.get("typing_", 0.0))
        im.alpha_composite(spr, off)
        if not top and robot.get("dust", 0) > 0.3 and t < T_WAKE:
            # zZ over the sleeping robot
            for i in range(2):
                ph = (t * 0.8 + i * 0.5) % 1.0
                a = int(200 * math.sin(math.pi * ph))
                d2 = ImageDraw.Draw(im)
                d2.text((CORNER_X - 20 + 30 * ph + i * 14, FY - 300 - 60 * ph), "z",
                        font=font("Inter-Bold.otf", 24 + 8 * i), fill=(200, 210, 230, a))
    for pts, body, far, f, prop in people:
        spr, off = person_sprite(pts, body, far, f, prop)
        if body == DOER:
            im.alpha_composite(PW.glow_of(spr, 0.5, 12), off)
        im.alpha_composite(spr, off)
    put_bubbles(im, t, bl, people, robot)
    return im


def frame(t):
    img = Image.new("RGBA", (W, H), (6, 6, 8, 255))
    img.alpha_composite(panel_frame(t, True), (0, TOP_Y0))
    img.alpha_composite(panel_frame(t, False), (0, BOT_Y0))
    d = ImageDraw.Draw(img)
    spaced(d, W / 2, 268, "DOER", font("Inter-SemiBold.otf", 40), (236, 238, 244, 255), 10)
    spaced(d, W / 2, BOT_Y0 + PH + 18, "OVERTHINKER", font("Inter-SemiBold.otf", 40), (200, 204, 214, 255), 10)
    spaced(d, W / 2, TOP_Y0 + PH + 18, "SAME JOB", font("Inter-SemiBold.otf", 34), (206, 210, 220, 255), 8)
    day = day_at(t)
    dpop = math.exp(-(t - T_365) * 6) if t >= T_365 else 0.0
    fl = font("Inter-SemiBold.otf", 40)
    fn = font("InterDisplay-Bold.otf", int(56 * (1 + 0.3 * dpop)))
    wl = sum(fl.getlength(c) for c in "DAY") + 16
    wn = fn.getlength(str(day))
    x0 = W / 2 - (wl + 20 + wn) / 2
    spaced(d, x0 + wl / 2, TOP_Y0 + PH + 66, "DAY", fl, (206, 210, 220, 255), 8)
    d.text((x0 + wl + 20, TOP_Y0 + PH + 52 - 8 * dpop), str(day), font=fn,
           fill=PW.lerp_c((250, 250, 252), (255, 120, 110), dpop) + (255,))
    d.line([(60, BOT_Y0 - 8), (W - 60, BOT_Y0 - 8)], fill=(50, 52, 60, 255), width=2)
    # the line, typed at the top
    fm = font(MONO, 50)
    for t0, s, y, col in ((T_L1, LINE1, 92, (250, 250, 252)), (T_L2, LINE2, 164, CYAN)):
        if t < t0:
            continue
        n = int(clamp((t - t0) * CPS, 0, len(s)))
        full = sum(fm.getlength(c) for c in s) + 3 * (len(s) - 1)
        x = W / 2 - full / 2
        for c in s[:n]:
            d.text((x, y), c, font=fm, fill=col + (255,))
            x += fm.getlength(c) + 3
        typing_now = n < len(s) or (s == LINE2 and t < t0 + len(s) / CPS + 1.0)
        if typing_now and int(t * 3.4) % 2 == 0:
            d.rectangle([x + 2, y + 6, x + 26, y + 56], fill=col + (220,))
    return np.asarray(img.convert("RGB"))


def init_worker():
    global ROOM
    ROOM = build_room()


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
def audio():
    n = int(DUR * SR)
    mus, fx = np.zeros((n, 2)), np.zeros((n, 2))
    # warm lo-fi loop for the year (bars 0-5): Fmaj7 - Em7 - Dm7 - Cmaj7
    chords = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]]
    roots = [41, 40, 38, 36]
    for b in range(6):
        t0 = b * BAR
        ch, rt = chords[b % 4], roots[b % 4]
        beats = 4 if b < 5 else 4
        for k, m in enumerate(ch):
            mix_in(mus, tone(midi(m), BAR + 0.1, (1, 0.35, 0.12, 0.05), a=0.02, d=1.2), t0, 0.05, (k - 1.5) * 0.35)
        for q in range(beats):
            tb = t0 + q * BEAT
            mix_in(mus, tone(105, 0.32, (1,), a=0.002, d=0.11, sweep=42), tb, 0.55 if q % 2 == 0 else 0.3)
            mix_in(mus, tone(midi(rt), BEAT * 0.9, (1, 0.4, 0.1), a=0.005, d=0.3), tb, 0.2)
            if q % 2 == 1:
                mix_in(mus, noise(0.12, 900 + b * 4 + q, lo=900, hi=5000) * env(int(0.12 * SR), 0.001, 0.03), tb, 0.14)
            for e in range(2):
                mix_in(mus, noise(0.04, 300 + b * 8 + q * 2 + e, lo=6000) * env(int(0.04 * SR), 0.0005, 0.008),
                       tb + e * BEAT / 2, 0.045, 0.4 - 0.8 * e)
            if (b * 4 + q) % 3 != 2:
                m = ch[(q * 2 + b) % 4] + 12
                mix_in(mus, tone(midi(m), 0.5, (1, 0.25, 0.08), a=0.004, d=0.18), tb + BEAT / 2, 0.065, 0.2)
    # day 365: the beat drops out, an alarm, a low drone; then the doer's theme returns for the line
    for i in range(4):
        mix_in(fx, tone(880 if i % 2 == 0 else 660, 0.16, (1, 0.5, 0.25), a=0.003, d=0.1), 14.45 + i * 0.2, 0.12)
    tt = np.arange(int(4.6 * SR)) / SR
    mix_in(mus, (np.sin(2 * np.pi * 55 * tt) + 0.4 * np.sin(2 * np.pi * 110 * tt)) * np.minimum(1, tt / 0.5)
           * np.clip((4.6 - tt) / 0.6, 0, 1), 14.4, 0.12)
    for b in range(4):
        t0 = 7 * BAR + b * BAR
        ch, rt = chords[(b + 2) % 4], roots[(b + 2) % 4]
        for k, m in enumerate(ch):
            mix_in(mus, tone(midi(m), BAR + 0.3, (1, 0.3, 0.1), a=0.2, d=1.5), t0, 0.06, (k - 1.5) * 0.4)
        mix_in(mus, tone(midi(rt), BAR, (1, 0.3), a=0.08, d=1.2), t0, 0.17)
        for q in range(4):
            mix_in(mus, tone(105, 0.3, (1,), a=0.002, d=0.1, sweep=42), t0 + q * BEAT, 0.35 if q % 2 == 0 else 0.2)
    # robots: rolling hum, beeps
    for side in (-0.3, 0.3):
        tr = np.arange(int(1.0 * SR)) / SR
        mix_in(fx, np.sin(2 * np.pi * np.cumsum(140 + 40 * tr) / SR) * np.minimum(1, tr / 0.1) * np.clip((1 - tr) / 0.3, 0, 1),
               T_ROLL0, 0.05, side)
    for i, m in enumerate((84, 88, 91)):
        mix_in(fx, tone(midi(m), 0.09, (1, 0.3), a=0.002, d=0.05), 1.95 + i * 0.08, 0.1)
    mix_in(fx, tone(midi(76), 0.25, (1, 0.3), a=0.002, d=0.15, sweep=midi(64)), T_PUSH1 - 0.3, 0.1, 0.3)  # sad beep
    for i, m in enumerate((79, 86, 91, 96)):
        mix_in(fx, tone(midi(m), 0.08, (1, 0.3), a=0.002, d=0.04), T_WAKE + i * 0.06, 0.12, 0.3)
    # salary up: a coin
    for t0, s in TOP_SAL[1:]:
        for i, m in enumerate((88, 95)):
            mix_in(fx, tone(midi(m), 0.4, (1, 0.3), a=0.002, d=0.16), t0 + i * 0.07, 0.07, -0.3)
    # salary zero: a sad down step
    for i, m in enumerate((67, 63, 60)):
        mix_in(fx, tone(midi(m), 0.35, (1, 0.4, 0.2), a=0.004, d=0.2), T_ZERO + i * 0.14, 0.12, 0.3)
    # robot types fast; keyboard ticks for the people
    r = np.random.default_rng(5)
    for tk in np.arange(0.1, 14.4, 0.11):
        mix_in(fx, noise(0.02, int(tk * 1000), lo=2500, hi=9000) * env(int(0.02 * SR), 0.0005, 0.004), tk
               + r.uniform(0, 0.03), 0.03, r.uniform(-0.5, 0.5))
    for tk in np.arange(T_RB1, T_RB1 + 1.4, 0.035):
        mix_in(fx, noise(0.02, int(tk * 1000) + 7, lo=2500, hi=9000) * env(int(0.02 * SR), 0.0005, 0.004), tk, 0.06, 0.2)
    for i in range(6):
        mix_in(fx, tone(midi(72 + i * 2), 0.07, (1,), a=0.002, d=0.04), T_RB1 + 1.4 + i * 0.05, 0.05, 0.2)
    # bubbles, the book, the typewriter line
    for lst in (BUBBLES_TOP, BUBBLES_BOT):
        for b0, b1, s, who in lst:
            mix_in(fx, tone(560, 0.11, (1, 0.3), a=0.002, d=0.05, sweep=1100), b0, 0.1, 0.0)
    mix_in(fx, noise(0.12, 77, lo=600, hi=4000) * env(int(0.12 * SR), 0.002, 0.04), T_BOOK + 0.4, 0.18)
    for t0, s in ((T_L1, LINE1), (T_L2, LINE2)):
        for i, c in enumerate(s):
            if c != " ":
                mix_in(fx, noise(0.03, 500 + i + int(t0), lo=2000, hi=8000) * env(int(0.03 * SR), 0.0005, 0.006),
                       t0 + i / CPS, 0.12)
    x = mus * 0.9 + fx
    m = int(XFADE * SR)
    k = np.linspace(0, 1, m)[:, None]
    x[-m:] = x[-m:] * (1 - k) + x[:m] * k
    x /= max(1.0, np.abs(x).max() / 0.9)
    return x


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "ai-job.mp4"
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
                          "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "slow", "-crf", "18",
                          "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100",
                          "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                         stdin=subprocess.PIPE)
    with Pool(os.cpu_count(), initializer=init_worker) as pool:
        for i, b in enumerate(pool.imap(render, range(NF), chunksize=4)):
            p.stdin.write(b)
            if i % 120 == 0:
                print(f"{i}/{NF}", flush=True)
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print(out)


if __name__ == "__main__":
    main()
