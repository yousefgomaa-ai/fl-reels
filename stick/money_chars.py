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


def head_dir(pts):
    hx, hy = pts["head"]
    nx, ny = pts["neck"]
    a = math.atan2(hy - ny, hx - nx)
    return hx, hy, a


def hero(stage, pts, mode="broke", f=1):
    figure(stage, pts, S, light=(0.4, -0.9), scarf=False)
    d = ImageDraw.Draw(stage)
    if mode == "broke":
        nx, ny = pts["neck"]
        hx, hy = pts["hip"]
        rrect(d, (nx - 34 * f - 18, ny + 6, nx - 34 * f + 18, hy - 14), 6, (86, 70, 54, 255), outline=(40, 32, 26, 255), w=2)
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


def girl(stage, pts, f=1, wind=0.0):
    hx, hy, _ = head_dir(pts)
    r = 31 * S
    d0 = ImageDraw.Draw(stage)
    # long hair behind the head and shoulders
    poly(d0, [(hx - f * 6, hy - r), (hx - f * (r + 10 + 10 * wind), hy - 4), (hx - f * (r + 18 + 26 * wind), hy + 70),
              (hx - f * 4, hy + 62), (hx + f * 6, hy + 10)], HAIR + (255,))
    figure(stage, pts, S, light=(0.4, -0.9))
    d = ImageDraw.Draw(stage)
    # fringe on top of the head
    d.chord(((hx - r - 3) * K, (hy - r - 4) * K, (hx + r + 3) * K, (hy + r) * K), 180, 360, fill=HAIR + (255,))
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
    ell(d, hx + f * 20, hy + 14, 3, 3, GOLD + (255,))   # earring


def rich(stage, pts, mode="rich", f=1):
    figure(stage, pts, S, light=(0.4, -0.9))
    d = ImageDraw.Draw(stage)
    hx, hy, _ = head_dir(pts)
    r = 31 * S
    if mode == "rich":
        outfit(d, pts, NAVY, f, shirt=True)
        nx, ny = pts["neck"]
        d.arc(((nx - 16) * K, (ny - 10) * K, (nx + 16) * K, (ny + 26) * K), 20, 160, fill=GOLD + (255,), width=int(4 * K))
        ell(d, pts["hr"][0], pts["hr"][1] - 8, 7, 5, GOLD + (255,))   # watch
        # slick hair with a quiff
        d.chord(((hx - r - 2) * K, (hy - r - 6) * K, (hx + r + 2) * K, (hy + r - 6) * K), 180, 360, fill=HAIR + (255,))
        poly(d, [(hx + f * 6, hy - r - 2), (hx + f * (r + 12), hy - r + 4), (hx + f * (r - 2), hy - 10)], HAIR + (255,))
        # sunglasses
        rrect(d, (hx + f * 2 - (0 if f > 0 else 30), hy - 8, hx + f * 2 + (30 if f > 0 else 0), hy + 6), 4, (12, 12, 16, 255))
        line(d, [(hx - f * 20, hy - 4), (hx + f * 4, hy - 4)], (12, 12, 16, 255), 3)
    else:   # broke employee: grey cheap suit, loose tie, messy hair
        outfit(d, pts, (96, 100, 110), f, shirt=True, tie=((90, 110, 150), 8 * f))
        d.chord(((hx - r - 2) * K, (hy - r - 6) * K, (hx + r + 2) * K, (hy + r - 6) * K), 180, 360, fill=HAIR + (255,))
        for j in range(5):
            a = math.pi * (1.1 + 0.2 * j)
            line(d, [(hx + 0.8 * r * math.cos(a), hy - 4 + 0.8 * r * math.sin(a)),
                     (hx + 1.3 * r * math.cos(a + 0.2), hy - 6 + 1.3 * r * math.sin(a + 0.2))], HAIR + (255,), 4)


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
    sheet()
