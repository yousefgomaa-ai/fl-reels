#!/usr/bin/env python3
"""Two Paths page art: profile picture (1080x1080) and Facebook cover (1640x856), in the reels' style.

    python3 stick/brand.py brand/
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perfect_wave as PW  # noqa
import ai_job as AJ  # noqa
import five_minutes as FM  # noqa
from perfect_wave import font, spaced  # noqa

BOLD = FM.BOLD
BG = (5, 5, 7)

PROUD = dict(PW.STAND, head=(0, -152), el=(-28, -146), hl=(-44, -194), er=(26, -148), hr=(40, -196))
SLUMP = dict(PW.STAND, head=(10, -128), neck=(6, -96), el=(-4, -50), hl=(-8, -2), er=(14, -50), hr=(16, -2),
             kl=(-6, 56), fl=(-13, 113), kr=(9, 56), fr=(13, 113))


def figure(im, pose, hip, sc, body, far, glow):
    pts = AJ.place(pose, hip, 1, sc)
    cv = AJ.Canvas(*PW.bbox_of(list(pts.values()), int(140 * sc)))
    AJ.draw_stick(cv, pts, body, far, 1, s=sc)
    spr, off = cv.done()
    if glow:
        im.alpha_composite(PW.glow_of(spr, 0.6, int(18 * sc)), off)
    im.alpha_composite(spr, off)


def paths(im, x0, y0, xl, xr, y1, w0, w1):
    """A road from (x0,y0) that forks to (xl,y1) bright and (xr,y1) dim."""
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for tx, col in ((xr, (70, 72, 82, 255)), (xl, (235, 236, 242, 255))):
        n = 60
        pts = []
        for i in range(n + 1):
            u = i / n
            k = u * u * (3 - 2 * u)
            pts.append((x0 + (tx - x0) * k, y0 + (y1 - y0) * u, w0 + (w1 - w0) * u))
        for (ax, ay, aw), (bx, by, bw) in zip(pts, pts[1:]):
            d.line([(ax, ay), (bx, by)], fill=col, width=int(aw))
            d.ellipse([bx - bw / 2, by - bw / 2, bx + bw / 2, by + bw / 2], fill=col)
    g = lay.filter(ImageFilter.GaussianBlur(14))
    im.alpha_composite(g)
    im.alpha_composite(lay)


def profile(out):
    S = 1080
    im = Image.new("RGBA", (S, S), BG + (255,))
    # soft vignette glow behind the bright figure
    gl = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(gl).ellipse([220, 160, 580, 600], fill=(255, 255, 255, 40))
    im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(90)))
    paths(im, S / 2, S + 20, 400, 690, 520 + 113 * 1.55, 84, 32)
    figure(im, SLUMP, (690, 520), 1.55, AJ.OT, AJ.OT_FAR, False)
    figure(im, PROUD, (400, 520), 1.55, AJ.DOER, AJ.DOER_FAR, True)
    im.convert("RGB").save(os.path.join(out, "profile.png"))


def cover(out):
    Wc, Hc = 1640, 856
    im = Image.new("RGBA", (Wc, Hc), BG + (255,))
    gl = Image.new("RGBA", (Wc, Hc), (0, 0, 0, 0))
    ImageDraw.Draw(gl).ellipse([60, 260, 540, 760], fill=(255, 255, 255, 34))
    im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(110)))
    # the fork, starting at the bottom middle
    paths(im, Wc / 2, Hc + 30, 300, 1340, 600 + 113 * 1.1, 90, 30)
    figure(im, PROUD, (300, 600), 1.1, AJ.DOER, AJ.DOER_FAR, True)
    figure(im, SLUMP, (1340, 600), 1.1, AJ.OT, AJ.OT_FAR, False)
    d = ImageDraw.Draw(im)
    spaced(d, Wc / 2, 250, "TWO PATHS", font(BOLD, 112), (250, 250, 252, 255), 10)
    spaced(d, Wc / 2, 390, "SAME START. DIFFERENT CHOICES.", font("Inter-SemiBold.otf", 34), (190, 194, 204, 255), 8)
    # small red clock, the channel's signature
    s = "NEW REEL EVERY DAY"
    fc = font(BOLD, 30)
    tw = fc.getlength(s) + 2 * len(s)
    d.rounded_rectangle([Wc / 2 - tw / 2 - 22, 450, Wc / 2 + tw / 2 + 22, 506], 8, fill=(16, 6, 6, 255),
                        outline=(90, 24, 22, 255), width=3)
    spaced(d, Wc / 2, 459, s, fc, (255, 64, 56, 255), 2)
    im.convert("RGB").save(os.path.join(out, "cover.png"))


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "brand"
    os.makedirs(out, exist_ok=True)
    profile(out)
    cover(out)
    print(out)
