#!/usr/bin/env python3
"""WILL IT FIT? - split screen, bright, one huge symbol (a couch jammed in a door). 16 s, loops.

Frame 0: a big yellow band "WILL IT FIT?"; in each panel a big couch is jammed against a doorway (84 in couch, 36 in
door). Top (orange) keeps ramming it sideways - the obviously wrong way - and the wall cracks a little more each time.
Bottom (blue) thinks, takes the legs off, stands the couch on its end (34 in < 36 in) and pushes it in... it sticks.
The answer is held to the last 1.5 s: blue's couch slides in with a THUNK - FITS!; orange's couch goes through the
wall - NEW DOOR. Then it loops.

    python3 stick/couch.py stick/couch.mp4
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
DUR = 16.0
NF = int(round(DUR * FPS))
XFADE = 0.5
K = hq.K
BOLD = hq.BOLD
MUSIC = "guitar_g"

TITLE_H = 300
PX0 = 20
PWD, PHT = 1040, 760
PANEL_Y = [310, 1080]
FL = 690                       # floor line in the panel
DOOR = (510, 690, 210, FL)     # opening x0, x1, y0, y1  (36 in wide)
DCX = 600
S = 1.5
HIPY = FL - 113 * S
ORG = (236, 112, 18)
BLU = (24, 118, 222)
COUCH_C = (64, 158, 120)
INK = (40, 34, 40)
WALL = (247, 239, 225)
YEL = (255, 210, 60)
GREEN = (30, 170, 80)
RED = (220, 50, 50)

T_JAM = 1.1
RAMS = [3.3, 4.9, 6.5, 8.0, 9.5, 11.0, 12.4, 13.5]
T_THINK = 2.0
T_LEGS = [3.7, 4.0, 4.3, 4.6]
T_TIP0, T_TIP1 = 5.0, 6.3
T_PUSH0, T_STUCK = 7.0, 9.3
T_REVEAL = 14.3
T_STAMP = 14.55


# ---------------------------------------------------------------- the couch
def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


COUCH_PARTS = [  # (polygon in local coords, origin bottom-centre, colour shade)
    (rect(-210, -70, 210, -12), 0.85),
    (rect(-172, -170, 172, -96), 1.0),
    (rect(-172, -100, 172, -66), 1.12),
    (rect(-212, -128, -162, -12), 0.92),
    (rect(162, -128, 212, -12), 0.92),
]
LEGS = [rect(-192, -12, -176, 6), rect(176, -12, 192, 6), rect(-120, -12, -106, 6), rect(106, -12, 120, 6)]


def shade(c, k):
    return tuple(int(clamp(v * k, 0, 255)) for v in c)


def draw_couch(d, x, y, sc, ang, legs=4, alpha=255):
    """x, y: bottom centre in panel px (1x); ang in radians around the couch centre."""
    piv = (0, -85)
    y = y - 125 * sc * abs(math.sin(ang))        # keep its lowest point on the floor when it stands on end

    def tf(q):
        rx, ry = q[0] - piv[0], q[1] - piv[1]
        c, s = math.cos(ang), math.sin(ang)
        return (x + (piv[0] + rx * c - ry * s) * sc) * K, (y + (piv[1] + rx * s + ry * c) * sc) * K
    for j, poly in enumerate(LEGS[:legs]):
        d.polygon([tf(q) for q in poly], fill=(90, 64, 44, alpha))
    for poly, k in COUCH_PARTS:
        pts = [tf(q) for q in poly]
        d.polygon(pts, fill=shade(COUCH_C, k) + (alpha,), outline=INK + (alpha,), width=int(3 * K))


def couch_width_in(ang):
    """visible width in inches, for the tape label"""
    return 84 * abs(math.cos(ang)) + 34 * abs(math.sin(ang))


# ---------------------------------------------------------------- people
STAND = PW.STAND
PUSH = dict(STAND, head=(16, -146), neck=(12, -106), el=(46, -84), hl=(86, -88), er=(42, -80), hr=(82, -84),
            kl=(-16, 56), fl=(-40, 113), kr=(14, 56), fr=(10, 113))
STRAIN = dict(PUSH, head=(30, -136), neck=(22, -98), kl=(-34, 52), fl=(-70, 108))
THINK = dict(STAND, el=(30, -90), hl=(14, -136), er=(14, -64), hr=(4, -88))
CROUCH = {"head": (40, -96), "neck": (30, -64), "el": (60, -40), "hl": (90, -10), "er": (56, -36), "hr": (86, -6),
          "kl": (30, 10), "fl": (0, 113), "kr": (40, 20), "fr": (20, 113)}
LIFT = dict(STAND, el=(40, -140), hl=(70, -190), er=(36, -136), hr=(66, -186))
FALL = dict(PUSH, head=(50, -120), neck=(36, -86))


def person(d, pts, col, alpha=255):
    w = 11
    for b0, b1 in [("neck", "hip"), ("neck", "el"), ("el", "hl"), ("neck", "er"), ("er", "hr"), ("hip", "kl"),
                   ("kl", "fl"), ("hip", "kr"), ("kr", "fr")]:
        (x0, y0), (x1, y1) = pts[b0], pts[b1]
        d.line([x0 * K, y0 * K, x1 * K, y1 * K], fill=col + (alpha,), width=int(w * K))
        for x, y in ((x0, y0), (x1, y1)):
            r = w * K / 2
            d.ellipse([x * K - r, y * K - r, x * K + r, y * K + r], fill=col + (alpha,))
    hx, hy = pts["head"]
    r = 27 * K
    d.ellipse([hx * K - r, hy * K - r, hx * K + r, hy * K + r], fill=col + (alpha,))


# ---------------------------------------------------------------- states
def last_ram(t):
    done = [r for r in RAMS if t >= r]
    return (done[-1] if done else None), len(done)


def orange_state(t):
    """couch (x, sc, ang, jolt), person (pose, hip, ang), cracks"""
    lr, n = last_ram(t)
    if t < T_JAM:
        sc = lerp(1.0, 0.93, smooth(prog(t, 0, T_JAM)))
        cx = DCX
        pose, hx = PUSH, DCX - 300 * sc
        return (cx, sc, 0.0), (pose, hx, 0.0), 0
    if t < T_REVEAL:
        sc = 0.93
        jolt = 0.0
        # back up and ram, again and again
        nxt = [r for r in RAMS if r > t]
        hx0 = DCX - 300 * sc
        hx = hx0
        pose = STRAIN if t < RAMS[0] - 0.9 else PUSH
        if nxt and nxt[0] - t < 0.9:
            u = prog(t, nxt[0] - 0.9, nxt[0])
            back = math.sin(math.pi * min(1, u * 1.4)) if u < 0.55 else 0
            hx = hx0 - 150 * (math.sin(math.pi * u / 0.55) if u < 0.55 else 0) + (0 if u < 0.55 else 0)
            if u >= 0.55:
                k = prog(u, 0.55, 1.0)
                hx = lerp(hx0 - 40, hx0, k)
                pose = AP.run(t * 18, 1.2)
            elif u > 0.1:
                pose = AJ.walk(t * 10, STAND)
        if lr is not None and t - lr < 0.25:
            jolt = 10 * (1 - (t - lr) / 0.25)
            pose = STRAIN
        return (DCX + jolt, sc - 0.01 * jolt / 10, 0.0), (pose, hx, 0.0), n
    # the reveal: the wall gives way
    k = smooth(prog(t, T_REVEAL, T_REVEAL + 0.5))
    return (DCX + 30 * k, lerp(0.93, 0.8, k), 0.25 * k), (FALL, lerp(DCX - 279, DCX - 150, k), 1.1 * k), 99


def blue_state(t):
    """couch (x, sc, ang, legs), person (pose, hip x, ang, alpha)"""
    legs = 4 - sum(1 for tl in T_LEGS if t >= tl)
    if t < T_JAM:
        sc = lerp(1.0, 0.93, smooth(prog(t, 0, T_JAM)))
        return (DCX, sc, 0.0, legs), (PUSH, DCX - 300 * sc, 0.0)
    if t < T_LEGS[0] - 0.3:
        k = smooth(prog(t, T_THINK, T_THINK + 0.3))
        return (DCX, 0.93, 0.0, legs), (lerp_pose(PUSH, THINK, k), DCX - 279, 0.0)
    if t < T_TIP0:
        return (DCX, 0.93, 0.0, legs), (CROUCH, DCX - 279 + 20, 0.0)
    if t < T_PUSH0:
        k = smooth(prog(t, T_TIP0, T_TIP1))
        ang = -math.pi / 2 * k
        return (DCX, 0.93, ang, legs), (LIFT if t < T_TIP1 else STAND, DCX - 279 + 40 * k, 0.0)
    if t < T_REVEAL:
        sc = lerp(0.93, 0.87, smooth(prog(t, T_PUSH0, T_STUCK)))
        wig = 0.0
        if t >= T_STUCK:
            wig = 0.008 * math.sin(t * 22) * (0.5 + 0.5 * math.sin(t * 2.3))
        edge = DCX - 85 * sc
        pose = PUSH if (t < T_STUCK or int(t * 1.5) % 2 == 0) else STRAIN
        return (DCX, sc + wig, -math.pi / 2, 0), (pose, edge - 84, 0.0)
    k = smooth(prog(t, T_REVEAL, T_REVEAL + 0.35))
    sc = lerp(0.87, 0.72, k)
    return (DCX, sc, -math.pi / 2, 0), (dict(STAND, el=(-30, -130), hl=(-44, -180), er=(30, -130), hr=(44, -180))
                                        if t > T_REVEAL + 0.4 else PUSH, DCX - 85 * 0.87 - 84 + 30 * k, 0.0)


# ---------------------------------------------------------------- panel art
def wall_layer(broken=False):
    """the wall with a hole (the doorway, or the smashed hole), at 2x, transparent where you can see through"""
    lay = Image.new("RGBA", (PWD * K, PHT * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rectangle([0, 0, PWD * K, FL * K], fill=WALL + (255,))
    for x in range(0, PWD, 70):
        d.line([x * K, 0, x * K, FL * K], fill=(236, 226, 210, 255), width=int(3 * K))
    d.rectangle([0, (FL - 26) * K, PWD * K, FL * K], fill=(255, 255, 255, 255), outline=(210, 200, 190, 255))
    # a framed picture on the left
    d.rectangle([90 * K, 210 * K, 230 * K, 320 * K], fill=(120, 190, 230, 255), outline=(150, 110, 70, 255),
                width=int(8 * K))
    d.polygon([(100 * K, 312 * K), (150 * K, 250 * K), (190 * K, 300 * K), (222 * K, 312 * K)], fill=(70, 150, 90, 255))
    x0, x1, y0, y1 = DOOR
    if not broken:
        d.rectangle([(x0 - 24) * K, (y0 - 24) * K, (x1 + 24) * K, y1 * K], fill=(176, 124, 80, 255))
        d.rectangle([x0 * K, y0 * K, x1 * K, y1 * K], fill=(0, 0, 0, 0))
        d.line([(x0 - 24) * K, (y0 - 24) * K, (x1 + 24) * K, (y0 - 24) * K], fill=INK + (255,), width=int(3 * K))
    else:
        rng = np.random.default_rng(3)
        pts = []
        for j in range(26):
            a = math.pi + j / 25 * math.pi
            r = 330 + rng.uniform(-30, 40)
            pts.append(((DCX + 40 + r * math.cos(a) * 1.05) * K, (FL + r * 0.95 * math.sin(a)) * K))
        pts = [((DCX - 330) * K, FL * K)] + pts + [((DCX + 400) * K, FL * K)]
        d.polygon(pts, fill=(0, 0, 0, 0))
        # bricks showing at the edge of the hole
        for (px, py) in pts[1:-1:2]:
            d.rectangle([px - 18 * K, py - 9 * K, px + 18 * K, py + 9 * K], fill=(196, 96, 70, 255),
                        outline=(140, 60, 40, 255))
    return lay


BG = None
WALLS = None
FRAME0 = None


def make_bg():
    im = Image.new("RGBA", (PWD * K, PHT * K), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    # the room behind the door: warm and darker
    d.rectangle([0, 0, PWD * K, FL * K], fill=(92, 74, 66, 255))
    d.rectangle([(DCX - 140) * K, 180 * K, (DCX + 160) * K, FL * K], fill=(122, 98, 84, 255))
    d.ellipse([(DCX - 40) * K, 240 * K, (DCX + 60) * K, 300 * K], fill=(255, 220, 160, 200))
    # wooden floor
    d.rectangle([0, FL * K, PWD * K, PHT * K], fill=(198, 150, 104, 255))
    for y in range(FL + 16, PHT, 22):
        d.line([0, y * K, PWD * K, y * K], fill=(176, 130, 88, 255), width=int(2 * K))
    return im


def cracks(d, n, seed):
    """cracks spreading on the wall around the door frame, n = rams so far"""
    rng = np.random.default_rng(seed)
    x0, x1, y0, y1 = DOOR
    starts = [(x0 - 24, 330), (x1 + 24, 300), (x0 - 24, 520), (x1 + 24, 560), (DCX, y0 - 24), (x0 - 24, 230),
              (x1 + 24, 420), (DCX + 40, y0 - 24)]
    for j in range(min(n, len(starts))):
        sx, sy = starts[j]
        dirx = -1 if sx < DCX else 1
        pts = [(sx, sy)]
        for k in range(5 + j):
            px, py = pts[-1]
            pts.append((px + dirx * rng.uniform(14, 34), py + rng.uniform(-26, 26)))
        d.line([(x * K, y * K) for x, y in pts], fill=INK + (255,), width=int(3 * K))
        bx, by = pts[2]
        d.line([bx * K, by * K, (bx + dirx * 30) * K, (by - 30) * K], fill=INK + (255,), width=int(2 * K))


def tape(d, x0, x1, y, label, col, alpha=255):
    d.line([x0 * K, y * K, x1 * K, y * K], fill=INK + (alpha,), width=int(3 * K))
    for x in (x0, x1):
        d.line([x * K, (y - 12) * K, x * K, (y + 12) * K], fill=INK + (alpha,), width=int(3 * K))
    f = font(BOLD, int(30 * K))
    tw = f.getlength(label)
    cx = (x0 + x1) / 2 * K
    d.rounded_rectangle([cx - tw / 2 - 14 * K, (y - 22) * K, cx + tw / 2 + 14 * K, (y + 22) * K], int(10 * K),
                        fill=YEL + (alpha,), outline=INK + (alpha,), width=int(2 * K))
    d.text((cx - tw / 2, (y - 20) * K), label, font=f, fill=col + (alpha,))


def panel(t, top):
    base = BG.copy()
    lay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    tops = []
    if top:
        (cx, sc, ang), (pose, hx, pang), n = orange_state(t)
        inside = t >= T_REVEAL
        legs = 4
        col = ORG
    else:
        (cx, sc, ang, legs), (pose, hx, pang) = blue_state(t)
        inside = t >= T_PUSH0 + 0.4
        n = 0
        col = BLU
    broken = top and t >= T_REVEAL
    # couch behind the wall (going through) or in front of it
    if inside:
        draw_couch(d, cx, FL - 6, sc, ang, legs)
        base.alpha_composite(lay)
        lay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
    base.alpha_composite(WALLS[1] if broken else WALLS[0])
    if not broken:
        cracks(d, n, 7)
    tape(d, DOOR[0], DOOR[1], DOOR[2] - 58, "36 in", INK)
    # shadow + couch in front
    if not inside:
        d.ellipse([(cx - 230 * sc) * K, (FL - 14) * K, (cx + 230 * sc) * K, (FL + 14) * K], fill=(0, 0, 0, 50))
        draw_couch(d, cx, FL - 6, sc, ang, legs)
    # the couch width tape (not while it rotates)
    if not inside and abs(ang) < 0.05 and not top or (top and t < T_REVEAL):
        w = 210 * sc
        tape(d, cx - w, cx + w, FL + 40, "84 in", RED)
    if not top and T_TIP1 <= t < T_REVEAL:
        w = 85 * sc
        tape(d, cx - w, cx + w, FL + 40, "34 in", GREEN)
    # the legs he took off lie on the floor
    if not top:
        for j, tl in enumerate(T_LEGS):
            if t >= tl:
                lx = 240 + j * 34
                d.rectangle([lx * K, (FL + 4) * K, (lx + 16) * K, (FL + 22) * K], fill=(90, 64, 44, 255))
    # the person
    pts = PW.place(pose, (hx, HIPY), 1, pang) if False else AJ.place(pose, (hx, HIPY), 1, S, pang)
    person(d, pts, col)
    # sweat while straining
    if top and T_JAM < t < T_REVEAL:
        hx_, hy_ = pts["head"]
        for j in range(2):
            ph = (t * 1.6 + j * 0.5) % 1
            sx, sy = hx_ - 30 - 10 * j, hy_ - 10 + 50 * ph
            d.ellipse([(sx - 6) * K, (sy - 9) * K, (sx + 6) * K, (sy + 9) * K], fill=(120, 190, 255, int(255 * (1 - ph))))
    # thinking dots
    if not top and T_THINK <= t < T_LEGS[0] - 0.3:
        hx_, hy_ = pts["head"]
        for j in range(3):
            if t > T_THINK + 0.2 * j:
                r = 7 + 4 * j
                d.ellipse([(hx_ + 40 + 22 * j - r) * K, (hy_ - 40 - 22 * j - r) * K, (hx_ + 40 + 22 * j + r) * K,
                           (hy_ - 40 - 22 * j + r) * K], fill=(255, 255, 255, 255), outline=INK + (255,),
                          width=int(2 * K))
    # impact bursts on every ram
    lr, _ = last_ram(t)
    if top and lr is not None and t - lr < 0.25 and t < T_REVEAL:
        k = (t - lr) / 0.25
        for j in range(8):
            a = j * 0.785
            r0, r1 = 30 + 60 * k, 60 + 100 * k
            bx, by = cx - 205 * sc, FL - 90
            d.line([(bx + r0 * math.cos(a)) * K, (by + r0 * math.sin(a)) * K, (bx + r1 * math.cos(a)) * K,
                    (by + r1 * math.sin(a)) * K], fill=INK + (int(255 * (1 - k)),), width=int(4 * K))
    # the wall explodes
    if broken and t < T_REVEAL + 1.2:
        rng = np.random.default_rng(9)
        u = t - T_REVEAL
        for j in range(26):
            vx, vy = rng.uniform(-420, 420), rng.uniform(-520, -160)
            px, py = DCX + vx * u, 360 + vy * u + 900 * u * u
            if py < PHT:
                s = rng.uniform(10, 22)
                c = (196, 96, 70) if j % 2 else WALL
                d.rectangle([(px - s) * K, (py - s * 0.5) * K, (px + s) * K, (py + s * 0.5) * K], fill=c + (255,),
                            outline=INK + (255,))
        for j in range(12):
            r = 40 + 400 * u
            a = j * 0.52
            d.ellipse([(DCX + r * math.cos(a) * 0.6 - 30) * K, (400 + r * math.sin(a) * 0.4 - 30) * K,
                       (DCX + r * math.cos(a) * 0.6 + 30) * K, (400 + r * math.sin(a) * 0.4 + 30) * K],
                      fill=(220, 210, 200, int(160 * max(0, 1 - u))))
    base.alpha_composite(lay)
    # stamps
    if t >= T_STAMP:
        p = hq.Panel(Image.new("RGBA", base.size, (0, 0, 0, 0)))
        p.tops = []
        AP.stamp(p, t, T_STAMP, PWD * 0.5, 150, "NEW DOOR" if top else "FITS!", RED if top else GREEN)
        for l_, pos in p.tops:
            base.alpha_composite(l_.filter(ImageFilter.GaussianBlur(8 * K)), pos)
            base.alpha_composite(l_, pos)
    im = hq.downsample(base, PWD, PHT)
    ev = [r for r in RAMS] if top else [T_LEGS[0], T_TIP1]
    ev = ev + [T_REVEAL, 0.0]
    dx, dy = hq.shake(t, ev, 10 if top else 6)
    im = hq.camera(im, 1.0 + 0.06 * prog(t, 0, T_REVEAL), dx, dy)
    ImageDraw.Draw(im).rounded_rectangle([1, 1, PWD - 2, PHT - 2], 16, outline=(col if True else INK) + (255,),
                                         width=6)
    return im


def frame(t):
    img = Image.new("RGBA", (W, H), (34, 32, 38, 255))
    # the question band
    band = Image.new("RGBA", (W * K, TITLE_H * K), YEL + (255,))
    bd = ImageDraw.Draw(band)
    kk = 1 + 0.05 * max(0, math.sin(t * 6)) * (1 if t < T_JAM else 0) + 0.08 * hq.pop(t, T_REVEAL, 0.25) * \
        (1 if t < T_REVEAL + 0.3 else 0)
    f = font(BOLD, int(118 * K * kk))
    s = "WILL IT FIT?"
    tw = sum(f.getlength(c) for c in s) + 6 * K * (len(s) - 1)
    x = W * K / 2 - tw / 2
    y = TITLE_H * K / 2 - 74 * K * kk
    for c in s:
        bd.text((x + 5 * K, y + 6 * K), c, font=f, fill=(0, 0, 0, 90))
        bd.text((x, y), c, font=f, fill=INK + (255,))
        x += f.getlength(c) + 6 * K
    img.alpha_composite(band.resize((W, TITLE_H), Image.LANCZOS), (0, 0))
    img.alpha_composite(panel(t, True), (PX0, PANEL_Y[0]))
    img.alpha_composite(panel(t, False), (PX0, PANEL_Y[1]))
    rgb = np.asarray(img.convert("RGB"))
    if T_REVEAL <= t < T_REVEAL + 0.12:
        rgb = np.clip(rgb.astype(np.float32) + 50 * (1 - (t - T_REVEAL) / 0.12), 0, 255).astype(np.uint8)
    return rgb


def init_worker():
    global BG, WALLS
    BG = make_bg()
    WALLS = (wall_layer(False), wall_layer(True))


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
def bam(fx, at, g=0.3, seed=1):
    mix_in(fx, tone(62, 0.45, (1, 0.6, 0.3), a=0.001, d=0.18, sweep=40), at, g)
    mix_in(fx, noise(0.3, seed, lo=150, hi=2500) * env(int(0.3 * SR), 0.001, 0.08), at, g * 0.6)


def crack(fx, at, g=0.12, seed=2):
    for j in range(4):
        mix_in(fx, noise(0.04, seed * 10 + j, lo=2000, hi=9000) * env(int(0.04 * SR), 0.0005, 0.012), at + j * 0.03,
               g, 0.3)


def audio():
    n = int(DUR * SR)
    fx = np.zeros((n, 2))
    mus = music.score(MUSIC, DUR, t_end=T_REVEAL - 0.1, t_warm=T_REVEAL + 0.4, t_line=T_REVEAL + 0.6, start=0.0,
                      loud=1.15)
    # hook: both couches thud into the doors
    bam(fx, 0.0, 0.32, 3)
    bam(fx, T_JAM, 0.22, 4)
    mix_in(fx, noise(1.1, 5, lo=100, hi=900) * np.linspace(0.3, 1, int(1.1 * SR)), 0.0, 0.05)     # scrape
    for j, r in enumerate(RAMS):
        mix_in(fx, noise(0.5, 30 + j, lo=200, hi=2000) * np.linspace(0, 1, int(0.5 * SR)) ** 2, r - 0.5, 0.05, -0.3)
        bam(fx, r, 0.2 + 0.015 * j, 10 + j)
        crack(fx, r + 0.05, 0.08 + 0.01 * j, 20 + j)
    # blue: thinking ding, legs unscrewed (squeaks + drops), tipping creak + thump, slide, stuck wiggles
    mix_in(fx, music.music_box(midi(84), 0.8), T_THINK + 0.3, 0.05, 0.3)
    for tl in T_LEGS:
        mix_in(fx, tone(900, 0.18, (1, 0.5), a=0.01, d=0.08, sweep=1400), tl - 0.2, 0.03, 0.3)
        mix_in(fx, tone(300, 0.15, (1, 0.6, 0.3), a=0.001, d=0.05), tl, 0.06, 0.3)
    mix_in(fx, tone(160, 1.2, (1, 0.6, 0.4), a=0.2, d=0.6, sweep=110), T_TIP0, 0.05, 0.3)
    bam(fx, T_TIP1, 0.16, 6)
    mix_in(fx, noise(2.2, 7, lo=120, hi=800) * env(int(2.2 * SR), 0.1, 1.0), T_PUSH0, 0.05, 0.3)
    tt = T_STUCK
    while tt < T_REVEAL:
        mix_in(fx, tone(140, 0.12, (1, 0.5), a=0.005, d=0.05), tt, 0.04, 0.3)
        tt += 0.45
    # suspense: a heartbeat before the reveal
    for j in range(5):
        for k2, dt in enumerate((0.0, 0.18)):
            mix_in(fx, tone(48, 0.2, (1, 0.5), a=0.003, d=0.08), T_REVEAL - 1.8 + j * 0.36 + dt, 0.16 - 0.06 * k2)
    # the reveal: THUNK + chime for blue, the wall blowing out for orange
    mix_in(fx, tone(90, 0.4, (1, 0.5), a=0.001, d=0.12), T_REVEAL, 0.3, 0.3)
    for j, m in enumerate((72, 76, 79, 84)):
        mix_in(fx, music.marimba(midi(m), 1.0), T_REVEAL + 0.12 + 0.07 * j, 0.09, 0.3)
    bam(fx, T_REVEAL, 0.4, 8)
    mix_in(fx, noise(1.4, 9, lo=80, hi=6000) * env(int(1.4 * SR), 0.002, 0.5), T_REVEAL, 0.3, -0.3)
    for j in range(10):
        mix_in(fx, tone(180 + 40 * (j % 4), 0.1, (1, 0.5), a=0.001, d=0.04), T_REVEAL + 0.25 + j * 0.06, 0.05, -0.3)
    for t0 in (T_STAMP, T_STAMP + 0.05):
        mix_in(fx, tone(70, 0.4, (1, 0.5), a=0.002, d=0.2) + 0.3 * noise(0.4, int(t0 * 100), lo=400, hi=5000) *
               env(int(0.4 * SR), 0.002, 0.1), t0, 0.15)
    x = mus + fx
    m = int(XFADE * SR)
    k = np.linspace(0, 1, m)[:, None]
    x[-m:] = x[-m:] * (1 - k) + x[:m] * k
    x /= max(1.0, np.abs(x).max() / 0.9)
    return x


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "couch.mp4"
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
