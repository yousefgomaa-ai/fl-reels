#!/usr/bin/env python3
"""IDEAS.md #10 - IT WAS RIGHT THERE. Split screen, 18 s, loops on itself. Opening: A (current style). Music: music box.

08:00, the same fridge, the butter on the middle shelf, right in front. Both: "BUTTER..."
Above: he sees it - FOUND IN 0:02 - toast, "PERFECT." Below: "WHERE IS IT?" - milk, eggs and jars land on the floor,
he crouches to the drawers, "WE HAVE NO BUTTER.", grabs his keys and goes to the store. 08:44 he is back with a new
butter, opens the fridge to put it in - and there it is, right in front. He holds two butters. "IT WASN'T THERE BEFORE."
"IT WAS RIGHT THERE. / IT'S ALWAYS RIGHT THERE."  FOLLOW FOR MORE.

    python3 stick/fridge.py stick/fridge.mp4
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
MUSIC = "music_box_d"

W, H, FPS = 1080, 1920, 30
SR = 44100
DUR = 18.0
NF = int(round(DUR * FPS))
XFADE = 0.45
SC = AJ.SC
INK = AJ.INK
GOOD_C, GOOD_FAR = AJ.DOER, AJ.DOER_FAR
BAD_C, BAD_FAR = AJ.OT, AJ.OT_FAR
RED = (255, 64, 56)
BOLD = FM.BOLD
PH, TOP_Y0, BOT_Y0, STRIP_Y, FYP = OC.PH, OC.TOP_Y0, OC.BOT_Y0, OC.STRIP_Y, OC.FYP
STAND_Y = FYP - 141

FR = (580, 820, FYP - 430)                 # fridge x0, x1, top
SHELVES = [FYP - 340, FYP - 250, FYP - 160]
BUTTER = (650, SHELVES[1] - 16)            # center, on the middle shelf, front
AT_FRIDGE = (470, STAND_Y)
COUNTER = (170, 400, FYP - 200)            # x0, x1, top
DOOR = (20, 140, FYP - 300)

# ---------------------------------------------------------------- timeline
T_OPEN = 0.5
T_SPOT = 1.2                               # top sees it
T_TAKE, T_CLOSE_G = 1.6, 2.1
T_SRCH0, T_SRCH1 = 1.4, 6.4
T_GIVEUP = 5.6
T_LEAVE0, T_LEAVE1 = 6.6, 7.6
T_BACK0, T_BACK1 = 9.8, 10.7
T_REOPEN = 11.0
T_RING = 11.6
T_CLOCK0, T_CLOCK1 = 1.0, 10.0
T_L1, T_L2 = 15.0, 16.1
CPS = 18.0
LINE1, LINE2 = "IT WAS RIGHT THERE.", "IT'S ALWAYS RIGHT THERE."
T_FOLLOW = 16.95

B0 = -0.3 if STRONG else 0.3
BUB_GOOD = [(B0, 1.2, "BUTTER...", "me"), (8.6, 9.8, "PERFECT.", "me")]
BUB_BAD = [(B0, 1.2, "BUTTER...", "me"), (2.2, 3.2, "WHERE IS IT?", "me"), (4.0, 5.0, "BEHIND THE EGGS?", "me"),
           (5.4, 6.5, "WE HAVE NO BUTTER.", "me"), (12.1, 12.8, "...", "me"),
           (13.3, 14.9, "IT WASN'T THERE BEFORE.", "me")]

# things he throws out of the fridge, below: (kind, color, time out, floor x)
THROWN = [("milk", (236, 236, 242), 2.0, 300), ("jar", (200, 70, 60), 2.6, 350), ("eggs", (240, 220, 180), 3.2, 250),
          ("jar", (90, 160, 90), 3.8, 400), ("apple", (220, 60, 60), 4.4, 330), ("milk", (240, 200, 90), 5.0, 210)]


def clock_minutes(t):
    return int(8 * 60 + 44 * prog(t, T_CLOCK0, T_CLOCK1))


def fridge_open(t, good):
    if good:
        return smooth(prog(t, T_OPEN, T_OPEN + 0.3)) * (1 - smooth(prog(t, T_CLOSE_G, T_CLOSE_G + 0.3)))
    k = smooth(prog(t, T_OPEN, T_OPEN + 0.3)) * (1 - smooth(prog(t, T_LEAVE0 - 0.3, T_LEAVE0)))
    return max(k, smooth(prog(t, T_REOPEN, T_REOPEN + 0.3)))


def search_label(t, good):
    if good:
        return ("FOUND IN", "0:02", (120, 230, 150)) if t >= T_TAKE else ("SEARCHING", f"0:0{int(prog(t, T_OPEN, T_TAKE) * 2)}",
                                                                          (240, 240, 244))
    if t < T_GIVEUP:
        s = int(200 * prog(t, T_OPEN, T_GIVEUP))
        return "SEARCHING", f"{s // 60}:{s % 60:02d}", (240, 200, 120)
    if t < T_RING:
        return "BUTTER", "NONE", (240, 120, 120)
    return "FOUND IN", "44 MIN", (240, 120, 120)


# ---------------------------------------------------------------- poses
STAND = PW.STAND
REACH = dict(STAND, head=(14, -148), el=(44, -96), hl=(100, -100), er=(36, -86), hr=(90, -90))
LEAN = dict(STAND, head=(46, -136), neck=(30, -98), el=(60, -80), hl=(110, -90), er=(54, -72), hr=(104, -80))
CROUCH = {"head": (48, -86), "neck": (34, -52), "el": (60, -36), "hl": (104, -40), "er": (54, -30), "hr": (98, -34),
          "kl": (44, 22), "fl": (20, 76), "kr": (34, 28), "fr": (8, 78)}
THROW = dict(STAND, head=(10, -148), el=(-30, -100), hl=(-70, -140), er=(30, -80), hr=(60, -90))
SPREAD = dict(STAND, el=(30, -76), hl=(74, -70), er=(26, -70), hr=(66, -62))
EAT = dict(STAND, el=(30, -96), hl=(20, -132), er=(26, -70), hr=(66, -62))
HOLD2 = dict(STAND, el=(-20, -80), hl=(-40, -100), er=(36, -84), hr=(64, -100))
CARRY = dict(STAND, el=(-14, -58), hl=(-20, -16), er=(10, -58), hr=(14, -10))


def walk(t, t0):
    return AJ.walk((t - t0) * 7, STAND)


def good_person(t):
    """pose, hip, facing, prop"""
    if t < T_SPOT:
        return lerp_pose(STAND, REACH, smooth(prog(t, T_OPEN, T_OPEN + 0.3)) * 0.4), AT_FRIDGE, 1, None
    if t < T_CLOSE_G:
        return REACH, AT_FRIDGE, 1, ("butter" if t >= T_TAKE else None)
    if t < 3.0:
        k = smooth(prog(t, T_CLOSE_G + 0.1, 3.0))
        return walk(t, T_CLOSE_G), (lerp(AT_FRIDGE[0], 330, k), STAND_Y), -1, "butter"
    if t < 7.6:
        k = 0.5 - 0.5 * math.cos((t - 3.0) * 7)
        return lerp_pose(SPREAD, dict(SPREAD, hl=(84, -66)), k), (330, STAND_Y), -1, "knife"
    ph = (t - 7.6) % 1.6
    k = math.sin(math.pi * clamp(ph / 0.8)) if ph < 0.8 else 0
    return lerp_pose(SPREAD, EAT, k), (330, STAND_Y), -1, "toast"


def bad_person(t):
    """pose, hip, facing, prop, alpha"""
    if t < T_SRCH0:
        return lerp_pose(STAND, REACH, smooth(prog(t, T_OPEN, T_OPEN + 0.3)) * 0.4), AT_FRIDGE, 1, None, 1
    if t < T_SRCH1:
        for kind, col, tt, fx in THROWN:
            if tt - 0.25 <= t < tt + 0.15:
                k = math.sin(math.pi * prog(t, tt - 0.25, tt + 0.15))
                base = CROUCH if 3.9 <= t < 5.0 else LEAN
                hip = (AT_FRIDGE[0], FYP - 98) if base is CROUCH else AT_FRIDGE
                return lerp_pose(base, THROW, k * 0.8), hip, 1, None, 1
        if 3.9 <= t < 5.0:
            k = smooth(prog(t, 3.9, 4.15)) * (1 - smooth(prog(t, 4.75, 5.0)))
            return lerp_pose(LEAN, CROUCH, k), (AT_FRIDGE[0], lerp(STAND_Y, FYP - 98, k)), 1, None, 1
        sway = 0.5 + 0.5 * math.sin(t * 5)
        return lerp_pose(REACH, LEAN, sway), AT_FRIDGE, 1, None, 1
    if t < T_LEAVE0:
        return STAND, AT_FRIDGE, -1, None, 1
    if t < T_LEAVE1 + 0.2:
        k = smooth(prog(t, T_LEAVE0, T_LEAVE1))
        a = 1 - smooth(prog(t, T_LEAVE1 - 0.15, T_LEAVE1 + 0.15))
        return walk(t, T_LEAVE0), (lerp(AT_FRIDGE[0], 80, k), STAND_Y), -1, None, a
    if t < T_BACK0:
        return STAND, (80, STAND_Y), 1, None, 0
    if t < T_BACK1:
        k = smooth(prog(t, T_BACK0 + 0.1, T_BACK1))
        a = smooth(prog(t, T_BACK0, T_BACK0 + 0.3))
        return walk(t, T_BACK0), (lerp(80, AT_FRIDGE[0], k), STAND_Y), 1, "bag", a
    if t < T_RING:
        return lerp_pose(CARRY, REACH, 0.4 * smooth(prog(t, T_REOPEN, T_REOPEN + 0.3))), AT_FRIDGE, 1, "bag", 1
    if t < T_RING + 0.6:
        return REACH, AT_FRIDGE, 1, "newbutter", 1
    return HOLD2, AT_FRIDGE, 1, "two", 1


# ---------------------------------------------------------------- drawing
def build_room():
    yy, xx = np.mgrid[0:PH, 0:W].astype(np.float32)
    base = np.array((31, 30, 40) if STRONG else (9, 9, 11), np.float32)
    img = np.zeros((PH, W, 3), np.float32) + base
    tile = ((xx // 50 + yy // 50) % 2 == 0) & (yy > COUNTER[2] - 120) & (yy < COUNTER[2])
    img = np.where(tile[..., None], img + 5, img)
    img = np.where((yy > FYP)[..., None], img * 0.75 + 6, img)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    ink = INK + (255,)
    d.line([(0, FYP), (W, FYP)], fill=(56, 54, 54, 255), width=2)
    # counter
    x0, x1, cy = COUNTER
    d.rectangle([x0, cy, x1, cy + 20], fill=(200, 196, 190, 255), outline=ink, width=4)
    d.rectangle([x0 + 10, cy + 20, x1 - 10, FYP], fill=(120, 96, 76, 255), outline=ink, width=4)
    for j in range(2):
        d.rectangle([x0 + 24 + j * 110, cy + 44, x0 + 110 + j * 110, FYP - 24], outline=ink, width=3)
    # shelf with mugs
    d.rectangle([x0, 150, x1, 166], fill=(120, 96, 76, 255), outline=ink, width=3)
    for j, c in enumerate(((220, 90, 80), (90, 160, 220), (240, 200, 90))):
        mx = x0 + 30 + j * 70
        d.rounded_rectangle([mx, 108, mx + 40, 150], 6, fill=c + (255,), outline=ink, width=3)
    # door (left)
    dx0, dx1, dy = DOOR
    d.rectangle([dx0 - 8, dy - 8, dx1 + 8, FYP], fill=(20, 20, 24, 255), outline=ink, width=4)
    return im


def draw_door(d, t, bottom):
    ink = INK + (255,)
    x0, x1, y0 = DOOR
    open_k = 0.0
    if bottom:
        for a, b in ((T_LEAVE1 - 0.4, T_LEAVE1 + 0.45), (T_BACK0 - 0.1, T_BACK0 + 0.7)):
            if a <= t < b:
                open_k = 1 - smooth(prog(t, (a + b) / 2, b))
    w = (x1 - x0) * (1 - 0.8 * open_k)
    d.rectangle([x0, y0, x0 + w, FYP], fill=(130, 96, 66, 255), outline=ink, width=4)
    d.ellipse([x0 + w - 30, y0 + 150, x0 + w - 14, y0 + 166], fill=(230, 200, 90, 255), outline=ink)


def butter_block(d, cx, cy, s=1.0):
    ink = INK + (255,)
    d.rounded_rectangle([cx - 30 * s, cy - 14 * s, cx + 30 * s, cy + 14 * s], 4, fill=(250, 220, 90, 255), outline=ink,
                        width=3)
    d.rectangle([cx - 30 * s, cy - 14 * s, cx - 10 * s, cy + 14 * s], fill=(240, 240, 236, 255), outline=ink, width=2)


def item(d, kind, col, cx, base_y):
    ink = INK + (255,)
    c = col + (255,)
    if kind == "milk":
        d.rectangle([cx - 16, base_y - 56, cx + 16, base_y], fill=c, outline=ink, width=3)
        d.polygon([(cx - 16, base_y - 56), (cx, base_y - 70), (cx + 16, base_y - 56)], fill=c, outline=ink)
    elif kind == "jar":
        d.rounded_rectangle([cx - 16, base_y - 38, cx + 16, base_y], 6, fill=c, outline=ink, width=3)
        d.rectangle([cx - 14, base_y - 46, cx + 14, base_y - 38], fill=(200, 200, 206, 255), outline=ink, width=2)
    elif kind == "eggs":
        d.rectangle([cx - 30, base_y - 18, cx + 30, base_y], fill=(200, 180, 150, 255), outline=ink, width=3)
        for j in range(3):
            d.ellipse([cx - 26 + j * 18, base_y - 30, cx - 12 + j * 18, base_y - 12], fill=c, outline=ink, width=2)
    elif kind == "apple":
        d.ellipse([cx - 14, base_y - 28, cx + 14, base_y], fill=c, outline=ink, width=3)


def draw_fridge(im, d, t, good):
    ink = INK + (255,)
    x0, x1, y0 = FR
    k = fridge_open(t, good)
    if k > 0.02:
        # the inside, lit
        d.rectangle([x0, y0, x1, FYP], fill=(220, 228, 236, 255), outline=ink, width=6)
        for sy in SHELVES:
            d.rectangle([x0 + 8, sy, x1 - 8, sy + 8], fill=(180, 196, 210, 255))
        gone = {kind_t[2] for kind_t in THROWN if not good and t >= kind_t[2]}
        # the fixed contents (top shelf, bottom shelf)
        item(d, "milk", (236, 236, 242), x0 + 40, SHELVES[0])
        if 2.0 not in gone:
            item(d, "milk", (236, 236, 242), x0 + 80, SHELVES[0])
        if 2.6 not in gone:
            item(d, "jar", (200, 70, 60), x0 + 140, SHELVES[0])
        if 3.2 not in gone:
            item(d, "eggs", (240, 220, 180), x0 + 160, SHELVES[1])
        if 3.8 not in gone:
            item(d, "jar", (90, 160, 90), x0 + 60, SHELVES[2])
        if 4.4 not in gone:
            item(d, "apple", (220, 60, 60), x0 + 130, SHELVES[2])
        if 5.0 not in gone:
            item(d, "milk", (240, 200, 90), x0 + 190, SHELVES[2])
        butter_here = not (good and t >= T_TAKE)
        if butter_here:
            butter_block(d, *BUTTER, 1.25)
        # the door, swung open to the right
        w = (x1 - x0) * (1 - k) + 26 * k
        d.rectangle([x1, y0, x1 + w, FYP], fill=(236, 238, 242, 255), outline=ink, width=5)
        g = Image.new("RGBA", (600, 600), (0, 0, 0, 0))
        ImageDraw.Draw(g).ellipse([100, 100, 500, 500], fill=(230, 240, 255, int(60 * k)))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(60)), (x0 - 180, y0 - 60))
        d = ImageDraw.Draw(im)
        # the ring around the butter
        for t0 in ((T_SPOT,) if good else (T_RING,)):
            if t0 <= t < t0 + 1.4 and butter_here or (not good and t >= T_RING):
                r = 46 + 6 * math.sin((t - t0) * 9)
                d.ellipse([BUTTER[0] - r, BUTTER[1] - r, BUTTER[0] + r, BUTTER[1] + r], outline=(255, 80, 70, 255),
                          width=6)
    else:
        d.rounded_rectangle([x0, y0, x1, FYP], 12, fill=(226, 230, 236, 255), outline=ink, width=6)
        d.line([(x0, y0 + 140), (x1, y0 + 140)], fill=ink, width=5)
        d.rectangle([x0 + 20, y0 + 40, x0 + 30, y0 + 110], fill=(150, 156, 166, 255))
        d.rectangle([x0 + 20, y0 + 170, x0 + 30, y0 + 280], fill=(150, 156, 166, 255))
        d.ellipse([x1 - 70, y0 + 30, x1 - 40, y0 + 60], fill=(240, 120, 110, 255), outline=ink, width=2)
    return d


def draw_floor_items(d, t):
    for kind, col, tt, fx in THROWN:
        if t < tt:
            continue
        k = prog(t, tt, tt + 0.35)
        x = lerp(AT_FRIDGE[0] + 20, fx, k)
        y = lerp(FYP - 240, FYP, k * k) - 80 * math.sin(math.pi * k)
        item(d, kind, col, x, y)


def draw_prop(d, pts, prop, facing):
    ink = INK + (255,)
    if prop in ("butter", "newbutter"):
        hx, hy = pts["hr"]
        butter_block(d, hx, hy - 6, 0.7)
    elif prop == "two":
        for j in ("hl", "hr"):
            hx, hy = pts[j]
            butter_block(d, hx, hy - 8, 0.7)
    elif prop == "bag":
        hx, hy = pts["hr"]
        d.rounded_rectangle([hx - 26, hy, hx + 26, hy + 56], 6, fill=(240, 236, 226, 255), outline=ink, width=3)
        d.arc([hx - 14, hy - 14, hx + 14, hy + 10], 180, 360, fill=ink, width=3)
    elif prop in ("knife", "toast"):
        cx = COUNTER[0] + 60
        cy = COUNTER[2]
        d.ellipse([cx - 50, cy - 14, cx + 50, cy + 4], fill=(236, 238, 244, 255), outline=ink, width=3)
        if prop == "knife":
            d.rounded_rectangle([cx - 30, cy - 34, cx + 30, cy - 6], 8, fill=(220, 170, 100, 255), outline=ink, width=3)
            d.rectangle([cx - 24, cy - 30, cx + 24, cy - 22], fill=(250, 220, 90, 255))
            hx, hy = pts["hl"]
            d.line([(hx, hy), (hx - 34, hy + 6)], fill=(200, 204, 214, 255), width=5)
        butter_block(d, cx + 90, cy - 14, 0.6)


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
    draw_door(d, t, not good)
    d = draw_fridge(im, d, t, good)
    if not good:
        draw_floor_items(d, t)
    if good:
        pose, hip, facing, prop = good_person(t)
        alpha = 1
    else:
        pose, hip, facing, prop, alpha = bad_person(t)
    pts = {"head": (80, 300)}
    if alpha > 0.01:
        pts = AJ.place(pose, hip, facing, SC)
        body, far = (GOOD_C, GOOD_FAR) if good else (BAD_C, BAD_FAR)
        spr, off = sprite(pts, body, far, facing)
        if alpha < 0.999:
            spr.putalpha(spr.split()[3].point(lambda v: int(v * alpha)))
        if good:
            im.alpha_composite(PW.glow_of(spr, 0.4, 12), off)
        im.alpha_composite(spr, off)
        d = ImageDraw.Draw(im)
        draw_prop(d, pts, prop, facing)
    if good and t >= T_CLOSE_G + 0.6:
        draw_prop(d, pts, "toast", facing)
    lab, val, col = search_label(t, good)
    if not (STRONG and t < 1.6) and t >= T_OPEN:
        widget(d, 820, 100, lab, val, col)
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
    img.alpha_composite(zoom(panel(t, True), t, (560, 400)), (0, TOP_Y0))
    img.alpha_composite(zoom(panel(t, False), t, (560, 400)), (0, BOT_Y0))
    d = ImageDraw.Draw(img)
    d.line([(0, STRIP_Y), (W, STRIP_Y)], fill=(56, 56, 62, 255), width=2)
    mm = clock_minutes(t)
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
    fl = font("Inter-SemiBold.otf", 38)
    la = smooth(prog(t, 1.5, 1.9)) if STRONG else 1.0
    if la > 0.01:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        if t < T_L1:
            spaced(ld, W / 2, TOP_Y0 + 14, "LOOKS", fl, (240, 242, 248, int(255 * la)), 10)
        spaced(ld, W / 2, BOT_Y0 + 14, "\"LOOKS\"", fl, (220, 224, 232, int(255 * la)), 10)
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
    mus = music.score(MUSIC, DUR, t_end=T_RING, start=0.0 if STRONG else 0.2, loud=1.2 if STRONG else 1.0)
    fx = np.zeros((n, 2))
    # fridge: door click and hum
    for tc in (T_OPEN, T_REOPEN):
        mix_in(fx, noise(0.08, int(tc * 100), lo=300, hi=3000) * env(int(0.08 * SR), 0.002, 0.04), tc, 0.06, 0.3)
    mix_in(fx, tone(60, 5.5, (1, 0.4), a=0.3, d=8) * 0.5, T_OPEN, 0.02, 0.3)
    # things landing on the floor
    for kind, col, tt, fx_ in THROWN:
        mix_in(fx, noise(0.1, int(tt * 100), lo=120, hi=1200) * env(int(0.1 * SR), 0.002, 0.05), tt + 0.33, 0.07, -0.2)
    # the toast scrape and bites
    for tk in np.arange(3.1, 7.5, 0.45):
        mix_in(fx, noise(0.12, int(tk * 100), lo=1500, hi=6000) * env(int(0.12 * SR), 0.01, 0.06), tk, 0.015, -0.3)
    # keys, door
    for tc in (T_LEAVE1, T_BACK0):
        mix_in(fx, noise(0.15, int(tc * 77), lo=80, hi=600) * env(int(0.15 * SR), 0.002, 0.08), tc, 0.09, -0.4)
    # the ring: a soft "ding" of realisation
    mix_in(fx, music.music_box(midi(86), 1.6), T_RING, 0.06)
    mix_in(fx, music.music_box(midi(81), 1.6), T_RING + 0.18, 0.05)
    for b0, b1, s, w in BUB_GOOD + BUB_BAD:
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
    out = sys.argv[1] if len(sys.argv) > 1 else "fridge.mp4"
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
