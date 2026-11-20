#!/usr/bin/env python3
"""IDEAS.md #9 - "I'M NOT HUNGRY." Split screen, 18 s, loops on itself.

The same couch, the same friend: "LAST BAG. SAVE IT." Both: "I'M NOT HUNGRY." The friend leaves - BACK IN 10:00.
Above, the bag stays on the table: CHIPS LEFT 40. Below: "JUST ONE." "ONE MORE." "IT'S BASICALLY AIR." - 40 ... 0 -
he pours the crumbs into his mouth, "...OOPS.", blows the empty bag up and puts it back. The friend returns:
above "THANKS!", below the bag is air - one crumb falls. "I WAS JUST CURIOUS."
"NOT HUNGRY. / JUST CURIOUS."  FOLLOW FOR MORE.

    VARIANT=A python3 stick/chips.py stick/chips-A.mp4      # current style
    VARIANT=B python3 stick/chips.py stick/chips-B.mp4      # stronger first second
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
GOOD_C, GOOD_FAR = AJ.DOER, AJ.DOER_FAR
BAD_C, BAD_FAR = AJ.OT, AJ.OT_FAR
FR_C, FR_FAR = (240, 190, 110), (200, 150, 80)
RED = (255, 64, 56)
BOLD = FM.BOLD
PH, TOP_Y0, BOT_Y0, STRIP_Y, FYP = OC.PH, OC.TOP_Y0, OC.BOT_Y0, OC.STRIP_Y, OC.FYP
STAND_Y = FYP - 141

SIT_HIP = (260, FYP - 140)
TABLE = (420, 620, FYP - 120)             # x0, x1, top
BAG_TABLE = (520, FYP - 170)
DOOR = (860, 990, FYP - 300)

# ---------------------------------------------------------------- timeline
T_LEAVE0, T_LEAVE1 = 1.7, 2.7
T_CLOCK0, T_CLOCK1 = 1.7, 12.0
T_GRAB = 3.0                               # below: the bag goes into his lap
T_EAT0, T_EAT1 = 3.4, 9.4
T_POUR0, T_POUR1 = 9.4, 10.4
T_BLOW0, T_BLOW1 = 10.9, 11.6
T_PUT = 11.7
T_BACK0, T_BACK1 = 12.0, 12.8
T_OPEN = 13.1
T_L1, T_L2 = 15.0, 16.1
CPS = 18.0
LINE1, LINE2 = "NOT HUNGRY.", "JUST CURIOUS."
T_FOLLOW = 16.95

B0 = -0.3 if STRONG else 0.3
FRIEND_BUBS = [(B0, 1.0, "LAST BAG. SAVE IT.", "me")]
FR_GOOD = [(13.4, 14.6, "THANKS!", "me")]
FR_BAD = [(13.5, 14.2, "...", "me")]
BUB_GOOD = [(1.0, 1.8, "I'M NOT HUNGRY.", "me"), (6.2, 7.2, "NOPE.", "me")]
BUB_BAD = [(1.0, 1.8, "I'M NOT HUNGRY.", "me"), (3.0, 3.9, "JUST ONE.", "me"), (4.9, 5.8, "ONE MORE.", "me"),
           (7.0, 8.1, "IT'S BASICALLY AIR.", "me"), (10.3, 10.9, "...OOPS.", "me"),
           (14.0, 14.95, "I WAS JUST CURIOUS.", "me")]


def chips_left(t, good):
    if good:
        return 40
    if t < T_EAT0:
        return 40
    if t >= T_POUR0:
        return 0
    return int(round(40 * (1 - prog(t, T_EAT0, T_EAT1) ** 1.6)))


def secs_left(t):
    return int(round(600 * (1 - prog(t, T_CLOCK0, T_CLOCK1))))


# ---------------------------------------------------------------- poses
SIT = dict(AJ.SIT_TYPE, el=(30, -60), hl=(54, -14), er=(26, -56), hr=(50, -10))
SIT_LAP = dict(AJ.SIT_TYPE, el=(36, -60), hl=(66, -40), er=(30, -56), hr=(60, -36))
SIT_EAT = dict(SIT_LAP, er=(34, -96), hr=(24, -134))
SIT_POUR = dict(AJ.SIT_TYPE, head=(4, -150), el=(30, -110), hl=(30, -170), er=(40, -106), hr=(44, -164))
SIT_BLOW = dict(SIT_LAP, head=(18, -146), el=(34, -90), hl=(40, -120), er=(40, -86), hr=(50, -114))
SIT_REACH = dict(AJ.SIT_TYPE, head=(30, -140), neck=(20, -100), el=(70, -60), hl=(120, -40), er=(64, -56), hr=(116, -36))
SIT_SHRUG = dict(SIT_LAP, el=(-20, -80), hl=(-30, -110), er=(40, -80), hr=(56, -110))
STAND = PW.STAND
FR_HOLD = dict(STAND, el=(-30, -70), hl=(-50, -90), er=(-24, -66), hr=(-46, -86))
FR_UP = dict(STAND, el=(-30, -110), hl=(-40, -160), er=(-24, -100), hr=(-50, -150))


def person(t, good):
    """pose, bag location ('table' | 'lap' | 'up' | 'blow'), bag fullness"""
    if good:
        k = smooth(prog(t, 3.6, 4.0)) * (1 - smooth(prog(t, 4.6, 5.0)))
        pose = lerp_pose(SIT, dict(SIT, head=(22, -146)), k)
        return pose, ("table" if t < T_OPEN - 0.3 else "friend"), 1.0
    if t < T_GRAB:
        return SIT, "table", 1.0
    if t < T_EAT0:
        k = smooth(prog(t, T_GRAB, T_GRAB + 0.2)) * (1 - smooth(prog(t, T_GRAB + 0.2, T_EAT0)))
        return lerp_pose(SIT_LAP, SIT_REACH, k), ("table" if t < T_GRAB + 0.2 else "lap"), 1.0
    if t < T_EAT1:
        speed = lerp(4.0, 13.0, prog(t, T_EAT0, T_EAT1))
        ph = (t - T_EAT0) * speed
        k = 0.5 - 0.5 * math.cos(ph)
        return lerp_pose(SIT_LAP, SIT_EAT, k), "lap", lerp(1.0, 0.75, prog(t, T_EAT0, T_EAT1))
    if t < T_POUR1:
        k = smooth(prog(t, T_POUR0, T_POUR0 + 0.3))
        return lerp_pose(SIT_LAP, SIT_POUR, k), "up", 0.45
    if t < T_BLOW0:
        k = smooth(prog(t, T_POUR1, T_POUR1 + 0.3))
        return lerp_pose(SIT_POUR, SIT_LAP, k), "lap", 0.4
    if t < T_PUT:
        k = smooth(prog(t, T_BLOW0, T_BLOW0 + 0.2))
        full = lerp(0.4, 1.05, smooth(prog(t, T_BLOW0 + 0.1, T_BLOW1)))
        return lerp_pose(SIT_LAP, SIT_BLOW, k), "blow", full
    if t < T_PUT + 0.5:
        k = math.sin(math.pi * prog(t, T_PUT, T_PUT + 0.5))
        return lerp_pose(SIT, SIT_REACH, k), ("blow" if t < T_PUT + 0.25 else "table"), 1.05
    if t >= 14.0:
        return lerp_pose(SIT, SIT_SHRUG, smooth(prog(t, 14.0, 14.3))), "friend", 1.05
    return SIT, ("table" if t < T_OPEN - 0.3 else "friend"), 1.05


def friend(t):
    """pose, hip, facing, alpha"""
    if t < T_LEAVE0:
        return FR_HOLD if t < 0.9 else STAND, (600, STAND_Y), -1, 1
    if t < T_LEAVE1 + 0.2:
        k = smooth(prog(t, T_LEAVE0, T_LEAVE1))
        a = 1 - smooth(prog(t, T_LEAVE1 - 0.15, T_LEAVE1 + 0.15))
        return AJ.walk((t - T_LEAVE0) * 7, STAND), (lerp(600, 925, k), STAND_Y), 1, a
    if t < T_BACK0:
        return STAND, (925, STAND_Y), -1, 0
    if t < T_BACK1:
        k = smooth(prog(t, T_BACK0 + 0.1, T_BACK1))
        a = smooth(prog(t, T_BACK0, T_BACK0 + 0.3))
        return AJ.walk((t - T_BACK0) * 7, STAND), (lerp(925, 660, k), STAND_Y), -1, a
    if t < T_OPEN - 0.3:
        return STAND, (660, STAND_Y), -1, 1
    if t < T_OPEN:
        return FR_HOLD, (660, STAND_Y), -1, 1
    return FR_HOLD, (660, STAND_Y), -1, 1


# ---------------------------------------------------------------- room
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
    # couch
    d.rounded_rectangle([90, FYP - 290, 420, FYP - 150], 26, fill=(110, 80, 140, 255), outline=ink, width=5)
    d.rounded_rectangle([80, FYP - 150, 430, FYP - 60], 20, fill=(130, 96, 160, 255), outline=ink, width=5)
    d.rounded_rectangle([60, FYP - 200, 120, FYP - 50], 18, fill=(110, 80, 140, 255), outline=ink, width=5)
    for x in (100, 400):
        d.rectangle([x, FYP - 60, x + 14, FYP], fill=(60, 48, 40, 255))
    # coffee table
    x0, x1, ty = TABLE
    d.rectangle([x0, ty, x1, ty + 16], fill=(150, 110, 76, 255), outline=ink, width=4)
    for lx in (x0 + 14, x1 - 30):
        d.rectangle([lx, ty + 16, lx + 16, FYP], fill=(130, 96, 66, 255), outline=ink, width=3)
    # wall frame
    d.rectangle([520, 120, 700, 250], fill=(60, 90, 120, 255), outline=ink, width=6)
    d.polygon([(530, 240), (600, 170), (650, 210), (690, 180), (690, 240)], fill=(90, 140, 100, 255))
    return im


def draw_door(d, t):
    ink = INK + (255,)
    x0, x1, y0 = DOOR
    d.rectangle([x0 - 8, y0 - 8, x1 + 8, FYP], fill=(20, 20, 24, 255), outline=ink, width=4)
    open_k = 0.0
    for a, b in ((T_LEAVE1 - 0.4, T_LEAVE1 + 0.45), (T_BACK0 - 0.1, T_BACK0 + 0.7)):
        if a <= t < b:
            open_k = 1 - smooth(prog(t, (a + b) / 2, b))
    w = (x1 - x0) * (1 - 0.8 * open_k)
    d.rectangle([x1 - w, y0, x1, FYP], fill=(130, 96, 66, 255), outline=ink, width=4)
    d.ellipse([x1 - w + 14, y0 + 150, x1 - w + 30, y0 + 166], fill=(230, 200, 90, 255), outline=ink)


def bag_sprite(full, rot=0.0, empty_look=False):
    w = 90
    h = int(lerp(70, 120, clamp(full)))
    bw = int(w * lerp(0.75, 1.0, clamp(full)))
    spr = Image.new("RGBA", (w + 40, 160), (0, 0, 0, 0))
    d = ImageDraw.Draw(spr)
    ink = INK + (255,)
    cx, by = (w + 40) // 2, 150
    top = by - h
    body = [(cx - bw / 2, by), (cx - bw / 2 - 6 * full, (top + by) / 2), (cx - bw / 2 + 4, top + 10),
            (cx + bw / 2 - 4, top + 10), (cx + bw / 2 + 6 * full, (top + by) / 2), (cx + bw / 2, by)]
    d.polygon(body, fill=(240, 196, 40, 255), outline=ink)
    d.line(body + [body[0]], fill=ink, width=4)
    for i in range(7):
        x = cx - bw / 2 + 4 + i * (bw - 8) / 6
        d.line([(x, top + 10), (x + 4, top)], fill=ink, width=3)
    d.rectangle([cx - bw / 2 + 4, top, cx + bw / 2 - 4, top + 10], fill=(220, 60, 50, 255))
    d.ellipse([cx - 22, top + h * 0.38, cx + 22, top + h * 0.38 + 30], fill=(220, 60, 50, 255), outline=ink, width=2)
    if full < 0.6:
        for i in range(3):
            y = top + 30 + i * 16
            d.line([(cx - bw / 2 + 8, y), (cx - bw / 2 + 24, y + 6)], fill=(170, 130, 20, 255), width=3)
    if rot:
        spr = spr.rotate(rot, resample=Image.BICUBIC, expand=True)
    return spr


def draw_bag(im, where, full, pts, fpts, t, good):
    if where == "table":
        spr = bag_sprite(full)
        im.alpha_composite(spr, (int(BAG_TABLE[0] - spr.width / 2), int(TABLE[2] - spr.height + 4)))
    elif where == "lap":
        hx, hy = pts["hl"]
        spr = bag_sprite(full)
        im.alpha_composite(spr, (int(hx - spr.width / 2 + 10), int(hy - spr.height + 30)))
    elif where == "up":
        hx, hy = pts["hl"]
        spr = bag_sprite(full, 165)
        im.alpha_composite(spr, (int(hx - spr.width / 2), int(hy - spr.height / 2 - 10)))
        d = ImageDraw.Draw(im)
        hx2, hy2 = pts["head"]
        for j in range(6):
            ph = (t * 3 + j / 6) % 1.0
            d.ellipse([hx + 4 - 3, hy + 30 + 30 * ph, hx + 4 + 3, hy + 36 + 30 * ph], fill=(240, 196, 60, 255))
    elif where == "blow":
        hx, hy = pts["hl"]
        spr = bag_sprite(full, 70)
        im.alpha_composite(spr, (int(hx - spr.width / 2 + 30), int(hy - spr.height / 2)))
    elif where == "friend" and fpts is not None:
        hx, hy = fpts["hl"]
        rot = 0
        if not good and t >= T_OPEN + 0.2:
            rot = 180 * smooth(prog(t, T_OPEN + 0.2, T_OPEN + 0.5))
        spr = bag_sprite(full, rot)
        im.alpha_composite(spr, (int(hx - spr.width / 2), int(hy - spr.height / 2 - 30)))
        d = ImageDraw.Draw(im)
        if good and t >= T_OPEN + 0.3:
            # a chip on its way to the friend's mouth
            k = (t - T_OPEN - 0.3) % 0.8 / 0.8
            hx2, hy2 = fpts["head"]
            x, y = lerp(hx, hx2 - 10, k), lerp(hy - 40, hy2 + 10, k)
            d.ellipse([x - 9, y - 6, x + 9, y + 6], fill=(240, 196, 60, 255), outline=INK + (255,))
        if not good and t >= T_OPEN + 0.5:
            k = prog(t, T_OPEN + 0.5, T_OPEN + 1.2)
            y = lerp(hy, FYP - 6, k * k)
            d.ellipse([hx - 4, y - 3, hx + 4, y + 3], fill=(240, 196, 60, 255))


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
    draw_door(d, t)
    pose, where, full = person(t, good)
    if not good and where in ("friend",) and t >= T_OPEN + 0.2:
        full = 0.4
    pts = AJ.place(pose, SIT_HIP, 1, SC)
    body, far = (GOOD_C, GOOD_FAR) if good else (BAD_C, BAD_FAR)
    spr, off = sprite(pts, body, far, 1)
    if good:
        im.alpha_composite(PW.glow_of(spr, 0.4, 12), off)
    im.alpha_composite(spr, off)
    fpose, fhip, ffacing, falpha = friend(t)
    fpts = None
    if falpha > 0.01:
        fpts = AJ.place(fpose, fhip, ffacing, SC)
        fspr, foff = sprite(fpts, FR_C, FR_FAR, ffacing)
        if falpha < 0.999:
            fspr.putalpha(fspr.split()[3].point(lambda v: int(v * falpha)))
        im.alpha_composite(fspr, foff)
    if t < 0.9 and fpts is not None:
        draw_bag(im, "friend", 1.0, pts, fpts, t, good)
    else:
        draw_bag(im, where, full, pts, fpts, t, good)
    d = ImageDraw.Draw(im)
    if not good and t >= 9.0:
        hx, hy = pts["head"]
        for j, (dx, dy) in enumerate(((22, 14), (30, 6), (14, 20))):
            d.ellipse([hx + dx - 3, hy + dy - 3, hx + dx + 3, hy + dy + 3], fill=(240, 196, 60, 255))
    if not (STRONG and t < 1.6):
        n = chips_left(t, good)
        widget(d, 800, 100, "CHIPS LEFT", str(n), (120, 230, 150) if n > 20 else (240, 200, 120) if n > 0
               else (240, 120, 120))
    OC.speech_at(im, t, BUB_GOOD if good else BUB_BAD, pts)
    if fpts is not None:
        OC.speech_at(im, t, FRIEND_BUBS + (FR_GOOD if good else FR_BAD), fpts)
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
    img.alpha_composite(zoom(panel(t, True), t, (540, 400)), (0, TOP_Y0))
    img.alpha_composite(zoom(panel(t, False), t, (540, 400)), (0, BOT_Y0))
    d = ImageDraw.Draw(img)
    d.line([(0, STRIP_Y), (W, STRIP_Y)], fill=(56, 56, 62, 255), width=2)
    sl = secs_left(t)
    s = f"BACK IN {sl // 60:02d}:{sl % 60:02d}" if t < T_BACK0 else "HE'S BACK"
    fc = font(BOLD, 60)
    tw = fc.getlength(s)
    d.rounded_rectangle([W / 2 - tw / 2 - 26, STRIP_Y - 48, W / 2 + tw / 2 + 26, STRIP_Y + 48], 10,
                        fill=(16, 6, 6, 255), outline=(90, 24, 22, 255), width=3)
    g = Image.new("RGBA", (int(tw + 120), 160), (0, 0, 0, 0))
    ImageDraw.Draw(g).text((60, 30), s, font=fc, fill=RED + (200,))
    g = g.filter(ImageFilter.GaussianBlur(10))
    img.alpha_composite(g, (int(W / 2 - tw / 2 - 60), int(STRIP_Y - 70)))
    d = ImageDraw.Draw(img)
    d.text((W / 2 - tw / 2, STRIP_Y - 38), s, font=fc, fill=RED + (255,))
    fl = font("Inter-SemiBold.otf", 38)
    la = smooth(prog(t, 1.5, 1.9)) if STRONG else 1.0
    if la > 0.01:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        if t < T_L1:
            spaced(ld, W / 2, TOP_Y0 + 14, "NOT HUNGRY", fl, (240, 242, 248, int(255 * la)), 10)
        spaced(ld, W / 2, BOT_Y0 + 14, "\"NOT HUNGRY\"", fl, (220, 224, 232, int(255 * la)), 10)
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
    t_end = T_OPEN + 0.3
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
    # crunches, faster and faster
    tk = T_EAT0 + 0.3
    while tk < T_EAT1:
        speed = lerp(4.0, 13.0, prog(tk, T_EAT0, T_EAT1))
        mix_in(fx, noise(0.07, int(tk * 1000) % 9999, lo=1500, hi=7000) * env(int(0.07 * SR), 0.002, 0.04), tk, 0.05,
               0.3)
        tk += 2 * math.pi / speed
    # bag crinkles, the pour, the blow
    for tc in (T_GRAB + 0.2, T_POUR0, T_PUT + 0.25, T_OPEN):
        mix_in(fx, noise(0.25, int(tc * 100), lo=2500, hi=9000) * env(int(0.25 * SR), 0.01, 0.15), tc, 0.04, 0.2)
    mix_in(fx, noise(0.7, 91, lo=200, hi=1500) * env(int(0.7 * SR), 0.1, 0.3), T_BLOW0 + 0.1, 0.06, 0.2)
    mix_in(fx, tone(70, 0.6, (1, 0.5), a=0.01, d=0.4), T_OPEN + 0.5, 0.12, 0.4)
    for k, m in enumerate((48, 55, 60, 64)):
        mix_in(mus, GS.pad(midi(m), 3.0, 0.5, 1.6), 14.6, 0.05, (k - 1.5) * 0.4)
    for j, m in enumerate((76, 72, 67, 72)):
        mix_in(mus, OC.piano(midi(m), 1.3, 0.5), 15.0 + j * 0.5, 0.05, 0.2)
    for b0, b1, s, w in FRIEND_BUBS + FR_GOOD + BUB_BAD:
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
    out = sys.argv[1] if len(sys.argv) > 1 else f"chips-{VARIANT}.mp4"
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
