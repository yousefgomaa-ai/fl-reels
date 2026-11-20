#!/usr/bin/env python3
"""$7 LATTE (queue #3). Split screen, 18 s, loops on itself. Opening: A. Music: lo-fi.

JAN 1, 7:30 AM, the same sleepy morning: "I NEED COFFEE." The months run JAN ... DEC.
Above, coffee at home - $0.40 a day - and the difference goes into a jar: TRIP FUND. Below, the café: "THE USUAL.",
"$7.", every month a fancier cup (oat milk, extra shot, whipped cream, caramel, sprinkles) - SPENT ON COFFEE climbs.
DEC: above, he breaks the jar - a plane ticket - and lies on a beach with a coconut: "WORTH IT."
Below, the phone: YOUR COFFEE WRAPPED - 365 lattes, $2,555, that's a trip to Hawaii. "...WORTH IT?"
"$7 A DAY. / HE DRANK A VACATION."  FOLLOW FOR MORE.

    python3 stick/latte.py stick/latte.mp4
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

VARIANT = os.environ.get("VARIANT", "A").upper()
STRONG = VARIANT == "B"
MUSIC = "lofi_eb"

W, H, FPS = 1080, 1920, 30
SR = 44100
DUR = 18.0
NF = int(round(DUR * FPS))
XFADE = 0.45
SC = AJ.SC
INK = AJ.INK
GOOD_C, GOOD_FAR = AJ.DOER, AJ.DOER_FAR
BAD_C, BAD_FAR = AJ.OT, AJ.OT_FAR
BAR_C, BAR_FAR = (240, 190, 110), (200, 150, 80)
RED = (255, 64, 56)
BOLD = FM.BOLD
PH, TOP_Y0, BOT_Y0, STRIP_Y, FYP = OC.PH, OC.TOP_Y0, OC.BOT_Y0, OC.STRIP_Y, OC.FYP
STAND_Y = FYP - 141

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
T_Y0, T_Y1 = 1.2, 11.6                    # JAN -> DEC
MONTH = (T_Y1 - T_Y0) / 11
T_BREAK = 11.7                            # above: the jar breaks
T_BEACH = 12.3
T_WRAP = 12.0                             # below: coffee wrapped
T_L1, T_L2 = 15.0, 16.1
CPS = 18.0
LINE1, LINE2 = "$7 A DAY.", "HE DRANK A VACATION."
T_FOLLOW = 16.95

# kitchen (above)
K_COUNTER = (440, 920, FYP - 200)
KETTLE = (520, K_COUNTER[2])
JAR = (690, K_COUNTER[2])
K_ME = (360, STAND_Y)
# café (below)
C_COUNTER = (560, 1050, FYP - 170)
BARISTA = (830, STAND_Y)
C_ME = (500, STAND_Y)

B0 = -0.3 if STRONG else 0.3
BUB_GOOD = [(B0, 1.2, "I NEED COFFEE.", "me"), (13.0, 14.4, "WORTH IT.", "me")]
BUB_BAD = [(B0, 1.2, "I NEED COFFEE.", "me"), (1.4, 2.3, "THE USUAL.", "me"), (3.9, 4.8, "ADD OAT MILK.", "me"),
           (5.8, 6.7, "EXTRA SHOT.", "me"), (7.7, 8.7, "AND WHIPPED CREAM.", "me"), (9.6, 10.6, "CARAMEL DRIZZLE.", "me"),
           (13.6, 14.95, "...WORTH IT?", "me")]
BUB_BARISTA = [(2.2, 3.0, "$7.", "me")]


def month_idx(t):
    if t < T_Y0:
        return 0
    return min(11, int((t - T_Y0) / MONTH + 0.5))


def day_of_year(t):
    return 1 + int(364 * prog(t, T_Y0, T_Y1))


def strip_text(t):
    if t < T_Y0:
        return "JAN 1"
    if t >= T_Y1:
        return "DEC 31"
    return MONTHS[month_idx(t)]


def cup_stage(t):
    return min(5, int(prog(t, T_Y0, T_Y1) * 6))


# ---------------------------------------------------------------- poses
STAND = PW.STAND
YAWN = dict(STAND, head=(-4, -150), el=(-20, -110), hl=(-30, -160), er=(24, -110), hr=(34, -160))
POUR = dict(STAND, head=(14, -148), el=(44, -96), hl=(100, -80), er=(36, -86), hr=(94, -74))
SIP = dict(STAND, el=(30, -96), hl=(22, -132), er=(14, -58), hr=(18, -10))
COIN = dict(STAND, head=(18, -146), el=(50, -100), hl=(110, -110), er=(14, -58), hr=(18, -10))
TAP = dict(STAND, head=(14, -148), el=(46, -96), hl=(104, -96), er=(14, -58), hr=(18, -10))
HOLD = dict(STAND, el=(30, -80), hl=(52, -96), er=(14, -58), hr=(18, -10))
PHONE = dict(STAND, el=(26, -66), hl=(44, -100), er=(22, -62), hr=(40, -96))
LOUNGE = {"head": (-96, -96), "neck": (-62, -74), "el": (-60, -20), "hl": (-30, -10), "er": (-30, -90), "hr": (-10, -120),
          "kl": (60, -24), "fl": (120, 4), "kr": (56, -18), "fr": (116, 10)}


def good_person(t):
    """pose, hip, facing, prop"""
    if t < T_Y0:
        k = math.sin(math.pi * prog(t, 0.2, 1.1))
        return lerp_pose(STAND, YAWN, k), K_ME, 1, None
    if t < T_BREAK:
        ph = ((t - T_Y0) / MONTH) % 1.0
        if ph < 0.35:
            k = math.sin(math.pi * ph / 0.35)
            return lerp_pose(STAND, POUR, k), K_ME, 1, "pour"
        if ph < 0.7:
            k = math.sin(math.pi * (ph - 0.35) / 0.35)
            return lerp_pose(HOLD, SIP, k), K_ME, 1, "mug"
        k = math.sin(math.pi * (ph - 0.7) / 0.3)
        return lerp_pose(STAND, COIN, k), (K_ME[0] + 120 * k, STAND_Y), 1, "coin"
    if t < T_BEACH:
        k = smooth(prog(t, T_BREAK - 0.2, T_BREAK + 0.1))
        return lerp_pose(STAND, COIN, k), (K_ME[0] + 230, STAND_Y), 1, "ticket" if t > T_BREAK + 0.15 else None
    return LOUNGE, (470, FYP - 140), 1, "coconut"


def bad_person(t):
    if t < T_Y0:
        k = math.sin(math.pi * prog(t, 0.2, 1.1))
        return lerp_pose(STAND, YAWN, k), C_ME, 1, None
    if t < T_WRAP:
        ph = ((t - T_Y0) / MONTH) % 1.0
        if ph < 0.3:
            k = math.sin(math.pi * ph / 0.3)
            return lerp_pose(STAND, TAP, k), C_ME, 1, "card"
        if ph < 0.45:
            return HOLD, C_ME, 1, "cup"
        k = math.sin(math.pi * clamp((ph - 0.45) / 0.4))
        return lerp_pose(HOLD, SIP, k), C_ME, 1, "cup"
    k = smooth(prog(t, T_WRAP, T_WRAP + 0.3))
    return lerp_pose(HOLD, PHONE, k), C_ME, 1, "cup_phone"


# ---------------------------------------------------------------- scenes
def base_room(col, strong_light=(1.0, 0.9, 0.7)):
    yy, xx = np.mgrid[0:PH, 0:W].astype(np.float32)
    base = np.array(tuple(min(255, c + 22) for c in col) if STRONG else col, np.float32)
    img = np.zeros((PH, W, 3), np.float32) + base
    img = np.where((yy > FYP)[..., None], img * 0.75 + 6, img)
    if STRONG:
        r = np.sqrt((xx - 500) ** 2 + (yy - 40) ** 2)
        img += (np.exp(-(r / 540) ** 2) * 34)[..., None] * np.array(strong_light)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def build_kitchen():
    im = base_room((9, 9, 11))
    d = ImageDraw.Draw(im)
    ink = INK + (255,)
    d.line([(0, FYP), (W, FYP)], fill=(56, 54, 54, 255), width=2)
    x0, x1, cy = K_COUNTER
    d.rectangle([x0, cy, x1, cy + 20], fill=(200, 196, 190, 255), outline=ink, width=4)
    d.rectangle([x0 + 10, cy + 20, x1 - 10, FYP], fill=(120, 96, 76, 255), outline=ink, width=4)
    for j in range(3):
        d.rectangle([x0 + 26 + j * 150, cy + 44, x0 + 150 + j * 150, FYP - 24], outline=ink, width=3)
    # window with morning light
    d.rectangle([120, 90, 330, 300], fill=(140, 180, 220, 255), outline=ink, width=8)
    d.line([(225, 90), (225, 300)], fill=ink, width=6)
    d.ellipse([150, 110, 196, 156], fill=(255, 230, 150, 255))
    # kettle
    kx, ky = KETTLE
    d.rounded_rectangle([kx - 40, ky - 90, kx + 40, ky], 18, fill=(200, 70, 60, 255), outline=ink, width=4)
    d.arc([kx - 30, ky - 120, kx + 30, ky - 70], 180, 360, fill=ink, width=6)
    d.polygon([(kx + 38, ky - 60), (kx + 70, ky - 80), (kx + 72, ky - 72), (kx + 40, ky - 46)], fill=(200, 70, 60, 255),
              outline=ink)
    return im


def build_cafe():
    im = base_room((12, 10, 9))
    d = ImageDraw.Draw(im)
    ink = INK + (255,)
    d.line([(0, FYP), (W, FYP)], fill=(56, 54, 54, 255), width=2)
    # menu board
    d.rounded_rectangle([600, 70, 1010, 250], 10, fill=(26, 34, 30, 255), outline=(120, 96, 76, 255), width=8)
    spaced(d, 805, 88, "COFFEE", font(BOLD, 34), (240, 236, 220, 255), 6)
    for j, (a, b) in enumerate((("LATTE", "$7"), ("OAT MILK", "+$1"), ("EXTRA SHOT", "+$1"))):
        d.text((630, 138 + j * 34), a, font=font(MONO, 24), fill=(220, 216, 200, 255))
        d.text((930, 138 + j * 34), b, font=font(MONO, 24), fill=(240, 200, 120, 255))
    # hanging lamps
    for x in (330, 480):
        d.line([(x, 58), (x, 90)], fill=(80, 80, 86, 255), width=3)
        d.chord([x - 40, 70, x + 40, 130], 180, 360, fill=(240, 200, 120, 255), outline=ink)
    return im


def draw_cafe_counter(d):
    ink = INK + (255,)
    x0, x1, cy = C_COUNTER
    d.rectangle([x0, cy, x1, FYP], fill=(110, 80, 60, 255), outline=ink, width=4)
    d.rectangle([x0, cy, x1, cy + 16], fill=(200, 196, 190, 255), outline=ink, width=3)
    # espresso machine and card reader
    d.rounded_rectangle([900, cy - 110, 1030, cy], 10, fill=(180, 184, 194, 255), outline=ink, width=4)
    d.rectangle([930, cy - 40, 1000, cy - 30], fill=(60, 60, 66, 255))
    d.rounded_rectangle([600, cy - 46, 650, cy], 6, fill=(40, 42, 50, 255), outline=ink, width=3)
    d.rectangle([608, cy - 40, 642, cy - 26], fill=(90, 200, 120, 255))


def build_beach():
    im = Image.new("RGBA", (W, PH), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    ink = INK + (255,)
    for y in range(0, 380):
        d.line([(0, y), (W, y)], fill=PW.lerp_c((90, 170, 230), (200, 230, 250), y / 380) + (255,))
    d.ellipse([760, 70, 880, 190], fill=(255, 220, 110, 255))
    d.rectangle([0, 380, W, 470], fill=(40, 150, 200, 255))
    for j in range(8):
        x = j * 140
        d.arc([x, 372, x + 70, 392], 200, 340, fill=(230, 245, 250, 255), width=4)
    d.rectangle([0, 470, W, PH], fill=(240, 214, 160, 255))
    # palm
    d.line([(900, FYP), (880, 300)], fill=(140, 100, 60, 255), width=22)
    for a in (-160, -120, -60, -20, 20):
        r = math.radians(a)
        d.line([(880, 300), (880 + 150 * math.cos(r), 300 + 60 * math.sin(r) + 40)], fill=(60, 150, 80, 255), width=16)
    # beach chair
    d.polygon([(300, FYP - 120), (620, FYP - 140), (630, FYP - 120), (310, FYP - 100)], fill=(240, 90, 80, 255),
              outline=ink)
    d.polygon([(300, FYP - 120), (230, FYP - 250), (250, FYP - 260), (320, FYP - 110)], fill=(240, 90, 80, 255),
              outline=ink)
    for x in (320, 600):
        d.line([(x, FYP - 115), (x, FYP)], fill=ink, width=6)
    return im


def draw_jar(d, t):
    ink = INK + (255,)
    jx, jy = JAR
    if t >= T_BREAK:
        k = prog(t, T_BREAK, T_BREAK + 0.5)
        rng = np.random.default_rng(4)
        for j in range(10):
            a = rng.uniform(-math.pi, 0)
            r = 20 + 90 * k
            x, y = jx + r * math.cos(a), jy - 50 + r * math.sin(a) + 160 * k * k
            if y < jy:
                d.polygon([(x, y), (x + 10, y + 4), (x + 4, y + 12)], fill=(200, 230, 240, 200))
                d.ellipse([x + 14, y, x + 26, y + 12], fill=(240, 200, 70, 255))
        return
    fill = prog(t, T_Y0, T_Y1)
    h = 110
    d.rounded_rectangle([jx - 40, jy - h, jx + 40, jy], 12, fill=(200, 230, 240, 90), outline=ink, width=4)
    if fill > 0:
        fy = jy - 6 - (h - 20) * fill
        d.rounded_rectangle([jx - 34, fy, jx + 34, jy - 6], 8, fill=(240, 200, 70, 255))
        for j in range(int(8 * fill)):
            cx = jx - 24 + (j % 4) * 16
            cy = jy - 14 - (j // 4) * 12
            d.ellipse([cx - 6, cy - 4, cx + 6, cy + 4], outline=(200, 150, 40, 255), width=2)
    d.rectangle([jx - 42, jy - h - 14, jx + 42, jy - h], fill=(150, 156, 166, 255), outline=ink, width=3)
    d.rounded_rectangle([jx - 36, jy - 70, jx + 36, jy - 44], 4, fill=(250, 250, 252, 255), outline=ink, width=2)
    spaced(d, jx, jy - 66, "TRIP FUND", font("Inter-Bold.otf", 14), (30, 30, 34, 255), 1)


def fancy_cup(d, cx, by, stage):
    """by = bottom y of the cup"""
    ink = INK + (255,)
    h = 54 + 10 * stage
    w = 40 + 4 * stage
    d.polygon([(cx - w / 2, by - h), (cx + w / 2, by - h), (cx + w / 2 - 6, by), (cx - w / 2 + 6, by)],
              fill=(250, 250, 252, 255), outline=ink)
    d.rectangle([cx - w / 2 + 4, by - h * 0.6, cx + w / 2 - 4, by - h * 0.35], fill=(170, 120, 80, 255))
    d.rectangle([cx - w / 2 - 2, by - h - 8, cx + w / 2 + 2, by - h], fill=(230, 230, 236, 255), outline=ink, width=2)
    top = by - h - 8
    if stage >= 2:
        d.chord([cx - w / 2, top - 30, cx + w / 2, top + 12], 180, 360, fill=(255, 255, 255, 255), outline=ink)
        top -= 18
    if stage >= 3:
        for j in range(3):
            d.arc([cx - w / 2 + 6 + j * 8, top - 6, cx + w / 2 - 6 - j * 8, top + 20], 200, 340, fill=(200, 130, 50, 255),
                  width=3)
    if stage >= 4:
        for j, c in enumerate(((240, 80, 120), (90, 170, 240), (250, 210, 60), (120, 200, 110))):
            d.rectangle([cx - 14 + j * 8, top + 2 - (j % 2) * 6, cx - 10 + j * 8, top + 6 - (j % 2) * 6], fill=c + (255,))
    if stage >= 5:
        d.line([(cx + 6, top + 6), (cx + 20, top - 50)], fill=(240, 80, 80, 255), width=6)


def draw_prop(d, pts, prop, t, good):
    ink = INK + (255,)
    hx, hy = pts["hl"]
    if prop in ("pour", "mug"):
        d.rounded_rectangle([hx - 14, hy - 30, hx + 14, hy + 2], 5, fill=(240, 240, 236, 255), outline=ink, width=3)
    elif prop == "coin":
        d.ellipse([hx - 8, hy - 8, hx + 8, hy + 8], fill=(240, 200, 70, 255), outline=ink, width=2)
    elif prop == "ticket":
        d.rounded_rectangle([hx - 6, hy - 60, hx + 80, hy - 14], 6, fill=(250, 250, 252, 255), outline=ink, width=3)
        d.polygon([(hx + 14, hy - 36), (hx + 40, hy - 50), (hx + 36, hy - 34), (hx + 60, hy - 30), (hx + 38, hy - 28)],
                  fill=(60, 120, 200, 255))
    elif prop == "coconut":
        hx, hy = pts["hr"]
        d.ellipse([hx - 18, hy - 24, hx + 18, hy + 10], fill=(130, 90, 50, 255), outline=ink, width=3)
        d.line([(hx + 4, hy - 20), (hx + 16, hy - 50)], fill=(240, 80, 120, 255), width=5)
    elif prop == "card":
        d.rounded_rectangle([hx - 4, hy - 14, hx + 30, hy + 6], 4, fill=(60, 120, 200, 255), outline=ink, width=2)
    elif prop in ("cup", "cup_phone"):
        st = cup_stage(t)
        fancy_cup(d, hx, hy + 20, st)
        if prop == "cup_phone":
            hx2, hy2 = pts["hr"]
            d.rounded_rectangle([hx2 - 10, hy2 - 26, hx2 + 12, hy2 + 10], 4, fill=(30, 32, 40, 255),
                                outline=(150, 180, 255, 255), width=3)


def wrapped(im, t):
    if t < T_WRAP:
        return
    k = out_back(prog(t, T_WRAP, T_WRAP + 0.35))
    cw, ch = 470, 330
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    for y in range(ch):
        d.line([(0, y), (cw, y)], fill=PW.lerp_c((120, 60, 200), (240, 90, 120), y / ch) + (255,))
    m = Image.new("L", (cw, ch), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, cw - 1, ch - 1], 24, fill=255)
    card.putalpha(m)
    d = ImageDraw.Draw(card)
    spaced(d, cw / 2, 24, "YOUR 2026", font("Inter-Bold.otf", 24), (255, 255, 255, 230), 4)
    spaced(d, cw / 2, 56, "COFFEE WRAPPED", font(BOLD, 38), (255, 255, 255, 255), 2)
    spaced(d, cw / 2, 122, "365 LATTES", font(BOLD, 34), (255, 240, 200, 255), 2)
    spaced(d, cw / 2, 170, "$2,555", font(BOLD, 64), (255, 255, 255, 255), 2)
    spaced(d, cw / 2, 260, "THAT'S A TRIP TO HAWAII.", font("Inter-Bold.otf", 24), (255, 255, 255, 240), 2)
    card = card.resize((max(1, int(cw * k)), max(1, int(ch * k))), Image.LANCZOS)
    im.alpha_composite(card, (int(760 - card.width / 2), int(250 - card.height / 2)))


def widget(d, x, y, label, value, col):
    d.rounded_rectangle([x, y, x + 260, y + 92], 8, fill=(18, 20, 28, 230), outline=(90, 94, 104, 255), width=2)
    spaced(d, x + 130, y + 10, label, font("Inter-SemiBold.otf", 21), (190, 194, 204, 255), 4)
    spaced(d, x + 130, y + 38, value, font(MONO, 40), col + (255,), 1)


def sprite(pts, body, far, facing):
    cv = AJ.Canvas(*PW.bbox_of(list(pts.values()), 140))
    AJ.draw_stick(cv, pts, body, far, facing)
    return cv.done()


KITCHEN = CAFE = BEACH = None
FRAME0 = None


def panel(t, good):
    if good:
        im = (BEACH if t >= T_BEACH else KITCHEN).copy()
    else:
        im = CAFE.copy()
    d = ImageDraw.Draw(im)
    if good and t < T_BEACH:
        draw_jar(d, t)
    pose, hip, facing, prop = good_person(t) if good else bad_person(t)
    if not good:
        bpts = AJ.place(dict(STAND, el=(-30, -70), hl=(-50, -90)) if (t % MONTH) < 0.3 and T_Y0 < t < T_WRAP else STAND,
                        BARISTA, -1, SC)
        bspr, boff = sprite(bpts, BAR_C, BAR_FAR, -1)
        im.alpha_composite(bspr, boff)
        d = ImageDraw.Draw(im)
        draw_cafe_counter(d)
    pts = AJ.place(pose, hip, facing, SC)
    body, far = (GOOD_C, GOOD_FAR) if good else (BAD_C, BAD_FAR)
    spr, off = sprite(pts, body, far, facing)
    if good:
        im.alpha_composite(PW.glow_of(spr, 0.4, 12), off)
    im.alpha_composite(spr, off)
    d = ImageDraw.Draw(im)
    draw_prop(d, pts, prop, t, good)
    if good and t < T_BEACH:
        # steam from the mug and the kettle
        kx, ky = KETTLE
        for j in range(2):
            ph = (t * 0.8 + j * 0.5) % 1.0
            d.ellipse([kx + 70 + 20 * ph - 8, ky - 100 - 50 * ph - 8, kx + 70 + 20 * ph + 8, ky - 100 - 50 * ph + 8],
                      fill=(230, 234, 244, int(120 * (1 - ph))))
    # widgets
    if good and t >= T_Y0:
        if t < T_BEACH:
            widget(d, 790, 70 if t < T_BEACH else 70, "COFFEE", "$0.40/DAY", (240, 240, 244))
            saved = int(round(6.6 * day_of_year(t)))
            widget(d, 790, 176, "TRIP FUND", f"${saved:,}", (120, 230, 150))
        else:
            widget(d, 40, 70, "TRIP FUND", "$2,409", (120, 230, 150))
    if not good and T_Y0 <= t < T_WRAP:
        spent = 7 * day_of_year(t)
        widget(d, 40, 70, "SPENT ON COFFEE", f"${spent:,}", (240, 120, 120) if spent > 1000 else (240, 200, 120))
    if not good:
        wrapped(im, t)
        OC.speech_at(im, t, BUB_BARISTA, bpts)
    OC.speech_at(im, t, BUB_GOOD if good else BUB_BAD, pts)
    if good:
        k = 1 - abs(prog(t, T_BEACH - 0.25, T_BEACH + 0.25) * 2 - 1)
        if k > 0:
            im.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, int(200 * k))))
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
    img.alpha_composite(zoom(panel(t, True), t, (460, 420)), (0, TOP_Y0))
    img.alpha_composite(zoom(panel(t, False), t, (460, 420)), (0, BOT_Y0))
    d = ImageDraw.Draw(img)
    d.line([(0, STRIP_Y), (W, STRIP_Y)], fill=(56, 56, 62, 255), width=2)
    s = strip_text(t)
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
            spaced(ld, W / 2, TOP_Y0 + 14, "HOME COFFEE", fl, (240, 242, 248, int(255 * la)), 10)
        spaced(ld, W / 2, BOT_Y0 + 14, "$7 LATTE", fl, (220, 224, 232, int(255 * la)), 10)
        img.alpha_composite(lay)
        d = ImageDraw.Draw(img)
    fm = font(BOLD, 56)
    for t0, s2, y in ((T_L1, LINE1, 40), (T_L2, LINE2, 110)):
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
    global KITCHEN, CAFE, BEACH
    KITCHEN, CAFE, BEACH = build_kitchen(), build_cafe(), build_beach()


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
    mus = music.score(MUSIC, DUR, t_end=T_BREAK, start=0.0 if STRONG else 0.2, loud=1.2 if STRONG else 1.0)
    fx = np.zeros((n, 2))
    m = 0
    while T_Y0 + m * MONTH < T_BREAK - 0.1:
        t0 = T_Y0 + m * MONTH
        # below: the card reader beep; above: a coin in the jar
        mix_in(fx, tone(1760, 0.07, (1,), a=0.002, d=0.035), t0 + 0.12, 0.03, 0.35)
        mix_in(fx, tone(2637, 0.18, (1, 0.4), a=0.001, d=0.08), t0 + 0.85 * MONTH, 0.025, -0.35)
        m += 1
    # the jar breaks, a whoosh to the beach, the wrapped "ta-da"
    mix_in(fx, noise(0.4, 3, lo=2000, hi=9000) * env(int(0.4 * SR), 0.001, 0.15), T_BREAK, 0.07, -0.3)
    mix_in(fx, noise(0.6, 5, lo=300, hi=3000) * env(int(0.6 * SR), 0.2, 0.25), T_BEACH - 0.3, 0.05, -0.3)
    w = noise(DUR - T_BEACH, 11, lo=200, hi=1500)
    i0 = int(T_BEACH * SR)
    sw = w * (0.5 + 0.5 * np.sin(np.arange(len(w)) / SR * 1.3)) * 0.012
    fx[i0:i0 + len(sw), 0] += sw * 1.2
    fx[i0:i0 + len(sw), 1] += sw * 0.6
    for j, f in enumerate((523, 659, 784)):
        mix_in(fx, tone(f, 0.4, (1, 0.3), a=0.003, d=0.25), T_WRAP + 0.06 * j, 0.03, 0.35)
    for b0, b1, s, w_ in BUB_GOOD + BUB_BAD + BUB_BARISTA:
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
    out = sys.argv[1] if len(sys.argv) > 1 else "latte.mp4"
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
