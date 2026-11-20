#!/usr/bin/env python3
"""BLACK FRIDAY (queue #1). Split screen, 18 s, loops on itself. Opening: A. Music: guitar.

11:00 PM, the same bed, the same ad: 65" TV $299 - BLACK FRIDAY, DOORS OPEN 6 AM. Both: "I NEED THAT TV."
Above, he goes to sleep; at 6:00 AM he taps BUY in bed - "DONE." - and sleeps on; the TV is at his door by 9.
Below, 3:00 AM in line outside MEGA MART in the cold: "WORTH IT." "I CAN'T FEEL MY FEET." The doors open, the crowd
rushes in, he comes out with the box, a bandage and one shoe: "GOT IT." - PAID $299, SLEPT 0h. Then his phone:
"65\" TV $299 online, free delivery." "...ONLINE?"
"SAME TV. SAME PRICE. / ONE OF THEM SLEPT."  FOLLOW FOR MORE.

    python3 stick/black_friday.py stick/black-friday.mp4
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
MUSIC = "guitar_g"

W, H, FPS = 1080, 1920, 30
SR = 44100
DUR = 18.0
NF = int(round(DUR * FPS))
XFADE = 0.45
SC = AJ.SC
INK = AJ.INK
GOOD_C, GOOD_FAR = AJ.DOER, AJ.DOER_FAR
BAD_C, BAD_FAR = AJ.OT, AJ.OT_FAR
CROWD_C, CROWD_FAR = (86, 92, 110), (66, 70, 86)
RED = (255, 64, 56)
BOLD = FM.BOLD
PH, TOP_Y0, BOT_Y0, STRIP_Y, FYP = OC.PH, OC.TOP_Y0, OC.BOT_Y0, OC.STRIP_Y, OC.FYP
STAND_Y = FYP - 141

BED = (90, 640)
MATT = FYP - 150
BED_HIP = (210, MATT - 10)
WIN = (330, 70, 560, 280)
DOOR = (870, 990, FYP - 300)
STORE_DOOR = (640, 860)                    # glass doors x0, x1
ME_X = 420

# ---------------------------------------------------------------- timeline
T_CUT = 1.7                                # below: bedroom -> the line
T_BUY = 8.2
T_OPEN = 8.0                               # store doors
T_OUT = 10.4                               # he comes out with the box
T_HOME0, T_HOME1 = 10.8, 12.6
T_BELL = 11.4
T_PING = 13.2
T_L1, T_L2 = 15.0, 16.1
CPS = 18.0
LINE1, LINE2 = "SAME TV. SAME PRICE.", "ONE OF THEM SLEPT."
T_FOLLOW = 16.95

B0 = -0.3 if STRONG else 0.3
BUB_GOOD = [(B0, 1.5, "I NEED THAT TV.", "me"), (8.5, 9.3, "DONE.", "me"), (12.9, 13.9, "NICE.", "me")]
BUB_BAD = [(B0, 1.5, "I NEED THAT TV.", "me"), (3.0, 4.1, "WORTH IT.", "me"), (5.4, 6.6, "I CAN'T FEEL MY FEET.", "me"),
           (10.7, 11.6, "GOT IT.", "me"), (13.9, 14.95, "...ONLINE?", "me")]


def clock_minutes(t):
    if t < T_CUT:
        return 23 * 60
    if t < 2.1:
        return 3 * 60 + 24 * 60
    if t < 8.0:
        return int(27 * 60 + 180 * prog(t, 2.1, 8.0))
    return int(30 * 60 + 210 * prog(t, 8.0, 13.0))


def fmt12(mm):
    mm %= 1440
    h, m = mm // 60, mm % 60
    ap = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d} {ap}"


def daylight(t):
    return smooth(prog(t, 7.6, 12.0))


# ---------------------------------------------------------------- poses
SIT_BED = {"head": (14, -148), "neck": (8, -106), "el": (30, -60), "hl": (58, -46), "er": (26, -56), "hr": (54, -42),
           "kl": (60, -10), "fl": (120, -4), "kr": (60, -4), "fr": (120, 2)}
SIT_PHONE = dict(SIT_BED, el=(28, -66), hl=(48, -98), er=(24, -62), hr=(44, -94))
LIE = {"head": (-110, -30), "neck": (-70, -24), "el": (-40, -50), "hl": (-20, -30), "er": (-44, -46), "hr": (-24, -26),
       "kl": (60, -8), "fl": (120, -4), "kr": (60, -2), "fr": (120, 2)}
LIE_PHONE = dict(LIE, el=(-30, -100), hl=(-50, -140), er=(-26, -96), hr=(-46, -136))
STAND = PW.STAND
THERMOS = dict(STAND, el=(26, -80), hl=(34, -112), er=(10, -58), hr=(14, -10))
HUDDLE = dict(STAND, head=(6, -144), el=(24, -70), hl=(-8, -92), er=(28, -66), hr=(-4, -88))
CARRY = dict(STAND, head=(4, -146), el=(30, -96), hl=(60, -110), er=(26, -92), hr=(56, -106))
PHONE_STAND = OC.STAND_PHONE


def walk(t, t0, speed=7.0):
    return AJ.walk((t - t0) * speed, STAND)


def good_person(t):
    """pose, hip, facing, prop"""
    if t < T_CUT:
        return SIT_PHONE, BED_HIP, 1, "phone"
    lie_hip = (300, MATT - 4)
    if t < 2.3:
        k = smooth(prog(t, T_CUT, 2.3))
        return lerp_pose(SIT_PHONE, LIE, k), (lerp(BED_HIP[0], 300, k), lerp(BED_HIP[1], MATT - 4, k)), 1, None
    if t < T_BUY - 0.4:
        return LIE, lie_hip, 1, "sleep"
    if t < 9.4:
        return LIE_PHONE, lie_hip, 1, "phone"
    if t < T_BELL:
        return LIE, lie_hip, 1, "sleep"
    # up to the door, picks up the box
    if t < T_BELL + 0.4:
        k = smooth(prog(t, T_BELL, T_BELL + 0.4))
        return lerp_pose(LIE, SIT_BED, k), (lerp(300, BED_HIP[0] + 120, k), lerp(MATT - 4, BED_HIP[1], k)), 1, None
    if t < 12.4:
        k = smooth(prog(t, T_BELL + 0.4, 12.4))
        return walk(t, T_BELL + 0.4), (lerp(BED_HIP[0] + 160, 790, k), STAND_Y), 1, None
    return CARRY, (790, STAND_Y), -1, "tv"


QUEUE = [(760, 1.0, False), (640, 1.0, False), (530, 1.0, False),            # ahead of him: x, appear, joins later
         (310, 3.4, True), (200, 4.6, True), (90, 5.8, True)]


def bad_person(t):
    """pose, hip, facing, prop, alpha"""
    if t < T_CUT:
        return SIT_PHONE, BED_HIP, 1, "phone", 1
    if t < T_OPEN:
        sip = math.sin(math.pi * clamp((t % 2.6) / 0.9)) if t % 2.6 < 0.9 else 0
        base = HUDDLE if t > 5.0 else STAND
        pose = lerp_pose(base, THERMOS, sip)
        return pose, (ME_X + 1.5 * math.sin(t * 40) * (t > 5.0), STAND_Y), 1, "thermos", 1
    if t < 8.9:
        k = smooth(prog(t, T_OPEN + 0.3, 8.9))
        a = 1 - smooth(prog(t, 8.7, 8.95))
        return walk(t, T_OPEN + 0.3, 11), (lerp(ME_X, 750, k), STAND_Y), 1, None, a
    if t < T_OUT:
        return STAND, (750, STAND_Y), -1, None, 0
    if t < T_HOME0:
        a = smooth(prog(t, T_OUT, T_OUT + 0.3))
        return CARRY, (750, STAND_Y), -1, "tv", a
    if t < T_HOME1:
        k = smooth(prog(t, T_HOME0, T_HOME1))
        p = dict(walk(t, T_HOME0, 4.5), **{j: CARRY[j] for j in ("el", "hl", "er", "hr", "head")})
        return p, (lerp(750, 380, k), STAND_Y + 4 * abs(math.sin(t * 4))), -1, "tv", 1
    if t < T_PING:
        return CARRY, (380, STAND_Y), -1, "tv", 1
    return PHONE_STAND, (380, STAND_Y), -1, "phone", 1


def crowd(t):
    """[(pose, hip, alpha)] for the people in the line"""
    out = []
    for i, (x, t_in, later) in enumerate(QUEUE):
        a = smooth(prog(t, t_in, t_in + 0.4)) if later else 1.0
        if t < T_CUT + 0.2 or a < 0.01:
            continue
        if t < T_OPEN:
            pose = HUDDLE if i % 2 else STAND
            out.append((pose, (x + 1.2 * math.sin(t * 30 + i), STAND_Y), a))
            continue
        start = T_OPEN + 0.05 * (len(QUEUE) - i) * 0 + (0.0 if x > ME_X else 0.4 + 0.1 * (ME_X - x) / 80)
        k = prog(t, start, start + 0.9 * (800 - x) / 400)
        xx = lerp(x, 760, k)
        fade = 1 - smooth(prog(xx, 720, 760))
        if fade > 0.01:
            out.append((walk(t, start, 11), (xx, STAND_Y), a * fade))
    return out


# ---------------------------------------------------------------- drawing
def build_bedroom():
    yy, xx = np.mgrid[0:PH, 0:W].astype(np.float32)
    base = np.array((31, 30, 40) if STRONG else (9, 9, 11), np.float32)
    img = np.zeros((PH, W, 3), np.float32) + base
    img = np.where((yy > FYP)[..., None], img * 0.75 + 6, img)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    ink = INK + (255,)
    d.line([(0, FYP), (W, FYP)], fill=(56, 54, 54, 255), width=2)
    x0, x1 = BED
    d.rounded_rectangle([x0 - 30, FYP - 330, x0 + 6, FYP], 10, fill=(84, 66, 52, 255), outline=ink, width=4)
    d.rounded_rectangle([x0, MATT, x1, MATT + 70], 12, fill=(222, 222, 228, 255), outline=ink, width=4)
    d.rectangle([x0, MATT + 70, x1, FYP - 30], fill=(84, 66, 52, 255), outline=ink, width=4)
    d.rounded_rectangle([x0 + 6, MATT - 60, x0 + 110, MATT + 6], 18, fill=(240, 240, 244, 255), outline=ink, width=3)
    d.rectangle([680, FYP - 150, 790, FYP], fill=(100, 76, 56, 255), outline=ink, width=4)
    return im


def build_store():
    """The store front with a transparent sky."""
    im = Image.new("RGBA", (W, PH), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ink = INK + (255,)
    d.rectangle([0, 60, W, FYP], fill=(60, 62, 72, 255))
    d.rectangle([0, 60, W, 80], fill=(80, 82, 94, 255))
    # sign
    d.rounded_rectangle([560, 96, 780, 176], 10, fill=(30, 90, 170, 255), outline=ink, width=4)
    spaced(d, 670, 118, "MEGA MART", font(BOLD, 30), (250, 250, 252, 255), 1)
    # windows
    for x in (40, 300):
        d.rectangle([x, 250, x + 220, FYP - 120], fill=(36, 44, 60, 255), outline=ink, width=5)
    d.rectangle([40, 120, 520, 176], fill=(220, 40, 40, 255), outline=ink, width=4)
    spaced(d, 280, 128, "BLACK FRIDAY", font(BOLD, 38), (255, 255, 255, 255), 6)
    # door frame
    x0, x1 = STORE_DOOR
    d.rectangle([x0 - 10, 210, x1 + 10, FYP], fill=(20, 22, 28, 255), outline=ink, width=5)
    # sidewalk
    d.rectangle([0, FYP, W, PH], fill=(40, 40, 44, 255))
    d.line([(0, FYP), (W, FYP)], fill=(80, 80, 86, 255), width=3)
    return im


def draw_sky(d, t):
    k = daylight(t)
    top = PW.lerp_c((8, 10, 24), (120, 160, 210), k)
    bot = PW.lerp_c((22, 26, 52), (230, 200, 160), k)
    for y in range(0, 62):
        d.line([(0, y), (W, y)], fill=PW.lerp_c(top, bot, y / 62) + (255,))
    if k < 0.5:
        rng = np.random.default_rng(1)
        for _ in range(30):
            x, y = rng.uniform(0, W), rng.uniform(0, 58)
            d.point((x, y), fill=(220, 220, 240, int(255 * (1 - 2 * k))))


def draw_store_doors(d, t):
    ink = INK + (255,)
    x0, x1 = STORE_DOOR
    k = smooth(prog(t, T_OPEN, T_OPEN + 0.4)) * (1 - smooth(prog(t, 11.5, 12.0)))
    inside = (230, 230, 210, 255) if t >= T_OPEN else (40, 50, 66, 255)
    d.rectangle([x0, 210, x1, FYP], fill=inside)
    half = (x1 - x0) / 2
    w = half * (1 - 0.85 * k)
    for xa, xb in ((x0, x0 + w), (x1 - w, x1)):
        d.rectangle([xa, 210, xb, FYP], fill=(120, 150, 180, 200), outline=ink, width=4)
    if t >= 10.0:
        a = int(255 * smooth(prog(t, 10.0, 10.3)))
        d.rounded_rectangle([60, 420, 240, 480], 8, fill=(250, 250, 252, a), outline=(220, 40, 40, a), width=4)
        spaced(d, 150, 432, "SOLD OUT", font(BOLD, 30), (220, 40, 40, a), 2)


def draw_bed_window(d, t, good):
    ink = INK + (255,)
    x0, y0, x1, y1 = WIN
    k = daylight(t) if t > T_CUT else 0
    top = PW.lerp_c((10, 14, 34), (110, 150, 210), k)
    bot = PW.lerp_c((24, 30, 60), (255, 200, 140), k)
    for i in range(y1 - y0):
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=PW.lerp_c(top, bot, i / (y1 - y0)) + (255,))
    for i in range(5):
        bx = x0 + 6 + i * 46
        bh = 40 + (i * 37) % 60
        d.rectangle([bx, y1 - bh, bx + 40, y1], fill=PW.lerp_c((14, 16, 28), (70, 70, 90), k) + (255,))
    d.rectangle([x0, y0, x1, y1], outline=ink, width=8)
    d.line([((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], fill=ink, width=6)


def draw_bed_door(d, t):
    ink = INK + (255,)
    x0, x1, y0 = DOOR
    d.rectangle([x0 - 8, y0 - 8, x1 + 8, FYP], fill=(20, 20, 24, 255), outline=ink, width=4)
    open_k = 0.0
    if 12.0 <= t < 13.4:
        open_k = math.sin(math.pi * prog(t, 12.0, 13.4))
    w = (x1 - x0) * (1 - 0.8 * open_k)
    d.rectangle([x1 - w, y0, x1, FYP], fill=(130, 96, 66, 255), outline=ink, width=4)
    d.ellipse([x1 - w + 14, y0 + 150, x1 - w + 30, y0 + 166], fill=(230, 200, 90, 255), outline=ink)
    if T_BELL <= t < 12.5:
        # the box waiting at the door
        d.rectangle([850, FYP - 70, 940, FYP], fill=(196, 150, 96, 255), outline=ink, width=3)


def tv_box(d, cx, cy, s=1.0):
    ink = INK + (255,)
    w, h = 130 * s, 90 * s
    d.rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], fill=(196, 150, 96, 255), outline=ink, width=4)
    d.rectangle([cx - w / 2 + 14, cy - h / 2 + 12, cx + w / 2 - 14, cy + h / 2 - 22], fill=(30, 32, 40, 255))
    spaced(d, cx, cy + h / 2 - 20, "65\" TV", font("Inter-Bold.otf", int(14 * s)), (30, 30, 34, 255), 1)


def draw_prop(d, pts, prop, t):
    ink = INK + (255,)
    if prop == "phone":
        hx, hy = pts["hl"]
        d.rounded_rectangle([hx - 10, hy - 26, hx + 12, hy + 10], 4, fill=(30, 32, 40, 255), outline=(150, 180, 255, 255),
                            width=3)
    elif prop == "thermos":
        hx, hy = pts["hl"]
        d.rounded_rectangle([hx - 10, hy - 34, hx + 10, hy + 6], 5, fill=(200, 60, 60, 255), outline=ink, width=3)
    elif prop == "tv":
        hx, hy = pts["hl"]
        hx2, hy2 = pts["hr"]
        tv_box(d, (hx + hx2) / 2, (hy + hy2) / 2 + 10, 1.0)
    elif prop == "sleep":
        for i in range(2):
            ph = (t * 0.7 + i * 0.5) % 1.0
            hx, hy = pts["head"]
            d.text((hx + 20 + 26 * ph + i * 12, hy - 60 - 50 * ph), "z", font=font("Inter-Bold.otf", 26 + 8 * i),
                   fill=(220, 226, 240, int(255 * math.sin(math.pi * ph))))


def draw_ad(im, t):
    if t >= T_CUT:
        return
    k = out_back(prog(t, 0.0 if STRONG else 0.2, 0.5))
    if k < 0.05:
        return
    cw, ch = 330, 300
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, cw - 1, ch - 1], 18, fill=(20, 20, 24, 255), outline=(220, 40, 40, 255), width=4)
    spaced(d, cw / 2, 16, "BLACK FRIDAY", font(BOLD, 30), (240, 60, 60, 255), 3)
    d.rectangle([60, 64, cw - 60, 160], fill=(40, 44, 56, 255), outline=(200, 204, 214, 255), width=4)
    d.rectangle([150, 160, 180, 176], fill=(200, 204, 214, 255))
    spaced(d, cw / 2, 186, "65\" TV  $299", font(BOLD, 34), (250, 250, 252, 255), 1)
    spaced(d, cw / 2, 240, "DOORS OPEN 6 AM", font("Inter-SemiBold.otf", 22), (200, 204, 214, 255), 3)
    card = card.resize((max(1, int(cw * k)), max(1, int(ch * k))), Image.LANCZOS)
    im.alpha_composite(card, (int(850 - card.width / 2), int(300 - card.height / 2)))


def draw_ping(im, t):
    if t < T_PING:
        return
    k = smooth(prog(t, T_PING, T_PING + 0.3))
    card = Image.new("RGBA", (680, 96), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, 679, 95], 18, fill=(245, 246, 250, 245), outline=(200, 204, 214, 255), width=2)
    d.rounded_rectangle([16, 18, 76, 78], 12, fill=(30, 90, 170, 255))
    spaced(d, 46, 32, "MM", font(BOLD, 22), (255, 255, 255, 255), 1)
    d.text((94, 16), "MEGA MART", font=font("Inter-Bold.otf", 22), fill=(20, 20, 24, 255))
    d.text((94, 48), "65\" TV $299 online · free delivery", font=font("Inter-SemiBold.otf", 24), fill=(40, 40, 46, 255))
    im.alpha_composite(card, (int(W / 2 - 340), int(lerp(-100, 70, k))))


def widget(d, x, y, label, value, col):
    d.rounded_rectangle([x, y, x + 240, y + 92], 8, fill=(18, 20, 28, 230), outline=(90, 94, 104, 255), width=2)
    spaced(d, x + 120, y + 10, label, font("Inter-SemiBold.otf", 21), (190, 194, 204, 255), 5)
    spaced(d, x + 120, y + 38, value, font(MONO, 40), col + (255,), 1)


def sprite(pts, body, far, facing, s=SC):
    cv = AJ.Canvas(*PW.bbox_of(list(pts.values()), 140))
    AJ.draw_stick(cv, pts, body, far, facing, s=s)
    return cv.done()


def bandage(d, pts):
    hx, hy = pts["head"]
    d.rounded_rectangle([hx - 26, hy - 20, hx + 6, hy - 8], 4, fill=(240, 220, 190, 255), outline=INK + (255,), width=2)
    d.line([(hx - 14, hy - 20), (hx - 14, hy - 8)], fill=(200, 170, 140, 255), width=2)


BEDROOM = STORE = None
FRAME0 = None


def panel(t, good):
    in_store = (not good) and t >= T_CUT
    if in_store:
        im = Image.new("RGBA", (W, PH), (0, 0, 0, 255))
        d = ImageDraw.Draw(im)
        draw_sky(d, t)
        im.alpha_composite(STORE)
        d = ImageDraw.Draw(im)
        draw_store_doors(d, t)
        # the line, behind him in depth order (left to right)
        for pose, hip, a in crowd(t):
            pts = AJ.place(pose, hip, 1, SC * 0.96)
            spr, off = sprite(pts, CROWD_C, CROWD_FAR, 1, SC * 0.96)
            if a < 0.999:
                spr.putalpha(spr.split()[3].point(lambda v, a=a: int(v * a)))
            im.alpha_composite(spr, off)
        # breath puffs in the cold
        if t < T_OPEN:
            d = ImageDraw.Draw(im)
            for x, t_in, later in QUEUE + [(ME_X, 0, False)]:
                ph = (t * 0.8 + x / 300) % 1.0
                if ph < 0.5 and (not later or t > t_in + 0.4):
                    r = 8 + 20 * ph
                    d.ellipse([x + 30 + 30 * ph - r, STAND_Y - 190 - 20 * ph - r, x + 30 + 30 * ph + r,
                               STAND_Y - 190 - 20 * ph + r], fill=(230, 234, 244, int(120 * (1 - 2 * ph))))
    else:
        im = BEDROOM.copy()
        d = ImageDraw.Draw(im)
        draw_bed_window(d, t, good)
        draw_bed_door(d, t)
    pose, hip, facing, prop, alpha = (good_person(t) + (1,)) if good else bad_person(t)
    pts = {"head": (750, 300)}
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
        if not in_store and (good or t < T_CUT) and pose in (LIE, LIE_PHONE) or (not in_store and pose is SIT_PHONE):
            # the blanket
            hx, hy = pts["hip"]
            d.rounded_rectangle([hx - 30, MATT - 40, BED[1] - 6, MATT + 50], 22, fill=(96, 110, 150, 255),
                                outline=INK + (255,), width=4)
        if in_store and t >= T_OUT:
            bandage(d, pts)
        draw_prop(d, pts, prop, t)
    # widgets
    if good:
        if T_CUT <= t < T_BUY + 0.3:
            hrs = int(7 * prog(t, T_CUT, T_BUY))
            widget(d, 800, 100, "SLEPT", f"{hrs}h", (120, 230, 150))
        elif t >= T_BUY + 0.3:
            widget(d, 800, 100, "PAID", "$299", (240, 240, 244))
            widget(d, 800, 206, "SLEPT", "9h", (120, 230, 150))
    elif in_store:
        if t < T_OUT:
            hrs = int(3 * prog(t, 2.1, T_OPEN))
            widget(d, 800, 60, "IN LINE", f"{hrs}h", (240, 200, 120))
        elif t < T_PING:
            widget(d, 800, 60, "PAID", "$299", (240, 240, 244))
            widget(d, 800, 166, "SLEPT", "0h", (240, 120, 120))
    if good and T_BUY - 0.4 <= t < 9.6:
        k = smooth(prog(t, T_BUY, T_BUY + 0.2))
        if k > 0:
            hx, hy = pts["hl"]
            d.rounded_rectangle([hx + 20, hy - 70, hx + 150, hy - 30], 8, fill=(60, 170, 90, int(255 * k)))
            spaced(d, hx + 85, hy - 62, "ORDERED", font("Inter-Bold.otf", 20), (255, 255, 255, int(255 * k)), 2)
    draw_ad(im, t)
    if not good:
        draw_ping(im, t)
    OC.speech_at(im, t, BUB_GOOD if good else BUB_BAD, pts)
    # the cut from the bedroom to the street (below)
    if not good:
        k = 1 - abs(prog(t, T_CUT - 0.25, T_CUT + 0.25) * 2 - 1)
        if 0 < k:
            im.alpha_composite(Image.new("RGBA", im.size, (0, 0, 0, int(255 * k))))
    return im


def frame(t):
    img = Image.new("RGBA", (W, H), (5, 5, 7, 255))
    img.alpha_composite(panel(t, True), (0, TOP_Y0))
    img.alpha_composite(panel(t, False), (0, BOT_Y0))
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
    if t < T_L1:
        spaced(d, W / 2, TOP_Y0 + 14, "SHOPS FROM BED", fl, (240, 242, 248, 255), 10)
    spaced(d, W / 2, BOT_Y0 + 14, "LINES UP AT 3 AM", fl, (220, 224, 232, 255), 10)
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
    global BEDROOM, STORE
    BEDROOM, STORE = build_bedroom(), build_store()


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
    mus = music.score(MUSIC, DUR, t_end=T_PING, start=0.0 if STRONG else 0.2, loud=1.2 if STRONG else 1.0)
    fx = np.zeros((n, 2))
    # night street hum below, wind
    w = noise(DUR, 12, lo=150, hi=700)
    e = np.clip((np.arange(n) / SR - T_CUT) / 0.5, 0, 1) * np.clip((T_OPEN + 0.5 - np.arange(n) / SR) / 0.5, 0, 1)
    fx[:, 0] += w * e * 0.012
    fx[:, 1] += np.roll(w, 2000) * e * 0.012
    # the buy tap, the doors, the rush
    mix_in(fx, tone(1320, 0.1, (1, 0.3), a=0.002, d=0.05), T_BUY, 0.05, -0.3)
    mix_in(fx, tone(1760, 0.14, (1, 0.3), a=0.002, d=0.07), T_BUY + 0.08, 0.04, -0.3)
    mix_in(fx, noise(0.5, 8, lo=200, hi=2000) * env(int(0.5 * SR), 0.05, 0.3), T_OPEN, 0.06, 0.3)
    mix_in(fx, noise(1.6, 9, lo=100, hi=1500) * env(int(1.6 * SR), 0.2, 0.8), T_OPEN + 0.3, 0.1, 0.3)
    for tk in (9.2, 9.5, 9.9):
        mix_in(fx, noise(0.15, int(tk * 10), lo=80, hi=900) * env(int(0.15 * SR), 0.002, 0.07), tk, 0.08, 0.4)
    # doorbell above, the phone ping below
    mix_in(fx, music.music_box(midi(76), 1.0), T_BELL, 0.07, -0.3)
    mix_in(fx, music.music_box(midi(72), 1.2), T_BELL + 0.3, 0.07, -0.3)
    mix_in(fx, tone(1568, 0.12, (1, 0.3), a=0.002, d=0.06), T_PING, 0.06, 0.3)
    mix_in(fx, tone(2093, 0.18, (1, 0.3), a=0.002, d=0.09), T_PING + 0.1, 0.05, 0.3)
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
    out = sys.argv[1] if len(sys.argv) > 1 else "black-friday.mp4"
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
