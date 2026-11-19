#!/usr/bin/env python3
"""ONE TURN FROM THE EXIT - Doer vs Overthinker in the same hedge maze, seen from above (split screen), 19.2 s, loops.

The exit glows in the top-right corner from the first frame. Together they walk in, hit a dead end (1), another (2),
walk past a turn and into a third (3). Each leaves a trail behind him, the same trail. Then: below, "NO WAY OUT." - he
sits down in the dead end, the exit three cells above him behind one hedge. Above, "?", a light bulb, a chalk X on
the hedge - one step back, the turn they both walked past, and out into the light. Below, the light comes through the
hedge next to him: "...IT WAS RIGHT THERE?"
"HE SAT DOWN / ONE TURN FROM THE EXIT."

    python3 stick/maze.py stick/one-turn.mp4
    ONLY_FRAMES=0,1.5,3.2,6,8.4,9.4,10.4,11.6,13,17 python3 stick/maze.py /tmp/mz
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
from perfect_wave import (MONO, clamp, env, font, lerp, lerp_pose, midi, mix_in, noise, out_back, out_cubic,  # noqa
                          prog, smooth, spaced, tone, write_wav)

W, H, FPS = 1080, 1920, 30
SR = 44100
BPM = 75
BEAT = 60 / BPM
BAR = 4 * BEAT
DUR = 6 * BAR                           # 19.2 s
NF = int(round(DUR * FPS))
XFADE = 0.5
INK = AJ.INK
PH, TOP_Y0, BOT_Y0 = AJ.PH, AJ.TOP_Y0, AJ.BOT_Y0
DOER, DOER_FAR, OT, OT_FAR = AJ.DOER, AJ.DOER_FAR, AJ.OT, AJ.OT_FAR
GOLD = (255, 214, 120)
S = 0.4                                 # the people are tokens on the map

# ---------------------------------------------------------------- the maze
COLS, ROWS = 9, 5
CELL = 98
MX0, MY0 = 22, 100
WALL = 22


def cxy(c, r):
    return MX0 + (c + 0.5) * CELL, MY0 + (r + 0.5) * CELL


PASS = set()


def link(a, b):
    PASS.add((a, b))
    PASS.add((b, a))


ROUTE = [(0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (4, 1), (5, 1), (6, 1), (6, 2), (7, 2), (7, 1), (7, 0), (8, 0)]
for a, b in zip(ROUTE, ROUTE[1:]):
    link(a, b)
for chain in ([(2, 2), (2, 1), (2, 0)],                                   # dead end A
              [(4, 2), (4, 3), (4, 4), (5, 4)],                           # dead end B
              [(7, 2), (8, 2), (8, 3)],                                   # dead end C, one turn past the way out
              [(0, 2), (0, 1), (1, 1), (1, 0), (0, 0)],
              [(3, 2), (3, 1), (3, 0), (4, 0), (5, 0), (6, 0)],
              [(1, 2), (1, 3), (0, 3), (0, 4), (1, 4), (2, 4), (2, 3), (3, 3), (3, 4)],
              [(5, 1), (5, 2), (5, 3), (6, 3), (6, 4), (7, 4), (8, 4)],
              [(6, 4), (7, 3)],
              [(8, 0), (8, 1)]):
    for a, b in zip(chain, chain[1:]):
        link(a, b)


def walls():
    segs = []
    for c in range(COLS):
        for r in range(ROWS):
            x0, y0 = MX0 + c * CELL, MY0 + r * CELL
            if c + 1 < COLS and ((c, r), (c + 1, r)) not in PASS:
                segs.append(((x0 + CELL, y0), (x0 + CELL, y0 + CELL)))
            if r + 1 < ROWS and ((c, r), (c, r + 1)) not in PASS:
                segs.append(((x0, y0 + CELL), (x0 + CELL, y0 + CELL)))
    X1, Y1 = MX0 + COLS * CELL, MY0 + ROWS * CELL
    # the outer hedge, with the way in (left of 0,2) and the way out (right of 8,0)
    segs += [((MX0, MY0), (X1, MY0)), ((MX0, Y1), (X1, Y1)),
             ((MX0, MY0), (MX0, MY0 + 2 * CELL)), ((MX0, MY0 + 3 * CELL), (MX0, Y1)),
             ((X1, MY0 + CELL), (X1, Y1))]
    return segs


SEGS = walls()
EXIT = (MX0 + COLS * CELL, MY0 + 0.5 * CELL)

# ---------------------------------------------------------------- the walk (both, together)
STEP = 0.3
PAUSE = 0.55
WALK = [("pt", (MX0 - 40, MY0 + 2.5 * CELL)), (0, 2), (1, 2), (2, 2), (2, 1), (2, 0), "bump", (2, 1), (2, 2), (3, 2),
        (4, 2), (4, 3), (4, 4), (5, 4), "bump", (4, 4), (4, 3), (4, 2), (4, 1), (5, 1), (6, 1), (6, 2), (7, 2), (8, 2),
        (8, 3), "bump"]


def build_track(seq, t0=0.0):
    """[(t, x, y)] keyframes; dead-end bumps as pauses."""
    keys, bumps = [], []
    t = t0
    for s in seq:
        if s == "bump":
            bumps.append(t)
            t += PAUSE
            keys.append((t, keys[-1][1], keys[-1][2]))
            continue
        if isinstance(s, tuple) and s and s[0] == "pt":
            x, y = s[1]
        else:
            x, y = cxy(*s)
        if keys:
            t += STEP
        keys.append((t, x, y))
    return keys, bumps


TRACK, BUMPS = build_track(WALK, 0.3)
T_C = BUMPS[-1]                          # both at dead end C
T_SPLIT = T_C + PAUSE
T_Q0, T_BULB, T_BULB1 = T_SPLIT + 0.05, T_SPLIT + 0.6, T_SPLIT + 1.15
T_CHALK0, T_CHALK1 = T_BULB1, T_BULB1 + 0.45
OUT_SEQ = [(8, 3), (8, 2), (7, 2), "look", (7, 1), (7, 0), (8, 0), ("pt", (EXIT[0] + 60, EXIT[1]))]


def build_out(t0):
    keys = []
    t = t0
    look = None
    for s in OUT_SEQ:
        if s == "look":
            look = t
            t += 0.45
            keys.append((t, keys[-1][1], keys[-1][2]))
            continue
        if isinstance(s, tuple) and s and s[0] == "pt":
            x, y = s[1]
        else:
            x, y = cxy(*s)
        if keys:
            t += STEP + 0.04
        keys.append((t, x, y))
    return keys, look


OUT, T_LOOK = build_out(T_CHALK1 + 0.05)
T_ESC = OUT[-2][0]                       # in the exit cell
T_OUT = OUT[-1][0]
T_SIT0, T_SIT1 = T_SPLIT + 0.2, T_SPLIT + 0.7
T_LIGHT = T_ESC + 0.3                    # below: the light behind the hedge
T_UP0, T_UP1 = T_LIGHT + 0.2, T_LIGHT + 0.7
T_L1, T_L2 = 14.2, 15.4
CPS = 16.0
LINE1, LINE2 = "HE SAT DOWN", "ONE TURN FROM THE EXIT."

BUB_BOTH = [(BUMPS[0] - 0.05, BUMPS[0] + 0.6, "DEAD END."), (BUMPS[1] - 0.05, BUMPS[1] + 0.6, "AGAIN?")]
BUB_TOP = []
BUB_BOT = [(T_SPLIT, T_SPLIT + 1.7, "NO WAY OUT."), (T_UP1, T_UP1 + 2.6, "...IT WAS RIGHT THERE?")]


def at(track, t):
    if t <= track[0][0]:
        return track[0][1], track[0][2], 0.0, 0.0
    for (t0, x0, y0), (t1, x1, y1) in zip(track, track[1:]):
        if t0 <= t < t1:
            u = (t - t0) / (t1 - t0)
            return lerp(x0, x1, u), lerp(y0, y1, u), x1 - x0, y1 - y0
    return track[-1][1], track[-1][2], 0.0, 0.0


def dead_ends(t, top):
    n = sum(1 for b in BUMPS if t >= b)
    return n


# ---------------------------------------------------------------- poses
STAND = PW.STAND
SIT = {"head": (10, -150), "neck": (4, -108), "el": (32, -76), "hl": (-6, -80), "er": (28, -72), "hr": (-10, -76),
       "kl": (62, -26), "fl": (92, 28), "kr": (56, -20), "fr": (86, 32)}
THINK = dict(STAND, er=(22, -70), hr=(18, -118), el=(-10, -60), hl=(-14, -12))
CHALK = dict(STAND, el=(40, -100), hl=(80, -110))
CHEER = PW.ARMS_UP
HANDS_HEAD = dict(STAND, el=(-34, -146), hl=(-10, -176), er=(34, -146), hr=(10, -176))


def person(t, top):
    """(pose, x, y(feet), facing)"""
    if t < T_SPLIT:
        x, y, dx, dy = at(TRACK, t)
        moving = abs(dx) + abs(dy) > 0
        f = 1 if dx >= 0 else -1
        return (AJ.walk(t * 9, STAND) if moving else STAND), x, y, f
    if top:
        if t < T_CHALK0:
            return THINK, *cxy(8, 3), 1
        if t < T_CHALK1:
            u = prog(t, T_CHALK0, T_CHALK1)
            p = dict(CHALK, hl=(80 + 18 * math.sin(u * 12), -110 + 14 * math.cos(u * 12)))
            return p, *cxy(8, 3), 1
        x, y, dx, dy = at(OUT, t)
        moving = abs(dx) + abs(dy) > 0
        f = 1 if dx >= 0 else -1
        if t >= T_ESC:
            k = smooth(prog(t, T_ESC, T_ESC + 0.25))
            return lerp_pose(AJ.walk(t * 9, STAND), CHEER, k), x, y, 1
        return (AJ.walk(t * 9, STAND) if moving else STAND), x, y, f
    cx, cy = cxy(8, 3)
    if t < T_UP0:
        k = smooth(prog(t, T_SIT0, T_SIT1))
        return lerp_pose(STAND, SIT, k), cx - 12 * k, cy + 6 * k, 1
    k = smooth(prog(t, T_UP0, T_UP1))
    return lerp_pose(SIT, HANDS_HEAD, k), cx - 12 * (1 - k), cy, -1


def trail_points(t, top):
    pts = []
    for (t0, x, y) in TRACK:
        if t0 <= t:
            pts.append((x, y))
    if t < T_SPLIT:
        x, y, _, _ = at(TRACK, t)
        pts.append((x, y))
        return pts
    if top and t >= T_CHALK1:
        for (t0, x, y) in OUT:
            if t0 <= t:
                pts.append((x, y))
        x, y, _, _ = at(OUT, t)
        pts.append((x, y))
    return pts


# ---------------------------------------------------------------- drawing
def build_ground():
    yy, xx = np.mgrid[0:PH, 0:W].astype(np.float32)
    img = np.zeros((PH, W, 3), np.float32) + np.array([40, 36, 30], np.float32)
    n = (np.sin(xx / 13) * np.sin(yy / 17) + np.sin((xx + yy) / 29)) * 4
    img += n[..., None]
    v = np.exp(-(((xx - 500) / 700) ** 2 + ((yy - 300) / 420) ** 2))
    img *= (0.7 + 0.45 * v)[..., None]
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(2)
    for _ in range(500):
        x, y = rng.uniform(0, W), rng.uniform(0, PH)
        c = int(rng.uniform(46, 66))
        d.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=(c + 6, c, c - 8, 255))
    # the hedges: a dark outline, the green, a lighter top
    for (a, b) in SEGS:
        d.line([a, b], fill=INK + (255,), width=WALL + 8)
    for (a, b) in SEGS:
        for p in (a, b):
            d.ellipse([p[0] - (WALL + 8) / 2, p[1] - (WALL + 8) / 2, p[0] + (WALL + 8) / 2, p[1] + (WALL + 8) / 2],
                      fill=INK + (255,))
    for (a, b) in SEGS:
        d.line([a, b], fill=(52, 112, 62, 255), width=WALL)
        for p in (a, b):
            d.ellipse([p[0] - WALL / 2, p[1] - WALL / 2, p[0] + WALL / 2, p[1] + WALL / 2], fill=(52, 112, 62, 255))
    for (a, b) in SEGS:
        d.line([(a[0] - 3, a[1] - 3), (b[0] - 3, b[1] - 3)], fill=(84, 150, 88, 255), width=6)
    for _ in range(300):
        (a, b) = SEGS[int(rng.uniform(0, len(SEGS)))]
        u = rng.uniform(0, 1)
        x, y = lerp(a[0], b[0], u) + rng.uniform(-6, 6), lerp(a[1], b[1], u) + rng.uniform(-6, 6)
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(70, 136, 76, 255))
    # the EXIT sign outside the way out
    ex, ey = EXIT
    d.rounded_rectangle([ex + 20, ey - 64, ex + 120, ey - 34], 5, fill=(40, 150, 80, 255), outline=INK + (255,), width=3)
    spaced(d, ex + 70, ey - 61, "EXIT", font("Inter-Bold.otf", 20), (255, 255, 255, 255), 4)
    return im


def exit_glow(im, t, k):
    ex, ey = EXIT
    gl = Image.new("RGBA", (520, 420), (0, 0, 0, 0))
    ImageDraw.Draw(gl).ellipse([160, 110, 360, 310], fill=GOLD + (int(min(255, 80 + 150 * k)),))
    gl = gl.filter(ImageFilter.GaussianBlur(40 + 20 * k))
    im.alpha_composite(gl, (int(ex - 260), int(ey - 210)))


def chalk_x(d, k):
    # on the hedge at the end of dead end C
    x0, y0 = MX0 + 8 * CELL + CELL / 2, MY0 + 4 * CELL
    s = 18
    a = int(255 * k)
    d.line([(x0 - s, y0 - s - 4), (x0 + s, y0 + s - 4)], fill=(250, 250, 250, a), width=5)
    if k > 0.5:
        d.line([(x0 + s, y0 - s - 4), (x0 - s, y0 + s - 4)], fill=(250, 250, 250, a), width=5)


def person_sprite(pts, body, far, facing):
    cv = AJ.Canvas(*PW.bbox_of(list(pts.values()), 60))
    AJ.draw_stick(cv, pts, body, far, facing, s=S)
    return cv.done()


def thought(d, t, head):
    if not (T_Q0 <= t < T_BULB1):
        return
    hx, hy = head
    bx, by = hx - 70, hy - 70
    sc = out_back(prog(t, T_Q0, T_Q0 + 0.2))
    a = int(255 * (1 - smooth(prog(t, T_BULB1 - 0.15, T_BULB1))))
    if sc < 0.05:
        return
    R = 34 * sc
    d.ellipse([hx - 30, hy - 36, hx - 20, hy - 26], fill=(242, 240, 234, a), outline=INK + (a,), width=2)
    d.ellipse([bx - R, by - R, bx + R, by + R], fill=(242, 240, 234, a), outline=INK + (a,), width=3)
    if t < T_BULB:
        spaced(d, bx, by - 22 * sc, "?", font("InterDisplay-Bold.otf", int(38 * sc)), INK + (a,), 0)
    else:
        k = out_back(prog(t, T_BULB, T_BULB + 0.2))
        r = 13 * k
        d.ellipse([bx - r, by - r - 4, bx + r, by + r - 4], fill=(255, 220, 90, a), outline=INK + (a,), width=3)
        d.rectangle([bx - 6 * k, by + r - 6, bx + 6 * k, by + r + 3], fill=(150, 150, 160, a), outline=INK + (a,), width=2)


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
        x = clamp(head[0] - spr.width / 2, 8, W - 8 - spr.width)
        y = clamp(head[1] - 40 - spr.height, 4, PH - spr.height - 4)
        im.alpha_composite(spr, (int(x), int(y)))


GROUND = None
FRAME0 = None


def panel(t, top):
    im = GROUND.copy()
    escaped = smooth(prog(t, T_ESC, T_ESC + 0.4)) if top else 0.0
    exit_glow(im, t, 0.4 + 0.15 * math.sin(t * 3) + 1.2 * escaped)
    d = ImageDraw.Draw(im)
    # below: the light from the way out comes down the corridor next to him
    if not top and t >= T_LIGHT:
        k = smooth(prog(t, T_LIGHT, T_LIGHT + 0.6))
        gl = Image.new("RGBA", (W, PH), (0, 0, 0, 0))
        g = ImageDraw.Draw(gl)
        x0, y0 = cxy(7, 0)
        x1, y1 = cxy(7, 2)
        g.rounded_rectangle([x0 - 36, y0 - 40, x1 + 36, y1 + 30], 20, fill=GOLD + (int(120 * k),))
        g.rounded_rectangle([x0 - 36, y0 - 40, EXIT[0] + 10, y0 + 36], 20, fill=GOLD + (int(120 * k),))
        gl = gl.filter(ImageFilter.GaussianBlur(18))
        im.alpha_composite(gl)
        d = ImageDraw.Draw(im)
    # trails
    tp = trail_points(t, top)
    col = (236, 238, 244) if top else (160, 162, 170)
    for (a, b) in zip(tp, tp[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = int(L / 16)
        for i in range(n):
            u = i / max(1, n)
            x, y = lerp(a[0], b[0], u), lerp(a[1], b[1], u)
            d.ellipse([x - 3, y + 18, x + 3, y + 24], fill=col + (150,))
    if top and t >= T_CHALK0:
        chalk_x(d, smooth(prog(t, T_CHALK0, T_CHALK1)))
    # the dead-end bumps: a little burst of leaves
    for b in BUMPS:
        if b <= t < b + 0.5:
            x, y, _, _ = at(TRACK, b)
            rng = np.random.default_rng(int(b * 100))
            u = (t - b) / 0.5
            for i in range(8):
                a = rng.uniform(0, 2 * math.pi)
                r = 18 + 40 * u
                d.ellipse([x + r * math.cos(a) - 3, y - 30 + r * math.sin(a) - 3, x + r * math.cos(a) + 3,
                           y - 30 + r * math.sin(a) + 3], fill=(90, 160, 90, int(255 * (1 - u))))
    pose, x, y, f = person(t, top)
    hip = (x, y - 113 * S + 16)
    if pose is SIT or (not top and t >= T_SIT0 and t < T_UP0):
        hip = (x, y - 37 * S + 10)
    pts = AJ.place(pose, hip, f, S)
    body, far = (DOER, DOER_FAR) if top else (OT, OT_FAR)
    alpha = 1.0
    if top and t >= OUT[-2][0]:
        alpha = 1 - smooth(prog(t, OUT[-2][0] + 0.1, OUT[-1][0]))
    spr, off = person_sprite(pts, body, far, f)
    if alpha < 0.999:
        spr.putalpha(spr.split()[3].point(lambda v: int(v * alpha)))
    if top:
        g = PW.glow_of(spr, 0.7 + escaped, 8, GOLD if escaped > 0.1 else (210, 228, 255))
        if alpha < 0.999:
            g.putalpha(g.split()[3].point(lambda v: int(v * alpha)))
        im.alpha_composite(g, off)
    im.alpha_composite(spr, off)
    d = ImageDraw.Draw(im)
    if top:
        thought(d, t, pts["head"])
        if T_LOOK and T_LOOK <= t < T_LOOK + 0.45:
            # he looks up the corridor: the turn they both walked past
            x0, y0 = cxy(7, 2)
            k = math.sin(math.pi * prog(t, T_LOOK, T_LOOK + 0.45))
            d.polygon([(x0 - 10, y0 - 40), (x0 + 10, y0 - 40), (x0, y0 - 64)], fill=(255, 230, 140, int(255 * k)))
    # counter
    n = dead_ends(t, top)
    bx, by = W - 162, PH - 100
    d.rounded_rectangle([bx, by, bx + 150, by + 88], 8, fill=(18, 20, 28, 230), outline=(90, 94, 104, 255), width=2)
    if top and escaped > 0.5:
        spaced(d, bx + 75, by + 10, "ESCAPED", font("Inter-SemiBold.otf", 20), (190, 194, 204, 255), 4)
        spaced(d, bx + 75, by + 36, "✓", font("Inter-Bold.otf", 40), AJ.GREEN + (255,), 0)
    else:
        spaced(d, bx + 75, by + 10, "DEAD ENDS", font("Inter-SemiBold.otf", 18), (190, 194, 204, 255), 3)
        spaced(d, bx + 75, by + 34, str(n), font(MONO, 42), (240, 240, 244, 255), 0)
    bubbles(im, t, BUB_BOTH + (BUB_TOP if top else BUB_BOT), pts["head"])
    return im


def frame(t):
    img = Image.new("RGBA", (W, H), (6, 6, 8, 255))
    img.alpha_composite(panel(t, True), (0, TOP_Y0))
    img.alpha_composite(panel(t, False), (0, BOT_Y0))
    d = ImageDraw.Draw(img)
    spaced(d, W / 2, 268, "DOER", font("Inter-SemiBold.otf", 40), (236, 238, 244, 255), 10)
    spaced(d, W / 2, BOT_Y0 + PH + 18, "OVERTHINKER", font("Inter-SemiBold.otf", 40), (200, 204, 214, 255), 10)
    spaced(d, W / 2, TOP_Y0 + PH + 34, "SAME MAZE", font("Inter-SemiBold.otf", 40), (206, 210, 220, 255), 9)
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
        for q in (0, 2):
            mix_in(mus, GS.keys(midi(mel[(b * 2 + q // 2) % len(mel)])), t0 + q * BEAT + 0.05, 0.04, 0.25)
    # soft steps on the gravel
    for (t0, x, y), (t1, _, _) in zip(TRACK, TRACK[1:]):
        if t1 - t0 > 0.2:
            mix_in(fx, noise(0.06, int(t0 * 100), lo=1500, hi=6000) * env(int(0.06 * SR), 0.003, 0.015), t0 + 0.05, 0.05)
    for (t0, x, y), (t1, _, _) in zip(OUT, OUT[1:]):
        if t1 - t0 > 0.2:
            mix_in(fx, noise(0.06, int(t0 * 100) + 3, lo=1500, hi=6000) * env(int(0.06 * SR), 0.003, 0.015), t0 + 0.05,
                   0.05, -0.3)
    # dead ends: a soft rustle into the hedge and a low note
    for i, b in enumerate(BUMPS):
        mix_in(fx, noise(0.3, 40 + i, lo=400, hi=4000) * env(int(0.3 * SR), 0.01, 0.08), b, 0.12)
        mix_in(fx, GS.keys(midi(50 - i), 0.6), b + 0.05, 0.05)
    # the idea, the chalk, the look, the way out
    for i, m in enumerate((84, 91)):
        mix_in(fx, GS.keys(midi(m), 1.2), T_BULB + i * 0.08, 0.06, -0.3)
    mix_in(fx, noise(0.4, 50, lo=2500, hi=8000) * env(int(0.4 * SR), 0.02, 0.1), T_CHALK0, 0.05, -0.3)
    mix_in(fx, GS.keys(midi(81), 0.8), T_LOOK, 0.05, -0.3)
    for i, m in enumerate((72, 76, 79, 84, 88)):
        mix_in(fx, GS.keys(midi(m), 1.6), T_ESC + i * 0.08, 0.06, -0.3)
    mix_in(fx, GS.pad(midi(38), 1.6, 0.05, 1.2), T_UP0, 0.12, 0.3)
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
    out = sys.argv[1] if len(sys.argv) > 1 else "one-turn.mp4"
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
