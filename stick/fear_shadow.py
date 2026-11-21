#!/usr/bin/env python3
"""Symbolic #2 - FEAR IS JUST A SHADOW. Split screen, 18 s, loops on itself. Minimal symbolic style. Music: strings.

A dark room lit by one candle on the floor, and on the wall a huge monster shadow - from the first frame. The same
man in the doorway, frozen. Above (LOOKS): step by step towards the wall, the shadow lurches and he flinches back,
then the last steps, and he flips the switch: the room lights up - the "monster" is a chair with a coat on it.
He sits down on it. Below (RUNS): he runs and dives under the blanket; the shadow sways bigger all night; he peeks,
it moves, he hides again.  "FEAR IS JUST A SHADOW. / TURN ON THE LIGHT."  FOLLOW FOR MORE.

    python3 stick/fear_shadow.py stick/fear-shadow.mp4
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

MUSIC = "strings_am"
W, H, FPS = 1080, 1920, 30
SR = 44100
DUR = 18.0
NF = int(round(DUR * FPS))
XFADE = 0.45
SC = AJ.SC
INK = AJ.INK
FIG, FIG_FAR = AJ.DOER, AJ.DOER_FAR
BOLD = FM.BOLD
PH, TOP_Y0, BOT_Y0, STRIP_Y, FYP = OC.PH, OC.TOP_Y0, OC.BOT_Y0, OC.STRIP_Y, OC.FYP
STAND_Y = FYP - 141

CHAIR_X = 780
CANDLE_X = 930
SWITCH = (600, FYP - 260)
DOOR_X = 110
BED = (30, 300)

# ---------------------------------------------------------------- timeline
T_FREEZE = 0.0
T_GO = 2.6                  # above: the first step
T_FLINCH0, T_FLINCH1 = 5.6, 6.6
T_SWITCH = 9.4
T_SIT0, T_SIT1 = 10.6, 12.0
T_RUN0, T_RUN1 = 2.4, 3.1   # below
T_DIVE = 3.3
T_PEEK0, T_PEEK1 = 10.6, 11.6
T_L1, T_L2 = 15.0, 16.1
CPS = 18.0
LINE1, LINE2 = "FEAR IS JUST A SHADOW.", "TURN ON THE LIGHT."
T_FOLLOW = 16.95


def lit(t, top):
    return smooth(prog(t, T_SWITCH, T_SWITCH + 0.25)) if top else 0.0


# ---------------------------------------------------------------- poses
STAND = PW.STAND
SCARED = dict(STAND, head=(-8, -144), neck=(-6, -104), el=(10, -84), hl=(30, -118), er=(16, -80), hr=(36, -112),
              kl=(-14, 54), fl=(-20, 112), kr=(10, 56), fr=(16, 112))
CREEP = dict(SCARED, head=(6, -146), el=(30, -90), hl=(60, -110))
REACH = dict(STAND, head=(10, -150), el=(40, -110), hl=(76, -140), er=(14, -60), hr=(18, -14))
RELIEF = dict(STAND, head=(0, -152), el=(-16, -60), hl=(-20, -14), er=(16, -60), hr=(20, -14))
SIT = dict(AJ.SIT_TYPE, el=(30, -60), hl=(54, -14), er=(26, -56), hr=(50, -10))


def walk(t, t0, speed=7.0, base=STAND):
    return AJ.walk((t - t0) * speed, base)


def top_person(t):
    """pose, hip, facing"""
    x0, x_mid, x_sw = DOOR_X + 40, 330, SWITCH[0] - 90
    jit = 1.6 * math.sin(t * 45) * (1 - smooth(prog(t, T_SWITCH, T_SWITCH + 0.5)))
    if t < T_GO:
        return SCARED, (x0 + jit, STAND_Y), 1
    if t < T_FLINCH0:
        k = smooth(prog(t, T_GO, T_FLINCH0))
        return walk(t, T_GO, 3.5, CREEP), (lerp(x0, x_mid, k) + jit, STAND_Y), 1
    if t < T_FLINCH1:
        k = math.sin(math.pi * prog(t, T_FLINCH0, T_FLINCH1))
        return SCARED, (x_mid - 60 * k + jit, STAND_Y), 1
    if t < T_SWITCH - 0.4:
        k = smooth(prog(t, T_FLINCH1, T_SWITCH - 0.4))
        return walk(t, T_FLINCH1, 3.0, CREEP), (lerp(x_mid, x_sw, k) + jit, STAND_Y), 1
    if t < T_SWITCH + 0.6:
        k = smooth(prog(t, T_SWITCH - 0.4, T_SWITCH))
        return lerp_pose(CREEP, REACH, k), (x_sw, STAND_Y), 1
    if t < T_SIT0:
        k = smooth(prog(t, T_SWITCH + 0.6, T_SWITCH + 1.0))
        return lerp_pose(REACH, RELIEF, k), (x_sw, STAND_Y), 1
    if t < T_SIT1 - 0.4:
        k = smooth(prog(t, T_SIT0, T_SIT1 - 0.4))
        return walk(t, T_SIT0, 6), (lerp(x_sw, CHAIR_X + 10, k), STAND_Y), 1
    k = smooth(prog(t, T_SIT1 - 0.4, T_SIT1))
    # sits on the chair, facing left, relaxed
    return lerp_pose(STAND, SIT, k), (CHAIR_X + 10 - 20 * k, lerp(STAND_Y, FYP - 140, k)), -1


def bottom_person(t):
    """pose, hip, facing, hidden"""
    x0 = DOOR_X + 40
    jit = 1.6 * math.sin(t * 45)
    if t < T_RUN0:
        return SCARED, (x0 + jit, STAND_Y), 1, False
    if t < T_RUN1:
        k = smooth(prog(t, T_RUN0, T_RUN1))
        return walk(t, T_RUN0, 14), (lerp(x0, 230, k), STAND_Y), -1, False
    if t < T_DIVE:
        return walk(t, T_RUN0, 14), (230, STAND_Y), -1, False
    return None, None, None, True


# ---------------------------------------------------------------- drawing
def chair_and_coat(scale=1.0):
    """The chair with the coat over its back, as one sprite (white-ish on transparent). Origin = floor centre."""
    s = scale
    w, h = int(260 * s), int(360 * s)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, fy = w / 2, h - 2
    col = (255, 255, 255, 255)
    # chair: back on the left, seat, legs
    d.rectangle([cx - 70 * s, fy - 230 * s, cx - 56 * s, fy], fill=col)
    d.rectangle([cx - 70 * s, fy - 110 * s, cx + 70 * s, fy - 96 * s], fill=col)
    d.rectangle([cx + 56 * s, fy - 110 * s, cx + 70 * s, fy], fill=col)
    # the coat hanging over the back: a hook, wide shoulders, two long sleeves, the body
    d.arc([cx - 78 * s, fy - 300 * s, cx - 48 * s, fy - 262 * s], 180, 20, fill=col, width=max(2, int(6 * s)))
    d.line([(cx - 63 * s, fy - 266 * s), (cx - 63 * s, fy - 246 * s)], fill=col, width=max(2, int(5 * s)))
    d.polygon([(cx - 63 * s, fy - 248 * s), (cx - 130 * s, fy - 220 * s), (cx + 4 * s, fy - 220 * s)], fill=col)
    d.polygon([(cx - 120 * s, fy - 222 * s), (cx - 6 * s, fy - 222 * s), (cx - 14 * s, fy - 80 * s),
               (cx - 112 * s, fy - 80 * s)], fill=col)
    for sx in (-1, 1):
        x = cx - 63 * s + sx * 60 * s
        ex, ey = x + sx * 70 * s, fy - 120 * s
        d.polygon([(x - 12 * s, fy - 224 * s), (x + 12 * s, fy - 224 * s), (ex + 12 * s, ey), (ex - 12 * s, ey)],
                  fill=col)
        # cuffs like claws
        for j in range(4):
            cxx = ex - 12 * s + j * 8 * s
            d.polygon([(cxx - 3 * s, ey - 2 * s), (cxx + 3 * s, ey - 2 * s), (cxx + sx * 4 * s, ey + 22 * s)], fill=col)
    return im


def chair_real(d, lightk):
    """The chair as an object in the room (seen when the light is on, a dim shape in the dark)."""
    cx, fy = CHAIR_X, FYP
    a = int(lerp(18, 255, lightk))
    ink = INK + (a,)
    wood = (130, 96, 66, a)
    coat = (90, 100, 130, a)
    d.rectangle([cx - 70, fy - 230, cx - 56, fy], fill=wood, outline=ink)
    d.rectangle([cx - 70, fy - 110, cx + 70, fy - 96], fill=wood, outline=ink)
    d.rectangle([cx + 56, fy - 110, cx + 70, fy], fill=wood, outline=ink)
    d.arc([cx - 78, fy - 300, cx - 48, fy - 262], 180, 20, fill=(180, 184, 194, a), width=6)
    d.polygon([(cx - 63, fy - 248), (cx - 130, fy - 220), (cx + 4, fy - 220)], fill=coat, outline=ink)
    d.polygon([(cx - 120, fy - 222), (cx - 6, fy - 222), (cx - 14, fy - 80), (cx - 112, fy - 80)], fill=coat,
              outline=ink)
    for sx in (-1, 1):
        x = cx - 63 + sx * 60
        ex, ey = x + sx * 70, fy - 120
        d.polygon([(x - 12, fy - 224), (x + 12, fy - 224), (ex + 12, ey), (ex - 12, ey)], fill=coat, outline=ink)


CHAIR_SPR = None


def shadow_layer(t, top):
    """The monster: the chair-and-coat silhouette, thrown huge on the wall by the candle."""
    k_l = lit(t, top)
    if k_l >= 0.999:
        return None
    flick = 1 + 0.025 * math.sin(t * 7.3) + 0.015 * math.sin(t * 13.1)
    grow = 1.0
    if not top:
        grow += 0.08 * smooth(prog(t, 3.0, 14.0))
        grow += 0.06 * math.sin(math.pi * prog(t, T_PEEK0, T_PEEK1))
    if top and T_FLINCH0 <= t < T_FLINCH1:
        grow += 0.07 * math.sin(math.pi * prog(t, T_FLINCH0, T_FLINCH1))
    sc = 1.85 * flick * grow
    spr = CHAIR_SPR.resize((int(CHAIR_SPR.width * sc), int(CHAIR_SPR.height * sc)), Image.BILINEAR)
    a = spr.split()[3].filter(ImageFilter.GaussianBlur(5))
    lay = Image.new("RGBA", (W, PH), (0, 0, 0, 0))
    sh = Image.new("RGBA", spr.size, (2, 2, 4, 255))
    sh.putalpha(a.point(lambda v: int(v * 0.92 * (1 - k_l))))
    sway = 10 * math.sin(t * 1.7)
    lay.alpha_composite(sh, (int(470 - spr.width / 2 + sway), int(FYP - spr.height + 6)))
    return lay


def build_room():
    yy, xx = np.mgrid[0:PH, 0:W].astype(np.float32)
    img = np.zeros((PH, W, 3), np.float32) + 6
    img = np.where((yy > FYP)[..., None], img * 0.8 + 4, img)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def room(t, top):
    """Background: dark room with the warm candle wash; with the light on, a soft grey room."""
    k_l = lit(t, top)
    yy, xx = np.mgrid[0:PH:2, 0:W:2].astype(np.float32)
    fl = 1 + 0.06 * math.sin(t * 9) + 0.04 * math.sin(t * 17)
    r = np.sqrt((xx - CANDLE_X) ** 2 + ((yy - (FYP - 30)) * 0.8) ** 2)
    warm = np.exp(-(r / (620 * fl)) ** 2)[..., None] * np.array([120, 88, 50]) * (1 - k_l)
    base = 6 + k_l * 60
    img = np.zeros(yy.shape + (3,), np.float32) + base + warm
    img = np.where((yy > FYP)[..., None], img * 0.75 + 4, img)
    if k_l > 0:
        rr = np.sqrt((xx - 300) ** 2 + (yy + 40) ** 2)
        img += (np.exp(-(rr / 700) ** 2) * 50 * k_l)[..., None] * np.array([1.0, 0.95, 0.85])
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").resize((W, PH), Image.BILINEAR).convert("RGBA")
    d = ImageDraw.Draw(im)
    d.line([(0, FYP), (W, FYP)], fill=(40, 38, 38, 255), width=2)
    return im


def draw_fixed(d, t, top):
    ink = INK + (255,)
    k_l = lit(t, top)
    # doorway (left)
    d.rectangle([DOOR_X - 70, FYP - 300, DOOR_X + 30, FYP], fill=(14, 14, 16, 255), outline=(40, 40, 46, 255), width=4)
    # ceiling lamp
    a = int(lerp(60, 255, k_l))
    d.line([(300, 0), (300, 60)], fill=(60, 60, 66, 255), width=3)
    d.chord([260, 50, 340, 100], 180, 360, fill=(int(lerp(40, 255, k_l)), int(lerp(40, 236, k_l)), int(lerp(44, 180, k_l)), 255))
    # light switch
    sx, sy = SWITCH
    d.rounded_rectangle([sx - 16, sy - 26, sx + 16, sy + 26], 4, fill=(120, 120, 126, 255) if top else (60, 60, 66, 255),
                        outline=ink, width=2)
    d.rectangle([sx - 5, sy - (14 if k_l < 0.5 else -2), sx + 5, sy + (2 if k_l < 0.5 else 14)], fill=(220, 220, 226, 255))
    if not top:
        # the bed in the dark corner
        x0, x1 = BED
        d.rectangle([x0, FYP - 90, x1, FYP - 30], fill=(40, 34, 30, 255), outline=(60, 54, 50, 255), width=3)
        d.rectangle([x0, FYP - 30, x0 + 12, FYP], fill=(40, 34, 30, 255))
        d.rectangle([x1 - 12, FYP - 30, x1, FYP], fill=(40, 34, 30, 255))
    # candle
    if k_l < 0.99:
        cx = CANDLE_X
        d.rectangle([cx - 8, FYP - 44, cx + 8, FYP], fill=(236, 230, 210, 255))
        fl = 1 + 0.15 * math.sin(t * 19)
        d.ellipse([cx - 6, FYP - 70 * fl, cx + 6, FYP - 44], fill=(255, 200, 90, int(255 * (1 - k_l))))


def blanket(d, t):
    """Him under the blanket on the bed: a trembling lump, eyes when he peeks."""
    x0, x1 = BED
    tr = 2.5 * math.sin(t * 38)
    d.chord([x0 + 30 + tr, FYP - 170, x1 - 20 + tr, FYP - 40], 180, 360, fill=(80, 90, 120, 255),
            outline=(20, 20, 24, 255))
    d.rectangle([x0 + 30 + tr, FYP - 106, x1 - 20 + tr, FYP - 86], fill=(80, 90, 120, 255))
    peek = math.sin(math.pi * clamp(prog(t, T_PEEK0, T_PEEK0 + 0.3) - prog(t, T_PEEK1 - 0.3, T_PEEK1)))
    if peek > 0.05 or (T_PEEK0 <= t < T_PEEK1):
        k = smooth(prog(t, T_PEEK0, T_PEEK0 + 0.25)) * (1 - smooth(prog(t, T_PEEK1 - 0.25, T_PEEK1)))
        ex, ey = x1 - 70, FYP - 150 + 18 * (1 - k)
        for dx in (0, 28):
            d.ellipse([ex + dx - 10, ey - 10, ex + dx + 10, ey + 10], fill=(255, 255, 255, int(255 * k)))
            d.ellipse([ex + dx - 2, ey - 3, ex + dx + 4, ey + 3], fill=(10, 10, 12, int(255 * k)))


def sprite(pts, body, far, facing):
    cv = AJ.Canvas(*PW.bbox_of(list(pts.values()), 140))
    AJ.draw_stick(cv, pts, body, far, facing)
    return cv.done()


FRAME0 = None


def panel(t, top):
    im = room(t, top)
    sh = shadow_layer(t, top)
    if sh is not None:
        im.alpha_composite(sh)
    d = ImageDraw.Draw(im)
    draw_fixed(d, t, top)
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    chair_real(ImageDraw.Draw(lay), lit(t, top))
    im.alpha_composite(lay)
    d = ImageDraw.Draw(im)
    if top:
        pose, hip, facing = top_person(t)
        pts = AJ.place(pose, hip, facing, SC)
        spr, off = sprite(pts, FIG, FIG_FAR, facing)
        k_l = lit(t, top)
        if k_l > 0:
            im.alpha_composite(PW.glow_of(spr, 0.4 * k_l, 12), off)
        im.alpha_composite(spr, off)
        d = ImageDraw.Draw(im)
        if t < T_SWITCH:
            # the "!" of fright at the start
            if t < 1.4:
                k = out_back(prog(t, 0.0, 0.3))
                hx, hy = pts["head"]
                spaced(d, hx + 6, hy - 110 - 10 * k, "!", font(BOLD, int(60 * max(0.2, k))), (255, 255, 255, 255), 0)
    else:
        pose, hip, facing, hidden = bottom_person(t)
        if not hidden:
            pts = AJ.place(pose, hip, facing, SC)
            spr, off = sprite(pts, FIG, FIG_FAR, facing)
            im.alpha_composite(spr, off)
            d = ImageDraw.Draw(im)
            if t < 1.4:
                k = out_back(prog(t, 0.0, 0.3))
                hx, hy = pts["head"]
                spaced(d, hx + 6, hy - 110 - 10 * k, "!", font(BOLD, int(60 * max(0.2, k))), (255, 255, 255, 255), 0)
        else:
            blanket(d, t)
    return im


def frame(t):
    img = Image.new("RGBA", (W, H), (2, 2, 3, 255))
    img.alpha_composite(panel(t, True), (0, TOP_Y0))
    img.alpha_composite(panel(t, False), (0, BOT_Y0))
    d = ImageDraw.Draw(img)
    fl = font(BOLD, 46)
    if t < T_L1:
        spaced(d, W / 2, TOP_Y0 + 24, "LOOKS", fl, (250, 250, 252, 255), 14)
    spaced(d, W / 2, BOT_Y0 + 24, "RUNS", fl, (230, 232, 238, 255), 14)
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
    global CHAIR_SPR
    CHAIR_SPR = chair_and_coat(1.0)


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
    mus = music.score(MUSIC, DUR, t_end=T_SWITCH, start=0.0, loud=1.15)
    fx = np.zeros((n, 2))
    # a low drone of dread that swells until the switch, then cuts
    t = np.arange(n) / SR
    drone = (np.sin(2 * np.pi * 55 * t) + 0.5 * np.sin(2 * np.pi * 58.3 * t)) * 0.02
    drone *= np.clip(t / 1.0, 0, 1) * (0.6 + 0.4 * np.clip(t / T_SWITCH, 0, 1)) * (t < T_SWITCH)
    fx[:, 0] += drone
    fx[:, 1] += drone
    # heartbeat while he creeps (above) and hides (below)
    for tb in np.arange(0.4, T_SWITCH, 0.85):
        mix_in(fx, tone(55, 0.16, (1, 0.4), a=0.004, d=0.07), tb, 0.12)
        mix_in(fx, tone(50, 0.14, (1, 0.4), a=0.004, d=0.06), tb + 0.18, 0.09)
    # the shadow lurch: a low whoosh
    for t0 in (T_FLINCH0, T_PEEK0 + 0.2):
        mix_in(fx, noise(0.7, int(t0 * 10), lo=60, hi=500) * env(int(0.7 * SR), 0.15, 0.3), t0, 0.12, 0.2)
    # running feet and the dive under the blanket
    for j in range(5):
        mix_in(fx, noise(0.06, 70 + j, lo=100, hi=900) * env(int(0.06 * SR), 0.002, 0.03), T_RUN0 + j * 0.14, 0.06, -0.3)
    mix_in(fx, noise(0.35, 80, lo=200, hi=2500) * env(int(0.35 * SR), 0.01, 0.15), T_DIVE, 0.07, -0.3)
    # the switch: a click, and light (a soft bright chord)
    mix_in(fx, noise(0.03, 90, lo=1500, hi=6000) * env(int(0.03 * SR), 0.001, 0.01), T_SWITCH - 0.02, 0.14, 0.2)
    for k, m in enumerate((69, 72, 76, 81)):
        mix_in(fx, music.strings(midi(m), 1.8, 0.05, 1.4), T_SWITCH + 0.02, 0.035, (k - 1.5) * 0.4)
    mix_in(fx, music.music_box(midi(88), 1.6), T_SWITCH + 0.1, 0.04, 0.2)
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
    out = sys.argv[1] if len(sys.argv) > 1 else "fear-shadow.mp4"
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
