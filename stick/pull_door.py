#!/usr/bin/env python3
"""IT SAID PULL - Doer vs Overthinker in two identical escape rooms (split screen), 25.6 s, loops on itself.

Same room, same locked door, same ring of 50 keys, the same 1:00 on the clock - and a small plate under the handle
that says PULL, there from the first frame. Together: they push (thud), "IT'S LOCKED.", take the ring, try five keys.
Below, the overthinker throws the ring ("THIS IS STUPID.") and sits down against the wall ("NO WAY OUT.").
Above, the doer keeps going - key 20, 40, 48, 49 - "LAST ONE..." - key 50 fails. His head goes down... then he steps
back, "?", the plate glints, a light bulb: he pulls, the door swings open, out he goes with 0:05 left.
Below, he hears it, sees his own plate, runs - and his hand reaches the handle as the clock hits 0:00: red light,
the bolt shoots, "...PULL?"
"IT SAID PULL. / THE WHOLE TIME."

    python3 stick/pull_door.py stick/it-said-pull.mp4
    ONLY_FRAMES=0,1.4,3.0,4.2,7.2,12,15.9,17.2,18.6,19.6,20.2,23 python3 stick/pull_door.py /tmp/pd
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
from perfect_wave import (MONO, clamp, env, font, in_quad, lerp, lerp_pose, midi, mix_in, noise, out_back,  # noqa
                          out_cubic, prog, rot, smooth, spaced, tone, write_wav)

W, H, FPS = 1080, 1920, 30
SR = 44100
BPM = 75
BEAT = 60 / BPM
BAR = 4 * BEAT
DUR = 8 * BAR                           # 25.6 s
NF = int(round(DUR * FPS))
XFADE = 0.5
SC = AJ.SC
INK = AJ.INK
PH, FY, TOP_Y0, BOT_Y0 = AJ.PH, AJ.FY, AJ.TOP_Y0, AJ.BOT_Y0
DOER, DOER_FAR, OT, OT_FAR = AJ.DOER, AJ.DOER_FAR, AJ.OT, AJ.OT_FAR
GOLD, RED, GREEN, CYAN = AJ.GOLD, AJ.RED, AJ.GREEN, AJ.CYAN
STAND_Y = FY - 113 * SC

# ---------------------------------------------------------------- the room
DOOR_X0, DOOR_X1 = 812, 962             # the door in the back wall
DOOR_TOP = FY - 330
HANDLE = (DOOR_X0 + 26, FY - 168)
KEYHOLE = (DOOR_X0 + 26, FY - 196)
BOARD = (64, FY - 360, 236, FY - 196)   # the key board on the wall
AT_DOOR = 742                           # where they stand to work the door
AT_BOARD = 300
START_X = 520
SIT_X = 330

# ---------------------------------------------------------------- timeline
T_W0, T_W1 = 0.4, 1.1
T_PUSH0, T_PUSH1 = 1.1, 1.8
T_TK0, T_TK1 = 2.0, 2.75
T_GRAB = 2.9
T_BK0, T_BK1 = 3.0, 3.7
KEY_START, KEY_STEP = 3.8, 0.55         # five keys together
T_CLOCK0 = 20.0                         # 1:00 -> 0:00 over 20 s

KEYS_TOP = [KEY_START + KEY_STEP * i for i in range(5)]
_t = KEY_START + KEY_STEP * 5 + 0.1
_gap = 0.3
while len(KEYS_TOP) < 47:
    KEYS_TOP.append(_t)
    _t += _gap
    _gap = max(0.12, _gap * 0.93)
KEYS_TOP += [13.9, 14.65, 15.45]        # 48, 49 ... 50, slow
KEY_FAIL = 0.42                          # each key: in, turn, no
T_LAST = KEYS_TOP[-1]
T_SLUMP0, T_SLUMP1 = T_LAST + KEY_FAIL, T_LAST + KEY_FAIL + 0.45
T_THINK0 = 16.35
T_Q0, T_GLINT, T_BULB, T_BULB1 = 16.55, 17.0, 17.35, 17.95
T_PULL0, T_OPEN0, T_OPEN1 = 17.95, 18.3, 18.75
T_OUT0, T_OUT1 = 18.8, 19.8

T_THROW = KEYS_TOP[4] + KEY_FAIL + 0.15   # below: after key 5
T_SIT0, T_SIT1 = T_THROW + 0.5, T_THROW + 1.5
T_HEAR = 18.45
T_SEE = 18.85
T_RUN0, T_RUN1 = 19.15, 19.9
T_ZERO = T_CLOCK0
T_L1, T_L2 = 20.9, 22.0
CPS = 16.0
LINE1, LINE2 = "IT SAID PULL.", "THE WHOLE TIME."

BUB_BOTH = [(1.8, 2.9, "IT'S LOCKED.")]
BUB_TOP = [(14.85, 15.6, "LAST ONE...")]
BUB_BOT = [(T_THROW, T_THROW + 1.6, "THIS IS STUPID."), (10.6, 12.4, "NO WAY OUT."), (20.35, 22.6, "...PULL?")]


def keys_tried(t, top):
    if top:
        return sum(1 for k in KEYS_TOP if t >= k + KEY_FAIL)
    return min(5, sum(1 for k in KEYS_TOP[:5] if t >= k + KEY_FAIL))


def clock(t, top):
    if top and t >= T_OPEN0:
        t = T_OPEN0
    s = max(0, math.ceil(60 * (1 - t / T_CLOCK0) - 1e-6))
    return s


# ---------------------------------------------------------------- poses (facing right)
STAND = PW.STAND
PUSH = dict(STAND, head=(26, -144), neck=(16, -104), el=(52, -96), hl=(96, -104), er=(48, -92), hr=(92, -100))
KEY = dict(STAND, el=(46, -100), hl=(86, -114), er=(26, -70), hr=(40, -40))
KEY_HOLD = dict(STAND, el=(26, -70), hl=(40, -40), er=(20, -66), hr=(34, -36))
SLUMP = dict(KEY_HOLD, head=(18, -132), neck=(10, -100))
THINK = dict(STAND, er=(22, -70), hr=(18, -118), el=(-10, -60), hl=(-14, -12))
PULL = dict(STAND, head=(-12, -148), neck=(-8, -106), el=(40, -96), hl=(86, -96), er=(36, -92), hr=(82, -92),
            kl=(-20, 56), fl=(-36, 113), kr=(16, 56), fr=(30, 113))
THROW = dict(STAND, el=(10, -150), hl=(30, -196))
SIT_FLOOR = {"head": (10, -150), "neck": (4, -108), "el": (32, -76), "hl": (-6, -80), "er": (28, -72), "hr": (-10, -76),
             "kl": (62, -26), "fl": (92, 28), "kr": (56, -20), "fr": (86, 32)}
SIT_LOOK = dict(SIT_FLOOR, head=(18, -152))
REACH = dict(STAND, head=(30, -140), neck=(20, -100), el=(58, -100), hl=(100, -106), er=(-20, -60), hr=(-40, -20),
             kl=(-30, 56), fl=(-50, 113), kr=(30, 54), fr=(46, 113))


def walk(t, base=STAND, speed=7.0):
    return AJ.walk(t * speed, base)


def key_cycle(t, k0):
    """Insert the key, try to turn it, take it out."""
    u = prog(t, k0, k0 + KEY_FAIL)
    if u <= 0 or u >= 1:
        return KEY_HOLD, 0.0
    k = math.sin(math.pi * u)
    return lerp_pose(KEY_HOLD, KEY, min(1.0, k * 1.6)), k


def person(t, top):
    """(pose, x, y, facing, prop, key_k)"""
    if t < T_W0:
        return STAND, START_X, STAND_Y, 1, None, 0
    if t < T_W1:
        x = lerp(START_X, AT_DOOR, smooth(prog(t, T_W0, T_W1)))
        return walk(t), x, STAND_Y, 1, None, 0
    if t < T_PUSH1:
        k = max(0.0, math.sin(2 * math.pi * prog(t, T_PUSH0, T_PUSH1) * 2 - 0.3))
        return lerp_pose(STAND, PUSH, 0.4 + 0.6 * k), AT_DOOR + 10 * k, STAND_Y, 1, None, 0
    if t < T_TK0:
        return STAND, AT_DOOR, STAND_Y, 1, None, 0
    if t < T_TK1:
        x = lerp(AT_DOOR, AT_BOARD, smooth(prog(t, T_TK0, T_TK1)))
        return walk(t), x, STAND_Y, -1, None, 0
    if t < T_BK0:
        k = math.sin(math.pi * prog(t, T_TK1, T_BK0))
        return lerp_pose(STAND, dict(STAND, el=(10, -150), hl=(24, -190)), k), AT_BOARD, STAND_Y, -1, \
            ("ring" if t > T_GRAB else None), 0
    if t < T_BK1:
        x = lerp(AT_BOARD, AT_DOOR, smooth(prog(t, T_BK0, T_BK1)))
        return walk(t, KEY_HOLD), x, STAND_Y, 1, "ring", 0
    if not top and t >= T_THROW - 0.1:
        return bottom_after(t)
    if top and t >= T_SLUMP0:
        return top_after(t)
    # trying keys
    pose, kk = KEY_HOLD, 0.0
    for k0 in KEYS_TOP:
        if k0 <= t < k0 + KEY_FAIL:
            pose, kk = key_cycle(t, k0)
    return pose, AT_DOOR, STAND_Y, 1, "ring", kk


def top_after(t):
    if t < T_THINK0:
        k = smooth(prog(t, T_SLUMP0, T_SLUMP1))
        return lerp_pose(KEY_HOLD, SLUMP, k), AT_DOOR, STAND_Y, 1, "ring", 0
    if t < T_PULL0:
        k = smooth(prog(t, T_THINK0, T_THINK0 + 0.45))
        x = lerp(AT_DOOR, AT_DOOR - 110, k)
        p = lerp_pose(SLUMP, THINK, k)
        if t < T_THINK0 + 0.45:
            p = walk(t, p, 5.0)
        return p, x, STAND_Y, 1, None, 0
    if t < T_OPEN1:
        k = smooth(prog(t, T_PULL0, T_OPEN0))
        x = lerp(AT_DOOR - 110, AT_DOOR - 30, k)
        return lerp_pose(THINK, PULL, k), x, STAND_Y, 1, None, 0
    if t < T_OUT1:
        u = prog(t, T_OUT0, T_OUT1)
        return walk(t), lerp(AT_DOOR - 30, (DOOR_X0 + DOOR_X1) / 2, smooth(u)), STAND_Y, 1, "out", u
    return STAND, -900, STAND_Y, 1, "gone", 0


def bottom_after(t):
    if t < T_THROW + 0.4:
        k = math.sin(math.pi * prog(t, T_THROW - 0.1, T_THROW + 0.4))
        return lerp_pose(KEY_HOLD, THROW, k), AT_DOOR, STAND_Y, 1, "ring" if t < T_THROW + 0.1 else None, 0
    if t < T_SIT0 + 0.6:
        x = lerp(AT_DOOR, SIT_X, smooth(prog(t, T_THROW + 0.4, T_SIT0 + 0.6)))
        return walk(t), x, STAND_Y, -1, None, 0
    if t < T_SIT1:
        k = smooth(prog(t, T_SIT0 + 0.6, T_SIT1))
        return lerp_pose(STAND, SIT_FLOOR, k), SIT_X, lerp(STAND_Y, FY - 37, k), 1, None, 0
    if t < T_RUN0:
        look = 0.0
        for g0 in (9.4, 13.3):
            look = max(look, math.sin(math.pi * prog(t, g0, g0 + 1.0)))
        if t >= T_HEAR:
            look = 1.0
        p = lerp_pose(SIT_FLOOR, SIT_LOOK, look)
        if t >= T_SEE:
            k = smooth(prog(t, T_SEE + 0.1, T_RUN0))
            return lerp_pose(p, STAND, k), SIT_X, lerp(FY - 37, STAND_Y, k), 1, None, 0
        return p, SIT_X, FY - 37, 1, None, 0
    if t < T_RUN1:
        u = prog(t, T_RUN0, T_RUN1)
        return PW.run(t * 15), lerp(SIT_X, AT_DOOR - 20, u), STAND_Y - 6 * abs(math.sin(t * 15)), 1, None, 0
    # at the handle as the clock runs out; he pulls - too late
    k = smooth(prog(t, T_RUN1, T_RUN1 + 0.2))
    tug = 0.5 + 0.5 * math.sin(t * 16) if T_ZERO <= t < T_ZERO + 0.9 else 0.5
    return lerp_pose(REACH, PULL, k * tug), AT_DOOR - 20, STAND_Y, 1, None, 0


# ---------------------------------------------------------------- drawing
def draw_board(d, t, empty):
    ink = INK + (255,)
    x0, y0, x1, y1 = BOARD
    d.rounded_rectangle([x0, y0, x1, y1], 6, fill=(86, 66, 46, 255), outline=ink, width=4)
    spaced(d, (x0 + x1) / 2, y0 + 8, "KEYS", font("Inter-Bold.otf", 18), (230, 210, 170, 255), 4)
    if empty:
        for i in range(10):
            for j in range(3):
                x, y = x0 + 18 + i * 15.5, y0 + 46 + j * 38
                d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(40, 30, 22, 255))
        return
    for i in range(10):
        for j in range(3):
            x, y = x0 + 18 + i * 15.5, y0 + 46 + j * 38
            d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(40, 30, 22, 255))
            d.line([(x, y), (x, y + 20)], fill=(220, 190, 90, 255), width=3)
            d.ellipse([x - 5, y + 18, x + 5, y + 28], outline=(220, 190, 90, 255), width=2)


def draw_door(img, d, t, top, red=0.0):
    ink = INK + (255,)
    opened = smooth(prog(t, T_OPEN0, T_OPEN1)) if top else 0.0
    x0, x1, y0, y1 = DOOR_X0, DOOR_X1, DOOR_TOP, FY
    d.rectangle([x0 - 12, y0 - 12, x1 + 12, y1], fill=(56, 50, 46, 255), outline=ink, width=4)
    if opened > 0:
        # the outside: a warm white light
        d.rectangle([x0, y0, x1, y1], fill=(255, 244, 214, 255))
        gl = Image.new("RGBA", (700, 700), (0, 0, 0, 0))
        ImageDraw.Draw(gl).polygon([(250, 100), (400, 100), (700, 700), (0, 700)], fill=(255, 236, 190, int(140 * opened)))
        gl = gl.filter(ImageFilter.GaussianBlur(30))
        img.alpha_composite(gl, (int(x0 - 250), int(y0 - 100)))
        d = ImageDraw.Draw(img)
    # the door leaf, hinged on the right, swings towards us as it opens
    w = (x1 - x0) * (1 - 0.82 * opened)
    lx0 = x1 - w
    skew = 26 * opened
    col = PW.lerp_c((120, 84, 56), (150, 60, 50), red)
    d.polygon([(lx0, y0 - skew), (x1, y0), (x1, y1), (lx0, y1 + skew * 0.3)], fill=col + (255,), outline=ink)
    d.line([(lx0, y0 - skew), (x1, y0), (x1, y1), (lx0, y1 + skew * 0.3), (lx0, y0 - skew)], fill=ink, width=4)
    if opened < 0.3:
        for (a, b) in ((0.15, 0.45), (0.55, 0.88)):
            d.rectangle([x0 + 20, y0 + (y1 - y0) * a, x1 - 20, y0 + (y1 - y0) * b], outline=(96, 66, 44, 255), width=4)
        # keyhole, handle and the little plate
        kx, ky = KEYHOLE
        d.ellipse([kx - 6, ky - 6, kx + 6, ky + 6], fill=ink)
        d.polygon([(kx - 3, ky), (kx + 3, ky), (kx + 5, ky + 14), (kx - 5, ky + 14)], fill=ink)
        hx, hy = HANDLE
        d.rounded_rectangle([hx - 8, hy - 8, hx + 34, hy + 8], 6, fill=(214, 190, 120, 255), outline=ink, width=3)
        px0, py0 = hx - 14, hy + 22
        glint = 0.0
        if top and T_GLINT <= t < T_BULB1:
            glint = math.sin(math.pi * prog(t, T_GLINT, T_BULB1))
        if not top and T_SEE - 0.1 <= t < T_SEE + 0.8:
            glint = math.sin(math.pi * prog(t, T_SEE - 0.1, T_SEE + 0.8))
        if glint > 0.01:
            g = Image.new("RGBA", (200, 120), (0, 0, 0, 0))
            ImageDraw.Draw(g).rounded_rectangle([40, 30, 160, 90], 10, fill=(255, 240, 160, int(200 * glint)))
            g = g.filter(ImageFilter.GaussianBlur(16))
            img.alpha_composite(g, (int(px0 - 40 + 6), int(py0 - 30 - 8)))
            d = ImageDraw.Draw(img)
        d.rounded_rectangle([px0, py0, px0 + 66, py0 + 26], 4, fill=(230, 226, 214, 255), outline=ink, width=2)
        spaced(d, px0 + 33, py0 + 3, "PULL", font("Inter-Bold.otf", 17), (30, 30, 36, 255), 2)
    # a lamp over the door: red when the clock runs out
    lc = PW.lerp_c((70, 70, 74), (255, 60, 50), red)
    d.ellipse([(x0 + x1) / 2 - 12, y0 - 40, (x0 + x1) / 2 + 12, y0 - 18], fill=lc + (255,), outline=ink, width=2)
    if red > 0.01 and not top and t >= T_ZERO:
        # the bolt shoots across
        bx = lerp(x1 + 30, x1 - 40, smooth(prog(t, T_ZERO, T_ZERO + 0.12)))
        d.rectangle([bx - 30, FY - 210, bx + 30, FY - 192], fill=(170, 170, 180, 255), outline=ink, width=3)
    return d


def ring_draw(d, cx, cy, n=12, spin=0.0):
    d.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], outline=(214, 190, 120, 255), width=4)
    for i in range(n):
        a = spin + i * 2 * math.pi / n * 0.55 + 1.2
        x, y = cx + 16 * math.cos(a), cy + 16 * math.sin(a)
        ex, ey = cx + 40 * math.cos(a), cy + 40 * math.sin(a)
        d.line([(x, y), (ex, ey)], fill=(220, 190, 90, 255), width=4)


def person_sprite(pts, body, far, facing, glow):
    cv = AJ.Canvas(*PW.bbox_of(list(pts.values()), 110))
    AJ.draw_stick(cv, pts, body, far, facing)
    return cv.done()


def thought(img, d, t, head):
    if not (T_Q0 <= t < T_BULB1):
        return d
    hx, hy = head
    bx, by = hx - 110, hy - 120
    sc = out_back(prog(t, T_Q0, T_Q0 + 0.2))
    al = 1 - smooth(prog(t, T_BULB1 - 0.2, T_BULB1))
    a = int(255 * al)
    if sc < 0.05:
        return d
    for r, ox, oy in ((7, -34, 70), (11, -60, 96)):
        d.ellipse([hx + ox - r, hy - oy - r, hx + ox + r, hy - oy + r], fill=(242, 240, 234, a), outline=INK + (a,), width=3)
    R = 50 * sc
    d.ellipse([bx - R, by - R, bx + R, by + R], fill=(242, 240, 234, a), outline=INK + (a,), width=4)
    if t < T_BULB:
        spaced(d, bx, by - 32 * sc, "?", font("InterDisplay-Bold.otf", int(56 * sc)), INK + (a,), 0)
    else:
        k = out_back(prog(t, T_BULB, T_BULB + 0.2))
        r = 20 * k
        d.ellipse([bx - r, by - r - 8, bx + r, by + r - 8], fill=(255, 220, 90, a), outline=INK + (a,), width=4)
        d.rectangle([bx - 9 * k, by + r - 10, bx + 9 * k, by + r + 5], fill=(150, 150, 160, a), outline=INK + (a,), width=3)
        for i in range(5):
            ang = -math.pi / 2 + (i - 2) * 0.5
            d.line([(bx + 28 * k * math.cos(ang), by - 8 + 28 * k * math.sin(ang)),
                    (bx + 38 * k * math.cos(ang), by - 8 + 38 * k * math.sin(ang))], fill=(255, 200, 60, a), width=4)
    return d


def box(d, x0, y0, label, value, col, w=230):
    d.rounded_rectangle([x0, y0, x0 + w, y0 + 92], 8, fill=(18, 20, 28, 230), outline=(90, 94, 104, 255), width=2)
    spaced(d, x0 + w / 2, y0 + 10, label, font("Inter-SemiBold.otf", 21), (190, 194, 204, 255), 5)
    spaced(d, x0 + w / 2, y0 + 38, value, font(MONO, 40), col + (255,), 1)


def bubbles(im, t, lst, head):
    for b0, b1, s in lst:
        if not (b0 <= t < b1) or head is None:
            continue
        bs = AJ.bubble(s)
        sc = out_back(prog(t, b0, b0 + 0.16))
        al = 1 - smooth(prog(t, b1 - 0.1, b1))
        if sc < 0.05:
            continue
        spr = bs.resize((max(1, int(bs.width * sc)), max(1, int(bs.height * sc))), Image.LANCZOS)
        if al < 0.999:
            spr.putalpha(spr.split()[3].point(lambda v: int(v * al)))
        x = clamp(head[0] - spr.width / 2 - 40, 16, W - 16 - spr.width)
        y = max(118, head[1] - 52 - spr.height)
        im.alpha_composite(spr, (int(x), int(y)))


ROOM = None
FRAME0 = None


def panel(t, top):
    im = ROOM.copy()
    d = ImageDraw.Draw(im)
    red = 0.0
    if not top and t >= T_ZERO:
        red = 0.65 + 0.35 * math.sin((t - T_ZERO) * 9)
    pose, x, y, f, prop, kk = person(t, top)
    took = t >= T_GRAB
    draw_board(d, t, took)
    d = draw_door(im, d, t, top, red if not top else 0.0)
    # the thrown ring lies on the floor below
    if not top and t >= T_THROW + 0.1:
        u = prog(t, T_THROW + 0.1, T_THROW + 0.5)
        rx = lerp(AT_DOOR + 40, 610, u)
        ry = lerp(STAND_Y - 200, FY - 18, out_cubic(u)) - 60 * math.sin(math.pi * u)
        ring_draw(d, rx, ry, spin=u * 6)
    body, far = (DOER, DOER_FAR) if top else (OT, OT_FAR)
    pts = None
    if prop != "gone":
        pts = AJ.place(pose, (x, y), f, SC)
        spr, off = person_sprite(pts, body, far, f, top)
        alpha = 1.0
        if prop == "out":
            alpha = 1 - smooth(prog(kk, 0.55, 1.0))
        if alpha < 0.999:
            spr.putalpha(spr.split()[3].point(lambda v: int(v * alpha)))
        if top:
            gcol = (255, 236, 190) if t >= T_OPEN0 else (210, 228, 255)
            g = PW.glow_of(spr, 0.55, 12, gcol)
            if alpha < 0.999:
                g.putalpha(g.split()[3].point(lambda v: int(v * alpha)))
            im.alpha_composite(g, off)
        im.alpha_composite(spr, off)
        d = ImageDraw.Draw(im)
        if prop == "ring":
            hx, hy = pts["hr"] if t < T_BK1 or kk == 0 else pts["hr"]
            ring_draw(d, hx, hy + 22, spin=t * 0.5)
        if kk > 0:
            # the key in the lock: in, a turn, and no
            kx, ky = KEYHOLE
            ang = -0.6 * kk
            d.line([(kx - 34 + 30 * kk, ky + 4), (kx, ky + 4)], fill=(220, 190, 90, 255), width=5)
            d.ellipse([kx - 48 + 30 * kk, ky - 6, kx - 30 + 30 * kk, ky + 12], outline=(220, 190, 90, 255), width=4)
            if kk > 0.85:
                spaced(d, kx - 4, ky - 60, "✕", font("Inter-Bold.otf", 30), RED + (255,), 0)
        if top:
            d = thought(im, d, t, pts["head"])
    # boxes: keys tried and the clock
    n = keys_tried(t, top)
    box(d, 26, 18, "KEYS TRIED", f"{n}/50", GOLD if n < 50 else (255, 170, 150))
    s = clock(t, top)
    if top and t >= T_OPEN0:
        box(d, W - 256, 18, "ESCAPED", f"0:{s:02d}", GREEN)
    else:
        box(d, W - 256, 18, "TIME LEFT", f"0:{s:02d}" if s < 60 else "1:00", RED if s <= 10 else (240, 240, 244))
    head = pts["head"] if pts else None
    bubbles(im, t, BUB_BOTH + (BUB_TOP if top else BUB_BOT), head)
    if red > 0:
        a = np.asarray(im).astype(np.float32)
        a[..., 0] = a[..., 0] * (1 - 0.25 * red) + 255 * 0.25 * red
        a[..., 1] *= 1 - 0.35 * red
        a[..., 2] *= 1 - 0.35 * red
        im = Image.fromarray(a.astype(np.uint8), "RGBA")
        d = ImageDraw.Draw(im)
        if t >= T_ZERO:
            spaced(d, 330, 150, "TIME'S UP", font("InterDisplay-Bold.otf", 44), (255, 230, 226, 255), 6)
    return im


def frame(t):
    img = Image.new("RGBA", (W, H), (6, 6, 8, 255))
    img.alpha_composite(panel(t, True), (0, TOP_Y0))
    img.alpha_composite(panel(t, False), (0, BOT_Y0))
    d = ImageDraw.Draw(img)
    spaced(d, W / 2, 268, "DOER", font("Inter-SemiBold.otf", 40), (236, 238, 244, 255), 10)
    spaced(d, W / 2, BOT_Y0 + PH + 18, "OVERTHINKER", font("Inter-SemiBold.otf", 40), (200, 204, 214, 255), 10)
    spaced(d, W / 2, TOP_Y0 + PH + 34, "SAME ROOM", font("Inter-SemiBold.otf", 40), (206, 210, 220, 255), 9)
    d.line([(60, BOT_Y0 - 8), (W - 60, BOT_Y0 - 8)], fill=(50, 52, 60, 255), width=2)
    fm = font(MONO, 54)
    for t0, s, y, col in ((T_L1, LINE1, 80, (250, 250, 252)), (T_L2, LINE2, 150, GOLD)):
        if t < t0:
            continue
        k = int(clamp((t - t0) * CPS, 0, len(s)))
        full = sum(fm.getlength(c) for c in s) + 3 * (len(s) - 1)
        xx = W / 2 - full / 2
        for c in s[:k]:
            d.text((xx, y), c, font=fm, fill=col + (255,))
            xx += fm.getlength(c) + 3
        if (k < len(s) or (s == LINE2 and t < t0 + len(s) / CPS + 1.0)) and int(t * 3.4) % 2 == 0:
            d.rectangle([xx + 2, y + 6, xx + 28, y + 60], fill=col + (220,))
    return np.asarray(img.convert("RGB"))


def init_worker():
    global ROOM
    ROOM = AJ.build_room()


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


# ---------------------------------------------------------------- sound: calm pads, a soft clock that keeps ticking
def audio():
    n = int(DUR * SR)
    mus, fx = np.zeros((n, 2)), np.zeros((n, 2))
    chords = [[50, 53, 57, 60], [46, 50, 53, 57], [48, 52, 55, 59], [45, 48, 52, 55]]
    roots = [38, 34, 36, 33]
    for b in range(int(round(DUR / BAR))):
        t0 = b * BAR
        ch, rt = chords[b % 4], roots[b % 4]
        g = 0.045 if b < 6 else 0.035
        for k, m in enumerate(ch):
            mix_in(mus, GS.pad(midi(m), BAR, 0.8, 1.4), t0, g, (k - 1.5) * 0.4)
        mix_in(mus, GS.pad(midi(rt - 12), BAR, 0.3, 1.0), t0, 0.11)
    # the clock: one soft tick a game second, faster near the end
    for i in range(60):
        tk = T_CLOCK0 * i / 60
        mix_in(fx, tone(1400 if i % 2 == 0 else 1100, 0.03, (1,), a=0.001, d=0.01), tk, 0.025 + 0.03 * (i / 60))
    # the push: two thuds
    for tp in (T_PUSH0 + 0.2, T_PUSH0 + 0.5):
        mix_in(fx, noise(0.2, int(tp * 100), lo=60, hi=500) * env(int(0.2 * SR), 0.002, 0.06), tp, 0.25)
    # the ring: a jingle when taken; the keys: in, a click, a low "no"
    mix_in(fx, noise(0.3, 7, lo=3000, hi=9000) * env(int(0.3 * SR), 0.003, 0.08), T_GRAB, 0.08)
    for i, k0 in enumerate(KEYS_TOP):
        top_only = i >= 5
        mix_in(fx, noise(0.04, 100 + i, lo=2000, hi=8000) * env(int(0.04 * SR), 0.001, 0.01), k0 + 0.1, 0.06,
               -0.3 if top_only else 0.0)
        mix_in(fx, GS.keys(midi(50), 0.35), k0 + KEY_FAIL * 0.8, 0.035, -0.3 if top_only else 0.0)
    # the throw: a clatter on the floor
    mix_in(fx, noise(0.5, 8, lo=2500, hi=9000) * env(int(0.5 * SR), 0.003, 0.12), T_THROW + 0.45, 0.12, 0.3)
    # key 50: nothing but the clock; then the idea and the door
    for i, m in enumerate((84, 91)):
        mix_in(fx, GS.keys(midi(m), 1.2), T_BULB + i * 0.08, 0.07, -0.3)
    mix_in(fx, tone(200, 0.4, (1, 0.5), a=0.02, d=0.2, sweep=150), T_OPEN0, 0.08, -0.3)
    mix_in(fx, noise(1.2, 9, lo=200, hi=3000) * env(int(1.2 * SR), 0.2, 0.4), T_OPEN0, 0.08, -0.3)
    for i, m in enumerate((72, 76, 79, 84, 88)):
        mix_in(fx, GS.keys(midi(m), 1.6), T_OPEN0 + 0.1 + i * 0.08, 0.06, -0.3)
    # time's up below: two low buzzes and the bolt
    for i in range(3):
        mix_in(fx, tone(110, 0.35, (1, 0.6, 0.4, 0.25), a=0.01, d=0.25), T_ZERO + i * 0.45, 0.16, 0.3)
    mix_in(fx, noise(0.15, 10, lo=200, hi=2500) * env(int(0.15 * SR), 0.001, 0.04), T_ZERO + 0.02, 0.3, 0.3)
    for lst in (BUB_BOTH, BUB_TOP, BUB_BOT):
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
    out = sys.argv[1] if len(sys.argv) > 1 else "it-said-pull.mp4"
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
