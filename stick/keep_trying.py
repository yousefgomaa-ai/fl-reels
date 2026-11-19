#!/usr/bin/env python3
"""QUITS vs KEEPS GOING - two stickmen jump the same gap; each try reaches a little further. The top one quits after
try 9, the bottom one makes it on try 14 ("the one who quit was 5 tries away"). 1080x1920, PIL + numpy, music and
sounds synthesised from sines (no samples, no noise).

    python3 stick/keep_trying.py out/keep-trying.mp4
    ONLY_FRAMES=1,5,12.5,18,22 python3 stick/keep_trying.py out/k.mp4
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scroller_reader import (BLACK, BOLD, GOLD, INK, MED, RED, WHITE, clamp, midi, mix_in, out_back, out_cubic,  # noqa
                             prog, put, text, tone, write_wav)

W, H, FPS = 1080, 1920, 30
SR = 44100
QUIT_AT, MADE_IT = 9, 14
DUR = 24.5

# ---------------------------------------------------------------- the set
FLOORS = {"top": 800, "bot": 1640}
PANEL = {"top": (0, 948), "bot": (972, H)}
LEDGE, FAR = 430, 790          # the gap runs from LEDGE to FAR
START_X = 120
FLAG_X = 935


def check():
    assert MADE_IT - QUIT_AT == 5


# ---------------------------------------------------------------- attempt schedule
def durations():
    d = []
    for n in range(1, MADE_IT + 1):
        if n <= 3:
            d.append(1.55)
        elif n <= 6:
            d.append(1.05)
        elif n <= QUIT_AT:
            d.append(0.85)
        elif n < MADE_IT:
            d.append(0.95)
        else:
            d.append(2.7)          # the last try, in slow motion
    return d


T0 = 2.0
DURS = durations()
STARTS = []
_t = T0
for _n, _d in enumerate(DURS, 1):
    if _n == QUIT_AT + 1:
        _t += 0.5                  # a beat for the quit
    if _n == MADE_IT:
        _t += 0.55                 # silence before the last try
    STARTS.append(_t)
    _t += _d
T_SUCCESS_LAND = STARTS[-1] + DURS[-1] * 0.78
T_QUIT = STARTS[QUIT_AT - 1] + DURS[QUIT_AT - 1]
T_END = T_SUCCESS_LAND + 2.0


def reach(n):
    """Jump length of try n as a share of what it takes to land (>= 1 lands)."""
    if n >= MADE_IT:
        return 1.06
    return 0.42 + 0.53 * ((n - 1) / 12) ** 0.85


def closest_pct(n):
    return min(100, int(round(reach(n) * 100)))


# ---------------------------------------------------------------- poses (angles in degrees, + = forward)
def pose_from(lean=0, dy=0, tl=8, sl=0, tr=-8, sr=0, al=-12, bl=10, ar=12, br=10):
    r = math.radians
    hip = (0.0, -180.0 + dy)
    neck = (hip[0] + 160 * math.sin(r(lean)), hip[1] - 160 * math.cos(r(lean)))
    head = (neck[0] + 54 * math.sin(r(lean)), neck[1] - 54 * math.cos(r(lean)))

    def limb(o, a1, a2, l1, l2):
        m = (o[0] + l1 * math.sin(r(a1)), o[1] + l1 * math.cos(r(a1)))
        e = (m[0] + l2 * math.sin(r(a1 + a2)), m[1] + l2 * math.cos(r(a1 + a2)))
        return m, e

    kl, fl = limb(hip, tl, sl, 95, 95)
    kr, fr = limb(hip, tr, sr, 95, 95)
    el, hl = limb(neck, al, bl, 80, 75)
    er, hr = limb(neck, ar, br, 80, 75)
    return {"head": head, "neck": neck, "hip": hip, "kl": kl, "fl": fl, "kr": kr, "fr": fr, "el": el, "hl": hl,
            "er": er, "hr": hr}


def stand(t):
    return pose_from(lean=2, dy=math.sin(t * 2.4) * 2)


def run(phase):
    s = math.sin(phase)
    return pose_from(lean=16, dy=-abs(math.cos(phase)) * 8, tl=42 * s, sl=-25 - 55 * max(0, -s), tr=-42 * s,
                     sr=-25 - 55 * max(0, s), al=-40 * s, bl=75, ar=40 * s, br=75)


def jump(x):
    """x 0..1 through the flight: stretch, tuck, reach."""
    tuck = math.sin(x * math.pi)
    return pose_from(lean=20, tl=30 + 40 * tuck, sl=-30 - 70 * tuck, tr=10 + 50 * tuck, sr=-20 - 80 * tuck,
                     al=120 + 30 * x, bl=-10, ar=140 + 20 * x, br=-10)


def fall(t):
    w = math.sin(t * 22) * 25
    return pose_from(lean=-12, tl=25, sl=-35, tr=-20, sr=-30, al=165 + w, bl=20, ar=-165 - w, br=-20)


def sit_down(x):
    """x 0..1 from standing to sitting on the ground hugging the knees, head down."""
    a = pose_from(lean=2)
    b = pose_from(lean=28, dy=130, tl=75, sl=-150, tr=65, sr=-140, al=55, bl=-40, ar=45, br=-50)
    return {k: (a[k][0] + (b[k][0] - a[k][0]) * x, a[k][1] + (b[k][1] - a[k][1]) * x) for k in a}


def cheer(t):
    j = abs(math.sin(t * 7)) * 14
    return pose_from(lean=-4, dy=-j, tl=6, tr=-6, al=170 + math.sin(t * 9) * 8, bl=5, ar=-170 - math.sin(t * 9) * 8, br=-5)


def land(x):
    """Crouch on landing (x 0..1 -> back up)."""
    c = math.sin(min(1, x) * math.pi)
    return pose_from(lean=22 * c, dy=55 * c, tl=55 * c, sl=-100 * c, tr=40 * c, sr=-90 * c, al=60, bl=20, ar=80, br=10)


# ---------------------------------------------------------------- stickman drawing
SCALE = 0.8


def draw_stick(pose, face="calm", glow=0.0):
    k = 2
    box = 560
    im = Image.new("RGBA", (box * k, box * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ox, oy = box / 2, box - 30
    s = SCALE

    def P(n):
        x, y = pose[n]
        return ((ox + x * s) * k, (oy + y * s) * k)

    body = tuple(int(a + (b - a) * glow) for a, b in zip((238, 238, 234), (255, 220, 130)))
    shade = tuple(int(c * 0.8) for c in body)
    back = [("hip", "kr"), ("kr", "fr"), ("neck", "er"), ("er", "hr")]
    front = [("neck", "hip"), ("hip", "kl"), ("kl", "fl"), ("neck", "el"), ("el", "hl")]
    ow, fw = 38 * s * k, 25 * s * k
    for segs, col in ((back, shade), (front, body)):
        for a, b in segs:
            d.line([P(a), P(b)], fill=INK + (255,), width=int(ow), joint="curve")
            for p in (P(a), P(b)):
                d.ellipse([p[0] - ow / 2, p[1] - ow / 2, p[0] + ow / 2, p[1] + ow / 2], fill=INK + (255,))
        for a, b in segs:
            d.line([P(a), P(b)], fill=col + (255,), width=int(fw), joint="curve")
            for p in (P(a), P(b)):
                d.ellipse([p[0] - fw / 2, p[1] - fw / 2, p[0] + fw / 2, p[1] + fw / 2], fill=col + (255,))
    hx, hy = P("head")
    r = 50 * s * k
    d.ellipse([hx - r - 6 * s * k, hy - r - 6 * s * k, hx + r + 6 * s * k, hy + r + 6 * s * k], fill=INK + (255,))
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=body + (255,))
    d.ellipse([hx - r * 0.6, hy - r * 0.78, hx - r * 0.1, hy - r * 0.35], fill=(255, 255, 255, 110))
    # face, looking right
    ex, ey, er_ = hx + r * 0.38, hy - r * 0.08, r * 0.11
    if face == "sad":
        ey += r * 0.18
    for dx in (0, r * 0.36):
        d.ellipse([ex + dx - er_, ey - er_, ex + dx + er_, ey + er_], fill=INK + (255,))
    mx, my = ex + r * 0.18, hy + r * 0.42
    mw = r * 0.26
    if face == "happy":
        d.arc([mx - mw, my - mw * 1.1, mx + mw, my + mw * 0.6], 10, 170, fill=INK + (255,), width=int(5 * s * k))
    elif face == "sad":
        d.arc([mx - mw, my, mx + mw, my + mw * 1.4], 200, 340, fill=INK + (255,), width=int(5 * s * k))
    elif face == "scared":
        d.ellipse([mx - mw * 0.4, my - mw * 0.2, mx + mw * 0.4, my + mw * 0.6], fill=INK + (255,))
    else:
        d.line([(mx - mw * 0.7, my), (mx + mw * 0.7, my)], fill=INK + (255,), width=int(5 * s * k))
    im = im.resize((box, box), Image.LANCZOS)
    return im, (ox, oy)


def put_clipped(c, spr, anchor, at, panel, alpha=1.0):
    """Paste the stickman with its feet anchor at `at`, clipped to its half of the screen."""
    if alpha <= 0.01:
        return
    if alpha < 0.999:
        spr = spr.copy()
        spr.putalpha(spr.split()[3].point(lambda v: int(v * alpha)))
    x, y = int(at[0] - anchor[0]), int(at[1] - anchor[1])
    y0, y1 = PANEL[panel]
    sx, sy = max(0, -x), max(0, y0 - y)
    ex, ey = min(spr.width, W - x), min(spr.height, y1 - y)
    if ex > sx and ey > sy:
        c.alpha_composite(spr, (x + sx, y + sy), (sx, sy, ex, ey))


# ---------------------------------------------------------------- background
def background():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img = np.zeros((H, W, 3), np.float32) + np.array([12, 12, 14], np.float32)
    light = np.zeros((H, W), np.float32)
    for panel in ("top", "bot"):
        fl = FLOORS[panel]
        y0, y1 = PANEL[panel]
        lx, ly = (LEDGE + FAR) / 2, y0 + 210
        inside = (yy >= ly) & (yy <= fl) & (yy >= y0) & (yy < y1)
        depth = np.clip((yy - ly) / (fl - ly), 0, 1)
        half = 40 + depth * 420
        light += np.where(inside, np.clip(1 - np.abs(xx - lx) / half, 0, 1) ** 1.7 * (0.5 + 0.3 * (1 - depth)), 0) * 0.5
        light += np.exp(-(((xx - lx) ** 2 + (yy - ly - 18) ** 2) / (2 * 55 ** 2))) * 0.9 * (yy >= y0) * (yy < y1)
        light += np.exp(-(((xx - 260) / 260) ** 2 + ((yy - fl) / 28) ** 2)) * 0.5
        light += np.exp(-(((xx - 920) / 200) ** 2 + ((yy - fl) / 28) ** 2)) * 0.5
    img += light[..., None] * np.array([255, 214, 160], np.float32) / 255 * 100
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    k = 2
    lay = Image.new("RGBA", (W * k, H * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    o = INK + (255,)
    for panel in ("top", "bot"):
        fl = FLOORS[panel]
        y0, y1 = PANEL[panel]
        lx, ly = (LEDGE + FAR) / 2, y0 + 210
        d.line([(lx * k, (ly - 120) * k), (lx * k, (ly - 18) * k)], fill=(60, 60, 62, 255), width=4 * k)
        d.polygon([((lx - 44) * k, (ly + 14) * k), ((lx + 44) * k, (ly + 14) * k), ((lx + 20) * k, (ly - 22) * k),
                   ((lx - 20) * k, (ly - 22) * k)], fill=(52, 52, 56, 255))
        d.ellipse([(lx - 12) * k, (ly + 6) * k, (lx + 12) * k, (ly + 26) * k], fill=(255, 236, 200, 255))
        bottom = min(y1 - 2, fl + 150)
        # platforms: a lit top edge and a dark block
        for xa, xb in ((40, LEDGE), (FAR, 1040)):
            d.rectangle([xa * k, fl * k, xb * k, bottom * k], fill=(46, 46, 50, 255), outline=o, width=5 * k)
            d.rectangle([xa * k, fl * k, xb * k, (fl + 14) * k], fill=(96, 96, 102, 255), outline=o, width=4 * k)
        # the gap fades to black
        for i in range(30):
            a = int(255 * i / 29)
            yt = fl + i * (bottom - fl) / 30
            d.rectangle([(LEDGE + 3) * k, yt * k, (FAR - 3) * k, (yt + (bottom - fl) / 30 + 1) * k], fill=(0, 0, 0, a))
        # flag on the far side
        d.line([(FLAG_X * k, (fl - 210) * k), (FLAG_X * k, fl * k)], fill=o, width=12 * k)
        d.line([(FLAG_X * k, (fl - 210) * k), (FLAG_X * k, fl * k)], fill=(200, 200, 200, 255), width=6 * k)
        d.polygon([(FLAG_X * k, (fl - 206) * k), ((FLAG_X + 92) * k, (fl - 178) * k), (FLAG_X * k, (fl - 150) * k)],
                  fill=GOLD + (255,), outline=o, width=4 * k)
    d.rectangle([0, 948 * k, W * k, 972 * k], fill=(7, 7, 8, 255))
    d.line([(0, 948 * k), (W * k, 948 * k)], fill=(58, 58, 62, 255), width=2 * k)
    d.line([(0, 972 * k), (W * k, 972 * k)], fill=(58, 58, 62, 255), width=2 * k)
    im.alpha_composite(lay.resize((W, H), Image.LANCZOS))
    return im


# ---------------------------------------------------------------- one runner
def runner_state(t, who):
    """(pose, x, y_offset_from_floor, alpha, face, attempts_so_far, closest) for 'top' (quits) or 'bot'."""
    last = QUIT_AT if who == "top" else MADE_IT
    attempts, closest = 0, 0
    for n in range(1, last + 1):
        s, d = STARTS[n - 1], DURS[n - 1]
        if t < s:
            break
        attempts = n
        if t >= s + d * 0.7:
            closest = max(closest, closest_pct(n))
    if attempts == 0:
        return stand(t), START_X, 0, 1.0, "calm", 0, 0
    n = attempts
    s, d = STARTS[n - 1], DURS[n - 1]
    lt = t - s
    L = reach(n) * (FAR + 10 - (LEDGE - 20))
    takeoff = LEDGE - 20
    if who == "top" and n == QUIT_AT and lt > d:
        # respawned at the start, sits down for good
        x = out_cubic(prog(t, T_QUIT + 0.15, 0.6))
        return sit_down(x), START_X + 40, 0, clamp((t - T_QUIT) / 0.25), "sad" if x > 0.3 else "calm", n, closest
    if n == MADE_IT:
        run_d, fly_d = 0.85, 1.2       # slow motion over the gap
    else:
        run_d, fly_d = d * 0.38, d * 0.32
    if lt < run_d:
        x = START_X + (takeoff - START_X) * (lt / run_d)
        a = clamp(lt / 0.12) if n > 1 else 1.0
        return run(lt / run_d * math.pi * 3), x, 0, a, "calm", n, closest
    if lt < run_d + fly_d:
        u = (lt - run_d) / fly_d
        x = takeoff + L * u
        y = -120 * 4 * u * (1 - u)
        return jump(u), x, y, 1.0, "calm", n, closest
    rest = lt - run_d - fly_d
    xend = takeoff + L
    if n == MADE_IT:
        if rest < 0.45:
            return land(rest / 0.45), xend, 0, 1.0, "happy", n, 100
        return cheer(t), xend, 0, 1.0, "happy", n, 100
    # missed: falls into the gap and fades
    y = 900 * rest ** 2 + 120 * rest
    a = 1 - clamp((rest - 0.12) / 0.18)
    return fall(t), xend + 60 * rest, y, a, "scared", n, closest


# ---------------------------------------------------------------- frame
BG = None


def frame(t):
    global BG
    if BG is None:
        BG = background()
    c = BG.copy()
    lamps = out_cubic(prog(t, 0.05, 0.4))
    if lamps < 1:
        c = Image.blend(Image.new("RGBA", (W, H), (8, 8, 9, 255)), c, lamps)
    d = ImageDraw.Draw(c)

    states = {}
    for who in ("top", "bot"):
        pose, x, yo, a, face, n, closest = runner_state(t, who)
        states[who] = (n, closest)
        glow = out_cubic(prog(t, T_SUCCESS_LAND, 0.5)) if who == "bot" and t >= T_SUCCESS_LAND else 0
        spr, anc = draw_stick(pose, face, glow)
        put_clipped(c, spr, anc, (x, FLOORS[who] + yo), who, a)

    if t >= T_SUCCESS_LAND:  # gold burst behind the winner
        g = out_cubic(prog(t, T_SUCCESS_LAND, 0.4)) * (1 - 0.5 * prog(t, T_SUCCESS_LAND + 0.4, 1.0))
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fl = FLOORS["bot"]
        ImageDraw.Draw(glow).ellipse([FAR + 10, fl - 330, 1060, fl + 20], fill=GOLD + (int(120 * g),))
        c.alpha_composite(glow.filter(ImageFilter.GaussianBlur(40)))

    ui = out_cubic(prog(t, 1.9, 0.4)) * (1 - 0.85 * out_cubic(prog(t, T_END, 0.5)))
    for who, y0 in (("top", 0), ("bot", 972)):
        n, closest = states[who]
        put(c, text("ATTEMPTS", 28, (150, 150, 150), MED, spacing=6), 190, y0 + 74, 1, ui)
        bump = 1 + 0.25 * math.exp(-((t - STARTS[max(0, n - 1)]) * 7) ** 2) if n else 1
        put(c, text(str(n), 76, WHITE, BLACK), 190, y0 + 138, bump, ui)
        put(c, text("CLOSEST", 28, (150, 150, 150), MED, spacing=6), W - 190, y0 + 74, 1, ui)
        col = GOLD if closest >= 100 else WHITE
        put(c, text(f"{closest}%", 76, col, BLACK), W - 190, y0 + 138, 1, ui)
    # labels appear when the story decides them
    if t >= T_QUIT + 0.3:
        p = out_back(prog(t, T_QUIT + 0.3, 0.4), 2)
        put(c, text("QUIT", 54, RED, BLACK, spacing=6), W / 2, 110, 0.6 + 0.4 * p, clamp(p) * ui)
    else:
        put(c, text("SAME GAP", 30, (170, 170, 170), MED, spacing=8), W / 2, 110, 1, ui)
    if t >= T_SUCCESS_LAND:
        p = out_back(prog(t, T_SUCCESS_LAND, 0.4), 2)
        put(c, text("KEPT GOING", 54, GOLD, BLACK, spacing=6), W / 2, 972 + 110, 0.6 + 0.4 * p, clamp(p) * ui)
    else:
        put(c, text("SAME SKILL", 30, (170, 170, 170), MED, spacing=8), W / 2, 972 + 110, 1, ui)

    # hook
    if t < 2.5:
        p = out_back(prog(t, 0.15, 0.4), 1.6)
        a = 1 - prog(t, 2.0, 0.45)
        put(c, text("HOW MANY TIMES", 88, WHITE, BLACK), W / 2, 905, 0.6 + 0.4 * p, min(1, p * 2) * a)
        p2 = out_back(prog(t, 0.55, 0.4), 1.6)
        put(c, text("WOULD YOU TRY?", 88, GOLD, BLACK), W / 2, 1012, 0.6 + 0.4 * p2, min(1, prog(t, 0.55, 0.2) * 2) * a)

    # end card
    if t >= T_END:
        p = out_cubic(prog(t, T_END, 0.5))
        c.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(170 * p))))
        put(c, text("THE ONE WHO QUIT", 80, WHITE, BLACK), W / 2, 780, 0.8 + 0.2 * out_back(prog(t, T_END, 0.45)), p)
        p2 = prog(t, T_END + 0.6, 0.45)
        put(c, text("WAS 5 TRIES AWAY.", 92, GOLD, BLACK), W / 2, 895, 0.8 + 0.2 * out_back(p2), p2)
        p3 = prog(t, T_END + 1.6, 0.45)
        put(c, text("HOW MANY TIMES", 58, WHITE, BOLD, spacing=3), W / 2, 1060, 0.85 + 0.15 * out_back(p3), p3)
        put(c, text("WOULD YOU TRY?", 58, WHITE, BOLD, spacing=3), W / 2, 1130, 0.85 + 0.15 * out_back(p3), p3)
        p4 = prog(t, T_END + 2.2, 0.4)
        if p4 > 0:
            ar = Image.new("RGBA", (90, 110), (0, 0, 0, 0))
            dd = ImageDraw.Draw(ar)
            dd.rounded_rectangle([33, 0, 57, 60], 8, fill=GOLD + (255,))
            dd.polygon([(5, 52), (85, 52), (45, 106)], fill=GOLD + (255,))
            put(c, ar, W / 2, 1250 + 16 * abs(math.sin(t * 5)), 1, p4)

    d = ImageDraw.Draw(c)
    d.rectangle([0, 0, int(W * t / DUR), 6], fill=GOLD + (255,))
    out = c.convert("RGB")
    if T_SUCCESS_LAND <= t < T_SUCCESS_LAND + 0.3:  # small shake on the landing
        a = 12 * (1 - (t - T_SUCCESS_LAND) / 0.3)
        base = out.copy()
        out.paste(base, (int(a * math.sin(t * 90)), int(a * math.cos(t * 70))))
    return out


# ---------------------------------------------------------------- audio
def audio():
    n = int(DUR * SR)
    mus, fx = np.zeros((n, 2)), np.zeros((n, 2))
    t_last = STARTS[-1]
    # tense pulse in A minor that grows with each try, stops before the last try
    chords = [[45, 52, 57, 60], [41, 48, 53, 57], [43, 50, 55, 59], [40, 47, 52, 56]]
    b = 0
    while b * 2.0 < t_last:
        t0 = b * 2.0
        ch = chords[b % 4]
        grow = clamp(t0 / t_last)
        for k, m in enumerate(ch):
            mix_in(mus, tone(midi(m), 2.1, (1, 0.45, 0.2, 0.08), a=0.05, d=1.2), t0, 0.045 + 0.04 * grow, (k - 1.5) * 0.3)
        step = 0.25 if t0 < 9 else 0.125
        j = 0
        while j * step < 2.0 and t0 + j * step < t_last - 0.1:
            m = ch[j % 4] + 12
            mix_in(mus, tone(midi(m), 0.3, (1, 0.35, 0.1), a=0.003, d=0.07), t0 + j * step, 0.05 + 0.03 * grow,
                   -0.4 if j % 2 else 0.4)
            j += 1
        if t0 >= 2.0:
            for q in range(4):
                if t0 + q * 0.5 < t_last - 0.1:
                    mix_in(mus, tone(110, 0.3, (1,), a=0.002, d=0.1, sweep=42), t0 + q * 0.5, 0.45 + 0.3 * grow)
        b += 1
    # each try: footsteps, a whoosh on take-off, and either a falling whistle + thud or the landing
    for i, (s, d) in enumerate(zip(STARTS, DURS), 1):
        run_d, fly_d = (0.85, 1.2) if i == MADE_IT else (d * 0.38, d * 0.32)
        steps = 4
        for k in range(steps):
            mix_in(fx, tone(180, 0.06, (1, 0.5), a=0.001, d=0.02), s + run_d * k / steps, 0.12, -0.2)
        ts = np.arange(int(0.3 * SR)) / SR
        fr = 300 * (1300 / 300) ** (ts / 0.3)
        wh = sum(np.sin(2 * np.pi * np.cumsum(fr * m) / SR) / (q + 1) for q, m in enumerate([1, 1.01, 1.5]))
        wh *= np.sin(np.pi * ts / 0.3) ** 2
        mix_in(fx, wh, s + run_d - 0.05, 0.07)
        if i < MADE_IT:
            mix_in(fx, tone(900, 0.5, (1, 0.3), a=0.01, d=0.3, sweep=250), s + run_d + fly_d, 0.07)
            mix_in(fx, tone(70, 0.4, (1, 0.5), a=0.002, d=0.1, sweep=40), s + run_d + fly_d + 0.33, 0.45)
    # the quit: two falling notes
    for k, m in enumerate([64, 60]):
        mix_in(fx, tone(midi(m), 0.6, (1, 0.4, 0.2), a=0.01, d=0.35), T_QUIT + 0.3 + k * 0.28, 0.12)
    # before the last try: heartbeat in the silence
    for k in range(3):
        hb = t_last - 0.55 + k * 0.6
        mix_in(fx, tone(60, 0.25, (1, 0.3), a=0.002, d=0.08, sweep=40), hb, 0.6)
        mix_in(fx, tone(60, 0.25, (1, 0.3), a=0.002, d=0.07, sweep=40), hb + 0.2, 0.4)
    # landing: impact + bright chord + chimes
    mix_in(fx, tone(85, 1.2, (1, 0.5), a=0.002, d=0.35, sweep=30), T_SUCCESS_LAND, 0.9)
    for k, m in enumerate([57, 61, 64, 69, 73]):
        mix_in(mus, tone(midi(m), 5, (1, 0.35, 0.12), a=0.02, d=2.2), T_SUCCESS_LAND + 0.02 + k * 0.05, 0.075, (k - 2) * 0.3)
    for k, m in enumerate([69, 73, 76, 81]):
        mix_in(fx, sum(tone(midi(m) * h, 1.2, (1,), a=0.002, d=dd) * g for h, dd, g in
                       [(1, 0.8, 1), (2.0, 0.4, 0.35), (3.01, 0.25, 0.2)]), T_SUCCESS_LAND + 0.1 + k * 0.08, 0.1)
    for k, m in enumerate([45, 52, 57, 61, 64]):
        mix_in(mus, tone(midi(m), DUR - T_END, (1, 0.3), a=0.6, d=6), T_END, 0.05, (k - 2) * 0.3)
    tt = np.arange(n) / SR
    fade = np.clip((DUR - tt) / 0.8, 0, 1) * np.clip(tt / 0.01, 0, 1)
    x = (mus * 0.9 + fx) * fade[:, None]
    x -= x.mean(axis=0)
    x = np.tanh(x * 1.2)
    return x * (0.89 / np.abs(x).max())


def main():
    check()
    out = sys.argv[1] if len(sys.argv) > 1 else "out/keep-trying.mp4"
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
    for i in range(int(DUR * FPS)):
        ff.stdin.write(frame(i / FPS).tobytes())
        if i % 90 == 0:
            print(f"frame {i}", flush=True)
    ff.stdin.close()
    if ff.wait():
        raise SystemExit("ffmpeg failed")
    os.remove(wav)
    print("wrote", out)


if __name__ == "__main__":
    main()
