#!/usr/bin/env python3
"""THIS YEAR I GET FIT - the doer trains in a real gym, the overthinker saves workout videos in his bedroom.

Same goal on January 1st. Day 1 -> 365: the doer's lifts get heavier and his body visibly grows (KG LIFTED), the
overthinker saves 2,340 workouts, buys gear he never opens and keeps saying "STARTING MONDAY." On day 365 the doer
finally rests and scrolls ("NOW I SCROLL."), the overthinker's calendar turns back to JAN 1 ("THIS YEAR I GET FIT.").
"ONE SAVED 2,340 WORKOUTS. / ONE DID THEM."  40.8 s (17 bars at 100 bpm), loops on itself.
Backgrounds: our own generated photos (stick/bg). 1080x1920, PIL + numpy, sounds from sines (no samples, no noise).

    python3 stick/get_fit.py out/get-fit.mp4
    ONLY_FRAMES=1.5,6,11,16,21,26,31,34,38 python3 stick/get_fit.py out/g.mp4
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scroller_reader import GOLD, INK, clamp, midi, mix_in, out_back, out_cubic, prog, put, tone, write_wav  # noqa
from keep_trying import pose_from  # noqa
from motivation_bus import FM, get_bubble, mono_text  # noqa

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
SR = 44100
BPM = 100
BAR = 4 * 60 / BPM
DUR = 17 * BAR                       # 40.8 s
LANE_H = 948
FLOOR = 800
T0, T365 = 3.0, 30.0                 # the days run between these
T_END_SCENE = 30.4
T_TEXT = 35.0
T_LOOP = DUR - 0.5
KEYS = [(3.0, 1), (7.5, 7), (12.0, 30), (16.5, 90), (21.0, 180), (25.5, 270), (30.0, 365)]
SAVED_365 = 2340
KG_PER_DAY = 1500
BODY = (244, 244, 240)
GREY = (176, 176, 176)
LINE1, LINE2 = "ONE SAVED 2,340 WORKOUTS.", "ONE DID THEM."


def check():
    assert SAVED_365 == 2340 and KG_PER_DAY * 365 == 547500


def day_at(t):
    if t <= KEYS[0][0]:
        return 1
    for (ta, da), (tb, db) in zip(KEYS, KEYS[1:]):
        if t <= tb:
            p = (t - ta) / (tb - ta)
            return int(round(da + (db - da) * (p * p * (3 - 2 * p))))
    return 365


def saved_at(day, t):
    return 0 if t < T0 + 0.6 else int(round(SAVED_365 * (day / 365) ** 0.85))


# ---------------------------------------------------------------- stickman with a body that can grow
def draw_man(pose, body, face="calm", look=1, s=0.8, bulk=0.0, prop=None):
    k = 2
    box = 680
    im = Image.new("RGBA", (box * k, box * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ox, oy = box / 2, box - 50

    def P(n):
        x, y = pose[n]
        return ((ox + x * s) * k, (oy + y * s) * k)

    shade = tuple(int(c * 0.78) for c in body)
    g = 1 + 1.25 * bulk
    limbs_back = [("hip", "kr"), ("kr", "fr"), ("neck", "er"), ("er", "hr")]
    limbs_front = [("hip", "kl"), ("kl", "fl"), ("neck", "el"), ("el", "hl")]
    torso = [("neck", "hip")]

    def seg(segs, col, wo, wf):
        for a, b in segs:
            d.line([P(a), P(b)], fill=INK + (255,), width=int(wo), joint="curve")
            for p in (P(a), P(b)):
                d.ellipse([p[0] - wo / 2, p[1] - wo / 2, p[0] + wo / 2, p[1] + wo / 2], fill=INK + (255,))
        for a, b in segs:
            d.line([P(a), P(b)], fill=col + (255,), width=int(wf), joint="curve")
            for p in (P(a), P(b)):
                d.ellipse([p[0] - wf / 2, p[1] - wf / 2, p[0] + wf / 2, p[1] + wf / 2], fill=col + (255,))

    seg(limbs_back, shade, 40 * s * k * g, 27 * s * k * g)
    tw = 1 + 2.8 * bulk                      # the chest gets wider the most
    seg(torso, body, 40 * s * k * tw, 27 * s * k * tw)
    seg(limbs_front, body, 40 * s * k * g, 27 * s * k * g)
    if bulk > 0.25:                          # biceps bumps
        for e, h_ in (("el", "hl"), ("er", "hr")):
            ex, ey = P(e)
            r = 30 * s * k * bulk
            d.ellipse([ex - r, ey - r, ex + r, ey + r], fill=body + (255,), outline=INK + (255,), width=int(4 * s * k))
    if prop == "phone":
        x, y = P("hl")
        d.rounded_rectangle([x - 14 * k, y - 30 * k, x + 16 * k, y + 14 * k], 6 * k, fill=(22, 26, 34, 255), outline=INK + (255,), width=3 * k)
        d.rounded_rectangle([x - 10 * k, y - 26 * k, x + 12 * k, y + 10 * k], 4 * k, fill=(120, 190, 255, 255))
    hx, hy = P("head")
    r = 52 * s * k
    d.ellipse([hx - r - 7 * s * k, hy - r - 7 * s * k, hx + r + 7 * s * k, hy + r + 7 * s * k], fill=INK + (255,))
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=body + (255,))
    d.ellipse([hx - r * 0.6, hy - r * 0.8, hx - r * 0.1, hy - r * 0.36], fill=(255, 255, 255, 90))
    ex, ey = hx + look * r * 0.30 - (r * 0.18 if look < 0 else 0), hy - r * 0.05
    er_ = r * 0.11
    for dx in (0, r * 0.36):
        d.ellipse([ex + dx - er_, ey - er_, ex + dx + er_, ey + er_], fill=INK + (255,))
    mx, my, mw = ex + r * 0.18, ey + r * 0.45, r * 0.24
    lw = int(5 * s * k)
    if face == "happy":
        d.arc([mx - mw, my - mw * 1.1, mx + mw, my + mw * 0.6], 10, 170, fill=INK + (255,), width=lw)
    elif face == "strain":
        d.line([(mx - mw * 0.7, my + 2), (mx + mw * 0.7, my - 2)], fill=INK + (255,), width=lw)
        d.ellipse([hx + r * 0.75, hy - r * 0.7, hx + r * 0.95, hy - r * 0.35], fill=(120, 190, 255, 255))   # sweat
    elif face == "sad":
        d.arc([mx - mw, my, mx + mw, my + mw * 1.3], 200, 340, fill=INK + (255,), width=lw)
    elif face == "o":
        d.ellipse([mx - mw * 0.35, my - mw * 0.1, mx + mw * 0.35, my + mw * 0.6], fill=INK + (255,))
    else:
        d.line([(mx - mw * 0.6, my), (mx + mw * 0.6, my)], fill=INK + (255,), width=lw)
    im = im.resize((box, box), Image.LANCZOS)
    return im, (ox, oy)


def place(c, pose, x, y, s=0.8, **kw):
    spr, (ax, ay) = draw_man(pose, s=s, **kw)
    sh = Image.new("RGBA", (170, 36), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([0, 0, 170, 36], fill=(0, 0, 0, 90))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)), (int(x - 85), int(y - 16)))
    c.alpha_composite(spr, (int(x - ax), int(y - ay)))


def at(pose, key, x, y, s=0.8):
    return x + pose[key][0] * s, y + pose[key][1] * s


# ---------------------------------------------------------------- backgrounds (our generated photos)
_bg = {}


def photo_lane(name, dim=0.72):
    if name in _bg:
        return _bg[name]
    ph = Image.open(os.path.join(HERE, "bg", name)).convert("RGB")
    sc = max(W / ph.width, LANE_H / ph.height)
    ph = ph.resize((int(ph.width * sc + 1), int(ph.height * sc + 1)), Image.LANCZOS)
    top = int((ph.height - LANE_H) * 0.55)
    ph = ph.crop(((ph.width - W) // 2, top, (ph.width - W) // 2 + W, top + LANE_H)).filter(ImageFilter.GaussianBlur(3))
    a = np.asarray(ph).astype(np.float32) * dim
    yy = np.linspace(0, 1, LANE_H)[:, None, None]
    a *= 0.75 + 0.25 * np.clip(yy * 3, 0, 1)          # a little darker at the top, for the counters
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    # a floor band so the characters stand on something
    fl = Image.new("RGBA", (W, LANE_H - FLOOR), (30, 26, 24, 150))
    im.alpha_composite(fl, (0, FLOOR))
    d.line([(0, FLOOR), (W, FLOOR)], fill=(200, 190, 170), width=3)
    _bg[name] = im
    return im


# ---------------------------------------------------------------- props
def barbell(d, cx, cy, plates):
    d.line([(cx - 230, cy), (cx + 230, cy)], fill=(70, 70, 76), width=14)
    d.line([(cx - 230, cy), (cx + 230, cy)], fill=(200, 200, 206), width=8)
    for side in (-1, 1):
        for p in range(plates):
            x = cx + side * (150 + p * 22)
            h_ = 120 - p * 8
            d.rounded_rectangle([x - 10, cy - h_ / 2, x + 10, cy + h_ / 2], 5, fill=(36, 36, 40), outline=(120, 120, 126), width=3)


def box_prop(c, x, y, label, col, p=1.0):
    if p <= 0:
        return
    w_, h_ = 150, 110
    im = Image.new("RGBA", (w_ + 10, h_ + 10), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([4, 4, w_ + 4, h_ + 4], fill=col, outline=INK, width=4)
    d.line([(w_ / 2 + 4, 4), (w_ / 2 + 4, h_ + 4)], fill=(220, 200, 150), width=8)
    d.text((w_ / 2 + 4, h_ / 2 + 14), label, font=FM(22), fill=INK, anchor="mm")
    sc = out_back(clamp(p), 2)
    put(c, im, x, y - h_ / 2 - (1 - clamp(p)) * 200, sc, clamp(p * 2))


def bed(d):
    d.rounded_rectangle([60, FLOOR - 170, 560, FLOOR - 90], 18, fill=(110, 120, 150), outline=INK, width=6)
    d.rounded_rectangle([70, FLOOR - 205, 210, FLOOR - 165], 16, fill=(230, 230, 236), outline=INK, width=5)
    d.rectangle([60, FLOOR - 230, 90, FLOOR], fill=(120, 86, 60), outline=INK, width=5)
    for lx in (100, 540):
        d.rectangle([lx, FLOOR - 90, lx + 18, FLOOR], fill=(90, 66, 46), outline=INK, width=3)


def calendar(c, x, y, txt, p=1.0, red=False):
    w_, h_ = 190, 170
    im = Image.new("RGBA", (w_, h_), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([3, 3, w_ - 3, h_ - 3], 14, fill=(250, 250, 246), outline=INK, width=5)
    d.rounded_rectangle([3, 3, w_ - 3, 56], 14, fill=(220, 60, 60) if red or True else (90, 90, 96), outline=INK, width=5)
    d.text((w_ / 2, 30), "JAN", font=FM(30), fill=(255, 255, 255), anchor="mm")
    d.text((w_ / 2, 110), txt, font=FM(64), fill=INK, anchor="mm")
    put(c, im, x, y, 0.5 + 0.5 * out_back(clamp(p), 2), clamp(p * 2))


def bubble(c, txt, x, y, p, a=1.0):
    b = get_bubble(txt)
    put(c, b, x + b.width * 0.22, y, 0.5 + 0.5 * out_back(clamp(p), 2.2), min(1, p * 2) * a)


# ---------------------------------------------------------------- lanes
DOER_SAYS = [(3.6, 5.6, "OUCH."), (9.0, 10.8, "+5 KG."), (13.5, 15.3, "AGAIN."), (18.2, 20.0, "+20 KG."), (27.0, 29.0, "EASY.")]
OVER_SAYS = [(4.0, 6.3, "SAVED."), (8.4, 10.6, "STARTING MONDAY."), (12.6, 14.8, "NEED NEW SHOES FIRST."),
             (17.0, 19.2, "AFTER THIS VIDEO."), (21.5, 23.7, "THIS ROUTINE LOOKS GOOD."), (26.0, 28.4, "ALMOST READY.")]
GEAR = [(9.0, "PROTEIN", (240, 210, 140)), (13.0, "SHOES", (190, 210, 240)), (17.5, "YOGA MAT", (200, 236, 200)),
        (22.0, "WATCH", (236, 200, 236)), (26.4, "PROTEIN", (240, 210, 140))]


def doer_lane(t, day):
    c = photo_lane("gym-night.jpg").copy()
    d = ImageDraw.Draw(c)
    bulk = clamp((day - 1) / 364) ** 0.7
    x = 540
    if t < T0:   # January 1st: the same promise
        place(c, pose_from(lean=0, al=-12, ar=12), x, FLOOR, bulk=0, face="happy", body=BODY)
        calendar(c, 860, 260, "1", prog(t, 0.2, 0.35))
        bubble(c, "THIS YEAR I GET FIT.", 250, 300, prog(t, 0.6, 0.25))
        return c
    if t >= T_END_SCENE:   # day 365: he finally rests and scrolls
        p = pose_from(lean=-10, dy=90, tl=85, sl=-70, tr=75, sr=-60, al=40, bl=-120, ar=20, br=-40)
        d.rounded_rectangle([380, FLOOR - 120, 700, FLOOR - 80], 10, fill=(70, 70, 76), outline=INK, width=5)   # bench
        for lx in (400, 660):
            d.rectangle([lx, FLOOR - 80, lx + 16, FLOOR], fill=(50, 50, 54), outline=INK, width=3)
        place(c, p, x, FLOOR - 40, bulk=bulk, face="happy", body=BODY, prop="phone")
        barbell(d, 540, FLOOR - 26, 4)
        bubble(c, "NOW I SCROLL.", 600, 280, prog(t, T_END_SCENE + 0.4, 0.25))
        return c
    plates = 1 + min(3, int((day - 1) / 70))
    period = 1.4
    ph = ((t - T0) % period) / period
    lift = math.sin(ph * math.pi) ** 2               # 0 down .. 1 up
    if (day // 40) % 2 == 0:   # deadlift
        p = pose_from(lean=48 * (1 - lift), dy=36 * (1 - lift), tl=30 * (1 - lift), sl=-40 * (1 - lift), tr=24 * (1 - lift),
                      sr=-40 * (1 - lift), al=-30 * (1 - lift) + 6, bl=0, ar=-24 * (1 - lift) + 6, br=0)
        hx, hy = at(p, "hl", x, FLOOR)
        barbell(d, x, min(hy + 10, FLOOR - 50), plates)
    else:                       # curls
        p = pose_from(lean=0, al=-6, bl=-150 * lift - 10, ar=6, br=150 * lift + 10)
        hx, hy = at(p, "hl", x, FLOOR)
        d.line([(hx - 150, hy), (hx + 150, hy)], fill=(200, 200, 206), width=8)
        for side in (-1, 1):
            d.rounded_rectangle([hx + side * 150 - 12, hy - 34, hx + side * 150 + 12, hy + 34], 5, fill=(36, 36, 40), outline=(120, 120, 126), width=3)
    face = "strain" if day < 20 else ("calm" if day < 150 else "happy")
    place(c, p, x, FLOOR, bulk=bulk, face=face, body=BODY)
    for s_, e_, txt in DOER_SAYS:
        if s_ <= t < e_:
            bubble(c, txt, 640, 330, prog(t, s_, 0.25), 1 - prog(t, e_ - 0.2, 0.2))
    return c


def over_lane(t, day):
    c = photo_lane("bedroom-night.jpg", 0.62).copy()
    d = ImageDraw.Draw(c)
    bed(d)
    for i, (tg, lab, col) in enumerate(GEAR):   # gear he orders and never opens
        if t >= tg:
            box_prop(c, 690 + (i % 3) * 120, FLOOR - (i // 3) * 112, lab, col, prog(t, tg, 0.4))
    if t < T0:
        place(c, pose_from(lean=0, al=-12, ar=12), 380, FLOOR, face="happy", body=GREY)
        calendar(c, 890, 470, "1", prog(t, 0.2, 0.35))
        bubble(c, "THIS YEAR I GET FIT.", 170, 330, prog(t, 1.0, 0.25))
        return c
    scroll = math.sin(t * 7) * 3 if (t * 1.1) % 1 < 0.7 else 0
    p = pose_from(lean=30, dy=110, tl=82, sl=-70, tr=74, sr=-66, al=40, bl=-100 + scroll, ar=30, br=-90)
    place(c, p, 330, FLOOR - 90, body=GREY, face="sad" if t >= T_END_SCENE + 1.4 else "calm", prop="phone")
    hx, hy = at(p, "hl", 330, FLOOR - 90)
    glow = Image.new("RGBA", (W, LANE_H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([hx - 90, hy - 110, hx + 90, hy + 50], fill=(120, 190, 255, 80))
    c.alpha_composite(glow.filter(ImageFilter.GaussianBlur(30)))
    if t >= T_END_SCENE:   # the calendar goes back to JAN 1
        calendar(c, 890, 470, "1", prog(t, T_END_SCENE + 0.2, 0.35))
        bubble(c, "THIS YEAR I GET FIT.", 170, 330, prog(t, T_END_SCENE + 1.0, 0.25))
    else:
        for s_, e_, txt in OVER_SAYS:
            if s_ <= t < e_:
                bubble(c, txt, 170, 330, prog(t, s_, 0.25), 1 - prog(t, e_ - 0.2, 0.2))
        # each save: a small "+1" bookmark flying up from the phone
        if t > T0 + 0.6 and (t * 2.2) % 1 < 0.5:
            u = (t * 2.2) % 1 / 0.5
            put(c, mono_text("SAVED", 22, (120, 190, 255), 2), hx + 40, hy - 40 - u * 90, 1, 1 - u)
    return c


# ---------------------------------------------------------------- frame
def counters(c, y0, kg, saved, label, col):
    put(c, mono_text(label, 34, col, 6), W / 2, y0 + 48)
    put(c, mono_text("KG LIFTED", 24, (210, 210, 210), 4), 200, y0 + 100)
    put(c, mono_text(f"{kg:,}", 52, (255, 255, 255) if kg else (150, 150, 150)), 200, y0 + 150)
    put(c, mono_text("WORKOUTS SAVED", 24, (210, 210, 210), 3), W - 220, y0 + 100)
    put(c, mono_text(f"{saved:,}", 52, (120, 190, 255) if saved else (150, 150, 150)), W - 220, y0 + 150)
    return


def frame_raw(t):
    day = day_at(t)
    c = Image.new("RGBA", (W, H), (16, 16, 18, 255))
    c.alpha_composite(doer_lane(t, day), (0, 0))
    c.alpha_composite(over_lane(t, day), (0, 972))
    d = ImageDraw.Draw(c)
    d.rectangle([0, 948, W, 972], fill=(10, 10, 12))
    kg = 0 if t < T0 else KG_PER_DAY * day
    counters(c, 0, kg, 0, "DOER", (255, 214, 102))
    counters(c, 972 + 40, 0, saved_at(day, t), "OVERTHINKER", (190, 190, 190))
    # middle: SAME GOAL / DAY n
    pw, ph = 420, 92
    im = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    dd.rounded_rectangle([0, 0, pw - 1, ph - 1], 46, fill=(24, 22, 28, 240), outline=(255, 255, 255), width=3)
    dd.text((pw / 2, 26), "SAME GOAL", font=FM(22), fill=(200, 200, 200), anchor="mm")
    dd.text((pw / 2, 62), f"DAY {day}" if t >= T0 else "JAN 1", font=FM(40), fill=(255, 255, 255), anchor="mm")
    put(c, im, W / 2, 960)
    if t >= T_TEXT:
        p = out_cubic(prog(t, T_TEXT, 0.4))
        c.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(165 * p))))
        chars = int((t - T_TEXT - 0.3) / 0.055)
        l1 = LINE1[:max(0, chars)]
        l2 = LINE2[:max(0, chars - len(LINE1) - 4)]
        cur = "_" if int(t * 3) % 2 == 0 else " "
        if l1:
            im = mono_text(l1 + (cur if not l2 else ""), 52, (245, 245, 240), 1)
            c.alpha_composite(im, (int(W / 2 - mono_text(LINE1, 52, spacing=1).width / 2), 860))
        if l2:
            im = mono_text(l2 + cur, 52, GOLD, 1)
            c.alpha_composite(im, (int(W / 2 - mono_text(LINE2, 52, spacing=1).width / 2), 940))
    return c


def frame(t):
    c = frame_raw(t)
    if t >= T_LOOP:
        c = Image.blend(c, frame_raw(0.0), out_cubic(prog(t, T_LOOP, DUR - T_LOOP)))
    return c.convert("RGB")


# ---------------------------------------------------------------- audio
def audio():
    n = int(DUR * SR)
    mus, fx = np.zeros((n, 2)), np.zeros((n, 2))
    beat = 60 / BPM
    chords = [[50, 57, 60, 65], [46, 53, 58, 62], [48, 55, 60, 64], [45, 52, 57, 60]]
    roots = [38, 34, 36, 33]
    for b in range(17):
        t0 = b * BAR
        ch, rt = chords[b % 4], roots[b % 4]
        grow = clamp((t0 - T0) / (T365 - T0))
        for k, m in enumerate(ch):
            mix_in(mus, tone(midi(m), BAR + 0.05, (1, 0.4, 0.15, 0.05), a=0.03, d=1.3), t0, 0.045 + 0.02 * grow, (k - 1.5) * 0.35)
        for q in range(4):
            tb = t0 + q * beat
            if t0 >= T0 - 0.01:
                mix_in(mus, tone(110, 0.3, (1,), a=0.002, d=0.1, sweep=42), tb, 0.45 + 0.25 * grow if q % 2 == 0 else 0.3 + 0.15 * grow)
                if q % 2 == 1:
                    mix_in(mus, tone(330, 0.16, (1, 0.6, 0.45, 0.3, 0.2), a=0.002, d=0.04, sweep=190), tb, 0.1 + 0.05 * grow)
                for e in range(2):
                    mix_in(mus, tone(3000, 0.03, (1,), a=0.0008, d=0.006), tb + e * beat / 2, 0.03, 0.4 - 0.8 * e)
            mix_in(mus, tone(midi(rt), beat * 0.45, (1, 0.5, 0.15), a=0.004, d=0.14), tb, 0.2)
            m = ch[(q + b) % 4] + 12
            mix_in(mus, tone(midi(m), 0.32, (1, 0.3, 0.1), a=0.003, d=0.1), tb + beat * 0.75, 0.05 + 0.02 * grow, 0.2)
    # lifts: a metal clank at the bottom of every rep
    t = T0
    while t < T_END_SCENE:
        mix_in(fx, tone(180, 0.25, (1, 0.7, 0.5, 0.35, 0.2), a=0.001, d=0.06), t, 0.08, -0.3)
        t += 1.4
    # saves: a soft tick
    t = T0 + 0.6
    while t < T_END_SCENE:
        mix_in(fx, tone(1900, 0.04, (1, 0.3), a=0.001, d=0.01), t, 0.035, 0.4)
        t += 1 / 2.2
    for tg, _, _ in GEAR:   # a parcel lands
        mix_in(fx, tone(95, 0.3, (1, 0.5), a=0.002, d=0.08, sweep=55), tg + 0.35, 0.3, 0.4)
    for s_, _, _ in DOER_SAYS + OVER_SAYS:
        mix_in(fx, tone(560, 0.11, (1, 0.3), a=0.002, d=0.05, sweep=1100), s_, 0.09)
    # day 365: a bright chord for the doer, the calendar flip and a low "dun" for the overthinker
    for k, m in enumerate([62, 66, 69, 74]):
        mix_in(fx, tone(midi(m), 1.6, (1, 0.35, 0.12), a=0.01, d=0.8), T_END_SCENE + k * 0.07, 0.07, -0.3)
    mix_in(fx, tone(800, 0.12, (1, 0.5), a=0.001, d=0.04, sweep=300), T_END_SCENE + 0.2, 0.12, 0.3)
    for k, (m, d_) in enumerate([(38, 0.5), (37, 1.0)]):
        mix_in(fx, tone(midi(m), d_ + 0.4, (1, 0.6, 0.4, 0.25), a=0.005, d=0.5), T_END_SCENE + 1.0 + k * 0.35, 0.25, 0.3)
    total = len(LINE1) + 4 + len(LINE2)
    for i in range(total):
        if (LINE1 + "    " + LINE2)[i] != " ":
            mix_in(fx, tone(1700 + (i % 3) * 140, 0.025, (1, 0.4), a=0.0006, d=0.005), T_TEXT + 0.3 + i * 0.055, 0.05)
    x = mus + fx
    x -= x.mean(axis=0)
    x = np.tanh(x * 1.3)
    x *= 0.89 / np.abs(x).max()
    r = int(0.005 * SR)
    x[:r] *= np.linspace(0, 1, r)[:, None]
    x[-r:] *= np.linspace(1, 0, r)[:, None]
    return x


def main():
    check()
    out = sys.argv[1] if len(sys.argv) > 1 else "out/get-fit.mp4"
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    only = os.environ.get("ONLY_FRAMES")
    if only:
        for s in only.split(","):
            frame(float(s)).save(f"{out[:-4]}-{float(s):05.2f}.png")
        return
    wav = out[:-4] + ".wav"
    write_wav(wav, audio())
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                           out], stdin=subprocess.PIPE)
    for i in range(int(round(DUR * FPS))):
        ff.stdin.write(frame(i / FPS).tobytes())
    ff.stdin.close()
    if ff.wait():
        raise SystemExit("ffmpeg failed")
    os.remove(wav)
    print("wrote", out)


if __name__ == "__main__":
    main()
