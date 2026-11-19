#!/usr/bin/env python3
"""SHARPEN THE AXE - Keeps Chopping vs Stops to Sharpen, two lanes and one counter (the "too busy to fix the wheel"
reels), 22.4 s, loops on itself.

Both chop with the same dull axe: TINK, sparks, a scratch in the bark. The one below stops ("IT'S DULL."), sits on
the stump and sharpens; TREES CUT 1 : 0, 2 : 0 ("NO TIME TO SHARPEN."). He stands up, the edge flashes ("READY."),
and two clean chops drop a tree: he catches up and passes, 4 : 7 at the end, while the one above sweats over the same
dull axe ("I'M TOO BUSY.") next to the stump and the stone he never used. The top lane is grey, the lower one in
colour, the floor a dark mirror.
"HE WAS TOO BUSY CHOPPING / TO SHARPEN THE AXE."

    python3 stick/sharpen_axe.py stick/sharpen-axe.mp4
    ONLY_FRAMES=0,0.7,1.5,4,6.6,8.4,14.5,20 python3 stick/sharpen_axe.py /tmp/sa   (PNG stills)
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
import game_spend as GS  # noqa  (the calm pad and keys)
from perfect_wave import (MONO, clamp, env, font, in_quad, lerp, lerp_pose, midi, mix_in, noise, out_back,  # noqa
                          out_cubic, prog, smooth, spaced, tone, write_wav)

W, H, FPS = 1080, 1920, 30
SR = 44100
BPM = 75
BEAT = 60 / BPM
BAR = 4 * BEAT                          # 3.2 s
DUR = 7 * BAR                           # 22.4 s
NF = int(round(DUR * FPS))
XFADE = 0.5
SC = AJ.SC
INK = AJ.INK

# ---------------------------------------------------------------- layout
LANE_H = 700                            # a lane is drawn on its own layer, floor at LF
LF = 620
FLOORS = {"top": 950, "bot": 1420}
CHAR_X = 430
TREE_X = 704
STUMP_X = 280
PILE_X = 46
HIP_Y = LF - 113 * SC

# ---------------------------------------------------------------- the chopping
TOP_PERIOD, TOP_PER_TREE = 0.95, 5      # dull: five chops for a tree
BOT_PERIOD = 0.68                       # sharp: two chops and a breath (three cycles) a tree
BOT_START = 7.4
CONTACT = 0.72                          # where in the cycle the axe meets the trunk
T_STOP, T_LOOK1 = 0.95, 1.8             # below: stops, looks at the edge
T_WALK0, T_WALK1 = 1.8, 2.4
T_SH0, T_SH1 = 2.4, 6.3                 # sharpening on the stump
T_UP1 = 6.6                             # stands, the edge flashes
T_BACK1 = 7.1
T_L1, T_L2 = 15.6, 17.3
CPS = 16.0
LINE1, LINE2 = "HE WAS TOO BUSY CHOPPING", "TO SHARPEN THE AXE."

BUB_TOP = [(2.6, 4.7, "NO TIME TO SHARPEN."), (11.2, 13.3, "I'M TOO BUSY.")]
BUB_BOT = [(1.15, 2.9, "IT'S DULL."), (6.55, 7.9, "READY.")]


def top_contacts():
    out, k = [], 0
    while True:
        tc = k * TOP_PERIOD + CONTACT * TOP_PERIOD
        if tc > DUR + 2:
            return out
        out.append(tc)
        k += 1


def bot_contacts():
    out = [CONTACT * TOP_PERIOD]                        # the first, dull chop, together with the other one
    k = 0
    while True:
        tc = BOT_START + k * BOT_PERIOD + CONTACT * BOT_PERIOD
        if tc > DUR + 2:
            return out
        if k % 3 != 2:
            out.append(tc)
        k += 1


TOP_C = top_contacts()
BOT_C = bot_contacts()
TOP_FALLS = [tc for i, tc in enumerate(TOP_C) if i % TOP_PER_TREE == TOP_PER_TREE - 1]
# below: the dull chop counts as a scratch; then every second sharp chop drops a tree
BOT_FALLS = [tc for i, tc in enumerate(BOT_C[1:]) if i % 2 == 1]


def count(falls, t):
    return sum(1 for f in falls if t >= f + 0.6)


def notch(lane, t):
    """How deep the cut in the current tree is (0..1)."""
    if lane == "top":
        done = [c for c in TOP_C if c <= t]
        if not done:
            return 0.0
        i = len(done) - 1
        if TOP_C[i] in TOP_FALLS:
            return 1.0
        return (i % TOP_PER_TREE + 1) / TOP_PER_TREE * 0.75
    done = [c for c in BOT_C if c <= t]
    if not done:
        return 0.0
    i = len(done) - 1
    if i == 0:
        return 0.1
    if BOT_C[i] in BOT_FALLS:
        return 1.0
    return 0.5


def last_fall(falls, t):
    lf = None
    for f in falls:
        if f <= t:
            lf = f
    return lf


# ---------------------------------------------------------------- poses (facing right, from the hip)
LEGS = {"kl": (-24, 56), "fl": (-38, 113), "kr": (24, 56), "fr": (38, 113)}
RAISE = dict(LEGS, head=(-6, -150), neck=(-4, -108), el=(-30, -140), hl=(-40, -180), er=(-24, -136), hr=(-34, -176))
STRIKE = {"head": (16, -142), "neck": (12, -100), "el": (44, -70), "hl": (78, -62), "er": (40, -66), "hr": (72, -58),
          "kl": (-20, 58), "fl": (-40, 113), "kr": (34, 52), "fr": (48, 113)}
TIRED = dict(STRIKE, head=(26, -128), neck=(18, -90))
LOOK = dict(LEGS, head=(4, -150), neck=(2, -108), el=(30, -120), hl=(46, -150), er=(26, -116), hr=(42, -146))
CARRY = dict(PW.STAND, el=(4, -58), hl=(16, -10))
SIT = AJ.SIT_TYPE
SHARPEN = dict(SIT, el=(30, -56), hl=(56, -40), er=(40, -60), hr=(90, -48))
A_RAISE, A_STRIKE = -2.3, 0.12


def swing(t, period, t0, dull, tired=0.0):
    """Pose and axe angle for a chop cycle started at t0."""
    u = ((t - t0) / period) % 1.0
    if u < 0.5:
        k = smooth(u / 0.5)
        pose, ang = lerp_pose(STRIKE, RAISE, k), lerp(A_STRIKE, A_RAISE, k)
    elif u < 0.62:
        pose, ang = RAISE, A_RAISE
    elif u < CONTACT:
        k = in_quad((u - 0.62) / (CONTACT - 0.62))
        pose, ang = lerp_pose(RAISE, STRIKE, k), lerp(A_RAISE, A_STRIKE, k)
    else:
        pose, ang = STRIKE, A_STRIKE
        if dull:                                         # the dull axe bounces back
            r = math.sin(math.pi * clamp((u - CONTACT) / 0.16))
            pose, ang = lerp_pose(STRIKE, RAISE, 0.22 * r), lerp(A_STRIKE, A_RAISE, 0.22 * r)
    if tired > 0:
        pose = lerp_pose(pose, dict(pose, head=(pose["head"][0] + 10, pose["head"][1] + 12),
                                    neck=(pose["neck"][0] + 6, pose["neck"][1] + 8)), tired)
    return pose, ang


def person(lane, t):
    """(pose, hip, facing, axe angle or None, axe mode, extra)"""
    hip = (CHAR_X, HIP_Y)
    if lane == "top":
        pose, ang = swing(t, TOP_PERIOD, 0.0, True, tired=smooth(prog(t, 6.0, 16.0)))
        return pose, hip, 1, ang, "hands"
    if t < T_STOP:
        pose, ang = swing(t, TOP_PERIOD, 0.0, True)
        return pose, hip, 1, ang, "hands"
    if t < T_LOOK1:
        k = smooth(prog(t, T_STOP, T_STOP + 0.35))
        return lerp_pose(STRIKE, LOOK, k), hip, 1, lerp(A_STRIKE, -1.45, k), "hands"
    if t < T_WALK1:
        u = prog(t, T_WALK0, T_WALK1)
        x = lerp(CHAR_X, STUMP_X + 20, smooth(u))
        p = AJ.walk(t * 7, CARRY)
        return p, (x, HIP_Y - 4 * abs(math.sin(t * 7))), -1, 1.75, "carry"
    if t < T_SH0 + 0.3:
        k = smooth(prog(t, T_WALK1, T_SH0 + 0.3))
        return lerp_pose(PW.STAND, SHARPEN, k), (STUMP_X + 20, lerp(HIP_Y, LF - 115 * SC, k)), 1, 0.0, "lap"
    if t < T_SH1:
        return SHARPEN, (STUMP_X + 20, LF - 115 * SC), 1, 0.0, "lap"
    if t < T_UP1:
        k = smooth(prog(t, T_SH1, T_UP1))
        return lerp_pose(SHARPEN, LOOK, k), (STUMP_X + 20, lerp(LF - 115 * SC, HIP_Y, k)), 1, lerp(0.0, -1.45, k), "hands"
    if t < T_UP1 + 0.3:
        return LOOK, (STUMP_X + 20, HIP_Y), 1, -1.45, "hands"
    if t < BOT_START:
        u = prog(t, T_UP1 + 0.3, BOT_START)
        x = lerp(STUMP_X + 20, CHAR_X, smooth(u))
        p = AJ.walk(t * 7, dict(CARRY, el=(30, -120), hl=(46, -150)))
        return p, (x, HIP_Y - 4 * abs(math.sin(t * 7))), 1, -1.45, "hands"
    k = (t - BOT_START) / BOT_PERIOD
    if int(k) % 3 == 2:                                   # a breath while the tree goes down
        u = k % 1.0
        pose = lerp_pose(STRIKE, RAISE, 0.35 * math.sin(math.pi * u))
        return pose, hip, 1, lerp(A_STRIKE, A_RAISE, 0.35 * math.sin(math.pi * u)), "hands"
    pose, ang = swing(t, BOT_PERIOD, BOT_START, False)
    return pose, hip, 1, ang, "hands"


def sharpness(t):
    return smooth(prog(t, T_SH0 + 0.4, T_SH1)) if t < BOT_START + 30 else 1.0


# ---------------------------------------------------------------- drawing
def draw_axe(cv, hand, ang, sharp, grey, glint=0.0):
    ink = INK + (255,)
    P = cv.P
    k = AJ.SS
    dx, dy = math.cos(ang), math.sin(ang)
    a = (hand[0] - 22 * dx, hand[1] - 22 * dy)
    b = (hand[0] + 135 * dx, hand[1] + 135 * dy)
    wood = (150, 150, 150) if grey else (170, 118, 70)
    cv.d.line([P(a), P(b)], fill=ink, width=int(15 * k))
    cv.d.line([P(a), P(b)], fill=wood + (255,), width=int(8 * k))
    # the head: a wedge at the tip, its edge facing forward along the handle
    nx, ny = -dy, dx
    tip = b
    pts = [(-10, -16), (12, -16), (30, -26), (34, 0), (30, 26), (12, 16), (-10, 16)]
    if sharp < 0.5:                                       # a chipped, blunt edge
        pts = [(-10, -16), (12, -16), (24, -22), (28, -10), (24, -2), (29, 8), (24, 20), (12, 16), (-10, 16)]
    poly = [(tip[0] + px * dx + py * nx, tip[1] + px * dy + py * ny) for px, py in pts]
    metal = PW.lerp_c((112, 112, 118), (222, 226, 236), sharp)
    if grey:
        metal = (118, 118, 122)
    cv.d.polygon([P(p) for p in poly], fill=metal + (255,), outline=ink)
    cv.d.line([P(p) for p in poly] + [P(poly[0])], fill=ink, width=int(4 * k), joint="curve")
    if sharp > 0.5 and not grey:
        e0 = (tip[0] + 30 * dx - 22 * nx, tip[1] + 30 * dy - 22 * ny)
        e1 = (tip[0] + 33 * dx, tip[1] + 33 * dy)
        e2 = (tip[0] + 30 * dx + 22 * nx, tip[1] + 30 * dy + 22 * ny)
        cv.d.line([P(e0), P(e1), P(e2)], fill=(255, 255, 255, int(255 * sharp)), width=int(3 * k))
    if glint > 0.01:
        gx, gy = tip[0] + 32 * dx, tip[1] + 32 * dy
        r = 34 * glint
        cv.d.line([P((gx - r, gy)), P((gx + r, gy))], fill=(255, 255, 255, int(255 * glint)), width=int(4 * k))
        cv.d.line([P((gx, gy - r)), P((gx, gy + r))], fill=(255, 255, 255, int(255 * glint)), width=int(4 * k))
    return tip


def person_sprite(lane, t):
    pose, hip, facing, ang, mode = person(lane, t)
    pts = AJ.place(pose, hip, facing)
    grey = lane == "top"
    body, far = (AJ.OT, AJ.OT_FAR) if grey else (AJ.DOER, AJ.DOER_FAR)
    cv = AJ.Canvas(*PW.bbox_of(list(pts.values()), 230))
    sharp = 0.0 if grey else sharpness(t)
    glint = 0.0
    if not grey and T_SH1 <= t < T_UP1 + 0.6:
        glint = math.sin(math.pi * prog(t, T_UP1 - 0.05, T_UP1 + 0.55))
    if mode == "lap":
        hand = pts["hl"]
        AJ.draw_stick(cv, pts, body, far, facing)
        draw_axe(cv, (hand[0] - 70, hand[1] + 6), 0.0, sharp, grey)
        # the whetstone in the other hand, rubbing along the edge
        sx = hand[0] + 76 + 14 * math.sin(t * 7)
        sy = hand[1] - 2
        q0, q1 = cv.P((sx - 18, sy - 9)), cv.P((sx + 18, sy + 9))
        cv.d.rounded_rectangle([q0[0], q0[1], q1[0], q1[1]], 5 * AJ.SS, fill=(96, 110, 124, 255), outline=INK + (255,),
                               width=3 * AJ.SS)
        AJ.disc(cv, (sx, sy - 4), 11 * SC + 6 * SC, INK + (255,))
        AJ.disc(cv, (sx, sy - 4), 11 * SC, body + (255,))
    else:
        hand = pts["hl"] if mode == "hands" else pts["hl"]
        AJ.draw_stick(cv, pts, body, far, facing)
        draw_axe(cv, hand, ang if facing > 0 else math.pi - ang, sharp, grey, glint)
        for hn in ("hl", "hr") if mode == "hands" else ("hl",):
            AJ.disc(cv, pts[hn], 11 * SC + 6 * SC, INK + (255,))
            AJ.disc(cv, pts[hn], 11 * SC, body + (255,))
    spr, off = cv.done()
    return spr, off, pts


def tree_img(grey, notch_k):
    """A tree on its own layer: trunk 64 wide, 260 tall, a round crown; (0,0) of the layer is the trunk's base left."""
    im = Image.new("RGBA", (720 * 2, 440 * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    k = 2
    ink = INK + (255,)
    ox, oy = 118, 410                                     # base left of the trunk in the layer
    bark = (128, 128, 130) if grey else (124, 84, 52)
    crown = [(108, 110, 114), (92, 94, 98)] if grey else [(70, 150, 80), (52, 122, 64)]
    for cx, cy, r in ((32, -300, 96), (-34, -270, 64), (96, -262, 62), (30, -230, 70)):
        d.ellipse([(ox + cx - r - 5) * k, (oy + cy - r - 5) * k, (ox + cx + r + 5) * k, (oy + cy + r + 5) * k], fill=ink)
    for i, (cx, cy, r) in enumerate(((32, -300, 96), (-34, -270, 64), (96, -262, 62), (30, -230, 70))):
        d.ellipse([(ox + cx - r) * k, (oy + cy - r) * k, (ox + cx + r) * k, (oy + cy + r) * k], fill=crown[i % 2] + (255,))
    d.rectangle([ox * k, (oy - 250) * k, (ox + 64) * k, oy * k], fill=bark + (255,), outline=ink, width=5 * k)
    for i in range(5):
        y = oy - 40 - i * 44
        d.line([((ox + 14) * k, y * k), ((ox + 24) * k, (y - 18) * k)], fill=ink, width=3 * k)
        d.line([((ox + 44) * k, (y - 10) * k), ((ox + 52) * k, (y - 26) * k)], fill=ink, width=3 * k)
    if notch_k > 0:
        dep = 44 * notch_k
        cy = oy - 120
        d.polygon([(ox * k, (cy - 14 - dep * 0.5) * k), ((ox + dep) * k, cy * k), (ox * k, (cy + 14) * k)],
                  fill=(232, 200, 150, 255) if not grey else (190, 190, 190, 255), outline=ink)
    return im.reduce(2), (ox, oy)


def draw_tree(lane_im, lane, t):
    grey = lane == "top"
    falls = TOP_FALLS if lane == "top" else BOT_FALLS
    lf = last_fall(falls, t)
    x0 = TREE_X - 32
    if lf is not None and t < lf + 0.93:
        # the old tree falls away to the right, then fades; the new one grows in behind it
        u = prog(t, lf, lf + 0.6)
        ang = 88 * in_quad(u)
        al = 1 - smooth(prog(t, lf + 0.66, lf + 0.86))
        im, (ox, oy) = tree_img(grey, 1.0)
        piv = (ox + 64, oy - 120)
        upper = im.copy()
        upper.paste((0, 0, 0, 0), (0, oy - 120, im.width, im.height))
        im_top = upper
        top = im_top.rotate(-ang, center=piv, resample=Image.BICUBIC)
        if al < 0.999:
            top.putalpha(top.split()[3].point(lambda v: int(v * al)))
        # the stump stays
        stump = im.crop((0, oy - 120, im.width, im.height))
        nk = smooth(prog(t, lf + 0.74, lf + 0.92))
        if nk > 0.01:
            nw, (nox, noy) = tree_img(grey, notch(lane, t) if t > lf + 0.92 else 0.0)
            nw = nw.resize((nw.width, nw.height))
            nw.putalpha(nw.split()[3].point(lambda v: int(v * nk)))
            lane_im.alpha_composite(nw, (int(x0 - nox), int(LF - noy)))
        lane_im.alpha_composite(top, (int(x0 - ox), int(LF - oy)))
        if nk < 0.99:
            st = stump.copy()
            st.putalpha(st.split()[3].point(lambda v: int(v * (1 - nk))))
            lane_im.alpha_composite(st, (int(x0 - ox), int(LF - 120)))
        return
    nk = notch(lane, t)
    im, (ox, oy) = tree_img(grey, nk)
    lane_im.alpha_composite(im, (int(x0 - ox), int(LF - oy)))


def draw_stump(d, grey):
    ink = INK + (255,)
    col = (120, 120, 122) if grey else (130, 92, 58)
    top_y = LF - 128
    d.rectangle([STUMP_X - 44, top_y, STUMP_X + 44, LF], fill=col + (255,), outline=ink, width=4)
    d.ellipse([STUMP_X - 44, top_y - 14, STUMP_X + 44, top_y + 14], fill=PW.lerp_c(col, (220, 200, 160), 0.5 if not grey
              else 0.2) + (255,), outline=ink, width=3)
    for r in (28, 16):
        d.ellipse([STUMP_X - r, top_y - r * 0.32, STUMP_X + r, top_y + r * 0.32], outline=ink, width=2)


def draw_stone(d, grey):
    ink = INK + (255,)
    d.rounded_rectangle([STUMP_X + 4, LF - 128 - 22, STUMP_X + 40, LF - 128 - 6], 4,
                        fill=((110, 110, 112) if grey else (96, 110, 124)) + (255,), outline=ink, width=3)


def draw_logs(d, n, grey):
    ink = INK + (255,)
    rows = [5, 4, 3, 2, 1]
    i = 0
    y = LF - 26
    for r, m in enumerate(rows):
        for j in range(m):
            if i >= n:
                return
            x = PILE_X + r * 24 + j * 48
            col = (150, 150, 152) if grey else (214, 168, 110)
            d.ellipse([x - 26, y - 26, x + 26, y + 26], fill=col + (255,), outline=ink, width=4)
            d.ellipse([x - 15, y - 15, x + 15, y + 15], outline=((110, 110, 110) if grey else (160, 112, 66)) + (255,),
                      width=3)
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=((110, 110, 110) if grey else (160, 112, 66)) + (255,))
            i += 1
        y -= 46


def particles(d, lane, t):
    contacts = TOP_C if lane == "top" else BOT_C
    for i, tc in enumerate(contacts):
        tau = t - tc
        if tau < 0 or tau > 0.9:
            continue
        dull = lane == "top" or i == 0
        rng = np.random.default_rng(int(tc * 1000) + (7 if lane == "top" else 3))
        x0, y0 = TREE_X - 34, LF - 120
        n = 10 if dull else 16
        for j in range(n):
            if dull:
                vx, vy = rng.uniform(-420, -120), rng.uniform(-520, -160)
                col = (255, 220, 120) if lane != "top" else (230, 230, 230)
                life = 0.35
            else:
                vx, vy = rng.uniform(-380, 160), rng.uniform(-560, -180)
                col = (236, 200, 150)
                life = 0.9
            if tau > life:
                continue
            x = x0 + vx * tau
            y = y0 + vy * tau + 0.5 * 1800 * tau * tau
            if y > LF - 3:
                y = LF - 3
            a = int(255 * (1 - tau / life))
            r = rng.uniform(2, 4) if dull else rng.uniform(3, 6)
            if dull:
                d.line([(x, y), (x - vx * 0.02, y - vy * 0.02)], fill=col + (a,), width=3)
            else:
                d.polygon([(x - r, y), (x, y - r * 0.6), (x + r, y), (x, y + r * 0.6)], fill=col + (a,))
    # sharpening sparks
    if lane == "bot" and T_SH0 + 0.3 <= t < T_SH1:
        rng = np.random.default_rng(int(t * 30))
        _, hip, _, _, _ = person("bot", t)
        sx = hip[0] + 56 * SC + 76 + 14 * math.sin(t * 7)
        sy = hip[1] - 40 * SC
        for j in range(5):
            x = sx + rng.uniform(-6, 24)
            y = sy + rng.uniform(-14, 4)
            dx, dy = rng.uniform(6, 20), rng.uniform(-14, 4)
            d.line([(x, y), (x + dx, y + dy)], fill=(255, 220, 130, int(rng.uniform(120, 240))), width=2)
    # wood chips that stay on the ground below
    if lane == "bot":
        rng = np.random.default_rng(99)
        nchips = int(60 * clamp(count(BOT_FALLS, t) / 7))
        for j in range(nchips):
            x = TREE_X - 140 + rng.uniform(-90, 90)
            d.polygon([(x - 4, LF - 2), (x, LF - 6), (x + 5, LF - 2)], fill=(214, 176, 126, 220))


def sweat(d, pts, t):
    k = smooth(prog(t, 9.0, 14.0))
    if k <= 0:
        return
    hx, hy = pts["head"]
    for i in range(2):
        ph = (t * 0.9 + i * 0.5) % 1.0
        x = hx - 30 - i * 10
        y = hy - 10 + 70 * ph
        a = int(220 * k * (1 - ph))
        d.polygon([(x, y - 9), (x - 6, y + 2), (x + 6, y + 2)], fill=(170, 210, 255, a))
        d.ellipse([x - 6, y - 3, x + 6, y + 8], fill=(170, 210, 255, a))


ROOM = {}
FRAME0 = None


def build_lane(lane):
    """A transparent lane: just its floor line (the light behind it is in the frame's background)."""
    im = Image.new("RGBA", (W, LANE_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.line([(0, LF), (W, LF)], fill=(54, 54, 58, 255), width=2)
    return im


def build_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img = np.zeros((H, W, 3), np.float32) + 5
    for lane, k, warm in (("top", 12, 0.0), ("bot", 18, 1.0)):
        fy = FLOORS[lane]
        g = np.exp(-(((xx - 560) / 520) ** 2 + ((yy - (fy - 200)) / 260) ** 2)) * k
        img += g[..., None] * (np.array([1.0, 1.0, 1.0], np.float32) + warm * np.array([0.5, 0.3, 0.0], np.float32))
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def lane_frame(lane, t):
    im = ROOM[lane].copy()
    d = ImageDraw.Draw(im)
    grey = lane == "top"
    draw_logs(d, count(TOP_FALLS if grey else BOT_FALLS, t), grey)
    draw_stump(d, grey)
    if grey or not (T_SH0 - 0.1 <= t < T_SH1 + 0.1):
        draw_stone(d, grey)
    draw_tree(im, lane, t)
    d = ImageDraw.Draw(im)
    spr, off, pts = person_sprite(lane, t)
    if not grey:
        im.alpha_composite(PW.glow_of(spr, 0.55, 14), off)
    im.alpha_composite(spr, off)
    d = ImageDraw.Draw(im)
    particles(d, lane, t)
    if grey:
        sweat(d, pts, t)
    for b0, b1, s in (BUB_TOP if grey else BUB_BOT):
        if b0 <= t < b1:
            bs = AJ.bubble(s)
            sc = out_back(prog(t, b0, b0 + 0.18))
            al = 1 - smooth(prog(t, b1 - 0.12, b1))
            if sc < 0.05:
                continue
            spr2 = bs.resize((max(1, int(bs.width * sc)), max(1, int(bs.height * sc))), Image.LANCZOS)
            if al < 0.999:
                spr2.putalpha(spr2.split()[3].point(lambda v: int(v * al)))
            hx, hy = pts["head"]
            x = clamp(hx - spr2.width / 2 + 30, 16, W - 16 - spr2.width)
            im.alpha_composite(spr2, (int(x), int(max(0, hy - 56 - spr2.height))))
    return im


def frame(t):
    img = ROOM["bg"].copy()
    for lane in ("top", "bot"):
        L = lane_frame(lane, t)
        fy = FLOORS[lane]
        y0 = fy - LF
        img.alpha_composite(L, (0, y0))
        # the dark mirror under the floor
        rh = 120 if lane == "top" else 230
        refl = L.crop((0, LF - rh, W, LF)).transpose(Image.FLIP_TOP_BOTTOM)
        a = np.asarray(refl).astype(np.float32)
        fade = (np.linspace(0.16 if lane == "top" else 0.2, 0.0, refl.height) ** 1.0)[:, None]
        a[..., 3] *= fade
        img.alpha_composite(Image.fromarray(a.astype(np.uint8), "RGBA"), (0, fy + 2))
    d = ImageDraw.Draw(img)
    # the counter
    spaced(d, W / 2, 132, "TREES CUT", font("Inter-SemiBold.otf", 26), (120, 124, 134, 255), 10)
    d.line([(W / 2, 176), (W / 2, 312)], fill=(46, 48, 54, 255), width=2)
    for cx, name, falls, col in ((270, "KEEPS CHOPPING", TOP_FALLS, (150, 154, 162)),
                                 (810, "STOPS TO SHARPEN", BOT_FALLS, (244, 244, 248))):
        spaced(d, cx, 186, name, font("Inter-Bold.otf", 34), col + (255,), 5)
        n = count(falls, t)
        ch = -9
        for f in falls:
            if f + 0.6 <= t:
                ch = f + 0.6
        pop = math.exp(-(t - ch) * 8) if ch > 0 else 0.0
        fn = font("InterDisplay-Bold.otf", int(96 * (1 + 0.2 * pop)))
        spaced(d, cx, 228 - 8 * pop, str(n), fn, PW.lerp_c(col, (255, 230, 150), pop * (cx > W / 2)) + (255,), 2)
    fm = font(MONO, 46)
    for t0, s, y in ((T_L1, LINE1, 352), (T_L2, LINE2, 414)):
        if t < t0:
            continue
        n = int(clamp((t - t0) * CPS, 0, len(s)))
        full = sum(fm.getlength(c) for c in s) + 3 * (len(s) - 1)
        x = W / 2 - full / 2
        for c in s[:n]:
            d.text((x, y), c, font=fm, fill=(250, 250, 252, 255))
            x += fm.getlength(c) + 3
        if (n < len(s) or (s == LINE2 and t < t0 + len(s) / CPS + 1.0)) and int(t * 3.4) % 2 == 0:
            d.rectangle([x + 2, y + 6, x + 24, y + 52], fill=(250, 250, 252, 220))
    return np.asarray(img.convert("RGB"))


def init_worker():
    ROOM["top"] = build_lane("top")
    ROOM["bot"] = build_lane("bot")
    ROOM["bg"] = build_bg()


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


# ---------------------------------------------------------------- sound (calm, like the split-room reels)
def audio():
    n = int(DUR * SR)
    mus, fx = np.zeros((n, 2)), np.zeros((n, 2))
    chords = [[50, 53, 57, 60], [46, 50, 53, 57], [48, 52, 55, 59], [45, 48, 52, 55]]   # Dm7 Bbmaj7 Cmaj7 Am7
    roots = [38, 34, 36, 33]
    mel = [69, 67, 65, 64, 65, 67, 69, 72]
    for b in range(int(round(DUR / BAR))):
        t0 = b * BAR
        ch, rt = chords[b % 4], roots[b % 4]
        for k, m in enumerate(ch):
            mix_in(mus, GS.pad(midi(m), BAR, 0.8, 1.4), t0, 0.045, (k - 1.5) * 0.4)
        mix_in(mus, GS.pad(midi(rt - 12), BAR, 0.3, 1.0), t0, 0.11)
        for q in (0, 2):
            mix_in(mus, GS.keys(midi(mel[(b * 2 + q // 2) % len(mel)])), t0 + q * BEAT + 0.05, 0.05, 0.25)
    mix_in(fx, noise(DUR, 3, lo=80, hi=500), 0, 0.012)
    # dull chops: a thin "tink" and a little knock; sharp chops: a clean wooden "thock"
    for i, tc in enumerate(TOP_C):
        if tc < DUR:
            mix_in(fx, tone(2400, 0.12, (1, 0.4), a=0.001, d=0.04), tc, 0.035, 0.3)
            mix_in(fx, tone(160, 0.12, (1, 0.3), a=0.001, d=0.04), tc, 0.07, 0.3)
    for i, tc in enumerate(BOT_C):
        if tc >= DUR:
            continue
        if i == 0:
            mix_in(fx, tone(2500, 0.12, (1, 0.4), a=0.001, d=0.04), tc, 0.035, -0.3)
            continue
        mix_in(fx, noise(0.16, 40 + i, lo=150, hi=1400) * env(int(0.16 * SR), 0.001, 0.04), tc, 0.22, -0.3)
        mix_in(fx, tone(120, 0.18, (1, 0.4), a=0.001, d=0.06), tc, 0.12, -0.3)
    # trees creak and land
    for falls, pan in ((TOP_FALLS, 0.3), (BOT_FALLS, -0.3)):
        for f in falls:
            if f >= DUR:
                continue
            tt = np.arange(int(0.6 * SR)) / SR
            creak = np.sin(2 * np.pi * np.cumsum(230 - 90 * tt + 18 * np.sin(2 * np.pi * 9 * tt)) / SR) * np.minimum(1, tt / 0.1) * np.clip((0.6 - tt) / 0.2, 0, 1)
            mix_in(fx, creak, f + 0.05, 0.02, pan)
            mix_in(fx, noise(0.4, int(f * 10), lo=40, hi=500) * env(int(0.4 * SR), 0.003, 0.12), f + 0.72, 0.25, pan)
    # sharpening strokes
    for ts in np.arange(T_SH0 + 0.35, T_SH1 - 0.1, math.pi / 7):
        mix_in(fx, noise(0.3, int(ts * 100), lo=2500, hi=7000) * env(int(0.3 * SR), 0.08, 0.1), ts, 0.03, -0.3)
    # the edge flashes; the counter below moves
    for i, m in enumerate((84, 88, 91)):
        mix_in(fx, GS.keys(midi(m), 1.0), T_UP1 + i * 0.06, 0.05, -0.3)
    for f in BOT_FALLS:
        if f + 0.6 < DUR:
            mix_in(fx, GS.keys(midi(79), 0.6), f + 0.6, 0.03, -0.3)
    for lst in (BUB_TOP, BUB_BOT):
        for b0, b1, s in lst:
            mix_in(fx, tone(700, 0.08, (1,), a=0.003, d=0.03), b0, 0.03)
    for t0, s in ((T_L1, LINE1), (T_L2, LINE2)):
        for i, c in enumerate(s):
            if c != " ":
                mix_in(fx, noise(0.03, 500 + i + int(t0), lo=1200, hi=4000) * env(int(0.03 * SR), 0.001, 0.008),
                       t0 + i / CPS, 0.05)
    x = mus + fx
    m = int(XFADE * SR)
    k = np.linspace(0, 1, m)[:, None]
    x[-m:] = x[-m:] * (1 - k) + x[:m] * k
    x /= max(1.0, np.abs(x).max() / 0.9)
    return x


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "sharpen-axe.mp4"
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
