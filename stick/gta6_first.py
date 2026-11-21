#!/usr/bin/env python3
"""WHO PLAYS GTA 6 FIRST? - the neon 4-mind format. 14 s, loops.

11:59 PM, launch night, four couches, four TVs: LAUNCH IN 0:01 - and at midnight IT'S OUT.
THE DOER sits down and plays: his playtime bar climbs, mission after mission. THE OVERTHINKER reads on his phone:
"BEST SETTINGS?" "REVIEW #47" "IS IT WORTH IT?" "TIER LIST". THE QUITTER plays, MISSION FAILED, throws the controller,
"I'M DONE.", leaves. THE SHOW-OFF sets up RGB lights, a ring light and a camera: "MIC CHECK" "GOING LIVE...".
3:00 AM, the results: 3H PLAYED for the Doer, 0H / 22 MIN / 0H for the rest - the Show-off is LIVE to 0 VIEWERS.
"WHO ACTUALLY PLAYED? / WHICH ONE ARE YOU?"  FOLLOW FOR MORE.  (No game logos or art: our own neon city.)

    python3 stick/gta6_first.py stick/gta6-first.mp4
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
import neon as N  # noqa
from perfect_wave import (MONO, clamp, env, font, lerp, lerp_pose, midi, mix_in, noise, out_back,  # noqa
                          prog, smooth, spaced, tone, write_wav)

W, H, FPS = 1080, 1920, 30
SR = 44100
DUR = 14.0
NF = int(round(DUR * FPS))
XFADE = 0.45
BOLD = N.BOLD
PW_ = N.PX1 - N.PX0
PH = N.PANEL_H
FLOOR = PH - 70
S = 0.95                       # figure scale

T_OUT = 1.0                    # midnight
T_PLAY = 1.5
T_FAIL, T_THROW, T_LEAVE0, T_LEAVE1 = 4.6, 5.0, 5.8, 7.0
T_LIVE = 9.0
T_RES = 9.5                    # the results (twist at ~68%)
T_L1, T_L2 = 10.8, 11.8
CPS = 18.0
LINE1, LINE2 = "WHO ACTUALLY PLAYED?", "WHICH ONE ARE YOU?"
T_FOLLOW = 12.8

COUCH = (90, 390)
TV = (600, 900, 70, 250)       # x0, x1, y0, y1 of the screen
SIT_HIP = (250, FLOOR - 104)


def clock(t):
    if t < T_OUT:
        return "11:59 PM"
    m = int(180 * prog(t, T_OUT, T_RES))
    h = m // 60
    return f"{12 if h == 0 else h}:{m % 60:02d} AM"


# ---------------------------------------------------------------- poses
SIT_PAD = dict(AJ.SIT_TYPE, head=(22, -144), neck=(14, -102), el=(40, -70), hl=(70, -84), er=(34, -66), hr=(64, -80))
SIT_PHONE = dict(AJ.SIT_TYPE, head=(16, -146), neck=(10, -104), el=(28, -66), hl=(48, -98), er=(24, -62), hr=(44, -94))
THROW = dict(PW.STAND, head=(4, -150), el=(30, -130), hl=(60, -180), er=(10, -60), hr=(14, -14))
STAND = PW.STAND
ARMS_UP = dict(STAND, el=(-26, -130), hl=(-20, -180), er=(26, -130), hr=(30, -180))
ADJUST = dict(STAND, el=(30, -120), hl=(70, -150), er=(10, -60), hr=(14, -14))
POINT_CAM = dict(STAND, el=(36, -96), hl=(80, -110), er=(30, -90), hr=(74, -104))


def doer(t):
    k = 0.5 + 0.5 * math.sin(t * 14)
    p = dict(SIT_PAD, hl=(70, -84 + 3 * k), hr=(64, -80 - 3 * k))
    return p, SIT_HIP, 1, 1.0


def overthinker(t):
    return SIT_PHONE, SIT_HIP, 1, 1.0


def quitter(t):
    if t < T_FAIL:
        k = 0.5 + 0.5 * math.sin(t * 16)
        return dict(SIT_PAD, hl=(70, -84 + 4 * k), hr=(64, -80 - 4 * k)), SIT_HIP, 1, 1.0
    if t < T_THROW:
        return lerp_pose(SIT_PAD, dict(SIT_PAD, head=(-6, -150), neck=(-4, -106)), smooth(prog(t, T_FAIL, T_THROW))), \
            SIT_HIP, 1, 1.0
    if t < T_LEAVE0:
        k = smooth(prog(t, T_THROW, T_THROW + 0.3))
        return lerp_pose(SIT_PAD, THROW, k), (SIT_HIP[0], lerp(SIT_HIP[1], FLOOR - 113 * S, k)), 1, 1.0
    if t < T_LEAVE1 + 0.2:
        k = smooth(prog(t, T_LEAVE0, T_LEAVE1))
        a = 1 - smooth(prog(t, T_LEAVE1 - 0.3, T_LEAVE1 + 0.1))
        return AJ.walk((t - T_LEAVE0) * 7, STAND), (lerp(SIT_HIP[0], 560, k), FLOOR - 113 * S), -1 if False else 1, a
    return STAND, (560, FLOOR - 113 * S), 1, 0.0


def showoff(t):
    hip = (330, FLOOR - 113 * S)
    seq = [(0.0, 2.2, ADJUST), (2.2, 4.0, ARMS_UP), (4.0, 5.6, ADJUST), (5.6, 7.4, POINT_CAM), (7.4, 9.0, ARMS_UP)]
    for a, b, pose in seq:
        if a <= t < b:
            k = 0.5 + 0.5 * math.sin((t - a) * 5)
            return lerp_pose(STAND, pose, 0.6 + 0.4 * k), hip, 1, 1.0
    return lerp_pose(STAND, POINT_CAM, 1.0), hip, 1, 1.0


PEOPLE = [doer, overthinker, quitter, showoff]

# ---------------------------------------------------------------- drawing
GAME = None


def build_game_screen(w, h):
    """Our own neon city at sunset: gradient sky, a striped sun, palms, a road. No game art."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    for y in range(h):
        k = y / h
        c = PW.lerp_c((40, 10, 70), (255, 90, 140), min(1, k * 1.3)) if k < 0.75 else PW.lerp_c((255, 140, 90),
                                                                                                  (30, 10, 50), (k - 0.75) * 4)
        d.line([(0, y), (w, y)], fill=c + (255,))
    cx, cy, r = w * 0.5, h * 0.62, h * 0.28
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 210, 90, 255))
    for j in range(5):
        yy = cy + r * (0.1 + j * 0.18)
        d.rectangle([cx - r, yy, cx + r, yy + 3 + j], fill=(255, 90, 140, 255))
    d.rectangle([0, h * 0.75, w, h], fill=(20, 8, 40, 255))
    for x in (w * 0.15, w * 0.85):
        d.line([(x, h * 0.75), (x + 6, h * 0.35)], fill=(10, 4, 20, 255), width=6)
        for a in (-150, -110, -60, -20):
            ra = math.radians(a)
            d.line([(x + 6, h * 0.35), (x + 6 + 50 * math.cos(ra), h * 0.35 + 22 * math.sin(ra) + 12)],
                   fill=(10, 4, 20, 255), width=5)
    return im


def tv(im, t, i):
    x0, x1, y0, y1 = TV
    d = ImageDraw.Draw(im)
    d.rectangle([x0 - 8, y0 - 8, x1 + 8, y1 + 8], fill=(8, 8, 12, 255), outline=(60, 60, 72, 255), width=3)
    d.rectangle([(x0 + x1) / 2 - 40, y1 + 8, (x0 + x1) / 2 + 40, FLOOR], fill=(30, 30, 38, 255))
    w, h = x1 - x0, y1 - y0
    if t < T_OUT:
        d.rectangle([x0, y0, x1, y1], fill=(10, 10, 16, 255))
        spaced(d, (x0 + x1) / 2, y0 + 50, "LAUNCH IN", font(BOLD, 26), (200, 204, 214, 255), 3)
        spaced(d, (x0 + x1) / 2, y0 + 92, "0:01", font(BOLD, 54), (255, 255, 255, 255), 2)
        return
    if t < T_OUT + 0.45:
        k = prog(t, T_OUT, T_OUT + 0.45)
        d.rectangle([x0, y0, x1, y1], fill=(255, 255, 255, 255))
        spaced(d, (x0 + x1) / 2, y0 + 70, "IT'S OUT!", font(BOLD, int(40 + 8 * k)), (255, 60, 180, 255), 2)
        return
    playing = i == 0 or (i == 2 and t < T_FAIL)
    if playing:
        g = GAME.copy()
        # the road moves
        gd = ImageDraw.Draw(g)
        for j in range(6):
            ph = ((t * 1.4) + j / 6) % 1.0
            yy = h * 0.78 + ph * h * 0.22
            ww = 4 + ph * 30
            gd.rectangle([w / 2 - ww / 2, yy, w / 2 + ww / 2, yy + 3 + ph * 6], fill=(255, 220, 120, 255))
        im.alpha_composite(g, (x0, y0))
        d = ImageDraw.Draw(im)
        if i == 0:
            n = 1 + int(8 * prog(t, 2.5, T_RES))
            d.rounded_rectangle([x0 + 10, y0 + 10, x0 + 170, y0 + 44], 6, fill=(10, 10, 16, 200))
            d.text((x0 + 18, y0 + 14), f"MISSION {n} ✓" if False else f"MISSION {n} OK", font=font(BOLD, 22),
                   fill=(120, 240, 150, 255))
        return
    if i == 2:
        d.rectangle([x0, y0, x1, y1], fill=(40, 6, 8, 255))
        if int(t * 3) % 2 == 0 or t < T_FAIL + 0.6:
            spaced(d, (x0 + x1) / 2, y0 + 70, "MISSION FAILED", font(BOLD, 34), (255, 70, 60, 255), 2)
        return
    if i == 1:
        d.rectangle([x0, y0, x1, y1], fill=(10, 10, 16, 255))
        if int(t * 1.5) % 2 == 0:
            spaced(d, (x0 + x1) / 2, y0 + 80, "PRESS START", font(BOLD, 28), (150, 150, 160, 255), 3)
        return
    # show-off: the stream overlay
    d.rectangle([x0, y0, x1, y1], fill=(14, 10, 20, 255))
    if t < T_LIVE:
        spaced(d, (x0 + x1) / 2, y0 + 80, "STARTING SOON...", font(BOLD, 28), (255, 90, 200, 255), 2)
    else:
        d.ellipse([x0 + 40, y0 + 74, x0 + 62, y0 + 96], fill=(255, 40, 40, 255))
        d.text((x0 + 74, y0 + 66), "LIVE · 0 VIEWERS", font=font(BOLD, 30), fill=(255, 255, 255, 255))


def couch(im):
    d = ImageDraw.Draw(im)
    x0, x1 = COUCH
    d.rounded_rectangle([x0, FLOOR - 150, x1, FLOOR - 70], 20, fill=(34, 30, 48, 255), outline=(70, 64, 96, 255), width=3)
    d.rounded_rectangle([x0 - 10, FLOOR - 80, x1 + 10, FLOOR - 20], 16, fill=(40, 36, 56, 255), outline=(70, 64, 96, 255),
                        width=3)


def setup(im, t):
    """The show-off's setup: an RGB strip that cycles, a ring light, a camera on a tripod."""
    hue = (t * 0.6) % 1.0
    import colorsys
    for j in range(12):
        c = colorsys.hsv_to_rgb((hue + j / 12) % 1.0, 0.8, 1.0)
        col = tuple(int(255 * v) for v in c)
        x = 60 + j * 44
        N.neon_line(im, [(x, 50), (x + 34, 50)], col, 5, 0.9)
    N.neon_line(im, [(170, FLOOR), (170, 150)], (120, 120, 130), 4, 0.3)
    N.neon_rect(im, [120, 60, 220, 160], (255, 250, 240), 6, 1.2, radius=50)
    d = ImageDraw.Draw(im)
    d.line([(470, FLOOR), (490, FLOOR - 140), (510, FLOOR)], fill=(90, 90, 100, 255), width=4)
    d.rounded_rectangle([462, FLOOR - 176, 524, FLOOR - 136], 6, fill=(30, 30, 38, 255), outline=(120, 120, 130, 255),
                        width=3)
    d.ellipse([480, FLOOR - 166, 502, FLOOR - 144], fill=(60, 140, 255, 255))


def float_text(im, t, items, col, x, y):
    for t0, s in items:
        if t0 <= t < t0 + 1.4:
            k = prog(t, t0, t0 + 1.4)
            a = math.sin(math.pi * min(1, k * 1.3))
            lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
            N.neon_text(lay, (x, y - 40 * k), s, 30, col, glow=0.8)
            lay.putalpha(lay.split()[3].point(lambda v, a=a: int(v * a)))
            im.alpha_composite(lay)


RESULTS = [("3H PLAYED", (120, 240, 150)), ("0H", (255, 80, 80)), ("21 MIN", (255, 80, 80)), ("0H", (255, 80, 80))]


def stamp(im, t, i):
    if t < T_RES:
        return
    k = out_back(prog(t, T_RES + 0.12 * i, T_RES + 0.12 * i + 0.3))
    if k < 0.05:
        return
    s, col = RESULTS[i]
    f = font(BOLD, 64)
    tw = f.getlength(s) + 3 * len(s)
    lay = Image.new("RGBA", (int(tw + 70), 110), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle([0, 0, lay.width - 1, 109], 14, fill=(8, 8, 12, 235), outline=col + (255,), width=5)
    spaced(ld, lay.width / 2, 18, s, f, col + (255,), 3)
    lay = lay.rotate(-4 if i else 0, resample=Image.BICUBIC, expand=True)
    lay = lay.resize((max(1, int(lay.width * k)), max(1, int(lay.height * k))), Image.LANCZOS)
    cx = PW_ / 2 + 120 if i != 3 else 260
    im.alpha_composite(lay, (int(cx - lay.width / 2), int(PH / 2 - lay.height / 2)))


def flying_controller(im, t):
    if not (T_THROW <= t < T_THROW + 0.9):
        return
    k = prog(t, T_THROW, T_THROW + 0.9)
    x = lerp(300, 840, k)
    y = 150 - 260 * k + 320 * k * k
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x - 22, y - 12, x + 22, y + 12], 8, fill=(255, 150, 40, 255))


BGS = []
FRAME0 = None


def panel(t, i):
    im = BGS[i].copy()
    name, col = N.CHARS[i]
    if i == 3:
        setup(im, t)
    else:
        couch(im)
    tv(im, t, i)
    pose, hip, facing, alpha = PEOPLE[i](t)
    if alpha > 0.01:
        pts = AJ.place(pose, hip, facing, S)
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        N.neon_stick(lay, pts, col, width=10, glow=1.3)
        if alpha < 0.999:
            lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
        im.alpha_composite(lay)
        d = ImageDraw.Draw(im)
        if i in (0, 2) and t < (T_THROW if i == 2 else 99):
            hx, hy = pts["hl"]
            d.rounded_rectangle([hx - 16, hy - 8, hx + 18, hy + 10], 6, fill=col + (255,))
        if i == 1:
            hx, hy = pts["hl"]
            d.rounded_rectangle([hx - 9, hy - 22, hx + 11, hy + 8], 4, fill=(20, 22, 30, 255), outline=col + (255,), width=3)
    if i == 1:
        float_text(im, t, [(1.4, "BEST SETTINGS?"), (2.9, "REVIEW #47"), (4.4, "IS IT WORTH IT?"), (5.9, "TIER LIST"),
                           (7.4, "SPOILER-FREE?")], col, 470, 120)
    if i == 2:
        flying_controller(im, t)
        if T_LEAVE0 - 0.4 <= t < T_LEAVE1:
            float_text(im, t, [(T_LEAVE0 - 0.4, "I'M DONE.")], col, 470, 110)
    if i == 3:
        float_text(im, t, [(1.2, "RGB OK"), (2.8, "MIC CHECK"), (4.4, "CAMERA ANGLE..."), (6.0, "MORE LIGHT"),
                           (7.5, "GOING LIVE...")], col, 440, 110)
    # playtime bar
    play = {0: prog(t, T_PLAY, T_RES), 1: 0.0, 2: prog(t, T_PLAY, T_FAIL) * 0.12, 3: 0.0}[i]
    mins = int(180 * play)
    bar_txt = f"PLAYTIME {mins // 60}:{mins % 60:02d}"
    N.bar(im, PW_ - 300, PH - 40, 260, play, col, bar_txt)
    N.label(im, i)
    stamp(im, t, i)
    # frame
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle([1, 1, im.width - 2, im.height - 2], 14, outline=col + (160,), width=3)
    im.alpha_composite(lay)
    return im


def frame(t):
    img = Image.new("RGBA", (W, H), (6, 6, 10, 255))
    for i in range(4):
        img.alpha_composite(panel(t, i), (N.PX0, N.panel_y(i)))
    # title: the question, or the closing lines
    if t < T_L1:
        f = font(BOLD, 66)
        parts = [("WHO PLAYS ", (250, 250, 252)), ("GTA 6", (255, 70, 200)), (" FIRST?", (250, 250, 252))]
        total = sum(f.getlength(p) for p, c in parts)
        x = W / 2 - total / 2
        for p, c in parts:
            N.neon_text(img, (x, 52), p, 66, c, anchor_center=False, glow=0.9 if c[0] == 255 and c[1] == 70 else 0.4)
            x += f.getlength(p)
        d = ImageDraw.Draw(img)
        spaced(d, W / 2, 150, clock(t), font(BOLD, 40), (255, 80, 80, 255), 4)
    else:
        d = ImageDraw.Draw(img)
        fm = font(BOLD, 58)
        for t0, s2, y in ((T_L1, LINE1, 50), (T_L2, LINE2, 130)):
            if t < t0:
                continue
            k = int(clamp((t - t0) * CPS, 0, len(s2)))
            full = sum(fm.getlength(c) for c in s2) + 3 * (len(s2) - 1)
            xx = W / 2 - full / 2
            for c in s2[:k]:
                d.text((xx, y), c, font=fm, fill=(250, 250, 252, 255))
                xx += fm.getlength(c) + 3
    if T_OUT <= t < T_OUT + 0.25:
        k = 1 - prog(t, T_OUT, T_OUT + 0.25)
        img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(120 * k))))
    arr = np.asarray(img.convert("RGB")).astype(np.float32)
    if t >= T_FOLLOW:
        k = smooth(prog(t, T_FOLLOW, T_FOLLOW + 0.3))
        arr *= 1 - 0.75 * k
        card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        ff = font(BOLD, 76)
        spaced(cd, W / 2, H / 2 - 90, "FOLLOW", ff, (250, 250, 252, int(255 * k)), 6)
        spaced(cd, W / 2, H / 2 + 6, "FOR MORE", ff, (250, 250, 252, int(255 * k)), 6)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
        base.alpha_composite(card)
        return np.asarray(base.convert("RGB"))
    return np.clip(arr, 0, 255).astype(np.uint8)


def init_worker():
    global GAME, BGS
    GAME = build_game_screen(TV[1] - TV[0], TV[3] - TV[2])
    BGS = [N.panel_bg(PW_, PH, seed=i) for i in range(4)]


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


def synth(f, dur, bright=0.6):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = sum((1 / k) * np.sin(2 * np.pi * f * k * tt) * (bright ** (k - 1)) for k in (1, 3, 5, 7))
    return x * np.minimum(1, tt / 0.004) * np.exp(-tt * 9)


def audio():
    """Night-drive synthwave: a 16th-note arpeggio and a pulsing bass from the midnight hit until 3 AM."""
    n = int(DUR * SR)
    mus, fx = np.zeros((n, 2)), np.zeros((n, 2))
    bpm = 108
    beat = 60 / bpm
    six = beat / 4
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]       # Am F C G
    # the last second before midnight: ticking
    for j, tk in enumerate((0.0, 0.25, 0.5, 0.75)):
        mix_in(fx, tone(1760 if j < 3 else 2093, 0.06, (1,), a=0.001, d=0.03), tk, 0.05)
    # midnight: a big hit
    mix_in(fx, tone(45, 1.2, (1, 0.6, 0.3), a=0.003, d=0.6), T_OUT, 0.35)
    mix_in(fx, noise(0.9, 4, lo=1500, hi=9000) * env(int(0.9 * SR), 0.005, 0.4), T_OUT, 0.08)
    tt, i = T_OUT, 0
    while tt < T_RES:
        bar_i = int((tt - T_OUT) / (4 * beat)) % 4
        ch = chords[bar_i]
        seq = [0, 1, 2, 1, 2, 0, 1, 2]
        m = ch[seq[i % 8]] + 12
        g = 0.035 + 0.03 * prog(tt, T_OUT, T_RES)
        mix_in(mus, synth(midi(m), 0.25, 0.5), tt, g, 0.3 if i % 2 else -0.3)
        if i % 2 == 0:
            mix_in(mus, synth(midi(ch[0] - 24), 0.3, 0.7) * 1.4, tt, g * 1.4)
        i += 1
        tt += six
    b = 0
    while T_OUT + b * 4 * beat < T_RES:
        t0 = T_OUT + b * 4 * beat
        for k, m in enumerate(chords[b % 4]):
            mix_in(mus, GS.pad(midi(m), min(4 * beat, T_RES - t0), 0.2, 0.6), t0, 0.03, (k - 1) * 0.4)
        # a soft kick on every beat (no snare)
        for q in range(4):
            tk = t0 + q * beat
            if tk < T_RES:
                mix_in(mus, tone(60, 0.18, (1,), a=0.002, d=0.08, sweep=40), tk, 0.12)
        b += 1
    # events: fail buzz, controller thud, RGB pings, live chime
    mix_in(fx, tone(140, 0.5, (1, 0.5, 0.3, 0.2), a=0.003, d=0.3, sweep=90), T_FAIL, 0.1, 0.2)
    mix_in(fx, noise(0.15, 9, lo=80, hi=900) * env(int(0.15 * SR), 0.002, 0.06), T_THROW + 0.9, 0.12, 0.3)
    for tk in (1.2, 2.8, 4.4, 6.0, 7.5):
        mix_in(fx, tone(2349, 0.15, (1, 0.3), a=0.002, d=0.08), tk, 0.025, 0.4)
    mix_in(fx, tone(1046, 0.25, (1, 0.3), a=0.002, d=0.12), T_LIVE, 0.04, 0.4)
    # the results: four stamps, then a warm chord
    for j in range(4):
        mix_in(fx, tone(80, 0.3, (1, 0.5), a=0.002, d=0.15) + 0.3 * noise(0.3, 30 + j, lo=500, hi=4000) *
               env(int(0.3 * SR), 0.002, 0.08), T_RES + 0.12 * j, 0.14)
    for k, m in enumerate((45, 57, 64, 69, 72)):
        mix_in(mus, GS.pad(midi(m), 3.0, 0.3, 1.6), T_RES + 0.5, 0.04, (k - 2) * 0.3)
    for j, m in enumerate((76, 72, 69, 64)):
        mix_in(mus, music.music_box(midi(m), 1.6), T_L1 + j * 0.45, 0.05, 0.2)
    for t0, s in ((T_L1, LINE1), (T_L2, LINE2)):
        for i2, c in enumerate(s):
            if c != " ":
                mix_in(fx, noise(0.03, 500 + i2 + int(t0), lo=1200, hi=4000) * env(int(0.03 * SR), 0.001, 0.008),
                       t0 + i2 / CPS, 0.05)
    x = mus + fx
    m = int(XFADE * SR)
    k = np.linspace(0, 1, m)[:, None]
    x[-m:] = x[-m:] * (1 - k) + x[:m] * k
    x /= max(1.0, np.abs(x).max() / 0.9)
    return x


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "gta6-first.mp4"
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
