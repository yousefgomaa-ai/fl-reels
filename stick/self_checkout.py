#!/usr/bin/env python3
"""SELF-CHECKOUT vs CASHIER - one supermarket, a moving camera. 20.5 s, loops.

Hook (frame 0): close on the self-checkout - the red light is already flashing, the alarm is going, and the machine
says UNEXPECTED ITEM IN BAGGING AREA. The orange guy throws his arms up.
Whip to the cashier lane: the cyan guy waits behind one shopper; the cashier scans beep-beep-beep.
Back at the machine: red again. HELP IS ON THE WAY. Whip: the cyan guy pays. Back: the attendant fixes it, then
PLACE ITEM IN BAG / REMOVE ITEM FROM BAG / PLACE ITEM IN BAG ... then ID CHECK REQUIRED.
Twist (~60%): the camera glides right - the cashier lane is empty, the cashier waves NEXT!, and through the glass the
cyan guy is already loading his car: DONE IN 5 MIN. Whip back: STILL HERE. 12 MIN.
"THE CASHIER LINE WAS FASTER. / WHICH ONE DO YOU PICK?"

    python3 stick/self_checkout.py stick/self-checkout.mp4
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
import ai_job as AJ  # noqa
import game_spend as GS  # noqa
import music  # noqa
import hq  # noqa
import airport as AP  # noqa  (scene helpers: SafePanel, gray_person, stick, say, stamp, synth, whoosh)
from perfect_wave import clamp, env, font, lerp, lerp_pose, midi, mix_in, noise, prog, smooth, spaced, tone, write_wav  # noqa

W, H, FPS = 1080, 1920, 30
SR = 44100
DUR = 20.5
NF = int(round(DUR * FPS))
XFADE = 0.5
K = hq.K
FLOOR = AP.FLOOR
S = AP.S
HIP_Y = AP.HIP_Y
SELF = (255, 150, 40)        # the self-checkout guy
CASH = (60, 220, 255)        # the cashier-line guy
GOLD, GREEN, REDC, WARM = AP.GOLD, AP.GREEN, AP.REDC, AP.WARM
YEL = (255, 210, 60)
TITLE_H = 300
MUSIC = "marimba_f"

# world layout (x)
KIOSK_X = 1000               # his machine (two more beside it)
BAG_X = KIOSK_X + 190
ORANGE_X = KIOSK_X - 170
LANE_X = 2250                # cashier's register
BELT = (1820, 2200)
CASHIER_X = 2380
CYAN_LINE = [1760, 1900, 2060]   # waiting, next, paying
EXIT_X = 2850                # glass front
CAR_X = 3250
CYAN_OUT = 3060

# timeline
T_ERR = [0.0, 3.9, 11.0]     # red alarms: unexpected item, unexpected item, ID check
T_WHIP1 = 1.5                # -> cashier lane
T_WHIP2 = 3.3                # -> kiosk
T_HELP = 4.3                 # HELP IS ON THE WAY
T_WHIP3 = 5.6                # -> cashier: he pays
T_PAY = 6.2
T_WHIP4 = 7.2                # -> kiosk: attendant, then the bag loop
T_ATT0, T_ATT1 = 7.0, 8.4
T_LOOP = 8.7                 # PLACE / REMOVE / PLACE / REMOVE
T_ID = 11.0
T_PAN = 12.2                 # twist: glide right to the empty lane and the car park
T_DONE = 13.4
T_BACK = 14.6                # whip back to him
T_STILL = 15.1
T_WIDE = 16.3
T_L1, T_L2 = 16.8, 17.9
CPS = 18.0
LINE1, LINE2 = "THE CASHIER LINE WAS FASTER.", "WHICH ONE DO YOU PICK?"
T_FOLLOW = 19.1


def timer_s(t):
    keys = [(0, 40), (T_WHIP2, 120), (T_WHIP3, 230), (T_PAY + 0.6, 300), (T_WHIP4, 330), (T_ID, 560),
            (T_PAN, 620), (T_STILL, 720), (DUR, 800)]
    for (a, va), (b, vb) in zip(keys, keys[1:]):
        if t <= b:
            return lerp(va, vb, prog(t, a, b))
    return keys[-1][1]


def machine_msg(t):
    """what the self-checkout says, and its light colour"""
    if t < 1.3:
        return "UNEXPECTED ITEM IN BAGGING AREA", REDC
    if t < T_ERR[1] - 0.6:
        return "SCAN YOUR NEXT ITEM", GREEN
    if t < T_HELP:
        return "UNEXPECTED ITEM IN BAGGING AREA", REDC
    if t < T_ATT1:
        return "HELP IS ON THE WAY", YEL
    if t < T_LOOP:
        return "SCAN YOUR NEXT ITEM", GREEN
    if t < T_ID:
        j = int((t - T_LOOP) / 0.55)
        return ("PLACE ITEM IN BAG", "REMOVE ITEM FROM BAG")[j % 2], REDC
    if t < T_BACK + 0.4:
        return "ID CHECK REQUIRED", YEL
    return "UNEXPECTED ITEM IN BAGGING AREA", REDC


# ---------------------------------------------------------------- camera
def cam(t):
    def kiosk(z):
        return lambda u: (KIOSK_X + 60, 1100, z + 0.04 * math.sin(u * 0.7))

    def lane(u):
        return LANE_X - 120, 1130, 1.38

    def pan(u):
        k = smooth(prog(u, T_PAN, T_DONE))
        return lerp(KIOSK_X + 60, CYAN_OUT - 60, k), lerp(1100, 1130, k), lerp(1.45, 1.25, k)

    def back(u):
        return KIOSK_X + 20, 1090, lerp(1.6, 1.75, prog(u, T_BACK, T_WIDE))

    def wide(u):
        k = smooth(prog(u, T_WIDE, T_WIDE + 1.6))
        return lerp(KIOSK_X + 20, 1500, k), lerp(1090, 900, k), lerp(1.75, 0.68, k)

    segs = [(0, kiosk(1.55)), (T_WHIP1, lane), (T_WHIP2, kiosk(1.45)), (T_WHIP3, lane), (T_WHIP4, kiosk(1.45)),
            (T_PAN, pan), (T_BACK, back), (T_WIDE, wide)]
    whips = {T_WHIP1: 0.34, T_WHIP2: 0.34, T_WHIP3: 0.34, T_WHIP4: 0.34, T_BACK: 0.34}
    cur_i = 0
    for i, (ts, fn) in enumerate(segs):
        if t >= ts:
            cur_i = i
    ts, fn = segs[cur_i]
    a = fn(t)
    d = whips.get(ts, 0)
    if d and t < ts + d and cur_i > 0:
        prev = segs[cur_i - 1][1](ts)
        k = smooth(smooth(prog(t, ts, ts + d)))
        a = tuple(lerp(p_, q_, k) for p_, q_ in zip(prev, a))
    cx, cy, z = a
    cx += 5 * math.sin(t * 1.7) + 3 * math.sin(t * 4.3 + 1)
    cy += 4 * math.sin(t * 2.1 + 2) + 2 * math.sin(t * 5.1)
    return cx, cy, z


WHIPS = (T_WHIP1, T_WHIP2, T_WHIP3, T_WHIP4, T_BACK)


class View(AP.View):
    def __init__(self, t):
        self.cx, self.cy, self.z = cam(t)


# ---------------------------------------------------------------- poses
STAND = PW.STAND
SCAN = dict(STAND, el=(34, -88), hl=(84, -96), er=(30, -80), hr=(76, -88))
ARMS_UP = dict(STAND, head=(-4, -152), el=(-30, -128), hl=(-44, -180), er=(30, -128), hr=(44, -180))
TO_BAG = dict(STAND, el=(40, -80), hl=(96, -64), er=(36, -76), hr=(92, -60))
FROM_BAG = dict(STAND, el=(20, -80), hl=(40, -100), er=(16, -76), hr=(36, -96))
HEAD_DOWN = {"head": (60, -120), "neck": (40, -92), "el": (70, -96), "hl": (96, -110), "er": (64, -92),
             "hr": (92, -106), "kl": (-9, 56), "fl": (-13, 113), "kr": (9, 56), "fr": (13, 113)}
WAIT = dict(STAND, el=(-26, -70), hl=(-4, -40), er=(26, -70), hr=(4, -40))
CARD = dict(STAND, el=(34, -92), hl=(74, -106))
WAVE = dict(STAND, el=(30, -128), hl=(46 + 0, -178), er=(10, -58), hr=(14, -10))
LOAD = dict(STAND, el=(36, -84), hl=(80, -70), er=(32, -80), hr=(76, -66))


def orange_state(t):
    """pose, x, prop"""
    x = ORANGE_X
    if t < 1.3:
        k = math.sin(math.pi * prog(t, 0.0, 1.3)) * 0.8 + 0.2
        return lerp_pose(SCAN, ARMS_UP, k), x, None
    if t < T_ERR[1]:
        ph = (t * 2.2) % 1
        return lerp_pose(SCAN, STAND, 0.5 - 0.5 * math.cos(ph * 6.28)), x, "item"
    if t < T_HELP:
        return lerp_pose(STAND, ARMS_UP, smooth(prog(t, T_ERR[1], T_ERR[1] + 0.2))), x, None
    if t < T_ATT1:
        return WAIT, x, None
    if t < T_LOOP:
        return SCAN, x, "item"
    if t < T_ID:
        j = int((t - T_LOOP) / 0.55)
        u = ((t - T_LOOP) / 0.55) % 1
        a, b = (TO_BAG, FROM_BAG) if j % 2 == 0 else (FROM_BAG, TO_BAG)
        return lerp_pose(a, b, smooth(clamp(u * 3))), x, "item"
    if t < T_BACK:
        return lerp_pose(STAND, ARMS_UP, smooth(prog(t, T_ID, T_ID + 0.2))), x, None
    return lerp_pose(STAND, HEAD_DOWN, smooth(prog(t, T_BACK + 0.2, T_BACK + 0.7))), x, None


def cyan_state(t):
    """pose, x, facing, prop"""
    if t < T_WHIP3 - 0.3:
        x = lerp(CYAN_LINE[0], CYAN_LINE[1], smooth(prog(t, 2.2, 2.9)))
        return WAIT, x, 1, None
    if t < T_PAY + 0.8:
        x = lerp(CYAN_LINE[1], CYAN_LINE[2], smooth(prog(t, T_WHIP3 - 0.3, T_WHIP3 + 0.2)))
        return (CARD if t >= T_PAY else WAIT), x, 1, ("card" if t >= T_PAY else None)
    if t < T_PAY + 2.4:
        k = prog(t, T_PAY + 0.8, T_PAY + 2.4)
        return AJ.walk(t * 9, STAND), lerp(CYAN_LINE[2], CYAN_OUT, k), 1, "bag"
    return (LOAD if t < T_DONE else WAVE), CYAN_OUT, -1 if t >= T_DONE else 1, None


# ---------------------------------------------------------------- the store
def kiosk(p, v, x, t, mine):
    z = v.z
    msg, col = machine_msg(t) if mine else ("", GREEN)
    flash = mine and col != GREEN and int(t * 6) % 2 == 0
    # pole light
    p.line(v.pts([(x - 70, FLOOR - 560), (x - 70, FLOOR - 760)]), (120, 126, 156), 6 * z, 255)
    lc = col if mine else GREEN
    p.circle(v.x(x - 70), v.y(FLOOR - 790), 30 * z, lc if (flash or not mine or col == GREEN) else (60, 30, 30),
             a=255, fill=True)
    if flash:
        p.circle(v.x(x - 70), v.y(FLOOR - 790), 70 * z, lc, 6 * z, 160)
    # body, screen, scanner
    p.fill_rect(v.box([x - 120, FLOOR - 330, x + 120, FLOOR]), (24, 26, 44), 255, r=10 * z)
    p.rect(v.box([x - 120, FLOOR - 330, x + 120, FLOOR]), (150, 160, 210), 4 * z, 230, r=10 * z)
    p.fill_rect(v.box([x - 110, FLOOR - 560, x + 110, FLOOR - 380]), (8, 10, 20), 255, r=8 * z)
    sc = col if mine else (90, 200, 140)
    p.rect(v.box([x - 110, FLOOR - 560, x + 110, FLOOR - 380]), sc, 5 * z, 255, r=8 * z)
    p.fill_rect(v.box([x - 96, FLOOR - 546, x + 96, FLOOR - 394]), sc, 60 if not flash else 120, r=6 * z)
    if mine:
        p.text((v.x(x), v.y(FLOOR - 500)), "!" if col != GREEN else "OK", 54 * z, (255, 255, 255), 255)
    p.line(v.pts([(x - 120, FLOOR - 380), (x - 120, FLOOR - 330)]), (120, 126, 156), 6 * z, 255)
    p.fill_rect(v.box([x - 100, FLOOR - 344, x + 100, FLOOR - 322]), (255, 60, 60), 120 if mine else 60)
    # bagging shelf with a bag
    bx = x + 190
    p.fill_rect(v.box([bx - 70, FLOOR - 320, bx + 70, FLOOR - 300]), (90, 96, 140), 255)
    p.line(v.pts([(bx, FLOOR - 300), (bx, FLOOR)]), (90, 96, 140), 6 * z, 255)
    p.fill_poly(v.pts([(bx - 50, FLOOR - 320), (bx + 50, FLOOR - 320), (bx + 42, FLOOR - 430), (bx - 42, FLOOR - 430)]),
                (230, 230, 220), 200)
    return msg, col


def world(p, v, t):
    z = v.z
    fy = v.y(FLOOR)
    p.fill_rect([0, 0, W, fy], (12, 12, 24), 255)
    p.fill_rect([0, fy, W, H], (20, 20, 30), 255)
    p.ds.line([0, fy * K, W * K, fy * K], fill=(90, 90, 130, 255), width=int(3 * K))
    # ceiling lights (parallax cue) and floor tiles
    x0 = int((v.cx - W / z) // 240) * 240
    for x in range(x0, int(v.cx + W / z) + 240, 240):
        sx = v.x(x)
        p.line([(sx - 80 * z, v.y(360)), (sx + 80 * z, v.y(360))], (230, 235, 255), 5 * z, 160)
        p.ds.line([sx * K, fy * K, (sx + (sx - W / 2) * 0.8) * K, H * K], fill=(60, 60, 90, 110), width=int(2 * K))
    # back-wall shelves full of products, left of the glass front
    rng = np.random.default_rng(11)
    cols = [(255, 120, 120), (120, 220, 255), (255, 210, 90), (150, 255, 150), (255, 140, 220), (200, 160, 255)]
    for sx0 in range(-400, 1700, 300):
        for row in range(3):
            yy = 600 + row * 150
            p.fill_rect(v.box([sx0, yy + 110, sx0 + 280, yy + 122]), (70, 74, 110), 255)
            xx = sx0 + 10
            while xx < sx0 + 260:
                w_ = rng.uniform(26, 50)
                h_ = rng.uniform(50, 100)
                c = cols[int(rng.integers(len(cols)))]
                p.fill_rect(v.box([xx, yy + 110 - h_, xx + w_, yy + 110]), c, 70)
                p.rect(v.box([xx, yy + 110 - h_, xx + w_, yy + 110]), c, 2 * z, 150)
                xx += w_ + 6
    # overhead signs: the two choices, readable at a glance
    # self-checkout row: his machine and two others
    kiosk(p, v, KIOSK_X - 420, t, False)
    msg = kiosk(p, v, KIOSK_X, t, True)
    # cashier lane: belt, register, items
    p.fill_rect(v.box([BELT[0], FLOOR - 300, BELT[1] + 120, FLOOR]), (26, 28, 48), 255, r=8 * z)
    p.rect(v.box([BELT[0], FLOOR - 300, BELT[1] + 120, FLOOR]), CASH, 4 * z, 200, r=8 * z)
    p.fill_rect(v.box([BELT[0], FLOOR - 320, BELT[1], FLOOR - 300]), (60, 64, 90), 255)
    for j in range(4):
        bx = BELT[0] + ((t * 160 + j * 95) % (BELT[1] - BELT[0] - 60)) if t < T_PAY + 0.4 else -9999
        if bx > 0:
            p.fill_rect(v.box([bx, FLOOR - 380, bx + 54, FLOOR - 320]), cols[j], 140, r=6 * z)
    p.fill_rect(v.box([LANE_X - 60, FLOOR - 470, LANE_X + 60, FLOOR - 330]), (10, 12, 22), 255, r=6 * z)
    p.rect(v.box([LANE_X - 60, FLOOR - 470, LANE_X + 60, FLOOR - 330]), CASH, 4 * z, 255, r=6 * z)
    tot = "$42.10" if T_PAY - 0.4 <= t < T_PAY + 1.4 else ("OPEN" if t >= T_PAY + 1.4 else "$" + f"{(t * 7.3) % 40:.2f}")
    p.text((v.x(LANE_X), v.y(FLOOR - 440)), tot, 26 * z, GREEN, 255, neon=True)
    # lane light: green when open
    p.line(v.pts([(BELT[1] + 100, FLOOR - 300), (BELT[1] + 100, FLOOR - 760)]), (120, 126, 156), 6 * z, 255)
    p.circle(v.x(BELT[1] + 100), v.y(FLOOR - 790), 30 * z, GREEN, a=255, fill=True)
    p.text((v.x(BELT[1] + 100), v.y(FLOOR - 812)), "3", 30 * z, (10, 10, 10), 255)
    # glass front and the car park
    p.fill_rect(v.box([EXIT_X, 700, EXIT_X + 1400, FLOOR]), (6, 10, 28), 255)
    for gx in range(EXIT_X, EXIT_X + 1400, 260):
        p.line(v.pts([(gx, 700), (gx, FLOOR)]), (110, 120, 170), 6 * z, 255)
    p.line(v.pts([(EXIT_X, 700), (EXIT_X + 1400, 700)]), (110, 120, 170), 8 * z, 255)
    p.text((v.x(EXIT_X + 130), v.y(760)), "EXIT", 44 * z, GREEN, 255, neon=True, spacing=6)
    # his car outside
    cb = FLOOR - 20
    body = [(-190, -40), (-150, -100), (-40, -126), (90, -108), (200, -70), (206, -24), (-190, -24)]
    p.fill_poly(v.pts([(CAR_X + a, cb + b) for a, b in body]), (20, 24, 44), 255)
    p.line(v.pts([(CAR_X + a, cb + b) for a, b in body] + [(CAR_X - 190, cb - 40)]), CASH, 5 * z, 230)
    for wx in (CAR_X - 110, CAR_X + 120):
        p.circle(v.x(wx), v.y(cb - 20), 36 * z, CASH, 5 * z, 230)
    for sx, s1, s2, c in ((KIOSK_X, "SELF", "CHECKOUT", SELF), ((BELT[0] + BELT[1]) / 2 + 60, "CASHIER", "", CASH)):
        p.text((v.x(sx), v.y(FLOOR - 250 if s2 else FLOOR - 200)), s1, 46 * z, c, 255, neon=True, spacing=4)
        if s2:
            p.text((v.x(sx), v.y(FLOOR - 190)), s2, 36 * z, c, 255, neon=True, spacing=3)
    return msg


BG = None
VIG = None
FRAME0 = None


def scene(t):
    v = View(t)
    p = AP.SafePanel(BG)
    p.tops = []
    msg, mcol = world(p, v, t)
    # shoppers and staff
    ahead = 1 - smooth(prog(t, 2.0, 2.8))
    if ahead > 0.02:
        AP.gray_person(p, v, lerp(CYAN_LINE[2], CYAN_OUT + 300, 1 - ahead) if ahead < 1 else CYAN_LINE[2],
                       AJ.walk(t * 9, STAND) if ahead < 1 else STAND, a=200 * ahead, bag=True)
    cpose = dict(STAND, el=(-30, -90), hl=(-70, -100)) if t < T_PAY + 1.4 else \
        dict(STAND, el=(-26, -124), hl=(-40, -172 - 10 * math.sin(t * 9)))
    AP.gray_person(p, v, CASHIER_X, cpose, facing=1)
    if T_ATT0 <= t < T_ATT1 + 0.8:
        if t < T_ATT0 + 0.5:
            ax, pose = lerp(KIOSK_X - 700, KIOSK_X - 20, prog(t, T_ATT0, T_ATT0 + 0.5)), AJ.walk(t * 9, STAND)
        elif t < T_ATT1:
            ax, pose = KIOSK_X - 20, dict(STAND, el=(30, -96), hl=(70, -110))
        else:
            ax, pose = lerp(KIOSK_X - 20, KIOSK_X - 700, prog(t, T_ATT1, T_ATT1 + 0.8)), AJ.walk(t * 9, STAND)
        AP.gray_person(p, v, ax, pose, facing=1 if t < T_ATT1 else -1, a=230)
    # the cyan guy
    pose, x, facing, prop = cyan_state(t)
    sp = AP.stick(p, v, AJ.place(pose, (x, HIP_Y), facing, S), CASH)
    hx, hy = sp["hl"]
    z = v.z
    if prop == "card":
        p.fill_rect([hx - 4 * z, hy - 18 * z, hx + 40 * z, hy + 10 * z], GOLD, 255, r=4 * z)
    if prop == "bag" or (t >= T_DONE - 0.6 and t < T_DONE):
        p.fill_poly([(hx - 24 * z, hy), (hx + 24 * z, hy), (hx + 20 * z, hy + 60 * z), (hx - 20 * z, hy + 60 * z)],
                    (230, 230, 220), 255)
    # the orange guy
    pose, x, prop = orange_state(t)
    sp = AP.stick(p, v, AJ.place(pose, (x, HIP_Y), 1, S), SELF)
    if prop == "item":
        hx, hy = sp["hl"]
        p.fill_rect([hx - 20 * z, hy - 30 * z, hx + 20 * z, hy + 10 * z], (255, 120, 120), 255, r=6 * z)
    # the machine's voice: big, over his head, the colour of the light
    if t < T_PAN + 0.3 or T_BACK <= t < T_WIDE + 0.6:
        words_ = msg.split()
        lines, cur = [], ""
        for w_ in words_:
            if len(cur) + len(w_) + 1 > 16 and cur:
                lines.append(cur)
                cur = w_
            else:
                cur = (cur + " " + w_).strip()
        lines.append(cur)
        k = 1 + 0.05 * (mcol != GREEN) * max(0, math.sin(t * 12))
        sz = 50 * k
        tw = max(len(l_) for l_ in lines) * sz * 0.64
        hh = len(lines) * sz * 1.2
        xx, yy = W / 2, 330
        p.fill_rect([xx - tw / 2 - 26, yy - 16, xx + tw / 2 + 26, yy + hh + 10], (8, 8, 14), 225, r=16)
        p.rect([xx - tw / 2 - 26, yy - 16, xx + tw / 2 + 26, yy + hh + 10], mcol, 5, 255, r=16)
        for j, l_ in enumerate(lines):
            p.text((xx, yy + j * sz * 1.2), l_, sz, mcol, 255, neon=True)
    # words
    AP.say(p, v, t, T_WHIP1 + 0.3, T_WHIP2, CYAN_LINE[1], FLOOR - 720, "I'LL JUST WAIT.", CASH, 40)
    AP.say(p, v, t, T_WHIP3 + 0.2, T_PAY, LANE_X - 100, FLOOR - 720, "BEEP BEEP BEEP", CASH, 40)
    AP.say(p, v, t, T_PAY, T_WHIP4, LANE_X - 100, FLOOR - 720, "PAID. BYE!", GREEN, 46)
    AP.say(p, v, t, T_PAN + 0.5, T_DONE + 0.2, LANE_X, FLOOR - 720, "NEXT!", CASH, 60)
    if t >= T_DONE:
        AP.stamp(p, t, T_DONE, v.x(CYAN_OUT + 40), v.y(FLOOR - 820), "DONE IN 5 MIN", GREEN)
    if t >= T_STILL:
        AP.stamp(p, t, T_STILL, W / 2, 640, "STILL HERE. 12 MIN", REDC)
    out = p.compose()
    from PIL import ImageFilter
    for lay, pos in p.tops:
        out.alpha_composite(lay.filter(ImageFilter.GaussianBlur(10 * K)), pos)
        out.alpha_composite(lay, pos)
    return hq.downsample(out, W, H)


def frame(t):
    img = scene(t).convert("RGBA")
    c0, c1 = cam(t - 1 / FPS), cam(t)
    vx = (c1[0] - c0[0]) * c1[2]
    if any(tw <= t < tw + 0.4 for tw in WHIPS) and abs(vx) > 18:
        span = min(abs(vx) * 0.7, 220)
        a_ = np.asarray(img, np.float32)
        acc = np.zeros_like(a_)
        n = 16
        for j in range(n):
            acc += np.roll(a_, int(span * (j / (n - 1) - 0.5)), axis=1)
        img = Image.fromarray((acc / n).astype(np.uint8), "RGBA")
    img.alpha_composite(VIG)
    tp = hq.Panel(Image.new("RGBA", (W * K, TITLE_H * K), (0, 0, 0, 0)))
    if t < T_L1:
        tp.text((W / 2, 22), "WHO GETS OUT FIRST?", 58, (250, 250, 252), 255)
        s = timer_s(t)
        tp.text((W / 2, 102), f"{int(s // 60)}:{int(s % 60):02d}", 76, GOLD, 255, neon=True, spacing=4)
        tp.text((W / 2, 200), "MINUTES AT CHECKOUT", 28, (200, 200, 215), 255, spacing=4)
    else:
        for t0, s2, y in ((T_L1, LINE1, 60), (T_L2, LINE2, 150)):
            if t < t0:
                continue
            k = int(clamp((t - t0) * CPS, 0, len(s2)))
            tp.text((W / 2, y), s2[:k] + " " * (len(s2) - k), 44 if len(s2) > 24 else 54,
                    (250, 250, 252) if t0 == T_L1 else GOLD, 255, neon=t0 == T_L2)
    tl = tp.compose(glow=0.8)
    img.alpha_composite(tl.resize((W, TITLE_H), Image.LANCZOS), (0, 0))
    rgb = hq.bloom(np.asarray(img.convert("RGB")), 0.45, 150, 26)
    # red pulse on every alarm
    for t0 in T_ERR:
        if t0 <= t < t0 + 0.25:
            k = 1 - (t - t0) / 0.25
            rgb = np.clip(rgb.astype(np.float32) + np.array([45, 0, 0]) * k, 0, 255).astype(np.uint8)
    for t0 in (T_DONE, T_STILL):
        if t0 <= t < t0 + 0.12:
            rgb = np.clip(rgb.astype(np.float32) + 40 * (1 - (t - t0) / 0.12), 0, 255).astype(np.uint8)
    arr = rgb.astype(np.float32)
    if t >= T_FOLLOW:
        k = smooth(prog(t, T_FOLLOW, T_FOLLOW + 0.3))
        arr *= 1 - 0.75 * k
        card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        ff = font(AP.BOLD, 76)
        spaced(cd, W / 2, H / 2 - 90, "FOLLOW", ff, (250, 250, 252, int(255 * k)), 6)
        spaced(cd, W / 2, H / 2 + 6, "FOR MORE", ff, (250, 250, 252, int(255 * k)), 6)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
        base.alpha_composite(card)
        return np.asarray(base.convert("RGB"))
    return np.clip(arr, 0, 255).astype(np.uint8)


def init_worker():
    global BG, VIG
    AP.init_worker()
    BG, VIG = AP.BG, AP.VIG


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
def alarm(fx, at, g=0.08):
    """the self-checkout error: two falling tones, twice"""
    for j in range(2):
        mix_in(fx, tone(988, 0.16, (1, 0.5, 0.3), a=0.003, d=0.08), at + j * 0.36, g, -0.2)
        mix_in(fx, tone(740, 0.22, (1, 0.5, 0.3), a=0.003, d=0.1), at + j * 0.36 + 0.16, g, -0.2)


def scan_beep(fx, at, g=0.05, pan=0.0):
    mix_in(fx, tone(1850, 0.07, (1,), a=0.001, d=0.03), at, g, pan)


def audio():
    n = int(DUR * SR)
    fx = np.zeros((n, 2))
    mus = music.score(MUSIC, DUR, t_end=T_PAN, t_warm=T_L1 - 0.2, t_line=T_L1 + 0.3, start=0.0, loud=1.1)
    # store hum
    mix_in(fx, noise(DUR, 77, lo=80, hi=600) * 0.5, 0, 0.02)
    # hook: hit + the alarm from frame 0
    mix_in(fx, tone(48, 0.9, (1, 0.6, 0.3), a=0.002, d=0.45), 0.0, 0.3)
    for t0 in T_ERR:
        alarm(fx, t0, 0.09)
    for tw in WHIPS:
        AP.whoosh(fx, tw, 0.12, int(tw * 10))
    # his scans
    for t0 in np.arange(1.6, T_ERR[1], 0.45):
        scan_beep(fx, t0, 0.04, -0.3)
    # cashier: fast steady beeps while the lane is on screen, then the card chime
    for t0 in np.arange(T_WHIP1 + 0.2, T_WHIP2, 0.3):
        scan_beep(fx, t0, 0.05, 0.3)
    for t0 in np.arange(T_WHIP3 + 0.1, T_PAY, 0.18):
        scan_beep(fx, t0, 0.06, 0.3)
    for j, m in enumerate((79, 84)):
        mix_in(fx, music.marimba(midi(m), 0.8), T_PAY + 0.1 + 0.1 * j, 0.08, 0.3)
    # help light, attendant footsteps, the place/remove loop
    mix_in(fx, tone(660, 0.6, (1, 0.5), a=0.01, d=0.3), T_HELP, 0.05)
    tt = T_LOOP
    while tt < T_ID:
        mix_in(fx, tone(880, 0.12, (1, 0.4), a=0.002, d=0.06), tt, 0.06, -0.2)
        mix_in(fx, noise(0.12, int(tt * 50), lo=1500, hi=7000) * env(int(0.12 * SR), 0.002, 0.05), tt + 0.05, 0.05)
        tt += 0.55
    # twist: the glide gets a soft riser, the stamps hit, then a sad horn for him
    rs = noise(1.2, 7, lo=400, hi=6000) * np.linspace(0, 1, int(1.2 * SR)) ** 2
    mix_in(fx, rs, T_PAN, 0.05)
    for t0, g in ((T_DONE, 0.24), (T_STILL, 0.26)):
        mix_in(fx, tone(70, 0.5, (1, 0.5), a=0.002, d=0.25) + 0.35 * noise(0.5, int(t0 * 10), lo=400, hi=5000) *
               env(int(0.5 * SR), 0.002, 0.12), t0, g)
    for j, m in enumerate((79, 84, 88)):
        mix_in(fx, AP.synth(midi(m), 0.7, 0.4, 4), T_DONE + 0.2 + 0.07 * j, 0.04)
    for j, f in enumerate((233, 220, 207, 185)):
        mix_in(fx, tone(f, 0.45 if j < 3 else 1.1, (1, 0.7, 0.5, 0.3), a=0.01, d=0.3 if j < 3 else 0.8),
               T_STILL + 0.3 + j * 0.4, 0.06)
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
    out = sys.argv[1] if len(sys.argv) > 1 else "self-checkout.mp4"
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
