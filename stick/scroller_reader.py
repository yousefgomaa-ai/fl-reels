#!/usr/bin/env python3
"""SCROLLER vs READER - a split-screen stickman comparison reel, 1080x1920, drawn with PIL and numpy; the music and
sounds are synthesised from sines (no samples, no noise); ffmpeg joins them.

    python3 stick/scroller_reader.py out/scroller-reader.mp4
    ONLY_FRAMES=0.5,6,17,21 python3 stick/scroller_reader.py out/x.mp4     # stills instead of the video

The numbers: 10 pages a day for 365 days = 3,650 pages (checked in check()).
"""
import math
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
DUR = 23.0
SR = 44100

PAGES_PER_DAY, DAYS = 10, 365
BOOK_PAGES = 250                       # one book on the shelf for every 250 pages read
T_LAMPS, T_RUN0, T_RUN1 = 0.0, 2.0, 16.4
T_STAND, T_END = 16.6, 18.6


def check():
    assert PAGES_PER_DAY * DAYS == 3650
    assert (PAGES_PER_DAY * DAYS) // BOOK_PAGES == 14


# ---------------------------------------------------------------- fonts
def font_path(names):
    for d in ["/usr/share/fonts/opentype/inter", "/usr/share/fonts/truetype/inter", "/usr/share/fonts/truetype/dejavu"]:
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return p
    raise SystemExit("no font found: install fonts-inter")


BLACK = font_path(["Inter-Black.otf", "Inter-Black.ttf", "DejaVuSans-Bold.ttf"])
BOLD = font_path(["Inter-Bold.otf", "Inter-Bold.ttf", "DejaVuSans-Bold.ttf"])
MED = font_path(["Inter-SemiBold.otf", "Inter-Medium.otf", "DejaVuSans.ttf"])
_fc = {}


def F(p, s):
    if (p, s) not in _fc:
        _fc[(p, s)] = ImageFont.truetype(p, s)
    return _fc[(p, s)]


WHITE = (240, 240, 236)
GOLD = (255, 196, 70)
RED = (230, 70, 70)
INK = (14, 14, 16)
BLUE = (90, 170, 255)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, s, d):
    return clamp((t - s) / d)


def out_cubic(x):
    return 1 - (1 - x) ** 3


def out_back(x, s=1.7):
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


def inout(x):
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


# ---------------------------------------------------------------- text
_ts = {}


def text(s, size, fill=WHITE, font=BOLD, spacing=0, alpha=255):
    k = (s, size, fill, font, spacing)
    if k not in _ts:
        f = F(font, size)
        if spacing:
            ws = [f.getlength(ch) for ch in s]
            tw = int(sum(ws) + spacing * (len(s) - 1))
        else:
            tw = int(f.getlength(s))
        asc, desc = f.getmetrics()
        im = Image.new("RGBA", (tw + 8, asc + desc + 8), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        if spacing:
            x = 4
            for ch, w in zip(s, ws):
                d.text((x, 4), ch, font=f, fill=fill + (255,))
                x += w + spacing
        else:
            d.text((4, 4), s, font=f, fill=fill + (255,))
        _ts[k] = im
    im = _ts[k]
    if alpha < 255:
        im = im.copy()
        im.putalpha(im.split()[3].point(lambda v: v * alpha // 255))
    return im


def put(c, spr, cx, cy, scale=1.0, alpha=1.0):
    if alpha <= 0.01 or scale <= 0.01:
        return
    if abs(scale - 1) > 1e-3:
        spr = spr.resize((max(1, int(spr.width * scale)), max(1, int(spr.height * scale))), Image.BICUBIC)
    if alpha < 0.999:
        spr = spr.copy()
        spr.putalpha(spr.split()[3].point(lambda v: int(v * alpha)))
    x, y = int(cx - spr.width / 2), int(cy - spr.height / 2)
    sx, sy = max(0, -x), max(0, -y)
    ex, ey = min(spr.width, W - x), min(spr.height, H - y)
    if ex > sx and ey > sy:
        c.alpha_composite(spr, (x + sx, y + sy), (sx, sy, ex, ey))


# ---------------------------------------------------------------- the set (computed once)
TOP_FLOOR, BOT_FLOOR = 820, 1630
TOP_LAMP, BOT_LAMP = (540, 300), (540, 1170)


def lit_background():
    """Dark room, a hanging lamp and its warm cone of light, for each half."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img = np.zeros((H, W, 3), np.float32)
    img[:] = np.array([13, 13, 15], np.float32)
    light = np.zeros((H, W), np.float32)
    for (lx, ly), floor, top in [(TOP_LAMP, TOP_FLOOR, 0), (BOT_LAMP, BOT_FLOOR, 960)]:
        inside = (yy >= ly) & (yy <= floor + 60) & (yy >= top)
        depth = np.clip((yy - ly) / (floor - ly), 0, 1.2)
        half = 40 + depth * 330
        cone = np.clip(1 - np.abs(xx - lx) / half, 0, 1) ** 1.6 * (0.55 + 0.45 * (1 - depth / 1.2))
        light += np.where(inside, cone, 0) * 0.55
        # pool of light on the floor
        pool = np.exp(-(((xx - lx) / 330) ** 2 + ((yy - floor - 10) / 34) ** 2))
        light += pool * 0.9 * (yy >= top) * (yy < top + 960)
        # glow around the bulb
        light += np.exp(-(((xx - lx) ** 2 + (yy - ly - 18) ** 2) / (2 * 60 ** 2))) * 0.9
    warm = np.array([255, 214, 160], np.float32) / 255
    img += light[..., None] * warm * 95
    # floors: slightly lighter band under each floor line
    for floor, top in [(TOP_FLOOR, 0), (BOT_FLOOR, 960)]:
        band = (yy > floor) & (yy < top + 960)
        img[band] += 6
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    for (lx, ly), floor in [(TOP_LAMP, TOP_FLOOR), (BOT_LAMP, BOT_FLOOR)]:
        d.line([(lx, max(ly - 140, 1060 if ly > 960 else 0)), (lx, ly - 18)], fill=(60, 60, 62), width=4)
        d.polygon([(lx - 44, ly + 14), (lx + 44, ly + 14), (lx + 20, ly - 22), (lx - 20, ly - 22)], fill=(52, 52, 56))
        d.ellipse([lx - 12, ly + 6, lx + 12, ly + 26], fill=(255, 236, 200))
        d.line([(60, floor), (W - 60, floor)], fill=(70, 70, 74), width=3)
    # divider band
    d.rectangle([0, 952, W, 968], fill=(8, 8, 9))
    d.line([(0, 952), (W, 952)], fill=(58, 58, 62), width=2)
    d.line([(0, 968), (W, 968)], fill=(58, 58, 62), width=2)
    return im


def draw_props_static(im):
    """Bed (top), armchair and empty bookshelf (bottom)."""
    k = 2
    lay = Image.new("RGBA", (W * k, H * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    o = (INK[0], INK[1], INK[2], 255)
    # bed, top half
    bx, by = 300, TOP_FLOOR
    d.rounded_rectangle([(bx - 10) * k, (by - 150) * k, (bx + 30) * k, by * k], 10 * k, fill=(78, 78, 84, 255), outline=o, width=5 * k)
    d.rounded_rectangle([bx * k, (by - 95) * k, (bx + 360) * k, (by - 40) * k], 14 * k, fill=(92, 92, 100, 255), outline=o, width=5 * k)
    d.rounded_rectangle([(bx + 20) * k, (by - 118) * k, (bx + 120) * k, (by - 92) * k], 12 * k, fill=(170, 170, 176, 255), outline=o, width=4 * k)
    for lx in (bx + 10, bx + 340):
        d.rectangle([lx * k, (by - 40) * k, (lx + 16) * k, by * k], fill=(60, 60, 64, 255), outline=o, width=3 * k)
    # nightstand with a phone charger
    d.rounded_rectangle([760 * k, (by - 120) * k, 860 * k, by * k], 8 * k, fill=(62, 62, 68, 255), outline=o, width=4 * k)
    d.line([800 * k, (by - 70) * k, 820 * k, (by - 70) * k], fill=(120, 120, 126, 255), width=4 * k)
    # armchair, bottom half
    cx, cy = 300, BOT_FLOOR
    d.rounded_rectangle([(cx - 30) * k, (cy - 330) * k, (cx + 30) * k, (cy - 60) * k], 22 * k, fill=(120, 74, 52, 255), outline=o, width=5 * k)
    d.rounded_rectangle([(cx - 10) * k, (cy - 165) * k, (cx + 210) * k, (cy - 95) * k], 20 * k, fill=(138, 86, 60, 255), outline=o, width=5 * k)
    d.rounded_rectangle([(cx + 170) * k, (cy - 220) * k, (cx + 230) * k, (cy - 95) * k], 18 * k, fill=(128, 80, 56, 255), outline=o, width=5 * k)
    for lx in (cx - 10, cx + 190):
        d.rectangle([lx * k, (cy - 95) * k, (lx + 16) * k, cy * k], fill=(70, 46, 34, 255), outline=o, width=3 * k)
    # bookshelf frame
    sx0, sx1, sy0 = SHELF_X0, SHELF_X1, SHELF_Y0
    d.rectangle([sx0 * k, sy0 * k, sx1 * k, cy * k], fill=(40, 30, 24, 255), outline=o, width=5 * k)
    for sy in SHELF_ROWS:
        d.rectangle([sx0 * k, sy * k, sx1 * k, (sy + 12) * k], fill=(92, 64, 44, 255), outline=o, width=3 * k)
    lay = lay.resize((W, H), Image.LANCZOS)
    im.alpha_composite(lay)
    return im


SHELF_X0, SHELF_X1, SHELF_Y0 = 690, 940, 1270
SHELF_ROWS = [1380, 1500, 1618]
BOOK_COLORS = [(180, 60, 60), (60, 110, 170), (200, 160, 60), (70, 140, 100), (150, 90, 160), (210, 120, 60),
               (90, 90, 100), (190, 70, 110), (60, 150, 160), (170, 140, 90), (110, 70, 50), (230, 196, 90),
               (80, 120, 200), (200, 90, 80)]


def book_slots():
    """14 book positions: 5 on each of the first two shelves, 4 on the bottom one."""
    slots = []
    for r, sy in enumerate(SHELF_ROWS):
        n = 5 if r < 2 else 4
        x = SHELF_X0 + 22
        for i in range(n):
            w = 30 + (i * 7 + r * 5) % 10
            h = 78 + (i * 13 + r * 9) % 22
            slots.append((x, sy, w, h))
            x += w + 7
    return slots[:14]


SLOTS = book_slots()


# ---------------------------------------------------------------- stickmen
STAND = {"head": (0, -392), "neck": (0, -338), "hip": (0, -178), "kl": (-20, -92), "fl": (-30, 0), "kr": (20, -92),
         "fr": (30, 0), "el": (-46, -262), "hl": (-52, -186), "er": (46, -262), "hr": (52, -186)}


def scroller_pose(t, slump):
    """Sitting on the edge of the bed, bent over the phone; slump 0..1 bends him further as the days pass."""
    flick = math.sin(t * 9) * 3 if (t * 1.3) % 1 < 0.6 else 0
    b = 18 * slump
    return {"head": (58 + b, -300 + b * 1.2), "neck": (32 + b * 0.6, -262 + b * 0.5), "hip": (0, -120),
            "kl": (78, -122), "fl": (88, 0), "kr": (64, -116), "fr": (70, 0),
            "el": (40, -178), "hl": (92 + b * 0.4, -200 + flick), "er": (54, -172), "hr": (98 + b * 0.4, -196 + flick)}


def reader_pose(t, page_turn):
    """Sitting in the armchair with a book; page_turn 0..1 swings the right hand over the book."""
    pt = math.sin(page_turn * math.pi)
    breathe = math.sin(t * 2.2) * 2
    return {"head": (34, -362 + breathe), "neck": (22, -314 + breathe), "hip": (0, -158),
            "kl": (96, -170), "fl": (110, 0), "kr": (84, -162), "fr": (96, 0),
            "el": (48, -230), "hl": (120, -256), "er": (62, -226 + pt * 10), "hr": (150 + pt * 30, -262 - pt * 26)}


def reader_stand_pose(t):
    p = dict(STAND)
    p["er"] = (52, -290)
    p["hr"] = (96, -360 + math.sin(t * 6) * 6)   # holding the book up
    return p


def lerp_pose(a, b, x):
    return {k: (a[k][0] + (b[k][0] - a[k][0]) * x, a[k][1] + (b[k][1] - a[k][1]) * x) for k in a}


def draw_stick(pose, origin, prop=None, glow=None, hl=0.0):
    """Returns (sprite, top-left) of a 2x supersampled stickman: dark outline, white fill, soft shading."""
    k = 2
    box = 620
    im = Image.new("RGBA", (box * k, box * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ox, oy = box // 2, box - 40

    def P(n):
        x, y = pose[n]
        return ((ox + x) * k, (oy + y) * k)

    segs = [("neck", "hip"), ("hip", "kl"), ("kl", "fl"), ("hip", "kr"), ("kr", "fr"), ("neck", "el"), ("el", "hl"),
            ("neck", "er"), ("er", "hr")]
    back = [("hip", "kr"), ("kr", "fr"), ("neck", "er"), ("er", "hr")]
    body = (236, 236, 232) if hl <= 0 else tuple(int(a + (b - a) * hl) for a, b in zip((236, 236, 232), (255, 226, 150)))
    shade = (190, 190, 188)
    for pass_, segs_ in (("back", back), ("front", [s for s in segs if s not in back])):
        col = shade if pass_ == "back" else body
        for a, b in segs_:
            d.line([P(a), P(b)], fill=INK + (255,), width=30 * k, joint="curve")
            for p in (P(a), P(b)):
                d.ellipse([p[0] - 15 * k, p[1] - 15 * k, p[0] + 15 * k, p[1] + 15 * k], fill=INK + (255,))
        for a, b in segs_:
            d.line([P(a), P(b)], fill=col + (255,), width=20 * k, joint="curve")
            for p in (P(a), P(b)):
                d.ellipse([p[0] - 10 * k, p[1] - 10 * k, p[0] + 10 * k, p[1] + 10 * k], fill=col + (255,))
    hx, hy = P("head")
    r = 44 * k
    d.ellipse([hx - r - 5 * k, hy - r - 5 * k, hx + r + 5 * k, hy + r + 5 * k], fill=INK + (255,))
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=body + (255,))
    d.ellipse([hx - r * 0.55, hy - r * 0.75, hx - r * 0.05, hy - r * 0.3], fill=(255, 255, 255, 120))
    if prop == "phone":
        x, y = P("hl")
        x += 14 * k
        d.rounded_rectangle([x - 12 * k, y - 26 * k, x + 14 * k, y + 14 * k], 6 * k, fill=(22, 26, 34, 255), outline=INK + (255,), width=3 * k)
        d.rounded_rectangle([x - 8 * k, y - 22 * k, x + 10 * k, y + 10 * k], 4 * k, fill=(120, 190, 255, 255))
    if prop == "book":
        x, y = P("hl")
        d.polygon([(x - 6 * k, y - 34 * k), (x + 46 * k, y - 50 * k), (x + 52 * k, y + 2 * k), (x, y + 18 * k)], fill=INK + (255,))
        d.polygon([(x - 1 * k, y - 28 * k), (x + 42 * k, y - 43 * k), (x + 46 * k, y - 2 * k), (x + 3 * k, y + 12 * k)], fill=(250, 246, 232, 255))
        d.line([(x + 20 * k, y - 36 * k), (x + 24 * k, y + 5 * k)], fill=(150, 140, 120, 255), width=2 * k)
    if prop == "book_up":
        x, y = P("hr")
        d.rounded_rectangle([x - 22 * k, y - 46 * k, x + 22 * k, y + 8 * k], 4 * k, fill=GOLD + (255,), outline=INK + (255,), width=4 * k)
    im = im.resize((box, box), Image.LANCZOS)
    if glow is not None:
        gx, gy, col, a = glow
        g = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(g).ellipse([ox + gx - 70, oy + gy - 70, ox + gx + 70, oy + gy + 70], fill=col + (int(110 * a),))
        g = g.filter(ImageFilter.GaussianBlur(26))
        im = Image.alpha_composite(g, im)
    return im, (int(origin[0] - ox), int(origin[1] - oy))


def book_sprite(i):
    x, y, w, h = SLOTS[i]
    col = BOOK_COLORS[i % len(BOOK_COLORS)]
    k = 2
    im = Image.new("RGBA", ((w + 8) * k, (h + 8) * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([4 * k, 4 * k, (w + 4) * k, (h + 4) * k], 3 * k, fill=col + (255,), outline=INK + (255,), width=3 * k)
    d.line([(4 + w * 0.2) * k, 18 * k, (4 + w * 0.8) * k, 18 * k], fill=(255, 255, 255, 120), width=3 * k)
    d.line([(4 + w * 0.2) * k, (h - 10) * k, (4 + w * 0.8) * k, (h - 10) * k], fill=(255, 255, 255, 90), width=3 * k)
    return im.resize((w + 8, h + 8), Image.LANCZOS)


BOOKS = [book_sprite(i) for i in range(14)]


# ---------------------------------------------------------------- timeline
def day_at(t):
    if t < T_RUN0:
        return 1
    p = prog(t, T_RUN0, T_RUN1 - T_RUN0)
    # slow start (1, 2, 3 ... readable), then it races
    return int(round(1 + (DAYS - 1) * (p ** 2.4)))


def fmt(n):
    return f"{n:,}"


BG = None


def frame(t):
    global BG
    if BG is None:
        BG = draw_props_static(lit_background())
    lamps = out_cubic(prog(t, T_LAMPS + 0.05, 0.35))
    flick = 1.0 if t > 0.6 else (0.4 + 0.6 * (math.sin(t * 60) > -0.2)) * lamps
    c = Image.new("RGBA", (W, H), (8, 8, 9, 255))
    bg = BG if flick > 0.99 else Image.blend(Image.new("RGBA", (W, H), (8, 8, 9, 255)), BG, flick)
    c.alpha_composite(bg)

    day = day_at(t)
    pages = day * PAGES_PER_DAY
    books = min(14, pages // BOOK_PAGES)
    end = t >= T_END

    # ---- books appear on the shelf, each with a small pop
    for i in range(books):
        t_i = book_time(i)
        p = out_back(prog(t, t_i, 0.25), 2.4)
        x, y, w, h = SLOTS[i]
        spr = BOOKS[i]
        if p < 0.999:
            spr = spr.resize((max(1, spr.width), max(1, int(spr.height * p))), Image.BICUBIC)
        c.alpha_composite(spr, (x - 4, y - spr.height + 4))
    if t >= T_STAND:  # the full shelf glows
        g = out_cubic(prog(t, T_STAND, 0.6))
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).rounded_rectangle([SHELF_X0 - 30, SHELF_Y0 - 30, SHELF_X1 + 30, BOT_FLOOR + 10], 30,
                                               fill=GOLD + (int(70 * g * (0.8 + 0.2 * math.sin(t * 5))),))
        c.alpha_composite(glow.filter(ImageFilter.GaussianBlur(30)))

    # ---- scroller (top)
    slump = clamp((day - 1) / 364)
    sp, so = draw_stick(scroller_pose(t, slump), (430, TOP_FLOOR - 8), prop="phone",
                        glow=(95, -205, BLUE, 1.0))
    c.alpha_composite(sp, so)

    # ---- reader (bottom): a page turn every 1.1 s while the days run, then stands up
    if t < T_STAND:
        turn = ((t - 1.2) % 1.1) / 0.35 if t > 1.2 else 1.0
        pose = reader_pose(t, clamp(turn) if turn < 1 else 0.0)
        rp, ro = draw_stick(pose, (330, BOT_FLOOR - 4), prop="book", glow=(130, -250, (255, 220, 160), 0.5))
    else:
        x = out_cubic(prog(t, T_STAND, 0.5))
        pose = lerp_pose(reader_pose(t, 0), reader_stand_pose(t), x)
        rp, ro = draw_stick(pose, (330 + 120 * x, BOT_FLOOR - 4), prop="book_up" if x > 0.5 else "book", hl=x)
    c.alpha_composite(rp, ro)

    # ---- labels and counters
    a0 = out_cubic(prog(t, 1.95, 0.4)) * (1 - 0.85 * out_cubic(prog(t, T_END, 0.5)))
    put(c, text("SCROLLER", 40, WHITE, BOLD, spacing=9), W / 2, 84, 1, a0)
    put(c, text("READER", 40, WHITE, BOLD, spacing=9), W / 2, 1022, 1, a0)
    put(c, text("PAGES READ", 26, (150, 150, 150), MED, spacing=6), 220, 150, 1, a0)
    put(c, text("0", 64, RED, BLACK), 220, 206, 1, a0)
    put(c, text("PAGES READ", 26, (150, 150, 150), MED, spacing=6), 220, 1088, 1, a0)
    pulse = 1 + 0.12 * math.exp(-((t - book_time(books - 1)) * 6) ** 2) if books else 1
    put(c, text(fmt(pages), 64, GOLD, BLACK), 220, 1144, pulse, a0)
    # center band: SAME 10 MINUTES / DAY n
    put(c, text("SAME 10 MINUTES", 26, (170, 170, 170), MED, spacing=7), W - 230, 150, 1, a0)
    put(c, text(f"DAY {day}", 64, WHITE, BLACK), W - 230, 206, 1, a0)

    # ---- hook (first 2 s): a big line over both halves
    if t < 2.4:
        p = out_back(prog(t, 0.15, 0.4), 1.6)
        a = 1 - prog(t, 1.9, 0.45)
        put(c, text("SAME 10 MINUTES.", 92, WHITE, BLACK), W / 2, 905, 0.6 + 0.4 * p, min(1, p * 2) * a)
        put(c, text("ONE YEAR LATER?", 92, GOLD, BLACK), W / 2, 1010, 0.6 + 0.4 * out_back(prog(t, 0.55, 0.4), 1.6),
            min(1, prog(t, 0.55, 0.2) * 2) * a)

    # ---- end card
    if end:
        p = out_cubic(prog(t, T_END, 0.5))
        dim = Image.new("RGBA", (W, H), (0, 0, 0, int(165 * p)))
        c.alpha_composite(dim)
        put(c, text("10 PAGES A DAY", 84, WHITE, BLACK), W / 2, 760, 0.8 + 0.2 * out_back(prog(t, T_END, 0.45)), p)
        p2 = prog(t, T_END + 0.55, 0.45)
        put(c, text("= 3,650 PAGES", 104, GOLD, BLACK), W / 2, 880, 0.8 + 0.2 * out_back(p2), p2)
        put(c, text("A YEAR", 84, GOLD, BLACK), W / 2, 990, 0.8 + 0.2 * out_back(p2), p2)
        p3 = prog(t, T_END + 1.5, 0.45)
        put(c, text("WHICH ONE ARE YOU?", 64, WHITE, BOLD, spacing=4), W / 2, 1160, 0.85 + 0.15 * out_back(p3), p3)
        p4 = prog(t, T_END + 2.2, 0.4)
        put(c, text("SCROLLER  or  READER", 44, (180, 180, 180), MED, spacing=3), W / 2, 1245, 1, p4)
        if p4 > 0:  # bouncing arrow toward the comments
            ay = 1350 + 16 * abs(math.sin(t * 5))
            ar = Image.new("RGBA", (90, 110), (0, 0, 0, 0))
            dd = ImageDraw.Draw(ar)
            dd.rounded_rectangle([33, 0, 57, 60], 8, fill=GOLD + (255,))
            dd.polygon([(5, 52), (85, 52), (45, 106)], fill=GOLD + (255,))
            put(c, ar, W / 2, ay, 1, p4)

    # thin progress line at the very top
    d = ImageDraw.Draw(c)
    d.rectangle([0, 0, int(W * t / DUR), 6], fill=GOLD + (255,))
    return c.convert("RGB")


_bt = {}


def book_time(i):
    """Time the (i+1)-th book appears: when pages reach (i+1)*250."""
    if i in _bt:
        return _bt[i]
    need = (i + 1) * BOOK_PAGES
    t = T_RUN0
    while t < T_RUN1 + 0.1 and day_at(t) * PAGES_PER_DAY < need:
        t += 1 / 300
    _bt[i] = t
    return t


def day_change_times():
    ts, last = [], 1
    t = T_RUN0
    while t <= T_RUN1 + 0.05:
        d = day_at(t)
        if d != last:
            ts.append(t)
            last = d
        t += 1 / 600
    return ts


# ---------------------------------------------------------------- audio
def env(n, a, d):
    t = np.arange(n) / SR
    e = np.minimum(1, t / a) * np.exp(-t / d)
    tail = min(n, int(0.006 * SR))
    e[-tail:] *= np.linspace(1, 0, tail)
    return e


def tone(f, dur, harm=(1.0,), a=0.004, d=0.2, sweep=None):
    n = int(dur * SR)
    t = np.arange(n) / SR
    fr = f * (sweep / f) ** (t / dur) if sweep else np.full(n, f)
    ph = 2 * np.pi * np.cumsum(fr) / SR
    return sum(h * np.sin(ph * (i + 1)) for i, h in enumerate(harm)) * env(n, a, d)


def midi(n):
    return 440 * 2 ** ((n - 69) / 12)


def mix_in(buf, sig, at, g=1.0, pan=0.0):
    i = int(at * SR)
    if i >= len(buf):
        return
    sig = sig[: len(buf) - i]
    l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
    buf[i:i + len(sig), 0] += sig * g * l * 1.41
    buf[i:i + len(sig), 1] += sig * g * r * 1.41


def audio():
    n = int(DUR * SR)
    mus, fx = np.zeros((n, 2)), np.zeros((n, 2))
    # warm piano-like pad progression, C - Am - F - G, one chord per 2 s, building up until the stand-up
    chords = [[48, 55, 60, 64], [45, 52, 57, 60], [41, 48, 57, 60], [43, 50, 55, 59]]
    for b in range(int(T_STAND // 2) + 1):
        t0 = b * 2.0
        ch = chords[b % 4]
        g = 0.05 + 0.05 * clamp(t0 / T_STAND)
        for k, m in enumerate(ch):
            mix_in(mus, tone(midi(m), 2.2, (1, 0.4, 0.15, 0.06), a=0.01, d=1.1), t0, g, (k - 1.5) * 0.3)
        # arpeggio in eighths from 2 s, faster in the last bars
        if t0 >= 2.0:
            step = 0.25 if t0 < 10 else 0.125
            j = 0
            while j * step < 2.0:
                m = ch[(j % 4)] + 12 + (12 if (j // 4) % 2 else 0)
                mix_in(mus, tone(midi(m), 0.35, (1, 0.3, 0.1), a=0.003, d=0.09), t0 + j * step, 0.06, (-0.4 if j % 2 else 0.4))
                j += 1
        # soft kick from 4 s
        if t0 >= 4.0:
            for q in range(4):
                mix_in(mus, tone(110, 0.3, (1,), a=0.002, d=0.1, sweep=42), t0 + q * 0.5, 0.55)
    # day ticks: one per new day while they are slow, then capped to about 12 a second
    last = -1
    for tt in day_change_times():
        if tt - last >= 0.085:
            mix_in(fx, tone(2100, 0.05, (1,), a=0.001, d=0.01), tt, 0.07)
            last = tt
    # book pops
    for i in range(14):
        tb = book_time(i)
        mix_in(fx, tone(520 + 30 * i, 0.12, (1, 0.3), a=0.002, d=0.05, sweep=(520 + 30 * i) * 2), tb, 0.16, 0.5)
    # lamps switching on
    for k, tt in enumerate([0.08, 0.22, 0.4]):
        mix_in(fx, tone(1200, 0.04, (1, 0.5), a=0.001, d=0.008), tt, 0.12)
    # hook hits
    mix_in(fx, tone(90, 0.7, (1, 0.4), a=0.002, d=0.22, sweep=34), 0.15, 0.7)
    mix_in(fx, tone(90, 0.7, (1, 0.4), a=0.002, d=0.22, sweep=34), 0.55, 0.6)
    # riser into the stand-up, impact, warm resolve
    rd = 1.6
    t = np.arange(int(rd * SR)) / SR
    f = 200 * (1600 / 200) ** (t / rd) ** 1.5
    r = (np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.4 * np.sin(4 * np.pi * np.cumsum(f) / SR)) * (t / rd) ** 2.5
    r[-int(0.01 * SR):] *= np.linspace(1, 0, int(0.01 * SR))
    mix_in(fx, r, T_STAND - rd, 0.08)
    mix_in(fx, tone(80, 1.2, (1, 0.5), a=0.002, d=0.35, sweep=30), T_STAND, 0.9)
    for k, m in enumerate([60, 64, 67, 72, 76]):
        mix_in(mus, tone(midi(m), 4.5, (1, 0.35, 0.12), a=0.02, d=1.8), T_STAND + 0.02 + k * 0.06, 0.07, (k - 2) * 0.3)
    for k, m in enumerate([72, 76, 79, 84]):
        mix_in(fx, sum(tone(midi(m) * h, 1.2, (1,), a=0.002, d=d) * g for h, d, g in [(1, 0.8, 1), (2.0, 0.4, 0.35), (3.01, 0.25, 0.2)]),
               T_END + 0.55 + k * 0.08, 0.1)
    # end card: a calm pad under the question
    for k, m in enumerate([48, 55, 60, 64, 67]):
        mix_in(mus, tone(midi(m), DUR - T_END, (1, 0.3), a=0.6, d=6), T_END, 0.05, (k - 2) * 0.3)
    tt = np.arange(n) / SR
    fade = np.clip((DUR - tt) / 0.8, 0, 1) * np.clip(tt / 0.01, 0, 1)
    x = (mus * 0.9 + fx) * fade[:, None]
    x -= x.mean(axis=0)
    x = np.tanh(x * 1.2)
    return x * (0.89 / np.abs(x).max())


def write_wav(path, x):
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


def main():
    check()
    out = sys.argv[1] if len(sys.argv) > 1 else "out/scroller-reader.mp4"
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
