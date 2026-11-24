#!/usr/bin/env python3
"""THE ROPE - "The rope can only hold one." 20 s, a cliff at night, licensed music, loops.

Frame 0: a close-up of a rope fraying over a rock lip, strands snapping; the camera slides down it: the red-scarf hero
hangs on it, below him a stranger in a yellow helmet. ROPE 62% and falling. The stranger looks up and points at the
knife on the hero's belt (cut it, save yourself). The hero takes the knife; the blade goes to the rope between them,
back, forward again, trembling. He throws the knife into the dark. He reaches down, grabs the stranger's wrist, and
they climb; strands snap, a hand slips; he drags himself over the edge and hauls the stranger up - the rope snaps
(0%) the moment the stranger's feet leave it. They lie on the ledge, breathing. HE COULD HAVE CUT IT. / HE CHOSE NOT TO.

Music: "Immersed" then "Eternal Hope" by Kevin MacLeod (incompetech.com), CC BY 4.0 - the swell lands on the rescue.

    python3 stick/rope.py stick/rope.mp4
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
from compare import ell, line, rrect, poly, figure, place, ik, K, W, H, INK, BODY  # noqa
from perfect_wave import clamp, env, font, lerp, lerp_pose, mix_in, noise, prog, smooth, tone, write_wav  # noqa

FPS = 30
SR = 44100
DUR = 21.0
NF = int(round(DUR * FPS))
SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
MDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "study", "music")
STAND = PW.STAND
LIP = (520, 640)              # where the rope goes over the rock edge (the fraying point)
LEDGE_Y = 628
YELLOW = (240, 196, 40)
T_ROCK, T_HIT = 2.3, 3.05         # a rock falls and hits the stranger's helmet
T_POINT0, T_POINT1 = 4.0, 5.3
T_KNIFE = 5.6
T_PITON = 6.4                      # the anchor starts pulling out of the rock
T_THROW = 8.6
T_GRAB = 9.3
T_BOLT = 10.0                      # lightning, then rain
T_SSLIP = 10.7                     # the stranger's other hand slips off: he hangs only from the hero's hand
T_GUST, T_WALL = 11.9, 12.4        # a gust slams them into the rock
T_CLIMB = 12.9
T_SLIP = 14.6                      # the edge crumbles under his hand
T_TOP = 15.2
T_SNAP = 17.0
T_LINES = 18.0


def rope_pct(t):
    keys = [(0, 62), (T_HIT - 0.01, 58), (T_HIT + 0.1, 50), (T_THROW, 38), (T_SSLIP, 31), (T_SSLIP + 0.1, 24),
            (T_WALL, 20), (T_WALL + 0.1, 13), (T_SLIP, 9), (T_SLIP + 0.1, 5), (T_SNAP, 0)]
    if t >= T_SNAP:
        return 0.0
    for (a, va), (b, vb) in zip(keys, keys[1:]):
        if a <= t < b:
            return lerp(va, vb, (t - a) / (b - a))
    return 0.0


def sway(t):
    return 1.0 * math.sin(t * 1.3) + 0.4 * math.sin(t * 3.1)


def gust(t):
    return smooth(prog(t, T_GUST, T_WALL)) * (1 - smooth(prog(t, T_WALL + 0.25, T_WALL + 1.1)))


def rope_x(y, t):
    return LIP[0] + 40 + sway(t) * (y - LIP[1]) * 0.03 - 150 * gust(t) * (y - LIP[1]) / 700


# ---------------------------------------------------------------- background (built once per worker)
BG = None


def build_bg():
    w2, h2 = W * K, H * K
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    sky = np.array((5, 7, 14), np.float32) * (1 - yy) + np.array((16, 22, 40), np.float32) * yy
    a = np.repeat(sky, W, axis=1)
    yg, xg = np.mgrid[0:H, 0:W].astype(np.float32)
    moon = np.exp(-(((xg - 820) ** 2 + (yg - 330) ** 2) / (260 ** 2)))
    a += moon[..., None] * np.array((60, 70, 100), np.float32)
    mist = np.clip((yg - 1300) / 600, 0, 1) ** 1.5
    a += mist[..., None] * np.array((40, 46, 60), np.float32)
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB").resize((w2, h2), Image.BICUBIC).convert("RGBA")
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(2)
    for _ in range(260):
        x, y = rng.uniform(0, W), rng.uniform(0, 1100)
        r = rng.uniform(0.6, 1.8)
        ell(d, x, y, r, r, (220, 228, 255, int(rng.uniform(50, 210))))
    ell(d, 820, 330, 58, 58, (236, 232, 214, 255))
    for cx, cy, r in ((-16, -12, 12), (14, 10, 9), (-6, 22, 7)):
        ell(d, 820 + cx, 330 + cy, r, r, (214, 208, 188, 255))
    # far mountains in the mist
    for k2, (base, col) in enumerate(((1480, (26, 32, 48)), (1620, (34, 40, 56)))):
        pts = [(0, H)]
        for x in range(0, W + 60, 60):
            pts.append((x, base - 120 * abs(math.sin(x * 0.006 + k2 * 2)) - 40 * math.sin(x * 0.02 + k2)))
        pts.append((W, H))
        poly(d, pts, col + (255,))
    # the cliff: a rock wall on the left with a ledge on top
    wall = [(-10, LEDGE_Y)]
    for y in range(LEDGE_Y, H + 40, 40):
        wall.append((LIP[0] - 20 - 70 * ((y - LEDGE_Y) / H) + 18 * math.sin(y * 0.03), y))
    wall += [(-10, H + 40)]
    poly(d, wall, (26, 27, 34, 255))
    edge = wall[1:-1]
    d.line([P2(x, y) for x, y in edge], fill=(120, 130, 160, 255), width=int(4 * K))
    for _ in range(70):
        x, y = rng.uniform(0, 420), rng.uniform(LEDGE_Y + 30, H)
        L = rng.uniform(20, 80)
        line(d, [(x, y), (x + rng.uniform(-20, 20), y + L)], (44, 46, 56, 255), 2)
    rrect(d, (-20, LEDGE_Y - 8, LIP[0] + 8, LEDGE_Y + 24), 8, (40, 42, 52, 255))
    line(d, [(-20, LEDGE_Y - 6), (LIP[0] + 4, LEDGE_Y - 6)], (150, 160, 190, 255), 4)
    for j in range(40):
        x = rng.uniform(0, LIP[0] - 10)
        for dx in (-4, 0, 4):
            line(d, [(x, LEDGE_Y - 6), (x + dx * 1.5, LEDGE_Y - 18)], (60, 80, 70, 255), 2)
    # the anchor (a piton) the rope is tied to
    return im


def P2(x, y):
    return (x * K, y * K)


# ---------------------------------------------------------------- the rope
def draw_rope(d, t, y_bottom, snapped=False):
    """from the piton over the lip and down; the fray point at the lip"""
    pct = rope_pct(t)
    col = (190, 150, 90)
    line(d, [(LIP[0] - 60, LEDGE_Y - 16), (LIP[0], LIP[1] - 10)], col + (255,), 9)
    if snapped:
        u = t - T_SNAP
        top = LIP[1] + 6
        stub = [(LIP[0] + 4, LIP[1] - 6), (LIP[0] + 14 + 10 * math.sin(t * 8), LIP[1] + 30)]
        line(d, stub, col + (255,), 8)
        # the rest falls into the dark
        fy = LIP[1] + 60 + 900 * u * u
        line(d, [(rope_x(fy, t) + 10 * u, fy), (rope_x(fy + 700, t) + 40 * u, fy + 700)], col + (int(255 * max(0, 1 - u)),),
             8)
        return
    xs = [(rope_x(y, t), y) for y in np.linspace(LIP[1], y_bottom, 30)]
    line(d, [(LIP[0], LIP[1] - 10)] + xs, col + (255,), 9)
    for j in range(0, 30, 2):
        x, y = xs[j]
        line(d, [(x - 4, y - 6), (x + 4, y + 6)], (150, 112, 60, 255), 2)
    # the fray just below the lip: thinner, loose strands
    fx, fy = rope_x(LIP[1] + 22, t), LIP[1] + 22
    th = 2 + 7 * pct / 62
    line(d, [(fx, fy - 18), (fx, fy + 18)], (26, 27, 34, 255), 11)
    line(d, [(fx, fy - 18), (fx, fy + 18)], col + (255,), th)
    rng = np.random.default_rng(1)
    n = int(14 * (1 - pct / 100) + 6)
    for j in range(n):
        a = rng.uniform(-2.6, 2.6)
        L = rng.uniform(8, 20)
        yy = fy + rng.uniform(-14, 14)
        line(d, [(fx, yy), (fx + L * math.sin(a) + 2 * math.sin(t * 9 + j), yy - L * math.cos(a) * 0.4)],
             (220, 186, 120, 255), 1.5)


SNAPS = [0.5, 1.3, 2.0, 3.1, 4.6, 6.6, 7.5, 10.8, 12.45, 13.6, 14.65, 16.0, 16.6]


def fibers(d, t):
    for s0 in SNAPS:
        if s0 <= t < s0 + 0.6:
            u = (t - s0) / 0.6
            rng = np.random.default_rng(int(s0 * 10))
            for j in range(8):
                vx, vy = rng.uniform(-90, 90), rng.uniform(-80, 20)
                x = rope_x(LIP[1] + 22, t) + vx * u
                y = LIP[1] + 22 + vy * u + 120 * u * u
                line(d, [(x, y), (x + 6, y + 2)], (230, 196, 130, int(255 * (1 - u))), 1.5)


# ---------------------------------------------------------------- people
HANG = {"head": (10, -146), "neck": (4, -106), "el": (-34, -160), "hl": (-4, -214), "er": (34, -184), "hr": (2, -246),
        "kl": (10, 52), "fl": (2, 110), "kr": (-8, 54), "fr": (-16, 108)}


def hanging(hand_y, t, s, ph=0.0, dx=0.0):
    """hip position for a figure hanging from the rope with its top hand at hand_y"""
    hx = rope_x(hand_y, t) + dx
    hip = (hx - 2 * s, hand_y + 246 * s)
    p = dict(HANG)
    sw = 6 * math.sin(t * 1.7 + ph)
    p["fl"] = (p["fl"][0] + sw, p["fl"][1])
    p["fr"] = (p["fr"][0] - sw, p["fr"][1])
    return p, hip


def helmet(d, head, s):
    hx, hy = head
    d.chord([(hx - 30 * s) * K, (hy - 36 * s) * K, (hx + 30 * s) * K, (hy + 14 * s) * K], 180, 360, fill=YELLOW + (255,),
            outline=INK + (255,), width=int(2 * K))
    rrect(d, (hx - 34 * s, hy - 14 * s, hx + 34 * s, hy - 7 * s), 3, (200, 160, 30, 255))
    ell(d, hx, hy - 26 * s, 5 * s, 4 * s, (255, 250, 200, 255))


def backpack(d, neck, hip, f, s):
    nx, ny = neck
    bx, by = hip
    cx, cy = (nx + bx) / 2 - f * 22 * s, (ny + by) / 2
    rrect(d, (cx - 18 * s, cy - 40 * s, cx + 18 * s, cy + 40 * s), 8, (60, 90, 140, 255), outline=INK + (255,), w=2)


def knife(d, p, ang, s, glint=0.0):
    x, y = p
    c, sn = math.cos(ang), math.sin(ang)
    blade = [(0, -3), (34, -3), (42, 0), (34, 3), (0, 3)]
    poly(d, [(x + (bx * c - by * sn) * s, y + (bx * sn + by * c) * s) for bx, by in blade], (210, 216, 230, 255),
         outline=INK + (255,), w=1.5)
    hl = [(-20, -4), (0, -4), (0, 4), (-20, 4)]
    poly(d, [(x + (bx * c - by * sn) * s, y + (bx * sn + by * c) * s) for bx, by in hl], (60, 40, 30, 255))
    if glint > 0:
        gx, gy = x + 30 * c * s, y + 30 * sn * s
        line(d, [(gx - 14, gy), (gx + 14, gy)], (255, 255, 255, int(255 * glint)), 2)
        line(d, [(gx, gy - 14), (gx, gy + 14)], (255, 255, 255, int(255 * glint)), 2)


def rock(d, x, y, r, ang):
    pts = []
    for j in range(7):
        a = ang + j * 2 * math.pi / 7
        rr = r * (0.75 + 0.25 * math.sin(j * 2.3))
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    poly(d, pts, (70, 72, 82, 255), outline=INK + (255,), w=2)
    line(d, [pts[0], pts[2]], (110, 114, 130, 255), 2)


def crack(d, head, s, t):
    if t < T_HIT:
        return
    hx, hy = head
    line(d, [(hx - 4 * s, hy - 34 * s), (hx + 4 * s, hy - 24 * s), (hx - 2 * s, hy - 16 * s), (hx + 8 * s, hy - 9 * s)],
         INK + (255,), 2)


def piton(d, t):
    """the anchor the rope is tied to: pulling out of the rock, and ripping free at the snap"""
    out = 0.0
    for t0, t1, amt in ((T_PITON, T_PITON + 1.2, 0.25), (T_WALL, T_WALL + 0.3, 0.2), (T_SLIP, T_SLIP + 0.3, 0.2),
                        (T_SNAP - 0.8, T_SNAP, 0.2)):
        out += amt * smooth(prog(t, t0, t1))
    bx, by = LIP[0] - 60, LEDGE_Y - 10
    if t >= T_SNAP:
        u = t - T_SNAP
        bx, by = bx + 300 * u, by - 200 * u + 900 * u * u
        ang = u * 12
    else:
        ang = -0.5 * out + 0.06 * math.sin(t * 30) * (out > 0.05)
    L = 30 + 30 * out
    c, s_ = math.cos(ang - math.pi / 2), math.sin(ang - math.pi / 2)
    line(d, [(bx, by), (bx + L * c, by + L * s_)], (150, 154, 172, 255), 7)
    ell(d, bx + L * c, by + L * s_, 8, 8, None, outline=(150, 154, 172, 255), w=3)
    if 0.05 < out and t < T_SNAP:
        rng = np.random.default_rng(int(t * 8))
        for j in range(5):
            ell(d, bx + rng.uniform(-12, 12), by + rng.uniform(-6, 4), 2.5, 2.5, (150, 140, 120, 160))


def reach(pts, s, hand, target, sgn=1):
    side = hand[-1]
    pts = dict(pts)
    pts["h" + side] = target
    pts["e" + side] = ik(pts["neck"], target, 42 * s, 40 * s, sgn)
    return pts


SH, SS = 1.15, 1.1               # hero / stranger scale
LIE = dict(STAND, el=(-20, -80), hl=(-30, -40), er=(20, -80), hr=(30, -40))
SIT_G = {"head": (-16, -138), "neck": (-10, -96), "el": (-32, -52), "hl": (-52, -4), "er": (-26, -48), "hr": (-46, 0),
         "kl": (52, -38), "fl": (104, -2), "kr": (46, -32), "fr": (100, 2)}


def scene(stage, d, t):
    """everything that moves. returns the hero's / stranger's key points for the camera"""
    # where the two are on the rope
    jolt = 26 * math.exp(-(t - T_HIT) * 7) * (t >= T_HIT) + 30 * math.exp(-(t - T_SSLIP) * 7) * (t >= T_SSLIP)
    if t < T_CLIMB:
        h_hand = 780.0 + jolt * 0.4
        s_hand = lerp(1270.0, 1030.0, smooth(prog(t, T_THROW + 0.2, T_GRAB))) + jolt     # he climbs up to him
    elif t < T_TOP:
        u = prog(t, T_CLIMB, T_TOP)
        slip = 46 * math.exp(-(t - T_SLIP) * 6) * (t >= T_SLIP)
        h_hand = lerp(780, LIP[1] + 40, smooth(u)) + slip
        s_hand = h_hand + 250 + slip * 0.5
    else:
        h_hand = LIP[1] + 40
        s_hand = lerp(LIP[1] + 290, LIP[1] + 40, smooth(prog(t, T_TOP + 0.6, T_SNAP)))
    snapped = t >= T_SNAP
    bottom = s_hand + 300 if not snapped else LIP[1]
    # lightning in the sky
    for b0 in (T_BOLT, T_BOLT + 0.32):
        if b0 <= t < b0 + 0.18:
            rng = np.random.default_rng(int(b0 * 10))
            pts = [(760 + rng.uniform(-30, 30), 0)]
            while pts[-1][1] < 1450:
                x, y = pts[-1]
                pts.append((x + rng.uniform(-60, 60), y + rng.uniform(60, 130)))
            a = int(255 * (1 - (t - b0) / 0.18))
            line(d, pts, (220, 230, 255, a), 5)
            line(d, pts, (255, 255, 255, a), 2)
    piton(d, t)
    draw_rope(d, t, bottom, snapped)
    fibers(d, t)
    info = {}
    # --- the stranger
    if t < T_SNAP - 0.05:
        sp, shp = hanging(s_hand, t, SS, 1.0, dx=-40)
        if T_POINT0 <= t < T_POINT1 + 0.6:
            k = smooth(prog(t, T_POINT0, T_POINT0 + 0.5)) * (1 - smooth(prog(t, T_POINT1, T_POINT1 + 0.6)))
            sp = lerp_pose(sp, dict(sp, head=(14, -154), el=(30, -150), hl=(56, -196)), k)
        if T_GRAB - 0.6 <= t < T_TOP + 0.8:
            sp = dict(sp, el=(20, -160), hl=(10, -214), head=(8, -152))
        if T_SSLIP <= t < T_TOP + 0.6:
            fl_ = math.sin(t * 7)
            sp = dict(sp, er=(36, -110), hr=(60 + 14 * fl_, -80 - 10 * fl_))        # the other hand flails
        if T_HIT <= t < T_HIT + 0.6:
            k = 1 - (t - T_HIT) / 0.6
            sp = dict(sp, head=(sp["head"][0] - 18 * k, sp["head"][1] + 10 * k))
        if t >= T_TOP + 0.8:
            sp = dict(sp, el=(10, -170), hl=(4, -224), er=(18, -176), hr=(6, -232))
        spts = place(sp, shp, 1, SS)
        backpack(d, spts["neck"], spts["hip"], 1, SS)
        figure(stage, spts, SS, light=(0.7, -0.7), body=(176, 184, 200))
        helmet(d, spts["head"], SS)
        crack(d, spts["head"], SS, t)
        info["stranger"] = spts
    else:
        u = smooth(prog(t, T_SNAP - 0.05, T_SNAP + 0.5))
        lp = lerp_pose(dict(STAND, el=(10, -170), hl=(4, -224), er=(18, -176), hr=(6, -232)), LIE, u)
        hip = (lerp(LIP[0] - 10, 320, u), lerp(LIP[1] + 10, LEDGE_Y - 14, u))
        ang = lerp(0, math.pi / 2, u)
        spts = C.place(lp, hip, 1, SS) if u < 0.01 else __import__("ai_job").place(lp, hip, 1, SS, ang)
        backpack(d, spts["neck"], spts["hip"], 1, SS)
        figure(stage, spts, SS, light=(0.7, -0.7), body=(176, 184, 200))
        helmet(d, spts["head"], SS)
        if t > T_LINES + 0.6:
            # a weak thumbs up to the hero
            hx, hy = spts["hl"]
            line(d, [(hx, hy), (hx - 4, hy - 30)], BODY + (255,), 6)
        info["stranger"] = spts
    # --- the hero
    if t < T_TOP:
        hp, hhp = hanging(h_hand, t, SH, 0.0, dx=30)
        look = smooth(prog(t, 1.6, 2.2))
        duck = math.sin(math.pi * prog(t, T_ROCK + 0.05, T_ROCK + 0.5))
        hp = dict(hp, head=(lerp(6, 18, look) - 26 * duck, lerp(-150, -138, look) + 10 * duck))
        # take the knife, hesitate, throw it
        kp = None
        if T_KNIFE <= t < T_THROW + 0.25:
            k_take = smooth(prog(t, T_KNIFE, T_KNIFE + 0.5))
            # the blade goes towards the rope below his feet, back, forward again - trembling
            cyc = 0.5 - 0.5 * math.cos((t - T_KNIFE - 0.5) * 2 * math.pi / 1.3) if t > T_KNIFE + 0.5 else 0.0
            tr = 3 * math.sin(t * 40)
            kp = (lerp(40, 70, cyc), lerp(-20, 50, cyc) + tr)
            if t >= T_THROW:
                u = prog(t, T_THROW, T_THROW + 0.25)
                kp = (lerp(kp[0], 110, u), lerp(kp[1], -60, u))
            hp = dict(hp, el=(lerp(-14, 30, k_take), lerp(-156, -60, k_take)), hl=(kp[0] * k_take, kp[1] * k_take +
                                                                                 (1 - k_take) * -200))
        if T_GRAB - 0.6 <= t < T_TOP:
            hp = dict(hp, el=(26, -40), hl=(30, 40), head=(18, -134))
        hpts = place(hp, hhp, 1, SH)
        if T_GRAB - 0.6 <= t < T_TOP:
            hpts = reach(hpts, SH, "hl", info["stranger"]["hl"], 1)
        figure(stage, hpts, SH, light=(0.7, -0.7), scarf=True, back=-1)
        # the knife: on the belt, in his hand, or falling
        if t < T_KNIFE:
            knife(d, (hpts["hip"][0] + 16, hpts["hip"][1] - 6), 1.4, 0.8,
                  glint=max(0.0, 1 - abs(t - 3.9) / 0.4) if T_POINT0 < t < T_POINT1 else 0.0)
        elif t < T_THROW + 0.2:
            knife(d, hpts["hl"], 0.6 + 0.4 * math.sin(t * 2), 1.0, glint=0.6 if t > 6.0 else 0.0)
        info["hero"] = hpts
    else:
        # over the edge: kneeling on the ledge, hauling; then lying back
        if t < T_SNAP + 0.3:
            kneel = {"head": (40, -130), "neck": (30, -92), "el": (60, -40), "hl": (80, 10), "er": (54, -36),
                     "hr": (76, 14), "kl": (40, 6), "fl": (-10, 60), "kr": (-20, 54), "fr": (-70, 60)}
            u = smooth(prog(t, T_TOP, T_TOP + 0.7))
            hip = (lerp(LIP[0] - 10, LIP[0] - 110, u), lerp(LIP[1] + 120, LEDGE_Y - 62 * SH, u))
            hpts = place(kneel, hip, 1, SH)
            if "stranger" in info and t < T_SNAP:
                pull = 0.5 + 0.5 * math.sin(t * 9)
                rp = (rope_x(LIP[1] + 40, t) - 4, LIP[1] + 20 + 30 * pull)
                tgt = info["stranger"]["hl"]
                if t > T_SNAP - 0.6 and math.hypot(tgt[0] - hpts["neck"][0], tgt[1] - hpts["neck"][1]) < 90 * SH:
                    rp = tgt
                hpts = reach(hpts, SH, "hl", rp, 1)
                hpts = reach(hpts, SH, "hr", (rp[0] - 6, rp[1] - 16), 1)
        else:
            u = smooth(prog(t, T_SNAP + 0.3, T_SNAP + 1.0))
            sp = lerp_pose(SIT_G, SIT_G, 0)
            b = 4 * math.sin(t * 5)
            sp = dict(sp, head=(sp["head"][0], sp["head"][1] + b), neck=(sp["neck"][0], sp["neck"][1] + b * 0.6))
            hpts = place(sp, (lerp(LIP[0] - 110, 70, u), LEDGE_Y - 12 * SH), 1, SH)
        figure(stage, hpts, SH, light=(0.7, -0.7), scarf=True, back=-1)
        info["hero"] = hpts
    # the rock that hits the helmet
    if T_ROCK <= t < T_HIT + 1.6:
        u = t - T_ROCK
        hit_y = info["stranger"]["head"][1] - 30 if "stranger" in info else 1250
        g = 2 * (hit_y - (LIP[1] - 20)) / (T_HIT - T_ROCK) ** 2
        if t < T_HIT:
            rx, ry = rope_x(LIP[1], t) + 26, LIP[1] - 20 + 0.5 * g * u * u
        else:
            v = t - T_HIT
            rx, ry = rope_x(hit_y, t) + 26 + 260 * v, hit_y - 120 * v + 900 * v * v
        rock(d, rx, ry, 26, u * 4)
        if T_HIT <= t < T_HIT + 0.35:
            k = (t - T_HIT) / 0.35
            sx, sy = info["stranger"]["head"][0], info["stranger"]["head"][1] - 34
            rng = np.random.default_rng(3)
            for j in range(14):
                a = rng.uniform(0, 6.28)
                rr = 10 + 60 * k
                line(d, [(sx + rr * 0.6 * math.cos(a), sy + rr * 0.6 * math.sin(a)),
                         (sx + rr * math.cos(a), sy + rr * math.sin(a))], (255, 230, 150, int(255 * (1 - k))), 2)
    # the edge crumbles under his hand
    if T_SLIP <= t < T_SLIP + 1.4:
        v = t - T_SLIP
        rng = np.random.default_rng(14)
        for j in range(6):
            x0 = LIP[0] - rng.uniform(0, 40)
            rock(d, x0 + rng.uniform(-30, 60) * v, LIP[1] - 4 + 300 * v * v * rng.uniform(0.8, 1.4) + 30 * v,
                 rng.uniform(7, 14), v * rng.uniform(2, 6) + j)
    # rain after the lightning
    if t >= T_BOLT:
        a = smooth(prog(t, T_BOLT, T_BOLT + 0.8))
        rng = np.random.default_rng(21)
        for j in range(120):
            x0, sp = rng.uniform(-100, W + 100), rng.uniform(1.0, 1.4)
            y = ((t * sp * 1.6 + rng.uniform(0, 1)) % 1.0) * (H + 100) - 50
            x = x0 - 0.25 * y
            line(d, [(x, y), (x - 10, y + 40)], (160, 180, 220, int(130 * a)), 1.6)
    # the knife falling into the dark
    if T_THROW + 0.2 <= t < T_THROW + 2.5:
        u = t - T_THROW - 0.2
        kx = 640 + 160 * u
        ky = 1000 - 260 * u + 520 * u * u
        knife(d, (kx, ky), u * 9, 1.0, glint=0.5 + 0.5 * math.sin(u * 20))
    # wind streaks
    rng = np.random.default_rng(5)
    for j in range(16):
        x0, y0, sp = rng.uniform(0, W), rng.uniform(200, H), rng.uniform(600, 1000)
        x = (x0 + t * sp) % (W + 300) - 150
        line(d, [(x, y0), (x + 80, y0 - 4)], (200, 210, 235, 40), 1.5)
    return info


def camera_at(t, info):
    lip = (rope_x(LIP[1] + 22, t), LIP[1] + 22)
    if t < T_ROCK:
        k = smooth(prog(t, 0.3, T_ROCK))
        return lerp(lip[0], 600, k), lerp(lip[1], 1000, k), lerp(3.0, 1.35, k)
    if t < T_HIT + 0.6:                              # follow the rock down to the helmet
        k = smooth(prog(t, T_ROCK, T_HIT))
        return 600, lerp(1000, 1250, k), lerp(1.35, 1.6, k)
    if t < T_KNIFE:
        k = smooth(prog(t, T_HIT + 0.6, T_POINT0 + 0.4))
        return 600, lerp(1250, 1120, k), lerp(1.6, 1.4, k)
    if t < T_THROW:
        hl = info["hero"]["hl"]
        if 7.3 <= t < 7.9:                           # a cut to the anchor, pulling out
            return LIP[0] - 50, LEDGE_Y - 20, 3.0
        k = smooth(prog(t, T_KNIFE, T_KNIFE + 0.8))
        return lerp(600, hl[0], k), lerp(1120, hl[1], k), lerp(1.4, 2.1, k)
    if t < T_GRAB:
        k = smooth(prog(t, T_THROW, T_THROW + 0.5))
        return lerp(620, 700, k), lerp(1000, 1250, k), lerp(1.8, 1.3, k)
    if t < T_CLIMB:
        return 560, 1180, 1.4
    if t < T_TOP:
        hy = info["hero"]["hip"][1]
        if T_SLIP - 0.1 <= t < T_SLIP + 0.5:
            return LIP[0], LIP[1] + 40, 2.2
        return 580, hy + 120, 1.35
    if t < T_SNAP + 0.6:
        return 480, 760, 1.4
    k = smooth(prog(t, T_SNAP + 0.6, T_SNAP + 2.4))
    return lerp(480, 300, k), lerp(760, 700, k), lerp(1.4, 1.25, k)


def frame(t):
    stage = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(stage)
    info = scene(stage, d, t)
    base = BG.copy()
    g = stage.resize((W * K // 8, H * K // 8), Image.BILINEAR).filter(ImageFilter.GaussianBlur(5))
    gl = Image.new("RGBA", g.size, (190, 205, 240, 0))
    gl.putalpha(g.split()[3].point(lambda v: int(v * 0.35)))
    base.alpha_composite(gl.resize(stage.size, Image.BILINEAR))
    base.alpha_composite(stage)
    fx, fy, z = camera_at(t, info)
    sh = 0.0
    for s0 in SNAPS + [T_HIT, T_SSLIP, T_WALL, T_SLIP, T_SNAP]:
        if s0 <= t < s0 + 0.3:
            sh = max(sh, (1 - (t - s0) / 0.3) * (16 if s0 in (T_HIT, T_SSLIP, T_WALL, T_SLIP, T_SNAP) else 5))
    dx = z * (W / 2 - fx) + sh * math.sin(t * 90)
    dy = z * (H / 2 - fy) + sh * 0.6 * math.cos(t * 77)
    im = hq.camera(base, z, dx * K, dy * K).resize((W, H), Image.LANCZOS)
    for b0 in (T_BOLT, T_BOLT + 0.32):
        if b0 <= t < b0 + 0.15:
            im = Image.blend(im, Image.new("RGBA", im.size, (230, 236, 255, 255)), 0.55 * (1 - (t - b0) / 0.15))
    dq = ImageDraw.Draw(im)
    # ROPE counter
    pct = rope_pct(t)
    col = tuple(int(lerp(a, b, 1 - pct / 62)) for a, b in zip((240, 236, 226), (240, 80, 70)))
    PW.spaced(dq, W / 2, 470 if t < 2.6 else 150, "ROPE", font(C.SERIF, 30), (180, 184, 198, 255), 10)
    PW.spaced(dq, W / 2, 506 if t < 2.6 else 186, f"{int(round(pct))}%", font(SERIF_B, 92), col + (255,), 4)
    if t < 2.6:
        k = 1 - smooth(prog(t, 2.3, 2.6))
        fb = font(SERIF_B, 66)
        for i, ln in enumerate(("THE ROPE CAN", "ONLY HOLD ONE.")):
            y = 230 + i * 86
            PW.spaced(dq, W / 2 + 3, y + 4, ln, fb, (0, 0, 0, int(170 * k)), 4)
            PW.spaced(dq, W / 2, y, ln, fb, (246, 240, 226, int(255 * k)), 4)
    lines = [(T_LINES, "HE COULD HAVE CUT IT."), (T_LINES + 0.8, "HE CHOSE NOT TO.")]
    C.caption(im, lines, t)
    return np.asarray(im.convert("RGB"))


def init_worker():
    global BG
    BG = build_bg()


def render(i):
    return frame(i / FPS).tobytes()


# ---------------------------------------------------------------- sound
def load(name, start, dur):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(start), "-t", str(dur), "-i", os.path.join(MDIR, name),
                          "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)


def audio():
    n = int(DUR * SR)
    tt = np.arange(n) / SR
    mus = np.zeros((n, 2))
    # tension: Immersed (quiet) until the knife is thrown; then Eternal Hope's build, its peak on the rescue
    a = load("Immersed.mp3", 2.0, T_THROW + 1.5)
    mus[:len(a)] += a[:n] * np.minimum(1, np.arange(len(a)) / (0.3 * SR))[:, None] * \
        np.clip((T_THROW + 1.5 - np.arange(len(a)) / SR) / 1.5, 0, 1)[:, None] * 1.3
    eh_start = 244.0 - (T_SNAP - 0.3)          # 244 s = the big swell
    i0 = int((T_THROW - 0.2) * SR)
    b = load("Eternal Hope.mp3", eh_start + T_THROW - 0.2, DUR - T_THROW + 0.2)
    fade_in = np.minimum(1, np.arange(len(b)) / (1.2 * SR))
    mus[i0:i0 + len(b)] += b[:n - i0] * fade_in[:n - i0, None]
    mus *= np.clip((DUR - tt) / 0.8, 0.2, 1)[:, None]
    fx = np.zeros((n, 2))
    wind = noise(DUR, 3, lo=150, hi=1500)[:n] * (0.6 + 0.4 * np.sin(tt * 0.9))
    fx[:, 0] += 0.05 * wind
    fx[:, 1] += 0.05 * np.roll(wind, 3000)
    for s0 in SNAPS:
        mix_in(fx, noise(0.06, int(s0 * 10), lo=1500, hi=7000)[:int(0.06 * SR)] * env(int(0.06 * SR), 0.0005, 0.02),
               s0, 0.14, 0.1)
        mix_in(fx, tone(240, 0.3, (1, 1.5), a=0.01, d=0.15, sweep=200), s0, 0.03)
    # heartbeat under the knife
    for j in range(7):
        for k2, dt in enumerate((0.0, 0.17)):
            mix_in(fx, tone(48, 0.2, (1, 0.5), a=0.003, d=0.08), T_KNIFE + 0.2 + j * 0.42 + dt, 0.16 - 0.06 * k2)
    mix_in(fx, tone(3000, 0.6, (1, 2.4), a=0.001, d=0.3), T_KNIFE + 0.4, 0.03)           # the blade drawn
    mix_in(fx, noise(0.5, 9, lo=500, hi=5000)[:int(0.5 * SR)] * np.sin(np.linspace(0, np.pi, int(0.5 * SR))),
           T_THROW, 0.07)
    mix_in(fx, tone(70, 0.4, (1, 0.5), a=0.002, d=0.15), T_SLIP, 0.16)                    # the slip
    mix_in(fx, noise(0.8, 10, lo=300, hi=6000)[:int(0.8 * SR)] * env(int(0.8 * SR), 0.001, 0.2), T_SNAP, 0.3)
    mix_in(fx, tone(60, 0.8, (1, 0.5), a=0.002, d=0.4), T_SNAP, 0.2)
    # the rock: a rumble, the clank on the helmet
    mix_in(fx, noise(0.7, 30, lo=80, hi=900)[:int(0.7 * SR)] * env(int(0.7 * SR), 0.05, 0.3), T_ROCK - 0.1, 0.1)
    mix_in(fx, tone(1800, 0.5, (1, 2.7, 4.1), a=0.0005, d=0.15) + 0.4 * noise(0.5, 31, lo=1000, hi=8000)[
        :int(0.5 * SR)] * env(int(0.5 * SR), 0.0005, 0.05), T_HIT, 0.22)
    # the anchor creaking out of the rock
    for t0 in (T_PITON + 0.2, T_PITON + 1.0, 7.4, T_WALL + 0.05, T_SLIP + 0.05, T_SNAP - 0.5):
        sq = tone(900, 0.35, (1, 1.5, 2.2), a=0.02, d=0.2, sweep=700)
        mix_in(fx, sq, t0, 0.04, -0.3)
    # thunder and rain
    th = noise(3.0, 32, lo=30, hi=400)[:3 * SR] * env(3 * SR, 0.02, 1.2)
    mix_in(fx, th, T_BOLT + 0.05, 0.35)
    mix_in(fx, noise(0.15, 33, lo=1000, hi=9000)[:int(0.15 * SR)] * env(int(0.15 * SR), 0.0005, 0.04), T_BOLT, 0.3)
    rl = DUR - T_BOLT
    rn = noise(rl, 34, lo=1200, hi=9000)[:int(rl * SR)] * np.minimum(1, np.arange(int(rl * SR)) / (0.8 * SR))
    mix_in(fx, rn, T_BOLT, 0.06)
    # the stranger's hand slips; the gust; the wall; the edge crumbling
    mix_in(fx, noise(0.3, 35, lo=500, hi=4000)[:int(0.3 * SR)] * env(int(0.3 * SR), 0.001, 0.1), T_SSLIP, 0.1)
    gw = noise(1.0, 36, lo=200, hi=2500)[:SR] * np.sin(np.linspace(0, np.pi, SR))
    mix_in(fx, gw, T_GUST - 0.2, 0.15)
    mix_in(fx, tone(60, 0.4, (1, 0.5), a=0.001, d=0.15) + 0.4 * noise(0.4, 37, lo=100, hi=2500)[:int(0.4 * SR)] *
           env(int(0.4 * SR), 0.001, 0.06), T_WALL, 0.25)
    for j in range(5):
        mix_in(fx, noise(0.12, 38 + j, lo=300, hi=4000)[:int(0.12 * SR)] * env(int(0.12 * SR), 0.001, 0.04),
               T_SLIP + j * 0.12, 0.08)
    mix_in(fx, tone(2400, 0.4, (1, 2.6), a=0.0005, d=0.15), T_SNAP + 0.05, 0.06)
    # heavy breathing at the end
    for j in range(5):
        mix_in(fx, noise(0.5, 20 + j, lo=300, hi=2500)[:int(0.5 * SR)] * np.sin(np.linspace(0, np.pi, int(0.5 * SR))),
               T_SNAP + 0.8 + j * 0.6, 0.04)
    x = mus + fx
    m = int(0.25 * SR)
    k = np.linspace(0, 1, m)[:, None]
    x[-m:] = x[-m:] * (1 - k) + x[:m] * k
    x /= max(1.0, np.abs(x).max() / 0.9)
    return x


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "rope.mp4"
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
