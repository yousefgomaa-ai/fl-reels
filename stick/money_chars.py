#!/usr/bin/env python3
"""Characters for "She Chose The Money": every one readable at a glance.

HERO   - the brand look: white figure, red scarf. Broke: grey hoodie + backpack. Later: charcoal suit, scarf stays.
GIRL   - long dark hair, lilac dress, small gold purse.
RICH   - slick black hair, black sunglasses, navy suit, gold chain. Broke: no glasses/chain, loose tie, messy hair.

    python3 stick/money_chars.py      # -> stick/money/chars.png
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perfect_wave as PW  # noqa
import compare as C  # noqa
from compare import ell, line, rrect, poly, figure, place, FLOOR, K, W, H  # noqa
from perfect_wave import font  # noqa

S = 0.95
STAND = PW.STAND
NAVY = (30, 38, 66)
CHAR = (52, 54, 62)
HOOD = (118, 122, 134)
LILAC = (186, 120, 206)
GOLD = (236, 190, 80)
HAIR = (26, 20, 18)
SHIRT = (236, 236, 240)
RED = (214, 44, 44)


def _limb(d, pts, a, b, c, col, w):
    line(d, [pts[a], pts[b], pts[c]], col + (255,), w)
    for p in (pts[a], pts[b], pts[c]):
        ell(d, p[0], p[1], w / 2, w / 2, col + (255,))


def outfit(d, pts, col, f=1, legs=True, shirt=False, tie=None):
    """clothes over the stick body: torso, sleeves, trousers"""
    w = 30 * S
    nx, ny = pts["neck"]
    hx, hy = pts["hip"]
    poly(d, [(nx - w / 2, ny), (nx + w / 2, ny), (hx + w / 2, hy + 6), (hx - w / 2, hy + 6)], col + (255,))
    ell(d, nx, ny + 2, w / 2 + 2, 8, col + (255,))
    _limb(d, pts, "neck", "el", "hl", col, 24 * S)
    _limb(d, pts, "neck", "er", "hr", col, 24 * S)
    if legs:
        dark = tuple(int(v * 0.7) for v in col)
        _limb(d, pts, "hip", "kl", "fl", dark, 24 * S)
        _limb(d, pts, "hip", "kr", "fr", dark, 24 * S)
    for side in ("hl", "hr"):   # hands stay white
        ell(d, *pts[side], 11 * S, 11 * S, (238, 238, 242, 255))
    if shirt:
        poly(d, [(nx - 6, ny - 2), (nx + 6, ny - 2), (nx + 2 * f, ny + 34)], SHIRT + (255,))
    if tie:
        poly(d, [(nx - 4, ny + 2), (nx + 4, ny + 2), (nx + 5 + tie[1], ny + 38), (nx + tie[1], ny + 46),
                 (nx - 5 + tie[1], ny + 38)], tie[0] + (255,))


TEAR = (120, 180, 255)
INKF = (28, 28, 34)


def face(d, pts, expr="neutral", f=1, t=0.0, glasses=False, fem=False):
    """simple readable face on the head circle, turned a little toward f"""
    if not expr:
        return
    hx, hy = pts["head"]
    cx, cy = hx + f * 7, hy + 6
    ex = (cx - 11, cx + 11)
    ey = cy - 5
    k = K

    LIP = (196, 64, 96) if fem else INKF

    def arc(x, y, rw, rh, a0, a1, w=3, col=INKF):
        d.arc(((x - rw) * k, (y - rh) * k, (x + rw) * k, (y + rh) * k), a0, a1, fill=col + (255,), width=int(w * k))

    def brow(x, y, tilt, w=3):   # tilt>0: inner end up (sad); <0: inner end down (angry)
        sgn = 1 if x > cx else -1
        line(d, [(x - 6, y - sgn * tilt * 3), (x + 6, y + sgn * tilt * 3)], INKF + (255,), w)

    # eyes
    if glasses:
        for x in ex:
            rrect(d, (x - 9, ey - 6, x + 9, ey + 6), 4, (12, 12, 16, 255))
        line(d, [ex[0] + 8, ey - 2, ex[1] - 8, ey - 2] and [(ex[0] + 8, ey - 2), (ex[1] - 8, ey - 2)], (12, 12, 16, 255), 3)
    else:
        if expr in ("laugh", "happy"):
            for x in ex:
                arc(x, ey + 3, 5, 4, 200, 340)
        elif expr in ("tired", "smug"):
            for x in ex:
                line(d, [(x - 5, ey), (x + 5, ey)], INKF + (255,), 3)
                ell(d, x, ey + 2, 3, 2, INKF + (255,))
        elif expr == "shocked":
            for x in ex:
                ell(d, x, ey, 6, 7, (255, 255, 255, 255))
                ell(d, x, ey, 2.5, 2.5, INKF + (255,))
                d.ellipse(((x - 6) * k, (ey - 7) * k, (x + 6) * k, (ey + 7) * k), outline=INKF + (255,), width=int(2 * k))
        elif expr in ("cry", "sad"):
            for x in ex:
                ell(d, x, ey + 1, 3, 3.5, INKF + (255,))
        else:
            for x in ex:
                ell(d, x, ey, 3, 3.8, INKF + (255,))
    if fem and not glasses:   # lashes + blush
        for j, x in enumerate(ex):
            o = 1 if x > cx else -1
            line(d, [(x + o * 4, ey - 3), (x + o * 9, ey - 8)], INKF + (255,), 2)
            line(d, [(x + o * 1, ey - 4), (x + o * 4, ey - 10)], INKF + (255,), 2)
            ell(d, x + o * 3, ey + 11, 6, 3.5, (250, 196, 206, 255))
    # brows
    by = ey - 10
    if expr in ("sad", "cry"):
        for x in ex:
            brow(x, by, 1.2)
    elif expr in ("determined", "angry"):
        for x in ex:
            brow(x, by + 1, -1.2)
    elif expr == "shocked":
        for x in ex:
            arc(x, by - 2, 6, 3, 200, 340)
    elif expr == "smug":
        brow(ex[0], by + 1, 0)
        arc(ex[1], by - 2, 6, 3, 200, 340)
    elif expr == "nervous":
        for x in ex:
            brow(x, by, 0.9)
    # mouth
    my = cy + 13
    if expr == "happy":
        arc(cx, my - 4, 9, 6, 20, 160, col=LIP)
    elif expr == "laugh":
        d.chord(((cx - 10) * k, (my - 6) * k, (cx + 10) * k, (my + 10) * k), 0, 180, fill=(120, 30, 40, 255))
        line(d, [(cx - 10, my + 2), (cx + 10, my + 2)], INKF + (255,), 2)
    elif expr in ("sad", "tired"):
        arc(cx, my + 5, 8, 5, 200, 340, col=LIP)
    elif expr == "cry":
        d.chord(((cx - 8) * k, (my - 3) * k, (cx + 8) * k, (my + 9) * k), 180, 360, fill=(90, 30, 40, 255))
        for j, x in enumerate(ex):
            v = (t * 1.6 + j * 0.5) % 1.0
            line(d, [(x, ey + 5), (x + 1, ey + 18)], TEAR + (230,), 4)
            ell(d, x + 1, ey + 8 + 22 * v, 3, 4, TEAR + (int(255 * (1 - v)),))
    elif expr == "shocked":
        ell(d, cx, my + 1, 6, 8, (90, 30, 40, 255))
    elif expr == "smug":
        line(d, [(cx - 8, my), (cx + 2, my)], LIP + (255,), 3)
        arc(cx + 6, my - 4, 6, 4, 20, 120, col=LIP)
    elif expr == "nervous":
        line(d, [(cx - 9, my), (cx - 4, my - 2), (cx + 1, my + 1), (cx + 6, my - 2), (cx + 10, my)], INKF + (255,), 2.5)
        ell(d, hx - f * 22, hy - 14, 3, 5, TEAR + (220,))
    elif expr in ("determined", "angry", "neutral"):
        if fem:
            ell(d, cx, my, 6, 3, LIP + (255,))
        else:
            line(d, [(cx - 7, my), (cx + 7, my)], INKF + (255,), 3)
    if expr == "tired":
        for x in ex:
            arc(x, ey + 6, 5, 2, 20, 160, 2)


def head_dir(pts):
    hx, hy = pts["head"]
    nx, ny = pts["neck"]
    a = math.atan2(hy - ny, hx - nx)
    return hx, hy, a


def hero(stage, pts, mode="broke", f=1, expr="neutral", t=0.0):
    figure(stage, pts, S, light=(0.4, -0.9), scarf=False)
    d = ImageDraw.Draw(stage)
    face(d, pts, expr, f, t)
    if mode == "broke":
        nx, ny = pts["neck"]
        hx, hy = pts["hip"]
        if hy - 14 > ny + 30:
            rrect(d, (nx - 34 * f - 18, ny + 6, nx - 34 * f + 18, hy - 14), 6, (86, 70, 54, 255),
                  outline=(40, 32, 26, 255), w=2)
        outfit(d, pts, HOOD, f, legs=False)
        line(d, [pts["hip"], pts["kl"], pts["fl"]], (64, 78, 110, 255), 24 * S)   # jeans
        line(d, [pts["hip"], pts["kr"], pts["fr"]], (64, 78, 110, 255), 24 * S)
    elif mode == "ceo":
        outfit(d, pts, CHAR, f, shirt=True)
    scarf(d, pts, f)


def scarf(d, pts, f=1):
    nx, ny = pts["neck"]
    ell(d, nx, ny + 2, 21 * S, 11 * S, RED + (255,))
    poly(d, [(nx, ny), (nx - f * 44 * S, ny + 26 * S), (nx - f * 30 * S, ny + 40 * S)], RED + (255,))


HAIR_G = (58, 34, 26)
HAIR_HI = (110, 70, 50)
DRESS = (192, 108, 214)
DRESS_D = (150, 76, 176)


def girl(stage, pts, f=1, wind=0.0, expr="neutral", t=0.0):
    hx, hy, _ = head_dir(pts)
    r = 31 * S
    d0 = ImageDraw.Draw(stage)
    sway = 4 * math.sin(t * 2.2) + 22 * wind
    # hair behind: volume around the head + long waves down the back
    ell(d0, hx - f * 3, hy + 2, r + 10, r + 9, HAIR_G + (255,))
    back = [(hx - f * (r + 8), hy - 6)]
    for j in range(7):
        yy = hy + 12 + j * 15
        back.append((hx - f * (r + 10 + sway * j / 6 + 5 * math.sin(j * 1.3 + t * 3)), yy))
    back += [(hx - f * (r * 0.2 + sway), hy + 112), (hx + f * (r * 0.5), hy + 70), (hx + f * (r + 6), hy + 20),
             (hx + f * (r + 8), hy - 4)]
    poly(d0, back, HAIR_G + (255,))
    figure(stage, pts, S, light=(0.4, -0.9))
    d = ImageDraw.Draw(stage)
    # dress: fitted top, gold belt, flared skirt with a soft hem
    nx, ny = pts["neck"]
    px, py = pts["hip"]
    wx, wy = lerp_pt((nx, ny), (px, py), 0.62)
    kx = (pts["kl"][0] + pts["kr"][0]) / 2
    ky = max(pts["kl"][1], pts["kr"][1])
    poly(d, [(nx - 15, ny + 6), (nx + 15, ny + 6), (wx + 11, wy), (wx - 11, wy)], DRESS + (255,))
    hem = []
    for j in range(9):
        u = j / 8
        hem.append((kx - 46 + 92 * u, ky + 10 + 5 * math.sin(u * math.pi * 3 + t * 4)))
    poly(d, [(wx - 11, wy), (wx + 11, wy)] + hem[::-1] if f < 0 else [(wx + 11, wy)] + hem[::-1] + [(wx - 11, wy)],
         DRESS + (255,))
    poly(d, [(wx, wy + 6), (kx + 12, ky + 8), (kx - 4, ky + 10)], DRESS_D + (255,))
    line(d, [(wx - 12, wy), (wx + 12, wy)], GOLD + (255,), 4)
    for side in ("el", "er"):   # little sleeves
        line(d, [(nx, ny + 4), lerp_pt((nx, ny + 4), pts[side], 0.35)], DRESS + (255,), 20 * S)
    # heels
    for side in ("fl", "fr"):
        fx, fy = pts[side]
        poly(d, [(fx - 10, fy - 2), (fx + 14 * f, fy + 4), (fx + 14 * f, fy + 10), (fx - 8, fy + 10)], (40, 24, 30, 255))
    # front hair: side-swept bangs + a lock framing the face
    pts_b = []
    for j in range(13):
        a = math.pi * (1.05 + 0.9 * j / 12)
        pts_b.append((hx + (r + 3) * math.cos(a), hy + (r + 3) * math.sin(a)))
    if f > 0:
        pts_b += [(hx + r * 0.95, hy - 6), (hx + r * 0.35, hy - r * 0.55), (hx - r * 0.2, hy - r * 0.35), (hx - r * 0.75, hy + 2)]
    else:
        pts_b = [(hx - x + hx, y) for x, y in pts_b]
        pts_b += [(hx - r * 0.95, hy - 6), (hx - r * 0.35, hy - r * 0.55), (hx + r * 0.2, hy - r * 0.35), (hx + r * 0.75, hy + 2)]
    poly(d, pts_b, HAIR_G + (255,))
    d.arc(((hx - r + 6) * K, (hy - r + 2) * K, (hx + r - 6) * K, (hy + r - 6) * K), 215, 265, fill=HAIR_HI + (255,),
          width=int(4 * K))
    poly(d, [(hx - f * (r - 2), hy - 8), (hx - f * (r + 4), hy + 30), (hx - f * (r - 10), hy + 38), (hx - f * (r - 8), hy + 4)],
         HAIR_G + (255,))
    # gold purse on the far hand, earring
    hx2, hy2 = pts["hl"]
    line(d, [(hx2, hy2), (hx2 - 6, hy2 + 22)], GOLD + (255,), 2)
    rrect(d, (hx2 - 18, hy2 + 20, hx2 + 6, hy2 + 38), 4, GOLD + (255,))
    ell(d, hx - f * 16, hy + 16, 3, 3, GOLD + (255,))
    face(d, pts, expr, f, t, fem=True)


def lerp_pt(a, b, u):
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)


def girl_old(stage, pts, f=1, wind=0.0, expr="neutral", t=0.0):
    hx, hy, _ = head_dir(pts)
    r = 31 * S
    d0 = ImageDraw.Draw(stage)
    # long hair behind the head and shoulders
    poly(d0, [(hx - f * 6, hy - r), (hx - f * (r + 10 + 10 * wind), hy - 4), (hx - f * (r + 18 + 26 * wind), hy + 70),
              (hx - f * 4, hy + 62), (hx + f * 6, hy + 10)], HAIR + (255,))
    figure(stage, pts, S, light=(0.4, -0.9))
    d = ImageDraw.Draw(stage)
    # fringe on top of the head
    d.chord(((hx - r - 3) * K, (hy - r - 4) * K, (hx + r + 3) * K, (hy + r - 22) * K), 180, 360, fill=HAIR + (255,))
    # dress
    nx, ny = pts["neck"]
    px, py = pts["hip"]
    kx = (pts["kl"][0] + pts["kr"][0]) / 2
    ky = max(pts["kl"][1], pts["kr"][1])
    poly(d, [(nx - 14, ny + 4), (nx + 14, ny + 4), (px + 16, py), (kx + 40, ky + 8), (kx - 40, ky + 8), (px - 16, py)],
         LILAC + (255,))
    line(d, [(px - 16, py), (px + 16, py)], (140, 80, 160, 255), 4)
    # gold purse on the far hand
    hx2, hy2 = pts["hl"]
    line(d, [(hx2, hy2), (hx2 - 6, hy2 + 22)], GOLD + (255,), 2)
    rrect(d, (hx2 - 18, hy2 + 20, hx2 + 6, hy2 + 38), 4, GOLD + (255,))
    ell(d, hx - f * 20, hy + 14, 3, 3, GOLD + (255,))   # earring
    face(d, pts, expr, f, t)


def rich(stage, pts, mode="rich", f=1, expr="neutral", t=0.0):
    figure(stage, pts, S, light=(0.4, -0.9))
    d = ImageDraw.Draw(stage)
    face(d, pts, expr, f, t, glasses=(mode == "rich" and expr not in ("shocked", "nervous")))
    hx, hy, _ = head_dir(pts)
    r = 31 * S
    if mode == "rich":
        outfit(d, pts, NAVY, f, shirt=True)
        nx, ny = pts["neck"]
        d.arc(((nx - 16) * K, (ny - 10) * K, (nx + 16) * K, (ny + 26) * K), 20, 160, fill=GOLD + (255,), width=int(4 * K))
        ell(d, pts["hr"][0], pts["hr"][1] - 8, 7, 5, GOLD + (255,))   # watch
        # slick hair with a quiff
        d.chord(((hx - r - 2) * K, (hy - r - 6) * K, (hx + r + 2) * K, (hy + r - 24) * K), 180, 360, fill=HAIR + (255,))
        poly(d, [(hx + f * 6, hy - r - 2), (hx + f * (r + 12), hy - r + 4), (hx + f * (r - 2), hy - 10)], HAIR + (255,))
    else:   # broke employee: grey cheap suit, loose tie, messy hair
        outfit(d, pts, (96, 100, 110), f, shirt=True, tie=((90, 110, 150), 8 * f))
        d.chord(((hx - r - 2) * K, (hy - r - 6) * K, (hx + r + 2) * K, (hy + r - 24) * K), 180, 360, fill=HAIR + (255,))
        for j in range(5):
            a = math.pi * (1.1 + 0.2 * j)
            line(d, [(hx + 0.8 * r * math.cos(a), hy - 4 + 0.8 * r * math.sin(a)),
                     (hx + 1.3 * r * math.cos(a + 0.2), hy - 6 + 1.3 * r * math.sin(a + 0.2))], HAIR + (255,), 4)


def girl_sheet():
    tiles = []
    for j, (fn, e, lab) in enumerate([(girl_old, "smug", "OLD"), (girl, "neutral", "NEW"), (girl, "laugh", "LAUGH"),
                                       (girl, "smug", "SMUG"), (girl, "cry", "CRY"), (girl, "sad", "SAD")]):
        stage = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
        pts = place(STAND, (540, FLOOR - 113 * S), 1, S)
        fn(stage, pts, 1, 0.2, e, 0.3)
        base = C.stage_bg(((540, 1.0),)).copy()
        base.alpha_composite(stage)
        tile = base.crop((400 * K, (FLOOR - 300) * K, 680 * K, (FLOOR + 20) * K)).resize((280, 320), Image.LANCZOS)
        PW.spaced(ImageDraw.Draw(tile), 140, 296, lab, font("Inter-SemiBold.otf", 16), (236, 238, 246, 255), 3)
        tiles.append(tile)
    out = Image.new("RGB", (280 * 6, 320))
    for i, tl in enumerate(tiles):
        out.paste(tl.convert("RGB"), (i * 280, 0))
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "money", "girl.png")
    out.save(p)
    print(p)


def expr_sheet():
    rows = [("HIM", ["cry", "tired", "determined", "happy"]), ("HER", ["laugh", "smug", "cry", "sad"]),
            ("THE RICH GUY", ["laugh", "smug", "nervous", "shocked"])]
    tiles = []
    for who, exprs in rows:
        for e in exprs:
            stage = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
            pts = place(STAND, (540, FLOOR - 113 * S), 1, S)
            if who == "HIM":
                hero(stage, pts, "ceo" if e == "happy" else "broke", 1, e, 0.3)
            elif who == "HER":
                girl(stage, pts, 1, 0.2, e, 0.3)
            else:
                rich(stage, pts, "broke" if e in ("nervous", "shocked") else "rich", 1, e)
            base = C.stage_bg(((540, 1.0),)).copy()
            base.alpha_composite(stage)
            hx, hy = pts["head"]
            tile = base.crop(((hx - 90) * K, (hy - 70) * K, (hx + 90) * K, (hy + 110) * K)).resize((270, 270), Image.LANCZOS)
            dd = ImageDraw.Draw(tile)
            PW.spaced(dd, 135, 240, f"{who} · {e.upper()}", font("Inter-SemiBold.otf", 15), (236, 238, 246, 255), 2)
            tiles.append(tile)
    out = Image.new("RGB", (270 * 4, 270 * 3))
    for i, tl in enumerate(tiles):
        out.paste(tl.convert("RGB"), ((i % 4) * 270, (i // 4) * 270))
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "money", "faces.png")
    out.save(p)
    print(p)


def sheet():
    stage = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    spots = ((150, 0.8), (540, 1.0), (930, 0.8))
    xs = [110, 320, 540, 760, 970]
    labels = [("HIM", "BROKE"), ("HER", ""), ("THE RICH GUY", ""), ("HIM", "5 YEARS LATER"), ("THE RICH GUY", "5 YEARS LATER")]
    for i, x in enumerate(xs):
        pts = place(STAND, (x, FLOOR - 113 * S), 1, S)
        if i == 0:
            hero(stage, pts, "broke")
        elif i == 1:
            girl(stage, pts, wind=0.3)
        elif i == 2:
            rich(stage, pts, "rich")
        elif i == 3:
            hero(stage, pts, "ceo")
        else:
            rich(stage, pts, "broke")
    base = C.stage_bg(spots).copy()
    base.alpha_composite(stage)
    im = base.resize((W, H), Image.LANCZOS).crop((0, 900, W, 1500))
    d = ImageDraw.Draw(im)
    for x, (a, b) in zip(xs, labels):
        PW.spaced(d, x, 470, a, font("Inter-SemiBold.otf", 22), (236, 238, 246, 255), 3)
        PW.spaced(d, x, 500, b, font("Inter-SemiBold.otf", 16), (150, 156, 176, 255), 3)
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "money", "chars.png")
    im.save(p)
    print(p)


if __name__ == "__main__":
    girl_sheet() if "--girl" in sys.argv else (expr_sheet() if "--faces" in sys.argv else sheet())
