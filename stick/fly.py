#!/usr/bin/env python3
"""THE FLY - two roommates, one fly, a moving camera. 18 s, loops.

Frame 0 is the peak: the orange guy mid-leap over the couch in slow motion, slipper raised, the floor lamp falling,
a vase in the air - and the fly calmly hovering next to his face. Then real time: CRASH. The chase breaks one thing
every ~1.5 s: the TV, the plant (after he swings at his roommate's head), the ceiling bulb, the chair, the picture
(the slipper bounces back into his face), and he slaps his own face. The cyan roommate never looks up from his book.
Twist: the cyan guy stands, switches off the light, opens the window - the fly flies straight out to the light.
Lights on, wide: everything is broken. "HE CHASED IT. / HE SHOWED IT OUT." A new fly buzzes in, he leaps... loop.
Rewatch hooks: count what he broke (7), the fly is in every shot, the loop.

    python3 stick/fly.py stick/fly.mp4
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
import airport as AP  # noqa
from perfect_wave import clamp, env, font, lerp, lerp_pose, midi, mix_in, noise, prog, smooth, spaced, tone, write_wav  # noqa

W, H, FPS = 1080, 1920, 30
SR = 44100
DUR = 18.0
NF = int(round(DUR * FPS))
XFADE = 0.5
K = hq.K
FLOOR = AP.FLOOR
S = AP.S
HIP_Y = AP.HIP_Y
ORG = (255, 150, 40)
CYN = (60, 220, 255)
GOLD, GREEN, REDC = AP.GOLD, AP.GREEN, AP.REDC
WARM = (255, 214, 150)
TITLE_H = 300
MUSIC = "kalimba_e"

# room (x)
LAMP_X = 380
TABLE_X = 520            # side table with the vase, the picture above it
COUCH = (650, 1150)
CYAN_X = 950
PLANT_X = 1235
CHAIR_X = 1385           # under the ceiling lamp
TV_X = 1560
SWITCH_X = 1760
WIN = (1800, 2060, 820, 1300)
SEAT_Y = FLOOR - 230

# timeline
T_SLOW = 1.2             # slow motion ends
T_LAMP, T_VASE, T_LAND = 1.35, 1.45, 1.5
T_TV = 2.72
T_SWING_C = 4.05         # at his roommate's head
T_PLANT = 4.42
T_CLIMB = 5.2
T_BULB = 5.88
T_TIP = 6.02
T_THROW = 7.1
T_FRAME = 7.36
T_BONK = 7.72
T_SLAP = 9.2
T_STAND = 10.1
T_OFF = 11.0
T_OPEN = 11.35
T_OUT0, T_OUT1 = 11.6, 12.3
T_CLOSE = 12.55
T_ON = 12.9
T_L1, T_L2 = 14.0, 14.9
CPS = 16.0
LINE1, LINE2 = "HE CHASED IT.", "HE SHOWED IT OUT."
T_FLY2 = 16.1
T_LEAP2 = 17.0
BREAKS = [T_LAMP, T_VASE, T_TV, T_PLANT, T_BULB, T_TIP, T_FRAME]


def phys(t):
    """hook clock: slow motion first (phys 0.35 -> 0.6 in 1.2 s), then real time"""
    if t < T_SLOW:
        return 0.35 + 0.25 * t / T_SLOW
    return 0.6 + (t - T_SLOW) * (0.45 / (T_LAND - T_SLOW))


def ease(a, b, t, t0, t1):
    return lerp(a, b, smooth(prog(t, t0, t1)))


# ---------------------------------------------------------------- the fly
FLY_KEYS = [
    (0.0, 700, 1060), (0.6, 740, 1040), (1.2, 720, 1080), (1.7, 900, 980), (2.35, 1600, 1260), (2.66, 1600, 1260),
    (2.9, 1500, 1020), (3.5, 960, 1090), (4.0, 960, 1090), (4.25, 1050, 950), (4.9, 1385, 720), (5.76, 1385, 720),
    (6.1, 1150, 820), (6.6, 520, 935), (7.08, 520, 935), (7.5, 900, 980), (8.2, 1360, 1010), (8.8, 1320, 1090),
    (9.17, 1320, 1090), (9.6, 1500, 960), (10.4, 1350, 930), (11.0, 1550, 1000), (11.6, 1700, 980),
    (12.3, 2300, 900), (16.1, -150, 980), (16.8, 1300, 1040), (17.4, 1000, 1000), (18.0, 700, 1060)]
LANDED = [(2.35, 2.66), (3.5, 4.0), (4.9, 5.76), (6.6, 7.08), (8.8, 9.17)]


def fly_pos(t):
    if T_OUT1 < t < T_FLY2:
        return None
    for (a, xa, ya), (b, xb, yb) in zip(FLY_KEYS, FLY_KEYS[1:]):
        if a <= t <= b:
            k = smooth(prog(t, a, b))
            x, y = lerp(xa, xb, k), lerp(ya, yb, k)
            break
    else:
        x, y = FLY_KEYS[-1][1:]
    if not any(a <= t <= b for a, b in LANDED):
        x += 26 * math.sin(t * 9.1) + 12 * math.sin(t * 23)
        y += 20 * math.sin(t * 7.3 + 1) + 10 * math.cos(t * 19)
    return x, y


def fly_flying(t):
    return fly_pos(t) is not None and not any(a <= t <= b for a, b in LANDED)


# ---------------------------------------------------------------- camera
CAM_KEYS = [
    (0.0, 650, 1110, 1.75), (1.2, 660, 1130, 1.86), (1.6, 760, 1230, 1.5), (2.2, 1430, 1240, 1.5),
    (3.0, 1440, 1240, 1.55), (3.5, 1080, 1240, 1.5), (4.6, 1120, 1240, 1.55), (5.0, 1380, 1060, 1.35),
    (5.9, 1380, 1020, 1.4), (6.3, 1360, 1250, 1.4), (6.7, 900, 1200, 1.15), (7.8, 980, 1200, 1.2),
    (8.1, 1320, 1130, 2.4), (9.5, 1320, 1130, 2.6), (9.9, 1060, 1240, 1.5), (10.3, 1060, 1240, 1.5),
    (11.0, 1780, 1180, 1.45), (12.4, 1900, 1120, 1.45), (12.9, 1900, 1120, 1.45), (13.6, 1220, 741, 0.66),
    (16.0, 1220, 741, 0.68), (16.9, 1150, 1150, 1.35), (18.0, 650, 1110, 1.75)]


def cam(t):
    for (a, xa, ya, za), (b, xb, yb, zb) in zip(CAM_KEYS, CAM_KEYS[1:]):
        if a <= t <= b:
            k = smooth(prog(t, a, b))
            cx, cy, z = lerp(xa, xb, k), lerp(ya, yb, k), lerp(za, zb, k)
            break
    else:
        cx, cy, z = CAM_KEYS[-1][1:] if t > 0 else CAM_KEYS[0][1:]
    cx += 5 * math.sin(t * 1.7) + 3 * math.sin(t * 4.3 + 1)
    cy += 4 * math.sin(t * 2.1 + 2) + 2 * math.sin(t * 5.1)
    sh = 0
    for t0 in BREAKS + [T_LAND, T_BONK, T_SLAP, 6.3]:
        if t0 <= t < t0 + 0.3:
            sh = max(sh, 20 * (1 - (t - t0) / 0.3))
    cx += sh * math.sin(t * 61) / z
    cy += sh * 0.7 * math.cos(t * 53) / z
    return cx, cy, z


class View(AP.View):
    def __init__(self, t):
        self.cx, self.cy, self.z = cam(t)


# ---------------------------------------------------------------- poses
STAND = PW.STAND
LEAP = {"head": (40, -138), "neck": (26, -100), "el": (-14, -136), "hl": (-60, -158), "er": (66, -90),
        "hr": (104, -80), "kl": (34, 40), "fl": (-26, 84), "kr": (-30, 44), "fr": (-84, 44)}
SPLAT = {"head": (60, -60), "neck": (40, -40), "el": (80, -10), "hl": (110, 20), "er": (20, 10), "hr": (40, 50),
         "kl": (-50, 30), "fl": (-100, 50), "kr": (-40, 40), "fr": (-90, 70)}
WIND = dict(STAND, el=(10, -150), hl=(-20, -200), er=(-20, -70), hr=(-40, -40))
HIT = dict(STAND, head=(14, -148), el=(50, -110), hl=(100, -80), er=(-20, -70), hr=(-40, -40))
UPSWING = dict(STAND, el=(20, -160), hl=(30, -230), er=(-20, -70), hr=(-40, -40))
THROW = dict(STAND, el=(40, -120), hl=(100, -110), er=(-30, -70), hr=(-50, -40))
DAZED = dict(STAND, head=(10, -146), el=(-30, -70), hl=(-30, -20), er=(30, -70), hr=(30, -20))
SLAP = dict(STAND, head=(-14, -144), el=(30, -110), hl=(10, -150), er=(-20, -70), hr=(-40, -40))
FLOOR_SIT = {"head": (6, -150), "neck": (3, -108), "el": (20, -60), "hl": (50, -40), "er": (-10, -60),
             "hr": (-30, -20), "kl": (60, -30), "fl": (120, 0), "kr": (50, -20), "fr": (110, 8)}
SIT = dict(PW.SIT, kl=(62, -2), fl=(66, 108), kr=(54, 2), fr=(56, 110))
READ = dict(SIT, el=(26, -70), hl=(52, -110), er=(20, -66), hr=(46, -104))
DUCK = dict(SIT, head=(40, -100), neck=(26, -78), el=(30, -110), hl=(56, -134), er=(10, -110), hr=(40, -138))
REACH = dict(STAND, el=(-30, -100), hl=(-80, -110))
OPEN_UP = dict(STAND, el=(30, -130), hl=(60, -170), er=(24, -126), hr=(50, -166))


def run_pose(t, lean=1.0):
    return AP.run(t * 15, lean)


def orange(t):
    """pose, hip, facing, slipper(True = in hand), ang"""
    if t < T_LAND + 0.1:
        u = prog(phys(t), 0.0, 1.05)
        x = lerp(560, 740, u)
        y = lerp(1250, 1400, u) - 330 * math.sin(math.pi * min(u, 1.0)) * 0.9
        pose = LEAP if u < 0.92 else lerp_pose(LEAP, SPLAT, smooth(prog(u, 0.92, 1.0)))
        return pose, (x, y), 1, True, 0.12 * (1 - smooth(prog(u, 0.85, 1.0)))
    if t < 1.65:
        return SPLAT, (760, 1440), 1, True, 0.0
    if t < 2.5:
        x = ease(780, 1430, t, 1.65, 2.5)
        return run_pose(t), (x, HIP_Y - 10 * abs(math.sin(t * 15))), 1, True, 0.0
    if t < 2.9:
        k = smooth(prog(t, 2.5, T_TV))
        return lerp_pose(WIND, HIT, k), (1430, HIP_Y), 1, True, 0.0
    if t < 3.85:
        x = ease(1430, 1090, t, 2.95, 3.8)
        return AJ.walk(t * 9, STAND), (x, HIP_Y), -1, True, 0.0
    if t < 4.5:
        k = smooth(prog(t, 3.85, T_SWING_C))
        x = ease(1090, 1180, t, T_SWING_C + 0.1, T_PLANT)
        return lerp_pose(WIND, HIT, k), (x, HIP_Y), -1, True, 0.0
    if t < T_CLIMB:
        x = ease(1180, CHAIR_X, t, 4.55, 5.1)
        return AJ.walk(t * 9, STAND), (x, HIP_Y), 1, True, 0.0
    if t < T_TIP:
        up = ease(0, 170, t, T_CLIMB, T_CLIMB + 0.25)
        k = smooth(prog(t, 5.5, T_BULB))
        return lerp_pose(STAND, UPSWING, k), (CHAIR_X, HIP_Y - up), 1, True, 0.0
    if t < 6.5:
        k = smooth(prog(t, T_TIP, 6.3))
        ang = lerp(0, 1.45, k)
        y = lerp(HIP_Y - 170, FLOOR - 40, k * k)
        return lerp_pose(UPSWING, DAZED, k), (lerp(CHAIR_X, CHAIR_X + 90, k), y), 1, True, ang
    if t < 6.85:
        k = smooth(prog(t, 6.5, 6.85))
        return DAZED, (CHAIR_X + 90 - 60 * k, lerp(FLOOR - 40, HIP_Y, k)), -1, True, lerp(1.45, 0, k)
    if t < T_BONK:
        k = smooth(prog(t, 6.85, T_THROW))
        return lerp_pose(WIND, THROW, k), (1320, HIP_Y), -1, t < T_THROW, 0.0
    if t < 8.1:
        k = math.sin(math.pi * prog(t, T_BONK, 8.1))
        return dict(DAZED, head=(-14 * k, -146)), (1320, HIP_Y), -1, True, -0.15 * k
    if t < T_SLAP - 0.15:
        return dict(STAND, head=(4 + 6 * math.sin(t * 3), -150)), (1320, HIP_Y), 1, True, 0.0
    if t < T_ON:
        if t < T_SLAP + 0.3:
            return SLAP, (1320, HIP_Y), 1, True, -0.12 * math.sin(math.pi * prog(t, T_SLAP, T_SLAP + 0.3))
        w = math.sin(t * 4) * 0.06
        return DAZED, (1320, HIP_Y), 1, True, w
    if t < T_FLY2 + 0.5:
        k = smooth(prog(t, T_ON, T_ON + 0.4))
        return lerp_pose(DAZED, FLOOR_SIT, k), (1320, lerp(HIP_Y, FLOOR - 40, k)), 1, True, 0.0
    if t < T_LEAP2:
        k = smooth(prog(t, T_FLY2 + 0.5, T_LEAP2))
        return lerp_pose(FLOOR_SIT, WIND, k), (1320, lerp(FLOOR - 40, HIP_Y, k)), -1, True, 0.0
    u = prog(t, T_LEAP2, DUR)
    x = lerp(1320, 590, u)
    y = lerp(HIP_Y, 1262, u) - 220 * math.sin(math.pi * u * 0.9)
    return LEAP, (x, y), -1 if u < 0.7 else 1, True, 0.12 * smooth(prog(u, 0.7, 1.0))


def cyan(t):
    """pose, hip, facing, book"""
    sit_hip = (CYAN_X, FLOOR - 110 * S - 6)
    if t < T_STAND:
        if 3.85 <= t < 4.45:
            k = math.sin(math.pi * prog(t, 3.85, 4.45))
            return lerp_pose(READ, DUCK, min(1, k * 1.6)), sit_hip, 1, True
        flip = 4 * math.sin(t * 1.3)
        return dict(READ, hl=(52, -110 + flip)), sit_hip, 1, True
    if t < 10.35:
        k = smooth(prog(t, T_STAND, 10.35))
        return lerp_pose(READ, STAND, k), (CYAN_X, lerp(sit_hip[1], HIP_Y, k)), 1, False
    if t < T_OFF - 0.05:
        x = ease(CYAN_X, SWITCH_X + 70, t, 10.35, T_OFF - 0.1)
        return AJ.walk(t * 9, STAND), (x, HIP_Y), 1, False
    if t < T_OFF + 0.25:
        return REACH, (SWITCH_X + 70, HIP_Y), 1, False
    if t < T_OPEN:
        x = ease(SWITCH_X + 70, 1930, t, T_OFF + 0.25, T_OPEN)
        return AJ.walk(t * 9, STAND), (x, HIP_Y), 1, False
    if t < T_CLOSE + 0.25:
        k = smooth(prog(t, T_OPEN, T_OPEN + 0.25)) if t < T_CLOSE else 1 - smooth(prog(t, T_CLOSE, T_CLOSE + 0.25))
        return lerp_pose(STAND, OPEN_UP, k), (1930, HIP_Y), 1, False
    if t < T_ON + 0.2:
        return REACH, (1930 - ease(0, 100, t, T_CLOSE + 0.2, T_ON + 0.15), HIP_Y), 1, False
    if t < 14.2:
        x = ease(1830, CYAN_X, t, T_ON + 0.2, 14.0)
        return AJ.walk(t * 9, STAND), (x, HIP_Y), -1, False
    k = smooth(prog(t, 14.2, 14.5))
    return lerp_pose(STAND, READ, k), (CYAN_X, lerp(HIP_Y, sit_hip[1], k)), 1, k > 0.6


# ---------------------------------------------------------------- the room
def shards(p, v, x, y, seed, col, n=9, spread=90):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        sx, sy = x + rng.uniform(-spread, spread), y - rng.uniform(0, 14)
        a = rng.uniform(0, 6.28)
        r = rng.uniform(10, 22)
        pts = [(sx + r * math.cos(a + k * 2.1), sy + r * 0.5 * math.sin(a + k * 2.1)) for k in range(3)]
        p.fill_poly(v.pts(pts), col, 230)


def spark(p, v, t, t0, x, y, col=(255, 240, 180)):
    if t0 <= t < t0 + 0.35:
        k = (t - t0) / 0.35
        for j in range(10):
            a = j * 0.628
            r0, r1 = 20 + 90 * k, 40 + 150 * k
            p.line(v.pts([(x + r0 * math.cos(a), y + r0 * math.sin(a)), (x + r1 * math.cos(a), y + r1 * math.sin(a))]),
                   col, 5 * v.z, 255 * (1 - k))


def room(p, v, t):
    z = v.z
    fy = v.y(FLOOR)
    p.fill_rect([0, 0, W, fy], (22, 16, 32), 255)
    p.fill_rect([0, fy, W, H], (30, 22, 30), 255)
    for x in range(-600, 2800, 90):
        p.line(v.pts([(x, 300), (x, FLOOR - 40)]), (26, 19, 37), 3 * z, 255)
    p.fill_rect(v.box([-600, FLOOR - 40, 2800, FLOOR]), (44, 34, 56), 255)
    for i in range(-30, 40):
        x = i * 110
        p.ds.line([v.x(x) * K, fy * K, (v.x(x) + (v.x(x) - W / 2) * 0.9) * K, H * K], fill=(60, 44, 62, 120),
                  width=int(2 * K))
    # window + night outside
    wx0, wx1, wy0, wy1 = WIN
    p.fill_rect(v.box([wx0, wy0, wx1, wy1]), (14, 24, 60), 255)
    p.circle(v.x(1990), v.y(900), 34 * z, (250, 245, 220), a=255, fill=True)
    p.circle(v.x(1990), v.y(900), 70 * z, (250, 245, 220), 10 * z, 50)
    for j in range(8):
        bx = wx0 + 10 + j * 32
        bh = 60 + (j * 37) % 120
        p.fill_rect(v.box([bx, wy1 - bh, bx + 26, wy1]), (26, 30, 60), 255)
        p.fill_rect(v.box([bx + 8, wy1 - bh + 14, bx + 14, wy1 - bh + 22]), (255, 220, 140), 200)
    sash = 0.0
    if T_OPEN <= t < T_CLOSE + 0.25:
        sash = smooth(prog(t, T_OPEN, T_OPEN + 0.25)) if t < T_CLOSE else 1 - smooth(prog(t, T_CLOSE, T_CLOSE + 0.25))
    mid = (wy0 + wy1) / 2
    lo0 = mid - sash * 230
    p.rect(v.box([wx0, lo0, wx1, lo0 + (wy1 - mid)]), (200, 210, 240), 5 * z, 255)
    p.rect(v.box([wx0, wy0, wx1, mid]), (200, 210, 240), 5 * z, 255)
    p.rect(v.box([wx0 - 14, wy0 - 14, wx1 + 14, wy1 + 14]), (150, 120, 190), 8 * z, 255)
    # switch
    p.fill_rect(v.box([SWITCH_X - 20, 1220, SWITCH_X + 20, 1280]), (230, 230, 235), 255, r=4 * z)
    p.fill_rect(v.box([SWITCH_X - 6, 1236 if T_OFF <= t < T_ON else 1250, SWITCH_X + 6,
                       1250 if T_OFF <= t < T_ON else 1264]), (120, 120, 130), 255)
    # picture (falls at T_FRAME)
    if t < T_FRAME:
        p.fill_rect(v.box([TABLE_X - 90, 860, TABLE_X + 90, 1020]), (20, 30, 40), 255)
        p.rect(v.box([TABLE_X - 90, 860, TABLE_X + 90, 1020]), GOLD, 6 * z, 255)
        p.fill_poly(v.pts([(TABLE_X - 70, 1000), (TABLE_X - 10, 920), (TABLE_X + 30, 970), (TABLE_X + 70, 1000)]),
                    (90, 160, 120), 255)
    else:
        k = smooth(prog(t, T_FRAME, T_FRAME + 0.25))
        y0 = lerp(860, FLOOR - 160, k)
        ang = lerp(0, 0.35, k)
        pts = [(-90, 0), (90, 0), (90, 160), (-90, 160)]
        pts = [(TABLE_X + 140 + PW.rot(q, ang)[0], y0 + PW.rot(q, ang)[1]) for q in pts]
        p.line(v.pts(pts + [pts[0]]), GOLD, 6 * z, 255)
        p.line(v.pts([pts[0], pts[2]]), (220, 230, 240), 2 * z, 200)
        p.line(v.pts([pts[1], pts[3]]), (220, 230, 240), 2 * z, 200)
    # side table + vase
    p.fill_rect(v.box([TABLE_X - 70, FLOOR - 260, TABLE_X + 70, FLOOR - 240]), (110, 80, 60), 255)
    p.line(v.pts([(TABLE_X, FLOOR - 240), (TABLE_X, FLOOR)]), (110, 80, 60), 8 * z, 255)
    vu = prog(phys(t), 0.3, 1.0)
    if t < T_VASE:
        vx = lerp(TABLE_X, TABLE_X + 60, vu)
        vy = lerp(FLOOR - 300, FLOOR - 30, vu * vu) - 120 * math.sin(math.pi * vu) * 0.8
        va = vu * 4
        pts = [(-26, 40), (-34, 0), (-16, -40), (16, -40), (34, 0), (26, 40)]
        pts = [(vx + PW.rot(q, va)[0], vy + PW.rot(q, va)[1]) for q in pts]
        p.fill_poly(v.pts(pts), (80, 170, 230), 255)
        p.line(v.pts(pts + [pts[0]]), (180, 230, 255), 3 * z, 255)
    else:
        shards(p, v, TABLE_X + 60, FLOOR - 6, 3, (80, 170, 230))
    spark(p, v, t, T_VASE, TABLE_X + 60, FLOOR - 30, (180, 230, 255))
    # floor lamp (falls)
    la = 1.5 * smooth(prog(phys(t), 0.15, 0.95)) if t < T_LAMP else 1.52
    top = (LAMP_X + PW.rot((0, -520), la)[0], FLOOR + PW.rot((0, -520), la)[1])
    p.line(v.pts([(LAMP_X, FLOOR), top]), (190, 190, 200), 6 * z, 255)
    shade = [(-60, 0), (60, 0), (36, -90), (-36, -90)]
    sp = [(top[0] + PW.rot(q, la)[0], top[1] + PW.rot(q, la)[1]) for q in shade]
    lit = t < T_LAMP
    p.fill_poly(v.pts(sp), WARM if lit else (90, 80, 70), 255)
    if lit:
        p.circle(v.x(top[0]), v.y(top[1]), 110 * z, WARM, 8 * z, 40)
    else:
        shards(p, v, top[0] - 20, FLOOR - 6, 9, (255, 240, 200), 7, 60)
    spark(p, v, t, T_LAMP, top[0], FLOOR - 30)
    # couch
    cx0, cx1 = COUCH
    bounce = 14 * math.sin(math.pi * prog(t, T_LAND, T_LAND + 0.3)) if T_LAND <= t < T_LAND + 0.3 else 0
    p.fill_rect(v.box([cx0, SEAT_Y - 150, cx1, SEAT_Y + 10]), (60, 40, 100), 255, r=24 * z)
    p.fill_rect(v.box([cx0 - 20, SEAT_Y + bounce, cx1 + 20, FLOOR - 50]), (80, 56, 130), 255, r=18 * z)
    p.rect(v.box([cx0 - 20, SEAT_Y + bounce, cx1 + 20, FLOOR - 50]), (190, 140, 255), 4 * z, 220, r=18 * z)
    p.rect(v.box([cx0, SEAT_Y - 150, cx1, SEAT_Y + 10]), (190, 140, 255), 4 * z, 200, r=24 * z)
    for lx in (cx0, cx1):
        p.line(v.pts([(lx, FLOOR - 50), (lx, FLOOR)]), (190, 140, 255), 6 * z, 220)
    # plant on its stand (falls at T_PLANT)
    p.fill_rect(v.box([PLANT_X - 50, FLOOR - 200, PLANT_X + 50, FLOOR - 186]), (110, 80, 60), 255)
    p.line(v.pts([(PLANT_X, FLOOR - 186), (PLANT_X, FLOOR)]), (110, 80, 60), 7 * z, 255)
    pk = smooth(prog(t, T_PLANT - 0.25, T_PLANT))
    if t < T_PLANT:
        px, py = PLANT_X + 70 * pk, lerp(FLOOR - 200, FLOOR - 20, pk * pk)
        pa = 1.4 * pk
        pot = [(-34, 0), (34, 0), (26, -70), (-26, -70)]
        pts = [(px + PW.rot(q, pa)[0], py + PW.rot(q, pa)[1]) for q in pot]
        p.fill_poly(v.pts(pts), (200, 110, 70), 255)
        for j in range(5):
            a = -0.9 + j * 0.45 + pa
            tipx, tipy = px + PW.rot((0, -70), pa)[0], py + PW.rot((0, -70), pa)[1]
            p.line(v.pts([(tipx, tipy), (tipx + 90 * math.sin(a), tipy - 90 * math.cos(a))]), (110, 230, 120),
                   7 * z, 255)
    else:
        shards(p, v, PLANT_X + 90, FLOOR - 6, 5, (200, 110, 70), 8, 70)
        p.fill_poly(v.pts([(PLANT_X + 20, FLOOR), (PLANT_X + 90, FLOOR - 40), (PLANT_X + 170, FLOOR)]),
                    (70, 50, 40), 255)
        for j in range(4):
            p.line(v.pts([(PLANT_X + 60 + j * 30, FLOOR - 10), (PLANT_X + 100 + j * 40, FLOOR - 50 - j * 8)]),
                   (110, 230, 120), 7 * z, 255)
    # TV
    p.fill_rect(v.box([TV_X - 160, FLOOR - 250, TV_X + 160, FLOOR]), (40, 34, 50), 255, r=6 * z)
    cracked = t >= T_TV
    p.fill_rect(v.box([TV_X - 150, FLOOR - 560, TV_X + 150, FLOOR - 290]), (10, 10, 16), 255, r=8 * z)
    if not cracked:
        p.fill_rect(v.box([TV_X - 136, FLOOR - 546, TV_X + 136, FLOOR - 304]), (40, 110, 200), 150, r=6 * z)
        p.circle(v.x(TV_X), v.y(FLOOR - 425), 40 * z, (255, 210, 90), a=200, fill=True)
    else:
        rng = np.random.default_rng(int(t * 20))
        for j in range(30):
            nx, ny = rng.uniform(TV_X - 130, TV_X + 130), rng.uniform(FLOOR - 540, FLOOR - 310)
            p.fill_rect(v.box([nx, ny, nx + 14, ny + 4]), (200, 200, 210), 120)
        cxp, cyp = TV_X + 40, FLOOR - 450
        for j in range(8):
            a = j * 0.8 + 0.3
            p.line(v.pts([(cxp, cyp), (cxp + 120 * math.cos(a), cyp + 90 * math.sin(a))]), (230, 235, 245),
                   3 * z, 255)
    p.rect(v.box([TV_X - 150, FLOOR - 560, TV_X + 150, FLOOR - 290]), (150, 160, 200), 5 * z, 255, r=8 * z)
    spark(p, v, t, T_TV, TV_X + 40, FLOOR - 450, (160, 220, 255))
    # chair (tips at T_TIP, a leg snaps)
    ca = 0 if t < T_TIP else 1.35 * smooth(prog(t, T_TIP, T_TIP + 0.3))
    piv = (CHAIR_X + 70, FLOOR)
    seat = [(-70, -170), (70, -170), (70, -150), (-70, -150)]
    back = [(-70, -170), (-70, -340)]
    legs = [[(-60, -150), (-60, 0)], [(60, -150), (60, 0)]]

    def tf(q):
        rx, ry = q[0] + CHAIR_X - piv[0], q[1]
        r = PW.rot((rx, ry), ca)
        return piv[0] + r[0], piv[1] + r[1]
    p.fill_poly(v.pts([tf(q) for q in seat]), (150, 110, 80), 255)
    p.line(v.pts([tf(q) for q in back]), (150, 110, 80), 9 * z, 255)
    p.line(v.pts([tf(q) for q in legs[0]]), (150, 110, 80), 8 * z, 255)
    if t < T_TIP:
        p.line(v.pts([tf(q) for q in legs[1]]), (150, 110, 80), 8 * z, 255)
    else:
        p.line(v.pts([(CHAIR_X + 140, FLOOR - 8), (CHAIR_X + 280, FLOOR - 30)]), (150, 110, 80), 8 * z, 255)
    # ceiling lamp (swings after the hit, bulb pops at T_BULB)
    sw = 0.6 * math.sin((t - T_BULB) * 5.5) * math.exp(-(t - T_BULB) * 0.35) if t >= T_BULB - 0.05 else \
        0.05 * math.sin(t * 1.2)
    anchor = (CHAIR_X, 300)
    bulb = (anchor[0] + 360 * math.sin(sw), anchor[1] + 360 * math.cos(sw))
    p.line(v.pts([anchor, bulb]), (160, 160, 170), 4 * z, 255)
    lshade = [(-70, 30), (70, 30), (30, -20), (-30, -20)]
    lp = [(bulb[0] + PW.rot(q, -sw)[0], bulb[1] + PW.rot(q, -sw)[1]) for q in lshade]
    p.fill_poly(v.pts(lp), (230, 120, 160), 255)
    if t < T_BULB and not (T_OFF <= t < T_ON):
        b0 = PW.rot((0, 40), -sw)
        p.circle(v.x(bulb[0] + b0[0]), v.y(bulb[1] + b0[1]), 18 * z, WARM, a=255, fill=True)
        cone = [(-60, 40), (60, 40), (300, 900), (-300, 900)]
        cp = [(bulb[0] + PW.rot(q, -sw)[0], bulb[1] + PW.rot(q, -sw)[1]) for q in cone]
        p.fill_poly(v.pts(cp), WARM, 18)
    spark(p, v, t, T_BULB, bulb[0], bulb[1] + 40, WARM)


BG = None
VIG = None
VIG_SIDES = None
FRAME0 = None


def scene(t):
    v = View(t)
    p = AP.SafePanel(BG)
    room(p, v, t)
    # cyan roommate
    pose, hip, facing, book = cyan(t)
    sp = AP.stick(p, v, AJ.place(pose, hip, facing, S), CYN)
    if book:
        hx, hy = sp["hl"]
        z = v.z
        p.fill_rect([hx - 6 * z, hy - 46 * z, hx + 40 * z, hy + 14 * z], (240, 240, 230), 255, r=3 * z)
        p.line([(hx + 17 * z, hy - 46 * z), (hx + 17 * z, hy + 14 * z)], (120, 120, 130), 2 * z, 255)
    # orange
    pose, hip, facing, slip, ang = orange(t)
    pts = AJ.place(pose, hip, facing, S, ang)
    sp = AP.stick(p, v, pts, ORG)
    z = v.z
    if slip:
        hx, hy = sp["hl"]
        p.fill_poly([(hx - 14 * z, hy - 10 * z), (hx + 14 * z, hy - 10 * z), (hx + 18 * z, hy - 80 * z),
                     (hx - 18 * z, hy - 80 * z)], (90, 200, 255), 255)
    # the thrown slipper: out to the picture, then back into his face
    if T_THROW <= t < T_BONK + 0.05:
        if t < T_FRAME:
            k = prog(t, T_THROW, T_FRAME)
            sx, sy = lerp(1240, TABLE_X + 40, k), lerp(1100, 940, k) - 80 * math.sin(math.pi * k)
        else:
            k = prog(t, T_FRAME, T_BONK)
            sx, sy = lerp(TABLE_X + 40, 1300, k), lerp(940, 1110, k) - 120 * math.sin(math.pi * k)
        a = t * 18
        q = [(-14, -34), (14, -34), (18, 34), (-18, 34)]
        p.fill_poly(v.pts([(sx + PW.rot(c, a)[0], sy + PW.rot(c, a)[1]) for c in q]), (90, 200, 255), 255)
    # bonk + slap stars
    for t0 in (T_BONK, T_SLAP):
        if t0 <= t < t0 + 0.7:
            hx, hy = sp["head"]
            for j in range(5):
                a = t * 6 + j * 1.256
                sx, sy = hx + 46 * z * math.cos(a), hy - 30 * z + 14 * z * math.sin(a)
                p.text((sx, sy - 12 * z), "*", 30 * z, GOLD, 255 * (1 - (t - t0) / 0.7), neon=True)
    out = p.compose()
    return hq.downsample(out, W, H), v


def draw_fly(img, v, t, bright):
    """the fly is drawn on top of everything, sharp, with its buzzing trail"""
    d = ImageDraw.Draw(img)
    z = v.z
    fp = fly_pos(t)
    if fp is None:
        return
    tc = (200, 200, 220) if not bright else (255, 255, 255)
    if fly_flying(t):
        for j in range(1, 14):
            q = fly_pos(t - j * 0.025)
            if q is None:
                continue
            x, y = v.p(q)
            r = max(1.0, 3.2 * z * (1 - j / 14))
            d.ellipse([x - r, y - r, x + r, y + r], fill=tc + (int(170 * (1 - j / 14)),))
    x, y = v.p(fp)
    s = max(0.6, z)
    flap = int(t * 40) % 2
    for side in (-1, 1):
        wx = x + side * 9 * s
        wy = y - (12 if flap else 6) * s
        d.ellipse([wx - 9 * s, wy - 6 * s, wx + 9 * s, wy + 6 * s], fill=(230, 240, 255, 190))
    d.ellipse([x - 9 * s, y - 7 * s, x + 9 * s, y + 7 * s], fill=(16, 16, 20, 255), outline=(235, 235, 245, 255),
              width=max(1, int(2 * s)))
    d.ellipse([x + 4 * s, y - 5 * s, x + 10 * s, y + 1 * s], fill=(200, 40, 40, 255))


def frame(t):
    img, v = scene(t)
    img = img.convert("RGBA")
    dark = 0.0
    if T_OFF <= t < T_ON:
        dark = smooth(prog(t, T_OFF, T_OFF + 0.08)) * (1 - smooth(prog(t, T_ON - 0.05, T_ON)))
    if dark > 0:
        a = np.asarray(img, np.float32)
        mask = np.ones(a.shape[:2], np.float32) * (1 - 0.84 * dark)
        x0, y0, x1, y1 = [int(c) for c in v.box([WIN[0] - 20, WIN[2] - 20, WIN[1] + 20, WIN[3] + 20])]
        x0, x1 = max(0, x0), min(W, x1)
        y0, y1 = max(0, y0), min(H, y1)
        if x1 > x0 and y1 > y0:
            mask[y0:y1, x0:x1] = 1.0
        a[..., :3] *= mask[..., None]
        img = Image.fromarray(a.astype(np.uint8), "RGBA")
        # moonlight spilling in when the window is open
        if t >= T_OPEN:
            glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            gd = ImageDraw.Draw(glow)
            cxw, cyw = v.p(((WIN[0] + WIN[1]) / 2, (WIN[2] + WIN[3]) / 2))
            for r in range(6):
                rr = (180 + r * 70) * v.z
                gd.ellipse([cxw - rr, cyw - rr, cxw + rr, cyw + rr], fill=(200, 210, 255, 10))
            img.alpha_composite(glow)
    draw_fly(img, v, t, dark > 0.5)
    img.alpha_composite(VIG if t >= T_L1 - 0.3 else VIG_SIDES)
    tp = hq.Panel(Image.new("RGBA", (W * K, TITLE_H * K), (0, 0, 0, 0)))
    for t0, s2, y, c in ((T_L1, LINE1, 50, ORG), (T_L2, LINE2, 150, CYN)):
        if t0 <= t < T_FLY2 + 0.6:
            k = int(clamp((t - t0) * CPS, 0, len(s2)))
            a = 255 * (1 - smooth(prog(t, T_FLY2, T_FLY2 + 0.6)))
            tp.text((W / 2, y), s2[:k] + " " * (len(s2) - k), 64, c, a, neon=True, spacing=5)
    tl = tp.compose(glow=0.8)
    img.alpha_composite(tl.resize((W, TITLE_H), Image.LANCZOS), (0, 0))
    rgb = hq.bloom(np.asarray(img.convert("RGB")), 0.45, 150, 26)
    for t0 in BREAKS:
        if t0 <= t < t0 + 0.1:
            rgb = np.clip(rgb.astype(np.float32) + 30 * (1 - (t - t0) / 0.1), 0, 255).astype(np.uint8)
    return rgb


def init_worker():
    global BG, VIG, VIG_SIDES
    AP.init_worker()
    BG, VIG = AP.BG, AP.VIG
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2)
    vig = (np.clip((r - 0.3) * 1.4, 0, 1) * 150).astype(np.uint8)
    VIG_SIDES = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    VIG_SIDES.putalpha(Image.fromarray(vig, "L"))


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
def crash(fx, at, g=0.25, glass=True, seed=1):
    mix_in(fx, tone(70, 0.4, (1, 0.5), a=0.001, d=0.15, sweep=45), at, g)
    if glass:
        for j in range(7):
            mix_in(fx, tone(2500 + 900 * ((j * 37) % 5), 0.25, (1, 0.4), a=0.001, d=0.08),
                   at + 0.02 + j * 0.035, g * 0.18, (j % 3 - 1) * 0.5)
        mix_in(fx, noise(0.5, seed, lo=3000, hi=10000) * env(int(0.5 * SR), 0.001, 0.15), at, g * 0.5)
    else:
        mix_in(fx, noise(0.4, seed, lo=200, hi=3000) * env(int(0.4 * SR), 0.001, 0.12), at, g * 0.6)


def buzz_track():
    n = int(DUR * SR)
    out = np.zeros((n, 2))
    step = int(SR / 100)
    env_ = np.zeros(n)
    pan = np.zeros(n)
    for i in range(0, n, step):
        t = i / SR
        on = 1.0 if fly_flying(t) else 0.0
        env_[i:i + step] = on
        fp = fly_pos(t)
        if fp is not None:
            v = View(t)
            pan[i:i + step] = clamp((v.x(fp[0]) - W / 2) / (W / 2), -1, 1)
    k = np.ones(441) / 441
    env_ = np.convolve(env_, k, mode="same")
    pan = np.convolve(pan, k, mode="same")
    tt = np.arange(n) / SR
    f = 210 + 25 * np.sin(2 * np.pi * 3.1 * tt) + 12 * np.sin(2 * np.pi * 11 * tt)
    ph = 2 * np.pi * np.cumsum(f) / SR
    saw = (ph / (2 * np.pi)) % 1.0 * 2 - 1
    sig = (0.7 * saw + 0.3 * np.sin(ph * 2)) * env_
    out[:, 0] = sig * (1 - 0.6 * np.clip(pan, 0, 1))
    out[:, 1] = sig * (1 + 0.6 * np.clip(pan, -1, 0))
    return out


def audio():
    n = int(DUR * SR)
    fx = np.zeros((n, 2))
    mus = music.score(MUSIC, DUR, t_end=T_OFF, t_warm=T_L1 - 0.1, t_line=T_L1 + 0.4, start=1.5, loud=1.0)
    fx += 0.022 * buzz_track()
    # hook: slow-motion whoosh from frame 0, then everything lands
    sw = noise(1.4, 4, lo=60, hi=900) * np.sin(np.linspace(0, np.pi, int(1.4 * SR)))
    mix_in(fx, sw, 0.0, 0.16)
    mix_in(fx, tone(55, 1.2, (1, 0.5), a=0.002, d=0.6, sweep=35), 0.0, 0.18)
    crash(fx, T_LAMP, 0.26, True, 11)
    crash(fx, T_VASE, 0.22, True, 12)
    mix_in(fx, tone(110, 0.35, (1, 0.5), a=0.002, d=0.12, sweep=70), T_LAND, 0.2)
    # TV: glass + zap
    crash(fx, T_TV, 0.26, True, 13)
    zap = np.sign(np.sin(2 * np.pi * 120 * np.arange(int(0.4 * SR)) / SR)) * env(int(0.4 * SR), 0.002, 0.15)
    mix_in(fx, zap, T_TV + 0.03, 0.04)
    # swing whooshes
    for t0 in (2.6, T_SWING_C - 0.05, T_BULB - 0.12, T_THROW - 0.05, T_SLAP - 0.08):
        mix_in(fx, noise(0.25, int(t0 * 31), lo=600, hi=5000) * np.sin(np.linspace(0, np.pi, int(0.25 * SR))), t0,
               0.08)
    mix_in(fx, tone(90, 0.3, (1, 0.5), a=0.002, d=0.1), T_SWING_C + 0.06, 0.16)            # hits the couch
    crash(fx, T_PLANT, 0.24, False, 14)
    crash(fx, T_PLANT + 0.03, 0.1, True, 15)
    for j in range(2):
        mix_in(fx, tone(180 + 40 * j, 0.25, (1, 0.6, 0.4), a=0.02, d=0.1, sweep=140), T_CLIMB + j * 0.15, 0.04)
    mix_in(fx, tone(1800, 0.12, (1, 0.5), a=0.001, d=0.04), T_BULB, 0.12)                   # bulb pop
    crash(fx, T_BULB + 0.02, 0.14, True, 16)
    crash(fx, T_TIP + 0.05, 0.2, False, 17)
    mix_in(fx, tone(60, 0.5, (1, 0.6), a=0.002, d=0.2), 6.3, 0.3)                           # body thud
    crash(fx, T_FRAME, 0.24, True, 18)
    mix_in(fx, tone(520, 0.4, (1, 0.5, 0.3), a=0.002, d=0.15, sweep=260), T_BONK, 0.12)     # bonk
    mix_in(fx, noise(0.12, 19, lo=1500, hi=9000) * env(int(0.12 * SR), 0.0005, 0.03), T_SLAP, 0.3)
    mix_in(fx, tone(480, 0.5, (1, 0.5), a=0.002, d=0.2, sweep=240), T_SLAP + 0.05, 0.08)
    # the twist: click, silence, crickets through the open window, click
    for t0 in (T_OFF, T_ON):
        mix_in(fx, tone(3000, 0.03, (1,), a=0.0005, d=0.008), t0, 0.2)
        mix_in(fx, noise(0.03, int(t0 * 7), lo=1000, hi=8000) * env(int(0.03 * SR), 0.0005, 0.008), t0, 0.15)
    mix_in(fx, noise(0.3, 20, lo=300, hi=2500) * env(int(0.3 * SR), 0.05, 0.15), T_OPEN, 0.06)
    mix_in(fx, noise(0.3, 21, lo=300, hi=2500) * env(int(0.3 * SR), 0.05, 0.15), T_CLOSE, 0.06)
    for j in range(10):
        mix_in(fx, tone(4200, 0.06, (1,), a=0.003, d=0.02), T_OPEN + 0.2 + j * 0.12, 0.025, 0.4)
    for j, m in enumerate((72, 76, 79)):
        mix_in(fx, music.music_box(midi(m + 12), 1.2), T_OUT0 + 0.2 + j * 0.15, 0.05)
    # the reveal: a deflating horn
    for j, f in enumerate((294, 277, 262, 247)):
        mix_in(fx, tone(f, 0.4 if j < 3 else 1.0, (1, 0.7, 0.5, 0.3), a=0.01, d=0.25 if j < 3 else 0.7),
               T_ON + 0.5 + j * 0.35, 0.05)
    for t0, s in ((T_L1, LINE1), (T_L2, LINE2)):
        for i2, c in enumerate(s):
            if c != " ":
                mix_in(fx, noise(0.03, 500 + i2 + int(t0 * 10), lo=1200, hi=4000) * env(int(0.03 * SR), 0.001, 0.008),
                       t0 + i2 / CPS, 0.05)
    mix_in(fx, noise(0.5, 22, lo=300, hi=4000) * np.sin(np.linspace(0, np.pi, int(0.5 * SR))), T_LEAP2 + 0.3, 0.1)
    x = mus + fx
    m = int(XFADE * SR)
    k = np.linspace(0, 1, m)[:, None]
    x[-m:] = x[-m:] * (1 - k) + x[:m] * k
    x /= max(1.0, np.abs(x).max() / 0.9)
    return x


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "fly.mp4"
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
