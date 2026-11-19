#!/usr/bin/env python3
"""WAITS vs STARTS - one scene, 14.4 s, loops on itself.

A grey stickman waits at a bus stop marked MOTIVATION ("ANY MINUTE." "TOMORROW." "AFTER COFFEE." "MONDAY."), a white
one climbs the stairs next to him. The MOTIVATION bus finally comes - at the top of the stairs, for the climber.
"MOTIVATION SHOWS UP AFTER YOU DO." is typed out, and the last half second fades back into the first frame.
1080x1920, PIL + numpy, music synthesised from sines (no samples, no noise), bar-aligned so the loop is seamless.

    python3 stick/motivation_bus.py out/motivation-bus.mp4
    ONLY_FRAMES=0,3.2,9.6,12.5 python3 stick/motivation_bus.py out/m.mp4
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scroller_reader import GOLD, INK, clamp, midi, mix_in, out_back, out_cubic, prog, put, tone, write_wav  # noqa
from keep_trying import pose_from  # noqa

W, H, FPS = 1080, 1920, 30
SR = 44100
BPM = 100
BAR = 4 * 60 / BPM                     # 2.4 s
DUR = 6 * BAR                          # 14.4 s: whole bars, so the music loops cleanly

MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
if not os.path.exists(MONO):
    MONO = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"
_f = {}


def FM(s):
    if s not in _f:
        _f[s] = ImageFont.truetype(MONO, s)
    return _f[s]


# ---------------------------------------------------------------- scene geometry
GROUND = 1540
STEP_W, STEP_H, STEPS = 27, 68, 12
STAIR_X0 = 450                          # first step's left edge
TOP_Y = GROUND - STEPS * STEP_H         # 604
TOP_X0 = STAIR_X0 + STEPS * STEP_W      # 1010: the top landing starts here... and runs off screen
SIGN_X = 200

T_STEP0, T_STEP = 0.35, 0.7             # one step every 0.7 s
T_TOP = T_STEP0 + STEPS * T_STEP        # 9.35
T_BUS0, T_BUS1 = 8.9, 9.7
T_BOARD = 10.1
T_TEXT = 10.5
T_LOOP = DUR - 0.5
BUBBLES = [(0.7, 1.9, "ANY MINUTE."), (2.7, 3.9, "TOMORROW."), (4.7, 5.9, "AFTER COFFEE."), (6.7, 7.9, "MONDAY."),
           (9.5, 10.4, "?"), (10.5, 13.6, "...")]
LINE1, LINE2 = "MOTIVATION SHOWS UP", "AFTER YOU DO."


def step_at(t):
    return int(clamp((t - T_STEP0) / T_STEP, 0, STEPS))


# ---------------------------------------------------------------- drawing helpers
def mono_text(s, size, fill=(235, 235, 230), spacing=2):
    f = FM(size)
    w = int(f.getlength(s) + spacing * max(0, len(s) - 1)) + 8
    asc, desc = f.getmetrics()
    im = Image.new("RGBA", (max(w, 8), asc + desc + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 4
    for ch in s:
        d.text((x, 4), ch, font=f, fill=fill + (255,))
        x += f.getlength(ch) + spacing
    return im


def bubble(s):
    tx = mono_text(s, 34, INK, spacing=1)
    pw, ph = tx.width + 36, tx.height + 22
    k = 2
    im = Image.new("RGBA", (pw * k, (ph + 22) * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([3 * k, 3 * k, (pw - 3) * k, (ph - 3) * k], 12 * k, fill=(240, 238, 232, 255), outline=INK + (255,), width=4 * k)
    d.polygon([(pw * 0.30 * k, (ph - 6) * k), (pw * 0.30 * k + 26 * k, (ph - 6) * k), (pw * 0.24 * k, (ph + 18) * k)], fill=INK + (255,))
    d.polygon([(pw * 0.30 * k + 5 * k, (ph - 8) * k), (pw * 0.30 * k + 19 * k, (ph - 8) * k), (pw * 0.255 * k, (ph + 10) * k)], fill=(240, 238, 232, 255))
    im = im.resize((pw, ph + 22), Image.LANCZOS)
    im.alpha_composite(tx, (18, 9))
    return im


_bub = {}


def get_bubble(s):
    if s not in _bub:
        _bub[s] = bubble(s)
    return _bub[s]


def draw_stick(pose, body, face="calm", look=1, scale=0.95, prop=None):
    """2x supersampled stickman: dark outline, light fill, a little shading; look = 1 right / -1 left / 0 up."""
    k = 2
    box = 640
    im = Image.new("RGBA", (box * k, box * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ox, oy = box / 2, box - 40
    s = scale

    def P(n):
        x, y = pose[n]
        return ((ox + x * s) * k, (oy + y * s) * k)

    shade = tuple(int(c * 0.78) for c in body)
    back = [("hip", "kr"), ("kr", "fr"), ("neck", "er"), ("er", "hr")]
    front = [("neck", "hip"), ("hip", "kl"), ("kl", "fl"), ("neck", "el"), ("el", "hl")]
    ow, fw = 40 * s * k, 27 * s * k
    for segs, col in ((back, shade), (front, body)):
        for a, b in segs:
            d.line([P(a), P(b)], fill=INK + (255,), width=int(ow), joint="curve")
            for p in (P(a), P(b)):
                d.ellipse([p[0] - ow / 2, p[1] - ow / 2, p[0] + ow / 2, p[1] + ow / 2], fill=INK + (255,))
        for a, b in segs:
            d.line([P(a), P(b)], fill=col + (255,), width=int(fw), joint="curve")
            for p in (P(a), P(b)):
                d.ellipse([p[0] - fw / 2, p[1] - fw / 2, p[0] + fw / 2, p[1] + fw / 2], fill=col + (255,))
    if prop == "cup":
        x, y = P("hl")
        d.rounded_rectangle([x - 4 * k, y - 34 * k, x + 26 * k, y + 4 * k], 5 * k, fill=(200, 200, 196, 255), outline=INK + (255,), width=4 * k)
    hx, hy = P("head")
    r = 52 * s * k
    d.ellipse([hx - r - 7 * s * k, hy - r - 7 * s * k, hx + r + 7 * s * k, hy + r + 7 * s * k], fill=INK + (255,))
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=body + (255,))
    d.ellipse([hx - r * 0.6, hy - r * 0.8, hx - r * 0.1, hy - r * 0.36], fill=(255, 255, 255, 90))
    if look == 0:
        ex, ey = hx - r * 0.18, hy - r * 0.38
    else:
        ex, ey = hx + look * r * 0.30 - (r * 0.18 if look < 0 else 0), hy - r * 0.05
    er_ = r * 0.11
    for dx in (0, r * 0.36):
        d.ellipse([ex + dx - er_, ey - er_, ex + dx + er_, ey + er_], fill=INK + (255,))
    mx, my, mw = ex + r * 0.18, ey + r * 0.45, r * 0.24
    lw = int(5 * s * k)
    if face == "happy":
        d.arc([mx - mw, my - mw * 1.1, mx + mw, my + mw * 0.6], 10, 170, fill=INK + (255,), width=lw)
    elif face == "sad":
        d.arc([mx - mw, my, mx + mw, my + mw * 1.3], 200, 340, fill=INK + (255,), width=lw)
    elif face == "o":
        d.ellipse([mx - mw * 0.35, my - mw * 0.1, mx + mw * 0.35, my + mw * 0.6], fill=INK + (255,))
    else:
        d.line([(mx - mw * 0.6, my), (mx + mw * 0.6, my)], fill=INK + (255,), width=lw)
    im = im.resize((box, box), Image.LANCZOS)
    return im, (ox, oy)


def paste_at(c, spr, anc, x, y, alpha=1.0, glow=None):
    if glow:
        g = spr.split()[3].filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * glow))
        gl = Image.new("RGBA", spr.size, (255, 255, 255, 0))
        gl.putalpha(g)
        c.alpha_composite(gl, (int(x - anc[0]), int(y - anc[1])))
    if alpha < 0.999:
        spr = spr.copy()
        spr.putalpha(spr.split()[3].point(lambda v: int(v * alpha)))
    c.alpha_composite(spr, (int(x - anc[0]), int(y - anc[1])))


# ---------------------------------------------------------------- the set
def background():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img = np.zeros((H, W, 3), np.float32) + np.array([11, 11, 13], np.float32)
    light = np.zeros((H, W), np.float32)
    # a street lamp over the bus stop, another over the top landing
    for lx, ly, fl, wid in ((SIGN_X + 70, 980, GROUND, 330), (880, 330, TOP_Y, 230)):
        inside = (yy >= ly) & (yy <= fl)
        depth = np.clip((yy - ly) / (fl - ly), 0, 1)
        half = 30 + depth * wid
        light += np.where(inside, np.clip(1 - np.abs(xx - lx) / half, 0, 1) ** 1.6 * (0.45 + 0.35 * (1 - depth)), 0) * 0.55
        light += np.exp(-(((xx - lx) / (wid * 0.9)) ** 2 + ((yy - fl) / 30) ** 2)) * 0.7
        light += np.exp(-(((xx - lx) ** 2 + (yy - ly) ** 2) / (2 * 50 ** 2))) * 0.9
    img += light[..., None] * np.array([255, 212, 158], np.float32) / 255 * 105
    photo = os.environ.get("BG_PHOTO")
    if photo:
        # a real photo behind the drawn set: cover-fit, a little blur (depth), darker at the top for the counter
        # and the typed line, then the drawn stairs, sign and characters stay crisp in front
        ph = Image.open(photo).convert("RGB")
        sc = max(W / ph.width, H / ph.height)
        ph = ph.resize((int(ph.width * sc + 1), int(ph.height * sc + 1)), Image.LANCZOS)
        ph = ph.crop(((ph.width - W) // 2, (ph.height - H) // 2, (ph.width - W) // 2 + W, (ph.height - H) // 2 + H))
        ph = ph.filter(ImageFilter.GaussianBlur(float(os.environ.get("BG_BLUR", "3"))))
        a = np.asarray(ph).astype(np.float32) * float(os.environ.get("BG_DIM", "0.78"))
        top = np.clip(1 - yy / 520, 0, 1)[..., None]
        a = a * (1 - 0.55 * top)
        img = a
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    k = 2
    lay = Image.new("RGBA", (W * k, H * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    o = INK + (255,)
    # ground
    d.rectangle([0, GROUND * k, W * k, (GROUND + 14) * k], fill=(88, 88, 94, 255), outline=o, width=4 * k)
    d.rectangle([0, (GROUND + 14) * k, W * k, H * k], fill=(26, 26, 30, 255))
    # stairs: each step a block from the ground up
    for i in range(STEPS):
        x0 = STAIR_X0 + i * STEP_W
        y0 = GROUND - (i + 1) * STEP_H
        d.rectangle([x0 * k, y0 * k, (x0 + STEP_W + 1) * k, GROUND * k], fill=(54, 54, 60, 255))
        d.line([(x0 * k, y0 * k), ((x0 + STEP_W) * k, y0 * k)], fill=(120, 120, 126, 255), width=5 * k)
        d.line([(x0 * k, y0 * k), (x0 * k, (y0 + STEP_H) * k)], fill=o, width=4 * k)
    # top landing (where the bus stops)
    d.rectangle([TOP_X0 * k, TOP_Y * k, W * k, GROUND * k], fill=(54, 54, 60, 255))
    d.rectangle([(STAIR_X0 + (STEPS - 1) * STEP_W) * k, TOP_Y * k, W * k, (TOP_Y + 12) * k], fill=(120, 120, 126, 255), outline=o, width=4 * k)
    # street lamps (the photo brings its own lights)
    for lx, ly, base in (() if photo else ((SIGN_X + 70, 980, GROUND), (880, 330, TOP_Y))):
        d.line([((lx + 90) * k, (ly - 10) * k), ((lx + 90) * k, base * k)], fill=o, width=12 * k)
        d.line([((lx + 90) * k, (ly - 10) * k), ((lx + 90) * k, base * k)], fill=(70, 70, 76, 255), width=6 * k)
        d.line([(lx * k, (ly - 10) * k), ((lx + 92) * k, (ly - 10) * k)], fill=(70, 70, 76, 255), width=8 * k)
        d.polygon([((lx - 30) * k, (ly + 6) * k), ((lx + 30) * k, (ly + 6) * k), ((lx + 14) * k, (ly - 14) * k), ((lx - 14) * k, (ly - 14) * k)], fill=(60, 60, 64, 255))
        d.ellipse([(lx - 10) * k, ly * k, (lx + 10) * k, (ly + 18) * k], fill=(255, 236, 200, 255))
    # bus stop sign
    sx = SIGN_X
    d.line([(sx * k, (GROUND - 420) * k), (sx * k, GROUND * k)], fill=o, width=14 * k)
    d.line([(sx * k, (GROUND - 420) * k), (sx * k, GROUND * k)], fill=(150, 150, 156, 255), width=7 * k)
    d.ellipse([(sx - 52) * k, (GROUND - 520) * k, (sx + 52) * k, (GROUND - 416) * k], fill=GOLD + (255,), outline=o, width=5 * k)
    d.rounded_rectangle([(sx - 196) * k, (GROUND - 400) * k, (sx + 8) * k, (GROUND - 350) * k], 8 * k, fill=(230, 228, 220, 255), outline=o, width=4 * k)
    im.alpha_composite(lay.resize((W, H), Image.LANCZOS))
    f = FM(26)
    dd = ImageDraw.Draw(im)
    dd.text((sx, GROUND - 468), "BUS", font=FM(30), fill=INK + (255,), anchor="mm")
    dd.text((sx - 94, GROUND - 375), "MOTIVATION", font=f, fill=INK + (255,), anchor="mm")
    return im


def bus_sprite():
    k = 2
    w, h = 470, 230
    im = Image.new("RGBA", (w * k, (h + 40) * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    o = INK + (255,)
    d.rounded_rectangle([4 * k, 4 * k, (w - 4) * k, h * k], 30 * k, fill=(214, 150, 62, 255), outline=o, width=6 * k)
    d.rectangle([4 * k, (h - 46) * k, (w - 4) * k, (h - 34) * k], fill=(160, 100, 40, 255))
    for i in range(4):
        x = 70 + i * 92
        d.rounded_rectangle([x * k, 40 * k, (x + 76) * k, 110 * k], 10 * k, fill=(40, 46, 58, 255), outline=o, width=4 * k)
    d.rounded_rectangle([18 * k, 40 * k, 58 * k, (h - 50) * k], 8 * k, fill=(60, 66, 78, 255), outline=o, width=4 * k)   # door (front)
    d.rounded_rectangle([75 * k, 128 * k, 275 * k, 168 * k], 8 * k, fill=(250, 240, 210, 255), outline=o, width=4 * k)
    for x in (100, 370):
        d.ellipse([(x - 36) * k, (h - 36) * k, (x + 36) * k, (h + 36) * k], fill=(30, 30, 34, 255), outline=o, width=5 * k)
        d.ellipse([(x - 13) * k, (h - 13) * k, (x + 13) * k, (h + 13) * k], fill=(130, 130, 136, 255))
    d.ellipse([(w - 26) * k, 140 * k, (w - 8) * k, 160 * k], fill=(255, 240, 190, 255))
    im = im.resize((w, h + 40), Image.LANCZOS)
    ImageDraw.Draw(im).text((175, 148), "MOTIVATION", font=FM(30), fill=INK + (255,), anchor="mm")
    return im


# ---------------------------------------------------------------- characters
GREY = (150, 150, 150)
WHITE_B = (244, 244, 240)


def waiter(t):
    """Pose, face, look and prop of the one who waits."""
    tap = math.sin(t * 9) * 6 if (t % 2.0) < 1.2 else 0
    base = dict(lean=0, dy=math.sin(t * 2) * 2, tl=6, sl=0, tr=-6 + tap * 0.4, sr=-tap, al=-14, bl=12, ar=10, br=10)
    face, look, prop = "calm", -1, None
    for s, e, txt in BUBBLES:
        if s <= t < e:
            if txt == "ANY MINUTE.":          # checks his watch
                base.update(ar=55, br=-120, look=None) if False else base.update(ar=55, br=-120)
            elif txt == "AFTER COFFEE.":
                base.update(al=40, bl=-95)
                prop = "cup"
            elif txt == "TOMORROW.":
                base.update(al=-30, bl=40, ar=30, br=60, lean=-4)   # a shrug
            elif txt == "MONDAY.":
                base.update(lean=6, ar=20, br=-130)                  # leans on the pole, hand on head
    if t >= T_BUS0 + 0.3:
        look = 0
        face = "o" if t < T_TEXT else "sad"
    return pose_from(**base), face, look, prop


def climber(t):
    """(pose, x, y) of the one who climbs; at the top he waits a beat, the bus comes, he steps in."""
    if t < T_STEP0:
        return pose_from(lean=3, dy=math.sin(t * 2) * 2), STAIR_X0 - 70, GROUND, "calm", 1.0
    if t < T_TOP:
        u = (t - T_STEP0) / T_STEP
        i = int(u)
        f = u - i
        # foot position climbs one step per T_STEP, with a little hop in the middle
        x = STAIR_X0 - 70 + (i + f) * STEP_W + 70 * clamp((t - T_STEP0) / 0.6)
        y = GROUND - (i + out_cubic(f)) * STEP_H - math.sin(f * math.pi) * 18
        s = math.sin(u * math.pi)
        pose = pose_from(lean=14, dy=-abs(math.cos(u * math.pi)) * 6, tl=38 * s, sl=-40 - 50 * max(0, -s),
                         tr=-38 * s + 10, sr=-40 - 50 * max(0, s), al=-32 * s, bl=55, ar=32 * s, br=55)
        return pose, x, y, "calm", 1.0
    xtop = STAIR_X0 - 70 + STEPS * STEP_W + 85
    if t < T_BOARD:
        face = "happy" if t > T_BUS1 - 0.2 else "calm"
        return pose_from(lean=0, dy=math.sin(t * 3) * 2, al=-12, ar=12), xtop, TOP_Y, face, 1.0
    # steps into the bus door and disappears
    p = clamp((t - T_BOARD) / 0.35)
    return pose_from(lean=10, tl=20, sl=-30, tr=-10), xtop + 40 * p, TOP_Y, "happy", 1 - p


def bus_x(t):
    stop = STAIR_X0 + STEPS * STEP_W + 60       # the door lines up with the climber
    if t < T_BUS0:
        return W + 400
    p = clamp((t - T_BUS0) / (T_BUS1 - T_BUS0))
    return stop + (W + 420 - stop) * (1 - out_cubic(p))


# ---------------------------------------------------------------- frame
BG = None
BUS = None


def frame_raw(t):
    global BG, BUS
    if BG is None:
        BG, BUS = background(), bus_sprite()
    c = BG.copy()
    # counter
    n = step_at(t)
    put(c, mono_text("STEPS", 26, (150, 150, 150), 6), W / 2, 92)
    put(c, mono_text("0", 72, (170, 170, 170)), W / 2 - 150, 160)
    put(c, mono_text(str(n), 72, (245, 245, 240)), W / 2 + 150, 160, 1 + 0.18 * math.exp(-(((t - T_STEP0) % T_STEP) * 9) ** 2) if 0 < n < STEPS else 1)
    put(c, mono_text("WAITS", 26, (150, 150, 150), 4), W / 2 - 150, 220)
    put(c, mono_text("STARTS", 26, (235, 235, 230), 4), W / 2 + 150, 220)
    d = ImageDraw.Draw(c)
    d.line([(W / 2, 130), (W / 2, 235)], fill=(70, 70, 74), width=2)

    # bus
    bx = bus_x(t)
    if bx < W + 300:
        c.alpha_composite(BUS, (int(bx - 30), int(TOP_Y - BUS.height + 8)))

    # climber (white, glowing)
    pose, x, y, face, a = climber(t)
    spr, anc = draw_stick(pose, WHITE_B, face, 1, 0.82)
    paste_at(c, spr, anc, x, y, a, glow=0.55 * a)

    # waiter (grey)
    pose, face, look, prop = waiter(t)
    spr, anc = draw_stick(pose, GREY, face, look, 0.95, prop)
    paste_at(c, spr, anc, SIGN_X + 105, GROUND)
    for s, e, txt in BUBBLES:
        if s <= t < e:
            p = out_back(prog(t, s, 0.22), 2.2)
            a = 1 - prog(t, e - 0.15, 0.15)
            bub = get_bubble(txt)
            put(c, bub, SIGN_X + 150 + bub.width * 0.25, GROUND - 640, 0.5 + 0.5 * p, min(1, p * 2) * a)

    # typed line
    if t >= T_TEXT:
        chars = int((t - T_TEXT) / 0.055)
        l1 = LINE1[:chars]
        l2 = LINE2[:max(0, chars - len(LINE1) - 4)]
        cursor = "_" if int(t * 3) % 2 == 0 else " "
        if l1:
            im = mono_text(l1 + (cursor if not l2 and len(l1) < len(LINE1) + 1 else ""), 50, (245, 245, 240), 2)
            c.alpha_composite(im, (int(W / 2 - mono_text(LINE1, 50).width / 2), 300))
        if l2:
            im = mono_text(l2 + cursor, 50, GOLD, 2)
            c.alpha_composite(im, (int(W / 2 - mono_text(LINE2, 50).width / 2), 372))
    return c


def frame(t):
    c = frame_raw(t)
    if t >= T_LOOP:  # dissolve back into the first frame, so the reel loops on itself
        c = Image.blend(c, frame_raw(0.0), out_cubic(prog(t, T_LOOP, DUR - T_LOOP)))
    return c.convert("RGB")


# ---------------------------------------------------------------- audio
def audio():
    n = int(DUR * SR)
    mus, fx = np.zeros((n, 2)), np.zeros((n, 2))
    beat = 60 / BPM
    # warm lo-fi loop: Fmaj7 - Em7 - Dm7 - Cmaj7, one chord per bar, the same 6 bars -> seamless loop
    chords = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]]
    roots = [41, 40, 38, 36]
    for b in range(6):
        t0 = b * BAR
        ch, rt = chords[b % 4], roots[b % 4]
        for k, m in enumerate(ch):
            mix_in(mus, tone(midi(m), BAR + 0.05, (1, 0.35, 0.12, 0.05), a=0.02, d=1.3), t0, 0.055, (k - 1.5) * 0.35)
        for q in range(4):
            tb = t0 + q * beat
            mix_in(mus, tone(105, 0.32, (1,), a=0.002, d=0.11, sweep=42), tb, 0.6 if q % 2 == 0 else 0.35)
            mix_in(mus, tone(midi(rt), beat * 0.9, (1, 0.4, 0.1), a=0.005, d=0.3), tb, 0.22)
            if q % 2 == 1:   # a soft "clap" from stacked sines
                mix_in(mus, tone(330, 0.16, (1, 0.6, 0.45, 0.3, 0.2), a=0.002, d=0.04, sweep=190), tb, 0.12)
            for e in range(2):  # a bright tick on the eighths
                mix_in(mus, tone(3200, 0.03, (1,), a=0.0008, d=0.006), tb + e * beat / 2, 0.035, 0.4 - 0.8 * e)
        # little melody: one note per beat from the chord, up an octave
        for q in range(4):
            if (b * 4 + q) % 3 != 2:
                m = ch[(q * 2 + b) % 4] + 12
                mix_in(mus, tone(midi(m), 0.5, (1, 0.25, 0.08), a=0.004, d=0.18), t0 + q * beat + beat / 2, 0.075, 0.2)
    # footsteps on each stair
    for i in range(STEPS):
        mix_in(fx, tone(240 + i * 9, 0.07, (1, 0.5), a=0.001, d=0.025), T_STEP0 + i * T_STEP + T_STEP * 0.5, 0.14, 0.3)
    # bubble pops
    for s, e, txt in BUBBLES:
        mix_in(fx, tone(560, 0.11, (1, 0.3), a=0.002, d=0.05, sweep=1100), s, 0.14, -0.4)
    # the bus: engine hum rising in, a two-tone horn, the door's hiss replaced by a soft chime
    t = np.arange(int(1.0 * SR)) / SR
    hum = (np.sin(2 * np.pi * np.cumsum(70 + 30 * (1 - t)) / SR) + 0.5 * np.sin(4 * np.pi * np.cumsum(70 + 30 * (1 - t)) / SR))
    hum *= np.minimum(1, t / 0.3) * np.clip((1.0 - t) / 0.3, 0, 1)
    mix_in(fx, hum, T_BUS0 - 0.1, 0.2, 0.5)
    for k, m in enumerate([67, 64]):
        mix_in(fx, tone(midi(m), 0.28, (1, 0.6, 0.4, 0.2), a=0.01, d=0.2), T_BUS1 - 0.05 + k * 0.22, 0.13, 0.5)
    for k, m in enumerate([72, 76, 79]):
        mix_in(fx, tone(midi(m), 0.9, (1, 0.3), a=0.002, d=0.4), T_BOARD + k * 0.07, 0.07, 0.3)
    # typewriter clicks for the line
    total = len(LINE1) + 4 + len(LINE2)
    for i in range(total):
        if LINE1[i:i + 1] == " " or i in range(len(LINE1), len(LINE1) + 4):
            continue
        mix_in(fx, tone(1700 + (i % 3) * 140, 0.025, (1, 0.4), a=0.0006, d=0.005), T_TEXT + i * 0.055, 0.05)
    x = mus + fx
    x -= x.mean(axis=0)
    x = np.tanh(x * 1.3)
    x *= 0.89 / np.abs(x).max()
    # no fade: the six bars end exactly where they begin, so the loop is seamless; 5 ms ramps avoid clicks
    r = int(0.005 * SR)
    x[:r] *= np.linspace(0, 1, r)[:, None]
    x[-r:] *= np.linspace(1, 0, r)[:, None]
    return x


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "out/motivation-bus.mp4"
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
