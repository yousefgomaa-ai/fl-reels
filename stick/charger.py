#!/usr/bin/env python3
"""IDEAS.md #2 - "WHERE'S MY CHARGER?" Split screen, the channel's current style, 18 s, loops on itself.

Above, YOU, phone at 1% (blinking red): the desk drawer (1), under the bed, pillows flying, the drawer again (2), the
bag shaken empty, the laundry basket, the drawer a third time (3); the room a mess, you sit in it: "IT'S GONE.
FOREVER." The red timer in the middle: SEARCHING 00:00 -> 20:00. A white cable tail peeks out of that drawer every
time it opens. Below, MOM at the kitchen table with her tea and her paper. "MOM! MY CHARGER!" She gets up, walks in,
opens the drawer, lifts the socks: the charger, in 0.4 SEC. "UNDER THE SOCKS." - "...I CHECKED THERE. THREE TIMES."
"MOMS DON'T SEARCH. / THEY KNOW."  FOLLOW FOR MORE.

    python3 stick/charger.py stick/charger.mp4
    ONLY_FRAMES=0.5,2.0,3.2,4.3,6.5,7.8,9.9,12.0,13.2,14.2,16.4 python3 stick/charger.py /tmp/ch
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
import one_call as OC  # noqa
import five_minutes as FM  # noqa
from perfect_wave import (MONO, clamp, env, font, lerp, lerp_pose, midi, mix_in, noise, out_back, out_cubic,  # noqa
                          prog, rot, smooth, spaced, tone, write_wav)

W, H, FPS = 1080, 1920, 30
SR = 44100
BPM = 100
BEAT = 60 / BPM
BAR = 4 * BEAT
DUR = 7.5 * BAR
NF = int(round(DUR * FPS))
XFADE = 0.45
SC = AJ.SC
INK = AJ.INK
YOU, YOU_FAR = AJ.OT, AJ.OT_FAR
MOM, MOM_FAR = AJ.DOER, AJ.DOER_FAR
RED, GREEN = (255, 64, 56), (90, 230, 130)
BOLD = FM.BOLD
PH, TOP_Y0, BOT_Y0, STRIP_Y, FYP = OC.PH, OC.TOP_Y0, OC.BOT_Y0, OC.STRIP_Y, OC.FYP
STAND_Y = FYP - 113 * SC

# ---------------------------------------------------------------- your room
BED = (30, 330)
DESK = (470, 690)                        # desk with three drawers; the top one is THE drawer
DRAWER_Y = FYP - 150
BASKET = (780, 880)
DOOR = (930, 1060)

# ---------------------------------------------------------------- timeline
DRAWER_TRIES = [(1.6, 2.5), (5.0, 5.8), (8.4, 9.2)]
T_BED0, T_BED1 = 2.7, 3.7
T_PILLOW0, T_PILLOW1 = 3.9, 4.8
T_BAG0, T_BAG1 = 6.0, 7.0
T_BASKET0, T_BASKET1 = 7.2, 8.2
T_GIVEUP0 = 9.4
T_SHOUT0, T_SHOUT1 = 10.3, 11.4
T_SEARCH_END = 10.4                      # the timer reads 20:00
T_MOM_UP, T_MOM_OUT = 10.8, 11.5
T_MOM_IN0, T_MOM_IN1 = 11.6, 12.4
T_OPEN = 12.55
T_FOUND = 12.95                          # 0.4 s later
T_L1, T_L2 = 14.8, 15.95
CPS = 18.0
LINE1, LINE2 = "MOMS DON'T SEARCH.", "THEY KNOW."
T_FOLLOW = 16.95

BUB_YOU = [(0.3, 1.5, "WHERE'S MY CHARGER?", "me"), (9.6, 10.3, "IT'S GONE. FOREVER.", "me"),
           (T_SHOUT0, T_SHOUT1, "MOM! MY CHARGER!", "me"), (13.6, 14.8, "...I CHECKED THERE. 3 TIMES.", "me")]
BUB_MOM_TOP = [(13.0, 13.6, "UNDER THE SOCKS.", "me")]
BUB_MOM = [(T_SHOUT0 + 0.5, T_MOM_UP + 0.5, "*SIGH*", "me")]


def search_seconds(t):
    if t < 1.5:
        return 0
    return int(1200 * prog(t, 1.5, T_SEARCH_END) ** 1.1)


def drawer_open(t):
    for a, b in DRAWER_TRIES:
        if a <= t < b:
            return math.sin(math.pi * prog(t, a, b))
    if T_OPEN <= t:
        return smooth(prog(t, T_OPEN, T_OPEN + 0.25))
    return 0.0


def drawer_checks(t):
    return sum(1 for a, b in DRAWER_TRIES if t >= a + 0.3)


# ---------------------------------------------------------------- poses
STAND = PW.STAND
BEND = dict(STAND, head=(40, -118), neck=(30, -82), el=(60, -50), hl=(86, -30), er=(56, -46), hr=(82, -26),
            kl=(-10, 56), fl=(-26, 113), kr=(20, 56), fr=(34, 113))
LIE_FLOOR = {"head": (110, -24), "neck": (72, -20), "el": (100, -6), "hl": (130, 0), "er": (96, -2), "hr": (126, 6),
             "kl": (-56, -4), "fl": (-112, -2), "kr": (-54, 2), "fr": (-110, 6)}
THROW_UP = dict(STAND, el=(10, -150), hl=(-10, -196), er=(30, -150), hr=(20, -196))
BAG = dict(STAND, el=(20, -150), hl=(40, -190), er=(40, -150), hr=(60, -190))
SIT_FLOOR = {"head": (10, -150), "neck": (4, -108), "el": (32, -76), "hl": (60, -50), "er": (28, -72), "hr": (56, -46),
             "kl": (62, -26), "fl": (92, 28), "kr": (56, -20), "fr": (86, 32)}
SHOUT = dict(SIT_FLOOR, el=(30, -130), hl=(22, -150), er=(26, -126), hr=(18, -146), head=(6, -152))
STARE = dict(STAND, el=(-6, -58), hl=(-10, -10), er=(6, -58), hr=(10, -10))
MOM_SIT = dict(AJ.SIT_TYPE, el=(30, -66), hl=(56, -96), er=(36, -62), hr=(70, -60))
MOM_REACH = dict(STAND, el=(50, -90), hl=(90, -70), er=(44, -86), hr=(84, -66))
MOM_HOLD = dict(STAND, el=(40, -120), hl=(70, -160), er=(-10, -58), hr=(-14, -10))


def you(t):
    """(pose, x, y(hip), facing, prop)"""
    dx = DESK[0] - 30
    for a, b in DRAWER_TRIES:
        if a - 0.35 <= t < b:
            if t < a:
                return AJ.walk(t * 8, STAND), lerp(you_pos_before(a), dx, smooth(prog(t, a - 0.35, a))), STAND_Y, 1, None
            return BEND, dx, STAND_Y, 1, None
    if t < 1.25:
        return OC.SIT_PHONE if False else dict(STAND, el=(26, -66), hl=(44, -100), er=(22, -62), hr=(40, -96)), 380, \
            STAND_Y, 1, "phone"
    if t < 1.6:
        return AJ.walk(t * 8, STAND), lerp(380, dx, smooth(prog(t, 1.25, 1.6))), STAND_Y, 1, None
    if t < T_BED0:
        return AJ.walk(t * 8, STAND), lerp(dx, 360, smooth(prog(t, 2.5, T_BED0))), STAND_Y, -1, None
    if t < T_BED1:
        k = smooth(prog(t, T_BED0, T_BED0 + 0.25)) * (1 - smooth(prog(t, T_BED1 - 0.25, T_BED1)))
        hip_y = lerp(STAND_Y, FYP - 20, k)
        if k > 0.5:
            return LIE_FLOOR, 400, FYP - 22, -1, "torch"
        return lerp_pose(STAND, BEND, k * 2), 360, STAND_Y, -1, None
    if t < T_PILLOW1:
        k = max(0.0, math.sin((t - T_PILLOW0) * 8))
        return lerp_pose(STAND, THROW_UP, k), 300, STAND_Y, -1, None
    if t < 5.0:
        return AJ.walk(t * 8, STAND), lerp(300, dx, smooth(prog(t, T_PILLOW1, 5.0))), STAND_Y, 1, None
    if t < T_BAG0:
        return AJ.walk(t * 8, STAND), lerp(dx, 620, smooth(prog(t, 5.8, T_BAG0))), STAND_Y, 1, None
    if t < T_BAG1:
        sh = 6 * math.sin(t * 30)
        p = dict(BAG, hl=(BAG["hl"][0] + sh, BAG["hl"][1]), hr=(BAG["hr"][0] + sh, BAG["hr"][1]))
        return p, 620, STAND_Y, 1, "bag"
    if t < T_BASKET0 + 0.2:
        return AJ.walk(t * 8, STAND), lerp(620, BASKET[0] - 40, smooth(prog(t, T_BAG1, T_BASKET0 + 0.2))), STAND_Y, 1, None
    if t < T_BASKET1:
        k = max(0.0, math.sin((t - T_BASKET0) * 7))
        return lerp_pose(BEND, THROW_UP, k), BASKET[0] - 40, STAND_Y, 1, None
    if t < 8.4:
        return AJ.walk(t * 8, STAND), lerp(BASKET[0] - 40, dx, smooth(prog(t, T_BASKET1, 8.4))), STAND_Y, -1, None
    if t < T_GIVEUP0:
        return AJ.walk(t * 6, STAND), lerp(dx, 360, smooth(prog(t, 9.2, T_GIVEUP0))), STAND_Y, -1, None
    if t < T_SHOUT0:
        k = smooth(prog(t, T_GIVEUP0, T_GIVEUP0 + 0.4))
        return lerp_pose(STAND, SIT_FLOOR, k), 360, lerp(STAND_Y, FYP - 37, k), 1, None
    if t < T_MOM_IN1:
        return SHOUT if t < T_SHOUT1 else SIT_FLOOR, 360, FYP - 37, 1, None
    if t < T_FOUND:
        k = smooth(prog(t, T_MOM_IN1, T_MOM_IN1 + 0.4))
        return lerp_pose(SIT_FLOOR, STAND, k), 360, lerp(FYP - 37, STAND_Y, k), 1, None
    return STARE, 360, STAND_Y, 1, None


def you_pos_before(a):
    return {1.6: 380, 5.0: 300, 8.4: BASKET[0] - 40}.get(a, 380)


def mom(t):
    """In the kitchen (bottom) until she leaves; returns (where, pose, x, y, facing, prop)."""
    if t < T_MOM_UP:
        return "bot", MOM_SIT, 360, FYP - 115 * SC, 1, "tea"
    if t < T_MOM_OUT:
        k = smooth(prog(t, T_MOM_UP, T_MOM_UP + 0.25))
        x = lerp(360, 1200, smooth(prog(t, T_MOM_UP + 0.2, T_MOM_OUT)))
        return "bot", AJ.walk(t * 8, STAND), x, lerp(FYP - 115 * SC, STAND_Y, k), 1, None
    if t < T_MOM_IN0:
        return None
    if t < T_MOM_IN1:
        x = lerp(DOOR[0] + 40, DESK[1] + 50, smooth(prog(t, T_MOM_IN0, T_MOM_IN1)))
        return "top", AJ.walk(t * 8, STAND), x, STAND_Y, -1, None
    if t < T_FOUND:
        return "top", MOM_REACH, DESK[1] + 50, STAND_Y, -1, None
    k = smooth(prog(t, T_FOUND, T_FOUND + 0.25))
    return "top", lerp_pose(MOM_REACH, MOM_HOLD, k), DESK[1] + 50, STAND_Y, -1, "charger"


# ---------------------------------------------------------------- the mess
MESS = [  # (time it lands, x, kind, colour)
    (4.05, 140, "pillow", (236, 236, 240)), (4.35, 520, "pillow", (200, 210, 240)), (4.65, 760, "pillow", (236, 236, 240)),
    (6.2, 600, "book", (200, 80, 70)), (6.35, 660, "book", (70, 120, 200)), (6.5, 560, "pen", (240, 200, 60)),
    (6.65, 700, "keys", (214, 190, 120)), (6.8, 640, "cup", (240, 240, 236)),
    (7.4, 860, "shirt", (220, 70, 70)), (7.6, 920, "shirt", (90, 170, 110)), (7.8, 740, "pants", (70, 110, 200)),
    (8.0, 980, "shirt", (240, 200, 60))]


def draw_item(d, x, y, kind, col, ang=0.0):
    ink = INK + (255,)
    if kind == "pillow":
        d.rounded_rectangle([x - 40, y - 20, x + 40, y + 6], 14, fill=col + (255,), outline=ink, width=3)
    elif kind == "book":
        d.rectangle([x - 22, y - 10, x + 22, y + 4], fill=col + (255,), outline=ink, width=3)
    elif kind == "pen":
        d.line([(x - 16, y), (x + 16, y - 4)], fill=col + (255,), width=6)
    elif kind == "keys":
        d.ellipse([x - 8, y - 12, x + 8, y + 2], outline=col + (255,), width=3)
        d.line([(x + 6, y - 4), (x + 20, y - 2)], fill=col + (255,), width=4)
    elif kind == "cup":
        d.rectangle([x - 10, y - 18, x + 10, y + 2], fill=col + (255,), outline=ink, width=3)
    elif kind == "shirt":
        d.polygon([(x - 26, y - 14), (x + 26, y - 14), (x + 36, y), (x + 20, y + 4), (x + 20, y + 10), (x - 20, y + 10),
                   (x - 20, y + 4), (x - 36, y)], fill=col + (255,), outline=ink)
    elif kind == "pants":
        d.polygon([(x - 20, y - 14), (x + 20, y - 14), (x + 22, y + 10), (x - 22, y + 10)], fill=col + (255,), outline=ink)


def draw_mess(d, t):
    for (tl, x, kind, col) in MESS:
        if t < tl - 0.35:
            continue
        u = prog(t, tl - 0.35, tl)
        if kind == "pillow":
            sx = 300 if tl < 5 else 620
        elif kind in ("shirt", "pants"):
            sx = BASKET[0] + 50
        else:
            sx = 640
        sy = FYP - 260
        px = lerp(sx, x, u)
        py = lerp(sy, FYP - 4, u) - 160 * math.sin(math.pi * u)
        draw_item(d, px, py, kind, col)


# ---------------------------------------------------------------- the rooms
def build_room():
    yy, xx = np.mgrid[0:PH, 0:W].astype(np.float32)
    img = np.zeros((PH, W, 3), np.float32) + 8
    img += (np.exp(-(((xx - 520) / 420) ** 2 + ((yy - 300) / 300) ** 2)) * 40)[..., None] * np.array([1.0, 0.86, 0.62])
    img = np.where((yy > FYP)[..., None], img * 0.8 + 8, img)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    ink = INK + (255,)
    d.line([(0, FYP), (W, FYP)], fill=(46, 44, 44, 255), width=2)
    # bed
    d.rounded_rectangle([BED[0], FYP - 270, BED[0] + 30, FYP], 8, fill=(80, 64, 52, 255), outline=ink, width=3)
    d.rounded_rectangle([BED[0] + 20, FYP - 120, BED[1], FYP - 60], 10, fill=(96, 110, 150, 255), outline=ink, width=3)
    d.rectangle([BED[0] + 20, FYP - 60, BED[1], FYP - 30], fill=(80, 64, 52, 255), outline=ink, width=3)
    # desk + lamp + three drawers (the top drawer is drawn per frame)
    x0, x1 = DESK
    d.rectangle([x0 - 20, FYP - 210, x1 + 20, FYP - 194], fill=(130, 96, 66, 255), outline=ink, width=3)
    d.rectangle([x0, FYP - 194, x1, FYP], fill=(110, 82, 58, 255), outline=ink, width=4)
    for i in range(1, 3):
        y = DRAWER_Y + i * 56
        d.rectangle([x0 + 12, y, x1 - 12, y + 46], outline=ink, width=3)
        d.ellipse([(x0 + x1) / 2 - 7, y + 17, (x0 + x1) / 2 + 7, y + 31], fill=(214, 190, 120, 255))
    d.line([(x1 - 40, FYP - 210), (x1 - 40, FYP - 290)], fill=(80, 80, 84, 255), width=4)
    d.polygon([(x1 - 70, FYP - 290), (x1 - 10, FYP - 290), (x1 - 24, FYP - 330), (x1 - 56, FYP - 330)],
              fill=(236, 206, 150, 255), outline=ink)
    # laundry basket
    x0, x1 = BASKET
    d.polygon([(x0, FYP - 110), (x1, FYP - 110), (x1 - 10, FYP), (x0 + 10, FYP)], fill=(190, 170, 130, 255), outline=ink)
    for i in range(4):
        d.line([(x0 + 10 + i * 24, FYP - 106), (x0 + 14 + i * 22, FYP - 4)], fill=(150, 130, 96, 255), width=3)
    # door (mom comes in here)
    x0, x1 = DOOR
    d.rectangle([x0 - 8, FYP - 330, x1, FYP], fill=(54, 50, 48, 255), outline=ink, width=4)
    d.rectangle([x0, FYP - 320, x1, FYP], fill=(120, 96, 74, 255), outline=ink, width=3)
    d.ellipse([x0 + 16, FYP - 170, x0 + 30, FYP - 156], fill=(214, 190, 120, 255))
    # poster
    d.rectangle([560, 90, 690, 240], fill=(60, 80, 120, 255), outline=ink, width=4)
    d.polygon([(590, 210), (625, 120), (660, 210)], fill=(240, 200, 80, 255))
    return im


def build_kitchen():
    yy, xx = np.mgrid[0:PH, 0:W].astype(np.float32)
    img = np.zeros((PH, W, 3), np.float32) + np.array([12, 11, 10], np.float32)
    img += (np.exp(-(((xx - 420) / 380) ** 2 + ((yy - 380) / 300) ** 2)) * 50)[..., None] * np.array([1.0, 0.86, 0.62])
    img = np.where((yy > FYP)[..., None], img * 0.8 + np.array([14, 12, 10], np.float32), img)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    ink = INK + (255,)
    d.line([(0, FYP), (W, FYP)], fill=(60, 52, 44, 255), width=2)
    # fridge, a window, a clock on the wall, the table
    d.rounded_rectangle([860, FYP - 380, 1040, FYP], 10, fill=(214, 216, 222, 255), outline=ink, width=4)
    d.line([(860, FYP - 250), (1040, FYP - 250)], fill=ink, width=4)
    d.rectangle([1010, FYP - 340, 1020, FYP - 280], fill=(140, 140, 150, 255))
    d.rectangle([560, 80, 760, 250], fill=(120, 170, 220, 255), outline=ink, width=6)
    d.line([(660, 80), (660, 250)], fill=ink, width=5)
    d.ellipse([110, 90, 190, 170], fill=(240, 236, 226, 255), outline=ink, width=4)
    d.line([(150, 130), (150, 104)], fill=ink, width=4)
    d.line([(150, 130), (170, 136)], fill=ink, width=4)
    d.rectangle([440, FYP - 196, 720, FYP - 180], fill=(150, 108, 72, 255), outline=ink, width=4)
    for lx in (456, 694):
        d.rectangle([lx, FYP - 180, lx + 12, FYP], fill=(110, 80, 54, 255))
    d.rectangle([290, FYP - 128, 390, FYP - 112], fill=(120, 84, 56, 255), outline=ink, width=3)
    d.rectangle([290, FYP - 270, 302, FYP - 112], fill=(120, 84, 56, 255), outline=ink, width=3)
    for lx in (296, 376):
        d.rectangle([lx, FYP - 112, lx + 10, FYP], fill=(100, 70, 48, 255))
    return im


def draw_drawer(im, d, t):
    """THE drawer: opens; socks inside; a white cable tail peeks out from under them."""
    ink = INK + (255,)
    x0, x1 = DESK
    k = drawer_open(t)
    y = DRAWER_Y + 12 * k
    if k > 0.05:
        # inside: socks and the cable tail
        d.rectangle([x0 + 8, y - 40 * k, x1 - 8, y + 4], fill=(60, 44, 32, 255), outline=ink, width=3)
        for i, col in enumerate(((240, 240, 240), (220, 80, 80), (80, 120, 220), (240, 200, 60))):
            sx = x0 + 40 + i * 44
            d.ellipse([sx - 22, y - 34 * k, sx + 22, y - 8 * k], fill=col + (255,), outline=ink, width=2)
        if t < T_FOUND:
            d.line([(x0 + 172, y - 20 * k), (x0 + 196, y - 34 * k), (x0 + 214, y - 30 * k)], fill=(250, 250, 250, 255),
                   width=4)
    d.rectangle([x0 + 12, y, x1 - 12, y + 46], fill=(120, 90, 64, 255), outline=ink, width=3)
    d.ellipse([(x0 + x1) / 2 - 7, y + 17, (x0 + x1) / 2 + 7, y + 31], fill=(214, 190, 120, 255))


def person(pts, body, far, facing, prop, t, bun=False):
    cv = AJ.Canvas(*PW.bbox_of(list(pts.values()), 140))
    AJ.draw_stick(cv, pts, body, far, facing)
    P = cv.P
    k = AJ.SS
    ink = INK + (255,)
    hx, hy = pts["head"]
    if bun:
        q0, q1 = P((hx - 22 - facing * 30, hy - 52)), P((hx + 22 - facing * 30, hy - 14))
        cv.d.ellipse([q0[0], q0[1], q1[0], q1[1]], fill=body + (255,), outline=ink, width=5 * k)
    if prop == "phone":
        px = (pts["hl"][0] + pts["hr"][0]) / 2
        py = (pts["hl"][1] + pts["hr"][1]) / 2
        q0, q1 = P((px - 13, py - 24)), P((px + 13, py + 24))
        cv.d.rounded_rectangle([q0[0], q0[1], q1[0], q1[1]], 5 * k, fill=(30, 34, 48, 255), outline=ink, width=3 * k)
        s0, s1 = P((px - 9, py - 19)), P((px + 9, py + 19))
        cv.d.rectangle([s0[0], s0[1], s1[0], s1[1]], fill=(140, 200, 255, 255))
    if prop == "tea":
        cx, cy = pts["hl"]
        q0, q1 = P((cx - 12, cy - 24)), P((cx + 12, cy + 4))
        cv.d.rectangle([q0[0], q0[1], q1[0], q1[1]], fill=(240, 236, 228, 255), outline=ink, width=3 * k)
        nx, ny = pts["hr"]
        q0, q1 = P((nx - 40, ny - 60)), P((nx + 10, ny + 10))
        cv.d.rectangle([q0[0], q0[1], q1[0], q1[1]], fill=(230, 226, 214, 255), outline=ink, width=3 * k)
        for i in range(4):
            cv.d.line([P((nx - 34, ny - 50 + i * 14)), P((nx + 2, ny - 50 + i * 14))], fill=(120, 120, 120, 255), width=2 * k)
    if prop == "bag":
        bx, by = (pts["hl"][0] + pts["hr"][0]) / 2, (pts["hl"][1] + pts["hr"][1]) / 2
        q0, q1 = P((bx - 40, by - 6)), P((bx + 40, by + 60))
        cv.d.rounded_rectangle([q0[0], q0[1], q1[0], q1[1]], 10 * k, fill=(60, 90, 70, 255), outline=ink, width=4 * k)
    if prop == "torch":
        hx2, hy2 = pts["hl"]
        q0, q1 = P((hx2 - 6, hy2 - 6)), P((hx2 + 16, hy2 + 6))
        cv.d.rectangle([q0[0], q0[1], q1[0], q1[1]], fill=(60, 60, 70, 255), outline=ink, width=2 * k)
    if prop == "charger":
        cx, cy = pts["hl"]
        q0, q1 = P((cx - 16, cy - 30)), P((cx + 16, cy + 4))
        cv.d.rounded_rectangle([q0[0], q0[1], q1[0], q1[1]], 4 * k, fill=(250, 250, 250, 255), outline=ink, width=3 * k)
        cv.d.line([P((cx, cy + 4)), P((cx + 10, cy + 40)), P((cx - 6, cy + 70))], fill=(250, 250, 250, 255), width=4 * k)
    return cv.done()


ROOM = KITCHEN = None
FRAME0 = None


def panel_room(t):
    im = ROOM.copy()
    d = ImageDraw.Draw(im)
    draw_drawer(im, d, t)
    draw_mess(d, t)
    # torch beam under the bed
    pose, x, y, f, prop = you(t)
    pts = AJ.place(pose, (x, y), f, SC)
    if prop == "torch":
        g = Image.new("RGBA", (W, PH), (0, 0, 0, 0))
        ImageDraw.Draw(g).polygon([(pts["hl"][0], pts["hl"][1]), (BED[0] + 30, FYP - 60), (BED[0] + 30, FYP - 2)],
                                  fill=(255, 240, 180, 90))
        g = g.filter(ImageFilter.GaussianBlur(8))
        im.alpha_composite(g)
    if prop == "phone":
        OC.phone_glow(im, pts, "phone")
    spr, off = person(pts, YOU, YOU_FAR, f, prop, t)
    im.alpha_composite(spr, off)
    # the phone's battery: 1%, blinking
    d = ImageDraw.Draw(im)
    if t < T_FOUND:
        on = int(t * 2.5) % 2 == 0
        bx, by = 40, 40
        d.rounded_rectangle([bx, by, bx + 70, by + 32], 6, outline=(240, 240, 244, 255), width=3)
        d.rectangle([bx + 70, by + 10, bx + 76, by + 22], fill=(240, 240, 244, 255))
        if on:
            d.rectangle([bx + 6, by + 6, bx + 10, by + 26], fill=RED + (255,))
        spaced(d, bx + 120, by + 2, "1%", font(BOLD, 26), (RED if on else (160, 60, 56)) + (255,), 0)
    m = mom(t)
    if m and m[0] == "top":
        _, mp, mx, my, mf, mprop = m
        mpts = AJ.place(mp, (mx, my), mf, SC)
        if mprop == "charger":
            g = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
            ImageDraw.Draw(g).ellipse([60, 60, 240, 240], fill=(255, 240, 160, int(140 * smooth(prog(t, T_FOUND, T_FOUND + 0.3)))))
            g = g.filter(ImageFilter.GaussianBlur(30))
            im.alpha_composite(g, (int(mpts["hl"][0] - 150), int(mpts["hl"][1] - 160)))
        spr2, off2 = person(mpts, MOM, MOM_FAR, mf, mprop, t, bun=True)
        im.alpha_composite(PW.glow_of(spr2, 0.45, 12), off2)
        im.alpha_composite(spr2, off2)
        OC.speech_at(im, t, BUB_MOM_TOP, mpts)
    OC.speech_at(im, t, BUB_YOU, pts)
    # the drawer counter
    d = ImageDraw.Draw(im)
    n = drawer_checks(t)
    bx, by = W - 250, 60
    d.rounded_rectangle([bx, by, bx + 220, by + 92], 8, fill=(18, 20, 28, 230), outline=(90, 94, 104, 255), width=2)
    spaced(d, bx + 110, by + 10, "DRAWER CHECKED", font("Inter-SemiBold.otf", 17), (190, 194, 204, 255), 3)
    spaced(d, bx + 110, by + 38, f"{n}x", font(MONO, 40), (240, 240, 244, 255), 1)
    return im


def panel_kitchen(t):
    im = KITCHEN.copy()
    m = mom(t)
    if m and m[0] == "bot":
        _, mp, mx, my, mf, mprop = m
        mpts = AJ.place(mp, (mx, my), mf, SC)
        spr, off = person(mpts, MOM, MOM_FAR, mf, mprop, t, bun=True)
        im.alpha_composite(PW.glow_of(spr, 0.45, 12), off)
        im.alpha_composite(spr, off)
        OC.speech_at(im, t, BUB_MOM, mpts)
        if mprop == "tea" and t % 3 < 2:
            d = ImageDraw.Draw(im)
            for j in range(2):
                ph = (t * 0.8 + j * 0.5) % 1.0
                sx = mpts["hl"][0] + 4 * math.sin(t * 3 + j)
                d.line([(sx, mpts["hl"][1] - 30 - 30 * ph), (sx + 4, mpts["hl"][1] - 42 - 30 * ph)],
                       fill=(220, 220, 220, int(160 * (1 - ph))), width=3)
    if t >= T_SHOUT0 and t < T_SHOUT1:
        # the shout from upstairs reaches the kitchen
        d = ImageDraw.Draw(im)
        a = int(255 * math.sin(math.pi * prog(t, T_SHOUT0, T_SHOUT1)))
        spaced(d, 760, 60, "\"MOM!\"", font(BOLD, 40), (240, 240, 244, a), 3)
    return im


def frame(t):
    img = Image.new("RGBA", (W, H), (5, 5, 7, 255))
    img.alpha_composite(panel_room(t), (0, TOP_Y0))
    img.alpha_composite(panel_kitchen(t), (0, BOT_Y0))
    d = ImageDraw.Draw(img)
    d.line([(0, STRIP_Y), (W, STRIP_Y)], fill=(56, 56, 62, 255), width=2)
    found = t >= T_FOUND
    if found:
        s, col = "0.4 SEC", GREEN
        label = "MOM"
    else:
        sec = search_seconds(t)
        s, col = f"{sec // 60:02d}:{sec % 60:02d}", RED
        label = "SEARCHING"
    fc = font(BOLD, 66)
    tw = fc.getlength(s)
    d.rounded_rectangle([W / 2 - tw / 2 - 26, STRIP_Y - 50, W / 2 + tw / 2 + 26, STRIP_Y + 50], 10,
                        fill=(16, 6, 6, 255) if not found else (6, 16, 8, 255),
                        outline=(90, 24, 22, 255) if not found else (30, 90, 40, 255), width=3)
    g = Image.new("RGBA", (int(tw + 120), 160), (0, 0, 0, 0))
    ImageDraw.Draw(g).text((60, 30), s, font=fc, fill=col + (200,))
    g = g.filter(ImageFilter.GaussianBlur(10))
    img.alpha_composite(g, (int(W / 2 - tw / 2 - 60), int(STRIP_Y - 75)))
    d = ImageDraw.Draw(img)
    d.text((W / 2 - tw / 2, STRIP_Y - 41), s, font=fc, fill=col + (255,))
    spaced(d, W / 2 - tw / 2 - 150, STRIP_Y - 14, label, font("Inter-SemiBold.otf", 24), (200, 204, 214, 255), 4)
    fl = font("Inter-SemiBold.otf", 38)
    if t < T_L1:
        spaced(d, W / 2, TOP_Y0 + 14, "YOU", fl, (220, 224, 232, 255), 10)
    spaced(d, W / 2, BOT_Y0 + 14, "MOM", fl, (240, 242, 248, 255), 10)
    fm = font(BOLD, 54)
    for t0, s2, y in ((T_L1, LINE1, 40), (T_L2, LINE2, 108)):
        if t < t0:
            continue
        k = int(clamp((t - t0) * CPS, 0, len(s2)))
        full = sum(fm.getlength(c) for c in s2) + 3 * (len(s2) - 1)
        xx = W / 2 - full / 2
        for c in s2[:k]:
            d.text((xx, y), c, font=fm, fill=(250, 250, 252, 255))
            xx += fm.getlength(c) + 3
    arr = np.asarray(img.convert("RGB")).astype(np.float32)
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
    global ROOM, KITCHEN
    ROOM = build_room()
    KITCHEN = build_kitchen()


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


def audio():
    n = int(DUR * SR)
    mus, fx = np.zeros((n, 2)), np.zeros((n, 2))
    eighth = BEAT / 2
    # G major, a busy little figure while he searches, slowly louder; it stops when mom gets up
    figure = [67, 71, 74, 71, 69, 72, 74, 72]
    chords = [[43, 47, 50], [40, 43, 47], [36, 40, 43], [38, 42, 45]]
    shifts = [0, -2, -5, -3]
    t_end = T_MOM_UP
    i, tt = 0, 0.1
    while tt < t_end:
        b = int(tt / BAR) % 4
        g = 0.03 + 0.05 * prog(tt, 0, t_end)
        mix_in(mus, OC.piano(midi(figure[i % 8] + shifts[b] + 12), 0.35, 0.5), tt, g, 0.25)
        i += 1
        tt += eighth
    for b in range(int(t_end / BAR) + 1):
        t0 = b * BAR
        if t0 >= t_end:
            break
        ch = chords[b % 4]
        g = 0.03 + 0.04 * prog(t0, 0, t_end)
        for k, m in enumerate(ch):
            mix_in(mus, GS.pad(midi(m), min(BAR, t_end - t0), 0.3, 0.8), t0, g, (k - 1) * 0.4)
        for q in range(4):
            mix_in(mus, OC.piano(midi(ch[0] - 12), 0.5, 0.3), t0 + q * BEAT, g * 1.4)
    # mom's walk: only her steps; the find: a bright little chime; then warm chords for the line
    for ts in np.arange(T_MOM_UP + 0.3, T_MOM_IN1, 0.34):
        mix_in(fx, noise(0.05, int(ts * 100), lo=300, hi=2000) * env(int(0.05 * SR), 0.002, 0.015), ts, 0.07)
    for j, m in enumerate((84, 88, 91, 96)):
        mix_in(fx, OC.piano(midi(m), 1.0, 0.4), T_FOUND + j * 0.05, 0.06, -0.2)
    for k, m in enumerate((43, 50, 55, 59)):
        mix_in(mus, GS.pad(midi(m), 3.0, 0.5, 1.6), 14.4, 0.05, (k - 1.5) * 0.4)
    for j, m in enumerate((74, 71, 67, 71)):
        mix_in(mus, OC.piano(midi(m), 1.3, 0.5), 14.8 + j * 0.5, 0.05, 0.2)
    # low battery beeps
    for tb in np.arange(0.6, T_FOUND, 3.0):
        mix_in(fx, tone(1000, 0.08, (1,), a=0.002, d=0.03), tb, 0.03)
        mix_in(fx, tone(800, 0.08, (1,), a=0.002, d=0.03), tb + 0.12, 0.03)
    # drawers, thumps, whooshes, a rattle
    for a, b in DRAWER_TRIES:
        mix_in(fx, noise(0.25, int(a * 10), lo=200, hi=2500) * env(int(0.25 * SR), 0.02, 0.07), a, 0.1, 0.1)
    mix_in(fx, noise(0.25, 99, lo=200, hi=2500) * env(int(0.25 * SR), 0.02, 0.07), T_OPEN, 0.1, 0.1)
    for (tl, x, kind, col) in MESS:
        mix_in(fx, noise(0.2, int(tl * 100), lo=300, hi=3000) * env(int(0.2 * SR), 0.03, 0.06), tl - 0.3, 0.05,
               (x / W) * 2 - 1)
        mix_in(fx, noise(0.1, int(tl * 100) + 1, lo=80, hi=800) * env(int(0.1 * SR), 0.002, 0.03), tl, 0.08,
               (x / W) * 2 - 1)
    sh = noise(T_BAG1 - T_BAG0, 12, lo=2000, hi=8000)
    sh *= (0.5 + 0.5 * np.sin(np.arange(len(sh)) / SR * 2 * np.pi * 5))
    mix_in(fx, sh, T_BAG0, 0.03)
    for b0, b1, s, w in BUB_YOU + BUB_MOM + BUB_MOM_TOP:
        mix_in(fx, tone(700, 0.07, (1,), a=0.003, d=0.025), b0, 0.025)
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
    out = sys.argv[1] if len(sys.argv) > 1 else "charger.mp4"
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
