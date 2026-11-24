#!/usr/bin/env python3
"""WOULD YOU PRESS IT? - a big red button under a spotlight, $1,000,000 on the sign. 20 s, split screen, loops.

Top: PRESSES (the red-scarf hero) - runs to it and presses, again and again; money rains, the pile grows to $6M -
and with every press he ages (25 -> 85: hunch, grey, a cane). He ends up alone on top of the pile.
Bottom: READS FIRST - bends to read the small plate under the button, shakes his head, walks away into the dark,
the camera follows him to a warm table where two friends wait; he sits with them. $0, AGE 25.
16 s: the top camera dives into the plate: EACH PRESS = 10 YEARS OF YOUR LIFE. The old man reaches for the button
again. YOU CAN EARN MONEY BACK. / NOT TIME.

    python3 stick/button.py stick/button.mp4
"""
import math
import os
import subprocess
import sys
import tempfile
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perfect_wave as PW  # noqa
import ai_job as AJ  # noqa
import hq  # noqa
import compare as C  # noqa
from compare import ell, line, rrect, poly, figure, place, ik, FLOOR, K, W, H, INK, BODY  # noqa
from perfect_wave import clamp, env, font, lerp, lerp_pose, midi, mix_in, noise, prog, smooth, tone, write_wav  # noqa

FPS = 30
SR = 44100
DUR = 20.0
NF = int(round(DUR * FPS))
SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SERIF = C.SERIF
STAND = PW.STAND
HEAD_H = 250
PH = 760
PANEL_Y = [HEAD_H, HEAD_H + PH + 20]
BAND0 = FLOOR - 600                      # the slice of the stage a panel shows
BTN_X = 560
BTN_TOP = FLOOR - 200
PRESSES = [0.9, 2.6, 4.2, 5.7, 7.1, 8.4]
T_SIT = 9.6
T_REVEAL0, T_REVEAL1 = 15.8, 17.9
T_LINES = 17.9
RED = (214, 40, 48)
GOLD = (246, 196, 92)
GREEN = (90, 170, 100)


def n_press(t):
    return sum(1 for p in PRESSES if t >= p)


def age_of(t):
    return 25 + 10 * n_press(t)


def aged(pose, a):
    p = dict(pose)
    p["head"] = (p["head"][0] + 26 * a, p["head"][1] + 16 * a)
    p["neck"] = (p["neck"][0] + 18 * a, p["neck"][1] + 8 * a)
    for k in ("el", "hl", "er", "hr"):
        x, y = p[k]
        p[k] = (x + 14 * a, y + 6 * a)
    return p


def grounded(pose, x, s, feet=FLOOR):
    return (x, feet - max(pose["fl"][1], pose["fr"][1]) * s)


def reach(pts, s, hand, target, sgn=1):
    side = hand[-1]
    pts = dict(pts)
    pts["h" + side] = target
    pts["e" + side] = ik(pts["neck"], target, 42 * s, 40 * s, sgn)
    return pts


# ---------------------------------------------------------------- props
def pedestal(d, layer, t, pressed_k, x=BTN_X, plate=True):
    rrect(d, (x - 70, BTN_TOP, x + 70, FLOOR), 6, (34, 34, 40, 255), outline=INK + (255,), w=3)
    rrect(d, (x - 84, BTN_TOP - 16, x + 84, BTN_TOP + 4), 6, (52, 52, 60, 255), outline=INK + (255,), w=3)
    dip = 12 * pressed_k
    gl = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    ell(ImageDraw.Draw(gl), x, BTN_TOP - 30, 120, 70, (255, 60, 60, int(60 + 120 * pressed_k)))
    layer.alpha_composite(gl.filter(ImageFilter.GaussianBlur(24 * K)))
    d.chord([(x - 58) * K, (BTN_TOP - 60 + dip) * K, (x + 58) * K, (BTN_TOP + 34 + dip) * K], 180, 360,
            fill=RED + (255,), outline=INK + (255,), width=3 * K)
    ell(d, x - 20, BTN_TOP - 36 + dip, 18, 8, (255, 150, 150, 230))
    if plate:
        rrect(d, (x - 50, FLOOR - 120, x + 50, FLOOR - 84), 4, (160, 150, 120, 255), outline=INK + (255,), w=2)
        for j in range(3):
            line(d, [(x - 40, FLOOR - 112 + j * 10), (x + 40 - 18 * (j == 2), FLOOR - 112 + j * 10)],
                 (70, 60, 40, 255), 2)


def sign(d, layer, x=BTN_X, y=FLOOR - 470, a=1.0):
    gl = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    rrect(ImageDraw.Draw(gl), (x - 210, y - 60, x + 210, y + 60), 20, (90, 220, 120, int(80 * a)))
    layer.alpha_composite(gl.filter(ImageFilter.GaussianBlur(26 * K)))
    rrect(d, (x - 190, y - 52, x + 190, y + 52), 16, (12, 30, 18, int(255 * a)), outline=(120, 240, 150, int(255 * a)),
          w=4)
    f = font(SERIF_B, 64 * K)
    s = "$1,000,000"
    d.text((x * K - f.getlength(s) / 2, (y - 40) * K), s, font=f, fill=(170, 255, 190, int(255 * a)))
    line(d, [(x, y + 52), (x, BTN_TOP - 70)], (60, 64, 76, int(255 * a)), 3)


def bill(d, x, y, ang, a=255, sc=1.0):
    c, s_ = math.cos(ang), math.sin(ang)
    pts = [(-30, -13), (30, -13), (30, 13), (-30, 13)]
    poly(d, [(x + (px * c - py * s_) * sc, y + (px * s_ + py * c) * sc) for px, py in pts], (120, 196, 120, a),
         outline=(30, 80, 40, a), w=2)
    ell(d, x, y, 6 * sc, 6 * sc, (60, 140, 70, a))


def money_pile(d, millions, cx=800):
    """bricks of cash stacked in a pyramid; returns the top y"""
    n = int(round(millions * 7))
    if n <= 0:
        return FLOOR
    bw, bh = 46, 22
    base = int(math.ceil((math.sqrt(8 * n + 1) - 1) / 2))
    row, placed, y = 0, 0, FLOOR
    top = FLOOR
    while placed < n:
        cnt = max(1, base - row)
        x0 = cx - cnt * bw / 2
        for j in range(cnt):
            if placed >= n:
                break
            x = x0 + j * bw
            rrect(d, (x + 2, y - bh, x + bw - 2, y), 3, (110, 186, 110, 255), outline=(30, 80, 40, 255), w=2)
            line(d, [(x + bw / 2 - 6, y - bh), (x + bw / 2 - 6, y)], (220, 230, 200, 255), 4)
            placed += 1
        top = y - bh
        y -= bh
        row += 1
    return top


def cane(d, hand, s):
    hx, hy = hand
    line(d, [(hx, hy), (hx + 6 * s, FLOOR)], (120, 84, 50, 255), 6 * s)


def table(d, x):
    rrect(d, (x - 150, FLOOR - 120, x + 150, FLOOR - 106), 4, (110, 80, 56, 255), outline=INK + (255,), w=2)
    line(d, [(x - 130, FLOOR - 106), (x - 130, FLOOR)], (70, 50, 36, 255), 8)
    line(d, [(x + 130, FLOOR - 106), (x + 130, FLOOR)], (70, 50, 36, 255), 8)
    for j, dx in enumerate((-80, 0, 80)):
        rrect(d, (x + dx - 18, FLOOR - 150, x + dx + 18, FLOOR - 120), 4, (240, 200, 120, 255), outline=INK + (255,), w=2)
    line(d, [(x, FLOOR - 560), (x, FLOOR - 400)], (40, 40, 46, 255), 3)
    poly(d, [(x - 40, FLOOR - 400), (x + 40, FLOOR - 400), (x + 20, FLOOR - 430), (x - 20, FLOOR - 430)],
         (70, 60, 40, 255), outline=INK + (255,), w=2)
    ell(d, x, FLOOR - 396, 14, 8, (255, 230, 160, 255))


SIT = {"head": (8, -146), "neck": (5, -104), "el": (24, -58), "hl": (46, -40), "er": (28, -60), "hr": (52, -42),
       "kl": (56, -2), "fl": (58, 62), "kr": (52, 2), "fr": (52, 64)}


# ---------------------------------------------------------------- the two panels (stage coords, full 1080x1920 stage)
def top_scene(stage, d, t):
    n = n_press(t)
    a = clamp((age_of(t) - 25) / 60)
    s = 1.25 - 0.08 * a
    body = tuple(int(lerp(c0, c1, a)) for c0, c1 in zip(BODY, (166, 168, 176)))
    pressed = 0.0
    for p0 in PRESSES:
        if p0 - 0.15 <= t < p0 + 0.25:
            pressed = max(pressed, 1 - abs(t - p0) / 0.25)
    sign(d, stage, a=1.0)
    pile_top = money_pile(d, n)
    pedestal(d, stage, t, pressed)
    # falling bills after each press
    for p0 in PRESSES:
        if p0 <= t < p0 + 1.4:
            u = t - p0
            rng = np.random.default_rng(int(p0 * 10))
            for j in range(18):
                x = 760 + rng.uniform(-170, 170) + 30 * math.sin(u * 4 + j)
                y = FLOOR - 540 + rng.uniform(0, 60) + 380 * u
                if y < FLOOR - 10:
                    bill(d, x, y, u * rng.uniform(-5, 5) + j, int(255 * min(1, (1.4 - u) * 2)))
    # him
    if t < 0.8:
        x = lerp(150, 440, smooth(t / 0.8))
        rp = C.run_pose(t * 15, 0.8)
        pts = place(rp, grounded(rp, x, s), 1, s)
        figure(stage, pts, s, light=(0.6, -0.8), scarf=True)
        return
    if t < T_SIT:
        reach_k = pressed
        dp = aged(dict(STAND, head=(14, -148)), a)
        pts = place(dp, grounded(STAND, 440, s), 1, s)
        btn = (BTN_X - 20, BTN_TOP - 40 + 12 * pressed)
        rest = (pts["neck"][0] + 30 * s, pts["neck"][1] + 70 * s)
        tgt = (lerp(rest[0], btn[0], reach_k), lerp(rest[1], btn[1], reach_k))
        pts = reach(pts, s, "hr", tgt, 1)
        figure(stage, pts, s, light=(0.6, -0.8), body=body, scarf=True)
        if a > 0.7:
            cane(d, pts["hl"], s)
        return
    # sitting on top of the pile, old and alone; at the end he reaches for the button again
    k = smooth(prog(t, T_SIT, T_SIT + 0.6))
    hip = (lerp(440, 800, k), lerp(grounded(STAND, 440, s)[1], pile_top - 20, k))
    sp = aged(dict(SIT, head=(22, -134)), a)
    pts = place(sp, hip, -1, s)
    if t >= T_LINES:
        u = smooth(prog(t, T_LINES, T_LINES + 1.2))
        pts = reach(pts, s, "hl", (lerp(pts["hl"][0], BTN_X + 80, u), lerp(pts["hl"][1], BTN_TOP - 60, u)), -1)
    figure(stage, pts, s, light=(0.4, -0.9), body=body, scarf=True, back=1)
    cane(d, pts["hr"], s)


def bottom_scene(stage, d, t, c):
    s = 1.25
    sign(d, stage, x=BTN_X - c)
    pedestal(d, stage, t, 0.0, x=BTN_X - c)
    table(d, -520 - c)
    # two friends waiting at the table
    for j, (fx, f) in enumerate(((-640, 1), (-400, -1))):
        bob = 4 * math.sin(t * 6 + j) if t > 7.6 else 0
        sp = dict(SIT, head=(8, -146 + bob))
        pts = place(sp, (fx - c, FLOOR - 66 * s * 0.98), f, s * 0.95)
        figure(stage, pts, s * 0.95, light=(0.5, -0.8), body=(206, 200, 190))
    if t < 1.0:
        x = lerp(150, 430, smooth(t))
        wp = AJ.walk(t * 9, STAND)
        pts = place(wp, grounded(wp, x - c, s), 1, s)
    elif t < 4.2:
        k = smooth(prog(t, 1.0, 1.5))
        bend = dict(STAND, head=(46, -126), neck=(32, -92), er=(40, -50), hr=(56, -24), el=(30, -46), hl=(46, -20))
        pts = place(lerp_pose(STAND, bend, k), grounded(STAND, 430 - c, s), 1, s)
    elif t < 5.0:
        k = smooth(prog(t, 4.2, 4.5))
        sh = 10 * math.sin((t - 4.5) * 24) if t > 4.5 else 0
        pts = place(dict(STAND, head=(sh, -150)), grounded(STAND, 430 - c, s), 1, s)
    elif t < 7.6:
        u = smooth(prog(t, 5.0, 7.4))
        wp = AJ.walk(t * 9, STAND)
        pts = place(wp, grounded(wp, lerp(430, -520, u) - c, s), -1, s)
    else:
        k = smooth(prog(t, 7.6, 8.0))
        pts = place(dict(SIT, head=(8, -146 + 4 * math.sin(t * 6 + 2))), (-520 - c, lerp(grounded(STAND, 0, s)[1],
                                                                                         FLOOR - 66 * s * 0.98, k)),
                    1, s)
    figure(stage, pts, s, light=(0.5, -0.8))


def bottom_cam(t):
    """world scroll of the bottom panel: follows him to the table"""
    return lerp(0, -1060, smooth(prog(t, 5.0, 7.6)))


# ---------------------------------------------------------------- compose
def grade(im, g):
    if abs(g) < 0.02:
        return im
    warm = np.array([1.12, 1.01, 0.82], np.float32)
    cold = np.array([0.84, 0.95, 1.16], np.float32)
    gain = 1 + (warm - 1) * g if g > 0 else 1 + (cold - 1) * (-g)
    a = np.asarray(im.convert("RGB"), np.float32)
    if g < 0:
        m = a.mean(axis=2, keepdims=True)
        a = a * (1 + 0.25 * g) + m * (-0.25 * g)
    return Image.fromarray(np.clip(a * gain, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def render_panel(t, top):
    stage = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(stage)
    if top:
        top_scene(stage, d, t)
        spots = ((BTN_X, 1.0), (800, 0.8))
    else:
        c = bottom_cam(t)
        bottom_scene(stage, d, t, c)
        spots = ((round((BTN_X - c) / 40) * 40, 1.0), (round((-520 - c) / 40) * 40, 0.9))
    base = C.stage_bg(tuple((float(x), float(s_)) for x, s_ in spots)).copy()
    C.dust(ImageDraw.Draw(base), t, spots, seed=3 if top else 4, n=25)
    tp = stage.crop((0, 0, W * K, FLOOR * K))
    refl = tp.transpose(Image.FLIP_TOP_BOTTOM).crop((0, 0, W * K, (PH - 600) * K))
    refl = refl.resize((refl.width // 4, refl.height // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
    refl = refl.resize((W * K, (PH - 600) * K), Image.BILINEAR)
    fade = np.linspace(0.32, 0.0, refl.height, dtype=np.float32)[:, None]
    refl.putalpha(Image.fromarray((np.asarray(refl.split()[3], np.float32) * fade).astype(np.uint8)))
    base.alpha_composite(refl, (0, FLOOR * K))
    g = stage.resize((W * K // 8, H * K // 8), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6))
    gl = Image.new("RGBA", g.size, (210, 215, 235, 0))
    gl.putalpha(g.split()[3].point(lambda v: int(v * 0.35)))
    base.alpha_composite(gl.resize(stage.size, Image.BILINEAR))
    base.alpha_composite(stage)
    band = base.crop((0, BAND0 * K, W * K, (BAND0 + PH) * K))
    # camera inside the band
    if top:
        if T_REVEAL0 <= t < T_LINES + 0.4:
            k = smooth(prog(t, T_REVEAL0, T_REVEAL0 + 0.8)) * (1 - smooth(prog(t, T_LINES, T_LINES + 0.4)))
            fx, fy, z = lerp(540, BTN_X, k), lerp(380, (FLOOR - 102) - BAND0, k), lerp(1.06, 3.4, k)
        else:
            z = 1.06 + 0.12 * smooth(prog(t, T_SIT, T_REVEAL0))
            fx, fy = lerp(540, 640, smooth(prog(t, T_SIT, T_REVEAL0))), 380
        sh = 0.0
        for p0 in PRESSES:
            if p0 <= t < p0 + 0.3:
                sh = 8 * (1 - (t - p0) / 0.3) * math.sin(t * 90)
        dx, dy = z * (W / 2 - fx) + sh, z * (PH / 2 - fy)
    else:
        z, dx, dy = 1.06, 0.0, 0.0
    band = hq.camera(band, z, dx * K, dy * K)
    im = band.resize((W, PH), Image.LANCZOS)
    if top:
        im = grade(im, -0.9 * clamp((age_of(t) - 25) / 60) * smooth(prog(t, 2.0, 10.0)))
    else:
        im = grade(im, 0.9 * smooth(prog(t, 6.0, 8.5)))
    return im


def counters(img, t):
    d = ImageDraw.Draw(img)
    fl = font("Inter-SemiBold.otf", 30)
    fn = font(SERIF_B, 56)
    fa = font(SERIF, 34)
    for i, (lab, money, age) in enumerate((("PRESSES", n_press(t), age_of(t)), ("READS FIRST", 0, 25))):
        y0 = PANEL_Y[i]
        x = 30
        for ch in lab:
            d.text((x + 2, y0 + 22), ch, font=fl, fill=(0, 0, 0, 160))
            d.text((x, y0 + 20), ch, font=fl, fill=(214, 220, 238, 255))
            x += fl.getlength(ch) + 8
        s = f"${money:,},000,000" if money else "$0"
        col = (170, 255, 190) if money else (200, 204, 214)
        k = 0.0
        for p0 in PRESSES:
            if i == 0 and p0 <= t < p0 + 0.35:
                k = 1 - (t - p0) / 0.35
        f2 = font(SERIF_B, int(56 * (1 + 0.15 * k)))
        tw = f2.getlength(s)
        d.text((W - 30 - tw + 2, y0 + 14 + 2), s, font=f2, fill=(0, 0, 0, 170))
        d.text((W - 30 - tw, y0 + 14), s, font=f2, fill=col + (255,))
        a = clamp((age - 25) / 60)
        acol = tuple(int(lerp(c0, c1, a)) for c0, c1 in zip((236, 236, 240), (240, 110, 100)))
        s2 = f"AGE {age}"
        tw2 = fa.getlength(s2)
        d.text((W - 30 - tw2, y0 + 82), s2, font=fa, fill=acol + (255,))


def header(img, t):
    d = ImageDraw.Draw(img)
    fb = font(SERIF_B, 84)
    if t < T_LINES:
        a = 1.0
        PW.spaced(d, W / 2 + 3, 86, "WOULD YOU PRESS IT?", fb, (0, 0, 0, 160), 4)
        PW.spaced(d, W / 2, 82, "WOULD YOU PRESS IT?", fb, (246, 242, 232, int(255 * a)), 4)
    else:
        a = smooth(prog(t, T_LINES, T_LINES + 0.35))
        b = smooth(prog(t, T_LINES + 0.7, T_LINES + 1.05))
        f1 = font(SERIF_B, 62)
        PW.spaced(d, W / 2, 46, "YOU CAN EARN MONEY BACK.", f1, (246, 242, 232, int(255 * a)), 3)
        PW.spaced(d, W / 2, 134, "NOT TIME.", font(SERIF_B, 76), (240, 110, 100, int(255 * b)), 6)


def reveal_text(img, t):
    if not (T_REVEAL0 + 0.6 <= t < T_LINES + 0.3):
        return
    a = smooth(prog(t, T_REVEAL0 + 0.6, T_REVEAL0 + 0.9)) * (1 - smooth(prog(t, T_LINES, T_LINES + 0.3)))
    d = ImageDraw.Draw(img)
    y0 = PANEL_Y[0] + PH / 2 - 120
    plate = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle([90, y0, W - 90, y0 + 240], 18, fill=(30, 24, 14, int(235 * a)),
                                            outline=(190, 170, 120, int(255 * a)), width=4)
    img.alpha_composite(plate)
    PW.spaced(d, W / 2, y0 + 34, "EACH PRESS =", font(SERIF_B, 58), (236, 228, 206, int(255 * a)), 4)
    PW.spaced(d, W / 2, y0 + 120, "10 YEARS OF YOUR LIFE", font(SERIF_B, 64), (240, 100, 90, int(255 * a)), 3)


BG = None


def frame(t):
    img = BG.copy()
    for i, top in enumerate((True, False)):
        p = render_panel(t, top)
        if not top and T_REVEAL0 <= t < T_LINES + 0.4:
            p = Image.blend(p, Image.new("RGBA", p.size, (0, 0, 0, 255)), 0.55 * smooth(prog(t, T_REVEAL0, T_REVEAL0 + 0.5)))
        img.alpha_composite(p, (0, PANEL_Y[i]))
        ImageDraw.Draw(img).line([(0, PANEL_Y[i]), (W, PANEL_Y[i])], fill=(44, 50, 70, 255), width=2)
    counters(img, t)
    header(img, t)
    reveal_text(img, t)
    return np.asarray(img.convert("RGB"))


def init_worker():
    global BG
    BG = Image.new("RGBA", (W, H), (7, 8, 12, 255))
    d = ImageDraw.Draw(BG)
    rng = np.random.default_rng(1)
    for _ in range(120):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        r = rng.uniform(0.6, 1.6)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(210, 220, 255, int(rng.uniform(40, 150))))


def render(i):
    return frame(i / FPS).tobytes()


# ---------------------------------------------------------------- music + sound
def score():
    import mido
    ev = []

    def note(t, du, ch, n, v):
        if t >= DUR:
            return
        ev.append((t, 1, ch, int(n), int(min(127, max(1, v)))))
        ev.append((min(DUR, t + du), 0, ch, int(n), 0))
    prg = {0: 0, 1: 48, 2: 42, 3: 116, 4: 47, 5: 61, 6: 52, 7: 43, 8: 89}
    # greedy, accelerating ostinato up to the last press
    t = 0.0
    beat = 0.5
    i = 0
    ch_up = [(45, 52, 57, 60), (41, 48, 53, 57), (43, 50, 55, 59), (40, 47, 52, 56)]
    while t < T_SIT:
        ch = ch_up[(i // 8) % 4]
        note(t, beat * 0.45, 1, ch[[1, 2, 3, 2][i % 4]] + 12, 92)
        note(t, beat * 0.9, 7, ch[0] - 12, 90 if i % 2 == 0 else 70)
        if i % 2 == 0:
            note(t, 0.3, 3, 60, 100)
        t += beat * (1 - 0.35 * t / T_SIT)
        i += 1
    for p0 in PRESSES:
        note(p0, 0.6, 4, 45, 120)
        for n in (45, 57):
            note(p0, 0.5, 5, n, 110)
    # the slow, sad turn: piano + cello + pad
    sad = [(45, 57, 60, 64), (41, 57, 60, 65), (43, 55, 59, 62), (40, 56, 59, 64)]
    t = T_SIT
    i = 0
    while t < T_REVEAL0:
        ch = sad[i % 4]
        for j, n in enumerate((ch[1], ch[2], ch[3], ch[2])):
            note(t + j * 0.55, 1.4, 0, n + 12, 64)
        note(t, 2.2, 2, ch[0], 80)
        for n in ch[1:]:
            note(t, 2.2, 8, n, 50)
        t += 2.2
        i += 1
    # the reveal: a low hit, then near silence; the last lines: a final chord
    note(T_REVEAL0, 1.5, 4, 33, 127)
    note(T_REVEAL0, 1.8, 5, 33, 110)
    for n in (45, 57, 60, 64, 69):
        note(T_LINES, DUR - T_LINES, 1, n, 96)
        note(T_LINES, DUR - T_LINES, 6, n, 80)
    note(T_LINES, 1.6, 0, 76, 90)
    note(T_LINES + 0.8, 1.6, 0, 72, 80)
    ev.sort(key=lambda e: (e[0], e[1]))
    mid = mido.MidiFile(ticks_per_beat=960)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))
    vol = {0: 104, 1: 96, 2: 104, 3: 116, 4: 118, 5: 100, 6: 90, 7: 104, 8: 70}
    for c_, p_ in prg.items():
        tr.append(mido.Message("program_change", channel=c_, program=p_, time=0))
    for c_, v in vol.items():
        tr.append(mido.Message("control_change", channel=c_, control=7, value=v, time=0))
        tr.append(mido.Message("control_change", channel=c_, control=91, value=90, time=0))
    now = 0
    for s_, on, c_, n, v in ev:
        tk = int(round(max(0.0, s_) * 1920))
        tr.append(mido.Message("note_on" if on else "note_off", channel=c_, note=n, velocity=v, time=max(0, tk - now)))
        now = max(now, tk)
    tmp = tempfile.mkdtemp()
    mp, wp = os.path.join(tmp, "s.mid"), os.path.join(tmp, "s.wav")
    mid.save(mp)
    subprocess.run(["fluidsynth", "-ni", "-g", "0.7", "-r", str(SR), "-F", wp, C.SF2, mp], check=True, capture_output=True)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", wp, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True).stdout
    m = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    n = int(DUR * SR)
    out = np.zeros((n, 2))
    out[:min(n, len(m))] = m[:n]
    out /= np.abs(out).max() + 1e-9
    return out * 0.55


def audio():
    n = int(DUR * SR)
    fx = np.zeros((n, 2))
    mus = score()
    for p0 in PRESSES:
        mix_in(fx, tone(120, 0.15, (1, 0.5), a=0.001, d=0.05) + 0.4 * noise(0.15, int(p0 * 10), lo=300, hi=3000)[
            :int(0.15 * SR)] * env(int(0.15 * SR), 0.001, 0.03), p0, 0.2, -0.2)
        for j, f_ in enumerate((1568, 2093, 2637)):
            mix_in(fx, tone(f_, 0.4, (1, 0.3), a=0.001, d=0.2), p0 + 0.08 + j * 0.05, 0.05, 0.3)
        mix_in(fx, noise(1.0, int(p0 * 7), lo=1500, hi=7000)[:SR] * np.linspace(1, 0, SR) ** 2, p0 + 0.1, 0.05, 0.3)
    for j in range(5):
        mix_in(fx, tone(150, 0.07, (1, 0.5), a=0.001, d=0.02), 0.1 + j * 0.15, 0.05, -0.2)
    # heartbeat under the reveal
    for j in range(3):
        for k2, dt in enumerate((0.0, 0.18)):
            mix_in(fx, tone(50, 0.2, (1, 0.5), a=0.003, d=0.08), T_REVEAL0 + 0.6 + j * 0.45 + dt, 0.14 - 0.05 * k2)
    # friends' warm chatter (soft murmur) in the bottom panel
    mur = noise(DUR - 7.8, 9, lo=200, hi=1200)[:int((DUR - 7.8) * SR)]
    mur *= (0.5 + 0.5 * np.sin(np.arange(len(mur)) / SR * 2 * np.pi * 3.1)) * 0.5
    mix_in(fx, mur, 7.8, 0.02, 0.2)
    x = mus + fx
    m = int(0.25 * SR)
    k = np.linspace(0, 1, m)[:, None]
    x[-m:] = x[-m:] * (1 - k) + x[:m] * k
    x /= max(1.0, np.abs(x).max() / 0.9)
    return x


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "button.mp4"
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
