#!/usr/bin/env python3
"""IDEAS.md #7 - CLEANS IT NOW vs "I'LL CLEAN TOMORROW". Split screen, 18 s, loops on itself.

DAY 1, the same room, the same sock and plate on the floor. Above: "CLEAN IT NOW." - two minutes, into the hamper,
the room stays clean and his plant grows. Below: "CLEAN IT TOMORROW." - every day more stuff lands on the floor
("TOMORROW." "AFTER THIS VIDEO." "WEEKEND." "MONDAY. NEW ME." "IT'S ORGANIZED."), his plant wilts. DAY 7 he walks out
over the pile; the door shuts and the pile slides against it. DAY 8: the door won't open - THUD, THUD - and he climbs
in through the window, onto the pile. "...TOMORROW."  "HE SAID TOMORROW. / TOMORROW NEVER CLEANS."  FOLLOW FOR MORE.

Two openings (the A/B test the channel asked for):
    VARIANT=A  the current style - dark room, calm start.
    VARIANT=B  a stronger first second - brighter room, close-up on both that eases out, the sock already flying and
               the two bubbles on screen from frame 0.

    VARIANT=A python3 stick/clean_tomorrow.py stick/clean-tomorrow-A.mp4
    VARIANT=B python3 stick/clean_tomorrow.py stick/clean-tomorrow-B.mp4
    VARIANT=B ONLY_FRAMES=0,1.0,2.8,6.0,9.8,11.2,12.5,13.6,14.4,15.8 python3 stick/clean_tomorrow.py /tmp/ct
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
from perfect_wave import (MONO, clamp, env, font, lerp, lerp_pose, midi, mix_in, noise, out_back,  # noqa
                          prog, smooth, spaced, tone, write_wav)

VARIANT = os.environ.get("VARIANT", "A").upper()
STRONG = VARIANT == "B"

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
NOW_C, NOW_FAR = AJ.DOER, AJ.DOER_FAR
TMR_C, TMR_FAR = AJ.OT, AJ.OT_FAR
RED = (255, 64, 56)
BOLD = FM.BOLD
PH, TOP_Y0, BOT_Y0, STRIP_Y, FYP = OC.PH, OC.TOP_Y0, OC.BOT_Y0, OC.STRIP_Y, OC.FYP

STAND_Y = FYP - 141
SIT_HIP = (200, FYP - 140)
BED = (40, 330, FYP - 128)                 # x0, x1, mattress top
WIN = (430, 110, 650, 330)                 # window; the sill is its bottom edge
DOOR = (850, 990, FYP - 300)               # x0, x1, top
HAMPER_X = 760
PILE_X0, PILE_X1 = 370, 800

# ---------------------------------------------------------------- timeline
DAYS = [0.0, 2.2, 3.6, 5.0, 6.4, 7.8, 9.2, 12.0]          # DAY 1 .. DAY 8 start
T_EXIT0, T_EXIT1 = 9.4, 10.5                               # walks out (both)
T_SHUT, T_SLIDE0, T_SLIDE1 = 10.75, 10.85, 11.5
T_THUD = [12.15, 12.5, 12.85]
T_CLIMB0, T_CLIMB1 = 13.1, 14.1
T_IN0, T_IN1 = 12.1, 13.0                                  # top comes home
T_L1, T_L2 = 15.0, 16.1
CPS = 18.0
LINE1, LINE2 = "HE SAID TOMORROW.", "TOMORROW NEVER CLEANS."
T_FOLLOW = 16.95

B0 = -0.3 if STRONG else 0.3
BUB_NOW = [(B0, 1.5, "CLEAN IT NOW.", "me"), (12.6, 13.6, "HOME.", "me")]
BUB_TMR = [(B0, 1.5, "CLEAN IT TOMORROW.", "me"), (2.7, 3.5, "TOMORROW.", "me"), (4.1, 4.9, "AFTER THIS VIDEO.", "me"),
           (5.5, 6.3, "WEEKEND.", "me"), (6.9, 7.7, "MONDAY. NEW ME.", "me"), (8.3, 9.2, "IT'S ORGANIZED.", "me"),
           (14.2, 14.95, "...TOMORROW.", "me")]


def day(t):
    n = 1
    for i, s in enumerate(DAYS):
        if t >= s:
            n = i + 1
    return n


# ---------------------------------------------------------------- the pile
def build_pile():
    rng = np.random.default_rng(7)
    bins = np.zeros(W // 10 + 1)
    items = []

    def put(x, w, h, kind, col, t_in, rot):
        b0, b1 = int((x - w / 2) // 10), int((x + w / 2) // 10) + 1
        base = bins[b0:b1].max()
        y = FYP - base - h / 2
        bins[b0:b1] = base + h * 0.85
        items.append(dict(x=x, y=y, w=w, h=h, kind=kind, col=col, t=t_in, rot=rot))

    cols = [(220, 80, 70), (80, 150, 220), (240, 200, 70), (120, 190, 110), (200, 120, 200), (230, 230, 236)]
    put(520, 46, 16, "sock", cols[0], -9, 8)
    put(640, 70, 14, "plate", cols[5], -9, 0)
    counts = [0, 4, 5, 5, 5, 4]
    for d in range(1, 6):
        for j in range(counts[d]):
            kind = ["shirt", "box", "bottle", "sock", "bag", "plate", "shirt", "box"][rng.integers(8)]
            w = 1.35 * {"shirt": 80, "box": 96, "bottle": 24, "sock": 46, "bag": 64, "plate": 70}[kind]
            h = 1.35 * {"shirt": 34, "box": 22, "bottle": 60, "sock": 16, "bag": 56, "plate": 14}[kind]
            cands = rng.uniform(PILE_X0 + w / 2, PILE_X1 - w / 2, 4)
            x = min(cands, key=lambda c: bins[int((c - w / 2) // 10):int((c + w / 2) // 10) + 1].max())
            put(x, w, h, kind, cols[rng.integers(len(cols))], DAYS[d] + 0.12 + j * 0.1, rng.uniform(-14, 14))
    # the slide against the door
    slide = []
    for j in range(7):
        kind = ["box", "shirt", "bag", "box", "shirt", "bottle", "bag"][j]
        w = {"shirt": 80, "box": 96, "bottle": 24, "bag": 64}[kind]
        h = {"shirt": 34, "box": 22, "bottle": 60, "bag": 56}[kind]
        x = 870 + (j % 3) * 40
        put(x, w, h, kind, cols[(j * 2) % len(cols)], T_SLIDE0 + j * 0.08, rng.uniform(-20, 20))
        slide.append(len(items) - 1)
    return items, set(slide)


PILE, SLIDE = build_pile()
if __name__ == '__main__' and os.environ.get('PILE_DEBUG'):
    print('pile top', min(it['y'] - it['h'] / 2 for it in PILE), 'sill', WIN[3])


def pile_top(x, t):
    top = FYP
    for it in PILE:
        if it["t"] <= t and abs(it["x"] - x) < it["w"] / 2:
            top = min(top, it["y"] - it["h"] / 2)
    return top


def draw_item(im, it, t, top_room):
    if top_room and it["t"] > 0:
        return
    if top_room and t >= TOP_PICK:
        return
    if it["t"] > t:
        return
    k = prog(t, it["t"], it["t"] + 0.28)
    if k <= 0:
        return
    x, y = it["x"], it["y"]
    if (it["x"], it["t"]) in SLIDE_KEYS:
        x = lerp(700, x, out_back(k)) if k < 1 else x
        y = lerp(y - 80, y, k * k)
    else:
        y = lerp(y - 160, y, k * k)
    w, h = it["w"], it["h"]
    spr = Image.new("RGBA", (int(w + 20), int(h + 20)), (0, 0, 0, 0))
    d = ImageDraw.Draw(spr)
    ink = INK + (255,)
    c = it["col"] + (255,)
    kind = it["kind"]
    bx0, by0, bx1, by1 = 10, 10, 10 + w, 10 + h
    if kind == "sock":
        d.rounded_rectangle([bx0, by0, bx1, by1], 7, fill=c, outline=ink, width=3)
    elif kind == "plate":
        d.ellipse([bx0, by0, bx1, by1], fill=(236, 238, 244, 255), outline=ink, width=3)
        d.ellipse([bx0 + 16, by0 + 3, bx1 - 16, by1 - 3], fill=(200, 150, 90, 255))
    elif kind == "shirt":
        d.polygon([(bx0, by0 + 8), (bx0 + 20, by0), (bx1 - 20, by0), (bx1, by0 + 8), (bx1 - 10, by1), (bx0 + 10, by1)],
                  fill=c, outline=ink)
    elif kind == "box":
        d.rectangle([bx0, by0, bx1, by1], fill=(196, 150, 96, 255), outline=ink, width=3)
        d.ellipse([bx0 + 30, by0 + 5, bx0 + 44, by0 + 15], fill=(200, 70, 50, 255))
    elif kind == "bottle":
        d.rounded_rectangle([bx0, by0 + 16, bx1, by1], 6, fill=(90, 170, 120, 230), outline=ink, width=3)
        d.rectangle([bx0 + 7, by0, bx1 - 7, by0 + 18], fill=(90, 170, 120, 230), outline=ink, width=2)
    elif kind == "bag":
        d.rounded_rectangle([bx0, by0 + 10, bx1, by1], 8, fill=(236, 236, 240, 255), outline=ink, width=3)
        d.arc([bx0 + 14, by0, bx1 - 14, by0 + 24], 180, 360, fill=ink, width=3)
    spr = spr.rotate(it["rot"], resample=Image.BICUBIC, expand=True)
    im.alpha_composite(spr, (int(x - spr.width / 2), int(y - spr.height / 2)))


SLIDE_KEYS = {(PILE[i]["x"], PILE[i]["t"]) for i in SLIDE}

# ---------------------------------------------------------------- poses
SIT = dict(AJ.SIT_TYPE, el=(30, -60), hl=(54, -14), er=(26, -56), hr=(50, -10))
SIT_PHONE = OC.SIT_PHONE
SIT_READ = dict(AJ.SIT_TYPE, head=(14, -146), el=(34, -70), hl=(62, -96), er=(30, -66), hr=(58, -92))
SIT_STRETCH = dict(AJ.SIT_TYPE, head=(2, -152), el=(-20, -150), hl=(-30, -200), er=(20, -150), hr=(30, -200))
SIT_GUITAR = dict(AJ.SIT_TYPE, el=(40, -52), hl=(70, -60), er=(24, -70), hr=(56, -80))
STAND = PW.STAND
BEND = {"head": (64, -96), "neck": (44, -70), "el": (60, -30), "hl": (70, 20), "er": (54, -26), "hr": (64, 24),
        "kl": (-4, 56), "fl": (-12, 113), "kr": (12, 56), "fr": (14, 113)}
CARRY = dict(STAND, el=(30, -66), hl=(54, -84), er=(26, -62), hr=(50, -80))
CLIMB = {"head": (40, -140), "neck": (28, -100), "el": (60, -60), "hl": (90, -10), "er": (54, -56), "hr": (84, -6),
         "kl": (50, -20), "fl": (60, 50), "kr": (-20, 50), "fr": (-50, 100)}
TOP_PICK = 1.45                            # the sock and the plate leave the top floor


def walk_pose(t, t0, speed=7.0):
    return AJ.walk((t - t0) * speed, STAND)


def stand_sit(k, to_pose):
    return lerp_pose(STAND, to_pose, k), (lerp(SIT_HIP[0] + 40, SIT_HIP[0], k), lerp(STAND_Y, SIT_HIP[1], k))


def person_now(t):
    """pose, hip, facing, prop, alpha"""
    if t < 0.35:
        return STAND, (300, STAND_Y), 1, None, 1
    if t < 1.15:
        k = smooth(prog(t, 0.35, 1.15))
        return walk_pose(t, 0.35), (lerp(300, 520, k), STAND_Y), 1, None, 1
    if t < 1.75:
        k = smooth(prog(t, 1.15, 1.4)) * (1 - smooth(prog(t, 1.5, 1.75)))
        return lerp_pose(STAND, BEND, k), (520, STAND_Y), 1, None, 1
    if t < 2.5:
        k = smooth(prog(t, 1.75, 2.5))
        return walk_pose(t, 1.75), (lerp(520, HAMPER_X - 60, k), STAND_Y), 1, "carry", 1
    if t < 3.4:
        k = smooth(prog(t, 2.6, 3.4))
        return walk_pose(t, 2.6), (lerp(HAMPER_X - 60, SIT_HIP[0] + 40, k), STAND_Y), -1, None, 1
    if t < T_EXIT0:
        d = min(day(t), 6)
        base = {3: SIT_READ, 4: SIT_GUITAR, 5: SIT_STRETCH, 6: SIT_READ}.get(d, SIT)
        k = smooth(prog(t, 3.4, 3.8))
        pose, hip = stand_sit(k, base)
        if d >= 3:
            prev = {3: SIT, 4: SIT_READ, 5: SIT_GUITAR, 6: SIT_STRETCH}[d]
            pose = lerp_pose(prev, base, smooth(prog(t, DAYS[d - 1], DAYS[d - 1] + 0.4)))
            hip = SIT_HIP
        if base is SIT_GUITAR and t > DAYS[3] + 0.4:
            pose = dict(pose, hr=(56, -80 + 8 * math.sin(t * 14)))
        return pose, hip, 1, ("book" if base is SIT_READ else "guitar" if base is SIT_GUITAR else None), 1
    if t < T_EXIT1 + 0.2:
        k = smooth(prog(t, T_EXIT0, T_EXIT0 + 0.3))
        if k < 1:
            pose, hip = stand_sit(1 - k, SIT_READ)
            return pose, hip, 1, None, 1
        kk = smooth(prog(t, T_EXIT0 + 0.3, T_EXIT1))
        a = 1 - smooth(prog(t, T_EXIT1 - 0.15, T_EXIT1 + 0.15))
        return walk_pose(t, T_EXIT0), (lerp(SIT_HIP[0] + 40, 925, kk), STAND_Y), 1, None, a
    if t < T_IN0:
        return STAND, (925, STAND_Y), -1, None, 0
    if t < T_IN1:
        k = smooth(prog(t, T_IN0 + 0.15, T_IN1))
        a = smooth(prog(t, T_IN0, T_IN0 + 0.3))
        return walk_pose(t, T_IN0), (lerp(925, SIT_HIP[0] + 40, k), STAND_Y), -1, None, a
    k = smooth(prog(t, T_IN1, T_IN1 + 0.35))
    pose, hip = stand_sit(k, SIT)
    return pose, hip, 1, None, 1


def person_tmr(t):
    if t < T_EXIT0:
        return SIT_PHONE, SIT_HIP, 1, "phone", 1
    if t < T_EXIT1 + 0.2:
        k = smooth(prog(t, T_EXIT0, T_EXIT0 + 0.3))
        if k < 1:
            pose, hip = stand_sit(1 - k, SIT_PHONE)
            return pose, hip, 1, None, 1
        kk = smooth(prog(t, T_EXIT0 + 0.3, T_EXIT1))
        x = lerp(SIT_HIP[0] + 40, 925, kk)
        a = 1 - smooth(prog(t, T_EXIT1 - 0.15, T_EXIT1 + 0.15))
        return walk_pose(t, T_EXIT0, 6), (x, pile_top(x, T_EXIT0) - 141), 1, None, a
    if t < T_CLIMB0:
        return STAND, (540, 600), 1, None, 0
    k = smooth(prog(t, T_CLIMB0, T_CLIMB1))
    land_x = 560
    land_y = pile_top(land_x, 20) - 24
    if t < T_CLIMB1:
        if k < 0.45:
            kk = k / 0.45
            return CLIMB, (540, lerp(WIN[3] + 120, WIN[3] - 40, kk)), 1, "clip", 1
        kk = (k - 0.45) / 0.55
        return lerp_pose(CLIMB, AJ.SIT_SLUMP, kk), (lerp(540, land_x, kk), lerp(WIN[3] - 40, land_y, kk)), 1, None, 1
    return AJ.SIT_SLUMP, (land_x, land_y), 1, None, 1


# ---------------------------------------------------------------- the room
def wall_rgb():
    return (30, 32, 42) if STRONG else (9, 9, 11)


def build_room():
    yy = np.mgrid[0:PH, 0:W][0].astype(np.float32)
    wc = np.array(wall_rgb(), np.float32)
    img = np.zeros((PH, W, 3), np.float32) + wc
    img = np.where((yy > FYP)[..., None], img * 0.75 + 6, img)
    if STRONG:
        # a warm ceiling light
        xx = np.mgrid[0:PH, 0:W][1].astype(np.float32)
        r = np.sqrt((xx - 540) ** 2 + (yy - 40) ** 2)
        img += (np.exp(-(r / 520) ** 2) * 34)[..., None] * np.array([1.0, 0.9, 0.7])
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    ink = INK + (255,)
    d.line([(0, FYP), (W, FYP)], fill=(56, 54, 54, 255), width=2)
    x0, x1, mt = BED
    d.rounded_rectangle([x0 - 10, mt - 170, x0 + 22, FYP], 8, fill=(84, 66, 52, 255), outline=ink, width=4)
    d.rounded_rectangle([x0, mt, x1, mt + 44], 12, fill=(222, 222, 228, 255), outline=ink, width=4)
    d.rectangle([x0, mt + 44, x1, FYP - 24], fill=(84, 66, 52, 255), outline=ink, width=4)
    d.rectangle([x1 - 22, FYP - 24, x1 - 10, FYP], fill=(60, 48, 40, 255))
    # window: day sky
    wx0, wy0, wx1, wy1 = WIN
    for i in range(wy1 - wy0):
        d.line([(wx0, wy0 + i), (wx1, wy0 + i)],
               fill=PW.lerp_c((110, 160, 220), (180, 214, 240), i / (wy1 - wy0)) + (255,))
    for i in range(5):
        bx = wx0 + 6 + i * 44
        bh = 40 + (i * 37) % 60
        d.rectangle([bx, wy1 - bh, bx + 38, wy1], fill=(70, 90, 120, 255))
    d.rectangle([wx0, wy0, wx1, wy1], outline=ink, width=8)
    d.line([((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, wy1)], fill=ink, width=6)
    d.rectangle([wx0 - 16, wy1, wx1 + 16, wy1 + 14], fill=(160, 150, 140, 255), outline=ink, width=3)
    return im


def draw_door(d, t, bottom):
    ink = INK + (255,)
    x0, x1, y0 = DOOR
    d.rectangle([x0 - 8, y0 - 8, x1 + 8, FYP], fill=(20, 20, 24, 255), outline=ink, width=4)
    open_k = 0.0
    if bottom:
        if T_EXIT1 - 0.4 <= t < T_SHUT:
            open_k = 1 - smooth(prog(t, T_EXIT1 + 0.15, T_SHUT))
        for tb in T_THUD:
            if tb <= t < tb + 0.2:
                open_k = 0.08 * math.sin(math.pi * (t - tb) / 0.2)
    else:
        if T_EXIT1 - 0.4 <= t < T_EXIT1 + 0.45:
            open_k = 1 - smooth(prog(t, T_EXIT1 + 0.1, T_EXIT1 + 0.45))
        if T_IN0 - 0.1 <= t < T_IN0 + 0.7:
            open_k = 1 - smooth(prog(t, T_IN0 + 0.35, T_IN0 + 0.7))
    w = (x1 - x0) * (1 - 0.8 * open_k)
    d.rectangle([x1 - w, y0, x1, FYP], fill=(130, 96, 66, 255), outline=ink, width=4)
    d.ellipse([x1 - w + 14, y0 + 150, x1 - w + 30, y0 + 166], fill=(230, 200, 90, 255), outline=ink)


def draw_plant(d, t, healthy):
    ink = INK + (255,)
    cx, cy = WIN[1] + 470 - 470 + 600, WIN[3]
    cx = 610
    d.polygon([(cx - 22, cy - 34), (cx + 22, cy - 34), (cx + 16, cy), (cx - 16, cy)], fill=(190, 100, 70, 255),
              outline=ink)
    g = prog(t, 0, 12.0)
    n = 3 + int(5 * g) if healthy else 4
    for i in range(n):
        ang = -90 + (i - (n - 1) / 2) * (22 if healthy else 30)
        L = (34 + 50 * g) if healthy else 40
        droop = 0 if healthy else 60 * prog(t, 2, 11)
        a = math.radians(ang + droop * (1 if ang > -90 else -1))
        ex, ey = cx + L * math.cos(a), cy - 34 + L * math.sin(a)
        col = (90, 190, 100) if healthy else PW.lerp_c((90, 190, 100), (150, 120, 60), prog(t, 2, 10))
        d.line([(cx, cy - 34), (ex, ey)], fill=col + (255,), width=6)
        d.ellipse([ex - 9, ey - 9, ex + 9, ey + 9], fill=col + (255,), outline=ink, width=2)


def draw_hamper(d):
    ink = INK + (255,)
    x = HAMPER_X
    d.polygon([(x - 40, FYP - 90), (x + 40, FYP - 90), (x + 32, FYP), (x - 32, FYP)], fill=(210, 190, 150, 255),
              outline=ink)
    for j in range(3):
        d.line([(x - 34 + j * 3, FYP - 66 + j * 22), (x + 34 - j * 3, FYP - 66 + j * 22)], fill=(170, 150, 110, 255),
               width=3)


def person_sprite(pts, body, far, facing):
    cv = AJ.Canvas(*PW.bbox_of(list(pts.values()), 140))
    AJ.draw_stick(cv, pts, body, far, facing)
    return cv.done()


def draw_prop(d, pts, prop, t):
    ink = INK + (255,)
    if prop == "phone":
        hx, hy = pts["hl"]
        d.rounded_rectangle([hx - 10, hy - 26, hx + 12, hy + 10], 4, fill=(30, 32, 40, 255), outline=(150, 180, 255, 255),
                            width=3)
    elif prop == "book":
        hx, hy = pts["hl"]
        d.polygon([(hx - 6, hy - 30), (hx + 30, hy - 40), (hx + 30, hy + 6), (hx - 6, hy + 14)], fill=(200, 70, 60, 255),
                  outline=ink)
    elif prop == "guitar":
        hx, hy = pts["hl"]
        d.ellipse([hx - 40, hy - 10, hx + 10, hy + 40], fill=(200, 140, 70, 255), outline=ink, width=3)
        d.line([(hx - 10, hy + 10), (hx + 70, hy - 40)], fill=(110, 76, 50, 255), width=8)
    elif prop == "carry":
        hx, hy = pts["hl"]
        d.rounded_rectangle([hx - 22, hy - 10, hx + 22, hy + 4], 6, fill=(220, 80, 70, 255), outline=ink, width=3)


ROOM = None
FRAME0 = None


def panel(t, top):
    im = ROOM.copy()
    d = ImageDraw.Draw(im)
    draw_door(d, t, not top)
    draw_plant(d, t, top)
    if top:
        draw_hamper(d)
    pose, hip, facing, prop, alpha = person_now(t) if top else person_tmr(t)
    # floor stuff behind the person
    for it in PILE:
        draw_item(im, it, t, top)
    if STRONG and not top and t < 0.6:
        # the sock is still in the air at frame 0
        k = prog(t, -0.2, 0.6)
        x, y = lerp(300, 520, k), lerp(FYP - 260, FYP - 18, k * k)
        d.rounded_rectangle([x - 23, y - 8, x + 23, y + 8], 7, fill=(220, 80, 70, 255), outline=INK + (255,), width=3)
    if alpha > 0.01:
        pts = AJ.place(pose, hip, facing, SC)
        body, far = (NOW_C, NOW_FAR) if top else (TMR_C, TMR_FAR)
        spr, off = person_sprite(pts, body, far, facing)
        if alpha < 0.999:
            spr.putalpha(spr.split()[3].point(lambda v: int(v * alpha)))
        if prop == "clip":
            m = Image.new("L", im.size, 0)
            ImageDraw.Draw(m).rectangle([WIN[0], 0, WIN[2], WIN[3]], fill=255)
            layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
            layer.alpha_composite(spr, off)
            layer.putalpha(Image.fromarray(np.minimum(np.asarray(layer.split()[3]), np.asarray(m))))
            im.alpha_composite(layer)
        else:
            if top:
                im.alpha_composite(PW.glow_of(spr, 0.4 * alpha, 12), off)
            im.alpha_composite(spr, off)
        d = ImageDraw.Draw(im)
        draw_prop(d, pts, prop, t)
    else:
        pts = {"head": (925, 200)}
    d = ImageDraw.Draw(im)
    if not top:
        for tb in T_THUD:
            if tb <= t < tb + 0.35:
                k = prog(t, tb, tb + 0.35)
                spaced(d, 760, DOOR[2] - 50 - 20 * k, "THUD", font(BOLD, 40), (240, 240, 244, int(255 * (1 - k))), 2)
    bubs = BUB_NOW if top else BUB_TMR
    OC.speech_at(im, t, bubs, pts)
    return im


def zoom(im, t, focus):
    """Variant B: a close-up that eases out over the first 1.8 s."""
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
    img.alpha_composite(zoom(panel(t, True), t, (430, 420)), (0, TOP_Y0))
    img.alpha_composite(zoom(panel(t, False), t, (430, 420)), (0, BOT_Y0))
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
            spaced(ld, W / 2, TOP_Y0 + 14, "CLEANS IT NOW", fl, (240, 242, 248, int(255 * la)), 10)
        spaced(ld, W / 2, BOT_Y0 + 14, "CLEANS IT TOMORROW", fl, (220, 224, 232, int(255 * la)), 10)
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
    mus, fx = np.zeros((n, 2)), np.zeros((n, 2))
    eighth = BEAT / 2
    figure = [72, 76, 79, 76, 74, 77, 81, 77]
    chords = [[48, 52, 55], [45, 48, 52], [41, 45, 48], [43, 47, 50]]
    shifts = [0, -3, -7, -5]
    t_end = T_THUD[0]
    i, tt = 0, 0.0 if STRONG else 0.2
    while tt < t_end:
        b = int(tt / BAR) % 4
        g = (0.045 if STRONG else 0.03) + 0.05 * prog(tt, 0, t_end)
        mix_in(mus, OC.piano(midi(figure[i % 8] + shifts[b] - 12), 0.4, 0.5), tt, g, 0.25)
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
    for s in DAYS[1:]:
        mix_in(fx, tone(1568, 0.5, (1, 0.3), a=0.003, d=0.3), s, 0.03, 0.0)
    for it in PILE:
        if it["t"] > 0:
            mix_in(fx, noise(0.09, int(it["t"] * 1000) % 9999, lo=150, hi=900) * env(int(0.09 * SR), 0.002, 0.05),
                   it["t"] + 0.26, 0.05, 0.3)
    mix_in(fx, noise(0.7, 33, lo=80, hi=700) * env(int(0.7 * SR), 0.05, 0.4), T_SLIDE0, 0.14, 0.4)
    mix_in(fx, noise(0.15, 34, lo=60, hi=400) * env(int(0.15 * SR), 0.002, 0.08), T_SHUT, 0.12, 0.4)
    for tb in T_THUD:
        mix_in(fx, tone(70, 0.25, (1, 0.5), a=0.002, d=0.12), tb, 0.3, 0.4)
        mix_in(fx, noise(0.12, int(tb * 100), lo=60, hi=500) * env(int(0.12 * SR), 0.002, 0.06), tb, 0.12, 0.4)
    for tk in (T_CLIMB0 + 0.2, T_CLIMB0 + 0.6, T_CLIMB1):
        mix_in(fx, noise(0.1, int(tk * 100), lo=200, hi=1500) * env(int(0.1 * SR), 0.003, 0.05), tk, 0.06, -0.2)
    for k, m in enumerate((48, 55, 60, 64)):
        mix_in(mus, GS.pad(midi(m), 3.0, 0.5, 1.6), 14.6, 0.05, (k - 1.5) * 0.4)
    for j, m in enumerate((76, 72, 67, 72)):
        mix_in(mus, OC.piano(midi(m), 1.3, 0.5), 15.0 + j * 0.5, 0.05, 0.2)
    for b0, b1, s, w in BUB_NOW + BUB_TMR:
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
    out = sys.argv[1] if len(sys.argv) > 1 else f"clean-tomorrow-{VARIANT}.mp4"
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
