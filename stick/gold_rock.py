#!/usr/bin/env python3
"""THE GOLD WAS UNDER IT - Doer vs Overthinker, two identical tunnels (split screen), 22.4 s, loops on itself.

A cut-away of the ground: both dig the same tunnel with the same pick, through dirt, through roots, to a big rock -
and the viewer sees, from the first frame, the gold buried right under the floor in front of that rock.
Two clangs on the rock, together. Then: below, "IT'S IMPOSSIBLE." - he throws the pick, walks back and sits down,
12 M dug, standing on top of the gold when he quit. Above, a third clang, a step back, "?", a light bulb - he
digs DOWN instead, and on the fourth swing the gold lights up the tunnel: 13 M. Below, the glow comes up through his
own floor: hands on his head, "...UNDER IT?"
"HE QUIT AT THE ROCK. / THE GOLD WAS UNDER IT."

    python3 stick/gold_rock.py stick/gold-under-it.mp4
    ONLY_FRAMES=0,2,5.3,7.0,8.6,9.6,11.5,13.0,14.8,19 python3 stick/gold_rock.py /tmp/gr
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
from perfect_wave import (MONO, clamp, env, font, in_quad, lerp, lerp_pose, midi, mix_in, noise, out_back,  # noqa
                          out_cubic, prog, rot, smooth, spaced, tone, write_wav)

W, H, FPS = 1080, 1920, 30
SR = 44100
BPM = 75
BEAT = 60 / BPM
BAR = 4 * BEAT
DUR = 7 * BAR                           # 22.4 s
NF = int(round(DUR * FPS))
XFADE = 0.5
S = 1.0                                 # people a little smaller here: they live in a tunnel
INK = AJ.INK
PH, TOP_Y0, BOT_Y0 = AJ.PH, AJ.TOP_Y0, AJ.BOT_Y0
DOER, DOER_FAR, OT, OT_FAR = AJ.DOER, AJ.DOER_FAR, AJ.OT, AJ.OT_FAR
GOLD = (255, 204, 80)

# ---------------------------------------------------------------- the ground (panel coordinates)
GRASS = 58
CEIL, FLOOR = 160, 480                  # the tunnel
STAND_Y = FLOOR - 113 * S
FRONT0 = 210                            # where the tunnel ends at the start
ROOTS0, ROCK_X = 450, 566               # roots from here; the rock's face
ROCK = [(566, 150), (612, 118), (700, 112), (770, 150), (792, 260), (782, 420), (760, 504), (690, 520), (600, 512),
        (566, 470)]
GOLD_BOX = (500, 512, 676, 590)         # the gold, just under the floor in front of the rock
PIT_X0, PIT_X1 = 486, 600               # the doer's pit
PX_PER_M = 30.0

# ---------------------------------------------------------------- timeline
PERIOD = 0.7
CONTACT = 0.72
DIRT_SWINGS = 6                         # contacts at 0.6 + 0.7 k
ROOT_SWINGS = 3
SWINGS = [0.1 + PERIOD * k + PERIOD * CONTACT for k in range(DIRT_SWINGS + ROOT_SWINGS + 2)]
DIG_STEP = (ROOTS0 - FRONT0) / DIRT_SWINGS
ROOT_STEP = (ROCK_X - ROOTS0) / ROOT_SWINGS
CLANGS = SWINGS[DIRT_SWINGS + ROOT_SWINGS:]           # two clangs, together
T_SPLIT = CLANGS[-1] + 0.4
T_CLANG3 = T_SPLIT + 0.2 + PERIOD * CONTACT          # the doer's third
T_BACK0, T_BACK1 = T_CLANG3 + 0.35, T_CLANG3 + 0.75
T_Q0, T_BULB, T_BULB1 = T_BACK1 + 0.05, T_BACK1 + 0.6, T_BACK1 + 1.2
T_DOWN0 = T_BULB1 + 0.05
DOWN = [T_DOWN0 + 0.15 + PERIOD * k + PERIOD * CONTACT for k in range(4)]
T_GOLD = DOWN[-1]
T_CHEER = T_GOLD + 0.7

T_THROW = T_SPLIT + 0.2
T_WALK0, T_WALK1 = T_THROW + 0.6, T_THROW + 2.6
T_SITQ = T_WALK1 + 0.4
T_GLOW = T_GOLD + 0.3                    # below: the glow comes up through his floor
T_STAND0, T_STAND1 = T_GLOW + 0.3, T_GLOW + 0.9
T_L1, T_L2 = 16.6, 18.0
CPS = 16.0
LINE1, LINE2 = "HE QUIT AT THE ROCK.", "THE GOLD WAS UNDER IT."

BUB_BOTH = [(4.4, 5.9, "ROOTS. GREAT.")]
BUB_TOP = []
BUB_BOT = [(T_SPLIT, T_SPLIT + 1.6, "IT'S IMPOSSIBLE."), (T_SITQ + 0.3, T_SITQ + 1.9, "WASTE OF TIME."),
           (T_STAND1, T_STAND1 + 2.2, "...UNDER IT?")]


def front(t, top):
    """How far the tunnel goes."""
    f = FRONT0
    for i, c in enumerate(SWINGS[:DIRT_SWINGS + ROOT_SWINGS]):
        if t >= c:
            f = FRONT0 + (i + 1) * DIG_STEP if i < DIRT_SWINGS else ROOTS0 + (i - DIRT_SWINGS + 1) * ROOT_STEP
    return f


def pit(t):
    n = sum(1 for c in DOWN if t >= c)
    return n / len(DOWN)


def meters(t, top):
    m = (front(t, top) - FRONT0) / PX_PER_M * (12 / ((ROCK_X - FRONT0) / PX_PER_M)) + 8
    if top:
        m += pit(t) * 1.0
    return m


# ---------------------------------------------------------------- poses (facing right, from the hip)
STAND = PW.STAND
RAISE = {"head": (-6, -150), "neck": (-4, -108), "el": (-30, -140), "hl": (-40, -180), "er": (-24, -136),
         "hr": (-34, -176), "kl": (-24, 56), "fl": (-38, 113), "kr": (24, 56), "fr": (38, 113)}
STRIKE = {"head": (20, -140), "neck": (14, -98), "el": (48, -76), "hl": (84, -80), "er": (44, -72), "hr": (78, -76),
          "kl": (-20, 58), "fl": (-40, 113), "kr": (34, 52), "fr": (48, 113)}
DOWN_RAISE = dict(RAISE, head=(16, -138), neck=(10, -98))
DOWN_STRIKE = {"head": (44, -110), "neck": (32, -76), "el": (56, -30), "hl": (80, 4), "er": (52, -26), "hr": (74, 8),
               "kl": (-14, 56), "fl": (-40, 113), "kr": (40, 46), "fr": (50, 113)}
THINK = dict(STAND, er=(22, -70), hr=(18, -118), el=(-10, -60), hl=(-14, -12), head=(10, -146))
THROW = dict(STAND, el=(10, -150), hl=(30, -196))
SIT_FLOOR = {"head": (10, -150), "neck": (4, -108), "el": (32, -76), "hl": (-6, -80), "er": (28, -72), "hr": (-10, -76),
             "kl": (62, -26), "fl": (92, 28), "kr": (56, -20), "fr": (86, 32)}
HANDS_HEAD = dict(STAND, el=(-34, -146), hl=(-10, -176), er=(34, -146), hr=(10, -176))
CHEER = PW.ARMS_UP
A_RAISE, A_STRIKE, A_DOWN = -2.3, 0.05, 1.15


def swing(t, t0, down=False, bounce=False):
    u = ((t - t0) / PERIOD) % 1.0
    R, Sk, a_s = (DOWN_RAISE, DOWN_STRIKE, A_DOWN) if down else (RAISE, STRIKE, A_STRIKE)
    if u < 0.5:
        k = smooth(u / 0.5)
        return lerp_pose(Sk, R, k), lerp(a_s, A_RAISE, k)
    if u < 0.62:
        return R, A_RAISE
    if u < CONTACT:
        k = in_quad((u - 0.62) / (CONTACT - 0.62))
        return lerp_pose(R, Sk, k), lerp(A_RAISE, a_s, k)
    if bounce:
        r = math.sin(math.pi * clamp((u - CONTACT) / 0.18))
        return lerp_pose(Sk, R, 0.3 * r), lerp(a_s, A_RAISE, 0.3 * r)
    return Sk, a_s


def digger_x(t, top):
    return front(t, top) - 96


def person(t, top):
    """(pose, x, y, facing, pick angle or None, extra)"""
    x = digger_x(t, top)
    if t < 0.1:
        return STAND, x, STAND_Y, 1, -1.2, None
    if t < T_SPLIT:
        bounce = t >= CLANGS[0] - PERIOD * CONTACT
        pose, a = swing(t, 0.1, bounce=bounce)
        return pose, x, STAND_Y, 1, a, None
    if top:
        if t < T_CLANG3 + 0.3:
            pose, a = swing(t, T_SPLIT + 0.2, bounce=True)
            return pose, x, STAND_Y, 1, a, None
        if t < T_DOWN0:
            k = smooth(prog(t, T_BACK0, T_BACK1))
            p = lerp_pose(STRIKE, THINK, k)
            return p, x - 50 * k, STAND_Y, 1, lerp(A_STRIKE, 1.75, k), "think"
        if t < T_GOLD + 0.05:
            k = smooth(prog(t, T_DOWN0, T_DOWN0 + 0.2))
            pose, a = swing(t, T_DOWN0 + 0.15, down=True)
            return pose, lerp(x - 50, x - 70, k), STAND_Y, 1, a, None
        k = smooth(prog(t, T_GOLD + 0.1, T_CHEER))
        return lerp_pose(DOWN_STRIKE, CHEER, k), x - 70, STAND_Y, 1, None, "nugget" if k > 0.5 else None
    # below
    if t < T_WALK0:
        k = math.sin(math.pi * prog(t, T_THROW - 0.1, T_THROW + 0.4))
        return lerp_pose(STRIKE, THROW, k), x, STAND_Y, 1, (A_RAISE if t < T_THROW + 0.1 else None), None
    if t < T_WALK1:
        u = prog(t, T_WALK0, T_WALK1)
        return AJ.walk(t * 6, STAND), lerp(x, 120, smooth(u)), STAND_Y, -1, None, None
    if t < T_STAND0:
        k = smooth(prog(t, T_WALK1, T_SITQ))
        return lerp_pose(STAND, SIT_FLOOR, k), 120, lerp(STAND_Y, FLOOR - 37 * S, k), 1, None, None
    k = smooth(prog(t, T_STAND0, T_STAND1))
    return lerp_pose(SIT_FLOOR, HANDS_HEAD, k), 120, lerp(FLOOR - 37 * S, STAND_Y, k), 1, None, None


def pick_on_floor(t):
    """Where the thrown pick lies below."""
    if t < T_THROW + 0.1:
        return None
    u = prog(t, T_THROW + 0.1, T_THROW + 0.55)
    x = lerp(digger_x(t, False) + 30, 470, u)
    y = lerp(STAND_Y - 160, FLOOR - 8, out_cubic(u)) - 40 * math.sin(math.pi * u)
    return x, y, lerp(-2.0, 0.1, u) + 4 * u


# ---------------------------------------------------------------- drawing
def draw_pick(d, hand, ang, scale=1.0):
    ink = INK + (255,)
    dx, dy = math.cos(ang), math.sin(ang)
    a = (hand[0] - 20 * dx, hand[1] - 20 * dy)
    b = (hand[0] + 118 * dx, hand[1] + 118 * dy)
    d.line([a, b], fill=ink, width=12)
    d.line([a, b], fill=(170, 118, 70, 255), width=6)
    nx, ny = -dy, dx
    # the head: a curved bar across the tip, pointed both ways
    pts = []
    for i in range(9):
        s = -1 + 2 * i / 8
        bend = -10 * (1 - s * s)
        pts.append((b[0] + s * 46 * nx + bend * dx, b[1] + s * 46 * ny + bend * dy))
    d.line(pts, fill=ink, width=14, joint="curve")
    d.line(pts, fill=(196, 200, 210, 255), width=7, joint="curve")
    return (b[0] + 46 * nx, b[1] + 46 * ny), (b[0] - 46 * nx, b[1] - 46 * ny)


def person_sprite(pts, body, far, facing):
    cv = AJ.Canvas(*PW.bbox_of(list(pts.values()), 110))
    AJ.draw_stick(cv, pts, body, far, facing, s=S)
    return cv.done()


def build_ground():
    yy, xx = np.mgrid[0:PH, 0:W].astype(np.float32)
    sky = (yy < GRASS)[..., None]
    skyc = np.array([10, 12, 24], np.float32) + (yy / GRASS)[..., None] * np.array([10, 12, 20], np.float32)
    depth = np.clip((yy - GRASS) / (PH - GRASS), 0, 1)[..., None]
    earth = (1 - depth) * np.array([92, 66, 44], np.float32) + depth * np.array([58, 40, 28], np.float32)
    # bands of earth
    band = (0.5 + 0.5 * np.sin(yy / 23 + np.sin(xx / 90) * 1.5))[..., None]
    earth = earth * (0.92 + 0.1 * band)
    img = np.where(sky, skyc, earth)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(4)
    for _ in range(40):
        x, y = rng.uniform(0, W), rng.uniform(0, GRASS - 10)
        b = int(rng.uniform(90, 200))
        d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(b, b, b + 20, 255))
    d.rectangle([0, GRASS - 6, W, GRASS + 6], fill=(70, 120, 60, 255))
    for i in range(140):
        x = rng.uniform(0, W)
        d.line([(x, GRASS - 4), (x + rng.uniform(-4, 4), GRASS - 14)], fill=(84, 140, 70, 255), width=2)
    for _ in range(260):
        x, y = rng.uniform(0, W), rng.uniform(GRASS + 12, PH)
        r = rng.uniform(2, 7)
        c = int(rng.uniform(60, 120))
        d.ellipse([x - r, y - r * 0.7, x + r, y + r * 0.7], fill=(c + 20, c, c - 18, 255))
    # roots coming down from the grass, tangled in the dirt ahead
    r2 = np.random.default_rng(9)
    for i in range(7):
        x = ROOTS0 + r2.uniform(-10, 100)
        pts = [(x, GRASS + 4)]
        y = GRASS + 4
        while y < FLOOR + 40:
            y += r2.uniform(26, 44)
            x += r2.uniform(-16, 16)
            pts.append((x, y))
        d.line(pts, fill=(150, 112, 74, 255), width=int(r2.uniform(4, 8)), joint="curve")
    # a fossil and an old bottle, for the eye
    d.arc([880, 300, 980, 360], 200, 340, fill=(214, 206, 186, 255), width=5)
    for i in range(5):
        x = 892 + i * 18
        d.line([(x, 318), (x + 2, 300)], fill=(214, 206, 186, 255), width=4)
    return im


def draw_tunnel(im, d, t, top):
    ink = INK + (255,)
    f = front(t, top)
    # the dug-out tunnel: dark, with a warm lantern near the digger
    pts = [(-10, CEIL), (f - 14, CEIL), (f, CEIL + 40), (f - 8, CEIL + 120), (f + 6, CEIL + 200), (f - 4, FLOOR - 40),
           (f - 16, FLOOR), (-10, FLOOR)]
    d.polygon(pts, fill=(30, 22, 18, 255))
    d.line(pts + [pts[0]], fill=(20, 14, 10, 255), width=4)
    if top and pit(t) > 0:
        depth = 112 * pit(t)
        d.polygon([(PIT_X0, FLOOR - 2), (PIT_X1, FLOOR - 2), (PIT_X1 - 10, FLOOR + depth), (PIT_X0 + 12, FLOOR + depth)],
                  fill=(30, 22, 18, 255))
    # support beams
    for bx in range(60, int(f) - 60, 240):
        d.rectangle([bx - 10, CEIL, bx + 10, FLOOR], fill=(110, 78, 48, 255), outline=ink, width=3)
        d.rectangle([bx - 46, CEIL, bx + 46, CEIL + 16], fill=(120, 86, 52, 255), outline=ink, width=3)
    # cut roots hang from the ceiling where the tunnel went through them
    if f > ROOTS0 + 10:
        rr = np.random.default_rng(3)
        for i in range(5):
            x = ROOTS0 + 10 + i * 20
            if x < f - 10:
                L = rr.uniform(20, 46)
                d.line([(x, CEIL), (x + rr.uniform(-8, 8), CEIL + L)], fill=(150, 112, 74, 255), width=5)
    # the lantern
    lx = max(140, f - 220)
    gl = Image.new("RGBA", (700, 500), (0, 0, 0, 0))
    ImageDraw.Draw(gl).ellipse([150, 60, 550, 440], fill=(255, 200, 120, 70))
    gl = gl.filter(ImageFilter.GaussianBlur(60))
    im.alpha_composite(gl, (int(lx - 350), int(CEIL - 140)))
    d = ImageDraw.Draw(im)
    d.line([(lx, CEIL + 16), (lx, CEIL + 40)], fill=ink, width=3)
    d.rounded_rectangle([lx - 12, CEIL + 40, lx + 12, CEIL + 72], 4, fill=(255, 210, 120, 255), outline=ink, width=3)
    return d


def draw_rock(d, t, top, shake=0.0):
    ink = INK + (255,)
    pts = [(x + shake, y) for x, y in ROCK]
    d.polygon(pts, fill=(112, 112, 122, 255), outline=ink)
    d.line(pts + [pts[0]], fill=ink, width=6)
    d.polygon([(600, 170), (690, 150), (740, 190), (650, 210)], fill=(140, 140, 150, 255))
    for (a, b) in (((640, 280), (690, 330)), ((690, 330), (676, 400)), ((720, 250), (760, 300))):
        d.line([(a[0] + shake, a[1]), (b[0] + shake, b[1])], fill=(70, 70, 78, 255), width=4)


def draw_gold(im, d, t, top, extra=0.0):
    """The gold under the floor; it glows a little from the start, a lot once found (or once he sees it below)."""
    x0, y0, x1, y1 = GOLD_BOX
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    pulse = 0.5 + 0.2 * math.sin(t * 3)
    glow = pulse * 0.6 + extra
    gl = Image.new("RGBA", (600, 400), (0, 0, 0, 0))
    ImageDraw.Draw(gl).ellipse([150, 120, 450, 280], fill=GOLD + (int(min(255, 110 * glow + 40)),))
    gl = gl.filter(ImageFilter.GaussianBlur(36))
    im.alpha_composite(gl, (int(cx - 300), int(cy - 200)))
    d = ImageDraw.Draw(im)
    d.ellipse([x0, y0, x1, y1], fill=(46, 32, 20, 255))
    rng = np.random.default_rng(12)
    for i in range(16):
        x = rng.uniform(x0 + 20, x1 - 20)
        y = rng.uniform(y0 + 20, y1 - 14)
        r = rng.uniform(9, 16)
        d.polygon([(x - r, y), (x - r * 0.4, y - r * 0.8), (x + r * 0.6, y - r * 0.7), (x + r, y + r * 0.1),
                   (x + r * 0.3, y + r * 0.7), (x - r * 0.6, y + r * 0.6)], fill=(255, 200, 60, 255), outline=INK + (255,))
        d.line([(x - r * 0.3, y - r * 0.4), (x + r * 0.2, y - r * 0.5)], fill=(255, 246, 200, 255), width=2)
    if extra > 0.2:
        r3 = np.random.default_rng(int(t * 12))
        for i in range(12):
            sx, sy = r3.uniform(x0, x1), r3.uniform(y0 - 120 * min(1, extra), y1)
            s = r3.uniform(3, 7)
            d.line([(sx - s, sy), (sx + s, sy)], fill=(255, 250, 220, 220), width=2)
            d.line([(sx, sy - s), (sx, sy + s)], fill=(255, 250, 220, 220), width=2)
    return d


def particles(d, t, top):
    hits = SWINGS[:DIRT_SWINGS + ROOT_SWINGS]
    for i, tc in enumerate(hits + CLANGS + ([T_CLANG3] + DOWN if top else [])):
        tau = t - tc
        if tau < 0 or tau > 0.8:
            continue
        rng = np.random.default_rng(int(tc * 1000) + (1 if top else 2))
        clang = tc in CLANGS or tc == T_CLANG3
        down = tc in DOWN
        if clang:
            x0, y0 = ROCK_X - 4, FLOOR - 190
        elif down:
            x0, y0 = (PIT_X0 + PIT_X1) / 2, FLOOR + 112 * pit(tc) - 10
        else:
            x0, y0 = front(tc, top) - 4, FLOOR - 190
        for j in range(14):
            if clang:
                vx, vy = rng.uniform(-420, -120), rng.uniform(-420, 120)
                if tau > 0.3:
                    continue
                x, y = x0 + vx * tau, y0 + vy * tau + 600 * tau * tau
                d.line([(x, y), (x - vx * 0.02, y - vy * 0.02)], fill=(255, 220, 120, int(255 * (1 - tau / 0.3))), width=3)
            else:
                vx, vy = rng.uniform(-300, -40), rng.uniform(-300, 50)
                if down:
                    vx = rng.uniform(-160, 160)
                    vy = rng.uniform(-420, -150)
                x = x0 + vx * tau
                y = min(FLOOR - 4, y0 + vy * tau + 0.5 * 1600 * tau * tau)
                r = rng.uniform(4, 9)
                a = int(255 * (1 - tau / 0.8))
                c = (150, 112, 74) if (not clang and hits.index(tc) >= DIRT_SWINGS if tc in hits else False) else (118, 84, 54)
                d.polygon([(x - r, y), (x, y - r * 0.7), (x + r, y), (x, y + r * 0.6)], fill=c + (a,))


def thought(im, d, t, head):
    if not (T_Q0 <= t < T_BULB1):
        return d
    hx, hy = head
    bx, by = hx + 70, hy - 110
    sc = out_back(prog(t, T_Q0, T_Q0 + 0.2))
    al = 1 - smooth(prog(t, T_BULB1 - 0.15, T_BULB1))
    a = int(255 * al)
    if sc < 0.05:
        return d
    for r, ox, oy in ((6, 26, 62), (9, 44, 84)):
        d.ellipse([hx + ox - r, hy - oy - r, hx + ox + r, hy - oy + r], fill=(242, 240, 234, a), outline=INK + (a,), width=3)
    R = 44 * sc
    d.ellipse([bx - R, by - R, bx + R, by + R], fill=(242, 240, 234, a), outline=INK + (a,), width=4)
    if t < T_BULB:
        spaced(d, bx, by - 28 * sc, "?", font("InterDisplay-Bold.otf", int(50 * sc)), INK + (a,), 0)
    else:
        k = out_back(prog(t, T_BULB, T_BULB + 0.2))
        r = 17 * k
        d.ellipse([bx - r, by - r - 6, bx + r, by + r - 6], fill=(255, 220, 90, a), outline=INK + (a,), width=3)
        d.rectangle([bx - 8 * k, by + r - 8, bx + 8 * k, by + r + 4], fill=(150, 150, 160, a), outline=INK + (a,), width=2)
    return d


def box(d, x0, y0, label, value, col, w=220):
    d.rounded_rectangle([x0, y0, x0 + w, y0 + 88], 8, fill=(18, 20, 28, 230), outline=(90, 94, 104, 255), width=2)
    spaced(d, x0 + w / 2, y0 + 10, label, font("Inter-SemiBold.otf", 21), (190, 194, 204, 255), 5)
    spaced(d, x0 + w / 2, y0 + 36, value, font(MONO, 40), col + (255,), 1)


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
        x = clamp(head[0] - spr.width / 2 + 30, 16, W - 260 - spr.width)
        y = max(GRASS + 8, head[1] - 46 - spr.height)
        im.alpha_composite(spr, (int(x), int(y)))


GROUND = None
FRAME0 = None


def panel(t, top):
    im = GROUND.copy()
    d = ImageDraw.Draw(im)
    found = smooth(prog(t, T_GOLD, T_GOLD + 0.5)) if top else 0.0
    seen = smooth(prog(t, T_GLOW, T_GLOW + 0.8)) if not top else 0.0
    d = draw_gold(im, d, t, top, 2.2 * found + 1.0 * seen)
    d = draw_tunnel(im, d, t, top)
    shake = 0.0
    for c in CLANGS + ([T_CLANG3] if top else []):
        if c <= t < c + 0.2:
            shake = 4 * math.sin((t - c) * 80) * (1 - (t - c) / 0.2)
    draw_rock(d, t, top, shake)
    if not top and seen > 0:
        # light seeps up through the floor in front of the rock
        gl = Image.new("RGBA", (400, 260), (0, 0, 0, 0))
        ImageDraw.Draw(gl).polygon([(110, 260), (290, 260), (250, 0), (150, 0)], fill=GOLD + (int(90 * seen),))
        gl = gl.filter(ImageFilter.GaussianBlur(24))
        im.alpha_composite(gl, (int((GOLD_BOX[0] + GOLD_BOX[2]) / 2 - 200), int(FLOOR - 230)))
        d = ImageDraw.Draw(im)
    pk = pick_on_floor(t) if not top else None
    if pk:
        draw_pick(d, (pk[0], pk[1]), pk[2])
    pose, x, y, f, ang, extra = person(t, top)
    pts = AJ.place(pose, (x, y), f, S)
    body, far = (DOER, DOER_FAR) if top else (OT, OT_FAR)
    spr, off = person_sprite(pts, body, far, f)
    if top:
        gcol = (255, 214, 120) if found > 0.1 else (210, 228, 255)
        im.alpha_composite(PW.glow_of(spr, 0.5 + 0.7 * found, 12, gcol), off)
    im.alpha_composite(spr, off)
    d = ImageDraw.Draw(im)
    if ang is not None:
        hand = pts["hl"]
        draw_pick(d, hand, ang if f > 0 else math.pi - ang)
        for hn in ("hl", "hr"):
            q = pts[hn]
            d.ellipse([q[0] - 14, q[1] - 14, q[0] + 14, q[1] + 14], fill=INK + (255,))
            d.ellipse([q[0] - 9, q[1] - 9, q[0] + 9, q[1] + 9], fill=body + (255,))
    if extra == "nugget":
        q = pts["hl"]
        d.polygon([(q[0] - 16, q[1] - 6), (q[0] - 4, q[1] - 22), (q[0] + 14, q[1] - 16), (q[0] + 18, q[1] + 2),
                   (q[0] + 2, q[1] + 10), (q[0] - 12, q[1] + 6)], fill=(255, 204, 60, 255), outline=INK + (255,))
    particles(d, t, top)
    if top:
        d = thought(im, d, t, pts["head"])
    m = meters(t, top)
    box(d, W - 246, GRASS + 14, "DUG", f"{int(round(m))} M", GOLD if (top and found > 0.5) else (240, 240, 244))
    bubbles(im, t, BUB_BOTH + (BUB_TOP if top else BUB_BOT), pts["head"])
    return im


def frame(t):
    img = Image.new("RGBA", (W, H), (6, 6, 8, 255))
    img.alpha_composite(panel(t, True), (0, TOP_Y0))
    img.alpha_composite(panel(t, False), (0, BOT_Y0))
    d = ImageDraw.Draw(img)
    spaced(d, W / 2, 268, "DOER", font("Inter-SemiBold.otf", 40), (236, 238, 244, 255), 10)
    spaced(d, W / 2, BOT_Y0 + PH + 18, "OVERTHINKER", font("Inter-SemiBold.otf", 40), (200, 204, 214, 255), 10)
    spaced(d, W / 2, TOP_Y0 + PH + 34, "SAME MINE", font("Inter-SemiBold.otf", 40), (206, 210, 220, 255), 9)
    d.line([(60, BOT_Y0 - 8), (W - 60, BOT_Y0 - 8)], fill=(50, 52, 60, 255), width=2)
    fm = font(MONO, 50)
    for t0, s, y, col in ((T_L1, LINE1, 80, (250, 250, 252)), (T_L2, LINE2, 148, GOLD)):
        if t < t0:
            continue
        k = int(clamp((t - t0) * CPS, 0, len(s)))
        full = sum(fm.getlength(c) for c in s) + 3 * (len(s) - 1)
        xx = W / 2 - full / 2
        for c in s[:k]:
            d.text((xx, y), c, font=fm, fill=col + (255,))
            xx += fm.getlength(c) + 3
        if (k < len(s) or (s == LINE2 and t < t0 + len(s) / CPS + 1.0)) and int(t * 3.4) % 2 == 0:
            d.rectangle([xx + 2, y + 6, xx + 26, y + 56], fill=col + (220,))
    return np.asarray(img.convert("RGB"))


def init_worker():
    global GROUND
    GROUND = build_ground()


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
    chords = [[50, 53, 57, 60], [46, 50, 53, 57], [48, 52, 55, 59], [45, 48, 52, 55]]
    roots = [38, 34, 36, 33]
    mel = [69, 67, 65, 64, 65, 67, 69, 72]
    for b in range(int(round(DUR / BAR))):
        t0 = b * BAR
        ch, rt = chords[b % 4], roots[b % 4]
        for k, m in enumerate(ch):
            mix_in(mus, GS.pad(midi(m), BAR, 0.8, 1.4), t0, 0.045, (k - 1.5) * 0.4)
        mix_in(mus, GS.pad(midi(rt - 12), BAR, 0.3, 1.0), t0, 0.11)
        if b != 3:
            for q in (0, 2):
                mix_in(mus, GS.keys(midi(mel[(b * 2 + q // 2) % len(mel)])), t0 + q * BEAT + 0.05, 0.04, 0.25)
    # dirt: a soft crunch; roots: a snap; the rock: a clang
    for i, tc in enumerate(SWINGS[:DIRT_SWINGS + ROOT_SWINGS]):
        mix_in(fx, noise(0.18, 30 + i, lo=120, hi=1500) * env(int(0.18 * SR), 0.002, 0.05), tc, 0.2)
        if i >= DIRT_SWINGS:
            mix_in(fx, noise(0.06, 60 + i, lo=1500, hi=6000) * env(int(0.06 * SR), 0.001, 0.015), tc + 0.02, 0.15)
    for tc in CLANGS + [T_CLANG3]:
        mix_in(fx, tone(1900, 0.5, (1, 0.5, 0.3), a=0.001, d=0.16), tc, 0.06, 0.0 if tc in CLANGS else -0.3)
        mix_in(fx, tone(240, 0.2, (1, 0.4), a=0.001, d=0.06), tc, 0.08, 0.0 if tc in CLANGS else -0.3)
    # the pick thrown down below
    mix_in(fx, noise(0.4, 70, lo=1500, hi=8000) * env(int(0.4 * SR), 0.002, 0.1), T_THROW + 0.5, 0.12, 0.3)
    # the idea, digging down, the gold
    for i, m in enumerate((84, 91)):
        mix_in(fx, GS.keys(midi(m), 1.2), T_BULB + i * 0.08, 0.06, -0.3)
    for i, tc in enumerate(DOWN):
        mix_in(fx, noise(0.18, 80 + i, lo=120, hi=1500) * env(int(0.18 * SR), 0.002, 0.05), tc, 0.2, -0.3)
    for i, m in enumerate((72, 76, 79, 84, 88, 91)):
        mix_in(fx, GS.keys(midi(m), 1.6), T_GOLD + 0.05 + i * 0.07, 0.06, -0.3 + i * 0.05)
    # below: a low note when he sees it
    mix_in(fx, GS.pad(midi(38), 1.6, 0.05, 1.2), T_STAND0, 0.12, 0.3)
    for lst in (BUB_BOTH, BUB_TOP, BUB_BOT):
        for b0, b1, s in lst:
            mix_in(fx, tone(700, 0.08, (1,), a=0.003, d=0.03), b0, 0.03)
    for t0, s in ((T_L1, LINE1), (T_L2, LINE2)):
        for i, c in enumerate(s):
            if c != " ":
                mix_in(fx, noise(0.03, 500 + i + int(t0), lo=1200, hi=4000) * env(int(0.03 * SR), 0.001, 0.008),
                       t0 + i / CPS, 0.05)
    x = mus + fx
    m = int(XFADE * SR)
    k = np.linspace(0, 1, m)[:, None]
    x[-m:] = x[-m:] * (1 - k) + x[:m] * k
    x /= max(1.0, np.abs(x).max() / 0.9)
    return x


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "gold-under-it.mp4"
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
