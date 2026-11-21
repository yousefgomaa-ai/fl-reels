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
def coat_chair(d, cx, fy, s, col):
    """The chair with the hooded winter coat, gloves and fringed scarf - drawn so that its shadow is a monster.
    col: dict of colours (all white for the silhouette)."""
    # chair
    d.rectangle([cx - 70 * s, fy - 230 * s, cx - 56 * s, fy], fill=col["wood"])
    d.rectangle([cx - 70 * s, fy - 110 * s, cx + 70 * s, fy - 96 * s], fill=col["wood"])
    d.rectangle([cx + 56 * s, fy - 110 * s, cx + 70 * s, fy], fill=col["wood"])
    hx = cx - 63 * s
    # body of the coat: wide shoulders down to the seat
    d.polygon([(hx - 70 * s, fy - 236 * s), (hx + 70 * s, fy - 236 * s), (hx + 52 * s, fy - 96 * s),
               (hx - 52 * s, fy - 96 * s)], fill=col["coat"])
    # the hood = the head, with two pointed tips = horns
    d.ellipse([hx - 40 * s, fy - 312 * s, hx + 40 * s, fy - 230 * s], fill=col["coat"])
    for sx in (-1, 1):
        d.polygon([(hx + sx * 22 * s, fy - 300 * s), (hx + sx * 40 * s, fy - 296 * s), (hx + sx * 58 * s, fy - 356 * s)],
                  fill=col["coat"])
    # the hanger hook on top
    d.arc([hx - 12 * s, fy - 336 * s, hx + 12 * s, fy - 312 * s], 180, 30, fill=col["hook"], width=max(2, int(5 * s)))
    # the scarf hanging from the neck with a jagged fringe = the open jaw
    d.polygon([(hx - 30 * s, fy - 236 * s), (hx + 30 * s, fy - 236 * s), (hx + 24 * s, fy - 178 * s),
               (hx - 24 * s, fy - 178 * s)], fill=col["scarf"])
    for j in range(6):
        x = hx - 24 * s + j * 9.6 * s
        d.polygon([(x, fy - 180 * s), (x + 9.6 * s, fy - 180 * s), (x + 4.8 * s, fy - 156 * s)], fill=col["scarf"])
    # sleeves spread up and out, ending in gloves with long fingers = claws
    for sx in (-1, 1):
        x0, y0 = hx + sx * 60 * s, fy - 230 * s
        ex, ey = hx + sx * 150 * s, fy - 300 * s
        d.polygon([(x0, y0 - 14 * s), (x0, y0 + 22 * s), (ex, ey + 14 * s), (ex, ey - 14 * s)], fill=col["coat"])
        d.ellipse([ex - 16 * s, ey - 18 * s, ex + 16 * s, ey + 18 * s], fill=col["glove"])
        for j in range(4):
            a = math.radians(-90 + sx * (10 + 22 * j))
            fx2, fy2 = ex + math.cos(a) * 52 * s * sx ** 0, ey + math.sin(a) * 52 * s
            fx2 = ex + sx * abs(math.cos(a)) * 52 * s
            d.line([(ex, ey), (fx2, fy2)], fill=col["glove"], width=max(2, int(8 * s)))
            d.polygon([(fx2 - 4 * s, fy2), (fx2 + 4 * s, fy2), (fx2 + sx * 10 * s, fy2 - 16 * s)], fill=col["glove"])


WHITE = {k: (255, 255, 255, 255) for k in ("wood", "coat", "hook", "scarf", "glove")}


def chair_and_coat(scale=1.0):
    w, h = int(420 * scale), int(400 * scale)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    coat_chair(ImageDraw.Draw(im), w / 2 + 63 * scale, h - 2, scale, WHITE)
    return im


def chair_real(d, lightk):
    """The real objects in the room: almost invisible in the dark, plain when the light is on."""
    a = int(lerp(14, 255, lightk))
    col = {"wood": (130, 96, 66, a), "coat": (90, 100, 130, a), "hook": (180, 184, 194, a), "scarf": (200, 70, 60, a),
           "glove": (70, 70, 76, a)}
    coat_chair(d, CHAIR_X, FYP, 1.0, col)


CHAIR_SPR = None


def shadow_layer(t, top):
    """The monster: the chair-and-coat silhouette thrown huge on the wall by the low candle - taller than wide,
    leaning, flickering, and it "breathes"."""
    k_l = lit(t, top)
    if k_l >= 0.999:
        return None
    flick = 1 + 0.03 * math.sin(t * 7.3) + 0.02 * math.sin(t * 13.1)
    grow = 1.0 + 0.03 * math.sin(t * 2.1)
    if not top:
        grow += 0.10 * smooth(prog(t, 3.0, 14.0))
        grow += 0.10 * math.sin(math.pi * prog(t, T_PEEK0, T_PEEK1))
    if top:
        grow += 0.06 * smooth(prog(t, T_GO, T_SWITCH))
        if T_FLINCH0 <= t < T_FLINCH1:
            grow += 0.12 * math.sin(math.pi * prog(t, T_FLINCH0, T_FLINCH1))
    sx, sy = 1.35 * flick * grow, 1.55 * flick * grow
    spr = CHAIR_SPR.resize((int(CHAIR_SPR.width * sx), int(CHAIR_SPR.height * sy)), Image.BILINEAR)
    spr = spr.transform(spr.size, Image.AFFINE, (1, 0.12 + 0.03 * math.sin(t * 1.7), -40, 0, 1, 0), Image.BILINEAR)
    a = spr.split()[3].filter(ImageFilter.GaussianBlur(4))
    lay = Image.new("RGBA", (W, PH), (0, 0, 0, 0))
    sh = Image.new("RGBA", spr.size, (2, 2, 4, 255))
    sh.putalpha(a.point(lambda v: int(v * 0.95 * (1 - k_l))))
    lay.alpha_composite(sh, (int(450 - spr.width / 2), int(FYP - spr.height + 8)))
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
    t = np.arange(n) / SR
    fx = np.zeros((n, 2))
    # after the light: only the warm chord and the soft closing notes of the strings track
    mus = music.score(MUSIC, DUR, t_end=0.01, start=0.0, loud=1.0)
    # 1) a deep, beating drone (two close low notes) that swells until the switch, then sinks to a quiet hum
    swell = np.clip(t / 1.2, 0, 1) * (0.5 + 0.5 * np.clip(t / T_SWITCH, 0, 1))
    after = np.where(t < T_SWITCH, 1.0, 0.25 * np.clip((15.0 - t) / 1.0, 0, 1))
    drone = (np.sin(2 * np.pi * 41.2 * t) + 0.8 * np.sin(2 * np.pi * 43.6 * t) + 0.35 * np.sin(2 * np.pi * 61.7 * t))
    drone = drone * 0.05 * swell * after
    fx[:, 0] += drone
    fx[:, 1] += drone
    # 2) high dissonant strings (a minor second) creeping in, eerie
    for f0, pan in ((659.3, -0.5), (698.5, 0.5)):
        x = music.strings(f0, T_SWITCH - 1.5, 3.0, 0.05)[: int((T_SWITCH - 1.5) * SR)]
        mix_in(fx, x * (1 + 0.3 * np.sin(np.arange(len(x)) / SR * 2 * np.pi * 5.5)), 1.5, 0.018, pan)
    # 3) a slow growl / breathing of the "monster"
    br = noise(DUR, 77, lo=40, hi=260)
    breath = (0.5 + 0.5 * np.sin(2 * np.pi * 0.45 * t)) ** 2
    g = br * breath * 0.05 * np.clip((t - 0.5) / 1.5, 0, 1) * np.where(t < T_SWITCH, 1.0, 0.35)
    fx[:, 0] += g
    fx[:, 1] += np.roll(g, 900)
    # 4) a heartbeat that gets faster as he gets closer
    tb, gap = 0.3, 0.95
    while tb < T_SWITCH - 0.4:
        mix_in(fx, tone(52, 0.18, (1, 0.5), a=0.004, d=0.08), tb, 0.2)
        mix_in(fx, tone(47, 0.16, (1, 0.5), a=0.004, d=0.07), tb + 0.17, 0.15)
        tb += gap
        gap = max(0.45, gap * 0.94)
    # 5) stings: the shadow lurches (above) and moves when he peeks (below)
    for t0 in (T_FLINCH0, T_PEEK0 + 0.2):
        mix_in(fx, tone(1800, 0.6, (1, 0.6, 0.3), a=0.01, d=0.35, sweep=2600), t0, 0.04, 0.3)
        mix_in(fx, tone(38, 0.9, (1, 0.6), a=0.005, d=0.5), t0, 0.3)
        mix_in(fx, noise(0.9, int(t0 * 10), lo=40, hi=300) * env(int(0.9 * SR), 0.05, 0.5), t0, 0.25)
    # running feet and the dive under the blanket
    for j in range(5):
        mix_in(fx, noise(0.06, 70 + j, lo=100, hi=900) * env(int(0.06 * SR), 0.002, 0.03), T_RUN0 + j * 0.14, 0.08, -0.3)
    mix_in(fx, noise(0.35, 80, lo=200, hi=2500) * env(int(0.35 * SR), 0.01, 0.15), T_DIVE, 0.08, -0.3)
    # 6) a breath of silence, then the click - and the light: a bright, warm chord
    i0, i1 = int((T_SWITCH - 0.35) * SR), int(T_SWITCH * SR)
    fx[i0:i1] *= np.linspace(1, 0.05, i1 - i0)[:, None]
    mix_in(fx, noise(0.03, 90, lo=1500, hi=6000) * env(int(0.03 * SR), 0.001, 0.01), T_SWITCH - 0.02, 0.18, 0.2)
    for k, m in enumerate((57, 64, 69, 72, 76)):
        mix_in(fx, music.strings(midi(m), 2.2, 0.08, 1.6), T_SWITCH + 0.02, 0.03, (k - 2) * 0.35)
    mix_in(fx, music.music_box(midi(88), 1.6), T_SWITCH + 0.1, 0.05, 0.2)
    mix_in(fx, music.music_box(midi(84), 1.6), T_SWITCH + 0.35, 0.04, 0.2)
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
