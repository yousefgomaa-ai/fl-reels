#!/usr/bin/env python3
"""THE HOURGLASS - "What if you could see everyone's time?" 22 s, night stage, licensed music, loops.

Everyone has a glowing hourglass above their head. The red-scarf hero walks a night street: an old man feeding
pigeons on a bench, smiling, with almost no sand left; a man shouting at a waiter over coffee, half his sand gone.
Home: his mother waits at the table under a warm lamp. He walks past with headphones on; her hand rises to speak and
falls. At his door he stops, turns slowly - her hourglass has a few grains left. The music drops to almost nothing.
He pulls off the headphones, goes back, sits, holds her. The last grain hangs in the air.
YOU CAN'T SEE IT. / BUT IT'S RUNNING.

Music: "Reunited" by Kevin MacLeod (incompetech.com), CC BY 4.0 - its swell (38 s) lands on the hug.

    python3 stick/hourglass.py stick/hourglass.mp4
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
import hq  # noqa
import compare as C  # noqa
from compare import ell, line, rrect, poly, figure, place, ik, FLOOR, K, W, H, INK, BODY  # noqa
from perfect_wave import clamp, env, font, lerp, lerp_pose, mix_in, noise, prog, smooth, tone, write_wav  # noqa

FPS = 30
SR = 44100
DUR = 22.0
NF = int(round(DUR * FPS))
SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
MUSIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "study", "music", "Reunited.mp3")
MUSIC_OFF = 22.0          # music time at video 0: its swell (37.6 s) lands on the hug (15.6 s)
STAND = PW.STAND
SC = [0.0, 3.2, 6.4, 9.2, 13.0, 15.5, DUR]
T_HUG = 15.6
GOLD = (250, 200, 110)
MOM = (222, 212, 206)


def scene_of(t):
    for i in range(6):
        if t < SC[i + 1]:
            return i, t - SC[i]
    return 5, t - SC[5]


def breathe(p, t, ph=0.0, amp=2.5):
    p = dict(p)
    b = amp * math.sin(t * 2.2 + ph)
    p["head"] = (p["head"][0], p["head"][1] + b)
    p["neck"] = (p["neck"][0], p["neck"][1] + b * 0.6)
    return p


def grounded(pose, x, s, feet=FLOOR):
    return (x, feet - max(pose["fl"][1], pose["fr"][1]) * s)


def reach(pts, s, hand, target, sgn=1):
    side = hand[-1]
    pts = dict(pts)
    pts["h" + side] = target
    pts["e" + side] = ik(pts["neck"], target, 42 * s, 40 * s, sgn)
    return pts


# ---------------------------------------------------------------- the hourglass
def hourglass(layer, d, head, s, frac, t, seed=0, hang=0.0, alpha=1.0, glow=1.0):
    """frac = sand left on top (0..1). drawn above the head"""
    hx, hy = head
    cx, cy = hx, hy - 62 * s - 34
    w, h = 26 * s + 8, 34 * s + 10
    a = int(255 * alpha)
    gl = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    ell(ImageDraw.Draw(gl), cx, cy, w * 2.2, h * 1.6, GOLD + (int(70 * glow * alpha),))
    layer.alpha_composite(gl.filter(ImageFilter.GaussianBlur(14 * K)))
    # sand: top triangle shrinking towards the neck, bottom heap growing
    top_h = h * frac
    if top_h > 0.5:
        tw = w * frac
        poly(d, [(cx - tw * 0.9, cy - top_h + 2), (cx + tw * 0.9, cy - top_h + 2), (cx, cy)], GOLD + (a,))
    bot = 1 - frac
    if bot > 0.02:
        bh = h * bot * 0.85
        poly(d, [(cx - w * 0.95, cy + h - 3), (cx + w * 0.95, cy + h - 3), (cx + w * 0.5 * (1 - bot * 0.4), cy + h - bh),
                 (cx - w * 0.5 * (1 - bot * 0.4), cy + h - bh)], GOLD + (a,))
    if 0.0 < frac < 1.0 and hang <= 0:
        line(d, [(cx, cy), (cx, cy + h - 4 - h * bot * 0.8)], (255, 226, 150, a), 2)
    if hang > 0:
        # the last grain, hanging in the air
        gy = cy + 6 + 10 * hang
        ell(d, cx, gy, 3.2, 3.2, (255, 236, 170, a))
        ell(d, cx, gy, 9, 9, (255, 220, 140, int(60 * alpha)))
    # glass + frame
    for sgn in (-1, 1):
        d.line([((cx - w) * K, (cy + sgn * h) * K), ((cx - 2) * K, cy * K), ((cx + 2) * K, cy * K),
                ((cx + w) * K, (cy + sgn * h) * K)], fill=(200, 220, 255, int(170 * alpha)), width=int(2.5 * K))
        rrect(d, (cx - w - 6, cy + sgn * h - 4, cx + w + 6, cy + sgn * h + 4), 2, (150, 110, 60, a))


# ---------------------------------------------------------------- props
def bench(d, x):
    rrect(d, (x - 120, FLOOR - 74, x + 120, FLOOR - 62), 3, (110, 80, 56, 255), outline=INK + (255,), w=2)
    rrect(d, (x - 120, FLOOR - 150, x + 120, FLOOR - 136), 3, (110, 80, 56, 255), outline=INK + (255,), w=2)
    for xx in (x - 100, x + 100):
        line(d, [(xx, FLOOR - 62), (xx, FLOOR)], (40, 40, 46, 255), 7)


def pigeon(d, x, t, ph):
    peck = max(0.0, math.sin(t * 5 + ph)) ** 3
    ell(d, x, FLOOR - 14, 16, 10, (90, 92, 104, 255), outline=INK + (255,), w=1.5)
    hx, hy = x + 14, FLOOR - 24 + 14 * peck
    ell(d, hx, hy, 7, 7, (110, 112, 126, 255), outline=INK + (255,), w=1.5)
    poly(d, [(hx + 6, hy), (hx + 12, hy + 2), (hx + 6, hy + 3)], (230, 180, 80, 255))


def table_home(d, x):
    rrect(d, (x - 170, FLOOR - 124, x + 170, FLOOR - 110), 4, (120, 86, 58, 255), outline=INK + (255,), w=2)
    for xx in (x - 150, x + 150):
        line(d, [(xx, FLOOR - 110), (xx, FLOOR)], (80, 58, 40, 255), 9)
    for dx in (-70, 70):
        ell(d, x + dx, FLOOR - 130, 40, 9, (236, 236, 240, 255), outline=INK + (255,), w=2)
    ell(d, x - 70, FLOOR - 136, 22, 6, (200, 120, 60, 255))
    ell(d, x + 70, FLOOR - 136, 22, 6, (200, 120, 60, 255))
    # the lamp
    line(d, [(x, FLOOR - 720), (x, FLOOR - 470)], (40, 40, 46, 255), 3)
    poly(d, [(x - 60, FLOOR - 470), (x + 60, FLOOR - 470), (x + 30, FLOOR - 510), (x - 30, FLOOR - 510)],
         (70, 58, 40, 255), outline=INK + (255,), w=2)
    ell(d, x, FLOOR - 466, 18, 9, (255, 226, 160, 255))


def chair(d, x, f=1):
    line(d, [(x - 34, FLOOR - 66), (x + 34, FLOOR - 66)], (90, 66, 46, 255), 8)
    line(d, [(x - 30, FLOOR - 66), (x - 30, FLOOR)], (70, 50, 36, 255), 6)
    line(d, [(x + 30, FLOOR - 66), (x + 30, FLOOR)], (70, 50, 36, 255), 6)
    bx = x - 34 * f
    line(d, [(bx, FLOOR - 66), (bx, FLOOR - 190)], (90, 66, 46, 255), 7)


def door(d, x, open_=0.0):
    rrect(d, (x - 70, FLOOR - 330, x + 70, FLOOR), 4, (30, 26, 24, 255), outline=(80, 70, 60, 255), w=4)
    w = 130 * (1 - 0.7 * open_)
    rrect(d, (x - 65, FLOOR - 325, x - 65 + w, FLOOR - 2), 3, (76, 56, 40, 255), outline=INK + (255,), w=2)
    ell(d, x - 65 + w - 16, FLOOR - 160, 6, 6, (200, 170, 100, 255))


def window(d, x):
    rrect(d, (x - 110, FLOOR - 560, x + 110, FLOOR - 330), 6, (18, 26, 46, 255), outline=(80, 70, 60, 255), w=6)
    line(d, [(x, FLOOR - 560), (x, FLOOR - 330)], (80, 70, 60, 255), 5)
    line(d, [(x - 110, FLOOR - 445), (x + 110, FLOOR - 445)], (80, 70, 60, 255), 5)
    rng = np.random.default_rng(3)
    for _ in range(14):
        sx, sy = rng.uniform(x - 100, x + 100), rng.uniform(FLOOR - 550, FLOOR - 340)
        ell(d, sx, sy, 1.4, 1.4, (220, 228, 255, 200))


def headphones(d, head, s):
    hx, hy = head
    d.arc([(hx - 30 * s) * K, (hy - 36 * s) * K, (hx + 30 * s) * K, (hy + 20 * s) * K], 190, 350, fill=(30, 30, 36, 255),
          width=int(7 * s * K))
    ell(d, hx - 26 * s, hy + 2 * s, 9 * s, 13 * s, (30, 30, 36, 255))
    ell(d, hx + 26 * s, hy + 2 * s, 9 * s, 13 * s, (30, 30, 36, 255))


def bun(d, head, s, f):
    hx, hy = head
    ell(d, hx - f * 24 * s, hy - 18 * s, 13 * s, 13 * s, (120, 110, 104, 255), outline=INK + (255,), w=2)


def cane(d, hand, s):
    hx, hy = hand
    line(d, [(hx, hy), (hx + 6 * s, FLOOR)], (120, 84, 50, 255), 6 * s)


SIT = {"head": (8, -146), "neck": (5, -104), "el": (24, -58), "hl": (46, -40), "er": (28, -60), "hr": (52, -42),
       "kl": (56, -2), "fl": (58, 62), "kr": (52, 2), "fr": (52, 64)}
SIT_SMILE = dict(SIT, head=(-4, -150), neck=(-2, -106))
SIT_FEED = dict(SIT_SMILE, er=(40, -70), hr=(76, -70))


# ---------------------------------------------------------------- scenes
S_HERO = 1.2


def street_people(stage, d, t, c):
    """passers-by in the world, each with an hourglass"""
    people = [(700, 0.95, -1, 0.62, 1), (1500, 1.0, 1, 0.35, 2), (2300, 0.92, -1, 0.8, 3), (3100, 1.0, 1, 0.5, 4)]
    for wx, s, f, frac, seed in people:
        x = wx - c + (40 * t * f)
        if -150 < x < W + 150:
            wp = breathe(AJ.walk(t * 7 + seed, STAND), t, seed)
            pts = place(wp, grounded(wp, x, s), f, s)
            figure(stage, pts, s, light=(0.4, -0.9), body=(176, 180, 196), alpha=0.85, blur=1.2)
            hourglass(stage, d, pts["head"], s, frac - 0.01 * t, t, seed, alpha=0.8)


def hero_walk(stage, d, t, x, f=1, phone=True, s=S_HERO):
    wp = AJ.walk(t * 8.5, STAND)
    if phone:
        wp = dict(wp, er=(24, -76), hr=(36, -110), head=(14, -144))
    pts = place(wp, grounded(wp, x, s), f, s)
    figure(stage, pts, s, light=(-0.4, -0.9), scarf=True, back=-f)
    if phone:
        rrect(d, (pts["hr"][0] - 8, pts["hr"][1] - 14, pts["hr"][0] + 8, pts["hr"][1] + 14), 3, (18, 18, 24, 255))
        rrect(d, (pts["hr"][0] - 6, pts["hr"][1] - 11, pts["hr"][0] + 6, pts["hr"][1] + 11), 2, (150, 190, 255, 255))
    headphones(d, pts["head"], s)
    hourglass(stage, d, pts["head"], s, 0.97, t, 0)
    return pts


def s0(stage, d, st, T):
    c = 130 * st
    C.street(d, c)
    street_people(stage, d, st, c)
    hero_walk(stage, d, st, 440)
    return [], ((440, 1.0),), (lerp(480, 440, smooth(st / 3)), 1080, lerp(1.25, 1.12, smooth(st / 3))), 0.0


def s1(stage, d, st, T):
    c = 130 * (st + 3.2)
    C.street(d, c)
    bx = 760 - 40 * st
    bench(d, bx)
    for j, (dx, ph) in enumerate(((-120, 0.0), (-60, 1.3), (160, 2.2))):
        pigeon(d, bx + dx, T, ph)
    p = breathe(lerp_pose(SIT_SMILE, SIT_FEED, 0.5 + 0.5 * math.sin(st * 2.5)), T, 1.0)
    p = dict(p, head=(p["head"][0] + 18, p["head"][1] + 10), neck=(p["neck"][0] + 12, p["neck"][1] + 6))
    pts = place(p, (bx - 10, FLOOR - 66 * 1.1), 1, 1.1)
    figure(stage, pts, 1.1, light=(0.4, -0.9), body=(196, 196, 204))
    cane(d, (bx - 70, FLOOR - 120), 1.1)
    hourglass(stage, d, pts["head"], 1.1, 0.06, T, 5)
    # crumbs falling from his hand
    for j in range(4):
        u = ((st * 1.5 + j / 4) % 1.0)
        ell(d, pts["hr"][0] + 6, pts["hr"][1] + 140 * u, 2, 2, (220, 200, 160, int(200 * (1 - u))))
    hp = hero_walk(stage, d, st, lerp(260, 420, st / 3.2))
    return [], ((bx, 1.0), (380, 0.6)), (lerp(500, 600, smooth(st / 3.2)), 1080, 1.18), 0.0


def s2(stage, d, st, T):
    c = 130 * (st + 6.4)
    C.street(d, c)
    tx = 720
    rrect(d, (tx - 70, FLOOR - 120, tx + 70, FLOOR - 108), 4, (90, 70, 56, 255), outline=INK + (255,), w=2)
    line(d, [(tx, FLOOR - 108), (tx, FLOOR)], (60, 46, 36, 255), 8)
    # spilled coffee
    rrect(d, (tx - 10, FLOOR - 140, tx + 12, FLOOR - 120), 3, (240, 240, 244, 255), outline=INK + (255,), w=1.5)
    ell(d, tx + 30, FLOOR - 112, 30, 5, (110, 70, 40, 255))
    wave = math.sin(st * 14)
    bp = dict(STAND, head=(18, -148), neck=(10, -106), el=(40, -120), hl=(70 + 10 * wave, -160 - 10 * wave),
              er=(30, -90), hr=(64, -110 + 12 * wave))
    pts = place(bp, grounded(STAND, tx - 140, 1.15), 1, 1.15)
    figure(stage, pts, 1.15, light=(0.4, -0.9), body=(200, 186, 186))
    hourglass(stage, d, pts["head"], 1.15, 0.48, T, 6)
    wp = dict(STAND, head=(-14, -136), neck=(-8, -100), er=(-30, -80), hr=(-56, -84))
    wpts = place(wp, grounded(STAND, tx + 140, 1.1), -1, 1.1)
    figure(stage, wpts, 1.1, light=(0.4, -0.9), body=(186, 190, 200))
    rrect(d, (wpts["hr"][0] - 30, wpts["hr"][1] - 6, wpts["hr"][0] + 30, wpts["hr"][1]), 2, (180, 184, 196, 255))
    hourglass(stage, d, wpts["head"], 1.1, 0.7, T, 7)
    hero_walk(stage, d, st, lerp(220, 380, st / 2.8))
    return [], ((tx - 60, 1.0), (300, 0.5)), (600, 1080, 1.2), ("shake", 0.0)


HOME_TABLE = 600
MOM_X = HOME_TABLE + 100


def mom(stage, d, st, T, raise_k=0.0, lean=0.0, frac=0.05, hang=0.0):
    p = breathe(dict(SIT, head=(14, -142), neck=(8, -102)), T, 0.5, 2.0)
    if raise_k > 0:
        p = lerp_pose(p, dict(p, el=(-10, -96), hl=(-40, -120)), raise_k)
    if lean > 0:
        p = lerp_pose(p, dict(p, head=(-26, -138), neck=(-16, -100), el=(-30, -70), hl=(-60, -80)), lean)
    pts = place(p, (MOM_X, FLOOR - 66 * 1.15), -1, 1.15)
    figure(stage, pts, 1.15, light=(-0.3, -0.95), body=MOM)
    bun(d, pts["head"], 1.15, -1)
    hourglass(stage, d, pts["head"], 1.15, frac, T, 9, hang=hang)
    return pts


def home(stage, d):
    window(d, 230)
    door(d, 80)
    door(d, 980)
    table_home(d, HOME_TABLE)
    chair(d, MOM_X + 30, -1)
    chair(d, HOME_TABLE - 130, 1)


def s3(stage, d, st, T):
    """he walks past her with headphones; her hand rises - and falls"""
    home(stage, d)
    raise_k = smooth(prog(st, 1.2, 1.8)) * (1 - smooth(prog(st, 2.6, 3.4)))
    mom(stage, d, st, T, raise_k=raise_k, frac=0.06 - 0.004 * st)
    x = lerp(60, 930, smooth(prog(st, 0.2, 3.7)))
    hero_walk(stage, d, st, x)
    return [], ((HOME_TABLE, 1.0),), (lerp(560, 640, smooth(st / 3.8)), 1090, 1.15), 0.4


def s4(stage, d, st, T):
    """at his door he stops; a breath; he turns slowly; her hourglass: a few grains"""
    home(stage, d)
    mpts = mom(stage, d, st, T, frac=0.045 - 0.006 * st)
    s = S_HERO
    turn = smooth(prog(st, 0.9, 1.7))
    p = breathe(dict(STAND, head=(lerp(14, -10, turn), -148), er=(24, -76), hr=(36, -110)), T, 0.0, 3.0)
    pts = place(p, grounded(STAND, 930, s), 1 if turn < 0.5 else -1, s)
    figure(stage, pts, s, light=(-0.4, -0.9), scarf=True, back=-1 if turn < 0.5 else 1)
    headphones(d, pts["head"], s)
    hourglass(stage, d, pts["head"], s, 0.97, T, 0)
    rrect(d, (pts["hr"][0] - 8, pts["hr"][1] - 14, pts["hr"][0] + 8, pts["hr"][1] + 14), 3, (18, 18, 24, 255))
    # camera: on him, then slowly into her hourglass
    k = smooth(prog(st, 1.4, 2.4))
    hgx, hgy = mpts["head"][0], mpts["head"][1] - 62 * 1.15 - 34
    fx = lerp(800, hgx, k)
    fy = lerp(1060, hgy + 20, k)
    z = lerp(1.25, 3.0, k)
    return [], ((HOME_TABLE, 1.0), (930, 0.7)), (fx, fy, z), 0.4


def s5(stage, d, st, T):
    """the headphones drop, he goes back, sits, holds her; the last grain hangs"""
    home(stage, d)
    s = S_HERO
    hang = smooth(prog(st, 1.4, 2.2))
    if st < 0.5:
        p = dict(STAND, head=(-10, -148), el=(-20, -120), hl=(-10, -160), er=(20, -120), hr=(10, -160))
        pts = place(p, grounded(STAND, 930, s), -1, s)
        mpts = mom(stage, d, st, T, frac=0.03)
        figure(stage, pts, s, light=(-0.4, -0.9), scarf=True, back=1)
        headphones(d, pts["head"], s)
        hourglass(stage, d, pts["head"], s, 0.97, T, 0)
    elif st < 1.4:
        u = smooth(prog(st, 0.5, 1.3))
        x = lerp(930, MOM_X + 150, u)
        rp = C.run_pose((st - 0.5) * 12, 0.6)
        pts = place(rp, grounded(rp, x, s), -1, s)
        mpts = mom(stage, d, st, T, frac=0.025, lean=smooth(prog(st, 1.0, 1.4)) * 0.3)
        figure(stage, pts, s, light=(-0.4, -0.9), scarf=True, back=1)
        hourglass(stage, d, pts["head"], s, 0.97, T, 0)
    else:
        lean = smooth(prog(st, 1.4, 2.0))
        mpts = mom(stage, d, st, T, frac=0.0, lean=lean, hang=hang)
        k = smooth(prog(st, 1.3, 1.8))
        hug = {"head": (-30, -136), "neck": (-22, -98), "el": (-56, -96), "hl": (-96, -100), "er": (-50, -72),
               "hr": (-90, -76), "kl": (-50, 6), "fl": (-52, 66), "kr": (-46, 2), "fr": (-46, 64)}
        p = breathe(lerp_pose(dict(STAND), hug, k), T, 2.0, 2.0)
        hip = (lerp(MOM_X + 150, MOM_X + 110, k), lerp(grounded(STAND, 0, s)[1], FLOOR - 66 * s, k))
        pts = place(p, hip, 1, s)
        pts = reach(pts, s, "hl", (mpts["neck"][0] + 6, mpts["neck"][1] + 20), -1)
        pts = reach(pts, s, "hr", (mpts["neck"][0] - 20, mpts["neck"][1] + 6), -1)
        figure(stage, pts, s, light=(-0.4, -0.9), scarf=True, back=1)
        hourglass(stage, d, pts["head"], s, 0.97, T, 0)
    # the headphones on the floor
    if st >= 0.3:
        u = prog(st, 0.3, 0.55)
        y = lerp(FLOOR - 300, FLOOR - 10, u * u)
        d.arc([(900 - 26) * K, (y - 20) * K, (900 + 26) * K, (y + 20) * K], 180, 360, fill=(30, 30, 36, 255),
              width=int(6 * K))
    pull = smooth(prog(st, 2.6, 5.5))
    lines = [(3.2, "YOU CAN'T SEE IT."), (3.9, "BUT IT'S RUNNING.")]
    return lines, ((MOM_X + 40, 1.0),), (lerp(MOM_X + 50, 560, pull), lerp(1020, 1080, pull), lerp(1.55, 1.15, pull)), \
        lerp(0.4, 1.0, smooth(prog(st, 1.4, 3.0)))


SCENES = [s0, s1, s2, s3, s4, s5]


def grade(im, g):
    if abs(g) < 0.02:
        return im
    warm = np.array([1.12, 1.01, 0.82], np.float32)
    cold = np.array([0.86, 0.95, 1.14], np.float32)
    gain = 1 + (warm - 1) * g if g > 0 else 1 + (cold - 1) * (-g)
    a = np.asarray(im.convert("RGB"), np.float32)
    return Image.fromarray(np.clip(a * gain, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def frame(t):
    sc, st = scene_of(t)
    stage = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(stage)
    lines, spots, camf, extra = SCENES[sc](stage, d, st, t)
    base = C.stage_bg(tuple((float(round(x / 20) * 20), round(float(s_), 1)) for x, s_ in spots)).copy()
    C.dust(ImageDraw.Draw(base), t, spots, seed=sc + 1)
    tp = stage.crop((0, 0, W * K, FLOOR * K))
    refl = tp.transpose(Image.FLIP_TOP_BOTTOM).crop((0, 0, W * K, (H - FLOOR) * K))
    refl = refl.resize((W * K // 4, (H - FLOOR) * K // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
    refl = refl.resize((W * K, (H - FLOOR) * K), Image.BILINEAR)
    fade = np.linspace(0.3, 0.0, (H - FLOOR) * K, dtype=np.float32)[:, None]
    refl.putalpha(Image.fromarray((np.asarray(refl.split()[3], np.float32) * fade).astype(np.uint8)))
    base.alpha_composite(refl, (0, FLOOR * K))
    g = stage.resize((W * K // 8, H * K // 8), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6))
    gl = Image.new("RGBA", g.size, (210, 215, 235, 0))
    gl.putalpha(g.split()[3].point(lambda v: int(v * 0.35)))
    base.alpha_composite(gl.resize(stage.size, Image.BILINEAR))
    base.alpha_composite(stage)
    fx, fy, z = camf
    z *= 1.05
    dx, dy = z * (W / 2 - fx), z * (H / 2 - fy)
    im = hq.camera(base, z, dx * K, dy * K).resize((W, H), Image.LANCZOS)
    g = extra if isinstance(extra, float) else -0.5
    if sc <= 2:
        g = -0.5
    im = grade(im, g)
    # soft dips between the street scenes and home
    for cut in SC[1:5]:
        if cut - 0.18 <= t < cut + 0.18:
            k = 1 - abs(t - cut) / 0.18
            im = Image.blend(im, Image.new("RGBA", im.size, (0, 0, 0, 255)), 0.7 * k)
    C.caption(im, lines, st)
    if t < 2.7:
        k = 1 - smooth(prog(t, 2.4, 2.7))
        dq = ImageDraw.Draw(im)
        fb = font(SERIF_B, 62)
        for i, ln in enumerate(("WHAT IF YOU COULD SEE", "EVERYONE'S TIME?")):
            y = 300 + i * 82
            PW.spaced(dq, W / 2 + 3, y + 4, ln, fb, (0, 0, 0, int(160 * k)), 2)
            PW.spaced(dq, W / 2, y, ln, fb, (246, 240, 226, int(255 * k)), 2)
    return np.asarray(im.convert("RGB"))


def render(i):
    return frame(i / FPS).tobytes()


# ---------------------------------------------------------------- sound: the licensed track + quiet effects
def load_music():
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(MUSIC_OFF), "-t", str(DUR), "-i", MUSIC, "-f", "f32le",
                          "-ac", "2", "-ar", str(SR), "-"], capture_output=True).stdout
    m = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    n = int(DUR * SR)
    out = np.zeros((n, 2))
    out[:min(n, len(m))] = m[:n]
    tt = np.arange(n) / SR
    g = np.ones(n)
    g *= np.minimum(1, tt / 0.25)                                       # soft start
    duck0, duck1 = SC[4] + 0.6, SC[5] + 0.05                          # the realization: almost silence
    g *= 1 - 0.85 * np.clip((tt - duck0) / 0.4, 0, 1) * np.clip((duck1 + 0.3 - tt) / 0.3, 0, 1)
    g *= np.clip((DUR - tt) / 0.6, 0, 1) * 0.85 + 0.15 * np.clip((DUR - tt) / 0.6, 0, 1)
    return out * g[:, None]


def audio():
    n = int(DUR * SR)
    fx = np.zeros((n, 2))
    mus = load_music()
    # street: footsteps, distant traffic hum, pigeons, the shouting man's muffled anger
    bed = noise(SC[3], 3, lo=80, hi=600)[:int(SC[3] * SR)] * 0.5
    mix_in(fx, bed, 0.0, 0.03)
    t0 = 0.1
    while t0 < SC[3]:
        mix_in(fx, tone(150, 0.06, (1, 0.5), a=0.002, d=0.02), t0, 0.025, -0.1)
        t0 += 0.38
    for j in range(6):
        mix_in(fx, tone(420, 0.12, (1, 0.6), a=0.01, d=0.06, sweep=360), SC[1] + 0.4 + j * 0.45, 0.02, 0.4)
    ang = noise(2.4, 5, lo=200, hi=900)[:int(2.4 * SR)] * (np.sin(np.linspace(0, 24, int(2.4 * SR))) > 0)
    mix_in(fx, ang, SC[2] + 0.2, 0.05, 0.3)
    # home: a clock ticking; the heartbeat as he turns; the headphones hit the floor
    t0 = SC[3]
    while t0 < SC[5] + 1.4:
        mix_in(fx, tone(2200, 0.02, (1,), a=0.0005, d=0.008), t0, 0.03)
        t0 += 0.5
    for j in range(4):
        for k2, dt in enumerate((0.0, 0.17)):
            mix_in(fx, tone(48, 0.2, (1, 0.5), a=0.003, d=0.08), SC[4] + 0.8 + j * 0.5 + dt, 0.16 - 0.06 * k2)
    mix_in(fx, tone(110, 0.2, (1, 0.5), a=0.001, d=0.06) + 0.3 * noise(0.2, 8, lo=300, hi=3000)[:int(0.2 * SR)] *
           env(int(0.2 * SR), 0.001, 0.03), SC[5] + 0.55, 0.12, 0.3)
    # the last grain: a tiny glass chime
    mix_in(fx, tone(2637, 1.2, (1, 2.76), a=0.002, d=0.6), SC[5] + 2.2, 0.03)
    x = mus + fx
    m = int(0.2 * SR)
    k = np.linspace(0, 1, m)[:, None]
    x[-m:] = x[-m:] * (1 - k) + x[:m] * k
    x /= max(1.0, np.abs(x).max() / 0.9)
    return x


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "hourglass.mp4"
    only = os.environ.get("ONLY_FRAMES")
    if only:
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
    with Pool(os.cpu_count()) as pool:
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
