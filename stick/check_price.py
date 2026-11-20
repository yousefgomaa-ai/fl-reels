#!/usr/bin/env python3
"""LET ME CHECK THE PRICE (queue #2). Split screen, 18 s, loops on itself. Opening: B. Music: kalimba.

The same store, the same gold headphones under a spotlight, no price on the shelf. Both: "OOH. NICE."
Above, he flips the box first: $1,200 - "NOPE." - takes the $49 pair next to it: "THESE ARE FINE.", and nods along.
Below, he puts them on first: "WOW.", the mirror, two selfies, "I LOOK RICH.", a little dance, then the register:
"I'LL TAKE THEM." - "THAT'S $1,200." The music stops. "..." "LET ME CHECK SOMETHING." He puts them back like glass and
walks out backwards. Then he comes back in for the $49 pair: "...THESE ARE FINE."
"CHECK THE PRICE / BEFORE YOU FALL IN LOVE."  FOLLOW FOR MORE.

    python3 stick/check_price.py stick/check-price.mp4
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
MUSIC = "kalimba_e"

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
GOLD = (240, 190, 60)
BLUE = (80, 150, 220)
RED = (255, 64, 56)
BOLD = FM.BOLD
PH, TOP_Y0, BOT_Y0, STRIP_Y, FYP = OC.PH, OC.TOP_Y0, OC.BOT_Y0, OC.STRIP_Y, OC.FYP
STAND_Y = FYP - 141

DOOR = (20, 140, FYP - 300)
MIRROR = (210, 330, 260, 560)
PED = (480, 580, FYP - 190)                # pedestal x0, x1, top
GOLD_POS = (530, PED[2] - 18)
LOW = (600, 720, FYP - 110)                # the cheap shelf
BLUE_POS = (660, LOW[2] - 14)
REG = (800, 1050, FYP - 160)               # register counter
AT_PED = 420
AT_REG = 720
CASHIER = (950, STAND_Y)

# ---------------------------------------------------------------- timeline
T_FLIP, T_TAG = 1.5, 1.8
T_PUTBACK_G = 2.6
T_CHEAP_G = 3.4
T_REG_G0, T_REG_G1 = 3.9, 4.8
T_PAID_G = 5.0
T_BACKWALK_G = 6.4

T_WEAR = 1.6
T_MIRROR0, T_MIRROR1 = 2.8, 3.5
T_SELFIE = [3.7, 4.3]
T_DANCE0, T_DANCE1 = 5.0, 6.7
T_TOREG0, T_TOREG1 = 6.8, 7.6
T_PRICE = 8.9
T_OFF = 11.0
T_BACK0, T_BACK1 = 11.2, 11.9               # walks back to the pedestal
T_PLACE0, T_PLACE1 = 11.9, 12.6
T_EXIT0, T_EXIT1 = 12.7, 13.6
T_RETURN0, T_RETURN1 = 13.8, 14.4
T_L1, T_L2 = 15.0, 16.1
CPS = 18.0
LINE1, LINE2 = "CHECK THE PRICE", "BEFORE YOU FALL IN LOVE."
T_FOLLOW = 16.95

B0 = -0.3 if STRONG else 0.3
BUB_GOOD = [(B0, 1.4, "OOH. NICE.", "me"), (2.3, 3.2, "NOPE.", "me"), (5.2, 6.3, "THESE ARE FINE.", "me")]
BUB_BAD = [(B0, 1.4, "OOH. NICE.", "me"), (2.0, 2.8, "WOW.", "me"), (4.1, 5.0, "I LOOK RICH.", "me"),
           (7.6, 8.6, "I'LL TAKE THEM.", "me"), (9.9, 10.5, "...", "me"), (10.6, 11.6, "LET ME CHECK SOMETHING.", "me"),
           (14.1, 14.95, "...THESE ARE FINE.", "me")]
CASH_GOOD = [(T_REG_G1, T_REG_G1 + 0.8, "$49.", "me")]
CASH_BAD = [(T_PRICE, T_PRICE + 1.0, "THAT'S $1,200.", "me")]


def clock_minutes(t):
    return int(14 * 60 + 18 * prog(t, 0.5, 14.5))


def fmt12(mm):
    h, m = mm // 60, mm % 60
    return f"{h % 12 or 12}:{m:02d} {'AM' if h < 12 else 'PM'}"


# ---------------------------------------------------------------- poses
STAND = PW.STAND
REACH = dict(STAND, head=(14, -148), el=(44, -96), hl=(96, -84), er=(36, -86), hr=(90, -78))
LOOK_TAG = dict(STAND, head=(18, -146), el=(40, -104), hl=(70, -130), er=(34, -96), hr=(64, -122))
LOW_REACH = {"head": (64, -96), "neck": (44, -70), "el": (70, -40), "hl": (110, -10), "er": (64, -36), "hr": (104, -6),
             "kl": (-4, 56), "fl": (-12, 113), "kr": (12, 56), "fr": (14, 113)}
HOLD = dict(STAND, el=(30, -76), hl=(58, -86), er=(26, -72), hr=(54, -82))
WEAR = dict(STAND, el=(-20, -110), hl=(-4, -160), er=(24, -110), hr=(10, -160))
SELFIE = dict(STAND, head=(4, -150), el=(40, -110), hl=(84, -150), er=(10, -70), hr=(24, -40))
DANCE_A = dict(STAND, head=(10, -150), el=(-30, -120), hl=(-40, -170), er=(36, -90), hr=(60, -60),
               kl=(-20, 56), fl=(-30, 110), kr=(16, 50), fr=(30, 106))
DANCE_B = dict(STAND, head=(-6, -150), el=(30, -120), hl=(40, -170), er=(-36, -90), hr=(-60, -60),
               kl=(-16, 50), fl=(-30, 106), kr=(20, 56), fr=(30, 110))
FROZEN = dict(STAND, head=(4, -150), el=(14, -70), hl=(30, -40), er=(10, -66), hr=(26, -36))
NOD = dict(STAND, head=(10, -142))
PLACE = dict(STAND, head=(20, -140), neck=(14, -104), el=(50, -80), hl=(90, -70), er=(44, -76), hr=(84, -66))


def walk(t, t0, speed=7.0):
    return AJ.walk((t - t0) * speed, STAND)


def good_person(t):
    """pose, hip, facing, worn(None|'gold'|'blue'), held"""
    hip = (AT_PED, STAND_Y)
    if t < T_FLIP:
        return STAND, hip, 1, None, None
    if t < T_PUTBACK_G:
        k = smooth(prog(t, T_FLIP, T_FLIP + 0.3))
        return lerp_pose(STAND, LOOK_TAG, k), hip, 1, None, "gold"
    if t < T_PUTBACK_G + 0.4:
        k = smooth(prog(t, T_PUTBACK_G, T_PUTBACK_G + 0.4))
        return lerp_pose(LOOK_TAG, REACH, k), hip, 1, None, ("gold" if k < 0.8 else None)
    if t < T_CHEAP_G:
        k = smooth(prog(t, T_PUTBACK_G + 0.4, T_CHEAP_G))
        return lerp_pose(REACH, LOW_REACH, k), (lerp(AT_PED, 560, k), STAND_Y), 1, None, None
    if t < T_REG_G0:
        k = smooth(prog(t, T_CHEAP_G, T_REG_G0))
        return lerp_pose(LOW_REACH, HOLD, k), (560, STAND_Y), 1, None, "blue"
    if t < T_REG_G1:
        k = smooth(prog(t, T_REG_G0, T_REG_G1))
        p = dict(walk(t, T_REG_G0), **{j: HOLD[j] for j in ("el", "hl", "er", "hr")})
        return p, (lerp(560, AT_REG, k), STAND_Y), 1, None, "blue"
    if t < T_PAID_G + 0.6:
        return HOLD, (AT_REG, STAND_Y), 1, None, "blue"
    if t < T_PAID_G + 1.2:
        k = math.sin(math.pi * prog(t, T_PAID_G + 0.6, T_PAID_G + 1.2))
        return lerp_pose(STAND, WEAR, k), (AT_REG, STAND_Y), -1, ("blue" if t > T_PAID_G + 0.9 else None), \
            (None if t > T_PAID_G + 0.9 else "blue")
    if t < T_BACKWALK_G + 1.0:
        k = smooth(prog(t, T_BACKWALK_G, T_BACKWALK_G + 1.0))
        return walk(t, T_BACKWALK_G, 5), (lerp(AT_REG, 380, k), STAND_Y), -1, "blue", None
    k = 0.5 + 0.5 * math.sin(t * 2 * math.pi * 1.4)
    return lerp_pose(STAND, NOD, k), (380, STAND_Y), 1, "blue", None


def bad_person(t):
    """pose, hip, facing, worn, held, alpha"""
    hip = (AT_PED, STAND_Y)
    if t < T_WEAR:
        return lerp_pose(STAND, REACH, smooth(prog(t, 1.2, T_WEAR))), hip, 1, None, None, 1
    if t < T_WEAR + 0.6:
        k = math.sin(math.pi * prog(t, T_WEAR, T_WEAR + 0.6))
        return lerp_pose(STAND, WEAR, k), hip, 1, ("gold" if t > T_WEAR + 0.3 else None), \
            (None if t > T_WEAR + 0.3 else "gold"), 1
    if t < T_MIRROR0:
        return lerp_pose(STAND, NOD, 0.5 + 0.5 * math.sin(t * 9)), hip, 1, "gold", None, 1
    if t < T_MIRROR1:
        k = smooth(prog(t, T_MIRROR0, T_MIRROR1))
        return walk(t, T_MIRROR0), (lerp(AT_PED, 380, k), STAND_Y), -1, "gold", None, 1
    if t < T_DANCE0:
        return SELFIE, (380, STAND_Y), -1, "gold", "phone", 1
    if t < T_DANCE1:
        k = 0.5 + 0.5 * math.sin((t - T_DANCE0) * 2 * math.pi * 1.6)
        bob = 6 * abs(math.sin((t - T_DANCE0) * 2 * math.pi * 1.6))
        return lerp_pose(DANCE_A, DANCE_B, k), (380, STAND_Y - bob), 1, "gold", None, 1
    if t < T_TOREG1:
        k = smooth(prog(t, T_TOREG0, T_TOREG1))
        return walk(t, T_TOREG0, 8), (lerp(380, AT_REG, k), STAND_Y), 1, "gold", None, 1
    if t < T_PRICE + 0.3:
        return lerp_pose(STAND, NOD, 0.5 + 0.5 * math.sin(t * 9)), (AT_REG, STAND_Y), 1, "gold", None, 1
    if t < T_OFF:
        return FROZEN, (AT_REG, STAND_Y), 1, "gold", None, 1
    if t < T_BACK0:
        k = math.sin(math.pi * prog(t, T_OFF, T_BACK0 + 0.1))
        return lerp_pose(FROZEN, WEAR, k), (AT_REG, STAND_Y), 1, None, "gold", 1
    if t < T_BACK1:
        k = smooth(prog(t, T_BACK0, T_BACK1))
        p = dict(walk(t, T_BACK0, 4), **{j: HOLD[j] for j in ("el", "hl", "er", "hr")})
        return p, (lerp(AT_REG, AT_PED, k), STAND_Y), -1, None, "gold", 1
    if t < T_PLACE1:
        k = smooth(prog(t, T_PLACE0, T_PLACE1))
        return lerp_pose(HOLD, PLACE, k), (AT_PED, STAND_Y), 1, None, ("gold" if k < 0.95 else None), 1
    if t < T_EXIT1 + 0.2:
        k = smooth(prog(t, T_EXIT0, T_EXIT1))
        a = 1 - smooth(prog(t, T_EXIT1 - 0.2, T_EXIT1 + 0.15))
        return AJ.walk(-(t - T_EXIT0) * 4, STAND), (lerp(AT_PED, 80, k), STAND_Y), 1, None, None, a
    if t < T_RETURN0:
        return STAND, (80, STAND_Y), 1, None, None, 0
    if t < T_RETURN1:
        k = smooth(prog(t, T_RETURN0, T_RETURN1))
        a = smooth(prog(t, T_RETURN0, T_RETURN0 + 0.2))
        return walk(t, T_RETURN0, 10), (lerp(80, 560, k), STAND_Y), 1, None, None, a
    k = smooth(prog(t, T_RETURN1, T_RETURN1 + 0.3))
    return lerp_pose(LOW_REACH, HOLD, k), (560, STAND_Y), 1, None, "blue", 1


# ---------------------------------------------------------------- drawing
def build_room():
    yy, xx = np.mgrid[0:PH, 0:W].astype(np.float32)
    base = np.array((34, 34, 44) if STRONG else (10, 10, 12), np.float32)
    img = np.zeros((PH, W, 3), np.float32) + base
    img = np.where((yy > FYP)[..., None], img * 0.75 + 8, img)
    if STRONG:
        r = np.sqrt((xx - 530) ** 2 + (yy - 40) ** 2)
        img += (np.exp(-(r / 560) ** 2) * 36)[..., None] * np.array([1.0, 0.95, 0.85])
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    ink = INK + (255,)
    d.line([(0, FYP), (W, FYP)], fill=(60, 58, 58, 255), width=2)
    # store sign on the wall
    d.rounded_rectangle([400, 70, 700, 130], 10, fill=(30, 32, 40, 255), outline=(90, 94, 104, 255), width=3)
    spaced(d, 550, 84, "TECH STORE", font(BOLD, 30), (240, 240, 244, 255), 4)
    # spotlight cone on the pedestal
    g = Image.new("RGBA", (W, PH), (0, 0, 0, 0))
    ImageDraw.Draw(g).polygon([(510, 140), (550, 140), (640, PED[2]), (420, PED[2])], fill=(255, 240, 200, 40))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    # mirror
    x0, x1, y0, y1 = MIRROR
    d.rounded_rectangle([x0, y0, x1, y1], 14, fill=(150, 176, 196, 255), outline=ink, width=6)
    d.line([(x0 + 24, y0 + 30), (x0 + 70, y0 + 100)], fill=(220, 236, 246, 255), width=8)
    # pedestal
    px0, px1, py = PED
    d.rectangle([px0, py, px1, FYP], fill=(236, 236, 240, 255), outline=ink, width=4)
    # cheap shelf
    lx0, lx1, ly = LOW
    d.rectangle([lx0, ly, lx1, FYP], fill=(120, 96, 76, 255), outline=ink, width=4)
    d.rounded_rectangle([lx0 + 30, ly + 20, lx1 - 30, ly + 50], 6, fill=(250, 250, 252, 255), outline=ink, width=2)
    spaced(d, (lx0 + lx1) / 2, ly + 22, "$49", font(BOLD, 22), (40, 140, 70, 255), 1)
    # register counter
    rx0, rx1, ry = REG
    d.rectangle([rx0, ry, rx1, FYP], fill=(90, 96, 110, 255), outline=ink, width=4)
    d.rectangle([rx0, ry, rx1, ry + 16], fill=(200, 204, 214, 255), outline=ink, width=3)
    # door (left)
    dx0, dx1, dy = DOOR
    d.rectangle([dx0 - 8, dy - 8, dx1 + 8, FYP], fill=(20, 20, 24, 255), outline=ink, width=4)
    return im


def draw_door(d, t, bottom):
    ink = INK + (255,)
    x0, x1, y0 = DOOR
    open_k = 0.0
    if bottom:
        for a, b in ((T_EXIT1 - 0.4, T_EXIT1 + 0.3), (T_RETURN0 - 0.1, T_RETURN0 + 0.5)):
            if a <= t < b:
                open_k = 1 - smooth(prog(t, (a + b) / 2, b))
    w = (x1 - x0) * (1 - 0.8 * open_k)
    d.rectangle([x0, y0, x0 + w, FYP], fill=(150, 176, 196, 200), outline=ink, width=4)
    d.rectangle([x0 + w - 20, y0 + 140, x0 + w - 12, y0 + 190], fill=(200, 204, 214, 255))


def headphones(d, cx, cy, col, s=1.0, worn=False):
    ink = INK + (255,)
    c = col + (255,)
    r = 30 * s
    d.arc([cx - r, cy - r - 6 * s, cx + r, cy + r], 190, 350, fill=ink, width=int(12 * s))
    d.arc([cx - r, cy - r - 6 * s, cx + r, cy + r], 190, 350, fill=c, width=int(7 * s))
    for sx in ((-1, 1) if not worn else (0,)):
        ex = cx + sx * r * 0.95
        d.rounded_rectangle([ex - 11 * s, cy - 4 * s, ex + 11 * s, cy + 22 * s], 7, fill=c, outline=ink, width=3)


def worn_phones(d, pts, col):
    hx, hy = pts["head"]
    ink = INK + (255,)
    c = col + (255,)
    r = 36
    d.arc([hx - r, hy - r - 4, hx + r, hy + r - 4], 200, 340, fill=ink, width=12)
    d.arc([hx - r, hy - r - 4, hx + r, hy + r - 4], 200, 340, fill=c, width=7)
    d.rounded_rectangle([hx - 12, hy - 10, hx + 12, hy + 22], 8, fill=c, outline=ink, width=3)


def price_tag(im, t):
    k = out_back(prog(t, T_TAG, T_TAG + 0.3)) * (1 - smooth(prog(t, T_PUTBACK_G + 0.2, T_PUTBACK_G + 0.5)))
    if k < 0.05:
        return
    tw, th = 220, 90
    tag = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(tag)
    d.rounded_rectangle([0, 0, tw - 1, th - 1], 12, fill=(250, 250, 252, 255), outline=(220, 40, 40, 255), width=4)
    spaced(d, tw / 2, 18, "$1,200", font(BOLD, 48), (220, 40, 40, 255), 1)
    tag = tag.resize((max(1, int(tw * k)), max(1, int(th * k))), Image.LANCZOS)
    im.alpha_composite(tag, (int(640 - tag.width / 2), int(230 - tag.height / 2)))


def register_screen(d, t, good):
    rx0, rx1, ry = REG
    ink = INK + (255,)
    d.rectangle([rx0 + 30, ry - 70, rx0 + 150, ry - 10], fill=(20, 24, 30, 255), outline=ink, width=4)
    d.rectangle([rx0 + 80, ry - 10, rx0 + 100, ry], fill=(60, 64, 74, 255))
    if good and t >= T_REG_G1:
        spaced(d, rx0 + 90, ry - 56, "$49", font(MONO, 28), (120, 230, 150, 255), 1)
    if not good and t >= T_PRICE:
        spaced(d, rx0 + 90, ry - 56, "$1200", font(MONO, 26), (255, 90, 80, 255), 0)


def notes(d, t, pts, t0, t1):
    if not (t0 <= t < t1):
        return
    hx, hy = pts["head"]
    for j in range(3):
        ph = ((t - t0) * 0.9 + j / 3) % 1.0
        x = hx + 40 + 50 * ph + 16 * math.sin(ph * 6 + j)
        y = hy - 30 - 90 * ph
        a = int(255 * math.sin(math.pi * ph))
        d.text((x, y), "♪" if j % 2 else "♫", font=font(MONO, 34), fill=(250, 220, 120, a))


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
    d = ImageDraw.Draw(im)
    draw_door(d, t, not good)
    if good:
        pose, hip, facing, worn, held = good_person(t)
        alpha = 1
    else:
        pose, hip, facing, worn, held, alpha = bad_person(t)
    # products still on display
    gold_on_ped = held != "gold" and worn != "gold"
    if gold_on_ped:
        headphones(d, *GOLD_POS, GOLD, 1.0)
    blue_taken = (good and t >= T_CHEAP_G) or (not good and t >= T_RETURN1)
    if not blue_taken:
        headphones(d, *BLUE_POS, BLUE, 0.8)
    # cashier
    cpts = AJ.place(STAND, CASHIER, -1, SC)
    cspr, coff = sprite(cpts, CASH_C, CASH_FAR, -1)
    im.alpha_composite(cspr, coff)
    d = ImageDraw.Draw(im)
    rx0, rx1, ry = REG
    d.rectangle([rx0, ry, rx1, FYP], fill=(90, 96, 110, 255), outline=INK + (255,), width=4)
    d.rectangle([rx0, ry, rx1, ry + 16], fill=(200, 204, 214, 255), outline=INK + (255,), width=3)
    register_screen(d, t, good)
    pts = {"head": (80, 300)}
    if alpha > 0.01:
        pts = AJ.place(pose, hip, facing, SC)
        body, far = (GOOD_C, GOOD_FAR) if good else (BAD_C, BAD_FAR)
        spr, off = sprite(pts, body, far, facing)
        if alpha < 0.999:
            spr.putalpha(spr.split()[3].point(lambda v: int(v * alpha)))
        if good:
            im.alpha_composite(PW.glow_of(spr, 0.4 * alpha, 12), off)
        im.alpha_composite(spr, off)
        d = ImageDraw.Draw(im)
        if worn:
            worn_phones(d, pts, GOLD if worn == "gold" else BLUE)
        if held in ("gold", "blue"):
            hx, hy = pts["hl"]
            if not good and T_PLACE0 <= t < T_PLACE1:
                k = smooth(prog(t, T_PLACE0, T_PLACE1))
                hx, hy = lerp(hx, GOLD_POS[0], k), lerp(hy, GOLD_POS[1], k)
            headphones(d, hx, hy - 10, GOLD if held == "gold" else BLUE, 0.8)
        elif held == "phone":
            hx, hy = pts["hl"]
            d.rounded_rectangle([hx - 10, hy - 26, hx + 12, hy + 10], 4, fill=(30, 32, 40, 255),
                                outline=(150, 180, 255, 255), width=3)
            for ts in T_SELFIE:
                if ts <= t < ts + 0.15:
                    f = Image.new("RGBA", im.size, (255, 255, 255, int(90 * (1 - (t - ts) / 0.15))))
                    im.alpha_composite(f)
                    d = ImageDraw.Draw(im)
        if good:
            notes(d, t, pts, T_BACKWALK_G + 1.0, 15.0)
        else:
            notes(d, t, pts, T_WEAR + 0.4, T_PRICE)
    if not good and T_PLACE0 + 0.3 <= t < T_PLACE1 + 0.4:
        k = math.sin(math.pi * prog(t, T_PLACE0 + 0.3, T_PLACE1 + 0.4))
        for j in range(4):
            a = math.radians(45 + 90 * j)
            x, y = GOLD_POS[0] + 46 * math.cos(a), GOLD_POS[1] - 10 + 46 * math.sin(a)
            d.line([(x - 8, y), (x + 8, y)], fill=(255, 255, 255, int(255 * k)), width=3)
            d.line([(x, y - 8), (x, y + 8)], fill=(255, 255, 255, int(255 * k)), width=3)
    if good:
        price_tag(im, t)
    d = ImageDraw.Draw(im)
    if not (STRONG and t < 1.6):
        if good:
            if t >= T_TAG:
                widget(d, 30, 40, "PRICE", "$1,200", (240, 120, 120))
            if t >= T_REG_G1:
                widget(d, 30, 142, "PAID", "$49", (120, 230, 150))
        else:
            widget(d, 30, 40, "PRICE", "$1,200" if t >= T_PRICE else "???",
                   (240, 120, 120) if t >= T_PRICE else (240, 240, 244))
            if t >= T_RETURN1 + 0.3:
                widget(d, 30, 142, "PAID", "$49", (120, 230, 150))
    OC.speech_at(im, t, BUB_GOOD if good else BUB_BAD, pts)
    OC.speech_at(im, t, CASH_GOOD if good else CASH_BAD, cpts)
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
    img.alpha_composite(zoom(panel(t, True), t, (500, 420)), (0, TOP_Y0))
    img.alpha_composite(zoom(panel(t, False), t, (500, 420)), (0, BOT_Y0))
    d = ImageDraw.Draw(img)
    d.line([(0, STRIP_Y), (W, STRIP_Y)], fill=(56, 56, 62, 255), width=2)
    s = fmt12(clock_minutes(t))
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
    fl = font("Inter-SemiBold.otf", 38)
    la = smooth(prog(t, 1.5, 1.9)) if STRONG else 1.0
    if la > 0.01:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        if t < T_L1:
            spaced(ld, W / 2, TOP_Y0 + 14, "PRICE FIRST", fl, (240, 242, 248, int(255 * la)), 10)
        spaced(ld, W / 2, BOT_Y0 + 14, "LOVE FIRST", fl, (220, 224, 232, int(255 * la)), 10)
        img.alpha_composite(lay)
        d = ImageDraw.Draw(img)
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


def audio():
    n = int(DUR * SR)
    # the music plays until the price, then stops dead
    mus = music.score(MUSIC, DUR, t_end=T_PRICE, start=0.0 if STRONG else 0.2, loud=1.2 if STRONG else 1.0)
    fx = np.zeros((n, 2))
    # a record scratch at the price
    sc = tone(900, 0.35, (1, 0.5, 0.3), a=0.002, d=0.25, sweep=180)
    sc = sc + 0.4 * noise(0.35, 4, lo=500, hi=4000) * env(int(0.35 * SR), 0.002, 0.2)
    mix_in(fx, sc, T_PRICE + 0.05, 0.07, 0.3)
    # selfies, the register beeps, the tag pop
    for ts in T_SELFIE:
        mix_in(fx, noise(0.05, int(ts * 100), lo=2000, hi=8000) * env(int(0.05 * SR), 0.001, 0.02), ts, 0.06, 0.3)
    mix_in(fx, tone(1760, 0.08, (1,), a=0.002, d=0.04), T_REG_G1 - 0.2, 0.05, -0.3)
    mix_in(fx, tone(1760, 0.08, (1,), a=0.002, d=0.04), T_PRICE - 0.25, 0.05, 0.3)
    mix_in(fx, tone(660, 0.12, (1, 0.3), a=0.002, d=0.06, sweep=990), T_TAG, 0.05, -0.3)
    # the careful put-back: a tiny glassy chime
    mix_in(fx, music.kalimba(midi(91), 1.2), T_PLACE1 - 0.05, 0.05, 0.2)
    for b0, b1, s, w_ in BUB_GOOD + BUB_BAD + CASH_GOOD + CASH_BAD:
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
    out = sys.argv[1] if len(sys.argv) > 1 else "check-price.mp4"
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
