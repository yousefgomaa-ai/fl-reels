#!/usr/bin/env python3
"""THE TIPPING SCREEN (queue #4). Split screen, 18 s, loops on itself. Opening: B. Music: harp.

The same café, the same $4 black coffee, the same line behind: "ONE BLACK COFFEE." The cashier turns the iPad:
18% / 20% / 25% / CUSTOM, and smiles. Above, he taps CUSTOM, $1, "THANKS!" - TOTAL $5 - pours his coffee at the
self-serve station and sits down. Below, the cashier stares, the line grows, someone coughs, "UM..." - 25%. Then:
ROUND UP FOR CHARITY? YES. A TIP FOR THE KITCHEN? YES. SUPPORT OUR FARMERS? ...YES. TOTAL $9.80. The cashier hands him an
empty cup: "SELF-SERVE IS OVER THERE." He pours it himself: "...I TIPPED FOR THIS?"
"HE TIPPED THE IPAD. / THEN POURED IT HIMSELF."  FOLLOW FOR MORE.

    python3 stick/tipping.py stick/tipping.mp4
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
import one_call as OC  # noqa
import five_minutes as FM  # noqa
import music  # noqa
from perfect_wave import (MONO, clamp, env, font, lerp, lerp_pose, midi, mix_in, noise, out_back,  # noqa
                          prog, smooth, spaced, tone, write_wav)

VARIANT = os.environ.get("VARIANT", "B").upper()
STRONG = VARIANT == "B"
MUSIC = "harp_bb"

W, H, FPS = 1080, 1920, 30
SR = 44100
DUR = 18.0
NF = int(round(DUR * FPS))
XFADE = 0.45
SC = AJ.SC
INK = AJ.INK
GOOD_C, GOOD_FAR = AJ.DOER, AJ.DOER_FAR
BAD_C, BAD_FAR = AJ.OT, AJ.OT_FAR
CASH_C, CASH_FAR = (240, 190, 110), (200, 150, 80)
CROWD_C, CROWD_FAR = (86, 92, 110), (66, 70, 86)
RED = (255, 64, 56)
BOLD = FM.BOLD
PH, TOP_Y0, BOT_Y0, STRIP_Y, FYP = OC.PH, OC.TOP_Y0, OC.BOT_Y0, OC.STRIP_Y, OC.FYP
STAND_Y = FYP - 141

COUNTER = (520, 860, FYP - 170)
CASHIER = (700, STAND_Y)
IPAD_X = 580
ME = (450, STAND_Y)
STATION = (890, 1050)                     # self-serve table x0, x1
URN_X = 970
TABLE = (40, 170)
POUR_X = 850
SEAT_X = 140

# ---------------------------------------------------------------- timeline
T_TURN = 1.6
# above
T_G_CUSTOM, T_G_ONE, T_G_THANKS = 2.3, 2.7, 3.0
T_G_CUP = 3.8
T_G_WALK0, T_G_WALK1 = 4.3, 5.2
T_G_POUR0, T_G_POUR1 = 5.3, 6.1
T_G_SIT0, T_G_SIT1 = 6.3, 7.9
# below
T_B_25 = 5.8
SCREENS = [(6.4, 7.2, "ROUND UP FOR", "CHARITY?", 6.00), (7.5, 8.3, "ADD A TIP FOR", "THE KITCHEN?", 8.00),
           (8.6, 9.4, "SUPPORT OUR", "FARMERS?", 9.80)]
T_B_CUP = 10.0
T_B_WALK0, T_B_WALK1 = 11.3, 12.2
T_B_POUR0, T_B_POUR1 = 12.3, 13.3
T_L1, T_L2 = 15.0, 16.1
CPS = 18.0
LINE1, LINE2 = "HE TIPPED THE IPAD.", "THEN POURED IT HIMSELF."
T_FOLLOW = 16.95

B0 = -0.3 if STRONG else 0.3
BUB_GOOD = [(B0, 1.3, "ONE BLACK COFFEE.", "me"), (T_G_THANKS, T_G_THANKS + 0.8, "THANKS!", "me"),
            (8.4, 9.6, "PERFECT.", "me")]
BUB_BAD = [(B0, 1.3, "ONE BLACK COFFEE.", "me"), (2.8, 3.8, "UM...", "me"), (6.9, 7.4, "SURE.", "me"),
           (8.0, 8.5, "YES.", "me"), (9.1, 9.7, "...YES.", "me"), (13.6, 14.95, "...I TIPPED FOR THIS?", "me")]
CASH_GOOD = [(1.2, 1.7, "$4.", "me"), (3.4, 4.1, "THANKS!", "me")]
CASH_BAD = [(1.2, 1.7, "$4.", "me"), (T_B_CUP, T_B_CUP + 1.3, "SELF-SERVE IS OVER THERE.", "me")]
LINE_BUBS = [(4.2, 5.0, "AHEM.", "me")]
QUEUE = [(300, 0.0), (200, 2.4), (100, 3.6)]


def total(t, good):
    if good:
        return "$5.00" if t >= T_G_ONE else "$4.00"
    v = 4.00
    if t >= T_B_25:
        v = 5.00
    for a, b, l1, l2, val in SCREENS:
        if t >= b - 0.2:
            v = val
    return f"${v:.2f}"


# ---------------------------------------------------------------- poses
STAND = PW.STAND
TAP = dict(STAND, head=(14, -148), el=(46, -96), hl=(108, -100), er=(14, -58), hr=(18, -10))
HOVER = dict(STAND, head=(10, -148), el=(40, -90), hl=(84, -100), er=(14, -58), hr=(18, -10))
HOLD = dict(STAND, el=(30, -80), hl=(52, -96), er=(14, -58), hr=(18, -10))
POUR = dict(STAND, head=(14, -146), el=(44, -96), hl=(90, -86), er=(36, -86), hr=(84, -80))
SIT = dict(AJ.SIT_TYPE, el=(30, -80), hl=(36, -116), er=(26, -56), hr=(50, -10))
SIP = dict(AJ.SIT_TYPE, el=(30, -96), hl=(20, -132), er=(26, -56), hr=(50, -10))
POINT = dict(STAND, el=(-40, -100), hl=(-90, -110), er=(-10, -60), hr=(-30, -40))
STARE = dict(STAND, head=(-20, -146), neck=(-12, -106))


def walk(t, t0, speed=7.0):
    return AJ.walk((t - t0) * speed, STAND)


def good_person(t):
    """pose, hip, facing, prop"""
    if t < T_G_CUSTOM - 0.2:
        return STAND, ME, 1, None
    if t < T_G_THANKS:
        k = smooth(prog(t, T_G_CUSTOM - 0.2, T_G_CUSTOM))
        tap = math.sin(math.pi * clamp((t - T_G_ONE) / 0.25)) if t > T_G_ONE else 0
        return lerp_pose(STAND, lerp_pose(HOVER, TAP, max(k * 0.6, tap)), k), ME, 1, None
    if t < T_G_CUP:
        return STAND, ME, 1, None
    if t < T_G_WALK0:
        k = smooth(prog(t, T_G_CUP, T_G_CUP + 0.3))
        return lerp_pose(TAP, HOLD, k), ME, 1, "cup_empty"
    if t < T_G_WALK1:
        k = smooth(prog(t, T_G_WALK0, T_G_WALK1))
        p = dict(walk(t, T_G_WALK0), **{j: HOLD[j] for j in ("el", "hl", "er", "hr")})
        return p, (lerp(ME[0], POUR_X, k), STAND_Y), 1, "cup_empty"
    if t < T_G_POUR1:
        k = math.sin(math.pi * prog(t, T_G_POUR0, T_G_POUR1))
        return lerp_pose(HOLD, POUR, k), (POUR_X, STAND_Y), 1, ("cup_empty" if t < (T_G_POUR0 + T_G_POUR1) / 2 else "cup")
    if t < T_G_SIT0:
        return HOLD, (POUR_X, STAND_Y), -1, "cup"
    if t < T_G_SIT1 - 0.4:
        k = smooth(prog(t, T_G_SIT0, T_G_SIT1 - 0.4))
        p = dict(walk(t, T_G_SIT0), **{j: HOLD[j] for j in ("el", "hl", "er", "hr")})
        return p, (lerp(POUR_X, SEAT_X + 40, k), STAND_Y), -1, "cup"
    if t < T_G_SIT1:
        k = smooth(prog(t, T_G_SIT1 - 0.4, T_G_SIT1))
        return lerp_pose(HOLD, SIT, k), (lerp(SEAT_X + 40, SEAT_X, k), lerp(STAND_Y, FYP - 140, k)), 1, "cup"
    ph = (t - T_G_SIT1) % 2.2
    k = math.sin(math.pi * clamp(ph / 0.9)) if ph < 0.9 else 0
    return lerp_pose(SIT, SIP, k), (SEAT_X, FYP - 140), 1, "cup"


def bad_person(t):
    """pose, hip, facing, prop, sweat"""
    sweat = smooth(prog(t, 2.6, 3.2)) * (1 - smooth(prog(t, T_B_CUP + 1.0, T_B_CUP + 1.4)))
    if t < T_TURN:
        return STAND, ME, 1, None, 0
    if t < T_B_25:
        k = smooth(prog(t, 2.0, 2.4))
        wav = 0.5 + 0.5 * math.sin(t * 5)
        p = lerp_pose(STAND, lerp_pose(HOVER, dict(HOVER, hl=(96, -116)), wav), k)
        return p, (ME[0] + 1.5 * math.sin(t * 40) * sweat, STAND_Y), 1, None, sweat
    if t < SCREENS[-1][1]:
        taps = [T_B_25] + [b - 0.4 for a, b, l1, l2, v in SCREENS]
        k = max(math.sin(math.pi * clamp((t - tp) / 0.3)) if t >= tp else 0 for tp in taps)
        return lerp_pose(HOVER, TAP, k), ME, 1, None, sweat
    if t < T_B_CUP:
        return STAND, ME, 1, None, sweat
    if t < T_B_WALK0:
        k = smooth(prog(t, T_B_CUP + 0.6, T_B_CUP + 0.9))
        return lerp_pose(TAP, HOLD, k), ME, 1, ("cup_empty" if t > T_B_CUP + 0.75 else None), sweat
    if t < T_B_WALK1:
        k = smooth(prog(t, T_B_WALK0, T_B_WALK1))
        p = dict(walk(t, T_B_WALK0, 5), **{j: HOLD[j] for j in ("el", "hl", "er", "hr")})
        return p, (lerp(ME[0], POUR_X, k), STAND_Y), 1, "cup_empty", 0
    if t < T_B_POUR1:
        k = math.sin(math.pi * prog(t, T_B_POUR0, T_B_POUR1))
        return lerp_pose(HOLD, POUR, k), (POUR_X, STAND_Y), 1, ("cup_empty" if t < (T_B_POUR0 + T_B_POUR1) / 2 else "cup"), 0
    return lerp_pose(HOLD, dict(HOLD, head=(10, -144)), smooth(prog(t, 13.4, 13.7))), (POUR_X, STAND_Y), -1, "cup", 0


def cashier_pose(t, good):
    if good:
        if T_G_CUP - 0.3 <= t < T_G_CUP + 0.3:
            return dict(STAND, el=(-40, -90), hl=(-90, -96)), None
        return STAND, None
    if T_TURN <= t < T_B_25:
        return lerp_pose(STAND, STARE, smooth(prog(t, 2.2, 3.0))), None
    if T_B_CUP <= t < T_B_CUP + 1.4:
        k = smooth(prog(t, T_B_CUP, T_B_CUP + 0.3))
        return lerp_pose(STAND, POINT, k), None
    return STAND, None


# ---------------------------------------------------------------- drawing
def build_cafe():
    yy, xx = np.mgrid[0:PH, 0:W].astype(np.float32)
    base = np.array((34, 30, 30) if STRONG else (12, 10, 9), np.float32)
    img = np.zeros((PH, W, 3), np.float32) + base
    img = np.where((yy > FYP)[..., None], img * 0.75 + 6, img)
    if STRONG:
        r = np.sqrt((xx - 600) ** 2 + (yy - 40) ** 2)
        img += (np.exp(-(r / 560) ** 2) * 34)[..., None] * np.array([1.0, 0.9, 0.7])
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    ink = INK + (255,)
    d.line([(0, FYP), (W, FYP)], fill=(56, 54, 54, 255), width=2)
    # self-serve station
    x0, x1 = STATION
    d.rectangle([x0, FYP - 150, x1, FYP], fill=(110, 80, 60, 255), outline=ink, width=4)
    d.rounded_rectangle([URN_X - 40, FYP - 290, URN_X + 40, FYP - 150], 14, fill=(190, 194, 204, 255), outline=ink,
                        width=4)
    d.rectangle([URN_X - 52, FYP - 190, URN_X - 30, FYP - 178], fill=(60, 60, 66, 255))
    d.rounded_rectangle([x0 - 10, FYP - 360, x1 + 10, FYP - 310], 8, fill=(250, 250, 252, 255), outline=ink, width=3)
    spaced(d, (x0 + x1) / 2, FYP - 350, "SELF-SERVE", font("Inter-Bold.otf", 22), (30, 30, 34, 255), 2)
    # little table and stool
    tx0, tx1 = TABLE
    d.rectangle([SEAT_X - 50, FYP - 140, SEAT_X + 40, FYP - 124], fill=(150, 110, 76, 255), outline=ink, width=3)
    d.rectangle([SEAT_X - 10, FYP - 124, SEAT_X + 4, FYP], fill=(120, 90, 60, 255))
    # menu board
    d.rounded_rectangle([500, 70, 860, 200], 10, fill=(26, 34, 30, 255), outline=(120, 96, 76, 255), width=8)
    spaced(d, 680, 86, "BLACK COFFEE  $4", font(MONO, 28), (240, 236, 220, 255), 1)
    spaced(d, 680, 136, "LATTE  $7", font(MONO, 28), (220, 216, 200, 255), 1)
    return im


def draw_counter(d):
    ink = INK + (255,)
    x0, x1, cy = COUNTER
    d.rectangle([x0, cy, x1, FYP], fill=(110, 80, 60, 255), outline=ink, width=4)
    d.rectangle([x0, cy, x1, cy + 16], fill=(200, 196, 190, 255), outline=ink, width=3)
    # the iPad on its swivel stand
    d.rectangle([IPAD_X - 4, cy - 40, IPAD_X + 4, cy], fill=(60, 60, 66, 255))


def draw_ipad_small(d, t):
    ink = INK + (255,)
    cy = COUNTER[2]
    k = smooth(prog(t, T_TURN, T_TURN + 0.3))
    w = lerp(70, 10, abs(math.cos(math.pi * k)) * 0 + (1 - k)) if k < 1 else 70
    w = 70 * abs(math.cos(math.pi * k)) if k < 1 else 70
    w = max(8, w)
    d.rounded_rectangle([IPAD_X - w / 2, cy - 100, IPAD_X + w / 2, cy - 40], 6,
                        fill=(30, 32, 40, 255) if k < 0.5 else (240, 244, 250, 255), outline=ink, width=3)


def ipad_card(im, t, good):
    """The big tipping screen, shown as an overlay."""
    if t < T_TURN + 0.1:
        return
    end = T_G_THANKS + 0.4 if good else SCREENS[-1][1]
    if t > end + 0.25:
        return
    k = out_back(prog(t, T_TURN + 0.1, T_TURN + 0.4)) * (1 - smooth(prog(t, end, end + 0.25)))
    if k < 0.05:
        return
    cw, ch = 360, 250
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, cw - 1, ch - 1], 20, fill=(28, 30, 38, 255), outline=(200, 204, 214, 255), width=6)
    d.rounded_rectangle([12, 12, cw - 13, ch - 13], 12, fill=(246, 247, 250, 255))
    screen = None
    if not good:
        for a, b, l1, l2, v in SCREENS:
            if a - 0.15 <= t:
                screen = (a, b, l1, l2)
    if screen is None:
        spaced(d, cw / 2, 26, "ADD A TIP?", font("Inter-Bold.otf", 26), (30, 30, 34, 255), 2)
        opts = ["18%", "20%", "25%", "CUSTOM"]
        sel = None
        if good and t >= T_G_CUSTOM:
            sel = 3
        if not good and t >= T_B_25 - 0.05:
            sel = 2
        for i, o in enumerate(opts):
            x = 26 + (i % 2) * 160
            y = 70 + (i // 2) * 80
            on = sel == i
            d.rounded_rectangle([x, y, x + 148, y + 66], 12, fill=(60, 140, 240, 255) if on else (226, 230, 238, 255))
            label = "$1" if (good and on and t >= T_G_ONE) else o
            spaced(d, x + 74, y + 18, label, font(BOLD, 28), (255, 255, 255, 255) if on else (30, 30, 34, 255), 1)
    else:
        a, b, l1, l2 = screen
        spaced(d, cw / 2, 30, l1, font("Inter-Bold.otf", 26), (30, 30, 34, 255), 2)
        spaced(d, cw / 2, 66, l2, font("Inter-Bold.otf", 26), (30, 30, 34, 255), 2)
        on = t >= b - 0.4
        d.rounded_rectangle([26, 140, 174, 210], 12, fill=(60, 170, 90, 255) if on else (226, 230, 238, 255))
        spaced(d, 100, 160, "YES", font(BOLD, 28), (255, 255, 255, 255) if on else (30, 30, 34, 255), 2)
        d.rounded_rectangle([186, 140, 334, 210], 12, fill=(226, 230, 238, 255))
        spaced(d, 260, 164, "no", font("Inter-SemiBold.otf", 22), (150, 150, 156, 255), 2)
    card = card.resize((max(1, int(cw * k)), max(1, int(ch * k))), Image.LANCZOS)
    im.alpha_composite(card, (int(860 - card.width / 2), int(170 - card.height / 2)))


def draw_prop(d, pts, prop, t):
    ink = INK + (255,)
    if prop in ("cup", "cup_empty"):
        hx, hy = pts["hl"]
        d.polygon([(hx - 16, hy - 40), (hx + 16, hy - 40), (hx + 12, hy + 4), (hx - 12, hy + 4)],
                  fill=(250, 250, 252, 255), outline=ink)
        if prop == "cup":
            d.rectangle([hx - 13, hy - 36, hx + 13, hy - 30], fill=(90, 60, 40, 255))
            for j in range(2):
                ph = (t * 0.8 + j * 0.5) % 1.0
                d.ellipse([hx - 6 + 6 * j, hy - 58 - 30 * ph, hx + 6 + 6 * j, hy - 46 - 30 * ph],
                          fill=(230, 234, 244, int(120 * (1 - ph))))


def pour_stream(d, t, t0, t1):
    if not (t0 + 0.25 <= t < t1 - 0.2):
        return
    d.line([(URN_X - 52, FYP - 184), (URN_X - 60, FYP - 140)], fill=(90, 60, 40, 255), width=5)


def widget(d, x, y, label, value, col):
    d.rounded_rectangle([x, y, x + 220, y + 92], 8, fill=(18, 20, 28, 230), outline=(90, 94, 104, 255), width=2)
    spaced(d, x + 110, y + 10, label, font("Inter-SemiBold.otf", 21), (190, 194, 204, 255), 5)
    spaced(d, x + 110, y + 38, value, font(MONO, 38), col + (255,), 1)


def sprite(pts, body, far, facing):
    cv = AJ.Canvas(*PW.bbox_of(list(pts.values()), 140))
    AJ.draw_stick(cv, pts, body, far, facing)
    return cv.done()


ROOM = None
FRAME0 = None


def panel(t, good):
    im = ROOM.copy()
    # cashier behind the counter
    cpose, _ = cashier_pose(t, good)
    cpts = AJ.place(cpose, CASHIER, -1, SC)
    cspr, coff = sprite(cpts, CASH_C, CASH_FAR, -1)
    im.alpha_composite(cspr, coff)
    d = ImageDraw.Draw(im)
    draw_counter(d)
    draw_ipad_small(d, t)
    # the line behind him
    for i, (x, t_in) in enumerate(QUEUE):
        a = smooth(prog(t, t_in, t_in + 0.4)) if t_in > 0 else 1
        if a < 0.01:
            continue
        leave = (good and t >= T_G_WALK0 - 0.2) or (not good and t >= T_B_WALK0 - 0.2)
        x2 = x + (90 if leave else 0) * smooth(prog(t, (T_G_WALK0 if good else T_B_WALK0) - 0.2,
                                                    (T_G_WALK0 if good else T_B_WALK0) + 0.4))
        if good and i > 0:
            continue
        qpts = AJ.place(STAND, (x2, STAND_Y), 1, SC * 0.96)
        qspr, qoff = sprite(qpts, CROWD_C, CROWD_FAR, 1)
        if a < 0.999:
            qspr.putalpha(qspr.split()[3].point(lambda v, a=a: int(v * a)))
        im.alpha_composite(qspr, qoff)
        if not good and i == 1:
            OC.speech_at(im, t, LINE_BUBS, qpts)
    d = ImageDraw.Draw(im)
    if good:
        pose, hip, facing, prop = good_person(t)
        sweat = 0
    else:
        pose, hip, facing, prop, sweat = bad_person(t)
    pts = AJ.place(pose, hip, facing, SC)
    body, far = (GOOD_C, GOOD_FAR) if good else (BAD_C, BAD_FAR)
    spr, off = sprite(pts, body, far, facing)
    if good:
        im.alpha_composite(PW.glow_of(spr, 0.4, 12), off)
    im.alpha_composite(spr, off)
    d = ImageDraw.Draw(im)
    draw_prop(d, pts, prop, t)
    # the cup the cashier holds out
    if (good and T_G_CUP - 0.3 <= t < T_G_CUP) or (not good and T_B_CUP + 0.2 <= t < T_B_CUP + 0.75):
        hx, hy = cpts["hl"]
        draw_prop(d, {"hl": (hx, hy)}, "cup_empty", t)
    if good:
        pour_stream(d, t, T_G_POUR0, T_G_POUR1)
    else:
        pour_stream(d, t, T_B_POUR0, T_B_POUR1)
    if sweat > 0.05:
        hx, hy = pts["head"]
        dy = 10 * ((t * 1.5) % 1.0)
        d.ellipse([hx - 34, hy - 30 + dy, hx - 22, hy - 12 + dy], fill=(140, 200, 255, int(255 * sweat)),
                  outline=INK + (int(255 * sweat),))
    ipad_card(im, t, good)
    d = ImageDraw.Draw(im)
    if not (STRONG and t < 1.6):
        tot = total(t, good)
        col = (240, 240, 244) if tot == "$4.00" else ((120, 230, 150) if good else (240, 120, 120))
        widget(d, 30, 40, "TOTAL", tot, col)
    OC.speech_at(im, t, BUB_GOOD if good else BUB_BAD, pts)
    OC.speech_at(im, t, CASH_GOOD if good else CASH_BAD, cpts)
    # pressure: the room closes in a little, below
    if not good:
        k = smooth(prog(t, 2.0, 3.5)) * (1 - smooth(prog(t, T_B_25, T_B_25 + 0.4)))
        if k > 0.01:
            yy, xx = np.mgrid[0:PH:4, 0:W:4].astype(np.float32)
            r = np.sqrt(((xx - 520) / W) ** 2 + ((yy - 360) / PH) ** 2)
            a = np.clip((r - 0.25) * 2.2, 0, 1) * 170 * k
            v = Image.fromarray(a.astype(np.uint8), "L").resize((W, PH), Image.BILINEAR)
            dark = Image.new("RGBA", (W, PH), (0, 0, 0, 255))
            dark.putalpha(v)
            im.alpha_composite(dark)
    return im


def zoom(im, t, focus):
    if not STRONG:
        return im
    k = smooth(prog(t, 0.6, 1.8))
    z = lerp(1.32, 1.0, k)
    if z <= 1.001:
        return im
    fx, fy = focus
    cw, ch = W / z, PH / z
    x0 = clamp(fx - cw / 2, 0, W - cw)
    y0 = clamp(fy - ch / 2, 0, PH - ch)
    return im.resize((W, PH), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))


def frame(t):
    img = Image.new("RGBA", (W, H), (5, 5, 7, 255))
    img.alpha_composite(zoom(panel(t, True), t, (600, 420)), (0, TOP_Y0))
    img.alpha_composite(zoom(panel(t, False), t, (600, 420)), (0, BOT_Y0))
    d = ImageDraw.Draw(img)
    d.line([(0, STRIP_Y), (W, STRIP_Y)], fill=(56, 56, 62, 255), width=2)
    s = "COFFEE: $4"
    fc = font(BOLD, 62)
    tw = fc.getlength(s)
    d.rounded_rectangle([W / 2 - tw / 2 - 26, STRIP_Y - 48, W / 2 + tw / 2 + 26, STRIP_Y + 48], 10,
                        fill=(16, 6, 6, 255), outline=(90, 24, 22, 255), width=3)
    g = Image.new("RGBA", (int(tw + 120), 160), (0, 0, 0, 0))
    ImageDraw.Draw(g).text((60, 30), s, font=fc, fill=RED + (200,))
    g = g.filter(ImageFilter.GaussianBlur(10))
    img.alpha_composite(g, (int(W / 2 - tw / 2 - 60), int(STRIP_Y - 72)))
    d = ImageDraw.Draw(img)
    d.text((W / 2 - tw / 2, STRIP_Y - 39), s, font=fc, fill=RED + (255,))
    fl = font("Inter-SemiBold.otf", 38)
    la = smooth(prog(t, 1.5, 1.9)) if STRONG else 1.0
    if la > 0.01:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        if t < T_L1:
            spaced(ld, W / 2, TOP_Y0 + 14, "DECIDES", fl, (240, 242, 248, int(255 * la)), 10)
        spaced(ld, W / 2, BOT_Y0 + 14, "FEELS THE PRESSURE", fl, (220, 224, 232, int(255 * la)), 10)
        img.alpha_composite(lay)
        d = ImageDraw.Draw(img)
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
    global ROOM
    ROOM = build_cafe()


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
    mus = music.score(MUSIC, DUR, t_end=T_B_CUP, start=0.0 if STRONG else 0.2, loud=1.2 if STRONG else 1.0)
    fx = np.zeros((n, 2))
    # a low heartbeat under the pressure
    for tb in np.arange(2.4, T_B_25, 0.75):
        mix_in(fx, tone(55, 0.18, (1, 0.4), a=0.005, d=0.08), tb, 0.12, 0.3)
        mix_in(fx, tone(50, 0.16, (1, 0.4), a=0.005, d=0.07), tb + 0.2, 0.09, 0.3)
    # the iPad swivel, taps, chimes
    mix_in(fx, noise(0.25, 2, lo=600, hi=3000) * env(int(0.25 * SR), 0.05, 0.1), T_TURN, 0.04)
    for tp in (T_G_CUSTOM, T_G_ONE):
        mix_in(fx, tone(1500, 0.06, (1,), a=0.001, d=0.03), tp, 0.04, -0.3)
    for tp in [T_B_25] + [b - 0.4 for a, b, l1, l2, v in SCREENS]:
        mix_in(fx, tone(1500, 0.06, (1,), a=0.001, d=0.03), tp, 0.04, 0.3)
        mix_in(fx, tone(2093, 0.15, (1, 0.3), a=0.002, d=0.08), tp + 0.08, 0.03, 0.3)
    # cough, pouring
    mix_in(fx, noise(0.2, 21, lo=200, hi=2500) * env(int(0.2 * SR), 0.005, 0.08), 4.2, 0.07, 0.4)
    for t0, t1 in ((T_G_POUR0, T_G_POUR1), (T_B_POUR0, T_B_POUR1)):
        d = t1 - t0 - 0.45
        mix_in(fx, noise(d, int(t0 * 10), lo=400, hi=3000) * env(int(d * SR), 0.05, 0.4) * 0.6, t0 + 0.25, 0.04)
    for b0, b1, s, w_ in BUB_GOOD + BUB_BAD + CASH_BAD + LINE_BUBS:
        mix_in(fx, tone(700, 0.07, (1,), a=0.003, d=0.025), max(0.0, b0), 0.025)
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
    out = sys.argv[1] if len(sys.argv) > 1 else "tipping.mp4"
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
