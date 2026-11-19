#!/usr/bin/env python3
"""IDEAS.md #1 - "I'M 5 MINUTES AWAY". Split screen in the channel's current style, 18 s, loops on itself.

Above, HIM, still in bed: "I'M 5 MINUTES AWAY". Below, YOU at the café, the chair across empty: "OK!".
The red clock in the middle runs 18:00 -> 18:52 and your WAITING box counts the minutes. He gets up, showers singing
(a wet hand comes out of the bathroom door: "ALMOST THERE!"), hunts for a sock among flying clothes ("LEAVING NOW"),
eats cereal standing ("PARKING", mouth full: "MMF."), grabs his keys and goes ("2 MIN"). Below, a coffee, a second,
a third, a fourth; chin on hand; head on the table, asleep. He walks into the café: "TRAFFIC WAS CRAZY."
"5 MINUTES IS A FEELING. / NOT A TIME."  FOLLOW FOR MORE.

    python3 stick/five_minutes.py stick/five-minutes.mp4
    ONLY_FRAMES=0.3,1.0,4.8,7.8,10.4,12.6,14.6,16.6,17.4 python3 stick/five_minutes.py /tmp/fm
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
import one_call as OC  # noqa  (the split layout, the speech bubbles, the piano)
from perfect_wave import (MONO, clamp, env, font, lerp, lerp_pose, midi, mix_in, noise, out_back, out_cubic,  # noqa
                          prog, rot, smooth, spaced, tone, write_wav)

W, H, FPS = 1080, 1920, 30
SR = 44100
BPM = 100
BEAT = 60 / BPM
BAR = 4 * BEAT
DUR = 7.5 * BAR                         # 18 s
NF = int(round(DUR * FPS))
XFADE = 0.45
SC = AJ.SC
INK = AJ.INK
HIM, HIM_FAR = AJ.OT, AJ.OT_FAR
YOU, YOU_FAR = AJ.DOER, AJ.DOER_FAR
RED = (255, 64, 56)
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

PH, TOP_Y0, BOT_Y0, STRIP_Y, FYP = OC.PH, OC.TOP_Y0, OC.BOT_Y0, OC.STRIP_Y, OC.FYP
STAND_Y = FYP - 113 * SC

# ---------------------------------------------------------------- his flat
BED = (30, 330)                          # x range; mattress top FYP-120
BATH = (420, 560)                        # the bathroom door
DRESSER = (610, 760)
COUNTER = (820, 1060)

# ---------------------------------------------------------------- timeline
MSGS = [(0.7, "I'M 5 MINUTES AWAY"), (4.6, "ALMOST THERE!"), (8.2, "LEAVING NOW"), (10.2, "PARKING"), (12.3, "2 MIN")]
MSG_HOLD = 1.3
T_UP0, T_UP1 = 2.2, 2.8
T_TOBATH0, T_TOBATH1 = 2.8, 3.4
T_SHOWER0, T_SHOWER1 = 3.5, 6.1
T_TODRESS0, T_TODRESS1 = 6.3, 6.9
T_SOCK0, T_SOCK1 = 6.9, 9.0
T_TOCOUNT0, T_TOCOUNT1 = 9.0, 9.4
T_EAT0, T_EAT1 = 9.4, 11.4
T_OUT0, T_OUT1 = 11.6, 12.4
T_IN0, T_IN1 = 13.5, 14.3               # he walks into the café
T_CLOCK0, T_CLOCK1 = 0.7, 14.3          # 18:00 -> 18:52
CUPS = [0.0, 4.0, 7.4, 10.4]
T_CHIN, T_SLUMP, T_SLEEP = 6.8, 10.6, 12.2
T_L1, T_L2 = 15.0, 16.35
CPS = 18.0
LINE1, LINE2 = "5 MINUTES IS A FEELING.", "NOT A TIME."
T_FOLLOW = 17.05

BUB_HIM = [(7.3, 8.7, "WHERE'S MY SOCK?", "me"), (10.6, 11.3, "MMF.", "me")]
BUB_YOU = [(1.35, 2.3, "OK!", "me"), (5.4, 6.3, "...", "me")]
BUB_HIM_CAFE = [(14.3, 15.9, "TRAFFIC WAS CRAZY.", "me")]


def minutes(t):
    return int(round(52 * prog(t, T_CLOCK0, T_CLOCK1) ** 1.15))


# ---------------------------------------------------------------- poses (facing right)
STAND = PW.STAND
LIE_BED = {"head": (-110, -40), "neck": (-70, -30), "el": (-40, -70), "hl": (-50, -110), "er": (-36, -66),
           "hr": (-46, -106), "kl": (56, -6), "fl": (116, 0), "kr": (56, 2), "fr": (116, 8)}
STRETCH = dict(STAND, el=(-20, -150), hl=(-30, -200), er=(20, -150), hr=(30, -200))
PHONE = dict(STAND, el=(26, -66), hl=(44, -100), er=(22, -62), hr=(40, -96))
SEARCH = dict(STAND, head=(40, -120), neck=(30, -84), el=(60, -60), hl=(86, -40), er=(56, -56), hr=(82, -36),
              kl=(-10, 56), fl=(-26, 113), kr=(20, 56), fr=(34, 113))
THROW = dict(SEARCH, el=(20, -120), hl=(-10, -160))
EAT = dict(STAND, el=(30, -60), hl=(44, -40), er=(30, -100), hr=(18, -132))
EAT_DOWN = dict(EAT, er=(36, -70), hr=(50, -50))
WAVE = dict(STAND, er=(36, -140), hr=(56, -186))
SIT = OC.SIT
SIT_PHONE = OC.SIT_PHONE
TAP = dict(AJ.SIT_TYPE, el=(40, -70), hl=(76, -60), er=(36, -66), hr=(72, -56))
CHIN = dict(AJ.SIT_TYPE, head=(22, -142), neck=(14, -102), el=(56, -82), hl=(40, -128), er=(46, -70), hr=(76, -60))
SLUMP = dict(CHIN, head=(34, -128), neck=(22, -94))
SLEEP = dict(AJ.SIT_TYPE, head=(74, -96), neck=(48, -78), el=(70, -60), hl=(100, -72), er=(66, -56), hr=(96, -68))


def him(t):
    """(pose, x, y(hip), facing, prop, visible) in his flat; None after he leaves."""
    if t < T_UP0:
        return LIE_BED, 190, FYP - 150, 1, "phone_up", 1.0
    if t < T_UP1:
        k = smooth(prog(t, T_UP0, T_UP1))
        p = lerp_pose(LIE_BED, STRETCH, k)
        return p, lerp(190, 360, k), lerp(FYP - 150, STAND_Y, k), 1, None, 1.0
    if t < T_TOBATH1:
        x = lerp(360, (BATH[0] + BATH[1]) / 2, smooth(prog(t, T_TOBATH0, T_TOBATH1)))
        return AJ.walk(t * 7, STAND), x, STAND_Y, 1, None, 1.0
    if t < T_SHOWER1:
        return STAND, (BATH[0] + BATH[1]) / 2, STAND_Y, 1, None, 0.0
    if t < T_TODRESS1:
        x = lerp((BATH[0] + BATH[1]) / 2, (DRESSER[0] + DRESSER[1]) / 2 - 90, smooth(prog(t, T_TODRESS0, T_TODRESS1)))
        return AJ.walk(t * 7, STAND), x, STAND_Y, 1, "towel", 1.0
    if t < T_SOCK1:
        u = (t - T_SOCK0) * 3.2
        p = lerp_pose(SEARCH, THROW, max(0.0, math.sin(u * math.pi)) ** 2)
        return p, (DRESSER[0] + DRESSER[1]) / 2 - 90, STAND_Y, 1, "towel", 1.0
    if t < T_TOCOUNT1:
        x = lerp((DRESSER[0] + DRESSER[1]) / 2 - 90, COUNTER[0] - 20, smooth(prog(t, T_TOCOUNT0, T_TOCOUNT1)))
        return AJ.walk(t * 7, STAND), x, STAND_Y, 1, "sock", 1.0
    if t < T_EAT1:
        k = 0.5 + 0.5 * math.sin((t - T_EAT0) * 9)
        p = lerp_pose(EAT_DOWN, EAT, k)
        if 10.15 <= t < 10.6:
            p = PHONE
        return p, COUNTER[0] - 20, STAND_Y, 1, "bowl" if not (10.15 <= t < 10.6) else "phone", 1.0
    if t < T_OUT1:
        x = lerp(COUNTER[0] - 20, 1200, smooth(prog(t, T_OUT0, T_OUT1)))
        return AJ.walk(t * 8, STAND), x, STAND_Y, 1, "keys", 1.0
    return None


def you(t):
    hip = (380, FYP - 115 * SC)
    if t < 1.3 or 1.3 <= t < 2.4:
        return (SIT_PHONE if t < 2.4 else SIT), hip, 1, "phone"
    if t < T_CHIN:
        k = 0.5 + 0.5 * math.sin(t * 10)
        return lerp_pose(TAP, dict(TAP, hr=(72, -66)), k), hip, 1, None
    if t < T_SLUMP:
        k = smooth(prog(t, T_CHIN, T_CHIN + 0.4))
        return lerp_pose(TAP, CHIN, k), hip, 1, None
    if t < T_SLEEP:
        k = smooth(prog(t, T_SLUMP, T_SLUMP + 1.0))
        return lerp_pose(CHIN, SLUMP, k), hip, 1, None
    k = smooth(prog(t, T_SLEEP, T_SLEEP + 0.5))
    return lerp_pose(SLUMP, SLEEP, k), hip, 1, "sleep"


def him_cafe(t):
    if t < T_IN0:
        return None
    if t < T_IN1:
        x = lerp(1180, 800, smooth(prog(t, T_IN0, T_IN1)))
        return AJ.walk(t * 7, STAND), x, STAND_Y, -1
    k = smooth(prog(t, T_IN1, T_IN1 + 0.3))
    return lerp_pose(STAND, WAVE, k), 800, STAND_Y, -1


# ---------------------------------------------------------------- the two rooms
def build_flat():
    yy, xx = np.mgrid[0:PH, 0:W].astype(np.float32)
    img = np.zeros((PH, W, 3), np.float32) + 8
    for lx in (200, 700):
        img += (np.exp(-(((xx - lx) / 340) ** 2 + ((yy - 300) / 300) ** 2)) * 36)[..., None] * np.array([1.0, 0.85, 0.6])
    img = np.where((yy > FYP)[..., None], img * 0.8 + 8, img)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    ink = INK + (255,)
    d.line([(0, FYP), (W, FYP)], fill=(46, 44, 44, 255), width=2)
    # bed
    d.rounded_rectangle([BED[0], FYP - 270, BED[0] + 30, FYP], 8, fill=(80, 64, 52, 255), outline=ink, width=3)
    d.rounded_rectangle([BED[0] + 20, FYP - 120, BED[1], FYP - 60], 10, fill=(214, 214, 220, 255), outline=ink, width=3)
    d.rectangle([BED[0] + 20, FYP - 60, BED[1], FYP - 30], fill=(80, 64, 52, 255), outline=ink, width=3)
    d.rounded_rectangle([BED[0] + 36, FYP - 150, BED[0] + 120, FYP - 112], 12, fill=(236, 236, 240, 255), outline=ink,
                        width=3)
    # bathroom door with a frosted window
    x0, x1 = BATH
    d.rectangle([x0 - 10, FYP - 330, x1 + 10, FYP], fill=(54, 50, 48, 255), outline=ink, width=4)
    d.rectangle([x0, FYP - 320, x1, FYP], fill=(120, 100, 82, 255), outline=ink, width=3)
    d.rectangle([x0 + 24, FYP - 290, x1 - 24, FYP - 170], fill=(170, 190, 200, 255), outline=ink, width=3)
    d.ellipse([x1 - 30, FYP - 160, x1 - 16, FYP - 146], fill=(214, 190, 120, 255), outline=ink, width=2)
    # dresser
    x0, x1 = DRESSER
    d.rectangle([x0, FYP - 170, x1, FYP], fill=(110, 82, 58, 255), outline=ink, width=4)
    for i in range(3):
        y = FYP - 160 + i * 52
        d.rectangle([x0 + 10, y, x1 - 10, y + 44], outline=ink, width=3)
        d.ellipse([(x0 + x1) / 2 - 6, y + 16, (x0 + x1) / 2 + 6, y + 28], fill=(214, 190, 120, 255))
    # counter + cereal box
    x0, x1 = COUNTER
    d.rectangle([x0, FYP - 160, x1, FYP], fill=(90, 92, 100, 255), outline=ink, width=4)
    d.rectangle([x0 - 6, FYP - 172, x1 + 6, FYP - 156], fill=(200, 198, 190, 255), outline=ink, width=3)
    d.rectangle([x0 + 150, FYP - 260, x0 + 200, FYP - 172], fill=(230, 160, 60, 255), outline=ink, width=3)
    spaced(d, x0 + 175, FYP - 240, "O's", font("Inter-Bold.otf", 18), (255, 255, 255, 255), 0)
    # a window
    d.rectangle([700, 60, 900, 220], fill=(30, 40, 70, 255), outline=ink, width=6)
    d.line([(800, 60), (800, 220)], fill=ink, width=5)
    return im


def build_cafe():
    yy, xx = np.mgrid[0:PH, 0:W].astype(np.float32)
    img = np.zeros((PH, W, 3), np.float32) + np.array([16, 12, 10], np.float32)
    img += (np.exp(-(((xx - 520) / 360) ** 2 + ((yy - 420) / 280) ** 2)) * 46)[..., None] * np.array([1.0, 0.8, 0.55])
    img = np.where((yy > FYP)[..., None], img * 0.8 + np.array([20, 14, 10], np.float32), img)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    ink = INK + (255,)
    d.line([(0, FYP), (W, FYP)], fill=(60, 48, 40, 255), width=2)
    # menu board, a pendant lamp, a plant
    d.rounded_rectangle([60, 70, 300, 230], 8, fill=(26, 34, 30, 255), outline=(110, 90, 70, 255), width=6)
    spaced(d, 180, 84, "CAFÉ", font("Inter-Bold.otf", 34), (240, 236, 220, 255), 6)
    for i, s in enumerate(("LATTE  3.5", "MOCHA  4.0", "TEA    2.5")):
        d.text((88, 136 + i * 28), s, font=font(MONO, 20), fill=(220, 214, 196, 255))
    d.line([(520, 0), (520, 120)], fill=(70, 66, 62, 255), width=3)
    d.polygon([(480, 160), (560, 160), (540, 120), (500, 120)], fill=(60, 52, 46, 255), outline=ink)
    d.ellipse([506, 152, 534, 170], fill=(255, 226, 170, 255))
    d.rectangle([960, FYP - 90, 1020, FYP], fill=(120, 80, 54, 255), outline=ink, width=3)
    for (cx, cy, r) in ((990, FYP - 130, 40), (960, FYP - 160, 30), (1020, FYP - 160, 30)):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(60, 120, 70, 255), outline=ink, width=3)
    # the table and the chair across (empty)
    d.ellipse([440, FYP - 196, 660, FYP - 168], fill=(150, 108, 72, 255), outline=ink, width=4)
    d.rectangle([540, FYP - 172, 560, FYP], fill=(90, 66, 46, 255), outline=ink, width=3)
    d.ellipse([480, FYP - 14, 620, FYP + 6], fill=(90, 66, 46, 255), outline=ink, width=3)
    for cx, back in ((290, -1), (760, 1)):
        d.rectangle([cx - 50, FYP - 128, cx + 50, FYP - 112], fill=(120, 84, 56, 255), outline=ink, width=3)
        bx = cx - 50 if back < 0 else cx + 40
        d.rectangle([bx, FYP - 270, bx + 12, FYP - 112], fill=(120, 84, 56, 255), outline=ink, width=3)
        for lx in (cx - 44, cx + 34):
            d.rectangle([lx, FYP - 112, lx + 10, FYP], fill=(100, 70, 48, 255))
    return im


def draw_cups(d, t):
    ink = INK + (255,)
    n = sum(1 for c in CUPS if t >= c)
    for i in range(n):
        x = 470 + i * 44
        pop = out_back(prog(t, CUPS[i], CUPS[i] + 0.25)) if CUPS[i] > 0 else 1.0
        h = 42 * pop
        d.polygon([(x, FYP - 196), (x + 32, FYP - 196), (x + 28, FYP - 196 - h), (x + 4, FYP - 196 - h)],
                  fill=(240, 236, 228, 255), outline=ink)
        d.arc([x + 22, FYP - 196 - h * 0.8, x + 44, FYP - 196 - h * 0.3], 270, 90, fill=ink, width=3)
        if i == n - 1 and t - CUPS[i] < 2.5:
            for j in range(2):
                ph = (t * 0.8 + j * 0.5) % 1.0
                sx = x + 12 + 8 * math.sin(t * 3 + j)
                d.line([(sx, FYP - 196 - h - 6 - 30 * ph), (sx + 4, FYP - 196 - h - 18 - 30 * ph)],
                       fill=(220, 220, 220, int(160 * (1 - ph))), width=3)


def flying_clothes(d, t):
    ink = INK + (255,)
    if not (T_SOCK0 <= t < T_SOCK1 + 1.2):
        if t < T_SOCK0:
            return
    items = [(7.05, (220, 70, 70), "shirt"), (7.4, (70, 110, 200), "pants"), (7.75, (240, 200, 60), "shirt"),
             (8.1, (120, 200, 120), "shirt"), (8.45, (240, 240, 240), "sock")]
    for i, (t0, col, kind) in enumerate(items):
        if t < t0:
            continue
        tau = min(t - t0, 0.7)
        x0, y0 = (DRESSER[0] + DRESSER[1]) / 2 - 30, FYP - 220
        vx = [-380, -260, 300, -150, 200][i]
        x = x0 + vx * tau
        y = y0 - 420 * tau + 0.5 * 1500 * tau * tau
        y = min(y, FYP - 10)
        if kind == "shirt":
            d.polygon([(x - 26, y - 14), (x + 26, y - 14), (x + 36, y), (x + 20, y + 4), (x + 20, y + 26), (x - 20, y + 26),
                       (x - 20, y + 4), (x - 36, y)], fill=col + (255,), outline=ink)
        elif kind == "pants":
            d.polygon([(x - 20, y - 20), (x + 20, y - 20), (x + 22, y + 26), (x + 4, y + 26), (x, y), (x - 4, y + 26),
                       (x - 22, y + 26)], fill=col + (255,), outline=ink)
        else:
            d.polygon([(x - 8, y - 20), (x + 6, y - 20), (x + 6, y + 6), (x + 20, y + 10), (x + 18, y + 20), (x - 8, y + 16)],
                      fill=col + (255,), outline=ink)


def shower(im, d, t):
    if not (T_SHOWER0 <= t < T_SHOWER1 + 0.6):
        return
    k = smooth(prog(t, T_SHOWER0, T_SHOWER0 + 0.4)) * (1 - smooth(prog(t, T_SHOWER1, T_SHOWER1 + 0.6)))
    x0, x1 = BATH
    g = Image.new("RGBA", (420, 360), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    rng = np.random.default_rng(int(t * 6))
    for i in range(10):
        px = 210 + rng.uniform(-90, 90)
        py = 300 - ((t * 60 + i * 37) % 260)
        r = 30 + rng.uniform(0, 30)
        gd.ellipse([px - r, py - r, px + r, py + r], fill=(230, 230, 236, int(70 * k)))
    g = g.filter(ImageFilter.GaussianBlur(14))
    im.alpha_composite(g, (int((x0 + x1) / 2 - 210), int(FYP - 330 - 260)))
    d = ImageDraw.Draw(im)
    # his silhouette in the frosted glass, swaying
    sx = (x0 + x1) / 2 + 8 * math.sin(t * 5)
    d.ellipse([sx - 16, FYP - 280, sx + 16, FYP - 248], fill=(110, 120, 130, int(255 * k)))
    d.rectangle([sx - 10, FYP - 248, sx + 10, FYP - 176], fill=(110, 120, 130, int(255 * k)))
    # singing
    for j in range(3):
        ph = (t * 0.7 + j * 0.33) % 1.0
        nx = x1 + 20 + 40 * ph
        ny = FYP - 300 - 80 * ph
        a = int(255 * k * math.sin(math.pi * ph))
        d.text((nx, ny), "♪", font=font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34), fill=(240, 240, 244, a))
    # the wet hand with the phone out of the door, typing "ALMOST THERE!"
    if 4.3 <= t < 5.6:
        u = smooth(prog(t, 4.3, 4.6)) * (1 - smooth(prog(t, 5.3, 5.6)))
        hx = x0 + 6 - 40 * u
        hy = FYP - 190
        d.line([(x0 + 10, hy), (hx, hy)], fill=INK + (255,), width=26)
        d.line([(x0 + 10, hy), (hx, hy)], fill=HIM + (255,), width=16)
        d.rounded_rectangle([hx - 26, hy - 30, hx - 4, hy + 10], 4, fill=(30, 34, 48, 255), outline=INK + (255,), width=3)
        d.rectangle([hx - 22, hy - 26, hx - 8, hy + 6], fill=(140, 200, 255, 255))
        for j in range(3):
            d.ellipse([hx - 10 + j * 6, hy + 14 + j * 8, hx - 6 + j * 6, hy + 20 + j * 8], fill=(160, 200, 255, 220))


def person(pts, body, far, facing, prop, t):
    cv = AJ.Canvas(*PW.bbox_of(list(pts.values()), 140))
    AJ.draw_stick(cv, pts, body, far, facing)
    P = cv.P
    k = AJ.SS
    ink = INK + (255,)
    if prop == "towel":
        hx, hy = pts["head"]
        q0, q1 = P((hx - 44, hy - 46)), P((hx + 44, hy - 4))
        cv.d.rounded_rectangle([q0[0], q0[1], q1[0], q1[1]], 16 * k, fill=(250, 250, 250, 255), outline=ink, width=3 * k)
    if prop in ("phone", "phone_up"):
        px = (pts["hl"][0] + pts["hr"][0]) / 2
        py = (pts["hl"][1] + pts["hr"][1]) / 2
        q0, q1 = P((px - 13, py - 24)), P((px + 13, py + 24))
        cv.d.rounded_rectangle([q0[0], q0[1], q1[0], q1[1]], 5 * k, fill=(30, 34, 48, 255), outline=ink, width=3 * k)
        s0, s1 = P((px - 9, py - 19)), P((px + 9, py + 19))
        cv.d.rectangle([s0[0], s0[1], s1[0], s1[1]], fill=(140, 200, 255, 255))
    if prop == "bowl":
        bx, by = pts["hl"]
        q0, q1 = P((bx - 30, by - 10)), P((bx + 30, by + 26))
        cv.d.chord([q0[0], q0[1], q1[0], q1[1]], 0, 180, fill=(240, 240, 236, 255), outline=ink, width=3 * k)
        sx, sy = pts["hr"]
        cv.d.line([P((sx, sy)), P((sx + 18, sy + 24))], fill=(200, 200, 210, 255), width=4 * k)
    if prop == "keys":
        kx, ky = pts["hr"]
        q0, q1 = P((kx - 8, ky + 4)), P((kx + 8, ky + 20))
        cv.d.ellipse([q0[0], q0[1], q1[0], q1[1]], outline=(214, 190, 120, 255), width=3 * k)
    return cv.done()


FLAT = CAFE = None
FRAME0 = None


def panel_flat(t):
    im = FLAT.copy()
    d = ImageDraw.Draw(im)
    shower(im, d, t)
    d = ImageDraw.Draw(im)
    st = him(t)
    if st:
        pose, x, y, f, prop, vis = st
        if vis > 0:
            pts = AJ.place(pose, (x, y), f, SC)
            if prop == "phone_up":
                OC.phone_glow(im, pts, "phone")
            spr, off = person(pts, HIM, HIM_FAR, f, prop, t)
            im.alpha_composite(spr, off)
            if prop == "phone_up":
                # the blanket over him in bed
                d = ImageDraw.Draw(im)
                d.rounded_rectangle([BED[0] + 140, FYP - 150, BED[1] + 4, FYP - 66], 20, fill=(96, 110, 150, 255),
                                    outline=INK + (255,), width=3)
            OC.speech_at(im, t, BUB_HIM, pts)
    d = ImageDraw.Draw(im)
    flying_clothes(d, t)
    if t >= T_OUT1:
        # the flat after him: clothes on the floor, the bowl, an empty bed
        pass
    return im


def panel_cafe(t):
    im = CAFE.copy()
    d = ImageDraw.Draw(im)
    pose, hip, f, prop = you(t)
    pts = AJ.place(pose, hip, f, SC)
    if prop == "phone":
        OC.phone_glow(im, pts, "phone")
    spr, off = person(pts, YOU, YOU_FAR, f, prop if prop == "phone" else None, t)
    im.alpha_composite(PW.glow_of(spr, 0.4, 12), off)
    im.alpha_composite(spr, off)
    d = ImageDraw.Draw(im)
    draw_cups(d, t)
    if prop == "sleep":
        for i in range(2):
            ph = (t * 0.7 + i * 0.5) % 1.0
            hx, hy = pts["head"]
            d.text((hx + 10 + 26 * ph + i * 12, hy - 60 - 50 * ph), "z", font=font("Inter-Bold.otf", 26 + 8 * i),
                   fill=(220, 226, 240, int(255 * math.sin(math.pi * ph))))
    OC.speech_at(im, t, BUB_YOU, pts)
    hc = him_cafe(t)
    if hc:
        pose2, x2, y2, f2 = hc
        pts2 = AJ.place(pose2, (x2, y2), f2, SC)
        spr2, off2 = person(pts2, HIM, HIM_FAR, f2, None, t)
        im.alpha_composite(spr2, off2)
        OC.speech_at(im, t, BUB_HIM_CAFE, pts2)
    # the WAITING box
    d = ImageDraw.Draw(im)
    m = minutes(t)
    bx, by = W - 250, 70
    d.rounded_rectangle([bx, by, bx + 220, by + 92], 8, fill=(18, 20, 28, 230), outline=(90, 94, 104, 255), width=2)
    spaced(d, bx + 110, by + 10, "WAITING", font("Inter-SemiBold.otf", 21), (190, 194, 204, 255), 5)
    spaced(d, bx + 110, by + 38, f"{m} MIN", font(MONO, 40), (RED if m > 5 else (240, 240, 244)) + (255,), 1)
    return im


def banner(img, t):
    for t0, msg in MSGS:
        if not (t0 <= t < t0 + MSG_HOLD):
            continue
        u_in = out_cubic(prog(t, t0, t0 + 0.25))
        a = 1 - smooth(prog(t, t0 + MSG_HOLD - 0.22, t0 + MSG_HOLD))
        bw, bh = 640, 104
        x0 = W / 2 - bw / 2
        y0 = STRIP_Y - bh / 2 - 40 * (1 - u_in)
        b = Image.new("RGBA", (bw * 2, bh * 2), (0, 0, 0, 0))
        bd = ImageDraw.Draw(b)
        bd.rounded_rectangle([0, 0, bw * 2 - 1, bh * 2 - 1], 30, fill=(246, 246, 248, 255))
        b = b.reduce(2)
        bd = ImageDraw.Draw(b)
        bd.rounded_rectangle([18, 16, 50, 48], 8, fill=(52, 199, 89, 255))
        bd.rounded_rectangle([25, 24, 43, 38], 4, fill=(255, 255, 255, 255))
        bd.text((64, 16), "ALEX", font=font("Inter-Bold.otf", 26), fill=(20, 20, 24, 255))
        bd.text((bw - 64, 20), "now", font=font("Inter-Regular.otf", 20), fill=(130, 130, 140, 255))
        bd.text((22, 58), msg, font=font(MONO, 28), fill=(30, 30, 36, 255))
        if a < 0.999:
            b.putalpha(b.split()[3].point(lambda v: int(v * a)))
        img.alpha_composite(b, (int(x0), int(y0)))


def frame(t):
    img = Image.new("RGBA", (W, H), (5, 5, 7, 255))
    img.alpha_composite(panel_flat(t), (0, TOP_Y0))
    img.alpha_composite(panel_cafe(t), (0, BOT_Y0))
    d = ImageDraw.Draw(img)
    d.line([(0, STRIP_Y), (W, STRIP_Y)], fill=(56, 56, 62, 255), width=2)
    mm = 18 * 60 + minutes(t)
    s = f"{mm // 60:02d}:{mm % 60:02d}"
    fc = font(BOLD, 66)
    tw = fc.getlength(s)
    d.rounded_rectangle([W / 2 - tw / 2 - 26, STRIP_Y - 50, W / 2 + tw / 2 + 26, STRIP_Y + 50], 10,
                        fill=(16, 6, 6, 255), outline=(90, 24, 22, 255), width=3)
    g = Image.new("RGBA", (int(tw + 120), 160), (0, 0, 0, 0))
    ImageDraw.Draw(g).text((60, 30), s, font=fc, fill=RED + (200,))
    g = g.filter(ImageFilter.GaussianBlur(10))
    img.alpha_composite(g, (int(W / 2 - tw / 2 - 60), int(STRIP_Y - 75)))
    d = ImageDraw.Draw(img)
    d.text((W / 2 - tw / 2, STRIP_Y - 41), s, font=fc, fill=RED + (255,))
    banner(img, t)
    d = ImageDraw.Draw(img)
    fl = font("Inter-SemiBold.otf", 38)
    if t < T_L1:
        spaced(d, W / 2, TOP_Y0 + 14, "HIM", fl, (220, 224, 232, 255), 10)
    spaced(d, W / 2, BOT_Y0 + 14, "YOU", fl, (240, 242, 248, 255), 10)
    fm = font(BOLD, 52)
    for t0, s2, y in ((T_L1, LINE1, 40), (T_L2, LINE2, 106)):
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
    global FLAT, CAFE
    FLAT = build_flat()
    CAFE = build_cafe()


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


# ---------------------------------------------------------------- sound: a light piano pulse that keeps going, ticks
def audio():
    n = int(DUR * SR)
    mus, fx = np.zeros((n, 2)), np.zeros((n, 2))
    eighth = BEAT / 2
    # C major, light and a little impatient: a staccato figure over C - Am - F - G, slowly louder
    figure = [72, 76, 79, 76, 72, 76, 79, 81]
    chords = [[48, 52, 55], [45, 48, 52], [41, 45, 48], [43, 47, 50]]
    shifts = [0, -3, -7, -5]
    t_end = T_IN0
    i, tt = 0, 0.1
    while tt < t_end:
        b = int(tt / BAR) % 4
        g = 0.03 + 0.05 * prog(tt, 0, t_end)
        mix_in(mus, OC.piano(midi(figure[i % 8] + shifts[b]), 0.35, 0.5), tt, g, 0.25)
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
            mix_in(mus, OC.piano(midi(ch[0] - 12), 0.5, 0.3), t0 + q * BEAT, g * 1.4, 0.0)
    # a clock ticking under everything
    for tk in np.arange(0.0, t_end, BEAT):
        mix_in(fx, tone(1500, 0.025, (1,), a=0.001, d=0.008), tk, 0.02)
    # when he finally walks in: a beat of quiet, then a warm chord for the line
    for k, m in enumerate((48, 55, 60, 64)):
        mix_in(mus, GS.pad(midi(m), 3.0, 0.5, 1.6), 14.6, 0.05, (k - 1.5) * 0.4)
    for j, m in enumerate((76, 72, 67, 72)):
        mix_in(mus, OC.piano(midi(m), 1.3, 0.5), 15.0 + j * 0.5, 0.05, 0.2)
    # each message: a soft "ding"
    for t0, msg in MSGS:
        mix_in(fx, OC.piano(midi(88), 0.4, 0.3), t0 + 0.02, 0.07)
        mix_in(fx, OC.piano(midi(84), 0.4, 0.3), t0 + 0.12, 0.07)
    # the shower: soft water, a hummed tune
    sh = noise(T_SHOWER1 - T_SHOWER0, 5, lo=1500, hi=7000)
    tt2 = np.arange(len(sh)) / SR
    sh *= np.minimum(1, tt2 / 0.3) * np.clip((T_SHOWER1 - T_SHOWER0 - tt2) / 0.4, 0, 1)
    mix_in(fx, sh, T_SHOWER0, 0.05, -0.2)
    for j, m in enumerate((67, 69, 71, 72, 71, 69, 67)):
        mix_in(fx, tone(midi(m), 0.3, (1, 0.3), a=0.03, d=0.2), T_SHOWER0 + 0.3 + j * 0.3, 0.025, -0.2)
    # clothes flying: whooshes; cereal: crunches; the door
    for t0 in (7.05, 7.4, 7.75, 8.1, 8.45):
        mix_in(fx, noise(0.25, int(t0 * 100), lo=400, hi=3000) * env(int(0.25 * SR), 0.05, 0.08), t0, 0.06, -0.2)
    for t0 in np.arange(T_EAT0 + 0.2, T_EAT1, 0.7):
        mix_in(fx, noise(0.12, int(t0 * 100) + 3, lo=1500, hi=6000) * env(int(0.12 * SR), 0.002, 0.03), t0, 0.06, -0.2)
    mix_in(fx, noise(0.2, 77, lo=100, hi=1500) * env(int(0.2 * SR), 0.002, 0.06), T_OUT1 - 0.1, 0.12, 0.3)
    # a cup put down each time; a soft snore
    for c in CUPS[1:]:
        mix_in(fx, tone(900, 0.12, (1, 0.4), a=0.001, d=0.04), c, 0.05, 0.2)
    for t0 in np.arange(T_SLEEP + 0.3, T_IN0, 1.0):
        mix_in(fx, noise(0.5, int(t0 * 10), lo=80, hi=500) * env(int(0.5 * SR), 0.2, 0.15), t0, 0.06, 0.2)
    for b0, b1, s, w in BUB_HIM + BUB_YOU + BUB_HIM_CAFE:
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
    out = sys.argv[1] if len(sys.argv) > 1 else "five-minutes.mp4"
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
