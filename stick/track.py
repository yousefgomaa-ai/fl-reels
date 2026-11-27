#!/usr/bin/env python3
"""NEVER STAY DOWN - a 400 m race at night. Real motion capture (CMU) for every runner, a tracking camera.

Cold open: he's mid-fall, EGO looks back. "EVERYONE PASSED HIM."
BANG - five runners. YOU (red scarf) climbs from 5th... EGO cuts in, clips him, he goes down (slow motion).
Everyone passes him. He gets up, limping, then runs - and passes them one by one. Last metres vs EGO, slow motion,
chest first. FALLING IS PART OF THE RACE. / STAYING DOWN ISN'T.

    python3 stick/track.py --stills [t ...]   # -> stick/track/stills.png
    python3 stick/track.py stick/track.mp4
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
import mocap  # noqa
from compare import ell, line, rrect, poly, figure, place, K, W, H  # noqa
from perfect_wave import clamp, env, font, lerp, mix_in, noise, prog, smooth, tone, write_wav  # noqa
from money_chars import hero, face, outfit, S, GOLD  # noqa
from money_chars import scarf  # noqa
from money import put, track, text  # noqa
from failfast import whip  # noqa

FPS, SR = 30, 44100
D = mocap.CMU + "/"
_C = {}


def clip(n):
    if n not in _C:
        _C[n] = mocap.load(D + n + ".bvh")
    return _C[n]


RUN, RUN_A, RUN_P, STRIDE = "009/09_01", 0.30, 0.742, 430.0
DIVE, GETUP, LIMP, WALK = "090/90_16", "140/140_01", "091/91_24", "091/91_04"
TRIP = "104/104_13"
STAND = PW.STAND
SET = dict(STAND, head=(46, -126), neck=(34, -92), kl=(34, 36), fl=(4, 104), kr=(-12, 50), fr=(-44, 110),
           el=(46, -48), hl=(40, -6), er=(14, -50), hr=(6, -8))
KNEES = dict(STAND, head=(44, -118), neck=(32, -86), el=(44, -40), hl=(36, 10), er=(52, -36), hr=(46, 14),
             kl=(12, 56), fl=(-4, 113), kr=(22, 56), fr=(16, 113))
VICTORY = dict(PW.ARMS_UP)

# ---------------------------------------------------------------- the race (story time s)
S_BANG = 0.6
S_HIT = 8.4            # EGO clips him
S_GROUND = 9.35
S_LAUGH0, S_LAUGH1 = 10.0, 11.7
S_UP0, S_UP1 = 11.9, 13.3
S_LIMP1 = 14.5
S_RUN = 15.2
S_FIN = 24.0
S_END = 27.9
DT = 1 / 240
TT = np.arange(0, S_END + 1, DT)

RUNNERS = {
    # name: lane, colour, speed keys
    "TALENT": (1, (222, 178, 60), [(0, 0), (S_BANG, 0), (1.2, 500), (12, 500), (15, 450), (18, 360), (S_END, 320)]),
    "MOTIVATION": (2, (70, 140, 230), [(0, 0), (S_BANG, 0), (1.1, 590), (3.4, 590), (5.0, 330), (S_END, 300)]),
    "YOU": (4, None, [(0, 0), (S_BANG, 0), (1.3, 500), (S_HIT, 490), (S_HIT + 0.3, 330), (S_GROUND, 60), (S_GROUND + 0.2, 0),
                      (S_UP1, 0), (S_UP1 + 0.3, 120), (S_LIMP1, 230), (S_RUN, 520), (S_RUN + 0.8, 760), (S_FIN - 2, 760),
                      (S_FIN, 800), (S_FIN + 0.8, 520), (S_FIN + 2.4, 90), (S_FIN + 3.0, 0), (S_END, 0)]),
    "EGO": (3, (140, 80, 200), [(0, 0), (S_BANG, 0), (1.2, 480), (S_HIT, 480), (16, 480), (S_FIN - 3, 470), (S_FIN, 470),
                                (S_FIN + 1.5, 200), (S_FIN + 2.5, 0), (S_END, 0)]),
    "LUCK": (0, (70, 175, 95), [(0, 0), (S_BANG, 0), (1.15, 465), (14, 465), (19, 430), (S_END, 400)]),
}
ORDER = ["LUCK", "TALENT", "MOTIVATION", "EGO", "YOU"]   # far -> near


def speed_curve(keys, nm=""):
    ks = np.array(keys, float)
    fast = ~((ks[:, 0] > S_UP1) & (ks[:, 0] <= S_LIMP1)) if nm == "YOU" else np.ones(len(ks), bool)
    ks[fast, 1] *= 2.0          # twice as fast
    return np.interp(TT, ks[:, 0], ks[:, 1])


X = {}
for nm, (lane, col, keys) in RUNNERS.items():
    v = speed_curve(keys, nm)
    X[nm] = np.concatenate([[0.0], np.cumsum((v[1:] + v[:-1]) / 2 * DT)])
    X[nm] += {"TALENT": 0, "MOTIVATION": 0, "YOU": 0, "EGO": 0, "LUCK": 0}[nm]
X_F = float(np.interp(S_FIN, TT, X["YOU"]))
# EGO must be just behind at the line: scale his race so he's 45 px short at S_FIN
_e = float(np.interp(S_FIN, TT, X["EGO"]))
_scale = (X_F - 80) / _e
X["EGO"] = np.where(TT <= S_FIN, X["EGO"] * _scale, X["EGO"] - _e + (X_F - 80))


def xat(nm, s):
    return float(np.interp(s, TT, X[nm]))


def vat(nm, s):
    return (xat(nm, s + 0.01) - xat(nm, s - 0.01)) / 0.02


def lane_of(nm, s):
    lane = RUNNERS[nm][0]
    if nm == "EGO":   # cuts into his lane
        lane += 0.62 * smooth(prog(s, S_HIT - 0.55, S_HIT)) * (1 - smooth(prog(s, S_HIT + 0.2, S_HIT + 1.0)))
    return lane


def position(s):
    me = xat("YOU", s)
    return 1 + sum(1 for nm in ORDER if nm != "YOU" and xat(nm, s) > me + 1)


# ---------------------------------------------------------------- the camera
LANE_GAP = 92


def cam(s):
    """(camx, camy, zoom) in world units"""
    hx = xat("YOU", s)
    keys = [(0, 1.15), (S_BANG, 1.15), (2.0, 0.95), (6.5, 1.05), (S_HIT - 0.8, 1.55), (S_HIT, 1.75), (S_GROUND, 1.9),
            (S_GROUND + 0.6, 1.35), (S_UP0, 1.6), (S_UP1, 2.0), (S_LIMP1, 1.5), (S_RUN + 0.6, 1.05), (S_FIN - 3, 1.15),
            (S_FIN - 0.6, 1.6), (S_FIN, 1.9), (S_FIN + 1.2, 1.45), (S_END, 1.6)]
    ks = np.array(keys)
    z = float(np.interp(s, ks[:, 0], ks[:, 1]))
    lead = 120 * clamp(vat("YOU", s) / 1000)          # look ahead of the runner
    # gently smoothed follow
    xs = [xat("YOU", s - k * 0.05) for k in range(8)]
    cx = sum(xs) / len(xs) + lead
    cy = 4 * LANE_GAP - 170 - 40 * (z - 1)
    k = smooth(prog(s, S_LAUGH0 - 0.15, S_LAUGH0)) * (1 - smooth(prog(s, S_LAUGH1, S_LAUGH1 + 0.25)))
    if k > 0:
        cx, cy, z = lerp(cx, hx, k), lerp(cy, 1.4 * LANE_GAP - 120, k), lerp(z, 1.25, k)
    return cx, cy, z


def to_screen(x, y, c):
    cx, cy, z = c
    return 540 + (x - cx) * z, 1180 + (y - cy) * z


# ---------------------------------------------------------------- poses
def run_pose(nm, s, hipx, gy, sc):
    dist = xat(nm, s)
    ph = (dist / STRIDE) % 1.0
    ct = RUN_A + ph * RUN_P
    return clip(RUN).pts(ct, x0=0, floor=gy, scale=sc, x_lock=hipx)


def static(pose, hipx, gy, sc, low=113):
    return place(pose, (hipx, gy - low * sc), 1, sc)


def blendp(a, b, k):
    if k <= 0:
        return a
    if k >= 1:
        return b
    return {j: (lerp(a[j][0], b[j][0], k), lerp(a[j][1], b[j][1], k)) for j in a}


def pose_of(nm, s, hipx, gy, sc):
    if s < S_BANG:
        return static(SET, hipx, gy, sc, 96)
    runp = run_pose(nm, s, hipx, gy, sc)
    p = blendp(static(SET, hipx, gy, sc, 96), runp, smooth(prog(s, S_BANG, S_BANG + 0.35)))
    if nm == "MOTIVATION":
        pass
    if nm == "EGO" and s > S_FIN + 1.2:
        p = blendp(p, static(KNEES, hipx, gy, sc, 108), smooth(prog(s, S_FIN + 1.2, S_FIN + 2.2)))
    if nm == "YOU":
        if s >= S_HIT - 0.05:          # a real trip: he stumbles, pitches forward, hands out...
            T1 = S_HIT + 0.5
            u = clamp((s - (S_HIT - 0.05)) / (T1 - S_HIT + 0.05))
            trip = clip(TRIP).pts(lerp(0.62, 1.18, u), x0=0, floor=gy, scale=sc, x_lock=hipx)
            p = blendp(p, trip, smooth(prog(s, S_HIT - 0.05, S_HIT + 0.08)))
            if s >= T1 - 0.08:         # ...and hits the track
                u2 = clamp((s - T1) / (S_GROUND - T1))
                dive = clip(DIVE).pts(lerp(3.3, 3.95, u2), x0=0, floor=gy, scale=sc, x_lock=hipx, facing=-1)
                p = blendp(p, dive, smooth(prog(s, T1 - 0.08, T1 + 0.08)))
        if s >= S_UP0 - 0.1:
            u = clamp((s - S_UP0) / (S_UP1 - S_UP0))
            up = clip(GETUP).pts(lerp(1.7, 4.6, u), x0=0, floor=gy, scale=sc, x_lock=hipx, facing=GETUP_F)
            p = blendp(p, up, smooth(prog(s, S_UP0 - 0.1, S_UP0 + 0.15)))
        if s >= S_UP1 - 0.1:
            u = s - S_UP1
            lp = clip(LIMP).pts(6.6 + (u * 1.1) % 3.2, x0=0, floor=gy, scale=sc, x_lock=hipx, facing=LIMP_F)
            p = blendp(p, lp, smooth(prog(s, S_UP1 - 0.1, S_UP1 + 0.15)))
        if s >= S_LIMP1:
            p = blendp(p, runp, smooth(prog(s, S_LIMP1, S_RUN)))
        if s >= S_FIN + 2.2:
            p = blendp(p, static(VICTORY, hipx, gy, sc), smooth(prog(s, S_FIN + 2.2, S_FIN + 2.8)))
        if S_HIT + 0.3 <= s < S_LIMP1:      # the dive was onto a mat: put his body on the track
            low = max(y for _, y in p.values()) + 9 * sc / S
            k = smooth(prog(s, S_HIT + 0.3, S_GROUND)) * (1 - smooth(prog(s, S_UP1 - 0.3, S_UP1 + 0.2)))
            p = {j: (x, y + (gy - low) * k) for j, (x, y) in p.items()}
    return p


GETUP_F = -1
LIMP_F = 1

# ---------------------------------------------------------------- the stadium
_B = {}


def crowd_strip():
    if "crowd" not in _B:
        w, h = 2600, 420
        im = Image.new("RGBA", (w * K, h * K), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        rng = np.random.default_rng(3)
        for row in range(9):
            y = 60 + row * 40
            d.rectangle((0, (y + 14) * K, w * K, (y + 40) * K), (22 + row * 2, 24 + row * 2, 32 + row * 2, 255))
            for x in np.arange(0, w, 24):
                sh = int(30 + row * 5 + rng.uniform(-8, 10))
                xx = x + rng.uniform(-6, 6) + (12 if row % 2 else 0)
                ell(d, xx, y, 9, 10, (sh, sh, sh + 8, 255))
                if rng.uniform() < 0.05:
                    ell(d, xx, y - 4, 3, 3, (255, 250, 230, 255))   # phone flash
        _B["crowd"] = im
    return _B["crowd"]


def stadium(st, d, s, c):
    cx, cy, z = c
    # sky
    a = np.zeros((H * K // 4, W * K // 4, 3), np.float32)
    k = np.linspace(0, 1, a.shape[0])[:, None, None]
    a[:] = np.array([6, 8, 16], np.float32) * (1 - k) + np.array([18, 22, 38], np.float32) * k
    st.alpha_composite(Image.fromarray(a.astype(np.uint8)).convert("RGBA").resize(st.size, Image.BILINEAR))
    top = to_screen(0, -70, c)[1]                       # far edge of the track
    # floodlights (far, slow parallax)
    for i in range(-2, 4):
        wx = i * 900 - (cx * 0.15) % 900
        sx = 540 + (wx - 0) * 0.6
        line(d, [(sx, top - 260), (sx, top - 760)], (40, 42, 52, 255), 8)
        rrect(d, (sx - 60, top - 820, sx + 60, top - 760), 6, (220, 230, 255, 255))
        g = Image.new("RGBA", st.size, (0, 0, 0, 0))
        ImageDraw.Draw(g).ellipse(((sx - 200) * K, (top - 950) * K, (sx + 200) * K, (top - 630) * K), (200, 220, 255, 60))
        st.alpha_composite(g.filter(ImageFilter.GaussianBlur(40 * K)))
    # stands with the crowd (parallax)
    cs = crowd_strip()
    sc = 0.85 + 0.2 * (z - 1)
    strip = cs.resize((int(cs.size[0] * sc), int(cs.size[1] * sc)), Image.BILINEAR)
    off = int(((cx * 0.45 * z) % (2600 * sc)) * K)
    y0 = int((top - 420 * sc) * K)
    for k_ in range(-1, 3):
        st.alpha_composite(strip, (k_ * strip.size[0] - off, y0)) if 0 <= y0 < st.size[1] else None
    # the wall + the track
    poly(d, [(0, top - 26), (W, top - 26), (W, top), (0, top)], (36, 60, 120, 255))
    poly(d, [(0, top), (W, top), (W, H), (0, H)], (170, 72, 56, 255))
    for j in range(6):   # lane lines
        y = to_screen(0, j * LANE_GAP - 36, c)[1]
        line(d, [(0, y), (W, y)], (240, 236, 230, 220), max(2, 3 * z))
    # distance markers + lane numbers (moving with the track)
    base = to_screen(0, 5 * LANE_GAP + 10, c)[1]
    m0 = int((cx - 700 / z) // 400) * 400
    for wx in range(m0, int(cx + 700 / z) + 400, 400):
        sx = to_screen(wx, 0, c)[0]
        line(d, [(sx, top + 4), (sx, base)], (240, 236, 230, 70), 2)
        rrect(d, (sx - 3, base - 30, sx + 3, base), 2, (240, 236, 230, 200))
    # finish line
    fx = to_screen(X_F, 0, c)[0]
    if -100 < fx < W + 100:
        for j in range(12):
            y0_ = top + (base - top) * j / 12
            y1_ = top + (base - top) * (j + 1) / 12
            for m in range(2):
                col = (245, 245, 245, 255) if (j + m) % 2 == 0 else (20, 20, 24, 255)
                poly(d, [(fx + m * 10 * z, y0_), (fx + (m + 1) * 10 * z, y0_), (fx + (m + 1) * 10 * z, y1_), (fx + m * 10 * z, y1_)], col)
        line(d, [(fx, top), (fx, top - 220 * z)], (230, 230, 236, 255), 6)
        rrect(d, (fx - 60 * z, top - 300 * z, fx + 60 * z, top - 220 * z), 6, (20, 20, 24, 255))
        PW.spaced(d, fx * K, (top - 260 * z) * K, "FINISH", font("InterDisplay-Bold.otf", int(26 * z * K)), (245, 245, 245, 255), 3)
    return top


def runner(st, d, nm, s, c, show_label=True):
    lane = lane_of(nm, s)
    x = xat(nm, s)
    hx, gy = to_screen(x, lane * LANE_GAP, c)
    z = c[2]
    sc = S * z * (0.84 + 0.05 * lane)
    if hx < -200 or hx > W + 200:
        return None
    ell(d, hx, gy + 4, 60 * sc / S, 10 * sc / S, (0, 0, 0, 90))
    p = pose_of(nm, s, hx, gy, sc)
    if nm == "YOU":
        hurt = s > S_GROUND - 0.2
        exp = "determined"
        if S_HIT <= s < S_GROUND + 0.4:
            exp = "shocked"
        elif S_GROUND + 0.4 <= s < S_UP1:
            exp = "cry"
        elif s > S_FIN + 0.4:
            exp = "happy"
        figure(st, p, sc, light=(0.4, -0.9))
        dh = ImageDraw.Draw(st)
        face(dh, p, exp, 1, s)
        nx, ny = p["neck"]
        ell(dh, nx, ny + 2, 21 * sc, 11 * sc, (214, 44, 44, 255))
        poly(dh, [(nx, ny), (nx - 44 * sc, ny + 26 * sc), (nx - 30 * sc, ny + 40 * sc)], (214, 44, 44, 255))
        if hurt:   # scraped knee + elbow
            kx, ky = p["kl"]
            line(d, [(kx - 6 * z, ky - 4 * z), (kx + 6 * z, ky + 6 * z)], (200, 40, 40, 255), 5 * z)
            ex, ey = p["er"]
            line(d, [(ex - 5 * z, ey), (ex + 5 * z, ey + 4 * z)], (200, 40, 40, 255), 4 * z)
        headband(d, p, (214, 44, 44))
    else:
        col = RUNNERS[nm][1]
        figure(st, p, sc, light=(0.4, -0.9))
        dd = ImageDraw.Draw(st)
        outfit(dd, p, col, 1, legs=False)
        exp = "smug" if nm in ("EGO", "TALENT") else "determined"
        if nm == "MOTIVATION" and s > 5.0:
            exp = "tired"
        if nm == "TALENT" and s > 19:
            exp = "tired"
        if nm == "EGO" and s > S_FIN - 2.2:
            exp = "nervous" if s < S_FIN else "shocked"
        if nm == "EGO" and S_HIT - 0.3 < s < S_HIT + 2.5:
            exp = "smug"
        face(dd, p, exp, 1, s)
        if nm == "EGO":
            hx_, hy_ = p["head"]
            rrect(dd, (hx_ - 4, hy_ - 10, hx_ + 30, hy_ + 2), 4, (12, 12, 16, 255))
    return p


def headband(d, p, col):
    hx, hy = p["head"]
    nx, ny = p["neck"]
    a = math.atan2(hy - ny, hx - nx) + math.pi / 2
    r = math.hypot(hx - nx, hy - ny) * 0.72
    c_, s_ = math.cos(a), math.sin(a)
    cx_, cy_ = hx + (hx - nx) * 0.05, hy + (hy - ny) * 0.05
    line(d, [(cx_ - r * c_, cy_ - r * s_), (cx_ + r * c_, cy_ + r * s_)], col + (255,), 8)


# ---------------------------------------------------------------- the people laughing at him
LAUGHERS = [(-430, "079/79_70", 1.0, 5.6, -1), (-250, "014/014_18".replace("014_", "14_"), 1.8, 4.4, 1),
            (-60, "014/14_17", 1.5, 4.6, -1), (140, "013/13_14", 9.8, 13.6, 1), (330, "079/79_70", 2.4, 5.8, -1),
            (520, "014/14_18", 7.0, 10.6, 1)]


def laughers(st, d, s, c):
    out = []
    if not (S_LAUGH0 - 0.2 <= s < S_LAUGH1 + 0.3):
        return out
    hx = xat("YOU", s)
    for i, (dx, nm, a, b, f) in enumerate(LAUGHERS):
        x, gy = to_screen(hx + dx, -40, c)
        sc = S * c[2] * 0.8
        ct = a + ((s - S_LAUGH0) * 1.0 + i * 0.37) % (b - a)
        p = clip(nm).pts(ct, x0=0, floor=gy, scale=sc, x_lock=x, facing=f)
        ell(d, x, gy + 3, 50 * sc / S, 8 * sc / S, (0, 0, 0, 80))
        figure(st, p, sc, light=(0.4, -0.9), body=(200, 204, 216))
        face(ImageDraw.Draw(st), p, "laugh", f, s)
        out.append((p, i))
    return out


def laugh_text(dd, s, people):
    for p, i in people:
        hx, hy = p["head"]
        bob = 10 * math.sin(s * 14 + i * 1.7)
        a = smooth(prog(s, S_LAUGH0 + 0.1 * i, S_LAUGH0 + 0.1 * i + 0.15)) * (1 - smooth(prog(s, S_LAUGH1 - 0.15, S_LAUGH1)))
        PW.spaced(dd, hx + 10 * math.sin(i * 2.3), hy - 90 + bob, "HAHAHA", font("InterDisplay-Bold.otf", 34 + 4 * (i % 2)),
                  (255, 255, 255, int(255 * a)), 2)


# ---------------------------------------------------------------- time
HOOK = 1.4


def rate(s):
    r = 1.0
    r = min(r, lerp(1.0, 0.33, smooth(prog(s, S_HIT - 0.3, S_HIT))) if s < S_GROUND + 0.3 else 1.0)
    if s >= S_GROUND + 0.3:
        r = lerp(0.33, 1.0, smooth(prog(s, S_GROUND + 0.3, S_GROUND + 0.8)))
    if S_FIN - 0.5 <= s <= S_FIN + 0.6:
        r = min(r, lerp(1.0, 0.28, smooth(prog(s, S_FIN - 0.5, S_FIN - 0.15))) if s < S_FIN + 0.2 else lerp(0.28, 1.0, smooth(prog(s, S_FIN + 0.2, S_FIN + 0.6))))
    return r


_V = [0.0]
_S = [0.0]
while _S[-1] < S_END:
    _S.append(_S[-1] + rate(_S[-1]) / 240)
    _V.append(_V[-1] + 1 / 240)
DUR = HOOK + _V[-1]
NF = int(round(DUR * FPS))


def story(t):
    if t < HOOK:
        return S_HIT + 0.28 + 0.07 * t
    return float(np.interp(t - HOOK, _V, _S))


def video_of(s):
    return HOOK + float(np.interp(s, _S, _V))


# ---------------------------------------------------------------- frame
def frame(t):
    s = story(t)
    c = cam(s)
    if t < HOOK:
        c = (c[0], c[1], 1.9)
    st = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(st)
    stadium(st, d, s, c)
    laughers_ = laughers(st, d, s, c)
    pts = {}
    for nm in ORDER:
        pts[nm] = runner(st, d, nm, s, c)
    # finish tape
    fx = to_screen(X_F, 0, c)[0]
    if -100 < fx < W + 100:
        y = to_screen(0, 4 * LANE_GAP, c)[1] - 130 * c[2]
        if s < S_FIN:
            line(d, [(fx, y - 200 * c[2]), (fx, y + 400 * c[2])], (230, 50, 50, 230), 4)
    im = st.resize((W, H), Image.LANCZOS)
    # spotlight vignette
    a = np.asarray(im.convert("RGB"), np.float32)
    a *= VIG
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    dd = ImageDraw.Draw(im)
    # labels above heads
    for nm, p in pts.items():
        if p is None or t < HOOK and nm not in ("YOU", "EGO"):
            continue
        hx, hy = p["head"]
        col = (246, 200, 90) if nm == "YOU" else (220, 224, 236)
        PW.spaced(dd, hx, hy - 70 * c[2] * 0.9, "DISCIPLINE" if nm == "YOU" else nm, font("Inter-SemiBold.otf", int(16 + 6 * c[2])), col + (255,), 4)
    # header: position
    if t >= HOOK and s >= 1.0:
        pos = position(s)
        gold = pos == 1 and s >= S_FIN
        PW.spaced(dd, W / 2, 60, "POSITION", font("Inter-SemiBold.otf", 26), (200, 206, 224, 255), 6)
        PW.spaced(dd, W / 2, 96, f"{pos}/5", font("InterDisplay-Bold.otf", 120), (GOLD if gold else (246, 246, 250)) + (255,), 4)
    if t < HOOK:
        im = Image.blend(im.convert("RGB"), Image.new("RGB", (W, H), (0, 0, 0)), 0.3).convert("RGBA")
        k = hq.pop(t, 0.3, 0.2) if t >= 0.3 else 0
        if k > 0:
            text(im, W / 2, 300, "EVERYONE", int(110 * max(0.3, k)))
            text(im, W / 2, 300 + int(124 * max(0.3, k)), "PASSED HIM.", int(110 * max(0.3, k)), col=GOLD)
    if S_GROUND + 0.4 <= s < S_LAUGH0 + 0.1:
        a_ = smooth(prog(s, S_GROUND + 0.4, S_GROUND + 0.6)) * (1 - smooth(prog(s, S_LAUGH0 - 0.1, S_LAUGH0 + 0.1)))
        text(im, W / 2, 330, "EVERYONE PASSED HIM.", 66, a=a_)
    if S_LAUGH0 <= s < S_LAUGH1:
        laugh_text(dd, s, laughers_)
    if S_UP1 - 0.3 <= s < S_LIMP1 + 0.4:
        a_ = smooth(prog(s, S_UP1 - 0.3, S_UP1)) * (1 - smooth(prog(s, S_LIMP1, S_LIMP1 + 0.4)))
        text(im, W / 2, 330, "BUT HE GOT UP.", 76, col=GOLD, a=a_)
    for j, (line_, col) in enumerate((("FALLING IS PART", (246, 240, 226)), ("OF THE RACE.", (246, 240, 226)), ("STAYING DOWN ISN'T.", GOLD))):
        t0 = S_FIN + 1.0 + (0 if j < 2 else 1.0)
        a_ = smooth(prog(s, t0, t0 + 0.4))
        if a_ > 0:
            text(im, W / 2, 300 + j * 88 + (30 if j == 2 else 0), line_, 72, col=col, a=a_)
    if abs(t - HOOK) < 0.12:
        im = whip(im, 1 - abs(t - HOOK) / 0.12)
    if S_HIT <= s < S_HIT + 0.25 or S_FIN - 0.05 <= s < S_FIN + 0.15:
        k = 1 - (s - (S_HIT if s < S_FIN - 1 else S_FIN - 0.05)) / 0.25
        im.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, int(70 * clamp(k)))))
    return np.asarray(im.convert("RGB"))


_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (0.35 + 0.75 * np.exp(-(((_xx - 540) / 700) ** 2 + ((_yy - 1050) / 1100) ** 2)))[..., None]


def render(i):
    acc = None
    for k in range(2):
        f = frame((i + k / 4) / FPS).astype(np.float32)
        acc = f if acc is None else acc + f
    return (acc / 2).astype(np.uint8).tobytes()


MUSIC = "Rynos Theme.mp3"
HIT = 30.0


def audio():
    n = int(DUR * SR)
    out = np.zeros((n, 2))
    t_fin = video_of(S_FIN)
    put(out, track(MUSIC, max(0.0, HIT - t_fin), DUR), 0.0, 1.6, fin=0.05, fout=1.0)
    tt = np.arange(n) / SR
    crowd = noise(DUR, 2, lo=250, hi=3000)[:n]
    crowd = np.pad(crowd, (0, n - len(crowd)))
    lvl = 0.06 + 0.14 * np.clip((tt - t_fin) / 0.4, 0, 1) * np.clip((DUR - tt) / 2, 0, 1)
    out += (crowd * lvl)[:, None]
    mix_in(out, noise(0.3, 7, lo=200, hi=6000)[:int(0.3 * SR)] * env(int(0.3 * SR), 0.001, 0.25), video_of(S_BANG), 0.9, 0.0)  # gun
    mix_in(out, tone(60, 0.5, (1, 2), a=0.001, d=0.4), video_of(S_BANG), 0.5, 0.0)
    for s_, g in ((S_HIT, 0.6), (S_GROUND - 0.35, 0.9)):
        mix_in(out, noise(0.3, 9, lo=40, hi=900)[:int(0.3 * SR)] * env(int(0.3 * SR), 0.002, 0.25), video_of(s_), g, 0.0)
    mix_in(out, tone(50, 0.8, (1, 2), a=0.002, d=0.7), video_of(S_GROUND - 0.35), 0.6, 0.0)
    gasp = noise(1.2, 4, lo=300, hi=2500)[:int(1.2 * SR)] * env(int(1.2 * SR), 0.05, 0.9)
    mix_in(out, gasp, video_of(S_HIT + 0.1), 0.4, 0.0)
    mix_in(out, noise(0.35, 9, lo=500, hi=7000)[:int(0.35 * SR)] * env(int(0.35 * SR), 0.25, 0.05), HOOK - 0.3, 0.2, 0.0)
    out *= np.clip((DUR - tt) / 0.7, 0.0, 1)[:, None]
    out /= max(1.0, np.abs(out).max() / 0.9)
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(here, "track"), exist_ok=True)
    if "--stills" in sys.argv:
        ss = [0.2, 0.4, 2.5, 5.5, 8.0, 8.6, 9.2, 10.2, 11.5, 12.8, 15.5, 18.5, 21.5, 23.8, 24.6, 26.5]
        ts = [float(a) for a in sys.argv[2:]] or [0.8] + [video_of(x) for x in ss[2:]]
        cols = 8
        rows = math.ceil(len(ts) / cols)
        sheet = Image.new("RGB", (200 * cols, 356 * rows))
        for j, t in enumerate(ts):
            sheet.paste(Image.fromarray(frame(t)).resize((200, 356), Image.LANCZOS), ((j % cols) * 200, (j // cols) * 356))
        p = os.path.join(here, "track", "stills.png")
        sheet.save(p)
        print(p, round(DUR, 1), "pos@", [position(x) for x in (3, 7, 8.3, 12, 16, 20, 23, S_FIN + 0.1)])
        return
    out = sys.argv[1]
    wav = out + ".wav"
    write_wav(wav, audio())
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                          "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-13:TP=-1.5:LRA=11", "-ar", "44100",
                          "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                         stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for b in pool.imap(render, range(NF), chunksize=2):
            p.stdin.write(b)
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print(out)
    print(f'Credit: Music: "{MUSIC[:-4]}" by Kevin MacLeod (incompetech.com), CC BY 4.0')


if __name__ == "__main__":
    main()
