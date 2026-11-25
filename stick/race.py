#!/usr/bin/env python3
"""WHO WINS? - three lanes, one 100 m race at night, 29.6 s, a perfect loop (the race rewinds into frame 0).

Each lane has its own camera that follows its runner along the road; the finish line only comes into view at the very
end. One counter on top: DISTANCE (M) for all three.

Top: SPRINTER - bursts to ~54 m, "EASY!", pants, sits down to rest (water, leans back, checks his phone), sees the
others coming ("!"), sprints again, takes the lead for a moment, cramps ("OW!"), limps on. Middle: CONSISTENT - a
winding road, the same steady jog the whole time, through the rain, one step from the tape. Bottom: RICH KID - never
runs: on a lounger at the start line with keys, juice, selfie, cash fan, drone pizza, gold watch. Before the end his
gift car arrives with a chauffeur, he gets in, the bow flies off, the car rockets down the road and breaks its tape
a moment before CONSISTENT reaches his. Stamps: TIRED / 2ND / 1ST. Then everything rewinds to the start.

    python3 stick/race.py stick/who-wins.mp4
    ONLY_FRAMES=0,4,11,15,16.2,18.5,19.8,22.5,24.8,25.95,26.4,27.2 python3 stick/race.py /tmp/race
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
import music  # noqa
import hq  # noqa
from perfect_wave import clamp, env, font, lerp, lerp_pose, midi, mix_in, noise, prog, smooth, tone, write_wav  # noqa

W, H, FPS = 1080, 1920, 30
SR = 44100
DUR = 21.63
NF = int(round(DUR * FPS))
K = hq.K
BOLD = hq.BOLD
MUSIC = "epic hybrid on FluidR3 GM (race.gm_score)"

TITLE_H = 292
PX0 = 20
PWD, PHT = 1040, 500
PANEL_Y = [296, 802, 1308]
HORIZON = 262
FEET = 412                 # feet line on the straight roads (screen)
S = 0.62                   # figure scale: ~180 px tall, 1 m = 100 px
PXM = 100                  # world pixels per metre
START = 300                # world x of the start line
FIN = START + 100 * PXM    # world x of the finish line
RUN_SX = 380               # where the camera keeps a runner on screen

INK = (14, 16, 28)
WHITE = (226, 230, 240)
NIGHT = (7, 10, 24)
GOLD = (255, 196, 40)
RED = (226, 54, 54)
GREEN = (40, 176, 86)
GREY = (120, 124, 134)
CAR = (230, 40, 52)

# ---------------------------------------------------------------- timeline (scene time)
VJOG = 5.0                 # CONSISTENT's steady jog (m/s)
T_STOP_S = 7.2             # sprinter stops at 56.7 m
T_EASY1 = 8.0
T_PANT1 = 8.6
T_SITDOWN = 9.0
T_DRINK0, T_DRINK1 = 9.1, 10.2
T_RELAX1 = 10.9
T_ALERT = 11.8             # "!" on his phone, just after CONSISTENT passes him
T_RUN2 = 12.2
T_CRAMP = 14.5
T_FALL = 14.9
T_UP = 15.6
T_LIMP = 16.0
T_RAIN0, T_RAIN1 = 7.6, 10.4
T_TOUCH = 0.6 + (100 - 0.3 * VJOG) / VJOG     # 20.3: CONSISTENT reaches his tape
T_REACH = T_TOUCH - 0.6
T_KEYS1 = 2.3
T_JUICE1 = 4.1
T_SELFIE = 4.8
T_FAN0, T_FAN1 = 5.6, 7.4
T_DRONE0, T_DRONE_HAND, T_DRONE1 = 7.4, 8.4, 9.6
T_EAT1 = 11.2
T_YAWN1 = 12.5
T_WATCH1 = 14.2
T_CAR0, T_CAR1 = 14.2, 15.5              # the car arrives
T_HONK = 15.2
T_CHAUF = 15.6                           # chauffeur steps out
T_KSTAND = 15.7
T_KWALK0, T_KWALK1 = 16.2, 16.9
T_IN = 17.2
T_IGN = 17.4
T_LAUNCH = 17.98
T_BOW = 99.0
T_CROSS = T_TOUCH - 0.37   # the car's nose breaks its tape
T_CUT = T_CROSS - 0.45     # the camera jumps to the finish line
T_STOP = T_CROSS + 0.35
T_STAMP = T_CROSS + 0.7
T_RW = T_CROSS + 0.9       # rewind into frame 0


def scene_t(t):
    if t < T_RW:
        return t
    return T_RW * (1 - smooth(prog(t, T_RW, DUR)))


# ---------------------------------------------------------------- distances (metres)
def m_s(t):
    if t < 0.6:
        return 7.5 * t * t
    if t < 6.0:
        return 2.7 + 9 * (t - 0.6)
    if t < T_STOP_S:
        u = t - 6.0
        return 51.3 + 9 * u - 3.75 * u * u
    if t < T_RUN2:
        return 56.7
    if t < T_RUN2 + 0.8:
        u = t - T_RUN2
        return 56.7 + 0.5 * (8.5 / 0.8) * u * u
    if t < T_CRAMP:
        return 60.1 + 8.5 * (t - T_RUN2 - 0.8)
    m0 = 60.1 + 8.5 * (T_CRAMP - T_RUN2 - 0.8)
    if t < T_FALL:
        u = t - T_CRAMP
        return m0 + 8.5 * u - 10.625 * u * u
    m1 = m0 + 1.7
    if t < T_LIMP:
        return m1
    return m1 + 1.3 * (t - T_LIMP)


def m_c(t):
    if t < 0.6:
        return VJOG * t * t / 1.2
    if t < T_TOUCH:
        return 0.3 * VJOG + VJOG * (t - 0.6)
    u = clamp((t - T_TOUCH) / 0.9)
    return 100 + 1.7 * (1 - (1 - u) ** 2)


CAR_STOP = 640             # world x (centre) where the car parks next to the lounger
CAR_FRONT = 190            # car nose, from its centre
FIN_SX = 600               # screen x of the finish line after the cut
A_END = FIN - FIN_SX - 700  # end of the chase shot: just off screen, left of the finish shot


def car_x(t):
    if t < T_CAR0:
        return -800.0
    if t < T_CAR1:
        u = prog(t, T_CAR0, T_CAR1)
        return lerp(-800, CAR_STOP, 1 - (1 - u) ** 2)
    if t < T_LAUNCH:
        return CAR_STOP
    if t < T_CUT:
        return CAR_STOP + (A_END - CAR_STOP) * prog(t, T_LAUNCH, T_CUT) ** 1.7
    cross = FIN - CAR_FRONT
    if t < T_CROSS:
        return lerp(A_END, cross, prog(t, T_CUT, T_CROSS))
    v = (cross - A_END) / (T_CROSS - T_CUT)
    u = prog(t, T_CROSS, T_STOP)
    return cross + v * (T_STOP - T_CROSS) * 0.5 * (1 - (1 - u) ** 2)


def m_r(t):
    return 100 * clamp((car_x(t) - CAR_STOP) / (FIN - CAR_FRONT - CAR_STOP))


def cam(lane, t):
    if lane == 0:
        return max(0.0, START + m_s(t) * PXM - RUN_SX)
    if lane == 1:
        return max(0.0, START + m_c(t) * PXM - RUN_SX)
    if t < T_LAUNCH:
        return 0.0
    if t < T_CUT:
        return car_x(t) - CAR_STOP
    return FIN - FIN_SX


def cam_v(lane, t):
    return (cam(lane, t + 0.01) - cam(lane, t - 0.01)) / 0.02


# gait phase, integrated over time so the legs never jump
_TG = np.arange(0, DUR + 0.5, 1 / 240)


def _phase(mf):
    m = np.array([mf(t) for t in _TG])
    v = np.gradient(m, _TG)
    L = (150 + 28 * np.abs(v)) / PXM            # metres per stride cycle
    ph = np.concatenate([[0], np.cumsum(2 * np.pi * np.abs(v[:-1]) / L[:-1] * np.diff(_TG))])
    return ph, v


PH_S, V_S = _phase(m_s)
PH_C, V_C = _phase(m_c)
PH_S = PH_S + 1.3            # frame 0 catches both mid-stride
PH_C = PH_C + 0.6


def gait(arr, t):
    return float(np.interp(t, _TG, arr))


def zig_y(wx):
    """the winding road of the middle lane (feet line), in world x"""
    return FEET + 26 * math.sin(2 * math.pi * wx / 760)


# ---------------------------------------------------------------- poses (hip-relative)
STAND = PW.STAND
HANDS_HIP = dict(STAND, el=(-34, -74), hl=(-14, -34), er=(34, -74), hr=(14, -34))
LAUGH = dict(HANDS_HIP, head=(-8, -150), neck=(-4, -108))
BENT = {"head": (66, -112), "neck": (44, -82), "el": (50, -36), "hl": (34, 22), "er": (44, -40), "hr": (28, 18),
        "kl": (22, 54), "fl": (6, 113), "kr": (18, 56), "fr": (-4, 113)}
SIT_G = {"head": (-16, -138), "neck": (-10, -96), "el": (-32, -52), "hl": (-52, -4), "er": (-26, -48), "hr": (-46, 0),
         "kl": (52, -38), "fl": (104, -2), "kr": (46, -32), "fr": (100, 2)}
SIT_DRINK = dict(SIT_G, head=(-24, -136), neck=(-12, -96), er=(10, -86), hr=(-6, -132))
SIT_RELAX = dict(SIT_G, head=(-30, -130), neck=(-22, -92), el=(-60, -112), hl=(-34, -140), er=(-48, -50),
                 hr=(-66, -4), kr=(60, -30), fr=(112, -20))
SIT_PHONE = dict(SIT_G, head=(4, -134), neck=(0, -96), el=(26, -56), hl=(46, -78), er=(22, -52), hr=(42, -74))
HOP = {"head": (18, -146), "neck": (12, -104), "el": (36, -62), "hl": (50, -16), "er": (30, -58), "hr": (46, -12),
       "kl": (8, 56), "fl": (2, 113), "kr": (48, -6), "fr": (24, 42)}
GRAB_HEAD = dict(STAND, el=(-40, -120), hl=(-12, -168), er=(40, -120), hr=(12, -168))
CHEER = dict(STAND, el=(-30, -130), hl=(-40, -180), er=(30, -130), hr=(40, -180))
PRESENT = dict(STAND, er=(40, -86), hr=(84, -96))
WAVE = dict(STAND, er=(30, -130), hr=(40, -180))
RECLINE = {"head": (-64, -126), "neck": (-46, -90), "el": (-86, -112), "hl": (-58, -150), "er": (-8, -58),
           "hr": (26, -84), "kl": (58, -16), "fl": (116, -8), "kr": (56, -10), "fr": (114, -2)}
R_JUICE = dict(RECLINE, er=(-6, -76), hr=(-34, -118))
R_SELFIE = dict(RECLINE, er=(6, -116), hr=(34, -166))
R_FAN = dict(RECLINE, er=(-4, -84), hr=(-24, -126))
R_TAKE = dict(RECLINE, er=(10, -112), hr=(22, -160))
R_EAT = dict(RECLINE, er=(-6, -76), hr=(-36, -116))
R_YAWN = dict(RECLINE, el=(-76, -150), hl=(-70, -200), er=(-30, -150), hr=(-18, -202))
R_WATCH = dict(RECLINE, el=(-16, -70), hl=(-30, -120), er=(-10, -60), hr=(-26, -114))


def run_pose(ph, amp, lean=0.24):
    """a real run cycle: thigh swing, knee folds in early swing, bent arms swinging opposite, torso lean"""
    p = {}
    L = lean * (0.4 + 0.6 * amp)
    p["neck"] = (104 * math.sin(L), -104 * math.cos(L))
    p["head"] = (p["neck"][0] + 42 * math.sin(L * 0.8), p["neck"][1] - 42 * math.cos(L * 0.8))
    for side, off in (("l", 0.0), ("r", math.pi)):
        q = ph + off
        thigh = 0.15 + 0.1 * amp + (0.3 + 0.55 * amp) * math.sin(q)
        flex = 0.32 + (0.5 + 1.6 * amp) * max(0.0, math.cos(q + 0.9)) ** 2
        kx, ky = 56 * math.sin(thigh), 56 * math.cos(thigh)
        sh = thigh - flex
        p["k" + side] = (kx, ky)
        p["f" + side] = (kx + 57 * math.sin(sh), ky + 57 * math.cos(sh))
        a = -(0.3 + 0.85 * amp) * math.sin(q) + L * 0.5
        nx, ny = p["neck"]
        ex, ey = nx + 40 * math.sin(a), ny + 40 * math.cos(a)
        fa = a + 1.35 + 0.25 * amp
        p["e" + side] = (ex, ey)
        p["h" + side] = (ex + 36 * math.sin(fa), ey + 36 * math.cos(fa))
    return p


def walk_pose(ph, amp=0.32):
    p = dict(STAND)
    for side, off in (("l", 0.0), ("r", math.pi)):
        q = ph + off
        a = amp * math.sin(q)
        kx, ky = 56 * math.sin(a), 56 * math.cos(a)
        bend = 0.08 + 0.6 * max(0.0, math.cos(q + 0.6)) ** 2
        p["k" + side] = (kx, ky)
        p["f" + side] = (kx + 57 * math.sin(a - bend), ky + 57 * math.cos(a - bend))
        b = -0.5 * amp * math.sin(q)
        ex, ey = 40 * math.sin(b), -104 + 40 * math.cos(b)
        p["e" + side] = (ex, ey)
        p["h" + side] = (ex + 38 * math.sin(b + 0.3), ey + 38 * math.cos(b + 0.3))
    return p


def grounded(pose, x, feet_y, s=S):
    """hip position so the lowest foot touches the ground"""
    low = max(pose["fl"][1], pose["fr"][1])
    return x, feet_y - low * s


# ---------------------------------------------------------------- the sprinter (world coords)
def sprinter(t):
    """pose, hip (world), facing, extra"""
    x = START + m_s(t) * PXM
    v = gait(V_S, t)
    ph = gait(PH_S, t)
    if t < T_STOP_S or T_RUN2 <= t < T_CRAMP:
        amp = clamp(v / 9.0, 0.3, 1.0)
        if t < 0.6:
            amp = max(amp, 0.8)
        pose = run_pose(ph, amp)
        if t > T_STOP_S - 0.35 and t < T_STOP_S:
            pose = lerp_pose(pose, STAND, smooth(prog(t, T_STOP_S - 0.35, T_STOP_S)))
        if T_RUN2 <= t < T_RUN2 + 0.2:
            pose = lerp_pose(STAND, pose, smooth(prog(t, T_RUN2, T_RUN2 + 0.2)))
        return pose, grounded(pose, x, FEET), 1, None
    if t < T_EASY1:
        k = smooth(prog(t, T_STOP_S, T_STOP_S + 0.3))
        b = 3 * math.sin(t * 16)
        pose = lerp_pose(STAND, dict(LAUGH, head=(-8, -150 + b)), k)
        return pose, grounded(pose, x, FEET), -1 if k > 0.5 else 1, "easy"
    if t < T_PANT1:
        k = smooth(prog(t, T_EASY1, T_EASY1 + 0.3))
        b = 5 * math.sin(t * 13)
        pose = lerp_pose(STAND, dict(BENT, head=(66, -112 + b), neck=(44, -82 + b * 0.6)), k)
        return pose, grounded(pose, x, FEET), 1, "sweat"
    sit_hip = (x, FEET - 12 * S)
    if t < T_SITDOWN:
        k = smooth(prog(t, T_PANT1, T_SITDOWN))
        pose = lerp_pose(BENT, SIT_G, k)
        hy = lerp(grounded(BENT, x, FEET)[1], sit_hip[1], k)
        return pose, (x, hy), 1, "sweat"
    if t < T_DRINK1:
        k = math.sin(math.pi * prog(t, T_DRINK0, T_DRINK1))
        return lerp_pose(SIT_G, SIT_DRINK, min(1, k * 2.2)), sit_hip, 1, "bottle"
    if t < T_RELAX1:
        k = math.sin(math.pi * prog(t, T_DRINK1, T_RELAX1))
        return lerp_pose(SIT_G, SIT_RELAX, min(1, k * 2.2)), sit_hip, 1, None
    if t < T_RUN2 - 0.5:
        k = smooth(prog(t, T_RELAX1, T_RELAX1 + 0.4))
        p = lerp_pose(SIT_G, SIT_PHONE, k)
        if t >= T_ALERT:
            p = dict(p, head=(12, -142))
        return p, sit_hip, 1, "phone"
    if t < T_RUN2:
        k = smooth(prog(t, T_RUN2 - 0.5, T_RUN2))
        return lerp_pose(SIT_PHONE, STAND, k), (x, lerp(sit_hip[1], grounded(STAND, x, FEET)[1], k)), 1, None
    if t < T_FALL:
        hop = 14 * abs(math.sin((t - T_CRAMP) * 14))
        hx, hy = grounded(HOP, x, FEET)
        return HOP, (hx, hy - hop), 1, "ow"
    if t < T_UP:
        k = smooth(prog(t, T_FALL, T_FALL + 0.18))
        return lerp_pose(HOP, SIT_G, k), (x, lerp(grounded(HOP, x, FEET)[1], sit_hip[1], k)), 1, "ow"
    if t < T_LIMP:
        k = smooth(prog(t, T_UP, T_LIMP))
        return lerp_pose(SIT_G, STAND, k), (x, lerp(sit_hip[1], grounded(STAND, x, FEET)[1], k)), 1, None
    ph = 2 * math.pi * (t - T_LIMP) * 1.1
    p = walk_pose(ph, 0.28)
    p["head"] = (10, -146)
    p["neck"] = (6, -104)
    hx, hy = grounded(p, x, FEET)
    return p, (hx, hy + 5 * max(0.0, math.sin(ph))), 1, "sweat"


# ---------------------------------------------------------------- the consistent one
def depth(y):
    return S * (1 + (y - FEET) / 26 * 0.05)


def consistent(t):
    x = START + m_c(t) * PXM
    y = zig_y(x)
    s = depth(y)
    ph = gait(PH_C, t)
    if t >= T_TOUCH + 0.9:
        k = smooth(prog(t, T_TOUCH + 0.9, T_TOUCH + 1.2))
        p = lerp_pose(STAND, GRAB_HEAD, k)
        return p, grounded(p, x, y, s), 1, s
    amp = 0.55 if t < T_TOUCH else 0.55 * (1 - prog(t, T_TOUCH, T_TOUCH + 0.9))
    rainy = T_RAIN0 + 0.3 <= t < T_RAIN1
    p = run_pose(ph, max(0.2, amp), lean=0.32 if rainy else 0.18)
    if t >= T_TOUCH + 0.6:
        p = lerp_pose(p, STAND, smooth(prog(t, T_TOUCH + 0.6, T_TOUCH + 0.9)))
    if T_REACH <= t < T_TOUCH + 0.3:
        k = smooth(prog(t, T_REACH, T_REACH + 0.35))
        p["er"] = (lerp(p["er"][0], 50, k), lerp(p["er"][1], -104, k))
        p["hr"] = (lerp(p["hr"][0], 92, k), lerp(p["hr"][1], -108, k))
    return p, grounded(p, x, y, s), 1, s


# ---------------------------------------------------------------- the rich kid
LOUNGE_X = 380             # world x (lounger centre), foreground
LOUNGE_Y = 444
KID_HIP = (LOUNGE_X - 6, LOUNGE_Y - 42)


def rich(t):
    """pose, hip, facing, prop (None when he is in the car)"""
    hip = KID_HIP
    if t < T_KEYS1:
        return RECLINE, hip, 1, "keys"
    if t < T_JUICE1:
        k = math.sin(math.pi * prog(t, T_KEYS1, T_JUICE1))
        return lerp_pose(RECLINE, R_JUICE, min(1, k * 2)), hip, 1, "juice"
    if t < T_FAN0:
        k = math.sin(math.pi * prog(t, T_JUICE1, T_FAN0))
        return lerp_pose(RECLINE, R_SELFIE, min(1, k * 2)), hip, 1, "phone"
    if t < T_FAN1:
        k = math.sin(math.pi * prog(t, T_FAN0, T_FAN1))
        p = lerp_pose(RECLINE, R_FAN, min(1, k * 2.5))
        w = 12 * math.sin(t * 22) * min(1, k * 2.5)
        p["hr"] = (p["hr"][0] + w, p["hr"][1] + w * 0.3)
        return p, hip, 1, "cash"
    if t < T_DRONE_HAND:
        k = smooth(prog(t, T_DRONE_HAND - 0.5, T_DRONE_HAND))
        return lerp_pose(RECLINE, R_TAKE, k), hip, 1, "box" if t >= T_DRONE_HAND - 0.02 else None
    if t < T_EAT1:
        k = smooth(prog(t, T_DRONE_HAND, T_DRONE_HAND + 0.4))
        p = lerp_pose(R_TAKE, R_EAT, k)
        ch = 4 * math.sin(t * 18) if t > T_DRONE_HAND + 0.5 else 0
        p["head"] = (p["head"][0], p["head"][1] + ch)
        return p, hip, 1, "slice"
    if t < T_YAWN1:
        k = math.sin(math.pi * prog(t, T_EAT1, T_YAWN1))
        return lerp_pose(RECLINE, R_YAWN, min(1, k * 1.6)), hip, 1, None
    if t < T_KSTAND:
        k = math.sin(math.pi * prog(t, T_YAWN1, T_WATCH1)) if t < T_WATCH1 else 0.0
        return lerp_pose(RECLINE, R_WATCH, min(1, k * 2.2)), hip, 1, "watch" if t < T_WATCH1 else None
    st = grounded(STAND, LOUNGE_X + 40, LOUNGE_Y)
    if t < T_KWALK0:
        k = smooth(prog(t, T_KSTAND, T_KWALK0))
        return lerp_pose(RECLINE, STAND, k), (lerp(hip[0], st[0], k), lerp(hip[1], st[1], k)), 1, None
    door = CAR_STOP - 70
    if t < T_KWALK1:
        u = smooth(prog(t, T_KWALK0, T_KWALK1))
        p = walk_pose((t - T_KWALK0) * 9, 0.32)
        x = lerp(st[0], door, u)
        fy = lerp(LOUNGE_Y, FEET + 4, u)
        return p, grounded(p, x, fy), 1, None
    if t < T_IN:
        u = prog(t, T_KWALK1, T_IN)
        g = grounded(STAND, door, FEET + 4)
        return lerp_pose(STAND, CHEER, math.sin(math.pi * u)), (g[0], g[1] - 40 * math.sin(math.pi * u)), 1, "hop"
    return None


def chauffeur(t):
    if t < T_CHAUF:
        return None
    x = CAR_STOP + 70
    if t < T_CHAUF + 0.3:
        k = smooth(prog(t, T_CHAUF, T_CHAUF + 0.3))
        return STAND, grounded(STAND, x, FEET + 22), k
    if t < T_IN:
        return PRESENT, grounded(PRESENT, x, FEET + 22), 1.0
    k = math.sin(math.pi * prog(t, T_LAUNCH, T_LAUNCH + 0.8)) if t >= T_LAUNCH else 0
    p = lerp_pose(STAND, WAVE, k)
    if t >= T_LAUNCH:
        p["hr"] = (p["hr"][0] + 12 * math.sin(t * 20) * k, p["hr"][1])
    return p, grounded(p, x, FEET + 22), 1.0


# ---------------------------------------------------------------- drawing helpers
def figure(d, pts, s, acc, facing=1, alpha=255, body=WHITE):
    lw0, lw1 = 19 * s, 12.5 * s
    for w, col in ((lw0, INK), (lw1, body)):
        for b0, b1 in [("neck", "hip"), ("neck", "el"), ("el", "hl"), ("neck", "er"), ("er", "hr"), ("hip", "kl"),
                       ("kl", "fl"), ("hip", "kr"), ("kr", "fr")]:
            (x0, y0), (x1, y1) = pts[b0], pts[b1]
            d.line([x0 * K, y0 * K, x1 * K, y1 * K], fill=col + (alpha,), width=int(w * K))
            for x, y in ((x0, y0), (x1, y1)):
                r = w * K / 2
                d.ellipse([x * K - r, y * K - r, x * K + r, y * K + r], fill=col + (alpha,))
    hx, hy = pts["head"]
    for r, col in ((31 * s, INK), (25.5 * s, body)):
        d.ellipse([(hx - r) * K, (hy - r) * K, (hx + r) * K, (hy + r) * K], fill=col + (alpha,))
    f = facing
    if acc == "band":
        d.line([(hx - 26 * s) * K, (hy - 9 * s) * K, (hx + 26 * s) * K, (hy - 9 * s) * K], fill=RED + (255,),
               width=int(9 * s * K))
        for j in (0, 1):
            ex = hx - f * (50 + 8 * j) * s
            d.line([(hx - f * 22 * s) * K, (hy - 9 * s) * K, ex * K, (hy + (-4 + 14 * j) * s) * K], fill=RED + (255,),
                   width=int(6 * s * K))
    elif acc == "cap":
        d.chord([(hx - 27 * s) * K, (hy - 32 * s) * K, (hx + 27 * s) * K, (hy + 14 * s) * K], 180, 360,
                fill=(50, 110, 220, 255), outline=INK + (255,), width=int(2 * K))
        x0, x1 = (hx, hx + 42 * s) if f > 0 else (hx - 42 * s, hx)
        d.rectangle([x0 * K, (hy - 12 * s) * K, x1 * K, (hy - 4 * s) * K], fill=(50, 110, 220, 255),
                    outline=INK + (255,), width=int(1.5 * K))
    elif acc == "rich":
        x0, x1 = (hx - 4 * s, hx + 28 * s) if f > 0 else (hx - 28 * s, hx + 4 * s)
        d.rounded_rectangle([x0 * K, (hy - 11 * s) * K, x1 * K, (hy + 3 * s) * K], int(3 * K), fill=(15, 15, 20, 255))
        nx, ny = pts["neck"]
        d.arc([(nx - 20 * s) * K, (ny - 16 * s) * K, (nx + 20 * s) * K, (ny + 20 * s) * K], 20, 160,
              fill=GOLD + (255,), width=int(4 * K))
    elif acc == "chauffeur":
        a = alpha
        d.rectangle([(hx - 24 * s) * K, (hy - 40 * s) * K, (hx + 24 * s) * K, (hy - 16 * s) * K], fill=(20, 20, 26, a))
        d.rectangle([(hx - 28 * s) * K, (hy - 20 * s) * K, (hx + 34 * s) * K, (hy - 13 * s) * K], fill=(20, 20, 26, a))
        nx, ny = pts["neck"]
        d.polygon([((nx - 10 * s) * K, (ny - 4 * s) * K), ((nx + 10 * s) * K, (ny + 4 * s) * K),
                   ((nx + 10 * s) * K, (ny - 4 * s) * K), ((nx - 10 * s) * K, (ny + 4 * s) * K)], fill=(20, 20, 26, a))


def text_c(d, x, y, s, size, col, stroke=0, stroke_col=INK, a=255):
    f = font(BOLD, max(4, int(size * K)))
    tw = f.getlength(s)
    d.text((x * K - tw / 2, y * K), s, font=f, fill=col + (int(a),), stroke_width=int(stroke * K),
           stroke_fill=stroke_col + (int(a),))


def bubble(lay, t, t0, t1, s, x, y, size=34):
    if not (t0 <= t < t1):
        return
    k = hq.pop(t, t0, 0.22) * (1 - smooth(prog(t, t1 - 0.15, t1)))
    if k < 0.05:
        return
    f = font(BOLD, max(4, int(size * K * k)))
    tw = f.getlength(s)
    bw, bh = tw + 36 * K * k, size * 1.75 * K * k
    d = ImageDraw.Draw(lay)
    x0, y0 = x * K - bw / 2, y * K - bh
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], int(14 * K * k), fill=(255, 255, 255, 250), outline=INK + (255,),
                        width=int(3 * K))
    d.polygon([(x * K - 12 * K * k, y0 + bh - 2), (x * K + 12 * K * k, y0 + bh - 2),
               (x * K - 4 * K * k, y0 + bh + 18 * K * k)], fill=(255, 255, 255, 250), outline=INK + (255,))
    d.text((x0 + 18 * K * k, y0 + 7 * K * k), s, font=f, fill=INK + (255,))


def stamp(base, t, t0, t1, s, col, x, y, size=74):
    if not (t0 <= t < t1):
        return
    k = hq.pop(t, t0, 0.28) * (1 - smooth(prog(t, t1 - 0.2, t1)))
    if k < 0.05:
        return
    f = font(BOLD, max(4, int(size * K * k)))
    tw = sum(f.getlength(c) for c in s) + 4 * K * k * (len(s) - 1)
    lay = Image.new("RGBA", (int(tw + 70 * K * k), int(size * 1.55 * K * k)), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle([0, 0, lay.width - 1, lay.height - 1], int(18 * K * k), fill=(255, 255, 255, 245),
                         outline=col + (255,), width=int(9 * K * k))
    xx = lay.width / 2 - tw / 2
    for c in s:
        ld.text((xx, lay.height / 2 - size * 0.62 * K * k), c, font=f, fill=col + (255,))
        xx += f.getlength(c) + 4 * K * k
    lay = lay.rotate(-6, resample=Image.BICUBIC, expand=True)
    base.alpha_composite(lay, (int(x * K - lay.width / 2), int(y * K - lay.height / 2)))


# ---------------------------------------------------------------- backgrounds
def make_sky(lane):
    a = np.zeros((PHT * K, PWD * K, 3), np.float32)
    yy = np.arange(PHT * K)[:, None] / K
    sky = np.clip(yy / HORIZON, 0, 1)
    c0, c1 = np.array([8, 12, 30]), np.array([30, 44, 86])
    g0, g1 = np.array([26, 38, 60]), np.array([12, 18, 32])
    gk = np.clip((yy - HORIZON) / (PHT - HORIZON), 0, 1)
    for c in range(3):
        a[..., c] = np.where(yy < HORIZON, c0[c] * (1 - sky) + c1[c] * sky, g0[c] * (1 - gk) + g1[c] * gk)
    im = Image.fromarray(a.astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(lane + 3)
    for _ in range(100):
        x, y = rng.uniform(0, PWD), rng.uniform(0, HORIZON - 40)
        r = rng.uniform(0.7, 2.0)
        d.ellipse([(x - r) * K, (y - r) * K, (x + r) * K, (y + r) * K], fill=(220, 228, 255, int(rng.uniform(70, 220))))
    mx, my = 640, 96
    halo = Image.new("RGBA", im.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    for r, a_ in ((210, 14), (160, 18), (115, 26), (80, 34)):
        hd.ellipse([(mx - r) * K, (my - r) * K, (mx + r) * K, (my + r) * K], fill=(110, 140, 220, a_))
    im.alpha_composite(halo)
    d.ellipse([(mx - 44) * K, (my - 44) * K, (mx + 44) * K, (my + 44) * K], fill=(240, 236, 214, 255))
    for cx, cy, r in ((-14, -10, 10), (12, 8, 8), (-6, 18, 6), (16, -16, 5)):
        d.ellipse([(mx + cx - r) * K, (my + cy - r) * K, (mx + cx + r) * K, (my + cy + r) * K], fill=(214, 208, 186, 255))
    d.polygon([(0, (HORIZON - 30) * K), (200 * K, (HORIZON - 70) * K), (420 * K, (HORIZON - 24) * K),
               (650 * K, (HORIZON - 80) * K), (880 * K, (HORIZON - 30) * K), (PWD * K, (HORIZON - 64) * K),
               (PWD * K, HORIZON * K), (0, HORIZON * K)], fill=(14, 20, 38, 255))
    return im


def _hash(k, lane, salt):
    return ((k * 73856093) ^ (lane * 19349663) ^ (salt * 83492791)) % 1000 / 1000.0


SIGN_FMT = lambda mk: f"{mk} M"   # noqa: E731 (versus.py overrides it)


def draw_world(d, lane, c, vc):
    """everything that scrolls: trees (parallax), the road and its dashes, grass, start, distance signs"""
    pc, pv = c * 0.45, abs(vc) * 0.45
    stretch = min(500.0, pv / 28.0)
    a_tree = int(255 * (1 - min(0.6, stretch / 600)))
    for k in range(int((pc - 700) // 150), int((pc + PWD + 200) // 150) + 1):
        tx = k * 150 + 60 * _hash(k, lane, 1) - pc
        th = 34 + 26 * _hash(k, lane, 2)
        ty = HORIZON + 6
        d.rectangle([(tx - 4) * K, (ty - 22) * K, (tx + 4 + stretch) * K, ty * K], fill=(10, 14, 26, a_tree))
        d.rounded_rectangle([(tx - 22) * K, (ty - 22 - th * 1.6) * K, (tx + 22 + stretch) * K, (ty - 18) * K],
                            int(20 * K), fill=(12, 18, 34, a_tree))
    if lane == 1:
        xs = np.linspace(-60, PWD + 60, 300)
        for hw, col in ((30, INK), (26.5, (84, 80, 98))):
            up = [(x * K, (zig_y(x + c) - hw) * K) for x in xs]
            dn = [(x * K, (zig_y(x + c) + hw) * K) for x in xs[::-1]]
            d.polygon(up + dn, fill=col + (255,))
        for k in range(int((c - 40) // 34), int((c + PWD + 40) // 34) + 1):
            wx = k * 34 + 20 * _hash(k, 1, 3)
            sx = wx - c
            yy = zig_y(wx) - 14 + 28 * _hash(k, 1, 4)
            d.ellipse([(sx - 3) * K, (yy - 3) * K, (sx + 3) * K, (yy + 3) * K], fill=(60, 58, 74, 255))
    else:
        d.rectangle([0, (FEET - 40) * K, PWD * K, (FEET + 32) * K], fill=(34, 38, 54, 255), outline=INK + (255,),
                    width=int(3 * K))
        dl = 60 + min(700.0, abs(vc) / 30.0)
        for k in range(int((c - 800) // 130), int((c + PWD) // 130) + 1):
            sx = k * 130 - c
            d.rectangle([sx * K, (FEET - 6) * K, (sx + dl) * K, (FEET - 1) * K], fill=(170, 180, 210, 170))
    for k in range(int((c - 40) // 46), int((c + PWD + 40) // 46) + 1):
        gx = k * 46 + 30 * _hash(k, lane, 5) - c
        gy = FEET + 50 + (PHT - FEET - 56) * _hash(k, lane, 6)
        for dx in (-5, 0, 5):
            d.line([gx * K, gy * K, (gx + dx * 1.6) * K, (gy - 13) * K], fill=(36, 54, 70, 255), width=int(2 * K))
    sx = START - c
    if -60 < sx < PWD + 60:
        fy = zig_y(START) if lane == 1 else FEET
        d.polygon([((sx + 14) * K, (fy - 36) * K), ((sx + 26) * K, (fy - 36) * K), ((sx + 2) * K, (fy + 28) * K),
                   ((sx - 10) * K, (fy + 28) * K)], fill=(235, 238, 248, 255))
    for mk in (25, 50, 75):
        wx = START + mk * PXM
        sx = wx - c
        if -120 < sx < PWD + 120:
            fy = (zig_y(wx) if lane == 1 else FEET) - 46
            d.rectangle([(sx - 3) * K, (fy - 70) * K, (sx + 3) * K, fy * K], fill=(150, 156, 176, 255))
            d.rounded_rectangle([(sx - 40) * K, (fy - 108) * K, (sx + 40) * K, (fy - 66) * K], int(8 * K),
                                fill=(36, 120, 70, 255), outline=(220, 230, 240, 255), width=int(2 * K))
            text_c(d, sx, fy - 104, SIGN_FMT(mk), 26 if len(SIGN_FMT(mk)) < 6 else 20, (240, 244, 250))


def finish(d, lane, c, broken_at, t):
    """checkered strip, flag and tape at world FIN; returns the front post (drawn last) or None"""
    fx = FIN - c
    if not (-160 < fx < PWD + 200):
        return None
    fy = zig_y(FIN) if lane == 1 else FEET
    for r in range(7):
        for cc in range(2):
            y0 = fy - 38 + r * 10
            x0 = fx + 18 - r * 10 * 0.5 + cc * 12 - 6
            col = (240, 240, 244, 255) if (r + cc) % 2 == 0 else (20, 20, 24, 255)
            d.polygon([(x0 * K, y0 * K), ((x0 + 12) * K, y0 * K), ((x0 + 12 - 5) * K, (y0 + 10) * K),
                       ((x0 - 5) * K, (y0 + 10) * K)], fill=col)
    back = (fx + 22, fy - 38)
    front = (fx - 12, fy + 30)
    d.rectangle([(back[0] - 4) * K, (back[1] - 230) * K, (back[0] + 4) * K, back[1] * K], fill=(230, 232, 240, 255),
                outline=INK + (255,), width=int(2 * K))
    wav = 5 * math.sin(t * 5)
    for r in range(4):
        for cc in range(6):
            x0 = back[0] + 4 + cc * 15
            y0 = back[1] - 230 + r * 14 + wav * cc / 6
            col = (240, 240, 244, 255) if (r + cc) % 2 == 0 else (20, 20, 24, 255)
            d.rectangle([x0 * K, y0 * K, (x0 + 15) * K, (y0 + 14) * K], fill=col)
    hb = (back[0], back[1] - 84)
    hf = (front[0], front[1] - 84)
    if broken_at is None or t < broken_at:
        d.line([hb[0] * K, hb[1] * K, hf[0] * K, hf[1] * K], fill=RED + (255,), width=int(6 * K))
    else:
        u = clamp((t - broken_at) / 0.4)
        for p0, sgn in ((hb, 1), (hf, -1)):
            ang = math.pi / 2 * (0.3 + 0.7 * u)
            ex = p0[0] + sgn * 50 * math.cos(ang) * 0.8 + 24 * (1 - u)
            ey = p0[1] + 50 * math.sin(ang)
            d.line([p0[0] * K, p0[1] * K, ex * K, ey * K], fill=RED + (255,), width=int(6 * K))
    return front


def front_pole(d, front):
    if front:
        d.rectangle([(front[0] - 4) * K, (front[1] - 110) * K, (front[0] + 4) * K, front[1] * K],
                    fill=(230, 232, 240, 255), outline=INK + (255,), width=int(2 * K))


# ---------------------------------------------------------------- props
CXS, CYS = 1.27, 0.95       # the car is drawn 1.27x longer, 0.95x taller than the base shape (~380 x 115 px)


def draw_car(d, cx, gy, t, bow, driver, vib=0.0, moving=0.0, chauffeur_in=False):
    cy = gy - 3 * vib * math.sin(t * 60)

    def P(x, y):
        return ((cx + x * CXS) * K, (cy + y * CYS) * K)
    if moving > 0.05:
        for j in range(6):
            y = -30 - j * 14
            L = 140 + 80 * (j % 2)
            d.line([P(-170 - L * moving, y), P(-160, y)], fill=(230, 236, 255, int(200 * moving)), width=int(3 * K))
    body = [(-152, -36), (152, -36), (158, -58), (70, -78), (10, -118), (-66, -118), (-126, -86), (-156, -80)]
    d.polygon([P(*p) for p in body], fill=CAR + (255,), outline=INK + (255,), width=int(3 * K))
    d.line([P(-140, -60), P(140, -60)], fill=(255, 110, 110, 255), width=int(3 * K))
    if driver or chauffeur_in:
        hx, hy = P(-22, -94)
        hx, hy = hx / K, hy / K
        r = 18
        d.ellipse([(hx - r) * K, (hy - r) * K, (hx + r) * K, (hy + r) * K], fill=WHITE + (255,), outline=INK + (255,),
                  width=int(2 * K))
        if driver:
            d.rounded_rectangle([(hx - 2) * K, (hy - 7) * K, (hx + 18) * K, (hy + 2) * K], int(2 * K),
                                fill=(15, 15, 20, 255))
        else:
            d.rectangle([(hx - 15) * K, (hy - 26) * K, (hx + 15) * K, (hy - 10) * K], fill=(20, 20, 26, 255))
    win = [(58, -80), (6, -112), (-60, -112), (-104, -82)]
    d.polygon([P(*p) for p in win], fill=(150, 210, 245, 95), outline=INK + (255,), width=int(2 * K))
    d.line([P(-24, -112), P(-24, -80)], fill=INK + (255,), width=int(2 * K))
    d.rectangle([P(-160, -100), P(-118, -92)], fill=(40, 40, 46, 255))
    d.line([P(-138, -92), P(-132, -84)], fill=(40, 40, 46, 255), width=int(3 * K))
    d.ellipse([P(140, -58), P(156, -46)], fill=(255, 240, 150, 255), outline=INK + (255,), width=int(2 * K))
    hx0, hy0 = P(156, -52)
    d.polygon([(hx0, hy0), (hx0 + 220 * K, hy0 - 26 * K), (hx0 + 220 * K, hy0 + 40 * K)], fill=(255, 240, 170, 40))
    for wx in (-96, 100):
        r = 30
        cxw, cyw = P(wx, -2)
        d.ellipse([cxw - r * K, cyw - r * K, cxw + r * K, cyw + r * K], fill=(24, 24, 28, 255), outline=INK + (255,),
                  width=int(2 * K))
        d.ellipse([cxw - 15 * K, cyw - 15 * K, cxw + 15 * K, cyw + 15 * K], fill=(190, 194, 204, 255))
        rot = -(cx / 30)
        for j in range(5):
            a = rot + j * 2 * math.pi / 5
            d.line([cxw, cyw, cxw + 13 * K * math.cos(a), cyw + 13 * K * math.sin(a)], fill=(90, 94, 104, 255),
                   width=int(3 * K))
    if bow is not None:
        bx, by, ang, al = bow
        if al > 0.02:
            a = int(255 * al)
            if bx is None:
                band = [(-30, -118), (-16, -118), (-14, -36), (-32, -36)]
                d.polygon([P(*p) for p in band], fill=GOLD + (a,), outline=INK + (a,))
                bx, by = P(-23, -120)
                bx, by = bx / K, by / K
            c, s = math.cos(ang), math.sin(ang)

            def Q(x, y):
                x, y = x * 0.75, y * 0.75
                return ((bx + x * c - y * s) * K, (by + x * s + y * c) * K)
            for sg in (-1, 1):
                d.polygon([Q(0, 0), Q(sg * 46, -36), Q(sg * 54, 6)], fill=(255, 90, 160, a), outline=INK + (a,),
                          width=int(2 * K))
                d.line([Q(0, 0), Q(sg * 26, 34)], fill=(255, 90, 160, a), width=int(6 * K))
            d.ellipse([(bx - 9) * K, (by - 9) * K, (bx + 9) * K, (by + 9) * K], fill=(230, 60, 140, a),
                      outline=INK + (a,), width=int(2 * K))


def lounger(d, x, y):
    sc = 0.8

    def P(a, b):
        return ((x + a * sc) * K, (y + b * sc) * K)
    d.line([P(-120, 0), P(-100, -44)], fill=INK + (255,), width=int(4 * K))
    d.line([P(110, 0), P(94, -44)], fill=INK + (255,), width=int(4 * K))
    d.polygon([P(-110, -58), P(120, -58), P(120, -44), P(-110, -44)], fill=(230, 120, 50, 255), outline=INK + (255,))
    d.polygon([P(-70, -58), P(-56, -46), P(-122, -160), P(-138, -150)], fill=(230, 120, 50, 255), outline=INK + (255,))
    for j in range(1, 5):
        xx = -110 + j * 46
        d.line([P(xx, -58), P(xx, -44)], fill=(255, 210, 120, 255), width=int(3 * K))


def keys(d, hx, hy, t):
    a = t * 14
    kx, ky = hx + 22 * math.cos(a), hy + 22 * math.sin(a)
    d.ellipse([(hx - 9) * K, (hy - 9) * K, (hx + 9) * K, (hy + 9) * K], outline=GOLD + (255,), width=int(3 * K))
    d.line([hx * K, hy * K, kx * K, ky * K], fill=GOLD + (255,), width=int(3 * K))
    d.rounded_rectangle([(kx - 12) * K, (ky - 7) * K, (kx + 12) * K, (ky + 7) * K], int(3 * K), fill=(20, 20, 24, 255),
                        outline=GOLD + (255,), width=int(2 * K))
    d.ellipse([(kx + 3) * K, (ky - 3) * K, (kx + 8) * K, (ky + 3) * K], fill=(255, 60, 60, 255))


def drone(d, x, y, t, box):
    for sx in (-26, 26):
        d.ellipse([(x + sx - 20) * K, (y - 13) * K, (x + sx + 20) * K, (y - 7) * K], fill=(200, 200, 210, 140))
        d.line([(x + sx) * K, (y - 10) * K, (x + sx) * K, y * K], fill=INK + (255,), width=int(2 * K))
    d.rounded_rectangle([(x - 27) * K, (y - 2) * K, (x + 27) * K, (y + 9) * K], int(4 * K), fill=(60, 64, 76, 255),
                        outline=INK + (255,), width=int(2 * K))
    d.ellipse([(x + 17) * K, (y + 1) * K, (x + 23) * K, (y + 7) * K], fill=(255, 60, 60, 255))
    if box:
        d.line([x * K, (y + 9) * K, x * K, (y + 28) * K], fill=INK + (255,), width=int(2 * K))
        pizza_box(d, x, y + 36)


def pizza_box(d, x, y):
    d.rectangle([(x - 24) * K, (y - 8) * K, (x + 24) * K, (y + 8) * K], fill=(230, 200, 150, 255),
                outline=INK + (255,), width=int(2 * K))
    text_c(d, x, y - 7, "PIZZA", 10, (200, 40, 40))


def slice_(d, x, y):
    d.polygon([((x - 10) * K, (y - 7) * K), ((x + 12) * K, (y - 11) * K), ((x + 1) * K, (y + 15) * K)],
              fill=(255, 200, 70, 255), outline=INK + (255,), width=int(2 * K))
    d.line([(x - 10) * K, (y - 7) * K, (x + 12) * K, (y - 11) * K], fill=(200, 130, 60, 255), width=int(4 * K))


def cash_fan(d, x, y):
    for j in range(5):
        a = -0.9 + j * 0.42
        ex, ey = x + 32 * math.sin(a), y - 32 * math.cos(a)
        d.line([x * K, y * K, ex * K, ey * K], fill=(70, 160, 80, 255), width=int(12 * K))
        d.line([x * K, y * K, ex * K, ey * K], fill=(150, 220, 140, 255), width=int(7 * K))


def bottle(d, x, y, ang=0.0):
    c, s = math.cos(ang), math.sin(ang)

    def P(a, b):
        return ((x + a * c - b * s) * K, (y + a * s + b * c) * K)
    d.polygon([P(-6, -4), P(6, -4), P(6, 26), P(-6, 26)], fill=(120, 190, 255, 230), outline=INK + (255,))
    d.polygon([P(-3, -12), P(3, -12), P(3, -4), P(-3, -4)], fill=(240, 240, 250, 255), outline=INK + (255,))


def phone_(d, x, y, lit=True):
    d.rounded_rectangle([(x - 7) * K, (y - 12) * K, (x + 7) * K, (y + 12) * K], int(3 * K), fill=(20, 20, 26, 255),
                        outline=INK + (255,))
    if lit:
        d.rectangle([(x - 5) * K, (y - 9) * K, (x + 5) * K, (y + 9) * K], fill=(140, 200, 255, 255))


def sweat(d, pts, t, f):
    hx, hy = pts["head"]
    for j in range(2):
        u = (t * 1.8 + j * 0.5) % 1.0
        x, y = hx - f * (20 + 10 * u) + j * 8, hy - 8 + 28 * u
        a = int(255 * (1 - u))
        d.polygon([(x * K, (y - 6) * K), ((x + 4) * K, (y + 2) * K), ((x - 4) * K, (y + 2) * K)], fill=(120, 200, 255, a))
        d.ellipse([(x - 4) * K, (y - 1) * K, (x + 4) * K, (y + 6) * K], fill=(120, 200, 255, a))


def rain(d, cx, cy, t, t0, t1):
    if not (t0 <= t < t1):
        return
    a = smooth(prog(t, t0, t0 + 0.4)) * (1 - smooth(prog(t, t1 - 0.4, t1)))
    for dx, dy, r in ((-50, 8, 30), (-16, -5, 38), (26, 0, 36), (60, 10, 26)):
        d.ellipse([(cx + dx - r) * K, (cy + dy - r * 0.8) * K, (cx + dx + r) * K, (cy + dy + r * 0.8) * K],
                  fill=(90, 96, 116, int(250 * a)), outline=INK + (int(255 * a),), width=int(2 * K))
    rng = np.random.default_rng(7)
    for j in range(30):
        x0 = cx + rng.uniform(-90, 90)
        sp = rng.uniform(500, 700)
        ph = rng.uniform(0, 1)
        y = cy + 20 + ((t * sp / 300 + ph) % 1.0) * (FEET + 20 - cy)
        d.line([x0 * K, y * K, (x0 - 6) * K, (y + 18) * K], fill=(110, 160, 240, int(220 * a)), width=int(2 * K))


def speed_lines(d, t, v):
    if v < 1500:
        return
    a = clamp((v - 1500) / 3000)
    rng = np.random.default_rng(int(t * 60))
    for _ in range(14):
        y = rng.uniform(40, PHT - 20)
        x = rng.uniform(-200, PWD)
        L = rng.uniform(120, 360)
        d.line([x * K, y * K, (x + L) * K, y * K], fill=(220, 230, 255, int(120 * a)), width=int(2 * K))


# ---------------------------------------------------------------- panel
SKY = None


def tag(base, lab):
    tl = ImageDraw.Draw(base)
    f = font("Inter-SemiBold.otf", int(32 * K))
    x = 28 * K
    for c in lab:
        tl.text((x, 18 * K), c, font=f, fill=(196, 204, 226, 255))
        x += f.getlength(c) + 9 * K


class _Pp:
    """adapter so hq.confetti can draw on our 2x layer"""

    def __init__(self, d):
        self.ds = d


def W2S(pts, c):
    return {k: (x - c, y) for k, (x, y) in pts.items()}


def panel(t, st, lane):
    base = SKY[lane].copy()
    lay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    c = cam(lane, st)
    vc = cam_v(lane, st)
    draw_world(d, lane, c, vc)
    focus = (PWD / 2, PHT / 2)
    ev = []
    if lane == 0:
        front = finish(d, 0, c, None, st)
        pose, hip, f, extra = sprinter(st)
        pts = W2S(AJ.place(pose, hip, f, S), c)
        if st < T_STOP_S - 0.3 or T_RUN2 + 0.2 <= st < T_CRAMP:
            ph = gait(PH_S, st)
            for j in range(3):
                u = ((ph / (2 * math.pi) * 2 + j / 3) % 1.0)
                px = pts["hip"][0] - 30 - 70 * u
                r = 5 + 12 * u
                d.ellipse([(px - r) * K, (FEET - r) * K, (px + r) * K, (FEET + r * 0.5) * K],
                          fill=(120, 130, 160, int(120 * (1 - u))))
        figure(d, pts, S, "band", f)
        focus = (pts["hip"][0] + 10, (pts["head"][1] + FEET) / 2)
        hx, hy = pts["head"]
        if extra == "sweat":
            sweat(d, pts, st, f)
        if extra == "bottle":
            k = math.sin(math.pi * prog(st, T_DRINK0, T_DRINK1))
            bottle(d, pts["hr"][0], pts["hr"][1] - 6, -2.4 * min(1, k * 2.2))
        if extra == "phone":
            phone_(d, pts["hr"][0] + 4, pts["hr"][1] - 10)
        if T_ALERT <= st < T_RUN2 + 0.3:
            k = hq.pop(st, T_ALERT, 0.2)
            text_c(d, hx + 6, hy - 50 - 30 * k, "!", 70 * k + 4, RED, stroke=4)
        bubble(lay, st, T_STOP_S + 0.1, T_EASY1, "EASY!", hx, hy - 36)
        bubble(lay, st, T_CRAMP + 0.05, T_LIMP - 0.1, "OW!", hx + 14, hy - 36)
        front_pole(d, front)
        ev = [T_CRAMP, T_FALL]
    elif lane == 1:
        front = finish(d, 1, c, T_TOUCH, st)
        pose, hip, f, s = consistent(st)
        pts = W2S(AJ.place(pose, hip, f, s), c)
        figure(d, pts, s, "cap", f)
        focus = (pts["hip"][0] + 10, (pts["head"][1] + max(pts["fl"][1], pts["fr"][1])) / 2)
        if T_RAIN0 + 0.3 <= st < T_RAIN1:
            for j in range(2):
                u = ((st * 2.4 + j / 2) % 1.0)
                fx_, fy_ = pts["fl"] if j else pts["fr"]
                r = 6 + 20 * u
                d.ellipse([(fx_ - r) * K, (fy_ - r * 0.25) * K, (fx_ + r) * K, (fy_ + r * 0.25) * K],
                          outline=(200, 220, 255, int(200 * (1 - u))), width=int(2 * K))
        rain(d, pts["head"][0] + 10, 70, st, T_RAIN0, T_RAIN1)
        if st >= T_REACH - 1.0:
            sweat(d, pts, st, f)
        front_pole(d, front)
        ev = [T_TOUCH]
    else:
        front = finish(d, 2, c, T_CROSS, st)
        cx = car_x(st) - c
        moving = 1.0 if T_LAUNCH + 0.15 <= st < T_STOP else 0.0
        if T_CROSS <= st < T_STOP:
            moving = 1 - prog(st, T_CROSS, T_STOP)
        vib = 1.0 if T_IGN <= st < T_LAUNCH + 0.15 else 0.0
        bow = (None, None, 0.0, 1.0)
        if T_IGN <= st < T_STOP + 0.4:
            for j in range(5):
                u = ((st * (1.6 if st < T_LAUNCH else 0.8) + j / 5) % 1.0)
                px, py = cx - 160 * CXS - 50 * u, FEET - 10 - 16 * u
                r = 6 + 16 * u
                d.ellipse([(px - r) * K, (py - r) * K, (px + r) * K, (py + r) * K], fill=(150, 156, 176, int(150 * (1 - u))))
        if T_CROSS <= st < T_STOP + 1.2:
            u = prog(st, T_CROSS, T_STOP + 1.2)
            for j in range(5):
                px = cx - 60 - j * 40 - 60 * u
                r = 16 + 26 * u
                d.ellipse([(px - r) * K, (FEET - 4 - r * 0.6) * K, (px + r) * K, (FEET - 4 + r * 0.4) * K],
                          fill=(170, 176, 196, int(170 * (1 - u))))
        if T_CAR0 <= st:
            draw_car(d, cx, FEET + 30, st, bow, st >= T_IN, vib, moving, chauffeur_in=st < T_CHAUF)
        ch = chauffeur(st)
        if ch is not None and st < T_CUT:
            pose, hip, al = ch
            fc = -1 if st >= T_LAUNCH else 1
            pts = W2S(AJ.place(pose, hip, fc, S), c)
            figure(d, pts, S, "chauffeur", fc, int(255 * al), body=(176, 182, 200))
        lx = LOUNGE_X - c
        if -200 < lx < PWD + 200:
            lounger(d, lx, LOUNGE_Y)
        rs = rich(st)
        if rs is not None:
            pose, hip, f, prop = rs
            pts = W2S(AJ.place(pose, hip, f, S), c)
            figure(d, pts, S, "rich", f)
            focus = (pts["hip"][0] + 10, pts["hip"][1] - 40)
            hx, hy = pts["hr"]
            if prop == "keys":
                keys(d, hx, hy - 6, st)
            elif prop == "juice":
                d.rounded_rectangle([(hx - 8) * K, (hy - 10) * K, (hx + 8) * K, (hy + 14) * K], int(3 * K),
                                    fill=(255, 160, 40, 255), outline=INK + (255,), width=int(2 * K))
                d.line([(hx + 3) * K, (hy - 10) * K, (hx - 6) * K, (hy - 26) * K], fill=(255, 80, 120, 255),
                       width=int(3 * K))
            elif prop == "phone":
                phone_(d, hx, hy, False)
                if T_SELFIE <= st < T_SELFIE + 0.25:
                    k = 1 - prog(st, T_SELFIE, T_SELFIE + 0.25)
                    for r in (70, 46, 26):
                        d.ellipse([(hx - r) * K, (hy - r) * K, (hx + r) * K, (hy + r) * K],
                                  fill=(255, 255, 255, int(110 * k)))
            elif prop == "cash":
                cash_fan(d, hx, hy)
            elif prop == "box":
                pizza_box(d, hx, hy - 8)
            elif prop == "slice":
                slice_(d, hx, hy)
            elif prop == "watch":
                lx_, ly_ = pts["hl"]
                d.rounded_rectangle([(lx_ - 8) * K, (ly_ - 4) * K, (lx_ + 8) * K, (ly_ + 9) * K], int(3 * K),
                                    fill=GOLD + (255,), outline=INK + (255,), width=int(2 * K))
                if st > T_YAWN1 + 0.6:
                    text_c(d, pts["head"][0] + 10, pts["head"][1] - 76, "...", 34, WHITE)
        if T_DRONE0 <= st < T_DRONE1:
            hx0, hy0 = AJ.place(R_TAKE, KID_HIP, 1, S)["hr"]
            if st < T_DRONE_HAND:
                u = smooth(prog(st, T_DRONE0, T_DRONE_HAND))
                drone(d, lerp(1120, hx0, u), lerp(-60, hy0 - 44, u), st, True)
            else:
                u = smooth(prog(st, T_DRONE_HAND, T_DRONE1))
                drone(d, lerp(hx0, 1140, u), lerp(hy0 - 44, -80, u), st, False)
        if T_HONK <= st < T_HONK + 0.5:
            k = hq.pop(st, T_HONK, 0.15)
            text_c(d, cx + 160, FEET - 170, "BEEP!", 30 * k + 2, (255, 220, 120), stroke=3)
        front_pole(d, front)
        speed_lines(d, st, abs(cam_v(2, st)))
        hq.confetti(_Pp(d), st, T_CROSS, T_CROSS + 0.6, FIN_SX, 150, 5, 50)
        ev = [T_IGN, T_LAUNCH, T_CROSS, T_STOP]
    g = lay.resize((lay.width // 4, lay.height // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(5))
    ga = g.split()[3].point(lambda v: int(v * 0.5))
    glow = Image.new("RGBA", g.size, (150, 180, 255, 0))
    glow.putalpha(ga)
    base.alpha_composite(glow.resize(lay.size, Image.BILINEAR))
    base.alpha_composite(lay)
    if lane == 2 and T_CROSS <= st < T_CROSS + 0.2:
        fl = Image.new("RGBA", base.size, (255, 255, 255, int(120 * (1 - prog(st, T_CROSS, T_CROSS + 0.2)))))
        base.alpha_composite(fl)
    if lane == 2 and T_CUT <= st < T_CUT + 0.12:
        fl = Image.new("RGBA", base.size, (255, 255, 255, int(90 * (1 - prog(st, T_CUT, T_CUT + 0.12)))))
        base.alpha_composite(fl)
    dx, dy = hq.shake(st, ev, 7) if t < T_RW else (0.0, 0.0)
    if lane == 2 and T_LAUNCH <= st < T_CUT:
        dx += 3 * math.sin(st * 70)
        dy += 2 * math.cos(st * 63)
    zo = 1 - smooth(prog(st, 0.0, 1.9))           # the opening close-up pulls back over the first ~2 s
    z = 1.0 + 0.03 * math.sin(math.pi * st / T_RW) + 0.85 * zo
    dx += z * (PWD / 2 - focus[0]) * zo
    dy += z * (PHT / 2 - focus[1]) * zo
    im = hq.downsample(hq.camera(base, z, dx * K, dy * K), PWD, PHT)
    di = ImageDraw.Draw(im)
    f = font("Inter-SemiBold.otf", 32)
    x = 28
    for ch_ in ["SPRINTER", "CONSISTENT", "RICH KID"][lane]:
        di.text((x + 2, 20), ch_, font=f, fill=(0, 0, 0, 160))
        di.text((x, 18), ch_, font=f, fill=(214, 220, 238, 255))
        x += f.getlength(ch_) + 9
    im = progress_bar(im, lane, st)
    di = ImageDraw.Draw(im)
    di.rounded_rectangle([1, 1, PWD - 2, PHT - 2], 16, outline=(44, 54, 88, 255), width=3)
    return im


T_MAP0, T_MAP1 = 4.0, 99.0          # from 4 s to the end: how far each one still has to go
LANE_COL = [RED, (70, 140, 255), GOLD]


def progress_bar(im, lane, st):
    if not (T_MAP0 <= st < T_MAP1):
        return im
    k = hq.pop(st, T_MAP0 + 0.08 * lane, 0.3) * (1 - smooth(prog(st, T_MAP1 - 0.25, T_MAP1)))
    if k < 0.02:
        return im
    m = [m_s, m_c, m_r][lane](st)
    left = max(0.0, 100 - m)
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    a = int(255 * min(1, k))
    y0 = 446 + 30 * (1 - min(1, k))
    x0, x1 = 24, PWD - 24
    d.rounded_rectangle([x0, y0, x1, y0 + 46], 12, fill=(6, 8, 20, int(215 * min(1, k))),
                        outline=LANE_COL[lane] + (a,), width=3)
    f = font("InterDisplay-Bold.otf", 27)
    lab = f"{left:.1f} M LEFT"
    col = (255, 90, 90) if (lane == 2 and left > 0.05) else (GOLD if lane == 2 else (240, 242, 250))
    d.text((x0 + 18, y0 + 8), lab, font=f, fill=col + (a,))
    tx0, tx1, ty = x0 + 270, x1 - 60, y0 + 23
    d.line([(tx0, ty), (tx1, ty)], fill=(70, 80, 110, a), width=6)
    px = lerp(tx0, tx1, m / 100)
    d.line([(tx0, ty), (px, ty)], fill=LANE_COL[lane] + (a,), width=6)
    d.ellipse([px - 11, ty - 11, px + 11, ty + 11], fill=(240, 242, 250, a), outline=LANE_COL[lane] + (a,), width=5)
    fx = tx1 + 18
    d.line([(fx, ty + 16), (fx, ty - 17)], fill=(220, 224, 236, a), width=3)
    for r in range(3):
        for c in range(4):
            colc = (240, 240, 244, a) if (r + c) % 2 == 0 else (20, 20, 24, a)
            d.rectangle([fx + 2 + c * 6, ty - 17 + r * 5, fx + 8 + c * 6, ty - 12 + r * 5], fill=colc)
    out = im.copy()
    out.alpha_composite(ov)
    return out


def title(img):
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(11)
    for _ in range(140):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        r = rng.uniform(0.6, 1.6)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(210, 220, 255, int(rng.uniform(40, 170))))
    PW.spaced(d, W / 2, 18, "WHO WINS?", font("InterDisplay-Bold.otf", 78), (240, 242, 250, 255), 10)
    PW.spaced(d, W / 2, 116, "DISTANCE  ( M )", font("Inter-SemiBold.otf", 26), (150, 158, 184, 255), 9)


COLS = [(190, "SPRINTER"), (540, "CONSISTENT"), (890, "RICH KID")]


def counter(img, st, t):
    d = ImageDraw.Draw(img)
    m = [min(100.0, m_s(st)), min(100.0, m_c(st)), m_r(st)]
    lead = max(range(3), key=lambda i: (m[i], -i))
    if m[2] >= 100:
        lead = 2
    fnum = font("InterDisplay-Bold.otf", 92)
    flab = font("Inter-SemiBold.otf", 24)
    for i, (cx, lab) in enumerate(COLS):
        v = int(m[i])
        win = i == 2 and v >= 100 and t < T_RW + 0.3
        txt = "100" if m[i] >= 99.95 else f"{m[i]:.1f}"
        col = GOLD if win else ((245, 246, 252) if i == lead else (128, 136, 160))
        PW.spaced(d, cx, 148, txt, fnum, col + (255,), 2)
        PW.spaced(d, cx, 254, lab, flab, ((230, 232, 242) if i == lead else (128, 136, 160)) + (255,), 6)


TITLE = None


def frame(t):
    st = scene_t(t)
    img = TITLE.copy()
    counter(img, st, t)
    for lane in range(3):
        img.alpha_composite(panel(t, st, lane), (PX0, PANEL_Y[lane]))
    if t >= T_RW:
        d = ImageDraw.Draw(img)
        a = int(230 * min(1, prog(t, T_RW, T_RW + 0.1)) * (1 - prog(t, DUR - 0.12, DUR)))
        cx, cy = W / 2, PANEL_Y[1] + PHT / 2
        d.rounded_rectangle([cx - 110, cy - 70, cx + 110, cy + 70], 20, fill=(0, 0, 0, int(a * 0.5)))
        for ox in (-46, 14):
            d.polygon([(cx + ox + 40, cy - 44), (cx + ox + 40, cy + 44), (cx + ox - 20, cy)], fill=(255, 255, 255, a))
        rng = np.random.default_rng(int(t * 30))
        for _ in range(3):
            y = rng.uniform(PANEL_Y[0], H - 200)
            d.rectangle([0, y, W, y + rng.uniform(3, 9)], fill=(255, 255, 255, int(a * 0.35)))
    return np.asarray(img.convert("RGB"))


def init_worker():
    global SKY, TITLE
    SKY = [make_sky(i) for i in range(3)]
    TITLE = Image.new("RGBA", (W, H), NIGHT + (255,))
    title(TITLE)


def render(i):
    return frame(i / FPS).tobytes()


# ---------------------------------------------------------------- sound
def engine(dur, f0, f1, curve=1.0, rough=0.25, seed=0):
    n = int(dur * SR)
    u = (np.arange(n) / n) ** curve
    f = f0 + (f1 - f0) * u
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = sum(np.sin(k * ph) / k for k in range(1, 9))
    x += rough * noise(dur, seed, lo=60, hi=2000)[:n]
    return x / (np.abs(x).max() + 1e-9)


def step(fx, at, g, pan, hi=False):
    mix_in(fx, tone(160 if not hi else 210, 0.07, (1, 0.5), a=0.001, d=0.025) +
           0.4 * noise(0.07, int(at * 1000) % 9999, lo=300, hi=3000) * env(int(0.07 * SR), 0.001, 0.015), at, g, pan)


def steps_from(ph_arr, v_arr, t0, t1):
    """a footstep every half stride while running"""
    out = []
    last = None
    for i in range(int(t0 * 240), min(int(t1 * 240), len(ph_arr))):
        n = int(ph_arr[i] // math.pi)
        if last is not None and n != last and abs(v_arr[i]) > 1.0:
            out.append(_TG[i])
        last = n
    return out


# ---------------------------------------------------------------- energetic race track (140 BPM, A minor)
BPM = 140
BEAT = 60 / BPM
CHORDS = [(45, 48, 52), (41, 45, 48), (48, 52, 55), (43, 47, 50)]      # Am F C G


def kick():
    n = int(0.28 * SR)
    tt = np.arange(n) / SR
    f = 45 + 110 * np.exp(-tt * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9) + 0.15 * noise(0.28, 1, lo=1500)[:n] * np.exp(-tt * 120)


def snare(seed=2):
    n = int(0.22 * SR)
    tt = np.arange(n) / SR
    return 0.8 * noise(0.22, seed, lo=900, hi=9000)[:n] * np.exp(-tt * 18) + 0.5 * np.sin(2 * np.pi * 190 * tt) * np.exp(-tt * 30)


def hat(seed=3, open_=False):
    d = 0.18 if open_ else 0.045
    n = int(d * SR)
    tt = np.arange(n) / SR
    return noise(d, seed, lo=7000)[:n] * np.exp(-tt * (14 if open_ else 70))


def saw(f, dur, bright=2500, decay=3.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = 2 * ((f * tt) % 1.0) - 1
    x += 2 * ((f * 1.007 * tt) % 1.0) - 1
    x = PW.filt(x, hi=bright)
    return x * np.minimum(1, tt / 0.004) * np.exp(-tt * decay)


def pulse(f, dur):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = np.sign(np.sin(2 * np.pi * f * tt)) * 0.6 + np.sin(2 * np.pi * f * 2 * tt) * 0.3
    return PW.filt(x, hi=5000) * np.minimum(1, tt / 0.003) * np.exp(-tt * 7)


def crash(seed=9):
    n = int(1.6 * SR)
    tt = np.arange(n) / SR
    return noise(1.6, seed, lo=3000)[:n] * np.exp(-tt * 2.5)


def hype():
    """drums + bass + arps; full from the pistol, thinner while the sprinter rests, a build into the car's launch,
    a drop on the launch, a final hit when the car breaks the tape, then a held chord into the rewind"""
    n = int(DUR * SR)
    mus = np.zeros((n, 2))
    K_, S_, H_, B_, A_ = kick(), snare(), hat(), None, None
    nb = int(T_CROSS / BEAT) + 1
    for b in range(nb):
        t0 = b * BEAT
        if t0 >= T_CROSS - 0.02:
            break
        bar = b // 4
        ch = CHORDS[bar % 4]
        rest = T_PANT1 <= t0 < T_RUN2 - 0.9          # the sprinter rests: lighter groove
        build = T_IGN - 1.7 <= t0 < T_LAUNCH            # snare build into the launch
        drop = t0 >= T_LAUNCH
        # kick: four on the floor (half time while resting)
        if not rest or b % 2 == 0:
            mix_in(mus, K_, t0, 0.55 if not rest else 0.4)
        if b % 2 == 1 and not build:
            mix_in(mus, S_, t0, 0.32 if not rest else 0.2, 0.1)
        for e in range(2 if not drop else 4):
            sub = BEAT / (2 if not drop else 4)
            mix_in(mus, H_, t0 + e * sub, (0.09 if e % 2 else 0.13) * (0.7 if rest else 1), 0.35)
        if b % 4 == 3 and not rest:
            mix_in(mus, hat(4, True), t0 + BEAT / 2, 0.08, 0.35)
        # bass: driving 8ths, octave jumps
        for e in range(2):
            m = ch[0] - 12 + (12 if e == 1 and b % 2 == 1 else 0)
            mix_in(mus, saw(midi(m), BEAT / 2 * 0.95, 900 if rest else 1400, 4.0), t0 + e * BEAT / 2,
                   0.16 if not rest else 0.11, -0.05)
        # arp lead (16ths) - off while resting
        if not rest:
            seq = [0, 1, 2, 1, 2, 3, 2, 1]
            notes = [ch[0] + 24, ch[1] + 24, ch[2] + 24, ch[0] + 36]
            for e in range(4 if (drop or t0 > T_RUN2) else 2):
                i = (b * 4 + e) % 8 if (drop or t0 > T_RUN2) else (b * 2 + e) % 8
                sub = BEAT / (4 if (drop or t0 > T_RUN2) else 2)
                mix_in(mus, pulse(midi(notes[seq[i] % 4]), sub * 0.9), t0 + e * sub, 0.05, 0.3 if e % 2 else -0.3)
        else:
            if b % 4 == 0:
                for k2, m in enumerate(ch):
                    mix_in(mus, saw(midi(m + 12), 4 * BEAT, 1200, 0.6), t0, 0.035, (k2 - 1) * 0.4)
        if build:
            u = prog(t0, T_IGN - 1.7, T_LAUNCH)
            for e in range(2 if u < 0.5 else 4):
                mix_in(mus, snare(5 + e), t0 + e * BEAT / (2 if u < 0.5 else 4), 0.12 + 0.2 * u, 0.1)
    # riser into the launch, crash on the launch, crash + big chord on the tape
    rl = T_LAUNCH - (T_IGN - 1.7)
    nr = int(rl * SR)
    rs = noise(rl, 11, lo=800, hi=9000)[:nr] * np.linspace(0, 1, nr) ** 2
    rs += 0.3 * np.sin(2 * np.pi * np.cumsum(200 + 1600 * np.linspace(0, 1, nr) ** 2) / SR) * np.linspace(0, 1, nr)
    mix_in(mus, rs, T_IGN - 1.7, 0.10)
    for t0 in (0.0, T_RUN2, T_LAUNCH):
        mix_in(mus, crash(int(t0 * 10)), t0, 0.12)
    mix_in(mus, crash(77), T_CROSS, 0.18)
    mix_in(mus, kick(), T_CROSS, 0.7)
    ch = CHORDS[0]
    tail = DUR - T_CROSS
    for k2, m in enumerate((ch[0] - 12, ch[0], ch[1], ch[2], ch[0] + 12)):
        mix_in(mus, saw(midi(m), tail, 2000, 0.9), T_CROSS, 0.07, (k2 - 2) * 0.3)
    mus /= np.abs(mus).max() + 1e-9
    return mus * 0.45


SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"


def gm_score():
    """an epic hybrid action cue on real GM instruments (FluidSynth): staccato strings, distorted guitar chugs,
    bass, rock kit, brass and horn theme, timpani, choir; full from the pistol, pulled back while the sprinter
    rests, back with the horn theme, a snare/timpani build into the launch, a drop, a final hit on the tape"""
    import mido
    import tempfile
    notes = []      # (start, dur, channel, note, vel)
    prg = {0: 48, 1: 30, 2: 33, 3: 61, 4: 60, 5: 47, 6: 81, 7: 52, 8: 44}
    B = BEAT
    prog_ = [(45, 52), (41, 48), (48, 55), (43, 50)]      # Am F C G (root, fifth)
    triad = {45: (57, 60, 64), 41: (53, 57, 60), 48: (55, 60, 64), 43: (55, 59, 62)}
    theme = [(0, 2, 69), (2, 1, 72), (3, 1, 71), (4, 3, 69), (7, 1, 64),
             (8, 2, 65), (10, 1, 69), (11, 1, 72), (12, 4, 71)]           # in beats over 4 bars
    end = T_CROSS
    nbeats = int(end / B) + 1
    for b in range(nbeats):
        t0 = b * B
        if t0 >= end - 0.01:
            break
        bar = b // 4
        root, fifth = prog_[(bar // 1) % 4]
        rest = T_PANT1 - 0.3 <= t0 < T_RUN2 - 0.4
        build = T_IGN - 1.75 <= t0 < T_LAUNCH
        drop = t0 >= T_LAUNCH - 0.01
        full = not rest
        # drums
        if full and not build:
            notes.append((t0, 0.1, 9, 36, 118 if b % 2 == 0 else 100))
            if b % 2 == 1:
                notes.append((t0, 0.1, 9, 38, 112))
            for e in range(2 if not drop else 4):
                notes.append((t0 + e * B / (2 if not drop else 4), 0.05, 9, 42, 80 if e % 2 else 96))
            if b % 8 == 7:
                for j, tm in enumerate((50, 48, 45, 43)):
                    notes.append((t0 + j * B / 4, 0.1, 9, tm, 110))
        elif rest:
            if b % 2 == 0:
                notes.append((t0, 0.1, 9, 36, 96))
            notes.append((t0 + B / 2, 0.05, 9, 42, 60))
        if build:
            u = prog(t0, T_IGN - 1.75, T_LAUNCH)
            div = 2 if u < 0.35 else (4 if u < 0.75 else 8)
            for e in range(div):
                notes.append((t0 + e * B / div, 0.05, 9, 38, int(70 + 55 * u)))
            notes.append((t0, 0.3, 5, 45, int(70 + 50 * u)))
        if bar % 4 == 0 and b % 4 == 0 and full:
            notes.append((t0, 0.5, 9, 49, 110))
        # staccato strings ostinato (16ths), always
        pat = [root + 12, root + 24, fifth + 12, root + 24]
        for e in range(4):
            notes.append((t0 + e * B / 4, B / 4 * 0.6, 0, pat[e], (70 if rest else 92) + (12 if drop else 0)))
        # guitar chugs + bass 8ths
        if full:
            for e in range(2):
                tt = t0 + e * B / 2
                for nn in (root - 12 + 12, fifth - 12 + 12):
                    notes.append((tt, B / 2 * 0.55, 1, nn, 100))
                notes.append((tt, B / 2 * 0.8, 2, root - 12 + (12 if e == 1 and b % 2 else 0), 105))
        else:
            if b % 4 == 0:
                notes.append((t0, 4 * B * 0.95, 2, root - 12, 85))
                for nn in triad[root]:
                    notes.append((t0, 4 * B * 0.98, 7, nn, 70))
                    notes.append((t0, 4 * B * 0.98, 8, nn - 12, 55))
        # brass stab on each bar's downbeat when full
        if full and b % 4 == 0:
            for nn in triad[root]:
                notes.append((t0, B * 0.45, 3, nn, 100 if not drop else 118))
        # horn theme after the sprinter gets back up, and in the drop
        if (T_RUN2 - 0.4 <= t0 < T_IGN - 1.75) or drop:
            pass
        # drop: saw arps on top
        if drop:
            ar = list(triad[root]) + [triad[root][0] + 12]
            for e in range(4):
                notes.append((t0 + e * B / 4, B / 4 * 0.8, 6, ar[(b * 4 + e) % 4] + 12, 90))
    # the horn theme (4 bars), placed on bar lines from the second sprint on, and once from the start
    for start in (0.0 + 4 * 4 * B, ):
        pass
    for t_th in (4 * B, 40 * B):
        for bb, du, nn in theme:
            if t_th + bb * B < T_LAUNCH - 0.05:
                notes.append((t_th + bb * B, du * B * 0.95, 4, nn, 104))
                notes.append((t_th + bb * B, du * B * 0.95, 3, nn - 12, 72))
    # opening hit with the pistol
    for nn in (45, 57, 60, 64):
        notes.append((0.0, 0.5, 3, nn, 120))
    notes.append((0.0, 0.6, 5, 45, 120))
    notes.append((0.0, 0.6, 9, 49, 120))
    # the launch hit
    for nn in (45, 57, 60, 64, 69):
        notes.append((T_LAUNCH, 0.4, 3, nn, 127))
    notes.append((T_LAUNCH, 0.6, 5, 45, 127))
    notes.append((T_LAUNCH, 0.6, 9, 49, 127))
    notes.append((T_LAUNCH, 0.6, 9, 57, 120))
    # the final hit on the tape, held into the rewind
    hold = T_RW - T_CROSS + 0.4
    for nn in (33, 45, 52, 57, 60, 64, 69):
        notes.append((T_CROSS, hold, 3 if nn > 40 else 2, nn, 120))
    for nn in (57, 60, 64, 69):
        notes.append((T_CROSS, hold, 7, nn, 100))
        notes.append((T_CROSS, hold, 8, nn - 12, 90))
    notes.append((T_CROSS, 1.0, 5, 45, 127))
    notes.append((T_CROSS, 1.0, 9, 49, 127))
    notes.append((T_CROSS, 1.0, 9, 57, 127))
    notes.append((T_CROSS, 0.2, 9, 36, 127))
    mid = mido.MidiFile(ticks_per_beat=960)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))      # 1 beat = 0.5 s -> 1920 ticks / s
    vol = {0: 100, 1: 78, 2: 110, 3: 92, 4: 108, 5: 110, 6: 70, 7: 80, 8: 70, 9: 118}
    for ch, pg in prg.items():
        tr.append(mido.Message("program_change", channel=ch, program=pg, time=0))
    for ch, v in vol.items():
        tr.append(mido.Message("control_change", channel=ch, control=7, value=v, time=0))
        tr.append(mido.Message("control_change", channel=ch, control=91, value=50 if ch != 9 else 30, time=0))
    tr.append(mido.Message("control_change", channel=1, control=10, value=30, time=0))
    tr.append(mido.Message("control_change", channel=6, control=10, value=96, time=0))
    ev = []
    for st_, du, ch, nn, v in notes:
        ev.append((st_, 1, ch, nn, v))
        ev.append((st_ + du, 0, ch, nn, 0))
    ev.sort(key=lambda e: (e[0], e[1]))
    now = 0
    for st_, on, ch, nn, v in ev:
        tk = int(round(max(0.0, st_) * 1920))
        tr.append(mido.Message("note_on" if on else "note_off", channel=ch, note=int(nn), velocity=int(min(127, v)),
                               time=max(0, tk - now)))
        now = max(now, tk)
    tmp = tempfile.mkdtemp()
    mp, wp = os.path.join(tmp, "s.mid"), os.path.join(tmp, "s.wav")
    mid.save(mp)
    subprocess.run(["fluidsynth", "-ni", "-g", "0.6", "-r", str(SR), "-F", wp, SF2, mp], check=True,
                   capture_output=True)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", wp, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True).stdout
    m = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    n = int(DUR * SR)
    out = np.zeros((n, 2))
    out[:min(n, len(m))] = m[:n]
    # gentle glue: soft-clip and level
    out = np.tanh(out * 1.6) / np.tanh(1.6)
    out /= np.abs(out).max() + 1e-9
    return out * 0.5


def audio():
    n = int(DUR * SR)
    fx = np.zeros((n, 2))
    mus = gm_score()
    tt = np.arange(n) / SR
    bed = noise(DUR, 3, lo=150, hi=900)[:n] * 0.02
    cr = np.sin(2 * np.pi * 4300 * tt) * (np.sin(2 * np.pi * 28 * tt) > 0.6) * (np.sin(2 * np.pi * 0.7 * tt) > 0)
    fx[:, 0] += bed + 0.004 * cr
    fx[:, 1] += bed + 0.004 * np.roll(cr, 9000)
    mix_in(fx, noise(0.5, 1, lo=200, hi=8000) * env(int(0.5 * SR), 0.0005, 0.07), 0.0, 0.32)
    mix_in(fx, tone(90, 0.4, (1, 0.5), a=0.001, d=0.15), 0.0, 0.25)
    for t0 in steps_from(PH_S, V_S, 0.0, T_FALL):
        step(fx, t0, 0.06, -0.3, True)
    for t0 in steps_from(PH_C, V_C, 0.0, T_TOUCH + 0.6):
        step(fx, t0, 0.028, 0.1)
    mix_in(fx, tone(880, 0.1, (1, 0.4), a=0.002, d=0.05, sweep=1200), T_STOP_S + 0.1, 0.05, -0.3)
    for j in range(5):
        mix_in(fx, noise(0.22, 20 + j, lo=500, hi=3000) * np.sin(np.linspace(0, np.pi, int(0.22 * SR))),
               T_EASY1 + 0.1 + j * 0.3, 0.05, -0.3)
    for j in range(4):
        mix_in(fx, tone(180, 0.12, (1, 0.5), a=0.005, d=0.05, sweep=120), T_DRINK0 + 0.6 + j * 0.3, 0.06, -0.3)
    mix_in(fx, tone(1320, 0.18, (1, 0.3), a=0.002, d=0.1), T_ALERT - 0.15, 0.05, -0.3)
    for j, m in enumerate((84, 88, 91)):
        mix_in(fx, tone(midi(m), 0.09, (1, 0.5), a=0.001, d=0.05), T_ALERT + j * 0.07, 0.05, -0.3)
    mix_in(fx, tone(300, 0.35, (1, 0.6), a=0.002, d=0.2, sweep=110), T_CRAMP, 0.08, -0.3)
    mix_in(fx, tone(70, 0.4, (1, 0.5), a=0.002, d=0.18) + 0.3 * noise(0.4, 77, lo=100, hi=2000) *
           env(int(0.4 * SR), 0.002, 0.08), T_FALL, 0.18, -0.3)
    rn = noise(T_RAIN1 - T_RAIN0, 9, lo=800, hi=9000)
    m = len(rn)
    rn *= np.minimum(1, np.minimum(np.arange(m), m - np.arange(m)) / (0.4 * SR))
    mix_in(fx, rn, T_RAIN0, 0.05, 0.1)
    for j in range(8):
        mix_in(fx, tone(3200 + 400 * (j % 3), 0.05, (1, 0.6), a=0.001, d=0.03), 0.15 + j * 0.34, 0.02, 0.4)
    mix_in(fx, noise(0.6, 31, lo=1500, hi=6000) * env(int(0.6 * SR), 0.05, 0.2), T_KEYS1 + 0.9, 0.04, 0.4)
    mix_in(fx, noise(0.12, 32, lo=1000, hi=8000) * env(int(0.12 * SR), 0.001, 0.03), T_SELFIE, 0.12, 0.4)
    mix_in(fx, noise(0.12, 33, lo=1000, hi=8000) * env(int(0.12 * SR), 0.001, 0.03), T_SELFIE + 0.07, 0.08, 0.4)
    for j in range(10):
        mix_in(fx, noise(0.08, 40 + j, lo=1200, hi=7000) * env(int(0.08 * SR), 0.002, 0.03), T_FAN0 + 0.3 + j * 0.2,
               0.03, 0.4)
    dn = int((T_DRONE1 - T_DRONE0) * SR)
    dr = np.sin(2 * np.pi * 180 * np.arange(dn) / SR) * 0.4 + noise(T_DRONE1 - T_DRONE0, 50, lo=200, hi=900)[:dn] * 0.6
    dr *= np.sin(np.linspace(0, np.pi, dn))
    mix_in(fx, dr, T_DRONE0, 0.06, 0.5)
    for j in range(5):
        mix_in(fx, noise(0.07, 60 + j, lo=800, hi=4000) * env(int(0.07 * SR), 0.002, 0.03),
               T_DRONE_HAND + 0.6 + j * 0.35, 0.04, 0.4)
    for j in range(6):
        mix_in(fx, tone(2400, 0.02, (1,), a=0.0005, d=0.01), T_YAWN1 + 0.6 + j * 0.25, 0.04, 0.4)
    arr = engine(T_CAR1 - T_CAR0, 60, 40, 1.0, 0.3, 69)
    arr *= np.linspace(0.2, 1, len(arr)) * np.minimum(1, (len(arr) - np.arange(len(arr))) / (0.3 * SR))
    mix_in(fx, arr, T_CAR0, 0.12, 0.4)
    for j in range(2):
        mix_in(fx, tone(440, 0.16, (1, 0.6, 0.4), a=0.005, d=0.1) + tone(554, 0.16, (1, 0.6), a=0.005, d=0.1),
               T_HONK + j * 0.2, 0.06, 0.4)
    for t0 in (T_CHAUF, T_IN):
        mix_in(fx, tone(100, 0.2, (1, 0.5), a=0.001, d=0.06) + 0.4 * noise(0.2, int(t0 * 10), lo=200, hi=3000) *
               env(int(0.2 * SR), 0.001, 0.04), t0, 0.16, 0.4)
    mix_in(fx, engine(0.5, 30, 70, 0.6, 0.6, 72) * env(int(0.5 * SR), 0.02, 0.3), T_IGN - 0.2, 0.10, 0.4)
    idle = engine(T_LAUNCH - T_IGN, 46, 58, 1.0, 0.3, 73)
    for tr in (0.3, 0.6):
        lo, hi_ = int(tr * SR), int((tr + 0.2) * SR)
        idle[lo:hi_] *= 1.6
    mix_in(fx, idle * np.minimum(1, np.arange(len(idle)) / (0.05 * SR)), T_IGN, 0.16, 0.4)
    for j in range(3):
        for k2, dt in enumerate((0.0, 0.17)):
            mix_in(fx, tone(48, 0.2, (1, 0.5), a=0.003, d=0.08), T_REACH - 0.6 + j * 0.42 + dt, 0.16 - 0.06 * k2)
    roar = engine(T_CUT - T_LAUNCH + 0.3, 70, 320, 0.6, 0.35, 74)
    mix_in(fx, roar * env(len(roar), 0.01, 1.2), T_LAUNCH, 0.28, 0.2)
    mix_in(fx, noise(0.5, 75, lo=300, hi=5000) * np.sin(np.linspace(0, np.pi, int(0.5 * SR))), T_CUT - 0.1, 0.16)
    mix_in(fx, tone(1200, 0.08, (1, 0.5), a=0.001, d=0.03, sweep=600), T_CROSS, 0.10)
    sk = noise(0.5, 76, lo=1500, hi=5000) * env(int(0.5 * SR), 0.01, 0.25)
    sk *= np.sin(2 * np.pi * 2200 * np.arange(len(sk)) / SR) * 0.5 + 0.5
    mix_in(fx, sk, T_CROSS + 0.05, 0.12, 0.3)
    mix_in(fx, tone(1000, 0.08, (1, 0.5), a=0.001, d=0.03, sweep=500), T_TOUCH, 0.06, -0.1)
    # the progress bars pop in (one blip per lane) at the mid-video re-hook
    mix_in(fx, noise(0.35, 90, lo=500, hi=6000) * np.sin(np.linspace(0, np.pi, int(0.35 * SR))), T_MAP0 - 0.15, 0.06)
    for j, f_ in enumerate((660, 880, 330)):
        mix_in(fx, tone(f_, 0.12, (1, 0.4), a=0.002, d=0.06), T_MAP0 + 0.08 * j, 0.07)
    rw = DUR - T_RW
    nrw = int(rw * SR)
    fr = 300 + 2200 * np.linspace(0, 1, nrw) ** 1.5
    w = np.sin(2 * np.pi * np.cumsum(fr) / SR) * 0.5 + noise(rw, 80, lo=1000, hi=6000)[:nrw] * 0.5
    w *= np.minimum(1, np.arange(nrw) / (0.05 * SR))
    mix_in(fx, w, T_RW, 0.06)
    x = mus + fx
    i0 = int(T_RW * SR)
    x[i0:] = fx[i0:] + mus[i0:] * np.linspace(1, 0.2, n - i0)[:, None]
    m = int(0.3 * SR)
    k = np.linspace(0, 1, m)[:, None]
    x[-m:] = x[-m:] * (1 - k) + x[:m] * k
    x /= max(1.0, np.abs(x).max() / 0.9)
    return x


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "who-wins.mp4"
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
