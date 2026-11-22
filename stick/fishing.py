#!/usr/bin/env python3
"""WOULD YOU WAIT 60 MIN? - split screen, sunset lake, thick white figures. 18 s, a perfect loop (last frame = first).

Both panels identical at frame 0: a fisherman on a dock, line in the water, and a huge glowing GOLDEN FISH right under
the hook - the viewer sees it, they don't. Timers run. Something happens every ~1.5 s: the fish teases the bait, a
nibble, the impatient one recasts and scares it off, a seagull steals his cap, a second tease. At 59:00 IMPATIENT packs
up and walks off - and the fish swims straight to where his hook was ("?"). The last minute stretches; at 60:00
PATIENT's float goes under, he fights it, lifts the golden fish: CAUGHT IT / LEFT AT 59. Then everything resets into
frame 0: the fish goes in the cooler, a new golden fish swims in, the impatient one comes back, the seagull drops his
cap on his head, both cast, timers spin back to 00:00.

    python3 stick/fishing.py stick/fishing.mp4
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
K = hq.K
BOLD = hq.BOLD
MUSIC = "harp_bb"

TITLE_H = 300
PX0 = 20
PWD, PHT = 1040, 760
PANEL_Y = [310, 1080]
WATER = 430
DOCK_Y = 420
DOCK_X1 = 380
S = 1.3
CHAIR_X = 210
HIP = (CHAIR_X, DOCK_Y - 142)
FLOAT_X = 610
HOOK = (FLOAT_X, 612)
FISH0 = (680, 640)
INK = (30, 28, 38)
WHITE = (250, 250, 250)
GOLD = (255, 196, 40)
RED = (226, 54, 54)
GREEN = (40, 176, 86)
YEL = (255, 210, 60)

# timeline
T_TEASE1 = 1.5
T_NIBBLE = 3.2
T_RECAST = 4.8
T_GULL = 7.0
T_TEASE2 = 9.0
T_REEL = 10.4
T_STAND = 11.0
T_LEAVE0, T_LEAVE1 = 11.8, 12.6
T_Q = 12.85
T_BITE = 15.0
T_LIFT = 16.0
T_COOLER = 16.8
T_BACK0, T_BACK1 = 16.6, 17.35
T_RESET = 17.2
T_CAST2 = 17.45


# ---------------------------------------------------------------- clocks
def secs(t):
    """seconds on the timer: fast, then the last minute stretches; resets to 0 at the end"""
    if t < 11.0:
        v = 3300 * t / 11.0
    elif t < 12.6:
        v = lerp(3300, 3540, prog(t, 11.0, 12.6))
    elif t < T_BITE:
        v = lerp(3540, 3600, prog(t, 12.6, T_BITE))
    else:
        v = 3600
    if t >= T_RESET:
        v *= 1 - smooth(prog(t, T_RESET, DUR - 0.15))
    return v


def secs_imp(t):
    if T_LEAVE1 <= t < T_RESET:
        return 3540
    if t >= T_RESET:
        return 3540 * (1 - smooth(prog(t, T_RESET, DUR - 0.15)))
    return secs(t)


# ---------------------------------------------------------------- the golden fish
COMMON = [(0.0, 680, 640), (T_TEASE1, 618, 622), (2.2, 780, 690), (3.0, 880, 600), (4.6, 730, 650),
          (6.5, 690, 662), (8.0, 830, 620), (T_TEASE2, 618, 618), (9.6, 740, 700), (11.0, 810, 650), (12.2, 770, 640)]
IMP_TAIL = [(12.85, 612, 616), (16.0, 640, 630), (DUR, 680, 640)]
PAT_TAIL = [(13.5, 720, 632), (14.4, 640, 622), (T_BITE, 612, 616)]
SCARE = [(T_RECAST, 730, 650), (5.2, 960, 710), (6.2, 700, 652)]


def path(keys, t):
    for (a, xa, ya), (b, xb, yb) in zip(keys, keys[1:]):
        if a <= t <= b:
            k = smooth(prog(t, a, b))
            return lerp(xa, xb, k), lerp(ya, yb, k), xb - xa
    return keys[-1][1], keys[-1][2], -1


def fish_state(t, top):
    """list of (x, y, facing, alpha, in_air)"""
    out = []
    if top:
        if T_RECAST <= t < 6.2:
            x, y, dx = path(SCARE, t)
        else:
            x, y, dx = path(COMMON + IMP_TAIL, t)
        out.append((x, y + 6 * math.sin(t * 2.3), -1 if dx < 0 else 1, 1.0, False))
        return out
    if t < T_BITE:
        x, y, dx = path(COMMON + PAT_TAIL, t)
        out.append((x, y + 6 * math.sin(t * 2.3), -1 if dx < 0 else 1, 1.0, False))
    elif t < T_LIFT:
        k = prog(t, T_BITE, T_LIFT)
        x = FLOAT_X + 50 * math.sin(k * 18) * (1 - k)
        y = lerp(616, WATER + 20, k * k)
        out.append((x, y, 1 if math.cos(k * 18) > 0 else -1, 1.0, False))
    elif t < T_COOLER + 0.3:
        # held up in his hands, then dropped into the cooler
        out.append(("held", 0, 1, 1.0, True))
    if t >= T_COOLER:
        x = lerp(1150, FISH0[0], smooth(prog(t, T_COOLER, DUR)))
        y = lerp(670, FISH0[1], smooth(prog(t, T_COOLER, DUR)))
        out.append((x, y + 6 * math.sin(t * 2.3), -1, 1.0, False))
    return out


def draw_fish(d, x, y, face, t, sc=1.0, glow=True, ang=0.0):
    L = 120 * sc
    wag = math.sin(t * 9) * 0.35
    if glow:
        for r, a in ((150, 24), (110, 36), (80, 50)):
            d.ellipse([(x - r * sc) * K, (y - r * 0.6 * sc) * K, (x + r * sc) * K, (y + r * 0.6 * sc) * K],
                      fill=(255, 220, 90, a))

    def P(px, py):
        c, s = math.cos(ang), math.sin(ang)
        px, py = px * face, py
        return (x + px * c - py * s) * K, (y + px * s + py * c) * K
    tail = [P(-L * 0.85, 0), P(-L * 1.35, -L * 0.45 + wag * 30), P(-L * 1.25, 0), P(-L * 1.35, L * 0.45 + wag * 30)]
    d.polygon(tail, fill=(240, 160, 20, 255), outline=INK + (255,), width=int(4 * K))
    body = [P(L * math.cos(a), L * 0.42 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 28)]
    d.polygon(body, fill=GOLD + (255,), outline=INK + (255,), width=int(5 * K))
    fin = [P(-L * 0.2, -L * 0.36), P(L * 0.15, -L * 0.62), P(L * 0.3, -L * 0.36)]
    d.polygon(fin, fill=(240, 160, 20, 255), outline=INK + (255,), width=int(4 * K))
    ex, ey = P(L * 0.62, -L * 0.1)
    d.ellipse([ex - 11 * K * sc, ey - 11 * K * sc, ex + 11 * K * sc, ey + 11 * K * sc], fill=(255, 255, 255, 255),
              outline=INK + (255,), width=int(3 * K))
    d.ellipse([ex - 5 * K * sc, ey - 5 * K * sc, ex + 5 * K * sc, ey + 5 * K * sc], fill=INK + (255,))
    for j in range(3):
        sx, sy = P(-L * 0.4 + j * L * 0.3, L * 0.05)
        d.arc([sx - 18 * K * sc, sy - 18 * K * sc, sx + 18 * K * sc, sy + 18 * K * sc], 300, 60,
              fill=(255, 240, 160, 255), width=int(3 * K))


# ---------------------------------------------------------------- people
STAND = PW.STAND
SIT_ROD = {"head": (8, -150), "neck": (4, -108), "el": (40, -72), "hl": (74, -86), "er": (34, -68), "hr": (66, -80),
           "kl": (62, -2), "fl": (66, 108), "kr": (54, 2), "fr": (56, 110)}
PHONE = dict(SIT_ROD, head=(14, -146), er=(30, -96), hr=(40, -130))
YAWN = dict(SIT_ROD, head=(0, -154), er=(-20, -120), hr=(-30, -160))
GRAB_HEAD = dict(SIT_ROD, el=(-20, -120), hl=(0, -160), er=(20, -120), hr=(10, -162))
REEL = SIT_ROD
PULL = dict(SIT_ROD, head=(-14, -148), neck=(-10, -106), el=(20, -90), hl=(50, -120), er=(14, -86), hr=(40, -112))
HOLD_UP = dict(STAND, el=(40, -96), hl=(84, -118), er=(34, -92), hr=(78, -114))
DROP = dict(STAND, head=(-14, -146), el=(-40, -90), hl=(-80, -60), er=(-36, -86), hr=(-76, -56))
CARRY = dict(STAND, el=(20, -60), hl=(40, -40))
CHEER = dict(STAND, el=(-30, -130), hl=(-40, -180), er=(30, -130), hr=(40, -180))


def walk(t):
    return AJ.walk(t * 9, STAND)


def figure(d, pts, hat):
    for w, col in ((17, INK), (11, WHITE)):
        for b0, b1 in [("neck", "hip"), ("neck", "el"), ("el", "hl"), ("neck", "er"), ("er", "hr"), ("hip", "kl"),
                       ("kl", "fl"), ("hip", "kr"), ("kr", "fr")]:
            (x0, y0), (x1, y1) = pts[b0], pts[b1]
            d.line([x0 * K, y0 * K, x1 * K, y1 * K], fill=col + (255,), width=int(w * K))
            for x, y in ((x0, y0), (x1, y1)):
                r = w * K / 2
                d.ellipse([x * K - r, y * K - r, x * K + r, y * K + r], fill=col + (255,))
    hx, hy = pts["head"]
    for r, col in ((33, INK), (28, WHITE)):
        d.ellipse([(hx - r) * K, (hy - r) * K, (hx + r) * K, (hy + r) * K], fill=col + (255,))
    if hat:
        col, kind = hat
        if kind == "cap":
            d.chord([(hx - 31) * K, (hy - 36) * K, (hx + 31) * K, (hy + 18) * K], 180, 360, fill=col + (255,),
                    outline=INK + (255,), width=int(3 * K))
            d.rectangle([(hx) * K, (hy - 12) * K, (hx + 46) * K, (hy - 4) * K], fill=col + (255,),
                        outline=INK + (255,), width=int(2 * K))
        else:
            d.polygon([((hx - 44) * K, (hy - 10) * K), ((hx + 44) * K, (hy - 10) * K), ((hx + 26) * K, (hy - 34) * K),
                       ((hx - 26) * K, (hy - 34) * K)], fill=col + (255,), outline=INK + (255,))
            d.rectangle([(hx - 26) * K, (hy - 52) * K, (hx + 26) * K, (hy - 30) * K], fill=col + (255,),
                        outline=INK + (255,), width=int(3 * K))


def person_state(t, top):
    """pose, hip, facing, holds_rod, rod_tip_override, hat_on"""
    hip = HIP
    if top:
        if t < T_NIBBLE - 1.0:
            return SIT_ROD, hip, 1, True, True
        if t < T_RECAST - 0.4:
            k = math.sin(math.pi * prog(t, T_NIBBLE - 1.0, T_RECAST - 0.4))
            return lerp_pose(SIT_ROD, PHONE, min(1, k * 1.5)), hip, 1, True, True
        if t < T_GULL - 0.2:
            return SIT_ROD, hip, 1, True, True
        if t < 8.2:
            k = math.sin(math.pi * prog(t, T_GULL - 0.2, 8.2))
            return lerp_pose(SIT_ROD, GRAB_HEAD, min(1, k * 1.8)), hip, 1, True, False
        if t < T_REEL:
            k = math.sin(math.pi * prog(t, 8.4, 9.6)) if t > 8.4 else 0
            return lerp_pose(SIT_ROD, YAWN, k), hip, 1, True, False
        if t < T_STAND:
            a = (t - T_REEL) * 18
            return dict(SIT_ROD, er=(34 + 10 * math.cos(a), -68 + 10 * math.sin(a)),
                        hr=(66 + 16 * math.cos(a), -80 + 16 * math.sin(a))), hip, 1, True, False
        if t < T_LEAVE0:
            k = smooth(prog(t, T_STAND, T_STAND + 0.4))
            return lerp_pose(SIT_ROD, CARRY, k), (hip[0], lerp(hip[1], DOCK_Y - 113 * S, k)), -1, False, False
        if t < T_LEAVE1:
            return walk(t), (lerp(hip[0], -120, prog(t, T_LEAVE0, T_LEAVE1)), DOCK_Y - 113 * S), -1, False, False
        if t < T_BACK0:
            return None
        if t < T_BACK1:
            return walk(t), (lerp(-120, hip[0], prog(t, T_BACK0, T_BACK1)), DOCK_Y - 113 * S), 1, False, False
        k = smooth(prog(t, T_BACK1, T_BACK1 + 0.15))
        return lerp_pose(CARRY, SIT_ROD, k), (hip[0], lerp(DOCK_Y - 113 * S, hip[1], k)), 1, True, t >= 17.75
    # patient
    if t < T_BITE:
        b = 2 * math.sin(t * 1.1)
        return dict(SIT_ROD, head=(8, -150 + b)), hip, 1, True, True
    if t < T_LIFT:
        return PULL, hip, 1, True, True
    if t < T_COOLER:
        k = smooth(prog(t, T_LIFT, T_LIFT + 0.25))
        return lerp_pose(PULL, HOLD_UP, k), (hip[0] + 20 * k, lerp(hip[1], DOCK_Y - 113 * S, k)), 1, False, True
    if t < T_COOLER + 0.35:
        return DROP, (hip[0] + 20, DOCK_Y - 113 * S), 1, False, True
    k = smooth(prog(t, T_COOLER + 0.35, T_CAST2))
    return lerp_pose(DROP, SIT_ROD, k), (hip[0] + 20 * (1 - k), lerp(DOCK_Y - 113 * S, hip[1], k)), 1, k > 0.9, True


# ---------------------------------------------------------------- the line
def rod_and_line(t, top, holds):
    """rod tip, float position (or None), hook position (or None), bend 0..1"""
    tip = (560, 96)
    bend = 0.0
    fl = (FLOAT_X, WATER + 3 * math.sin(t * 2.0))
    hk = HOOK
    if not top and T_BITE <= t < T_LIFT:
        bend = 0.6 + 0.2 * math.sin(t * 24)
        k = prog(t, T_BITE, T_LIFT)
        fx, fy, _, _, _ = fish_state(t, False)[0]
        hk = (fx, fy)
        fl = (fx, max(WATER + 10, fy - 30))
    # nibbles and teases
    for t0, depth in ((T_TEASE1, 10), (T_NIBBLE, 18), (T_TEASE2, 14)):
        if t0 - 0.1 <= t < t0 + 0.5:
            fl = (fl[0], fl[1] + depth * math.sin(math.pi * prog(t, t0 - 0.1, t0 + 0.5)) *
                  (0.5 + 0.5 * math.sin(t * 30)))
    if not top and T_BITE - 0.15 <= t < T_BITE + 0.2:
        fl = (fl[0], WATER + 40 * prog(t, T_BITE - 0.15, T_BITE))
    # the impatient recast
    if top and T_RECAST - 0.4 <= t < T_RECAST:
        k = prog(t, T_RECAST - 0.4, T_RECAST)
        fl = (lerp(FLOAT_X, 560, 1 - abs(2 * k - 1)), lerp(WATER, 96, 1 - abs(2 * k - 1)))
        hk = (fl[0], fl[1] + 40)
    # reeling in, gone, casting back
    if top:
        if T_REEL <= t < T_STAND:
            k = prog(t, T_REEL, T_STAND)
            fl = (lerp(FLOAT_X, 560, k), lerp(WATER, 130, k))
            hk = (fl[0], lerp(HOOK[1], 170, k))
        if not holds and t >= T_STAND:
            return None, None, None, 0.0
        if t >= T_BACK1 and t < 17.95:
            k = smooth(prog(t, 17.55, 17.95))
            if t < 17.55:
                return tip, (560, 130), (560, 170), 0.0
            fl = (lerp(560, FLOAT_X, k), lerp(130, WATER, k) - 120 * math.sin(math.pi * k))
            hk = (fl[0], lerp(170, HOOK[1], k))
    else:
        if T_LIFT <= t < T_CAST2 + 0.05:
            return None, None, None, 0.0
        if T_CAST2 <= t < DUR:
            k = smooth(prog(t, T_CAST2 + 0.05, 17.95))
            fl = (lerp(560, FLOAT_X, k), lerp(130, WATER, k) - 120 * math.sin(math.pi * k))
            hk = (fl[0], lerp(170, HOOK[1], k))
    return tip, fl, hk, bend


# ---------------------------------------------------------------- panel
BG = None
FRAME0 = None


def make_bg():
    im = Image.new("RGBA", (PWD * K, PHT * K), (0, 0, 0, 255))
    a = np.zeros((PHT * K, PWD * K, 3), np.float32)
    yy = np.arange(PHT * K)[:, None] / K
    sky = np.clip(yy / WATER, 0, 1)
    top_c, bot_c = np.array([255, 178, 120]), np.array([246, 124, 146])
    a[:] = (top_c * (1 - sky) + bot_c * sky)[:, None, :] if False else 0
    for c in range(3):
        a[..., c] = (top_c[c] * (1 - sky) + bot_c[c] * sky)
    wk = np.clip((yy - WATER) / (PHT - WATER), 0, 1)
    w0, w1 = np.array([60, 140, 160]), np.array([18, 60, 86])
    for c in range(3):
        a[..., c] = np.where(yy >= WATER, w0[c] * (1 - wk) + w1[c] * wk, a[..., c])
    im = Image.fromarray(a.astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    # sun and its reflection
    d.ellipse([(760 - 80) * K, (300 - 80) * K, (760 + 80) * K, (300 + 80) * K], fill=(255, 236, 170, 255))
    for j in range(7):
        y = WATER + 10 + j * 14
        w = 120 - j * 12
        d.rectangle([(760 - w) * K, y * K, (760 + w) * K, (y + 5) * K], fill=(255, 220, 150, 120))
    # far hills
    d.polygon([(0, (WATER - 80) * K), (220 * K, (WATER - 150) * K), (430 * K, (WATER - 90) * K),
               (640 * K, (WATER - 170) * K), (880 * K, (WATER - 100) * K), (PWD * K, (WATER - 140) * K),
               (PWD * K, WATER * K), (0, WATER * K)], fill=(150, 90, 130, 255))
    # light rays under water
    ray = Image.new("RGBA", im.size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(ray)
    for j in range(5):
        x = 420 + j * 140
        rd.polygon([(x * K, WATER * K), ((x + 50) * K, WATER * K), ((x - 80) * K, PHT * K), ((x - 160) * K, PHT * K)],
                   fill=(200, 240, 255, 22))
    im.alpha_composite(ray)
    # lake bed weeds
    for j in range(12):
        x = 420 + j * 55
        d.line([(x * K, PHT * K), ((x + 12) * K, (PHT - 60 - (j * 17) % 40) * K)], fill=(30, 110, 90, 255),
               width=int(6 * K))
    # dock
    d.rectangle([0, (DOCK_Y - 2) * K, DOCK_X1 * K, (DOCK_Y + 22) * K], fill=(150, 96, 56, 255),
                outline=INK + (255,), width=int(3 * K))
    for x in range(0, DOCK_X1, 46):
        d.line([x * K, DOCK_Y * K, x * K, (DOCK_Y + 22) * K], fill=(110, 70, 40, 255), width=int(2 * K))
    for x in (40, 200, 350):
        d.rectangle([(x - 10) * K, (DOCK_Y + 22) * K, (x + 10) * K, (PHT - 30) * K], fill=(110, 70, 40, 255),
                    outline=INK + (255,), width=int(2 * K))
    # cooler
    d.rectangle([60 * K, (DOCK_Y - 60) * K, 140 * K, DOCK_Y * K], fill=(60, 150, 220, 255), outline=INK + (255,),
                width=int(3 * K))
    d.rectangle([56 * K, (DOCK_Y - 70) * K, 144 * K, (DOCK_Y - 56) * K], fill=(245, 245, 245, 255),
                outline=INK + (255,), width=int(3 * K))
    return im


def chair(d, x, folded=False, carried=None):
    if carried:
        cx, cy = carried
        d.rectangle([(cx - 8) * K, (cy - 50) * K, (cx + 8) * K, (cy + 30) * K], fill=(60, 120, 200, 255),
                    outline=INK + (255,), width=int(2 * K))
        return
    d.line([(x - 50) * K, DOCK_Y * K, (x + 40) * K, (DOCK_Y - 140) * K], fill=INK + (255,), width=int(5 * K))
    d.line([(x + 40) * K, DOCK_Y * K, (x - 40) * K, (DOCK_Y - 140) * K], fill=INK + (255,), width=int(5 * K))
    d.rectangle([(x - 60) * K, (DOCK_Y - 150) * K, (x + 50) * K, (DOCK_Y - 132) * K], fill=(60, 120, 200, 255),
                outline=INK + (255,), width=int(3 * K))
    d.rectangle([(x - 66) * K, (DOCK_Y - 250) * K, (x - 50) * K, (DOCK_Y - 140) * K], fill=(60, 120, 200, 255),
                outline=INK + (255,), width=int(3 * K))


def stamp(base, t, t0, t1, s, col, x, y):
    if not (t0 <= t < t1):
        return
    k = hq.pop(t, t0, 0.28) * (1 - smooth(prog(t, t1 - 0.25, t1)))
    if k < 0.05:
        return
    f = font(BOLD, max(4, int(64 * K * k)))
    tw = sum(f.getlength(c) for c in s) + 4 * K * k * (len(s) - 1)
    lay = Image.new("RGBA", (int(tw + 70 * K * k), int(120 * K * k)), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle([0, 0, lay.width - 1, lay.height - 1], int(18 * K * k), fill=(255, 255, 255, 245),
                         outline=col + (255,), width=int(8 * K * k))
    xx = lay.width / 2 - tw / 2
    for c in s:
        ld.text((xx, lay.height / 2 - 40 * K * k), c, font=f, fill=col + (255,))
        xx += f.getlength(c) + 4 * K * k
    lay = lay.rotate(-5, resample=Image.BICUBIC, expand=True)
    base.alpha_composite(lay, (int(x * K - lay.width / 2), int(y * K - lay.height / 2)))


def panel(t, top):
    base = BG.copy()
    lay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    # surface shimmer
    for j in range(10):
        x = (j * 113 + t * 30) % PWD
        d.line([x * K, (WATER + 4) * K, (x + 40) * K, (WATER + 4) * K], fill=(255, 240, 220, 150), width=int(2 * K))
    st = person_state(t, top)
    holds = st[3] if st else False
    tip, fl, hk, bend = rod_and_line(t, top, holds)
    # fish under water (drawn before the line so the line crosses it)
    for fx, fy, face, al, air in fish_state(t, top):
        if fx == "held":
            continue
        draw_fish(d, fx, fy, face, t)
    # ripples
    for t0 in (T_TEASE1, T_NIBBLE, T_TEASE2) + ((T_RECAST,) if top else (T_BITE,)):
        if t0 <= t < t0 + 1.0 and fl:
            u = t - t0
            for j in range(3):
                r = 20 + 120 * u + j * 26
                d.ellipse([(fl[0] - r) * K, (WATER - r * 0.18) * K, (fl[0] + r) * K, (WATER + r * 0.18) * K],
                          outline=(255, 255, 255, int(200 * (1 - u))), width=int(3 * K))
    # the chair
    if st is None or (top and T_LEAVE0 <= t < T_BACK1):
        pass
    else:
        chair(d, CHAIR_X)
    if top and T_STAND + 0.4 <= t < T_LEAVE1 + 0.1 and st:
        pass
    # rod + line
    if st and holds and tip:
        pose, hip, facing, _, hat = st
        pts = AJ.place(pose, hip, facing, S)
        hx, hy = pts["hl"]
        if bend > 0:
            mx = (hx + tip[0]) / 2
            my = (hy + tip[1]) / 2 + 60 * bend
            tipb = (tip[0] - 30 * bend, tip[1] + 140 * bend)
            d.line([(hx * K, hy * K), (mx * K, my * K), (tipb[0] * K, tipb[1] * K)], fill=INK + (255,),
                   width=int(7 * K), joint="curve")
            tip_ = tipb
        else:
            d.line([hx * K, hy * K, tip[0] * K, tip[1] * K], fill=INK + (255,), width=int(7 * K))
            tip_ = tip
        if fl:
            d.line([tip_[0] * K, tip_[1] * K, fl[0] * K, fl[1] * K], fill=(250, 250, 250, 230), width=int(2 * K))
            d.line([fl[0] * K, fl[1] * K, hk[0] * K, hk[1] * K], fill=(230, 240, 250, 170), width=int(2 * K))
            d.arc([(hk[0] - 10) * K, (hk[1] - 4) * K, (hk[0] + 10) * K, (hk[1] + 16) * K], 0, 180, fill=INK + (255,),
                  width=int(3 * K))
            d.ellipse([(hk[0] - 7) * K, (hk[1] + 4) * K, (hk[0] + 7) * K, (hk[1] + 16) * K], fill=(220, 70, 90, 255))
            d.chord([(fl[0] - 13) * K, (fl[1] - 13) * K, (fl[0] + 13) * K, (fl[1] + 13) * K], 180, 360,
                    fill=(230, 40, 40, 255), outline=INK + (255,), width=int(2 * K))
            d.chord([(fl[0] - 13) * K, (fl[1] - 13) * K, (fl[0] + 13) * K, (fl[1] + 13) * K], 0, 180,
                    fill=(255, 255, 255, 255), outline=INK + (255,), width=int(2 * K))
    # the person
    if st:
        pose, hip, facing, _, hat = st
        pts = AJ.place(pose, hip, facing, S)
        hat_spec = None
        if top:
            hat_spec = ((220, 50, 50), "cap") if hat else None
        else:
            hat_spec = ((60, 150, 90), "bucket")
        figure(d, pts, hat_spec)
        if top and T_LEAVE0 <= t < T_BACK1:
            chair(d, 0, carried=pts["hl"])
        if not top and T_LIFT <= t < T_COOLER + 0.3:
            hx, hy = pts["hl"]
            if t < T_COOLER:
                draw_fish(d, hx + 40, hy - 6, 1, t, 0.9, glow=True, ang=-0.25)
            else:
                k = prog(t, T_COOLER, T_COOLER + 0.3)
                draw_fish(d, lerp(hx, 100, k), lerp(hy, DOCK_Y - 70, k), -1, t, 0.9 * (1 - 0.6 * k), glow=False,
                          ang=1.2 * k)
        # phone in hand
        if top and T_NIBBLE - 0.8 <= t < T_RECAST - 0.5:
            hx, hy = pts["hr"]
            d.rectangle([(hx - 8) * K, (hy - 22) * K, (hx + 10) * K, (hy + 6) * K], fill=INK + (255,))
    # the seagull that steals his cap (and brings it back)
    if top:
        gull = None
        if T_GULL - 0.6 <= t < T_GULL + 0.8:
            k = prog(t, T_GULL - 0.6, T_GULL + 0.8)
            hx, hy = AJ.place(SIT_ROD, HIP, 1, S)["head"]
            if k < 0.43:
                gull = (lerp(1100, hx, k / 0.43), lerp(60, hy - 40, k / 0.43), False)
            else:
                gull = (lerp(hx, -100, (k - 0.43) / 0.57), lerp(hy - 40, 40, (k - 0.43) / 0.57), True)
        elif 17.1 <= t < 17.95:
            k = prog(t, 17.1, 17.95)
            hx, hy = AJ.place(SIT_ROD, HIP, 1, S)["head"]
            if k < 0.6:
                gull = (lerp(-100, hx, k / 0.6), lerp(40, hy - 50, k / 0.6), True)
            else:
                gull = (lerp(hx, 1150, (k - 0.6) / 0.4), lerp(hy - 50, 30, (k - 0.6) / 0.4), False)
        if gull:
            gx, gy, cap = gull
            flap = math.sin(t * 24) * 18
            d.polygon([((gx - 46) * K, (gy - flap) * K), (gx * K, (gy + 6) * K), ((gx + 46) * K, (gy - flap) * K),
                       (gx * K, (gy - 4) * K)], fill=(245, 245, 245, 255), outline=INK + (255,), width=int(3 * K))
            d.ellipse([(gx - 16) * K, (gy - 8) * K, (gx + 16) * K, (gy + 12) * K], fill=(245, 245, 245, 255),
                      outline=INK + (255,), width=int(3 * K))
            d.polygon([((gx + 14) * K, gy * K), ((gx + 30) * K, (gy + 4) * K), ((gx + 14) * K, (gy + 8) * K)],
                      fill=(250, 180, 40, 255))
            if cap:
                d.chord([(gx - 18) * K, (gy + 6) * K, (gx + 18) * K, (gy + 34) * K], 180, 360, fill=(220, 50, 50, 255),
                        outline=INK + (255,))
    # "?" over the fish where his hook was
    if top and T_Q <= t < T_BACK0:
        k = hq.pop(t, T_Q, 0.3)
        fx, fy, _, _, _ = fish_state(t, True)[0]
        f = font(BOLD, int(70 * K * k + 4))
        d.text(((fx + 30) * K, (fy - 150) * K), "?", font=f, fill=(255, 255, 255, 255), stroke_width=int(4 * K),
               stroke_fill=INK + (255,))
    base.alpha_composite(lay)
    # label + timer
    lab = "IMPATIENT" if top else "PATIENT"
    tl = Image.new("RGBA", base.size, (0, 0, 0, 0))
    td = ImageDraw.Draw(tl)
    fl_ = font(BOLD, int(34 * K))
    lw = fl_.getlength(lab)
    td.rounded_rectangle([18 * K, 18 * K, 18 * K + lw + 40 * K, 74 * K], int(14 * K), fill=(255, 255, 255, 240),
                         outline=INK + (255,), width=int(3 * K))
    td.text((38 * K, 26 * K), lab, font=fl_, fill=INK + (255,))
    v = secs_imp(t) if top else secs(t)
    stopped = top and T_LEAVE1 <= t < T_RESET
    s = f"{int(v // 60):02d}:{int(v % 60):02d}"
    ft = font(BOLD, int(64 * K))
    tw = ft.getlength(s)
    col = RED if stopped else (INK if v < 3480 else (200, 40, 40))
    td.rounded_rectangle([PWD * K - tw - 70 * K, 14 * K, PWD * K - 18 * K, 100 * K], int(16 * K),
                         fill=(255, 255, 255, 245), outline=INK + (255,), width=int(3 * K))
    td.text((PWD * K - tw - 44 * K, 18 * K), s, font=ft, fill=col + (255,))
    base.alpha_composite(tl)
    # answer stamps (held to the last 1.5 s window), gone before the loop point
    if top:
        stamp(base, t, T_LIFT, T_RESET + 0.3, "LEFT AT 59", RED, PWD / 2, 300)
    else:
        stamp(base, t, T_LIFT + 0.1, T_RESET + 0.3, "CAUGHT IT!", GREEN, PWD / 2 + 160, 260)
    im = hq.downsample(base, PWD, PHT)
    ev = [T_RECAST, T_GULL] if top else [T_BITE, T_LIFT]
    dx, dy = hq.shake(t, ev, 8)
    z = 1.0 + 0.035 * math.sin(math.pi * t / DUR)
    im = hq.camera(im, z, dx, dy)
    ImageDraw.Draw(im).rounded_rectangle([1, 1, PWD - 2, PHT - 2], 16, outline=INK + (255,), width=5)
    return im


def frame(t):
    img = Image.new("RGBA", (W, H), (30, 28, 38, 255))
    band = Image.new("RGBA", (W * K, TITLE_H * K), YEL + (255,))
    bd = ImageDraw.Draw(band)
    for line, y, sz in (("WOULD YOU WAIT", 34, 92), ("60 MIN?", 146, 118)):
        f = font(BOLD, int(sz * K))
        tw = sum(f.getlength(c) for c in line) + 5 * K * (len(line) - 1)
        x = W * K / 2 - tw / 2
        for c in line:
            bd.text((x + 5 * K, y * K + 6 * K), c, font=f, fill=(0, 0, 0, 80))
            bd.text((x, y * K), c, font=f, fill=INK + (255,))
            x += f.getlength(c) + 5 * K
    img.alpha_composite(band.resize((W, TITLE_H), Image.LANCZOS), (0, 0))
    img.alpha_composite(panel(t, True), (PX0, PANEL_Y[0]))
    img.alpha_composite(panel(t, False), (PX0, PANEL_Y[1]))
    return np.asarray(img.convert("RGB"))


def init_worker():
    global BG
    BG = make_bg()


def render(i):
    t = i / FPS
    return frame(t).tobytes()


# ---------------------------------------------------------------- sound
def splash(fx, at, g=0.15, seed=1):
    mix_in(fx, noise(0.5, seed, lo=300, hi=6000) * env(int(0.5 * SR), 0.003, 0.18), at, g)
    mix_in(fx, tone(220, 0.2, (1, 0.5), a=0.002, d=0.08, sweep=120), at, g * 0.5)


def bloop(fx, at, g=0.06):
    mix_in(fx, tone(520, 0.12, (1,), a=0.002, d=0.05, sweep=900), at, g)


def audio():
    n = int(DUR * SR)
    fx = np.zeros((n, 2))
    mus = music.score(MUSIC, DUR, t_end=T_BITE, t_warm=T_LIFT + 0.05, t_line=T_LIFT + 0.3, start=0.0, loud=1.0)
    # lake bed: lapping water, birds - continuous so the loop is seamless
    tt = np.arange(n) / SR
    lap = noise(DUR, 3, lo=80, hi=700) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.4 * tt))
    fx[:, 0] += 0.03 * lap
    fx[:, 1] += 0.03 * lap
    for j, t0 in enumerate((0.8, 5.6, 9.9, 14.2)):
        for k2 in range(3):
            mix_in(fx, tone(2600 + 300 * k2, 0.08, (1,), a=0.003, d=0.04, sweep=3200), t0 + k2 * 0.12, 0.02, 0.5)
    # the hook: a soft bloop + a low swell under the golden fish from frame 0
    bloop(fx, 0.0, 0.07)
    mix_in(fx, tone(55, 1.6, (1, 0.5), a=0.3, d=1.0), 0.0, 0.12)
    # timer ticks speeding up as 60:00 nears
    tt0 = 0.0
    while tt0 < T_BITE:
        step = 0.5 if tt0 < 11 else (0.35 if tt0 < 12.6 else 0.25)
        mix_in(fx, tone(1900, 0.03, (1,), a=0.0005, d=0.01), tt0, 0.025 if tt0 < 12.6 else 0.04, 0.3)
        tt0 += step
    for t0 in (T_TEASE1, T_TEASE2):
        mix_in(fx, noise(0.8, int(t0 * 10), lo=100, hi=900) * np.sin(np.linspace(0, np.pi, int(0.8 * SR))), t0 - 0.4,
               0.08)
        bloop(fx, t0, 0.05)
    for j in range(3):
        bloop(fx, T_NIBBLE + j * 0.12, 0.05)
    splash(fx, T_RECAST, 0.16, 4)
    mix_in(fx, noise(0.5, 6, lo=400, hi=4000) * np.sin(np.linspace(0, np.pi, int(0.5 * SR))), T_RECAST - 0.4, 0.06)
    # seagull squawks
    for t0 in (T_GULL - 0.1, 17.4):
        for j in range(2):
            mix_in(fx, tone(1300, 0.18, (1, 0.7, 0.5, 0.3), a=0.01, d=0.08, sweep=900), t0 + j * 0.2, 0.05, -0.3)
    # reel ratchet, footsteps
    for j in range(16):
        mix_in(fx, noise(0.02, 40 + j, lo=2000, hi=7000) * env(int(0.02 * SR), 0.0005, 0.006), T_REEL + j * 0.036,
               0.08, 0.2)
    for t0 in list(np.arange(T_LEAVE0, T_LEAVE1, 0.3)) + list(np.arange(T_BACK0, T_BACK1, 0.3)):
        mix_in(fx, tone(140, 0.08, (1, 0.5), a=0.002, d=0.03), t0, 0.05, -0.2)
    # the "?" plink and a sad trombone note, then a heartbeat for the last minute
    for j, f in enumerate((660, 880)):
        mix_in(fx, tone(f, 0.15, (1, 0.4), a=0.002, d=0.06), T_Q + j * 0.12, 0.05)
    mix_in(fx, tone(196, 0.9, (1, 0.7, 0.5, 0.3), a=0.02, d=0.5, sweep=170), T_Q + 0.3, 0.05)
    for j in range(4):
        for k2, dt in enumerate((0.0, 0.18)):
            mix_in(fx, tone(48, 0.2, (1, 0.5), a=0.003, d=0.08), 13.5 + j * 0.4 + dt, 0.15 - 0.06 * k2)
    # the bite: float plunges, reel screams, the lift
    splash(fx, T_BITE, 0.2, 7)
    reel = np.sin(2 * np.pi * np.cumsum(np.full(int(1.0 * SR), 900.0) + 300 * np.sin(np.arange(int(1.0 * SR)) / SR *
                                                                                     2 * np.pi * 14)) / SR)
    mix_in(fx, np.sign(reel) * 0.4 * env(int(1.0 * SR), 0.01, 0.6), T_BITE + 0.05, 0.05, 0.2)
    splash(fx, T_LIFT, 0.3, 8)
    for j, m in enumerate((72, 76, 79, 84, 88)):
        mix_in(fx, music.music_box(midi(m), 1.2), T_LIFT + 0.08 + 0.06 * j, 0.07)
    for t0 in (T_LIFT, T_LIFT + 0.1):
        mix_in(fx, tone(70, 0.4, (1, 0.5), a=0.002, d=0.2) + 0.3 * noise(0.4, int(t0 * 100), lo=400, hi=5000) *
               env(int(0.4 * SR), 0.002, 0.1), t0, 0.14)
    mix_in(fx, tone(120, 0.2, (1, 0.5), a=0.001, d=0.06), T_COOLER + 0.3, 0.14)      # cooler lid
    # reset: timers spin back, both cast
    for j in range(14):
        mix_in(fx, tone(1500 - 60 * j, 0.03, (1,), a=0.0005, d=0.01), T_RESET + j * 0.05, 0.03)
    for t0 in (17.6, 17.95):
        mix_in(fx, noise(0.3, int(t0 * 10), lo=400, hi=4000) * np.sin(np.linspace(0, np.pi, int(0.3 * SR))), t0 - 0.3,
               0.05)
    x = mus + fx
    m = int(0.35 * SR)
    k = np.linspace(0, 1, m)[:, None]
    x[-m:] = x[-m:] * (1 - k) + x[:m] * k
    x /= max(1.0, np.abs(x).max() / 0.9)
    return x


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "fishing.mp4"
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
