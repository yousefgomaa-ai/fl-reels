#!/usr/bin/env python3
"""Style frames for Two Paths' own look (owner, 2026-11-19: light, not dark, nothing taken from other channels).

The format: every short starts at one point at the bottom; the road forks in two and each character walks up its own
branch while the camera climbs with them. Characters are round "bean" people (no stick limbs), each with one colour.

    python3 stick/styles.py stick/styles
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scroller_reader import BLACK, BOLD  # noqa

W, H = 1080, 1920
K = 2  # supersampling


def font(p, s):
    return ImageFont.truetype(p, s)


def bean(color, face="happy", tilt=0.0, scale=1.0, outline=(40, 36, 52), legs=0.0, arm=None):
    """A round bean person: pill body in one colour, big eyes, tiny legs and arms. Returns (sprite, foot anchor)."""
    s = scale
    w, h = int(150 * s), int(220 * s)
    pad = int(60 * s)
    im = Image.new("RGBA", ((w + 2 * pad) * K, (h + 2 * pad) * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ox, oy = pad * K, pad * K
    lw = int(7 * s * K)
    dark = tuple(int(c * 0.72) for c in color)
    # legs
    for i, side in enumerate((-1, 1)):
        lx = ox + (w / 2 + side * w * 0.2) * K
        swing = math.sin(legs + i * math.pi) * 14 * s * K
        d.line([(lx, oy + (h - 30 * s) * K), (lx + swing, oy + (h + 26 * s) * K)], fill=outline + (255,), width=int(26 * s * K))
        d.line([(lx, oy + (h - 30 * s) * K), (lx + swing, oy + (h + 26 * s) * K)], fill=dark + (255,), width=int(13 * s * K))
    # body
    d.rounded_rectangle([ox, oy, ox + w * K, oy + h * K], radius=int(w * 0.5 * K), fill=color + (255,), outline=outline + (255,), width=lw)
    d.rounded_rectangle([ox + w * 0.16 * K, oy + h * 0.08 * K, ox + w * 0.42 * K, oy + h * 0.42 * K], radius=int(w * 0.2 * K),
                        fill=(255, 255, 255, 70))
    # arms
    for side in (-1, 1):
        ax = ox + (w / 2 + side * w * 0.5) * K
        ay = oy + h * 0.55 * K
        up = arm == "up"
        ex = ax + side * 34 * s * K
        ey = ay - (60 if up else -40) * s * K
        d.line([(ax, ay), (ex, ey)], fill=outline + (255,), width=int(22 * s * K))
        d.line([(ax, ay), (ex, ey)], fill=dark + (255,), width=int(11 * s * K))
    # face
    fx, fy = ox + w * 0.5 * K, oy + h * 0.36 * K
    for side in (-1, 1):
        ex = fx + side * w * 0.17 * K
        r = w * 0.12 * K
        d.ellipse([ex - r, fy - r * 1.15, ex + r, fy + r * 1.15], fill=(255, 255, 255, 255), outline=outline + (255,), width=int(4 * s * K))
        pr = r * 0.48
        py = fy + (r * 0.25 if face == "sad" else 0)
        d.ellipse([ex - pr + r * 0.15, py - pr, ex + pr + r * 0.15, py + pr], fill=outline + (255,))
    my = fy + w * 0.26 * K
    mw = w * 0.13 * K
    if face == "happy":
        d.chord([fx - mw, my - mw * 0.7, fx + mw, my + mw * 0.9], 0, 180, fill=outline + (255,))
    elif face == "sad":
        d.arc([fx - mw, my, fx + mw, my + mw * 1.2], 200, 340, fill=outline + (255,), width=int(5 * s * K))
    else:
        d.line([(fx - mw * 0.6, my + 4), (fx + mw * 0.6, my + 4)], fill=outline + (255,), width=int(5 * s * K))
    im = im.resize((im.width // K, im.height // K), Image.LANCZOS)
    if tilt:
        im = im.rotate(tilt, resample=Image.BICUBIC, expand=False)
    return im, (pad + w / 2, pad + h + 26 * s)


def place(c, spr_anc, x, y, shadow=(0, 0, 0, 50)):
    spr, (ax, ay) = spr_anc
    sh = Image.new("RGBA", (int(spr.width * 0.7), 40), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([0, 0, sh.width, sh.height], fill=shadow)
    sh = sh.filter(ImageFilter.GaussianBlur(6))
    c.alpha_composite(sh, (int(x - sh.width / 2), int(y - 16)))
    c.alpha_composite(spr, (int(x - ax), int(y - ay)))


def fork_road(d, base_x, base_y, split_y, left_end, right_end, color, edge, width=150):
    """A road from the bottom that splits in two curving branches."""
    def curve(p0, p1, p2, n=40):
        return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                 (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in [i / n for i in range(n + 1)]]
    trunk = [(base_x, H + 100), (base_x, split_y)]
    lb = curve((base_x, split_y), (base_x, split_y - 260), left_end)
    rb = curve((base_x, split_y), (base_x, split_y - 260), right_end)
    for path in (trunk, lb, rb):
        d.line([(x * K, y * K) for x, y in path], fill=edge + (255,), width=(width + 22) * K, joint="curve")
    for path in (trunk, lb, rb):
        d.line([(x * K, y * K) for x, y in path], fill=color + (255,), width=width * K, joint="curve")
    for path in (lb, rb):  # dashed centre line
        for i in range(0, len(path) - 1, 3):
            d.line([(path[i][0] * K, path[i][1] * K), (path[i + 1][0] * K, path[i + 1][1] * K)], fill=(255, 255, 255, 200), width=6 * K)
    return lb, rb


def sign(c, x, y, text_, bg, fg, size=46):
    f = font(BLACK, size)
    tw = f.getlength(text_)
    w_, h_ = int(tw + 50), size + 34
    im = Image.new("RGBA", (w_ * K, (h_ + 70) * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([(w_ / 2 - 6) * K, h_ * K, (w_ / 2 + 6) * K, (h_ + 70) * K], fill=(90, 80, 70, 255))
    d.rounded_rectangle([0, 0, w_ * K, h_ * K], 14 * K, fill=bg + (255,), outline=(40, 36, 52, 255), width=5 * K)
    im = im.resize((w_, h_ + 70), Image.LANCZOS)
    ImageDraw.Draw(im).text((w_ / 2, h_ / 2 + 1), text_, font=f, fill=fg, anchor="mm")
    c.alpha_composite(im, (int(x - w_ / 2), int(y - h_ - 70)))


def style_a():
    """Paper Day: warm cream paper, soft greens, a teal bean and a coral bean."""
    c = Image.new("RGBA", (W, H), (246, 240, 228, 255))
    lay = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    # hills
    d.ellipse([-400 * K, 1100 * K, 900 * K, 2400 * K], fill=(196, 222, 170, 255))
    d.ellipse([400 * K, 1000 * K, 1600 * K, 2300 * K], fill=(178, 212, 156, 255))
    fork_road(d, 540, 1500, 1250, (220, 520), (870, 470), (232, 214, 186), (205, 182, 150))
    for tx, ty, r in ((120, 1050, 70), (960, 1020, 80), (980, 1350, 60)):  # round trees
        d.rectangle([(tx - 10) * K, ty * K, (tx + 10) * K, (ty + 110) * K], fill=(150, 112, 80, 255))
        d.ellipse([(tx - r) * K, (ty - r * 1.4) * K, (tx + r) * K, (ty + r * 0.4) * K], fill=(126, 180, 110, 255), outline=(40, 36, 52, 255), width=5 * K)
    c.alpha_composite(lay.resize((W, H), Image.LANCZOS))
    sign(c, 250, 760, "DAY 30", (255, 255, 255), (40, 36, 52))
    sign(c, 830, 700, "DAY 30", (255, 214, 102), (40, 36, 52))
    place(c, bean((120, 196, 206), "sad", scale=0.85, legs=0.4), 300, 900)
    place(c, bean((255, 128, 102), "happy", scale=0.85, legs=1.6, arm="up"), 790, 850)
    d2 = ImageDraw.Draw(c)
    d2.text((W / 2, 230), "SAME START.", font=font(BLACK, 76), fill=(40, 36, 52), anchor="mm")
    d2.text((W / 2, 320), "TWO PATHS.", font=font(BLACK, 76), fill=(240, 104, 80), anchor="mm")
    return c


def style_b():
    """Two Skies: the screen split on a diagonal, a grey drizzle on the left path, sun on the right."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    left = (xx / W + (H - yy) / H * 0.25) < 0.55
    sky_l = np.stack([150 + yy / H * 30, 162 + yy / H * 30, 182 + yy / H * 20], -1)
    sky_r = np.stack([255 - yy / H * 20, 214 - yy / H * 40 + 30, 150 + yy / H * 40], -1)
    img = np.where(left[..., None], sky_l, sky_r)
    c = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    lay = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.ellipse([820 * K, 260 * K, 1000 * K, 440 * K], fill=(255, 236, 140, 255), outline=(40, 36, 52, 255), width=6 * K)   # sun
    for cx, cy in ((180, 380), (330, 330)):  # cloud
        d.ellipse([(cx - 110) * K, (cy - 60) * K, (cx + 110) * K, (cy + 60) * K], fill=(214, 220, 230, 255), outline=(40, 36, 52, 255), width=5 * K)
    for i in range(26):  # rain streaks
        x = 60 + (i * 53) % 480
        y = 480 + (i * 137) % 700
        d.line([(x * K, y * K), ((x - 14) * K, (y + 46) * K)], fill=(110, 140, 190, 255), width=5 * K)
    fork_road(d, 540, 1500, 1250, (240, 560), (850, 540), (236, 230, 222), (60, 56, 70), width=140)
    c.alpha_composite(lay.resize((W, H), Image.LANCZOS))
    sign(c, 250, 820, "$0 SAVED", (255, 255, 255), (40, 36, 52), 40)
    sign(c, 840, 790, "$1,825", (255, 214, 102), (40, 36, 52), 40)
    place(c, bean((150, 154, 170), "sad", scale=0.85, legs=0.4), 300, 960)
    place(c, bean((255, 168, 60), "happy", scale=0.85, legs=1.6, arm="up"), 800, 930)
    d2 = ImageDraw.Draw(c)
    d2.text((W / 2, 160), "$5 A DAY", font=font(BLACK, 84), fill=(40, 36, 52), anchor="mm")
    return c


def style_c():
    """Pop Board: flat bold colours like a board game, chunky outlines, the road as game tiles."""
    c = Image.new("RGBA", (W, H), (126, 104, 230, 255))
    lay = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i in range(0, H, 120):  # soft diagonal stripes
        d.polygon([(0, i * K), (W * K, (i - 400) * K), (W * K, (i - 340) * K), (0, (i + 60) * K)], fill=(138, 118, 238, 255))
    lb, rb = fork_road(d, 540, 1500, 1300, (230, 520), (860, 480), (255, 246, 222), (40, 36, 52), width=150)
    for path, col in ((lb, (255, 120, 150)), (rb, (90, 214, 170))):  # tiles on each branch
        for j in range(4, len(path) - 1, 7):
            x, y = path[j]
            d.rounded_rectangle([(x - 40) * K, (y - 26) * K, (x + 40) * K, (y + 26) * K], 10 * K, fill=col + (255,), outline=(40, 36, 52, 255), width=5 * K)
    c.alpha_composite(lay.resize((W, H), Image.LANCZOS))
    sign(c, 240, 760, "TRIES: 9", (255, 255, 255), (40, 36, 52), 42)
    sign(c, 850, 720, "TRIES: 14", (255, 226, 92), (40, 36, 52), 42)
    place(c, bean((255, 120, 150), "sad", scale=0.85, legs=0.4), 300, 900)
    place(c, bean((90, 214, 170), "happy", scale=0.85, legs=1.6, arm="up"), 790, 860)
    d2 = ImageDraw.Draw(c)
    d2.text((W / 2, 200), "WHO MAKES IT?", font=font(BLACK, 80), fill=(255, 255, 255), anchor="mm", stroke_width=8, stroke_fill=(40, 36, 52))
    return c


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "stick/styles"
    os.makedirs(out, exist_ok=True)
    frames = [("style-a-paper-day.png", style_a()), ("style-b-two-skies.png", style_b()), ("style-c-pop-board.png", style_c())]
    for n, im in frames:
        im.convert("RGB").save(f"{out}/{n}")
    pv = Image.new("RGB", (3 * 360 + 40, 680), (30, 30, 34))
    for i, (n, im) in enumerate(frames):
        pv.paste(im.convert("RGB").resize((360, 640), Image.LANCZOS), (10 + i * 370, 30))
        ImageDraw.Draw(pv).text((10 + i * 370 + 180, 14), "ABC"[i], font=font(BOLD, 22), fill=(255, 255, 255), anchor="mm")
    pv.save(f"{out}/styles-preview.png")
    print("wrote", out)


if __name__ == "__main__":
    main()
