#!/usr/bin/env python3
"""ONE MORE MATCH - Doer vs Overthinker, the split-room style (same room, same game, same day), 24 s, loops on itself.

Day 1, both have REAL BANK $500 and the same new game on the same TV. The doer plays one match ("ONE MATCH."),
turns the TV off and goes back to his laptop: clients pay, the cash pile on the floor grows, REAL BANK $500 -> $28,000.
The overthinker keeps playing and keeps buying: LEGENDARY SKIN $19.99, BATTLE PASS, LOOT BOX x10... his avatar on the
screen gets wings and a crown, his REAL BANK goes $500 -> $0 -> -$2,400, cans and pizza boxes pile up, bills come.
Day 365: his card is DECLINED and the power goes out ("...ONE MORE MATCH?"). The doer closes the laptop, turns the TV
on, buys the ULTIMATE BUNDLE ("PAID") and plays ("NOW I PLAY.").
"ONE PAID TO PLAY. / ONE GOT PAID, THEN PLAYED."

    python3 stick/game_spend.py stick/game-spend.mp4
    ONLY_FRAMES=0,2,3.6,7,12,15.2,16.4,17,21 python3 stick/game_spend.py /tmp/gs   (PNG stills)
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perfect_wave as PW  # noqa
import ai_job as AJ  # noqa  (the split-room layout, the people, the bubbles)
from perfect_wave import (MONO, clamp, env, font, lerp, lerp_pose, midi, mix_in, noise, out_back, out_cubic, prog,  # noqa
                          smooth, spaced, tone, write_wav)

W, H, FPS = 1080, 1920, 30
SR = 44100
BPM = 100
BEAT = 60 / BPM
BAR = 4 * BEAT
DUR = 10 * BAR                          # 24 s
NF = int(round(DUR * FPS))
XFADE = 0.5

PH, FY, TOP_Y0, BOT_Y0, SC = AJ.PH, AJ.FY, AJ.TOP_Y0, AJ.BOT_Y0, AJ.SC
INK, DOER, DOER_FAR, OT, OT_FAR = AJ.INK, AJ.DOER, AJ.DOER_FAR, AJ.OT, AJ.OT_FAR
GOLD, CYAN, RED, GREEN = AJ.GOLD, AJ.CYAN, AJ.RED, AJ.GREEN

# ---------------------------------------------------------------- the room: work desk left, a swivel chair, the TV right
CHAIR_X = 450
HIP = (CHAIR_X, FY - 115 * SC)
DESK_X0, DESK_X1 = 100, 352
DESK_TOP = FY - 196
LAPTOP_X = 282
TV_X, TV_W, TV_H = 846, 300, 190
TV_Y1 = FY - 190                         # bottom of the screen
PILE_X = 668                             # the cash pile (doer) / the cans and pizza boxes (overthinker)

# ---------------------------------------------------------------- timeline
T_TURN0, T_TURN1 = 3.0, 3.5              # the doer turns the TV off and swivels to the laptop
T_D0, T_D1, T_365 = 4.2, 14.2, 14.4
T_DECLINE = 14.9
T_DARK0, T_DARK1 = 16.1, 16.5            # the power goes out below
T_BACK0, T_BACK1 = 14.7, 15.2            # the doer closes the laptop and swivels to the TV
T_TVON = 15.3
T_BUY = 15.8
T_PAID = 16.15
T_L1, T_L2 = 17.6, 18.55
CPS = 24.0
LINE1, LINE2 = "ONE PAID TO PLAY.", "ONE GOT PAID, THEN PLAYED."

PURCHASES = [(1.4, "LEGENDARY SKIN", 19.99), (3.3, "1,000 COINS", 9.99), (5.0, "BATTLE PASS", 24.99),
             (5.9, "SKIN BUNDLE", 29.99),
             (6.8, "LOOT BOX x10", 49.99), (7.7, "MYTHIC WINGS", 39.99), (8.6, "5,000 COINS", 49.99),
             (9.5, "LOOT BOX x20", 99.99), (10.4, "PET DRAGON", 79.99), (11.3, "VIP PASS", 99.99),
             (12.2, "GOLD CROWN", 149.99), (13.1, "LOOT BOX x50", 249.99)]
PAYMENTS = [(5.3, 150), (6.5, 300), (7.7, 500), (8.9, 800), (10.1, 1200), (11.3, 2000), (12.5, 3000), (13.7, 5000)]
BILLS = [10.2, 11.6, 12.9, 13.8]

BUB_TOP = [(0.15, 1.3, "ONE MATCH."), (3.6, 4.6, "BACK TO WORK."), (8.0, 9.0, "NEXT CLIENT."),
           (16.3, 17.5, "NOW I PLAY.")]
BUB_BOT = [(0.3, 1.25, "JUST ONE MORE."), (1.6, 2.6, "I NEED THIS SKIN."), (6.0, 7.0, "IT'S ON SALE!"),
           (9.0, 10.2, "LAST ONE, I PROMISE."), (12.0, 13.1, "I'LL PAY IT LATER."), (15.0, 15.9, "NO NO NO!"),
           (16.6, 17.6, "...ONE MORE MATCH?")]


def day_at(t):
    if t < T_D0:
        return 1
    if t < T_365:
        return min(364, 1 + int(round(363 * prog(t, T_D0, T_D1) ** 1.25)))
    return 365


def doer_bank(t):
    if t < 4.6:
        return 500
    v = 500 + 27500 * prog(t, 4.6, T_D1) ** 1.6
    if t >= T_PAID:
        v -= 100
    return int(round(v / 10) * 10) if t < T_D1 else (28000 if t < T_PAID else 27900)


def ot_bank(t):
    if t < 1.45:
        return 500
    if t < 3.35:
        return 480
    if t < 4.6:
        return 470
    if t < T_D1:
        return int(round(470 - 2870 * prog(t, 4.6, T_D1) ** 1.15))
    return -2400


def money(v):
    return ("-$" if v < 0 else "$") + f"{abs(v):,}"


# ---------------------------------------------------------------- poses
SIT_PLAY = {"head": (14, -146), "neck": (8, -104), "el": (36, -64), "hl": (70, -72), "er": (32, -60), "hr": (64, -68),
            "kl": (58, -4), "fl": (60, 110), "kr": (52, 0), "fr": (52, 112)}
SIT_PLAY_SLUMP = dict(SIT_PLAY, head=(30, -126), neck=(18, -90), el=(40, -50), hl=(70, -60), er=(36, -48),
                      hr=(64, -56))
SIT_CHEER = dict(SIT_PLAY, el=(26, -140), hl=(40, -190), er=(20, -138), hr=(34, -186))
SIT_TYPE = AJ.SIT_TYPE
SIT_DARK = dict(SIT_PLAY_SLUMP, head=(26, -122))


def playing(pose, t, amp=4.0):
    p = dict(pose)
    j = amp * math.sin(t * 23)
    p["hl"] = (p["hl"][0] + j * 0.5, p["hl"][1] - abs(j))
    p["hr"] = (p["hr"][0] - j * 0.5, p["hr"][1] - abs(math.sin(t * 19)) * amp)
    return p


def person(t, top):
    """(pose, facing, prop) of the person in this room."""
    if top:
        if t < T_TURN0:
            return playing(SIT_PLAY, t), 1, "pad"
        if t < T_TURN1:
            k = smooth(prog(t, T_TURN0 + 0.2, T_TURN1))
            if t < T_TURN0 + 0.2:
                p = dict(SIT_PLAY, el=(50, -80), hl=(100, -92))       # reaches for the TV's button
                return p, 1, None
            return lerp_pose(SIT_PLAY, SIT_TYPE, k), (1 if k < 0.5 else -1), None
        if t < T_BACK0:
            return AJ.typing(SIT_TYPE, t), -1, None
        if t < T_BACK1:
            k = smooth(prog(t, T_BACK0 + 0.15, T_BACK1))
            return lerp_pose(SIT_TYPE, SIT_PLAY, k), (-1 if k < 0.5 else 1), ("pad" if k > 0.5 else None)
        if t < T_PAID:
            return playing(SIT_PLAY, t, 1.5), 1, "pad"
        if t < T_PAID + 0.6:
            return SIT_CHEER, 1, "pad"
        return playing(SIT_PLAY, t), 1, "pad"
    # the overthinker never leaves the chair
    if t < T_D0:
        return playing(SIT_PLAY, t), 1, "pad"
    if t < T_DECLINE:
        k = 0.8 * smooth(prog(t, T_D0, T_D1))
        return playing(lerp_pose(SIT_PLAY, SIT_PLAY_SLUMP, k), t, 3.5), 1, "pad"
    if t < T_DARK0:
        shake = 6 * math.sin(t * 40)
        p = dict(SIT_PLAY, hl=(70, -72 + shake), hr=(64, -68 - shake))
        return p, 1, "pad"
    return lerp_pose(SIT_PLAY_SLUMP, SIT_DARK, smooth(prog(t, T_DARK0, T_DARK1))), 1, "pad"


def person_sprite(pts, body, far, facing, prop):
    cv = AJ.Canvas(*PW.bbox_of(list(pts.values()), 110))
    AJ.draw_stick(cv, pts, body, far, facing)
    if prop == "pad":
        ink = INK + (255,)
        hx = (pts["hl"][0] + pts["hr"][0]) / 2
        hy = (pts["hl"][1] + pts["hr"][1]) / 2
        P = cv.P
        a, b = P((hx - 34, hy - 16)), P((hx + 34, hy + 14))
        cv.d.rounded_rectangle([a[0], a[1], b[0], b[1]], 14 * AJ.SS, fill=(236, 236, 240, 255), outline=ink,
                               width=4 * AJ.SS)
        for dx, dy in ((-16, -2), (16, -2)):
            q = P((hx + dx, hy + dy))
            cv.d.ellipse([q[0] - 6 * AJ.SS, q[1] - 6 * AJ.SS, q[0] + 6 * AJ.SS, q[1] + 6 * AJ.SS], fill=ink)
        for hand in ("hl", "hr"):
            AJ.disc(cv, pts[hand], 11 * SC + 6 * SC, ink)
            AJ.disc(cv, pts[hand], 11 * SC, body + (255,))
    return cv.done()


# ---------------------------------------------------------------- the room's things
def draw_chair(d, facing):
    ink = INK + (255,)
    sx, sy = CHAIR_X, FY - 112
    d.rounded_rectangle([sx - 50, sy - 12, sx + 50, sy + 6], 6, fill=(74, 72, 70, 255), outline=ink, width=3)
    bx = sx - 66 if facing > 0 else sx + 46
    d.rounded_rectangle([bx, sy - 150, bx + 20, sy - 6], 8, fill=(74, 72, 70, 255), outline=ink, width=3)
    d.line([(sx, sy + 6), (sx, FY - 22)], fill=(60, 60, 62, 255), width=8)
    d.line([(sx - 46, FY - 14), (sx + 46, FY - 14)], fill=(60, 60, 62, 255), width=6)
    for wx in (sx - 46, sx + 46):
        d.ellipse([wx - 9, FY - 18, wx + 9, FY], fill=(40, 40, 42, 255), outline=ink, width=2)


def draw_desk(d):
    ink = INK + (255,)
    d.rectangle([DESK_X0, DESK_TOP, DESK_X1, DESK_TOP + 16], fill=(96, 88, 80, 255), outline=ink, width=3)
    for lx in (DESK_X0 + 12, DESK_X1 - 22):
        d.rectangle([lx, DESK_TOP + 16, lx + 10, FY], fill=(70, 66, 62, 255), outline=ink, width=2)


def draw_laptop(d, open_k, lit, t, note=None):
    """A laptop on the desk, its screen turned to the viewer. open_k 0..1."""
    ink = INK + (255,)
    x = LAPTOP_X
    d.rounded_rectangle([x - 70, DESK_TOP - 10, x + 70, DESK_TOP], 3, fill=(130, 134, 144, 255), outline=ink, width=2)
    if open_k < 0.05:
        return
    h = 112 * open_k
    d.rounded_rectangle([x - 66, DESK_TOP - 10 - h, x + 62, DESK_TOP - 10], 6, fill=(130, 134, 144, 255), outline=ink,
                        width=3)
    if lit and open_k > 0.8:
        d.rectangle([x - 58, DESK_TOP - 4 - h, x + 54, DESK_TOP - 16], fill=(28, 60, 98, 255))
        for i in range(6):
            y = DESK_TOP - h + 4 + i * 14
            L = 24 + 50 * abs(math.sin(i * 1.9 + int(t * 5) * 0.6))
            d.line([(x - 50, y), (x - 50 + L, y)], fill=(140, 210, 255, 255), width=4)


def draw_cash(d, h):
    """Bundles of cash stacked on the floor; h = height in px."""
    ink = INK + (255,)
    n = int(h / 15)
    rng = np.random.default_rng(4)
    cols = 3 if h > 80 else (2 if h > 30 else 1)
    for c in range(cols):
        y = FY
        m = n - c * 3
        for i in range(max(0, m)):
            w = 64
            x = PILE_X - 100 + c * 70 + rng.uniform(-3, 3)
            d.rectangle([x, y - 15, x + w, y], fill=(110, 178, 104, 255), outline=ink, width=2)
            d.rectangle([x + 24, y - 15, x + 38, y], fill=(232, 222, 170, 255), outline=ink, width=1)
            y -= 15


def draw_junk(d, k, t):
    """Pizza boxes and cans at the overthinker's feet, more and more."""
    ink = INK + (255,)
    nbox = int(9 * k)
    y = FY
    for i in range(nbox):
        x = PILE_X - 96 + ((i * 13) % 11 - 5)
        d.rectangle([x, y - 14, x + 96, y], fill=(198, 160, 110, 255), outline=ink, width=2)
        d.ellipse([x + 38, y - 12, x + 58, y - 3], fill=(214, 80, 60, 255))
        y -= 14
    rng = np.random.default_rng(8)
    ncan = int(16 * k)
    for i in range(ncan):
        x = PILE_X + 10 + rng.uniform(0, 80)
        yy = FY - (i % 4) * 30
        col = [(70, 200, 120), (220, 70, 80), (70, 140, 230)][i % 3]
        d.rounded_rectangle([x, yy - 30, x + 17, yy], 3, fill=col + (255,), outline=ink, width=2)


def draw_bills(d, t):
    for i, tb in enumerate(BILLS):
        if t < tb:
            continue
        u = out_cubic(prog(t, tb, tb + 0.3))
        x = 120 + i * 58
        y = lerp(FY - 160, FY - 12, u)
        ang = (-1) ** i * 0.2
        w, h = 66, 32
        pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
        pts = [(x + px * math.cos(ang) - py * math.sin(ang), y + px * math.sin(ang) + py * math.cos(ang)) for px, py in pts]
        d.polygon(pts, fill=(220, 54, 50, 255), outline=INK + (255,))
        d.text((x - 20, y - 11), "DUE", font=font("Inter-Bold.otf", 20), fill=(255, 255, 255, 255))


def draw_tv_frame(d):
    ink = INK + (255,)
    x0, y0 = TV_X - TV_W / 2, TV_Y1 - TV_H
    d.rectangle([TV_X - 8, TV_Y1, TV_X + 8, FY - 10], fill=(54, 54, 58, 255))
    d.rectangle([TV_X - 60, FY - 12, TV_X + 60, FY], fill=(54, 54, 58, 255))
    d.rounded_rectangle([x0 - 10, y0 - 10, x0 + TV_W + 10, TV_Y1 + 10], 8, fill=(36, 38, 44, 255), outline=ink, width=3)
    return x0, y0


def avatar(d, x, y, t, level, run=True):
    """The little game hero; level adds the skin, wings, the crown."""
    ink = INK + (255,)
    body = PW.lerp_c((240, 240, 240), (255, 200, 60), clamp(level / 3))
    if level >= 4:
        for s in (-1, 1):
            fl = 6 * math.sin(t * 14)
            d.polygon([(x, y - 30), (x - s * 34, y - 52 - fl), (x - s * 26, y - 22)], fill=(170, 120, 255, 255),
                      outline=ink)
    ph = t * 16 if run else 0
    d.line([(x, y - 34), (x, y - 12)], fill=body + (255,), width=5)
    for s in (-1, 1):
        d.line([(x, y - 12), (x + s * 9 * math.sin(ph) + s * 3, y + 4)], fill=body + (255,), width=5)
        d.line([(x, y - 28), (x + s * 12, y - 18 - 4 * s * math.sin(ph))], fill=body + (255,), width=4)
    d.ellipse([x - 9, y - 52, x + 9, y - 34], fill=body + (255,), outline=ink, width=2)
    if level >= 2:
        d.line([(x - 9, y - 30), (x - 20, y - 20 + 3 * math.sin(t * 9))], fill=(230, 60, 60, 255), width=5)   # cape
    if level >= 5:
        d.polygon([(x - 10, y - 50), (x - 12, y - 64), (x - 4, y - 56), (x, y - 66), (x + 4, y - 56), (x + 12, y - 64),
                   (x + 10, y - 50)], fill=(255, 210, 60, 255), outline=ink)
    if level >= 3:
        d.ellipse([x + 16 + 6 * math.sin(t * 5), y - 30, x + 30 + 6 * math.sin(t * 5), y - 18], fill=(240, 90, 60, 255))


def draw_tv(d, im, t, top):
    x0, y0 = draw_tv_frame(d)
    x1 = x0 + TV_W
    if top:
        on = t < T_TURN0 + 0.15 or t >= T_TVON
    else:
        on = t < T_DARK0
    if not on:
        d.rectangle([x0, y0, x1, TV_Y1], fill=(14, 15, 20, 255))
        d.line([(x0 + 30, y0 + 20), (x0 + 90, y0 + 60)], fill=(34, 36, 44, 255), width=6)
        return
    # the game: a night city road, our hero runs
    d.rectangle([x0, y0, x1, TV_Y1], fill=(24, 44, 92, 255))
    for i in range(6):
        bx = x0 + ((i * 60 - t * 40) % (TV_W + 40)) - 20
        bh = 40 + (i * 37) % 60
        if min(x1, bx + 40) > max(x0, bx):
            d.rectangle([max(x0, bx), TV_Y1 - 46 - bh, min(x1, bx + 40), TV_Y1 - 46], fill=(16, 28, 60, 255))
    d.rectangle([x0, TV_Y1 - 46, x1, TV_Y1], fill=(40, 44, 54, 255))
    for i in range(5):
        lx = x0 + ((i * 70 - t * 160) % (TV_W + 60)) - 30
        if min(x1, lx + 30) > max(x0, lx):
            d.line([(max(x0, lx), TV_Y1 - 24), (min(x1, lx + 30), TV_Y1 - 24)], fill=(230, 230, 230, 255), width=4)
    spaced(d, x0 + 46, y0 + 8, "SEASON 1", font(MONO, 15), (170, 210, 255, 255), 1)
    if top:
        level = 5 if t >= T_PAID else 0
    else:
        level = sum(1 for p in PURCHASES if t >= p[0] + 0.5) // 2 if t < T_D1 + 1 else 5
        level = 5 if t > 13.0 else level
    avatar(d, x0 + 90, TV_Y1 - 46, t, level)
    # title card on day 1
    if t < 0.6:
        fb = font("InterDisplay-Bold.otf", 44)
        d.rectangle([x0, y0, x1, TV_Y1], fill=(10, 16, 40, 230))
        spaced(d, TV_X, y0 + 34, "NEW GAME", fb, (255, 214, 90, 255), 3)
        spaced(d, TV_X, y0 + 98, "OUT NOW", font(MONO, 26), (220, 230, 255, 255), 3)
    # the shop
    card = None
    if not top:
        for t0, name, price in PURCHASES:
            if t0 - 0.35 <= t < t0 + 0.55:
                card = (t0, name, f"${price:.2f}", "BUY")
        if T_DECLINE - 0.4 <= t < T_DARK0:
            card = (T_DECLINE, "ULTIMATE BUNDLE", "$99.99", "DECLINED")
    elif T_BUY - 0.4 <= t < T_PAID + 0.7:
        card = (T_PAID, "ULTIMATE BUNDLE", "$99.99", "PAID")
    if card:
        t0, name, price, state = card
        sc = out_back(prog(t, t0 - 0.35, t0 - 0.2))
        cw, ch = 220 * sc, 140 * sc
        cx0, cy0 = TV_X - cw / 2, y0 + (TV_H - ch) / 2
        d.rounded_rectangle([cx0, cy0, cx0 + cw, cy0 + ch], 10, fill=(250, 248, 240, 255), outline=INK + (255,),
                            width=3)
        if sc > 0.9:
            spaced(d, TV_X, cy0 + 12, name, font(MONO, 17), INK + (255,), 1)
            spaced(d, TV_X, cy0 + 38, price, font("InterDisplay-Bold.otf", 36), (40, 40, 48, 255), 1)
            pressed = t >= t0
            if state == "BUY":
                bc = (60, 180, 90) if not pressed else (40, 130, 60)
                label = "BUY" if not pressed else "BOUGHT"
            elif state == "DECLINED":
                bc = RED if (not pressed or int(t * 8) % 2 == 0) else (150, 40, 40)
                label = "BUY" if not pressed else "CARD DECLINED"
                if not pressed:
                    bc = (60, 180, 90)
            else:
                bc = (60, 180, 90) if not pressed else (40, 150, 80)
                label = "BUY" if not pressed else "PAID ✓"
            d.rounded_rectangle([cx0 + 18, cy0 + 90, cx0 + cw - 18, cy0 + 126], 8, fill=bc + (255,))
            spaced(d, TV_X, cy0 + 96 + (3 if len(label) > 10 else 0), label,
                   font("Inter-Bold.otf", 16 if len(label) > 10 else 21), (255, 255, 255, 255), 1 if len(label) > 10 else 2)


def bank_box(d, value, t, floats, red_when_negative=True):
    x0, y0, bw, bh = 40, 18, 300, 92
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], 8, fill=(22, 24, 30, 235), outline=(90, 94, 104, 255), width=2)
    spaced(d, x0 + bw / 2, y0 + 10, "REAL BANK", font("Inter-SemiBold.otf", 22), (190, 194, 204, 255), 6)
    col = RED if value <= 0 and red_when_negative else GOLD
    spaced(d, x0 + bw / 2, y0 + 40, money(value), font(MONO, 40), col + (255,), 1)
    for t0, txt, c in floats:
        if t0 <= t < t0 + 1.0:
            u = prog(t, t0, t0 + 1.0)
            a = int(255 * (1 - smooth(prog(u, 0.55, 1.0))))
            spaced(d, x0 + bw + 96, y0 + 34 - 34 * out_cubic(u), txt, font(MONO, 32), c + (a,), 1)


def bubbles(im, t, lst, head):
    for b0, b1, s in lst:
        if not (b0 <= t < b1) or head is None:
            continue
        bs = AJ.bubble(s)
        sc = out_back(prog(t, b0, b0 + 0.16))
        al = 1 - smooth(prog(t, b1 - 0.1, b1))
        if sc < 0.05:
            continue
        spr = bs.resize((max(1, int(bs.width * sc)), max(1, int(bs.height * sc))), Image.LANCZOS)
        if al < 0.999:
            spr.putalpha(spr.split()[3].point(lambda v: int(v * al)))
        x = clamp(head[0] - spr.width / 2 + 40, 16, W - 16 - spr.width)
        y = max(122, head[1] - 52 - spr.height)
        im.alpha_composite(spr, (int(x), int(y)))


# ---------------------------------------------------------------- one frame
ROOM = None
FRAME0 = None


def panel(t, top):
    im = ROOM.copy()
    d = ImageDraw.Draw(im)
    pose, facing, prop = person(t, top)
    draw_desk(d)
    if top:
        k = 1.0
        if t < T_TURN1:
            k = 0.0 if t < T_TURN0 + 0.3 else smooth(prog(t, T_TURN0 + 0.3, T_TURN1))
        if t >= T_BACK0:
            k = 1 - smooth(prog(t, T_BACK0, T_BACK0 + 0.3))
        draw_laptop(d, k, True, t)
        draw_cash(d, 230 * clamp((doer_bank(t) - 500) / 27500))
    else:
        draw_laptop(d, 0.0, False, t)
        draw_junk(d, smooth(prog(t, 3.5, T_D1)), t)
        draw_bills(d, t)
    draw_tv(d, im, t, top)
    draw_chair(d, facing)
    pts = AJ.place(pose, HIP, facing)
    spr, off = person_sprite(pts, DOER if top else OT, DOER_FAR if top else OT_FAR, facing, prop)
    if top:
        im.alpha_composite(PW.glow_of(spr, 0.5, 12), off)
    im.alpha_composite(spr, off)
    # money boxes and the floats
    if top:
        fl = [(t0, f"+${a:,}", GREEN) for t0, a in PAYMENTS] + [(T_PAID, "-$100", (255, 170, 150))]
        bank_box(d, doer_bank(t), t, fl, red_when_negative=False)
        # "CLIENT PAID" over the laptop
        for t0, a in PAYMENTS:
            if t0 <= t < t0 + 0.9:
                u = prog(t, t0, t0 + 0.9)
                al = int(255 * (1 - smooth(prog(u, 0.6, 1.0))))
                y = DESK_TOP - 150 - 40 * out_cubic(u)
                d.rounded_rectangle([LAPTOP_X - 92, y, LAPTOP_X + 92, y + 40], 8, fill=(30, 120, 70, al))
                spaced(d, LAPTOP_X, y + 8, f"CLIENT PAID +${a:,}", font(MONO, 16), (255, 255, 255, al), 1)
    else:
        fl = [(t0 + 0.05, f"-${p:.2f}", (255, 120, 110)) for t0, n, p in PURCHASES]
        bank_box(d, ot_bank(t), t, fl)
    bubbles(im, t, BUB_TOP if top else BUB_BOT, pts["head"])
    if not top and t >= T_DARK0:
        # the power goes out: lights flicker, then the room is dark
        if t < T_DARK1:
            k = 0.85 if int(t * 22) % 2 == 0 else 0.25
        else:
            k = 0.82
        a = np.asarray(im).astype(np.float32)
        a[..., :3] *= (1 - k)
        im = Image.fromarray(a.astype(np.uint8), "RGBA")
        d = ImageDraw.Draw(im)
        if t >= T_DARK1:
            bank_box(d, ot_bank(t), t, [])
            spaced(d, 760, 30, "POWER CUT", font("Inter-Bold.otf", 30), RED + (255,), 4)
            bubbles(im, t, [b for b in BUB_BOT if b[0] >= T_DARK0], pts["head"])
    return im


def frame(t):
    img = Image.new("RGBA", (W, H), (6, 6, 8, 255))
    img.alpha_composite(panel(t, True), (0, TOP_Y0))
    img.alpha_composite(panel(t, False), (0, BOT_Y0))
    d = ImageDraw.Draw(img)
    spaced(d, W / 2, 268, "DOER", font("Inter-SemiBold.otf", 40), (236, 238, 244, 255), 10)
    spaced(d, W / 2, BOT_Y0 + PH + 18, "OVERTHINKER", font("Inter-SemiBold.otf", 40), (200, 204, 214, 255), 10)
    spaced(d, W / 2, TOP_Y0 + PH + 18, "SAME GAME", font("Inter-SemiBold.otf", 34), (206, 210, 220, 255), 8)
    day = day_at(t)
    dpop = math.exp(-(t - T_365) * 6) if t >= T_365 else 0.0
    fl = font("Inter-SemiBold.otf", 40)
    fn = font("InterDisplay-Bold.otf", int(56 * (1 + 0.3 * dpop)))
    wl = sum(fl.getlength(c) for c in "DAY") + 16
    wn = fn.getlength(str(day))
    x0 = W / 2 - (wl + 20 + wn) / 2
    spaced(d, x0 + wl / 2, TOP_Y0 + PH + 66, "DAY", fl, (206, 210, 220, 255), 8)
    d.text((x0 + wl + 20, TOP_Y0 + PH + 52 - 8 * dpop), str(day), font=fn,
           fill=PW.lerp_c((250, 250, 252), (255, 120, 110), dpop) + (255,))
    d.line([(60, BOT_Y0 - 8), (W - 60, BOT_Y0 - 8)], fill=(50, 52, 60, 255), width=2)
    fm = font(MONO, 50)
    for t0, s, y, col in ((T_L1, LINE1, 92, (250, 250, 252)), (T_L2, LINE2, 164, GOLD)):
        if t < t0:
            continue
        n = int(clamp((t - t0) * CPS, 0, len(s)))
        full = sum(fm.getlength(c) for c in s) + 3 * (len(s) - 1)
        x = W / 2 - full / 2
        for c in s[:n]:
            d.text((x, y), c, font=fm, fill=col + (255,))
            x += fm.getlength(c) + 3
        if (n < len(s) or (s == LINE2 and t < t0 + len(s) / CPS + 1.0)) and int(t * 3.4) % 2 == 0:
            d.rectangle([x + 2, y + 6, x + 26, y + 56], fill=col + (220,))
    return np.asarray(img.convert("RGB"))


def init_worker():
    global ROOM
    ROOM = AJ.build_room()


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
def audio():
    n = int(DUR * SR)
    mus, fx = np.zeros((n, 2)), np.zeros((n, 2))
    chords = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]]
    roots = [41, 40, 38, 36]
    for b in range(6):                       # the year, bars 0-5 (to 14.4 s)
        t0 = b * BAR
        ch, rt = chords[b % 4], roots[b % 4]
        for k, m in enumerate(ch):
            mix_in(mus, tone(midi(m), BAR + 0.1, (1, 0.35, 0.12, 0.05), a=0.02, d=1.2), t0, 0.05, (k - 1.5) * 0.35)
        for q in range(4):
            tb = t0 + q * BEAT
            mix_in(mus, tone(105, 0.32, (1,), a=0.002, d=0.11, sweep=42), tb, 0.55 if q % 2 == 0 else 0.3)
            mix_in(mus, tone(midi(rt), BEAT * 0.9, (1, 0.4, 0.1), a=0.005, d=0.3), tb, 0.2)
            if q % 2 == 1:
                mix_in(mus, noise(0.12, 900 + b * 4 + q, lo=900, hi=5000) * env(int(0.12 * SR), 0.001, 0.03), tb, 0.14)
            for e in range(2):
                mix_in(mus, noise(0.04, 300 + b * 8 + q * 2 + e, lo=6000) * env(int(0.04 * SR), 0.0005, 0.008),
                       tb + e * BEAT / 2, 0.045, 0.4 - 0.8 * e)
            if (b * 4 + q) % 3 != 2:
                m = ch[(q * 2 + b) % 4] + 12
                mix_in(mus, tone(midi(m), 0.5, (1, 0.25, 0.08), a=0.004, d=0.18), tb + BEAT / 2, 0.065, 0.2)
    # day 365 to the end: the beat thins out, then the line on soft chords (bars 6-9)
    tt = np.arange(int(3.0 * SR)) / SR
    mix_in(mus, (np.sin(2 * np.pi * 55 * tt) + 0.4 * np.sin(2 * np.pi * 110 * tt)) * np.minimum(1, tt / 0.4)
           * np.clip((3.0 - tt) / 0.6, 0, 1), 14.4, 0.12)
    for b in range(4):
        t0 = 6 * BAR + b * BAR
        ch, rt = chords[(b + 2) % 4], roots[(b + 2) % 4]
        for k, m in enumerate(ch):
            mix_in(mus, tone(midi(m), BAR + 0.3, (1, 0.3, 0.1), a=0.2, d=1.5), t0, 0.06 if b else 0.03, (k - 1.5) * 0.4)
        mix_in(mus, tone(midi(rt), BAR, (1, 0.3), a=0.08, d=1.2), t0, 0.16)
        if b >= 1:
            for q in range(4):
                mix_in(mus, tone(105, 0.3, (1,), a=0.002, d=0.1, sweep=42), t0 + q * BEAT, 0.3 if q % 2 == 0 else 0.18)
    # game blips while they play
    r = np.random.default_rng(2)
    for tb in np.arange(0.1, T_DARK0, 0.3):
        if r.uniform() < 0.6:
            mix_in(fx, tone(midi(int(r.choice([72, 76, 79, 84]))), 0.06, (1, 0.5, 0.3), a=0.001, d=0.03), tb, 0.035, 0.3)
    # every purchase: a "buy" chime, then the money going (a falling coin)
    for t0, name, p in PURCHASES:
        mix_in(fx, tone(midi(84), 0.08, (1, 0.3), a=0.001, d=0.04), t0, 0.08, 0.3)
        mix_in(fx, tone(midi(79), 0.35, (1, 0.4), a=0.002, d=0.15, sweep=midi(67)), t0 + 0.06, 0.08, 0.3)
    # every payment: a cash register
    for t0, a in PAYMENTS:
        for i, m in enumerate((88, 95)):
            mix_in(fx, tone(midi(m), 0.4, (1, 0.3), a=0.002, d=0.16), t0 + i * 0.07, 0.08, -0.3)
        mix_in(fx, noise(0.1, int(t0 * 10), lo=3000, hi=9000) * env(int(0.1 * SR), 0.001, 0.03), t0, 0.06, -0.3)
    # the TV clicks off, the laptop opens / closes
    for tc in (T_TURN0 + 0.15, T_BACK0, T_TVON):
        mix_in(fx, tone(1800, 0.03, (1,), a=0.0005, d=0.01), tc, 0.15)
    # declined: a buzzer x2; the power cut: a falling hum, then quiet
    for i in range(2):
        mix_in(fx, tone(150, 0.22, (1, 0.6, 0.4, 0.3, 0.2), a=0.003, d=0.15), T_DECLINE + i * 0.28, 0.22, 0.3)
    td = np.arange(int(0.9 * SR)) / SR
    hum = np.sin(2 * np.pi * np.cumsum(220 * (1 - td / 1.0) + 30) / SR) * np.clip(1 - td / 0.9, 0, 1)
    mix_in(fx, hum, T_DARK0, 0.18, 0.3)
    # paid: a bright chord
    for i, m in enumerate((76, 81, 84, 88)):
        mix_in(fx, tone(midi(m), 0.7, (1, 0.3), a=0.003, d=0.3), T_PAID + i * 0.04, 0.07, -0.3)
    # bubbles, typewriter
    for lst in (BUB_TOP, BUB_BOT):
        for b0, b1, s in lst:
            mix_in(fx, tone(560, 0.11, (1, 0.3), a=0.002, d=0.05, sweep=1100), b0, 0.1)
    for t0, s in ((T_L1, LINE1), (T_L2, LINE2)):
        for i, c in enumerate(s):
            if c != " ":
                mix_in(fx, noise(0.03, 500 + i + int(t0), lo=2000, hi=8000) * env(int(0.03 * SR), 0.0005, 0.006),
                       t0 + i / CPS, 0.12)
    x = mus * 0.9 + fx
    m = int(XFADE * SR)
    k = np.linspace(0, 1, m)[:, None]
    x[-m:] = x[-m:] * (1 - k) + x[:m] * k
    x /= max(1.0, np.abs(x).max() / 0.9)
    return x


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "game-spend.mp4"
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
