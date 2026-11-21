#!/usr/bin/env python3
"""$1,000 EMERGENCY. WHO SURVIVES? - high-quality neon 4-mind reel. 26.5 s, loops.

Hook (frame 0): BANG - all four cars break down at once: smoke, a blinking CHECK ENGINE, REPAIR: $1,000.
Balances pop: Doer $400, Overthinker EMERGENCY FUND $5,000, Quitter $40, Show-off $12.
Overthinker pays at once ("I KNEW THIS WOULD HAPPEN."), FIXED, drives off and comes back on time.
Doer sells things - SOLD! GUITAR $250, CONSOLE $180, BIKE $90 - is $80 short - SOLD! LAMP $80 - FIXED on day 7.
Show-off swipes the card ("JUST SWIPE IT."), keeps swiping (SHOES, DINNER, CONCERT) - CARD DEBT climbs to $3,200.
Quitter can't pay, takes the bus, is late - "YOU'RE FIRED." - sits on the curb.
Results: LOST HIS JOB / DEBT $3,200 / FIXED IN 7 DAYS / FIXED IN 1 HOUR (winner, crown).
"OVERTHINKING FINALLY PAID OFF. / SAVE BEFORE YOU NEED IT."  FOLLOW FOR MORE.

    python3 stick/emergency.py stick/emergency.mp4
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
DUR = 26.5
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
CAR_X = 700

T_BANG = 0.05
T_BANK = [2.4, 2.8, 3.2, 3.6]          # doer, overthinker, quitter, show-off
T_OT_PAY, T_OT_FIX = 4.6, 5.1
T_OT_DRIVE0, T_OT_DRIVE1 = 6.3, 7.3
T_OT_BACK0, T_OT_BACK1 = 9.0, 9.9
SALES = [(6.4, "GUITAR", 250), (8.2, "CONSOLE", 180), (9.8, "BIKE", 90), (11.3, "LAMP", 80)]
T_SHORT = 10.6                          # doer is $80 short
T_DOER_FIX = 12.0
SWIPES = [(4.9, "REPAIR", 1000), (13.0, "NEW SHOES", 450), (14.6, "DINNER", 380), (16.2, "CONCERT", 520)]
T_BUS0, T_BUS1 = 5.6, 7.4
T_FIRED = 8.8
T_RES = 19.4
RES_T = {2: T_RES, 3: T_RES + 0.3, 0: T_RES + 0.6, 1: T_RES + 1.05}
RESULTS = {2: ("LOST HIS JOB", REDC), 3: ("DEBT $3,200", REDC), 0: ("FIXED IN 7 DAYS", GOLD),
           1: ("FIXED IN 1 HOUR", GREEN)}
T_L1, T_L2 = 21.6, 22.8
CPS = 18.0
LINE1, LINE2 = "OVERTHINKING FINALLY PAID OFF.", "SAVE BEFORE YOU NEED IT."
T_FOLLOW = 24.4


def day(t):
    if t < 2.0:
        return 1
    if t < 12.0:
        return 1 + int(6 * prog(t, 2.0, 12.0))
    return 7 + int(358 * prog(t, 12.0, T_RES - 0.6) ** 1.4)


def panel_y(i):
    return TITLE_H + i * (PH + GAP)


# ---------------------------------------------------------------- money
def balance(t, i):
    if i == 0:
        v = 400
        for t0, item, val in SALES:
            if t >= t0 + 0.5:
                v += val
        if t >= T_DOER_FIX:
            v -= 1000
        if t >= T_DOER_FIX + 3:
            v += int(400 * prog(t, T_DOER_FIX + 3, T_RES))
        return v
    if i == 1:
        if t < T_OT_PAY + 0.3:
            return 5000
        return 4000 + int(1000 * prog(t, 12.0, T_RES) ** 1.2)
    if i == 2:
        return 40
    return 12


def debt(t):
    v = 0
    for t0, item, val in SWIPES:
        if t >= t0 + 0.3:
            v += val
    interest = 850 * prog(t, 12.0, T_RES - 0.4) ** 1.3
    return int(v + interest) // 10 * 10


# ---------------------------------------------------------------- poses
STAND = PW.STAND
PHONE = dict(STAND, el=(26, -66), hl=(44, -100), er=(22, -62), hr=(40, -96))
THINK = dict(STAND, head=(8, -148), el=(30, -90), hl=(18, -128), er=(14, -64), hr=(4, -88))
SHOCK = dict(STAND, head=(-6, -150), el=(-24, -110), hl=(-20, -150), er=(24, -110), hr=(20, -150))
HOLD = dict(STAND, el=(30, -80), hl=(56, -96), er=(26, -76), hr=(52, -92))
THROW = dict(STAND, el=(40, -110), hl=(90, -120), er=(14, -60), hr=(18, -14))
RELAX = dict(STAND, el=(-34, -70), hl=(-6, -40), er=(34, -70), hr=(6, -40))
CHEER = dict(STAND, head=(0, -152), el=(-30, -130), hl=(-40, -180), er=(30, -130), hr=(40, -180))
SWIPE = dict(STAND, el=(36, -96), hl=(84, -100), er=(14, -60), hr=(18, -14))
CURB = {"head": (20, -96), "neck": (12, -62), "el": (36, -40), "hl": (50, -6), "er": (30, -36), "hr": (44, -2),
        "kl": (60, -20), "fl": (100, 40), "kr": (50, -14), "fr": (90, 44)}
CALL = dict(STAND, el=(36, -110), hl=(18, -150), er=(14, -60), hr=(18, -14))


def hip(x):
    return (x, FY - 113 * S)


def person(t, i):
    """pose, hip, facing, alpha, prop"""
    x = 250
    if t < 2.2:
        k = math.sin(math.pi * prog(t, 0.05, 0.6))
        return lerp_pose(STAND, SHOCK, max(k, 0.6)), hip(x), 1, 1, None
    if t < T_BANK[i] + 0.9:
        return PHONE, hip(x), 1, 1, "phone"
    if i == 0:
        for t0, item, val in SALES:
            if t0 - 0.6 <= t < t0 + 0.4:
                k = smooth(prog(t, t0 - 0.6, t0 - 0.2))
                kt = smooth(prog(t, t0 - 0.1, t0 + 0.3))
                return lerp_pose(lerp_pose(STAND, HOLD, k), THROW, kt), hip(x), 1, 1, ("item", item, kt)
        if t >= T_DOER_FIX:
            k = math.sin(math.pi * prog(t, T_DOER_FIX, T_DOER_FIX + 1.0))
            return lerp_pose(RELAX, CHEER, k), hip(x), 1, 1, None
        if T_SHORT <= t < T_SALES_LAST():
            return THINK, hip(x), 1, 1, None
        return RELAX, hip(x), 1, 1, None
    if i == 1:
        if t < T_OT_DRIVE0:
            return lerp_pose(PHONE, RELAX, smooth(prog(t, T_OT_PAY, T_OT_PAY + 0.4))), hip(x), 1, 1, None
        if t < T_OT_DRIVE0 + 0.5:
            k = smooth(prog(t, T_OT_DRIVE0, T_OT_DRIVE0 + 0.5))
            return AJ.walk((t - T_OT_DRIVE0) * 7, STAND), hip(lerp(x, CAR_X - 60, k)), 1, 1 - k, None
        if t < T_OT_BACK1 + 0.3:
            return STAND, hip(CAR_X - 60), 1, 0, None
        k = smooth(prog(t, T_OT_BACK1 + 0.3, T_OT_BACK1 + 0.9))
        a = smooth(prog(t, T_OT_BACK1 + 0.3, T_OT_BACK1 + 0.5))
        return AJ.walk((t - T_OT_BACK1) * 7, STAND) if k < 1 else RELAX, hip(lerp(CAR_X - 60, x, k)), -1 if k < 1 else 1, \
            a, ("coffee" if k >= 1 else None)
    if i == 2:
        if t < T_BUS0:
            return lerp_pose(STAND, THINK, 0.7), hip(x), 1, 1, None
        if t < T_BUS1:
            k = smooth(prog(t, T_BUS0, T_BUS0 + 0.6))
            a = 1 - smooth(prog(t, T_BUS0 + 0.5, T_BUS0 + 0.8))
            return AJ.walk((t - T_BUS0) * 7, STAND), hip(lerp(x, 120, k)), -1, a, None
        if t < T_FIRED - 0.3:
            k = smooth(prog(t, T_BUS1, T_BUS1 + 0.4))
            return STAND, hip(120), 1, k, None
        if t < T_FIRED + 1.4:
            return CALL, hip(120), 1, 1, "phone_r"
        k = smooth(prog(t, T_FIRED + 1.4, T_FIRED + 1.9))
        return lerp_pose(STAND, CURB, k), (120, lerp(FY - 113 * S, FY - 60, k)), 1, 1, None
    # show-off
    for t0, item, val in SWIPES:
        if t0 - 0.3 <= t < t0 + 0.6:
            return SWIPE, hip(x), 1, 1, "card"
    if t >= SWIPES[0][0] + 0.6 and t < 12.0:
        return lerp_pose(RELAX, CHEER, 0.5 + 0.5 * math.sin(t * 6)), hip(x), 1, 1, None
    return RELAX, hip(x), 1, 1, None


def T_SALES_LAST():
    return SALES[-1][0] - 0.6


# ---------------------------------------------------------------- scenery
def car(p, cx, col, a=255, lit=0.0, broken=0.0, t=0.0, jolt=0.0):
    base = FY - 8 + jolt
    pts = [(-180, -40), (-140, -92), (-40, -118), (90, -100), (190, -64), (196, -22), (-180, -22)]
    body = [(cx + x, base + y) for x, y in pts]
    p.fill_poly(body, (22, 18, 36), a)
    p.line(body, col, 5, a, closed=True)
    p.line([(cx - 120, base - 92), (cx - 40, base - 108), (cx + 60, base - 94), (cx - 120, base - 62)], col, 3, a * 0.6)
    for wx in (cx - 110, cx + 120):
        p.ds.ellipse([(wx - 34) * K, (base - 52) * K, (wx + 34) * K, (base + 16) * K], fill=(12, 10, 20, int(a)))
        p.circle(wx, base - 18, 34, col, 5, a)
        p.circle(wx, base - 18, 12, col, 3, a * 0.6)
    if lit > 0.02:
        p.circle(cx + 188, base - 52, 9, (255, 250, 220), a=a * lit, fill=True)
        p.fill_poly([(cx + 196, base - 60), (cx + 330, base - 90), (cx + 330, base - 10), (cx + 196, base - 44)],
                    (255, 240, 180), 50 * lit * a / 255)
    if broken > 0.02 and int(t * 3) % 2 == 0:
        p.circle(cx - 10, base - 150, 20, REDC, 4, a * broken)
        p.text((cx - 10, base - 166), "!", 26, REDC, a * broken, neon=True)


def smoke(p, t, cx, k, seed):
    if k <= 0.02:
        return
    rng = np.random.default_rng(seed)
    for j in range(16):
        ph = (t * 0.45 + j / 16) % 1.0
        x = cx + 150 + rng.uniform(-20, 20) + 60 * ph * (0.5 + rng.uniform())
        y = FY - 90 - 180 * ph
        r = 14 + 34 * ph
        a = int(110 * k * (1 - ph))
        p.ds.ellipse([(x - r) * K, (y - r) * K, (x + r) * K, (y + r) * K], fill=(150, 150, 165, a))


def tag(p, x, y, label, value, col, a=255, sub=None):
    f = font(BOLD, int(36 * K))
    fl = font(BOLD, int(17 * K))
    tw = max(f.getlength(value) / K + 40, (fl.getlength(label) + 2 * K * len(label)) / K + 30, 200)
    h = 76 + (24 if sub else 0)
    p.fill_rect([x - tw, y, x, y + h], (10, 10, 18), a * 0.92, r=10)
    p.rect([x - tw, y, x, y + h], col, 3, a, r=10)
    p.text((x - tw / 2, y + 8), label, 17, (190, 194, 210), a)
    p.text((x - tw / 2, y + 30), value, 36, col, a, neon=True)
    if sub:
        p.text((x - tw / 2, y + 74), sub, 16, col, a)


def words(p, t, items, x=600, y=116):
    live = [it for it in items if it[0] <= t < it[1]]
    for t0, t1, s, c in live[-1:] if live else []:
        if True:
            k = hq.pop(t, t0, 0.28)
            a = 255 * (1 - smooth(prog(t, t1 - 0.25, t1)))
            p.text((x, y), s, 34 * max(0.3, k), c, a, neon=True)


def item_icon(p, name, x, y, col, a=255):
    if name == "GUITAR":
        p.circle(x, y + 10, 18, col, 4, a)
        p.line([(x + 12, y - 2), (x + 54, y - 40)], col, 4, a)
    elif name == "CONSOLE":
        p.rect([x - 28, y - 16, x + 28, y + 16], col, 4, a, r=6)
        p.circle(x + 14, y, 5, col, a=a, fill=True)
    elif name == "BIKE":
        p.circle(x - 24, y + 10, 16, col, 3, a)
        p.circle(x + 24, y + 10, 16, col, 3, a)
        p.line([(x - 24, y + 10), (x, y - 12), (x + 24, y + 10)], col, 3, a)
    else:
        p.line([(x, y + 20), (x, y - 10)], col, 3, a)
        p.fill_poly([(x - 18, y - 10), (x + 18, y - 10), (x + 10, y - 30), (x - 10, y - 30)], WARM, a)


def bus(p, t):
    if not (T_BUS0 + 0.2 <= t < T_BUS1 + 0.6):
        return
    k = prog(t, T_BUS0 + 0.2, T_BUS1 + 0.6)
    x = lerp(-420, PW_ + 40, k)
    col = (255, 150, 40)
    p.fill_rect([x, FY - 160, x + 380, FY - 20], (26, 20, 12), 255, r=16)
    p.rect([x, FY - 160, x + 380, FY - 20], col, 5, 255, r=16)
    for j in range(5):
        p.fill_rect([x + 20 + j * 70, FY - 140, x + 70 + j * 70, FY - 96], WARM, 200)
    for wx in (x + 70, x + 310):
        p.circle(wx, FY - 18, 26, col, 5)
    p.text((x + 190, FY - 70), "BUS 42", 26, col, 255, neon=True)


def stamp(p, t, t0, s, col, crown=False):
    if t < t0:
        return
    k = hq.pop(t, t0, 0.3)
    f = font(BOLD, int(52 * K))
    tw = (f.getlength(s) + 3 * K * len(s)) / K + 60
    w, h = tw * k, 98 * k
    if w < 10:
        return
    lay = Image.new("RGBA", (int(w * K), int(h * K)), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle([0, 0, lay.width - 1, lay.height - 1], int(14 * K * k), fill=(8, 8, 12, 238),
                         outline=col + (255,), width=int(6 * K * k))
    fs = font(BOLD, max(4, int(52 * K * k)))
    tws = sum(fs.getlength(c) for c in s) + 3 * K * k * (len(s) - 1)
    xx = lay.width / 2 - tws / 2
    for c in s:
        ld.text((xx, lay.height / 2 - 32 * K * k), c, font=fs, fill=col + (255,))
        xx += fs.getlength(c) + 3 * K * k
    lay = lay.rotate(-4, resample=Image.BICUBIC, expand=True)
    cx, cy = PW_ * 0.62, PH * 0.5
    p.top = (lay, (int(cx * K - lay.width / 2), int(cy * K - lay.height / 2)))
    if crown and k > 0.9:
        cxx, cyy = cx, cy - h / 2 - 34
        pts = [(cxx - 46, cyy + 26), (cxx - 46, cyy - 10), (cxx - 22, cyy + 8), (cxx, cyy - 22), (cxx + 22, cyy + 8),
               (cxx + 46, cyy - 10), (cxx + 46, cyy + 26)]
        p.fill_poly(pts, GOLD, 255)
        p.line(pts, GOLD, 4, 255, closed=True)


BGS = []
FRAME0 = None


def panel(t, i):
    name, col = hq.CHARS[i]
    p = hq.Panel(BGS[i])
    p.top = None
    hq.dust(p, t, 70 + i)
    jolt = 0.0
    if t < 0.6:
        jolt = 10 * math.sin((t - T_BANG) * 60) * max(0, 1 - t / 0.6)
    # ---- the car of each, and its state
    if i == 1:
        fixed = t >= T_OT_FIX
        if t < T_OT_DRIVE0:
            cx = CAR_X
        elif t < T_OT_DRIVE1:
            cx = lerp(CAR_X, PW_ + 260, hq.ease(prog(t, T_OT_DRIVE0 + 0.4, T_OT_DRIVE1)))
        elif t < T_OT_BACK0:
            cx = -9999
        else:
            cx = lerp(-260, CAR_X, hq.ease(prog(t, T_OT_BACK0, T_OT_BACK1)))
        if cx > -9000:
            car(p, cx, col, lit=1.0 if fixed else 0.0, broken=0 if fixed else 1, t=t, jolt=jolt)
        smoke(p, t, CAR_X, 1 - smooth(prog(t, T_OT_FIX, T_OT_FIX + 0.6)), 3)
    elif i == 0:
        fixed = t >= T_DOER_FIX
        car(p, CAR_X, col, lit=smooth(prog(t, T_DOER_FIX, T_DOER_FIX + 0.4)), broken=0 if fixed else 1, t=t, jolt=jolt)
        smoke(p, t, CAR_X, 1 - smooth(prog(t, T_DOER_FIX, T_DOER_FIX + 0.6)), 1)
    elif i == 2:
        car(p, CAR_X, col, broken=1, t=t, jolt=jolt)
        smoke(p, t, CAR_X, 1 - 0.6 * prog(t, 2, 12), 2)
        bus(p, t)
    else:
        fixed = t >= SWIPES[0][0] + 0.4
        car(p, CAR_X, col, lit=1.0 if fixed else 0.0, broken=0 if fixed else 1, t=t, jolt=jolt)
        smoke(p, t, CAR_X, 1 - smooth(prog(t, SWIPES[0][0] + 0.4, SWIPES[0][0] + 1.0)), 4)
    # ---- the person
    pose, hp, facing, a, prop = person(t, i)
    pts = AJ.place(pose, hp, facing, S)
    if a > 0.02:
        p.stick(pts, col, 10, 255 * a)
        hx, hy = pts["hl"]
        if prop == "phone":
            p.fill_rect([hx - 10, hy - 26, hx + 12, hy + 10], (20, 22, 30), 255 * a, r=4)
            p.rect([hx - 10, hy - 26, hx + 12, hy + 10], col, 3, 255 * a, r=4)
        elif prop == "phone_r":
            p.fill_rect([hx - 10, hy - 18, hx + 12, hy + 18], (20, 22, 30), 255, r=4)
            if int(t * 8) % 2 == 0 and t < T_FIRED + 0.3:
                p.text((hx + 40, hy - 40), ")))", 22, REDC, 255, neon=True)
        elif prop == "card":
            p.fill_rect([hx - 4, hy - 16, hx + 40, hy + 10], GOLD, 255, r=4)
        elif prop == "coffee":
            p.fill_rect([hx - 10, hy - 26, hx + 10, hy + 4], (240, 240, 236), 255, r=4)
        elif prop and prop[0] == "item":
            _, item, kt = prop
            ix = lerp(hx + 20, PW_ + 60, kt)
            iy = lerp(hy - 10, 60, kt) - 80 * math.sin(math.pi * kt)
            item_icon(p, item, ix, iy, col, 255 * (1 - kt * 0.8))
    # ---- the money tag (one counter per panel)
    if t < T_BANK[i]:
        tag(p, PW_ - 20, 20, "REPAIR", "$1,000", REDC)
    elif i == 3:
        if t < SWIPES[0][0] + 0.3:
            k = hq.pop(t, T_BANK[i], 0.3)
            tag(p, PW_ - 20, 20, "BALANCE", "$12", REDC, 255)
        else:
            dv = debt(t)
            tag(p, PW_ - 20, 20, "CARD DEBT", f"${dv:,}", REDC if dv > 1000 else GOLD, 255, sub="APR 29%")
    else:
        v = balance(t, i)
        col_v = GREEN if (i == 1 or v >= 1000) else (GOLD if v >= 400 else REDC)
        lab = "EMERGENCY FUND" if i == 1 else "BALANCE"
        tag(p, PW_ - 20, 20, lab, f"${v:,}", col_v)
    # ---- words and events (one every 2-3 s)
    ev = {0: [(T_BANK[0] + 0.9, T_BANK[0] + 2.4, "I'LL FIX IT.", col)] +
             [(t0 + 0.1, t0 + 1.4, f"SOLD! {it} ${v}", GREEN) for t0, it, v in SALES] +
             [(T_SHORT, T_SHORT + 0.7, "$80 SHORT...", REDC), (T_DOER_FIX, T_DOER_FIX + 1.4, "FIXED!", GREEN),
              (15.0, 16.4, "STARTED A FUND", col)],
          1: [(T_BANK[1] + 0.3, T_OT_PAY + 0.2, "I KNEW THIS WOULD HAPPEN.", col), (T_OT_FIX, T_OT_FIX + 1.2, "FIXED!", GREEN),
              (T_OT_BACK1 + 0.6, T_OT_BACK1 + 2.0, "ON TIME FOR WORK", GREEN), (14.2, 15.6, "REFILLING THE FUND", col)],
          2: [(T_BANK[2] + 0.9, T_BUS0, "I CAN'T AFFORD IT.", col), (T_BUS1 + 0.2, T_FIRED - 0.3, "LATE AGAIN...", REDC),
              (T_FIRED, T_FIRED + 1.6, "\"YOU'RE FIRED.\"", REDC), (13.0, 14.4, "JOB HUNTING", col),
              (16.0, 17.4, "STILL LOOKING", col)],
          3: [(T_BANK[3] + 0.9, SWIPES[0][0] + 0.6, "JUST SWIPE IT.", col)] +
             [(t0 + 0.1, t0 + 1.3, f"{it} +${v}", REDC) for t0, it, v in SWIPES[1:]]}[i]
    words(p, t, ev)
    if i in RES_T:
        s, c = RESULTS[i]
        stamp(p, t, RES_T[i], s, c, crown=(i == 1))
    p.ds.ellipse([18 * K, 20 * K, 32 * K, 34 * K], fill=col + (255,))
    p.ds.text((42 * K, 12 * K), name, font=font(BOLD, 28 * K), fill=col + (255,))
    out = p.compose()
    if p.top:
        lay, pos = p.top
        out.alpha_composite(lay.filter(ImageFilter.GaussianBlur(10 * K)), pos)
        out.alpha_composite(lay, pos)
    im = hq.downsample(out, PW_, PH)
    events = [RES_T[i], T_BANG]
    if i == 2:
        events.append(T_FIRED)
    if i == 0:
        events.append(T_DOER_FIX)
    dx, dy = hq.shake(t, events, 9)
    im = hq.camera(im, 1.0 + 0.035 * prog(t, 0, DUR), dx, dy)
    ImageDraw.Draw(im).rounded_rectangle([1, 1, PW_ - 2, PH - 2], 14, outline=col + (170,), width=3)
    return im


def frame(t):
    img = Image.new("RGBA", (W, H), (4, 4, 9, 255))
    for i in range(4):
        img.alpha_composite(panel(t, i), (PX0, panel_y(i)))
    tp = hq.Panel(Image.new("RGBA", (W * K, TITLE_H * K), (0, 0, 0, 0)))
    if t < T_L1:
        tp.text((W / 2, 24), "WHO SURVIVES A", 46, (250, 250, 252), 255)
        kk = 1 + 0.12 * max(0, 1 - t / 0.4)
        tp.text((W / 2, 84 - 6 * (kk - 1)), "$1,000 EMERGENCY?", 64 * kk, REDC, 255, neon=True)
        tp.text((W / 2, 178), f"DAY {day(t)}", 38, GOLD, 255, neon=True, spacing=6)
    else:
        for t0, s2, y in ((T_L1, LINE1, 52), (T_L2, LINE2, 140)):
            if t < t0:
                continue
            k = int(clamp((t - t0) * CPS, 0, len(s2)))
            tp.text((W / 2, y), s2[:k] + " " * (len(s2) - k), 46 if len(s2) > 24 else 54, (250, 250, 252), 255)
    tl = tp.compose(glow=0.8)
    img.alpha_composite(tl.resize((W, TITLE_H), Image.LANCZOS), (0, 0))
    rgb = hq.bloom(np.asarray(img.convert("RGB")), 0.5, 150, 26)
    if t < 0.25:
        rgb = np.clip(rgb.astype(np.float32) + 90 * (1 - t / 0.25), 0, 255).astype(np.uint8)
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
    BGS = [hq.night_bg(PW_, PH, seed=40 + i, floor_y=FY) for i in range(4)]


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


def ping(at, g, pan, fx, f=1568):
    mix_in(fx, tone(f, 0.15, (1, 0.4), a=0.002, d=0.07), at, g, pan)
    mix_in(fx, tone(f * 1.335, 0.2, (1, 0.4), a=0.002, d=0.09), at + 0.07, g, pan)


def audio():
    n = int(DUR * SR)
    mus, fx = np.zeros((n, 2)), np.zeros((n, 2))
    # HOOK: the bang - a low boom, a metal clank, a hiss of steam - and the check-engine beeps
    mix_in(fx, tone(38, 1.4, (1, 0.6, 0.3), a=0.002, d=0.7), T_BANG, 0.45)
    mix_in(fx, noise(0.5, 1, lo=60, hi=900) * env(int(0.5 * SR), 0.001, 0.2), T_BANG, 0.3)
    mix_in(fx, tone(1800, 0.25, (1, 0.7, 0.5, 0.3), a=0.001, d=0.12, sweep=900), T_BANG + 0.02, 0.06)
    mix_in(fx, noise(2.0, 2, lo=2000, hi=9000) * env(int(2.0 * SR), 0.05, 1.0), 0.2, 0.025)
    for j in range(5):
        mix_in(fx, tone(880, 0.12, (1, 0.3), a=0.002, d=0.05), 0.5 + j * 0.33, 0.05, 0.3)
    # balances: a good chime for the fund, flat blips for the rest
    for i2, tk in enumerate(T_BANK):
        if i2 == 1:
            for j, m in enumerate((76, 81, 84)):
                mix_in(fx, music.music_box(midi(m), 1.0), tk + 0.05 * j, 0.06, -0.2)
        else:
            mix_in(fx, tone(330 if i2 != 0 else 523, 0.25, (1, 0.5), a=0.002, d=0.12, sweep=260 if i2 != 0 else 523),
                   tk, 0.06, 0.2)
    # music: tense minor synth until the results, picking up as things go wrong
    bpm = 104
    beat = 60 / bpm
    six = beat / 4
    chords = [[57, 60, 64], [53, 57, 60], [50, 53, 57], [52, 56, 59]]        # Am F Dm E
    tt, i = 1.0, 0
    while tt < T_RES - 0.6:
        bi = int((tt - 1.0) / (4 * beat)) % 4
        ch = chords[bi]
        seq = [0, 1, 2, 1, 2, 0, 1, 2]
        g = 0.02 + 0.035 * prog(tt, 1.0, T_RES)
        mix_in(mus, synth(midi(ch[seq[i % 8]] + 12), 0.22, 0.45), tt, g, 0.3 if i % 2 else -0.3)
        if i % 4 == 0:
            mix_in(mus, synth(midi(ch[0] - 24), 0.4, 0.6, 5) * 1.3, tt, g * 1.3)
        i += 1
        tt += six
    b = 0
    while 1.0 + b * 4 * beat < T_RES - 0.6:
        t0 = 1.0 + b * 4 * beat
        for k, m in enumerate(chords[b % 4]):
            mix_in(mus, GS.pad(midi(m), min(4 * beat, T_RES - 0.6 - t0), 0.3, 0.6), t0, 0.028, (k - 1) * 0.4)
        for q in range(4):
            tk = t0 + q * beat
            if tk < T_RES - 0.6 and tk > 2.0:
                mix_in(mus, tone(58, 0.2, (1,), a=0.002, d=0.09, sweep=40), tk, 0.12)
        b += 1
    # events
    for k, m in enumerate((69, 73, 76)):
        mix_in(fx, synth(midi(m), 0.6, 0.4, 4), T_OT_FIX + 0.05 * k, 0.04, -0.3)
    mix_in(fx, noise(1.2, 9, lo=80, hi=800) * env(int(1.2 * SR), 0.2, 0.5), T_OT_DRIVE0 + 0.4, 0.1, 0.3)
    for t0, item, v in SALES:
        ping(t0 + 0.1, 0.05, -0.3, fx)
    mix_in(fx, tone(300, 0.5, (1, 0.5), a=0.003, d=0.3, sweep=200), T_SHORT, 0.06)
    for k, m in enumerate((72, 76, 79, 84)):
        mix_in(fx, synth(midi(m), 0.7, 0.4, 4), T_DOER_FIX + 0.06 * k, 0.045, -0.3)
    for t0, item, v in SWIPES:
        mix_in(fx, tone(1320, 0.08, (1,), a=0.001, d=0.04), t0, 0.05, 0.4)
        mix_in(fx, tone(220, 0.35, (1, 0.5), a=0.003, d=0.2, sweep=160), t0 + 0.12, 0.05, 0.4)
    mix_in(fx, noise(1.6, 12, lo=60, hi=500) * env(int(1.6 * SR), 0.3, 0.6), T_BUS0 + 0.2, 0.12, -0.2)
    for j in range(4):
        mix_in(fx, tone(1046, 0.2, (1, 0.5), a=0.003, d=0.05) + tone(1318, 0.2, (1,), a=0.003, d=0.05),
               T_FIRED - 0.6 + j * 0.25, 0.04, 0.2)
    mix_in(fx, tone(60, 1.0, (1, 0.6), a=0.003, d=0.5), T_FIRED + 0.1, 0.25)
    # riser, stamps, the winner's fanfare
    rs = noise(1.6, 7, lo=400, hi=6000) * np.linspace(0, 1, int(1.6 * SR)) ** 2
    mix_in(fx, rs, T_RES - 1.7, 0.07)
    for i2, t0 in RES_T.items():
        g = 0.24 if i2 == 1 else 0.14
        mix_in(fx, tone(70, 0.5, (1, 0.5), a=0.002, d=0.25) + 0.35 * noise(0.5, 40 + i2, lo=400, hi=5000) *
               env(int(0.5 * SR), 0.002, 0.12), t0, g)
    for j, m in enumerate((72, 76, 79, 84, 88)):
        mix_in(fx, synth(midi(m), 0.9, 0.4, 3), RES_T[1] + 0.25 + 0.08 * j, 0.04, 0.0)
    for k, m in enumerate((45, 57, 64, 69, 72, 76)):
        mix_in(mus, GS.pad(midi(m), 4.0, 0.4, 2.0), RES_T[1] + 0.6, 0.035, (k - 2.5) * 0.3)
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
    out = sys.argv[1] if len(sys.argv) > 1 else "emergency.mp4"
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
