#!/usr/bin/env python3
"""SHE CHOSE THE MONEY - 25.5 s.

0.0  cold open: the office, a broke man with a folder, the CEO chair starting to turn - freeze "SHE LEFT HIM / FOR MONEY."
1.3  the bench: him and her under a street lamp. A gold car stops, the rich guy steps out. She looks at him, then at
     the car, stands up and goes. The car leaves. Rain. "SHE CHOSE THE MONEY."   ($12 vs $2,000,000)
6.3  five years, split screen: HIM - rejections, "FUNDED", a team, a tower.  THE RICH GUY - party, car, casino, she
     leaves him too, SOLD.  Re-hook: "ONE OF THEM IS ABOUT TO NEED A JOB."
16.8 5 YEARS LATER: the rich guy, broke, walks into an office for a job. The chair turns: it's him. The folder drops.
     He stands, walks over, holds out his hand. Pull back: she's behind the glass, watching. DON'T GET EVEN. / GET BETTER.

    python3 stick/money.py --stills [t ...]     # -> stick/money/stills.png
    python3 stick/money.py stick/money.mp4
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
import hq  # noqa
import compare as C  # noqa
import race as R  # noqa
from compare import ell, line, rrect, poly, figure, place, ik, FLOOR, K, W, H  # noqa
from perfect_wave import clamp, env, font, lerp, lerp_pose, mix_in, noise, prog, smooth, tone, write_wav  # noqa
from money_chars import hero, girl, rich, S, GOLD, LILAC, RED  # noqa

FPS, SR = 30, 44100
HOOK, T_SPLIT, T_OFFICE, DUR = 1.3, 6.3, 16.8, 25.5
NF = int(round(DUR * FPS))
SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
MDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "study", "music")
STAND, SIT = PW.STAND, PW.SIT
YEAR_LEN = 2.0
RH = 11.2   # re-hook (video time)


# ---------------------------------------------------------------- helpers
def pts_of(pose, x, y_hip, f=1):
    return place(pose, (x, y_hip), f, S)


def stand_hip():
    return FLOOR - 113 * S


def sit_hip(seat_y):
    return seat_y - 4


def walk(x0, x1, u, f):
    """walking from x0 to x1, u in 0..1; returns (pose, x)"""
    x = lerp(x0, x1, u)
    ph = abs(x1 - x0) / 55 * u * math.pi
    return R.walk_pose(ph, 0.3), x


def text(im, x, y, s, size=56, col=(246, 240, 226), a=1.0, serif=True, sp=4):
    d = ImageDraw.Draw(im)
    f = font(SERIF_B, size) if serif else font("InterDisplay-Bold.otf", size)
    PW.spaced(d, x, y, s, f, col + (int(255 * clamp(a)),), sp)


def stamp(d, x, y, s, col, k, rot=-0.18, size=40):
    """a rubber stamp on the 2x layer"""
    if k <= 0:
        return
    sc = 1 + 0.8 * (1 - k)
    fnt = font("InterDisplay-Bold.otf", int(size * sc * K))
    tmp = Image.new("RGBA", (int(size * 9 * K), int(size * 2.4 * K)), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    w = td.textlength(s, font=fnt)
    tw, th = tmp.size
    td.rounded_rectangle(((tw - w) / 2 - 14 * K, th * 0.18, (tw + w) / 2 + 14 * K, th * 0.82), 8 * K,
                         outline=col + (255,), width=int(4 * K))
    td.text((tw / 2, th / 2), s, font=fnt, fill=col + (255,), anchor="mm")
    tmp = tmp.rotate(math.degrees(rot), resample=Image.BICUBIC, expand=True)
    d._image.alpha_composite(tmp, (int(x * K - tmp.size[0] / 2), int(y * K - tmp.size[1] / 2)))


def money_fmt(v):
    return f"${int(round(v)):,}"


def log_interp(vals, u):
    """vals at integer steps, u continuous"""
    i = min(int(u), len(vals) - 2)
    f = smooth(clamp(u - i))
    a, b = math.log(vals[i]), math.log(vals[i + 1])
    return math.exp(lerp(a, b, f))


# ---------------------------------------------------------------- props
def lamp(d, x, t):
    line(d, [(x, FLOOR), (x, FLOOR - 470)], (60, 64, 76, 255), 8)
    line(d, [(x, FLOOR - 470), (x - 50, FLOOR - 480)], (60, 64, 76, 255), 7)
    rrect(d, (x - 80, FLOOR - 488, x - 36, FLOOR - 474), 5, (240, 226, 180, 255))


def lamp_glow(x):
    g = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    cx, cy = (x - 58) * K, (FLOOR - 470) * K
    d.polygon([(cx - 20 * K, cy), (cx + 20 * K, cy), (cx + 230 * K, FLOOR * K), (cx - 230 * K, FLOOR * K)],
              (255, 226, 160, 34))
    d.ellipse((cx - 300 * K, FLOOR * K - 50 * K, cx + 300 * K, FLOOR * K + 50 * K), (255, 226, 160, 40))
    return g.filter(ImageFilter.GaussianBlur(26 * K))


_G = {}


def cached(key, fn):
    if key not in _G:
        _G[key] = fn()
    return _G[key]


def bench(d, x0, x1, seat_y):
    for x in (x0 + 20, x1 - 20):
        line(d, [(x, seat_y), (x, FLOOR)], (50, 40, 32, 255), 7)
    rrect(d, (x0, seat_y - 8, x1, seat_y + 6), 3, (122, 86, 56, 255), outline=(60, 40, 26, 255), w=1.5)
    for j in range(2):
        rrect(d, (x0, seat_y - 70 + j * 26, x1, seat_y - 58 + j * 26), 3, (110, 78, 50, 255), outline=(60, 40, 26, 255),
              w=1.5)
    for x in (x0 + 20, x1 - 20):
        line(d, [(x, seat_y - 74), (x, seat_y)], (50, 40, 32, 255), 6)


def car(d, cx, gy, f=-1, col=(22, 22, 28), sold=False):
    """a low sports car; f=-1 nose to the left"""
    L = 330
    def X(u):
        return cx + f * u
    body = [(X(-L / 2), gy - 30), (X(-L / 2 + 10), gy - 64), (X(-40), gy - 76), (X(10), gy - 118), (X(90), gy - 120),
            (X(140), gy - 82), (X(L / 2 - 6), gy - 72), (X(L / 2), gy - 30)]
    poly(d, body, col + (255,), outline=GOLD + (255,), w=2)
    poly(d, [(X(-26), gy - 80), (X(14), gy - 112), (X(84), gy - 113), (X(124), gy - 82)], (40, 52, 70, 255))
    line(d, [(X(-L / 2 + 14), gy - 52), (X(L / 2 - 10), gy - 52)], GOLD + (255,), 3)
    ell(d, X(-L / 2 + 8), gy - 50, 9, 6, (255, 246, 210, 255))    # headlight (front)
    ell(d, X(L / 2 - 4), gy - 50, 6, 5, (220, 40, 40, 255))
    for u in (-L / 2 + 66, L / 2 - 66):
        ell(d, X(u), gy - 22, 30, 30, (16, 16, 20, 255))
        ell(d, X(u), gy - 22, 15, 15, GOLD + (255,))
    if sold:
        rrect(d, (X(30) - 44, gy - 104, X(30) + 44, gy - 72), 3, (240, 236, 220, 255), outline=(200, 40, 40, 255), w=3)
        PW.spaced(d, X(30) * K, (gy - 88) * K, "SOLD", font("InterDisplay-Bold.otf", 22 * K), (200, 40, 40, 255), 2)


def headlights(cx, gy, f=-1):
    g = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    x, y = (cx + f * 160) * K, (gy - 50) * K
    d.polygon([(x, y - 6 * K), (x, y + 6 * K), (x + f * 700 * K, y + 120 * K), (x + f * 700 * K, y - 90 * K)],
              (255, 240, 200, 60))
    return g.filter(ImageFilter.GaussianBlur(18 * K))


def rain(d, t, a, seed=4, n=170):
    if a <= 0.01:
        return
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x0, sp = rng.uniform(-60, W + 60), rng.uniform(1.0, 1.4)
        y = ((t * sp * 1.6 + rng.uniform(0, 1)) % 1.0) * (FLOOR + 60) - 40
        line(d, [(x0 - 0.15 * y, y), (x0 - 0.15 * y - 6, y + 34)], (150, 170, 210, int(150 * a)), 1.6)


def desk(d, x0, x1, top, label=None):
    rrect(d, (x0, top, x1, FLOOR), 4, (44, 40, 40, 255), outline=(20, 18, 18, 255), w=2)
    rrect(d, (x0 - 10, top - 10, x1 + 10, top + 2), 3, (90, 70, 52, 255), outline=(40, 30, 22, 255), w=1.5)
    if label:
        rrect(d, ((x0 + x1) / 2 - 50, top + 30, (x0 + x1) / 2 + 50, top + 64), 3, (200, 170, 90, 255))
        PW.spaced(d, (x0 + x1) / 2 * K, (top + 47) * K, label, font("InterDisplay-Bold.otf", 22 * K), (30, 26, 20, 255), 3)


def laptop(d, x, top, glow=True, f=1):
    poly(d, [(x - 34, top - 2), (x + 34, top - 2), (x + 40, top + 4), (x - 40, top + 4)], (150, 154, 164, 255))
    poly(d, [(x - 30 * f - 4 * f, top - 2), (x - 26 * f, top - 52), (x + 22 * f, top - 52), (x + 26 * f, top - 2)],
         (50, 54, 64, 255))
    if glow:
        poly(d, [(x - 26 * f, top - 6), (x - 23 * f, top - 48), (x + 19 * f, top - 48), (x + 22 * f, top - 6)],
             (120, 170, 255, 255))


def chair(d, x, seat_y, f=-1):
    line(d, [(x, seat_y), (x, FLOOR - 16)], (40, 40, 46, 255), 7)
    line(d, [(x - 34, FLOOR - 6), (x + 34, FLOOR - 6)], (40, 40, 46, 255), 7)
    rrect(d, (x - 34, seat_y - 6, x + 34, seat_y + 8), 4, (30, 30, 36, 255))


def chair_back(d, x, seat_y, w):
    rrect(d, (x - w / 2, seat_y - 190, x + w / 2, seat_y + 4), 14, (26, 26, 32, 255), outline=(60, 60, 70, 255), w=2)


def city(d, x0, x1, top, bottom, seed=2):
    poly(d, [(x0, top), (x1, top), (x1, bottom), (x0, bottom)], (16, 22, 40, 255))
    rng = np.random.default_rng(seed)
    x = x0
    while x < x1:
        w = rng.uniform(40, 90)
        h = rng.uniform(80, (bottom - top) * 0.85)
        poly(d, [(x, bottom - h), (x + w, bottom - h), (x + w, bottom), (x, bottom)], (24, 30, 50, 255))
        for yy in np.arange(bottom - h + 10, bottom - 8, 16):
            for xx in np.arange(x + 6, x + w - 8, 12):
                if rng.uniform() < 0.35:
                    rrect(d, (xx, yy, xx + 6, yy + 8), 1, (250, 210, 120, int(rng.uniform(120, 230))))
        x += w + rng.uniform(4, 14)
    for xx in np.linspace(x0, x1, 5):
        line(d, [(xx, top), (xx, bottom)], (70, 76, 96, 255), 4)
    line(d, [(x0, top), (x1, top)], (70, 76, 96, 255), 5)
    line(d, [(x0, bottom), (x1, bottom)], (70, 76, 96, 255), 5)


# ---------------------------------------------------------------- compose
def compose(stage, glow=None, z=1.0, cx=W / 2, cy=H / 2, spots=((540, 0.9),), back=None, refl=True):
    base = C.stage_bg(spots).copy()
    if back is not None:
        base.alpha_composite(back)
    if glow is not None:
        base.alpha_composite(glow)
    if refl:
        tp = stage.crop((0, 0, W * K, FLOOR * K))
        r = tp.transpose(Image.FLIP_TOP_BOTTOM).crop((0, 0, W * K, (H - FLOOR) * K))
        r = r.resize((W * K // 4, (H - FLOOR) * K // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
        r = r.resize((W * K, (H - FLOOR) * K), Image.BILINEAR)
        fade = np.linspace(0.3, 0.0, (H - FLOOR) * K, dtype=np.float32)[:, None]
        r.putalpha(Image.fromarray((np.asarray(r.split()[3], np.float32) * fade).astype(np.uint8)))
        base.alpha_composite(r, (0, FLOOR * K))
    base.alpha_composite(stage)
    im = hq.camera(base, z, z * (W / 2 - cx) * K, z * (H / 2 - cy) * K)
    return im.resize((W, H), Image.LANCZOS)


# ---------------------------------------------------------------- act 1: the bench
SEAT = FLOOR - 76
CAR_GY = FLOOR + 46


def bench_scene(u, tv):
    stage = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(stage)
    lamp(d, 900, u)
    bench(d, 560, 860, SEAT)
    # her
    gx, gf = 640, 1
    stand_k = smooth(prog(u, 2.5, 2.9))
    if u >= 2.0:
        gf = -1          # she looks at the car
    if u < 2.9:
        pose = lerp_pose(SIT, STAND, stand_k)
        gp = pts_of(pose, gx, lerp(sit_hip(SEAT), stand_hip(), stand_k), gf)
        if u < 2.0:      # leaning toward him, a hand on the bench
            gp = pts_of(dict(SIT, head=(14, -148)), gx, sit_hip(SEAT), 1)
    elif u < 3.6:
        pose, x = walk(gx, 500, smooth(prog(u, 2.9, 3.6)), -1)
        gp = pts_of(pose, x, stand_hip(), -1)
    elif u < 4.2:   # with him, walking to the car
        pose, x = walk(500, 360, smooth(prog(u, 3.7, 4.2)), -1)
        gp = pts_of(pose, x, stand_hip(), -1)
    else:
        gp = None
    # the rich guy
    rp = None
    if 1.7 <= u < 4.25:
        if u < 3.7:
            rp = pts_of(STAND, 450, stand_hip(), 1)
        else:
            pose, x = walk(450, 330, smooth(prog(u, 3.7, 4.2)), -1)
            rp = pts_of(pose, x, stand_hip(), -1)
    # him
    hp = pts_of(dict(SIT, head=(4, -150)), 770, sit_hip(SEAT), -1)
    if 2.9 <= u < 3.7:   # reaches out for her
        k = smooth(prog(u, 2.9, 3.2)) * (1 - smooth(prog(u, 3.4, 3.7)))
        hp = dict(hp)
        tgt = (lerp(hp["hr"][0], 690, k), lerp(hp["hr"][1], hp["neck"][1] + 10, k))
        hp["hr"] = tgt
        hp["er"] = ik(hp["neck"], tgt, 42 * S, 40 * S, -1)
    if u >= 4.0:          # head down
        k = smooth(prog(u, 4.0, 4.6))
        hp = pts_of(dict(SIT, head=(lerp(4, 30, k), lerp(-150, -126, k)), neck=(lerp(3, 12, k), -106),
                         el=(30, -50), hl=(36, -10), er=(24, -46), hr=(30, -8)), 770, sit_hip(SEAT), -1)
    hero(stage, hp, "broke", f=-1)
    if gp is not None:
        girl(stage, gp, f=gf, wind=0.2)
    if rp is not None:
        rich(stage, rp, "rich", f=(1 if u < 3.7 else -1))
    if 3.6 <= u < 4.2:   # holding hands
        line(d, [rp["hl"] if rp else (0, 0), gp["hr"] if gp else (0, 0)], (238, 238, 242, 255), 8)
    # the car: in from the right, stops, leaves left
    if u < 1.6:
        cx = lerp(1500, 330, 1 - (1 - smooth(prog(u, 0.5, 1.6))) ** 2)
    elif u < 4.3:
        cx = 330
    else:
        cx = 330 - 1600 * (u - 4.3) ** 2
    if u >= 0.5 and cx > -400:
        car(d, cx, CAR_GY, -1)
    rain(d, tv, smooth(prog(u, 3.9, 4.6)))
    glow = cached("lamp", lambda: lamp_glow(900))
    if 0.5 <= u and cx > -400:
        hl = headlights(cx, CAR_GY, -1)
        g2 = glow.copy()
        g2.alpha_composite(hl)
        glow = g2
    return compose(stage, glow, 1.55, 600, 1170, spots=((700, 0.7),))


# ---------------------------------------------------------------- act 2: five years, split
LX, RX = 270, 810
HIM_M = [12, 340, 25000, 480000, 3200000, 10000000]
RICH_M = [2000000, 1600000, 900000, 150000, 9000, 40]


def split_scene(u, tv):
    yr = min(5, 1 + int(u / YEAR_LEN))
    yu = u - (yr - 1) * YEAR_LEN
    stage = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(stage)
    # ---------------- him
    if yr <= 2:
        desk(d, LX - 10, LX + 150, FLOOR - 92)
        laptop(d, LX + 60, FLOOR - 102, f=-1)
        for j in range(yr + 1):
            rrect(d, (LX + 110 + j * 14, FLOOR - 120, LX + 122 + j * 14, FLOOR - 102), 2, (236, 236, 236, 255))
        chair(d, LX - 60, SEAT + 6)
        p = pts_of(PW.SIT, LX - 60, sit_hip(SEAT + 6), 1)
        p = dict(p)
        for side, dx in (("hl", 0), ("hr", 18)):
            tgt = (LX + 30 + dx, FLOOR - 104 - 5 * max(0, math.sin(tv * 14 + dx)))
            p[side] = tgt
            p["e" + side[1]] = ik(p["neck"], tgt, 42 * S, 40 * S, 1)
        hero(stage, p, "broke", 1)
        if yr == 1:
            for j, t0 in enumerate((0.3, 0.9, 1.5)):
                stamp(d, LX + 60 - 20 * j, FLOOR - 230 - 46 * j, "REJECTED", (220, 50, 50), hq.pop(yu, t0, 0.18) if yu >= t0 else 0,
                      rot=-0.2 + 0.15 * j, size=30)
        else:
            stamp(d, LX + 40, FLOOR - 220, "REJECTED", (220, 50, 50), hq.pop(yu, 0.3, 0.18) if yu >= 0.3 else 0, size=30)
            stamp(d, LX + 60, FLOOR - 300, "FUNDED", (60, 200, 110), hq.pop(yu, 1.1, 0.2) if yu >= 1.1 else 0,
                  rot=0.12, size=40)
    elif yr == 3:     # a team
        for j, x in enumerate((LX - 10, LX + 130)):
            desk(d, x - 20, x + 60, FLOOR - 92)
            laptop(d, x + 20, FLOOR - 102, f=1)
        for j, x in enumerate((LX - 10, LX + 130)):
            p = pts_of(STAND, x - 40, stand_hip(), 1)
            figure(stage, p, S * 0.98, light=(0.4, -0.9))
        p = pts_of(dict(STAND, er=(30, -150), hr=(60, -180)), LX - 120, stand_hip(), 1)
        hero(stage, p, "broke", 1)
    else:            # the tower
        hgt = 300 + 260 * smooth(clamp((u - 6.0) / 3.5))
        poly(d, [(LX - 90, FLOOR - hgt), (LX + 90, FLOOR - hgt), (LX + 90, FLOOR), (LX - 90, FLOOR)], (30, 38, 62, 255),
             outline=(80, 90, 120, 255), w=2)
        rng = np.random.default_rng(5)
        for yy in np.arange(FLOOR - hgt + 50, FLOOR - 14, 22):
            for xx in np.arange(LX - 78, LX + 78, 18):
                if rng.uniform() < 0.7:
                    rrect(d, (xx, yy, xx + 10, yy + 12), 1, (250, 214, 130, 230))
        rrect(d, (LX - 40, FLOOR - hgt + 8, LX + 40, FLOOR - hgt + 40), 4, RED + (255,))
        PW.spaced(d, LX * K, (FLOOR - hgt + 24) * K, "HIM", font("InterDisplay-Bold.otf", 22 * K), (255, 255, 255, 255), 3)
        p = pts_of(STAND, LX + 150, stand_hip(), -1)
        hero(stage, p, "ceo" if yr == 5 else "broke", -1)
    # ---------------- the rich guy
    if yr == 1:       # the party
        bob = 10 * abs(math.sin(tv * 8))
        rp = pts_of(dict(PW.ARMS_UP, head=(6, -150)), RX - 70, stand_hip() - bob, 1)
        gp = pts_of(dict(STAND, el=(-26, -120), hl=(-30, -170)), RX + 60, stand_hip() - bob * 0.6, -1)
        rich(stage, rp, "rich", 1)
        girl(stage, gp, f=-1, wind=0.3)
        rng = np.random.default_rng(int(tv * 6))
        for _ in range(30):
            ell(d, RX + rng.uniform(-240, 240), rng.uniform(FLOOR - 700, FLOOR - 20), 4, 7,
                tuple(int(c) for c in rng.choice([[240, 200, 80], [220, 80, 160], [80, 200, 240]])) + (255,))
    elif yr == 2:     # the car, money flying
        car(d, RX + 60, FLOOR, -1, col=(200, 40, 40))
        rp = pts_of(dict(STAND, er=(30, -150), hr=(50, -190)), RX - 160, stand_hip(), 1)
        rich(stage, rp, "rich", 1)
        rng = np.random.default_rng(7)
        for j in range(14):
            v = (yu * 0.9 + j / 14) % 1
            x = RX - 140 + rng.uniform(-40, 220) * v
            y = FLOOR - 330 - 200 * v + 260 * v * v
            rrect(d, (x - 16, y - 8, x + 16, y + 8), 2, (110, 180, 110, int(255 * (1 - v * 0.6))))
    elif yr == 3:     # casino
        desk(d, RX - 60, RX + 160, FLOOR - 92)
        poly(d, [(RX - 70, FLOOR - 102), (RX + 170, FLOOR - 102), (RX + 160, FLOOR - 92), (RX - 60, FLOOR - 92)],
             (30, 110, 60, 255))
        n = max(0, 8 - int(yu * 5))
        for j in range(n):
            ell(d, RX + 60, FLOOR - 108 - j * 7, 18, 6, (200, 40, 40, 255))
        rp = pts_of(dict(STAND, head=(24, -138), neck=(12, -104), hl=(26, -140), el=(30, -96), hr=(20, -144),
                         er=(28, -100)), RX - 110, stand_hip(), 1)
        rich(stage, rp, "rich", 1)
    elif yr == 4:     # she leaves him too
        rp = pts_of(dict(STAND, er=(30, -100), hr=(70, -110)), RX - 80, stand_hip(), 1)
        rich(stage, rp, "rich", 1)
        pose, x = walk(RX + 20, RX + 260, smooth(clamp(yu / 1.8)), 1)
        girl(stage, pts_of(pose, x, stand_hip(), 1), f=1, wind=0.4)
    else:             # SOLD
        car(d, RX + 60, FLOOR, -1, col=(200, 40, 40), sold=True)
        rp = pts_of(dict(R.SIT_G, head=(20, -120), neck=(10, -92), el=(30, -50), hl=(40, -20), er=(36, -46),
                         hr=(46, -18)), RX - 170, FLOOR - 12 * S, 1)
        rich(stage, rp, "broke", 1)
    rain(d, tv, 1.0 if yr == 5 else 0.0, seed=9, n=90)
    im = compose(stage, None, 1.22, W / 2, 1150, spots=((LX, 0.9), (RX, 0.9)))
    dd = ImageDraw.Draw(im)
    line(dd, [(W / 2 * K / K, 470), (W / 2, FLOOR + 40)], (80, 86, 110, 255), 3) if False else None
    dd.line(((W / 2, 560), (W / 2, H)), (70, 76, 100), 3)
    return im


# ---------------------------------------------------------------- act 3: the office
DESK = (600, 900)
CH_X = 790
OSEAT = FLOOR - 86


def office_scene(u, tv, freeze=None):
    """u = seconds since the office act starts. freeze: hold the chair turn"""
    stage = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    back = cached("office", office_back)
    d = ImageDraw.Draw(stage)
    # her, behind the glass (left), only seen when the camera pulls back
    if u >= 5.2:
        k = smooth(prog(u, 5.6, 6.4))
        gp = pts_of(dict(STAND, head=(lerp(0, 8, k), lerp(-150, -146, k)), er=(22, -100), hr=(30, -150)), 90,
                    stand_hip(), 1)
        girl(stage, gp, f=1, wind=0.0)
    # the glass partition
    gl = Image.new("RGBA", stage.size, (0, 0, 0, 0))
    poly(ImageDraw.Draw(gl), [(0, FLOOR - 520), (190, FLOOR - 520), (190, FLOOR), (0, FLOOR)], (150, 190, 230, 46))
    stage.alpha_composite(gl)
    for x in (0, 190):
        line(d, [(x, FLOOR - 520), (x, FLOOR)], (120, 130, 150, 255), 6)
    line(d, [(0, FLOOR - 520), (190, FLOOR - 520)], (120, 130, 150, 255), 6)
    for j in range(3):
        line(d, [(30 + j * 50, FLOOR - 480), (80 + j * 50, FLOOR - 400)], (230, 240, 255, 60), 4)
    # chair + him
    ang = math.pi * smooth(prog(u, 2.0, 2.6)) if freeze is None else freeze
    stand_k = smooth(prog(u, 3.4, 3.9))
    chair(d, CH_X, OSEAT)
    hp = None
    if ang > math.pi / 2 and u < 3.9:
        if stand_k <= 0:
            hp = pts_of(PW.SIT, CH_X, sit_hip(OSEAT), -1)
        else:
            hp = pts_of(lerp_pose(PW.SIT, STAND, stand_k), CH_X - 30 * stand_k, lerp(sit_hip(OSEAT), stand_hip(), stand_k), -1)
    elif u >= 3.9:
        if u < 4.9:
            pose, x = walk(CH_X - 30, 520, smooth(prog(u, 3.9, 4.9)), -1)
            hp = pts_of(pose, x, stand_hip(), -1)
        else:
            hp = pts_of(STAND, 520, stand_hip(), -1)
        hp = dict(hp)
    if ang > math.pi / 2 or u >= 3.9:
        chair_back(d, CH_X + 34, OSEAT, 22 if u < 3.9 else 22)
    if u < 3.9:
        desk(d, *DESK, FLOOR - 96, label="CEO")
    if hp is not None and u >= 4.9:   # hand out
        k = smooth(prog(u, 4.9, 5.3))
        tgt = (lerp(hp["hr"][0], 470, k), lerp(hp["hr"][1], FLOOR - 150, k))
        hp["hr"] = tgt
        hp["er"] = ik(hp["neck"], tgt, 42 * S, 40 * S, 1)
    if hp is not None:
        hero(stage, hp, "ceo", -1)
    if u >= 3.9:
        desk(d, *DESK, FLOOR - 96, label="CEO")
    if ang <= math.pi / 2:
        chair_back(d, CH_X, OSEAT, 100 * max(0.7, math.cos(ang)))
    # the rich guy, broke, with a folder
    if u < 1.8:
        pose, x = walk(150, 420, smooth(prog(u, 0.0, 1.8)), 1)
    else:
        pose, x = STAND, 420
    rp = dict(pts_of(pose, x, stand_hip(), 1))
    folder_drop = u >= 2.9 and freeze is None
    if not folder_drop:
        tgt = (rp["neck"][0] + 30, rp["neck"][1] + 60)
        rp["hr"] = tgt
        rp["er"] = ik(rp["neck"], tgt, 42 * S, 40 * S, 1)
    if u >= 5.2:   # slowly takes the hand
        k = smooth(prog(u, 5.2, 5.9))
        tgt = (lerp(rp["hr"][0], 472, k), lerp(rp["hr"][1], FLOOR - 150, k))
        rp["hr"] = tgt
        rp["er"] = ik(rp["neck"], tgt, 42 * S, 40 * S, -1)
    rich(stage, rp, "broke", 1)
    if not folder_drop:
        fx, fy = rp["hr"]
        rrect(d, (fx - 6, fy - 40, fx + 20, fy + 10), 2, (200, 170, 100, 255), outline=(120, 96, 50, 255), w=1.5)
    else:
        v = u - 2.9
        rng = np.random.default_rng(11)
        for j in range(6):
            vv = min(v, 0.6 + 0.1 * j)
            px = 440 + rng.uniform(-60, 80) * vv
            py = min(FLOOR - 4, FLOOR - 190 + 600 * vv * vv)
            a = rng.uniform(-2, 2) * vv
            c_, s_ = math.cos(a), math.sin(a)
            pts = [(-16, -11), (16, -11), (16, 11), (-16, 11)]
            poly(d, [(px + x * c_ - y * s_, py + x * s_ + y * c_) for x, y in pts], (240, 238, 230, 255),
                 outline=(150, 150, 150, 255), w=1)
    # camera: close on the two, pull back to find her
    pb = smooth(prog(u, 5.4, 6.6))
    z = lerp(1.55, 1.25, pb)
    cx = lerp(600, 470, pb)
    cy = lerp(1170, 1120, pb)
    hit = 0.04 * hq.pop(u, 2.6, 0.25) if u >= 2.6 and freeze is None else 0
    return compose(stage, None, z + hit, cx, cy, spots=((520, 1.0), (790, 0.6)), back=back)


def office_back():
    g = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    poly(d, [(0, 0), (W, 0), (W, FLOOR), (0, FLOOR)], (18, 20, 28, 255))
    city(d, 560, 1080, FLOOR - 640, FLOOR - 130)
    return g


# ---------------------------------------------------------------- frame
def header_money(im, him, rich_v, show_rich=1.0, yr=None):
    d = ImageDraw.Draw(im)
    if yr is not None:
        PW.spaced(d, W / 2, 40, f"YEAR {yr}", font("InterDisplay-Bold.otf", 96), (246, 246, 250, 255), 6)
    for x, lab, v, a, col in ((LX, "HIM", him, 1.0, (236, 238, 246)), (RX, "THE RICH GUY", rich_v, show_rich, GOLD)):
        if a <= 0:
            continue
        PW.spaced(d, x, 170, lab, font("Inter-SemiBold.otf", 24), (214, 220, 238, int(255 * a)), 6)
        PW.spaced(d, x, 206, money_fmt(v), font("InterDisplay-Bold.otf", 58), col + (int(255 * a),), 2)


def frame(t):
    if t < HOOK:
        fr = min(t, 0.85)
        u = 1.7 + fr / 0.85 * 0.6
        im = office_scene(u, t, freeze=math.pi * 0.42 * fr / 0.85)
        if t >= 0.85:
            im = Image.blend(im.convert("RGB"), Image.new("RGB", (W, H), (0, 0, 0)), 0.35).convert("RGBA")
            k = hq.pop(t, 0.85, 0.2)
            text(im, W / 2, 360, "SHE LEFT HIM", int(110 * max(0.3, k)))
            text(im, W / 2, 360 + int(124 * max(0.3, k)), "FOR MONEY.", int(110 * max(0.3, k)), col=GOLD)
    elif t < T_SPLIT:
        u = t - HOOK
        im = bench_scene(u, t)
        header_money(im, 12, 2000000, smooth(prog(u, 1.8, 2.1)))
        a = smooth(prog(u, 4.4, 4.7))
        if a > 0:
            text(im, W / 2, 470, "SHE CHOSE THE MONEY.", 64, a=a)
    elif t < T_OFFICE:
        u = t - T_SPLIT
        im = split_scene(u, t)
        yr = min(5, 1 + int(u / YEAR_LEN))
        yu = clamp(u / YEAR_LEN, 0, 5)
        header_money(im, log_interp(HIM_M, yu), log_interp(RICH_M, yu), yr=yr)
        a = hq.pop(t, RH, 0.25) * (1 - smooth(prog(t, RH + 2.1, RH + 2.5))) if t >= RH else 0
        if a > 0:
            text(im, W / 2, 330, "ONE OF THEM IS ABOUT", 54, a=min(1, a))
            text(im, W / 2, 396, "TO NEED A JOB.", 54, col=(255, 140, 40), a=min(1, a))
    else:
        u = t - T_OFFICE
        im = office_scene(u, t)
        a = smooth(prog(u, 0.0, 0.3)) * (1 - smooth(prog(u, 1.4, 1.8)))
        if a > 0:
            text(im, W / 2, 300, "5 YEARS LATER", 60, a=a)
        for j, s in enumerate(("DON'T GET EVEN.", "GET BETTER.")):
            a = smooth(prog(u, 6.8 + 0.7 * j, 7.2 + 0.7 * j))
            if a > 0:
                text(im, W / 2, 220 + j * 90, s, 76, col=(GOLD if j else (246, 240, 226)), a=a)
    # cut flashes
    for c in (HOOK, T_SPLIT, T_OFFICE):
        if c <= t < c + 0.1:
            im = Image.blend(im.convert("RGB"), Image.new("RGB", (W, H), (255, 255, 255)), 0.6 * (1 - (t - c) / 0.1))
    return np.asarray(im.convert("RGB"))


def render(i):
    return frame(i / FPS).tobytes()


# ---------------------------------------------------------------- sound
def track(name, start, dur):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(start), "-t", str(dur), "-i", os.path.join(MDIR, name),
                          "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)


def put(out, sig, at, gain=1.0, fin=0.05, fout=0.3):
    i = int(at * SR)
    n = min(len(sig), len(out) - i)
    if n <= 0:
        return
    s = sig[:n] * gain
    e = np.ones(n)
    a, b = int(fin * SR), int(fout * SR)
    e[:a] = np.linspace(0, 1, a)
    if b:
        e[-b:] *= np.linspace(1, 0, b)
    out[i:i + n] += s * e[:, None]


HIT = 30.0          # Rynos Theme: the big entrance
T_REVEAL = T_OFFICE + 2.6


def audio():
    n = int(DUR * SR)
    out = np.zeros((n, 2))
    put(out, track("Rynos Theme.mp3", HIT - 0.4, HOOK + 0.2), 0.0, 0.9, fout=0.2)                  # cold open
    put(out, track("Bittersweet.mp3", 2.0, T_SPLIT - HOOK + 0.6), HOOK, 0.9, fin=0.1, fout=0.6)    # the bench
    st = HIT - (T_REVEAL - T_SPLIT)
    put(out, track("Rynos Theme.mp3", st, DUR - T_SPLIT), T_SPLIT - 0.1, 1.0, fin=0.4, fout=1.0)   # rise
    mix_in(out, noise(0.5, 3, lo=40, hi=1800)[:int(0.5 * SR)] * env(int(0.5 * SR), 0.003, 0.35), 0.85, 0.45, 0.0)
    rew = noise(0.35, 9, lo=500, hi=7000)[:int(0.35 * SR)] * env(int(0.35 * SR), 0.25, 0.05)
    mix_in(out, rew, HOOK - 0.3, 0.2, 0.0)
    # car engine in / out
    for at, d_ in ((HOOK + 0.5, 1.1), (HOOK + 4.3, 0.9)):
        eng = noise(d_, 5, lo=40, hi=400)[:int(d_ * SR)] * env(int(d_ * SR), 0.1, 0.4)
        mix_in(out, eng, at, 0.25, 0.0)
    # stamps
    for t0 in (0.3, 0.9, 1.5, YEAR_LEN + 0.3):
        mix_in(out, tone(90, 0.12, (1, 2.5), a=0.001, d=0.08), T_SPLIT + t0, 0.35, -0.5)
    mix_in(out, tone(660, 0.5, (1, 2, 3), a=0.002, d=0.35), T_SPLIT + YEAR_LEN + 1.1, 0.15, -0.5)
    # the chair, the folder
    mix_in(out, noise(0.5, 4, lo=200, hi=3000)[:int(0.5 * SR)] * env(int(0.5 * SR), 0.05, 0.3), T_OFFICE + 2.0, 0.08, 0.3)
    mix_in(out, noise(0.4, 6, lo=400, hi=5000)[:int(0.4 * SR)] * env(int(0.4 * SR), 0.005, 0.25), T_OFFICE + 2.95, 0.2, -0.2)
    tt = np.arange(n) / SR
    out *= np.clip((DUR - tt) / 0.8, 0.0, 1)[:, None]
    out /= max(1.0, np.abs(out).max() / 0.9)
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    if "--stills" in sys.argv:
        ts = [float(a) for a in sys.argv[2:]] or [0.9, 4.6, 8.0, 19.6]
        sheet = Image.new("RGB", (360 * len(ts), 640))
        for j, t in enumerate(ts):
            sheet.paste(Image.fromarray(frame(t)).resize((360, 640), Image.LANCZOS), (j * 360, 0))
        p = os.path.join(here, "money", "stills.png")
        sheet.save(p)
        print(p)
        return
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "money.mp4")
    wav = out + ".wav"
    write_wav(wav, audio())
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                          "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100",
                          "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                         stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for b in pool.imap(render, range(NF), chunksize=2):
            p.stdin.write(b)
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print(out)
    print('Credit: Music: "Bittersweet" and "Rynos Theme" by Kevin MacLeod (incompetech.com), CC BY 4.0')


if __name__ == "__main__":
    main()
