#!/usr/bin/env python3
"""IDEAS.md #11 - EXPECTATION SHIPPED SEPARATELY. Split screen, 18 s, loops on itself. Opening: B. Music: marimba.

It's snowing, the same room, the same t-shirt: "I NEED A JACKET." Above, he walks to the store: PAID $60, "PERFECT.",
warm with a mug while the snow piles up. Below, a phone ad: WINTER JACKET $9.99 ★★★★★ - "SAME JACKET. $9.99!" -
ARRIVES IN 21 DAYS. He waits and shivers (DAY 1 ... DAY 21), wraps up in a blanket: "ANY DAY NOW." Ding-dong: a tiny box,
a tiny jacket - it fits his teddy bear. "AT LEAST HE'S WARM."
"HE ORDERED A JACKET. / EXPECTATION SHIPPED SEPARATELY."  FOLLOW FOR MORE.

    python3 stick/jacket.py stick/jacket.mp4
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
MUSIC = "marimba_f"

W, H, FPS = 1080, 1920, 30
SR = 44100
DUR = 18.0
NF = int(round(DUR * FPS))
XFADE = 0.45
SC = AJ.SC
INK = AJ.INK
GOOD_C, GOOD_FAR = AJ.DOER, AJ.DOER_FAR
BAD_C, BAD_FAR = AJ.OT, AJ.OT_FAR
JACKET = (220, 70, 60)
RED = (255, 64, 56)
BOLD = FM.BOLD
PH, TOP_Y0, BOT_Y0, STRIP_Y, FYP = OC.PH, OC.TOP_Y0, OC.BOT_Y0, OC.STRIP_Y, OC.FYP
STAND_Y = FYP - 141

HOME = (360, STAND_Y)
WIN = (430, 110, 650, 320)
DOOR = (870, 990, FYP - 300)
TEDDY = (620, FYP)
BOX_X = 820

# ---------------------------------------------------------------- timeline
T_OUT0, T_OUT1 = 1.5, 2.3                  # top walks to the store
T_IN0, T_IN1 = 3.6, 4.4
T_WEAR0, T_WEAR1 = 4.6, 5.2
T_AD0, T_BUY, T_AD1 = 1.5, 3.0, 3.6        # bottom: the ad
T_D0, T_D1 = 3.6, 11.8                     # DAY 1 -> 21
T_BELL = 12.0
T_TO_BOX0, T_TO_BOX1 = 12.2, 12.7
T_OPENBOX = 12.8
T_HOLD = 13.1
T_TEDDY0, T_TEDDY1 = 13.9, 14.3
T_L1, T_L2 = 15.0, 16.1
CPS = 18.0
LINE1, LINE2 = "HE ORDERED A JACKET.", "EXPECTATION SHIPPED SEPARATELY."
T_FOLLOW = 16.95

B0 = -0.3 if STRONG else 0.3
BUB_GOOD = [(B0, 1.4, "I NEED A JACKET.", "me"), (T_WEAR1, T_WEAR1 + 1.0, "PERFECT.", "me"),
            (9.0, 10.2, "LET IT SNOW.", "me")]
BUB_BAD = [(B0, 1.4, "I NEED A JACKET.", "me"), (2.2, 3.4, "SAME JACKET. $9.99!", "me"), (6.4, 7.4, "ANY DAY NOW.", "me"),
           (9.4, 10.5, "IT'S COMING...", "me"), (13.2, 13.9, "...", "me"), (14.2, 14.95, "AT LEAST HE'S WARM.", "me")]


def day(t):
    return 1 + int(round(20 * prog(t, T_D0, T_D1)))


def snow_level(t):
    return prog(t, 0, 12)


# ---------------------------------------------------------------- poses
STAND = PW.STAND
STAND_PHONE = OC.STAND_PHONE
SHIVER = dict(STAND, head=(4, -146), el=(24, -70), hl=(-8, -92), er=(28, -66), hr=(-4, -88))
MUG = dict(STAND, el=(26, -80), hl=(36, -110), er=(10, -58), hr=(14, -10))
CARRY = dict(STAND, el=(10, -58), hl=(16, -12), er=(16, -58), hr=(24, -10))
DRESS = dict(STAND, el=(-30, -110), hl=(-10, -160), er=(30, -110), hr=(10, -160))
CROUCH = {"head": (48, -86), "neck": (34, -52), "el": (60, -36), "hl": (100, -20), "er": (54, -30), "hr": (94, -14),
          "kl": (44, 22), "fl": (20, 76), "kr": (34, 28), "fr": (8, 78)}
HOLD_UP = dict(STAND, head=(8, -146), el=(34, -100), hl=(56, -134), er=(30, -96), hr=(52, -130))
BEND = {"head": (64, -96), "neck": (44, -70), "el": (60, -30), "hl": (80, 10), "er": (54, -26), "hr": (74, 14),
        "kl": (-4, 56), "fl": (-12, 113), "kr": (12, 56), "fr": (14, 113)}


def walk(t, t0):
    return AJ.walk((t - t0) * 7, STAND)


def good_person(t):
    """pose, hip, facing, jacket(0..1), prop, alpha"""
    if t < T_OUT0:
        return SHIVER, HOME, 1, 0, None, 1
    if t < T_OUT1 + 0.2:
        k = smooth(prog(t, T_OUT0, T_OUT1))
        a = 1 - smooth(prog(t, T_OUT1 - 0.15, T_OUT1 + 0.15))
        return walk(t, T_OUT0), (lerp(HOME[0], 925, k), STAND_Y), 1, 0, None, a
    if t < T_IN0:
        return STAND, (925, STAND_Y), -1, 0, None, 0
    if t < T_IN1:
        k = smooth(prog(t, T_IN0 + 0.1, T_IN1))
        a = smooth(prog(t, T_IN0, T_IN0 + 0.3))
        return walk(t, T_IN0), (lerp(925, HOME[0], k), STAND_Y), -1, 0, "bag", a
    if t < T_WEAR1:
        k = math.sin(math.pi * prog(t, T_WEAR0, T_WEAR1))
        return lerp_pose(STAND, DRESS, k), HOME, 1, smooth(prog(t, T_WEAR0 + 0.2, T_WEAR1)), None, 1
    k = smooth(prog(t, 6.0, 6.5))
    sway = 0.5 + 0.5 * math.sin(t * 2.2)
    pose = lerp_pose(STAND, lerp_pose(MUG, dict(MUG, hl=(30, -124)), sway), k)
    return pose, HOME, 1, 1, ("mug" if t >= 6.0 else None), 1


def bad_person(t):
    """pose, hip, facing, blanket(0..1), prop"""
    jit = 0
    if T_D0 <= t < T_BELL:
        jit = (1 + 3 * prog(t, T_D0, T_D1)) * math.sin(t * 55)
    hip = (HOME[0] + jit, STAND_Y)
    blanket = smooth(prog(t, 6.0, 6.5)) if t < T_TO_BOX0 else 0
    if t < T_AD0:
        return SHIVER, hip, 1, 0, None
    if t < T_AD1:
        return STAND_PHONE, hip, 1, 0, "phone"
    if t < T_BELL + 0.2:
        return SHIVER, hip, 1, blanket, None
    if t < T_TO_BOX1:
        k = smooth(prog(t, T_TO_BOX0, T_TO_BOX1))
        return walk(t, T_TO_BOX0), (lerp(HOME[0], BOX_X - 90, k), STAND_Y), 1, 0, None
    if t < T_HOLD:
        return CROUCH, (BOX_X - 90, FYP - 98), 1, 0, None
    if t < T_TEDDY0:
        k = smooth(prog(t, T_HOLD, T_HOLD + 0.3))
        return lerp_pose(CROUCH, HOLD_UP, k), (BOX_X - 90, lerp(FYP - 98, STAND_Y, k)), 1, 0, "tiny"
    k = smooth(prog(t, T_TEDDY0, T_TEDDY0 + 0.3))
    return lerp_pose(STAND, BEND, k * (1 - smooth(prog(t, T_TEDDY1, T_TEDDY1 + 0.3)))), (BOX_X - 90, STAND_Y), -1, 0, \
        ("tiny" if t < T_TEDDY1 else None)


# ---------------------------------------------------------------- drawing
def build_room():
    yy, xx = np.mgrid[0:PH, 0:W].astype(np.float32)
    base = np.array((31, 30, 40) if STRONG else (9, 9, 11), np.float32)
    img = np.zeros((PH, W, 3), np.float32) + base
    img = np.where((yy > FYP)[..., None], img * 0.75 + 6, img)
    if STRONG:
        r = np.sqrt((xx - 400) ** 2 + (yy - 40) ** 2)
        img += (np.exp(-(r / 540) ** 2) * 34)[..., None] * np.array([1.0, 0.9, 0.7])
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    ink = INK + (255,)
    d.line([(0, FYP), (W, FYP)], fill=(56, 54, 54, 255), width=2)
    # a rug and a radiator
    d.ellipse([200, FYP - 14, 560, FYP + 14], fill=(110, 60, 70, 255))
    d.rounded_rectangle([90, FYP - 160, 230, FYP - 40], 8, fill=(190, 196, 206, 255), outline=ink, width=4)
    for j in range(6):
        d.line([(106 + j * 22, FYP - 150), (106 + j * 22, FYP - 50)], fill=(150, 156, 166, 255), width=4)
    return im


def draw_window(im, d, t):
    ink = INK + (255,)
    x0, y0, x1, y1 = WIN
    for i in range(y1 - y0):
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=PW.lerp_c((70, 90, 120), (150, 170, 196), i / (y1 - y0)) + (255,))
    for i in range(5):
        bx = x0 + 6 + i * 44
        bh = 40 + (i * 37) % 60
        d.rectangle([bx, y1 - bh, bx + 38, y1], fill=(50, 60, 80, 255))
    # snow piles up on the sill and falls
    lvl = snow_level(t)
    d.rectangle([x0, y1 - 10 - 40 * lvl, x1, y1], fill=(240, 244, 250, 255))
    rng = np.random.default_rng(2)
    for j in range(40):
        sx = x0 + rng.uniform(0, x1 - x0)
        sp = rng.uniform(40, 90)
        sy = y0 + ((rng.uniform(0, 200) + t * sp) % (y1 - y0))
        r = rng.uniform(2, 4)
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(250, 250, 255, 230))
    d.rectangle([x0, y0, x1, y1], outline=ink, width=8)
    d.line([((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], fill=ink, width=6)


def draw_door(d, t, good):
    ink = INK + (255,)
    x0, x1, y0 = DOOR
    d.rectangle([x0 - 8, y0 - 8, x1 + 8, FYP], fill=(20, 20, 24, 255), outline=ink, width=4)
    open_k = 0.0
    spans = ((T_OUT1 - 0.4, T_OUT1 + 0.45), (T_IN0 - 0.1, T_IN0 + 0.7)) if good else ((T_BELL - 0.1, T_BELL + 0.5),)
    for a, b in spans:
        if a <= t < b:
            open_k = 1 - smooth(prog(t, (a + b) / 2, b))
    w = (x1 - x0) * (1 - 0.8 * open_k)
    d.rectangle([x1 - w, y0, x1, FYP], fill=(130, 96, 66, 255), outline=ink, width=4)
    d.ellipse([x1 - w + 14, y0 + 150, x1 - w + 30, y0 + 166], fill=(230, 200, 90, 255), outline=ink)


def draw_teddy(d, dressed):
    ink = INK + (255,)
    x, y = TEDDY
    br = (170, 120, 80, 255)
    d.ellipse([x - 34, y - 70, x + 34, y], fill=br, outline=ink, width=3)
    if dressed:
        d.chord([x - 36, y - 74, x + 36, y - 2], 200, 340, fill=JACKET + (255,), outline=ink)
        d.rectangle([x - 34, y - 52, x + 34, y - 18], fill=JACKET + (255,), outline=ink, width=3)
        d.line([(x, y - 52), (x, y - 18)], fill=ink, width=2)
    d.ellipse([x - 26, y - 118, x + 26, y - 66], fill=br, outline=ink, width=3)
    for s in (-1, 1):
        d.ellipse([x + s * 22 - 10, y - 122, x + s * 22 + 10, y - 102], fill=br, outline=ink, width=3)
    d.ellipse([x - 9, y - 94, x - 3, y - 88], fill=ink)
    d.ellipse([x + 3, y - 94, x + 9, y - 88], fill=ink)
    d.ellipse([x - 6, y - 84, x + 6, y - 76], fill=(60, 40, 30, 255))


def draw_jacket(d, pts, k):
    if k <= 0.01:
        return
    a = int(255 * k)
    ink = INK + (a,)
    col = JACKET + (a,)
    neck, hip = pts["neck"], pts["hip"]
    d.line([neck, hip], fill=ink, width=46)
    d.line([neck, hip], fill=col, width=38)
    for e, h in (("el", "hl"), ("er", "hr")):
        d.line([neck, pts[e], pts[h]], fill=ink, width=24, joint="curve")
        d.line([neck, pts[e], pts[h]], fill=col, width=17, joint="curve")
    d.line([neck, hip], fill=(240, 220, 120, a), width=3)


def draw_blanket(d, pts, k):
    if k <= 0.01:
        return
    a = int(255 * k)
    hx, hy = pts["neck"]
    px, py = pts["hip"]
    d.polygon([(hx - 36, hy - 6), (hx + 36, hy - 10), (px + 60, py + 60), (px - 60, py + 60)],
              fill=(90, 120, 170, a), outline=INK + (a,))
    for j in range(3):
        y = hy + 30 + j * 40
        d.line([(hx - 30 - j * 8, y), (hx + 34 + j * 8, y)], fill=(130, 160, 210, a), width=4)


def draw_prop(d, pts, prop):
    ink = INK + (255,)
    if prop == "phone":
        hx, hy = pts["hl"]
        d.rounded_rectangle([hx - 10, hy - 26, hx + 12, hy + 10], 4, fill=(30, 32, 40, 255), outline=(150, 180, 255, 255),
                            width=3)
    elif prop == "bag":
        hx, hy = pts["hr"]
        d.rounded_rectangle([hx - 30, hy, hx + 30, hy + 60], 6, fill=(240, 236, 226, 255), outline=ink, width=3)
        d.arc([hx - 16, hy - 14, hx + 16, hy + 10], 180, 360, fill=ink, width=3)
    elif prop == "mug":
        hx, hy = pts["hl"]
        d.rounded_rectangle([hx - 14, hy - 30, hx + 14, hy + 2], 5, fill=(240, 240, 236, 255), outline=ink, width=3)
        for j in range(2):
            d.arc([hx - 10 + j * 10, hy - 60, hx + 6 + j * 10, hy - 34], 200, 340, fill=(220, 224, 236, 200), width=3)
    elif prop == "tiny":
        hx, hy = pts["hl"]
        hx2, hy2 = pts["hr"]
        cx, cy = (hx + hx2) / 2, (hy + hy2) / 2
        d.polygon([(cx - 18, cy - 12), (cx + 18, cy - 12), (cx + 22, cy + 18), (cx - 22, cy + 18)], fill=JACKET + (255,),
                  outline=ink)
        d.line([(cx, cy - 12), (cx, cy + 18)], fill=ink, width=2)


def draw_ad(im, t):
    if not (T_AD0 <= t < T_AD1 + 0.2):
        return
    k = out_back(prog(t, T_AD0, T_AD0 + 0.3)) * (1 - smooth(prog(t, T_AD1, T_AD1 + 0.2)))
    if k < 0.05:
        return
    cw, ch = 330, 430
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    ink = INK + (255,)
    d.rounded_rectangle([0, 0, cw - 1, ch - 1], 18, fill=(250, 250, 252, 255), outline=(200, 204, 214, 255), width=3)
    d.rectangle([16, 16, cw - 16, 230], fill=(220, 230, 240, 255))
    # the model in the photo
    m = {"head": (165, 60), "neck": (165, 92), "hip": (165, 168)}
    d.line([m["neck"], m["hip"]], fill=ink, width=50)
    d.line([m["neck"], m["hip"]], fill=JACKET + (255,), width=42)
    for sx in (-1, 1):
        d.line([m["neck"], (165 + sx * 40, 140), (165 + sx * 46, 180)], fill=ink, width=24, joint="curve")
        d.line([m["neck"], (165 + sx * 40, 140), (165 + sx * 46, 180)], fill=JACKET + (255,), width=17, joint="curve")
    d.line([(150, 168), (146, 226)], fill=ink, width=14)
    d.line([(180, 168), (184, 226)], fill=ink, width=14)
    d.ellipse([140, 36, 190, 86], fill=(240, 240, 244, 255), outline=ink, width=4)
    spaced(d, cw / 2, 244, "WINTER JACKET", font("Inter-Bold.otf", 26), (20, 20, 24, 255), 2)
    spaced(d, cw / 2, 282, "$9.99", font(BOLD, 44), (220, 40, 40, 255), 1)
    spaced(d, cw / 2, 336, "★★★★★", font("DejaVuSans-Bold.ttf" if False else MONO, 26), (240, 170, 30, 255), 3)
    pressed = t >= T_BUY
    d.rounded_rectangle([40, 372, cw - 40, 416], 10, fill=(60, 170, 90, 255) if pressed else (240, 160, 40, 255))
    spaced(d, cw / 2, 380, "ORDERED ✓" if pressed and False else ("ORDERED" if pressed else "BUY NOW"),
           font("Inter-Bold.otf", 24), (255, 255, 255, 255), 3)
    card = card.resize((max(1, int(cw * k)), max(1, int(ch * k))), Image.LANCZOS)
    im.alpha_composite(card, (int(860 - card.width / 2), int(330 - card.height / 2)))


def draw_box(d, t):
    if t < T_BELL:
        return
    ink = INK + (255,)
    k = smooth(prog(t, T_BELL, T_BELL + 0.3))
    x = lerp(DOOR[0] + 40, BOX_X, k)
    y = FYP
    opened = t >= T_OPENBOX
    d.rectangle([x - 22, y - 30, x + 22, y], fill=(196, 150, 96, 255), outline=ink, width=3)
    if opened:
        d.polygon([(x - 22, y - 30), (x - 40, y - 46), (x - 10, y - 30)], fill=(196, 150, 96, 255), outline=ink)
        d.polygon([(x + 22, y - 30), (x + 40, y - 46), (x + 10, y - 30)], fill=(196, 150, 96, 255), outline=ink)
    else:
        d.line([(x, y - 30), (x, y)], fill=(160, 120, 70, 255), width=4)


def widget(d, x, y, label, value, col):
    d.rounded_rectangle([x, y, x + 240, y + 92], 8, fill=(18, 20, 28, 230), outline=(90, 94, 104, 255), width=2)
    spaced(d, x + 120, y + 10, label, font("Inter-SemiBold.otf", 21), (190, 194, 204, 255), 5)
    spaced(d, x + 120, y + 38, value, font(MONO, 40), col + (255,), 1)


def sprite(pts, body, far, facing):
    cv = AJ.Canvas(*PW.bbox_of(list(pts.values()), 140))
    AJ.draw_stick(cv, pts, body, far, facing)
    return cv.done()


ROOM = None
FRAME0 = None


def panel(t, good):
    im = ROOM.copy()
    d = ImageDraw.Draw(im)
    draw_window(im, d, t)
    draw_door(d, t, good)
    if not good:
        draw_teddy(d, t >= T_TEDDY1)
        draw_box(d, t)
    if good:
        pose, hip, facing, jk, prop, alpha = good_person(t)
        blanket = 0
    else:
        pose, hip, facing, blanket, prop = bad_person(t)
        jk, alpha = 0, 1
    pts = {"head": (925, 300)}
    if alpha > 0.01:
        pts = AJ.place(pose, hip, facing, SC)
        body, far = (GOOD_C, GOOD_FAR) if good else (BAD_C, BAD_FAR)
        spr, off = sprite(pts, body, far, facing)
        if alpha < 0.999:
            spr.putalpha(spr.split()[3].point(lambda v: int(v * alpha)))
        if good:
            im.alpha_composite(PW.glow_of(spr, 0.4 * alpha, 12), off)
        im.alpha_composite(spr, off)
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        draw_jacket(ld, pts, jk)
        draw_blanket(ld, pts, blanket)
        im.alpha_composite(lay)
        d = ImageDraw.Draw(im)
        draw_prop(d, pts, prop)
    if not (STRONG and t < 1.6):
        if good:
            if t >= T_IN1:
                widget(d, 800, 100, "PAID", "$60", (240, 240, 244))
                widget(d, 800, 206, "WARM", "YES", (120, 230, 150))
        elif T_AD1 <= t < T_HOLD:
            widget(d, 800, 100, "PAID", "$9.99", (240, 240, 244))
            if t < T_BELL:
                left = 21 - day(t) + 1
                widget(d, 800, 206, "ARRIVES IN", f"{left} DAYS" if left > 1 else "1 DAY", (240, 200, 120))
            else:
                widget(d, 800, 206, "ARRIVED", "TODAY", (120, 230, 150))
    if not good:
        draw_ad(im, t)
    OC.speech_at(im, t, BUB_GOOD if good else BUB_BAD, pts)
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
    img.alpha_composite(zoom(panel(t, True), t, (440, 400)), (0, TOP_Y0))
    img.alpha_composite(zoom(panel(t, False), t, (440, 400)), (0, BOT_Y0))
    d = ImageDraw.Draw(img)
    d.line([(0, STRIP_Y), (W, STRIP_Y)], fill=(56, 56, 62, 255), width=2)
    s = f"DAY {day(t)}"
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
            spaced(ld, W / 2, TOP_Y0 + 14, "BUYS IN STORE", fl, (240, 242, 248, int(255 * la)), 10)
        spaced(ld, W / 2, BOT_Y0 + 14, "BUYS FROM AN AD", fl, (220, 224, 232, int(255 * la)), 10)
        img.alpha_composite(lay)
        d = ImageDraw.Draw(img)
    for t0, s2, y, size in ((T_L1, LINE1, 40, 52), (T_L2, LINE2, 106, 44)):
        if t < t0:
            continue
        fm = font(BOLD, size)
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
    mus = music.score(MUSIC, DUR, t_end=T_HOLD, start=0.0 if STRONG else 0.2, loud=1.2 if STRONG else 1.0)
    fx = np.zeros((n, 2))
    # wind outside, rising with the days
    w = noise(DUR, 41, lo=200, hi=900)
    wenv = 0.004 + 0.012 * np.clip(np.arange(n) / SR / 12, 0, 1)
    fx[:, 0] += w * wenv
    fx[:, 1] += np.roll(w, 3000) * wenv
    # the ad: pop and the buy click
    mix_in(fx, tone(880, 0.12, (1, 0.3), a=0.002, d=0.06), T_AD0, 0.04, 0.4)
    mix_in(fx, tone(1320, 0.1, (1, 0.3), a=0.002, d=0.05), T_BUY, 0.05, 0.4)
    mix_in(fx, tone(1760, 0.14, (1, 0.3), a=0.002, d=0.07), T_BUY + 0.08, 0.04, 0.4)
    # teeth chattering below
    for tk in np.arange(T_D0 + 0.5, T_BELL, 1.1):
        for j in range(5):
            mix_in(fx, noise(0.02, int(tk * 100) + j, lo=2000, hi=6000) * env(int(0.02 * SR), 0.001, 0.008),
                   tk + j * 0.05, 0.02, 0.3)
    # doorbell, box, the tiny jacket
    mix_in(fx, music.music_box(midi(76), 1.0), T_BELL, 0.08, 0.4)
    mix_in(fx, music.music_box(midi(72), 1.2), T_BELL + 0.3, 0.08, 0.4)
    mix_in(fx, noise(0.25, 55, lo=1500, hi=7000) * env(int(0.25 * SR), 0.01, 0.12), T_OPENBOX, 0.05, 0.3)
    mix_in(fx, tone(1568, 0.25, (1,), a=0.003, d=0.12, sweep=2093), T_HOLD + 0.05, 0.04, 0.2)
    for b0, b1, s, w_ in BUB_GOOD + BUB_BAD:
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
    out = sys.argv[1] if len(sys.argv) > 1 else "jacket.mp4"
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
