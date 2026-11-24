#!/usr/bin/env python3
"""Channel art in the night-stage look of the newer reels (compare.py / steps.py): the red-scarf hero under a
spotlight at a fork - a dark flat road fading into the night (a grey figure walking it), and steps rising into a warm
gold light. Banner 2560x1440 (everything that matters inside the 1546x423 centre) + an 800x800 avatar.

    python3 stick/brand_night.py stick/avatar
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perfect_wave as PW  # noqa
import compare as C  # noqa
from compare import K, INK, BODY, place  # noqa
from perfect_wave import font  # noqa

SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
GOLD = (240, 192, 96)
STAND = PW.STAND


def stage(w, h, floor, spots, warm=None):
    """near-black stage with soft cones, a floor pool and a vignette (1x, returned at 2x RGBA)"""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    img = np.zeros((h, w, 3), np.float32) + np.array([7, 8, 11], np.float32)
    img[yy > floor] = np.array([10, 11, 15], np.float32)
    for sx, st, col in spots:
        half = 40 + (yy / floor) * 260
        cone = np.clip(1 - (np.abs(xx - sx) - half * 0.55) / (half * 0.6), 0, 1) * (yy < floor + 4)
        img += cone[..., None] * np.array(col, np.float32) * 0.55 * st
        pool = np.exp(-(((xx - sx) / 300) ** 2 + ((yy - floor - 26) / 46) ** 2)) * (yy > floor)
        img += pool[..., None] * np.array(col, np.float32) * 1.6 * st
    if warm:
        wx, wy, r = warm
        g = np.exp(-(((xx - wx) / r) ** 2 + ((yy - wy) / (r * 0.8)) ** 2))
        img += g[..., None] * np.array([120, 84, 30], np.float32)
    r = np.sqrt(((xx - w / 2) / w) ** 2 + ((yy - h / 2) / h) ** 2)
    img *= np.clip(1.3 - r * 1.4, 0.2, 1.0)[..., None]
    rng = np.random.default_rng(2)
    img += rng.normal(0, 1.3, img.shape)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").resize((w * K, h * K), Image.BICUBIC)
    im = im.convert("RGBA")
    d = ImageDraw.Draw(im)
    for _ in range(int(w * h / 9000)):
        x, y = rng.uniform(0, w), rng.uniform(0, floor - 60)
        rr = rng.uniform(0.6, 1.8)
        a = int(rng.uniform(40, 190))
        d.ellipse([(x - rr) * K, (y - rr) * K, (x + rr) * K, (y + rr) * K], fill=(220, 226, 255, a))
    return im


def reflect(base, layer, floor, h, strength=0.3):
    top = layer.crop((0, 0, layer.width, floor * K))
    refl = top.transpose(Image.FLIP_TOP_BOTTOM).crop((0, 0, layer.width, (h - floor) * K))
    refl = refl.resize((refl.width // 4, max(1, refl.height // 4)), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
    refl = refl.resize((layer.width, (h - floor) * K), Image.BILINEAR)
    fade = np.linspace(strength, 0.0, refl.height, dtype=np.float32)[:, None]
    refl.putalpha(Image.fromarray((np.asarray(refl.split()[3], np.float32) * fade).astype(np.uint8)))
    base.alpha_composite(refl, (0, floor * K))


def glow_of(layer, a=0.4):
    g = layer.resize((layer.width // 8, layer.height // 8), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6))
    gl = Image.new("RGBA", g.size, (210, 215, 235, 0))
    gl.putalpha(g.split()[3].point(lambda v: int(v * a)))
    return gl.resize(layer.size, Image.BILINEAR)


def steps(d, x0, floor, n=4, w=78, hgt=44, lit=1.0):
    for j in range(n):
        x = x0 + j * w
        top = floor - (j + 1) * hgt
        c = tuple(int(v) for v in (26 + 10 * j, 26 + 9 * j, 30 + 6 * j))
        d.rectangle([x * K, top * K, (x + w) * K, floor * K], fill=c + (255,), outline=INK + (255,), width=2 * K)
        d.line([(x * K, top * K), ((x + w) * K, top * K)], fill=(255, 214, 140, int(140 + 115 * j / (n - 1) * lit)),
               width=4 * K)
    return x0 + n * w, floor - n * hgt


def banner(out):
    BW, BH = 2560, 1440
    SAFE = (BW // 2 - 773, BH // 2 - 211, BW // 2 + 773, BH // 2 + 211)
    floor = SAFE[3] - 40
    hx = 760
    top_x0 = hx + 70
    base = stage(BW, BH, floor, [(hx, 1.0, (40, 42, 50)), (top_x0 + 200, 0.8, (60, 48, 26))],
                 warm=(top_x0 + 330, floor - 230, 260))
    lay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    # the dark road to the left, and the grey figure walking it into the night
    d.line([(SAFE[0] - 200) * K, (floor + 2) * K, hx * K, (floor + 2) * K], fill=(40, 42, 50, 255), width=3 * K)
    gp = place(C.SAD, (hx - 190, floor - 113 * 0.8), -1, 0.8)
    C.figure(lay, gp, 0.8, light=(0.8, -0.6), body=(92, 94, 104), alpha=0.85, blur=1.5)
    # the steps rising into the light
    ex, ey = steps(d, top_x0, floor, w=66)
    d.line([(ex * K, ey * K), ((ex + 70) * K, ey * K)], fill=GOLD + (255,), width=5 * K)
    # the hero: one foot on the first step, looking up at the light
    pose = dict(STAND, head=(10, -152), neck=(4, -108), kr=(26, 40), fr=(56, 70), er=(26, -64), hr=(40, -20))
    pts = place(pose, (hx, floor - 113 * 1.0), 1, 1.0)
    C.figure(lay, pts, 1.0, light=(0.7, -0.7), scarf=True)
    base.alpha_composite(glow_of(lay))
    reflect(base, lay, floor, BH)
    base.alpha_composite(lay)
    im = base.resize((BW, BH), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    tx = 1640
    PW.spaced(d, tx + 4, SAFE[1] + 124, "TWO PATHS", font(SERIF_B, 112), (0, 0, 0, 170), 14)
    PW.spaced(d, tx, SAFE[1] + 120, "TWO PATHS", font(SERIF_B, 112), (244, 240, 230, 255), 14)
    PW.spaced(d, tx, SAFE[1] + 280, "SAME DAY.  TWO CHOICES.", font(SERIF, 38), GOLD + (255,), 12)
    im.convert("RGB").save(os.path.join(out, "banner-night.png"))
    # previews: what a phone shows (the safe band) and what a desktop shows
    im.crop(SAFE).save(os.path.join(out, "banner-night-phone.png"))
    im.crop((0, BH // 2 - 211 - 0, BW, BH // 2 + 211)).resize((1280, 211)).save(os.path.join(out, "banner-night-desktop.png"))


def avatar(out):
    S = 800
    floor = 690
    base = stage(S, S, floor, [(380, 1.3, (46, 48, 58))], warm=(600, 330, 240))
    lay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    steps(d, 470, floor, n=3, w=92, hgt=60)
    pose = dict(STAND, head=(12, -152), neck=(5, -108), kr=(26, 40), fr=(56, 70), er=(26, -64), hr=(40, -20))
    s = 1.95
    pts = place(pose, (360, floor - 113 * s), 1, s)
    C.figure(lay, pts, s, light=(0.7, -0.7), scarf=True)
    base.alpha_composite(glow_of(lay, 0.5))
    reflect(base, lay, floor, S, 0.35)
    base.alpha_composite(lay)
    im = base.resize((S, S), Image.LANCZOS).convert("RGB")
    im.save(os.path.join(out, "avatar-night.png"))
    # circle preview
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).ellipse([0, 0, S - 1, S - 1], fill=255)
    pv = Image.new("RGB", (S, S), (24, 24, 28))
    pv.paste(im, (0, 0), m)
    pv.resize((200, 200), Image.LANCZOS).save(os.path.join(out, "avatar-night-circle.png"))


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "avatar"
    os.makedirs(out, exist_ok=True)
    banner(out)
    avatar(out)
    print("ok")
