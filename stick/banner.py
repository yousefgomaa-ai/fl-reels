#!/usr/bin/env python3
"""YouTube banner for "Two Paths" (2560x1440; everything that matters inside the 1546x423 centre that every device
shows). A grey stickman and a glowing white one under two lamps, their paths splitting: one flat and dark, one rising
in steps to a gold edge.

    python3 stick/banner.py stick/avatar
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from keep_trying import pose_from  # noqa
from motivation_bus import GREY, WHITE_B, draw_stick  # noqa
from scroller_reader import BLACK, GOLD, INK, MED  # noqa

BW, BH = 2560, 1440
SAFE = (BW // 2 - 773, BH // 2 - 211, BW // 2 + 773, BH // 2 + 211)   # 1546 x 423
FLOOR = SAFE[3] - 34


def background():
    yy, xx = np.mgrid[0:BH, 0:BW].astype(np.float32)
    img = np.zeros((BH, BW, 3), np.float32) + np.array([10, 10, 12], np.float32)
    light = np.zeros((BH, BW), np.float32)
    for lx, w, s in ((BW / 2 - 470, 230, 0.55), (BW / 2 + 600, 300, 1.0)):
        top = SAFE[1] - 40
        inside = (yy >= top) & (yy <= FLOOR)
        depth = np.clip((yy - top) / (FLOOR - top), 0, 1)
        half = 24 + depth * w
        light += np.where(inside, np.clip(1 - np.abs(xx - lx) / half, 0, 1) ** 1.5 * (0.45 + 0.35 * (1 - depth)), 0) * 0.6 * s
        light += np.exp(-(((xx - lx) / (w * 1.1)) ** 2 + ((yy - FLOOR) / 22) ** 2)) * 0.8 * s
        light += np.exp(-(((xx - lx) ** 2 + (yy - top) ** 2) / (2 * 36 ** 2))) * 0.9
    img += light[..., None] * np.array([255, 214, 160], np.float32) / 255 * 115
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    for lx in (BW / 2 - 470, BW / 2 + 600):
        top = SAFE[1] - 40
        d.polygon([(lx - 38, top + 8), (lx + 38, top + 8), (lx + 17, top - 20), (lx - 17, top - 20)], fill=(50, 50, 54))
        d.ellipse([lx - 10, top, lx + 10, top + 18], fill=(255, 236, 200))
        d.line([(lx, 0), (lx, top - 20)], fill=(50, 50, 54), width=4)
    # left path: flat and dark; right path: steps rising to a gold edge
    d.line([(SAFE[0] - 400, FLOOR), (BW / 2 - 60, FLOOR)], fill=(80, 80, 86), width=5)
    x = BW / 2 + 330
    for i in range(4):
        y0 = FLOOR - (i + 1) * 34
        d.rectangle([x + i * 70, y0, x + i * 70 + 72, FLOOR], fill=(52, 52, 58), outline=INK, width=3)
        d.line([(x + i * 70, y0), (x + i * 70 + 70, y0)], fill=GOLD if i == 3 else (120, 120, 126), width=6)
    d.line([(BW / 2 - 60, FLOOR), (x, FLOOR)], fill=(80, 80, 86), width=5)
    d.line([(x + 4 * 70, FLOOR - 4 * 34), (SAFE[2] + 400, FLOOR - 4 * 34)], fill=GOLD, width=5)
    return im


def paste(c, spr, anc, x, y, glow=0.0):
    if glow:
        g = spr.split()[3].filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * glow))
        gl = Image.new("RGBA", spr.size, (255, 255, 255, 0))
        gl.putalpha(g)
        c.alpha_composite(gl, (int(x - anc[0]), int(y - anc[1])))
    c.alpha_composite(spr, (int(x - anc[0]), int(y - anc[1])))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "stick/avatar"
    os.makedirs(out, exist_ok=True)
    c = background()
    # grey: slow walk, head down, on the flat path
    p = pose_from(lean=10, tl=14, sl=-10, tr=-12, sr=-20, al=-8, bl=6, ar=8, br=6)
    spr, anc = draw_stick(p, GREY, "sad", 1, 0.5)
    paste(c, spr, anc, BW / 2 - 470, FLOOR)
    # white: striding up the steps
    s = math.sin(1.1)
    p = pose_from(lean=12, tl=40 * s, sl=-35, tr=-35 * s, sr=-75, al=-35 * s, bl=55, ar=35 * s, br=55)
    spr, anc = draw_stick(p, WHITE_B, "happy", 1, 0.5)
    paste(c, spr, anc, BW / 2 + 330 + 3 * 70 + 40, FLOOR - 4 * 34, 0.7)
    # title in the middle, tagline under it
    d = ImageDraw.Draw(c)
    d.text((BW / 2, BH / 2 - 60), "TWO PATHS", font=ImageFont.truetype(BLACK, 128), fill=(244, 244, 240), anchor="mm")
    tag = "SAME DAY.  TWO CHOICES."
    f = ImageFont.truetype(MED, 40)
    x = BW / 2 - (f.getlength(tag) + 8 * (len(tag) - 1)) / 2
    for ch in tag:
        d.text((x, BH / 2 + 30), ch, font=f, fill=GOLD + (255,))
        x += f.getlength(ch) + 8
    c.convert("RGB").save(f"{out}/banner-two-paths.png")
    # preview: the parts phones (safe area) and TVs (whole) show
    pv = c.convert("RGB").resize((1280, 720), Image.LANCZOS)
    dd = ImageDraw.Draw(pv)
    dd.rectangle([s_ // 2 for s_ in SAFE], outline=(255, 70, 70), width=2)
    pv.save(f"{out}/banner-preview.png")
    print("wrote", out)


if __name__ == "__main__":
    main()
