#!/usr/bin/env python3
"""Facebook page cover in the split look of the avatar (avatar-pro-C2-split.png): cold rain on the left with the
grey figure walking away, warm gold light on the right with the red-scarf hero walking on. 1640x924: phones show
all of it (16:9) with the profile picture over the bottom centre; desktops crop it to the middle 1640x624 band.
So the title sits high in the middle, the two figures on the sides, the bottom centre stays empty.

    python3 stick/fb_cover.py stick/avatar
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perfect_wave as PW  # noqa
import compare as C  # noqa
import avatar_pro as A  # noqa
from compare import K, place  # noqa
from perfect_wave import font  # noqa

FW, FH = 1640, 924
DESK = (0, (FH - 624) // 2, FW, (FH - 624) // 2 + 624)      # what a desktop shows
SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
STAND = PW.STAND
GOLD = (246, 196, 92)


def glow(a, cx, cy, r, col, k=1.0):
    yy, xx = np.mgrid[0:FH, 0:FW].astype(np.float32)
    g = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r)))
    return a + g[..., None] * np.array(col, np.float32) * k


def cover(out):
    floor = 720
    mid = FW // 2
    yy = np.linspace(0, 1, FH, dtype=np.float32)[:, None, None]
    left = np.array((12, 22, 44), np.float32) * (1 - yy) + np.array((5, 8, 16), np.float32) * yy
    right = np.array((52, 34, 10), np.float32) * (1 - yy) + np.array((14, 10, 6), np.float32) * yy
    xx = np.arange(FW)[None, :, None]
    a = np.where(xx < mid, np.repeat(left, FW, 1), np.repeat(right, FW, 1))
    a = glow(a, 1330, 420, 360, (150, 100, 26))
    a = glow(a, 300, 430, 340, (16, 40, 90))
    a = glow(a, mid, 300, 120, (90, 80, 60), 0.6)
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB").resize((FW * K, FH * K), Image.BICUBIC)
    im = im.convert("RGBA")
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(4)
    for _ in range(260):
        x, y = rng.uniform(0, FW), rng.uniform(0, floor - 40)
        r = rng.uniform(0.6, 1.8)
        d.ellipse([(x - r) * K, (y - r) * K, (x + r) * K, (y + r) * K], fill=(225, 230, 255, int(rng.uniform(50, 200))))
    rays = Image.new("RGBA", im.size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(rays)
    for j in range(7):
        x0 = 1080 + j * 85
        rd.polygon([(x0 * K, 0), ((x0 + 40) * K, 0), ((x0 - 80) * K, floor * K), ((x0 - 150) * K, floor * K)],
                   fill=(255, 210, 120, 22))
    im.alpha_composite(rays.filter(ImageFilter.GaussianBlur(12 * K)))
    d = ImageDraw.Draw(im)
    d.rectangle([0, floor * K, mid * K, FH * K], fill=(8, 12, 24, 255))
    d.rectangle([mid * K, floor * K, FW * K, FH * K], fill=(22, 15, 8, 255))
    d.line([0, floor * K, mid * K, floor * K], fill=(70, 96, 150, 255), width=3 * K)
    d.line([mid * K, floor * K, FW * K, floor * K], fill=GOLD + (255,), width=4 * K)
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    s = 1.45
    gp = {"head": (-26, -134), "neck": (-16, -98), "el": (-8, -54), "hl": (6, -14), "er": (-30, -56), "hr": (-26, -12),
          "kl": (-26, 52), "fl": (-36, 112), "kr": (16, 52), "fr": (28, 110)}
    gpts = place(gp, (330, floor - 113 * s), -1, s)
    C.figure(lay, gpts, s, light=(-0.7, -0.7), body=(116, 126, 148))
    hp = dict(STAND, head=(10, -154), neck=(5, -109), el=(-28, -66), hl=(-44, -28), er=(30, -70), hr=(48, -34),
              kl=(-26, 52), fl=(-40, 110), kr=(30, 50), fr=(44, 110))
    hpts = place(hp, (1310, floor - 113 * s), 1, s)
    C.figure(lay, hpts, s, light=(0.7, -0.7))
    A.scarf_tails(ImageDraw.Draw(lay), hpts["neck"], s, -1)
    gl_l = Image.new("RGBA", im.size, (0, 0, 0, 0))
    gl_l.alpha_composite(lay.crop((0, 0, mid * K, FH * K)), (0, 0))
    gl_r = Image.new("RGBA", im.size, (0, 0, 0, 0))
    gl_r.alpha_composite(lay.crop((mid * K, 0, FW * K, FH * K)), (mid * K, 0))
    A.tinted_glow(im, gl_l, (90, 140, 255), 0.55)
    A.tinted_glow(im, gl_r, (255, 200, 110), 0.65)
    top = lay.crop((0, 0, FW * K, floor * K))
    refl = top.transpose(Image.FLIP_TOP_BOTTOM).crop((0, 0, FW * K, (FH - floor) * K))
    refl = refl.resize((refl.width // 4, refl.height // 4)).filter(ImageFilter.GaussianBlur(2)).resize(refl.size)
    fade = np.linspace(0.4, 0.0, refl.height, dtype=np.float32)[:, None]
    refl.putalpha(Image.fromarray((np.asarray(refl.split()[3], np.float32) * fade).astype(np.uint8)))
    im.alpha_composite(refl, (0, floor * K))
    im.alpha_composite(lay)
    d = ImageDraw.Draw(im)
    for _ in range(110):
        x, y = rng.uniform(0, mid - 8), rng.uniform(0, floor + 40)
        d.line([(x * K, y * K), ((x - 8) * K, (y + 30) * K)], fill=(150, 175, 220, 110), width=int(1.6 * K))
    for _ in range(70):
        x, y = rng.uniform(mid + 12, FW), rng.uniform(100, floor - 10)
        r = rng.uniform(1.5, 3.8)
        d.ellipse([(x - r) * K, (y - r) * K, (x + r) * K, (y + r) * K], fill=(255, 222, 150, int(rng.uniform(110, 230))))
    seam = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(seam).line([(mid * K, 0), (mid * K, FH * K)], fill=(255, 240, 210, 255), width=10 * K)
    im.alpha_composite(seam.filter(ImageFilter.GaussianBlur(9 * K)))
    d = ImageDraw.Draw(im)
    d.line([(mid * K, 0), (mid * K, FH * K)], fill=(255, 246, 226, 255), width=2 * K)
    out_im = im.resize((FW, FH), Image.LANCZOS)
    # title high in the middle (inside the desktop band), dark plate behind it
    d = ImageDraw.Draw(out_im)
    plate = Image.new("RGBA", out_im.size, (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle([mid - 420, 196, mid + 420, 396], 30, fill=(0, 0, 0, 150))
    out_im.alpha_composite(plate.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(out_im)
    PW.spaced(d, mid + 4, 214, "TWO PATHS", font(SERIF_B, 120), (0, 0, 0, 180), 14)
    PW.spaced(d, mid, 210, "TWO PATHS", font(SERIF_B, 120), (246, 242, 232, 255), 14)
    PW.spaced(d, mid, 345, "SAME START.  TWO CHOICES.", font(SERIF, 36), GOLD + (255,), 10)
    out_im = out_im.convert("RGB")
    out_im.save(os.path.join(out, "fb-cover.png"))
    # previews: desktop crop, and the phone with the profile circle over the bottom centre
    out_im.crop(DESK).resize((820, 312), Image.LANCZOS).save(os.path.join(out, "fb-cover-desktop.png"))
    ph = out_im.resize((820, 462), Image.LANCZOS)
    av = Image.open(os.path.join(out, "avatar-pro-C2-split.png")).resize((200, 200), Image.LANCZOS)
    m = Image.new("L", (200, 200), 0)
    ImageDraw.Draw(m).ellipse([0, 0, 199, 199], fill=255)
    ring = Image.new("RGB", (212, 212), (36, 37, 41))
    mr = Image.new("L", (212, 212), 0)
    ImageDraw.Draw(mr).ellipse([0, 0, 211, 211], fill=255)
    canvas = Image.new("RGB", (820, 620), (36, 37, 41))
    canvas.paste(ph, (0, 0))
    canvas.paste(ring, (304, 330), mr)
    canvas.paste(av, (310, 336), m)
    canvas.save(os.path.join(out, "fb-cover-phone.png"))


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "avatar"
    cover(out)
    print("ok")
