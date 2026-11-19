#!/usr/bin/env python3
"""Channel profile pictures (800x800, shown as a circle) in the reels' style: glowing stickmen under a spotlight.

    python3 stick/avatar.py out_dir
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from keep_trying import pose_from  # noqa
from motivation_bus import GREY, WHITE_B, draw_stick  # noqa
from scroller_reader import GOLD, INK  # noqa

S = 800


def spotlight(cx=400, top=40, floor=640, width=300, strength=1.0):
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    img = np.zeros((S, S, 3), np.float32) + np.array([10, 10, 12], np.float32)
    depth = np.clip((yy - top) / (floor - top), 0, 1)
    half = 26 + depth * width
    cone = np.where((yy >= top) & (yy <= floor), np.clip(1 - np.abs(xx - cx) / half, 0, 1) ** 1.5 * (0.5 + 0.4 * (1 - depth)), 0)
    pool = np.exp(-(((xx - cx) / (width * 1.05)) ** 2 + ((yy - floor) / 26) ** 2))
    bulb = np.exp(-(((xx - cx) ** 2 + (yy - top) ** 2) / (2 * 40 ** 2)))
    light = (cone * 0.6 + pool * 0.8 + bulb) * strength
    img += light[..., None] * np.array([255, 214, 160], np.float32) / 255 * 120
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    d.line([(60, floor), (S - 60, floor)], fill=(90, 90, 96), width=4)
    d.polygon([(cx - 40, top + 8), (cx + 40, top + 8), (cx + 18, top - 22), (cx - 18, top - 22)], fill=(50, 50, 54))
    d.ellipse([cx - 11, top, cx + 11, top + 20], fill=(255, 236, 200))
    return im


def glow_paste(c, spr, anc, x, y, glow):
    if glow:
        g = spr.split()[3].filter(ImageFilter.GaussianBlur(20)).point(lambda v: int(v * glow))
        gl = Image.new("RGBA", spr.size, (255, 255, 255, 0))
        gl.putalpha(g)
        c.alpha_composite(gl, (int(x - anc[0]), int(y - anc[1])))
    c.alpha_composite(spr, (int(x - anc[0]), int(y - anc[1])))


def a_walker():
    """One glowing stickman striding forward under the lamp."""
    c = spotlight()
    s = math.sin(1.2)
    p = pose_from(lean=12, tl=38 * s, sl=-40, tr=-38 * s, sr=-70, al=-35 * s, bl=55, ar=35 * s, br=55)
    spr, anc = draw_stick(p, WHITE_B, "happy", 1, 1.15)
    glow_paste(c, spr, anc, 400, 640, 0.7)
    return c


def b_two():
    """The grey one and the white one side by side: the comparison the channel is about."""
    c = spotlight(width=340)
    p1 = pose_from(lean=8, al=-6, bl=4, ar=6, br=4)                # grey, shoulders down
    spr, anc = draw_stick(p1, GREY, "sad", 1, 1.0)
    glow_paste(c, spr, anc, 300, 640, 0)
    p2 = pose_from(lean=-2, al=-140, bl=-15, ar=140, br=15)       # white, arms up in a V
    spr, anc = draw_stick(p2, WHITE_B, "happy", -1, 1.0)
    glow_paste(c, spr, anc, 500, 640, 0.75)
    return c


def c_steps():
    """A glowing stickman on the top of three steps, gold step edge: starting, moving up."""
    c = spotlight(cx=470, top=60, floor=640, width=260)
    d = ImageDraw.Draw(c)
    for i in range(3):
        x0, y0 = 170 + i * 120, 640 - (i + 1) * 70
        d.rectangle([x0, y0, x0 + 122, 640], fill=(52, 52, 58), outline=INK, width=4)
        d.line([(x0, y0), (x0 + 120, y0)], fill=GOLD if i == 2 else (120, 120, 126), width=7)
    s = math.sin(1.0)
    p = pose_from(lean=14, tl=40 * s, sl=-35, tr=-30 * s, sr=-80, al=-35 * s, bl=55, ar=35 * s, br=55)
    spr, anc = draw_stick(p, WHITE_B, "happy", 1, 0.72)
    glow_paste(c, spr, anc, 470, 640 - 210, 0.7)
    return c


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "stick/avatar"
    os.makedirs(out, exist_ok=True)
    ims = {"avatar-a-walker.png": a_walker(), "avatar-b-two.png": b_two(), "avatar-c-steps.png": c_steps()}
    for name, im in ims.items():
        im.convert("RGB").save(f"{out}/{name}")
    # preview: each as YouTube shows it (circle, big and small)
    pv = Image.new("RGB", (3 * 420, 560), (32, 32, 36))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, S, S], fill=255)
    for i, im in enumerate(ims.values()):
        circ = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        circ.paste(im, (0, 0), mask)
        pv.paste(circ.resize((380, 380), Image.LANCZOS), (20 + i * 420, 20), circ.resize((380, 380)).split()[3])
        sm = circ.resize((88, 88), Image.LANCZOS)
        pv.paste(sm, (166 + i * 420, 440), sm.split()[3])
    pv.save(f"{out}/preview.png")
    print("wrote", out)


if __name__ == "__main__":
    main()
