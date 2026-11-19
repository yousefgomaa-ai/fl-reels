#!/usr/bin/env python3
"""THE PERFECT WAVE - Overthinker vs Doer, one beach at night, 16.8 s, loops on itself.

The overthinker sits on the sand next to a brand-new board (the price tag still on) waiting for the perfect wave:
"TOO SMALL." "TOO MESSY." "NOT TODAY." The doer paddles out, wipes out, wipes out again, then rides; DAY 1 -> 365,
WAVES CAUGHT 0 : 41. On day 365 the sea goes quiet and the perfect wave comes. The overthinker runs in ("THAT'S THE
ONE!"), the doer drops in and flies off the lip in front of the moon, and the lip lands on the overthinker ("WAIT-").
He washes up face down, his board lands upright next to his head, tag still on.
"THE PERFECT WAVE CAME. / HE WASN'T READY FOR IT."  The last half second dissolves back into the first frame.

1080x1920, 30 fps, PIL + numpy only; the music and the sea are synthesised here.

    python3 stick/perfect_wave.py stick/perfect-wave.mp4
    ONLY_FRAMES=0,1.3,6,9.6,10.9,11.25,12.9,15 python3 stick/perfect_wave.py /tmp/pw   (PNG stills)
"""
import math
import os
import subprocess
import sys
import wave
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
SR = 44100
BPM = 100
BEAT = 60 / BPM
BAR = 4 * BEAT                          # 2.4 s
DUR = 7 * BAR                           # 16.8 s, whole bars: the music loops with the picture
NF = int(round(DUR * FPS))
XFADE = 0.5                             # the last half second dissolves into frame 0

# ---------------------------------------------------------------- fonts
FD = "/usr/share/fonts/opentype/inter/"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
_fc = {}


def font(name, size):
    k = (name, size)
    if k not in _fc:
        path = name if name.startswith("/") else FD + name
        _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]


# ---------------------------------------------------------------- small maths
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def prog(t, a, b):
    return clamp((t - a) / (b - a))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def out_cubic(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def in_quad(x):
    x = clamp(x)
    return x * x


def out_back(x, s=1.8):
    x = clamp(x) - 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def lerp(a, b, k):
    return a + (b - a) * k


def lerp_c(a, b, k):
    return tuple(int(round(lerp(x, y, k))) for x, y in zip(a, b))


# ---------------------------------------------------------------- the set
HORIZON = 1080
SEA = 1470                              # calm water line where the action is
MX, MY, MR = 430, 770, 76               # the moon (the doer's aerial crosses it)
SHORE = 860                             # where the sand line meets the calm sea


def sand_y(x):
    return 1600 - (x - 600) * 0.5       # the beach, and the sea bed under the water


SLOPE = math.atan(-0.5)
INK = (12, 14, 22)
DOER = (246, 246, 242)
DOER_FAR = (204, 205, 206)
OT = (148, 150, 156)
OT_FAR = (116, 118, 124)

# ---------------------------------------------------------------- the waves
LINE_X = 280                            # where the doer sits and waits for his waves
WAVE_SPEED, WAVE_W = 600, 150
WAVE_T = [0.9 + 1.2 * k for k in range(7)]          # a wave every half bar; crest passes the doer at these times
WAVE_A = [70, 72, 78, 84, 92, 98, 104]
RIDE_OFF = 0.22                                     # the rider sits this far (in wave widths) ahead of the crest

PW_T0, PW_C0, PW_SPEED, PW_W, PW_A = 9.0, -520.0, 450.0, 300.0, 560.0
T_CRASH = 11.15
T_LAND = None                           # set below, when the doer's aerial meets the water


def wave_c(k, t):
    return LINE_X - RIDE_OFF * WAVE_W + WAVE_SPEED * (t - WAVE_T[k])


def wave_amp(k, t):
    c = wave_c(k, t)
    if c < -420 or c > SHORE + 260:
        return 0.0, c
    a = WAVE_A[k] * smooth(prog(c, -330, -60)) * (1 + 0.25 * smooth(prog(c, 250, 600)))
    a *= 1 - smooth(prog(c, 640, SHORE + 130))
    return a, c


def pw_c(t):
    return PW_C0 + PW_SPEED * (t - PW_T0)


def pw_amp(t):
    if t < PW_T0:
        return 0.0
    a = PW_A * smooth(prog(t, PW_T0, 10.55))
    if t > T_CRASH:
        a *= 1 - out_cubic(prog(t, T_CRASH, T_CRASH + 0.6))
    return a


XS = np.arange(W, dtype=np.float32)


def bump(c, w, a, front=0.5):
    u = (XS - c) / w
    return a * np.where(u < 0, np.exp(-(u / 1.15) ** 2), np.exp(-(u / front) ** 2))


def surface(t):
    s = SEA + 4.0 * np.sin(XS * 0.031 - t * 2.1) + 2.5 * np.sin(XS * 0.073 + t * 3.3)
    for k in range(len(WAVE_T)):
        a, c = wave_amp(k, t)
        if a > 0.3:
            s = s - bump(c, WAVE_W, a)
    a = pw_amp(t)
    if a > 0.3:
        s = s - bump(pw_c(t), PW_W, a, front=0.38)
    return s.astype(np.float32)


def at(S, x):
    return float(S[int(clamp(x, 0, W - 1))])


def slope(S, x):
    i = int(clamp(x, 2, W - 3))
    return math.atan((S[i + 2] - S[i - 2]) / 4.0)


# ---------------------------------------------------------------- poses (facing right, y down, relative to the hip)
STAND = {"head": (0, -150), "neck": (0, -108), "el": (-10, -58), "hl": (-14, -10), "er": (10, -58), "hr": (14, -10),
         "kl": (-9, 56), "fl": (-13, 113), "kr": (9, 56), "fr": (13, 113)}
ARMS_UP = dict(STAND, el=(-28, -146), hl=(-44, -194), er=(26, -148), hr=(40, -196))
SIT = {"head": (6, -150), "neck": (3, -108), "el": (16, -60), "hl": (34, -24), "er": (-6, -60), "hr": (2, -18),
       "kl": (34, 22), "fl": (30, 82), "kr": (24, 26), "fr": (16, 86)}
SIT_LOOKUP = dict(SIT, head=(-8, -150), neck=(-3, -108), el=(4, -66), hl=(26, -40))
SURF = {"head": (24, -134), "neck": (14, -93), "el": (-30, -82), "hl": (-74, -74), "er": (54, -76), "hr": (96, -88),
        "kl": (-40, 44), "fl": (-52, 98), "kr": (38, 40), "fr": (50, 98)}
AIR = {"head": (30, -118), "neck": (20, -80), "el": (-20, -70), "hl": (-66, -96), "er": (40, -30), "hr": (42, 40),
       "kl": (-34, 6), "fl": (-50, 60), "kr": (40, 0), "fr": (46, 60)}
HUG = {"head": (16, -140), "neck": (8, -98), "el": (40, -62), "hl": (60, -48), "er": (34, -58), "hr": (54, -44),
       "kl": (52, -52), "fl": (66, 4), "kr": (46, -48), "fr": (58, 6)}
SPLAT = {"head": (0, -150), "neck": (0, -108), "el": (-34, -140), "hl": (-44, -190), "er": (34, -140),
         "hr": (46, -190), "kl": (-16, 56), "fl": (-26, 112), "kr": (16, 56), "fr": (28, 110)}
CARRY = dict(STAND, el=(4, -60), hl=(22, -22))       # near arm holds the board at the hip

HIP_OFF = {"sit": (0, -14), "prone": (-34, -16), "surf": (0, -106), "air": (0, -64)}


def prone(ph):
    p = {"head": (134, -32), "neck": (94, -16), "kl": (-56, -2), "fl": (-112, -10), "kr": (-54, 2), "fr": (-108, 2)}
    for side, off in (("l", 0.0), ("r", math.pi)):
        th = math.pi / 2 - 1.05 * math.sin(ph + off)
        nx, ny = p["neck"]
        p["h" + side] = (nx + 92 * math.cos(th), ny + 92 * math.sin(th))
        p["e" + side] = (nx + 47 * math.cos(th - 0.35), ny + 47 * math.sin(th - 0.35))
    return p


def run(ph):
    p = {"head": (26, -146), "neck": (16, -104)}
    for side, off in (("l", 0.0), ("r", math.pi)):
        s = math.sin(ph + off)
        a = 0.62 * s
        kx, ky = 55 * math.sin(a), 55 * math.cos(a)
        bend = 0.25 + 1.0 * max(0.0, -math.cos(ph + off))
        p["k" + side] = (kx, ky)
        p["f" + side] = (kx + 58 * math.sin(a - bend), ky + 58 * math.cos(a - bend))
        b = -0.9 * s
        ex, ey = 16 + 46 * math.sin(b), -104 + 46 * math.cos(b)
        p["e" + side] = (ex, ey)
        p["h" + side] = (ex + 44 * math.sin(b + 1.1), ey + 44 * math.cos(b + 1.1))
    return p


def lerp_pose(a, b, k):
    return {j: (lerp(a[j][0], b[j][0], k), lerp(a[j][1], b[j][1], k)) for j in a}


def rot(p, ang):
    c, s = math.cos(ang), math.sin(ang)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def place(pose, hip, facing=1, ang=0.0):
    out = {"hip": hip}
    for j, (x, y) in pose.items():
        dx, dy = rot((x * facing, y), ang)
        out[j] = (hip[0] + dx, hip[1] + dy)
    return out


# ---------------------------------------------------------------- the doer's timeline
def build_doer_segs():
    S = []

    def add(a, b, kind, **kw):
        S.append((a, b, kind, kw))

    add(0.0, 0.45, "sit")
    add(0.45, 0.65, "to_prone")
    add(0.65, 0.9, "paddle")
    add(0.9, 1.0, "pop", k=0)
    add(1.0, 1.15, "ride", k=0)
    add(1.15, 1.45, "fall", k=0)
    add(1.45, 1.85, "hidden")
    add(1.85, 2.05, "emerge")
    add(2.05, 2.85, "sit")
    add(2.85, 3.05, "to_prone")
    add(3.05, 3.3, "paddle")
    add(3.3, 3.4, "pop", k=2)
    add(3.4, 3.72, "ride", k=2)
    add(3.72, 4.0, "fall", k=2)
    add(4.0, 4.2, "hidden")
    for k, carve in ((3, 0), (4, 1), (5, 1), (6, 1)):
        tw = WAVE_T[k]
        add(tw - 0.28, tw, "paddle_in")
        add(tw, tw + 0.1, "pop", k=k)
        if k < 6:
            add(tw + 0.1, tw + 0.55, "ride", k=k, carve=carve, trail=1)
            add(tw + 0.55, tw + 0.75, "kick", k=k)
            add(tw + 0.75, WAVE_T[k + 1] - 0.28, "hidden")
        else:
            add(tw + 0.1, tw + 0.45, "ride", k=k, carve=1, trail=1)
            add(tw + 0.45, tw + 0.78, "air", k=k)
            add(tw + 0.78, tw + 0.88, "kick", k=k, fromair=1)
            add(tw + 0.88, 9.05, "hidden")
    add(9.05, 9.25, "fade_sit")
    add(9.25, 10.18, "sit")
    add(10.18, 10.38, "to_prone")
    add(10.38, 10.63, "paddle")
    add(10.63, 10.75, "pop", k="pw")
    add(10.75, 10.98, "ride_pw")
    return S


DSEGS = build_doer_segs()

# the aerial off the perfect wave
A_T0 = 10.98
A_G = 3306.0
A_V0 = math.sqrt(2 * A_G * 80)
A_X1 = 540.0


def aerial_y0():
    return at(surface(A_T0), pw_c(A_T0) + 5) - 8


A_Y0 = aerial_y0()
# landing: when the board meets the calm water again
_tl = A_T0
while True:
    _tl += 1 / 600
    _tau = _tl - A_T0
    if A_Y0 - A_V0 * _tau + 0.5 * A_G * _tau ** 2 >= SEA - 8:
        break
T_LAND = _tl
A_X0 = pw_c(A_T0) + 5


def board_on(S, x, lift=8.0):
    return x, at(S, x) - lift, clamp(slope(S, x), -0.95, 0.95)


def doer_state(t, S=None):
    """Board centre (bx, by), board angle, rider pose + hip offset, extra spin, alpha, flags."""
    if S is None:
        S = surface(t)
    st = {"alpha": 1.0, "spin": 0.0, "rider_rot": 0.0, "hip_dy": 0.0, "trail": 0, "backlit": 0.0, "sep_board": None}
    bob = 0.06 * math.sin(t * 2.3)
    if t >= T_LAND:
        x = A_X1
        bx, by, ang = board_on(S, x, 6)
        k = smooth(prog(t, T_LAND, T_LAND + 0.28))
        st.update(bx=bx, by=by, ang=ang + bob * k, pose=lerp_pose(SURF, SIT, k),
                  hip=(lerp(HIP_OFF["surf"][0], HIP_OFF["sit"][0], k), lerp(HIP_OFF["surf"][1], HIP_OFF["sit"][1], k)))
        return st
    if t >= A_T0:
        tau = t - A_T0
        x = lerp(A_X0, A_X1, tau / (T_LAND - A_T0))
        y = A_Y0 - A_V0 * tau + 0.5 * A_G * tau * tau
        u = tau / (T_LAND - A_T0)
        ang = lerp(-0.55, 0.05, smooth(u)) - 0.25 * math.sin(math.pi * u)
        pose = lerp_pose(AIR, SURF, smooth(prog(u, 0.7, 1.0)))
        d = math.hypot(x + 10 - MX, y - 70 - MY)
        st.update(bx=x, by=y, ang=ang, pose=pose, hip=HIP_OFF["air"], backlit=clamp(1.25 - d / (MR * 1.9)))
        return st
    t = max(0.0, t)
    seg = DSEGS[0]
    for s in DSEGS:
        if s[0] <= t:
            seg = s           # the last segment that has started (covers rounding gaps between them)
    a, b, kind, kw = seg
    u = (t - a) / (b - a)
    if kind in ("sit", "fade_sit", "emerge"):
        bx, by, ang = board_on(S, LINE_X, 6)
        st.update(bx=bx, by=by, ang=ang + bob, pose=SIT, hip=HIP_OFF["sit"])
        if kind == "fade_sit":
            st["alpha"] = smooth(u)
        if kind == "emerge":
            st["hip_dy"] = 90 * (1 - out_cubic(u))
            st["alpha"] = smooth(u * 2)
        return st
    if kind == "hidden":
        st["alpha"] = 0.0
        bx, by, ang = board_on(S, LINE_X, 6)
        st.update(bx=bx, by=by, ang=ang, pose=SIT, hip=HIP_OFF["sit"])
        return st
    if kind == "to_prone":
        bx, by, ang = board_on(S, LINE_X, 6)
        k = smooth(u)
        p = lerp_pose(SIT, prone(0.0), k)
        hip = (lerp(HIP_OFF["sit"][0], HIP_OFF["prone"][0], k), lerp(HIP_OFF["sit"][1], HIP_OFF["prone"][1], k))
        st.update(bx=bx, by=by, ang=ang, pose=p, hip=hip)
        return st
    if kind in ("paddle", "paddle_in"):
        x = LINE_X - 24 * (1 - u)
        bx, by, ang = board_on(S, x, 6)
        st.update(bx=bx, by=by, ang=ang, pose=prone(t * 15.0), hip=HIP_OFF["prone"])
        if kind == "paddle_in":
            st["alpha"] = smooth(u * 3.5)
        return st
    if kind == "pop":
        k = kw["k"]
        c = pw_c(t) + 66 if k == "pw" else wave_c(k, t) + RIDE_OFF * WAVE_W
        bx, by, ang = board_on(S, c, 8)
        e = smooth(u)
        hip = (lerp(HIP_OFF["prone"][0], HIP_OFF["surf"][0], e), lerp(HIP_OFF["prone"][1], HIP_OFF["surf"][1], e))
        st.update(bx=bx, by=by, ang=ang, pose=lerp_pose(prone(0.0), SURF, e), hip=hip)
        return st
    if kind == "ride":
        k = kw["k"]
        carve = kw.get("carve", 0)
        tau = t - a
        x = wave_c(k, t) + RIDE_OFF * WAVE_W + (28 * math.sin(2 * math.pi * 1.6 * tau) if carve else 0)
        bx, by, ang = board_on(S, x, 8)
        if carve:
            ang += 0.22 * math.cos(2 * math.pi * 1.6 * tau)
        wob = 0.12 * math.sin(t * 40) if k in (0, 2) else 0.0
        st.update(bx=bx, by=by, ang=ang, pose=SURF, hip=HIP_OFF["surf"], rider_rot=wob, trail=kw.get("trail", 0),
                  carve=carve)
        return st
    if kind == "fall":
        k = kw["k"]
        x0 = wave_c(k, a) + RIDE_OFF * WAVE_W
        x = x0 + 70 * u
        bx, by, ang = board_on(S, x, 8)
        e = in_quad(u)
        st.update(bx=bx, by=by, ang=ang, pose=lerp_pose(SURF, ARMS_UP, smooth(u * 1.5)), hip=HIP_OFF["surf"],
                  rider_rot=1.9 * e, hip_dy=110 * e)
        st["sep_board"] = (bx - 70 * u, by - 110 * math.sin(math.pi * min(1.0, u * 1.2)), ang - 3.0 * u)
        st["alpha"] = 1.0 - smooth(prog(u, 0.75, 1.0))
        return st
    if kind == "kick":
        k = kw["k"]
        x = wave_c(k, t) + RIDE_OFF * WAVE_W - 150 * u - (40 if kw.get("fromair") else 0)
        bx, by, ang = board_on(S, x, 8)
        by -= 50 * math.sin(math.pi * u)
        st.update(bx=bx, by=by, ang=ang - 0.4 * u, pose=SURF, hip=HIP_OFF["surf"], trail=1)
        st["alpha"] = 1 - smooth(u)
        return st
    if kind == "air":
        k = kw["k"]
        x = wave_c(k, t) + RIDE_OFF * WAVE_W - 40 * u
        bx, by, ang = board_on(S, x, 8)
        by -= 170 * math.sin(math.pi * u)
        st.update(bx=bx, by=by, ang=ang * (1 - u), pose=lerp_pose(SURF, AIR, math.sin(math.pi * u)), hip=HIP_OFF["air"],
                  spin=-2 * math.pi * smooth(u), trail=1)
        return st
    if kind == "ride_pw":
        c = pw_c(t)
        off = 66 + 70 * math.sin(math.pi * clamp(u * 1.25)) - 60 * smooth(prog(u, 0.55, 1.0))
        bx, by, ang = board_on(S, c + off, 8)
        st.update(bx=bx, by=by, ang=ang, pose=SURF, hip=HIP_OFF["surf"], trail=1, carve=1)
        return st
    raise RuntimeError(kind)


def doer_points(st):
    """World joints of the rider and the board polygon parameters."""
    bx, by, ang = st["bx"], st["by"], st["ang"]
    spin = st["spin"]
    hx, hy = st["hip"]
    hip_local = rot((hx, hy + st["hip_dy"]), ang + spin)
    hip = (bx + hip_local[0], by + hip_local[1])
    pts = place(st["pose"], hip, 1, ang + spin + st["rider_rot"])
    if st["sep_board"]:
        board = st["sep_board"]
    else:
        board = (bx, by, ang + spin)
    return pts, board


# ---------------------------------------------------------------- the overthinker's timeline
OT_X = 960.0
OT_BOARD_STUCK = (1040.0, sand_y(1040.0) - 95 + 38, math.pi / 2 + 0.07)
OT_LIE_X = 855.0
BOARD_LAND = (1040.0, sand_y(1040.0) - 95 + 40)
BF_T0, BF_T1 = 11.2, 12.8
BF_X0, BF_Y0 = 735.0, SEA - 15.0
BF_G = 2600.0
BF_VX = (BOARD_LAND[0] - BF_X0) / (BF_T1 - BF_T0)
BF_VY = (BOARD_LAND[1] - BF_Y0 - 0.5 * BF_G * (BF_T1 - BF_T0) ** 2) / (BF_T1 - BF_T0)


def ot_state(t, S):
    """Returns (points or None, alpha, board (cx, cy, ang) or None, facing)."""
    f = -1
    ground = lambda x: sand_y(x) - 14
    if t < 9.0:
        hip = (OT_X, ground(OT_X) + 1.5 * math.sin(t * 2.0))
        p = dict(HUG)
        hd = 3 * math.sin(t * 1.3)
        p["head"] = (p["head"][0], p["head"][1] + hd)
        return place(p, hip, f), 1.0, OT_BOARD_STUCK, f
    if t < 9.3:
        k = smooth(prog(t, 9.0, 9.3))
        hip = (OT_X, lerp(ground(OT_X), sand_y(OT_X) - 113, k))
        return place(lerp_pose(HUG, STAND, k), hip, f), 1.0, OT_BOARD_STUCK, f
    if t < 10.0:
        u = t - 9.3
        jump = 34 * abs(math.sin(2 * math.pi * 2.2 * u)) * (1 - smooth(prog(t, 9.85, 10.0)))
        hip = (OT_X, sand_y(OT_X) - 113 - jump)
        return place(ARMS_UP, hip, f), 1.0, OT_BOARD_STUCK, f
    if t < 10.15:
        k = smooth(prog(t, 10.0, 10.15))
        hip = (OT_X, sand_y(OT_X) - 113)
        pts = place(lerp_pose(STAND, CARRY, k), hip, f)
        hl = pts["hl"]
        bx = lerp(OT_BOARD_STUCK[0], hl[0] - 10, k)
        by = lerp(OT_BOARD_STUCK[1], hl[1] + 4, k)
        return pts, 1.0, (bx, by, lerp(OT_BOARD_STUCK[2], 0.08, k)), f
    if t < 10.45:
        u = prog(t, 10.15, 10.45)
        x = lerp(OT_X, 830, u)
        hip = (x, sand_y(x) - 108 - 6 * abs(math.sin(t * 22)))
        p = run(t * 22)
        p["el"], p["hl"] = CARRY["el"], CARRY["hl"]
        pts = place(p, hip, f)
        return pts, 1.0, (pts["hl"][0] - 10, pts["hl"][1] + 4, 0.08), f
    if t < 10.85:
        u = prog(t, 10.45, 10.85)
        x = lerp(820, 735, u)
        by = at(S, x) - 6
        ang = -slope(S, x)
        hip_local = rot((HIP_OFF["prone"][0] * f, HIP_OFF["prone"][1]), ang)
        hip = (x + hip_local[0], by + hip_local[1])
        return place(prone(t * 9.0), hip, f, ang), 1.0, (x, by, ang), f
    if t < T_CRASH:
        u = prog(t, 10.85, 11.0)
        x = 735
        by = at(S, x) - 6
        ang = 0.0
        hip = (x, by - 14)
        return place(lerp_pose(prone(0.0), SIT_LOOKUP, smooth(u)), hip, f), 1.0, (x, by, ang), f
    board = None
    if t < BF_T1:
        tau = t - BF_T0
        if tau >= 0:
            bx = BF_X0 + BF_VX * tau
            by = BF_Y0 + BF_VY * tau + 0.5 * BF_G * tau * tau
            ang = math.pi / 2 - 8.0 * (BF_T1 - t)
            board = (bx, by, ang)
    else:
        wob = 0.22 * math.exp(-(t - BF_T1) * 9) * math.sin((t - BF_T1) * 40)
        board = (BOARD_LAND[0], BOARD_LAND[1], math.pi / 2 - 0.08 + wob)
    if t < 11.6:
        return None, 0.0, board, f
    u = prog(t, 11.6, 12.05)
    x = lerp(815, OT_LIE_X, out_cubic(u))
    hip_lift = rot((0, -16), SLOPE)
    hip = (x + hip_lift[0], sand_y(x) + hip_lift[1])
    return place(SPLAT, hip, 1, math.pi / 2 + SLOPE), smooth(u * 2.5), board, 1


# ---------------------------------------------------------------- the gull on the overthinker's board
def gull_state(t):
    perch = (OT_BOARD_STUCK[0] + 6, OT_BOARD_STUCK[1] - 96)
    if t < 4.2 or t > 10.0:
        return None
    if t < 4.7:
        u = smooth(prog(t, 4.2, 4.7))
        return (lerp(1180, perch[0], u), lerp(940, perch[1], u) - 40 * math.sin(math.pi * u), True, -1)
    if t < 9.32:
        return (perch[0], perch[1], False, -1)
    u = prog(t, 9.32, 10.0)
    return (lerp(perch[0], 1220, u), lerp(perch[1], 830, out_cubic(u)), True, 1)


# ---------------------------------------------------------------- drawing: sprites at 2x
SS = 2


class Canvas:
    """A 2x canvas over a world rectangle; draw in world coordinates, get a 1x RGBA sprite back."""

    def __init__(self, x0, y0, x1, y1):
        self.x0, self.y0 = int(math.floor(x0)), int(math.floor(y0))
        self.w, self.h = int(math.ceil(x1)) - self.x0, int(math.ceil(y1)) - self.y0
        self.im = Image.new("RGBA", (max(2, self.w * SS), max(2, self.h * SS)), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def P(self, p):
        return ((p[0] - self.x0) * SS, (p[1] - self.y0) * SS)

    def done(self):
        return self.im.reduce(SS), (self.x0, self.y0)


def seg(cv, a, b, w, col):
    pa, pb = cv.P(a), cv.P(b)
    r = w * SS / 2
    cv.d.line([pa, pb], fill=col, width=int(w * SS))
    for p in (pa, pb):
        cv.d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=col)


def disc(cv, p, r, col):
    q = cv.P(p)
    cv.d.ellipse([q[0] - r * SS, q[1] - r * SS, q[0] + r * SS, q[1] + r * SS], fill=col)


LIMB, OUT = 24, 6


def draw_stick(cv, pts, body, far, facing=1):
    ink = INK + (255,)
    order = [((("neck", "er"), ("er", "hr")), far, "hr"), ((("hip", "kr"), ("kr", "fr")), far, "fr"),
             ((("neck", "hip"),), body, None), ((("hip", "kl"), ("kl", "fl")), body, "fl"),
             ((("neck", "el"), ("el", "hl")), body, "hl")]
    for segs, col, end in order:
        w = LIMB + (4 if segs[0] == ("neck", "hip") else 0)
        for a, b in segs:
            seg(cv, pts[a], pts[b], w + 2 * OUT, ink)
        if end and end[0] == "f":
            fx, fy = pts[end]
            disc(cv, (fx + facing * 6, fy + 2), 13 + OUT, ink)
        if end and end[0] == "h":
            disc(cv, pts[end], 11 + OUT, ink)
        for a, b in segs:
            seg(cv, pts[a], pts[b], w, col + (255,))
        if end and end[0] == "f":
            fx, fy = pts[end]
            q = cv.P((fx + facing * 6, fy + 2))
            cv.d.ellipse([q[0] - 16 * SS, q[1] - 10 * SS, q[0] + 16 * SS, q[1] + 10 * SS], fill=col + (255,))
        if end and end[0] == "h":
            disc(cv, pts[end], 11, col + (255,))
    hx, hy = pts["head"]
    disc(cv, (hx, hy), 31 + OUT, ink)
    disc(cv, (hx, hy), 31, body + (255,))
    q = cv.P((hx - 10, hy - 11))
    cv.d.ellipse([q[0] - 9 * SS, q[1] - 6 * SS, q[0] + 9 * SS, q[1] + 6 * SS], fill=(255, 255, 255, 110))


def board_poly(cx, cy, ang, L=200, T=22, nose=1):
    top, bot = [], []
    for i in range(41):
        s = -1 + 2 * i / 40
        h = T / 2 * (1 - abs(s) ** 2.4) ** 0.55
        rocker = -14 * max(0.0, s * nose) ** 3
        x = s * L / 2
        top.append(rot((x, rocker - h), ang))
        bot.append(rot((x, rocker + h), ang))
    pts = top + bot[::-1]
    return [(cx + x, cy + y) for x, y in pts]


def draw_board(cv, b, col, stripe, tag=False, L=200):
    cx, cy, ang = b
    poly = board_poly(cx, cy, ang, L)
    cv.d.polygon([cv.P(p) for p in poly], fill=col + (255,), outline=INK + (255,))
    cv.d.line([cv.P(p) for p in poly] + [cv.P(poly[0])], fill=INK + (255,), width=4 * SS, joint="curve")
    a0, a1 = rot((-L * 0.42, 0), ang), rot((L * 0.42, 0), ang)
    cv.d.line([cv.P((cx + a0[0], cy + a0[1])), cv.P((cx + a1[0], cy + a1[1]))], fill=stripe + (255,), width=4 * SS)
    if tag:
        # the price tag on a string at the tail: the board was never used
        tail = rot((-L * 0.40, 0), ang)
        p0 = (cx + tail[0], cy + tail[1])
        p1 = (p0[0] - 6, p0[1] + 30)
        cv.d.line([cv.P(p0), cv.P(p1)], fill=(220, 220, 214, 255), width=2 * SS)
        tw, th = 30, 18
        r = [cv.P((p1[0] - tw / 2, p1[1])), cv.P((p1[0] + tw / 2, p1[1] + th))]
        cv.d.rounded_rectangle([r[0][0], r[0][1], r[1][0], r[1][1]], 3 * SS, fill=(236, 226, 196, 255),
                               outline=INK + (255,), width=2 * SS)
        cv.d.text(cv.P((p1[0] - 11, p1[1] + 1)), "$", font=font("Inter-Bold.otf", 15 * SS), fill=INK + (255,))


def bbox_of(points, pad=70):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad


def doer_sprite(st):
    pts, board = doer_points(st)
    bp = board_poly(*board)
    cv = Canvas(*bbox_of(list(pts.values()) + bp))
    body = lerp_c(DOER, (30, 34, 48), 0.86 * st["backlit"])
    far = lerp_c(DOER_FAR, (24, 28, 40), 0.86 * st["backlit"])
    draw_board(cv, board, lerp_c((238, 234, 224), (40, 44, 58), 0.8 * st["backlit"]), (240, 148, 56))
    draw_stick(cv, pts, body, far, 1)
    return cv.done(), pts, board


def ot_sprite(pts, board, facing):
    allp = (list(pts.values()) if pts else []) + (board_poly(*board) if board else [])
    cv = Canvas(*bbox_of(allp))
    if pts and board and pts.get("_board_front"):
        pass
    if board:
        draw_board(cv, board, (152, 152, 158), (104, 106, 114), tag=True)
    if pts:
        draw_stick(cv, pts, OT, OT_FAR, facing)
    return cv.done()


def gull_sprite(g, t):
    x, y, flying, facing = g
    cv = Canvas(x - 70, y - 80, x + 70, y + 30)
    body = (226, 228, 232, 255)
    ink = INK + (255,)
    f = facing
    q = cv.P((x, y - 22))
    cv.d.ellipse([q[0] - 26 * SS, q[1] - 12 * SS, q[0] + 26 * SS, q[1] + 12 * SS], fill=body, outline=ink, width=3 * SS)
    hq = cv.P((x + f * 22, y - 38))
    cv.d.ellipse([hq[0] - 11 * SS, hq[1] - 11 * SS, hq[0] + 11 * SS, hq[1] + 11 * SS], fill=body, outline=ink,
                 width=3 * SS)
    cv.d.polygon([cv.P((x + f * 31, y - 40)), cv.P((x + f * 46, y - 36)), cv.P((x + f * 31, y - 33))],
                 fill=(240, 170, 60, 255), outline=ink)
    e = cv.P((x + f * 25, y - 41))
    cv.d.ellipse([e[0] - 2 * SS, e[1] - 2 * SS, e[0] + 2 * SS, e[1] + 2 * SS], fill=ink)
    if flying:
        flap = math.sin(t * 26)
        for side in (-1, 1):
            tip = (x - f * 8 + side * 4, y - 22 - 46 * flap * side * 0 - 40 * flap)
            mid = (x - f * 2, y - 26)
            cv.d.line([cv.P(mid), cv.P((x - f * 30, tip[1] + 6)), cv.P((x - f * 52, tip[1] + 14))], fill=ink,
                      width=9 * SS, joint="curve")
            cv.d.line([cv.P(mid), cv.P((x - f * 30, tip[1] + 6)), cv.P((x - f * 52, tip[1] + 14))],
                      fill=(200, 202, 208, 255), width=4 * SS, joint="curve")
    else:
        q = cv.P((x - f * 6, y - 20))
        cv.d.ellipse([q[0] - 18 * SS, q[1] - 8 * SS, q[0] + 18 * SS, q[1] + 8 * SS], fill=(150, 154, 162, 255),
                     outline=ink, width=2 * SS)
        for dx in (-6, 6):
            cv.d.line([cv.P((x + dx, y - 12)), cv.P((x + dx, y + 2))], fill=(240, 170, 60, 255), width=3 * SS)
    return cv.done()


def glow_of(spr, strength, radius=14, col=(210, 228, 255)):
    a = spr.split()[3].filter(ImageFilter.GaussianBlur(radius)).point(lambda v: int(min(255, v * strength)))
    g = Image.new("RGBA", spr.size, col + (0,))
    g.putalpha(a)
    return g


# ---------------------------------------------------------------- the static background
YY = np.arange(H, dtype=np.float32)[:, None]
SAND_Y = sand_y(XS).astype(np.float32)


def build_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.clip(yy / HORIZON, 0, 1)[..., None]
    img = (1 - g) * np.array([4, 6, 14], np.float32) + g * np.array([18, 28, 54], np.float32)
    d = np.sqrt((xx - MX) ** 2 + (yy - MY) ** 2)
    glow = np.exp(-(d / 330) ** 2) * 0.55 + np.exp(-(d / 130) ** 2) * 0.6
    img += glow[..., None] * np.array([70, 84, 112], np.float32)
    # distant sea between the horizon and the action line
    sea = (yy >= HORIZON)
    k = np.clip((yy - HORIZON) / (SEA - HORIZON), 0, 1)[..., None]
    seac = (1 - k) * np.array([22, 34, 62], np.float32) + k * np.array([14, 24, 46], np.float32)
    refl = np.exp(-((xx - MX) / (60 + (yy - HORIZON) * 0.35)) ** 2) * np.exp(-((yy - HORIZON) / 520))
    seac = seac + refl[..., None] * np.array([60, 72, 96], np.float32)
    img = np.where(sea[..., None], seac, img)
    # moon disc
    m = np.clip((MR - d) / 1.5, 0, 1)[..., None]
    moon = np.array([238, 234, 216], np.float32) - np.clip((xx - MX + yy - MY) / MR, -1, 1)[..., None] * 10
    img = img * (1 - m) + moon * m
    # sand (the beach and the sea bed)
    sy = SAND_Y[None, :]
    sm = yy >= sy
    depth = np.clip((yy - sy) / 260, 0, 1)[..., None]
    sandc = (1 - depth) * np.array([96, 88, 88], np.float32) + depth * np.array([36, 34, 42], np.float32)
    rim = np.exp(-((yy - sy) / 3.0) ** 2)[..., None] * np.array([70, 72, 86], np.float32)
    sandc = sandc + rim
    under = (yy > SEA)[..., None]
    sandc = np.where(under, sandc * np.array([0.62, 0.78, 1.05], np.float32), sandc)
    img = np.where(sm[..., None], sandc, img)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")
    dr = ImageDraw.Draw(im)
    rng = np.random.default_rng(7)
    for _ in range(2600):
        x = rng.uniform(0, W)
        y = rng.uniform(sand_y(x) + 4, H)
        b = rng.uniform(-14, 14)
        c = im.getpixel((int(x), int(min(H - 1, y))))
        r = rng.uniform(0.8, 2.2)
        dr.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(clamp(v + b, 0, 255)) for v in c))
    for _ in range(280):
        x, y = rng.uniform(0, W), rng.uniform(0, HORIZON - 30)
        if math.hypot(x - MX, y - MY) < MR + 30:
            continue
        b = int(rng.uniform(70, 235))
        r = rng.choice([0.8, 1.0, 1.4, 2.0], p=[0.45, 0.3, 0.17, 0.08])
        dr.ellipse([x - r, y - r, x + r, y + r], fill=(b, b, min(255, b + 15)))
    for cx_, cy_, cr in ((MX - 22, MY - 12, 15), (MX + 18, MY + 20, 11), (MX + 26, MY - 26, 8), (MX - 10, MY + 30, 7)):
        dr.ellipse([cx_ - cr, cy_ - cr, cx_ + cr, cy_ + cr], fill=(222, 218, 200))
    # a far island on the horizon
    pts = [(0, HORIZON)]
    for i in range(0, 361, 12):
        pts.append((i, HORIZON - 34 * math.exp(-((i - 140) / 120) ** 2) - 14 * math.exp(-((i - 290) / 50) ** 2)
                    - 6 * math.sin(i * 0.11) ** 2))
    pts.append((360, HORIZON))
    dr.polygon(pts, fill=(9, 12, 24))
    dr.line([(0, HORIZON), (W, HORIZON)], fill=(52, 66, 96), width=2)
    return np.asarray(im).copy()


VIG = None


def build_vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.55) / (H * 0.62)) ** 2)
    return np.clip(1.08 - 0.42 * d ** 2, 0.55, 1.0)[..., None].astype(np.float32)


# rays of moonlight under the water
def build_rays():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    ang = np.arctan2(xx - MX, yy - (SEA - 650))
    r = (0.5 + 0.5 * np.cos(ang * 34)) ** 10 * 0.6 + (0.5 + 0.5 * np.cos(ang * 21 + 1.3)) ** 8 * 0.5
    return (r * np.exp(-np.clip(yy - SEA, 0, None) / 330)).astype(np.float32)


BG = RAYS = None


def init_worker():
    global BG, VIG, RAYS, FRAME0
    BG = build_bg()
    VIG = build_vignette()
    RAYS = build_rays()
    FRAME0 = None


# ---------------------------------------------------------------- particles
def droplets(dr, t, t0, x, y, n, power, seed, life=1.0, spread=(0.12, 0.88), g=2600.0, size=(3, 9),
             col=(226, 238, 255), floor=None):
    tau = t - t0
    if tau < 0 or tau > life:
        return
    rng = np.random.default_rng(seed)
    for i in range(n):
        a = math.pi * (1 + rng.uniform(*spread))
        v = power * rng.uniform(0.35, 1.0)
        lf = life * rng.uniform(0.55, 1.0)
        if tau > lf:
            continue
        px = x + rng.uniform(-30, 30) + math.cos(a) * v * tau
        py = y + math.sin(a) * v * tau + 0.5 * g * tau * tau
        if floor is not None and py > floor + 10 and tau > 0.15:
            continue
        r = rng.uniform(*size) * (1 - 0.5 * tau / lf)
        al = int(235 * (1 - (tau / lf) ** 2))
        dr.ellipse([px - r, py - r, px + r, py + r], fill=col + (al,))


def foam_blobs(dr, t, t0, x, y, n, seed, life=1.0, rise=230, spread=230, rmax=95):
    tau = t - t0
    if tau < 0 or tau > life:
        return
    rng = np.random.default_rng(seed)
    u = tau / life
    for i in range(n):
        ox = rng.uniform(-1, 1) * spread * (0.4 + 0.6 * out_cubic(u * 2))
        oy = -rng.uniform(0.2, 1.0) * rise * math.sin(math.pi * min(1.0, u * 1.25)) - rng.uniform(0, 40)
        r = rng.uniform(0.35, 1.0) * rmax * (0.35 + 0.65 * out_cubic(u * 3)) * (1 - 0.4 * u)
        al = int(250 * (1 - smooth(prog(u, 0.45, 1.0))))
        c = int(rng.uniform(225, 255))
        dr.ellipse([x + ox - r, y + oy - r, x + ox + r, y + oy + r], fill=(c, c, 255, al))


# ---------------------------------------------------------------- HUD text helpers
def spaced(dr, cx, y, s, f, fill, spacing):
    w = sum(f.getlength(ch) for ch in s) + spacing * (len(s) - 1)
    x = cx - w / 2
    for ch in s:
        dr.text((x, y), ch, font=f, fill=fill)
        x += f.getlength(ch) + spacing
    return w


def doer_count(t):
    if t < WAVE_T[3] + 0.55:
        return 0
    if t < T_LAND + 0.03:
        return 1 + int(round(40 * smooth(prog(t, 5.4, 8.6))))
    return 42


def day_at(t):
    if t < 2.6:
        return 1
    if t < 8.8:
        return 1 + int(round(363 * prog(t, 2.6, 8.6) ** 1.35))
    return 365


def last_change(fn, t, back=0.4):
    v = fn(t)
    s = t
    while s > t - back:
        s -= 1 / FPS
        if fn(s) != v:
            return s + 1 / FPS
    return -9


BUBBLES = [(0.25, 1.05, "TOO SMALL."), (1.55, 2.35, "TOLD YOU."), (3.25, 4.05, "TOO MESSY."),
           (4.6, 5.4, "TOO WINDY."), (5.9, 6.7, "NOT TODAY."), (7.15, 8.6, "WAITING FOR\nTHE PERFECT ONE."),
           (9.32, 10.15, "THAT'S THE ONE!"), (10.86, 11.15, "WAIT—"), (13.0, 16.2, "...")]
LINE1, LINE2 = "THE PERFECT WAVE CAME.", "HE WASN'T READY FOR IT."
T_L1, T_L2 = 12.35, 13.45
CPS = 26.0
_bub = {}


def bubble_sprite(s):
    if s in _bub:
        return _bub[s]
    f = font(MONO, 32)
    lines = s.split("\n")
    lw = max(f.getlength(l) + 2 * (len(l) - 1) for l in lines)
    lh = 40
    pw, ph = int(lw + 44), int(len(lines) * lh + 24)
    k = 2
    im = Image.new("RGBA", (pw * k, (ph + 24) * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([3 * k, 3 * k, (pw - 3) * k, (ph - 3) * k], 14 * k, fill=(14, 17, 26, 238),
                        outline=(236, 238, 244, 255), width=3 * k)
    tx = pw * 0.5
    d.polygon([((tx - 13) * k, (ph - 5) * k), ((tx + 13) * k, (ph - 5) * k), (tx * k, (ph + 20) * k)],
              fill=(236, 238, 244, 255))
    d.polygon([((tx - 8) * k, (ph - 7) * k), ((tx + 8) * k, (ph - 7) * k), (tx * k, (ph + 11) * k)],
              fill=(14, 17, 26, 255))
    im = im.reduce(k)
    dd = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        spaced(dd, pw / 2, 12 + i * lh, l, f, (240, 242, 246, 255), 2)
    _bub[s] = im
    return im


# ---------------------------------------------------------------- one frame
def frame(t, shake=True):
    S = surface(t)
    img = Image.fromarray(BG)
    dr = ImageDraw.Draw(img)
    # moonlight glitter on the far sea
    rng = np.random.default_rng(int(t * 7) + 11)
    for _ in range(80):
        y = rng.uniform(HORIZON + 6, SEA - 6)
        spread = 40 + (y - HORIZON) * 0.4
        x = MX + rng.normal(0, 1) * spread
        L = rng.uniform(6, 26) * (0.6 + (y - HORIZON) / 400)
        b = int(rng.uniform(120, 230) * math.exp(-abs(x - MX) / (spread * 1.6)))
        dr.line([(x - L / 2, y), (x + L / 2, y)], fill=(b, b + 4, min(255, b + 18)), width=2)
    base = np.asarray(img).copy()

    # the water body (a cut-away): lighter just under the surface, deep blue below, rays of moonlight
    y0 = int(max(0, S.min() - 2))
    sub = base[y0:]
    yy = YY[y0:]
    depth = yy - S[None, :]
    mask = (depth >= 0) & (yy < SAND_Y[None, :])
    tall = np.clip((SEA - 120 - S) / 380, 0, 1)[None, :, None]
    top = np.array([40, 78, 128], np.float32) * (1 - tall) + np.array([62, 136, 162], np.float32) * tall
    kd = np.clip(depth / 520, 0, 1)[..., None]
    water = top * (1 - kd) + np.array([5, 11, 24], np.float32) * kd
    water += RAYS[y0:, :, None] * np.array([26, 40, 60], np.float32)
    water += np.exp(-np.clip(depth, 0, None) / 7)[..., None] * np.array([36, 46, 62], np.float32)
    sub[:] = np.where(mask[..., None], np.clip(water, 0, 255).astype(np.uint8), sub)
    wmask = np.zeros((H, W), bool)
    wmask[y0:] = mask

    # ---- actors
    act = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    st = doer_state(t, S)
    d_pts = None
    if st["alpha"] > 0.01:
        if st.get("trail"):
            for lag, al in ((0.1, 0.16), (0.05, 0.3)):
                s2 = doer_state(t - lag)
                if s2["alpha"] > 0.01 and s2.get("trail"):
                    (spr2, off2), _, _ = doer_sprite(s2)
                    spr2.putalpha(spr2.split()[3].point(lambda v, a=al * s2["alpha"]: int(v * a)))
                    act.alpha_composite(spr2, off2)
        (spr, off), d_pts, d_board = doer_sprite(st)
        gl = glow_of(spr, 0.75 + 1.4 * st["backlit"], 14 + 6 * st["backlit"])
        if st["alpha"] < 0.999:
            spr.putalpha(spr.split()[3].point(lambda v: int(v * st["alpha"])))
            gl.putalpha(gl.split()[3].point(lambda v: int(v * st["alpha"])))
        act.alpha_composite(gl, off)
        act.alpha_composite(spr, off)
    o_pts, o_al, o_board, o_f = ot_state(t, S)
    if o_pts or o_board:
        spr, off = ot_sprite(o_pts if o_al > 0.01 else None, o_board, o_f)
        if o_pts and o_al < 0.999:
            # fade the body only while it washes up; the board is drawn in the same sprite, keep it simple
            spr.putalpha(spr.split()[3].point(lambda v: int(v * max(o_al, 0.0 if not o_board else o_al))))
        act.alpha_composite(spr, off)
    g = gull_state(t)
    if g:
        spr, off = gull_sprite(g, t)
        act.alpha_composite(spr, off)
    A = np.asarray(act).astype(np.float32)
    a = A[..., 3:4] / 255
    rgb = A[..., :3]
    # what is under the water line is seen through the water
    wm = wmask[..., None]
    rgb = np.where(wm, rgb * 0.42 + np.array([30, 62, 104], np.float32) * 0.58, rgb)
    a = np.where(wm, a * 0.9, a)
    out = base.astype(np.float32) * (1 - a) + rgb * a

    # ---- the water line, foam, the lip, splashes (in front of everyone)
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    line = [(float(x), float(S[x])) for x in range(0, W, 3) if S[x] < SAND_Y[x] - 1]
    if len(line) > 2:
        od.line(line, fill=(150, 190, 240, 60), width=10, joint="curve")
        od.line(line, fill=(196, 222, 255, 230), width=3, joint="curve")
    # breaking waves: white water on the crest and foam lines behind
    for k in range(len(WAVE_T)):
        amp, c = wave_amp(k, t)
        br = smooth(prog(c, 470, 640)) * (1 - smooth(prog(c, 940, 1080)))
        if br <= 0.01:
            continue
        r2 = np.random.default_rng(100 + k)
        for i in range(70):
            x = c + r2.uniform(-0.45, 0.55) * WAVE_W + (c - 640) * 0.15 * r2.uniform(0, 1)
            if x < 0 or x >= W:
                continue
            y = min(at(S, x), sand_y(x)) - r2.uniform(-4, 14)
            rr = r2.uniform(4, 12) * (0.6 + 0.4 * br)
            al = int(230 * br * r2.uniform(0.5, 1))
            od.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(236, 244, 255, al))
        for i in range(30):
            x = c - r2.uniform(0.6, 2.2) * WAVE_W
            if x < 0 or x >= W:
                continue
            y = at(S, x) + r2.uniform(-2, 3)
            L = r2.uniform(6, 22)
            od.line([(x - L, y), (x + L, y)], fill=(220, 232, 250, int(120 * br)), width=3)
    # the perfect wave: spray off the crest, the lip, the crash, the white water
    pa = pw_amp(t)
    pc = pw_c(t)
    if pa > 120 and t < T_CRASH:
        cy = at(S, pc)
        r2 = np.random.default_rng(int(t * FPS))
        for i in range(int(40 * clamp((pa - 120) / 300))):
            x = pc + r2.uniform(-60, 40)
            y = cy - r2.uniform(0, 60)
            rr = r2.uniform(1.5, 4.5)
            od.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(230, 240, 255, int(r2.uniform(60, 170))))
        s = smooth(prog(t, 10.15, 10.95))
        f = in_quad(prog(t, 10.95, T_CRASH))
        if s > 0.01:
            L = 0.95 * PW_W * s
            P0 = (pc - 6, cy + 14)
            P1 = (pc + 0.5 * L, cy - 0.28 * L)
            P2 = (pc + (0.95 + 0.1 * f) * L, cy + (0.12 + 1.85 * f) * L)
            pts = []
            for i in range(26):
                u = i / 25
                bx = (1 - u) ** 2 * P0[0] + 2 * (1 - u) * u * P1[0] + u * u * P2[0]
                by = (1 - u) ** 2 * P0[1] + 2 * (1 - u) * u * P1[1] + u * u * P2[1]
                pts.append((bx, by, 44 * (1 - u) + 9))
            for bx, by, r in pts:
                od.ellipse([bx - r - 3, by - r - 3, bx + r + 3, by + r + 3], fill=(200, 226, 252, 255))
            for bx, by, r in pts:
                od.ellipse([bx - r, by - r + 4, bx + r, by + r + 4], fill=(58, 128, 160, 255))
            tx, ty, _ = pts[-1]
            r2 = np.random.default_rng(int(t * FPS) + 5)
            for i in range(14):
                rr = r2.uniform(3, 9)
                x, y = tx + r2.uniform(-18, 18), ty + r2.uniform(-18, 10)
                od.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(236, 244, 255, 220))
    fl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fl)
    # crash: an explosion of white water over the overthinker
    foam_blobs(fd, t, T_CRASH, 740, SEA - 30, 46, 9, life=1.15, rise=260, spread=230, rmax=96)
    droplets(od, t, T_CRASH, 740, SEA - 50, 140, 2300, 3, life=1.2, spread=(0.08, 0.92), size=(3, 10), floor=SEA)
    # the white water runs up the beach and back
    if T_CRASH < t < 13.4:
        xf = 735 + (1010 - 735) * out_cubic(prog(t, T_CRASH, 11.9)) - 70 * smooth(prog(t, 11.9, 12.7))
        fade = 1 - smooth(prog(t, 12.4, 13.4))
        r2 = np.random.default_rng(42)
        for i in range(120):
            x = xf - r2.uniform(0, 420)
            if x < 0 or x >= W:
                continue
            ytop = min(at(S, x), sand_y(x))
            y = ytop - r2.uniform(-3, 16) * (1 + 0.6 * (1 - prog(t, T_CRASH, 12.2)))
            rr = r2.uniform(5, 15)
            od.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(236, 244, 255, int(r2.uniform(120, 235) * fade)))
    # wipe-outs and landings
    for t0, x, y, n, pw_, sd in SPLASHES:
        droplets(od, t, t0, x, y, n, pw_, sd, life=0.8, floor=SEA)
        foam_blobs(fd, t, t0, x, y, 10, sd + 1, life=0.6, rise=60, spread=60, rmax=30)
    # spray off the tail when the doer carves
    if st["alpha"] > 0.3 and st.get("carve") and d_pts is not None:
        for j in range(12):
            te = t - j * 0.025
            s3 = doer_state(te)
            if not s3.get("carve"):
                continue
            tail = rot((-80, 6), s3["ang"])
            tx, ty = s3["bx"] + tail[0], s3["by"] + tail[1]
            tau = t - te
            r2 = np.random.default_rng(int(te * 1000))
            for i in range(4):
                vx = r2.uniform(-380, -120)
                vy = r2.uniform(-520, -200)
                x = tx + vx * tau
                y = ty + vy * tau + 0.5 * 2400 * tau * tau
                rr = r2.uniform(2, 5) * (1 - tau * 2)
                if rr > 0.5:
                    od.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(230, 240, 255, int(220 * (1 - tau * 3.2))))
    # the board lands in the sand: a puff of sand
    droplets(od, t, BF_T1, BOARD_LAND[0], sand_y(BOARD_LAND[0]) - 4, 26, 520, 77, life=0.55,
             spread=(0.05, 0.95), g=1600, size=(2, 5), col=(150, 140, 128))
    if fl.getbbox():
        img.alpha_composite(fl.filter(ImageFilter.GaussianBlur(3)))
    img.alpha_composite(ov)

    # ---- HUD
    hd = ImageDraw.Draw(img)
    day = day_at(t)
    dpop = math.exp(-max(0.0, t - 8.8) * 6) if t >= 8.8 else 0.0
    fl_ = font("Inter-SemiBold.otf", 34)
    fnum = font("InterDisplay-Bold.otf", int(44 * (1 + 0.35 * dpop)))
    wl = sum(fl_.getlength(c) for c in "DAY") + 16
    wn = fnum.getlength(str(day))
    x0 = W / 2 - (wl + 18 + wn) / 2
    spaced(hd, x0 + wl / 2, 172, "DAY", fl_, (150, 158, 176, 255), 8)
    hd.text((x0 + wl + 18, 166 - 8 * dpop), str(day), font=fnum, fill=(240, 242, 248, 255))
    spaced(hd, W / 2, 252, "WAVES CAUGHT", font("Inter-SemiBold.otf", 28), (140, 148, 166, 255), 9)
    nd = doer_count(t)
    ch = last_change(doer_count, t)
    pop = math.exp(-(t - ch) * 11) if ch > 0 else 0.0
    f0 = font("InterDisplay-Bold.otf", 118)
    spaced(hd, 330, 292, "0", f0, (168, 172, 182, 255), 0)
    fN = font("InterDisplay-Bold.otf", int(118 * (1 + 0.22 * pop)))
    num = str(nd)
    wN = fN.getlength(num)
    if pop > 0.05:
        gl = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
        ImageDraw.Draw(gl).text((750 - wN / 2, 60 - 12 * pop), num, font=fN,
                                fill=(200, 225, 255, int(200 * pop)))
        gl = gl.filter(ImageFilter.GaussianBlur(14))
        img.alpha_composite(gl, (0, 232))
    hd.text((750 - wN / 2, 292 - 12 * pop), num, font=fN, fill=(250, 250, 252, 255))
    fn_ = font("Inter-SemiBold.otf", 30)
    spaced(hd, 330, 434, "OVERTHINKER", fn_, (150, 154, 166, 255), 7)
    spaced(hd, 750, 434, "DOER", fn_, (240, 242, 248, 255), 7)

    # ---- the overthinker's lines
    for b0, b1, s in BUBBLES:
        if b0 <= t < b1:
            if s == "..." and o_pts:
                head = o_pts["head"]
                anchor = (head[0], head[1] - 52)
            elif o_pts:
                head = o_pts["head"]
                anchor = (head[0] - 6, head[1] - 54)
            else:
                continue
            bs = bubble_sprite(s)
            sc = out_back(prog(t, b0, b0 + 0.16)) * (1 - smooth(prog(t, b1 - 0.1, b1)) * 0.0)
            al = 1 - smooth(prog(t, b1 - 0.1, b1))
            if sc < 0.05:
                continue
            spr = bs.resize((max(1, int(bs.width * sc)), max(1, int(bs.height * sc))), Image.LANCZOS)
            if al < 0.999:
                spr.putalpha(spr.split()[3].point(lambda v: int(v * al)))
            x = anchor[0] - spr.width / 2
            x = clamp(x, 24, W - 24 - spr.width)
            y = anchor[1] - spr.height
            img.alpha_composite(spr, (int(x), int(y)))

    # ---- the line, typed
    fm = font(MONO, 50)
    for (t0, s, y) in ((T_L1, LINE1, 528), (T_L2, LINE2, 596)):
        n = int(clamp((t - t0) * CPS, 0, len(s)))
        if t < t0:
            continue
        part = s[:n]
        full_w = sum(fm.getlength(c) for c in s) + 3 * (len(s) - 1)
        x = W / 2 - full_w / 2
        tl = Image.new("RGBA", (W, 90), (0, 0, 0, 0))
        tdr = ImageDraw.Draw(tl)
        xx = x
        for c in part:
            tdr.text((xx, 14), c, font=fm, fill=(250, 250, 252, 255))
            xx += fm.getlength(c) + 3
        typing = n < len(s) or (s == LINE2 and t < T_L2 + len(s) / CPS + 1.2)
        if typing and int(t * 3.4) % 2 == 0:
            tdr.rectangle([xx + 2, 20, xx + 26, 70], fill=(250, 250, 252, 220))
        sh = tl.filter(ImageFilter.GaussianBlur(10))
        img.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", sh.size, (0, 0, 0)).split(), sh.split()[3])),
                            (0, y - 10))
        img.alpha_composite(tl, (0, y - 10))

    arr = np.asarray(img.convert("RGB")).astype(np.float32) * VIG
    # the crash and the board shake the camera
    if shake:
        amp = 20 * math.exp(-max(0.0, t - T_CRASH) * 7) if t >= T_CRASH else 0.0
        amp += 7 * math.exp(-max(0.0, t - BF_T1) * 12) if t >= BF_T1 else 0.0
        if amp > 0.6:
            dx = int(amp * math.sin(t * 97))
            dy = int(amp * math.cos(t * 83))
            arr = np.roll(arr, (dy, dx), axis=(0, 1))
    return np.clip(arr, 0, 255).astype(np.uint8)


def splashes():
    out = []
    for s in DSEGS:
        if s[2] == "fall":
            te = s[1] - 0.1
            st = doer_state(te)
            pts, _ = doer_points(st)
            out.append((te, pts["head"][0], SEA - 4, 34, 900, int(te * 100)))
        if s[2] == "emerge":
            out.append((s[0] + 0.05, LINE_X, SEA - 4, 14, 420, int(s[0] * 100)))
    out.append((T_LAND, A_X1, SEA - 4, 40, 1100, 555))
    out.append((10.5, 740, SEA - 4, 10, 380, 556))
    return out


SPLASHES = splashes()
FRAME0 = None


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
def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / max(d, 1e-4))


def tone(f, dur, harm=(1.0,), a=0.004, d=0.2, sweep=None):
    n = int(dur * SR)
    t = np.arange(n) / SR
    fr = f * (sweep / f) ** (t / dur) if sweep else np.full(n, f)
    ph = 2 * np.pi * np.cumsum(fr) / SR
    return sum(h * np.sin(ph * (i + 1)) for i, h in enumerate(harm)) * env(n, a, d)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def mix_in(buf, sig, at_, g=1.0, pan=0.0):
    i = int(at_ * SR)
    if i >= len(buf) or i + len(sig) <= 0:
        return
    if i < 0:
        sig, i = sig[-i:], 0
    sig = sig[: len(buf) - i]
    l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
    buf[i:i + len(sig), 0] += sig * g * l * 1.41
    buf[i:i + len(sig), 1] += sig * g * r * 1.41


def filt(x, lo=None, hi=None):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.ones_like(f)
    if hi:
        g /= 1 + (f / hi) ** 4
    if lo:
        g *= 1 - 1 / (1 + (f / lo) ** 4)
    return np.fft.irfft(X * g, len(x))


def noise(dur, seed, lo=None, hi=None):
    r = np.random.default_rng(seed)
    x = filt(r.standard_normal(int(dur * SR)), lo, hi)
    return x / (np.abs(x).max() + 1e-9)


def audio():
    n = int(DUR * SR)
    mus, fx = np.zeros((n, 2)), np.zeros((n, 2))
    # lo-fi loop, bars 0-3.5: Dmaj7 - C#m7 - Bm7 - Amaj7
    chords = [[50, 54, 57, 61], [49, 52, 56, 59], [47, 50, 54, 57], [45, 49, 52, 56]]
    roots = [38, 37, 35, 33]
    for b in range(4):
        t0 = b * BAR
        ch, rt = chords[b], roots[b]
        last = 2 if b == 3 else 4                      # the music stops at 8.4 s: the sea goes quiet
        for k, m in enumerate(ch):
            mix_in(mus, tone(midi(m), (last * BEAT) + 0.6, (1, 0.35, 0.12, 0.05), a=0.02, d=1.1), t0, 0.05,
                   (k - 1.5) * 0.35)
        for q in range(last):
            tb = t0 + q * BEAT
            mix_in(mus, tone(105, 0.32, (1,), a=0.002, d=0.11, sweep=42), tb, 0.6 if q % 2 == 0 else 0.35)
            mix_in(mus, tone(midi(rt), BEAT * 0.9, (1, 0.4, 0.1), a=0.005, d=0.3), tb, 0.22)
            if q % 2 == 1:
                mix_in(mus, noise(0.12, 900 + b * 4 + q, lo=900, hi=5000) * env(int(0.12 * SR), 0.001, 0.03), tb, 0.16)
            for e in range(2):
                mix_in(mus, noise(0.04, 300 + b * 8 + q * 2 + e, lo=6000) * env(int(0.04 * SR), 0.0005, 0.008),
                       tb + e * BEAT / 2, 0.05, 0.4 - 0.8 * e)
        for q in range(last):
            if (b * 4 + q) % 3 != 2:
                m = ch[(q * 2 + b) % 4] + 12
                mix_in(mus, tone(midi(m), 0.5, (1, 0.25, 0.08), a=0.004, d=0.18), t0 + q * BEAT + BEAT / 2, 0.07, 0.2)
    # the end, bars 5-6: Bm7 -> Amaj7, soft, it resolves into Dmaj7 at the loop
    for b, (ch, rt) in enumerate(((chords[2], roots[2]), (chords[3], roots[3]))):
        t0 = 5 * BAR + b * BAR
        for k, m in enumerate(ch):
            mix_in(mus, tone(midi(m), BAR + 0.4, (1, 0.3, 0.1), a=0.25, d=1.6), t0, 0.06, (k - 1.5) * 0.4)
        mix_in(mus, tone(midi(rt), BAR, (1, 0.3), a=0.1, d=1.2), t0, 0.18)
        for q, m in enumerate((ch[3] + 12, ch[2] + 12, ch[1] + 12)):
            mix_in(mus, tone(midi(m), 0.9, (1, 0.2, 0.06), a=0.004, d=0.4), t0 + q * BEAT * 1.33 + 0.2, 0.06, 0.2)
    # tension, 8.4 -> the crash: a drone, a heartbeat, the wave's roar rising
    td = T_CRASH - 8.4
    nd = int(td * SR)
    tt = np.arange(nd) / SR
    dr = (np.sin(2 * np.pi * 55 * tt) + 0.5 * np.sin(2 * np.pi * 82.4 * tt)) * (tt / td) ** 1.5
    mix_in(mus, dr, 8.4, 0.22)
    for hb in (8.85, 9.45, 9.95, 10.38, 10.7, 10.93):
        mix_in(mus, tone(62, 0.3, (1, 0.3), a=0.003, d=0.09, sweep=40), hb, 0.55)
        mix_in(mus, tone(58, 0.3, (1, 0.3), a=0.003, d=0.08, sweep=38), hb + 0.18, 0.35)
    roar = noise(td, 21, lo=60, hi=900) * (tt / td) ** 2.2
    mix_in(fx, roar, 8.4, 0.5)
    riser = noise(1.0, 22, lo=1500, hi=7000) * np.linspace(0, 1, int(SR)) ** 3
    mix_in(fx, riser, T_CRASH - 1.0, 0.18)
    # the crash
    nb = int(1.8 * SR)
    mix_in(fx, noise(1.8, 23, lo=40, hi=2500) * env(nb, 0.005, 0.5), T_CRASH, 0.95)
    mix_in(fx, noise(1.2, 24, lo=2000, hi=9000) * env(int(1.2 * SR), 0.003, 0.25), T_CRASH, 0.35)
    mix_in(fx, tone(48, 1.4, (1, 0.4), a=0.004, d=0.45, sweep=30), T_CRASH, 0.9)
    # the doer lands, the counter: 42
    mix_in(fx, noise(0.5, 25, lo=400, hi=4000) * env(int(0.5 * SR), 0.003, 0.12), T_LAND, 0.4, -0.3)
    for k, m in enumerate((81, 88)):
        mix_in(fx, tone(midi(m), 0.6, (1, 0.3), a=0.002, d=0.25), T_LAND + 0.04 + k * 0.08, 0.1, 0.3)
    # the board in the sand: thunk + a wobble
    mix_in(fx, tone(95, 0.3, (1, 0.5, 0.2), a=0.001, d=0.08, sweep=60), BF_T1, 0.6, 0.5)
    mix_in(fx, noise(0.25, 26, lo=300, hi=3000) * env(int(0.25 * SR), 0.001, 0.05), BF_T1, 0.25, 0.5)
    mix_in(fx, tone(210, 0.35, (1, 0.3), a=0.002, d=0.15) * np.sin(np.arange(int(0.35 * SR)) / SR * 2 * np.pi * 11),
           BF_T1 + 0.02, 0.12, 0.5)
    # the sea: a low bed all the time, a wash for each wave on the beach
    bed = noise(DUR, 27, lo=80, hi=700)
    mix_in(fx, bed, 0, 0.09)
    for k in range(len(WAVE_T)):
        tshore = WAVE_T[k] + (SHORE - wave_c(k, WAVE_T[k])) / WAVE_SPEED
        w = noise(1.3, 40 + k, lo=200, hi=3500) * env(int(1.3 * SR), 0.35, 0.35)
        mix_in(fx, w, tshore - 0.3, 0.2, 0.4)
    wsh = noise(2.0, 60, lo=150, hi=3000) * env(int(2.0 * SR), 0.4, 0.6)
    mix_in(fx, wsh, 11.6, 0.35, 0.4)
    # wipe-outs, the rides
    for t0, x, y, nn, p, sd in SPLASHES:
        mix_in(fx, noise(0.5, sd, lo=500, hi=6000) * env(int(0.5 * SR), 0.002, 0.11), t0, 0.32, (x / W) * 2 - 1)
    for k in (3, 4, 5, 6):
        mix_in(fx, noise(0.5, 70 + k, lo=1200, hi=7000) * env(int(0.5 * SR), 0.12, 0.15), WAVE_T[k] + 0.1, 0.12, -0.3)
    mix_in(fx, noise(0.6, 80, lo=1200, hi=7000) * env(int(0.6 * SR), 0.15, 0.2), 10.75, 0.18, -0.2)
    # the gull
    for tg in (4.35, 9.36):
        for j in range(2):
            mix_in(fx, tone(1700, 0.16, (1, 0.5, 0.3, 0.2), a=0.01, d=0.07, sweep=1150), tg + j * 0.2, 0.06, 0.6)
    # the overthinker's bubbles
    for b0, b1, s in BUBBLES:
        mix_in(fx, tone(560, 0.11, (1, 0.3), a=0.002, d=0.05, sweep=1100), b0, 0.12, 0.4)
    # typewriter
    for t0, s in ((T_L1, LINE1), (T_L2, LINE2)):
        for i, c in enumerate(s):
            if c != " ":
                mix_in(fx, noise(0.03, 500 + i, lo=2000, hi=8000) * env(int(0.03 * SR), 0.0005, 0.006),
                       t0 + i / CPS, 0.12, 0.0)
    x = mus * 0.9 + fx
    # the end dissolves into the start, like the picture
    m = int(XFADE * SR)
    k = np.linspace(0, 1, m)[:, None]
    x[-m:] = x[-m:] * (1 - k) + x[:m] * k
    x /= max(1.0, np.abs(x).max() / 0.9)
    return x


def write_wav(path, x):
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "perfect-wave.mp4"
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
                          "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                          out], stdin=subprocess.PIPE)
    with Pool(os.cpu_count(), initializer=init_worker) as pool:
        for i, b in enumerate(pool.imap(render, range(NF), chunksize=4)):
            p.stdin.write(b)
            if i % 60 == 0:
                print(f"{i}/{NF}", flush=True)
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print(out)


if __name__ == "__main__":
    main()
