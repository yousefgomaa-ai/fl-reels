#!/usr/bin/env python3
"""4 MINDSETS WIN THE LOTTERY - WHO STAYS RICH? The neon 4-mind format. 14 s, loops.

Hook: four winning tickets, JACKPOT, $1,000,000 on every panel. The years run 0 -> 10.
THE DOER invests and keeps working: a green chart climbs, $1M -> $2.5M. THE OVERTHINKER holds the ticket and thinks:
"STOCKS OR GOLD?" "TAXES?" "WHAT IF..." "NEXT YEAR." - his counter still says $1,000,000. THE QUITTER quits his job,
lies on a beach chair; the money drains; NOW HIRING. THE SHOW-OFF buys a neon supercar and throws cash; $0 in a year,
the car gets a REPO stamp.  Twist: the Overthinker's ticket - EXPIRED. He never cashed it.
"IT WASN'T LUCK. / IT WAS THE NEXT DECISION."  FOLLOW FOR MORE.

    python3 stick/lottery.py stick/lottery.mp4
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
import neon as N  # noqa
from perfect_wave import (MONO, clamp, env, font, lerp, lerp_pose, midi, mix_in, noise, out_back,  # noqa
                          prog, smooth, spaced, tone, write_wav)

W, H, FPS = 1080, 1920, 30
SR = 44100
DUR = 24.0
NF = int(round(DUR * FPS))
XFADE = 0.45
BOLD = N.BOLD
PW_ = N.PX1 - N.PX0
PH = N.PANEL_H
FLOOR = PH - 70
S = 0.95
GOLD = (255, 205, 60)
GREEN = (110, 240, 140)

T_HOOK = 2.0                   # the jackpot
T_DEC = 2.0                    # 2-6 s: the first decisions
T_Y0, T_Y1 = 6.0, 17.0         # YEAR 0 -> YEAR 10
T_CRASH0, T_CRASH1 = 13.0, 15.2
T_RES = 17.0
T_L1, T_L2 = 19.0, 20.0
CPS = 18.0
LINE1, LINE2 = "IT WASN'T LUCK.", "IT WAS THE NEXT DECISION."
T_FOLLOW = 21.9


def year(t):
    return int(10 * prog(t, T_Y0, T_Y1) + 0.0001)


def doer_value(t):
    base = 1 + 1.5 * prog(t, T_Y0, T_Y1) ** 1.5
    dip = 0.55 * math.sin(math.pi * prog(t, T_CRASH0, T_CRASH1)) if T_CRASH0 <= t < T_CRASH1 else 0
    return 1e6 * max(0.4, base - dip)


def money(t, i):
    if i == 0:
        return doer_value(t)
    if i == 1:
        return 1e6 if t < T_RES else 0
    if i == 2:
        return 1e6 * (1 - prog(t, T_Y0, 12.0) ** 0.8)
    return 1e6 * (1 - prog(t, T_Y0, 10.5) ** 0.7)


def fmt(v):
    if v >= 1e6:
        return f"${v / 1e6:.2f}M" if v < 9.995e6 else f"${v / 1e6:.1f}M"
    return f"${int(v):,}"


# ---------------------------------------------------------------- poses
STAND = PW.STAND
HOLD_UP = dict(STAND, head=(0, -152), el=(36, -100), hl=(70, -120), er=(-20, -100), hr=(-30, -130))
SIT_TYPE = dict(AJ.SIT_TYPE)
THINK = dict(AJ.SIT_TYPE, head=(10, -146), el=(30, -90), hl=(22, -128), er=(34, -66), hr=(60, -80))
LOUNGE = {"head": (-96, -96), "neck": (-62, -74), "el": (-70, -110), "hl": (-90, -130), "er": (-30, -90),
          "hr": (-10, -120), "kl": (60, -24), "fl": (120, 4), "kr": (56, -18), "fr": (116, 10)}
QUIT = dict(STAND, head=(0, -152), el=(-30, -130), hl=(-40, -180), er=(30, -130), hr=(40, -180))
LOOK = dict(STAND, head=(14, -146), el=(14, -60), hl=(20, -14), er=(10, -60), hr=(16, -14))
FLEX = dict(STAND, el=(-40, -110), hl=(-30, -150), er=(40, -110), hr=(30, -150))
THROW = dict(STAND, el=(30, -110), hl=(70, -140), er=(-20, -70), hr=(-30, -40))
SLUMP = {"head": (20, -96), "neck": (12, -62), "el": (36, -40), "hl": (50, -6), "er": (30, -36), "hr": (44, -2),
         "kl": (60, -20), "fl": (100, 40), "kr": (50, -14), "fr": (90, 44)}


def stand_hip(x):
    return (x, FLOOR - 113 * S)


def person(t, i):
    """pose, hip, facing"""
    if t < T_HOOK:
        k = 0.5 + 0.5 * math.sin(t * 12)
        return lerp_pose(STAND, HOLD_UP, 0.7 + 0.3 * k), stand_hip(240), 1
    if i == 0:
        k = smooth(prog(t, 2.6, 3.0))
        typ = 0.5 + 0.5 * math.sin(t * 16)
        p = dict(SIT_TYPE, hl=(84, -50 + 3 * typ), hr=(78, -46 - 3 * typ))
        return lerp_pose(HOLD_UP, p, k), (240, lerp(FLOOR - 113 * S, FLOOR - 104, k)), 1
    if i == 1:
        k = smooth(prog(t, 2.8, 3.2))
        sway = math.sin(t * 2.5)
        return lerp_pose(HOLD_UP, dict(THINK, head=(10 + 4 * sway, -146)), k), \
            (240, lerp(FLOOR - 113 * S, FLOOR - 104, k)), 1
    if i == 2:
        if t < T_Y0:
            return QUIT, stand_hip(240), 1
        if t < 12.3:
            k = smooth(prog(t, T_Y0, T_Y0 + 0.4))
            return lerp_pose(QUIT, LOUNGE, k), (lerp(240, 330, k), lerp(FLOOR - 113 * S, FLOOR - 72, k)), 1
        k = smooth(prog(t, 12.3, 12.7))
        return lerp_pose(LOUNGE, LOOK, k), (lerp(330, 560, k), lerp(FLOOR - 72, FLOOR - 113 * S, k)), 1
    # show-off
    if t < 10.6:
        k = 0.5 + 0.5 * math.sin(t * 9)
        return lerp_pose(FLEX, THROW, k), stand_hip(240), 1
    k = smooth(prog(t, 10.6, 11.1))
    return lerp_pose(STAND, SLUMP, k), (240, lerp(FLOOR - 113 * S, FLOOR - 60, k)), 1


# ---------------------------------------------------------------- props
def ticket(im, x, y, col, expired=False, ang=0):
    tw, th = 150, 74
    lay = Image.new("RGBA", (tw + 20, th + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([10, 10, 10 + tw, 10 + th], 8, fill=(255, 230, 140, 255), outline=(200, 150, 40, 255), width=3)
    d.text((22, 16), "JACKPOT", font=font(BOLD, 22), fill=(120, 60, 10, 255))
    d.text((22, 46), "$1,000,000", font=font(BOLD, 22), fill=(120, 60, 10, 255))
    lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    im.alpha_composite(lay, (int(x - lay.width / 2), int(y - lay.height / 2)))


def desk(im, t):
    N.neon_line(im, [(330, FLOOR - 110), (560, FLOOR - 110)], (200, 200, 210), 5, 0.5)
    N.neon_line(im, [(350, FLOOR - 110), (350, FLOOR)], (200, 200, 210), 4, 0.3)
    N.neon_line(im, [(540, FLOOR - 110), (540, FLOOR)], (200, 200, 210), 4, 0.3)
    N.neon_line(im, [(400, FLOOR - 112), (470, FLOOR - 112), (490, FLOOR - 170)], (200, 200, 210), 4, 0.6)
    # the growing chart
    k = prog(t, T_Y0, T_Y1)
    if k > 0:
        pts = []
        steps = max(2, int(40 * k))
        crash = T_CRASH0 <= t < T_CRASH1 + 0.6
        for j in range(steps + 1):
            u = j / 40
            tt = T_Y0 + u * (T_Y1 - T_Y0)
            v = doer_value(tt) / 1e6
            pts.append((620 + 360 * u, 290 - 230 * (v - 0.4) / 2.1 + 6 * math.sin(u * 30)))
        N.neon_line(im, pts, (255, 80, 80) if crash else GREEN, 5, 1.2)
        N.neon_line(im, [(620, 300), (990, 300)], (80, 80, 90), 2, 0.2)
        d = ImageDraw.Draw(im)
        d.text((640, 300), "INDEX FUND", font=font(BOLD, 22), fill=GREEN + (255,))


def beach(im, t):
    if t < T_Y0:
        return
    a = smooth(prog(t, T_Y0, T_Y0 + 0.4))
    col = (255, 150, 40)
    N.neon_line(im, [(250, FLOOR - 40), (420, FLOOR - 70), (440, FLOOR)], col, 5, 0.7 * a)
    N.neon_line(im, [(250, FLOOR - 40), (200, FLOOR - 130)], col, 5, 0.7 * a)
    # sun and palm
    N.neon_rect(im, [700, 70, 780, 150], (255, 200, 80), 4, 0.8 * a, radius=40)
    N.neon_line(im, [(880, FLOOR), (870, 150)], (255, 150, 40), 5, 0.5 * a)
    for ang in (-150, -110, -60, -20):
        r = math.radians(ang)
        N.neon_line(im, [(870, 150), (870 + 70 * math.cos(r), 150 + 30 * math.sin(r) + 20)], (120, 220, 120), 4, 0.6 * a)
    if t >= 12.5:
        k = out_back(prog(t, 12.5, 12.8))
        N.neon_rect(im, [620, 80, 620 + 300 * k, 80 + 110 * k], (255, 255, 255), 4, 1.0)
        if k > 0.9:
            N.neon_text(im, (770, 110), "NOW HIRING", 40, (255, 255, 255), glow=0.8)


def car(im, t):
    col = (255, 70, 200)
    if t < T_Y0:
        return
    a = smooth(prog(t, T_Y0, T_Y0 + 0.3)) if t < 11.0 else 1 - 0.7 * smooth(prog(t, 11.0, 11.8))
    base = FLOOR - 10
    body = [(520, base - 40), (560, base - 90), (700, base - 110), (860, base - 90), (980, base - 60), (990, base - 20),
            (520, base - 20)]
    N.neon_line(im, body, col, 5, 1.1 * a, closed=True)
    for wx in (600, 900):
        N.neon_rect(im, [wx - 34, base - 54, wx + 34, base + 14], col, 5, 1.1 * a, radius=34)
    if t >= 11.0:
        k = out_back(prog(t, 11.0, 11.3))
        lay = Image.new("RGBA", (280, 110), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        ld.rounded_rectangle([0, 0, 279, 109], 12, outline=(255, 60, 60, 255), width=6)
        spaced(ld, 140, 16, "REPO", font(BOLD, 64), (255, 60, 60, 255), 6)
        lay = lay.rotate(-10, expand=True, resample=Image.BICUBIC)
        lay = lay.resize((max(1, int(lay.width * k)), max(1, int(lay.height * k))))
        im.alpha_composite(lay, (int(760 - lay.width / 2), int(base - 80 - lay.height / 2)))


def cash_rain(im, t, pts):
    if not (T_Y0 <= t < 10.6):
        return
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(7)
    hx, hy = pts["hl"]
    for j in range(14):
        ph = (t * 1.2 + j / 14) % 1.0
        x = hx + rng.uniform(-40, 260) * ph
        y = hy - 60 * ph + 300 * ph * ph
        ang = ph * 6 + j
        w, h = 30, 14
        c, s_ = math.cos(ang), math.sin(ang)
        poly = [(x + c * dx - s_ * dy, y + s_ * dx + c * dy) for dx, dy in ((-w, -h), (w, -h), (w, h), (-w, h))]
        if y < FLOOR:
            d.polygon(poly, fill=(110, 220, 120, 230), outline=(40, 120, 50, 255))


def thoughts(im, t, col):
    for t0, s in [(4.0, "STOCKS OR GOLD?"), (6.6, "TAXES?"), (9.0, "WHAT IF..."), (11.5, "NEXT YEAR."),
                  (14.0, "MAYBE LATER.")]:
        if t0 <= t < t0 + 2.0:
            k = prog(t, t0, t0 + 2.0)
            a = math.sin(math.pi * min(1, k * 1.2))
            lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
            N.neon_text(lay, (680, 120 - 40 * k), s, 34, col, glow=0.8)
            lay.putalpha(lay.split()[3].point(lambda v, a=a: int(v * a)))
            im.alpha_composite(lay)


def counter(im, t, i, col):
    v = money(t, i)
    s = fmt(v)
    if i == 1 and t < T_RES:
        s = "$1,000,000"
    c = (GREEN if v > 1.05e6 else GOLD) if v > 0 else (255, 80, 80)
    d = ImageDraw.Draw(im)
    f = font(BOLD, 40)
    tw = f.getlength(s)
    d.text((PW_ - tw - 30, 14), s, font=f, fill=c + (255,))
    if i == 1 and t < T_RES:
        d.text((PW_ - 172, 60), "UNCLAIMED", font=font(BOLD, 22), fill=(150, 150, 160, 255))


RESULTS = [("$2.5M", GREEN), ("EXPIRED", (255, 80, 80)), ("$0", (255, 80, 80)), ("$0", (255, 80, 80))]


def stamp(im, t, i):
    order = [0, 2, 3, 1]                       # the Overthinker comes last: the twist
    j = order.index(i)
    t0 = T_RES + 0.25 * j + (0.35 if i == 1 else 0)
    if t < t0:
        return
    k = out_back(prog(t, t0, t0 + 0.3))
    if k < 0.05:
        return
    s, col = RESULTS[i]
    f = font(BOLD, 70 if i == 1 else 64)
    tw = f.getlength(s) + 3 * len(s)
    lay = Image.new("RGBA", (int(tw + 70), 116), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle([0, 0, lay.width - 1, 115], 14, fill=(8, 8, 12, 235), outline=col + (255,), width=6)
    spaced(ld, lay.width / 2, 18, s, f, col + (255,), 3)
    lay = lay.rotate(-6 if i else 0, resample=Image.BICUBIC, expand=True)
    lay = lay.resize((max(1, int(lay.width * k)), max(1, int(lay.height * k))), Image.LANCZOS)
    cx = [760, 600, 400, 480][i]
    im.alpha_composite(lay, (int(cx - lay.width / 2), int(PH / 2 - lay.height / 2 + 10)))


BGS = []
FRAME0 = None


def panel(t, i):
    im = BGS[i].copy()
    name, col = N.CHARS[i]
    if i == 0:
        desk(im, t)
    if i == 2:
        beach(im, t)
    if i == 3:
        car(im, t)
    pose, hip, facing = person(t, i)
    pts = AJ.place(pose, hip, facing, S)
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    N.neon_stick(lay, pts, col, width=10, glow=1.3)
    im.alpha_composite(lay)
    if t < T_HOOK:
        ticket(im, pts["hl"][0] + 10, pts["hl"][1] - 30, col, ang=8 * math.sin(t * 10))
    elif i == 1:
        ticket(im, pts["hr"][0] + 40, pts["hr"][1] - 10, col, ang=-10)
    if i == 3:
        cash_rain(im, t, pts)
        if t < 10.6:
            hx, hy = pts["neck"]
            N.neon_line(im, [(hx - 16, hy + 6), (hx, hy + 30), (hx + 16, hy + 6)], GOLD, 4, 1.0)
    if i == 1:
        thoughts(im, t, col)
    events = {0: [(2.2, 3.4, "INVEST IT."), (T_CRASH0, T_CRASH0 + 1.2, "MARKET CRASH!"), (14.3, 15.5, "STAY CALM.")],
              1: [(2.6, 3.8, "LET ME THINK...")],
              2: [(3.0, 4.6, "I QUIT!"), (7.0, 8.2, "PARIS!"), (8.5, 9.7, "BALI!"), (10.0, 11.2, "VEGAS!")],
              3: [(3.4, 4.6, "BUY EVERYTHING!"), (6.2, 7.3, "NEW CAR"), (7.6, 8.7, "YACHT"), (9.0, 10.1, "MANSION"),
                  (10.5, 11.6, "BALANCE: $0")]}[i]
    for a0, a1, s_ in events:
        if a0 <= t < a1:
            k = out_back(prog(t, a0, a0 + 0.25))
            c = (255, 80, 80) if ("CRASH" in s_ or "$0" in s_) else col
            lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
            N.neon_text(lay, (660 if i == 1 else 560, 100), s_, int(44 * max(0.3, min(1.0, k))), c)
            im.alpha_composite(lay)
    # the jackpot flash on the hook
    if t < T_HOOK:
        k = 0.5 + 0.5 * math.sin(t * 20)
        N.neon_text(im, (PW_ / 2 + 200, 140), "JACKPOT!", 62, GOLD, glow=0.8 + 0.6 * k)
        rng = np.random.default_rng(i)
        d = ImageDraw.Draw(im)
        for j in range(30):
            x = rng.uniform(0, PW_)
            y = (rng.uniform(0, PH) + t * 300) % PH
            c = [(255, 205, 60), (255, 70, 200), (60, 220, 255), (255, 255, 255)][j % 4]
            d.rectangle([x, y, x + 8, y + 14], fill=c + (255,))
    counter(im, t, i, col)
    N.label(im, i)
    stamp(im, t, i)
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle([1, 1, im.width - 2, im.height - 2], 14, outline=col + (160,), width=3)
    im.alpha_composite(lay)
    return im


def frame(t):
    img = Image.new("RGBA", (W, H), (6, 6, 10, 255))
    for i in range(4):
        img.alpha_composite(panel(t, i), (N.PX0, N.panel_y(i)))
    if t < T_L1:
        f = font(BOLD, 58)
        parts = [("4 MINDSETS WIN ", (250, 250, 252)), ("$1,000,000", GOLD)]
        total = sum(f.getlength(p) for p, c in parts)
        x = W / 2 - total / 2
        for p, c in parts:
            N.neon_text(img, (x, 46), p, 58, c, anchor_center=False, glow=0.9 if c == GOLD else 0.4)
            x += f.getlength(p)
        d = ImageDraw.Draw(img)
        spaced(d, W / 2, 140, f"YEAR {year(t)}", font(BOLD, 44), (255, 80, 80, 255), 6)
    else:
        d = ImageDraw.Draw(img)
        fm = font(BOLD, 56)
        for t0, s2, y in ((T_L1, LINE1, 50), (T_L2, LINE2, 128)):
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
    global BGS
    BGS = [N.panel_bg(PW_, PH, seed=10 + i) for i in range(4)]


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


def kaching(at, g, pan, fx):
    mix_in(fx, tone(2637, 0.25, (1, 0.5, 0.3), a=0.001, d=0.12), at, g, pan)
    mix_in(fx, tone(3520, 0.3, (1, 0.4), a=0.001, d=0.15), at + 0.06, g * 0.8, pan)


def audio():
    n = int(DUR * SR)
    fx = np.zeros((n, 2))
    mus = music.score("marimba_f", DUR, t_end=T_RES, t_warm=T_L1 - 0.4, t_line=T_L1, start=T_HOOK, loud=1.3)
    # the hook: a jackpot fanfare and falling coins from frame 0
    for j, m in enumerate((72, 76, 79, 84)):
        mix_in(fx, tone(midi(m), 0.5, (1, 0.5, 0.3), a=0.003, d=0.3), 0.04 * j, 0.06, (j - 1.5) * 0.3)
    for k, m in enumerate((48, 60, 64, 67, 72)):
        mix_in(fx, GS.pad(midi(m), 0.9, 0.01, 0.4), 0.0, 0.05, (k - 2) * 0.3)
    rng = np.random.default_rng(3)
    for tk in np.arange(0.0, T_HOOK, 0.05):
        mix_in(fx, tone(2600 + rng.uniform(0, 1500), 0.08, (1, 0.4), a=0.001, d=0.03), tk, 0.02, rng.uniform(-0.6, 0.6))
    # the Doer: a ka-ching every year; the Show-off: cash throws; the Quitter: a slow sad slide
    for y in range(1, 11):
        kaching(T_Y0 + (T_Y1 - T_Y0) * y / 10, 0.035, -0.3, fx)
    for tk in np.arange(T_Y0, 10.6, 0.3):
        mix_in(fx, noise(0.12, int(tk * 100), lo=2000, hi=8000) * env(int(0.12 * SR), 0.005, 0.06), tk, 0.03, 0.4)
    mix_in(fx, tone(330, 0.8, (1, 0.4), a=0.01, d=0.5, sweep=200), 12.0, 0.04, 0.2)
    mix_in(fx, tone(180, 0.4, (1, 0.5), a=0.003, d=0.2, sweep=120), 11.0, 0.07, 0.3)
    # the market crash: a falling tone and a low rumble; the recovery: a rising chime
    mix_in(fx, tone(600, 1.2, (1, 0.5, 0.3), a=0.01, d=0.8, sweep=120), T_CRASH0, 0.06, -0.3)
    mix_in(fx, noise(1.4, 61, lo=40, hi=300) * env(int(1.4 * SR), 0.05, 0.8), T_CRASH0, 0.18)
    for j, m in enumerate((72, 76, 79, 84)):
        mix_in(fx, music.music_box(midi(m), 1.2), T_CRASH1 + 0.1 * j, 0.04, -0.3)
    # the first decisions: one pop each
    for tk in (2.2, 2.6, 3.0, 3.4):
        mix_in(fx, tone(1046, 0.12, (1, 0.3), a=0.002, d=0.06), tk, 0.04)
    # the results: stamps, the Overthinker's last and heaviest
    for j, i in enumerate([0, 2, 3, 1]):
        t0 = T_RES + 0.25 * j + (0.35 if i == 1 else 0)
        g = 0.22 if i == 1 else 0.13
        mix_in(fx, tone(70 if i else 90, 0.4, (1, 0.5), a=0.002, d=0.2) + 0.3 * noise(0.4, 40 + j, lo=400, hi=4000) *
               env(int(0.4 * SR), 0.002, 0.1), t0, g)
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
    out = sys.argv[1] if len(sys.argv) > 1 else "lottery.mp4"
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
