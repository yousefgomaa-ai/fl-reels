#!/usr/bin/env python3
"""4 MINDSETS WANT A HOUSE - high-quality neon 4-mind reel. 28 s, loops.

2016: the same small house, FOR SALE $250K, in all four panels (the hook). Decisions: the Doer buys it (SOLD);
the Overthinker waits for prices to drop; the Quitter says rent is fine (an apartment tower); the Show-off wants big
(a mansion, confetti). The years run to 2026: the Doer's home value climbs and a tree grows; the Overthinker's sign
ticks up every year (one small dip: "SEE?!" - then higher); the Quitter's rent climbs (RENT +18%); the Show-off parties,
then RATES UP!, MISSED PAYMENT, FORECLOSED. Results: HOME OWNER / RENT PAID $210K / FORECLOSED / STILL WAITING +68%.
"PRICES DIDN'T WAIT. / WAITING IS ALSO A DECISION."  FOLLOW FOR MORE.

    python3 stick/house.py stick/house.mp4
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
import music  # noqa
import hq  # noqa
from perfect_wave import clamp, env, font, lerp, lerp_pose, midi, mix_in, noise, prog, smooth, spaced, tone, write_wav  # noqa

W, H, FPS = 1080, 1920, 30
SR = 44100
DUR = 28.0
NF = int(round(DUR * FPS))
XFADE = 0.5
K = hq.K
BOLD = hq.BOLD
PX0 = 22
PW_ = W - 2 * PX0
PH = 398
GAP = 12
TITLE_H = 262
FY = PH - 66
S = 0.95
GOLD = (255, 205, 60)
GREEN = (110, 240, 140)
REDC = (255, 80, 80)
WARM = (255, 200, 120)

T_HOOK = 2.0
T_D = [2.2, 2.9, 3.6, 4.3]        # decisions: doer, overthinker, quitter, show-off
T_Y0, T_Y1 = 6.0, 20.0            # 2016 -> 2026
T_RES = 20.6
T_L1, T_L2 = 22.6, 23.7
CPS = 18.0
LINE1, LINE2 = "PRICES DIDN'T WAIT.", "WAITING IS ALSO A DECISION."
T_FOLLOW = 25.9


def year_f(t):
    return 2016 + 10 * prog(t, T_Y0, T_Y1)


def t_of(year):
    return T_Y0 + (year - 2016) / 10 * (T_Y1 - T_Y0)


def panel_y(i):
    return TITLE_H + i * (PH + GAP)


# ---------------------------------------------------------------- values
def home_value(t):
    return 250 + 170 * prog(t, T_Y0, T_Y1) ** 1.2


def sign_price(t):
    y = int(year_f(t))
    base = {2016: 250, 2017: 262, 2018: 275, 2019: 289, 2020: 304, 2021: 338, 2022: 371, 2023: 360,
            2024: 384, 2025: 401, 2026: 420}
    return base.get(y, 420)


def rent(t):
    r = 1200 + 600 * prog(t, T_Y0, T_Y1) ** 1.1
    if t >= t_of(2022):
        r += 230
    return int(r // 10 * 10)


def rent_paid(t):
    return int(210 * prog(t, T_Y0, T_Y1) ** 1.1)


# ---------------------------------------------------------------- poses
STAND = PW.STAND
POINT = dict(STAND, el=(36, -100), hl=(80, -112), er=(10, -60), hr=(14, -14))
THINK = dict(STAND, head=(8, -148), el=(30, -90), hl=(18, -128), er=(14, -64), hr=(4, -88))
ARMS_UP = dict(STAND, head=(0, -152), el=(-30, -130), hl=(-40, -180), er=(30, -130), hr=(40, -180))
SHRUG = dict(STAND, el=(-36, -76), hl=(-56, -100), er=(36, -76), hr=(56, -100))
SLUMP = dict(STAND, head=(14, -132), neck=(10, -98), el=(14, -54), hl=(18, -8), er=(10, -54), hr=(14, -8))
CARRY = dict(SLUMP, el=(26, -70), hl=(48, -80), er=(22, -66), hr=(44, -76))
RELAX = dict(STAND, el=(-34, -70), hl=(-6, -40), er=(34, -70), hr=(6, -40))


def hip(x):
    return (x, FY - 113 * S)


def person(t, i):
    x = 250
    if t < T_HOOK:
        return lerp_pose(STAND, POINT, 0.5 + 0.5 * math.sin(t * 3)), hip(x), 1
    if i == 0:
        k = math.sin(math.pi * prog(t, T_D[0], T_D[0] + 0.9))
        return lerp_pose(RELAX, ARMS_UP, k), hip(x), 1
    if i == 1:
        sway = math.sin(t * 2.2)
        p = dict(THINK, head=(8 + 4 * sway, -148))
        if t_of(2023) - 0.2 <= t < t_of(2023) + 0.9:            # the small dip: "SEE?!"
            p = lerp_pose(THINK, POINT, math.sin(math.pi * prog(t, t_of(2023) - 0.2, t_of(2023) + 0.9)))
        return p, hip(x), 1
    if i == 2:
        return lerp_pose(STAND, SHRUG, 0.4 + 0.2 * math.sin(t * 2)), hip(x), 1
    # show-off
    t_fc = t_of(2024)
    if t < t_of(2021):
        k = 0.5 + 0.5 * math.sin(t * 8)
        return lerp_pose(ARMS_UP, POINT, k * 0.6), hip(x), 1
    if t < t_fc:
        return lerp_pose(STAND, SHRUG, 0.6), hip(x), 1
    k = smooth(prog(t, t_fc + 0.4, t_fc + 2.2))
    a = 1 - smooth(prog(t, t_fc + 1.8, t_fc + 2.4))
    return AJ.walk((t - t_fc) * 4, CARRY), hip(lerp(x, 40, k)), -1


# ---------------------------------------------------------------- scenery
def small_house(p, cx, w, col, a=255, lit=1.0, sold=False):
    h = w * 0.62
    x0, x1 = cx - w / 2, cx + w / 2
    y1, y0 = FY, FY - h
    p.fill_rect([x0, y0, x1, y1], (22, 18, 40), a)
    p.rect([x0, y0, x1, y1], col, 4, a)
    p.fill_poly([(x0 - 14, y0), (cx, y0 - w * 0.42), (x1 + 14, y0)], (26, 20, 46), a)
    p.line([(x0 - 14, y0), (cx, y0 - w * 0.42), (x1 + 14, y0)], col, 4, a)
    dw = w * 0.16
    p.rect([cx - dw / 2, y1 - h * 0.55, cx + dw / 2, y1], col, 3, a)
    for wx in (x0 + w * 0.12, x1 - w * 0.12 - w * 0.2):
        p.fill_rect([wx, y0 + h * 0.2, wx + w * 0.2, y0 + h * 0.5], WARM, a * lit)
        p.rect([wx, y0 + h * 0.2, wx + w * 0.2, y0 + h * 0.5], col, 3, a)


def mansion(p, x0, x1, col, a=255, lit=1.0):
    h = 190
    y0 = FY - h
    p.fill_rect([x0, y0, x1, FY], (26, 18, 40), a)
    p.rect([x0, y0, x1, FY], col, 4, a)
    cx = (x0 + x1) / 2
    p.fill_poly([(x0 - 20, y0), (cx, y0 - 70), (x1 + 20, y0)], (30, 20, 48), a)
    p.line([(x0 - 20, y0), (cx, y0 - 70), (x1 + 20, y0)], col, 4, a)
    for j in range(5):
        x = x0 + 30 + j * (x1 - x0 - 60) / 4
        p.line([(x, y0 + 10), (x, FY)], col, 3, a * 0.8)
    for row in (y0 + 24, y0 + 96):
        for j in range(4):
            x = x0 + 50 + j * (x1 - x0 - 100) / 3 - 18
            p.fill_rect([x, row, x + 36, row + 46], WARM, a * lit)
            p.rect([x, row, x + 36, row + 46], col, 2, a)


def tower(p, x0, x1, col, a=255, t=0.0):
    y0 = 60
    p.fill_rect([x0, y0, x1, FY], (18, 16, 34), a)
    p.rect([x0, y0, x1, FY], col, 4, a)
    rng = np.random.default_rng(4)
    for row in np.arange(y0 + 20, FY - 40, 38):
        for x in np.arange(x0 + 18, x1 - 30, 40):
            on = rng.uniform() < 0.55
            p.fill_rect([x, row, x + 22, row + 24], WARM if on else (40, 36, 60), a * (0.9 if on else 0.6))
    p.rect([(x0 + x1) / 2 - 22, FY - 60, (x0 + x1) / 2 + 22, FY], col, 3, a)


def sign(p, x, top_txt, val_txt, col, a=255, val_col=None):
    p.line([(x, FY), (x, FY - 110)], (150, 150, 170), 4, a * 0.7)
    p.fill_rect([x - 78, FY - 186, x + 78, FY - 106], (14, 12, 24), a, r=8)
    p.rect([x - 78, FY - 186, x + 78, FY - 106], col, 3, a, r=8)
    p.text((x, FY - 178), top_txt, 18, (220, 220, 235), a)
    p.text((x, FY - 152), val_txt, 34, val_col or col, a, neon=True)


def tree(p, x, k, a=255):
    if k <= 0.02:
        return
    h = 30 + 120 * k
    p.line([(x, FY), (x, FY - h)], (170, 120, 70), 4 + 3 * k, a)
    r = 18 + 40 * k
    p.ds.ellipse([(x - r) * K, (FY - h - r * 1.6) * K, (x + r) * K, (FY - h + r * 0.4) * K], fill=(40, 110, 60, int(a)))
    p.circle(x, FY - h - r * 0.6, r, (110, 220, 120), 4, a)


def tag(p, x, y, label, value, col, a=255):
    f = font(BOLD, int(36 * K))
    fl = font(BOLD, int(17 * K))
    tw = max(f.getlength(value) / K + 40, (fl.getlength(label) + 2 * K * len(label)) / K + 30, 190)
    p.fill_rect([x - tw, y, x, y + 76], (10, 10, 18), a * 0.92, r=10)
    p.rect([x - tw, y, x, y + 76], col, 3, a, r=10)
    p.text((x - tw / 2, y + 8), label, 17, (190, 194, 210), a)
    p.text((x - tw / 2, y + 30), value, 36, col, a, neon=True)


def bubble_text(p, t, items, col, x, y):
    for t0, t1, s in items:
        if t0 <= t < t1:
            k = hq.pop(t, t0, 0.28)
            a = 255 * (1 - smooth(prog(t, t1 - 0.25, t1)))
            size = 40 * max(0.3, k)
            p.text((x, y), s, size, col, a, neon=True)


def stamp(p, t, t0, s, col):
    if t < t0:
        return
    k = hq.pop(t, t0, 0.3)
    f = font(BOLD, int(56 * K))
    tw = (f.getlength(s) + 3 * K * len(s)) / K + 60
    cx, cy = PW_ * 0.64, PH * 0.5
    w, h = tw * k, 100 * k
    if w < 10:
        return
    lay = Image.new("RGBA", (int(w * K), int(h * K)), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle([0, 0, lay.width - 1, lay.height - 1], int(14 * K * k), fill=(8, 8, 12, 238),
                         outline=col + (255,), width=int(6 * K * k))
    fs = font(BOLD, max(4, int(56 * K * k)))
    tws = sum(fs.getlength(c) for c in s) + 3 * K * k * (len(s) - 1)
    xx = lay.width / 2 - tws / 2
    for c in s:
        ld.text((xx, lay.height / 2 - 34 * K * k), c, font=fs, fill=col + (255,))
        xx += fs.getlength(c) + 3 * K * k
    lay = lay.rotate(-5, resample=Image.BICUBIC, expand=True)
    p.top = (lay, (int(cx * K - lay.width / 2), int(cy * K - lay.height / 2)))


RESULTS = {0: ("HOME OWNER", GREEN), 2: ("RENT PAID $210K", REDC), 3: ("LOST IT ALL", REDC), 1: ("STILL WAITING", REDC)}
RES_T = {0: T_RES, 2: T_RES + 0.3, 3: T_RES + 0.6, 1: T_RES + 1.05}


def decision(t, i):
    return t >= T_D[i] + 0.2


BGS = []
FRAME0 = None


def panel(t, i):
    name, col = hq.CHARS[i]
    p = hq.Panel(BGS[i])
    hq.dust(p, t, 50 + i)
    # ------- scenery: the same house for everyone until each decision
    if i == 0:
        small_house(p, 650, 230, col)
        sold = t >= T_D[0] + 0.2
        if t < T_Y0 + 0.4:
            sign(p, 860, "FOR SALE" if not sold else "SOLD!", "$250K", GOLD if not sold else GREEN)
        tree(p, 880, prog(t, T_Y0, T_Y1))
        if t >= T_Y0:
            tag(p, PW_ - 20, 20, "HOME VALUE", f"${int(home_value(t))}K", GREEN)
    elif i == 1:
        small_house(p, 650, 230, col)
        price = sign_price(t) if t >= T_Y0 else 250
        up = t >= T_Y0 and price > 250
        sign(p, 860, "FOR SALE", f"${price}K", GOLD if not up else REDC)
        if up:
            pct = int(round((price - 250) / 250 * 100))
            p.text((860, FY - 230), f"+{pct}%", 30, REDC, 255, neon=True)
    elif i == 2:
        k = hq.ease(prog(t, T_D[2] + 0.2, T_D[2] + 0.8))
        if k < 1:
            small_house(p, 650, 230, col, a=255 * (1 - k))
            sign(p, 860, "FOR SALE", "$250K", GOLD, a=255 * (1 - k))
        if k > 0:
            tower(p, 560, 800, col, a=255 * k, t=t)
        if t >= T_Y0:
            tag(p, PW_ - 20, 20, "RENT / MONTH", f"${rent(t):,}", REDC if t >= t_of(2022) else GOLD)
    else:
        k = hq.ease(prog(t, T_D[3] + 0.2, T_D[3] + 0.8))
        t_fc = t_of(2024)
        lit = 1.0 - smooth(prog(t, t_fc, t_fc + 0.3)) * 0.9
        if k < 1:
            small_house(p, 650, 230, col, a=255 * (1 - k))
            sign(p, 860, "FOR SALE", "$250K", GOLD, a=255 * (1 - k))
        if k > 0:
            mansion(p, 470 + 120 * (1 - k), 960 - 120 * (1 - k), col, a=255 * k, lit=lit)
        if t >= T_Y0 and t < t_fc:
            tag(p, PW_ - 20, 20, "MORTGAGE / MONTH", "$9,800", GOLD if t < t_of(2022) else REDC)
        hq.confetti(p, t, T_D[3] + 0.3, t_of(2019), 720, 150, 9, 60)
        if t_fc <= t < RES_T[3]:
            kk = hq.pop(t, t_fc, 0.3)
            if kk > 0.05:
                p.text((715, 140), "FORECLOSED", 54 * kk, REDC, 255, neon=True)
                p.line([(480, 120), (950, 300)], REDC, 6, 230)
    # ------- the character
    pose, hp, facing = person(t, i)
    pts = AJ.place(pose, hp, facing, S)
    a = 255
    if i == 3 and t >= t_of(2024) + 1.8:
        a = 255 * (1 - smooth(prog(t, t_of(2024) + 1.8, t_of(2024) + 2.4)))
    if a > 3:
        p.stick(pts, col, 10, a)
        if i == 3 and t >= t_of(2024):
            hx, hy = pts["hl"]
            p.fill_rect([hx - 26, hy - 34, hx + 26, hy + 6], (150, 110, 70), a)
    # ------- the words
    words = {0: [(T_D[0], T_D[0] + 1.6, "I'LL BUY IT.")],
             1: [(T_D[1], T_D[1] + 1.6, "WAIT FOR A DROP."), (t_of(2018), t_of(2018) + 1.2, "NEXT YEAR."),
                 (t_of(2020), t_of(2020) + 1.2, "TOO EXPENSIVE."), (t_of(2023) - 0.2, t_of(2023) + 1.0, "SEE?!"),
                 (t_of(2025), t_of(2025) + 1.2, "...NEXT YEAR.")],
             2: [(T_D[2], T_D[2] + 1.6, "RENT IS FINE."), (t_of(2022), t_of(2022) + 1.4, "RENT +18%")],
             3: [(T_D[3], T_D[3] + 1.6, "TOO SMALL. GO BIG!"), (t_of(2020), t_of(2020) + 1.2, "NEW POOL!"),
                 (t_of(2022), t_of(2022) + 1.3, "RATES UP!"), (t_of(2023), t_of(2023) + 1.2, "MISSED PAYMENT")]}[i]
    wcol = {0: col, 1: col, 2: col, 3: col}[i]
    for t0, t1, s in words:
        c = REDC if s in ("RENT +18%", "RATES UP!", "MISSED PAYMENT") else wcol
        bubble_text(p, t, [(t0, t1, s)], c, 590, 66)
    # ------- the results
    if i in RES_T:
        s, c = RESULTS[i]
        stamp(p, t, RES_T[i], s, c)
    # ------- label and frame
    p.ds.ellipse([18 * K, 20 * K, 32 * K, 34 * K], fill=col + (255,))
    p.ds.text((42 * K, 12 * K), name, font=font(BOLD, 28 * K), fill=col + (255,))
    out = p.compose()
    if getattr(p, "top", None):
        lay, pos = p.top
        g = lay.filter(ImageFilter.GaussianBlur(10 * K))
        out.alpha_composite(g, pos)
        out.alpha_composite(lay, pos)
    im = hq.downsample(out, PW_, PH)
    # camera: a slow push-in, shakes on the big moments
    events = [RES_T.get(i, 99)]
    if i == 3:
        events.append(t_of(2024))
    if i == 2:
        events.append(t_of(2022))
    dx, dy = hq.shake(t, events, 9)
    im = hq.camera(im, 1.0 + 0.035 * prog(t, 0, DUR), dx, dy)
    ImageDraw.Draw(im).rounded_rectangle([1, 1, PW_ - 2, PH - 2], 14, outline=col + (170,), width=3)
    return im


def frame(t):
    img = Image.new("RGBA", (W, H), (4, 4, 9, 255))
    for i in range(4):
        img.alpha_composite(panel(t, i), (PX0, panel_y(i)))
    # title
    tl = Image.new("RGBA", (W * K, TITLE_H * K), (0, 0, 0, 0))
    tp = hq.Panel(Image.new("RGBA", (W * K, TITLE_H * K), (0, 0, 0, 0)))
    if t < T_L1:
        tp.text((W / 2 - 110, 40), "4 MINDSETS WANT A", 50, (250, 250, 252), 255)
        tp.text((W / 2 + 290, 40), "HOUSE", 50, GOLD, 255, neon=True)
        y = int(year_f(t))
        kk = 1.0
        if t >= T_Y0:
            frac = (year_f(t) - y)
            kk = 1 + 0.18 * max(0, 1 - frac * 6)
        tp.text((W / 2, 112 - 10 * (kk - 1)), str(y), 86 * kk, REDC, 255, neon=True, spacing=8)
    else:
        for t0, s2, y in ((T_L1, LINE1, 52), (T_L2, LINE2, 140)):
            if t < t0:
                continue
            k = int(clamp((t - t0) * CPS, 0, len(s2)))
            tp.text((W / 2, y), s2[:k] + " " * (len(s2) - k), 54 if len(s2) < 22 else 48, (250, 250, 252), 255)
    tl = tp.compose(glow=0.8)
    img.alpha_composite(tl.resize((W, TITLE_H), Image.LANCZOS), (0, 0))
    rgb = np.asarray(img.convert("RGB"))
    rgb = hq.bloom(rgb, 0.5, 150, 26)
    if T_HOOK - 0.05 <= t < T_HOOK + 0.2:
        rgb = np.clip(rgb.astype(np.float32) + 60 * (1 - prog(t, T_HOOK - 0.05, T_HOOK + 0.2)), 0, 255).astype(np.uint8)
    arr = rgb.astype(np.float32)
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
    global BGS
    BGS = [hq.night_bg(PW_, PH, seed=20 + i, floor_y=FY) for i in range(4)]


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


# ---------------------------------------------------------------- sound
def synth(f, dur, bright=0.5, dec=7.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = sum((1 / k) * np.sin(2 * np.pi * f * k * tt) * (bright ** (k - 1)) for k in (1, 3, 5, 7))
    return x * np.minimum(1, tt / 0.004) * np.exp(-tt * dec)


def audio():
    n = int(DUR * SR)
    mus, fx = np.zeros((n, 2)), np.zeros((n, 2))
    bpm = 100
    beat = 60 / bpm
    six = beat / 4
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]      # Am F C G
    # hook: a soft pad and a bell from frame 0, the "FOR SALE" sign swings in
    for k, m in enumerate((45, 57, 64, 69)):
        mix_in(mus, GS.pad(midi(m), 2.2, 0.02, 0.8), 0.0, 0.05, (k - 1.5) * 0.3)
    mix_in(fx, music.music_box(midi(81), 1.6), 0.0, 0.07, 0.2)
    mix_in(fx, tone(60, 0.6, (1, 0.5), a=0.003, d=0.3), 0.0, 0.18)
    # decisions: one bright pop each
    for j, tk in enumerate(T_D):
        mix_in(fx, synth(midi(72 + 4 * j), 0.4, 0.4, 9), tk, 0.05, (j - 1.5) * 0.4)
    # the years: arpeggio + pulse that grows, a tick on every new year
    tt, i = T_HOOK, 0
    while tt < T_RES - 0.6:
        bi = int((tt - T_HOOK) / (4 * beat)) % 4
        ch = chords[bi]
        seq = [0, 1, 2, 1, 2, 0, 1, 2]
        g = 0.022 + 0.035 * prog(tt, T_HOOK, T_RES)
        if tt >= T_Y0 - 0.5 or i % 2 == 0:
            mix_in(mus, synth(midi(ch[seq[i % 8]] + 12), 0.25, 0.45), tt, g, 0.3 if i % 2 else -0.3)
        if i % 4 == 0 and tt >= T_Y0:
            mix_in(mus, synth(midi(ch[0] - 24), 0.4, 0.6, 5) * 1.3, tt, g * 1.3)
        i += 1
        tt += six
    b = 0
    while T_HOOK + b * 4 * beat < T_RES - 0.6:
        t0 = T_HOOK + b * 4 * beat
        for k, m in enumerate(chords[b % 4]):
            mix_in(mus, GS.pad(midi(m), min(4 * beat, T_RES - 0.6 - t0), 0.3, 0.6), t0, 0.03, (k - 1) * 0.4)
        if t0 >= T_Y0:
            for q in range(4):
                tk = t0 + q * beat
                if tk < T_RES - 0.6:
                    mix_in(mus, tone(58, 0.2, (1,), a=0.002, d=0.09, sweep=40), tk, 0.13)
        b += 1
    for y in range(2017, 2027):
        tk = t_of(y)
        mix_in(fx, tone(1760, 0.05, (1,), a=0.001, d=0.02), tk, 0.03)
        mix_in(fx, tone(2637, 0.2, (1, 0.4), a=0.001, d=0.1), tk + 0.02, 0.018, -0.4)     # doer: value up
    # events
    mix_in(fx, tone(500, 0.6, (1, 0.5, 0.3), a=0.01, d=0.35, sweep=250), t_of(2022), 0.06, 0.3)     # rates / rent up
    mix_in(fx, tone(420, 0.5, (1, 0.5), a=0.01, d=0.3, sweep=220), t_of(2023), 0.05, 0.3)
    fc = t_of(2024)
    mix_in(fx, tone(40, 1.4, (1, 0.6, 0.3), a=0.003, d=0.8), fc, 0.35)
    mix_in(fx, noise(1.2, 3, lo=60, hi=600) * env(int(1.2 * SR), 0.01, 0.6), fc, 0.2)
    mix_in(fx, noise(0.5, 4, lo=3000, hi=10000) * env(int(0.5 * SR), 0.001, 0.2), fc + 0.05, 0.05)
    for tk in np.arange(T_D[3] + 0.3, t_of(2019), 0.4):
        mix_in(fx, noise(0.08, int(tk * 100), lo=2000, hi=9000) * env(int(0.08 * SR), 0.002, 0.04), tk, 0.025, 0.4)
    # riser into the results, silence, stamps
    rs = noise(1.6, 7, lo=400, hi=6000) * np.linspace(0, 1, int(1.6 * SR)) ** 2
    mix_in(fx, rs, T_RES - 1.7, 0.07)
    mix_in(fx, tone(200, 1.6, (1, 0.5), a=1.4, d=0.3, sweep=800), T_RES - 1.7, 0.03)
    for i2, t0 in RES_T.items():
        g = 0.26 if i2 == 1 else 0.15
        mix_in(fx, tone(70, 0.5, (1, 0.5), a=0.002, d=0.25) + 0.35 * noise(0.5, 40 + i2, lo=400, hi=5000) *
               env(int(0.5 * SR), 0.002, 0.12), t0, g)
    for k, m in enumerate((45, 57, 64, 69, 72, 76)):
        mix_in(mus, GS.pad(midi(m), 4.0, 0.4, 2.0), T_RES + 1.4, 0.035, (k - 2.5) * 0.3)
    for j, m in enumerate((81, 76, 72, 69)):
        mix_in(mus, music.music_box(midi(m), 1.8), T_L1 + j * 0.5, 0.05, 0.2)
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
    out = sys.argv[1] if len(sys.argv) > 1 else "house.mp4"
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
                          "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                          "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100",
                          "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                         stdin=subprocess.PIPE)
    with Pool(os.cpu_count(), initializer=init_worker) as pool:
        for i, b in enumerate(pool.imap(render, range(NF), chunksize=2)):
            p.stdin.write(b)
            if i % 120 == 0:
                print(f"{i}/{NF}", flush=True)
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print(out)


if __name__ == "__main__":
    main()
